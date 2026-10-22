"""The «Templates» view's preview: a document shown with a content template and a form chosen, and nothing of the project but its basic data (calc/template_preview.py, issue #88, docs/ui/tab-project.md).

What is held: that the module needs no Qt; that the real project is left exactly as it was -- every file's name, size and time -- and none of its files but the project file and its config.typ is opened; that the throw-away project carries the real one's name, title page and language and the content template and form asked for; that the neutral and the BFH forms compile, the BFH one with its own title page; that the previews built before are taken away, the engine's read-only copy among them; and that a preview that cannot be made says why by a code the window translates.
"""

import builtins
import json
import os
import subprocess
import sys
from pathlib import Path

import conftest
from conftest import CALC, ROOT

import project
import project_template
import template_preview


def _real(name, language="fr", **details):
    """A project of the engineer's, as the «Projet» tab would preview it: its report made, its title page filled."""
    root = conftest.tmpdir(name)
    here = project_template.create_skeleton(root / "Real", "Hangar Dupont", language, client="Commune", author="F. L.", **details)
    return project_template.create_document(here, "rs")


def _snapshot(here):
    return sorted((p.relative_to(here.root).as_posix(), p.stat().st_size, p.stat().st_mtime_ns) for p in here.root.rglob("*") if p.is_file())


def test_the_module_needs_no_qt():
    done = subprocess.run([sys.executable, "-c", "import sys; sys.path.insert(0, sys.argv[1]); import template_preview; print(any(m.startswith('PySide6') for m in sys.modules))", str(CALC)],
                          capture_output=True, text=True, encoding="utf-8", cwd=str(ROOT))
    assert done.returncode == 0 and done.stdout.strip() == "False", done.stdout + done.stderr


def test_a_preview_writes_nothing_into_the_project_and_reads_only_its_basic_data():
    here = _real("preview_untouched")
    cache = conftest.tmpdir("preview_untouched_cache")
    before = _snapshot(here)
    opened = []
    original = builtins.open

    def spying(file, *args, **kwargs):
        path = Path(os.fspath(file)) if isinstance(file, (str, os.PathLike)) else None
        if path is not None and project._is_within(path, here.root):
            opened.append(path)
        return original(file, *args, **kwargs)

    builtins.open = spying
    try:
        with project.using(conftest.PROJECT):   # another project current, as in the window of another project
            shown = template_preview.prepare(here, "cu", "builtin:cu/standard", "builtin:bfh", root=cache)
    finally:
        builtins.open = original
    assert _snapshot(here) == before, "the preview wrote into the project"
    allowed = {here.file.resolve(), here.config_typ.resolve(), here.report_typ.resolve()}
    strays = sorted({str(p) for p in opened if p.resolve() not in allowed})
    assert not strays, f"the preview opened files of the project beyond its basic data: {strays}"
    assert project._is_within(shown.root, cache) and shown.created_modes == ("cu",)
    assert shown.name == "Hangar Dupont" and shown.detail("client") == "Commune" and shown.detail("author") == "F. L."
    assert shown.content_template("cu") == "builtin:cu/standard"
    info = json.loads((shown.data_dir / "project.json").read_text(encoding="utf-8"))
    assert info["name"] == "Hangar Dupont" and info["client"] == "Commune"
    import templates
    assert templates.project_language(shown, fallback="") == "fr"


def test_the_neutral_and_the_bfh_forms_compile_and_the_bfh_carries_its_title_page():
    if not conftest.have_typst():
        raise conftest.Skip("typst is not installed here")
    import documents
    from pypdf import PdfReader
    here = _real("preview_compiles", "de")
    cache = conftest.tmpdir("preview_compiles_cache")
    pages = {}
    for form in ("builtin:neutral", "builtin:bfh"):
        shown = template_preview.prepare(here, "rs", None, form, root=cache)
        done = subprocess.run([project.typst_executable(), *documents.compile_args(shown, "rs")], capture_output=True, text=True, encoding="utf-8", errors="replace")
        assert done.returncode == 0, (form, done.stderr[-2000:])
        reader = PdfReader(str(shown.document_pdf("rs")))
        pages[form] = " ".join((reader.pages[0].extract_text() or "").split())
        assert "Hangar Dupont" in pages[form], (form, pages[form][:300])
    assert pages["builtin:neutral"] != pages["builtin:bfh"], "the two forms give the same title page"


def test_the_previews_before_are_taken_away_read_only_engine_included():
    here = _real("preview_clean")
    cache = conftest.tmpdir("preview_clean_cache")
    first = template_preview.prepare(here, "bp", None, None, root=cache)
    second = template_preview.prepare(here, "bp", None, None, root=cache)
    assert first.root != second.root and first.root.is_dir()
    assert any(not os.access(p, os.W_OK) for p in first.generated_dir.rglob("*") if p.is_file()), "the engine's copy is not read-only: this test proves nothing"
    assert template_preview.clean(here, keep=second, root=cache) == 1
    assert not first.root.exists() and second.root.is_dir()
    assert template_preview.clean(here, root=cache) == 1 and not any(cache.iterdir())


def test_a_preview_that_cannot_be_made_says_why_by_a_code():
    here = _real("preview_errors")
    cache = conftest.tmpdir("preview_errors_cache")
    for mode, content, code in (("xx", None, "bad_mode"), ("cu", "builtin:cu/no-such-template", "template_unusable")):
        try:
            template_preview.prepare(here, mode, content, None, root=cache)
        except template_preview.TemplatePreviewError as exc:
            assert exc.code == code and exc.code in template_preview.CODES, (mode, exc.code, str(exc))
        else:
            raise AssertionError(f"{mode} {content}: a preview made")
    bare = project_template.create_skeleton(conftest.tmpdir("preview_errors_bare") / "P", "Probe", "fr")   # no document: its config.typ alone says the language
    config = bare.config_typ
    config.write_text(config.read_text(encoding="utf-8").replace('doc-lang = "fr"', 'doc-lang = ""'), encoding="utf-8")
    try:
        template_preview.prepare(bare, "cu", None, None, root=cache)
    except template_preview.TemplatePreviewError as exc:
        assert exc.code == "no_language", exc.code
    else:
        raise AssertionError("a preview made without a language")
