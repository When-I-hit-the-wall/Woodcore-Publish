"""The title page of the three documents: one `title.typ` at the top of the project, shared by the convention d'utilisation, the base de projet and the statical report, plain Typst the engineer edits in VS Code (his request of 03.10.2026).

What is held here. A new project made from Standard carries `title.typ` at its Typst root and nowhere else, and its three documents set it (`#title-page(document: "cu")`); each compiles in German, French and English, and the words the page prints of its own -- the document's name, the rows' labels, the date written out -- come out in the document's language, the people taken from the .woodcore, a field of people cut into persons at «,», «;» and new lines and an address at new lines alone. A row is set inline or one person per line, in bold or not, in some documents and not others, and a row of the engineer's own takes a label in three languages and a value of free content; a value naming no field of the .woodcore is refused by name. `title.typ` is never written over -- not by a new project's creation, not by `ensure_title` -- and a template that carries none gets Standard's, so that the two documents beside the report, which import it, compile. The archive of a document and the stamp's fallback list take it as they take config.typ. And the BFH's template, where it lies beside the program, makes a project whose three documents all print the BFH's title page, its school's words in the project's language.
"""

import re
import shutil
import subprocess
import sys

import conftest
from conftest import Skip

if str(conftest.CALC / "tools") not in sys.path:
    sys.path.insert(0, str(conftest.CALC / "tools"))
import archive_export  # noqa: E402
import documents  # noqa: E402
import project  # noqa: E402
import project_template  # noqa: E402
import stamps  # noqa: E402
import templates  # noqa: E402

LANGS = ("de", "fr", "en")
PEOPLE = {
    "author": "Hans Peter Beispiel, Lea Exempel",
    "client": "Urs Bauherr\n- Claire Exemple",
    "address": "Bahnhofstrasse 1, 2502 Biel\nSchweiz",
    "number": "2026-17",
    "company": "Muster Holzbau SA",
    "checker": "Prof. Anna Muster",
}
# What the standard page prints of its own in each language: the labels of its rows and the month of a date written out.
LABELS = {
    "de": ("Bauherrschaft", "Projektadresse", "Verfasst von", "Geprüft von", "Projekt-Nr."),
    "fr": ("Maître de l'ouvrage", "Adresse du projet", "Rédigé par", "Vérifié par", "N° de projet"),
    "en": ("Client", "Project address", "Prepared by", "Checked by", "Project no."),
}
MONTHS = {
    "de": ("Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November", "Dezember"),
    "fr": ("janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"),
    "en": ("January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"),
}
# The BFH's template, in its own repository beside the program's: a test of it is skipped where it is not there.
BFH = conftest.ROOT.parent / "templates" / "bfh-academique"

_PROJECTS = {}


def _project(lang, template=None, key=None, form=None):
    """A new project in `lang` with the engineer's own people, made once per run and per template and form."""
    key = key or (lang, str(template), str(form))
    if key not in _PROJECTS:
        name = "title_" + "_".join(str(k) for k in key if k).replace(":", "").replace("\\", "_").replace("/", "_")[-40:]
        _PROJECTS[key] = project_template.create(conftest.tmpdir(name) / "Halle", "Halle Nord", template=template, form=form,
                                                 document_language=lang, report_language=lang, **PEOPLE)
    return _PROJECTS[key]


def _compile(here, mode):
    run = subprocess.run([project.typst_executable(), *documents.compile_args(here, mode, [])],
                         capture_output=True, text=True, encoding="utf-8", errors="replace")
    assert run.returncode == 0, f"{here.name} {mode}: {run.stderr[:3000]}"
    return here.document_pdf(mode)


def _page(pdf, index=0):
    """The lines of page `index` of `pdf` as a reader reads them, the typographic apostrophe read back as «'»."""
    from pypdf import PdfReader
    text = PdfReader(str(pdf)).pages[index].extract_text() or ""
    return [" ".join(line.split()).replace("’", "'") for line in text.split("\n") if line.strip()]


def _bold(pdf, index=0):
    """The runs of page `index` set in a bold face, as (text, font)."""
    from pypdf import PdfReader
    runs = []

    def visit(text, _cm, _tm, font, _size):
        if text.strip() and font is not None and "Bold" in str(font.get("/BaseFont", "")):
            runs.append(text.strip())

    PdfReader(str(pdf)).pages[index].extract_text(visitor_text=visit)
    return runs


def _set_rows(here, rows):
    """`here`'s title.typ with its `rows` list replaced by `rows` (Typst source, one row a line), everything else of the file kept."""
    path = here.title_typ
    text = path.read_bytes().decode("utf-8")
    start = text.index("#let rows = (")
    end = text.index("\n)", start) + 2
    path.write_bytes((text[:start] + "#let rows = (\n" + "".join(f"  {row},\n" for row in rows) + ")" + text[end:]).encode("utf-8"))


def _need_typst():
    if not conftest.have_typst():
        raise Skip("no typst on the path")


def test_a_new_project_carries_title_typ_at_its_root_and_its_three_documents_set_it():
    here = _project("de")
    assert here.title_typ == here.config_dir / project.TITLE_FILE and here.title_typ.is_file(), "in 000-Typst-Config/ laid out by folders (issue #64)"
    import forms
    assert here.title_typ.read_bytes() == documents.relocate_config_text(here, forms.default().title_typ.read_text(encoding="utf-8")).encode("utf-8"), "a new project's title.typ is the default form's (neutral)"
    for mode in project.MODES:
        assert not (here.document_dir(mode) / project.TITLE_FILE).exists(), f"{mode}: a second title.typ in the document's folder"
        entry = here.document_typ(mode).read_text(encoding="utf-8")
        assert '#import "/000-Typst-Config/title.typ": title-page' in entry and f'#title-page(document: "{mode}")' in entry, mode
        assert "project-info()" not in entry, f"{mode}: the entry still writes a title page of its own"


def test_the_title_page_speaks_the_documents_language_and_takes_the_people_of_the_woodcore():
    _need_typst()
    for lang in LANGS:
        here = _project(lang)
        for mode in project.MODES:
            lines = _page(_compile(here, mode))
            where = f"{lang}/{mode}"
            assert lines[0] == documents.MODE_NAMES[lang][mode], (where, lines)
            assert "Halle Nord" in lines, (where, lines)
            text = "\n".join(lines)
            for label in LABELS[lang]:
                assert label in text, (where, label, lines)
            # the authors inline, joined by a comma; the client one person a line, the dash taken off; the address cut at its new line and not at its comma
            assert any(line.endswith("Hans Peter Beispiel, Lea Exempel") for line in lines), (where, lines)
            assert any(line.endswith("Urs Bauherr") for line in lines) and "Claire Exemple" in lines, (where, lines)
            assert "- Lambert" not in text, where
            assert any(line.endswith("Bahnhofstrasse 1, 2502 Biel") for line in lines) and "Schweiz" in lines, (where, lines)
            assert re.search(r"\b\d{1,2}(\.|er)? (" + "|".join(MONTHS[lang]) + r") \d{4}\b", text), (where, lines)
        # what the other languages print is not printed in this one
        others = [label for other in LANGS if other != lang for label in LABELS[other] if label not in LABELS[lang]]
        text = "\n".join(_page(here.document_pdf("cu")))
        assert not [label for label in others if label in text], (lang, text)


def test_a_row_is_set_inline_or_one_person_a_line_in_bold_or_not_and_in_some_documents_only():
    _need_typst()
    here = _project("de", key=("rows",))
    _set_rows(here, [
        'row("author", layout: "lines", bold: true)',
        'row("client")',
        'row((de: "Architektur", fr: "Architecture", en: "Architecture"), value: [Muster Architekten AG \\ Bahnhofstrasse 1], layout: "lines")',
        'row((de: "Fachplaner", fr: "Spécialistes", en: "Specialists"), value: ("Anna Muster", "Beat Beispiel"))',
        'row("checker", documents: ("rs",))',
        'row(none, value: [Vorabzug])',
    ])
    rs = _compile(here, "rs")
    lines = _page(rs)
    text = "\n".join(lines)
    assert "Hans Peter Beispiel" in [line.replace("Verfasst von ", "") for line in lines] and "Lea Exempel" in lines, lines
    bold = " ".join(_bold(rs))
    assert "Beispiel" in bold and "Exempel" in bold, bold
    assert "Bauherr" not in bold and "Muster Architekten" not in bold, bold
    assert any(line.endswith("Urs Bauherr, Claire Exemple") for line in lines), lines
    assert any(line.startswith("Architektur") and line.endswith("Muster Architekten AG") for line in lines) and "Bahnhofstrasse 1" in lines, lines
    assert any(line.endswith("Anna Muster, Beat Beispiel") and line.startswith("Fachplaner") for line in lines), lines
    assert "Geprüft von" in text and "Vorabzug" in lines, lines
    assert "Projektadresse" not in text and "Ingenieurbüro" not in text, "a row taken out of `rows` is printed no more"
    cu = "\n".join(_page(_compile(here, "cu")))
    assert "Geprüft von" not in cu and "Architektur" in cu, "a row for the statical report alone is in the convention d'utilisation"


def test_a_value_naming_no_field_of_the_woodcore_is_refused_by_name():
    _need_typst()
    here = _project("fr", key=("refused",))
    _set_rows(here, ['row("Architecte", value: "architect")'])
    run = subprocess.run([project.typst_executable(), *documents.compile_args(here, "cu", [])],
                         capture_output=True, text=True, encoding="utf-8", errors="replace")
    assert run.returncode != 0
    message = conftest.panic_message(run.stderr) or run.stderr
    assert "architect" in message and "is no field of the .woodcore" in message and '"author"' in message, message
    _set_rows(here, ['row("Architecte")'])
    run = subprocess.run([project.typst_executable(), *documents.compile_args(here, "cu", [])],
                         capture_output=True, text=True, encoding="utf-8", errors="replace")
    message = conftest.panic_message(run.stderr) or run.stderr
    assert run.returncode != 0 and "names no field of the .woodcore" in message, message


def test_title_typ_is_never_written_over():
    here = _project("en", key=("kept",))
    own = "// mine\n#let title-page(document: \"rs\") = [My own #document title page] + pagebreak()\n"
    here.title_typ.write_text(own, encoding="utf-8", newline="\n")
    assert project_template.ensure_title(here) is None
    assert here.title_typ.read_text(encoding="utf-8") == own
    if conftest.have_typst():
        assert _page(_compile(here, "bp"))[0] == "My own bp title page"


def test_a_template_without_title_typ_gets_standards_and_its_documents_compile():
    folder = conftest.tmpdir("title_template") / "ohne-titel"
    shutil.copytree(templates.standard().folder, folder)
    (folder / "Statischer Bericht (typst)" / project.TITLE_FILE).unlink()
    entry = folder / "Statischer Bericht (typst)" / "Statischer Rapport.typ"
    text = entry.read_text(encoding="utf-8")
    start, end = text.index('#import "title.typ"'), text.index("#title-page(")   # the template's own literal, relative on purpose
    # a report keeping a title page of its own in its entry, as one saved before title.typ did
    entry.write_text(text[:start] + text[start:end].replace('#import "title.typ": title-page\n', "")   # relative on purpose
                     + text[end:].replace('#title-page(document: "rs")', "= Mein eigenes Titelblatt\n#pagebreak()", 1), encoding="utf-8", newline="\n")
    template = templates.read(folder, "user")
    assert not template.error, template.error
    here = project_template.create(conftest.tmpdir("title_template_project") / "P", "P", template=template, document_language="de")
    assert here.title_typ.read_bytes() == documents.relocate_config_text(here, project_template.standard_title().read_text(encoding="utf-8")).encode("utf-8")
    if conftest.have_typst():
        for mode in ("cu", "bp"):
            assert _page(_compile(here, mode))[0] == documents.MODE_NAMES["de"][mode], mode
        assert any(line.endswith("Mein eigenes Titelblatt") for line in _page(_compile(here, "rs"))), "the report keeps the title page its entry writes"


def test_the_archive_and_the_stamps_fallback_take_title_typ():
    here = _project("de")
    for mode in project.MODES:
        assert here.title_typ in stamps.enumerated(here, mode), mode
        names = [name for _path, name in archive_export.members_of_document(here, mode)]
        assert here.rel(here.title_typ) in names, (mode, names[:20])


def test_a_project_saved_as_a_template_carries_title_typ():
    here = _project("de", key=("saved",))
    marked = here.title_typ.read_text(encoding="utf-8") + "\n// my own edit\n"
    here.title_typ.write_text(marked, encoding="utf-8", newline="\n")
    saved = None
    try:
        saved = templates.save_project(here, "Mit Titel", "user", {})
        assert (saved.folder / here.rel(here.title_typ)).read_text(encoding="utf-8") == marked
    finally:
        if saved is not None:
            shutil.rmtree(saved.folder, ignore_errors=True)


def _bfh_checks(here, lang, label):
    school = {
        "de": ("Architektur, Holz und Bau", "BSc Holztechnik", "Biel, ", "Betreuung"),
        "fr": ("Architecture, bois et génie civil", "BSc Technique du bois", "Bienne, le ", "Encadrement"),
        "en": ("Architecture, Wood and Civil Engineering", "BSc Wood Technology", "Biel/Bienne, ", "Supervision"),
    }
    for mode in project.MODES:
        pdf = _compile(here, mode)
        text = "\n".join(_page(pdf))
        where = f"{label} {lang}/{mode}"
        department, programme, place, supervision = school[lang]
        assert department in text and programme in text and supervision in text, (where, text)
        # the title is letter-spaced: where the fallback font's spacing is wide, the PDF's text carries a space between the letters
        assert documents.MODE_NAMES[lang][mode].upper().replace(" ", "") in text.replace(" ", ""), (where, text)
        assert any(line.startswith(place) for line in _page(pdf)), (where, text)
        others = [w for other in LANGS if other != lang for w in school[other][:2]]
        assert not [w for w in others if w in text], (where, text)
        # the BFH's running footer on the pages after the title page, which has none
        assert "Bern University of Applied Sciences" in "\n".join(_page(pdf, 1)), where


def test_the_bfh_form_prints_its_title_page_in_the_three_documents_in_the_projects_language():
    """The BFH is a form (calc/forms.py, the builtin `bfh`) since 06.10.2026: a new project made with it carries the form's title.typ, and its three documents print the BFH's title page, its school's words in the project's language."""
    import forms
    _need_typst()
    for lang in LANGS:
        here = _project(lang, form="bfh", key=("bfh-form", lang))
        assert forms.current(here).ref == "builtin:bfh"
        assert here.title_typ.read_bytes() == documents.relocate_config_text(here, (conftest.ROOT / "templates" / "forms" / "bfh" / project.TITLE_FILE).read_text(encoding="utf-8")).encode("utf-8"), "the BFH form's title.typ"
        _bfh_checks(here, lang, "bfh form")


def test_the_office_s_copy_of_the_bfh_form_is_the_builtin_one_and_is_offered_as_shared():
    """The templates repository beside the program carries the BFH form in `forms/bfh-academique/` for the office's shared folder: file for file the builtin `bfh`, and offered as `shared:bfh-academique` once the settings name that folder."""
    import forms
    shared = conftest.ROOT.parent / "templates"
    copy = shared / "forms" / "bfh-academique"
    if not (copy / forms.FILE).is_file():
        raise Skip(f"the office's templates are not beside the program ({shared})")
    builtin = conftest.ROOT / "templates" / "forms" / "bfh"
    for name in sorted(p.name for p in builtin.iterdir()):
        assert (copy / name).read_bytes() == (builtin / name).read_bytes(), name
    settings = {"templates": {"shared_folder": str(shared)}}
    found = forms.find("shared:bfh-academique", settings)
    assert found.place == "shared" and not found.error and found.name("fr") == "BFH – Académique"


def test_the_bfh_template_prints_its_title_page_in_the_three_documents_in_the_projects_language():
    """The old BFH project template, still where an engineer saved a project from it: a project made from it keeps its own report, config.typ and title page -- the legacy path (calc/project_template.py)."""
    if not (BFH / "template.json").is_file():
        raise Skip(f"the BFH template is not beside the program ({BFH})")
    _need_typst()
    template = templates.read(BFH, "shared")
    assert not template.error, template.error
    for lang in LANGS:
        here = _project(lang, template=template, key=("bfh", lang))
        assert here.title_typ.read_bytes() == (BFH / "Statischer Bericht (typst)" / project.TITLE_FILE).read_bytes(), "the BFH's title.typ"
        _bfh_checks(here, lang, "bfh")
