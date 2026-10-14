"""The test harness itself: two runs of the suite at once must not reach into each other's files (docs/conventions/testing.md §11ter).

Until v0.64.2 they did. `conftest.tmpdir(name)` wiped and recreated `tests/.tmp/<name>` at the start of each test, and the path carried nothing to tell one run from another -- so run A removed run B's probe in the middle of a test, and B failed with `file not found (searched at ...\\tests\\.tmp\\formula\\probe.typ)`.

What made it expensive is that it looks exactly like a defect in the code. Two sessions measured it apart from one another -- **20, 21 and 29 failures in a shared run against 0 for the same tests run alone** -- and every one of them was in a suite that writes a `.typ`, none in the nine that do not. A duration tells nothing here and was tried: a run that aborts early is short, and so is a warm one, the second effect being the larger (44/44 in 24 s on a quiet machine against 60 s for the same tests an hour before).

`TMP` carries the process id now, and `command_preview` already did -- which is why `test_commands` was the one suite that never collided. The removing lives in `conftest` alone; the runner had a second copy of the loop, and a second copy is what lets a repair be applied to one and not the other.

⚠️ The one thing a deeper path could have broken is a relative `#import` in a probe, which is what caught `command_preview`. It does not bite here, and the last test below is what keeps saying so.
"""

import os
import re
from pathlib import Path

import conftest
from conftest import ROOT

HERE = Path(__file__).resolve().parent


def test_the_temporary_directory_is_this_processs_own():
    assert conftest.TMP.name == str(os.getpid()), conftest.TMP
    assert conftest.TMP.parent == ROOT / "tests" / ".tmp", conftest.TMP.parent


def test_a_directory_for_one_test_sits_inside_it_and_starts_clean():
    d = conftest.tmpdir("harness_probe")
    assert d.parent == conftest.TMP, d
    (d / "left-over.txt").write_text("x", encoding="utf-8")
    again = conftest.tmpdir("harness_probe")
    assert list(again.iterdir()) == [], "tmpdir did not start clean"


def test_cleanup_leaves_a_neighbours_directory_alone():
    """The whole point. A run that removed `tests/.tmp` entire would take the neighbour with it -- the same fault moved one level up rather than repaired."""
    neighbour = conftest.TMP.parent / f"neighbour-{os.getpid()}"   # a sibling of ours, named after us so two concurrent runs of this very test do not collide
    (neighbour / "formula").mkdir(parents=True, exist_ok=True)
    probe = neighbour / "formula" / "probe.typ"
    probe.write_text("#import \"/commands.typ\": *", encoding="utf-8")
    try:
        conftest.tmpdir("harness_mine")
        conftest.cleanup()
        assert not conftest.TMP.exists(), "this run's own directory survived cleanup"
        assert probe.exists(), "cleanup reached into a neighbour's directory"
        assert probe.read_text(encoding="utf-8").startswith("#import"), "the neighbour's file was truncated"
    finally:
        conftest._wipe(neighbour)


def test_cleanup_is_idempotent_and_survives_an_empty_parent():
    """The runner calls it before printing its summary and `atexit` calls it again; under pytest only `atexit` does. None of the three may raise."""
    conftest.cleanup()
    conftest.cleanup()
    conftest.tmpdir("harness_again")
    conftest.cleanup()
    assert not conftest.TMP.exists()


def test_the_runner_keeps_no_copy_of_the_removing():
    """`run_tests.py` carried its own `rglob`/`rmdir` loop over `conftest.TMP`. One place, or the next repair lands on one of the two."""
    source = (HERE / "run_tests.py").read_text(encoding="utf-8")
    assert "conftest.cleanup()" in source, "the runner no longer asks conftest to clean up"
    assert "rglob" not in source, "the runner has a second copy of the removing again"


def test_a_probe_imports_by_a_path_its_depth_cannot_break():
    """Putting the process id in the path moved every probe one directory deeper, and Typst resolves a relative `#import` from the importing file -- so a literal `"../.."` in a probe would have broken the moment the repair was applied, with the very message the repair exists to remove.

    Each `#import` a test writes is therefore absolute, read from the Typst root, or built from a prefix computed at run time. Neither form can be broken by depth; a literal `..` can.
    """
    # test_typst_paths.py writes relative literals on purpose: they are what it rewrites, inside a tree it builds itself, where each one's depth is the tree's own and not the temporary folder's.
    exempt = {"test_typst_paths.py"}
    # A line may say the same of itself, with this comment: a report-shaped template's own relative import that a test holds the creation of a project to rewrite, or a file written to be refused and never compiled.
    marker = "relative on purpose"
    written = []
    for path in sorted(HERE.glob("test_*.py")) + [HERE / "conftest.py"]:
        if path.name in exempt:
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            if marker in line and path.name != "test_harness.py":
                continue
            for target in re.findall(r'#import\s+"([^"]*)"', line):
                written.append((path.name, target))
    assert written, "no #import found in the folder at all -- has the scan stopped matching?"
    for name, target in written:
        computed = "{" in target                     # an f-string filling in a prefix of its own
        absolute = target.startswith("/")            # resolved from the Typst root, whatever the depth
        assert computed or absolute, f"{name} writes a depth-dependent import: {target!r}"


def test_k_selects_a_test_by_its_function_name_alone():
    """`run_tests.py -k <name>` runs that test even when the name of its file does not contain the pattern.

    The runner skipped every file whose stem lacked the pattern before looking at the names inside it, so `-k test_cleanup_is_idempotent_and_survives_an_empty_parent` ran nothing and printed "0 passed" -- the very command the audit prompt tells one to rerun a single failure with (periodic audit 260916, AUD-1-4).
    """
    import subprocess
    import sys
    run = subprocess.run([sys.executable, "-u", str(HERE / "run_tests.py"), "-k", "test_cleanup_is_idempotent_and_survives_an_empty_parent"],
                         capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=str(ROOT), timeout=120)
    assert "1 passed" in run.stdout, run.stdout[-600:] + run.stderr[-600:]


def test_skip_is_a_skip_for_pytest_as_well():
    """`Skip` must be a skip under pytest too, which docs/conventions/testing.md §11ter says discovers these files unchanged: a plain `Exception` is an error there (periodic audit 260916, AUD-7-412)."""
    import unittest
    assert issubclass(conftest.Skip, unittest.SkipTest), conftest.Skip.__mro__


def test_every_python_file_compiles_without_a_warning():
    """No `SyntaxWarning` anywhere in calc/ or tests/: an invalid escape sequence is a warning today and an error in a later Python. `tests/test_formula.py` wrote Typst's escaped division in a plain f-string and printed the warning on every import (periodic audit 260916, AUD-6-18)."""
    import warnings
    bad = []
    for path in sorted((ROOT / "calc").rglob("*.py")) + sorted(HERE.rglob("*.py")):
        # tests/.tmp, and every run's copy of the example project (tests/.project-<pid>): not this repository's code, and another run's copy vanishes under the walk when its process ends (issue #22)
        if any(part.startswith(".") for part in path.relative_to(ROOT).parts):
            continue
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            try:
                compile(path.read_text(encoding="utf-8"), str(path), "exec")
            except SyntaxError as exc:
                bad.append(f"{path.relative_to(ROOT)}: {exc}")
    assert not bad, "\n  ".join(["files that do not compile cleanly:"] + bad)


def _runner():
    import importlib.util
    spec = importlib.util.spec_from_file_location("run_tests_under_test", HERE / "run_tests.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_a_stuck_test_is_stopped_named_and_the_rest_of_its_file_still_runs():
    """Issue #22: one test waiting on something that never came kept the whole suite running all night, saying nothing. The runner now stops a test after `--test-timeout` seconds (faulthandler writes every thread's stack first), counts it as failed under its own name, and runs the tests after it in a new process -- planted here: a test that sleeps an hour between two that pass."""
    import argparse
    runner = _runner()
    d = conftest.tmpdir("harness_stuck")
    planted = d / "test_planted_stuck.py"
    planted.write_text("import time\n\ndef test_a():\n    assert True\n\ndef test_b_sleeps():\n    time.sleep(3600)\n\ndef test_c():\n    assert True\n", encoding="utf-8")
    args = argparse.Namespace(test_timeout=3)
    _path, _names, _shard, result, output, seconds = runner.run_worker(planted, None, None, args, d)
    assert sorted(result["passed"]) == ["test_a", "test_c"], (result, output[-1500:])
    stuck = [f for f in result["failed"] if f["name"] == "test_b_sleeps"]
    assert stuck and stuck[0]["message"].startswith("stopped after 3 s"), result["failed"]
    assert "test_b_sleeps" in stuck[0]["traceback"], "the stack names the stuck test"
    assert seconds < 60, f"the stuck test held the file {seconds:.0f} s"


def test_failed_and_related_select_only_what_they_name():
    """Issue #23's repair loop reruns only what failed and what the repair touched: `--failed` takes the previous run's failures test by test, `--related` the test files naming a changed module, and both narrow nothing else."""
    import argparse
    import json
    runner = _runner()
    files = sorted(HERE.glob("test_*.py"))
    saved = runner.LAST_RUN.read_bytes() if runner.LAST_RUN.exists() else None
    try:
        runner.LAST_RUN.write_text(json.dumps({"failed": ["test_harness.test_skip_is_a_skip_for_pytest_as_well"]}), encoding="utf-8")
        failed = runner.select(argparse.Namespace(failed=True, related=None, k=""), files)
        assert [(p.stem, n) for p, n in failed] == [("test_harness", {"test_skip_is_a_skip_for_pytest_as_well"})], failed
        related = runner.select(argparse.Namespace(failed=False, related=["calc/renumbering.py"], k=""), files)
        stems = {p.stem for p, _n in related}
        assert "test_renumbering" in stems, stems
        assert "test_harness" in stems, "the previous run's failure is rerun with the related files"
        assert len(stems) < len(files) / 2, f"--related took {len(stems)} of {len(files)} files"
    finally:
        if saved is None:
            runner.LAST_RUN.unlink(missing_ok=True)
        else:
            runner.LAST_RUN.write_bytes(saved)


def test_a_long_file_is_cut_into_parts_that_share_its_tests_between_them():
    """Issue #22: `test_fire_tab` alone took 24 minutes of a 25-minute run. A file whose tests took longer than `SHARD_S` in the previous run is cut into parts, one process each, its tests dealt the longest first to the least loaded part -- every test in exactly one part, and the parts within a test of each other."""
    runner = _runner()
    path = HERE / "test_harness.py"
    names = runner._test_names(path)
    timings = {f"test_harness.{n}": float(runner.SHARD_S) for n in names}
    items = runner.plan([(path, None)], 4, timings)
    assert len(items) == 4 and all(shard is not None for _p, _n, shard, _e in items), items
    saved = runner.TIMINGS.read_bytes() if runner.TIMINGS.exists() else None
    try:
        import json
        runner.TIMINGS.write_text(json.dumps(timings), encoding="utf-8")
        parts = [runner._shard(names, i, 4, "test_harness") for i in range(4)]
    finally:
        if saved is None:
            runner.TIMINGS.unlink(missing_ok=True)
        else:
            runner.TIMINGS.write_bytes(saved)
    assert sorted(n for part in parts for n in part) == sorted(names), "every test in exactly one part"
    sizes = sorted(len(part) for part in parts)
    assert sizes[-1] - sizes[0] <= 1, sizes
    short = runner.plan([(path, None)], 4, {})
    assert len(short) == 1 and short[0][2] is None, "a short file stays whole"
