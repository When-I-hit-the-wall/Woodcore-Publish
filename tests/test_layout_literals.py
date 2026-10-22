"""The names of a project's folders are written once (issue #64, spec 2026-10-15-structure-projet-dossiers ARCH-001).

A project's layout -- 000-Typst-Config/, 000-Woodcore/, Domains/, the folders of the domains, and before them `_woodcore`, `Woodcore-Datei`, `_Archiv`, `Formules` and `/commands.typ` at the root -- is calc/project.py's and calc/documents.py's. A module that spells one of them again ages without saying so the day the layout moves, which is the defect the layout by folders had to hunt down in some fifteen files. This walks every string the code of calc/ and lib/ holds -- the string constants Python reads, not its comments and docstrings -- and names each one that spells a folder of the layout outside the modules allowed to.
"""

TIER = "fast"  # tests/run_tests.py --fast

import ast
import re

from conftest import CALC, ROOT

# The modules where the names are defined, and the ones that must read the layout as it was: the migration, which moves a project out of it, the path rewriter, and the frozen documentation examples (examples/ is not a project).
ALLOWED = {
    "project.py", "documents.py", "project_migrate.py", "typst_paths.py",
    "tools/command_preview.py", "tools/build_examples.py",
    # the writers of what a template, a form or a content template holds, in the one canonical form every project laid out before reads -- `/commands.typ`, `/Template/…` at the root -- which the creation of a project laid out by folders rewrites where 000-Typst-Config/ keeps it (documents.relocate_config_paths)
    "forms.py", "structure.py",
}
# The spellings a module may not hold: a folder of either layout, by itself or at the start of a path -- and the ones that are also words of the window (`Domains`, the English name of a tab and a group) only at the start of a path.
FOLDERS = ("_woodcore", "Woodcore-Datei", "_Archiv", "Formules", "000-Typst-Config", "000-Woodcore")
PATH_FOLDERS = ("Domains",)
COMMANDS = re.compile(r'"/commands\.typ"|^/commands\.typ$|^/Template/|"/Template/')


def _strings(path):
    """Every string constant of the module at `path` that is not a docstring, with its line."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    docstrings = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.body:
            first = node.body[0]
            if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) and isinstance(first.value.value, str):
                docstrings.add(id(first.value))
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in docstrings:
            yield node.lineno, node.value


def test_no_module_spells_a_folder_of_the_layout_again():
    found = []
    for path in sorted(CALC.rglob("*.py")):
        rel = path.relative_to(CALC).as_posix()
        if rel in ALLOWED or "__pycache__" in rel:
            continue
        for line, value in _strings(path):
            first = value.strip().lstrip("/").split("/", 1)[0]
            if first in FOLDERS or (first in PATH_FOLDERS and "/" in value) or COMMANDS.search(value):
                found.append(f"calc/{rel}:{line}: {value[:80]!r}")
    assert not found, "a folder of the layout spelled outside calc/project.py and calc/documents.py:\n" + "\n".join(found)


def test_the_engine_names_no_folder_of_the_layout():
    """lib/ is copied into every project and reads what it reads relatively (`../data/…`) or from what the export hands it: a folder of the layout written there would be one more place for it to age."""
    found = []
    for path in sorted((ROOT / "lib").glob("*.typ")):
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            code = line.split("//", 1)[0] if not line.lstrip().startswith("///") else ""
            for folder in FOLDERS:
                if re.search(r'"/?' + re.escape(folder) + r'(/|")', code):
                    found.append(f"lib/{path.name}:{number}: {line.strip()[:100]}")
    assert not found, "\n".join(found)
