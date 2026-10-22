"""Forms: the look of a project's three documents (calc/forms.py, templates/forms/, docs/conventions/build-and-release.md §12, the engineer's decision of 06.10.2026).

What is held here. The three builtin forms -- neutral, compact and bfh -- are listed, found by reference, by id and by name in any language, and each is sound. A form with a defect planted in it is refused by name and listed with its reason. `config_text` writes the new-format config.typ and `is_form_config` tells it from a monolithic one. `apply` switches a project's form all or nothing: the old `Template/`, `title.typ` and a monolithic config.typ go to the archives and are never deleted, the project's language survives, the engineer's adjustments in a new-format config.typ survive a second switch and win over the form's, and a failure half way puts everything back. Every builtin form compiles the project's three documents, and the BFH form sets all its text in Lucida Sans -- body, tables, captions -- with Libertinus nowhere. The engineer's own forms are imported, saved from a project and archived.
"""

import hashlib
import json
import os
import re
import shutil
import subprocess
from pathlib import Path
import sys

import conftest
from conftest import Skip

if str(conftest.CALC / "tools") not in sys.path:
    sys.path.insert(0, str(conftest.CALC / "tools"))
import documents  # noqa: E402
import forms  # noqa: E402
import project  # noqa: E402
import project_template  # noqa: E402
import templates  # noqa: E402

PEOPLE = {"author": "Lea Exempel", "client": "Urs Bauherr", "address": "Bahnhofstrasse 1, 2502 Biel", "number": "2026-17", "company": "Muster Holzbau SA"}
BUILTIN = ("neutral", "compact", "bfh")


def _need_typst():
    if not conftest.have_typst():
        raise Skip("no typst on the path")


def _need_font(family):
    """Skip where Typst does not find `family` -- a font of the system, not of Woodcore's (Lucida Sans ships with Windows, not with a Linux runner)."""
    import subprocess
    listed = subprocess.run(["typst", "fonts"], capture_output=True, text=True, encoding="utf-8").stdout.splitlines()
    if family not in (line.strip() for line in listed):
        raise Skip(f"{family} is not installed")


def _new(name, lang="de"):
    """A project in `lang`, made in this run's own folder **as one was before forms**: from a project template of the engineer's own that is Standard's old skeleton, so that its config.typ is the monolithic one and its title.typ the old Standard's (a new project made from Standard now has the neutral form already)."""
    import shutil
    import templates
    folder = conftest.tmpdir(name + "_template") / "Vorlage"
    shutil.copytree(templates.standard().folder, folder)
    legacy = templates.read(folder, "user")
    assert not legacy.error, legacy.error
    return project_template.create(conftest.tmpdir(name) / "Halle", "Halle Nord", template=legacy, document_language=lang, report_language=lang, **PEOPLE)


def _compile(here, mode, flags=()):
    run = subprocess.run([project.typst_executable(), *documents.compile_args(here, mode, list(flags))],
                         capture_output=True, text=True, encoding="utf-8", errors="replace")
    assert run.returncode == 0, f"{here.name} {mode}: {run.stderr[:3000]}"
    return here.document_pdf(mode)


def _tree(root):
    """{relative path: sha256} of every file under `root`, for a before and after that must be identical."""
    root = Path(root)
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(root.rglob("*")) if p.is_file()}


def _fonts(pdf):
    """The base fonts every page of `pdf` uses, subset tags taken off."""
    from pypdf import PdfReader
    names = set()

    def walk(resources):
        resources = resources.get_object() if resources is not None else None
        if not resources:
            return
        for font in (resources.get("/Font") or {}).values():
            base = str(font.get_object().get("/BaseFont", ""))
            names.add(base.split("+")[-1].lstrip("/"))
        for xobject in (resources.get("/XObject") or {}).values():
            walk(xobject.get_object().get("/Resources"))

    for page in PdfReader(str(pdf)).pages:
        walk(page.get("/Resources"))
    return names


def _runs(pdf, text):
    """(font size, x position in pt) of every run of the first page of `pdf` containing `text`."""
    from pypdf import PdfReader
    found = []

    def visit(run, cm, tm, _font, size):
        if text in run:
            found.append((round(size, 1), round(cm[4] + tm[4], 1)))

    PdfReader(str(pdf)).pages[0].extract_text(visitor_text=visit)
    return found


# --- the builtin forms ----------------------------------------------------------------------------

def test_the_three_builtin_forms_are_listed_neutral_first_and_each_is_sound():
    found = [f for f in forms.list_forms() if f.place == "builtin"]
    assert [f.id for f in found] == ["neutral", "bfh", "compact"], [f.id for f in found]
    assert {f.id for f in found} == set(BUILTIN)
    for form in found:
        assert not form.error, (form.id, form.error)
        assert form.ref == f"builtin:{form.id}" and form.read_only
        for lang in forms.LANGUAGES:
            assert form.name(lang) and form.name(lang) != form.id, (form.id, lang)
            assert form.description(lang), (form.id, lang)
        assert "ß" not in json.dumps(form.meta, ensure_ascii=False), form.id
        assert form.template_typ.is_file() and form.title_typ.is_file()
    assert forms.default().id == "neutral"
    # a form is the layout alone: no client, no number, no date in what it ships
    for form in found:
        for path in (form.template_typ,):
            assert "project-info" not in path.read_text(encoding="utf-8"), path


def test_a_form_is_found_by_reference_by_id_and_by_a_name_in_any_language():
    assert forms.find("builtin:bfh").id == "bfh"
    assert forms.find("bfh").ref == "builtin:bfh"
    assert forms.find("").ref == "builtin:neutral" and forms.find(None).ref == "builtin:neutral"
    # the styles of the same names are the forms: `neutral` and `compact` resolve
    assert forms.find("neutral").ref == "builtin:neutral" and forms.find("compact").ref == "builtin:compact"
    for text in ("Neutre", "NEUTRAL", "Kompakt", "compact", "BFH – Akademisch", "bfh – académique"):
        assert forms.find(text).id in BUILTIN, text
    assert forms.find("Kompakt").id == "compact" and forms.find("Neutre").id == "neutral"
    for ref in ("builtin:nope", "nope", "user:neutral"):
        try:
            forms.find(ref)
        except forms.FormError as exc:
            assert exc.code == "no_such_form" and "neutral" in str(exc) and "bfh" in str(exc), exc
        else:
            raise AssertionError(f"{ref!r} found")


def _shared_place(name, plant=None):
    """A shared folder of the office holding a copy of the builtin `neutral` form named `mine`, `plant` (a function of its folder) breaking it; returns (settings, form folder)."""
    root = conftest.tmpdir(name)
    folder = root / "forms" / "mine"
    shutil.copytree(forms.place_dir("builtin") / "neutral", folder)
    if plant:
        plant(folder)
    return {"templates": {"shared_folder": str(root)}}, folder


def test_a_form_with_a_defect_is_listed_with_its_reason_and_refused_by_name():
    def corrupt(folder):
        (folder / "form.json").write_text("{not json", encoding="utf-8")

    def wrong_format(folder):
        meta = json.loads((folder / "form.json").read_text(encoding="utf-8"))
        meta["format"] = "woodcore-template"
        (folder / "form.json").write_text(json.dumps(meta), encoding="utf-8")

    def no_function(folder):
        (folder / "template.typ").write_text("#let look(doc) = doc\n", encoding="utf-8")

    def no_title(folder):
        (folder / "title.typ").unlink()

    def title_without_function(folder):
        (folder / "title.typ").write_text("// nothing\n", encoding="utf-8")

    def foreign_language(folder):
        meta = json.loads((folder / "form.json").read_text(encoding="utf-8"))
        meta["name"]["it"] = "Neutra"
        (folder / "form.json").write_text(json.dumps(meta), encoding="utf-8")

    def no_name(folder):
        meta = json.loads((folder / "form.json").read_text(encoding="utf-8"))
        meta["name"] = {}
        (folder / "form.json").write_text(json.dumps(meta), encoding="utf-8")

    for index, (plant, word) in enumerate(((corrupt, "cannot be read"), (wrong_format, "woodcore-form"), (no_function, "#let template("),
                                           (no_title, "title.typ"), (title_without_function, "#let title-page("), (foreign_language, "no language"),
                                           (no_name, "no name"))):
        settings, folder = _shared_place(f"forms_bad_{index}", plant)
        listed = [f for f in forms.list_forms(settings) if f.place == "shared"]
        assert len(listed) == 1 and listed[0].error, (plant.__name__, listed)
        assert word in listed[0].error, (plant.__name__, listed[0].error)
        try:
            forms.find("shared:mine", settings)
        except forms.FormError as exc:
            assert exc.code == "form_unusable", (plant.__name__, exc.code)
        else:
            raise AssertionError(f"{plant.__name__}: found a form with a defect")
        try:
            forms.apply(_new(f"forms_bad_apply_{index}"), listed[0])
        except forms.FormError as exc:
            assert exc.code == "form_unusable"
        else:
            raise AssertionError(f"{plant.__name__}: applied a form with a defect")
    # the sound copy is found
    settings, _ = _shared_place("forms_ok")
    assert forms.find("shared:mine", settings).ref == "shared:mine"
    assert forms.find("mine", settings).place == "shared"


# --- config.typ ----------------------------------------------------------------------------------

def test_the_new_config_states_the_language_and_calls_the_form_and_a_monolithic_one_is_told_apart():
    text = forms.config_text("fr", "CH")
    assert templates._DOC_LANG.search(text).group(2) == "fr" and templates._DOC_REGION.search(text).group(2) == "CH"
    assert templates._CONF.search(text), "the entry files import `conf`"
    assert '#import "/Template/template.typ": template' in text and "show: template.with(lang: doc-lang, region: doc-region)" in text
    assert "\r" not in text
    path = conftest.tmpdir("forms_config") / "config.typ"
    path.write_text(text, encoding="utf-8")
    assert forms.is_form_config(path)
    monolithic = Path(project_template.standard_title()).parent / "config.typ"
    assert monolithic.is_file() and not forms.is_form_config(monolithic) and not forms.is_form_config(path.with_name("absent.typ"))
    for bad in ('de"; #panic("x', "d e"):
        try:
            forms.config_text(bad, "CH")
        except forms.FormError as exc:
            assert exc.code == "invalid"
        else:
            raise AssertionError(f"{bad!r} written into a config")


def test_an_adjustment_written_in_the_new_config_wins_over_the_form():
    _need_typst()
    here = _new("forms_adjust")
    forms.apply(here, "neutral")
    config = here.config_typ
    text = config.read_text(encoding="utf-8")
    marker = "  doc\n}"
    assert marker in text
    config.write_text(text.replace(marker, "  set text(size: 14pt)\n  set page(margin: (left: 4cm, top: 3cm))\n  doc\n}"), encoding="utf-8")
    probe = here.typst_root / "probe_forms.typ"
    probe.write_text('#import "/000-Typst-Config/config.typ": conf\n#show: conf\nAdjusted body text\n', encoding="utf-8")
    pdf = here.typst_root / "probe_forms.pdf"
    run = subprocess.run([project.typst_executable(), "compile", "--root", str(here.typst_root), str(probe), str(pdf)], capture_output=True, text=True, encoding="utf-8", errors="replace")
    assert run.returncode == 0, run.stderr[:2000]
    runs = _runs(pdf, "Adjusted")
    assert runs and runs[0][0] == 14.0, f"the engineer's text size does not win: {runs}"
    assert abs(runs[0][1] - 4 * 28.3465) < 1.0, f"the engineer's left margin does not win (4 cm = 113.4 pt): {runs}"


# --- switching a project's form -------------------------------------------------------------------

def test_a_form_is_applied_to_a_project_the_old_files_archived_and_its_language_kept():
    here = _new("forms_apply", "fr")
    old_config = here.config_typ.read_bytes()
    old_title = here.title_typ.read_bytes()
    assert forms.current(here) is None and not forms.is_form_config(here.config_typ)
    done = forms.apply(here, forms.find("bfh"))
    root = here.typst_root
    # the form is in place, stamped with where it came from
    meta = json.loads((here.template_dir / "form.json").read_text(encoding="utf-8"))
    assert (meta["id"], meta["place"], meta["format"]) == ("bfh", "builtin", "woodcore-form"), meta
    assert (here.template_dir / "template.typ").is_file() and (here.template_dir / "logo-bfh.png").is_file()
    assert not (here.template_dir / "title.typ").exists(), "title.typ belongs at the top of the project"
    import documents   # the form's title page as the project holds it: its paths in 000-Typst-Config/ laid out by folders (issue #64)
    assert here.title_typ.read_bytes() == documents.relocate_config_text(here, (forms.place_dir("builtin") / "bfh" / "title.typ").read_text(encoding="utf-8")).encode("utf-8")
    assert f'import "{here.from_root(here.template_dir / "template.typ")}"' in here.title_typ.read_text(encoding="utf-8")
    current = forms.current(here)
    assert current is not None and current.ref == "builtin:bfh" and current.name("de") == "BFH – Akademisch"
    # the config is the new format and keeps the project's language
    assert forms.is_form_config(here.config_typ)
    assert templates._DOC_LANG.search(here.config_typ.read_text(encoding="utf-8")).group(2) == "fr"
    # nothing was deleted: the old config and title are in the archives
    assert done.config_written and done.archive is not None and done.archive.parent == here.archives_dir
    assert done.archive.name.endswith("-forme"), done.archive
    assert (done.archive / "config.typ").read_bytes() == old_config and (done.archive / "title.typ").read_bytes() == old_title
    assert not (done.archive / "Template").exists(), "there was no Template/ to keep"
    # no staging folder is left behind
    assert not [p for p in root.iterdir() if p.name.startswith(forms.STAGING)], list(root.iterdir())


def test_a_second_switch_keeps_the_engineers_adjustments_and_archives_the_old_form():
    here = _new("forms_second", "en")
    forms.apply(here, "neutral")
    config = here.config_typ
    text = config.read_text(encoding="utf-8")
    mine = "  set text(size: 9pt) // my own adjustment\n"
    config.write_text(text.replace("  doc\n}", mine + "  doc\n}"), encoding="utf-8")
    config_before = config.read_bytes()
    title_before = here.title_typ.read_bytes()
    here.title_typ.write_text(here.title_typ.read_text(encoding="utf-8") + "\n// my own row\n", encoding="utf-8")
    edited_title = here.title_typ.read_bytes()
    first_template = _tree(here.template_dir)
    done = forms.apply(here, "bfh")
    assert config.read_bytes() == config_before, "the engineer's config.typ was touched"
    assert not done.config_written
    assert "my own adjustment" in config.read_text(encoding="utf-8")
    assert forms.current(here).id == "bfh"
    # title.typ replaced by the form's, and the engineer's edited one is in the archives, with the old Template/
    assert here.title_typ.read_bytes() != edited_title and b"my own row" not in here.title_typ.read_bytes()
    assert (done.archive / "title.typ").read_bytes() == edited_title and edited_title != title_before
    assert _tree(done.archive / "Template") == first_template
    assert not (done.archive / "config.typ").exists(), "a config.typ already in the new format is neither moved nor archived"
    # a third switch, within the same second, gets an archive of its own
    again = forms.apply(here, "compact")
    assert again.archive != done.archive and again.archive.is_dir() and done.archive.is_dir()
    assert forms.current(here).id == "compact" and (here.template_dir / "logo-bfh.png").exists() is False


def test_a_failure_while_applying_puts_everything_back():
    here = _new("forms_fail")
    forms.apply(here, "neutral")
    config = here.config_typ
    config.write_text(config.read_text(encoding="utf-8").replace("  doc\n}", "  set text(size: 9pt)\n  doc\n}"), encoding="utf-8")
    before = _tree(here.root)
    archives_before = _tree(here.archives_dir) if here.archives_dir.exists() else {}
    real = forms._retried
    calls = {"n": 0}

    def failing(call, *args):
        calls["n"] += 1
        if calls["n"] == 5:   # the staged form.json is call 1, the two archivings 2 and 3, the new Template/ placed 4: the new title.typ is the one that fails
            raise OSError("a file held by another program")
        return real(call, *args)

    forms._retried = failing
    try:
        try:
            forms.apply(here, "bfh")
        except forms.FormError as exc:
            assert exc.code == "write_failed", exc.code
        else:
            raise AssertionError("the failure was swallowed")
    finally:
        forms._retried = real
    assert calls["n"] >= 5
    assert _tree(here.root) == before, "the project is not what it was"
    assert forms.current(here).id == "neutral"
    leftover = {k: v for k, v in _tree(here.archives_dir).items() if k not in archives_before} if here.archives_dir.exists() else {}
    assert not leftover, f"an archive of a switch that did not happen is left: {list(leftover)}"


def test_a_project_without_forms_asks_for_none_and_apply_refuses_a_missing_reference():
    here = _new("forms_none")
    assert forms.current(here) is None
    try:
        forms.apply(here, "nope")
    except forms.FormError as exc:
        assert exc.code == "no_such_form"
    else:
        raise AssertionError("applied a form that does not exist")
    assert not (here.template_dir).exists()


# --- compiling ----------------------------------------------------------------------------------

def test_every_builtin_form_compiles_the_three_documents():
    _need_typst()
    for index, form in enumerate(BUILTIN):
        here = _new(f"forms_compile_{index}", "de")
        forms.apply(here, form)
        for mode in project.MODES:
            pdf = _compile(here, mode)
            assert pdf.is_file() and pdf.stat().st_size > 1000, (form, mode)


def test_the_bfh_form_sets_all_its_text_in_lucida_sans_and_no_libertinus():
    _need_typst()
    _need_font("Lucida Sans")
    here = _new("forms_bfh_fonts", "de")
    forms.apply(here, "bfh")
    # the statical report carries tables, captions, the outline and the engine's lines; the convention headings and paragraphs
    for mode in project.MODES:
        names = _fonts(_compile(here, mode))
        where = f"{mode}: {sorted(names)}"
        assert any("LucidaSans" in name for name in names), f"Lucida Sans is not used -- {where}"
        assert not any("Libertinus" in name for name in names), f"Libertinus is used -- {where}"
        extra = {name for name in names if "LucidaSans" not in name and "Math" not in name and "NewComputerModern" not in name and "SegoeUI" not in name and "Arial" not in name}
        assert not extra, f"another font than the form's -- {where}"
    # the neutral form still sets the body in Typst's own serif
    neutral = _new("forms_neutral_fonts", "de")
    forms.apply(neutral, "neutral")
    assert any("Libertinus" in name for name in _fonts(_compile(neutral, "rs")))


# --- the engineer's own forms -----------------------------------------------------------------------

def test_a_project_is_saved_as_a_form_imported_back_and_archived():
    settings = {"templates": {"shared_folder": str(conftest.tmpdir("forms_office"))}}
    # a project of the engineer's, written in the bfh form with its own row
    here = _new("forms_mine", "de")
    forms.apply(here, "bfh")
    here.title_typ.write_text(here.title_typ.read_text(encoding="utf-8") + "\n// my row\n", encoding="utf-8")
    try:
        forms.save_from_project(here, "BFH", settings=settings)
    except forms.FormError as exc:
        assert exc.code == "name_is_builtin"
    else:
        raise AssertionError("saved a form under a builtin name")
    for refused, code in (("", "no_name"),):
        try:
            forms.save_from_project(here, refused, settings=settings)
        except forms.FormError as exc:
            assert exc.code == code
    saved = forms.save_from_project(here, "Mein Büro", place="shared", settings=settings, description="Für alle Berichte")
    assert saved.place == "shared" and not saved.error and saved.ref == "shared:Mein Büro"
    assert all(saved.name(lang) == "Mein Büro" for lang in forms.LANGUAGES) and saved.description("fr") == "Für alle Berichte"
    assert b"my row" in saved.title_typ.read_bytes() and (saved.folder / "logo-bfh.png").is_file()
    assert saved.meta.get("id") is None, "the stamp of a project's Template/ is not the saved form's own id"
    assert forms.find("Mein Büro", settings).ref == "shared:Mein Büro"
    # a second save of the same name does not overwrite
    second = forms.save_from_project(here, "Mein Büro", place="shared", settings=settings)
    assert second.folder != saved.folder and saved.folder.is_dir()
    # a project from before forms has nothing to save
    old = _new("forms_mine_old", "de")
    try:
        forms.save_from_project(old, "X", place="shared", settings=settings)
    except forms.FormError as exc:
        assert exc.code == "no_project_form"
    else:
        raise AssertionError("saved a form out of a project with none")
    # a form applied from there stamps its place
    other = _new("forms_mine_apply", "de")
    forms.apply(other, saved)
    assert forms.current(other).place == "shared" and b"my row" in other.title_typ.read_bytes()
    # archived, never deleted
    moved = forms.archive(second)
    assert moved.is_dir() and not second.folder.exists() and moved.parent.name == forms.ARCHIVES
    assert [f.ref for f in forms.list_forms(settings) if f.place == "shared"] == ["shared:Mein Büro"], "the archives are listed as a form"
    try:
        forms.archive(forms.find("neutral"))
    except forms.FormError as exc:
        assert exc.code == "read_only"
    else:
        raise AssertionError("archived a builtin form")


def test_a_folder_is_imported_into_the_engineers_own_place_and_never_over_a_form_unasked():
    user_root = forms.place_dir("user")
    mine = user_root / "Importiert"
    outside = conftest.tmpdir("forms_import") / "Importiert"
    shutil.copytree(forms.place_dir("builtin") / "compact", outside)
    try:
        found = forms.import_folder(outside)
        assert found.place == "user" and found.folder == mine and not found.error
        assert forms.find("user:Importiert").ref == "user:Importiert"
        for refused, code in ((outside.parent / "absent", "not_a_folder"), (outside.parent, "no_form")):
            try:
                forms.import_folder(refused)
            except forms.FormError as exc:
                assert exc.code == code, (refused, exc.code)
            else:
                raise AssertionError(f"{refused} imported")
        try:
            forms.import_folder(outside)
        except forms.FormError as exc:
            assert exc.code == "exists"
        else:
            raise AssertionError("imported over a form")
        (outside / "title.typ").write_text(((outside / "title.typ").read_text(encoding="utf-8")) + "\n// new\n", encoding="utf-8")
        replaced = forms.import_folder(outside, replace=True)
        assert b"// new" in replaced.title_typ.read_bytes()
        kept = [p for p in (user_root / forms.ARCHIVES).iterdir()] if (user_root / forms.ARCHIVES).is_dir() else []
        assert kept and any((p / "title.typ").is_file() and b"// new" not in (p / "title.typ").read_bytes() for p in kept), "the replaced form is not in the archives"
        # a folder named like a builtin form is refused
        builtin_named = outside.parent / "bfh"
        shutil.copytree(forms.place_dir("builtin") / "compact", builtin_named)
        try:
            forms.import_folder(builtin_named)
        except forms.FormError as exc:
            assert exc.code == "name_is_builtin"
        else:
            raise AssertionError("imported over a builtin name")
        # a broken folder is refused naming why, and writes nothing
        broken = outside.parent / "Kaputt"
        shutil.copytree(forms.place_dir("builtin") / "compact", broken)
        (broken / "template.typ").write_text("nothing\n", encoding="utf-8")
        try:
            forms.import_folder(broken)
        except forms.FormError as exc:
            assert exc.code == "invalid" and "#let template(" in str(exc)
        else:
            raise AssertionError("imported a broken form")
        assert not (user_root / "Kaputt").exists()
    finally:
        shutil.rmtree(user_root, ignore_errors=True)


def test_the_schema_is_what_every_builtin_form_json_says():
    schema = json.loads((conftest.ROOT / "schemas" / "form.schema.json").read_text(encoding="utf-8"))
    assert schema["properties"]["format"]["const"] == forms.FORMAT == "woodcore-form"
    assert schema["properties"]["schema_version"]["const"] == forms.SCHEMA_VERSION
    assert tuple(schema["properties"]["place"]["enum"]) == forms.PLACES
    for name in BUILTIN:
        meta = json.loads((forms.place_dir("builtin") / name / "form.json").read_text(encoding="utf-8"))
        assert meta["schema_version"] == "1.0" and set(meta["name"]) == set(forms.LANGUAGES) == set(meta["description"])
        assert re.match(r"^\{\n  \"schema_version\"", (forms.place_dir("builtin") / name / "form.json").read_text(encoding="utf-8"))
