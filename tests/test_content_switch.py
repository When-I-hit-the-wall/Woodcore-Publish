"""Switching a document's content template (calc/content_switch.py): the document and a template compared section by section, and what the engineer keeps, takes or drops written back -- the engineer's decision of 06.10.2026.

What is held here: a document made from a template compares `same` everywhere and a switch at the defaults writes nothing; a section edited compares `differs` -- its objects saying which one --, one removed `template_only`, one of the engineer's own `document_only` and placed after the section that preceded it; `keep`, `take` and `drop` write the structure, the files and the entry the choices say, every replaced or dropped file archived and none deleted, and the document still compiles; a shared section dropped is unshared in the other document (sharing.reconcile); the report likewise, numbered again 001, 002 … with its include lines; a document not laid out with its headings at their level refused; a choice that is none, a node that is none and a file changed since the comparison refused before anything is written; and a write that fails midway leaving the project byte for byte as it was.

Every file a check writes goes into this process's own temporary folder.
"""

import shutil
import subprocess
from pathlib import Path

import conftest
from conftest import ROOT, Skip

import content_switch
import doc_templates
import documents
import project
import project_template
import structure
import templates

_PROJECTS = {}


def _base(lang):
    """A new project written in `lang`, made once per run -- its convention and base the builtin templates', its report **the old skeleton's** (a project template of the engineer's that is Standard's old skeleton): a project made from Standard now has the rs content template's report, which would leave nothing for a switch of the report's content to change."""
    if lang not in _PROJECTS:
        folder = conftest.tmpdir(f"cs_base_template_{lang}") / "Vorlage"
        shutil.copytree(templates.standard().folder, folder)
        legacy = templates.read(folder, "user")
        assert not legacy.error, legacy.error
        _PROJECTS[lang] = project_template.create(conftest.tmpdir(f"cs_base_{lang}") / "Halle", "Halle", template=legacy, document_language=lang, report_language=lang)
    return _PROJECTS[lang]


def _project(name, lang="fr"):
    """A copy of the base project of `lang`, for one check to change."""
    base = _base(lang)
    target = conftest.tmpdir(name) / "Halle"
    shutil.copytree(base.root, target, ignore=shutil.ignore_patterns("_Archiv", "stamps", "*.pdf"))
    return project.Project.load(target / base.file.name)


def _read(path):
    with open(path, encoding="utf-8", newline="") as handle:
        return handle.read()


def _tree(root):
    """{relative path: bytes} of every file under `root`, and every folder (None): a switch put back leaves no folder of its own behind either."""
    return {p.relative_to(root).as_posix(): (p.read_bytes() if p.is_file() else None) for p in sorted(Path(root).rglob("*"))}


def _refused(code, call, *args, **kwargs):
    try:
        call(*args, **kwargs)
    except content_switch.ContentSwitchError as exc:
        assert exc.code == code, f"refused with {exc.code!r} and not {code!r}: {exc}"
        assert exc.code in content_switch.CODES
        return exc
    raise AssertionError(f"accepted, and {code!r} was expected")


def _compile(here, mode):
    if not conftest.have_typst():
        raise Skip("no typst on the path")
    run = subprocess.run([project.typst_executable(), *documents.compile_args(here, mode, [])],
                         capture_output=True, text=True, encoding="utf-8", errors="replace")
    assert run.returncode == 0, f"{mode}: {run.stderr[:3000]}"
    from pypdf import PdfReader
    return " ".join(" ".join((page.extract_text() or "").split()) for page in PdfReader(str(here.document_pdf(mode))).pages)


def _leaf_ids(here, mode):
    return [node["id"] for node, _d in structure.leaves(structure.read(here.structure_file(mode)))]


# --- a CU ----------------------------------------------------------------------------------------------

def test_a_document_made_from_its_template_compares_same_and_the_defaults_write_nothing():
    here = _project("cs_same")
    for mode in ("cu", "bp"):
        comparison = content_switch.compare(here, mode)
        assert comparison.template_ref == f"builtin:{mode}/standard" and comparison.language == "fr"
        counts = comparison.counts()
        assert counts["same"] == len(_leaf_ids(here, mode)) and counts["same"] == sum(counts.values()), counts
        assert all(n.status == "same" for n in comparison.walk()), [n.id for n in comparison.walk() if n.status != "same"]
        assert all(o.status == "same" for n in comparison.sections() for o in n.children)
        before = _tree(here.root)
        result = content_switch.apply(here, mode, comparison)
        assert not result.changed and not result.structure and not result.entry, result
        assert _tree(here.root) == before, "a switch at the defaults on a document equal to its template wrote something"
    assert [t.ref for t in content_switch.templates_for(here, "rs")] == ["builtin:rs/standard"]
    assert "builtin:cu/standard" in [t.ref for t in content_switch.templates_for(here, "cu")]


def _edited(name):
    """A project whose convention: has `purpose` edited (a paragraph changed and one of its own added), `radon` removed, and a section of the engineer's own, `my-own`, right after `purpose`."""
    here = _project(name)
    folder = here.document_dir("cu")
    path = folder / "Sections" / "purpose.typ"
    text = _read(path)
    first = text.index("// woodcore:object text p1\n") + len("// woodcore:object text p1\n")
    end = text.index("// woodcore:/object p1", first)
    text = text[:first] + "Mon objet à moi.\n" + text[end:] + "\n// woodcore:object text mine\nUn paragraphe à moi.\n// woodcore:/object mine\n"
    path.write_text(text, encoding="utf-8", newline="")
    structure.remove_section(here, "cu", "radon")
    parent = structure.find(structure.read(here.structure_file("cu")), "purpose")[2]
    structure.add_section(here, "cu", parent["id"], 1, "my-own", "Ma section")
    return here


def test_an_edited_a_removed_and_an_own_section_are_said_so_and_placed():
    here = _edited("cs_statuses")
    comparison = content_switch.compare(here, "cu")
    purpose, mine, radon = comparison.find("purpose"), comparison.find("my-own"), comparison.find("radon")
    assert purpose.status == "differs" and purpose.choices == ("keep", "take", "drop") and purpose.default == "keep"
    objects = {o.id: o.status for o in purpose.children}
    assert objects["title"] == "same" and objects["p1"] == "differs" and objects["mine"] == "document_only", objects
    assert mine.status == "document_only" and mine.title_document == "Ma section" and mine.title_template is None and mine.default == "keep"
    assert radon.status == "template_only" and radon.choices == ("take", "skip") and radon.default == "take" and radon.file_document is None
    chapter = comparison.find(purpose.parent)
    ids = [n.id for n in chapter.children]
    assert ids[ids.index("purpose") + 1] == "my-own", "a section of the engineer's own stands after the one that preceded it in the document"
    counts = comparison.counts()
    assert counts["differs"] == 1 and counts["document_only"] == 1 and counts["template_only"] == 1, counts
    assert comparison.default_choices()["radon"] == "take"


def test_keep_take_and_drop_write_the_structure_the_files_and_the_entry_and_archive_what_they_replace():
    here = _edited("cs_apply")
    folder = here.document_dir("cu")
    edited = _read(folder / "Sections" / "purpose.typ")
    own = _read(folder / "Sections" / "my-own.typ")
    template_purpose = _read(doc_templates.find("builtin:cu/standard").language_dir("fr") / "Sections" / "purpose.typ")
    comparison = content_switch.compare(here, "cu")
    # settlements is shared with the base de projet: dropped here, it is shared with nobody there any more
    assert "bp" in comparison.find("settlements").shared_with
    result = content_switch.apply(here, "cu", comparison, {"purpose": "take", "my-own": "drop", "radon": "skip", "settlements": "drop"})
    assert result.structure and result.entry
    ids = _leaf_ids(here, "cu")
    assert "my-own" not in ids and "radon" not in ids and "settlements" not in ids and "purpose" in ids
    assert _read(folder / "Sections" / "purpose.typ") == template_purpose, "taken: the template's text"
    assert not (folder / "Sections" / "my-own.typ").exists() and not (folder / "Sections" / "settlements.typ").exists()
    archived = {to.name.split("-", 2)[2]: _read(to) for _from, to in result.archived}
    assert set(archived) == {"purpose.typ", "my-own.typ", "settlements.typ"}, sorted(archived)
    assert archived["purpose.typ"] == edited and archived["my-own.typ"] == own, "what was replaced and dropped is kept, never deleted"
    assert all(to.parent == folder / "Sections" / "archives" for _from, to in result.archived)
    entry = _read(here.document_typ("cu"))
    assert '"Sections/my-own.typ"' not in entry and '"Sections/settlements.typ"' not in entry and '#include "Sections/purpose.typ"' in entry
    bp = structure.find(structure.read(here.structure_file("bp")), "settlements")[0]
    assert "cu" not in bp.get("shared_with", ()), "the other document follows the tags"
    # a second comparison sees what was written
    again = content_switch.compare(here, "cu")
    assert again.find("purpose").status == "same" and again.find("settlements").status == "template_only" and again.find("my-own") is None
    # and taking back what was removed brings its file back at its place
    content_switch.apply(here, "cu", again, {"radon": "take", "settlements": "take"})
    assert "radon" in _leaf_ids(here, "cu") and (folder / "Sections" / "radon.typ").is_file()
    assert content_switch.compare(here, "cu").counts()["template_only"] == 0
    text = _compile(here, "cu")
    assert "Convention d'utilisation" in text.replace("’", "'")


def test_a_chapter_with_no_section_left_goes_and_its_file_is_archived():
    here = _project("cs_chapter")
    comparison = content_switch.compare(here, "cu")
    chapter = comparison.nodes[0]
    assert chapter.kind == "group" and chapter.choices == ("keep",)
    choices = {child.id: "drop" for child in chapter.children}
    result = content_switch.apply(here, "cu", comparison, choices)
    held = structure.read(here.structure_file("cu"))
    assert structure.find(held, chapter.id) is None
    assert any(to.name.endswith(f"-{chapter.id}.typ") for _f, to in result.archived), "the chapter's file is archived"
    assert not (here.document_dir("cu") / structure.group_file(chapter.id)).exists()
    again = content_switch.compare(here, "cu")
    assert again.find(chapter.id).status == "template_only"
    _compile(here, "cu")


def test_a_document_not_laid_out_with_its_headings_at_their_level_is_refused():
    here = _project("cs_legacy")
    comparison = content_switch.compare(here, "bp")
    path = here.structure_file("bp")
    source = structure.read(path)
    source.pop("headings")
    structure.write(path, source)
    assert _refused("legacy_headings", content_switch.compare, here, "bp").values["side"] == "document"
    _refused("legacy_headings", content_switch.apply, here, "bp", comparison)


def test_what_cannot_be_chosen_or_has_changed_is_refused_before_anything_is_written():
    here = _edited("cs_refusals")
    comparison = content_switch.compare(here, "cu")
    before = _tree(here.root)
    _refused("unknown_node", content_switch.apply, here, "cu", comparison, {"nope": "keep"})
    exc = _refused("bad_choice", content_switch.apply, here, "cu", comparison, {"radon": "keep"})
    assert exc.values["allowed"] == ["take", "skip"]
    _refused("bad_choice", content_switch.apply, here, "cu", comparison, {"my-own": "take"})
    _refused("wrong_comparison", content_switch.apply, here, "bp", comparison)
    _refused("bad_mode", content_switch.compare, here, "xx")
    _refused("language_missing", content_switch.compare, here, "cu", language="de", template=_saved_one_language(here))
    _refused("mode_mismatch", content_switch.compare, here, "cu", template="builtin:bp/standard")
    _refused("no_such_template", content_switch.compare, here, "cu", template="nope")
    assert _tree(here.root) == before, "a refusal wrote something"
    with open(here.document_dir("cu") / "Sections" / "my-own.typ", "a", encoding="utf-8") as handle:
        handle.write("\nchanged\n")
    assert _refused("changed_meanwhile", content_switch.apply, here, "cu", comparison).values["file"] == "Sections/my-own.typ"
    legacy = project.Project(conftest.tmpdir("cs_refusals_legacy") / "Old.woodcore", {"schema_version": project.SCHEMA_VERSION, "format": project.FORMAT, "name": "Old"})
    _refused("no_such_document", content_switch.compare, legacy, "cu")


def _saved_one_language(here):
    """A copy of the builtin convention in French alone, as a DocTemplate of the engineer's."""
    folder = conftest.tmpdir("cs_one_language") / "Courte"
    if not folder.exists():
        shutil.copytree(doc_templates.find("builtin:cu/standard").folder, folder)
        for lang in ("de", "en"):
            shutil.rmtree(folder / lang)
        import json
        meta = json.loads((folder / "template.json").read_text(encoding="utf-8"))
        meta["languages"] = ["fr"]
        meta["name"] = {"fr": "Courte"}
        meta["description"] = {"fr": "Courte"}
        (folder / "template.json").write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")
    found = doc_templates.read(folder, "cu", "user")
    assert not found.error, found.error
    return found


def test_a_write_that_fails_midway_leaves_the_project_as_it_was():
    for mode, name in (("cu", "cs_fail_cu"), ("rs", "cs_fail_rs")):
        here = _edited(name) if mode == "cu" else _project(name)
        comparison = content_switch.compare(here, mode)
        choices = {"purpose": "take", "my-own": "drop", "radon": "take"} if mode == "cu" else {n.id: "take" for n in comparison.nodes}
        before = _tree(here.root)
        real = content_switch._put
        calls = []

        def failing(path, text):
            calls.append(path)
            if len(calls) == 4:
                raise OSError("the disk is full")
            return real(path, text)

        content_switch._put = failing
        try:
            exc = _refused("write_failed", content_switch.apply, here, mode, comparison, choices)
        finally:
            content_switch._put = real
        assert len(calls) == 4 and "the disk is full" in exc.values["error"]
        assert _tree(here.root) == before, f"{mode}: a failed switch left the project changed"


# --- the report ----------------------------------------------------------------------------------------

def test_the_report_is_compared_by_its_sections_names_and_numbered_again():
    here = _project("cs_report", "en")
    folder = here.document_dir("rs")
    entry = here.document_typ("rs")
    structure.remove_section(here, "rs", "006-nachweise")
    structure.add_section(here, "rs", None, None, "009-fire-safety", "Fire safety")
    entry.write_text(_read(entry).replace('#include "Sections/005-tragwerksanalyse.typ"', '// #include "Sections/005-tragwerksanalyse.typ"'), encoding="utf-8")
    loose = folder / "Sections" / "010-loose.typ"
    loose.write_text("= Loose\n", encoding="utf-8")
    comparison = content_switch.compare(here, "rs")
    assert comparison.template_ref == "builtin:rs/standard" and comparison.language == "en"
    assert [n.id for n in comparison.nodes] == ["einleitung", "grundlagen", "baustoffe", "einwirkungen", "tragwerksanalyse", "nachweise", "literatur", "journal", "fire-safety", "anhang"]
    status = {n.id: n.status for n in comparison.nodes}
    assert status["einleitung"] == "differs" and status["nachweise"] == "template_only" and status["fire-safety"] == "document_only", status
    assert comparison.find("tragwerksanalyse").enabled_document is False
    assert comparison.find("einleitung").title_template == "Introduction" and comparison.find("einleitung").title_document == "Einleitung"
    old_literatur = _read(folder / "Sections" / "007-literatur.typ")
    old_journal = _read(folder / "Sections" / "008-journal.typ")
    choices = {"einleitung": "take", "grundlagen": "take", "nachweise": "skip", "literatur": "drop", "fire-safety": "keep", "anhang": "skip"}   # the template's switched-off annexes (v0.115) are left out
    result = content_switch.apply(here, "rs", comparison, choices)
    names = [name for name, _p in doc_templates.report_includes(_read(entry))]
    assert names == ["001-einleitung.typ", "002-grundlagen.typ", "003-baustoffe.typ", "004-einwirkungen.typ", "005-tragwerksanalyse.typ", "006-journal.typ", "007-fire-safety.typ"], names
    assert ("005-tragwerksanalyse.typ", False) in doc_templates.report_includes(_read(entry)), "a section switched off stays switched off"
    assert _read(folder / "Sections" / "006-journal.typ") == old_journal, "a kept section keeps its text under its new number"
    assert "= Introduction" in _read(folder / "Sections" / "001-einleitung.typ").split("\n")
    assert "= Fire safety" in _read(folder / "Sections" / "007-fire-safety.typ")
    archived = {to.name.split("-", 2)[2]: _read(to) for _f, to in result.archived}
    assert archived["007-literatur.typ"] == old_literatur and "001-einleitung.typ" in archived and "002-grundlagen.typ" in archived, sorted(archived)
    assert not (folder / "Sections" / "008-journal.typ").exists() and not (folder / "Sections" / "009-fire-safety.typ").exists()
    assert loose.is_file(), "a file the report does not include is left alone"
    again = content_switch.compare(here, "rs")
    assert {n.id: n.status for n in again.nodes}["einleitung"] == "same"
    assert again.find("literatur").status == "template_only"
    text = _compile(here, "rs")
    assert "Introduction" in text and "Fire safety" in text


def test_every_refusal_of_the_module_states_a_code_of_the_list():
    import re
    source = _read(ROOT / "calc" / "content_switch.py")
    start = source.index("CODES = (")
    body = source[:start] + source[source.index("\n)", start):]
    stated = set(re.findall(r'_refuse\(\s*"([a-z_]+)"', body))
    assert stated <= set(content_switch.CODES), sorted(stated - set(content_switch.CODES))
    assert len(set(content_switch.CODES)) == len(content_switch.CODES)
    for status in content_switch.STATUSES:
        assert content_switch.DEFAULTS[status] in content_switch.CHOICES[status]
        assert content_switch.GROUP_DEFAULTS[status] in content_switch.GROUP_CHOICES[status]
