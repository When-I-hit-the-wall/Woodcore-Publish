"""The modules split out of another import on their own, in a fresh interpreter, and every name the module they came from had is still read from it (docs/architecture/layout.md §11, «How long a module may be»; spec docs/requirements/completed/2026-10-10-audit-issues-26-a-33.md, REQ-30-02, ARCH-02; issue #30).

A split moves text and closes the set moved over what it reads, so a part never imports its module and no import goes round in a circle -- which only a fresh interpreter proves: in this one everything has long been imported. And calc/domains/ stays Qt-free: every module of it is imported with PySide6 out of reach.
"""

import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from conftest import ROOT

SPLIT = re.compile(r"^from ([\w.]+) import \(?(.*?)\)?\s*# split out of this module \(issue #30\)", re.M)


def splits():
    """[(the module split, as imported; the part, as imported; the names it imports back)] of every split of calc/."""
    found = []
    for path in sorted((ROOT / "calc").rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        text = path.read_text(encoding="utf-8")
        for m in re.finditer(r"^\s*from ([\w.]+) import (\((?:[^()]*)\)|[^\n]*?)\s*(?:# split out of this module \(issue #30\).*)?$", text, re.M):
            line_end = text.find("\n", m.start())
            head = text[m.start():line_end]
            if "# split out of this module (issue #30)" not in head or m.group(1).startswith("tools."):
                continue   # tools.x is x imported by the package's name, where the export reaches calc/tools/ (build_reference): the same file
            names = re.findall(r"\b[A-Za-z_][A-Za-z0-9_]*\b", m.group(2).split("#")[0] if not m.group(2).startswith("(") else re.sub(r"#[^\n]*", "", m.group(2)))
            module = ("domains." + path.stem) if path.parent.name == "domains" else path.stem
            found.append((module, m.group(1), names))
    return found


def _run(code):
    """`code` run in an interpreter of its own, from a file: the check of every split is longer than the 32 767 characters Windows allows a command line (WinError 206)."""
    paths = [str(ROOT / "calc"), str(ROOT / "calc" / "tools")]
    with tempfile.TemporaryDirectory() as d:
        script = Path(d) / "probe.py"
        script.write_text(f"import sys; sys.path[:0] = {paths!r}\n" + code, encoding="utf-8")
        return subprocess.run([sys.executable, str(script)], capture_output=True, text=True, encoding="utf-8", timeout=600)


def test_every_part_imports_alone_and_its_module_still_has_every_name():
    found = splits()
    assert found, "no module of calc/ has been split yet"
    code = "import importlib\n"
    for module, part, names in found:
        code += f"importlib.import_module({part!r})\n"
        code += f"m = importlib.import_module({module!r}); p = importlib.import_module({part!r})\n"
        code += f"missing = [n for n in {names!r} if getattr(m, n, None) is not getattr(p, n, object())]\n"
        code += f"assert not missing, ({module!r}, {part!r}, missing)\n"
    # each part first, in an interpreter of its own: a part that imported its module would fail here
    for _module, part, _names in found:
        done = _run(f"import importlib; importlib.import_module({part!r})")
        assert done.returncode == 0, f"{part} does not import alone:\n{done.stderr[-2000:]}"
    done = _run(code)
    assert done.returncode == 0, done.stderr[-3000:]


def test_the_domain_is_imported_with_pyside6_out_of_reach():
    code = (
        "import importlib.abc, sys\n"
        "class Block(importlib.abc.MetaPathFinder):\n"
        "    def find_spec(self, name, path, target=None):\n"
        "        if name.split('.')[0] in ('PySide6', 'shiboken6'):\n"
        "            raise ImportError('PySide6 is out of reach: calc/domains/ is Qt-free')\n"
        "sys.meta_path.insert(0, Block())\n"
        "import importlib, pathlib\n"
        f"for path in sorted(pathlib.Path({str(ROOT / 'calc' / 'domains')!r}).glob('*.py')):\n"
        "    if path.stem != '__init__':\n"
        "        importlib.import_module('domains.' + path.stem)\n"
    )
    done = _run(code)
    assert done.returncode == 0, done.stderr[-3000:]


def test_the_window_imports_with_calc_tools_alone_on_the_path():
    """Woodcore.bat, woodcore_start and test_panes' probe start the window with calc/tools alone on the path, and woodcore_gui puts calc/ there itself: the parts split out of it (issue #30) import calc/'s modules, so they must be imported after it does -- the re-imports once sat above that line, and the window did not start that way (the Windows CI's test_panes, 10.10.2026)."""
    done = subprocess.run([sys.executable, "-"], input=f"import sys; sys.path.insert(0, {str(ROOT / 'calc' / 'tools')!r})\nimport woodcore_gui\nprint('ok')\n",
                          capture_output=True, text=True, encoding="utf-8", timeout=600, env=dict(os.environ, QT_QPA_PLATFORM="offscreen"))
    assert done.returncode == 0 and done.stdout.strip().endswith("ok"), done.stderr[-2000:]
