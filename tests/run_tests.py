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

No framework, on purpose: this project already carries three dependencies outside the standard library (requirements.txt), and a fourth that exists only to call functions whose names start with `test_` would be one more thing to install before a report can be checked. `pytest`, if it happens to be there, discovers these same files unchanged -- the convention below is its own.

**Every test file runs in a process of its own** (issue #22). Its own process means its own `conftest` -- its own copy of the example project, its own temporary directory and settings, all under its process id (v0.64.2, v0.81) -- so files run side by side as two whole runs of the suite always could. The longest files, as the previous run measured them (`tests/.timings.json`, gitignored), start first.

**No test can hold the run** (issue #22). A test still running after `--test-timeout` seconds is stopped by `faulthandler`, which first writes the Python stack of every thread -- the frame it was stuck in, a modal `exec()` or a `wait()` with no end -- and the run goes on with the next file, counting it as failed. Until then one test waiting on something that never came kept the suite running all night.

**The tests of time are apart** (v0.117, issue #26): a file that sets `PERF = True` runs with `--perf` only, and is neither run nor counted as skipped otherwise -- a slow or shared machine must not fail the functional suite. **So are the tests of another system**: a test that raises `conftest.OtherSystem` (a console window, the Windows API, Windows' fonts) is counted apart, not among the skips MAX_SKIPPED bounds -- it says nothing missing from this machine, and the CI's job on that system runs it.

Exits 0 when everything passed or was skipped, 1 otherwise (`exit_code`), so woodcore-cli or a CI job can call it. What failed is kept in `tests/.last-run.json` (gitignored) for `--failed`.
"""

import argparse
import faulthandler
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
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

# One test longer than this is stuck, not slow: the slowest test of a full run took about two minutes in v0.117 (`--times`). A file gets the sum of its tests' allowance and a margin for its import.
TEST_TIMEOUT_S = 300
FILE_MARGIN_S = 300

# A file whose tests took longer than this in the previous run is cut into as many processes as it takes to bring each under it: `test_fire_tab` alone took 24 minutes of a 25-minute run in v0.117, the other 142 files sharing the cores meanwhile. Each part is a whole process with its own conftest, as a file is; its tests are dealt by their own measured times, the longest first, to the least loaded part.
SHARD_S = 150

TIMINGS = HERE / ".timings.json"    # "test_x.test_y" -> seconds it took when it last ran: the order the next run starts the files in, and how a long file is cut
LAST_RUN = HERE / ".last-run.json"  # {"failed": ["test_x.test_y", ...]}: what --failed reruns

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


def run_file(path, names, timeout, result_file, shard=None):
    """Runs the tests `names` of `path` (all of them when None; part `shard` = (i, n) of them when given) in this process, printing a line per test, and writes what happened to `result_file` as JSON for the parent."""
    sys.path.insert(0, str(HERE))
    import conftest  # noqa: E402  -- puts calc/ on the path before any test imports it

    result = {"passed": [], "failed": [], "skipped": [], "other_system": [], "times": {}, "seconds": 0.0, "planned": []}
    started = time.perf_counter()

    def save():
        result["seconds"] = time.perf_counter() - started
        Path(result_file).write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")

    # the import is a step that can hang too: a module that compiles or opens a window at import
    faulthandler.dump_traceback_later(timeout, exit=True)
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
        faulthandler.dump_traceback_later(timeout, exit=True)
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
    if os.name == "nt":
        subprocess.run(["taskkill", "/T", "/F", "/PID", str(proc.pid)], capture_output=True)
    else:
        proc.kill()


def _run_once(path, names, shard, args, scratch, attempt):
    """The tests `names` of `path` (None: all; part `shard` of them when given) in one process. Returns (result dict, output text, the test it was stopped in or None)."""
    tag = f"{path.stem}-{shard[0] if shard else 0}-{attempt}"
    result_file = scratch / f"{tag}.json"
    out_file = scratch / f"{tag}.out"
    cmd = [sys.executable, str(Path(__file__).resolve()), "--worker", str(path),
           "--test-timeout", str(args.test_timeout), "--result", str(result_file)]
    if names is not None:
        cmd += ["--names", ",".join(sorted(names))]
    if shard is not None:
        cmd += ["--shard", f"{shard[0]}/{shard[1]}"]
    count = len(names) if names is not None else max(1, len(_test_names(path)))
    limit = count * args.test_timeout + FILE_MARGIN_S
    started = time.perf_counter()
    env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUNBUFFERED="1")
    with open(out_file, "w", encoding="utf-8", errors="replace") as out:
        proc = subprocess.Popen(cmd, cwd=str(ROOT), stdout=out, stderr=subprocess.STDOUT, env=env)
        try:
            code = proc.wait(timeout=limit)
        except subprocess.TimeoutExpired:
            _kill_tree(proc)
            proc.wait()
            code = None
    seconds = time.perf_counter() - started
    output = out_file.read_text(encoding="utf-8", errors="replace")
    result = _read_json(result_file, None) or {"passed": [], "failed": [], "skipped": [], "other_system": [], "times": {}, "seconds": seconds}
    result.setdefault("other_system", [])
    if code != 0:
        # The process ended before its tests did: stopped by the watchdog (faulthandler prints «Timeout (0:05:00)!» and every thread's stack), killed at the file's limit, or crashed in C. The test it was in is the last one it announced and did not finish.
        done = set(result["passed"]) | {f["name"] for f in result["failed"]} | {s["name"] for s in result["skipped"] + result["other_system"]}
        announced = re.findall(r"\.\.\.  " + re.escape(path.stem) + r"\.(test_\w+)", output)
        if not announced:
            stuck = "<import>"
        elif announced[-1] not in done:
            stuck = announced[-1]
        else:
            stuck = "<process>"  # after its last test: conftest's cleanup, an atexit, a thread left running
        if "Timeout (" in output:
            why = f"stopped after {args.test_timeout} s -- stuck; the stack of every thread is in the output (-v)"
        elif code is None:
            why = f"the file ran past its limit of {limit} s and was killed"
        else:
            why = f"the process ended with code {code}"
        result["failed"].append({"name": stuck, "message": why, "traceback": output[-8000:], "process": True})
        return result, output, stuck
    return result, output, None


def run_worker(path, names, shard, args, scratch):
    """One file -- or one part of a long one -- in a process of its own; and, when a test of it had to be stopped, the tests after it in a new one, so that one stuck test costs its own result and no other. Returns (path, names, shard, result dict, output text, seconds)."""
    started = time.perf_counter()
    result, output, stuck = _run_once(path, names, shard, args, scratch, 0)
    everything = result.get("planned") or (sorted(names) if names is not None else sorted(set(_test_names(path))))
    attempt = 0
    while stuck is not None and stuck.startswith("test_"):
        done = set(result["passed"]) | {f["name"] for f in result["failed"]} | {s["name"] for s in result["skipped"] + result["other_system"]}
        rest = {n for n in everything if n not in done}
        if not rest:
            break
        attempt += 1
        more, more_output, stuck = _run_once(path, rest, None, args, scratch, attempt + (100 * shard[0] if shard else 0))
        for key in ("passed", "failed", "skipped", "other_system"):
            result[key] += more[key]
        result["times"].update(more["times"])
        output += more_output
    return path, names, shard, result, output, time.perf_counter() - started


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("-k", metavar="PATTERN", default="", help="only tests whose file or function name contains this")
    ap.add_argument("-v", action="store_true", help="print the traceback of a failure")
    ap.add_argument("-j", type=int, default=0, metavar="N", help="files run at once (default: the machine's cores)")
    ap.add_argument("--failed", action="store_true", help="only the tests that failed in the previous run")
    ap.add_argument("--related", nargs="+", metavar="PATH", help="only the test files naming one of these modules, and the previous run's failures")
    ap.add_argument("--times", action="store_true", help="print the time per file and the slowest tests after the summary")
    ap.add_argument("--perf", action="store_true", help="run the tests of time too (files that set PERF = True)")
    ap.add_argument("--fast", action="store_true", help='only the fast tier (files that set TIER = "fast"): the engine, the norms, the contracts and the export, in about three minutes')
    ap.add_argument("--test-timeout", type=int, default=TEST_TIMEOUT_S, metavar="S", help=f"a test running longer is stopped and fails (default {TEST_TIMEOUT_S})")
    ap.add_argument("--worker", help=argparse.SUPPRESS)
    ap.add_argument("--names", help=argparse.SUPPRESS)
    ap.add_argument("--result", help=argparse.SUPPRESS)
    ap.add_argument("--shard", help=argparse.SUPPRESS)
    args = ap.parse_args()

    if args.worker:
        names = set(args.names.split(",")) if args.names else None
        shard = tuple(int(x) for x in args.shard.split("/")) if args.shard else None
        run_file(Path(args.worker), names, args.test_timeout, args.result, shard)
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
    items = plan(work, jobs, timings)
    jobs = min(jobs, len(items))
    cut = {i[0].stem for i in items if i[2]}
    print(f"{len(work)} files" + (f", {len(cut)} of them cut into parts" if cut else "") + f", {len(items)} processes, {jobs} at once")

    passed = failed = skipped = other_system = 0
    failures = []      # (stem, name, message, traceback)
    per_file = {}
    per_test = []
    started = time.time()
    with tempfile.TemporaryDirectory(prefix="woodcore-tests-") as scratch, ThreadPoolExecutor(max_workers=jobs) as pool:
        futures = [pool.submit(run_worker, path, names, shard, args, Path(scratch)) for path, names, shard, _estimate in items]
        for done_count, future in enumerate(as_completed(futures), 1):
            path, names, shard, result, output, seconds = future.result()
            # The worker's own lines, whole and together, once its file is done: files running side by side would otherwise interleave their lines.
            for line in output.splitlines():
                if not line.startswith(f"{DIM}...  ") and not line.startswith("...  "):
                    print(line)
            passed += len(result["passed"])
            skipped += len(result["skipped"])
            other_system += len(result["other_system"])
            failed += len(result["failed"])
            for f in result["failed"]:
                failures.append((path.stem, f["name"], f["message"], f.get("traceback", "")))
                if f.get("process"):
                    print(f"{RED}FAIL{OFF} {path.stem}.{f['name']}: {f['message']}")
            per_file[path.stem] = per_file.get(path.stem, 0.0) + seconds
            per_test.extend((s, f"{path.stem}.{n}") for n, s in result["times"].items())
            timings.update({f"{path.stem}.{n}": round(s, 2) for n, s in result["times"].items()})
            part = f" (part {shard[0] + 1}/{shard[1]})" if shard else ""
            print(f"{DIM}[{done_count}/{len(items)}] {path.stem}{part} {seconds:.1f} s, {time.time() - started:.0f} s since the start{OFF}")

    # keyed by test (a file's own total kept where an older run left one), and only what still exists: a renamed test does not keep its old time forever
    known = {f"{p.stem}.{n}" for p in files for n in _test_names(p)}
    TIMINGS.write_text(json.dumps({k: v for k, v in sorted(timings.items()) if k in known or k in {p.stem for p in files}}, indent=1) + "\n", encoding="utf-8")
    LAST_RUN.write_text(json.dumps({"failed": sorted(f"{s}.{n}" for s, n, _m, _t in failures)}, indent=1) + "\n", encoding="utf-8")

    if args.v and failures:
        print()
        for stem, name, _msg, tb in failures:
            print(f"{DIM}{'-' * 72}{OFF}")
            print(f"{stem}.{name}")
            print(tb)

    elapsed = time.time() - started
    print()
    if failures:
        print("Failed:")
        for stem, name, msg, _tb in failures:
            print(f"  {RED}{stem}.{name}{OFF} -- {msg.splitlines()[0] if msg else ''}")
        print(f"  {DIM}python tests/run_tests.py --failed   reruns these alone{OFF}")
        print()
    summary = f"{passed} passed"
    if skipped:
        summary += f", {skipped} skipped"
    if failed:
        summary += f", {failed} FAILED"
    print(f"{summary} in {elapsed:.1f} s")
    if args.times:
        cpu = sum(per_file.values())
        print()
        print(f"Time per file (import included, its parts added up), slowest first -- {cpu:.0f} s in all, {jobs} at once:")
        for stem, seconds in sorted(per_file.items(), key=lambda item: -item[1]):
            print(f"  {seconds:7.1f} s  {seconds / cpu:5.1%}  {stem}")
        print()
        print("Slowest tests:")
        for seconds, label in sorted(per_test, reverse=True)[:10]:
            print(f"  {seconds:7.1f} s  {label}")
    if left_out:
        print(f"{DIM}tests of time left out (run them with --perf): {', '.join(left_out)}{OFF}")
    if other_system:
        print(f"{DIM}{other_system} tests of another operating system left out (conftest.OtherSystem; the CI runs them there){OFF}")
    full = not (args.k or args.failed or args.related)
    if full and skipped > MAX_SKIPPED:
        print(f"{RED}{skipped} tests skipped, more than the {MAX_SKIPPED} a clone of the code skips -- this run checked less than it seems{OFF}")
    return exit_code(failed, skipped, not full)


if __name__ == "__main__":
    sys.exit(main())
