# -*- coding: utf-8 -*-
"""The objects taken out of a document, kept where they stood and put back (calc/removed_objects.py, the engineer's request of 06.10.2026): the register written and read; an object put back right after the closing tag of the object that stood before it, whatever was written between the two meanwhile; before the next one where that one is gone; at the end where both are; under a free id where its own was taken; with its body as written; CRLF kept; and refused where its file or its copy is gone."""

import sys

import conftest

sys.path.insert(0, str(conftest.CALC))

import removed_objects  # noqa: E402
import typst_objects  # noqa: E402
import typst_paths  # noqa: E402

TEXT = """#import "/commands.typ": *

// woodcore:object heading title
= Erdbeben
// woodcore:/object title

// woodcore:object text p1
Erster Absatz.
// woodcore:/object p1

// woodcore:object text p2
Zweiter Absatz, *von Hand*  geschrieben.
// woodcore:/object p2

// woodcore:object text p3
Dritter Absatz.
// woodcore:/object p3
"""


def _document(name, text=TEXT):
    doc = conftest.tmpdir(name)
    (doc / "Sections").mkdir()
    path = doc / "Sections" / "earthquake.typ"
    typst_paths.write_text(path, text)
    return doc, path


def _remove(doc, path, object_id):
    """What the tab does: the block copied, its neighbours noted, the object cut out, the register written."""
    text = typst_paths.read_text(path)
    found = typst_objects.find(text, object_id)
    lines = typst_objects._lines(text)
    block = "".join(lines[found.start:found.end + 1])
    after, before = removed_objects.neighbours(text, object_id)
    archive = removed_objects.archives_dir(doc) / f"260106-120000-earthquake-{object_id}.typ"
    archive.parent.mkdir(parents=True, exist_ok=True)
    typst_paths.write_text(archive, block)
    typst_paths.write_text(path, typst_objects.remove_object(text, object_id))
    return removed_objects.record(doc, "Sections/earthquake.typ", found, archive, after, before)


def _ids(path):
    return [o.id for o in typst_objects.objects(typst_paths.read_text(path))]


def test_an_object_removed_is_registered_where_it_stood():
    doc, path = _document("removed_register")
    entry = _remove(doc, path, "p2")
    assert (entry["after"], entry["before"]) == ("p1", "p3")
    assert entry["type"] == "text" and entry["title"].startswith("Zweiter Absatz") and entry["archive"].startswith("Sections/archives/")
    assert removed_objects.entries_for(doc, "Sections/earthquake.typ") == [entry]
    assert _ids(path) == ["title", "p1", "p3"]


def test_it_comes_back_right_after_the_object_before_it_whatever_was_written_since():
    doc, path = _document("removed_after")
    entry = _remove(doc, path, "p2")
    text = typst_paths.read_text(path)
    # the engineer wrote something between p1 and p3 meanwhile
    text = text.replace("// woodcore:/object p1\n", "// woodcore:/object p1\n\n#v(1em)\nVon Hand dazugeschrieben.\n")
    typst_paths.write_text(path, text)
    _path, new_text, object_id, _old = removed_objects.restore(doc, entry)
    assert object_id == "p2" and _ids(path) == ["title", "p1", "p2", "p3"]
    p1_end = new_text.index("// woodcore:/object p1")
    p2_start = new_text.index("// woodcore:object text p2")
    assert new_text.index("Von Hand dazugeschrieben.") > p2_start > p1_end, "the object did not come back right after the closing tag of the one before it"
    assert "Zweiter Absatz, *von Hand*  geschrieben." in new_text, "the body was not put back as written"
    assert "\n\n// woodcore:object text p2" in new_text and "// woodcore:/object p2\n\n" in new_text, "no blank line around the object put back"
    assert removed_objects.read(doc) == [], "the entry stayed in the register"


def test_it_comes_back_before_the_next_one_where_the_one_before_is_gone_and_at_the_end_where_both_are():
    doc, path = _document("removed_before")
    entry = _remove(doc, path, "p2")
    typst_paths.write_text(path, typst_objects.remove_object(typst_paths.read_text(path), "p1"))
    removed_objects.restore(doc, entry)
    assert _ids(path) == ["title", "p2", "p3"]
    doc, path = _document("removed_end")
    entry = _remove(doc, path, "p2")
    text = typst_objects.remove_object(typst_objects.remove_object(typst_paths.read_text(path), "p1"), "p3")
    typst_paths.write_text(path, text)
    removed_objects.restore(doc, entry)
    assert _ids(path) == ["title", "p2"]


def test_it_comes_back_under_a_free_id_where_its_own_was_taken():
    doc, path = _document("removed_taken")
    entry = _remove(doc, path, "p2")
    text = typst_paths.read_text(path)
    at = typst_objects.find(text, "p3").end
    typst_paths.write_text(path, typst_objects.insert_object(text, at, "text", "p2", "Ein neuer Absatz."))
    _path, new_text, object_id, _old = removed_objects.restore(doc, entry)
    assert object_id == "p2-2"
    assert "// woodcore:object text p2-2" in new_text and "// woodcore:/object p2-2" in new_text
    assert _ids(path) == ["title", "p1", "p2-2", "p3", "p2"]


def test_crlf_is_kept_and_a_file_or_a_copy_gone_is_refused():
    doc, path = _document("removed_crlf", TEXT.replace("\n", "\r\n"))
    entry = _remove(doc, path, "p2")
    removed_objects.restore(doc, entry)
    raw = path.read_bytes()
    assert b"\r\n" in raw and b"\n" not in raw.replace(b"\r\n", b""), "the file's line endings were mixed"
    doc, path = _document("removed_gone")
    entry = _remove(doc, path, "p2")
    (doc / entry["archive"]).unlink()
    try:
        removed_objects.restore(doc, entry)
    except removed_objects.RemovedError as exc:
        assert exc.code == "copy_gone"
    else:
        raise AssertionError("a copy gone was not refused")
    path.unlink()
    try:
        removed_objects.restore(doc, entry)
    except removed_objects.RemovedError as exc:
        assert exc.code == "file_gone"
    else:
        raise AssertionError("a file gone was not refused")


def test_forgetting_takes_the_entry_off_and_leaves_the_copy():
    doc, path = _document("removed_forget")
    entry = _remove(doc, path, "p1")
    assert removed_objects.forget(doc, entry) is True
    assert removed_objects.read(doc) == [] and (doc / entry["archive"]).is_file()
    assert removed_objects.forget(doc, entry) is False
