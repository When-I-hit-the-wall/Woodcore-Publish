"""Project templates (calc/templates.py, calc/project_template.py, calc/cli.py; v0.94, docs/conventions/build-and-release.md §12).

A new project is a template copied: Standard (templates/projet/, read only), one of the engineer's (usersettings.templates_dir) or one of the office's (the settings' shared folder), its template.json saying its name, its languages, its layout and its people. These hold the three places, what a template.json may say and what it may not, a project made from a template -- laid out in three documents whatever the template's shape, its languages written, its layout stated, its skeleton copied without template.json, its pictures moved up with the paths that name them --, «Enregistrer ce projet comme modèle» leaving out the export, the drawings, the archives, the workbooks, a PDF and a picture nothing names -- and, from three documents, whatever else lies at the top of the project --, the sections added, renamed, moved and deleted with the report's #include lines following, and `woodcore-cli new --template`.

Every template a check writes goes into this process's own folder (`WOODCORE_TEMPLATES`), never the engineer's.
"""

import contextlib
import json
import os
import struct
import subprocess
import sys
import zlib

import conftest
from conftest import CALC

import documents
import project
import project_template
import templates

sys.path.insert(0, str(CALC / "tools"))
import build_reference  # noqa: E402  -- the one place the import line a section starts with is spelt (docs/typst/reference-workbook.md §10ter)


@contextlib.contextmanager
def _own_templates(name):
    """The engineer's templates redirected into a clean folder of this process for the length of a check."""
    folder = conftest.tmpdir(name)
    saved = os.environ.get("WOODCORE_TEMPLATES")
    os.environ["WOODCORE_TEMPLATES"] = str(folder / "user")
    try:
        yield folder
    finally:
        if saved is None:
            os.environ.pop("WOODCORE_TEMPLATES", None)
        else:
            os.environ["WOODCORE_TEMPLATES"] = saved


def _holzbau(settings=None):
    """A template of the engineer's, from Standard: French, its report in a folder of its own, its drawings in another, an author of its own."""
    template = templates.duplicate(templates.standard(), "Holzbau", "user", settings or {})
    return templates.update(template, description="Rapports de bois", document_language="fr", report_language="fr", author="L. Exempel",
                            layout={"report": "Bericht/Rapport.typ", "sources": "Daten", "archives": ""})


# --- the three places --------------------------------------------------------------------------

def _png():
    """A PNG of one white pixel, whole and valid, for a check that compiles a picture."""
    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(b"\x00\xff\xff\xff")) + chunk(b"IEND", b""))


def test_standard_is_builtin_read_only_and_says_what_its_files_say():
    standard = templates.standard()
    assert standard.ref == templates.STANDARD and standard.name == "Standard" and standard.read_only and not standard.error, standard.error
    assert standard.layout == project.DEFAULT_LAYOUT, "Standard keeps the layout every project was made with until v0.94"
    assert not standard.document_language and not standard.report_language, "Standard follows the settings' report language"
    assert templates.read_languages(standard.report) == ("de", "de")
    # Standard stays a report alone on disk, though every project made from it is laid out in three documents: its folder is what `report_folder_offered` measures a template's own against (below), and the shared files move up as a project is made
    assert not standard.has_modes and standard.modes == project.REPORT_ONLY and standard.entries == [standard.report]
    assert standard.config == standard.report_dir / "config.typ" and standard.config.is_file()
    assert not (standard.folder / "config.typ").exists() and (standard.folder / "Statischer Bericht (typst)" / "commands.typ").is_file()
    for lang in ("fr", "de", "en"):
        assert standard.description(lang), f"Standard has no description in {lang}"
    try:
        templates.delete(standard)
    except templates.TemplateError:
        pass
    else:
        raise AssertionError("Standard was deleted")
    try:
        templates.update(standard, name="Autre")
    except templates.TemplateError:
        pass
    else:
        raise AssertionError("Standard was written")


def test_the_three_places_are_listed_builtin_first_and_a_broken_one_says_why():
    with _own_templates("templates_places") as base:
        shared = base / "shared"
        settings = {"templates": {"shared_folder": str(shared)}}
        mine = templates.duplicate(templates.standard(), "Holzbau", "user", settings)
        office = templates.duplicate(templates.standard(), "Bureau", "shared", settings)
        (shared / "no template here").mkdir()
        broken = shared / "Kaputt"
        broken.mkdir()
        (broken / templates.FILE).write_text('{"schema_version": "1.0", "format": "woodcore-template"}', encoding="utf-8")
        found = templates.list_templates(settings)
        assert [t.ref for t in found] == ["builtin:projet", "user:Holzbau", "shared:Bureau", "shared:Kaputt"], [t.ref for t in found]
        assert mine.place == "user" and mine.folder.parent == base / "user"
        assert office.place == "shared" and office.folder.parent == shared
        assert found[-1].error and "name" in found[-1].error, found[-1].error
        assert not mine.description("fr"), "a copy of Standard kept Standard's description"
        # without a shared folder, the office's are not there, and a template cannot be written into it
        assert [t.ref for t in templates.list_templates({})] == ["builtin:projet", "user:Holzbau"]
        try:
            templates.duplicate(mine, "Ailleurs", "shared", {})
        except templates.TemplateError as exc:
            assert "shared" in str(exc)
        else:
            raise AssertionError("a template was written into a shared folder nobody named")


def test_a_template_is_found_by_its_reference_its_folder_or_its_name():
    with _own_templates("templates_find") as base:
        settings = {"templates": {"shared_folder": str(base / "shared")}}
        mine = templates.duplicate(templates.standard(), "Holzbau", "user", settings)
        templates.update(mine, name="Holzbau Nord")
        office = templates.duplicate(templates.standard(), "Holzbau", "shared", settings)
        assert templates.find("Standard", settings).ref == templates.STANDARD
        assert templates.find("builtin:projet", settings).ref == templates.STANDARD
        assert templates.find("holzbau nord", settings).ref == "user:Holzbau", "a name is found, whatever its case"
        assert templates.find("Holzbau", settings).ref == "user:Holzbau", "the engineer's own first, then the office's"
        assert templates.find("shared:Holzbau", settings).ref == office.ref
        try:
            templates.find("Brücke", settings)
        except templates.TemplateError as exc:
            assert "Standard" in str(exc) and "Holzbau Nord" in str(exc), exc
        else:
            raise AssertionError("a template nobody made was found")
        assert templates.default_template({"templates": {"default": "user:Holzbau"}}).ref == "user:Holzbau"
        assert templates.default_template({"templates": {"default": "user:Weg"}}).ref == templates.STANDARD, "a default that is gone falls back on Standard"
        for name in ("Standard", "  standard "):
            try:
                templates.duplicate(templates.standard(), name, "user", settings)
            except templates.TemplateError:
                pass
            else:
                raise AssertionError(f"a template of the engineer's was named {name!r}, the builtin one's name")


def test_what_a_template_json_may_not_say():
    with _own_templates("templates_check"):
        good = templates.duplicate(templates.standard(), "Prüfung", "user", {})
        meta = dict(good.meta)
        wrong = {
            "schema_version": dict(meta, schema_version="2.0"),
            "format": dict(meta, format="woodcore-project"),
            "name": {k: v for k, v in meta.items() if k != "name"},
            "language": dict(meta, report_language="it"),
            "leaves": dict(meta, layout={"sources": "../anderswo"}),
            "export outside the report": dict(meta, layout={"generated": "_woodcore"}),
            "no entry file": dict(meta, layout={"report": "Bericht/Rapport.typ"}),
            "a document's key without the root": dict(meta, layout={"images": "Images"}),
        }
        for what, bad in wrong.items():
            (good.folder / templates.FILE).write_text(json.dumps(bad), encoding="utf-8")
            read = templates.read(good.folder, "user")
            assert read.error, f"a template.json whose {what} is wrong was read as sound"
        # a language stated, and a config.typ with no doc-lang line to write it into
        (good.folder / templates.FILE).write_text(json.dumps(dict(meta, document_language="fr")), encoding="utf-8")
        config = good.config
        config.write_text(config.read_text(encoding="utf-8").replace("#let doc-lang", "#let dok-sprache"), encoding="utf-8")
        assert "doc-lang" in templates.read(good.folder, "user").error


# --- a project made from a template ---------------------------------------------------------------

def test_a_project_made_from_a_template_takes_its_languages_layout_and_skeleton():
    with _own_templates("templates_create") as base:
        template = _holzbau()
        assert not template.error, template.error
        assert template.layout["report"] == "Bericht/Rapport.typ" and template.layout["generated"] == "Bericht/_woodcore" and template.layout["pdf"] == "Bericht/Rapport.pdf"
        assert template.report.is_file() and not (template.folder / "Statischer Bericht (typst)").exists(), "the report was not moved in the skeleton"
        assert templates.read_languages(template.report) == ("fr", "fr"), "the template's languages are not in its own files"
        document, report = templates.languages_for(template, {})
        here = project_template.create(base / "Halle", "Halle", template=template, document_language=document, report_language=report, author="L. Exempel")
        data = json.loads(here.file.read_text(encoding="utf-8"))
        # laid out in three documents: the report in the folder the template names -- it means it --, the two others in the project's language, the template's own sources kept
        assert data["layout"] == {
            "typst_root": ".", "report": "Bericht/Rapport.typ", "pdf": "Bericht/Rapport.pdf",
            "report_cu": "1_Convention d'utilisation/Convention d'utilisation.typ", "pdf_cu": "1_Convention d'utilisation/Convention d'utilisation.pdf",
            "report_bp": "2_Base de projet/Base de projet.typ", "pdf_bp": "2_Base de projet/Base de projet.pdf",
            "generated": "_woodcore", "images": "Images", "sources": "Daten", "archives": "_Archiv"}, data
        assert here.report_typ == (base / "Halle" / "Bericht" / "Rapport.typ").resolve() and here.report_typ.is_file()
        for mode in project.MODES:
            assert templates.read_languages(here.document_typ(mode)) == ("fr", "fr"), mode
        assert not (here.root / templates.FILE).exists(), "template.json was copied into the project"
        for sub in project.SOURCE_FOLDERS:
            assert (here.root / "Daten" / sub).is_dir(), sub
        assert (here.root / "_Archiv").is_dir() and (here.root / "Images").is_dir() and here.config_typ.is_file()
        assert project.engine_state(here)[0] == "current" and (here.data_dir / "project.json").is_file(), "the engine and the seed follow the template's layout"
        assert here.detail("author") == "L. Exempel"


def test_standard_is_the_neutral_form_and_the_standard_contents_and_a_language_is_written_only_where_it_differs():
    """Standard no longer makes a report by itself (the engineer's decision of 06.10.2026): a project made from it is the neutral form -- `Template/`, title.typ, a config.typ that keeps the language -- and the report is the builtin content template `rs/standard`, its entry file and sections written as that template has them, in the project's language."""
    import doc_templates
    import forms
    with _own_templates("templates_standard") as base:
        here = project_template.create(base / "Eins", "Eins", template=templates.STANDARD, document_language="de", report_language="de")
        assert here.layout == documents.layout_for("de") and json.loads(here.file.read_text(encoding="utf-8"))["layout"] == here.layout
        assert forms.current(here).ref == "builtin:neutral" and forms.is_form_config(here.config_typ)
        assert here.config_typ.read_text(encoding="utf-8") == forms.config_text("de", "CH"), "config.typ is not the form's, written for the language"
        assert here.title_typ.read_bytes() == forms.default().title_typ.read_bytes()
        content = doc_templates.find("builtin:rs/standard").language_dir("de")
        assert here.report_typ.read_bytes() == (content / here.report_typ.name).read_bytes(), "the report's entry is not the content template's"
        assert sorted(p.name for p in (here.report_typ.parent / "Sections").glob("*.typ")) == sorted(p.name for p in (content / "Sections").glob("*.typ"))
        assert not list(here.archives_dir.glob("*-forme")), "a new project has no old form to keep"
        french = project_template.create(base / "Deux", "Deux", document_language="fr", report_language="en")
        for mode in project.MODES:
            assert templates.read_languages(french.document_typ(mode)) == ("fr", "en"), mode
        assert french.config_typ.read_text(encoding="utf-8") == forms.config_text("fr", "CH"), "config.typ changed beyond its language"
        # one language given, the other the template's own: the two documents beside the report print the engine's words in the report's
        mixed = project_template.create(base / "Drei", "Drei", document_language="fr")
        assert [templates.read_languages(mixed.document_typ(mode)) for mode in project.MODES] == [("fr", "de")] * 3
        assert [mixed.document_dir(mode).name for mode in project.MODES] == list(documents.MODE_FOLDERS["fr"].values())


def test_a_skeleton_s_pictures_move_up_and_the_paths_that_name_them_follow():
    """A template of the engineer's may keep pictures in its report's folder, and a section may set one -- `image("../Images/Logo.png")`, and a path continued at compile time from that folder. In three documents the pictures lie at the top of the project, shared by the three, and each such path is rewritten to reach them from the project's own folder (calc/typst_paths.py); the report compiles."""
    with _own_templates("templates_images") as base:
        template = templates.duplicate(templates.standard(), "Bilder", "user", {})
        (template.report_dir / "Images").mkdir()
        (template.report_dir / "Images" / "Logo.png").write_bytes(_png())
        section = template.sections_dir / "001-einleitung.typ"
        section.write_bytes(section.read_bytes() + b'\n#image("../Images/Logo.png", width: 1cm)\n#let bild = "Logo.png"\n#image("../Images/" + bild, width: 1cm)\n')
        here = project_template.create(base / "Mit Bild", "Mit Bild", template=template)
        assert (here.images_dir / "Logo.png").read_bytes() == _png() and not (here.report_typ.parent / "Images").exists()
        text = (here.report_typ.parent / "Sections" / "001-einleitung.typ").read_text(encoding="utf-8")
        assert '#image("/Images/Logo.png", width: 1cm)' in text and '#image("/Images/" + bild, width: 1cm)' in text, text
        if conftest.have_typst():
            run = subprocess.run([project.typst_executable(), *documents.compile_args(here, "rs")], capture_output=True, text=True, encoding="utf-8", errors="replace")
            assert run.returncode == 0, run.stdout + run.stderr


def test_a_template_whose_report_lies_at_its_top_makes_no_project():
    """A project in three documents keeps each document in a folder of its own, and a report-shaped template whose report lies at its very top -- one a hand-written template.json can say -- has no folder to make the report's: refused by name before anything is written."""
    with _own_templates("templates_top") as base:
        folder = base / "user" / "Oben"
        folder.mkdir(parents=True)
        (folder / "Rapport.typ").write_text('#import "commands.typ": *\n= Bericht\n', encoding="utf-8")   # refused before it is compiled: relative on purpose
        (folder / templates.FILE).write_text(json.dumps({"schema_version": "1.0", "format": "woodcore-template", "name": "Oben", "layout": {"report": "Rapport.typ"}}), encoding="utf-8")
        template = templates.read(folder, "user")
        assert not template.error, template.error
        target = base / "Neu"
        try:
            project_template.create(target, "Neu", template=template)
        except project.ProjectError as exc:
            assert "top of the template" in str(exc), exc
        else:
            raise AssertionError("a template whose report lies at its top made a project in three documents")
        assert not target.exists()


def test_the_languages_and_people_follow_the_template_else_the_settings():
    with _own_templates("templates_defaults"):
        settings = {"defaults": {"company": "Büro Muster", "author": "M. Muster", "report_language": "en"}}
        assert templates.languages_for(templates.standard(), settings) == ("en", "en")
        assert templates.languages_for(templates.standard(), {}) == ("de", "de")
        template = _holzbau(settings)
        assert templates.languages_for(template, settings) == ("fr", "fr")
        assert templates.people_for(template, settings) == {"company": "Büro Muster", "author": "L. Exempel", "checker": ""}
        french_doc = templates.update(template, report_language="", document_language="fr")
        assert templates.languages_for(french_doc, settings) == ("fr", "en"), "a document language of its own, the report the settings'"


# --- «Enregistrer ce projet comme modèle» ---------------------------------------------------------

def test_a_project_saved_as_a_template_leaves_out_its_export_drawings_archives_and_workbooks():
    """A project in three documents is saved as a documents-shaped template: what the three share at its top and each document's own folder -- and nothing else of the top of the project, where the architect's plans and the office's other folders lie -- an RFEM-Export/ folder an older project carries among them (the RFEM import was retired in 0.117). A project made from it is laid out as the one it came from, its three folders renamed where asked, and its layout is not edited in *Paramètres*."""
    with _own_templates("templates_save") as base:
        here = project_template.create(base / "Quelle", "Quelle", company="Büro Muster", author="F. L.", number="42", client="Bauherr")
        report = here.report_typ.parent
        (here.archives_dir / "250101-1200.zip").write_bytes(b"zip")
        (here.connectors_dir / "SD-10.json").write_text("{}", encoding="utf-8")
        (report / "Statischer Rapport.pdf").write_bytes(b"%PDF")
        (here.document_dir("cu") / "Nutzungsvereinbarung.pdf").write_bytes(b"%PDF")
        (here.images_dir / "logo.png").write_bytes(_png())
        (here.images_dir / "Baustelle.jpg").write_bytes(b"jpg")
        (here.root / "RFEM-Export").mkdir()
        (here.root / "RFEM-Export" / "Modell.csv").write_text("x", encoding="utf-8")
        (here.root / "01_Pläne").mkdir()
        (here.root / "01_Pläne" / "Grundriss.png").write_bytes(b"png")
        section = report / "Sections" / "001-einleitung.typ"
        section.write_text(section.read_text(encoding="utf-8") + '\n#image("/Images/logo.png", width: 1cm)\n', encoding="utf-8")
        saved = templates.save_project(here, "Aus Quelle", "user", {})
        assert not saved.error, saved.error
        assert saved.has_modes and saved.layout == here.layout and saved.meta["layout"] == here.layout, saved.meta.get("layout")
        kept = {p.relative_to(saved.folder).as_posix() for p in saved.folder.rglob("*") if p.is_file()}
        names = documents.MODE_FOLDERS["de"]
        for wanted in ("config.typ", "commands.typ", "references.bib", "title.typ", "Template/template.typ", "Template/form.json", "Images/logo.png", f"{names['rs']}/Statischer Rapport.typ",
                       f"{names['rs']}/Sections/001-einleitung.typ", f"{names['cu']}/Nutzungsvereinbarung.typ", f"{names['cu']}/structure.json",
                       f"{names['bp']}/Sections/purpose-of-basis-of-design.typ", ".vscode/settings.json", templates.FILE):
            assert wanted in kept, (wanted, sorted(kept))
        for refused in ("_woodcore", "Woodcore-Datei", "_Archiv", ".pdf", ".xlsx", ".woodcore", "Baustelle.jpg", "01_Pläne", "RFEM-Export"):
            assert not any(refused in path for path in kept), (refused, sorted(kept))
        assert saved.person("company") == "Büro Muster" and saved.person("author") == "F. L." and "number" not in saved.meta and "client" not in saved.meta
        assert saved.document_language == "de" and saved.report_language == "de"
        assert templates.folders_offered(saved, "fr") == names, "a documents-shaped template means its own folders"
        # a project made from it is laid out as the one it came from ...
        again = project_template.create(base / "Neu", "Neu", template=saved)
        assert again.layout == here.layout and (again.images_dir / "logo.png").is_file()
        # ... or with its folders named otherwise, the paths that named them following
        other = project_template.create(base / "Anders", "Anders", template=saved, folders={"cu": "NV", "rs": names["cu"]})
        assert [other.document_dir(mode).name for mode in project.MODES] == ["NV", names["bp"], names["cu"]], other.layout
        assert other.report_typ.name == "Statischer Rapport.typ" and other.document_typ("cu").name == "Nutzungsvereinbarung.typ"
        if conftest.have_typst():
            for mode in other.modes:
                run = subprocess.run([project.typst_executable(), *documents.compile_args(other, mode)], capture_output=True, text=True, encoding="utf-8", errors="replace")
                assert run.returncode == 0, (mode, run.stdout + run.stderr)
        # its layout is not edited here, and saying what the form showed is no edit
        shown = {key: templates.template_layout(saved.layout).get(key, "") for key in templates.EDITED_LAYOUT}
        renamed = templates.update(saved, name="Aus Quelle 2", layout=shown)
        assert renamed.name == "Aus Quelle 2" and renamed.layout == here.layout
        try:
            templates.update(renamed, layout=dict(shown, report="Bericht/Rapport.typ"))
        except templates.TemplateError as exc:
            assert "three documents" in str(exc), exc
        else:
            raise AssertionError("the layout of a documents-shaped template was edited")


def test_a_project_saved_as_a_template_leaves_out_the_documents_sync_records():
    """What a document shares with the others is recorded in its `sync.json` (calc/sync.py): Woodcore's own file about this project's copies. A template carries the sections and the shared tags, **never that record** -- a document made from it has no copy of another one to be in step with -- so «Enregistrer ce projet comme modèle» skips it, in every document's folder."""
    import sync
    assert templates.SYNC_FILE == sync.FILE, "calc/templates.py names the file calc/sync.py writes"
    with _own_templates("templates_save_sync") as base:
        here = project_template.create(base / "Quelle", "Quelle")
        for mode in ("cu", "bp"):
            sync.status(here, mode)     # the record is written the first time it is asked for
        recorded = [mode for mode in here.modes if sync.state_file(here, mode).is_file()]
        assert recorded, "no document had a sync.json: the check below would hold nothing"
        saved = templates.save_project(here, "Ohne Sync", "user", {})
        assert not saved.error, saved.error
        kept = {p.relative_to(saved.folder).as_posix() for p in saved.folder.rglob("*") if p.is_file()}
        assert not [path for path in kept if path.endswith(sync.FILE)], sorted(kept)
        assert any(path.endswith("structure.json") for path in kept), "the documents themselves are saved"
        again = project_template.create(base / "Neu", "Neu", template=saved)
        assert again.has_modes


def test_a_report_alone_saved_as_a_template_stays_report_shaped():
    """A project laid out as a report alone -- every project made before the three documents -- is saved as it always was: its report's folder and `.vscode/`, no layout where it keeps the default one."""
    with _own_templates("templates_save_alone") as base:
        root = base / "Allein"
        import shutil
        shutil.copytree(templates.standard().folder, root, ignore=shutil.ignore_patterns(templates.FILE))
        here = project.write(root / "Allein.woodcore", "Allein", company="Büro Muster")
        report = here.typst_root
        (report / "Images").mkdir()
        (report / "Images" / "logo.png").write_bytes(b"png")
        section = report / "Sections" / "001-einleitung.typ"
        section.write_text(section.read_text(encoding="utf-8") + '\n#image("../Images/logo.png")\n', encoding="utf-8")
        saved = templates.save_project(here, "Allein", "user", {})
        assert not saved.error and not saved.has_modes and "layout" not in saved.meta, (saved.error, saved.meta)
        kept = {p.relative_to(saved.folder).as_posix() for p in saved.folder.rglob("*") if p.is_file()}
        for wanted in ("Statischer Rapport.typ", "config.typ", "commands.typ", "Sections/001-einleitung.typ", "Images/logo.png"):
            assert f"Statischer Bericht (typst)/{wanted}" in kept, wanted
        assert saved.person("company") == "Büro Muster"


def test_a_project_whose_report_lies_at_the_top_of_its_folder_is_not_saved_whole():
    with _own_templates("templates_save_top") as base:
        root = base / "Alt"
        (root / "000-Python").mkdir(parents=True)
        (root / "Statischer Rapport.typ").write_text("= Bericht\n", encoding="utf-8")
        here = project_template.convert(root)
        assert here.typst_root.resolve() == here.root.resolve()
        try:
            templates.save_project(here, "Alt", "user", {})
        except templates.TemplateError as exc:
            assert "top" in str(exc)
        else:
            raise AssertionError("a project whose report lies at the top of its folder was saved as a template, whole")
        assert not (base / "user" / "Alt").exists()


# --- the sections ------------------------------------------------------------------------------

def _includes(report):
    return [line.strip() for line in report.read_text(encoding="utf-8").splitlines() if "#include" in line]


def test_sections_are_added_renamed_moved_and_deleted_and_the_includes_follow():
    with _own_templates("templates_sections"):
        template = templates.duplicate(templates.standard(), "Abschnitte", "user", {})
        report = template.report
        text = report.read_text(encoding="utf-8")
        # a line the engineer put between two includes stays where it is, and a section he left out stays left out
        text = text.replace('#include "Sections/003-baustoffe.typ"\n', '#pagebreak()\n// #include "Sections/003-baustoffe.typ"\n')
        report.write_bytes(text.encode("utf-8"))
        # the standard template ends on 007-literatur and 008-journal (v0.99), so a section added is the ninth
        added = templates.add_section(report, "Brandschutz Nachweis")
        # a report-shaped template's section starts with a report alone's line -- documents.import_line of no project, and not the one of the project the suite works on, which is laid out in three documents
        assert added.name == "009-brandschutz-nachweis.typ" and added.read_text(encoding="utf-8") == f"{documents.import_line(None)}\n\n= Brandschutz Nachweis\n"
        assert _includes(report)[-1] == '#include "Sections/009-brandschutz-nachweis.typ"'
        moved = templates.move_section(report, added.name, -1)
        assert moved.name == "008-brandschutz-nachweis.typ"
        assert _includes(report)[-2:] == ['#include "Sections/008-brandschutz-nachweis.typ"', '#include "Sections/009-journal.typ"']
        renamed = templates.rename_section(report, "002-grundlagen.typ", "Grundlagen und Normen")
        assert renamed.name == "002-grundlagen-und-normen.typ" and '#include "Sections/002-grundlagen-und-normen.typ"' in _includes(report)
        templates.delete_section(report, "001-einleitung.typ")
        names = [p.name for p in templates.sections(template.report_dir)]
        assert names == ["001-grundlagen-und-normen.typ", "002-baustoffe.typ", "003-einwirkungen.typ", "004-tragwerksanalyse.typ",
                         "005-nachweise.typ", "006-literatur.typ", "007-brandschutz-nachweis.typ", "008-journal.typ"], names
        assert _includes(report) == ['#include "Sections/001-grundlagen-und-normen.typ"', '// #include "Sections/002-baustoffe.typ"'] \
            + [f'#include "Sections/{name}"' for name in names[2:]], _includes(report)
        assert "#pagebreak()" in report.read_text(encoding="utf-8")
        body = report.read_text(encoding="utf-8")
        assert body.index("#pagebreak()") < body.index('// #include "Sections/002-baustoffe.typ"'), "the engineer's own line moved"


def test_a_report_with_crlf_keeps_its_line_endings_when_its_includes_change():
    with _own_templates("templates_crlf"):
        template = templates.duplicate(templates.standard(), "CRLF", "user", {})
        report = template.report
        report.write_bytes(report.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n"))
        templates.add_section(report, "Anhang")
        data = report.read_bytes()
        assert b"\r\n" in data and data.count(b"\n") == data.count(b"\r\n"), "a line ending of another kind was written"


# --- the command line ----------------------------------------------------------------------------

def test_woodcore_cli_new_takes_a_template_and_the_settings_defaults():
    with _own_templates("templates_cli") as base:
        settings_file = base / "settings.json"
        settings_file.write_text(json.dumps({"defaults": {"company": "Büro Muster", "report_language": "en"}}), encoding="utf-8")
        env = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8", WOODCORE_SETTINGS=str(settings_file))
        env.pop(project.ENV, None)
        _holzbau()
        folder = base / "Scheune"
        run = subprocess.run([sys.executable, str(CALC / "cli.py"), "new", str(folder), "--template", "Holzbau", "--checker", "P. Prüfer"],
                             capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)
        assert run.returncode == 0, run.stdout + run.stderr
        here = project.Project.load(folder / "Scheune.woodcore")
        assert here.has_modes and here.layout["report"] == "Bericht/Rapport.typ" and templates.read_languages(here.report_typ) == ("fr", "fr")
        assert (here.detail("company"), here.detail("author"), here.detail("checker")) == ("Büro Muster", "L. Exempel", "P. Prüfer")
        # without --template: the settings' default, Standard here, and the settings' report language
        plain = base / "Stall"
        run = subprocess.run([sys.executable, str(CALC / "cli.py"), "new", str(plain)], capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)
        assert run.returncode == 0, run.stdout + run.stderr
        stall = project.Project.load(plain / "Stall.woodcore")
        # v0.100: and the folders are the settings language's own words -- the three of a project in three documents since 30.09.2026 -- stated in full
        assert stall.layout == documents.layout_for("en"), stall.layout
        assert templates.read_languages(stall.report_typ) == ("en", "en")
        # a template nobody made is refused by name, nothing written
        refused = subprocess.run([sys.executable, str(CALC / "cli.py"), "new", str(base / "Nichts"), "--template", "Brücke"],
                                 capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)
        assert refused.returncode == 1 and "Brücke" in refused.stderr and not (base / "Nichts").exists(), refused.stderr


def test_woodcore_cli_new_takes_a_form_and_a_content_template_for_each_document():
    """`--form` names the look and `--content-cu|bp|rs` the content of each document (the engineer's decision of 06.10.2026); `--style` is the older name of `--form`; the settings' default form is used where none is given; an unknown form or content is refused by name before anything is written, and `--template` stays as the legacy way."""
    import forms
    with _own_templates("templates_cli_form") as base:
        settings_file = base / "settings.json"
        settings_file.write_text(json.dumps({"forms": {"default": "builtin:compact"}}), encoding="utf-8")
        env = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8", WOODCORE_SETTINGS=str(settings_file))
        env.pop(project.ENV, None)

        def new(folder, *args):
            return subprocess.run([sys.executable, str(CALC / "cli.py"), "new", str(folder), *args], capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)

        run = new(base / "Bfh", "--form", "bfh", "--content-rs", "builtin:rs/standard", "--content-cu", "builtin:cu/standard", "--content-bp", "builtin:bp/standard", "--language", "fr")
        assert run.returncode == 0, run.stdout + run.stderr
        here = project.Project.load(base / "Bfh" / "Bfh.woodcore")
        assert forms.current(here).ref == "builtin:bfh" and (here.typst_root / "Template" / "logo-bfh.png").is_file()
        assert templates.read_languages(here.report_typ) == ("fr", "fr")
        assert here.title_typ.read_bytes() == forms.find("bfh").title_typ.read_bytes()
        # nothing asked: the settings' default form
        run = new(base / "Standardform")
        assert run.returncode == 0, run.stdout + run.stderr
        assert forms.current(project.Project.load(base / "Standardform" / "Standardform.woodcore")).ref == "builtin:compact"
        # the older name
        run = new(base / "Stil", "--style", "neutral")
        assert run.returncode == 0, run.stdout + run.stderr
        assert forms.current(project.Project.load(base / "Stil" / "Stil.woodcore")).ref == "builtin:neutral"
        for args, word in ((("--form", "barock"), "barock"), (("--content-rs", "user:rs/nichts"), "nichts"), (("--form", "bfh", "--style", "compact"), "builtin:compact")):
            folder = base / ("Nein-" + word.replace(":", "-"))
            refused = new(folder, *args)
            assert refused.returncode == 1 and word in refused.stderr and not folder.exists(), (args, refused.stderr)


def test_the_default_form_is_read_from_and_written_into_the_settings():
    """`forms.default_ref` reads `forms.default` and falls back on builtin neutral; `set_default` writes it into the dict the caller then saves; one that is gone or unusable falls back on neutral (`default_form`)."""
    import forms
    assert forms.default_ref({}) == "builtin:neutral" and forms.default_ref({"forms": {"default": "  "}}) == "builtin:neutral"
    settings = forms.set_default({}, "shared:bfh-academique")
    assert settings == {"forms": {"default": "shared:bfh-academique"}} and forms.default_ref(settings) == "shared:bfh-academique"
    assert forms.default_form(settings).ref == "builtin:neutral", "a form that is not there falls back on neutral"
    assert forms.default_form(forms.set_default({}, "bfh")).ref == "builtin:bfh"
    assert forms.set_default(settings, "") == {"forms": {}}


def test_the_report_folder_is_one_folder_and_not_a_path():
    """`check_report_folder` refuses where the name is typed and not when the file is next read: a separator would put the report somewhere the engineer did not ask for, and `..` outside the project -- which `Project.__init__` refuses by then, the folder having been made and the project written (v0.100)."""
    assert templates.check_report_folder("  Rapport de statique  ") == "Rapport de statique"
    refused = ["", "   ", "a/b", "a" + chr(92) + "b", ".", "..", 'x"y', "x?y", "trail.", "CON", "nul.txt", "LPT3"]
    for bad in refused:
        try:
            templates.check_report_folder(bad)
        except templates.TemplateError:
            pass
        else:
            raise AssertionError(f"{bad!r} was accepted as a folder's name")


def test_a_renamed_report_folder_takes_the_pdf_and_the_export_with_it():
    """Only `report` is stated and `pdf` and `generated` follow it (layout_of), so the three cannot come apart -- `Project.__init__` refuses a `generated` outside the report's own folder. What lies outside that folder, `sources` and `archives`, stays where it is (v0.100)."""
    out = templates.layout_in_folder(dict(project.DEFAULT_LAYOUT), "Rapport de statique")
    assert out["report"] == "Rapport de statique/Statischer Rapport.typ"
    assert out["pdf"] == "Rapport de statique/Statischer Rapport.pdf"
    assert out["generated"] == "Rapport de statique/_woodcore"
    assert out["sources"] == project.DEFAULT_LAYOUT["sources"]
    assert out["archives"] == project.DEFAULT_LAYOUT["archives"]


def test_a_template_that_names_its_report_folder_keeps_it():
    """A template that states its report folder in its own template.json means it, whatever the language; Standard states no layout at all and so takes the language's word.

    Which is why `templates/projet/`'s own folder is still «Statischer Bericht (typst)» and is deliberately not renamed: `stated_layout` compares a template's layout against `project.DEFAULT_LAYOUT`, so renaming that folder would make Standard *state* a report folder and the language's word would never be offered again (v0.100).
    """
    standard = templates.standard()
    assert not templates.template_layout(standard.layout).get("report"), "Standard states no report folder"
    assert templates.report_folder_offered(standard, "fr") == "3_Rapport de statique"
    own = templates.Template("user", standard.folder, {"layout": {"report": "Tragwerk/Bericht.typ"}})
    assert templates.report_folder_offered(own, "fr") == "Tragwerk"
    assert templates.folders_offered(own, "fr") == {"cu": "1_Convention d'utilisation", "bp": "2_Base de projet", "rs": "Tragwerk"}


def test_a_documents_shaped_layout_is_stated_whole_and_only_known_keys_are_read():
    """A layout of three documents is what the project's .woodcore states and what a template.json saved from it states: every key, in project.LAYOUT_ORDER, nothing read from DEFAULT_LAYOUT; and a key calc/project.py does not know is not read in either shape (project.LAYOUT_KEYS)."""
    layout = documents.layout_for("fr")
    assert templates.stated_layout(layout) == layout and list(templates.stated_layout(layout)) == list(project.LAYOUT_ORDER)
    assert templates.template_layout(layout) == layout
    assert templates.layout_of({"layout": dict(layout, unknown="x")}) == layout
    assert templates.layout_of({"layout": {"report": "Bericht/R.typ", "unknown": "x"}}) == {**project.DEFAULT_LAYOUT, "report": "Bericht/R.typ", "pdf": "Bericht/R.pdf", "generated": "Bericht/_woodcore"}
    assert templates.stated_layout(dict(project.DEFAULT_LAYOUT, unknown="x")) == {}
    assert templates.IMAGES == project.IMAGES_FOLDER and templates.CONFIG == project.CONFIG_FILE
    schema = json.loads((CALC.parent / "schemas" / "template.schema.json").read_text(encoding="utf-8"))
    # a key retired in 0.117 (project.RETIRED_KEYS) stays described, as retired, so that a template written before goes on validating
    described = set(project.LAYOUT_KEYS) | {key for section, key in project.RETIRED_KEYS if section == "layout"}
    assert set(schema["properties"]["layout"]["properties"]) == described, "template.schema.json does not document every key a template's layout may state"


# --- archived and imported: the settings' one «Modèles» page (v0.113) ----------------------------------

def _tree(folder):
    """{relative path: bytes} of every file under `folder`."""
    return {p.relative_to(folder).as_posix(): p.read_bytes() for p in sorted(folder.rglob("*")) if p.is_file()}


def _import_refused(code, *args, **kwargs):
    """`templates.import_folder(*args, **kwargs)` is refused, stating `code`; the refusal is returned."""
    try:
        templates.import_folder(*args, **kwargs)
    except templates.TemplateImportError as exc:
        assert exc.code == code, f"refused with {exc.code!r} and not {code!r}: {exc}"
        assert exc.code in templates.IMPORT_CODES and str(exc), exc
        return exc
    raise AssertionError(f"{args} was imported, and {code!r} was expected")


def test_a_project_template_folder_is_imported_and_one_of_that_name_replaced_on_request():
    with _own_templates("templates_import") as base:
        settings = {"templates": {"shared_folder": str(base / "office")}}
        office = templates.duplicate(templates.standard(), "Halle Nord", "shared", settings)
        templates.update(office, author="L. Exempel", description="Pour les halles")
        files = _tree(office.folder)
        made = templates.import_folder(office.folder, settings=settings)
        assert made.ref == "user:Halle Nord" and made.place == "user" and made.folder == base / "user" / "Halle Nord" and not made.error, made.error
        assert made.name == "Halle Nord" and made.person("author") == "L. Exempel" and made.description("fr") == "Pour les halles"
        assert _tree(made.folder) == files, "the copy is not the folder imported"
        assert _tree(office.folder) == files, "the folder imported was changed"
        assert [t.ref for t in templates.list_templates(settings)] == ["builtin:projet", "user:Halle Nord", "shared:Halle Nord"]
        assert not list((base / "user").glob(".importing-*")), "the import left its staging folder behind"
        # one of that folder's name is there: refused, nothing changed -- then replaced on request, the old one archived and never deleted
        (made.folder / "marker.txt").write_text("the old one\n", encoding="utf-8")
        exc = _import_refused("exists", office.folder, settings=settings)
        assert exc.values["folder"] == "Halle Nord" and (made.folder / "marker.txt").is_file()
        again = templates.import_folder(office.folder, replace=True, settings=settings)
        assert again.ref == made.ref and not (again.folder / "marker.txt").exists() and _tree(again.folder) == files
        archived = list((base / "user" / templates.ARCHIVES).iterdir())
        assert len(archived) == 1 and archived[0].name.endswith("-Halle Nord") and (archived[0] / "marker.txt").is_file(), archived
        assert [t.ref for t in templates.list_templates(settings)] == ["builtin:projet", "user:Halle Nord", "shared:Halle Nord"], "the archives are listed as a template"


def test_importing_a_project_template_refuses_what_it_cannot_import_and_writes_nothing():
    import doc_templates
    with _own_templates("templates_import_refused") as base:
        settings = {"templates": {"shared_folder": str(base / "office")}}
        _import_refused("not_a_folder", base / "nowhere", settings=settings)
        (base / "a file.txt").write_text("x", encoding="utf-8")
        _import_refused("not_a_folder", base / "a file.txt", settings=settings)
        (base / "empty").mkdir()
        assert _import_refused("no_template", base / "empty", settings=settings).values["folder"] == str(base / "empty")
        doc = _import_refused("document_template", doc_templates.find("builtin:cu/standard").folder, settings=settings)
        assert doc.values["document"] == "cu"
        office = templates.duplicate(templates.standard(), "Kaputt", "shared", settings)
        office.report.unlink()
        assert "entry file" in _import_refused("invalid", office.folder, settings=settings).values["error"]
        (base / "office" / "Unlesbar").mkdir()
        (base / "office" / "Unlesbar" / templates.FILE).write_text("{not json", encoding="utf-8")
        _import_refused("invalid", base / "office" / "Unlesbar", settings=settings)
        assert _import_refused("name_is_builtin", templates.standard().folder, settings=settings).values["name"] == "Standard"
        assert not (base / "user").exists() or not any((base / "user").iterdir()), "a refused import wrote something"
        mine = templates.duplicate(templates.standard(), "Holzbau", "user", settings)
        _import_refused("already_mine", mine.folder, settings=settings)
        assert [t.ref for t in templates.list_templates(settings) if t.place == "user"] == ["user:Holzbau"]


def test_a_template_taken_away_is_archived_and_never_deleted():
    with _own_templates("templates_archive") as base:
        mine = templates.duplicate(templates.standard(), "Holzbau", "user", {})
        files = _tree(mine.folder)
        gone = templates.archive(mine)
        assert gone.parent == base / "user" / templates.ARCHIVES and gone.name.endswith("-Holzbau") and _tree(gone) == files
        assert not mine.folder.exists() and [t.ref for t in templates.list_templates({})] == ["builtin:projet"]
        # the same name archived again in the same second does not meet the first
        again = templates.archive(templates.duplicate(templates.standard(), "Holzbau", "user", {}))
        assert again != gone and again.is_dir() and gone.is_dir()
        try:
            templates.archive(templates.standard())
        except templates.TemplateError:
            pass
        else:
            raise AssertionError("a builtin template was archived")
        assert templates.standard().folder.is_dir()
