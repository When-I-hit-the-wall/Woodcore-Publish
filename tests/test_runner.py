"""tests/run_tests.py's own rules: what makes a run red, and the tests of time kept apart (docs/conventions/testing.md §11ter; spec docs/requirements/completed/2026-10-10-audit-issues-26-a-33.md, REQ-26-04, REQ-27-01; issue #26).

A CI job reads nothing but the runner's exit code, so the code is the contract: 1 for a failure, 1 for a full run that skipped more than MAX_SKIPPED -- a run that checked less than it seems --, 0 otherwise.
"""

TIER = "fast"  # tests/run_tests.py --fast

import conftest
from conftest import ROOT

import run_tests


def test_a_failure_or_too_many_skips_in_a_full_run_is_red():
    ceiling = run_tests.MAX_SKIPPED
    assert run_tests.exit_code(failed=0, skipped=0, filtered=False) == 0
    assert run_tests.exit_code(failed=0, skipped=ceiling, filtered=False) == 0
    assert run_tests.exit_code(failed=0, skipped=ceiling + 1, filtered=False) == 1, "a full run that skipped more than the ceiling passed"
    assert run_tests.exit_code(failed=0, skipped=ceiling + 1, filtered=True) == 0, "a run filtered by -k skips what it does not select"
    assert run_tests.exit_code(failed=1, skipped=0, filtered=False) == 1
    assert run_tests.exit_code(failed=1, skipped=0, filtered=True) == 1


def test_a_test_of_another_system_is_counted_apart_from_the_skips():
    """`conftest.OtherSystem`: a test of Windows' own behaviour on Linux is neither a pass nor a skip -- it says nothing missing from this machine, and MAX_SKIPPED counts only what is. Run as the runner runs a file, in a worker process of its own (tests/test_harness.py holds the rest of the workers' rules)."""
    import argparse
    folder = conftest.tmpdir("runner-system")
    probe = folder / "test_probe_system.py"
    probe.write_text("import conftest\n\ndef test_a():\n    raise conftest.OtherSystem('not this system')\n\ndef test_b():\n    raise conftest.Skip('not here')\n\ndef test_c():\n    pass\n", encoding="utf-8")
    scratch = conftest.tmpdir("runner-system-scratch")
    _path, _names, _shard, result, output, _seconds = run_tests.run_worker(probe, None, None, argparse.Namespace(test_timeout=120), scratch)
    assert [s["name"] for s in result["other_system"]] == ["test_a"], (result, output)
    assert [s["name"] for s in result["skipped"]] == ["test_b"] and result["passed"] == ["test_c"] and not result["failed"], (result, output)


def test_the_tests_of_time_are_left_out_unless_asked_for():
    assert run_tests.is_perf(ROOT / "tests" / "test_startup.py"), "the start screen's timing is a test of time"
    assert not run_tests.is_perf(ROOT / "tests" / "test_startup_imports.py"), "what the start loads is functional and runs every time"
    perf = sorted(p.stem for p in (ROOT / "tests").glob("test_*.py") if run_tests.is_perf(p))
    assert perf == ["test_startup"], perf
    folder = conftest.tmpdir("runner-perf")
    (folder / "test_x.py").write_text('"""A file that mentions PERF = True in its text only."""\nX = "PERF = True"\n', encoding="utf-8")
    assert not run_tests.is_perf(folder / "test_x.py"), "a mention of the marker is not the marker"
    (folder / "test_y.py").write_text("PERF = True  # a test of time\n", encoding="utf-8")
    assert run_tests.is_perf(folder / "test_y.py")


def test_the_fast_tier_is_the_files_that_say_so_and_holds_the_engine_the_norms_and_the_export():
    """REQ-005 (spec 2026-10-19-base-saine-nettoyage): `--fast` runs the files that set `TIER = "fast"`, read off their text as `PERF` is. It must keep what a commit most needs checked -- the engine's contracts, the norms, the export -- and stay out of the tests of time."""
    tests = ROOT / "tests"
    fast = {p.stem for p in tests.glob("test_*.py") if run_tests.is_fast(p)}
    for stem in ("test_norms", "test_export", "test_schema", "test_units", "test_dowel", "test_steel_check", "test_snow_source", "test_wind_source", "test_dead_load_source", "test_runner"):
        assert stem in fast, f"{stem} belongs to the fast tier"
    assert not fast & {p.stem for p in tests.glob("test_*.py") if run_tests.is_perf(p)}, "a test of time is never fast"
    folder = conftest.tmpdir("runner-fast")
    (folder / "test_x.py").write_text('"""Mentions TIER = "fast" in its text only."""\nX = \'TIER = "fast"\'\n', encoding="utf-8")
    assert not run_tests.is_fast(folder / "test_x.py"), "a mention of the marker is not the marker"
    (folder / "test_y.py").write_text('TIER = "fast"  # tests/run_tests.py --fast\n', encoding="utf-8")
    assert run_tests.is_fast(folder / "test_y.py")


# --- issue #108: the parent holds each test's limit, limits drawn from measured times, a ceiling for the suite ---------------
# spec docs/requirements/completed/2026-10-24-lanceur-tests-limites.md. The planted tests below write fake test files into a temporary folder and run the runner's own workers on them, with limits of seconds -- the grace, the floor and the wait for a killed process lowered through the run's knobs (`run_tests._knob`), so that the whole file stays short.

def _planted(folder, name, text):
    path = folder / f"{name}.py"
    path.write_text(text, encoding="utf-8")
    return path


def _quick(**knobs):
    """The run's settings for a planted test: limits of seconds, no measured times unless given."""
    import argparse
    values = dict(test_timeout=2, grace=2, abandon_wait=2, limit_floor=2, timings={})
    values.update(knobs)
    return argparse.Namespace(**values)


def test_a_test_s_limit_is_ten_times_its_measured_time_between_the_floor_and_the_ceiling():
    """REQ-003 (D-4): `min(--test-timeout, max(30 s, 10 x the measured time))`; the ceiling for a test never measured; the origin said."""
    timings = {"test_x.test_short": 0.2, "test_x.test_mid": 4.37, "test_x.test_long": 40.0, "test_x.test_zero": 0.0}
    assert run_tests.LIMIT_K == 10 and run_tests.LIMIT_FLOOR_S == 30 and run_tests.TEST_TIMEOUT_S == 300 and run_tests.GRACE_S == 30
    seconds, origin = run_tests.test_limit(timings, "test_x.test_short", 300)
    assert seconds == 30 and "10 x 0.2 s measured" in origin and "floor" in origin, (seconds, origin)
    assert run_tests.test_limit(timings, "test_x.test_zero", 300)[0] == 30, "a test measured at 0 s is measured, and gets the floor"
    seconds, origin = run_tests.test_limit(timings, "test_x.test_mid", 300)
    assert seconds == 44 and origin == "10 x 4.37 s measured", (seconds, origin)
    seconds, origin = run_tests.test_limit(timings, "test_x.test_long", 300)
    assert seconds == 300 and "ceiling" in origin, (seconds, origin)
    assert run_tests.test_limit(timings, "test_x.test_long", 1000)[0] == 400, "min(ceiling, 10 x 40 s)"
    seconds, origin = run_tests.test_limit(timings, "test_x.test_new", 300)
    assert seconds == 300 and "never measured" in origin, (seconds, origin)


def test_the_watch_follows_the_worker_s_lines_cut_anywhere_and_bounds_the_silence_outside_a_test():
    """ARCH-002, ARCH-005, REQ-005: `_Watch` reads the announcement and the end of each test from chunks cut anywhere; `stop_reason` stops a test past its limit and the grace, a process silent outside any test past FILE_MARGIN_S -- its import or its exit --, and never a file for its number of tests."""
    lines = ["...  test_p.test_a\n", "ok   test_p.test_a\n", "...  test_p.test_b\n", "FAIL test_p.test_b\n", "       boom\n", "...  test_p.test_c\n"]
    whole = run_tests._Watch("test_p", 0.0)
    for line in lines:
        whole.feed(line, 1.0)
    text = "".join(lines)
    cut = run_tests._Watch("test_p", 0.0)
    for i in range(0, len(text), 7):
        cut.feed(text[i:i + 7], 1.0)
    assert whole.state() == cut.state() == ("test_c", 1.0, 1.0), (whole.state(), cut.state())
    assert run_tests._Watch("test_p", 0.0).feed("...  test_p.test_a", 1.0)[0] is None, "a line is not read before its end"
    coloured = run_tests._Watch("test_p", 0.0)
    coloured.feed("\033[2m...  test_p.test_a\033[0m\n", 1.0)
    assert coloured.current == "test_a"
    coloured.feed("\033[33mSKIP\033[0m test_p.test_a \033[2m-- no workbook\033[0m\n", 2.0)
    assert coloured.state() == (None, 1.0, 2.0)
    # seventeen tests one after the other, ten minutes in all: never a limit of the file
    many = run_tests._Watch("test_p", 0.0)
    for i in range(17):
        many.feed(f"...  test_p.test_{i:02d}\n", i * 40.0)
        assert run_tests.stop_reason(many.state(), i * 40.0 + 39.0, 30, 300, 30) is None
        many.feed(f"ok   test_p.test_{i:02d}\n", i * 40.0 + 39.0)
    # a test running: only its own limit and the grace
    assert run_tests.stop_reason(("test_a", 100.0, 100.0), 100.0 + 59.0, 30, 300, 30) is None
    assert run_tests.stop_reason(("test_a", 100.0, 100.0), 100.0 + 61.0, 30, 300, 30)[0] == "limit"
    assert run_tests.stop_reason(("test_a", 100.0, 100.0), 100.0 + 320.0, 300, 300, 30) is None, "a test within its limit is no silence"
    # no test running: its import, or after its last test
    assert run_tests.stop_reason((None, 0.0, 0.0), 299.0, 300, 300, 30) is None
    assert run_tests.stop_reason((None, 0.0, 0.0), 301.0, 300, 300, 30)[0] == "silence", "an import silent past FILE_MARGIN_S"
    assert run_tests.stop_reason((None, 5.0, 680.0), 981.0, 300, 300, 30)[0] == "silence", "an exit that never returns"


def test_a_stopped_test_keeps_its_last_good_time_and_the_last_run_keeps_only_what_failed():
    """REQ-004: tests/.timings.json the one source of the times -- a test failed or stopped keeps the time of its last good run; tests/.last-run.json stays {"failed": [...]}."""
    timings = {"test_p.test_a": 1.5, "test_p.test_b": 0.8, "test_p.test_c": 2.0, "test_q.test_z": 9.0}
    result = {"passed": ["test_a"], "failed": [{"name": "test_b", "message": "stopped after 30 s"}], "skipped": [{"name": "test_d", "message": "-"}], "other_system": [],
              "times": {"test_a": 1.234, "test_b": 31.0, "test_d": 0.01}}
    merged = run_tests.merge_timings(timings, result, "test_p")
    assert merged == {"test_p.test_a": 1.23, "test_p.test_b": 0.8, "test_p.test_c": 2.0, "test_p.test_d": 0.01, "test_q.test_z": 9.0}, merged
    assert timings["test_p.test_a"] == 1.5, "a new dict, the given one untouched"
    assert run_tests.last_run([("test_p", "test_b", "stopped", "tb"), ("test_p", "test_b", "again", "tb")]) == {"failed": ["test_p.test_b"]}


def test_an_endless_loop_whose_exit_hangs_is_stopped_by_the_parent_within_its_limit_and_the_grace():
    """REQ-001, REQ-009 (a), UI-001: a test that never returns, its worker's own watchdog out of the way -- as when `faulthandler`'s `_exit` hangs under Windows (issue #108) -- is stopped by the parent, counted red under its name, in one `FAIL` line naming its file; the test after it still runs; and a test whose limit already was the ceiling is not replayed (REQ-010)."""
    import time
    folder = conftest.tmpdir("runner-loop")
    probe = _planted(folder, "test_probe_loop", "import faulthandler\n\ndef test_loops():\n    faulthandler.cancel_dump_traceback_later()  # as if its _exit hung: only the parent can stop it now\n    while True:\n        pass\n\ndef test_z_after():\n    pass\n")
    started = time.monotonic()
    _p, _n, _s, result, output, _seconds = run_tests.run_worker(probe, None, None, _quick(), folder)
    took = time.monotonic() - started
    stopped = [f for f in result["failed"] if f["name"] == "test_loops"]
    assert stopped and stopped[0]["message"].startswith("stopped after 2 s -- limit = never measured"), (result["failed"], output[-1500:])
    assert "process tree killed by the runner at" in stopped[0]["message"], stopped[0]["message"]
    assert result["passed"] == ["test_z_after"], (result, output[-1500:])
    assert took < 2 + 30, f"stopped after {took:.0f} s, past its limit and 30 s"
    assert took < 2 + 2 + 2 + 15, f"{took:.0f} s: the limit, the grace, a wait and two processes' start"
    fails = [line for line in run_tests.report_lines("test_probe_loop", result, output) if line.startswith("FAIL")]
    assert len(fails) == 1 and fails[0].startswith("FAIL test_probe_loop.test_loops: stopped after 2 s"), fails
    assert "replayed alone" not in output and not result["flaky"], "a test stopped at the ceiling is not replayed"


def test_a_modal_exec_that_never_ends_is_stopped_by_the_parent():
    """REQ-009 (b): the frame of the issue -- a Qt loop's `exec()` that nothing quits, its worker's own watchdog out of the way -- stopped by the parent within its limit and the grace."""
    import importlib.util
    import time
    if importlib.util.find_spec("PySide6") is None:
        raise conftest.Skip("PySide6 is not installed")
    folder = conftest.tmpdir("runner-modal")
    probe = _planted(folder, "test_probe_modal", "import faulthandler\n\ndef test_modal():\n    from PySide6.QtCore import QCoreApplication, QEventLoop\n    app = QCoreApplication.instance() or QCoreApplication([])\n    faulthandler.cancel_dump_traceback_later()\n    QEventLoop().exec()\n")
    started = time.monotonic()
    _p, _n, _s, result, output, _seconds = run_tests.run_worker(probe, None, None, _quick(test_timeout=3), folder)
    took = time.monotonic() - started
    stopped = [f for f in result["failed"] if f["name"] == "test_modal"]
    assert stopped and stopped[0]["message"].startswith("stopped after 3 s"), (result["failed"], output[-1500:])
    assert took < 3 + 30 and took < 3 + 2 + 2 + 15, f"stopped after {took:.0f} s"


def test_a_process_that_will_not_die_is_abandoned_and_never_waited_for():
    """REQ-002, REQ-009 (c), ARCH-003: the kill has no effect -- as `taskkill` on a worker stuck in its exit in the kernel (issue #108's PID 11516) --, so the process stays alive; the parent waits the bounded few seconds, abandons it, counts the test red with its PID, returns, and the runner's temporary folder is cleaned without an error while the process still holds its output."""
    import os
    import shutil
    import signal
    import tempfile
    import time
    from pathlib import Path
    folder = conftest.tmpdir("runner-abandon")
    probe = _planted(folder, "test_probe_undying", "import faulthandler\nimport time\n\ndef test_undying():\n    faulthandler.cancel_dump_traceback_later()\n    time.sleep(3600)\n")
    real_kill = run_tests._kill_tree
    run_tests._kill_tree = lambda proc: None
    scratch = tempfile.TemporaryDirectory(prefix="woodcore-runner-probe-", ignore_cleanup_errors=True)
    pid = None
    try:
        started = time.monotonic()
        _p, _n, _s, result, output, _seconds = run_tests.run_worker(probe, None, None, _quick(), Path(scratch.name))
        took = time.monotonic() - started
        stopped = [f for f in result["failed"] if f["name"] == "test_undying"]
        assert stopped, (result, output[-1500:])
        pid = stopped[0]["stop"]["pid"]
        assert stopped[0]["stop"]["abandoned"] and f"process not ended (PID {pid}), abandoned" in stopped[0]["message"], stopped[0]["message"]
        assert took < 2 + 2 + 2 + 15, f"the parent held {took:.0f} s for a process that would not die"
        assert run_tests.exit_code(len(result["failed"]), 0, True) == 1
        scratch.cleanup()  # the process is still alive and holds its output: no exception
    finally:
        run_tests._kill_tree = real_kill
        if pid:
            try:
                os.kill(pid, signal.SIGTERM)
            except OSError:
                pass
        shutil.rmtree(scratch.name, ignore_errors=True)


def test_the_worker_s_own_watchdog_fires_at_the_measured_limit_and_a_flaky_test_passes_when_replayed():
    """ARCH-001, ARCH-004, REQ-010: the worker reads its limits from the parent (`--limits`): a test measured at 0.1 s with a floor of 2 s is stopped at 2 s by its own `faulthandler`, which writes the stack, before the parent's grace -- the parent kills nothing. Stopped by a limit tighter than the ceiling, it is replayed once alone at the ceiling; passing then, it counts as passed and is reported flaky."""
    import time
    folder = conftest.tmpdir("runner-flaky")
    marker = folder / "first-time"
    probe = _planted(folder, "test_probe_flaky", f"import time\nfrom pathlib import Path\n\ndef test_sleeps_once():\n    marker = Path({str(marker)!r})\n    if not marker.exists():\n        marker.write_text('slept')\n        time.sleep(3600)\n")
    kills = []
    real_kill = run_tests._kill_tree
    run_tests._kill_tree = lambda proc: (kills.append(proc.pid), real_kill(proc))
    try:
        started = time.monotonic()
        _p, _n, _s, result, output, _seconds = run_tests.run_worker(probe, None, None, _quick(test_timeout=20, grace=20, timings={"test_probe_flaky.test_sleeps_once": 0.1}), folder)
        took = time.monotonic() - started
    finally:
        run_tests._kill_tree = real_kill
    assert "Timeout (0:00:02)!" in output and "test_sleeps_once" in output, output[-1500:]
    assert not kills, "the worker's own watchdog fired first: the parent killed nothing"
    assert result["passed"] == ["test_sleeps_once"] and not result["failed"], (result, output[-1500:])
    assert [f["name"] for f in result["flaky"]] == ["test_sleeps_once"], result["flaky"]
    assert "stopped after 2 s -- limit = 10 x 0.1 s measured, raised to the floor of 2 s" in result["flaky"][0]["message"], result["flaky"]
    assert any(line.startswith("FLAKY test_probe_flaky.test_sleeps_once") for line in run_tests.report_lines("test_probe_flaky", result, output))
    assert took < 20, f"{took:.0f} s: the parent waited for its grace"


def test_a_test_stopped_twice_is_red_with_both_limits():
    """REQ-010: a test that sleeps every time -- stopped at its measured limit, then again when replayed at the ceiling -- is red, the message naming both attempts."""
    folder = conftest.tmpdir("runner-twice")
    probe = _planted(folder, "test_probe_twice", "import time\n\ndef test_sleeps():\n    time.sleep(3600)\n")
    _p, _n, _s, result, output, _seconds = run_tests.run_worker(probe, None, None, _quick(test_timeout=4, timings={"test_probe_twice.test_sleeps": 0.1}), folder)
    assert not result["passed"] and not result["flaky"], (result, output[-1500:])
    [stopped] = [f for f in result["failed"] if f["name"] == "test_sleeps"]
    assert stopped["message"].startswith("stopped after 4 s -- limit = a replay alone"), stopped["message"]
    assert "a first attempt stopped after 2 s -- limit = 10 x 0.1 s measured" in stopped["message"], stopped["message"]


def test_the_suite_stops_at_its_ceiling_names_what_runs_and_starts_nothing_more():
    """REQ-006, REQ-009 (d), ARCH-006: `execute` with a deadline of 5 s, one process at a time, a first file whose test sleeps ten minutes and a second one: it returns within the deadline and the bounded waits, the sleeping test red and named, the second file not started, the stopped test in what `--failed` reruns."""
    import time
    folder = conftest.tmpdir("runner-ceiling")
    slow = _planted(folder, "test_probe_slow", "import time\n\ndef test_sleeps_ten_minutes():\n    time.sleep(600)\n")
    never = _planted(folder, "test_probe_never", "def test_a():\n    pass\n")
    items = [(slow, None, None, 600.0), (never, None, None, 1.0)]
    started = time.monotonic()
    finished, not_started, hung = run_tests.execute(items, 1, _quick(test_timeout=300), folder, deadline=started + 5)
    took = time.monotonic() - started
    assert took < 5 + 2 + 10, f"the suite ran {took:.0f} s past a ceiling of 5 s"
    assert not hung and [p.stem for p, _n, _s in not_started] == ["test_probe_never"], (not_started, hung)
    [(path, _names, _shard, result, output, _seconds)] = finished
    [stopped] = result["failed"]
    assert stopped["name"] == "test_sleeps_ten_minutes" and stopped["stop"]["kind"] == "deadline", stopped
    assert stopped["message"].startswith("still running at the suite's deadline"), stopped["message"]
    fails = [line for line in run_tests.report_lines(path.stem, result, output) if line.startswith("FAIL")]
    assert len(fails) == 1 and "test_probe_slow.test_sleeps_ten_minutes" in fails[0], fails
    assert run_tests.last_run([(path.stem, stopped["name"], stopped["message"], "")]) == {"failed": ["test_probe_slow.test_sleeps_ten_minutes"]}


def test_the_runner_waits_for_nothing_without_a_limit_and_offers_one_option_more():
    """REQ-002, ARCH-006, ARCH-RISK-007: no wait in tests/run_tests.py without its `timeout=` -- `taskkill` is a wait too --; `--help` offers `--suite-timeout` and keeps `--limits` hidden, as `--result` is."""
    import re
    import subprocess
    import sys
    source = (ROOT / "tests" / "run_tests.py").read_text(encoding="utf-8")
    calls = [line.strip() for line in source.splitlines() if re.search(r"\.wait\(|\bwait_for\(|subprocess\.run\(", line.split("#")[0])]
    assert calls, "the waits of the runner were found"
    unbounded = [line for line in calls if "timeout=" not in line]
    assert not unbounded, unbounded
    shown = subprocess.run([sys.executable, str(ROOT / "tests" / "run_tests.py"), "--help"], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60).stdout
    assert "--suite-timeout" in shown and "--test-timeout" in shown, shown
    assert "--limits" not in shown and "--result" not in shown and "--worker" not in shown, shown


def test_a_test_is_replayed_only_when_stopped_by_a_tighter_limit_its_process_ended_and_the_suite_not_past_its_deadline():
    """REQ-010 (D-6): no replay at the ceiling, after an abandon, for what did not stop on a limit, or past the suite's deadline."""
    import time
    stopped = {"name": "test_a", "kind": "limit", "limit": 30, "abandoned": False}
    assert run_tests._replayable(stopped, 300, None)
    assert run_tests._replayable(stopped, 300, time.monotonic() + 60)
    assert not run_tests._replayable(dict(stopped, limit=300), 300, None), "at the ceiling the replay would be the same run"
    assert not run_tests._replayable(dict(stopped, abandoned=True), 300, None), "an abandoned process may still hold what the test uses"
    assert not run_tests._replayable(dict(stopped, kind="crash"), 300, None) and not run_tests._replayable(dict(stopped, kind="deadline"), 300, None)
    assert not run_tests._replayable(dict(stopped, name="<process>"), 300, None)
    assert not run_tests._replayable(stopped, 300, time.monotonic() - 1), "past the suite's deadline"
    assert not run_tests._replayable(None, 300, None)


def test_a_full_run_past_its_ceiling_is_red_lists_what_ran_and_keeps_the_stopped_test_for_failed():
    """REQ-006, REQ-007, end to end through `main`, on a folder of planted files in place of tests/ (the module's own paths pointed at it for the call): `--suite-timeout 4`, a file whose test sleeps ten minutes beside one that passes. Exit 1, the sleeping test listed as still running at the deadline and failed, `.last-run.json` holding it alone, `.timings.json` the passing test's time, and `--times` the tightest limits."""
    import contextlib
    import io
    import json
    import sys
    import time
    folder = conftest.tmpdir("runner-main")
    _planted(folder, "test_probe_main_slow", "import time\n\ndef test_sleeps():\n    time.sleep(600)\n")
    _planted(folder, "test_probe_main_fine", "def test_fine():\n    pass\n")
    saved = run_tests.HERE, run_tests.TIMINGS, run_tests.LAST_RUN, sys.argv
    run_tests.HERE, run_tests.TIMINGS, run_tests.LAST_RUN = folder, folder / ".timings.json", folder / ".last-run.json"
    sys.argv = ["run_tests.py", "--suite-timeout", "4", "-j", "2", "--times"]
    printed = io.StringIO()
    try:
        started = time.monotonic()
        with contextlib.redirect_stdout(printed):
            code = run_tests.main()
        took = time.monotonic() - started
    finally:
        run_tests.HERE, run_tests.TIMINGS, run_tests.LAST_RUN, sys.argv = saved
    text = printed.getvalue()
    assert code == 1, text
    assert took < 4 + run_tests.KILL_WAIT_S + run_tests.ABANDON_WAIT_S, f"{took:.0f} s for a ceiling of 4 s"
    assert "reached its ceiling of 4 s" in text and "Still running at the deadline:" in text and "test_probe_main_slow.test_sleeps -- for" in text, text
    assert text.count("FAIL test_probe_main_slow.test_sleeps:") == 1, text
    assert json.loads((folder / ".last-run.json").read_text(encoding="utf-8")) == {"failed": ["test_probe_main_slow.test_sleeps"]}
    timings = json.loads((folder / ".timings.json").read_text(encoding="utf-8"))
    assert "test_probe_main_fine.test_fine" in timings and "test_probe_main_slow.test_sleeps" not in timings, timings
    assert "Tightest limits" in text and "test_probe_main_fine.test_fine" in text.split("Tightest limits", 1)[1], text
