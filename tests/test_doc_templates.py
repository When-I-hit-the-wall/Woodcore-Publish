"""Document templates (calc/doc_templates.py, templates/documents/, schemas/document-template.schema.json): what a new Convention d'utilisation or Base de projet is made from.

The two builtin templates, `cu/standard` and `bp/standard`, are the **complete** documents of the section catalogue of the three document modes (work package 3.2), written in French, German and English by `calc/tools/build_document_templates.py` from a catalogue the maintainers keep: every chapter and every lowest-level section in SIA 260's order, the sections switched off where the catalogue switches them off, each section's text as Typst markup and every other block -- a table, the live loads, a list to tick, a choice, a picture, the norms a section names, the signatures -- as the parametric object of `lib/document.typ` that prints it, between its tags and in the canonical form the editor writes back.

What is held here: the two templates found, read and sound in fr, de and en; each language folder **exactly a document's folder** -- one entry file, a structure.json of the right document whose leaves are all there and whose `Sections/` holds nothing else, an entry whose generated block is already what the structure says, root-absolute imports; the section ids valid and unique, every tag paired, every object one call in the canonical form with its arguments in the order of its command's signature; the sections the catalogue shares by default the same file in both documents, between shared tags, `shared_with` naming the other document on both sides; the live loads the `live-load-table` of SIA 261 Tabelle 8 in both, q_k and Q_k `auto` and the ψ columns of SIA 260 Tabelle 2 there and hidden; the norms named by their keys in calc/norms/norms.json, which carries their current editions; no eszett, no client's name, the French punctuation spaced; `instantiate` in each mode and language, never overwriting and never leaving half a document; every defect `check` names -- and **every mode in every language made into a new project and compiled by the real engine**, its outline holding every section the structure prints at the level the structure means.

Every file a check writes goes into this process's own temporary folder.
"""

import contextlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
import types
from pathlib import Path

import conftest
from conftest import ROOT, Skip

import doc_templates
import documents
import project
import project_template
import structure
import validation

sys.path.insert(0, str(ROOT / "calc" / "tools"))
import usersettings  # noqa: E402  -- Woodcore's preferences: the office's folder of templates is one of them

LANGS = ("fr", "de", "en")
MODES = ("cu", "bp")
OTHER = {"cu": "bp", "bp": "cu"}

# What each document is called in each language: SIA 260's own terms (the English are its English edition's), and what the title page prints.
DOC_NAMES = {
    "cu": {"fr": "Convention d'utilisation", "de": "Nutzungsvereinbarung", "en": "Service criteria agreement"},
    "bp": {"fr": "Base de projet", "de": "Projektbasis", "en": "Basis of design"},
}
JOURNAL = {"fr": "Historique des versions", "de": "Änderungsverzeichnis", "en": "Revision history"}
# The first chapter of each document and its first section, as the catalogue writes them.
FIRST = {
    "cu": ({"fr": "Explications", "de": "Zweck und Abgrenzung", "en": "Purpose and scope"}, "purpose",
           {"fr": "Objet de la convention d'utilisation", "de": "Zweck der Nutzungsvereinbarung", "en": "Purpose of the service criteria agreement"}),
    "bp": ({"fr": "Généralités", "de": "Allgemeines", "en": "General"}, "purpose-of-basis-of-design",
           {"fr": "Objet de la base de projet", "de": "Zweck der Projektbasis", "en": "Purpose of the basis of design"}),
}
# How many lowest-level sections each template holds -- the catalogue's 58 and 70, the journal, the BP's «Grundlagen der Bauphysik», and the switched-off «Annexes» section of each (v0.115) -- and how many chapters.
LEAVES = {"cu": 60, "bp": 73}
GROUPS = {"cu": 10, "bp": 18}
# The sections the catalogue shares between the two documents by default: the same id, the same file.
SHARED = {"scope-and-limits", "building-description", "transport-dimensions", "sustainability-certification", "ground-conditions",
          "live-loads", "superimposed-dead-loads", "service-life", "deformation-limits", "settlements", "vibrations", "durability",
          "earthquake", "impact", "accepted-risks", "project-documents", "norms"}
# What the section catalogue's own build refuses (its gen/build.py), a client's or an office's name above all: the repository is shared.
FORBIDDEN = [r"\bBFH\b", r"Berner", r"RB\d{3}", r"@\w+\.\w+", r"\+41", r"Sherpa", r"Velo", r"Pavillon", r"\bNV\.pdf"]
# The norms the chapters switched on by default rest on, and the edition each prints -- calc/norms/norms.json's, the current one.
EDITIONS = ("SIA 260:2013", "SIA 261:2020", "SIA 262:2025", "SIA 263:2013", "SIA 265:2021", "SIA 267:2013",
            "SIA 180:2014", "SIA 380/1:2016", "SIA 181:2020", "SIA 181/1:2026")
OBJECT_START = re.compile(r"^// woodcore:object (?P<type>[a-z-]+) (?P<id>\S+)$")
# The two objects that are markup and no call (calc/typst_objects.py): every heading and every paragraph of a section is one.
MARKUP = ("heading", "text")



def _in_config(data):
    """A template's bytes as a project laid out by folders holds them once made: what it names at the root -- `/config.typ`, `/commands.typ`, `/title.typ` -- named in 000-Typst-Config/ (issue #64, documents.relocate_config_paths)."""
    for name in ("config.typ", "commands.typ", "title.typ"):
        data = data.replace(f'"/{name}'.encode(), f'"/{project.CONFIG_FOLDER}/{name}'.encode())
    return data

def _template(mode):
    template = doc_templates.find(f"builtin:{mode}/standard")
    assert not template.error, template.error
    return template


def _read(path):
    with open(path, encoding="utf-8", newline="") as handle:
        return handle.read()


def _copy(name, mode="cu"):
    """A copy of the builtin template of `mode` in this process's own folder, for a check to break."""
    target = conftest.tmpdir(name) / "standard"
    shutil.copytree(_template(mode).folder, target)
    return target


def _broken(name, what, mutate, mode="cu"):
    """`mutate(copy)` applied to a copy of the template, and the template read from it says `what`."""
    folder = _copy(name, mode)
    mutate(folder)
    template = doc_templates.read(folder, mode, "user")
    assert template.error, f"a template with {what} was accepted"
    assert what in template.error, f"refused, but for another reason: {template.error}"
    try:
        doc_templates.instantiate(mode, "fr", conftest.tmpdir(name + "_target"), template=template)
    except doc_templates.DocTemplateError as exc:
        assert what in str(exc)
    else:
        raise AssertionError("a document was made from a template that cannot be used")


def _sections(mode, lang):
    """{file name: text} of every section file of the template of `mode` in `lang`."""
    folder = _template(mode).language_dir(lang) / structure.SECTIONS_DIR
    return {p.name: _read(p) for p in sorted(folder.glob("*.typ"))}


def _structure(mode, lang):
    return structure.read(_template(mode).structure_file(lang))


def _objects(text):
    """(type, id, body lines) of every parametric object of `text`."""
    lines = text.split("\n")
    out = []
    for i, line in enumerate(lines):
        found = OBJECT_START.match(line)
        if found:
            end = lines.index(f"// woodcore:/object {found['id']}", i)
            out.append((found["type"], found["id"], lines[i + 1:end]))
    return out


def _signatures():
    """{command: [argument names, in the signature's order]} of the objects of lib/document.typ."""
    sys.path.insert(0, str(ROOT / "calc" / "tools"))
    import build_reference as ref
    records = {r["name"]: r for r in ref.lib_bindings(ROOT)}
    import typst_objects
    return {name: [param for param, _default in ref.split_params(records[name]["params"])] for name in typst_objects.CALL_TYPES}


# --- the templates -------------------------------------------------------------------------------

def test_the_builtin_templates_are_there_and_sound_in_three_languages():
    found = doc_templates.list_templates()
    assert [t.ref for t in found] == ["builtin:cu/standard", "builtin:bp/standard", "builtin:rs/standard"], [t.ref for t in found]
    found = [t for t in found if t.mode in MODES]       # the report's own is held by the checks of its own further down
    for template in found:
        assert not template.error, template.error
        assert template.read_only and template.place == "builtin"
        assert template.languages == list(LANGS)
        for lang in LANGS:
            assert template.name(lang) and template.description(lang), f"{template.ref} has no name or no description in {lang}"
            assert "SIA 260" in template.description(lang), "the description says what the document is written against"
        assert len({template.name(lang) for lang in LANGS}) == 3, "the three names are one text"
        validation.validate_structure(template.meta, "document-template")
    assert [t.ref for t in doc_templates.list_templates("bp")] == ["builtin:bp/standard"]
    assert [t.ref for t in doc_templates.list_templates("rs")] == ["builtin:rs/standard"], "the report has content templates too (v0.114)"
    assert doc_templates.MODES == ("cu", "bp") and doc_templates.ALL_MODES == ("cu", "bp", "rs")
    try:
        doc_templates.list_templates("xx")
    except doc_templates.DocTemplateError as exc:
        assert "'xx'" in str(exc) and exc.code == "bad_mode"
    else:
        raise AssertionError("a document that does not exist was listed")


def test_a_template_is_found_by_its_reference_its_folder_or_its_name():
    assert doc_templates.default_ref("cu") == "builtin:cu/standard"
    for name, mode, ref in (("builtin:cu/standard", None, "builtin:cu/standard"), ("cu/standard", None, "builtin:cu/standard"),
                            ("standard", "cu", "builtin:cu/standard"), ("standard", "bp", "builtin:bp/standard"),
                            ("builtin:bp/standard", "bp", "builtin:bp/standard"), ("", "cu", "builtin:cu/standard"),
                            ("Convention d'utilisation — standard", "cu", "builtin:cu/standard"),
                            ("basis of design — STANDARD", "bp", "builtin:bp/standard"),
                            # a mode in the name wins over the mode asked for: instantiate then says the two differ
                            ("builtin:bp/standard", "cu", "builtin:bp/standard")):
        assert doc_templates.find(name, mode).ref == ref, (name, mode)
    for bad, mode in (("nope", "cu"), ("builtin:cu/nope", None), ("xx/standard", None), ("user:cu/standard", None), ("", None)):
        try:
            doc_templates.find(bad, mode)
        except doc_templates.DocTemplateError as exc:
            assert "no document template" in str(exc), exc
            if mode == "cu":
                assert "builtin:cu/standard" in str(exc), exc
        else:
            raise AssertionError(f"{bad!r} found a template")


# --- each language folder is a document's folder --------------------------------------------------------

def test_every_language_folder_is_a_document_folder():
    for mode in MODES:
        template = _template(mode)
        for lang in LANGS:
            where = f"{mode}/{lang}"
            folder = template.language_dir(lang)
            entry = template.entry_file(lang)
            assert entry is not None and entry.name == DOC_NAMES[mode][lang] + ".typ", (where, entry)
            assert sorted(p.name for p in folder.iterdir()) == sorted([entry.name, "structure.json", "Sections"]), where
            source = structure.read(template.structure_file(lang))
            assert source["document"] == mode
            assert structure.is_absolute(source), f"{where}: the template does not write its headings at the level they print at"
            named = {file for _node, file in structure.named_files(source)}     # the sections' files and the chapters' (06.10.2026)
            assert named == {f"Sections/{p.name}" for p in (folder / "Sections").iterdir()}, where
            # the entry's generated block is already what the structure says, so instantiating changes nothing in it
            copy = conftest.tmpdir(f"doc_templates_sync_{mode}_{lang}") / entry.name
            shutil.copyfile(entry, copy)
            assert structure.sync_entry(copy, source, lang) is False, f"{where}: the committed structure block is not what structure.json says"
            assert not structure.check_tags(_read(entry)), where
            # the three languages are one document: the same sections, in the same order, switched on and off alike
            if lang != LANGS[0]:
                assert structure.ordered(source) == structure.ordered(_structure(mode, LANGS[0])), f"{where}: its structure is not the {LANGS[0]} one"
            assert b"\r" not in template.structure_file(lang).read_bytes() and b"\r" not in entry.read_bytes(), f"{where}: written LF"


def test_the_whole_catalogue_is_there_in_the_order_of_sia_260():
    """Every chapter and every lowest-level section of the catalogue, the journal last; the first chapter what the catalogue opens with; some sections switched off by default and each of them keeping its file; a chapter whose every section is off switched off too, so that it prints no heading over nothing."""
    for mode in MODES:
        source = _structure(mode, "fr")
        leaves = [node for node, _d in structure.leaves(source)]
        groups = [node for node, _d, _p in structure.walk(source) if "children" in node]
        assert len(leaves) == LEAVES[mode] and len(groups) == GROUPS[mode], (mode, len(leaves), len(groups))
        assert source["sections"][-1] == {"id": "journal", "file": "Sections/journal.typ", "enabled": True}, "the journal is the last section"
        first_group, first_leaf, _titles = FIRST[mode]
        assert source["sections"][0]["title"] == {lang: first_group[lang] for lang in LANGS} and source["sections"][0]["children"][0]["id"] == first_leaf
        off = [n["id"] for n in leaves if not n["enabled"]]
        assert 4 <= len(off) < len(leaves) // 4, (mode, off)
        for node, _depth, _parent in structure.walk(source):
            if "children" in node:
                below = [leaf for leaf in structure.leaves({"sections": node["children"]})]
                assert node["enabled"] == any(leaf["enabled"] for leaf, _d in below), f"{mode}: group {node['id']} enabled={node['enabled']}"
    cu = {n["id"]: n for n, _d in structure.leaves(_structure("cu", "de"))}
    assert not cu["future-extension"]["enabled"] and not cu["radon"]["enabled"] and cu["live-loads"]["enabled"]
    assert not next(n for n, _d, _p in structure.walk(_structure("cu", "de")) if n["id"] == "annexes")["enabled"], "the annexes, all off, print no heading"


def test_the_entry_files_say_what_their_document_and_language_are():
    for mode in MODES:
        template = _template(mode)
        first_group, first_leaf, _titles = FIRST[mode]
        for lang in LANGS:
            where = f"{mode}/{lang}"
            text = _read(template.entry_file(lang))
            assert '#import "/config.typ": conf' in text and '#import "/commands.typ": *' in text, f"{where}: the imports are not root-absolute"
            assert "../" not in text, f"{where}: a relative path"
            assert f'#show: woodcore-document.with(document: "{mode}")' in text, where
            assert re.search(rf'set-report-language\(\s*sys\.inputs\.at\(\s*"lang"\s*,\s*default:\s*"{lang}"\s*\)\s*\)', text), f"{where}: the report language's default is not {lang}"
            # the title page is the project's title.typ, shared by the three documents, which names the document in its own language (tests/test_title_page.py)
            assert '#import "/title.typ": title-page' in text and f'#title-page(document: "{mode}")' in text, f"{where}: the title page is not title.typ's"
            assert "#outline()" in text, where
            # a chapter is a file of its own, its heading at its level in the document's language; every file included as it is, no offset (06.10.2026)
            first = _structure(mode, lang)["sections"][0]
            assert f'#include "Sections/{first["id"]}.typ"' in text, f"{where}: the first chapter is not its own file"
            assert f"= {first_group[lang]}" in _read(template.language_dir(lang) / "Sections" / f'{first["id"]}.typ').split("\n"), f"{where}: the first chapter's heading is not in the document's language"
            assert f'#include "Sections/{first_leaf}.typ"' in text and "set heading(offset" not in text, where
            assert text.rstrip().endswith('#include "Sections/journal.typ"\n' + structure.END_TAG), f"{where}: the journal is not the last section"


def test_the_section_files_write_their_headings_at_the_level_they_print_at():
    """Every section file and every chapter's file imports the engine from the Typst root, then -- between the tags of its heading object, and **before** its shared block where it is shared, the two documents placing a shared section at different depths -- its own heading at the level it prints at, which is its depth in the structure (the engineer's request of 06.10.2026: «dans le document type, il doit y avoir deux égales»); no relative path, no heading deeper than the file's own below it."""
    for mode in MODES:
        _first_group, first_leaf, titles = FIRST[mode]
        for lang in LANGS:
            files = _sections(mode, lang)
            depths = {file.split("/")[-1]: depth for node, depth, _p in structure.walk(_structure(mode, lang))
                      for file in [node.get("file") or structure.group_file(node["id"])]}
            for name, text in files.items():
                where = f"{mode}/{lang}/{name}"
                lines = [line for line in text.split("\n") if line.strip() and not line.startswith("// woodcore:")]
                assert text.startswith('#import "/commands.typ": *\n\n'), f"{where}: does not import /commands.typ root-absolute"
                level = depths[name]
                assert lines[1].startswith("=" * level + " ") and len(lines[1]) > level + 1, f"{where}: its heading is {lines[1]!r} and its depth {level}"
                assert not any(line.startswith("=" * (level + 1)) for line in lines), f"{where}: a heading below its own"
                assert "../" not in text, f"{where}: a relative path"
                assert text.endswith("\n") and "\r" not in text, f"{where}: not LF with a final newline"
            assert [line for line in files[f"{first_leaf}.typ"].split("\n") if line.startswith("=")][0] == f"== {titles[lang]}", (mode, lang)
            assert files["journal.typ"] == (f'#import "/commands.typ": *\n\n// woodcore:object heading title\n= {JOURNAL[lang]}\n// woodcore:/object title\n\n#include domain-file("journal", "{mode}")\n'), (mode, lang)


# --- ids, tags, objects ------------------------------------------------------------------------------

def test_every_id_is_valid_and_unique_and_every_tag_pairs():
    """A section's id is its file's name, English, unique in its document (structure.check_source); an object's id is an id, unique in its file, and every tag is paired, nothing standing where it may not (structure.check_tags) -- so Woodcore's editors can rewrite every file of the template."""
    for mode in MODES:
        for lang in LANGS:
            source = structure.check_source(_structure(mode, lang))
            ids = [node["id"] for node, _d, _p in structure.walk(source)]
            assert len(ids) == len(set(ids)) and all(structure.ID_PATTERN.match(i) for i in ids), (mode, lang)
            for name, text in _sections(mode, lang).items():
                assert not structure.check_tags(text), (mode, lang, name, structure.check_tags(text))
                blocks, _problems = structure.pair_tags(text)
                objects = [b for b in blocks if b.kind == "object"]
                assert len({b.id for b in objects}) == len(objects), (mode, lang, name)
                assert all(b.type in structure.OBJECT_TYPES for b in objects)
            assert not structure.check_tags(_read(_template(mode).entry_file(lang)))


def test_every_object_is_one_call_in_the_canonical_form():
    """What the editor writes back: `#<command>(`, one named argument a line, two spaces in, a trailing comma everywhere, an array of columns, rows, options or notes an item a line four spaces in, `)` -- one call and nothing else between the tags -- and the arguments a subset of the command's own, in the order of its signature."""
    signatures = _signatures()
    kinds = set()
    for mode in MODES:
        for lang in LANGS:
            for name, text in _sections(mode, lang).items():
                for kind, object_id, body in _objects(text):
                    where = f"{mode}/{lang}/{name}#{object_id}"
                    if kind in MARKUP or kind == "table":   # a raw table is markup, read by its own model (ARCH-004)
                        continue
                    kinds.add(kind)
                    assert body[0] == f"#{kind}(" and body[-1] == ")", f"{where}: not one call"
                    names, inside = [], False
                    for line in body[1:-1]:
                        assert line.endswith(",") or (not inside and line.endswith(": (")), f"{where}: no trailing comma on {line!r}"
                        if inside:
                            if line == "  ),":
                                inside = False
                            else:
                                assert line.startswith("    ") and not line.startswith("     "), f"{where}: an item not four spaces in: {line!r}"
                            continue
                        found = re.match(r"^  ([a-z][a-z-]*): (\($|.*,$)", line)
                        assert found, f"{where}: not one named argument two spaces in: {line!r}"
                        names.append(found[1])
                        if found[2] == "(":  # an array written an item a line
                            inside = True
                    assert not inside, f"{where}: an array is never closed"
                    order = signatures[kind]
                    assert all(n in order for n in names), f"{where}: {names} -- {kind} takes {order}"
                    assert names == sorted(names, key=order.index), f"{where}: {names} not in the order of {kind}'s signature {order}"
                    assert len(names) == len(set(names)), where
    # the templates written in raw Typst (spec 2026-10-21-commandes-typst-refonte, REQ-019, lot 18): their tables, signatures, choices and lists are raw tables, markup read by its own model (ARCH-004); the list of the norms is the one call left
    assert kinds == {"show-norm-list"}, kinds


def test_every_heading_and_every_paragraph_is_an_object_with_the_same_ids_in_every_language():
    """The engineer's rework of 01.10.2026: a section file is its import line, tags and objects -- **every heading and every paragraph between tags** (`heading title`, `heading h2`, `text p1`, `text p2` …), nothing else standing outside them but the import line, the shared tags and the journal's inclusion, `#include domain-file("journal", document)`. The same objects with the same ids in fr, de and en, so that a shared section has the same ids in both documents. A heading is one line `= Titel`, a paragraph has no blank line in it, and every one reads as canonical."""
    import typst_objects
    for mode in MODES:
        ids = {}
        for lang in LANGS:
            for name, text in _sections(mode, lang).items():
                where = f"{mode}/{lang}/{name}"
                objects = typst_objects.objects(text)
                headings = [o for o in objects if o.type == "heading"]
                assert headings and headings[0].id == "title", f"{where}: the file's first heading is the object `title`"
                for o in objects:
                    if o.type == "heading":
                        assert o.state == "canonical" and re.match(r"^=+ \S", o.written) and "\n" not in o.written, (where, o.id)
                    elif o.type == "text":
                        assert o.state == "canonical" and o.written.strip() and not re.search(r"\n[ \t]*\n", o.written), (where, o.id)
                        assert not o.written.startswith("="), (where, o.id)
                assert not typst_objects.untagged(text), f"{where}: a heading or a paragraph stands outside its tags"
                rest = text.split("\n")
                for o in sorted(objects, key=lambda o: -o.start):
                    del rest[o.start:o.end + 1]
                left = [line for line in rest if line.strip() and not line.startswith(("// woodcore:shared", "// woodcore:/shared", "#import"))]
                assert left == [] or (len(left) == 1 and re.fullmatch(r'#include domain-file\("journal", "(cu|bp|rs)"\)', left[0])), f"{where}: {left}"
                ids.setdefault(name, []).append([o.id for o in objects if o.type in MARKUP])
        for name, per_language in ids.items():
            assert per_language[0] == per_language[1] == per_language[2], f"{mode}/{name}: the languages carry different headings and paragraphs: {per_language}"



def test_every_object_is_canonical_by_the_editors_own_reading():
    """The editor's own parser and writer (calc/typst_objects.py, work package 4.1) read every object of the templates as `canonical`: what it would write back is byte for byte what is there, so the first edit of a template's object in Woodcore warns about nothing."""
    try:
        import typst_objects
    except ImportError:
        raise Skip("calc/typst_objects.py is not there yet")
    seen = 0
    for mode in MODES:
        for lang in LANGS:
            for name, text in _sections(mode, lang).items():
                for found in typst_objects.objects(text):
                    seen += 1
                    assert found.state == "canonical", f"{mode}/{lang}/{name}#{found.id}: {found.state} {found.error or ''} -- " + found.diff()
    assert seen > 300, seen

def test_the_sections_shared_by_default_are_one_file_in_both_documents():
    """A section the catalogue shares between the convention d'utilisation and the base de projet: the same id and the same file, byte for byte, in the two documents of each language, its body after the import line between `// woodcore:shared <id>` and `// woodcore:/shared <id>`, and structure.json naming the other document in `shared_with` on both sides. Nothing else is shared, and nothing with the report."""
    for lang in LANGS:
        shared = {}
        for mode in MODES:
            shared[mode] = {node["id"]: node.get("shared_with") for node, _d in structure.leaves(_structure(mode, lang)) if node.get("shared_with")}
            assert set(shared[mode]) == SHARED, (mode, lang, sorted(set(shared[mode]) ^ SHARED))
            assert all(value == [OTHER[mode]] for value in shared[mode].values()), (mode, lang)
        cu, bp = _sections("cu", lang), _sections("bp", lang)
        for section_id in SHARED:
            name = f"{section_id}.typ"
            # the title is the document's own, at the level its place gives it there; the shared block is the same bytes in both (06.10.2026)
            assert cu[name].split(f"// woodcore:shared {section_id}")[1] == bp[name].split(f"// woodcore:shared {section_id}")[1], f"{lang}/{name}: the two copies' shared blocks differ"
            text = cu[name]
            assert text.startswith('#import "/commands.typ": *\n\n// woodcore:object heading title\n='), f"{lang}/{name}: the title does not follow the import"
            assert f"// woodcore:/object title\n// woodcore:shared {section_id}\n" in text, f"{lang}/{name}: the shared block does not open after the title"
            assert text.endswith(f"\n// woodcore:/shared {section_id}\n"), f"{lang}/{name}: the shared block does not close the file"
            blocks, problems = structure.pair_tags(text)
            assert not problems and [b.id for b in blocks if b.kind == "shared"] == [section_id]
        for mode, files in (("cu", cu), ("bp", bp)):
            for name, text in files.items():
                if name[:-4] not in SHARED:
                    assert "woodcore:shared" not in text, f"{mode}/{lang}/{name} carries a shared tag and is not shared"


def test_the_live_loads_are_the_live_load_table_in_both_documents():
    """SIA 261 8.2.2 wants the live loads in the Nutzungsvereinbarung and in the Projektbasis: one shared section, whose table is written in raw Typst (spec 2026-10-21-commandes-typst-refonte, REQ-019) -- a category of Tabelle 8 a row's own, q_k and Q_k each a `#sync` read live by `#var(…, domain: ("live-load", category), display: "value")` (Q-007), printed the same at every level, the uniform one included, and **no ψ column** (the Reduktionsbeiwerte are never shown for live loads)."""
    for mode in MODES:
        for lang in LANGS:
            text = _sections(mode, lang)["live-loads.typ"]
            [(kind, object_id, body)] = [o for o in _objects(text) if o[1] == "live-loads-table"]
            table = "\n".join(body)
            assert kind == "table" and "columns: (auto, auto, 1fr, auto, auto, auto)," in table, (mode, lang)
            assert "psi" not in table and "ψ" not in table, (mode, lang)
            for category in ("A1", "H"):
                for key in ("q_k", "Q_k"):
                    assert f'#sync("live-load/{category}/{key}")[#var("{key}", domain: ("live-load", "{category}"), display: "value"' in table, (mode, lang, category, key)
            [(dead_kind, _id, _body)] = [o for o in _objects(_sections(mode, lang)["superimposed-dead-loads.typ"]) if o[1] == "superimposed-table"]
            assert dead_kind == "table", (mode, lang)


# --- words ---------------------------------------------------------------------------------------------

def _all_texts():
    for mode in MODES:
        template = _template(mode)
        yield template.folder / doc_templates.FILE, _read(template.folder / doc_templates.FILE), None
        for lang in LANGS:
            for path in sorted(template.language_dir(lang).rglob("*")):
                if path.is_file():
                    yield path, _read(path), lang


def test_no_eszett_no_clients_name_and_the_french_spaced():
    """Swiss German, never an ß; no name, address or number of a client or of the examples the catalogue was drawn from; and the French prose puts its narrow no-break space before «: ; ! ?», as the catalogue does -- code, math and the calls a text carries left aside."""
    for path, text, lang in _all_texts():
        assert "ß" not in text, f"{path}: an eszett"
        for pattern in FORBIDDEN:
            assert not re.search(pattern, text), f"{path}: {pattern}"
        if lang != "fr" or path.parent.name != "Sections":
            continue
        inside = False
        for line in text.split("\n"):
            if line.startswith("// woodcore:object"):
                inside = line.split()[2] not in MARKUP     # a heading or a paragraph is prose from its first line; a call has its prose in content blocks
                continue
            if line.startswith("// woodcore:/object"):
                inside = False
                continue
            if line.startswith("//") or line.startswith("#import"):
                continue
            line = re.sub(r'#[a-z-]+\((?:[^()"]|"[^"]*"|\([^()]*\))*\)', "", line)   # a call in a cell, `#sync(…)`, `#var(…, domain: (…))`: code, its arguments no prose
            prose = re.findall(r"\[((?:[^\[\]]|\[[^\[\]]*\])*)\]", line) if inside or line.lstrip().startswith("#") else [line]   # a call written in a paragraph has its prose in its content blocks
            for part in prose:
                part = re.sub(r"\$[^$]*\$", "", re.sub(r"#[a-z-]+\([^)]*\)", "", part))
                for m in re.finditer(r"(.)([:;!?])(?=\s|$)", part):
                    assert m.group(1) == "\u202f", f"{path.name}: no narrow no-break space before {m.group(2)!r} in {part!r}"


def test_the_norms_are_named_by_their_keys_and_their_current_editions():
    """What `show-norm-list` lists is a key of calc/norms/norms.json -- which carries its current edition -- or a line in the document's own words; the building physics, the noise and the fire chapters stay switched on and name SIA 180, SIA 380/1, SIA 181, SIA 181/1 and the VKF / AEAI directives; `cite-norm` cites a norm in their text; and no superseded edition of SIA 262 is quoted anywhere."""
    catalogue = json.loads((ROOT / "calc" / "norms" / "norms.json").read_text(encoding="utf-8"))["references"]
    known = {e["key"] for e in catalogue} | {a for e in catalogue for a in e.get("aliases", ())}
    for mode in MODES:
        for lang in LANGS:
            for name, text in _sections(mode, lang).items():
                for kind, object_id, body in _objects(text):
                    if kind == "show-norm-list":
                        for line in body:
                            key = re.match(r'^    "(.*)",$', line)
                            if key:
                                assert key[1] in known, f"{mode}/{lang}/{name}: {key[1]!r} is not in norms.json"
                for cited in re.findall(r'#cite-norm\(norm: "([^"]+)"', text):
                    assert cited in known, (name, cited)
                assert not re.search(r"SIA 262(:| \()2013", text), f"{mode}/{lang}/{name}: the superseded SIA 262:2013"
    bp = _sections("bp", "de")
    norms = "\n".join(bp["norms.typ"].split("\n"))
    for key in ("SIA 262", "SIA 180", "SIA 380/1", "SIA 181", "SIA 181/1", "VKF 14-15", "VKF 15-15"):
        assert f'    "{key}",' in norms, key
    assert '"VKF 1-15"' in bp["fire-protection-bases.typ"] and '"SIA 181/1"' in bp["noise-protection-bases.typ"]
    assert '"SIA 180"' in bp["building-physics-bases.typ"] and '"SIA 380/1"' in bp["building-physics-bases.typ"]
    assert '#cite-norm(norm: "SIA 180")' in bp["airtightness.typ"] and '#cite-norm(norm: "SIA 380/1")' in bp["heating.typ"]
    source = _structure("bp", "de")
    for group in ("fire-protection", "building-physics", "noise-protection"):
        node, _depth, _parent = structure.find(source, group)
        assert node["enabled"] and all(leaf["enabled"] for leaf, _d in structure.leaves({"sections": node["children"]})), group


# --- instantiating ----------------------------------------------------------------------------------------------

def _files(folder):
    return sorted(p.relative_to(folder).as_posix() for p in folder.rglob("*") if p.is_file())


def _expected_files(mode, lang, entry_name):
    return sorted([entry_name, "structure.json"] + [file for _node, file in structure.named_files(_structure(mode, lang))])


def test_instantiate_makes_a_valid_document_folder_in_each_mode_and_language():
    for mode in MODES:
        for lang in LANGS:
            where = f"{mode}/{lang}"
            target = conftest.tmpdir(f"doc_templates_make_{mode}_{lang}") / "1_Folder"
            entry = doc_templates.instantiate(mode, lang, target, f"{DOC_NAMES[mode][lang]}.typ")
            assert entry == target / f"{DOC_NAMES[mode][lang]}.typ" and entry.is_file(), where
            assert _files(target) == _expected_files(mode, lang, entry.name), where
            source = structure.read(target / "structure.json")
            assert source["document"] == mode
            template = _template(mode)
            for _node, file in structure.named_files(source):
                assert (target / file).read_bytes() == (template.language_dir(lang) / file).read_bytes(), f"{where}: {file} is not the template's"
            assert (target / "structure.json").read_bytes() == template.structure_file(lang).read_bytes()
            assert structure.sync_entry(entry, target / "structure.json", lang) is False, f"{where}: the entry's block is not what the structure says"
            assert not structure.check_tags(_read(entry))
            assert not list(target.rglob("*.tmp"))


def test_the_entry_is_named_what_the_project_calls_it_and_its_block_follows_the_copied_structure():
    target = conftest.tmpdir("doc_templates_named") / "Nested" / "1_Folder"
    entry = doc_templates.instantiate("cu", "fr", target, "Mon document")
    assert entry.name == "Mon document.typ", "`.typ` is added where left out"
    assert _files(target) == _expected_files("cu", "fr", "Mon document.typ")
    # the template's own name where none is given
    other = conftest.tmpdir("doc_templates_default_name") / "x"
    assert doc_templates.instantiate("bp", "de", other).name == "Projektbasis.typ"
    # the block is written from the copied structure: a structure edited afterwards and synced moves it
    source = structure.read(target / "structure.json")
    source["sections"][-1]["enabled"] = False
    structure.write(target / "structure.json", source)
    assert structure.sync_entry(entry, target / "structure.json", "fr") is True
    assert "// disabled: journal (Sections/journal.typ)" in _read(entry)


def test_instantiate_refuses_what_it_cannot_make_and_says_why():
    folder = conftest.tmpdir("doc_templates_refusals")

    def refused(what, *args, **kwargs):
        try:
            doc_templates.instantiate(*args, **kwargs)
        except doc_templates.DocTemplateError as exc:
            assert what in str(exc), f"refused, but for another reason: {exc}"
        else:
            raise AssertionError(f"{args} was accepted")

    refused("mode 'xx'", "xx", "fr", folder / "a")
    refused("language 'it'", "cu", "it", folder / "a")
    refused("no document template 'nope'", "cu", "fr", folder / "a", template="nope")
    refused("makes the document 'bp'", "cu", "fr", folder / "a", template="builtin:bp/standard")
    for bad in ("a/b.typ", "a\\b.typ", "..", "x:y", "bad?.typ", ".typ", "trailing.", "  "):
        refused("not the name of a document's entry file", "cu", "fr", folder / "b", bad)
    assert not (folder / "a").exists() and not (folder / "b").exists(), "a refusal left a folder behind"


def test_instantiate_never_overwrites_and_leaves_nothing_where_it_refuses():
    target = conftest.tmpdir("doc_templates_no_overwrite") / "1_Folder"
    (target / "Sections").mkdir(parents=True)
    (target / "Sections" / "purpose.typ").write_text("the engineer's own section\n", encoding="utf-8")
    try:
        doc_templates.instantiate("cu", "fr", target, "Doc.typ")
    except doc_templates.DocTemplateError as exc:
        assert "Sections/purpose.typ is there already" in str(exc), exc
    else:
        raise AssertionError("a file was written over")
    assert _files(target) == ["Sections/purpose.typ"], "a refused copy still wrote a file"
    assert (target / "Sections" / "purpose.typ").read_text(encoding="utf-8") == "the engineer's own section\n"
    # an existing empty folder is fine, and so is one holding something that does not collide
    empty = conftest.tmpdir("doc_templates_empty_target")
    (empty / "notes.txt").write_text("mine\n", encoding="utf-8")
    doc_templates.instantiate("cu", "fr", empty, "Doc.typ")
    assert "notes.txt" in _files(empty) and "Doc.typ" in _files(empty)


def test_a_copy_that_fails_midway_leaves_no_half_document():
    root = conftest.tmpdir("doc_templates_failure")
    saved = structure.sync_entry

    def failing(*args, **kwargs):
        raise RuntimeError("the disk is full")

    structure.sync_entry = failing
    try:
        try:
            doc_templates.instantiate("cu", "fr", root / "new" / "1_Folder", "Doc.typ")
        except RuntimeError:
            pass
        else:
            raise AssertionError("the failure was swallowed")
        assert not (root / "new").exists(), "the folders the copy made were left behind"
        # into an existing folder: what it wrote is taken away, the folder stays
        (root / "existing").mkdir()
        try:
            doc_templates.instantiate("cu", "fr", root / "existing", "Doc.typ")
        except RuntimeError:
            pass
        assert (root / "existing").is_dir() and _files(root / "existing") == []
    finally:
        structure.sync_entry = saved


def test_a_template_in_one_language_is_offered_for_that_language_alone():
    folder = _copy("doc_templates_one_language")
    for lang in ("de", "en"):
        shutil.rmtree(folder / lang)
    meta = json.loads((folder / "template.json").read_text(encoding="utf-8"))
    meta["languages"] = ["fr"]
    (folder / "template.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    template = doc_templates.read(folder, "cu", "user")
    assert not template.error and template.languages == ["fr"] and not template.read_only
    target = conftest.tmpdir("doc_templates_one_language_target") / "1"
    assert doc_templates.instantiate("cu", "fr", target, template=template).is_file()
    try:
        doc_templates.instantiate("cu", "de", target.parent / "2", template=template)
    except doc_templates.DocTemplateError as exc:
        assert "exists in fr and not in de" in str(exc), exc
    else:
        raise AssertionError("a template was instantiated in a language it does not have")


# --- what check names ---------------------------------------------------------------------------------------------

def test_a_template_that_cannot_make_a_document_says_what_is_wrong_with_it():
    def meta(change):
        def mutate(folder):
            path = folder / "template.json"
            data = json.loads(path.read_text(encoding="utf-8"))
            change(data)
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return mutate

    _broken("dt_schema_version", "expected '1.0'", meta(lambda d: d.update(schema_version="2.0")))
    _broken("dt_format", "expected 'woodcore-document-template'", meta(lambda d: d.update(format="woodcore-template")))
    _broken("dt_mode_value", "expected one of", meta(lambda d: d.update(mode="xx")))
    _broken("dt_mode_report", "lies in the folder of 'cu'", meta(lambda d: d.update(mode="rs")))
    _broken("dt_mode_folder", "lies in the folder of 'cu'", meta(lambda d: d.update(mode="bp")))
    _broken("dt_no_languages", "at least one language", meta(lambda d: d.update(languages=[])))
    _broken("dt_twice", "each once", meta(lambda d: d.update(languages=["fr", "fr"])))
    _broken("dt_no_name", "has no name in de", meta(lambda d: d["name"].pop("de")))
    _broken("dt_no_description", "a description and none in en", meta(lambda d: d["description"].pop("en")))
    _broken("dt_no_folder", "has no folder de/", lambda f: shutil.rmtree(f / "de"))
    _broken("dt_two_entries", "exactly one .typ", lambda f: (f / "fr" / "Second.typ").write_text("x\n", encoding="utf-8"))
    _broken("dt_no_entry", "exactly one .typ", lambda f: next((f / "fr").glob("*.typ")).unlink())
    _broken("dt_no_structure", "could not be read", lambda f: (f / "fr" / "structure.json").unlink())
    _broken("dt_bad_structure", "missing required field", lambda f: (f / "fr" / "structure.json").write_text('{"schema_version": "1.0"}', encoding="utf-8"))
    _broken("dt_other_document", "is the structure of the document 'bp'",
            lambda f: (f / "fr" / "structure.json").write_text((_template("bp").structure_file("fr")).read_text(encoding="utf-8"), encoding="utf-8"))
    _broken("dt_missing_section", "names Sections/purpose.typ, which is not there", lambda f: (f / "fr" / "Sections" / "purpose.typ").unlink())
    _broken("dt_orphan", "no section of structure.json names it", lambda f: (f / "fr" / "Sections" / "orphan.typ").write_text("x\n", encoding="utf-8"))

    def unclosed(folder):
        entry = next((folder / "fr").glob("*.typ"))
        entry.write_text(_read(entry).replace(structure.END_TAG, "// end"), encoding="utf-8")
    _broken("dt_unclosed_block", "never closed", unclosed)

    def no_block(folder):
        entry = next((folder / "fr").glob("*.typ"))
        entry.write_text("#include \"Sections/purpose.typ\"\n", encoding="utf-8")
    _broken("dt_no_block", "exactly one woodcore:structure block", no_block)


def test_a_folder_without_a_template_json_is_not_a_template_and_an_unreadable_one_is_listed_with_its_error():
    folder = conftest.tmpdir("dt_unreadable") / "standard"
    folder.mkdir()
    missing = doc_templates.read(folder, "cu", "user")
    assert "no template.json" in missing.error
    (folder / "template.json").write_text("{not json", encoding="utf-8")
    assert "cannot be read" in doc_templates.read(folder, "cu", "user").error
    (folder / "template.json").write_text("[]", encoding="utf-8")
    assert "not an object" in doc_templates.read(folder, "cu", "user").error


# --- a new project in each language, compiled by the real engine -----------------------------------------------------

_PROJECTS = {}


def _project(lang):
    """A new project written in `lang`, made once per run: its convention d'utilisation and its base de projet are the templates' -- `project_template.create` instantiates them -- with the engine and the export a new project has before any export."""
    if lang not in _PROJECTS:
        _PROJECTS[lang] = project_template.create(conftest.tmpdir(f"doc_templates_project_{lang}") / "Halle", "Halle",
                                                  document_language=lang, report_language=lang)
    return _PROJECTS[lang]


def _compile(here, mode, flags=()):
    started = time.perf_counter()
    run = subprocess.run([project.typst_executable(), *documents.compile_args(here, mode, list(flags))],
                         capture_output=True, text=True, encoding="utf-8", errors="replace")
    return run, time.perf_counter() - started


def _text(pdf):
    from pypdf import PdfReader
    # the typographic apostrophe Typst sets for a «'» read back as the one the names are written with
    return " ".join(" ".join((page.extract_text() or "").split()) for page in PdfReader(str(pdf)).pages).replace("\u2019", "'")


def test_every_mode_in_every_language_compiles_in_a_new_project_as_its_structure_says():
    """The two documents of a new project in fr, de and en, compiled by the engine the project carries through the one spelling of a compile's command line: no error and no warning; the title page naming the document; every section the structure prints in the PDF's outline at the level the structure means (structure.align, what the Structure tab scrolls by); the live loads' category values and the norms with their current editions on the page."""
    if not conftest.have_typst():
        raise Skip("no typst on the path")
    times = {}
    for lang in LANGS:
        here = _project(lang)
        for mode in MODES:
            where = f"{mode}/{lang}"
            source = structure.read(here.structure_file(mode))
            assert structure.ordered(source) == structure.ordered(_structure(mode, lang)), f"{where}: the project's structure is not the template's"
            run, seconds = _compile(here, mode)
            times[where] = seconds
            assert run.returncode == 0, f"{where}: {run.stderr[:3000]}"
            assert "warning" not in run.stderr, f"{where}: {run.stderr[:3000]}"
            text = _text(here.document_pdf(mode))
            assert DOC_NAMES[mode][lang] in text, where
            nodes = [n for n in structure.flatten(structure.tree(here, mode)) if n.active and (n.kind in ("group", "file") or n.object_type == "heading")]
            found = structure.align(nodes, structure.bookmarks_from_pdf(here.document_pdf(mode)))
            missing = [n.id for n in nodes if n.id not in found]
            assert not missing, f"{where}: sections the structure prints and the outline has not: {missing}"
            wrong = [(n.id, n.level, found[n.id].level) for n in nodes if found[n.id].level != n.level]
            assert not wrong, f"{where}: at another level than the structure means: {wrong}"
            # SIA 261 Tabelle 8, read by the live-load table: A1's 2 kN/m² and H's 0.4 -- the export's own
            assert re.search(r"A1 2 2 ", text) and re.search(r"H 0\.4 1 ", text), f"{where}: the live loads are not Tabelle 8's"
            for edition in ("SIA 260:2013", "SIA 261:2020", "SIA 262:2025", "SIA 180:2014", "SIA 181/1:2026"):
                assert edition in text, f"{where}: {edition} is not listed"
        bp = _text(here.document_pdf("bp"))
        for edition in EDITIONS:
            assert edition in bp, f"bp/{lang}: {edition} is not listed"
    assert max(times.values()) < 30, times


def test_a_document_compiles_at_every_level_and_its_cells_carry_no_footnote():
    """The three report levels, a level forced with `--input uniform=3` included, compile the base de projet -- the level reaching every `val` whatever it was given, and none of the template's cells, which quote their values with `doc-value`. Since v0.120 every command that prints takes a level (spec 2026-10-20-indices-et-niveaux, UI-003): at 1 a plan, a list or a table of the document prints alone, so level 1 may differ; 2, 3 and the uniform 3 print the same, the document's objects citing nothing more at 3."""
    if not conftest.have_typst():
        raise Skip("no typst on the path")
    here = _project("de")
    texts = {}
    for flags in (["--input", "level=1"], ["--input", "level=2"], ["--input", "level=3"], ["--input", "uniform=3"]):
        run, _seconds = _compile(here, "bp", flags)
        assert run.returncode == 0 and "warning" not in run.stderr, (flags, run.stderr[:2000])
        texts[" ".join(flags)] = _text(here.document_pdf("bp"))
    texts.pop("--input level=1")   # compiles; at 1 the document's figures and tables print alone (UI-003)
    assert len(set(texts.values())) == 1, "level 2, 3 or the uniform 3 changed what a document of text and objects prints"


def test_a_document_with_its_structure_changed_compiles_as_the_structure_says():
    if not conftest.have_typst():
        raise Skip("no typst on the path")
    source_project = _project("de")
    folder = conftest.tmpdir("doc_templates_changed")
    target = folder / "Halle"
    shutil.copytree(source_project.root, target, ignore=shutil.ignore_patterns("_Archiv", "stamps", "*.pdf"))
    here = project.Project.load(target / source_project.file.name)
    path = here.structure_file("bp")
    source = structure.read(path)
    # the first section switched off, the ground chapter switched off whole, and the journal moved into the first chapter -- through Woodcore's own operations, which give a section moved to another depth the level of its heading there (06.10.2026)
    general = source["sections"][0]
    structure.set_enabled(here, "bp", general["children"][0]["id"], False)
    structure.set_enabled(here, "bp", "ground", False)
    structure.move_node(here, "bp", source["sections"][-1]["id"], general["id"], None)
    assert "== " in (here.document_dir("bp") / "Sections" / "journal.typ").read_text(encoding="utf-8"), "the journal moved one level down kept its level-1 heading"
    run, _seconds = _compile(here, "bp")
    assert run.returncode == 0, run.stderr[:2000]
    outline = [(b.level, structure.normalize_title(b.title)) for b in structure.bookmarks_from_pdf(here.document_pdf("bp"))]
    titles = [t for _l, t in outline]
    assert "zweck der projektbasis" not in titles and "baugrundverhältnisse" not in titles and "baugrundkennwerte" not in titles, titles
    assert (2, structure.normalize_title(JOURNAL["de"])) in outline and (1, structure.normalize_title(JOURNAL["de"])) not in outline, outline
    assert (here.document_dir("bp") / "Sections" / "purpose-of-basis-of-design.typ").is_file(), "a disabled section keeps its file"


# --- a document saved as a template: the engineer's and the office's (work package 6.1) -----------------------------------------------
#
# What is held here: a document saved from a project -- its structure with the flags as they stand, its sections as written, and nothing that is not the document --; a new project made from it carrying the choices and the text and compiling; the template offered only for the language it has, and a language added to it; an existing folder refused unless overwritten and the old language folder kept, or put back where the write fails; every refusal stating its code and leaving nothing behind; a template taken away into archives/; the office's place beside the engineer's; the shared sections shared again where the other document carries the id. Every template a check writes goes into this process's own folder (`WOODCORE_TEMPLATES`), never the engineer's.

MARK = "MODELEMARQUEUR"


@contextlib.contextmanager
def _own(name):
    """The engineer's document templates redirected into a clean folder of this process for the length of a check, and the office's named in the settings the check passes on: yields a namespace of `settings` (for every call), `user` and `office` (the `documents/` folders of the two places, which may not exist yet) and `base`."""
    base = conftest.tmpdir(name)
    saved = os.environ.get("WOODCORE_TEMPLATES")
    os.environ["WOODCORE_TEMPLATES"] = str(base / "user")
    try:
        yield types.SimpleNamespace(base=base, settings={"templates": {"shared_folder": str(base / "office")}},
                                    user=base / "user" / "documents", office=base / "office" / "documents")
    finally:
        if saved is None:
            os.environ.pop("WOODCORE_TEMPLATES", None)
        else:
            os.environ["WOODCORE_TEMPLATES"] = saved


@contextlib.contextmanager
def _settings_file(settings):
    """Woodcore's settings file -- the test run's own -- holding `settings` over what it held, for a call that reads the preferences itself (`project_template.create` finds an office's template by reading them)."""
    saved = usersettings.read()
    usersettings.write({**saved, **settings})
    try:
        yield
    finally:
        usersettings.write(saved)


def _new_project(name, lang="fr", **kwargs):
    return project_template.create(conftest.tmpdir(name) / "Halle", "Halle", document_language=lang, report_language=lang, **kwargs)


def _leaves(here, mode):
    return [node for node, _depth in structure.leaves(structure.read(here.structure_file(mode)))]


def _prefill(here, mode):
    """A project's document made the engineer's own: a marker written into its first section, its second section switched off, and -- lying in its folder -- what is not the document: an archived section, a PDF, a preview and a note. Returns (the first leaf, the second)."""
    first, second = _leaves(here, mode)[:2]
    folder = here.document_dir(mode)
    with open(folder / first["file"], "a", encoding="utf-8", newline="") as handle:
        handle.write(f"\n{MARK}\n")
    structure.set_enabled(here, mode, second["id"], False)
    (folder / "Sections" / "archives").mkdir(exist_ok=True)
    (folder / "Sections" / "archives" / "260101-000000-old.typ").write_text("= Old\n", encoding="utf-8")
    (folder / "preview.pdf").write_bytes(b"%PDF-1.4\n")
    here.document_typ(mode).with_suffix(".pdf").write_bytes(b"%PDF-1.4\n")
    (folder / "notes.txt").write_text("not a template's\n", encoding="utf-8")
    return first, second


def _saved_files(here, mode):
    """Every file a template saved from `here`'s document `mode` holds, in its language folder."""
    return sorted([here.document_typ(mode).name, "structure.json"] + [file for _node, file in structure.named_files(structure.read(here.structure_file(mode)))])


def _refused(code, *args, **kwargs):
    """`save_from_document(*args, **kwargs)` is refused, stating `code`; the refusal is returned."""
    try:
        doc_templates.save_from_document(*args, **kwargs)
    except doc_templates.DocTemplateError as exc:
        assert exc.code == code, f"refused with {exc.code!r} and not {code!r}: {exc}"
        assert str(exc), "a refusal without a sentence"
        return exc
    raise AssertionError(f"{args[1:]} {kwargs} was saved, and {code!r} was expected")


def _nothing_staged(root):
    assert not list(Path(root).glob(doc_templates.STAGING + "*")), "a save left its staging folder behind"


def _copy_project(here, name):
    target = conftest.tmpdir(name) / "Halle"
    shutil.copytree(here.root, target, ignore=shutil.ignore_patterns("_Archiv", "stamps", "*.pdf"))
    return project.Project.load(target / here.file.name)


def test_a_document_is_saved_as_a_template_with_its_structure_its_text_and_nothing_else():
    with _own("dt_save") as ctx:
        here = _new_project("dt_save_project")
        first, second = _prefill(here, "cu")
        template = doc_templates.save_from_document(here, "cu", "Convention courte", "Pour les petits objets", settings=ctx.settings)
        assert template.ref == "user:cu/Convention courte" and template.place == "user" and template.mode == "cu"
        assert not template.error and not template.read_only, template.error
        assert template.languages == ["fr"] and template.name("fr") == "Convention courte" and template.description("fr") == "Pour les petits objets"
        assert template.folder == ctx.user / "cu" / "Convention courte" and template.notes == []
        validation.validate_structure(template.meta, "document-template")
        folder = template.language_dir("fr")
        assert _files(folder) == _saved_files(here, "cu"), "the template holds the document and nothing else"
        for rel in _files(folder):
            assert (folder / rel).read_bytes() == (here.document_dir("cu") / rel).read_bytes(), f"{rel} is not the document's, byte for byte"
        kept = structure.read(template.structure_file("fr"))
        assert structure.find(kept, second["id"])[0]["enabled"] is False and structure.find(kept, first["id"])[0]["enabled"] is True, "the flags as they stand"
        assert MARK in _read(folder / first["file"]), "the text the engineer wrote"
        shared = [node for node, _depth in structure.leaves(kept) if node.get("shared_with")]
        assert shared and all("// woodcore:shared" in _read(folder / node["file"]) for node in shared), "a shared section keeps its tags and its flag"
        assert not (folder / "Sections" / "archives").exists() and not list(ctx.user.rglob("*.pdf")) and not list(ctx.user.rglob("notes.txt"))
        assert not list(ctx.user.rglob("*.tmp")) and not [p for p in ctx.user.iterdir() if p.name != "cu"], "only the template is in its place"
        _nothing_staged(ctx.user)
        for name in (template.ref, "user:cu/convention courte", "CU/Convention courte", "convention courte", "Convention courte"):
            assert doc_templates.find(name, settings=ctx.settings).ref == template.ref, name
        assert doc_templates.find("Convention courte", "cu", ctx.settings).folder == template.folder
        # a description is optional, and a name may be given in several languages
        bare = doc_templates.save_from_document(here, "bp", {"fr": "Base courte", "de": "Kurze Basis"}, settings=ctx.settings)
        assert bare.meta.get("description") is None and bare.meta["name"] == {"fr": "Base courte", "de": "Kurze Basis"} and bare.languages == ["fr"]
        assert doc_templates.find("kurze basis", settings=ctx.settings).ref == "user:bp/Base courte"
        # the language of the document is the one saved, whatever the call says of another: it is asked for
        assert doc_templates.save_from_document(here, "cu", "Convention corta", language="en", settings=ctx.settings).languages == ["en"]


def test_a_new_project_made_from_a_saved_template_carries_its_choices_and_its_text_and_compiles():
    with _own("dt_from_saved") as ctx:
        here = _new_project("dt_from_saved_source")
        first, second = _prefill(here, "cu")
        template = doc_templates.save_from_document(here, "cu", "Convention courte", settings=ctx.settings)
        made = project_template.create(conftest.tmpdir("dt_from_saved_new") / "Neuf", "Neuf", document_language="fr", report_language="fr",
                                       document_templates={"cu": template.ref})
        # the template's files, and the journal the new project is given beside its entry (export_all.seed: the templates carry none)
        assert _files(made.document_dir("cu")) == sorted(_saved_files(here, "cu") + ["journal.typ"]) and made.document_typ("cu").is_file()
        for rel in [f for f in _files(made.document_dir("cu")) if f != "journal.typ"]:
            if rel != "structure.json" and not rel.endswith("Convention d'utilisation.typ"):
                assert (made.document_dir("cu") / rel).read_bytes() == _in_config((template.language_dir("fr") / rel).read_bytes()), rel
        kept = structure.read(made.structure_file("cu"))
        assert structure.find(kept, second["id"])[0]["enabled"] is False, "the section switched off stays switched off"
        assert f"// disabled: {second['id']} (" in _read(made.document_typ("cu")), "and the entry says so"
        assert MARK in _read(made.document_dir("cu") / first["file"]), "the text the engineer wrote came across"
        assert structure.sync_entry(made.document_typ("cu"), made.structure_file("cu"), "fr") is False, "the entry's block is what the structure says"
        # the other document is the builtin one, and the two share what they shared: every flag has its other side, and settling changes nothing
        builtin_bp = doc_templates.find("builtin:bp/standard").language_dir("fr")
        assert (made.document_dir("bp") / "Sections" / "live-loads.typ").read_bytes() == _in_config((builtin_bp / "Sections" / "live-loads.typ").read_bytes())
        cu_shared = {node["id"]: node["shared_with"] for node in _leaves(made, "cu") if node.get("shared_with")}
        bp_shared = {node["id"]: node["shared_with"] for node in _leaves(made, "bp") if node.get("shared_with")}
        assert "live-loads" in cu_shared and cu_shared["live-loads"] == ["bp"] and bp_shared["live-loads"] == ["cu"]
        assert not doc_templates.settle_sharing(made).changes, "a template made from a project that shared its sections shares them again"
        if not conftest.have_typst():
            raise Skip("no typst on the path")
        run, _seconds = _compile(made, "cu")
        assert run.returncode == 0 and "warning" not in run.stderr, run.stderr[:2000]
        assert MARK in _text(made.document_pdf("cu")), "the pre-filled text is in the PDF"
        titles = [structure.normalize_title(b.title) for b in structure.bookmarks_from_pdf(made.document_pdf("cu"))]
        disabled = structure.normalize_title(structure.scan_headings(_read(made.document_dir("cu") / second["file"]))[0].title)
        assert disabled not in titles, "a section switched off in the template is not printed"


def test_a_saved_template_is_offered_for_the_languages_it_has_and_a_language_can_be_added_to_it():
    with _own("dt_languages") as ctx:
        here = _new_project("dt_languages_fr", "fr")
        _prefill(here, "cu")
        courte = doc_templates.save_from_document(here, "cu", {"fr": "Convention courte"}, "Petits objets", settings=ctx.settings)
        (ctx.user / "cu" / "Broken").mkdir()
        (ctx.user / "cu" / "Broken" / doc_templates.FILE).write_text("{not json", encoding="utf-8")

        def refs(**kwargs):
            return [t.ref for t in doc_templates.list_templates(settings=ctx.settings, **kwargs)]

        assert refs() == ["builtin:cu/standard", "builtin:bp/standard", "builtin:rs/standard", "user:cu/Broken", "user:cu/Convention courte"], "builtin first, a template that cannot be used listed with its error"
        assert next(t for t in doc_templates.list_templates(settings=ctx.settings) if t.folder.name == "Broken").error
        assert refs(mode="cu", language="fr") == ["builtin:cu/standard", "user:cu/Convention courte"], "offered for the language it has, and only what can be used"
        assert refs(mode="cu", language="de") == ["builtin:cu/standard"] and refs(mode="cu", language="en") == ["builtin:cu/standard"]
        assert refs(mode="bp") == ["builtin:bp/standard"] and refs(mode="bp", language="fr") == ["builtin:bp/standard"]
        try:
            doc_templates.list_templates(language="it", settings=ctx.settings)
        except doc_templates.DocTemplateError as exc:
            assert exc.code == "bad_language"
        else:
            raise AssertionError("a language the engine does not write was listed")
        # a project in another language is refused, naming the languages the template has -- by instantiate, and before anything is created by a new project
        try:
            doc_templates.instantiate("cu", "de", conftest.tmpdir("dt_languages_target") / "1", template=courte)
        except doc_templates.DocTemplateError as exc:
            assert exc.code == "language_missing" and exc.values["languages"] == ["fr"] and "exists in fr and not in de" in str(exc), exc
        else:
            raise AssertionError("a template was made into a document in a language it does not have")
        target = conftest.tmpdir("dt_languages_new") / "Neu"
        try:
            project_template.create(target, "Neu", document_language="de", report_language="de", document_templates={"cu": courte.ref})
        except project.ProjectError as exc:
            assert "exists in fr and not in de" in str(exc), exc
        else:
            raise AssertionError("a project was created from a template that has not its language")
        assert not target.exists(), "a refused creation left a folder behind"
        # the same folder saved from a project written in German adds the language: two folders, one template.json naming both
        german = _new_project("dt_languages_de", "de")
        _prefill(german, "cu")
        before = {rel: (courte.language_dir("fr") / rel).read_bytes() for rel in _files(courte.language_dir("fr"))}
        _refused("exists", german, "cu", "Kurze Vereinbarung", folder="Convention courte", settings=ctx.settings)
        both = doc_templates.save_from_document(german, "cu", "Kurze Vereinbarung", "Kleine Objekte", folder="Convention courte", overwrite=True, settings=ctx.settings)
        assert not both.error and both.languages == ["fr", "de"] and both.name("fr") == "Convention courte" and both.name("de") == "Kurze Vereinbarung"
        assert both.description("fr") == "Petits objets" and both.description("de") == "Kleine Objekte"
        assert {rel: (both.language_dir("fr") / rel).read_bytes() for rel in _files(both.language_dir("fr"))} == before, "the French folder is as it was"
        assert _files(both.language_dir("de")) == _saved_files(german, "cu")
        assert refs(mode="cu", language="de") == ["builtin:cu/standard", "user:cu/Convention courte"]
        assert doc_templates.find("kurze vereinbarung", settings=ctx.settings).ref == both.ref, "the name in the language added finds it"
        made = doc_templates.instantiate("cu", "de", conftest.tmpdir("dt_languages_de_target") / "1", template=both)
        assert made.is_file() and MARK in _read(made.parent / _leaves(german, "cu")[0]["file"])
        # a description saved for the first time in a language, where the template had none of its own: every language of a template that has one is given one
        bare = doc_templates.save_from_document(here, "bp", "Base courte", settings=ctx.settings)
        assert bare.meta.get("description") is None
        again = doc_templates.save_from_document(german, "bp", "Kurze Basis", "Eine kurze Basis", folder="Base courte", overwrite=True, settings=ctx.settings)
        assert again.languages == ["fr", "de"] and again.description("de") == "Eine kurze Basis" and again.description("fr") == "Eine kurze Basis" and not again.error


def test_an_existing_template_is_refused_unless_overwritten_and_what_is_replaced_is_kept():
    with _own("dt_overwrite") as ctx:
        here = _new_project("dt_overwrite_project")
        first, _second = _prefill(here, "cu")
        saved = doc_templates.save_from_document(here, "cu", "Courte", "Première", settings=ctx.settings)
        old = {rel: (saved.language_dir("fr") / rel).read_bytes() for rel in _files(saved.language_dir("fr"))}
        exc = _refused("exists", here, "cu", "Courte", settings=ctx.settings)
        assert "user:cu/Courte" in str(exc) and "overwrite" in str(exc)
        assert {rel: (saved.language_dir("fr") / rel).read_bytes() for rel in _files(saved.language_dir("fr"))} == old, "a refusal wrote nothing"
        # the document changes, and the template is written over: the French folder replaced, the old one kept in archives/
        with open(here.document_dir("cu") / first["file"], "a", encoding="utf-8", newline="") as handle:
            handle.write("\nSECONDEMARQUE\n")
        again = doc_templates.save_from_document(here, "cu", "Courte", "Seconde", overwrite=True, settings=ctx.settings)
        assert not again.error and again.languages == ["fr"] and again.description("fr") == "Seconde" and again.folder == saved.folder
        assert "SECONDEMARQUE" in _read(again.language_dir("fr") / first["file"]) and MARK in _read(again.language_dir("fr") / first["file"])
        kept = sorted((ctx.user / doc_templates.ARCHIVES).iterdir())
        assert len(kept) == 1 and kept[0].name.endswith("-cu-Courte-fr"), [p.name for p in kept]
        assert {rel: (kept[0] / rel).read_bytes() for rel in _files(kept[0])} == old, "the old language folder is kept whole"
        assert [t.ref for t in doc_templates.list_templates(settings=ctx.settings)] == ["builtin:cu/standard", "builtin:bp/standard", "builtin:rs/standard", "user:cu/Courte"], "an archive is no template"
        _nothing_staged(ctx.user)
        # a write that fails after the old folder was moved puts it back, and leaves the template.json as it was
        now = {rel: (again.language_dir("fr") / rel).read_bytes() for rel in _files(again.language_dir("fr"))}
        meta_bytes = (again.folder / doc_templates.FILE).read_bytes()
        real = doc_templates._write_json

        def failing(path, meta):
            if Path(path).parent.parent.name == "cu":
                raise OSError("the disk is full")
            return real(path, meta)

        with open(here.document_dir("cu") / first["file"], "a", encoding="utf-8", newline="") as handle:
            handle.write("\nTROISIEMEMARQUE\n")
        doc_templates._write_json = failing
        try:
            _refused("write_failed", here, "cu", "Courte", "Troisième", overwrite=True, settings=ctx.settings)
        finally:
            doc_templates._write_json = real
        assert {rel: (again.language_dir("fr") / rel).read_bytes() for rel in _files(again.language_dir("fr"))} == now, "the folder replaced was not put back"
        assert (again.folder / doc_templates.FILE).read_bytes() == meta_bytes
        assert "TROISIEMEMARQUE" not in _read(again.language_dir("fr") / first["file"]), "the template took the document of the write that failed"
        assert len(sorted((ctx.user / doc_templates.ARCHIVES).iterdir())) == 1, "an undone replacement left its archive behind"
        _nothing_staged(ctx.user)
        # a folder that is not a template of this module is not written over, nor one of another document
        (ctx.user / "cu" / "Stranger").mkdir()
        _refused("not_a_template", here, "cu", "Autre", folder="Stranger", overwrite=True, settings=ctx.settings)
        (ctx.user / "cu" / "Foreign").mkdir()
        (ctx.user / "cu" / "Foreign" / doc_templates.FILE).write_text(json.dumps({"mode": "bp", "languages": ["fr"]}), encoding="utf-8")
        _refused("mode_mismatch", here, "cu", "Autre", folder="Foreign", overwrite=True, settings=ctx.settings)


def test_saving_refuses_what_it_cannot_save_with_a_code_and_writes_nothing():
    with _own("dt_refusals") as ctx:
        here = _new_project("dt_refusals_project")
        builtin_name = _template("cu").name("fr")
        s = ctx.settings
        _refused("bad_mode", here, "xx", "Rapport", settings=s)
        _refused("read_only", here, "cu", "Courte", place="builtin", settings=s)
        _refused("bad_place", here, "cu", "Courte", place="nowhere", settings=s)
        _refused("no_folder", here, "cu", "Courte", place="office", settings={})
        _refused("no_folder", here, "cu", "Courte", place="shared", settings={})
        _refused("bad_language", here, "cu", "Courte", language="it", settings=s)
        legacy = project.Project(conftest.tmpdir("dt_refusals_legacy") / "Old.woodcore", {"schema_version": project.SCHEMA_VERSIONS[0], "format": project.FORMAT, "name": "Old"})
        _refused("no_such_document", legacy, "cu", "Courte", settings=s)
        for bad in ("", "   ", None, {"de": "Kurz"}, {"fr": "  "}, "a\nb", 5):
            _refused("no_name", here, "cu", bad, settings=s)
        _refused("bad_language", here, "cu", {"fr": "Courte", "it": "Corta"}, settings=s)
        for folder in ("a/b", "a\\b", "..", ".", "a?b", "NUL", "con.txt", "trailing.", "x:y"):
            _refused("bad_folder", here, "cu", "Courte", folder=folder, settings=s)
        _refused("name_is_builtin", here, "cu", builtin_name, settings=s)
        _refused("name_is_builtin", here, "cu", builtin_name.upper(), folder="Autre", settings=s)
        assert not ctx.user.exists() and not ctx.office.exists(), "a refusal created a place"
        # the document itself
        for name, what, code in (("entry", lambda h: h.document_typ("cu").unlink(), "no_entry"),
                                 ("structure", lambda h: h.structure_file("cu").write_text("{", encoding="utf-8"), "structure_unreadable"),
                                 ("other", lambda h: h.structure_file("cu").write_bytes(h.structure_file("bp").read_bytes()), "structure_unreadable"),
                                 ("section", lambda h: (h.document_dir("cu") / _leaves(h, "cu")[0]["file"]).unlink(), "section_missing"),
                                 ("block", lambda h: h.document_typ("cu").write_text(_read(h.document_typ("cu")).replace(structure.END_TAG, "// end"), encoding="utf-8"), "entry_unreadable")):
            broken = _copy_project(here, f"dt_refusals_{name}")
            what(broken)
            _refused(code, broken, "cu", "Courte", settings=s)
            _nothing_staged(ctx.user)
        assert not ctx.user.exists(), "a document that could not be read left a place behind"
        # what is taken: a folder, a name, a project template's place
        doc_templates.save_from_document(here, "cu", "Courte", settings=s)
        _refused("exists", here, "cu", "Courte", settings=s)
        _refused("name_taken", here, "cu", "Courte", folder="Autre", settings=s)
        _refused("name_taken", here, "cu", {"fr": "courte"}, folder="Encore", settings=s)
        assert sorted(p.name for p in (ctx.user / "cu").iterdir()) == ["Courte"]
        # the same name in another place, and for another document, is not a clash
        doc_templates.save_from_document(here, "cu", "Courte", place="office", settings=s)
        doc_templates.save_from_document(here, "bp", "Courte", settings=s)
        (ctx.office / doc_templates.FILE).write_text("{}", encoding="utf-8")
        _refused("place_taken", here, "cu", "Autre", place="office", settings=s)
        # the template made is read back before it is moved: one that cannot be used is not put in its place
        real = doc_templates.read

        def flawed(folder, mode, place="builtin"):
            found = real(folder, mode, place)
            if Path(folder).parent.name.startswith(doc_templates.STAGING):
                found.error = "a defect only the check finds"
            return found

        doc_templates.read = flawed
        try:
            _refused("invalid", here, "cu", "Invalide", settings=s)
        finally:
            doc_templates.read = real
        assert not (ctx.user / "cu" / "Invalide").exists()
        _nothing_staged(ctx.user)
        _nothing_staged(ctx.office)


def test_a_template_taken_away_is_moved_into_archives_and_a_builtin_one_cannot_be():
    with _own("dt_delete") as ctx:
        here = _new_project("dt_delete_project")
        _prefill(here, "cu")
        s = ctx.settings
        mine = doc_templates.save_from_document(here, "cu", "Courte", settings=s)
        office = doc_templates.save_from_document(here, "cu", "Courte bureau", place="office", folder="Bureau", settings=s)
        files = {rel: (mine.language_dir("fr") / rel).read_bytes() for rel in _files(mine.language_dir("fr"))}
        gone = doc_templates.delete(mine.ref, settings=s)
        assert gone.parent == ctx.user / doc_templates.ARCHIVES and gone.name.endswith("-cu-Courte") and gone.is_dir()
        assert {rel: (gone / "fr" / rel).read_bytes() for rel in _files(gone / "fr")} == files and (gone / doc_templates.FILE).is_file(), "nothing is deleted"
        assert not mine.folder.exists()
        assert [t.ref for t in doc_templates.list_templates("cu", settings=s)] == ["builtin:cu/standard", "office:cu/Bureau"]
        for ref in (mine.ref, "user:cu/courte"):
            try:
                doc_templates.find(ref, settings=s)
            except doc_templates.DocTemplateError as exc:
                assert exc.code == "no_such_template"
            else:
                raise AssertionError("a template taken away was found")
        # the same name saved and taken away again in the same second does not meet the first archive
        again = doc_templates.save_from_document(here, "cu", "Courte", settings=s)
        second = doc_templates.delete(again, settings=s)
        assert second != gone and second.is_dir() and gone.is_dir()
        # the office's, by a reference in either word for its place
        assert doc_templates.delete("shared:cu/Bureau", settings=s).parent == ctx.office / doc_templates.ARCHIVES and not office.folder.exists()
        # builtin ones and what is not a reference
        for ref, code in (("builtin:cu/standard", "read_only"), ("builtin:bp/standard", "read_only"), ("standard", "no_such_template"), ("Courte", "no_such_template"),
                          ("user:cu/nope", "no_such_template"), ("user:xx/nope", "no_such_template"), ("", "no_such_template"), ("user:cu/", "no_such_template")):
            try:
                doc_templates.delete(ref, settings=s)
            except doc_templates.DocTemplateError as exc:
                assert exc.code == code, (ref, exc.code, str(exc))
            else:
                raise AssertionError(f"{ref!r} was deleted")
        assert doc_templates.find("builtin:cu/standard", settings=s).folder.is_dir(), "a builtin template is where it was"
        # a template that cannot be used can be taken away all the same
        (ctx.user / "cu" / "Broken").mkdir(parents=True)
        (ctx.user / "cu" / "Broken" / doc_templates.FILE).write_text("{not json", encoding="utf-8")
        assert doc_templates.delete("user:cu/Broken", settings=s).is_dir() and not (ctx.user / "cu" / "Broken").exists()


def test_the_office_place_lies_beside_the_engineers_and_the_builtin_ones():
    with _own("dt_office") as ctx:
        here = _new_project("dt_office_project")
        _prefill(here, "cu")
        s = ctx.settings
        mine = doc_templates.save_from_document(here, "cu", "Courte", settings=s)
        office = doc_templates.save_from_document(here, "cu", "Courte bureau", place="shared", folder="Courte", settings=s)
        assert office.ref == "office:cu/Courte" and office.place == "office" and office.folder == ctx.office / "cu" / "Courte" and not office.read_only
        assert doc_templates.place_dir("user", s) == ctx.user and doc_templates.place_dir("office", s) == ctx.office and doc_templates.place_dir("shared", s) == ctx.office
        assert doc_templates.place_dir("builtin") == doc_templates.BUILTIN_DIR
        assert doc_templates.place_dir("office", {}) is None, "no shared folder named, no office's place"
        assert [t.ref for t in doc_templates.list_templates("cu", settings=s)] == ["builtin:cu/standard", "user:cu/Courte", "office:cu/Courte"]
        assert [t.ref for t in doc_templates.list_templates("cu", settings={})] == ["builtin:cu/standard", "user:cu/Courte"]
        assert [t.ref for t in doc_templates.list_templates("cu", "fr", s)] == ["builtin:cu/standard", "user:cu/Courte", "office:cu/Courte"]
        assert doc_templates.find("Courte", settings=s).ref == mine.ref, "a bare name: the engineer's own first, then the office's"
        assert doc_templates.find("courte bureau", settings=s).ref == office.ref
        assert doc_templates.find("office:cu/Courte", settings=s).ref == office.ref and doc_templates.find("shared:cu/Courte", settings=s).ref == office.ref
        assert doc_templates.find("user:cu/Courte", settings=s).ref == mine.ref
        try:
            doc_templates.find("office:cu/Courte", settings={})
        except doc_templates.DocTemplateError as exc:
            assert exc.code == "no_such_template"
        else:
            raise AssertionError("the office's template was found without the office's folder")
        # a bare name that matches a template that cannot be used and a sound one finds the sound one; a reference to the broken one says why
        (ctx.user / "cu" / "Standard").mkdir()
        (ctx.user / "cu" / "Standard" / doc_templates.FILE).write_text("{not json", encoding="utf-8")
        assert doc_templates.find("standard", "cu", s).ref == "builtin:cu/standard"
        try:
            doc_templates.find("user:cu/Standard", settings=s)
        except doc_templates.DocTemplateError as exc:
            assert exc.code == "template_unusable" and "cannot be read" in str(exc)
        else:
            raise AssertionError("a template that cannot be read was found")
        # a new project made from the office's template, found by reading the preferences as a window does
        with _settings_file(s):
            made = project_template.create(conftest.tmpdir("dt_office_new") / "Neuf", "Neuf", document_language="fr", report_language="fr",
                                           document_templates={"cu": "office:cu/Courte", "bp": "builtin:bp/standard"})
        assert MARK in _read(made.document_dir("cu") / _leaves(made, "cu")[0]["file"])


def test_the_shared_sections_of_a_template_are_shared_again_where_the_other_document_carries_the_id():
    with _own("dt_sharing") as ctx:
        here = _new_project("dt_sharing_project")
        # live-loads is shared with the report as well as with the base de projet, in the document the template is saved from
        path = here.structure_file("cu")
        held = structure.read(path)
        structure.find(held, "live-loads")[0]["shared_with"] = ["bp", "rs"]
        structure.write(path, held)
        template = doc_templates.save_from_document(here, "cu", "Partagée", settings=ctx.settings)

        def flags(entry):
            return {node["id"]: node["shared_with"] for node, _d in structure.leaves(structure.read(entry.parent / "structure.json")) if node.get("shared_with")}

        def made(name, **kwargs):
            return doc_templates.instantiate("cu", "fr", conftest.tmpdir(name) / "1", template=template, **kwargs)

        everything = made("dt_sharing_all")
        assert flags(everything)["live-loads"] == ["bp", "rs"], "by default a template is copied as it is"
        assert flags(made("dt_sharing_both", siblings=("bp", "rs"))) == flags(everything), "the documents the project has keep every flag"
        only = made("dt_sharing_bp", siblings=("bp",))
        assert flags(only)["live-loads"] == ["bp"] and flags(only)["norms"] == ["bp"], "a document the project has keeps its flag"
        nobody = made("dt_sharing_nobody", siblings=())
        assert flags(nobody) == {}, "no document to share with, no flag"
        assert "// woodcore:shared live-loads" in _read(nobody.parent / "Sections" / "live-loads.typ"), "the tags stay: they are what sharing is"
        assert structure.sync_entry(nobody, nobody.parent / "structure.json", "fr") is False
        for bad in (("xx",), ("cu-bp",)):
            target = conftest.tmpdir("dt_sharing_bad") / "1"
            try:
                doc_templates.instantiate("cu", "fr", target, template=template, siblings=bad)
            except doc_templates.DocTemplateError as exc:
                assert exc.code == "bad_mode", exc
            else:
                raise AssertionError("a document that is none was taken for a sibling")
            assert not target.exists()
        # settling: the flags written again from the tags. A project whose base de projet does not carry the block has a flag that says nothing
        new = _new_project("dt_sharing_new", document_templates={"cu": template.ref})
        # create settles the sharing once both documents are there: the flag for a report that holds no copy is already gone
        cu_live = structure.find(structure.read(new.structure_file("cu")), "live-loads")[0]
        assert cu_live["shared_with"] == ["bp"], cu_live
        assert not doc_templates.settle_sharing(new).changes, "create left a flag to settle"
        live = new.document_dir("bp") / "Sections" / "live-loads.typ"
        text = _read(live)
        for tag in ("// woodcore:shared live-loads\n", "// woodcore:/shared live-loads\n"):
            assert tag in text
            text = text.replace(tag, "")
        with open(live, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)
        result = doc_templates.settle_sharing(new)
        assert not result.problems, result.problems
        assert {(d.mode, d.id) for d in result.changes} >= {("cu", "live-loads"), ("bp", "live-loads")}, result.changes
        assert "live-loads" not in {n["id"] for n in _leaves(new, "cu") if n.get("shared_with")} and "live-loads" not in {n["id"] for n in _leaves(new, "bp") if n.get("shared_with")}
        assert not doc_templates.settle_sharing(new).changes, "settled"


def test_a_saved_template_says_what_a_document_made_from_it_would_miss():
    with _own("dt_notes") as ctx:
        here = _new_project("dt_notes_project")
        first, second = _leaves(here, "cu")[:2]
        folder = here.document_dir("cu")
        with open(folder / first["file"], "a", encoding="utf-8", newline="") as handle:
            handle.write('\n#image("/Images/site.png")\n#doc-image(file: "/Images/plan.png")\n')
        with open(folder / second["file"], "a", encoding="utf-8", newline="") as handle:
            handle.write('\n#image("/Images/site.png")\n// woodcore:object doc-field unclosed\n')
        template = doc_templates.save_from_document(here, "cu", "Avec images", settings=ctx.settings)
        assert not template.error, "a template that names a missing picture is still a template"
        codes = {note.code: note for note in template.notes}
        assert set(codes) == {"template_files", "template_tags"}, [n.code for n in template.notes]
        files = codes["template_files"].args["files"]
        assert files == {"/Images/site.png": [first["file"], second["file"]], "/Images/plan.png": [first["file"]]}, files
        assert "/Images/plan.png" in str(codes["template_files"]) and isinstance(codes["template_files"], str)
        assert codes["template_tags"].args["file"] == second["file"] and second["file"] in str(codes["template_tags"])
        # what the engine itself names is not a file the project is missing
        clean = doc_templates.save_from_document(_new_project("dt_notes_clean"), "bp", "Sans images", settings=ctx.settings)
        assert clean.notes == [], [str(n) for n in clean.notes]


def test_every_refusal_of_the_module_states_a_code_of_the_list():
    source = _read(ROOT / "calc" / "doc_templates.py")
    start = source.index("CODES = (")
    body = source[:start] + source[source.index("\n)", start):]
    stated = set(re.findall(r'_refuse\(\s*"([a-z_]+)"', body)) | set(re.findall(r'code = "([a-z_]+)"', body))
    assert stated <= set(doc_templates.CODES), sorted(stated - set(doc_templates.CODES))
    assert set(doc_templates.CODES) <= set(re.findall(r'"([a-z_]+)"', body)), sorted(set(doc_templates.CODES) - set(re.findall(r'"([a-z_]+)"', body)))
    assert len(set(doc_templates.CODES)) == len(doc_templates.CODES)
    error = doc_templates.DocTemplateError("x")
    assert error.code == "" and error.values == {}, "an older refusal states no code"
    assert isinstance(error, validation.ValidationError)

# --- bringing one in: the settings' «Importer un dossier…» (v0.113) ------------------------------------

def _importable(name, mode="cu", folder="courte"):
    """A copy of the builtin template of `mode` in this process's own folder, under `folder` and named «Courte <lang>» in each of its languages -- a template an office's shared folder could hold."""
    target = conftest.tmpdir(name) / folder
    shutil.copytree(_template(mode).folder, target)
    meta = json.loads(_read(target / doc_templates.FILE))
    meta["name"] = {lang: f"Courte {lang}" for lang in meta["languages"]}
    (target / doc_templates.FILE).write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return target


def _tree(folder):
    return {p.relative_to(folder).as_posix(): p.read_bytes() for p in sorted(Path(folder).rglob("*")) if p.is_file()}


def _import_refused(code, *args, **kwargs):
    """`doc_templates.import_folder(*args, **kwargs)` is refused, stating `code`; the refusal is returned."""
    try:
        doc_templates.import_folder(*args, **kwargs)
    except doc_templates.DocTemplateError as exc:
        assert exc.code == code, f"refused with {exc.code!r} and not {code!r}: {exc}"
        assert exc.code in doc_templates.CODES and str(exc), exc
        return exc
    raise AssertionError(f"{args} was imported, and {code!r} was expected")


def test_a_document_template_folder_is_imported_into_the_engineers_own_place_and_replaced_on_request():
    with _own("dt_import") as ctx:
        s = ctx.settings
        source = _importable("dt_import_source")
        files = _tree(source)
        made = doc_templates.import_folder(source, "cu", settings=s)
        assert made.ref == "user:cu/courte" and made.place == "user" and made.folder == ctx.user / "cu" / "courte" and not made.error, made.error
        assert made.name("fr") == "Courte fr" and made.languages == ["fr", "de", "en"]
        assert _tree(made.folder) == files and _tree(source) == files, "the copy is not the folder imported, or the folder imported was changed"
        assert [t.ref for t in doc_templates.list_templates("cu", settings=s)] == ["builtin:cu/standard", "user:cu/courte"]
        _nothing_staged(ctx.user)
        # one of that folder's name is there: refused, nothing changed -- then replaced on request, the old one archived and never deleted
        (made.folder / "marker.txt").write_text("the old one\n", encoding="utf-8")
        assert _import_refused("exists", source, "cu", settings=s).values["folder"] == "courte"
        assert (made.folder / "marker.txt").is_file()
        again = doc_templates.import_folder(source, "cu", replace=True, settings=s)
        assert again.ref == made.ref and not again.error and _tree(again.folder) == files
        archived = list((ctx.user / doc_templates.ARCHIVES).iterdir())
        assert len(archived) == 1 and archived[0].name.endswith("-cu-courte") and (archived[0] / "marker.txt").is_file(), archived
        assert [t.ref for t in doc_templates.list_templates(settings=s)] == ["builtin:cu/standard", "builtin:bp/standard", "builtin:rs/standard", "user:cu/courte"]
        _nothing_staged(ctx.user)


def test_importing_a_document_template_refuses_what_is_not_one_of_that_document_and_writes_nothing():
    import templates
    with _own("dt_import_refused") as ctx:
        s = ctx.settings
        _import_refused("not_a_folder", ctx.base / "nowhere", "cu", settings=s)
        (ctx.base / "empty").mkdir()
        assert _import_refused("no_template", ctx.base / "empty", "cu", settings=s).values["folder"] == str(ctx.base / "empty")
        _import_refused("project_template", templates.standard().folder, "cu", settings=s)
        other = _importable("dt_import_bp", "bp", "kurz")
        exc = _import_refused("mode_mismatch", other, "cu", settings=s)
        assert exc.values["document"] == "bp" and exc.values["mode"] == "cu"
        assert doc_templates.import_folder(other, "bp", settings=s).ref == "user:bp/kurz", "the same folder is imported under its own document"
        broken = _importable("dt_import_broken", folder="kaputt")
        shutil.rmtree(broken / "de")
        assert "de" in _import_refused("invalid", broken, "cu", settings=s).values["error"]
        _import_refused("name_is_builtin", _template("cu").folder, "cu", settings=s)
        _import_refused("bad_mode", other, "xx", settings=s)
        assert _import_refused("mode_mismatch", other, "rs", settings=s).values["document"] == "bp"
        _import_refused("already_mine", ctx.user / "bp" / "kurz", "bp", settings=s)
        assert [t.ref for t in doc_templates.list_templates(settings=s) if t.place == "user"] == ["user:bp/kurz"], "a refused import wrote something"
        _nothing_staged(ctx.user)


# --- the report's content templates (v0.114) --------------------------------------------------------------------

RS_STEMS = ["001-einleitung", "002-grundlagen", "003-baustoffe", "004-einwirkungen", "005-tragwerksanalyse", "006-nachweise", "007-literatur", "008-journal", "009-anhang"]
# The report marks a section it does not print by commenting its include line out: the annexes are off by default (v0.115).
RS_PRINTED = {"009-anhang": False}
RS_FIRST = {"de": "Einleitung", "fr": "Introduction", "en": "Introduction"}


def test_the_reports_template_is_there_and_sound_in_three_languages():
    """`builtin:rs/standard`: found by `default_ref("rs")`, sound, named and described in the three languages; each language folder exactly a report's folder -- `Statischer Rapport.typ`, as a project names it, and `Sections/` with the same numbered files in every language, each included once in order -- root-absolute imports, the title page and the metadata the report's own, the engine's language the folder's, every heading and paragraph an object, its headings in the folder's language, LF, no ß, the French spaced."""
    template = doc_templates.find(doc_templates.default_ref("rs"), "rs")
    assert template.ref == "builtin:rs/standard" and not template.error and template.read_only, template.error
    assert template.languages == list(LANGS)
    assert len({template.name(lang) for lang in LANGS}) == 3 and all(template.description(lang) for lang in LANGS)
    validation.validate_structure(template.meta, "document-template")
    for lang in LANGS:
        folder = template.language_dir(lang)
        entry = template.entry_file(lang)
        assert entry is not None and entry.name == documents.RS_ENTRY, (lang, entry)
        assert sorted(p.name for p in folder.iterdir()) == sorted([entry.name, "Sections"]), lang
        assert sorted(p.stem for p in (folder / "Sections").iterdir()) == RS_STEMS, lang
        text = _read(entry)
        assert doc_templates.report_includes(text) == [(f"{stem}.typ", RS_PRINTED.get(stem, True)) for stem in RS_STEMS], lang
        assert '#import "/config.typ": conf' in text and '#import "/commands.typ": *' in text and "../" not in text, lang
        assert '#show: woodcore-document.with(document: "rs")' in text and '#title-page(document: "rs")' in text, lang
        assert re.search(rf'set-report-language\(\s*sys\.inputs\.at\(\s*"lang"\s*,\s*default:\s*"{lang}"\s*\)\s*\)', text), lang
        for path in sorted((folder / "Sections").iterdir()):
            body = _read(path)
            where = f"rs/{lang}/{path.name}"
            assert body.startswith('#import "/commands.typ": *\n\n') and "../" not in body and "\r" not in body, where
            assert not structure.check_tags(body), where
            assert "ß" not in body, where
            assert body.split("\n")[2:5] == ["// woodcore:object heading title", body.split("\n")[3], "// woodcore:/object title"] and body.split("\n")[3].startswith("= "), where
        assert "= " + RS_FIRST[lang] in _read(folder / "Sections" / "001-einleitung.typ").split("\n"), lang
        assert "= " + JOURNAL[lang] in _read(folder / "Sections" / "008-journal.typ").split("\n"), lang
        if lang == "fr":
            for path in sorted((folder / "Sections").iterdir()):
                inside = False
                for line in _read(path).split("\n"):
                    if line.startswith("// woodcore:"):
                        inside = line.startswith("// woodcore:object")     # a heading or a paragraph: prose; what stands between them is code
                        continue
                    if not inside:
                        continue
                    for m in re.finditer(r"(.)([:;!?])(?=\s|$)", line):
                        assert m.group(1) == "\u202f", f"{path.name}: {line!r}"


def test_a_reports_template_that_cannot_make_a_report_says_what_is_wrong_with_it():
    def broken(name, what, mutate):
        folder = conftest.tmpdir(name) / "standard"
        shutil.copytree(doc_templates.find("builtin:rs/standard").folder, folder)
        mutate(folder)
        template = doc_templates.read(folder, "rs", "user")
        assert template.error and what in template.error, (what, template.error)

    entry = documents.RS_ENTRY
    broken("dt_rs_orphan", "no #include of the entry names it", lambda f: (f / "fr" / "Sections" / "009-extra.typ").write_text("= X\n", encoding="utf-8"))
    broken("dt_rs_missing", "which is not there", lambda f: (f / "fr" / "Sections" / "003-baustoffe.typ").unlink())
    broken("dt_rs_name", "is not named NNN-<name>.typ", lambda f: (f / "fr" / "Sections" / "001-einleitung.typ").rename(f / "fr" / "Sections" / "einleitung.typ"))
    broken("dt_rs_twice", "more than once", lambda f: (f / "fr" / entry).write_text(_read(f / "fr" / entry) + '#include "Sections/001-einleitung.typ"\n', encoding="utf-8"))
    broken("dt_rs_subfolder", "lies in a folder inside Sections/", lambda f: ((f / "fr" / "Sections" / "archives").mkdir(), (f / "fr" / "Sections" / "archives" / "x.typ").write_text("x", encoding="utf-8")))

    def clash(folder):
        sections = folder / "fr" / "Sections"
        (sections / "009-einleitung.typ").write_text("= X\n", encoding="utf-8")
        path = folder / "fr" / entry
        path.write_text(_read(path) + '#include "Sections/009-einleitung.typ"\n', encoding="utf-8")
    broken("dt_rs_clash", "two sections are called 'einleitung'", clash)


def test_the_reports_template_is_instantiated_never_over_another_and_compiles_in_a_project():
    """`instantiate("rs", ...)` copies the entry and the sections, writes nothing over another file and leaves nothing behind where it refuses; and a project's report replaced by the template's -- the report's folder emptied of its sections and its entry, the template's copied in -- compiles with the engine the project carries, its headings in the project's language."""
    target = conftest.tmpdir("dt_rs_instantiate") / "3"
    entry = doc_templates.instantiate("rs", "en", target)
    assert entry.name == documents.RS_ENTRY and sorted(_files(target)) == sorted([documents.RS_ENTRY] + [f"Sections/{s}.typ" for s in RS_STEMS])
    assert _read(target / "Sections" / "001-einleitung.typ") == _read(doc_templates.find("builtin:rs/standard").language_dir("en") / "Sections" / "001-einleitung.typ")
    try:
        doc_templates.instantiate("rs", "en", target)
    except doc_templates.DocTemplateError as exc:
        assert "is there already" in str(exc)
    else:
        raise AssertionError("a report was written over another")
    try:
        doc_templates.instantiate("rs", "fr", conftest.tmpdir("dt_rs_mismatch") / "3", template="builtin:cu/standard")
    except doc_templates.DocTemplateError as exc:
        assert exc.code == "mode_mismatch"
    else:
        raise AssertionError("a convention was made into a report")
    if not conftest.have_typst():
        raise Skip("no typst on the path")
    for lang in LANGS:
        here = _copy_project(_project(lang), f"dt_rs_project_{lang}")
        folder = here.document_dir("rs")
        shutil.rmtree(folder / "Sections")
        here.document_typ("rs").unlink()
        doc_templates.instantiate("rs", lang, folder, entry_name=here.document_typ("rs").name)
        run, _seconds = _compile(here, "rs")
        assert run.returncode == 0, f"rs/{lang}: {run.stderr[:3000]}"
        text = _text(here.document_pdf("rs"))
        assert RS_FIRST[lang] in text and JOURNAL[lang] in text, lang


def test_a_report_is_saved_as_a_template_and_read_back():
    """«Enregistrer comme modèle…» on the report: its entry and the section files its include lines name -- a commented-out one too --, and nothing else (no archive, no PDF, no section the entry does not include); the template made sound and offered for the project's language, and a new report made from it the same files."""
    with _own("dt_rs_save") as ctx:
        here = _new_project("dt_rs_save_project", "de")
        folder = here.document_dir("rs")
        sections = folder / "Sections"
        with open(sections / "002-grundlagen.typ", "a", encoding="utf-8", newline="") as handle:
            handle.write(f"\n{MARK}\n")
        entry = here.document_typ("rs")
        entry.write_text(_read(entry).replace('#include "Sections/006-nachweise.typ"', '// #include "Sections/006-nachweise.typ"'), encoding="utf-8")
        (sections / "archives").mkdir()
        (sections / "archives" / "260101-000000-old.typ").write_text("= Old\n", encoding="utf-8")
        (sections / "099-loose.typ").write_text("= Loose\n", encoding="utf-8")
        (folder / "Statischer Rapport.pdf").write_bytes(b"%PDF-1.4\n")
        saved = doc_templates.save_from_document(here, "rs", "Bericht kurz", "Ein kurzer Bericht", settings=ctx.settings)
        assert saved.ref == "user:rs/Bericht kurz" and not saved.error, saved.error
        assert saved.languages == ["de"]
        assert sorted(_files(saved.language_dir("de"))) == sorted([documents.RS_ENTRY] + [f"Sections/{p.name}" for p in sections.glob("0[0-8]*.typ")])
        assert MARK in _read(saved.language_dir("de") / "Sections" / "002-grundlagen.typ")
        assert ("006-nachweise.typ", False) in doc_templates.report_includes(_read(saved.language_dir("de") / documents.RS_ENTRY))
        assert [t.ref for t in doc_templates.list_templates("rs", "de", ctx.settings)] == ["builtin:rs/standard", "user:rs/Bericht kurz"]
        assert [t.ref for t in doc_templates.list_templates("rs", "fr", ctx.settings)] == ["builtin:rs/standard"]
        made = conftest.tmpdir("dt_rs_save_made") / "3"
        doc_templates.instantiate("rs", "de", made, template=saved)
        assert {rel: _read(made / rel) for rel in _files(made)} == {rel: _read(saved.language_dir("de") / rel) for rel in _files(saved.language_dir("de"))}
        # a report whose include names a file that is not there is refused, and nothing is written
        entry.write_text(_read(entry) + '#include "Sections/050-ghost.typ"\n', encoding="utf-8")
        exc = _refused("section_missing", here, "rs", "Bericht zwei", settings=ctx.settings)
        assert "Sections/050-ghost.typ" in exc.values["files"]
        _nothing_staged(ctx.user)
