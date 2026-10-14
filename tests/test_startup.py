"""Woodcore's start, timed: the start screen is up within a second and a half (calc/tools/woodcore_start.py; spec docs/requirements/completed/2026-10-07-performance-erreurs-plans-legendes.md, REQ-002).

The engineer, 07.10.2026: «Lorsque l'utilisateur lance woodcore.exe il doit immédiatement obtenir un retour visuel». Measured before (docs/architecture/performance.md): nothing on screen for 4-5 s warm, 30 s cold. Each check runs in a fresh process, since the suite's own has imported everything long ago.

**A test of time, run by `python tests/run_tests.py --perf` only** (v0.117, issue #26): a slow or shared machine -- a CI runner, a cloud session -- must not fail the functional suite. What the start does, rather than how fast, is tests/test_startup_imports.py's, which every run runs.
"""

import subprocess
import sys
import time

from conftest import ROOT
from test_startup_imports import _env

PERF = True  # tests/run_tests.py runs this file with --perf only


def test_the_start_screen_is_up_within_a_second_and_a_half():
    import shutil
    work, env, file = _env()
    env["WOODCORE_START_TRACE"] = "1"
    try:
        timings = []
        for _run in range(2):   # the second is warm, as the engineer's second start of a day is
            begun = time.monotonic()
            done = subprocess.Popen([sys.executable, "-u", str(ROOT / "calc" / "tools" / "woodcore_gui.py"), "--project", str(file), "--self-test"],
                                    env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8")
            shown = None
            output = []
            for line in done.stderr:
                output.append(line)
                if "screen shown" in line and shown is None:
                    shown = time.monotonic() - begun
            assert done.wait(timeout=300) == 0, "".join(output[-30:])
            assert shown is not None, "the start screen never said it was up:\n" + "".join(output[-30:])
            timings.append(shown)
        assert timings[-1] < 1.5, f"the start screen came {timings[-1]:.2f} s after the start (warm), {timings[0]:.2f} s the first time"
    finally:
        shutil.rmtree(work, ignore_errors=True)
