"""The three documents a project is written as, by name (calc/documents.py, the engineer's request of 30.09.2026).

A project is laid out as a report alone, or in three documents -- the convention d'utilisation, the base de projet and the rapport de statique, which is the report and keeps every name it had. What each is called in each language, the folder a new project gives it, its entry file, and the one spelling of the command line that compiles one are calc/documents.py's; where each lies is calc/project.py's, which tests/test_project.py holds.

The checks here hold the names the engineer wrote down in their exact forms, the layout built from them, and the command line -- its order, which every reader of one relies on, and that it compiles a document whose sections import from the project's own folder.
"""

TIER = "fast"  # tests/run_tests.py --fast

import json
import subprocess

import conftest

import documents
import project
import templates


def test_the_folders_are_the_engineer_s_own_forms():
    """Exactly as he chose them (issue #64, spec 2026-10-15-structure-projet-dossiers D-07, D-14): one name per document, English and the same in every language -- a folder name that drifts by a character is a folder the migration does not find."""
    assert documents.MODE_FOLDERS == {"cu": "100-Service criteria agreement", "bp": "200-Basis of design", "rs": "300-Statical report"}
    assert documents.folders_for("fr") == documents.folders_for("de") == documents.folders_for("en") == documents.MODE_FOLDERS


def test_a_folder_is_its_document_s_number_and_its_english_name():
    assert list(documents.MODE_NUMBERS) == list(documents.MODES) == ["cu", "bp", "rs"]
    assert [documents.MODE_NUMBERS[mode] for mode in documents.MODES] == [100, 200, 300]
    for mode, folder in documents.MODE_FOLDERS.items():
        assert folder == f"{documents.MODE_NUMBERS[mode]}-{documents.MODE_NAMES['en'][mode]}", (mode, folder)


def test_the_documents_are_named_in_the_three_languages():
    assert documents.MODE_NAMES == {
        "fr": {"cu": "Convention d'utilisation", "bp": "Base de projet", "rs": "Rapport de statique"},
        "de": {"cu": "Nutzungsvereinbarung", "bp": "Projektbasis", "rs": "Statischer Bericht"},
        "en": {"cu": "Service criteria agreement", "bp": "Basis of design", "rs": "Statical report"},
    }
    assert documents.LANGUAGES == templates.LANGUAGES, "the three documents are named in the languages a project is created in"
    for table in (documents.MODE_NAMES, documents.ENTRY_NAMES):
        assert set(table) == set(documents.LANGUAGES) and all(set(row) == set(documents.MODES) for row in table.values())
    assert not any("ß" in name for name in documents.MODE_NAMES["de"].values()), "Swiss German writes no ß"


def test_the_entry_files_are_named_after_their_document_and_the_report_keeps_its_own():
    """Nothing of the report is renamed by its becoming the third document: its entry file is `Statischer Rapport.typ` in every language, so every route that names its PDF after it names the PDF it always did."""
    assert documents.ENTRY_NAMES == {
        "fr": {"cu": "Convention d'utilisation.typ", "bp": "Base de projet.typ", "rs": "Statischer Rapport.typ"},
        "de": {"cu": "Nutzungsvereinbarung.typ", "bp": "Projektbasis.typ", "rs": "Statischer Rapport.typ"},
        "en": {"cu": "Service criteria agreement.typ", "bp": "Basis of design.typ", "rs": "Statischer Rapport.typ"},
    }
    assert documents.RS_ENTRY == project.DEFAULT_LAYOUT["report"].rsplit("/", 1)[1]


def test_the_drop_down_offers_the_three_in_their_order():
    assert documents.mode_choices("fr") == [("cu", "Convention d'utilisation"), ("bp", "Base de projet"), ("rs", "Rapport de statique")]
    assert documents.mode_choices("de") == [("cu", "Nutzungsvereinbarung"), ("bp", "Projektbasis"), ("rs", "Statischer Bericht")]
    assert documents.mode_choices("en") == [("cu", "Service criteria agreement"), ("bp", "Basis of design"), ("rs", "Statical report")]
    assert documents.mode_choices("it") == documents.mode_choices("de"), "a language not one of the three is German's, as the report's folder is"
    assert documents.mode_name("bp", "fr") == "Base de projet"
    offered = documents.folders_for("fr")
    offered["cu"] = "edited"
    assert documents.MODE_FOLDERS["cu"] == "100-Service criteria agreement", "a dialog editing what it was offered edited the table"


def test_each_document_has_a_journal_of_its_own():
    assert documents.JOURNAL_FILES == {"rs": "journal.json", "cu": "journal-cu.json", "bp": "journal-bp.json"}
    assert documents.JOURNAL_FILES is project.JOURNAL_FILES, "the journals' names are written down twice"


def test_a_layout_names_each_document_s_folder_and_what_the_three_share():
    layout = documents.layout_for("en")
    assert list(layout) == list(project.LAYOUT_ORDER)
    assert layout == {
        "typst_root": ".", "config": "000-Typst-Config",
        "report": "300-Statical report/Statischer Rapport.typ", "pdf": "300-Statical report/Statischer Rapport.pdf",
        "report_cu": "100-Service criteria agreement/Service criteria agreement.typ",
        "pdf_cu": "100-Service criteria agreement/Service criteria agreement.pdf",
        "report_bp": "200-Basis of design/Basis of design.typ", "pdf_bp": "200-Basis of design/Basis of design.pdf",
        "generated": "000-Woodcore", "images": "Images",
        "sources": "000-Woodcore/sources", "archives": "000-Woodcore/archives",
    }
    # the folders are the same in every language, the entry files named in it
    assert documents.layout_for("fr")["report_cu"] == "100-Service criteria agreement/Convention d'utilisation.typ"
    folder = conftest.tmpdir("documents_layout")
    written = project.write(folder / "E.woodcore", "E", layout)
    assert written.has_modes and written.has_folders
    assert json.loads(written.file.read_text(encoding="utf-8"))["schema_version"] == "1.1"
    # the folders a caller named, the others kept; a sequence in the documents' order; the report's entry the template's
    edited = documents.layout_for("de", folders={"cu": "A_NV"})
    assert (edited["report_cu"], edited["report_bp"]) == ("A_NV/Nutzungsvereinbarung.typ", "200-Basis of design/Projektbasis.typ")
    assert documents.modes_layout(["N", "P", "S"], documents.ENTRY_NAMES["de"]) == documents.modes_layout({"cu": "N", "bp": "P", "rs": "S"}, documents.ENTRY_NAMES["de"])
    alone = documents.modes_layout(["N", "P", "S"], {"cu": "N.typ", "bp": "P.typ"}, rs_entry="Bericht.typ")
    assert (alone["report"], alone["pdf"]) == ("S/Bericht.typ", "S/Bericht.pdf")
    assert documents.modes_layout(["N", "P", "S"], {"cu": "N.typ", "bp": "P.typ"})["report"] == "S/Statischer Rapport.typ"
    assert documents.modes_layout([" N ", "P", "S"], {"cu": "N.typ", "bp": "P.typ"})["report_cu"] == "N/N.typ", "a name is stripped, as the report's folder is"


def _refused(call, words):
    try:
        call()
    except project.ProjectError as exc:
        assert words in str(exc), exc
        return
    raise AssertionError(f"accepted, and should have been refused for {words!r}")


def test_a_layout_refuses_the_folders_nobody_can_create():
    """Checked before anything is created, as the report's folder is when it is typed: a name with a separator, one Windows refuses, two documents in one folder, a folder missing."""
    entries = documents.ENTRY_NAMES["de"]
    _refused(lambda: documents.modes_layout(["NV", "nv", "SB"], entries), "the service criteria agreement and the basis of design are both given")
    _refused(lambda: documents.modes_layout(["NV", "Doku/PB", "SB"], entries), "the folder of the basis of design")
    _refused(lambda: documents.modes_layout(["NV", "PB", "CON"], entries), "reserves for a device")
    _refused(lambda: documents.modes_layout(["NV", "PB", "  "], entries), "needs a name")
    _refused(lambda: documents.modes_layout(["NV", "PB"], entries), "three folders are named")
    _refused(lambda: documents.modes_layout({"cu": "NV", "rs": "SB"}, entries), "no folder is named for bp")
    _refused(lambda: documents.modes_layout(["NV", "PB", "SB"], {"cu": "NV.typ"}), "no entry file is named for bp")
    _refused(lambda: documents.modes_layout(["NV", "PB", "SB"], {**entries, "cu": "NV.pdf"}), "must be the name of a .typ file")
    _refused(lambda: documents.modes_layout(["NV", "PB", "SB"], {**entries, "bp": "sub/PB.typ"}), "must be the name of a .typ file")


def test_the_command_line_ends_on_the_entry_and_the_target():
    """The root always stated, the flags after it, `--deps` only where asked for, and the entry file and the target last -- where tests/test_pdf_button.py and every reader of a command line look for them."""
    folder = conftest.tmpdir("documents_args")
    here = project.write(folder / "M.woodcore", "M", documents.layout_for("fr"))
    flags = ["--input", "level=2", "--input", "lang=fr"]
    args = documents.compile_args(here, "cu", flags)
    assert args == ["compile", "--root", str(folder.resolve()), *flags, str(here.document_typ("cu")), str(here.document_pdf("cu"))]
    deps = here.stamps_dir / "cu.deps.json"
    args = documents.compile_args(here, "cu", flags, deps=deps)
    assert args[args.index("--deps"):args.index("--deps") + 4] == ["--deps", str(deps), "--deps-format", "json"]
    assert args[-2:] == [str(here.document_typ("cu")), str(here.document_pdf("cu"))]
    assert documents.compile_args(here, "rs", [], folder / "out.pdf")[-2:] == [str(here.report_typ), str(folder / "out.pdf")]
    # a report alone compiles from its own folder, which is the root Typst takes where it is given none
    alone = project.write(folder / "A.woodcore", "A")
    assert documents.compile_args(alone, "rs") == ["compile", "--root", str(alone.report_typ.parent), str(alone.report_typ), str(alone.report_pdf)]
    _refused(lambda: documents.compile_args(alone, "cu"), "laid out as one report")


def test_a_document_compiles_whose_sections_import_from_the_project_s_own_folder():
    """What the three documents rest on, with the very command line compile_args writes: a section two folders down, in a folder whose name carries an apostrophe and spaces, imports the config.typ of 000-Typst-Config/ from the project's top -- and Typst writes what it read where `--deps` says, a JSON of `inputs` and `outputs`."""
    if not conftest.have_typst():
        raise conftest.Skip("no typst binary on PATH")
    folder = conftest.tmpdir("documents_compile")
    here = project.write(folder / "M.woodcore", "M", documents.layout_for("fr", folders={"cu": "1_Convention d'utilisation"}))
    here.config_typ.parent.mkdir(parents=True)
    here.config_typ.write_text("#let shared = [Partagé]\n", encoding="utf-8")
    config = here.from_root(here.config_typ)
    assert config == "/000-Typst-Config/config.typ"
    section = here.document_dir("cu") / "Sections" / "purpose.typ"
    section.parent.mkdir(parents=True)
    section.write_text(f'#import "{config}": shared\n= But\n#shared\n', encoding="utf-8")
    here.document_typ("cu").write_text(f'#import "{config}": shared\n#shared\n#include "Sections/purpose.typ"\n', encoding="utf-8")
    deps = here.stamps_dir / "cu.deps.json"
    deps.parent.mkdir(parents=True)
    run = subprocess.run([project.typst_executable(), *documents.compile_args(here, "cu", [], deps=deps)],
                         capture_output=True, text=True, encoding="utf-8", errors="replace")
    assert run.returncode == 0, run.stderr
    assert here.document_pdf("cu").is_file()
    read = json.loads(deps.read_text(encoding="utf-8"))
    names = {name.replace("\\", "/").rsplit("/", 1)[-1] for name in read["inputs"]}
    assert {"purpose.typ", "config.typ", "Convention d'utilisation.typ"} <= names, read


def test_a_section_imports_the_engine_from_the_root_in_three_documents():
    """From the root in three documents -- `/000-Typst-Config/commands.typ` laid out by folders, `/commands.typ` in a project laid out before 0.119 -- valid in every document's folder and at every depth, which is what lets one section be copied into another document; and `../commands.typ`, what every section has written until then, in a report alone or where no project is named."""
    folder = conftest.tmpdir("documents_import")
    modes = project.write(folder / "M.woodcore", "M", documents.layout_for("de"))
    alone = project.write(folder / "A.woodcore", "A")
    relative = "../commands.typ"             # built, so test_harness's scan does not read it as a probe's depth-dependent import
    assert documents.import_line() == f'#import "{relative}": *'
    assert documents.import_line(alone) == f'#import "{relative}": *'
    assert documents.import_line(modes) == '#import "/000-Typst-Config/commands.typ": *'
    assert documents.commands_import(modes) == "/" + project.CONFIG_FOLDER + "/" + modes.commands_typ.name
    before = dict(documents.layout_for("de"))
    before.pop("config")
    legacy = project.write(folder / "L.woodcore", "L", before)
    assert not legacy.has_folders and documents.import_line(legacy) == '#import "/commands.typ": *', "a project laid out before 0.119 imports as it always did"
