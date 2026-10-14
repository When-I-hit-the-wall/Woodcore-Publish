# -*- mode: python ; coding: utf-8 -*-
# Woodcore's two executables in one folder (docs/conventions/build-and-release.md §12, v0.83): Woodcore.exe, the window, and woodcore-cli.exe, the command line -- which the window's «Importer Excel» runs. Run by packaging/build.py, which sets WOODCORE_BUILD_WORK to the folder holding what it generated first: build-info.json, woodcore.ico, the two version resources, and typst.exe.
#
# The program's modules are NOT frozen into the archive: they are shipped as they are, under _internal/calc/, and the two entry points import them from there (entry_gui.py). Every path a module derives from its own file is then the path it has in the checkout -- a norm's JSON beside its reader, the schemas beside calc/ -- and `domains`, `norms` and `i18n`, packages without an __init__.py, import as they do from the sources. What they import from outside is found by reading every import statement of calc/ (`imported()`), those inside a function included, and handed to PyInstaller as hidden imports: nothing the program imports late is left out of the folder.

import ast
import importlib.util
import os
from pathlib import Path

ROOT = Path(SPECPATH).parent
CALC = ROOT / "calc"
WORK = Path(os.environ["WOODCORE_BUILD_WORK"])


def app_modules():
    """The top-level names of the program's own modules and packages: calc/'s and calc/tools/'s."""
    names = set()
    for base in (CALC, CALC / "tools"):
        for path in base.iterdir():
            if path.suffix == ".py":
                names.add(path.stem)
            elif path.is_dir() and path.name not in ("tools", "__pycache__") and any(path.rglob("*.py")):
                names.add(path.name)
    return names


APP = app_modules()


def imported():
    """Every module calc/ imports from outside itself, by name, where the build's interpreter can find it."""
    found = set()
    for path in CALC.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Import):
                found.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                found.add(node.module)
                found.update(f"{node.module}.{alias.name}" for alias in node.names)
    keep = []
    for name in sorted(found):
        if name.split(".")[0] in APP:
            continue
        try:
            if importlib.util.find_spec(name) is not None:
                keep.append(name)
        except (ImportError, ValueError, AttributeError):
            pass
    return keep


def tree(folder):
    """Every file under ROOT/folder, where the checkout has it -- hidden folders (templates/projet/.vscode) included, compiled leftovers not."""
    out = []
    for path in sorted((ROOT / folder).rglob("*")):
        if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc":
            out.append((str(path), str(path.parent.relative_to(ROOT))))
    return out


datas = tree("calc") + tree("lib") + tree("schemas") + tree("examples") + tree("templates") + tree("legal") + [
    (str(ROOT / "requirements.txt"), "."),
    (str(WORK / "build-info.json"), "."),
    (str(WORK / "typst.exe"), "."),
]

common = dict(
    pathex=[str(CALC), str(CALC / "tools")],
    hiddenimports=imported(),
    excludes=["tkinter", "pytest", "IPython"],
    noarchive=False,
)

gui = Analysis([str(Path(SPECPATH) / "entry_gui.py")], datas=datas, **common)
cli = Analysis([str(Path(SPECPATH) / "entry_cli.py")], **common)
for analysis in (gui, cli):
    analysis.pure = [entry for entry in analysis.pure if entry[0].split(".")[0] not in APP]

gui_exe = EXE(
    PYZ(gui.pure), gui.scripts, [],
    exclude_binaries=True, name="Woodcore", console=False,
    icon=str(WORK / "woodcore.ico"), version=str(WORK / "version-gui.txt"), upx=False,
)
cli_exe = EXE(
    PYZ(cli.pure), cli.scripts, [],
    exclude_binaries=True, name="woodcore-cli", console=True,
    icon=str(WORK / "woodcore.ico"), version=str(WORK / "version-cli.txt"), upx=False,
)
COLLECT(gui_exe, gui.binaries, gui.datas, cli_exe, cli.binaries, cli.datas, name="Woodcore", upx=False)
