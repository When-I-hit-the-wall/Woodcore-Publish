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
    for stem in ("test_norms", "test_export", "test_schema", "test_units", "test_dowel", "test_steel_check", "test_snow_source", "test_wind_source", "test_dead_load", "test_runner"):
        assert stem in fast, f"{stem} belongs to the fast tier"
    assert not fast & {p.stem for p in tests.glob("test_*.py") if run_tests.is_perf(p)}, "a test of time is never fast"
    folder = conftest.tmpdir("runner-fast")
    (folder / "test_x.py").write_text('"""Mentions TIER = "fast" in its text only."""\nX = \'TIER = "fast"\'\n', encoding="utf-8")
    assert not run_tests.is_fast(folder / "test_x.py"), "a mention of the marker is not the marker"
    (folder / "test_y.py").write_text('TIER = "fast"  # tests/run_tests.py --fast\n', encoding="utf-8")
    assert run_tests.is_fast(folder / "test_y.py")
