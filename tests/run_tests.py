"""Runs every test in this folder. Standard library only.

    python tests/run_tests.py                 every test, one file per process, as many at once as the machine has cores
    python tests/run_tests.py -k wind         only those whose file or function name matches
    python tests/run_tests.py --failed        only the tests that failed in the previous run
    python tests/run_tests.py --related calc/project.py calc/tools/busy.py
                                              only the test files that name one of these modules (and the failures of the previous run)
    python tests/run_tests.py -j 1            one file at a time
    python tests/run_tests.py -v              the traceback of a failure, not just its message
    python tests/run_tests.py --times         after the summary, the time per file and the slowest tests
    python tests/run_tests.py --perf          the tests of time too (files that set PERF = True), left out otherwise
    python tests/run_tests.py --fast          the fast tier only (files that set TIER = "fast"): about three minutes, before every commit
    python tests/run_tests.py --suite-timeout 2400   a full run's ceiling, in seconds (default 1800; 0: none)

No framework, on purpose: this project already carries three dependencies outside the standard library (requirements.txt), and a fourth that exists only to call functions whose names start with `test_` would be one more thing to install before a report can be checked. `pytest`, if it happens to be there, discovers these same files unchanged -- the convention below is its own.

**Every test file runs in a process of its own** (issue #22). Its own process means its own `conftest` -- its own copy of the example project, its own temporary directory and settings, all under its process id (v0.64.2, v0.81) -- so files run side by side as two whole runs of the suite always could. The longest files, as the previous run measured them (`tests/.timings.json`, gitignored), start first.

**No test can hold the run** (issues #22, #108). Each test has a limit drawn from its measured time -- ten times what it took in the previous run, at least 30 s, at most `--test-timeout` (300 s), the ceiling for a test never measured (`test_limit`). The worker's `faulthandler` stops it there first and writes the Python stack of every thread -- the frame it was stuck in, a modal `exec()`, a wait with no end. The parent watches too: it reads the line the worker writes before each test, and kills the process tree of a test still running 30 s past its limit (`GRACE_S`) -- on Windows `faulthandler`'s own `_exit` can hang in the kernel. A process that does not die even then is abandoned after 10 s (`ABANDON_WAIT_S`), named with its PID, and never waited for again. A process silent outside any test for `FILE_MARGIN_S` (its import, its exit) is stopped the same way. A test stopped by a limit tighter than the ceiling is replayed once, alone, at the ceiling: passing then it counts as passed and is reported FLAKY. A full run has a ceiling of its own, `--suite-timeout` (1800 s): past it nothing starts, everything running is stopped and named, and the run is red. Until issue #22 one test waiting on something that never came kept the suite running all night; until issue #108 a worker stuck in its exit kept it running over an hour.

**The tests of time are apart** (v0.117, issue #26): a file that sets `PERF = True` runs with `--perf` only, and is neither run nor counted as skipped otherwise -- a slow or shared machine must not fail the functional suite. **So are the tests of another system**: a test that raises `conftest.OtherSystem` (a console window, the Windows API, Windows' fonts) is counted apart, not among the skips MAX_SKIPPED bounds -- it says nothing missing from this machine, and the CI's job on that system runs it.

Exits 0 when everything passed or was skipped, 1 otherwise (`exit_code`), so woodcore-cli or a CI job can call it. What failed is kept in `tests/.last-run.json` (gitignored) for `--failed`.
"""

import argparse
import codecs
import faulthandler
import importlib.util
import json
import math
import os
import re
import subprocess
import sys
import tempfile
import time
import traceback
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor
from concurrent.futures import wait as wait_for
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent

# Windows consoles default to cp1252, which cannot write a Sigma, a degree sign or an umlaut -- and half the messages in this project carry one, being German and structural. Without this the runner dies on the first failure it tries to print, which is the one moment it must not.
for stream in (sys.stdout, sys.stderr):
    try:
        stream.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)  # line by line into a log file too, so a run in the background can be followed
    except (AttributeError, ValueError):
        pass

# A full run that skips more than this fails (v0.81). Since the project left the code's repository, a test that needs the engineer's own workbooks skips on a clone without them -- which is right -- but a run in which most of the suite quietly skipped would pass while checking nothing. The ceiling is the skips of a clone with no project of its own, and a little room.
MAX_SKIPPED = 15

# One test longer than this is stuck, not slow: the slowest test of a full run took about two minutes in v0.117 (`--times`). The ceiling of every test's limit, and the limit of a test never measured.
TEST_TIMEOUT_S = 300
# A process that neither starts nor finishes a test for this long while no test is running -- its import, between two tests, after its last one (conftest's cleanup, `atexit`) -- is stuck (issue #108, REQ-005). A file has no total limit: one that goes on finishing tests is not stuck, however many it has (a sum of 300 s per test gave the 17 tests of test_updates 90 minutes).
FILE_MARGIN_S = 300

# A measured test's limit (issue #108, D-4): ten times its time in the previous run, at least 30 s, at most --test-timeout. The times were measured with every core busy, so a false red would need a machine ten times slower; a blocked test costs half a minute rather than five.
LIMIT_K = 10
LIMIT_FLOOR_S = 30
# The parent stops a test this long after its limit: the worker's own faulthandler, set to the same limit, has fired by then and written every thread's stack -- the parent arrives after it, for the case where its `_exit` hangs (issue #108).
GRACE_S = 30
# How long the parent waits for a process it killed to end; past it the process is abandoned, never waited for again. On Windows a process stuck in its exit cannot even be killed (`taskkill` answers that there is no such task while it is still listed).
ABANDON_WAIT_S = 10
# `taskkill` itself is a wait: bounded too.
KILL_WAIT_S = 10
# A full run's ceiling (issue #108, D-5): finish's budget of 20 minutes and half as much again, so a healthy suite on a slow machine stays green.
SUITE_TIMEOUT_S = 1800
# How often the parent reads what a worker wrote.
POLL_S = 0.5

# A file whose tests took longer than this in the previous run is cut into as many processes as it takes to bring each under it: `test_fire_tab` alone took 24 minutes of a 25-minute run in v0.117, the other 142 files sharing the cores meanwhile. Each part is a whole process with its own conftest, as a file is; its tests are dealt by their own measured times, the longest first, to the least loaded part.
SHARD_S = 150

TIMINGS = HERE / ".timings.json"    # "test_x.test_y" -> seconds it took when it last ran: the order the next run starts the files in, and how a long file is cut
LAST_RUN = HERE / ".last-run.json"  # {"failed": ["test_x.test_y", ...]}: what --failed reruns -- the times stay in TIMINGS alone

GREEN, RED, YELLOW, DIM, OFF = "\033[32m", "\033[31m", "\033[33m", "\033[2m", "\033[0m"
if not sys.stdout.isatty():
    GREEN = RED = YELLOW = DIM = OFF = ""

TEST_DEF = re.compile(r"^def (test_\w+)\s*\(", re.M)


def is_perf(path):
    """Whether a test file declares itself a test of time: a line `PERF = True` at its top level, read off its text so that the file is not imported to know it."""
    return any(line.split("#")[0].strip() == "PERF = True" for line in path.read_text(encoding="utf-8").splitlines())


def is_fast(path):
    """Whether a test file belongs to the fast tier (`--fast`, spec 2026-10-19-base-saine-nettoyage REQ-005): a line `TIER = "fast"` at its top level, read off its text as `PERF` is. A file that says nothing is in the full suite only -- the default, so that a new test file costs the fast tier nothing until it is chosen for it."""
    return any(line.split("#")[0].strip() in ('TIER = "fast"', "TIER = 'fast'") for line in path.read_text(encoding="utf-8").splitlines())


def exit_code(failed, skipped, filtered):
    """1 where a test failed, or where a full run (`filtered` false: no -k, --failed, --related) skipped more than MAX_SKIPPED; 0 otherwise."""
    if failed:
        return 1
    return 1 if not filtered and skipped > MAX_SKIPPED else 0


# --- the limits, pure: no process, no clock (the time is a parameter) -- tests/test_runner.py calls them directly ---

def test_limit(timings, label, ceiling, k=LIMIT_K, floor=LIMIT_FLOOR_S):
    """The limit of test `label` ("test_x.test_y") and where it comes from, as (seconds, origin): `min(ceiling, max(floor, k x its measured time))`, the time read off `timings` (tests/.timings.json, the previous run's); the ceiling for a test never measured -- new, renamed, a first run on this machine."""
    measured = timings.get(label)
    if not isinstance(measured, (int, float)) or isinstance(measured, bool) or measured < 0:
        return ceiling, "never measured, the ceiling --test-timeout"
    raw = k * measured
    seconds = min(ceiling, max(floor, math.ceil(raw)))
    origin = f"{k} x {measured:g} s measured"
    if seconds == ceiling and raw >= ceiling:
        origin += ", at the ceiling --test-timeout"
    elif seconds == floor and raw <= floor:
        origin += f", raised to the floor of {floor} s"
    return seconds, origin
test_limit.__test__ = False  # a function of the runner, not a test (pytest collects this module's names otherwise)


def stop_reason(state, now, limit, silence=FILE_MARGIN_S, grace=GRACE_S):
    """Whether a worker must be stopped now, from what `_Watch.state()` says it is doing: ("limit", seconds) when the test it runs has gone `grace` past its `limit`; ("silence", seconds) when no test is running and it has neither started nor finished one for more than `silence` -- its import, between two tests, its exit; None otherwise. A file's number of tests is no part of it: one that goes on finishing tests is never stopped for being long (issue #108, REQ-005)."""
    current, since, quiet_since = state
    if current is not None:
        elapsed = now - since
        return ("limit", elapsed) if elapsed > limit + grace else None
    elapsed = now - quiet_since
    return ("silence", elapsed) if elapsed > silence else None


def merge_timings(timings, result, stem):
    """`timings` with the times of what `result` (one worker's) passed or skipped: a test that failed, or was stopped by its limit, keeps the time of its last good run -- else a test failing in 0.01 s would tighten its own limit, and one stopped at its limit widen it (issue #108, REQ-004). A new dict; the tests this run did not reach keep theirs."""
    kept = set(result.get("passed", [])) | {s["name"] for s in result.get("skipped", []) + result.get("other_system", [])}
    merged = dict(timings)
    merged.update({f"{stem}.{n}": round(s, 2) for n, s in result.get("times", {}).items() if n in kept})
    return merged


def last_run(failures):
    """The content of tests/.last-run.json: the labels of what failed, a stopped test among them, for `--failed` -- and nothing else (the times live in TIMINGS alone)."""
    return {"failed": sorted({f"{stem}.{name}" for stem, name, *_rest in failures})}


class _Watch:
    """What a worker is doing, read off the lines it writes (`...  test_x.test_y` before a test, `ok`/`FAIL`/`ERROR`/`SKIP`/`--` and the label after it): the test it is in and since when, or since when it has been between tests. Fed chunks as they come, cut anywhere -- a partial last line is kept for the next chunk (issue #108, ARCH-002). A test printing a line `...  test_x.test_y` of its own would be taken for an announcement: a risk accepted, no test does."""

    def __init__(self, stem, now):
        self._announce = re.compile(r"\.\.\.  " + re.escape(stem) + r"\.(test_\w+)")
        self._end = re.compile(r"(?:ok|FAIL|ERROR|SKIP|--)\S*\s+(?:\S*?)" + re.escape(stem) + r"\.(test_\w+)\b")
        self._partial = ""
        self.current = None     # the test running, or None between tests
        self.since = now        # when it was announced
        self.quiet_since = now  # when the last test started or ended (the start of the process before any)

    def feed(self, chunk, now):
        lines = (self._partial + chunk).split("\n")
        self._partial = lines.pop()
        for line in lines:
            self._line(line.rstrip("\r"), now)
        return self.state()

    def _line(self, line, now):
        started = self._announce.search(line)
        if started:
            self.current, self.since, self.quiet_since = started.group(1), now, now
            return
        ended = self._end.search(line)
        if ended and ended.group(1) == self.current:
            self.current, self.quiet_since = None, now

    def state(self):
        return self.current, self.since, self.quiet_since


def _knob(args, name, default):
    """An attribute of the run that the command line does not offer -- the measured times, the grace, the floor -- set by `main`, or by tests/test_runner.py to make the limits seconds long; its constant otherwise (an `argparse.Namespace` built by a test has none of them)."""
    value = getattr(args, name, None)
    return default if value is None else value


def _load(path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# --- the worker: one file, in a process of its own ---------------------------------------------

def _shard(names, part, parts, stem):
    """The tests of part `part` of `parts`: every name dealt, the longest first by the previous run's times, to the part with the least time so far. Deterministic, so every part computes the same split on its own."""
    timings = _read_json(TIMINGS, {})
    loads = [0.0] * parts
    mine = set()
    for name in sorted(names, key=lambda n: (-timings.get(f"{stem}.{n}", 1.0), n)):
        least = min(range(parts), key=lambda i: (loads[i], i))
        loads[least] += timings.get(f"{stem}.{name}", 1.0)
        if least == part:
            mine.add(name)
    return mine


def run_file(path, names, timeout, result_file, shard=None, limits_file=None):
    """Runs the tests `names` of `path` (all of them when None; part `shard` = (i, n) of them when given) in this process, printing a line per test, and writes what happened to `result_file` as JSON for the parent. Each test's watchdog is set to its limit in `limits_file` (`{"test_x.test_y": seconds, "<import>": seconds}`, written by the parent: the same limits it holds, so the stack is written before the parent has to kill), `timeout` for a test it does not name."""
    limits = _read_json(Path(limits_file), {}) if limits_file else {}
    sys.path.insert(0, str(HERE))
    import conftest  # noqa: E402  -- puts calc/ on the path before any test imports it

    result = {"passed": [], "failed": [], "skipped": [], "other_system": [], "times": {}, "seconds": 0.0, "planned": []}
    started = time.perf_counter()

    def save():
        result["seconds"] = time.perf_counter() - started
        Path(result_file).write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")

    # the import is a step that can hang too: a module that compiles or opens a window at import
    faulthandler.dump_traceback_later(limits.get("<import>", timeout), exit=True)
    try:
        module = _load(path)
    except Exception as exc:
        faulthandler.cancel_dump_traceback_later()
        result["failed"].append({"name": "<import>", "message": f"could not be imported: {exc}", "traceback": traceback.format_exc()})
        print(f"{RED}FAIL{OFF} {path.stem} could not be imported: {exc}", flush=True)
        save()
        return
    faulthandler.cancel_dump_traceback_later()

    planned = [n for n in sorted(dir(module)) if n.startswith("test_") and callable(getattr(module, n))]
    if names is not None:
        planned = [n for n in planned if n in names]
    if shard is not None:
        mine = _shard(planned, shard[0], shard[1], path.stem)
        planned = [n for n in planned if n in mine]
    result["planned"] = planned  # what this process was to run: the parent reruns the rest of it after a test it had to stop
    save()

    for name in planned:
        fn = getattr(module, name)
        label = f"{path.stem}.{name}"
        # Said before the test starts, so that a test stopped by the watchdog below is named by the last line of the output even before the stack is read.
        print(f"{DIM}...  {label}{OFF}", flush=True)
        test_started = time.perf_counter()
        faulthandler.dump_traceback_later(limits.get(label, timeout), exit=True)
        try:
            fn()
        except conftest.OtherSystem as exc:
            result["other_system"].append({"name": name, "message": str(exc)})
            print(f"{DIM}--   {label} -- {exc}{OFF}", flush=True)
        except conftest.Skip as exc:
            result["skipped"].append({"name": name, "message": str(exc)})
            print(f"{YELLOW}SKIP{OFF} {label} {DIM}-- {exc}{OFF}", flush=True)
        except AssertionError as exc:
            result["failed"].append({"name": name, "message": str(exc).strip() or "(no message)", "traceback": traceback.format_exc()})
            print(f"{RED}FAIL{OFF} {label}", flush=True)
            print(f"       {str(exc).strip() or '(no message)'}", flush=True)
        except Exception as exc:  # an error is a failure that says so
            result["failed"].append({"name": name, "message": f"{type(exc).__name__}: {exc}", "traceback": traceback.format_exc()})
            print(f"{RED}ERROR{OFF} {label}: {type(exc).__name__}: {exc}", flush=True)
        else:
            result["passed"].append(name)
            print(f"{GREEN}ok{OFF}   {label}", flush=True)
        finally:
            faulthandler.cancel_dump_traceback_later()
            result["times"][name] = time.perf_counter() - test_started
        save()  # after every test, so that a process stopped later still says what it had done

    # This process's own temporary directory, and never a neighbour's: conftest owns both the path and the removing (v0.64.2). A file a test's thread or child still holds is left for the next run rather than failing this one: what is checked here is the tests, and the directory is gitignored.
    try:
        conftest.cleanup()
    except OSError as exc:
        print(f"{DIM}(tests/.tmp of this process not removed: {exc}){OFF}", flush=True)
    save()


def _leave():
    """Ends a worker without tearing the interpreter down: the `atexit` handlers run (conftest's copy of the project and settings removed), the output is flushed, and the process exits 0. A Qt application torn down at interpreter exit crashed some files' processes after their last test (0xC0000409 for test_notice_bar and test_toolbar) -- a crash a single process for the whole suite hid, and one that says nothing about the tests."""
    import atexit
    try:
        atexit._run_exitfuncs()
    except Exception as exc:  # an exit handler is no test: said, not counted
        print(f"(an exit handler failed: {exc})", flush=True)
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(0)


# --- the parent: which files, how many at once, and the summary ----------------------------------

def _read_json(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def _test_names(path):
    return TEST_DEF.findall(path.read_text(encoding="utf-8"))


def select(args, files):
    """The work of this run: (file, names or None for all) per file, in the order they should start."""
    wanted = {}  # path -> set of names, or None for the whole file

    def add(path, names):
        if names is None or wanted.get(path, set()) is None:
            wanted[path] = None
        else:
            wanted.setdefault(path, set()).update(names)

    by_stem = {p.stem: p for p in files}
    if args.failed or args.related:
        for label in _read_json(LAST_RUN, {}).get("failed", []):
            stem, _, name = label.partition(".")
            if stem in by_stem:
                add(by_stem[stem], None if name in ("", "<import>") else {name})
    if args.related:
        # A test file is related to a module when its text names the module -- an import, a path, a call. A test file given itself is related to itself.
        stems = {Path(p).stem for p in args.related}
        for path in files:
            if path.stem in stems:
                add(path, None)
                continue
            text = path.read_text(encoding="utf-8")
            if any(re.search(rf"\b{re.escape(s)}\b", text) for s in stems if s not in ("__init__", "conftest")):
                add(path, None)
        if any(Path(p).stem in ("conftest", "run_tests") for p in args.related):
            for path in files:
                add(path, None)
    if not (args.failed or args.related):
        for path in files:
            add(path, None)

    if args.k:
        # A file is passed over only when neither its name nor its text holds the pattern: `-k <function name>` must reach a test whose file is named otherwise (periodic audit 260916).
        narrowed = {}
        for path, names in wanted.items():
            if args.k in path.stem:
                narrowed[path] = names
                continue
            if args.k not in path.read_text(encoding="utf-8"):
                continue
            matching = {n for n in _test_names(path) if args.k in n}
            if names is not None:
                matching &= names
            if matching:
                narrowed[path] = matching
        wanted = narrowed

    return list(wanted.items())


def _estimate(path, names, timings):
    """The seconds the tests `names` of `path` (None: all) took in the previous run; a test never measured counts one second. A file none of whose tests was measured falls back on its own total, as the first version of the timings kept it."""
    names = names if names is not None else _test_names(path)
    if not any(f"{path.stem}.{n}" in timings for n in names) and path.stem in timings:
        return timings[path.stem]
    return sum(timings.get(f"{path.stem}.{n}", 1.0) for n in names)


def plan(work, jobs, timings):
    """The processes of this run, the longest first: (path, names, (part, parts) or None, estimated seconds). A file estimated past SHARD_S is cut into parts, at most one per core."""
    items = []
    for path, names in work:
        estimate = _estimate(path, names, timings)
        count = len(names) if names is not None else len(_test_names(path))
        parts = min(jobs, max(1, count), max(1, -(-int(estimate) // SHARD_S)))
        if parts > 1:
            items += [(path, names, (i, parts), estimate / parts) for i in range(parts)]
        else:
            items.append((path, names, None, estimate))
    return sorted(items, key=lambda item: (-item[3], item[0].stem, item[2] or (0, 1)))


def _kill_tree(proc):
    """The process and every process it started, killed -- asked, not waited for: whether it died is `_stop`'s question (issue #108: a worker stuck in its exit outlives `taskkill`)."""
    if os.name == "nt":
        try:
            subprocess.run(["taskkill", "/T", "/F", "/PID", str(proc.pid)], capture_output=True, timeout=KILL_WAIT_S)
        except (subprocess.TimeoutExpired, OSError):
            pass
    try:
        proc.kill()
    except OSError:
        pass


def _stop(proc, abandon_wait):
    """Kills the process tree and waits at most `abandon_wait` seconds for the process to end: "killed" when it did, "abandoned" when it did not -- it is then never waited for again (issue #108, REQ-002)."""
    _kill_tree(proc)
    try:
        proc.wait(timeout=abandon_wait)
        return "killed"
    except subprocess.TimeoutExpired:
        return "abandoned"


def _past(deadline):
    return deadline is not None and time.monotonic() >= deadline


def _empty(**extra):
    return dict({"passed": [], "failed": [], "skipped": [], "other_system": [], "times": {}, "seconds": 0.0, "limits": {}, "flaky": []}, **extra)


def _done(result):
    return set(result["passed"]) | {f["name"] for f in result["failed"]} | {s["name"] for s in result["skipped"] + result["other_system"]}


def _run_once(path, names, shard, args, scratch, attempt, deadline=None, replay=False):
    """The tests `names` of `path` (None: all; part `shard` of them when given) in one process, watched while it runs (issue #108): the parent reads the output as it is written, stops the process tree of a test gone past its limit and the grace, of a process silent outside any test, or of any at the suite's `deadline` (monotonic), and never waits for a process that will not die. `replay`: every test at the ceiling. Returns (result dict, output text, how it was stopped or None)."""
    stem = path.stem
    tag = f"{stem}-{shard[0] if shard else 0}-{attempt}"
    result_file = scratch / f"{tag}.json"
    out_file = scratch / f"{tag}.out"
    limits_file = scratch / f"{tag}.limits.json"
    ceiling = args.test_timeout
    grace = _knob(args, "grace", GRACE_S)
    silence = _knob(args, "silence", FILE_MARGIN_S)
    floor = _knob(args, "limit_floor", LIMIT_FLOOR_S)
    abandon_wait = _knob(args, "abandon_wait", ABANDON_WAIT_S)
    timings = _knob(args, "timings", None)
    if timings is None:
        timings = _read_json(TIMINGS, {})
    planned = sorted(names) if names is not None else sorted(set(_test_names(path)))
    if replay:
        limits = {n: (ceiling, "a replay alone, at the ceiling --test-timeout") for n in planned}
    else:
        limits = {n: test_limit(timings, f"{stem}.{n}", ceiling, floor=floor) for n in planned}
    # the worker's watchdog on its import fires before the parent's silence limit, so that its stack is written first
    import_limit = max(1, silence - grace)
    limits_file.write_text(json.dumps(dict({f"{stem}.{n}": s for n, (s, _o) in limits.items()}, **{"<import>": import_limit})), encoding="utf-8")
    cmd = [sys.executable, str(Path(__file__).resolve()), "--worker", str(path),
           "--test-timeout", str(ceiling), "--result", str(result_file), "--limits", str(limits_file)]
    if names is not None:
        cmd += ["--names", ",".join(sorted(names))]
    if shard is not None:
        cmd += ["--shard", f"{shard[0]}/{shard[1]}"]
    started = time.monotonic()
    env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUNBUFFERED="1")
    with open(out_file, "wb") as out:
        proc = subprocess.Popen(cmd, cwd=str(ROOT), stdout=out, stderr=subprocess.STDOUT, env=env)
    watch = _Watch(stem, started)
    decoder = codecs.getincrementaldecoder("utf-8")(errors="replace")
    code = stop = fate = None
    with open(out_file, "rb") as reader:
        while True:
            try:
                code = proc.wait(timeout=POLL_S)
            except subprocess.TimeoutExpired:
                code = None
            now = time.monotonic()
            watch.feed(decoder.decode(reader.read()), now)
            if code is not None:
                break
            current = watch.current
            stop = stop_reason(watch.state(), now, limits.get(current, (ceiling, ""))[0], silence, grace)
            if stop is None and deadline is not None and now >= deadline:
                stop = ("deadline", now - (watch.since if current is not None else started))
            if stop is not None:
                fate = _stop(proc, abandon_wait)
                break
        watch.feed(decoder.decode(reader.read(), final=True) + "\n", time.monotonic())
    output = out_file.read_text(encoding="utf-8", errors="replace")
    result = _read_json(result_file, None) or _empty(seconds=time.monotonic() - started)
    result.setdefault("other_system", [])
    result.setdefault("flaky", [])
    result["limits"] = {n: s for n, (s, _o) in limits.items()}
    if code == 0 and stop is None:
        return result, output, None

    # The process ended before its tests did, or was stopped. The test it was in is the last one it announced and did not finish.
    announced = re.findall(r"\.\.\.  " + re.escape(stem) + r"\.(test_\w+)", output)
    if stop is not None and stop[0] != "silence" and watch.current is not None:
        stuck = watch.current
    elif not announced:
        stuck = "<import>"
    elif announced[-1] not in _done(result):
        stuck = announced[-1]
    else:
        stuck = "<process>"  # after its last test: conftest's cleanup, an atexit, a thread left running
    limit, origin = limits.get(stuck, (ceiling, "never measured, the ceiling --test-timeout"))
    stack = "Timeout (" in output
    where = "the stack of every thread is in the output (-v)" if stack else "what it printed is in the output (-v)"
    kind = stop[0] if stop is not None else ("limit" if stack and stuck.startswith("test_") else "watchdog" if stack else "crash")
    elapsed = stop[1] if stop is not None else limit
    fate_said = {"killed": f"process tree killed by the runner at {elapsed:.0f} s", "abandoned": f"process not ended (PID {proc.pid}), abandoned -- it may still be running",
                 None: "ended by its own watchdog"}[fate]
    if kind == "limit":
        why = f"stopped after {limit} s -- limit = {origin}; {fate_said}; {where}"
    elif kind == "silence":
        during = "its import" if stuck == "<import>" else "after its last test" if stuck == "<process>" else "between two tests"
        why = f"silent for {elapsed:.0f} s outside any test ({during}), past the {silence} s a process may be; {fate_said}; {where}"
    elif kind == "deadline":
        why = f"still running at the suite's deadline (--suite-timeout), {elapsed:.0f} s into {'this test' if stuck.startswith('test_') else 'this process'}; {fate_said}; {where}"
    elif kind == "watchdog":
        why = f"its import ran past {import_limit} s and was stopped by its own watchdog; {where}"
    else:
        why = f"the process ended with code {code}"
    stopped = {"name": stuck, "kind": kind, "limit": limit, "origin": origin, "abandoned": fate == "abandoned", "pid": proc.pid, "elapsed": elapsed}
    result["failed"].append({"name": stuck, "message": why, "traceback": output[-8000:], "process": True, "stop": stopped})
    return result, output, stopped


def _replayable(stopped, ceiling, deadline):
    """Whether a test stopped by its limit is replayed once at the ceiling (issue #108, REQ-010, D-6): not when its limit already was the ceiling (the replay would be the same run, five minutes more), when its process was abandoned (it may still hold what the test uses), when it did not stop on a limit (an assertion is a plain red), or past the suite's deadline."""
    return (stopped is not None and stopped["kind"] == "limit" and stopped["name"].startswith("test_")
            and stopped["limit"] < ceiling and not stopped["abandoned"] and not _past(deadline))


def run_worker(path, names, shard, args, scratch, deadline=None):
    """One file -- or one part of a long one -- in a process of its own; when a test of it had to be stopped, the tests after it in a new one, so that one stuck test costs its own result and no other; and then that test once more, alone, at the ceiling, when it was stopped by a tighter limit (REQ-010). Past the suite's `deadline` nothing starts. Returns (path, names, shard, result dict, output text, seconds)."""
    started = time.monotonic()
    if _past(deadline):
        return path, names, shard, _empty(not_started=True), "", 0.0
    result, output, stopped = _run_once(path, names, shard, args, scratch, 0, deadline)
    everything = result.get("planned") or (sorted(names) if names is not None else sorted(set(_test_names(path))))
    attempt = 100 * shard[0] if shard else 0
    stops = [stopped] if stopped else []
    while stopped is not None and stopped["name"].startswith("test_") and not _past(deadline):
        rest = {n for n in everything if n not in _done(result)}
        if not rest:
            break
        attempt += 1
        more, more_output, stopped = _run_once(path, rest, None, args, scratch, attempt, deadline)
        for key in ("passed", "failed", "skipped", "other_system"):
            result[key] += more[key]
        result["times"].update(more["times"])
        result["limits"].update(more["limits"])
        output += more_output
        if stopped:
            stops.append(stopped)
    for first in stops:
        if not _replayable(first, args.test_timeout, deadline):
            continue
        name = first["name"]
        attempt += 1
        more, more_output, again = _run_once(path, {name}, None, args, scratch, attempt, deadline, replay=True)
        output += f"\n(replayed alone at the ceiling of {args.test_timeout} s: {path.stem}.{name})\n" + more_output
        before = next(f for f in result["failed"] if f["name"] == name and f.get("process"))
        result["failed"].remove(before)
        if name in more["passed"]:
            result["passed"].append(name)
            result["flaky"].append({"name": name, "message": f"passed when replayed alone; the first attempt was {before['message']}"})
        else:
            for f in more["failed"]:
                if f["name"] == name:
                    f["message"] = f"{f['message']} -- replayed alone after a first attempt {before['message']}"
            result["failed"] += more["failed"]
            result["skipped"] += more["skipped"]
            result["other_system"] += more["other_system"]
        result["times"].update(more["times"])
    return path, names, shard, result, output, time.monotonic() - started


def execute(items, jobs, args, scratch, deadline=None, on_done=None):
    """Runs the processes `items` (as `plan` gives them), `jobs` at once, until all are done or the suite's `deadline` (monotonic) passes: then nothing more starts, and each worker stops what it runs (issue #108, REQ-006). Never joins a thread that does not return -- the pool is shut down without waiting. `on_done(item, count)` is called as each process ends. Returns (finished items, the (path, names, shard) never started, those whose thread still had not returned well after the deadline)."""
    abandon_wait = _knob(args, "abandon_wait", ABANDON_WAIT_S)
    pool = ThreadPoolExecutor(max_workers=jobs)
    futures = {pool.submit(run_worker, path, names, shard, args, scratch, deadline): (path, names, shard) for path, names, shard, _estimate in items}
    pending = set(futures)
    finished, not_started, hung = [], [], []
    give_up = None
    try:
        while pending:
            now = time.monotonic()
            if deadline is not None and now >= deadline and give_up is None:
                pool.shutdown(wait=False, cancel_futures=True)
                # each worker notices the deadline within a poll, then kills and waits at most abandon_wait
                give_up = now + KILL_WAIT_S + abandon_wait + 4 * POLL_S + 5
            # a future cancelled by the shutdown is not "done" for `wait` (only one cancelled by the pool itself is): taken out here
            for future in [f for f in pending if f.cancelled()]:
                pending.discard(future)
                not_started.append(futures[future])
            if not pending:
                break
            if give_up is not None and now >= give_up:
                hung = [futures[f] for f in pending]
                break
            until = give_up if give_up is not None else deadline
            timeout = max(0.05, until - now) if until is not None else 5.0
            done, pending = wait_for(pending, timeout=timeout, return_when=FIRST_COMPLETED)
            for future in done:
                if future.cancelled():
                    not_started.append(futures[future])
                    continue
                item = future.result()
                if item[3].get("not_started"):
                    not_started.append(futures[future])
                    continue
                finished.append(item)
                if on_done is not None:
                    on_done(item, len(finished))
    finally:
        pool.shutdown(wait=False, cancel_futures=True)
    return finished, not_started, hung


def report_lines(stem, result, output):
    """What the parent prints of one finished process: the worker's own lines (its announcements left out), one `FAIL` line per test it had to stop, one `FLAKY` line per test that passed only when replayed."""
    lines = [line for line in output.splitlines() if not line.startswith(f"{DIM}...  ") and not line.startswith("...  ")]
    for f in result["failed"]:
        if f.get("process"):
            lines.append(f"{RED}FAIL{OFF} {stem}.{f['name']}: {f['message']}")
    for f in result.get("flaky", []):
        lines.append(f"{YELLOW}FLAKY{OFF} {stem}.{f['name']}: {f['message']}")
    return lines


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("-k", metavar="PATTERN", default="", help="only tests whose file or function name contains this")
    ap.add_argument("-v", action="store_true", help="print the traceback of a failure")
    ap.add_argument("-j", type=int, default=0, metavar="N", help="files run at once (default: the machine's cores)")
    ap.add_argument("--failed", action="store_true", help="only the tests that failed in the previous run")
    ap.add_argument("--related", nargs="+", metavar="PATH", help="only the test files naming one of these modules, and the previous run's failures")
    ap.add_argument("--times", action="store_true", help="print the time per file, the slowest tests and the tightest limits after the summary")
    ap.add_argument("--perf", action="store_true", help="run the tests of time too (files that set PERF = True)")
    ap.add_argument("--fast", action="store_true", help='only the fast tier (files that set TIER = "fast"): the engine, the norms, the contracts and the export, in about three minutes')
    ap.add_argument("--test-timeout", type=int, default=TEST_TIMEOUT_S, metavar="S", help=f"a test running longer is stopped and fails: the ceiling of each test's limit, which is {LIMIT_K} x its measured time, at least {LIMIT_FLOOR_S} s (default {TEST_TIMEOUT_S})")
    ap.add_argument("--suite-timeout", type=int, default=SUITE_TIMEOUT_S, metavar="S", help=f"a full run still going after this is stopped, what runs named, and red; 0: no ceiling (default {SUITE_TIMEOUT_S})")
    ap.add_argument("--worker", help=argparse.SUPPRESS)
    ap.add_argument("--names", help=argparse.SUPPRESS)
    ap.add_argument("--result", help=argparse.SUPPRESS)
    ap.add_argument("--shard", help=argparse.SUPPRESS)
    ap.add_argument("--limits", help=argparse.SUPPRESS)
    args = ap.parse_args()

    if args.worker:
        names = set(args.names.split(",")) if args.names else None
        shard = tuple(int(x) for x in args.shard.split("/")) if args.shard else None
        run_file(Path(args.worker), names, args.test_timeout, args.result, shard, args.limits)
        _leave()

    files = sorted(HERE.glob("test_*.py"))
    left_out = [p.stem for p in files if not args.perf and is_perf(p)]
    files = [p for p in files if p.stem not in left_out]
    if args.fast:
        files = [p for p in files if is_fast(p)]
    work = select(args, files)
    if not work:
        print("no test selected" + (" -- the previous run failed nothing" if args.failed else ""))
        return 0
    jobs = max(1, args.j or os.cpu_count() or 4)
    timings = _read_json(TIMINGS, {})
    args.timings = timings  # what each process's limits are drawn from: the times of the previous run, read once
    items = plan(work, jobs, timings)
    jobs = min(jobs, len(items))
    cut = {i[0].stem for i in items if i[2]}
    full = not (args.k or args.failed or args.related)
    # the suite's ceiling holds for a full run only: a partial one has the limits of its tests and processes
    deadline = time.monotonic() + args.suite_timeout if full and args.suite_timeout > 0 else None
    print(f"{len(work)} files" + (f", {len(cut)} of them cut into parts" if cut else "") + f", {len(items)} processes, {jobs} at once"
          + (f", a ceiling of {args.suite_timeout} s" if deadline else ""))

    counts = {"passed": 0, "failed": 0, "skipped": 0, "other_system": 0, "flaky": 0}
    failures = []      # (stem, name, message, traceback)
    flaky = []         # (stem, name, message)
    abandoned = []     # (stem, name, pid)
    at_deadline = []   # (stem, name, seconds, traceback)
    per_file = {}
    per_test = []
    tight = []         # (share of its limit, seconds, limit, label)
    merged = {"timings": timings}
    started = time.time()

    def on_done(item, done_count):
        path, names, shard, result, output, seconds = item
        # The worker's own lines, whole and together, once its file is done: files running side by side would otherwise interleave their lines.
        for line in report_lines(path.stem, result, output):
            print(line)
        for key in counts:
            counts[key] += len(result.get(key, []))
        for f in result["failed"]:
            failures.append((path.stem, f["name"], f["message"], f.get("traceback", "")))
            stopped = f.get("stop") or {}
            if stopped.get("abandoned"):
                abandoned.append((path.stem, f["name"], stopped.get("pid")))
            if stopped.get("kind") == "deadline":
                at_deadline.append((path.stem, f["name"], stopped.get("elapsed", 0.0), f.get("traceback", "")))
        flaky.extend((path.stem, f["name"], f["message"]) for f in result.get("flaky", []))
        per_file[path.stem] = per_file.get(path.stem, 0.0) + seconds
        per_test.extend((s, f"{path.stem}.{n}") for n, s in result["times"].items())
        for n, s in result["times"].items():
            limit = result.get("limits", {}).get(n)
            if limit:
                tight.append((s / limit, s, limit, f"{path.stem}.{n}"))
        merged["timings"] = merge_timings(merged["timings"], result, path.stem)
        part = f" (part {shard[0] + 1}/{shard[1]})" if shard else ""
        print(f"{DIM}[{done_count}/{len(items)}] {path.stem}{part} {seconds:.1f} s, {time.time() - started:.0f} s since the start{OFF}")

    # ignore_cleanup_errors: an abandoned process may still hold its output file open (Windows refuses to remove it)
    with tempfile.TemporaryDirectory(prefix="woodcore-tests-", ignore_cleanup_errors=True) as scratch:
        _finished, not_started, hung = execute(items, jobs, args, Path(scratch), deadline, on_done)

    # keyed by test (a file's own total kept where an older run left one), and only what still exists: a renamed test does not keep its old time forever
    known = {f"{p.stem}.{n}" for p in files for n in _test_names(p)}
    TIMINGS.write_text(json.dumps({k: v for k, v in sorted(merged["timings"].items()) if k in known or k in {p.stem for p in files}}, indent=1) + "\n", encoding="utf-8")
    LAST_RUN.write_text(json.dumps(last_run(failures), indent=1) + "\n", encoding="utf-8")

    if args.v and failures:
        print()
        for stem, name, _msg, tb in failures:
            print(f"{DIM}{'-' * 72}{OFF}")
            print(f"{stem}.{name}")
            print(tb)

    elapsed = time.time() - started
    print()
    if at_deadline or not_started or hung:
        print(f"{RED}The suite reached its ceiling of {args.suite_timeout} s (--suite-timeout).{OFF}")
        if at_deadline:
            print("Still running at the deadline:")
            for stem, name, seconds, tb in at_deadline:
                print(f"  {stem}.{name} -- for {seconds:.0f} s")
                if "Timeout (" in tb:
                    print("\n".join("    " + line for line in tb[tb.index("Timeout ("):].splitlines()[:40]))
        if hung:
            print("Still running, their thread never returned: " + ", ".join(p.stem + (f" (part {s[0] + 1}/{s[1]})" if s else "") for p, _n, s in hung))
        if not_started:
            print("Not started: " + ", ".join(p.stem + (f" (part {s[0] + 1}/{s[1]})" if s else "") for p, _n, s in not_started))
        print()
    if abandoned:
        print("Processes abandoned, perhaps still running: " + ", ".join(f"{stem}.{name} (PID {pid})" for stem, name, pid in abandoned))
        print()
    if flaky:
        print("Flaky (stopped by its limit, passed when replayed alone):")
        for stem, name, msg in flaky:
            print(f"  {YELLOW}{stem}.{name}{OFF} -- {msg.splitlines()[0] if msg else ''}")
        print()
    if failures:
        print("Failed:")
        for stem, name, msg, _tb in failures:
            print(f"  {RED}{stem}.{name}{OFF} -- {msg.splitlines()[0] if msg else ''}")
        print(f"  {DIM}python tests/run_tests.py --failed   reruns these alone{OFF}")
        print()
    summary = f"{counts['passed']} passed"
    if counts["skipped"]:
        summary += f", {counts['skipped']} skipped"
    if counts["flaky"]:
        summary += f", {counts['flaky']} flaky"
    if counts["failed"]:
        summary += f", {counts['failed']} FAILED"
    if not_started or hung:
        summary += f", {len(not_started) + len(hung)} processes not finished"
    print(f"{summary} in {elapsed:.1f} s")
    if args.times:
        cpu = sum(per_file.values()) or 1.0
        print()
        print(f"Time per file (import included, its parts added up), slowest first -- {cpu:.0f} s in all, {jobs} at once:")
        for stem, seconds in sorted(per_file.items(), key=lambda item: -item[1]):
            print(f"  {seconds:7.1f} s  {seconds / cpu:5.1%}  {stem}")
        print()
        print("Slowest tests:")
        for seconds, label in sorted(per_test, reverse=True)[:10]:
            print(f"  {seconds:7.1f} s  {label}")
        if tight:
            print()
            print("Tightest limits (this run's time against the limit it ran under):")
            for share, seconds, limit, label in sorted(tight, reverse=True)[:10]:
                print(f"  {seconds:7.1f} s of {limit:4d} s  {share:5.1%}  {label}")
    if left_out:
        print(f"{DIM}tests of time left out (run them with --perf): {', '.join(left_out)}{OFF}")
    if counts["other_system"]:
        print(f"{DIM}{counts['other_system']} tests of another operating system left out (conftest.OtherSystem; the CI runs them there){OFF}")
    if full and counts["skipped"] > MAX_SKIPPED:
        print(f"{RED}{counts['skipped']} tests skipped, more than the {MAX_SKIPPED} a clone of the code skips -- this run checked less than it seems{OFF}")
    code = exit_code(counts["failed"], counts["skipped"], not full)
    if not_started or hung:
        code = 1
    if hung:
        # a thread that never returned would hold the interpreter's exit, which joins the pool's threads: leave without it
        sys.stdout.flush()
        sys.stderr.flush()
        os._exit(code)
    return code


if __name__ == "__main__":
    sys.exit(main())
