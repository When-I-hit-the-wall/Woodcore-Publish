"""Woodcore's start: everything loaded behind the start screen, and its steps said in three languages (calc/tools/woodcore_start.py; spec docs/requirements/completed/2026-10-07-performance-erreurs-plans-legendes.md, REQ-003, REQ-004).

The engineer, 07.10.2026: «l'immense majorité des éléments nécessaires au fonctionnement de Woodcore soient initialisés pendant le démarrage». Each check runs in a fresh process, since the suite's own has imported everything long ago. Split from tests/test_startup.py in v0.117 (issue #26): what the start does is checked by every run, how fast it does it by `--perf` alone.
"""

import os
import subprocess
import sys

import conftest
from conftest import ROOT, Skip

CHILD = r'''
import os, sys
sys.path[:0] = [os.path.join(sys.argv[1], "calc", "tools"), os.path.join(sys.argv[1], "calc")]
from PySide6.QtWidgets import QApplication
app = QApplication([])
import theme, woodcore_start as ws
theme.apply(app)
for key in ("libraries", "calc", "typst"):
    ws._import_in_thread(ws.IMPORTS[key])
import importlib
for name in ws.WINDOW_MODULES:
    importlib.import_module(name)
import woodcore_gui
window = woodcore_gui.open_project(app, os.environ["WOODCORE_PROJECT"], quiet=True)
before = set(sys.modules)
for index in range(window.tab_widget.count()):
    window.tab_widget.setCurrentIndex(index)
    app.processEvents()
    tab = window.tabs[index]
    for view in getattr(tab, "VIEWS", ()):
        try:
            tab.set_view(view)
        except Exception:
            pass
        app.processEvents()
new = sorted(name for name in set(sys.modules) - before if not name.startswith(("encodings.", "_")))
print("NEW:" + ",".join(new), flush=True)
# what was measured is written: the process ends here, without tearing a window down outside its event loop -- which a real start never does (it quits through app.exec(), see the self-test above) and which crashed this script's interpreter at exit (0xC0000409) once in a while
os._exit(0)
'''


def _env():
    import perf_startup
    work, file = perf_startup._copy_project()
    return work, perf_startup._environment(work, file), file


def test_after_the_start_no_tab_imports_anything_when_it_is_first_shown():
    """REQ-004: what the tabs need is imported while the start screen is up -- going through every tab and every view afterwards imports nothing new."""
    import shutil
    work, env, _file = _env()
    try:
        done = subprocess.run([sys.executable, "-c", CHILD, str(ROOT)], env=env, capture_output=True, text=True, encoding="utf-8", timeout=600)
        assert done.returncode == 0, done.stderr[-3000:]
        line = next((l for l in done.stdout.splitlines() if l.startswith("NEW:")), None)
        assert line is not None, done.stdout[-2000:] + done.stderr[-2000:]
        new = [name for name in line[4:].split(",") if name]
        assert not new, f"imported on a tab's first showing, after the start: {new}"
    finally:
        shutil.rmtree(work, ignore_errors=True)


def test_the_start_s_steps_are_said_in_three_languages_and_weighed_by_the_last_start():
    import json
    tools = str(ROOT / "calc" / "tools")
    if tools not in sys.path:
        sys.path.insert(0, tools)
    try:
        import woodcore_start
    except ImportError as exc:
        raise Skip(f"PySide6 is not installed ({exc})")
    keys = {f"start_{key}" for key, _w in woodcore_start.STEPS} | {"start_title"}
    for lang in ("fr", "de", "en"):
        assert keys <= set(woodcore_start.STRINGS[lang]), (lang, keys - set(woodcore_start.STRINGS[lang]))
    folder = conftest.tmpdir("start-weights")
    saved = woodcore_start._weights_path
    woodcore_start._weights_path = lambda: folder / "start-weights.json"
    try:
        assert woodcore_start.read_weights() == dict(woodcore_start.STEPS), "no cache: the default weights"
        woodcore_start.write_weights({"tabs": 3.5, "libraries": 1.0})
        weights = woodcore_start.read_weights()
        assert weights["tabs"] == 3.5 and weights["calc"] == dict(woodcore_start.STEPS)["calc"]
        (folder / "start-weights.json").write_text("{not json", encoding="utf-8")
        assert woodcore_start.read_weights() == dict(woodcore_start.STEPS), "a cache that does not read is no cache"
        (folder / "start-weights.json").write_text(json.dumps({"schema_version": "9.0", "seconds": {"tabs": 1}}), encoding="utf-8")
        assert woodcore_start.read_weights()["tabs"] == dict(woodcore_start.STEPS)["tabs"], "another version is not read"
    finally:
        woodcore_start._weights_path = saved
