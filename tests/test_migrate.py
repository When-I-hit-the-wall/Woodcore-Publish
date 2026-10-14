"""A project laid out as one report, moved into three documents (calc/project_migrate.py, the three document modes, work package 1.3).

The migration moves the engineer's real project on disk one day, so what is held here is less that it gets the layout right -- calc/project.py and calc/documents.py hold what a layout in three documents is -- than that it cannot leave a project half-moved. Four things, in that order. **The plan** reads and never writes, finds everything a migration would move, rewrite and make, and refuses by name what it cannot do: a project already migrated, a report at the top of its project, a place a move would put something where something already is, a path it cannot make follow its target, a window holding the project. **The pieces** that decide whether a migration went right are held on cases made for them: the project file written again in Woodcore's form or edited in place where it is hand-written, Tinymist's settings touched only where they name the old folder, the export and the pages compared modulo the one path allowed to move. **A migration of the example** goes through, is laid out in three documents, prints what it printed, and is undone on request -- refused where the engineer has worked in it since, and keeping what he added. **A failure** at the last step, and one in the middle of the moves, leave the project exactly as it was, the two new documents set aside rather than deleted.

⚠️ Every run works on a copy of tests/projet-exemple in this process's own temporary folder, never on the committed example and never on the engineer's project, which is only planned -- read, and checked to have been read and nothing else. The runs are skipped where Typst or pypdf is missing, the migration comparing compiled pages.
"""

import hashlib
import importlib.util
import json
import os
import re
import shutil
import socket

import conftest
from conftest import Skip

import documents
import project
import project_lock
import project_migrate as pm
import project_template


# --- a copy of the example to migrate ----------------------------------------------------------

def _example(name):
    """The example project laid out as one report -- as it was committed before it was itself migrated, rebuilt from the committed one by tests/fixtures/legacy_example.py -- in a directory of its own, its engine copied in as the tests' own copy of it is, so its engine is current before anything is hashed. A short name: the migration's own folder already goes deep."""
    from fixtures import legacy_example
    work = conftest.tmpdir(name)
    here = legacy_example.build(work / "p", conftest.SAMPLE)
    project.sync_engine(here)
    return here


def _tree(top):
    """Every file under `top` with its SHA-256, and every folder -- what «the project is as it was» is checked by. The archives are left out: the migration's own folder lies there, and is meant to stay."""
    out = {}
    for path in sorted(top.rglob("*")):
        rel = path.relative_to(top).as_posix()
        if rel == "_Archiv" or rel.startswith("_Archiv/") or rel.endswith(project_lock.SUFFIX):
            continue
        out[rel] = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else "folder"
    return out


def _differences(before, after):
    return {
        "gone": sorted(set(before) - set(after))[:8],
        "added": sorted(set(after) - set(before))[:8],
        "changed": sorted(k for k in before if k in after and before[k] != after[k])[:8],
    }


def _guard():
    if not conftest.have_typst():
        raise Skip("typst is not on the path")
    if importlib.util.find_spec("pypdf") is None:
        raise Skip("pypdf is not installed")


def _codes(refusals):
    return {r.code for r in refusals}


def _pages(path):
    from pypdf import PdfReader
    return [re.sub(r"\s+", " ", page.extract_text() or "").strip() for page in PdfReader(str(path)).pages]


# --- the plan ----------------------------------------------------------------------------------

def test_the_plan_of_the_example_reads_and_writes_nothing():
    here = _example("mgp")
    before = _tree(here.root)
    stamp = here.file.stat().st_mtime_ns
    p = pm.plan(here)
    assert _tree(here.root) == before and here.file.stat().st_mtime_ns == stamp, "planning wrote into the project"
    assert not p.refusals, [str(r) for r in p.refusals]
    top, old = here.root, here.report_typ.parent
    assert [(m.source, m.target) for m in p.moves] == [
        (old / "_woodcore", top / "_woodcore"),
        (old / "Images", top / "Images"),
        (old / "config.typ", top / "config.typ"),
        (old / "commands.typ", top / "commands.typ"),
        (old, top / "3_Statischer Bericht"),
    ], "the moves are not the shared things first, in their order, and the report's folder last"
    assert p.language == "de" and p.folders == documents.MODE_FOLDERS["de"]
    assert p.layout == documents.layout_for("de"), "the layout is not the full layout of a new German project"
    assert [c.mode for c in p.creates] == ["cu", "bp"] and all(not c.folder.exists() for c in p.creates)
    changes = {(r.file_new.relative_to(top).as_posix(), c.old, c.new) for r in p.rewrites for c in r.changes}
    assert ("3_Statischer Bericht/Sections/001-einleitung.typ", "../commands.typ", "/commands.typ") in changes
    assert ("3_Statischer Bericht/Sections/001-einleitung.typ", "../Images/Situation.png", "/Images/Situation.png") in changes
    assert ("3_Statischer Bericht/Statischer Rapport.typ", "config.typ", "/config.typ") in changes
    assert not any(c.literal.kind == "include" for r in p.rewrites for c in r.changes), "an include moved with its entry and was rewritten"
    assert p.woodcore_route == "canonical"
    # the example has no .vscode: it is given the template's settings, which state Tinymist's root
    assert p.vscode.created and p.vscode.root_path and p.vscode.output_path is None
    assert p.vscode.path == top / ".vscode" / "settings.json" and not p.vscode.path.exists()
    assert p.vscode.text == pm.TEMPLATE_SETTINGS.read_text(encoding="utf-8") and pm.vscode_root_text(p.vscode.text) is None
    migrated = project.Project(here.file, p.data)
    assert migrated.has_modes and migrated.retired_keys() == here.retired_keys()


def test_a_form_in_the_reports_folder_goes_up_with_what_the_three_share():
    """A report alone written with a form (calc/forms.py) keeps `Template/` beside its config.typ; in three documents the form is shared by all three and lies at the top of the project, so the migration moves it like the pictures -- renamed, never copied or deleted -- and what is already at the top under that name is in the way."""
    here = _example("mgf")
    old = here.report_typ.parent
    (old / "Template").mkdir()
    (old / "Template" / "template.typ").write_text("#let template(doc, lang: \"de\", region: \"CH\") = doc\n", encoding="utf-8")
    p = pm.plan(here)
    assert not p.refusals, [str(r) for r in p.refusals]
    moves = [(m.source, m.target) for m in p.moves]
    assert (old / "Template", here.root / "Template") in moves, moves
    assert moves.index((old / "Template", here.root / "Template")) < moves.index((old, here.root / "3_Statischer Bericht")), "the report's folder moves last"
    (here.root / "Template").mkdir()
    assert "collision" in _codes(pm.plan(here).refusals), "a form already at the top of the project is in the way of the one that moves up"


def test_what_stands_in_the_way_is_refused_by_name():
    here = _example("mgr")
    top = here.root
    assert _codes(pm.check(pm.plan(here))) <= {"no_typst", "no_pypdf"}, "the example itself is refused"

    # a place a move puts something where something already is, and a folder a document would be made in
    (top / "config.typ").write_text("// in the way\n", encoding="utf-8")
    (top / "1_Nutzungsvereinbarung").mkdir()
    p = pm.plan(here)
    collisions = [r for r in p.refusals if r.code == "collision"]
    assert {r.args["path"] for r in collisions} == {"config.typ", "1_Nutzungsvereinbarung"}, [str(r) for r in p.refusals]
    try:
        pm.run(here, skip_data=True, archive=False, log=None)
    except pm.MigrationError as exc:
        assert exc.code == "refused" and "collision" in _codes(exc.refusals) and exc.workspace is None
    else:
        raise AssertionError("a migration that stands refused ran")
    assert not (top / "_Archiv").exists(), "a refused migration wrote its folder"
    (top / "config.typ").unlink()
    (top / "1_Nutzungsvereinbarung").rmdir()

    # a path of the report that cannot be made to follow its target
    section = here.report_typ.parent / "Sections" / "001-einleitung.typ"
    original = section.read_bytes()
    section.write_bytes(original + b'#image("../Images/not-there.png")\n')
    p = pm.plan(here)
    assert [r.args["literal"] for r in p.refusals if r.code == "unrewritable"] == ["../Images/not-there.png"], [str(r) for r in p.refusals]
    section.write_bytes(original)

    # folder names refused, or taken by what the three documents share
    assert "bad_names" in _codes(pm.plan(here, names=["Images", "2_Projektbasis", "3_Bericht"]).refusals)
    assert "bad_names" in _codes(pm.plan(here, names=["a/b", "2_Projektbasis", "3_Bericht"]).refusals)
    assert "bad_names" in _codes(pm.plan(here, names=["same", "same", "3_Bericht"]).refusals)
    assert "bad_language" in _codes(pm.plan(here, language="it").refusals)

    # the project held by another machine's window -- and by the window that asked for the migration, which is no refusal
    lock = project_lock.lock_path(here)
    lock.write_text(json.dumps({"user": "someone", "host": "another-machine", "pid": 1, "since": "2026-09-30T08:00:00"}), encoding="utf-8")
    assert "locked" in _codes(pm.check(pm.plan(here)))
    parent = os.getppid()
    lock.write_text(json.dumps({"user": "me", "host": socket.gethostname(), "pid": parent, "since": "now"}), encoding="utf-8")
    if project_lock._alive(parent):
        assert "locked" in _codes(pm.check(pm.plan(here))), "another live process's lock was taken for this one's"
        assert "locked" not in _codes(pm.check(pm.plan(here), lock_owner=parent)), "the window's own lock refused its migration"
    lock.unlink()

    # an engine edited by hand is replaced only when the migration is told to
    engine_file = here.generated_dir / "lib" / "calc-engine.typ"
    os.chmod(engine_file, 0o666)
    engine_file.write_bytes(engine_file.read_bytes() + b"\n// edited\n")
    assert "engine_asked" in _codes(pm.check(pm.plan(here)))
    assert "engine_asked" not in _codes(pm.check(pm.plan(here), update_engine=True))


def test_a_project_already_migrated_or_with_its_report_at_the_top_is_refused():
    d = conftest.tmpdir("mgt")
    modes = d / "modes"
    modes.mkdir()
    project.write(modes / "M.woodcore", "M", layout=documents.layout_for("fr"))
    assert _codes(pm.plan(modes / "M.woodcore").refusals) == {"already_modes"}
    top = d / "top"
    top.mkdir()
    (top / "Statischer Rapport.typ").write_text("= Bericht\n", encoding="utf-8")
    project.write(top / "T.woodcore", "T", layout={"report": "Statischer Rapport.typ", "pdf": "Statischer Rapport.pdf", "generated": "_woodcore"})
    assert _codes(pm.plan(top / "T.woodcore").refusals) == {"report_at_top"}
    inside = d / "inside"
    (inside / "R").mkdir(parents=True)
    (inside / "R" / "Statischer Rapport.typ").write_text("= Bericht\n", encoding="utf-8")
    project.write(inside / "I.woodcore", "I", layout={"report": "R/Statischer Rapport.typ", "pdf": "R/Statischer Rapport.pdf",
                                                      "generated": "R/_woodcore", "sources": "R/Quellen"})
    assert _codes(pm.plan(inside / "I.woodcore").refusals) == {"sources_inside"}


# --- the pieces --------------------------------------------------------------------------------

LAYOUT = documents.layout_for("de")


def test_a_project_file_in_woodcores_form_is_written_again_in_it_keeping_its_line_endings():
    data = {"schema_version": "1.0", "format": "woodcore-project", "name": "G", "author": "A",
            "gui": {"empty_folders": {"tab_plan": ["x"]}, "rfem_models": ["Bericht/RFEM-Export/m.xlsx", "elsewhere.xlsx"]}}
    raw = (json.dumps(data, ensure_ascii=False, indent=2) + "\n").replace("\n", "\r\n")
    text, route = pm.woodcore_text(raw, LAYOUT)
    assert route == "canonical"
    assert "\r\n" in text and "\n" not in text.replace("\r\n", ""), "the line endings were not kept"
    written = json.loads(text)
    assert written["layout"] == LAYOUT and list(written)[-1] == "layout"
    # a key retired in 0.117 (project.RETIRED_KEYS) is kept as it was: the migration no longer makes it follow anything
    assert written["gui"] == data["gui"]
    assert {k: v for k, v in written.items() if k not in ("layout", "gui")} == {k: v for k, v in data.items() if k != "gui"}


def test_a_hand_written_project_file_is_edited_in_place_and_never_reserialised():
    raw = (
        '{\n'
        '    "schema_version" : "1.0",\n'
        '    "format": "woodcore-project",\n'
        '    "name":   "Handgeschrieben",\n'
        '    "katalog": {"rfem_models": ["Bericht/RFEM-Export/M\\u00e4tzli.xlsx"]},\n'
        '    "layout": {"sources": "Quellen"}\n'
        '}'
    )
    layout = dict(LAYOUT, sources="Quellen")
    text, route = pm.woodcore_text(raw, layout)
    assert route == "textual"
    for line in ('    "schema_version" : "1.0",\n', '    "name":   "Handgeschrieben",\n'):
        assert line in text, f"{line!r} was not kept as it was written"
    assert '    "katalog": {"rfem_models": ["Bericht/RFEM-Export/M\\u00e4tzli.xlsx"]},\n' in text, "a member the migration does not touch was not kept byte for byte"
    written = json.loads(text)
    assert written["layout"] == layout and written["katalog"]["rfem_models"] == ["Bericht/RFEM-Export/Mätzli.xlsx"]
    assert not text.endswith("\n"), "a file that ended without a newline was given one"
    # no layout at all: appended after the last member, at the file's own indentation
    bare = '{\n\t"schema_version": "1.0",\n\t"format": "woodcore-project",\n\t"name": "B"\n}\n'
    text, route = pm.woodcore_text(bare, LAYOUT)
    assert route == "textual" and json.loads(text)["layout"] == LAYOUT
    assert '\t"name": "B",\n\t"layout": {\n\t\t"typst_root": "."' in text, text


def test_tinymists_settings_follow_the_folder_only_where_they_name_it():
    raw = (
        '{\n'
        '  // "tinymist.outputPath": "${workspaceFolder}/Statischer Bericht (typst)/$name",\n'
        '  "tinymist.outputPath": "${workspaceFolder}/Statischer Bericht (typst)/$name",\n'
        '  "files.associations": {"*.typ": "typst"},\n'
        '}\n'
    )
    text, (old, new) = pm.vscode_text(raw, "Statischer Bericht (typst)", "3_Statischer Bericht")
    assert old == "${workspaceFolder}/Statischer Bericht (typst)/$name" and new == "${workspaceFolder}/3_Statischer Bericht/$name"
    assert text == raw.replace('  "tinymist.outputPath": "${workspaceFolder}/Statischer Bericht (typst)/$name"',
                               '  "tinymist.outputPath": "${workspaceFolder}/3_Statischer Bericht/$name"'), "more than the setting changed"
    assert pm.vscode_text('{\n  "tinymist.outputPath": "$dir/../$name",\n}\n', "Statischer Bericht (typst)", "3_Statischer Bericht") is None
    assert pm.vscode_text('{\n  // "tinymist.outputPath": "Statischer Bericht (typst)/x",\n}\n', "Statischer Bericht (typst)", "3_x") is None
    assert pm.vscode_text('{\n  "tinymist.outputPath": "Statischer Bericht (typst) alt/x",\n}\n', "Statischer Bericht (typst)", "3_x") is None
    for name in ("templates/projet/.vscode/settings.json", "tests/projet-exemple/.vscode/settings.json"):
        path = conftest.ROOT / name
        if path.is_file():
            assert pm.vscode_text(path.read_text(encoding="utf-8"), "Statischer Bericht (typst)", "3_Statischer Bericht") is None, name


def test_tinymists_root_is_stated_as_a_line_of_its_own():
    """The engineer's safety net (30.09.2026): Tinymist told that the Typst root is the folder VS Code was opened on -- `"tinymist.rootPath": "${workspaceFolder}"`, which the VS Code extension substitutes before Tinymist reads it, Tinymist refusing a relative root. Inserted as a line of its own in a settings.json the engineer wrote, with its comments and its trailing comma, every other byte kept; a root he states already, whatever it is, left alone; a file that does not read as JSONC left alone too, with a note -- a safety net missing is no reason to refuse a migration."""
    template = pm.TEMPLATE_SETTINGS.read_text(encoding="utf-8")
    assert pm.vscode_root_text(template) is None, "the template does not state the root a new project is compiled from"
    assert json.loads(pm.jsonc_plain(template))[pm.ROOT_PATH_KEY] == "${workspaceFolder}"
    # the engineer's own shape: comments, a trailing comma, CRLF
    raw = ('{\r\n'
           '  // No "tinymist.outputPath": the PDF beside its .typ.\r\n'
           '  // "tinymist.rootPath": "commented out, not a setting",\r\n'
           '  "files.associations": {\r\n    "*.typ": "typst"\r\n  },\r\n\r\n'
           '  "cSpell.language": "en,de",\r\n'
           '}\r\n')
    text = pm.vscode_root_text(raw)
    assert text.startswith("{") and text.endswith(raw[1:]), "more than the lines inserted changed"
    added = text[1:len(text) - len(raw) + 1]
    assert added == "\r\n  " + pm.ROOT_PATH_COMMENT + '\r\n  "tinymist.rootPath": "${workspaceFolder}",\r\n', repr(added)
    assert "\n" not in text.replace("\r\n", ""), "a line ending other than the file's own"
    assert json.loads(pm.jsonc_plain(text)) == {"tinymist.rootPath": "${workspaceFolder}", "files.associations": {"*.typ": "typst"}, "cSpell.language": "en,de"}
    # a tab-indented file keeps its tab; a file on one line and an empty object come out as valid JSON
    assert '\n\t"tinymist.rootPath": "${workspaceFolder}",' in pm.vscode_root_text('{\n\t"a": 1\n}\n')
    for one in ('{"a": 1}', "{}", "// head\n{ /* why */ }\n"):
        assert json.loads(pm.jsonc_plain(pm.vscode_root_text(one)))["tinymist.rootPath"] == "${workspaceFolder}", one
    # a root already stated is the engineer's, whatever it says
    for stated in ('{\n  "tinymist.rootPath": "C:/Projekte/Halle",\n}\n', '{\n  "tinymist.rootPath": null\n}\n'):
        assert pm.vscode_root_text(stated) is None, stated
    for bad in ("[1, 2]", '{"a": ', "{ /* never closed", '{"a": "never closed}'):
        try:
            pm.vscode_root_text(bad)
        except ValueError:
            pass
        else:
            raise AssertionError(f"{bad!r} was read as settings")
    # what the plan does with it: the output that followed the folder and the root stated, in one text; an unreadable file left as it is, with a note
    d = conftest.tmpdir("mgvs")
    settings = d / ".vscode" / "settings.json"
    settings.parent.mkdir()
    settings.write_text('{\n  "tinymist.outputPath": "${workspaceFolder}/Statischer Bericht (typst)/$name",\n}\n', encoding="utf-8")
    notes = []
    planned = pm._vscode_plan(settings, "Statischer Bericht (typst)", "3_Statischer Bericht", notes)
    assert not planned.created and planned.root_path and planned.output_path[1] == "${workspaceFolder}/3_Statischer Bericht/$name" and not notes
    assert json.loads(pm.jsonc_plain(planned.text)) == {"tinymist.rootPath": "${workspaceFolder}", "tinymist.outputPath": "${workspaceFolder}/3_Statischer Bericht/$name"}
    settings.write_text('{\n  "tinymist.rootPath": "${workspaceFolder}",\n}\n', encoding="utf-8")
    assert pm._vscode_plan(settings, "Statischer Bericht (typst)", "3_x", notes) is None and not notes, "a file stating its root already was touched"
    settings.write_text('{\n  "a": ', encoding="utf-8")
    assert pm._vscode_plan(settings, "Statischer Bericht (typst)", "3_x", notes) is None
    assert notes and "tinymist.rootPath" in notes[0], notes


def test_the_export_is_compared_byte_for_byte_but_for_the_journals_of_the_new_documents():
    d = conftest.tmpdir("mgd")
    ref, cur = d / "ref", d / "cur"
    for top in (ref, cur):
        (top / "statics").mkdir(parents=True)
        (top / "statics.json").write_text('{"models": {}}', encoding="utf-8")
        (top / "statics" / "m.svg").write_text("<svg/>", encoding="utf-8")
        (top / "plan.pdf").write_bytes(b"%PDF same")
    assert pm.compare_data(ref, cur) == []
    (cur / "journal-cu.json").write_text("{}", encoding="utf-8")
    assert pm.compare_data(ref, cur, {"journal-cu.json"}) == []
    assert any("is exported after" in d_ for d_ in pm.compare_data(ref, cur))
    (cur / "plan.pdf").write_bytes(b"%PDF other")
    assert pm.compare_data(ref, cur, {"journal-cu.json"}) == ["data/plan.pdf differs from the export made before the migration"]
    # a path written into the export is no longer allowed to have moved: the one that could, an RFEM export's, went with the RFEM import in 0.117
    (cur / "plan.pdf").write_bytes(b"%PDF same")
    (cur / "statics.json").write_text('{"models": {"x": {}}}', encoding="utf-8")
    assert pm.compare_data(ref, cur, {"journal-cu.json"}) == ["data/statics.json differs from the export made before the migration"]


def test_the_pages_are_compared_modulo_white_and_the_day():
    reference = {"pages": ["Bericht\n01.10.2026", "Quelle:  Positionen"], "outline": [{"title": "Einleitung", "page": 2, "level": 1}], "attachment": {"domains": {"": {"x": {"source": "python:x"}}}}}
    current = {"pages": ["Bericht 02.10.2026", "Quelle: Positionen"], "outline": [{"title": "Einleitung", "page": 2, "level": 1}], "attachment": {"domains": {"": {"x": {"source": "python:x"}}}}}
    assert pm.compare_pdf(reference, current, ["01.10.2026", "02.10.2026"]) == []
    assert pm.compare_pdf(reference, current, ["01.10.2026"]) != [], "a date other than the compile's was taken for it"
    assert pm.compare_pdf(reference, dict(current, pages=current["pages"][:1]), ["01.10.2026", "02.10.2026"])[0].startswith("the report has 1 page")
    assert pm.compare_pdf(reference, dict(current, attachment=None), ["01.10.2026", "02.10.2026"]) != []
    assert pm.compare_pdf(reference, dict(current, outline=[]), ["01.10.2026", "02.10.2026"]) != []


# --- a migration of the example ----------------------------------------------------------------

def test_a_migration_goes_through_and_is_undone_on_request():
    _guard()
    here = _example("mg1")
    top = here.root
    # a key of the window's own, which the migration must carry through untouched
    here = project.set_empty_folders(here, "tab_plan", ["Leer"])
    before = _tree(top)
    woodcore = here.file.read_bytes()
    old_rs = here.report_typ.parent

    outcome = pm.run(here, skip_data=True, archive=False, log=None)
    # the title page the two new documents set, Standard's, written at the top where the report carried none -- the report keeping the title page its entry writes
    assert outcome["ok"] and outcome["created"] == [project.TITLE_FILE, "1_Nutzungsvereinbarung", "2_Projektbasis"]
    migrated = project.Project.load(here.file)
    assert migrated.has_modes and migrated.modes == project.MODES
    assert migrated.layout == documents.layout_for("de")
    for mode in project.MODES:
        assert migrated.document_typ(mode).is_file() and migrated.document_pdf(mode).is_file(), f"{mode}: no entry or no PDF"
    assert not old_rs.exists() and (top / "_woodcore" / "data").is_dir() and (top / "config.typ").is_file()
    assert (top / project.TITLE_FILE).read_bytes() == project_template.standard_title().read_bytes()
    assert "project-info()" in migrated.report_typ.read_text(encoding="utf-8"), "the report's own title page was rewritten"
    for mode in ("cu", "bp"):
        assert (migrated.data_dir / documents.JOURNAL_FILES[mode]).is_file(), f"no export journal for {mode}"
    # the RFEM keys retired in 0.117 (project.RETIRED_KEYS) are kept as the project file had them, and said
    assert migrated.empty_folders("tab_plan") == ["Leer"] and migrated.gui().get("rfem_models") == here.gui().get("rfem_models")
    assert {k: migrated.data.get(k) for k in ("name", "company", "author")} == {k: here.data.get(k) for k in ("name", "company", "author")}
    section = migrated.document_dir("rs") / "Sections" / "001-einleitung.typ"
    assert section.read_text(encoding="utf-8").startswith('#import "/commands.typ": *'), "a section still imports from its folder"
    assert not project_lock.lock_path(here).exists(), "the migration left its lock behind"
    settings = top / ".vscode" / "settings.json"
    assert settings.is_file() and not (old_rs / ".vscode").exists(), "the project that had no .vscode was not given the template's"
    assert json.loads(pm.jsonc_plain(settings.read_text(encoding="utf-8")))[pm.ROOT_PATH_KEY] == pm.ROOT_PATH_VALUE
    ws = top / outcome["workspace"]
    log = json.loads((ws / pm.LOG_FILE).read_text(encoding="utf-8"))
    assert log["state"] == "done" and all(m["state"] == "done" for m in log["moves"])
    assert json.loads((ws / pm.RESULT_FILE).read_text(encoding="utf-8"))["ok"] is True
    # the report prints what it printed -- read here apart from the migration's own comparison
    today = re.compile(r"\d{2}\.\d{2}\.\d{4}")
    ref_pages = [today.sub("<day>", t) for t in _pages(ws / pm.REFERENCE_DIR / "reference.pdf")]
    new_pages = [today.sub("<day>", t) for t in _pages(migrated.document_pdf("rs"))]
    assert new_pages == ref_pages, "the migrated report prints something else"
    assert "Tinymist" in outcome["reminder"] and "3_Statischer Bericht/Statischer Rapport.typ" in outcome["reminder"]

    # undone on request -- but not over the engineer's work
    rewritten = migrated.document_dir("rs") / "Sections" / "003-baustoffe.typ"
    kept = rewritten.read_bytes()
    rewritten.write_bytes(kept + b"\n// the engineer's own line\n")
    try:
        pm.rollback(ws, log=None)
    except pm.MigrationError as exc:
        assert exc.code == "rollback_refused" and "edited_since" in _codes(exc.refusals)
    else:
        raise AssertionError("a rollback went over a file edited since the migration")
    rewritten.write_bytes(kept)
    added = migrated.document_dir("rs") / "Sections" / "099-neu.typ"
    added.write_text('#import "/commands.typ": *\n\n= Neu\n', encoding="utf-8")
    result = pm.rollback(ws, log=None)
    assert result["ok"] and result["kept"] == ["Statischer Bericht (typst)/Sections/099-neu.typ"]
    assert (old_rs / "Sections" / "099-neu.typ").is_file(), "what the engineer added since was not kept"
    (old_rs / "Sections" / "099-neu.typ").unlink()
    assert _tree(top) == before, _differences(before, _tree(top))
    assert here.file.read_bytes() == woodcore, "the project file is not the bytes it was"
    assert (ws / pm.ROLLED_BACK_DIR / "1_Nutzungsvereinbarung").is_dir() and (ws / pm.ROLLED_BACK_DIR / "2_Projektbasis").is_dir()
    assert (ws / pm.ROLLED_BACK_DIR / project.TITLE_FILE).is_file() and not (top / project.TITLE_FILE).exists(), "the title page the migration wrote was not set aside"
    assert not (top / ".vscode").exists() and (ws / pm.ROLLED_BACK_DIR / ".vscode" / "settings.json").is_file(), "the settings the migration made were not set aside"
    try:
        pm.rollback(ws, log=None)
    except pm.MigrationError as exc:
        assert exc.code == "rollback_refused"
    else:
        raise AssertionError("a migration was undone twice")


def test_a_failure_at_the_proof_undoes_everything():
    """Everything, the reference's own engine update included: the example starts here with no engine copy, as the committed one has none, so the reference step writes one -- and the backup, taken before it, is what the undo gives back."""
    _guard()
    here = _example("mg2")
    top = here.root
    for name in ("lib", "calc", project.ENGINE_STAMP):
        conftest._wipe(here.generated_dir / name) if (here.generated_dir / name).is_dir() else (here.generated_dir / name).unlink()
    assert project.engine_state(here)[0] == "absent"
    # commands.typ imports an engine that is not there yet: a note while the reference is still to write it, a refusal once it should have
    assert not pm.plan(here).refusals and any("names nothing yet" in n for n in pm.plan(here).notes)
    assert "unrewritable" in _codes(pm.plan(here, strict=True).refusals)
    before = _tree(top)
    woodcore = here.file.read_bytes()
    planted = pm.compare_pdf
    pm.compare_pdf = lambda *args, **kwargs: ["a difference planted by the test"]
    try:
        pm.run(here, skip_data=True, archive=False, log=None)
    except pm.MigrationError as exc:
        assert exc.code == "failed" and exc.diffs == ["a difference planted by the test"] and exc.workspace is not None
        ws = exc.workspace
    else:
        raise AssertionError("a migration whose proof failed went through")
    finally:
        pm.compare_pdf = planted
    assert _tree(top) == before, _differences(before, _tree(top))
    assert here.file.read_bytes() == woodcore, "the project file is not the bytes it was"
    assert not project.Project.load(here.file).has_modes
    for folder in ("1_Nutzungsvereinbarung", "2_Projektbasis"):
        assert (ws / pm.ROLLED_BACK_DIR / folder).is_dir() and not (top / folder).exists(), f"{folder} was not set aside"
    result = json.loads((ws / pm.RESULT_FILE).read_text(encoding="utf-8"))
    assert result["ok"] is False and result["rolled_back"] is True and result["diffs"] == ["a difference planted by the test"]
    assert json.loads((ws / pm.LOG_FILE).read_text(encoding="utf-8"))["state"] == "rolled-back"
    assert not project_lock.lock_path(here).exists()


def test_a_failure_in_the_middle_of_the_moves_undoes_the_moves_done():
    _guard()
    here = _example("mg3")
    top = here.root
    before = _tree(top)
    woodcore = here.file.read_bytes()
    original, calls = pm._rename, []

    def third_fails(source, target):
        calls.append(source)
        if len(calls) == 3:
            raise PermissionError(f"planted: {source} is held by another program")
        original(source, target)

    pm._rename = third_fails
    try:
        pm.run(here, skip_data=True, archive=False, log=None)
    except pm.MigrationError as exc:
        assert exc.code == "failed" and "planted" in str(exc)
        ws = exc.workspace
    else:
        raise AssertionError("a migration whose third move failed went through")
    finally:
        pm._rename = original
    assert _tree(top) == before, _differences(before, _tree(top))
    assert here.file.read_bytes() == woodcore
    log = json.loads((ws / pm.LOG_FILE).read_text(encoding="utf-8"))
    assert [m["state"] for m in log["moves"]][:3] == ["done", "done", "moving"], log["moves"]


# --- the command, and the engineer's project -----------------------------------------------------

def test_the_command_reads_its_arguments_and_a_dry_run_writes_nothing():
    here = _example("mgc")
    before = _tree(here.root)
    assert pm.command(["--project", str(here.file), "--dry-run"]) == 0
    assert _tree(here.root) == before and not (here.root / "_Archiv").exists()
    assert pm.command(["--names", "only-one"]) == 2
    assert pm.command(["--rollback", str(here.root / "_Archiv" / "migration-none")]) == 1


def test_the_engineers_project_is_planned_and_left_as_it_is():
    """The engineer's own project, planned and never migrated -- which is WP1.8's, on his word. What is held is that planning it reads and writes nothing, and that what it would do is what the layout says: the report's shared things up, and the report's folder last."""
    real = conftest.real_project()
    if real.has_modes:
        raise Skip("the engineer's project is laid out in three documents already")

    def snapshot():
        out = {}
        for folder, dirs, files in os.walk(real.root):
            for name in dirs + files:
                path = os.path.join(folder, name)
                st = os.stat(path)
                out[path] = (st.st_size, st.st_mtime_ns)
        return out

    before = snapshot()
    p = pm.plan(real)
    pm.check(p)
    pm.describe(p)
    after = snapshot()
    touched = sorted(k for k in set(before) | set(after) if before.get(k) != after.get(k))
    assert not touched, f"planning the engineer's project touched it: {[(k, before.get(k), after.get(k)) for k in touched[:6]]}"
    old = real.report_typ.parent
    assert p.moves and p.moves[-1].source == old and p.moves[-1].target.parent == real.root
    # an RFEM-Export/ folder is no longer one of the shared things (the RFEM import was retired in 0.117): it stays in the report's folder and moves with it
    assert not any(m.source == old / "RFEM-Export" for m in p.moves)
