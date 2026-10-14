"""Importing from another document of the project and moving objects (calc/doc_import.py, the three document modes, rework package R1-F).

What is held here: `importable` listing a document's sections -- chapters, sections, and under each the tagged objects of its file, with their type, their label and what they are shared as; `import_items` bringing **whole sections** in at the bottom of the target's tree, linked (shared, `shared_with` on both sides) or as an independent copy (no shared tag, a fresh id), from the convention into the base de projet and the report and back; **objects ticked alone** appended to the section «Importé» -- created at the bottom the first time, written to where it is after -- linked (wrapped in shared tags in the source file **and** the copy, the block identical between the tags, the shared id made from the object's own) or independent (no tag, a free object id); an object that is alone in a shared block shared under that block's id, one inside a larger block refused when linked; the section winning where it and its objects are ticked together; every refusal with its code and **nothing written**; a failure halfway putting back everything; CRLF files staying CRLF; the copies **compiling**. `move_object` moving an object -- with its shared tags where it is alone in a shared block -- inside a file and into another, above, below and to the end, refusing to take one out of a larger shared block or to nest a shared block, and everything else of both files staying byte for byte; `move_section` being structure.move_node.

The synchronisation records (calc/sync.py): the copies an import makes start in step, and a shared block reordered in one document is local there and incoming in the others.

Every project is a copy of one made once by project_template.create, and the sections a check imports from or moves are written here -- by structure.add_section, whose file is then overwritten with known text -- so the checks do not depend on what the content templates of the convention and the base de projet hold.
"""

import re
import shutil
import subprocess
import types
from pathlib import Path

import conftest
from conftest import Skip

import doc_import
import documents
import project
import project_template
import sharing
import structure
import sync
import typst_objects
import typst_paths

TITLES = {"fr": "Sondes", "de": "Sonden", "en": "Probes"}
C = typst_objects.Content


# --- the project ---------------------------------------------------------------------------------------------

def _field(label, value):
    return typst_objects.Call("doc-field", {"label": C(label), "value": C(value)})


def _table(caption, rows):
    return typst_objects.Call("doc-table", {
        "columns": [{"id": "a", "title": C("Raum")}, {"id": "b", "title": C("Fläche")}],
        "hidden": [], "rows": [{"a": C(a), "b": C(b)} for a, b in rows], "caption": C(caption)})


def _set_section(here, mode, section_id, title, parts):
    """The section's file written: the import line, the heading, then `parts` one after the other -- a string is a paragraph, (kind, id, call) an object -- a blank line between two."""
    path = _file(here, mode, section_id)
    pieces = [documents.import_line(here), "", f"= {title}", ""]
    for part in parts:
        if isinstance(part, str):
            pieces += [part, ""]
        else:
            kind, object_id, call = part
            pieces += [typst_objects.insert_object("", -1, kind, object_id, call).rstrip("\n"), ""]
    typst_paths.write_text(path, "\n".join(pieces))


def _file(here, mode, name):
    return here.document_dir(mode) / "Sections" / f"{name}.typ"


_BASE = {}


def _build_base():
    """A project of three documents -- a group `probes` in the convention and the base de projet, three probe sections in the convention, two in the base de projet, one in the report. What the content templates put in the convention and the base de projet is taken out first: the checks work on what they write themselves, and a tree of a few sections is read in a tenth of the time."""
    here = project_template.create(conftest.tmpdir("doc_import_base") / "Halle", "Halle")
    for mode in ("cu", "bp"):
        for old in (here.document_dir(mode) / "Sections").glob("*.typ"):
            old.unlink()
        structure.write(here.structure_file(mode), structure.blank(mode))
        structure.sync_entry(here.document_typ(mode), here.structure_file(mode), structure.document_language(here, mode))
        structure.add_group(here, mode, None, None, "probes", TITLES)
    for section_id, title in (("probe-a", "Sonde A"), ("probe-b", "Sonde B"), ("probe-c", "Sonde C")):
        structure.add_section(here, "cu", "probes", None, section_id, title)
    for section_id, title in (("probe-bp", "Sonde BP"), ("probe-bp2", "Sonde BP zwei")):
        structure.add_section(here, "bp", "probes", None, section_id, title)
    structure.add_section(here, "rs", None, None, "009-probe-rs", "Sonde RS")
    _set_section(here, "cu", "probe-a", "Sonde A", [
        "Text eins.",
        ("doc-field", "use-field", _field("Nutzung", "Büro")),
        "Text zwei.",
        "== Detail",
        ("doc-table", "rooms-table", _table("Räume", [("Küche", "12")])),
        "Text drei.",
    ])
    _set_section(here, "cu", "probe-b", "Sonde B", [("doc-field", "only-field", _field("Dauer", "50 Jahre"))])
    _set_section(here, "cu", "probe-c", "Sonde C", [
        "Text C.",
        ("doc-field", "c-one", _field("Eins", "a")),
        ("doc-field", "c-two", _field("Zwei", "b")),
        "Ende C.",
    ])
    _set_section(here, "bp", "probe-bp", "Sonde BP", ["BP-Text.", ("doc-field", "bp-field", _field("Basis", "x"))])
    _set_section(here, "bp", "probe-bp2", "Sonde BP zwei", ["Zweiter BP-Text.", ("doc-field", "bp-two", _field("Zwei", "y"))])
    _set_section(here, "rs", "009-probe-rs", "Sonde RS", ["RS-Text.", ("doc-field", "rs-field", _field("Bericht", "z"))])
    return here


def _project(name):
    """A project of its own for one check: a copy of the base one."""
    base = _BASE.get("here")
    if base is None or not base.file.exists():
        _BASE["here"] = base = _build_base()
    target = conftest.tmpdir(name) / "Halle"
    shutil.copytree(base.root, target)
    return project.Project.load(target / base.file.name)


# --- reading what happened --------------------------------------------------------------------------------

def _text(path):
    return typst_paths.read_text(path)


def _lines_of(text):
    return re.findall(r"[^\r\n]*(?:\r\n|\r|\n)|[^\r\n]+", text)


def _folders(here):
    return [here.document_dir(mode) for mode in here.modes]


def _snapshot(here):
    """{path from the project's folder: bytes} of every file of the three documents' folders -- the entry files, the structures, the sections and their archives: what a refusal must leave as it was."""
    root = here.root
    return {p.relative_to(root).as_posix(): p.read_bytes() for folder in _folders(here) for p in sorted(folder.rglob("*")) if p.is_file()}


def _leftovers(here):
    return [p for folder in _folders(here) for p in folder.rglob("*") if p.is_file() and p.suffix in (".tmp", ".part")]


def _code(code, what, *args, **kwargs):
    """`what(*args, **kwargs)` refuses with `code`: the error, its code and an English sentence."""
    try:
        what(*args, **kwargs)
    except structure.StructureError as exc:
        assert exc.code == code, f"refused with {exc.code!r}, not {code!r}: {exc}"
        assert str(exc), "a refusal says something"
        return exc
    raise AssertionError(f"{what.__name__}{args} was not refused with {code!r}")


def _order(text):
    """The ids of the objects of a file, in the order it writes them."""
    return [b.id for b in structure.pair_tags(text)[0] if b.kind == "object"]


def _blocks(text):
    """{object id: the lines of its two tags and what lies between them, as written}."""
    lines = _lines_of(text)
    return {b.id: "".join(lines[b.start:b.end + 1]) for b in structure.pair_tags(text)[0] if b.kind == "object"}


def _residue(text, object_id):
    """`text` without the object's lines and with every run of blank lines made one: what a move must leave of the file it takes the object out of, or it puts the object into."""
    blocks = structure.pair_tags(text)[0]
    block = next(b for b in blocks if b.kind == "object" and b.id == object_id)
    lines = _lines_of(text)
    kept = lines[:block.start] + lines[block.end + 1:]
    return re.sub(r"(\r?\n){2,}", "\n", "".join(kept).replace("\r\n", "\n"))


def _collapse(text):
    """`text` with every run of blank lines made one, as `_residue` leaves it."""
    return re.sub(r"(\r?\n){2,}", "\n", text.replace("\r\n", "\n"))


def _leaf(here, mode, section_id):
    found = structure.find(structure.read(here.structure_file(mode)), section_id)
    assert found is not None, f"{mode} has no section {section_id!r}"
    return found


def _top_ids(here, mode):
    return [node["id"] for node in structure.read(here.structure_file(mode))["sections"]]


def _includes(here):
    return [line.strip() for line in _text(here.document_typ("rs")).splitlines() if '#include "Sections/' in line]


def _crlf(path):
    path.write_bytes(path.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n"))


def _only_crlf(text):
    return "\n" not in text.replace("\r\n", "")


def _only_lf(text):
    return "\r" not in text


def _compiles(here, sections, name):
    """The sections -- [(document, file name without .typ)] -- compile, one after the other in a probe of their own: Typst is the judge -- and the words their PDF prints. A probe rather than the document, so that what the content templates of the convention and the base de projet hold at the moment does not matter."""
    from pypdf import PdfReader
    root = here.typst_root
    includes = "\n".join(f'#include "/{_file(here, mode, section).relative_to(root).as_posix()}"' for mode, section in sections)
    probe = root / f".probe-{name}.typ"
    probe.write_text(f'#import "/commands.typ": *\n{includes}\n', encoding="utf-8")
    out = conftest.tmpdir(f"doc_import_pdf_{name}") / "probe.pdf"
    try:
        done = subprocess.run(["typst", "compile", "--root", str(root), str(probe), str(out)], capture_output=True, text=True, encoding="utf-8")
    finally:
        probe.unlink(missing_ok=True)
    assert done.returncode == 0, f"{sections} do not compile: {done.stderr}"
    return " ".join(page.extract_text() or "" for page in PdfReader(str(out)).pages)


# --- the codes ---------------------------------------------------------------------------------------------------

def test_the_codes_are_unique_and_a_refusal_is_a_structure_error():
    assert len(doc_import.CODES) == len(set(doc_import.CODES)) and all(isinstance(c, str) and c for c in doc_import.CODES)
    exc = doc_import.DocImportError("plain", "no_items", id="x")
    assert isinstance(exc, structure.StructureError), "whatever catches the catalogue's refusals catches these"
    assert (exc.code, exc.values, str(exc)) == ("no_items", {"id": "x"}, "plain")


# --- the tree of what can be imported -------------------------------------------------------------------------

def test_importable_lists_the_sections_and_under_each_the_objects_of_its_file():
    here = _project("imp_list")
    items = doc_import.importable(here, "cu")
    flat = doc_import.flatten(items)
    group = next(i for i in items if i.id == "probes")
    assert (group.kind, group.parent, group.title) == ("group", None, "Sonden")
    assert [(i.kind, i.id) for i in group.children] == [("section", "probe-a"), ("section", "probe-b"), ("section", "probe-c")]
    a = group.children[0]
    assert (a.title, a.parent, a.file, a.mode) == ("Sonde A", "probes", "Sections/probe-a.typ", "cu")
    assert [(o.kind, o.id, o.object_type, o.section) for o in a.children] == [("object", "use-field", "doc-field", "probe-a"), ("object", "rooms-table", "doc-table", "probe-a")]
    assert [o.title for o in a.children] == ["Nutzung", "Räume"], "the label is the caption or the label of the call"
    assert all(o.shared_id is None and not o.alone for o in a.children)
    assert flat.index(a) < flat.index(a.children[0]) < flat.index(group.children[1]), "document order, an item before its children"
    # the report: sections only, and its objects where its files are tagged
    rs = doc_import.importable(here, "rs")
    assert all(i.kind == "section" for i in rs) and "009-probe-rs" in [i.id for i in rs]
    probe = next(i for i in rs if i.id == "009-probe-rs")
    assert [(o.id, o.object_type) for o in probe.children] == [("rs-field", "doc-field")]
    # what the objects are shared as
    sharing.share(here, "cu", "probe-c", ["bp"])
    c = next(i for i in doc_import.flatten(doc_import.importable(here, "cu")) if i.id == "probe-c")
    assert c.shared_ids == ("probe-c",) and c.shared_with == ("bp",)
    assert [(o.shared_id, o.alone) for o in c.children] == [("probe-c", False), ("probe-c", False)], "inside the shared block of the whole file"
    _code("bad_mode", doc_import.importable, here, "xx")
    _code("no_such_document", doc_import.importable, types.SimpleNamespace(modes=("rs",)), "cu")


def test_an_object_that_is_a_shared_block_alone_says_so():
    here = _project("imp_alone")
    doc_import.import_items(here, "bp", "cu", [("object", "probe-b", "only-field")])
    item = next(i for i in doc_import.flatten(doc_import.importable(here, "cu")) if i.id == "only-field")
    assert (item.shared_id, item.alone) == ("only-field", True)
    copy = next(i for i in doc_import.flatten(doc_import.importable(here, "bp")) if i.id == "only-field")
    assert (copy.shared_id, copy.alone) == ("only-field", True)


# --- whole sections ------------------------------------------------------------------------------------------------

def test_a_section_is_imported_linked_at_the_bottom_of_the_other_document():
    here = _project("sec_linked")
    before = _text(_file(here, "cu", "probe-a"))
    result = doc_import.import_items(here, "bp", "cu", [("section", "probe-a")])
    assert (result.op, result.mode, result.source, result.linked) == ("import", "bp", "cu", True)
    assert result.sections == (("probe-a", "probe-a"),) and result.shared_ids == ("probe-a",) and result.changed
    source, copy = _text(_file(here, "cu", "probe-a")), _text(_file(here, "bp", "probe-a"))
    assert source == copy, "the same file, tags and all"
    assert "// woodcore:shared probe-a" in source and source.replace("// woodcore:shared probe-a\n", "").replace("// woodcore:/shared probe-a\n", "") == before
    # the bottom of the tree: not in the group the sharing module would have put it in
    assert _top_ids(here, "bp")[-1] == "probe-a"
    assert "probe-a" not in [n["id"] for n in _leaf(here, "bp", "probes")[0]["children"]]
    assert _leaf(here, "bp", "probe-a")[0]["shared_with"] == ["cu"] and _leaf(here, "cu", "probe-a")[0]["shared_with"] == ["bp"]
    assert not sharing.reconcile(here, write=False).changes and not _leftovers(here)
    assert _file(here, "bp", "probe-a") in result.written and here.structure_file("bp") in result.written
    # a second section lands under the first
    doc_import.import_items(here, "bp", "cu", [("section", "probe-b")])
    assert _top_ids(here, "bp")[-2:] == ["probe-a", "probe-b"]
    if not conftest.have_typst():
        raise Skip("no typst on the path")
    for mode in ("cu", "bp"):
        assert "Büro" in _compiles(here, [(mode, "probe-a")], "sec_linked"), f"{mode} does not print the section"


def test_a_section_is_imported_as_an_independent_copy_with_a_fresh_id():
    here = _project("sec_copy")
    before = _snapshot(here)
    first = doc_import.import_items(here, "bp", "cu", [("section", "probe-a")], linked=False)
    second = doc_import.import_items(here, "bp", "cu", [("section", "probe-a")], linked=False)
    assert first.sections == (("probe-a", "probe-a"),) and second.sections == (("probe-a", "probe-a-2"),)
    assert first.shared_ids == () and not first.linked
    source = _text(_file(here, "cu", "probe-a"))
    assert source.encode("utf-8") == before["1_Nutzungsvereinbarung/Sections/probe-a.typ"], "the source is not touched"
    for name in ("probe-a", "probe-a-2"):
        assert _text(_file(here, "bp", name)) == source, "a copy of the file, no shared tag"
        leaf = _leaf(here, "bp", name)[0]
        assert "shared_with" not in leaf
    assert _top_ids(here, "bp")[-2:] == ["probe-a", "probe-a-2"], "at the bottom, in order"
    assert "woodcore:shared" not in _text(_file(here, "bp", "probe-a"))
    assert _leaf(here, "cu", "probe-a")[0].get("shared_with") is None
    assert not sharing.reconcile(here, write=False).changes and not _leftovers(here)
    if conftest.have_typst():
        assert "Büro" in _compiles(here, [("bp", "probe-a"), ("bp", "probe-a-2")], "sec_copy")


def test_an_independent_copy_takes_the_shared_tags_of_its_source_off():
    here = _project("sec_copy_tags")
    sharing.share(here, "cu", "probe-c", ["bp"])   # probe-c carries a shared block now, and so does its copy in the base de projet
    source = _text(_file(here, "cu", "probe-c"))
    assert "woodcore:shared probe-c" in source
    result = doc_import.import_items(here, "bp", "cu", [("section", "probe-c")], linked=False)
    assert result.sections == (("probe-c", "probe-c-2"),)
    copy = _text(_file(here, "bp", "probe-c-2"))
    assert "woodcore:shared" not in copy and copy.replace("\n", "") != source.replace("\n", "")
    assert copy == source.replace("// woodcore:shared probe-c\n", "").replace("// woodcore:/shared probe-c\n", "")
    assert structure.check_tags(copy) == [] and _order(copy) == ["c-one", "c-two"]
    assert _text(_file(here, "cu", "probe-c")) == source


def test_a_group_ticked_imports_every_section_under_it_in_order():
    here = _project("sec_group")
    group = next(i for i in doc_import.importable(here, "cu") if i.id == "probes")
    result = doc_import.import_items(here, "bp", "cu", [group])
    assert [pair for pair in result.sections] == [("probe-a", "probe-a"), ("probe-b", "probe-b"), ("probe-c", "probe-c")]
    assert _top_ids(here, "bp")[-3:] == ["probe-a", "probe-b", "probe-c"]


def test_a_heading_of_a_file_stands_for_its_section():
    here = _project("sec_heading")
    result = doc_import.import_items(here, "bp", "cu", [("section", "probe-a#2")], linked=False)
    assert result.sections == (("probe-a", "probe-a"),)


def test_sections_go_between_the_base_de_projet_the_report_and_back():
    here = _project("sec_all")
    entry_before = _text(here.document_typ("rs"))
    # the base de projet into the report, linked: an #include line after the last one, one id in the documents
    result = doc_import.import_items(here, "rs", "bp", [("section", "probe-bp")])
    assert result.sections == (("probe-bp", "probe-bp"),) and result.shared_ids == ("probe-bp",)
    assert _includes(here)[-1] == '#include "Sections/probe-bp.typ"'
    after = _text(here.document_typ("rs"))
    assert after.replace('#include "Sections/probe-bp.typ"\n', "", 1) == entry_before, "one line added and nothing else of the entry moved"
    assert _text(_file(here, "rs", "probe-bp")) == _text(_file(here, "bp", "probe-bp")) and "woodcore:shared probe-bp" in _text(_file(here, "rs", "probe-bp"))
    node = structure.find_node(structure.tree(here, "rs"), "probe-bp")
    assert node.shared_with == ("bp",)
    # independent: the report's next numbered file name
    copy = doc_import.import_items(here, "rs", "bp", [("section", "probe-bp2")], linked=False)
    [(source_id, stem)] = copy.sections
    assert source_id == "probe-bp2" and re.fullmatch(r"\d{3}-probe-bp2", stem), stem
    assert _includes(here)[-1] == f'#include "Sections/{stem}.typ"'
    assert "woodcore:shared" not in _text(_file(here, "rs", stem)) and _text(_file(here, "rs", stem)) == _text(_file(here, "bp", "probe-bp2"))
    # the report into the convention: the id made from the stem, at the bottom
    back = doc_import.import_items(here, "cu", "rs", [("section", "009-probe-rs")])
    assert back.sections == (("009-probe-rs", "probe-rs"),) and _top_ids(here, "cu")[-1] == "probe-rs"
    assert "woodcore:shared" in _text(_file(here, "rs", "009-probe-rs")), "the report's file is wrapped too"
    again = doc_import.import_items(here, "bp", "rs", [("section", "009-probe-rs")], linked=False)
    assert again.sections == (("009-probe-rs", "probe-rs"),) and _top_ids(here, "bp")[-1] == "probe-rs"
    assert not sharing.reconcile(here, write=False).changes and not _leftovers(here)
    if conftest.have_typst():
        assert "BP-Text" in _compiles(here, [("rs", "probe-bp"), ("rs", stem)], "sec_all_rs")
        assert "RS-Text" in _compiles(here, [("cu", "probe-rs"), ("bp", "probe-rs"), ("rs", "009-probe-rs")], "sec_all_cu")


# --- objects ticked alone ------------------------------------------------------------------------------------------

def test_objects_imported_alone_go_into_the_section_imported_created_at_the_bottom():
    here = _project("obj_linked")
    original = _text(_file(here, "cu", "probe-a"))
    result = doc_import.import_items(here, "bp", "cu", [("object", "probe-a", "use-field"), ("object", "probe-a", "rooms-table")])
    assert (result.imported, result.created, result.linked) == ("imported", True, True)
    assert result.objects == (("probe-a", "use-field", "use-field", "use-field"), ("probe-a", "rooms-table", "rooms-table", "rooms-table"))
    assert result.shared_ids == ("use-field", "rooms-table") and result.sections == ()
    assert _top_ids(here, "bp")[-1] == "imported", "at the bottom of the tree"
    copy = _text(_file(here, "bp", "imported"))
    lines = copy.splitlines()
    assert lines[0] == documents.import_line(here) and "= Importiert" in lines, "the heading is in the document's language"
    assert _order(copy) == ["use-field", "rooms-table"] and structure.check_tags(copy) == []
    source = _text(_file(here, "cu", "probe-a"))
    assert structure.check_tags(source) == [] and _order(source) == ["use-field", "rooms-table"]
    for object_id in ("use-field", "rooms-table"):
        # wrapped in both files, the same block between the tags
        assert f"// woodcore:shared {object_id}\n// woodcore:object" in source and f"// woodcore:shared {object_id}\n// woodcore:object" in copy
        found = sharing.copies(here, object_id)
        assert sorted(c.mode for c in found) == ["bp", "cu"] and len({c.block_text for c in found}) == 1, "the block is identical in the copies"
        assert found[0].block_text.startswith("// woodcore:object ")
    assert _blocks(source).keys() == _blocks(copy).keys()
    assert re.search(r"\n\n// woodcore:shared rooms-table\n", copy), "a blank line between two objects"
    assert not re.search(r"\n\n\n", copy)
    leaf = _leaf(here, "bp", "imported")[0]
    assert leaf["shared_with"] == ["cu"] and _leaf(here, "cu", "probe-a")[0]["shared_with"] == ["bp"]
    assert not sharing.reconcile(here, write=False).changes and not _leftovers(here)
    # the source says exactly what it said, with the two blocks wrapped
    assert re.sub(r"// woodcore:/?shared (use-field|rooms-table)\n", "", source) == original
    # a second import goes into the section that is there
    again = doc_import.import_items(here, "bp", "cu", [("object", "probe-b", "only-field")])
    assert (again.imported, again.created) == ("imported", False)
    text = _text(_file(here, "bp", "imported"))
    assert _order(text) == ["use-field", "rooms-table", "only-field"] and not re.search(r"\n\n\n", text)
    assert _top_ids(here, "bp").count("imported") == 1
    if conftest.have_typst():
        assert "Büro" in _compiles(here, [("cu", "probe-a")], "obj_linked_cu")
        words = _compiles(here, [("bp", "imported")], "obj_linked_bp")
        assert "Büro" in words and "Räume" in words and "50 Jahre" in words and "Importiert" in words


def test_the_imported_section_is_written_to_where_it_has_been_moved():
    here = _project("obj_moved")
    doc_import.import_items(here, "bp", "cu", [("object", "probe-a", "use-field")])
    doc_import.move_section(here, "bp", "imported", "probes", 0)
    assert _top_ids(here, "bp")[-1] != "imported"
    again = doc_import.import_items(here, "bp", "cu", [("object", "probe-b", "only-field")])
    assert (again.imported, again.created) == ("imported", False)
    assert _order(_text(_file(here, "bp", "imported"))) == ["use-field", "only-field"]


def test_objects_are_imported_in_document_order_whatever_the_order_they_were_ticked_in():
    here = _project("obj_order")
    doc_import.import_items(here, "bp", "cu", [("object", "probe-c", "c-two"), ("object", "probe-a", "rooms-table"), ("object", "probe-a", "use-field")], linked=False)
    assert _order(_text(_file(here, "bp", "imported"))) == ["use-field", "rooms-table", "c-two"]


def test_an_object_that_is_alone_in_a_shared_block_is_shared_under_that_block():
    here = _project("obj_reuse")
    doc_import.import_items(here, "bp", "cu", [("object", "probe-b", "only-field")])   # wrapped alone in the source now, shared with the base de projet
    before = _text(_file(here, "cu", "probe-b"))
    result = doc_import.import_items(here, "rs", "cu", [("object", "probe-b", "only-field")])
    assert result.objects == (("probe-b", "only-field", "only-field", "only-field"),) and result.shared_ids == ("only-field",)
    assert _text(_file(here, "cu", "probe-b")) == before, "already a shared block: the source is not touched again"
    assert sorted(c.mode for c in sharing.copies(here, "only-field")) == ["bp", "cu", "rs"]
    assert len({c.block_text for c in sharing.copies(here, "only-field")}) == 1
    # the report holds a copy of that block now: the base de projet does already
    _code("already_shared", doc_import.import_items, here, "bp", "cu", [("object", "probe-b", "only-field")])
    assert "only-field" in {i.id for i in doc_import.flatten(doc_import.importable(here, "rs"))}


def test_a_shared_id_is_free_in_the_whole_project():
    here = _project("obj_unique")
    # a shared block of another document already uses the id the object would be shared as
    path = _file(here, "bp", "probe-bp")
    text = _text(path).replace("= Sonde BP\n", "= Sonde BP\n\n// woodcore:shared use-field\nBlock.\n// woodcore:/shared use-field\n")
    typst_paths.write_text(path, text)
    result = doc_import.import_items(here, "rs", "cu", [("object", "probe-a", "use-field")])
    assert result.shared_ids == ("use-field-2",) and result.objects[0][2] == "use-field"
    assert "// woodcore:shared use-field-2\n// woodcore:object doc-field use-field\n" in _text(_file(here, "cu", "probe-a"))


def test_an_object_inside_a_larger_shared_block_is_refused_linked_and_copied_independent():
    here = _project("obj_larger")
    sharing.share(here, "cu", "probe-c", ["bp"])
    before = _snapshot(here)
    exc = _code("inside_shared", doc_import.import_items, here, "rs", "cu", [("object", "probe-c", "c-one")])
    assert exc.values["shared_id"] == "probe-c" and exc.values["id"] == "c-one"
    assert _snapshot(here) == before, "nothing written"
    result = doc_import.import_items(here, "rs", "cu", [("object", "probe-c", "c-one")], linked=False)
    assert result.objects == (("probe-c", "c-one", "c-one", None),) and result.shared_ids == ()
    imported = _text(_file(here, "rs", result.imported))
    assert "woodcore:object doc-field c-one" in imported and "woodcore:shared" not in imported
    assert _text(_file(here, "cu", "probe-c")).encode("utf-8") == before["1_Nutzungsvereinbarung/Sections/probe-c.typ"]


def test_independent_objects_carry_no_shared_tag_and_take_a_free_object_id():
    here = _project("obj_copy")
    before = _snapshot(here)
    first = doc_import.import_items(here, "bp", "cu", [("object", "probe-a", "use-field")], linked=False)
    second = doc_import.import_items(here, "bp", "cu", [("object", "probe-a", "use-field")], linked=False)
    assert first.objects == (("probe-a", "use-field", "use-field", None),) and second.objects == (("probe-a", "use-field", "use-field-2", None),)
    assert first.shared_ids == () and second.shared_ids == ()
    text = _text(_file(here, "bp", "imported"))
    assert "woodcore:shared" not in text and structure.check_tags(text) == [] and _order(text) == ["use-field", "use-field-2"]
    blocks = _blocks(text)
    assert blocks["use-field-2"] == blocks["use-field"].replace("use-field", "use-field-2"), "only the id differs"
    assert blocks["use-field"] == _blocks(_text(_file(here, "cu", "probe-a")))["use-field"], "the object as it was written"
    assert _text(_file(here, "cu", "probe-a")).encode("utf-8") == before["1_Nutzungsvereinbarung/Sections/probe-a.typ"], "the source is not touched"
    assert _leaf(here, "bp", "imported")[0].get("shared_with") is None
    assert not sharing.reconcile(here, write=False).changes and not _leftovers(here)


def test_a_section_ticked_with_its_own_objects_wins():
    here = _project("obj_section_wins")
    result = doc_import.import_items(here, "bp", "cu", [("object", "probe-a", "use-field"), ("section", "probe-a"), ("object", "probe-b", "only-field")])
    assert result.sections == (("probe-a", "probe-a"),)
    assert result.skipped == (("object", "use-field", "probe-a", "section_selected"),)
    assert result.objects == (("probe-b", "only-field", "only-field", "only-field"),) and result.imported == "imported"
    assert _order(_text(_file(here, "bp", "imported"))) == ["only-field"], "the object of the whole section is not imported a second time"
    # all of them in whole sections: nothing is created for the objects
    here = _project("obj_section_wins2")
    result = doc_import.import_items(here, "bp", "cu", [("section", "probe-a"), ("object", "probe-a", "rooms-table")])
    assert result.objects == () and result.imported is None and "imported" not in _top_ids(here, "bp")
    assert result.skipped == (("object", "rooms-table", "probe-a", "section_selected"),)


def test_the_title_of_the_imported_section_follows_the_document_language():
    assert doc_import.IMPORTED_TITLES == {"fr": "Importé", "de": "Importiert", "en": "Imported"} and doc_import.IMPORTED_ID == "imported"
    here = _project("obj_report")
    result = doc_import.import_items(here, "rs", "cu", [("object", "probe-a", "use-field")])
    assert result.created and re.fullmatch(r"\d{3}-imported", result.imported), result.imported
    assert _includes(here)[-1] == f'#include "Sections/{result.imported}.typ"'
    assert "= Importiert" in _text(_file(here, "rs", result.imported))
    again = doc_import.import_items(here, "rs", "cu", [("object", "probe-b", "only-field")])
    assert (again.imported, again.created) == (result.imported, False)
    assert _order(_text(_file(here, "rs", result.imported))) == ["use-field", "only-field"]
    if conftest.have_typst():
        assert "Büro" in _compiles(here, [("rs", result.imported)], "obj_report")


def test_the_report_is_a_source_too_and_an_object_comes_back_into_the_convention():
    here = _project("obj_from_report")
    result = doc_import.import_items(here, "cu", "rs", [("object", "009-probe-rs", "rs-field")])
    assert result.objects == (("009-probe-rs", "rs-field", "rs-field", "rs-field"),) and _top_ids(here, "cu")[-1] == "imported"
    assert "woodcore:shared rs-field" in _text(_file(here, "rs", "009-probe-rs"))
    assert sorted(c.mode for c in sharing.copies(here, "rs-field")) == ["cu", "rs"]


# --- refusals ------------------------------------------------------------------------------------------------------

def test_every_refusal_has_its_code_and_writes_nothing():
    here = _project("refusals")
    before = _snapshot(here)
    imp = doc_import.import_items
    _code("bad_mode", imp, here, "xx", "cu", [("section", "probe-a")])
    _code("bad_mode", imp, here, "bp", "xx", [("section", "probe-a")])
    _code("no_such_document", imp, types.SimpleNamespace(modes=("rs",)), "rs", "cu", [("section", "probe-a")])
    _code("same_document", imp, here, "cu", "cu", [("section", "probe-a")])
    _code("no_items", imp, here, "bp", "cu", [])
    _code("bad_item", imp, here, "bp", "cu", ["probe-a"])
    _code("bad_item", imp, here, "bp", "cu", [("object", "probe-a")])
    _code("no_such_node", imp, here, "bp", "cu", [("section", "nothing")])
    _code("no_such_node", imp, here, "bp", "cu", [("object", "nothing", "x")])
    _code("not_a_section", imp, here, "bp", "cu", [("object", "probes", "x")])
    _code("no_such_object", imp, here, "bp", "cu", [("object", "probe-a", "nothing")])
    _code("no_such_object", imp, here, "bp", "cu", [("object", "probe-a", "use-field"), ("object", "probe-a", "nothing")], linked=False)
    assert _snapshot(here) == before and not _leftovers(here)


def test_a_file_whose_tags_cannot_be_read_is_not_imported_and_nothing_is_written():
    here = _project("refuse_tags")
    path = _file(here, "cu", "probe-b")
    path.write_bytes(path.read_bytes() + b"\n// woodcore:object doc-field broken\n")
    before = _snapshot(here)
    for linked in (True, False):
        exc = _code("tags_unreadable", doc_import.import_items, here, "bp", "cu", [("object", "probe-b", "only-field")], linked=linked)
        assert exc.values["problems"]
    _code("tags_unreadable", doc_import.import_items, here, "bp", "cu", [("section", "probe-b")], linked=False)
    assert _snapshot(here) == before and not _leftovers(here)


def test_a_group_called_imported_leaves_the_objects_no_file_to_go_into():
    here = _project("refuse_group")
    structure.add_group(here, "bp", None, None, "imported", TITLES)
    before = _snapshot(here)
    exc = _code("imported_not_a_section", doc_import.import_items, here, "bp", "cu", [("object", "probe-a", "use-field")])
    assert exc.values["id"] == "imported" and _snapshot(here) == before


def test_a_linked_object_is_given_a_fresh_id_in_the_source_and_the_copy_where_the_destination_has_its_id():
    here = _project("fresh_id")
    doc_import.import_items(here, "bp", "cu", [("object", "probe-a", "use-field")], linked=False)   # an independent copy holds the id in «Importé»
    result = doc_import.import_items(here, "bp", "cu", [("object", "probe-a", "use-field")])
    assert result.objects == (("probe-a", "use-field", "use-field-2", "use-field-2"),), "the id in the copy, and the shared id made from it"
    source, copy = _text(_file(here, "cu", "probe-a")), _text(_file(here, "bp", "imported"))
    assert _order(source) == ["use-field-2", "rooms-table"] and _order(copy) == ["use-field", "use-field-2"], "renamed in the source too: one id in every copy of the block"
    assert structure.check_tags(source) == [] and structure.check_tags(copy) == []
    assert "// woodcore:shared use-field-2\n// woodcore:object doc-field use-field-2\n" in source
    found = sharing.copies(here, "use-field-2")
    assert sorted(c.mode for c in found) == ["bp", "cu"] and len({c.block_text for c in found}) == 1
    assert not sharing.reconcile(here, write=False).changes and not _leftovers(here)
    assert sync.status(here, "bp").state_of("use-field-2") == "in_sync"


def test_an_object_that_is_a_shared_block_alone_keeps_its_id_so_a_destination_that_has_it_refuses():
    here = _project("refuse_id")
    doc_import.import_items(here, "rs", "cu", [("object", "probe-b", "only-field")])   # alone in a shared block, shared with the report
    doc_import.import_items(here, "bp", "cu", [("object", "probe-b", "only-field")], linked=False)   # an independent copy holds the id in the base de projet
    before = _snapshot(here)
    exc = _code("id_exists", doc_import.import_items, here, "bp", "cu", [("object", "probe-b", "only-field")])
    assert exc.values["id"] == "only-field"
    assert _snapshot(here) == before, "nothing was renamed or written"


def test_headings_and_paragraphs_are_objects_and_two_sections_may_have_the_same_ids():
    here = _project("markup_objects")
    for section_id, title, word in (("probe-a", "Sonde A", "A"), ("probe-b", "Sonde B", "B")):
        _set_section(here, "cu", section_id, title, [
            ("heading", "title", f"= Titel {word}"),
            ("text", "p1", f"Absatz {word}, der erste."),
            ("text", "p2", f"Absatz {word}, der zweite."),
        ])
    items = {i.id: i for i in doc_import.flatten(doc_import.importable(here, "cu")) if i.kind == "section"}
    objects = items["probe-a"].children
    assert [(o.id, o.object_type) for o in objects] == [("title", "heading"), ("p1", "text"), ("p2", "text")]
    assert objects[0].title == "Titel A" and objects[1].title.startswith("Absatz A"), "the words of the tree"
    result = doc_import.import_items(here, "bp", "cu", [("object", "probe-a", "title"), ("object", "probe-a", "p1"), ("object", "probe-b", "title"), ("object", "probe-b", "p1")])
    assert [(o[1], o[2]) for o in result.objects] == [("title", "title"), ("p1", "p1"), ("title", "title-2"), ("p1", "p1-2")]
    copy = _text(_file(here, "bp", "imported"))
    assert _order(copy) == ["title", "p1", "title-2", "p1-2"] and structure.check_tags(copy) == []
    assert _order(_text(_file(here, "cu", "probe-b"))) == ["title-2", "p1-2", "p2"], "renamed in the source where the copy needed it"
    assert "= Titel B" in copy and "Absatz B, der erste." in copy
    assert not sharing.reconcile(here, write=False).changes and not _leftovers(here)
    # as independent copies the ids are free in the file, and the sources are not touched
    here = _project("markup_objects_copy")
    _set_section(here, "cu", "probe-a", "Sonde A", [("heading", "title", "= Titel A"), ("text", "p1", "Absatz A.")])
    _set_section(here, "cu", "probe-b", "Sonde B", [("heading", "title", "= Titel B"), ("text", "p1", "Absatz B.")])
    sources = (_text(_file(here, "cu", "probe-a")), _text(_file(here, "cu", "probe-b")))
    doc_import.import_items(here, "bp", "cu", [("object", "probe-a", "title"), ("object", "probe-b", "title"), ("object", "probe-b", "p1")], linked=False)
    assert _order(_text(_file(here, "bp", "imported"))) == ["title", "title-2", "p1"]
    assert (_text(_file(here, "cu", "probe-a")), _text(_file(here, "cu", "probe-b"))) == sources
    if conftest.have_typst():
        words = _compiles(here, [("bp", "imported")], "markup_objects")
        assert "Titel A" in words and "Titel B" in words and "Absatz B." in words


def test_a_section_the_target_already_has_is_refused_linked_with_the_sharing_codes():
    here = _project("refuse_section")
    doc_import.import_items(here, "bp", "cu", [("section", "probe-a")], linked=False)
    before = _snapshot(here)
    _code("id_exists", doc_import.import_items, here, "bp", "cu", [("section", "probe-a")])
    assert _snapshot(here) == before and not _leftovers(here)
    doc_import.import_items(here, "bp", "cu", [("section", "probe-b")])
    before = _snapshot(here)
    _code("already_shared", doc_import.import_items, here, "bp", "cu", [("section", "probe-b")])
    assert _snapshot(here) == before


# --- all or nothing ----------------------------------------------------------------------------------------------

def test_a_section_that_fails_halfway_takes_back_what_the_ones_before_it_wrote():
    here = _project("atomic_sections")
    before = _snapshot(here)
    real, calls = sharing.share, []

    def flaky(*args, **kwargs):
        calls.append(args[3])
        if len(calls) == 2:
            raise OSError("disk full")
        return real(*args, **kwargs)

    sharing.share = flaky
    try:
        exc = _code("write_failed", doc_import.import_items, here, "bp", "cu", [("section", "probe-a"), ("section", "probe-b")])
    finally:
        sharing.share = real
    assert len(calls) == 2 and "disk full" in exc.values["error"]
    assert _snapshot(here) == before, "the first section's copy, tags and structure are gone again"
    assert not _leftovers(here)
    # and the same import goes through afterwards
    assert doc_import.import_items(here, "bp", "cu", [("section", "probe-a"), ("section", "probe-b")]).sections == (("probe-a", "probe-a"), ("probe-b", "probe-b"))


def test_a_write_that_fails_while_objects_are_put_in_takes_everything_back_including_the_new_section():
    here = _project("atomic_objects")
    before = _snapshot(here)
    real, calls = doc_import._put, []

    def flaky(path, data):
        calls.append(path)
        if Path(path).name == "probe-b.typ":
            raise OSError("disk full")
        return real(path, data)

    doc_import._put = flaky
    try:
        _code("write_failed", doc_import.import_items, here, "bp", "cu", [("object", "probe-a", "use-field"), ("object", "probe-b", "only-field")])
    finally:
        doc_import._put = real
    assert any(Path(p).name == "imported.typ" for p in calls), "the section «Importé» had been written by then"
    assert _snapshot(here) == before, "the section made for them, the wrapped source, everything is as it was"
    assert not (_file(here, "bp", "imported")).exists() and not _leftovers(here)


def test_a_write_tried_again_when_the_sync_client_holds_a_file():
    here = _project("retry")
    real = doc_import.os.replace
    state = {"left": 2}

    def held(source, target):
        if state["left"] and Path(target).name == "probe-a.typ":
            state["left"] -= 1
            raise PermissionError("held by the sync client")
        return real(source, target)

    doc_import.os.replace = held
    try:
        result = doc_import.import_items(here, "bp", "cu", [("object", "probe-a", "use-field")])
    finally:
        doc_import.os.replace = real
    assert state["left"] == 0 and result.objects and "woodcore:shared use-field" in _text(_file(here, "cu", "probe-a"))


# --- line endings ----------------------------------------------------------------------------------------------------

def test_the_line_endings_of_every_file_are_kept():
    here = _project("crlf")
    cu_a, cu_b, bp_bp = _file(here, "cu", "probe-a"), _file(here, "cu", "probe-b"), _file(here, "bp", "probe-bp")
    _crlf(cu_a)
    assert b"\r\n" in cu_a.read_bytes() and b"\r\n" not in cu_b.read_bytes()
    # objects of a CRLF source into a section made now (LF), and an object of an LF source into a CRLF one
    doc_import.import_items(here, "bp", "cu", [("object", "probe-a", "use-field")])
    assert _only_crlf(_text(cu_a)) and "// woodcore:shared use-field\r\n" in _text(cu_a), "the tags written in the source are CRLF"
    imported = _file(here, "bp", "imported")
    assert _only_lf(_text(imported))
    _crlf(imported)
    doc_import.import_items(here, "bp", "cu", [("object", "probe-b", "only-field")])
    assert _only_crlf(_text(imported)) and _only_lf(_text(cu_b)), "each file keeps its own"
    assert _order(_text(imported)) == ["use-field", "only-field"]
    # a CRLF section, linked and as a copy
    _crlf(bp_bp)
    doc_import.import_items(here, "cu", "bp", [("section", "probe-bp")])
    assert _only_crlf(_text(bp_bp)) and _only_crlf(_text(_file(here, "cu", "probe-bp")))
    doc_import.import_items(here, "rs", "bp", [("section", "probe-bp2")], linked=False)
    _crlf(_file(here, "bp", "probe-bp2"))
    doc_import.import_items(here, "cu", "bp", [("section", "probe-bp2")], linked=False)
    assert _only_crlf(_text(_file(here, "cu", "probe-bp2")))
    assert not sharing.reconcile(here, write=False).changes and not _leftovers(here)


def test_an_independent_copy_of_an_object_that_is_a_shared_block_alone_leaves_the_tags_behind():
    here = _project("obj_copy_alone")
    doc_import.import_items(here, "bp", "cu", [("object", "probe-b", "only-field")])   # alone in a shared block, shared with the base de projet
    source = _text(_file(here, "cu", "probe-b"))
    result = doc_import.import_items(here, "rs", "cu", [("object", "probe-b", "only-field")], linked=False)
    assert result.objects == (("probe-b", "only-field", "only-field", None),)
    copy = _text(_file(here, "rs", result.imported))
    assert "woodcore:shared" not in copy and _order(copy) == ["only-field"]
    assert _text(_file(here, "cu", "probe-b")) == source and sorted(c.mode for c in sharing.copies(here, "only-field")) == ["bp", "cu"]


def test_a_section_that_cannot_be_put_at_the_bottom_is_not_left_half_imported():
    here = _project("atomic_bottom")
    before = _snapshot(here)
    real = structure.move_node

    def refuse(*args, **kwargs):
        raise structure.StructureError("the tree cannot be written", "write_failed", error="refused")

    structure.move_node = refuse
    try:
        _code("write_failed", doc_import.import_items, here, "bp", "cu", [("section", "probe-a")])
    finally:
        structure.move_node = real
    assert _snapshot(here) == before and not _leftovers(here), "the sharing had written the copy; it is taken back"


def test_other_documents_lists_the_documents_one_can_import_from():
    here = _project("others")
    assert doc_import.other_documents(here, "bp") == ("cu", "rs") and doc_import.other_documents(here, "rs") == ("cu", "bp")
    _code("bad_mode", doc_import.other_documents, here, "xx")


# --- the synchronisation records ----------------------------------------------------------------------------------

def test_the_copies_an_import_makes_start_in_step():
    here = _project("sync_import")
    doc_import.import_items(here, "bp", "cu", [("section", "probe-a"), ("object", "probe-b", "only-field")])
    for mode in ("cu", "bp"):
        status = sync.status(here, mode)
        assert status.state_of("probe-a") == "in_sync" and status.state_of("only-field") == "in_sync", f"{mode}: {status.counts()}"
        assert not status.conflicts and not status.incoming
    # a third document holding the block of an object already shared: the new copy stands with it as its source does
    result = doc_import.import_items(here, "rs", "cu", [("object", "probe-b", "only-field")])
    assert result.unrecorded == ()
    for mode in ("cu", "bp", "rs"):
        assert sync.status(here, mode).state_of("only-field") == "in_sync", mode


def test_an_object_reordered_inside_a_shared_block_is_a_local_edit_here_and_incoming_elsewhere():
    here = _project("sync_move")
    sharing.share(here, "cu", "probe-c", ["bp"])
    assert sync.status(here, "cu").state_of("probe-c") == "in_sync"
    result = doc_import.move_object(here, "cu", "probe-c", "c-two", "probe-c", before="c-one")
    assert result.shared_changed == ("probe-c",) and result.unrecorded == ()
    assert sync.status(here, "cu").state_of("probe-c") == "local"
    assert sync.status(here, "bp").state_of("probe-c") == "incoming"
    # an object put into the block from outside is an edit of it as well
    sharing.share(here, "cu", "probe-a", ["bp"])
    doc_import.import_items(here, "cu", "bp", [("object", "probe-bp", "bp-field")], linked=False)
    assert sync.status(here, "bp").state_of("probe-a") == "in_sync"
    doc_import.move_object(here, "cu", "imported", "bp-field", "probe-a", before="use-field")
    assert sync.status(here, "cu").state_of("probe-a") == "local" and sync.status(here, "bp").state_of("probe-a") == "incoming"


# --- moving objects ---------------------------------------------------------------------------------------------------

def test_an_object_is_moved_above_and_below_another_inside_its_file():
    here = _project("move_within")
    path = _file(here, "cu", "probe-a")
    before = _text(path)
    result = doc_import.move_object(here, "cu", "probe-a", "rooms-table", "probe-a", before="use-field")
    after = _text(path)
    assert (result.op, result.moved, result.shared_changed, result.shared_ids) == ("move_object", (("rooms-table", "probe-a", "probe-a"),), (), ())
    assert path in result.written and result.changed
    assert _order(after) == ["rooms-table", "use-field"] and _blocks(after) == _blocks(before), "the objects as they were written"
    assert _residue(after, "rooms-table") == _residue(before, "rooms-table"), "everything else is as it was"
    assert not re.search(r"\n\n\n", after) and structure.check_tags(after) == []
    doc_import.move_object(here, "cu", "probe-a", "use-field", "probe-a", after="rooms-table")
    assert _order(_text(path)) == ["rooms-table", "use-field"], "below the last one: where it is"
    doc_import.move_object(here, "cu", "probe-a", "rooms-table", "probe-a", after="use-field")
    assert _order(_text(path)) == ["use-field", "rooms-table"]
    assert _residue(_text(path), "rooms-table") == _residue(before, "rooms-table"), "directly below the other: the words between them stay where they were"
    doc_import.move_object(here, "cu", "probe-a", "use-field", "probe-a")
    end = _text(path)
    assert _order(end) == ["rooms-table", "use-field"] and end.rstrip("\n").endswith("// woodcore:/object use-field"), "no place given: the end of the file"
    assert _blocks(end) == _blocks(before) and structure.check_tags(end) == [] and not re.search(r"\n\n\n", end) and not _leftovers(here)


def test_an_object_put_where_it_stands_or_onto_itself_writes_nothing():
    here = _project("move_nothing")
    before = _snapshot(here)
    result = doc_import.move_object(here, "cu", "probe-a", "use-field", "probe-a", before="use-field")
    assert not result.changed and result.moved == () and result.written == ()
    result = doc_import.move_object(here, "cu", "probe-a", "use-field", "probe-a", after="use-field")
    assert not result.changed
    # probe-c: c-one is directly above c-two, with nothing between them but a blank line
    result = doc_import.move_object(here, "cu", "probe-c", "c-one", "probe-c", before="c-two")
    assert not result.changed, "directly above the one it is above already"
    result = doc_import.move_object(here, "cu", "probe-c", "c-two", "probe-c", after="c-one")
    assert not result.changed, "directly below the one it is below already"
    assert _snapshot(here) == before


def test_an_object_is_moved_into_another_file_of_the_document():
    here = _project("move_across")
    a, b = _file(here, "cu", "probe-a"), _file(here, "cu", "probe-b")
    a_before, b_before = _text(a), _text(b)
    result = doc_import.move_object(here, "cu", "probe-a", "use-field", "probe-b", after="only-field")
    assert result.moved == (("use-field", "probe-a", "probe-b"),) and {a, b} <= set(result.written)
    assert _order(_text(b)) == ["only-field", "use-field"] and _order(_text(a)) == ["rooms-table"]
    assert _blocks(_text(b))["use-field"] == _blocks(a_before)["use-field"], "the object as it was written"
    assert _collapse(_text(a)) == _residue(a_before, "use-field"), "what it left behind is the file less the object"
    assert _residue(_text(b), "use-field") == _collapse(b_before), "and the other file is the file plus the object"
    doc_import.move_object(here, "cu", "probe-a", "rooms-table", "probe-b", before="only-field")
    assert _order(_text(b)) == ["rooms-table", "only-field", "use-field"] and _order(_text(a)) == []
    doc_import.move_object(here, "cu", "probe-b", "only-field", "probe-a")
    assert _order(_text(a)) == ["only-field"] and _order(_text(b)) == ["rooms-table", "use-field"], "no place given: the end of the other file"
    assert _text(a).endswith("// woodcore:/object only-field\n") and not re.search(r"\n\n\n", _text(a) + _text(b)) and not _leftovers(here)
    if conftest.have_typst():
        words = _compiles(here, [("cu", "probe-a"), ("cu", "probe-b")], "move_across")
        assert "Büro" in words and "50 Jahre" in words and "Räume" in words


def test_a_shared_block_alone_moves_with_its_tags_and_the_structures_follow():
    here = _project("move_shared")
    doc_import.import_items(here, "bp", "cu", [("object", "probe-b", "only-field")])   # alone in a shared block in probe-b, shared with the base de projet
    b, a = _file(here, "cu", "probe-b"), _file(here, "cu", "probe-a")
    assert _leaf(here, "cu", "probe-b")[0]["shared_with"] == ["bp"] and "shared_with" not in _leaf(here, "cu", "probe-a")[0]
    block = _blocks(_text(b))
    result = doc_import.move_object(here, "cu", "probe-b", "only-field", "probe-a", after="use-field")
    assert result.shared_ids == ("only-field",) and result.moved == (("only-field", "probe-b", "probe-a"),)
    moved = _text(a)
    assert "// woodcore:shared only-field\n// woodcore:object doc-field only-field\n" in moved and "// woodcore:/shared only-field\n" in moved, "the shared tags moved with it"
    assert "woodcore:shared" not in _text(b) and structure.check_tags(moved) == []
    assert _order(moved) == ["use-field", "only-field", "rooms-table"], "above and below an object: outside a shared block of its own"
    assert _blocks(moved)["only-field"] == block["only-field"]
    # the leaves say where the block is now
    assert _leaf(here, "cu", "probe-a")[0]["shared_with"] == ["bp"] and "shared_with" not in _leaf(here, "cu", "probe-b")[0]
    assert not sharing.reconcile(here, write=False).changes
    assert sorted(c.mode for c in sharing.copies(here, "only-field")) == ["bp", "cu"]
    # a shared block cannot be put between the tags of another
    sharing.share(here, "cu", "probe-c", ["bp"])
    before = _snapshot(here)
    exc = _code("nested_shared", doc_import.move_object, here, "cu", "probe-a", "only-field", "probe-c", before="c-two")
    assert exc.values["shared_id"] == "probe-c" and _snapshot(here) == before


def test_an_object_of_a_larger_shared_block_stays_in_it_but_may_be_reordered():
    here = _project("move_larger")
    sharing.share(here, "cu", "probe-c", ["bp"])
    path = _file(here, "cu", "probe-c")
    before = _snapshot(here)
    # out of the block: to the end of the file, which lies after the closing tag, or into another file
    exc = _code("leaves_shared_block", doc_import.move_object, here, "cu", "probe-c", "c-one", "probe-c")
    assert exc.values["shared_id"] == "probe-c" and exc.values["id"] == "c-one"
    _code("leaves_shared_block", doc_import.move_object, here, "cu", "probe-c", "c-one", "probe-a", after="use-field")
    _code("leaves_shared_block", doc_import.move_object, here, "cu", "probe-c", "c-two", "probe-b")
    assert _snapshot(here) == before
    # inside it: the block is edited
    result = doc_import.move_object(here, "cu", "probe-c", "c-two", "probe-c", before="c-one")
    assert result.shared_changed == ("probe-c",) and result.changed and result.shared_ids == ()
    text = _text(path)
    assert _order(text) == ["c-two", "c-one"] and structure.check_tags(text) == []
    assert text.index("// woodcore:shared probe-c") < text.index("// woodcore:object doc-field c-two") < text.index("// woodcore:/shared probe-c")
    # the other copy now differs: what the synchronisation will say
    differing = [c for c in sharing.copies(here, "probe-c")]
    assert len({c.block_text for c in differing}) == 2
    # an object put into the block from outside enters it
    doc_import.move_object(here, "cu", "probe-a", "use-field", "probe-c", before="c-one")
    assert _order(_text(path)) == ["c-two", "use-field", "c-one"]
    result = doc_import.move_object(here, "cu", "probe-a", "rooms-table", "probe-c", after="c-one")
    assert result.shared_changed == ("probe-c",)
    assert not _leftovers(here)


def test_an_object_lies_tight_against_the_tag_of_a_shared_block_and_the_words_around_it_stay():
    here = _project("move_tight")
    path = _file(here, "cu", "probe-a")
    one = typst_objects.insert_object("", -1, "doc-field", "one", _field("Eins", "a")).rstrip("\n")
    two = typst_objects.insert_object("", -1, "doc-field", "two", _field("Zwei", "b")).rstrip("\n")
    head = documents.import_line(here) + "\n\n"
    typst_paths.write_text(path, f"{head}// woodcore:shared tight\n{one}\n\n{two}\n// woodcore:/shared tight\n\nNach dem Block.\n")
    doc_import.move_object(here, "cu", "probe-a", "two", "probe-a", before="one")
    assert _text(path) == f"{head}// woodcore:shared tight\n{two}\n\n{one}\n// woodcore:/shared tight\n\nNach dem Block.\n", "no blank line against either tag"
    doc_import.move_object(here, "cu", "probe-a", "two", "probe-a", after="one")
    assert _text(path) == f"{head}// woodcore:shared tight\n{one}\n\n{two}\n// woodcore:/shared tight\n\nNach dem Block.\n"
    # the end of the file is after the closing tag: out of the block, so refused; named by its last object it is inside
    _code("leaves_shared_block", doc_import.move_object, here, "cu", "probe-a", "one", "probe-a")
    doc_import.move_object(here, "cu", "probe-a", "one", "probe-a", after="two")
    assert _text(path) == f"{head}// woodcore:shared tight\n{two}\n\n{one}\n// woodcore:/shared tight\n\nNach dem Block.\n"


def test_a_move_that_cannot_be_made_is_refused_with_its_code_and_writes_nothing():
    here = _project("move_refuse")
    before = _snapshot(here)
    mv = doc_import.move_object
    _code("bad_mode", mv, here, "xx", "probe-a", "use-field", "probe-b")
    _code("bad_place", mv, here, "cu", "probe-a", "use-field", "probe-b", before="only-field", after="only-field")
    _code("no_such_node", mv, here, "cu", "nothing", "use-field", "probe-b")
    _code("no_such_node", mv, here, "cu", "probe-a", "use-field", "nothing")
    _code("not_a_section", mv, here, "cu", "probes", "use-field", "probe-b")
    _code("not_a_section", mv, here, "cu", "probe-a", "use-field", "probes")
    _code("no_such_object", mv, here, "cu", "probe-a", "nothing", "probe-b")
    _code("no_such_object", mv, here, "cu", "probe-a", "use-field", "probe-b", before="nothing")
    assert _snapshot(here) == before
    # an id the other file has
    other = _file(here, "cu", "probe-b")
    other.write_bytes(other.read_bytes() + b"\n// woodcore:object doc-field use-field\n#doc-field()\n// woodcore:/object use-field\n")
    before = _snapshot(here)
    _code("id_exists", mv, here, "cu", "probe-a", "use-field", "probe-b")
    # a shared block the other file carries already
    doc_import.import_items(here, "bp", "cu", [("object", "probe-a", "rooms-table")])
    other.write_bytes(other.read_bytes() + b"\n// woodcore:shared rooms-table\n// woodcore:/shared rooms-table\n")
    before = _snapshot(here)
    _code("already_shared", mv, here, "cu", "probe-a", "rooms-table", "probe-b")
    assert _snapshot(here) == before
    # tags that cannot be read, in the source and in the destination
    other.write_bytes(other.read_bytes() + b"\n// woodcore:object doc-field broken\n")
    before = _snapshot(here)
    _code("tags_unreadable", mv, here, "cu", "probe-b", "only-field", "probe-a")
    _code("tags_unreadable", mv, here, "cu", "probe-a", "use-field", "probe-b")
    assert _snapshot(here) == before and not _leftovers(here)


def test_a_move_is_all_or_nothing():
    here = _project("move_atomic")
    before = _snapshot(here)
    real, calls = doc_import._put, []

    def flaky(path, data):
        calls.append(path)
        if len(calls) == 2:
            raise OSError("disk full")
        return real(path, data)

    doc_import._put = flaky
    try:
        _code("write_failed", doc_import.move_object, here, "cu", "probe-a", "use-field", "probe-b")
    finally:
        doc_import._put = real
    assert len(calls) >= 2
    assert _snapshot(here) == before, "the first file was put back"
    assert not _leftovers(here)


def test_a_moved_object_is_written_in_the_line_ending_of_its_new_file():
    here = _project("move_crlf")
    a, b = _file(here, "cu", "probe-a"), _file(here, "cu", "probe-b")
    _crlf(b)
    a_before = _text(a)
    doc_import.move_object(here, "cu", "probe-a", "use-field", "probe-b", after="only-field")
    assert _only_crlf(_text(b)) and _only_lf(_text(a)) and _order(_text(b)) == ["only-field", "use-field"]
    _crlf(a)
    doc_import.move_object(here, "cu", "probe-b", "only-field", "probe-a", after="rooms-table")
    assert _only_crlf(_text(a)) and _only_crlf(_text(b)) and _order(_text(a)) == ["rooms-table", "only-field"]
    assert a_before != _text(a)


def test_a_section_is_moved_by_the_structure_module():
    here = _project("move_section")
    edit = doc_import.move_section(here, "cu", "probe-b", None, 0)
    assert isinstance(edit, structure.Edit) and edit.op == "move_node" and edit.changed
    assert _top_ids(here, "cu")[0] == "probe-b"
    edit = doc_import.move_section(here, "cu", "probe-c", "probes", 0)
    assert [n["id"] for n in _leaf(here, "cu", "probes")[0]["children"]][0] == "probe-c"
    edit = doc_import.move_section(here, "rs", "009-probe-rs", None, 0)
    assert edit.mode == "rs" and _includes(here)[0] == '#include "Sections/009-probe-rs.typ"'
    _code("no_such_node", doc_import.move_section, here, "cu", "nothing", None, 0)
