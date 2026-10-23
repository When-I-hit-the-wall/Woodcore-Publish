"""Shared setup for every test in this folder.

Puts `calc/` on the import path so a test imports the pipeline exactly as `export_all.py` does -- `import validation`, `from domains import dead_load` -- rather than through a package path that only tests would use. pytest imports this file automatically; `run_tests.py` imports it first for the same reason.
"""

import atexit
import contextlib
import os
import re
import sys
import unittest
from pathlib import Path

# 000-Python/, the program: calc/, lib/, schemas/ (docs/architecture/layout.md §11).
ROOT = Path(__file__).resolve().parent.parent
CALC = ROOT / "calc"

for path in (str(CALC), str(ROOT)):
    if path not in sys.path:
        sys.path.insert(0, path)

import project  # noqa: E402  -- calc/project.py: the project every test below works on

# Where a test may write, and **one directory per process**. Under the Typst root, so a .typ written here compiles with --root on the report's folder; under the process id, so two runs of the suite at once cannot reach into each other's files (v0.64.2).
#
# That last part repairs a defect rather than guarding against a theoretical one. `tmpdir()` wipes and recreates the directory it is handed, so run A removed run B's probe in the middle of a test and B failed with `file not found (searched at ...\tests\.tmp\formula\probe.typ)` -- a message that cannot come from the code under test. Two sessions measured it apart from one another, 20, 21 and 29 failures against 0 for the same tests run alone, and the line between them was exactly whether a suite writes a .typ. It is the same fault, and the same repair, as command_preview's own directory.
TMP = ROOT / "tests" / ".tmp" / str(os.getpid())

# Woodcore's preferences, redirected for the whole run (v0.75; `WOODCORE_SETTINGS` since v0.83, `TYPST_KATALOG_SETTINGS` until then): a test building a window, or the start page, must never write the engineer's own `%APPDATA%\Woodcore\settings.json` -- the language, the window's size, the recent projects. usersettings.py reads the variable at every read and write.
#
# ⚠️ The file is seeded in English, the language the suite ran under until then by reading the engineer's own file. The window's minimum widths are language-dependent -- French labels are wider -- and a test that silently changed language with the machine it runs on would measure a different window on each (tests/test_panes.py measures 320 px of play in French against more than 400 in English).
#
# ⚠️ Beside `TMP` and not inside it: `tests/test_harness.py` calls `cleanup()` in the middle of a run, which removes `TMP` whole, and a settings file inside it vanished with it -- every window built after the harness tests then opened in French and `test_panes` measured the French window. Removed at exit (registered after `cleanup`, so it runs first and `tests/.tmp` can still be taken away empty).
SETTINGS = ROOT / "tests" / f".settings-{os.getpid()}.json"
os.environ.setdefault("WOODCORE_SETTINGS", str(SETTINGS))
if os.environ["WOODCORE_SETTINGS"] == str(SETTINGS) and not SETTINGS.exists():
    SETTINGS.write_text('{"lang": "en", "appearance": "light"}', encoding="utf-8")  # the light scheme whatever Windows' is, so a colour a test reads is one colour (theme.py, v0.90)

# Qt draws without a screen, set here once for every test and every process a test starts (v0.117, issue #26): a CI runner and a cloud session have no display, and a test that opened a real window on the engineer's machine would take the focus while he works. A value already set wins -- tests/test_no_console.py removes it on purpose, for a real window.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

# A window opened by a test checks no Typst at its start (calc/tools/typst_check.py, v0.94): no modal on a machine whose Typst is not the pin, and no request to GitHub. tests/test_typst_check.py sets it for the checks it makes.
os.environ.setdefault("WOODCORE_TYPST_CHECK", "0")

# And its «Variables» tab reads no report by itself (calc/variables.py): a reading is a full compile, and a suite that brings every tab forward to look at its buttons must not pay for one -- nor leave the thread of one running behind a window it is about to close. tests/test_variables.py reads deliberately, by calling the module.
os.environ.setdefault("WOODCORE_VARIABLES_READ", "0")


class Skip(unittest.SkipTest):
    """Raised by a test that cannot run here -- no workbook, no Typst binary. Printed and counted, never a failure -- by run_tests.py, and by pytest too, which treats a `unittest.SkipTest` as a skip (periodic audit 260916)."""


class OtherSystem(Skip):
    """Raised by a test of another operating system's own behaviour -- a console window, the Windows API, Windows' fonts (v0.117, issue #26). Printed and counted apart by run_tests.py, as a test of time is: it says nothing missing from this machine, and the CI's job on that system runs it. A skip still for pytest."""


def _wipe(path):
    """`path` and everything under it, gone, and nothing said if it was never there. One place rather than two: the runner carried a second copy of this loop, which is what let the repair be applied to one of them and not the other."""
    if not path.exists():
        return
    for p in sorted(path.rglob("*"), reverse=True):
        if p.is_file():
            if not os.access(p, os.W_OK):
                os.chmod(p, 0o666)   # the engine copied into a project is left read-only (calc/project.py sync_engine), which Windows will not delete
            p.unlink()
        else:
            _rmdir(p)
    _rmdir(path)


def _rmdir(path):
    """A directory removed even when Windows marks it read-only -- `tests/projet-exemple/Formules` carries the attribute, `copytree` copies it, and `rmdir` was refused at every exit: each run left its `.project-<pid>` copy behind, forty of them after a night, and `test_harness`'s walk of `tests/` went through every one (issue #22)."""
    try:
        path.rmdir()
    except PermissionError:
        os.chmod(path, 0o777)
        path.rmdir()


def tmpdir(name):
    """A clean directory for one test to write in, inside this process's own."""
    d = TMP / name
    _wipe(d)
    d.mkdir(parents=True)
    return d


def cleanup():
    """This process's temporary directory, removed. Idempotent: the runner calls it before printing its summary, `atexit` calls it again, and pytest -- which never runs the runner -- is covered by `atexit` alone.

    The parent `tests/.tmp` goes too, but only when it is empty. It is not empty exactly when another run still holds a directory of its own in it, and there the refusal is the right answer rather than a fault worth reporting.
    """
    _wipe(TMP)
    try:
        TMP.parent.rmdir()
    except OSError:
        pass


atexit.register(cleanup)
atexit.register(lambda: SETTINGS.unlink(missing_ok=True))


# The project every test works on (v0.81): a copy of tests/projet-exemple/, made once per process, with the engine synced into it as an export does. The example is a real project anonymised -- the sources drawn in its window, its export and its report, no workbook, blank pages in place of the architect's (the engineer's decision, 19.09.2026) -- so a clone of the code tests itself without any project of its own.
#
# ⚠️ Since the three document modes (work package 1.8) the example is laid out in three documents, as a migrated project is -- `1_Nutzungsvereinbarung/`, `2_Projektbasis/`, `3_Statischer Bericht/` at its top, with the config.typ, commands.typ, pictures and export the three share -- and its Typst root is **its own folder**, no longer the report's. The one report alone it was laid out as until then is rebuilt from it where a test needs one: tests/fixtures/legacy_example.py.
#
# ⚠️ A copy, and beside `TMP` rather than inside it, for the reasons SETTINGS is: a test writes into the project it works on -- a connector saved, a ghost position planted -- and must never write into the committed example; and `cleanup()`, which test_harness.py calls mid-run, would take a copy inside `TMP` with it.
SAMPLE = ROOT / "tests" / "projet-exemple" / "Exemple.woodcore"
WORK = ROOT / "tests" / f".project-{os.getpid()}"


def _session_project():
    import shutil
    _wipe(WORK)
    # the engine a sync wrote, the stamps a compile wrote and the archives a run on the committed example left are not the example's (all gitignored) -- in the export's folder, `_woodcore/` or 000-Woodcore/ since the layout by folders (issue #64), which holds the archives too
    top = SAMPLE.parent.resolve()

    def ignore(directory, names):
        here = Path(directory).resolve()
        if here == top:
            return {n for n in names if n in ("_Archiv",) or n.startswith(".woodcore-") or n.endswith(".lock")}
        if here.parent == top and here.name in ("_woodcore", project.WOODCORE_FOLDER):
            return {n for n in names if n in ("lib", "calc", "VERSION", "stamps", "archives", "out", ".preview")}
        return set()
    shutil.copytree(SAMPLE.parent, WORK, ignore=ignore)
    here = project.use(WORK / SAMPLE.name)
    project.sync_engine(here)
    # a subprocess a test starts -- an export, a probe of project.current() -- works on the same copy
    os.environ[project.ENV] = str(here.file)
    return here


PROJECT = _session_project()
atexit.register(lambda: _wipe(WORK))

# The Typst root of that project -- its own folder, the example being laid out in three documents: what a probe is compiled with as --root, and where `/commands.typ` resolves.
TYPST_ROOT = PROJECT.typst_root


def probe_dir(name):
    """A clean directory for one test's .typ probes, inside the Typst root of the project the tests work on -- a probe has to sit under --root to compile. Per process like everything here, the project being this process's own copy."""
    d = TYPST_ROOT / ".probe" / name
    _wipe(d)
    d.mkdir(parents=True)
    return d


def import_path(path):
    """`path` as an absolute Typst import, read from TYPST_ROOT: `/_woodcore/data/connections.json`. Computed, never written down (tests/test_harness.py)."""
    return "/" + Path(path).resolve().relative_to(TYPST_ROOT.resolve()).as_posix()


# The engineer's own project, for the few checks that read a workbook -- the example carries none. `WOODCORE_REAL_PROJECT` names its .woodcore; without it the one beside this checkout (Musterprojekt.woodcore, while the code and the project share a folder) is taken.
REAL_ENV = "WOODCORE_REAL_PROJECT"


def real_project():
    """The engineer's own project, or a Skip where this machine has none -- a clone of the code on another machine."""
    named = os.environ.get(REAL_ENV)
    file = Path(named) if named else project.checkout_project()
    if file is None or not Path(file).is_file():
        raise Skip(f"no project of the engineer's here -- name its .woodcore in {REAL_ENV}")
    return project.Project.load(file)


def engine_source():
    """The text of the report engine's display layer: lib/calc-engine.typ and the parts it was cut into by subject (spec 2026-10-19-base-saine-nettoyage, G9), in the order they import one another -- what a test that reads the engine's text reads, so that a binding moved from one part to another is still found."""
    lib = ROOT / "lib"
    parts = [lib / "calc-engine.typ"] + [lib / f"calc-engine-{name}.typ" for name in ("core", "drawings", "display", "records", "connections")]
    return "\n".join(path.read_text(encoding="utf-8") for path in parts if path.is_file())


# The norms' PDFs the JSON of calc/norms/ were read off: shipped with Woodcore in `norm-library/` since the spec 2026-10-22-onglet-neige-type (D-24), `WOODCORE_NORMS_LIBRARY` naming another folder where it is set (spec 2026-10-19-base-saine-nettoyage, REQ-004). No path of the engineer's machine is written in the repository.
NORMS_ENV = "WOODCORE_NORMS_LIBRARY"


def norms_library():
    """The folder of the norms' PDFs: `WOODCORE_NORMS_LIBRARY` where it is set, else the shipped `norm-library/` -- a test that needs a page skips, naming it, on a clone that lacks it."""
    named = os.environ.get(NORMS_ENV)
    return Path(named) if named else ROOT / "norm-library"


def project_copy(name, data=True):
    """A copy of the current project in this process's own temp folder, laid out as the real one, as a `calc/project.py` Project -- for a test to work on with `project.using(...)`.

    It carries what a window reads and writes: the .woodcore (its layout the real one's), the sources drawn in the window and the export when `data`. Neither the report nor the plans' backgrounds are copied: a plan then says its background is missing, as it does on a machine NextCloud has not synced yet -- and a copied PDF would be held open by the plan tab's renderer, which Windows then refuses to let the run delete. Until v0.81 a test pointed each module's path constants and two default arguments at copies of the folders it needed; a project is now one object, so pointing it at a copy moves every path at once.
    """
    import json
    import shutil
    import project
    real = project.current()
    root = tmpdir(name)
    copied = project.Project(root / real.file.name, dict(real.data))
    for folder in project.SOURCE_FOLDERS:
        source = real.sources_dir / folder
        target = copied.sources_dir / folder
        if source.is_dir():
            shutil.copytree(source, target, ignore=shutil.ignore_patterns("archives"))
        else:
            target.mkdir(parents=True)
    # the project's positions, Woodcore's own file since v0.114 (calc/positions_store.py): a source like the folders above, and what every tab and the export read the positions from
    positions = real.positions_dir / "positions.json"
    if positions.is_file():
        copied.positions_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(positions, copied.positions_dir / "positions.json")
    # the scripts, which a project laid out by folders keeps in Scripts/ rather than in its sources (issue #64) -- the scripts and not their stubs, as no domain's .typ is copied
    if real.has_folders and real.domain_dir("script").is_dir():
        copied.domain_dir("script").mkdir(parents=True, exist_ok=True)
        for path in real.domain_dir("script").glob("*.py"):
            shutil.copy2(path, copied.domain_dir("script") / path.name)
    # the order of the window's lists, Woodcore's own file since issue #15 (calc/list_order.py)
    if real.lists_file.is_file():
        shutil.copy2(real.lists_file, copied.lists_file)
    # the building VKF 15-15 reads the fire resistance off, Woodcore's own file since issue #46 (project.building_file)
    if real.building_file.is_file():
        shutil.copy2(real.building_file, copied.building_file)
    if data and real.data_dir.is_dir():
        shutil.copytree(real.data_dir, copied.data_dir)
    copied.typst_root.mkdir(parents=True, exist_ok=True)
    # each document's entry file, and that alone: a document is made where its entry is there (Project.created_modes, issue #90), and a copy without them would be a project none of whose documents is made yet -- every tab greyed but «Projet»
    for mode in real.created_modes:
        entry = copied.document_typ(mode)
        entry.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(real.document_typ(mode), entry)
    copied.file.write_text(json.dumps(real.data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return project.Project.load(copied.file)


def legacy_modes_layout(lang="de"):
    """The layout of a project in three documents as Woodcore wrote one before the project laid out by folders (0.111 to 0.118, issue #64): the documents in `1_…`, `2_…`, `3_…` named in the project's language, config.typ and commands.typ at the top of the project, `_woodcore/`, `Woodcore-Datei/`, `_Archiv/`, and no `layout.config` -- what a project made then still states until it is migrated (calc/documents.py `legacy_modes_layout`)."""
    import documents
    lang = documents.language_of(lang)
    return documents.legacy_modes_layout(documents.LEGACY_MODE_FOLDERS[lang], documents.ENTRY_NAMES[lang])


@contextlib.contextmanager
def notices_said(record):
    """Every notice reported while the block runs -- and every one reported again, its count going up -- handed to `record(notice)`: what a test reads where it once stubbed a message box (v0.117: no box for an error, a warning or an information, calc/notifications.py). An information is handed over before the window's bar sends it to the status line."""
    import notifications
    seen = {n.id: n.count for n in notifications.STORE.items()}

    def listener():
        for notice in reversed(notifications.STORE.items()):
            if seen.get(notice.id) != notice.count:
                seen[notice.id] = notice.count
                record(notice)
    notifications.STORE.listen(listener)
    try:
        yield
    finally:
        notifications.STORE.unlisten(listener)


def have_typst():
    import shutil
    return shutil.which("typst") is not None


# How a panic reaches stderr, in the two forms the two Typst versions print. 0.14 printed the value's
# repr -- `panicked with: "..."`, quoted, its own quotes escaped -- and 0.15 prints the string itself,
# unquoted and unescaped, the message running to the line that opens the diagnostic frame (or to the
# end, where there is none). Both are read, so the suite says the same thing on either.
_PANIC = re.compile(r'panicked with: (?:"(?P<quoted>.*?)"\n|(?P<plain>.*?)(?:\n *┌─|\Z))', re.S)


def panic_message(stderr):
    """The message a Typst panic carries, alone -- or None where `stderr` holds no panic, a compile error being another thing.

    A refusal in this engine is a panic (docs/typst/formulas.md §10quinquies, docs/domain/member-checks.md §3.3undecies), so a test that holds a refusal reads one, and it has to read the *message* rather than the whole diagnostic: the stderr also quotes the engine's own source, so a check that the message does not send the reader to `value:` passes over a source line that does (tests/test_command_review.py), and one that reads what the message starts with reads «error: panicked with: ...» instead.

    It is one function because five call sites across four test files parsed the quoted form by hand, and every one of them went stale the day the Typst on the path moved from 0.14.2 to 0.15.1: the two that isolate a message failed, and the other three -- falling back to the whole stderr, which still holds the words a substring check looks for -- were waiting to.
    """
    found = _PANIC.search(stderr)
    if found is None:
        return None
    quoted = found.group("quoted")
    return quoted if quoted is not None else found.group("plain")


def exported(name):
    """One file of the current project's data/, or a Skip when the export has never been run here."""
    import json
    import project
    p = project.current().data_dir / name
    if not p.exists():
        raise Skip(f"data/{name} is not there -- run python calc/export_all.py first")
    return json.loads(p.read_text(encoding="utf-8"))

def module_source(path):
    """The text of a module of calc/ and of every part split out of it (docs/architecture/layout.md §11, issue #30): what a test that reads a module's source reads, the module having kept its name and moved some of its text beside it. `path` a Path or a name relative to calc/ (`tools/woodcore_gui.py`)."""
    import re
    path = Path(path) if Path(path).is_absolute() else ROOT / "calc" / path
    text = path.read_text(encoding="utf-8")
    parts = [text]
    seen = set()
    for m in re.finditer(r"^\s*from ([\w.]+) import .*# split out of this module \(issue #30\)", text, re.M):
        part = path.parent / (m.group(1).split(".")[-1] + ".py")   # tools.x is x.py: the same file, imported by the package's name
        if part.is_file() and part not in seen:
            seen.add(part)
            parts.append(module_source(part))
    return "\n".join(parts)

def dispose(window):
    """A window a test is done with, closed **and destroyed** (v0.117, issue #26). Closed alone it stays alive, and every window left alive makes each later deletion of a Qt object slower -- shiboken releases a wrapper among all the others: on a fresh Linux test_fire_tab, fifty tests each opening Woodcore's window, ran for over an hour and held 3.6 GB, and takes three minutes once each window is destroyed when its test ends."""
    from PySide6.QtCore import QCoreApplication, QEvent
    window.close()
    window.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)



def figure(here, name):
    """The file of a figure as an export's JSON names it -- from the Typst root in a project laid out by folders (`/Plans/Position-plan/Exports/Figures/P01.svg`), under data/ before (`plans/P01.svg`): calc/engine.py `Figures.path`, the one reader (issue #64)."""
    import engine
    return engine.Figures(here.data_dir, "plan", here).path(name)
