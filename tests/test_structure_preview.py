"""The Typst source of what the «Structure du document» tab previews (calc/structure_preview.py; the engineer's rework of 01.10.2026, work package R2-D1): **the node chosen and nothing else**.

A chapter shows only its printed sections, a section only itself, an object only its body, several nodes one after the other, nothing the whole document -- and each is held twice: by the source that is written (root-absolute paths, the heading offset a section has in its document, the preamble an object relies on, a heading of a file with no tags standing for its file) and, where Typst is installed, by **compiling that source from standard input and reading the words on the page it gives** (pypdf), which is the only way to say that a snippet shows what it should and none of what it should not.

Qt-free: the tab's own tests (tests/test_structure_tab.py) show the same pages in the window. The project is made once by `project_template.create`, in this process's own temp folder, and nothing here writes into it.
"""

import io
import re

import conftest
from conftest import Skip

import project
import proc
import structure
import structure_preview
import typst_objects

_STATE = {}


def _here():
    if "here" not in _STATE:
        import project_template
        base = conftest.tmpdir("structure_preview")
        _STATE["here"] = project_template.create(base / "Halle", "Halle", document_language="fr", report_language="fr", author="L. Exempel")
    return _STATE["here"]


def _words(text):
    """The words of a page as one line: a hyphen at a line's end joined, the typographic apostrophe and the non-breaking spaces Typst sets made plain -- the titles the tree shows are typed with a straight one."""
    text = re.sub(r"[-­‑]\s*\n\s*", "", text).replace("’", "'").replace(" ", " ").replace(" ", " ")
    return re.sub(r"\s+", " ", text).strip()


def _page_text(source, here):
    """The words of the page a snippet compiles to -- Typst run on the source from standard input, the way the tab's pane runs it."""
    if not conftest.have_typst():
        raise Skip("typst is not installed here")
    import project as p
    out = conftest.tmpdir("structure_preview_pdf") / "snippet.pdf"
    done = proc.run([str(p.typst_executable()), "compile", "--root", str(here.typst_root), "-", str(out)],
                    input=source, capture_output=True, text=True, encoding="utf-8", errors="replace")
    assert done.returncode == 0, done.stderr[:2000]
    from pypdf import PdfReader
    reader = PdfReader(io.BytesIO(out.read_bytes()))
    return _words(" ".join(page.extract_text() or "" for page in reader.pages)), len(reader.pages)


def _first_words(markup, count=4):
    """The first `count` words of a paragraph's markup, plain: what its page begins with."""
    return " ".join(structure.plain_title(markup).split()[:count])


def _object(nodes, kind, file_id=None):
    return next(n for n in structure.flatten(nodes) if n.kind == "object" and n.object_type == kind and (file_id is None or n.parent == file_id))


def _paragraph(here, node):
    text = typst_objects.find((here.document_dir("cu") / node.file).read_text(encoding="utf-8"), node.object_id)
    return text.written


def _plain_sections(nodes):
    """(chapter, its two first sections) of the first chapter that holds two printed sections of their own -- not shared, so that nothing here depends on the catalogue's sharing."""
    for node in structure.flatten(nodes):
        if node.kind == "group":
            files = [c for c in node.children if c.kind == "file" and c.enabled]
            if len(files) >= 2:
                return node, files[0], files[1]
    raise AssertionError("no chapter with two sections")


# --- the source ------------------------------------------------------------------------------------

def test_nothing_chosen_is_the_whole_document_and_what_a_snippet_cannot_isolate_is_too():
    here = _here()
    nodes = structure.tree(here, "cu")
    assert structure_preview.build(here, "cu", nodes, []) is None
    assert structure_preview.build(here, "cu", nodes, None) is None
    assert structure_preview.build(here, "cu", nodes, ["not-a-node"]) is None
    rs = structure.tree(here, "rs")
    entry_headings = [n for n in structure.flatten(rs) if n.kind == "heading" and n.file == here.document_typ("rs").name]
    if entry_headings:
        assert structure_preview.build(here, "rs", rs, [entry_headings[0].id]) is None


def test_every_snippet_starts_with_the_projects_conf_a_page_as_tall_as_it_needs_and_the_documents_engine():
    here = _here()
    nodes = structure.tree(here, "cu")
    node = _plain_sections(nodes)[1]
    snippet = structure_preview.build(here, "cu", nodes, [node.id])
    lines = snippet.source.splitlines()
    assert lines[:4] == ['#import "/000-Typst-Config/config.typ": conf', '#import "/000-Typst-Config/commands.typ": *', "#show: conf", structure_preview.page_line(here)], lines[:4]
    page = structure_preview.page_line(here)
    assert "height: auto" in page and "footer: none" in page and "header: none" in page and "numbering: none" in page
    assert page.startswith("#set page(width: ") and "margin: (x: 0.8cm, y: 1.0cm)" in page
    assert '#wc-document.update("cu")' in lines and '#set-report-language("fr")' in lines
    assert "#set heading(numbering: none)" in lines, "a part of a document has no heading number to show"
    # nothing of the document's own front: no title page, no outline, no revision attachment
    assert "outline" not in snippet.source and "woodcore-document" not in snippet.source and "datetime" not in snippet.source


def test_a_section_is_included_from_the_root_as_its_document_includes_it():
    """A section of a document that writes its headings at the level they print at (06.10.2026) is included as it is, with no offset -- its file says its level."""
    here = _here()
    nodes = structure.tree(here, "cu")
    chapter, first, _second = _plain_sections(nodes)
    snippet = structure_preview.build(here, "cu", nodes, [first.id])
    folder = here.document_dir("cu").name
    assert snippet.kind == "file" and snippet.ids == (first.id,)
    assert f'#include "/{folder}/{first.file}"' in snippet.source and "set heading(offset" not in snippet.source, snippet.source
    assert "/Sections/" in snippet.source and "include \"Sections/" not in snippet.source, "a path relative to a source with no folder reads nothing"
    assert snippet.files == (here.document_dir("cu") / first.file,)
    # the report's sections have no offset: they are included as they are
    rs = structure.tree(here, "rs")
    section = next(n for n in rs if n.kind == "file")
    rs_snippet = structure_preview.build(here, "rs", rs, [section.id])
    assert "set heading(offset" not in rs_snippet.source and f'#include "/{here.document_dir("rs").name}/{section.file}"' in rs_snippet.source, rs_snippet.source
    assert '#wc-document.update("rs")' in rs_snippet.source


def test_a_chapter_is_its_heading_and_the_sections_it_prints_and_a_disabled_one_is_left_out():
    here = _here()
    nodes = structure.tree(here, "cu")
    chapter, first, second = _plain_sections(nodes)
    snippet = structure_preview.build(here, "cu", nodes, [chapter.id])
    folder = here.document_dir("cu").name
    assert snippet.kind == "group" and snippet.ids == (chapter.id,)
    # the chapter is its own file, its heading at its level (06.10.2026)
    assert chapter.file and f'#include "/{folder}/{chapter.file}"' in snippet.source, snippet.source
    for child in chapter.children:
        if child.kind == "file":
            assert (f'include "/{folder}/{child.file}"' in snippet.source) == bool(child.enabled), child.id
    # a section switched off is not in its chapter's page, as it is not in the document's
    import copy
    off = copy.deepcopy(nodes)
    flat = {n.id: n for n in structure.flatten(off)}
    flat[first.id].enabled = False
    again = structure_preview.build(here, "cu", off, [chapter.id])
    assert f'include "/{folder}/{first.file}"' not in again.source and f'include "/{folder}/{second.file}"' in again.source
    # ... but the section chosen itself is shown, printed or not: the engineer is looking at what it would print
    alone = structure_preview.build(here, "cu", off, [first.id])
    assert f'include "/{folder}/{first.file}"' in alone.source


def test_an_object_is_the_preamble_of_its_file_the_offset_of_its_section_and_its_body_as_written():
    here = _here()
    nodes = structure.tree(here, "cu")
    chapter, first, _second = _plain_sections(nodes)
    objects = [c for c in first.children if c.kind == "object"]
    assert objects, "the template's sections are tagged"
    paragraph = next(c for c in objects if c.object_type == "text")
    snippet = structure_preview.build(here, "cu", nodes, [paragraph.id])
    assert snippet.kind == "object" and snippet.ids == (paragraph.id,)
    body = _paragraph(here, paragraph)
    assert "#set heading(offset: 0)" in snippet.source and '#import "/000-Typst-Config/commands.typ": *' in snippet.source     # the file writes its headings at the level they print at
    assert body in snippet.source and "woodcore:object" not in snippet.source, "the tags are comments of the file and not part of what it prints"
    assert structure_preview.preamble('#import "/000-Typst-Config/commands.typ": *\n#let x = 1\n\n// woodcore:object text a\nhello\n// woodcore:/object a\n#set text(size: 9pt)\n') == '#import "/000-Typst-Config/commands.typ": *\n#let x = 1\n'
    # the objects of one file chosen together stand one after the other, in the file's order
    two = structure_preview.build(here, "cu", nodes, [objects[1].id, objects[0].id])
    assert two.ids == (objects[0].id, objects[1].id)


def test_what_is_chosen_with_what_holds_it_is_shown_once_and_a_heading_of_an_untagged_file_stands_for_its_file():
    here = _here()
    nodes = structure.tree(here, "cu")
    chapter, first, second = _plain_sections(nodes)
    inside = next(c for c in first.children if c.kind == "object")
    snippet = structure_preview.build(here, "cu", nodes, [inside.id, first.id, chapter.id])
    assert snippet.ids == (chapter.id,) and snippet.kind == "group" and snippet.source.count(first.file) == 1
    mixed = structure_preview.build(here, "cu", nodes, [first.id, second.id, inside.id])
    assert mixed.ids == (first.id, second.id) and mixed.kind == "file"
    several = structure_preview.build(here, "cu", nodes, [first.id, _object(nodes, "text", second.id).id])
    assert several.kind == "mixed"
    # an untagged file: the report's files are not tagged, so its headings are nested heading nodes
    rs = structure.tree(here, "rs")
    heading = next((n for n in structure.flatten(rs) if n.kind == "heading" and n.file and n.file != here.document_typ("rs").name), None)
    if heading is not None:
        found = structure_preview.build(here, "rs", rs, [heading.id])
        assert found.kind == "file" and found.ids and heading.file in found.source.replace("\\", "/")


def test_a_key_names_the_source_and_the_document_and_changes_with_both():
    here = _here()
    nodes = structure.tree(here, "cu")
    _chapter, first, second = _plain_sections(nodes)
    one = structure_preview.build(here, "cu", nodes, [first.id])
    again = structure_preview.build(here, "cu", nodes, [first.id])
    other = structure_preview.build(here, "cu", nodes, [second.id])
    assert one.key == again.key and one.key != other.key and re.fullmatch(r"[0-9a-f]{12}", one.key)


def test_a_text_the_engineer_typed_reaches_typst_quoted_never_as_code():
    here = _here()
    nodes = structure.tree(here, "cu")
    chapter = _plain_sections(nodes)[0]
    chapter.file = None     # a chapter with no file of its own, as one laid out before 06.10.2026: its heading is written from its title
    chapter.title = 'Le « chapitre » "piège" \\ #panic("x")'
    snippet = structure_preview.build(here, "cu", nodes, [chapter.id])
    heading = next(line for line in snippet.source.splitlines() if line.startswith("#heading("))
    assert heading.startswith('#heading(level: 1, "') and heading.endswith('")'), heading
    inside = heading[len('#heading(level: 1, "'):-2]
    # one string literal: no quote of the title's own is left bare
    assert not re.search(r'(?<!\\)"', inside.replace("\\\\", "")), heading
    assert "panic" in inside, heading


# --- the page -----------------------------------------------------------------------------------------

def test_an_object_compiles_to_its_own_words_and_none_of_its_section_s():
    here = _here()
    nodes = structure.tree(here, "cu")
    chapter, first, second = _plain_sections(nodes)
    paragraph = next(c for c in first.children if c.kind == "object" and c.object_type == "text")
    heading = next(c for c in first.children if c.kind == "object" and c.object_type == "heading")
    text, pages = _page_text(structure_preview.build(here, "cu", nodes, [paragraph.id]).source, here)
    assert _first_words(_paragraph(here, paragraph)) in text, text[:300]
    assert structure.plain_title(heading.title) not in text, "the heading of the section is not the paragraph's"
    other = next(c for c in second.children if c.kind == "object" and c.object_type == "text")
    assert _first_words(_paragraph(here, other)) not in text
    assert pages == 1


def test_a_section_compiles_to_itself_only_and_a_chapter_to_its_own_sections():
    here = _here()
    nodes = structure.tree(here, "cu")
    chapter, first, second = _plain_sections(nodes)
    title = lambda node: structure.plain_title(node.title)   # noqa: E731
    text, _pages = _page_text(structure_preview.build(here, "cu", nodes, [first.id]).source, here)
    assert title(first) in text and title(second) not in text and title(chapter) not in text, text[:400]
    chapter_text, _pages = _page_text(structure_preview.build(here, "cu", nodes, [chapter.id]).source, here)
    assert title(chapter) in chapter_text and title(first) in chapter_text and title(second) in chapter_text, chapter_text[:400]
    elsewhere = next(n for n in structure.flatten(nodes) if n.kind == "file" and n.enabled and n.parent != chapter.id and n.parent)
    assert title(elsewhere) not in chapter_text
    # the two sections chosen together are the two and nothing else
    both, _pages = _page_text(structure_preview.build(here, "cu", nodes, [first.id, second.id]).source, here)
    assert title(first) in both and title(second) in both and title(elsewhere) not in both and title(chapter) not in both


def test_a_table_is_a_page_the_height_of_a_table():
    here = _here()
    nodes = structure.tree(here, "cu")
    table = next(n for n in structure.flatten(nodes) if n.kind == "object" and n.object_type == "table")
    source = structure_preview.build(here, "cu", nodes, [table.id]).source
    out = conftest.tmpdir("structure_preview_table") / "table.pdf"
    if not conftest.have_typst():
        raise Skip("typst is not installed here")
    done = proc.run([str(project.typst_executable()), "compile", "--root", str(here.typst_root), "-", str(out)], input=source, capture_output=True, text=True, encoding="utf-8")
    assert done.returncode == 0, done.stderr[:1500]
    from pypdf import PdfReader
    reader = PdfReader(io.BytesIO(out.read_bytes()))
    assert len(reader.pages) == 1
    height, width = float(reader.pages[0].mediabox.height), float(reader.pages[0].mediabox.width)
    wanted = (structure_preview.text_width_cm(here) + 2 * structure_preview.SIDE_CM) / 2.54 * 72
    assert abs(width - wanted) < 1.5 and height < 500, (width, wanted, height)     # as wide as the text and a margin each side, and short: a table alone is not a page of paper


# --- the width of the page ---------------------------------------------------------------------------------

class _Config:
    """A project as far as `text_width_cm` asks anything of it: the file its config.typ is."""

    def __init__(self, path):
        self.config_typ = path


def _width_of(text):
    path = conftest.tmpdir("structure_preview_config") / "config.typ"
    path.write_text(text, encoding="utf-8")
    return structure_preview.text_width_cm(_Config(path))


def test_the_page_of_a_snippet_is_as_wide_as_the_text_of_the_documents_pages_and_a_margin():
    """A snippet is shown fitted to the width of a pane about 600 px wide: on a whole A4 page its text is set at two thirds of its size. Its page is the width of the text plus 0.8 cm either side, and the line breaking is the printed document's."""
    here = _here()
    assert structure_preview.text_width_cm(here) == 16.0, "the neutral style: an A4 less 2.5 cm each side"
    assert structure_preview.page_line(here).startswith("#set page(width: 17.60cm, "), structure_preview.page_line(here)
    compact = project_template_create("structure_preview_compact", style="compact")
    assert structure_preview.text_width_cm(compact) == 17.0 and structure_preview.page_line(compact).startswith("#set page(width: 18.60cm, ")
    # the project's own config.typ is read, in the form it is written
    assert _width_of('#let conf(d) = { set page(paper: "a4", margin: (top: 3cm, bottom: 2.5cm, left: 2.5cm, right: 2.5cm)); d }') == 16.0
    assert _width_of('#let conf(d) = { set page(paper: "a5", margin: 1cm); d }') == 12.8
    assert _width_of('#let conf(d) = { set page(margin: (x: 2cm, y: 3cm)); d }') == 17.0
    assert _width_of('#let conf(d) = { set page(width: 20cm, margin: (left: 3cm, right: 1.5cm)); d }') == 15.5
    assert _width_of('#let conf(d) = { set page(paper: "a4"); d }') == 16.0, "a margin left out is Typst's own: 2.5 cm on an A4"
    assert _width_of('#let conf(d) = { set page(paper: "us-letter", flipped: true); d }') == 22.8
    assert _width_of('#let conf(d) = { set page(paper: "a4", margin: 3cm); set page(margin: (x: 2cm)); d }') == 17.0, "the later rule wins for what it states"
    # what is only a comment or a string is not read
    comment = '// set page(paper: "a3")' + chr(10) + '#let x = "set page(paper: \\"a3\\")"' + chr(10) + '#let conf(d) = d' + chr(10)
    assert _width_of(comment) == 16.0


def test_a_page_the_config_does_not_say_in_a_form_this_reads_is_the_reports_own_measure_of_sixteen_centimetres():
    for text in ('#let conf(d) = { set page(width: 20cm, margin: 2em); d }',                 # a unit this does not read
                 '#let conf(d) = { set page(paper: "a4", margin: (x: 10%)); d }',
                 '#let conf(d) = { set page(paper: "zork"); d }',                           # a paper it does not know
                 '#let conf(d) = { set page(paper: "a4", margin: (left: 12cm, right: 12cm)); d }',     # a text of no width
                 '#let conf(d) = d'):
        found = _width_of(text)
        assert found is None or 5 <= found <= 21, (text, found)
    for text in ('#let conf(d) = { set page(width: 20cm, margin: 2em); d }', '#let conf(d) = { set page(paper: "zork"); d }'):
        assert _width_of(text) is None
    missing = _Config(conftest.tmpdir("structure_preview_config") / "not-there.typ")
    assert structure_preview.text_width_cm(missing) is None
    assert structure_preview.page_line(missing).startswith("#set page(width: 17.60cm, "), "16 cm and a margin each side"


def project_template_create(name, style=None):
    import project_template
    base = conftest.tmpdir(name)
    return project_template.create(base / "Halle", "Halle", document_language="fr", report_language="fr", author="L. Exempel", style=style)


def test_a_snippet_compiles_to_a_page_as_wide_as_the_text_and_breaks_its_lines_as_the_document_does():
    """Read back from Typst: the page's width, and the lines of a paragraph -- broken where they are on a page of the document's own width (an A4 with the margins its config.typ sets, which is what a snippet was until the rework), not where a narrower page would break them."""
    if not conftest.have_typst():
        raise Skip("typst is not installed here")
    from pypdf import PdfReader
    here = _here()
    nodes = structure.tree(here, "cu")
    _chapter, first, _second = _plain_sections(nodes)
    paragraph = max((c for c in first.children if c.kind == "object" and c.object_type == "text"), key=lambda c: len(_paragraph(here, c)))
    source = structure_preview.build(here, "cu", nodes, [paragraph.id]).source

    def compile_to(text, name):
        out = conftest.tmpdir("structure_preview_width") / name
        done = proc.run([str(project.typst_executable()), "compile", "--root", str(here.typst_root), "-", str(out)], input=text, capture_output=True, text=True, encoding="utf-8")
        assert done.returncode == 0, done.stderr[:1500]
        return PdfReader(io.BytesIO(out.read_bytes())).pages[0]

    narrow = compile_to(source, "snippet.pdf")
    assert abs(float(narrow.mediabox.width) - 17.6 / 2.54 * 72) < 1.5, float(narrow.mediabox.width)
    old_page = "#set page(height: auto, margin: (top: 1cm, bottom: 1cm), header: none, footer: none, numbering: none)"
    whole = compile_to(source.replace(structure_preview.page_line(here), old_page), "a4.pdf")
    assert abs(float(whole.mediabox.width) - 595.3) < 1.5, "the old snippet was a whole A4 page wide"
    lines = lambda page: [line for line in page.extract_text().splitlines() if line.strip()]   # noqa: E731
    assert lines(narrow) == lines(whole) and len(lines(narrow)) >= 3, (lines(narrow), lines(whole))
