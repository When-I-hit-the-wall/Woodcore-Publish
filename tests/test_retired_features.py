"""What Woodcore retired, and that it is retired whole (spec docs/requirements/completed/2026-10-08-onglet-formule-domaines.md, REQ-001 to REQ-004).

The engineer, 08.10.2026: «Tu peux supprimer les onglets RFEM ainsi que Formule. Mets-les dans un dossier archive, mais retire définitivement le code de Woodcore.» Two features went in 0.117: the RFEM import -- its tab, the reader of RFEM's table export, the `rfem` domain, `#rfem-max`, `#show-rfem-forces`, `#show-rfem-combination`, `woodcore-cli import`, the static models it generated and their internal-force diagrams -- and v0.100's «Formules» tab of keyword lines. Their code is in archive/, kept and not run.

What is held here:

* nothing of the program names them any more -- a line that does says why (it names the retirement) or it is a leftover;
* the archive is there, says what it holds, and is out of the way of a test run;
* a project file that still names RFEM -- the example project's does, on purpose, and the engineer's Musterprojekt does -- opens and exports, the key ignored and said at every export, and the export no longer writes `data/rfem*` and removes what an older one left.
"""

import os
import re
import subprocess
import sys

import conftest
from conftest import ROOT

TOOLS = ROOT / "calc" / "tools"

# What the retired features were called in the code: a module, a tab, a Typst file or command, a project key.
RETIRED = re.compile(r"rfem_import|rfem_tab|dsl_tab|\bdsl\b|statics_view|rfem\.typ|\brfem-[a-z]|rfem_models|rfem_export|RfemTab|DslTab")
# Where the program lives: what the installer carries and the engine copies into a project.
SCANNED = ("calc", "lib", "schemas", "packaging", "templates")
# A line may name a retired feature only to say it was retired.
SAYS_WHY = re.compile(r"0\.117|[Rr]etired|RETIRED")


def test_nothing_of_the_program_names_a_retired_feature_but_to_say_it_was_retired():
    found = []
    for top in SCANNED:
        for path in sorted((ROOT / top).rglob("*")):
            if not path.is_file() or "__pycache__" in path.parts or path.suffix.lower() not in (".py", ".typ", ".json", ".spec", ".iss", ".md", ".bat", ".txt"):
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            lines = text.splitlines()
            for number, line in enumerate(lines, 1):
                # a schema's property names the key on one line and says it is retired in its description, on the next two
                if RETIRED.search(line) and not any(SAYS_WHY.search(near) for near in lines[number - 1:number + 2]):
                    found.append(f"{path.relative_to(ROOT).as_posix()}:{number}: {line.strip()[:140]}")
    assert not found, "a retired feature is still named without saying it was retired:\n" + "\n".join(found[:20])


def test_the_window_has_neither_tab_and_no_icon_for_them():
    if str(TOOLS) not in sys.path:
        sys.path.insert(0, str(TOOLS))
    try:
        import chrome
    except ImportError as exc:
        raise conftest.Skip(f"PySide6 is not installed ({exc})")
    import woodcore_gui
    keys = [key for key, _factory in woodcore_gui.TABS]
    grouped = [key for _title, members in woodcore_gui.NAV_GROUPS for key in members]
    for gone in ("tab_rfem", "tab_dsl"):
        assert gone not in keys and gone not in grouped and gone not in chrome.ICONS, gone
    for lang in ("fr", "de", "en"):
        stale = sorted(key for key in woodcore_gui.STRINGS[lang] if key.startswith(("rf_", "dsl_")))
        assert not stale, (lang, stale[:5])


def test_the_archive_holds_both_features_and_stays_out_of_the_way():
    archive = ROOT / "archive"
    for feature, files in (("rfem", ("calc/tools/rfem_tab.py", "calc/rfem_import/import_controller.py", "calc/domains/rfem.py", "lib/rfem.typ",
                                     "schemas/rfem.schema.json", "docs/domain/rfem.md", "tests/test_rfem_tab.py")),
                           ("formules-dsl", ("calc/dsl.py", "calc/tools/dsl_tab.py", "tests/test_dsl.py"))):
        assert (archive / feature / "README.md").is_file(), f"archive/{feature}/ says nothing of what it holds"
        for rel in files:
            assert (archive / feature / rel).is_file(), f"archive/{feature}/{rel} is missing: an archived file keeps the path it had"
            assert not (ROOT / rel).exists(), f"{rel} is archived and still in the program"
    # a bare `pytest` from the repository's root must not collect the archived tests, whose imports no longer resolve
    assert "collect_ignore_glob" in (archive / "conftest.py").read_text(encoding="utf-8")
    # tests/run_tests.py collects tests/test_*.py alone, and the installer takes the program's folders by name
    spec = (ROOT / "packaging" / "woodcore.spec").read_text(encoding="utf-8")
    assert not re.search(r"[\"'/]archive[/\"']", spec), "the installer names the archive"
    site = (ROOT / ".github" / "workflows" / "site.yml").read_text(encoding="utf-8")
    assert '"archive/**"' in site, "a push that changes only the archive rebuilds the site"


def test_a_project_still_naming_rfem_exports_with_a_warning_and_no_rfem_file():
    """REQ-004: the example project keeps its `gui.rfem_models` and `layout.rfem_export` on purpose -- the bench of this test, as the engineer's Musterprojekt names an RFEM model too. The export goes through, says each key is ignored, writes no `data/rfem*`, and removes what an export of 0.116 left there (a copy that would age without saying so)."""
    import notifications
    import project
    here = conftest.project_copy("retired_export")
    # the plans and the fire plans are drawn over backgrounds a copy does not carry, which stops an export: they are not what this test is about
    for folder in (here.plans_dir, here.fire_dir):
        for source in folder.glob("*.json"):
            source.unlink()
    keys = sorted(note.args["key"] for note in here.retired_keys())
    assert keys == ["gui.rfem_models", "layout.rfem_export"], f"the example project no longer names RFEM -- REQ-004 has lost its bench: {keys}"
    here.data_dir.mkdir(parents=True, exist_ok=True)
    (here.data_dir / "rfem.json").write_text("{}", encoding="utf-8")
    (here.data_dir / "rfem").mkdir(exist_ok=True)
    (here.data_dir / "rfem" / "Beispiel-Modell.json").write_text("{}", encoding="utf-8")
    out = subprocess.run(
        [sys.executable, str(ROOT / "calc" / "export_all.py"), "--project", str(here.file)],
        capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=str(ROOT),
        env={k: v for k, v in dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8").items() if k != notifications.STRUCTURED_ENV},   # the sentences, as run by hand
    )
    assert out.returncode == 0, (out.stdout + out.stderr)[-2000:]
    for key in keys:
        assert f"{key} is ignored" in out.stderr, (key, out.stderr[-2000:])
    assert not (here.data_dir / "rfem.json").exists() and not (here.data_dir / "rfem").exists(), "the export left data/rfem* behind"
    assert "removed data/rfem.json" in out.stdout and "removed data/rfem/" in out.stdout, out.stdout[-2000:]
    # the project file is the engineer's: the export never takes a retired key out of it
    again = project.Project.load(here.file)
    assert sorted(note.args["key"] for note in again.retired_keys()) == keys
