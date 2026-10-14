"""Woodcore's start, timed phase by phase (spec docs/requirements/completed/2026-10-07-performance-erreurs-plans-legendes.md, REQ-001).

Not a test -- its name keeps run_tests.py from collecting it: it measures, it does not judge, and what it prints goes into docs/architecture/performance.md, before a change and after it. Each run is a fresh process, since a module imported once is never imported again in the same one: the first run of a session is the coldest the disk cache allows, the next ones warm.

    python tests/perf_startup.py [--runs 3] [--json out.json]

Phases of the window's start, in the order main() runs them: the interpreter itself, PySide6, QApplication, woodcore_gui's own imports, opening the project (lock, seed, the window built tab by tab), show(), then rebuild() -- what a language switch and the end of every export run again. Then the export a window starts (calc/cli.py export --data-only), timed as a whole and by its imports.

It works on a copy of tests/projet-exemple in the system's temp folder and on settings of its own, so it writes neither into the committed example nor into the engineer's settings.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "tests" / "projet-exemple" / "Exemple.woodcore"


def _child(started):
    """One start of the window, offscreen; prints the phases as JSON on the last line of standard output."""
    phases = [("interpreter", time.time() - started)]
    mark = time.perf_counter()

    def lap(name):
        nonlocal mark
        now = time.perf_counter()
        phases.append((name, now - mark))
        mark = now

    from PySide6.QtWidgets import QApplication  # noqa: F401
    import PySide6.QtGui  # noqa: F401
    lap("PySide6")
    app = QApplication([sys.argv[0]])
    lap("QApplication")
    for path in (ROOT / "calc" / "tools", ROOT / "calc", ROOT):
        sys.path.insert(0, str(path))
    import woodcore_gui
    lap("import woodcore_gui")
    tabs = []

    def timed(key, factory):
        def build(window):
            begun = time.perf_counter()
            tab = factory(window)
            tabs.append((key, time.perf_counter() - begun))
            return tab
        return build
    woodcore_gui.TABS = tuple((key, timed(key, factory)) for key, factory in woodcore_gui.TABS)
    window = woodcore_gui.open_project(app, os.environ["WOODCORE_PROJECT"], quiet=True)
    lap("open_project (window built)")
    if window is None:
        raise SystemExit("the project did not open")
    app.processEvents()
    lap("first events")
    first_build = list(tabs)
    tabs.clear()
    window.rebuild()
    lap("rebuild()")
    print(json.dumps({"phases": phases, "tabs": first_build, "rebuild_tabs": tabs}))
    window.close()


def _copy_project():
    """The example, copied where nothing committed is touched, its engine synced as conftest does."""
    work = Path(tempfile.mkdtemp(prefix="woodcore-perf-"))
    target = work / SAMPLE.parent.name
    shutil.copytree(SAMPLE.parent, target, ignore=shutil.ignore_patterns("lib", "VERSION", "stamps", "_Archiv"))
    sys.path.insert(0, str(ROOT / "calc"))
    import project
    with project.using(target / SAMPLE.name) as copied:   # the process's own project put back after: test_startup and test_no_console call this inside the suite,
        project.sync_engine(copied)                       # where a `use()` left behind sent every later test to a folder deleted since
    return work, target / SAMPLE.name


def _environment(work, file):
    env = dict(os.environ)
    env.update({
        "QT_QPA_PLATFORM": "offscreen",
        "WOODCORE_SETTINGS": str(work / "settings.json"),
        "WOODCORE_TYPST_CHECK": "0",
        "WOODCORE_VARIABLES_READ": "0",
        "WOODCORE_PROJECT": str(file),
        "PYTHONIOENCODING": "utf-8",
    })
    # Windows' fonts for the offscreen platform, which looks for them in Qt's own folder otherwise; elsewhere fontconfig finds the system's (v0.117: the folder named here on Linux held nothing)
    if sys.platform == "win32" and not env.get("QT_QPA_FONTDIR"):
        env["QT_QPA_FONTDIR"] = str(Path(env.get("WINDIR", "C:/Windows")) / "Fonts")
    return env


def _window_run(env):
    started = time.time()
    done = subprocess.run([sys.executable, "-u", str(Path(__file__)), "--child", repr(started)], env=env, cwd=ROOT,
                          capture_output=True, text=True, encoding="utf-8", timeout=600)
    total = time.time() - started
    if done.returncode != 0:
        raise SystemExit(f"the window's run failed ({done.returncode}):\n{done.stderr[-3000:]}")
    result = json.loads(done.stdout.strip().splitlines()[-1])
    result["total"] = total
    return result


def _export_run(env, file):
    """The export a window starts, timed whole; then once more under -X importtime, for what its imports cost."""
    command = [sys.executable, str(ROOT / "calc" / "cli.py"), "export", "--data-only", "--project", str(file)]
    begun = time.perf_counter()
    done = subprocess.run(command, env=env, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", timeout=600)
    total = time.perf_counter() - begun
    timed = subprocess.run([sys.executable, "-X", "importtime", *command[1:]], env=env, cwd=ROOT,
                           capture_output=True, text=True, encoding="utf-8", timeout=600)
    imports = {}
    for line in timed.stderr.splitlines():
        if line.startswith("import time:") and "|" in line:
            _self, cumulative, name = (part.strip() for part in line[len("import time:"):].split("|"))
            if cumulative.isdigit() and not name.startswith(" "):
                imports[name.strip()] = int(cumulative) / 1e6
    top = sorted(((name, seconds) for name, seconds in imports.items() if "." not in name), key=lambda pair: -pair[1])[:8]
    return {"total": total, "returncode": done.returncode, "imports_total": sum(s for n, s in imports.items() if "." not in n), "top_imports": top}


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--json")
    parser.add_argument("--no-export", action="store_true")
    parser.add_argument("--child")
    args = parser.parse_args()
    if args.child:
        _child(float(args.child))
        return
    work, file = _copy_project()
    env = _environment(work, file)
    try:
        runs = [_window_run(env) for _ in range(args.runs)]
        export = None if args.no_export else _export_run(env, file)
    finally:
        shutil.rmtree(work, ignore_errors=True)
    for number, run in enumerate(runs, 1):
        print(f"\nrun {number} ({'first' if number == 1 else 'warm'}) -- {run['total']:.2f} s in all")
        for name, seconds in run["phases"]:
            print(f"  {name:<30} {seconds:7.2f} s")
        slow = sorted(run["tabs"], key=lambda pair: -pair[1])[:6]
        print("  slowest tabs: " + ", ".join(f"{key} {seconds:.2f} s" for key, seconds in slow))
    if export:
        print(f"\nexport --data-only: {export['total']:.2f} s (exit {export['returncode']}), imports {export['imports_total']:.2f} s")
        print("  " + ", ".join(f"{name} {seconds:.2f} s" for name, seconds in export["top_imports"]))
    if args.json:
        Path(args.json).write_text(json.dumps({"runs": runs, "export": export}, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
