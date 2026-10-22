"""Whether a document's Typst changed since its PDF was written (calc/stamps.py, the engineer's rule of 30.09.2026: «export a document only if its Typst changed since its PDF»).

Every check here compiles for real -- `typst compile --deps ...` through `documents.compile_args`, the one spelling of a compile command line -- and then records and asks, because what a stamp stands on is the file Typst writes of what it read, and a test that wrote that file by hand would prove the stamp against the test and not against Typst. Typst is found as the rest of the suite finds it, and a machine without it skips.

Two projects are worked on. A small one built here, in three documents, whose entry files import `/config.typ` and `/commands.typ` from the Typst root, read the export's data and a picture, and include a section of their own -- the shape a project of three documents has, without the ten seconds of a real report. And a copy of the example project, which is a report alone (or is migrated by the time this runs: every assertion is derived from the project's own layout, never from a name), compiled once and asked all the same.
"""

import json
import os
import shutil
import subprocess
import time
from pathlib import Path

import conftest

import documents
import engine
import project
import stamps

SECTION = "Sections/intro.typ"
PICTURE = "Images/dot.svg"
DOT = '<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10"><rect width="10" height="10" fill="red"/></svg>\n'
INPUT_LEVEL = ["--input", "level=2"]


def _need_typst():
    if not conftest.have_typst():
        raise conftest.Skip("no Typst on this machine")


def _write(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def _modes_project(name):
    """A project in three documents, small enough to compile in a fraction of a second.

    The folders and entry files are those of a project laid out before the folders of issue #64 (`conftest.legacy_modes_layout`), whose names the checks below read as literals -- the layout by folders has a test of its own; config.typ and commands.typ lie at its top; the export has one file, `_woodcore/data/project.json`, which commands.typ reads. Every document includes `Sections/intro.typ` of its own folder, the convention d'utilisation also sets a picture from Images/, so the three read different files.
    """
    root = conftest.tmpdir(name)
    here = project.write(root / "Synth.woodcore", "Synth", layout=conftest.legacy_modes_layout("de"))
    _write(here.config_typ, "#let conf(body) = {\n  set page(width: 10cm, height: 6cm, margin: 1cm)\n  body\n}\n")
    _write(here.commands_typ, '#let project-name() = json("/_woodcore/data/project.json").name\n#let hello(who) = [Hello #who]\n')
    _write(here.data_dir / "project.json", '{"name": "Synth"}\n')
    _write(here.images_dir / "dot.svg", DOT)
    for mode in here.modes:
        body = f'#import "/config.typ": conf\n#import "/commands.typ": *\n#show: conf\n= {mode}\n#hello(project-name())\n#include "{SECTION}"\n'
        if mode == "cu":
            body += '#image("/Images/dot.svg", width: 1cm)\n'
        _write(here.document_typ(mode), body)
        _write(here.document_dir(mode) / SECTION, f"Intro of {mode}.\n")
    return here


def _compile(here, mode, flags=(), target=None, deps=True, preview=False):
    """Compiles document `mode` as the command line does: `--deps` into the stamps' own file where `deps`. Returns the deps file (or None) and the PDF it wrote."""
    where = stamps.deps_file(here, mode, preview) if deps else None
    target = here.document_pdf(mode) if target is None else Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    # started in the Typst root, as every compile of Woodcore's is: Typst writes the deps file's paths from there where it can
    result = subprocess.run([project.typst_executable(), *documents.compile_args(here, mode, flags, target=target, deps=where)],
                            capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=here.typst_root)
    assert result.returncode == 0, f"{mode} does not compile:\n{result.stderr}"
    return where, target


def _stamped(here, mode, flags=(), deps=True, preview=False, target=None):
    where, pdf = _compile(here, mode, flags, target=target, deps=deps, preview=preview)
    return stamps.record(here, mode, flags, where, pdf, preview=preview)


def _key(here, path):
    return Path(path).resolve().relative_to(here.root.resolve()).as_posix()


def _is_unchanged(here, mode, flags=(), **kw):
    changed, why = stamps.changed(here, mode, flags, **kw)
    assert not changed, f"{mode} should be unchanged, and {why.code}: {why}"
    assert why.code == "stamp_unchanged"


def _is_changed(here, mode, code, flags=(), **kw):
    changed, why = stamps.changed(here, mode, flags, **kw)
    assert changed, f"{mode} should have changed ({code})"
    assert why.code == code, f"{mode}: expected {code}, got {why.code}: {why}"
    return why


class _Edited:
    """A file's text changed for a `with` block, its bytes and its modification time put back after: what an edit and its undo are to a stamp, which is a digest of the content and so must say «unchanged» once the content is back."""

    def __init__(self, path, text=None, append=None):
        self.path, self.text, self.append = Path(path), text, append

    def __enter__(self):
        self.bytes = self.path.read_bytes()
        self.info = self.path.stat()
        self.mode = self.info.st_mode
        os.chmod(self.path, 0o666)   # the engine copied into a project is left read-only
        if self.text is not None:
            self.path.write_text(self.text, encoding="utf-8", newline="\n")
        else:
            self.path.write_bytes(self.bytes + (self.append or "").encode("utf-8"))
        return self

    def __exit__(self, *exc):
        self.path.write_bytes(self.bytes)
        os.utime(self.path, ns=(self.info.st_atime_ns, self.info.st_mtime_ns))
        os.chmod(self.path, self.mode)


def test_a_stamp_follows_a_compile_and_says_nothing_changed():
    _need_typst()
    here = _modes_project("stamps-basic")
    for mode in here.modes:
        stamp = _stamped(here, mode, INPUT_LEVEL)
        _is_unchanged(here, mode, INPUT_LEVEL)
        written = json.loads(stamps.stamp_file(here, mode).read_text(encoding="utf-8"))
        assert written == stamp
        assert stamp["stamp_version"] == 1 and stamp["document"] == mode
        assert stamp["entry"] == _key(here, here.document_typ(mode))
        assert stamp["pdf"] == _key(here, here.document_pdf(mode))
        assert stamp["pdf_sha256"] == stamps._sha256(here.document_pdf(mode))
        assert stamp["typst"] == project.typst_version() != ""
        assert stamp["flags"] == INPUT_LEVEL
        assert stamp["inputs_from"] == "deps"


def test_a_stamp_lists_what_typst_read_and_nothing_else():
    """The inputs are Typst's own list: the entry, the section, config.typ, commands.typ and the export's data -- the picture for the document that sets it only --, each a path from the project's folder with forward slashes and a SHA-256, and never the PDF, the deps file or the stamp."""
    _need_typst()
    here = _modes_project("stamps-inputs")
    cu, bp = _stamped(here, "cu"), _stamped(here, "bp")
    want = {_key(here, here.document_typ("cu")), _key(here, here.document_dir("cu") / SECTION), "config.typ", "commands.typ", "_woodcore/data/project.json", PICTURE}
    assert set(cu["inputs"]) == want, set(cu["inputs"]) ^ want
    assert PICTURE not in bp["inputs"] and _key(here, here.document_dir("cu") / SECTION) not in bp["inputs"]
    assert _key(here, here.document_dir("bp") / SECTION) in bp["inputs"]
    assert all(digest.startswith("sha256:") and len(digest) == len("sha256:") + 64 for digest in cu["inputs"].values())
    assert list(cu["inputs"]) == sorted(cu["inputs"]), "in key order, so an unchanged stamp is unchanged to the byte"
    for key in cu["inputs"]:
        assert "\\" not in key and not key.startswith("//"), key
    shown = json.dumps(cu)
    assert ".deps.json" not in shown and ".pdf" not in "".join(cu["inputs"])


def test_there_is_no_stamp_until_a_compile_was_recorded():
    _need_typst()
    here = _modes_project("stamps-none")
    assert stamps.read(here, "cu") is None
    why = _is_changed(here, "cu", "stamp_no_record")
    assert isinstance(why, engine.Note) and isinstance(why, str) and "cu" in why and why.args["document"] == "cu"


def test_a_stamp_that_is_not_one_is_no_stamp():
    _need_typst()
    here = _modes_project("stamps-garbled")
    _stamped(here, "bp")
    path = stamps.stamp_file(here, "bp")
    good = path.read_text(encoding="utf-8")
    for garbled in ("{not json", "[]", json.dumps({**json.loads(good), "stamp_version": 2}),
                    json.dumps({**json.loads(good), "inputs": ["config.typ"]}),
                    json.dumps({k: v for k, v in json.loads(good).items() if k != "pdf_sha256"}),
                    json.dumps({**json.loads(good), "inputs_from": "guess"})):
        path.write_text(garbled, encoding="utf-8")
        assert stamps.read(here, "bp") is None, garbled
        _is_changed(here, "bp", "stamp_no_record")
    path.write_text(good, encoding="utf-8")
    _is_unchanged(here, "bp")


def test_a_change_in_the_content_of_an_input_names_the_file():
    _need_typst()
    here = _modes_project("stamps-content")
    for mode in here.modes:
        _stamped(here, mode)
    section = here.document_dir("cu") / SECTION
    with _Edited(section, text="Another intro.\n"):
        why = _is_changed(here, "cu", "stamp_input_changed")
        assert why.args["file"] == _key(here, section) and _key(here, section) in why
        _is_unchanged(here, "bp")
        _is_unchanged(here, "rs")
    _is_unchanged(here, "cu")   # the content is back, so nothing changed


def test_what_the_three_documents_share_changes_all_three_and_a_picture_only_the_one_that_sets_it():
    _need_typst()
    here = _modes_project("stamps-shared")
    for mode in here.modes:
        _stamped(here, mode)
    for shared in (here.config_typ, here.commands_typ, here.data_dir / "project.json"):
        with _Edited(shared, append="\n"):
            for mode in here.modes:
                why = _is_changed(here, mode, "stamp_input_changed")
                assert why.args["file"] == _key(here, shared)
    with _Edited(here.images_dir / "dot.svg", append="\n"):
        _is_changed(here, "cu", "stamp_input_changed")
        _is_unchanged(here, "bp")
        _is_unchanged(here, "rs")
    for mode in here.modes:
        _is_unchanged(here, mode)


def test_a_modification_time_alone_changes_nothing():
    """The stamp is a digest of the content: NextCloud setting a time, an editor saving without a change and the export writing identical bytes must not cost a compile."""
    _need_typst()
    here = _modes_project("stamps-touch")
    _stamped(here, "cu")
    section = here.document_dir("cu") / SECTION
    now = time.time()
    for when in (now + 3600, now - 3600, None):
        os.utime(section, None if when is None else (when, when))
        _is_unchanged(here, "cu")
    section.write_bytes(section.read_bytes())
    _is_unchanged(here, "cu")
    # the same bytes written by another route, the export's way: a new file moved over the old one
    data = here.data_dir / "project.json"
    text = data.read_bytes()
    _write(data.with_name("project.json.new"), text.decode("utf-8"))
    os.replace(data.with_name("project.json.new"), data)
    _is_unchanged(here, "cu")


def test_a_missing_input_names_the_file():
    _need_typst()
    here = _modes_project("stamps-missing")
    _stamped(here, "cu")
    picture = here.images_dir / "dot.svg"
    kept = picture.read_bytes()
    picture.unlink()
    why = _is_changed(here, "cu", "stamp_input_missing")
    assert why.args["file"] == PICTURE
    picture.write_bytes(kept)
    _is_unchanged(here, "cu")


def test_other_flags_change_a_document_unless_they_are_ignored():
    _need_typst()
    here = _modes_project("stamps-flags")
    _stamped(here, "bp", INPUT_LEVEL)
    _is_unchanged(here, "bp", INPUT_LEVEL)
    for other in ([], ["--input", "level=3"], ["--input", "lang=fr"], INPUT_LEVEL + ["--input", "lang=fr"]):
        why = _is_changed(here, "bp", "stamp_flags", other)
        assert why.args["then"] == INPUT_LEVEL and why.args["now"] == other
        _is_unchanged(here, "bp", other, ignore_flags=True)
    _is_unchanged(here, "bp", list(INPUT_LEVEL))
    # tuples are the flags a caller has at hand
    _is_unchanged(here, "bp", tuple(INPUT_LEVEL))


def test_a_pdf_that_is_gone_or_is_not_the_one_written_changes_the_document():
    _need_typst()
    here = _modes_project("stamps-pdf")
    _stamped(here, "rs")
    pdf = here.document_pdf("rs")
    kept = pdf.read_bytes()
    pdf.unlink()
    why = _is_changed(here, "rs", "stamp_pdf_missing")
    assert why.args["file"] == _key(here, pdf)
    _is_changed(here, "rs", "stamp_pdf_missing", ignore_flags=True)
    pdf.write_bytes(kept + b"\n%%")
    _is_changed(here, "rs", "stamp_pdf_changed")
    pdf.write_bytes(kept)
    _is_unchanged(here, "rs")
    # recompiled, the PDF is whatever Typst wrote -- and the stamp of that compile is the one to ask
    _stamped(here, "rs")
    _is_unchanged(here, "rs")


def test_another_typst_changes_every_document():
    _need_typst()
    here = _modes_project("stamps-typst")
    _stamped(here, "cu")
    real = project.typst_version
    try:
        project.typst_version = lambda: "0.0.1"
        why = _is_changed(here, "cu", "stamp_typst")
        assert why.args["now"] == "0.0.1" and why.args["then"] == real()
        project.typst_version = lambda: ""
        why = _is_changed(here, "cu", "stamp_typst")
        assert "not installed" in why
    finally:
        project.typst_version = real
    _is_unchanged(here, "cu")


def test_the_layout_moving_changes_the_document():
    """A stamp says where the entry file and the PDF were: a project whose layout moved since is not one whose PDF is current."""
    _need_typst()
    here = _modes_project("stamps-moved")
    _stamped(here, "cu")
    path = stamps.stamp_file(here, "cu")
    good = json.loads(path.read_text(encoding="utf-8"))
    for field, code in (("entry", "stamp_entry"), ("pdf", "stamp_pdf_place")):
        path.write_text(json.dumps({**good, field: "elsewhere/" + good[field].rsplit("/", 1)[-1]}), encoding="utf-8")
        _is_changed(here, "cu", code)
    path.write_text(json.dumps(good), encoding="utf-8")
    _is_unchanged(here, "cu")


def test_an_input_modified_after_the_pdf_was_written_is_not_vouched_for():
    """`record` runs after the compile: a file saved in between would be hashed in its new state and the stamp would call current a PDF made from the old one. Such a file is recorded unsettled and named at the next question."""
    _need_typst()
    here = _modes_project("stamps-unsettled")
    where, pdf = _compile(here, "cu")
    section = here.document_dir("cu") / SECTION
    time.sleep(0.05)
    section.write_text("Saved while the record was about to be made.\n", encoding="utf-8")
    written = pdf.stat().st_mtime_ns
    halfway = written + (time.time_ns() - written) // 2
    os.utime(section, ns=(halfway, halfway))
    assert written < section.stat().st_mtime_ns <= time.time_ns()
    stamp = stamps.record(here, "cu", [], where, pdf)
    assert stamp["inputs"][_key(here, section)] == stamps.UNSETTLED
    why = _is_changed(here, "cu", "stamp_input_changed")
    assert why.args["file"] == _key(here, section)
    # the compile that follows settles it
    _stamped(here, "cu")
    _is_unchanged(here, "cu")


def test_a_modification_time_in_the_future_is_not_held_against_a_file():
    """A file another machine's clock dated is newer than any PDF for ever: it must not make its document compile at every export."""
    _need_typst()
    here = _modes_project("stamps-future")
    section = here.document_dir("cu") / SECTION
    where, pdf = _compile(here, "cu")
    ahead = time.time() + 3600
    os.utime(section, (ahead, ahead))
    stamp = stamps.record(here, "cu", [], where, pdf)
    assert stamp["inputs"][_key(here, section)].startswith("sha256:")
    _is_unchanged(here, "cu")


def test_recording_twice_writes_the_same_bytes():
    _need_typst()
    here = _modes_project("stamps-stable")
    where, pdf = _compile(here, "bp", INPUT_LEVEL)
    stamps.record(here, "bp", INPUT_LEVEL, where, pdf)
    first = stamps.stamp_file(here, "bp").read_bytes()
    stamps.record(here, "bp", INPUT_LEVEL, where, pdf)
    assert stamps.stamp_file(here, "bp").read_bytes() == first
    assert b"\r" not in first, "\\n whatever the platform"
    assert not list(here.stamps_dir.glob("*.tmp")), "written beside and moved into place, nothing left behind"


def test_a_preview_keeps_a_stamp_of_its_own():
    _need_typst()
    here = _modes_project("stamps-preview")
    deliverable = _stamped(here, "cu", INPUT_LEVEL)
    deliverable_bytes = stamps.stamp_file(here, "cu").read_bytes()
    preview_pdf = here.generated_dir / "preview" / "cu.pdf"
    assert stamps.deps_file(here, "cu", preview=True).name == "cu.preview.deps.json"
    assert stamps.stamp_file(here, "cu", preview=True).name == "cu.preview.json"
    preview = _stamped(here, "cu", [], preview=True, target=preview_pdf)
    assert preview["pdf"] == _key(here, preview_pdf) != deliverable["pdf"]
    assert _key(here, here.document_pdf("cu")) not in preview["inputs"] and preview["pdf"] not in preview["inputs"]
    assert stamps.stamp_file(here, "cu").read_bytes() == deliverable_bytes, "the preview's record does not touch the deliverable's"
    _is_unchanged(here, "cu", [], preview=True)
    _is_unchanged(here, "cu", INPUT_LEVEL)
    section = here.document_dir("cu") / SECTION
    with _Edited(section, append="more\n"):
        _is_changed(here, "cu", "stamp_input_changed", [], preview=True)
        _is_changed(here, "cu", "stamp_input_changed", INPUT_LEVEL)
    preview_pdf.unlink()
    _is_changed(here, "cu", "stamp_pdf_missing", [], preview=True)
    _is_unchanged(here, "cu", INPUT_LEVEL)
    assert stamps.read(here, "bp", preview=True) is None


def test_no_stamp_of_a_document_the_project_does_not_have():
    _need_typst()
    root = conftest.tmpdir("stamps-legacy-modes")
    here = project.write(root / "Old.woodcore", "Old")
    assert not here.has_modes
    for mode in ("cu", "bp"):
        for ask in (lambda: stamps.deps_file(here, mode), lambda: stamps.stamp_file(here, mode), lambda: stamps.read(here, mode)):
            try:
                ask()
            except project.ProjectError:
                continue
            raise AssertionError(f"a report alone has no {mode} document")
    assert stamps.read(here, "rs") is None


def test_a_deps_file_that_names_other_paths_is_read_as_typst_writes_them():
    """Handwritten in the shape Typst writes on Windows -- absolute paths with the `\\\\?\\` prefix, the target among the outputs -- with the three things a stamp leaves out put in the inputs on purpose, and one file outside the project."""
    _need_typst()
    here = _modes_project("stamps-handmade")
    where, pdf = _compile(here, "cu")
    outside = conftest.tmpdir("stamps-outside") / "a package.typ"
    outside.write_text("#let x = 1\n", encoding="utf-8")
    stamp_path = stamps.stamp_file(here, "cu")

    def verbatim(path):
        return "\\\\?\\" + str(Path(path).resolve())
    listed = [here.document_typ("cu"), here.config_typ, here.commands_typ, here.document_dir("cu") / SECTION, pdf, where, stamp_path, outside]
    where.write_text(json.dumps({"inputs": [verbatim(p) for p in listed], "outputs": [str(pdf)]}), encoding="utf-8")
    stamp = stamps.record(here, "cu", [], where, pdf)
    assert stamp["inputs_from"] == "deps"
    outside_key = Path(os.path.realpath(outside)).as_posix()
    assert set(stamp["inputs"]) == {_key(here, here.document_typ("cu")), "config.typ", "commands.typ", _key(here, here.document_dir("cu") / SECTION), outside_key}
    assert stamp["inputs"][outside_key] == f"stat:{outside.stat().st_size}:{outside.stat().st_mtime_ns}"
    assert stamp["inputs"]["config.typ"].startswith("sha256:")
    _is_unchanged(here, "cu")
    # a file of Typst's, outside the project, is known by its size and its time
    outside.write_text("#let x = 12\n", encoding="utf-8")
    why = _is_changed(here, "cu", "stamp_input_changed")
    assert why.args["file"] == outside_key
    outside.unlink()
    _is_changed(here, "cu", "stamp_input_missing")


def test_a_deps_file_of_relative_paths_is_read_from_the_typst_root():
    """Handwritten in the shape Typst writes on Linux and macOS -- every path from the folder it was started in, which is the Typst root (calc/stamps.py _read_deps) -- with the target among the outputs."""
    _need_typst()
    here = _modes_project("stamps-relative")
    where, pdf = _compile(here, "cu")
    root = here.typst_root.resolve()

    def relative(path):
        return os.path.relpath(Path(path).resolve(), root)
    listed = [here.document_typ("cu"), here.config_typ, here.commands_typ, here.document_dir("cu") / SECTION]
    where.write_text(json.dumps({"inputs": [relative(p) for p in listed], "outputs": [relative(pdf)]}), encoding="utf-8")
    stamp = stamps.record(here, "cu", [], where, pdf)
    assert stamp["inputs_from"] == "deps", "the outputs name the target: the file is this compile's"
    assert set(stamp["inputs"]) == {_key(here, here.document_typ("cu")), "config.typ", "commands.typ", _key(here, here.document_dir("cu") / SECTION)}
    _is_unchanged(here, "cu")


def test_windows_extended_paths_are_written_plain():
    assert stamps._plain("\\\\?\\C:\\Users\\a\\b.typ") == "C:\\Users\\a\\b.typ"
    assert stamps._plain("\\\\?\\UNC\\server\\share\\b.typ") == "\\\\server\\share\\b.typ"
    assert stamps._plain("C:\\Users\\a\\b.typ") == "C:\\Users\\a\\b.typ"
    assert stamps._plain("/home/a/b.typ") == "/home/a/b.typ"


def test_without_a_deps_file_the_inputs_are_enumerated_and_the_stamp_says_so():
    _need_typst()
    here = _modes_project("stamps-fallback")
    _write(here.references_bib, "% no entries\n")
    _write(here.typst_root / "Template" / "template.typ", "// the form\n")
    _write(here.typst_root / "Template" / "logo.png", "png")
    _write(here.document_dir("cu") / "notes.txt", "not Typst, not read\n")
    stamp = _stamped(here, "cu", INPUT_LEVEL, deps=False)
    assert stamp["inputs_from"] == "enumerated"
    want = {_key(here, here.document_typ("cu")), _key(here, here.document_dir("cu") / SECTION), "config.typ", "commands.typ", "references.bib", "Template/template.typ", "Template/logo.png", "_woodcore/data/project.json", PICTURE}
    assert set(stamp["inputs"]) >= want, want - set(stamp["inputs"])
    assert not any(key.endswith(".pdf") or ".deps" in key or "stamps" in key for key in stamp["inputs"])
    assert _key(here, here.document_dir("cu") / "notes.txt") not in stamp["inputs"], "only the document's .typ files"
    _is_unchanged(here, "cu", INPUT_LEVEL)
    section = here.document_dir("cu") / SECTION
    with _Edited(section, append="more\n"):
        assert _is_changed(here, "cu", "stamp_input_changed", INPUT_LEVEL).args["file"] == _key(here, section)
    with _Edited(here.references_bib, append="% an entry\n"):
        assert _is_changed(here, "cu", "stamp_input_changed", INPUT_LEVEL).args["file"] == "references.bib"
    with _Edited(here.typst_root / "Template" / "template.typ", append="// the form changed\n"):
        assert _is_changed(here, "cu", "stamp_input_changed", INPUT_LEVEL).args["file"] == "Template/template.typ", "the form is an input of every document"
    _is_unchanged(here, "cu", INPUT_LEVEL)
    # a file that appears in the set is a change: nothing says what reads it
    _write(here.document_dir("cu") / "Sections" / "added.typ", "New.\n")
    why = _is_changed(here, "cu", "stamp_input_added", INPUT_LEVEL)
    assert why.args["file"] == _key(here, here.document_dir("cu") / "Sections" / "added.typ")
    (here.document_dir("cu") / "Sections" / "added.typ").unlink()
    _write(here.images_dir / "extra.svg", DOT)
    _is_changed(here, "cu", "stamp_input_added", INPUT_LEVEL)
    (here.images_dir / "extra.svg").unlink()
    _is_unchanged(here, "cu", INPUT_LEVEL)


def test_a_deps_file_that_is_not_this_compile_s_is_not_trusted():
    """A file another compile left behind, a garbled one and one of another shape are not answers for this compile: the stamp falls back on the enumerated set and says so."""
    _need_typst()
    here = _modes_project("stamps-stale-deps")
    where, pdf = _compile(here, "cu")
    good = where.read_text(encoding="utf-8")
    assert stamps.record(here, "cu", [], where, pdf)["inputs_from"] == "deps"
    other = here.generated_dir / "somewhere else.pdf"
    for text in ("{not json", "[]", '{"inputs": "config.typ"}', '{"inputs": [1, 2]}',
                 json.dumps({"inputs": json.loads(good)["inputs"], "outputs": [str(other)]})):
        where.write_text(text, encoding="utf-8")
        assert stamps.record(here, "cu", [], where, pdf)["inputs_from"] == "enumerated", text
    where.unlink()
    assert stamps.record(here, "cu", [], where, pdf)["inputs_from"] == "enumerated"
    assert stamps.record(here, "cu", [], None, pdf)["inputs_from"] == "enumerated"
    where.write_text(good, encoding="utf-8")
    assert stamps.record(here, "cu", [], where, pdf)["inputs_from"] == "deps"
    _is_unchanged(here, "cu")


def test_recording_without_a_pdf_says_so():
    _need_typst()
    here = _modes_project("stamps-nopdf")
    where, pdf = _compile(here, "rs")
    pdf.unlink()
    try:
        stamps.record(here, "rs", [], where, pdf)
    except FileNotFoundError:
        pass
    else:
        raise AssertionError("a compile that worked leaves a PDF; one that did not is not recorded")
    assert stamps.read(here, "rs") is None


def test_a_report_alone_is_stamped_like_the_three_documents():
    """The example project, a copy of it: a real report of a dozen sections, its pictures and its export, compiled once. Whatever its layout -- a report alone today, migrated to three documents later -- its report is the `rs` document, and every name below is derived from the project's own paths."""
    _need_typst()
    work = conftest.tmpdir("stamps-example") / "project"
    shutil.copytree(conftest.PROJECT.root, work, ignore=shutil.ignore_patterns(".probe", "_Archiv", "stamps", "__pycache__"))
    here = project.Project.load(work / conftest.SAMPLE.name)
    entry, pdf_path = here.document_typ("rs"), here.document_pdf("rs")
    sections = sorted((here.document_dir("rs") / "Sections").glob("*.typ"))
    assert sections, "the example report has sections"
    section = sections[0]

    stamp = _stamped(here, "rs", INPUT_LEVEL)
    assert stamp["document"] == "rs" and stamp["inputs_from"] == "deps"
    assert stamp["entry"] == _key(here, entry) and stamp["pdf"] == _key(here, pdf_path)
    assert _key(here, here.stamps_dir).startswith(_key(here, here.generated_dir) + "/"), "the stamps lie in the export's folder, which the documents share"
    keys = set(stamp["inputs"])
    assert {_key(here, entry), _key(here, section), _key(here, here.config_typ), _key(here, here.commands_typ), _key(here, here.data_dir / "project.json")} <= keys
    assert _key(here, here.generated_dir / "lib" / "calc-engine.typ") in keys, "the engine's copy is an input: a new engine is a new report"
    assert any(key.startswith(_key(here, here.images_dir) + "/") for key in keys), "the pictures are inputs"
    assert not any(key.endswith(".deps.json") or key == stamp["pdf"] or "/stamps/" in key for key in keys)
    assert len(keys) > 20
    assert not any(Path(key).is_absolute() for key in keys), "nothing of this project lies outside it"
    _is_unchanged(here, "rs", INPUT_LEVEL)
    _is_changed(here, "rs", "stamp_flags", [])
    _is_unchanged(here, "rs", [], ignore_flags=True)

    # a mtime-only touch, then a real edit and its undo
    os.utime(section, None)
    _is_unchanged(here, "rs", INPUT_LEVEL)
    with _Edited(section, append="\n// edited\n"):
        assert _is_changed(here, "rs", "stamp_input_changed", INPUT_LEVEL).args["file"] == _key(here, section)
    _is_unchanged(here, "rs", INPUT_LEVEL)
    with _Edited(here.data_dir / "project.json", append="\n"):
        assert _is_changed(here, "rs", "stamp_input_changed", INPUT_LEVEL).args["file"] == _key(here, here.data_dir / "project.json")
    with _Edited(here.generated_dir / "lib" / "calc-engine.typ", append="\n"):
        _is_changed(here, "rs", "stamp_input_changed", INPUT_LEVEL)
    _is_unchanged(here, "rs", INPUT_LEVEL)

    # the PDF, taken away
    kept = pdf_path.read_bytes()
    pdf_path.unlink()
    _is_changed(here, "rs", "stamp_pdf_missing", INPUT_LEVEL)
    pdf_path.write_bytes(kept)
    _is_unchanged(here, "rs", INPUT_LEVEL)

    # the enumerated fallback, on the same PDF: more inputs than Typst read, never fewer
    fallback = stamps.record(here, "rs", INPUT_LEVEL, None, pdf_path)
    assert fallback["inputs_from"] == "enumerated"
    assert set(fallback["inputs"]) >= keys, "everything Typst read is in the set, which errs on the side of more"
    assert _key(here, here.generated_dir / "lib" / "i18n.typ") in fallback["inputs"]
    _is_unchanged(here, "rs", INPUT_LEVEL)
    probe = here.typst_root / ".probe" / "a" / "probe.typ"
    _write(probe, "#let x = 1\n")
    _is_unchanged(here, "rs", INPUT_LEVEL)   # a probe the suite compiles is not part of the report
    with _Edited(section, append="\n// edited\n"):
        assert _is_changed(here, "rs", "stamp_input_changed", INPUT_LEVEL).args["file"] == _key(here, section)
    added = here.document_dir("rs") / "Sections" / "zz-new.typ"
    _write(added, "New.\n")
    assert _is_changed(here, "rs", "stamp_input_added", INPUT_LEVEL).args["file"] == _key(here, added)
    added.unlink()
    _is_unchanged(here, "rs", INPUT_LEVEL)

    # and a report alone has no other document
    if here.has_modes:
        assert stamps.deps_file(here, "cu").name == "cu.deps.json"
        return
    try:
        stamps.deps_file(here, "cu")
    except project.ProjectError:
        return
    raise AssertionError("a report alone has no cu document")


def test_a_project_laid_out_by_folders_is_stamped_from_its_folders():
    """Issue #64: config.typ, commands.typ, references.bib and the form in 000-Typst-Config/, the export in 000-Woodcore/ -- read by every document --, and the sources and the archives in 000-Woodcore/ beside it, read by none: an enumerated stamp takes the first in and leaves the second out, by their paths and not by a folder's name (spec 2026-10-15 ARCH-RISK-A01)."""
    _need_typst()
    root = conftest.tmpdir("stamps-folders")
    here = project.write(root / "Synth.woodcore", "Synth", layout=documents.layout_for("fr"))
    here.ensure_folders()
    _write(here.config_typ, "#let conf(body) = {\n  set page(width: 10cm, height: 6cm, margin: 1cm)\n  body\n}\n")
    data = here.from_root(here.data_dir / "project.json")
    _write(here.commands_typ, "#let project-name() = json(\"" + data + "\").name\n")
    _write(here.data_dir / "project.json", '{"name": "Synth"}\n')
    _write(here.references_bib, "% no entries\n")
    _write(here.template_dir / "template.typ", "// the form\n")
    _write(here.sources_dir / "positions.json", "{}\n")
    _write(here.archives_dir / "old.zip", "zip")
    _write(here.formulas_dir / "mine.typ", "Mine.\n")
    head = "#import \"" + here.from_root(here.config_typ) + "\": conf\n#import \"" + here.from_root(here.commands_typ) + "\": *\n#show: conf\n"
    _write(here.document_typ("cu"), head + "#project-name()\n#include \"" + here.from_root(here.formulas_dir / "mine.typ") + "\"\n")
    stamp = _stamped(here, "cu", INPUT_LEVEL, deps=False)
    assert stamp["inputs_from"] == "enumerated"
    inputs = set(stamp["inputs"])
    for path in (here.config_typ, here.commands_typ, here.references_bib, here.template_dir / "template.typ", here.data_dir / "project.json", here.formulas_dir / "mine.typ"):
        assert _key(here, path) in inputs, _key(here, path)
    assert not any(key.startswith(("000-Woodcore/sources/", "000-Woodcore/archives/")) for key in inputs), inputs
    _is_unchanged(here, "cu", INPUT_LEVEL)
    _write(here.archives_dir / "newer.zip", "zip")
    _is_unchanged(here, "cu", INPUT_LEVEL)   # an archive written is no change of the document
    with _Edited(here.commands_typ, append="// edited\n"):
        assert _is_changed(here, "cu", "stamp_input_changed", INPUT_LEVEL).args["file"] == "000-Typst-Config/commands.typ"
