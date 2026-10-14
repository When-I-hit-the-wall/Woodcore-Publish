"""A print report of a FEM program, made up for the tests (docs/domain/annexes.md §3.3undevicies): what calc/domains/annex.py reads, with nothing of anybody's project in it.

It is built by pypdf alone -- no Typst, no RFEM -- so the annex tests run on any machine. It carries what the engineer's own RFEM export carries and nothing more: numbered headings, one bookmark per heading with the page and the height of the heading (`/FitBH`, as RFEM's «Visionneuse du rapport» writes them), and a framed box under each heading standing for its diagram. The same title is used twice («Charges de barre», once under each load case), which is what an anchor's path and its occurrence exist for.

`build(2)` is the next version of the same report: a chapter added in front, so every heading is renumbered, one page more, and the moments' diagram moved to another page and another height -- everything an excerpt has to survive.

`build(1, bookmarks=False)` is the same report printed through a PDF printer: the pages and no outline.
"""

import io

from pypdf import PdfWriter
from pypdf.generic import (
    ArrayObject, DecodedStreamObject, DictionaryObject, Fit, FloatObject, NameObject, NumberObject,
)

WIDTH, HEIGHT = 595.28, 841.89

# (title, down) of the headings of a page -- `down` in points from the top of the page, as the report is read.
# A tuple for a heading under another: the level is the number of dots in its chapter number.
VERSIONS = {
    1: [
        [("Couverture", 60)],
        [("1 Charges", 60), ("1.1 CC1 - Poids propre", 100), ("1.1.1 Charges de barre", 130),
         ("1.2 CC2 - Neige", 420), ("1.2.1 Charges de barre", 450)],
        [("2 Résultats", 60), ("2.1 CO1: Efforts internes N", 100), ("2.2 CO1: Efforts internes M_y", 440)],
    ],
    2: [
        [("Couverture", 60)],
        [("1 Objets de base", 60), ("1.1 Matériaux", 100)],
        [("2 Charges", 60), ("2.1 CC1 - Poids propre", 100), ("2.1.1 Charges de barre", 130),
         ("2.2 CC2 - Neige", 420), ("2.2.1 Charges de barre", 450)],
        [("3 Résultats", 60), ("3.1 CO1: Efforts internes N", 100)],
        [("3.2 CO1: Efforts internes M_y", 150)],
    ],
}

# How far below a heading's bookmark its diagram's box starts, and how tall it is.
BOX_GAP, BOX_HEIGHT = 30, 220


def _escape(text):
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _content(headings):
    """The page's drawing: each heading's text, and a framed box under it."""
    ops = []
    for title, down in headings:
        y = HEIGHT - down - 14
        ops.append(f"BT /F1 12 Tf 60 {y:.2f} Td ({_escape(title.encode('latin-1', 'replace').decode('latin-1'))}) Tj ET")
        if "Charges de barre" in title or "Efforts" in title or "Mat" in title:
            top = HEIGHT - down - BOX_GAP
            ops.append(f"0.2 0.4 0.8 RG 1 w 60 {top - BOX_HEIGHT:.2f} 470 {BOX_HEIGHT} re S")
            ops.append(f"BT /F1 9 Tf 70 {top - 20:.2f} Td (diagram of {_escape(title.split(' ', 1)[-1])}) Tj ET")
            if "Efforts" in title:
                # a two-span beam on three supports, and the diagram of its internal force under it: two sagging spans and a hogging peak over the middle support, as a moment diagram of the engineer's frame draws it
                beam = top - 80
                ops.append(f"0.85 0.45 0.1 RG 2 w 110 {beam:.2f} m 480 {beam:.2f} l S")
                for x in (110, 295, 480):
                    ops.append(f"0.1 0.6 0.2 rg {x - 8} {beam - 14:.2f} m {x + 8} {beam - 14:.2f} l {x} {beam:.2f} l f")
                ops.append(f"0.9 0.4 0.4 rg 0.6 0.2 0.2 RG 0.8 w 110 {beam:.2f} m 150 {beam - 90:.2f} 255 {beam - 90:.2f} 295 {beam:.2f} c "
                           f"335 {beam - 90:.2f} 440 {beam - 90:.2f} 480 {beam:.2f} c h B")
                ops.append(f"0.4 0.55 0.8 rg 270 {beam:.2f} m 295 {beam + 45:.2f} l 320 {beam:.2f} l h f")
                ops.append(f"0 0 0 rg BT /F1 8 Tf 185 {beam - 75:.2f} Td (708.32) Tj ET")
                ops.append(f"BT /F1 8 Tf 282 {beam + 50:.2f} Td (-979.26) Tj ET")
    return "\n".join(ops).encode("latin-1")


def build(version=1, bookmarks=True):
    """The bytes of the report's `version`: 1 or 2."""
    writer = PdfWriter()
    font = DictionaryObject({
        NameObject("/Type"): NameObject("/Font"),
        NameObject("/Subtype"): NameObject("/Type1"),
        NameObject("/BaseFont"): NameObject("/Helvetica"),
        NameObject("/Encoding"): NameObject("/WinAnsiEncoding"),
    })
    font_ref = writer._add_object(font)
    pages = VERSIONS[version]
    for headings in pages:
        page = writer.add_blank_page(WIDTH, HEIGHT)
        stream = DecodedStreamObject()
        stream.set_data(_content(headings))
        page[NameObject("/Contents")] = writer._add_object(stream)
        page[NameObject("/Resources")] = DictionaryObject({
            NameObject("/Font"): DictionaryObject({NameObject("/F1"): font_ref}),
        })
    if bookmarks:
        parents = {}
        for number, headings in enumerate(pages):
            for title, down in headings:
                chapter = title.split(" ", 1)[0]
                level = chapter.count(".") if chapter[0].isdigit() else 0
                parent = parents.get(level - 1) if level else None
                item = writer.add_outline_item(title, number, parent=parent, fit=Fit.fit_box_horizontally(HEIGHT - down))
                parents[level] = item
                for deeper in [k for k in parents if k > level]:
                    del parents[deeper]
    buffer = io.BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


def write(path, version=1, bookmarks=True):
    from pathlib import Path
    Path(path).write_bytes(build(version, bookmarks))
    return Path(path)


def build_frames():
    """A page of frames drawn every way a print report draws them, for the frames found in a page (issue #16, annex.find_rects): a rectangle under a scaled and moved matrix (`cm` inside `q … Q`), a path of four sides closed by `h`, a filled rectangle inside a form called with its own `/Matrix`, a form that calls itself -- never followed twice --, a clip (`re W n`) that is no frame, a curve, and a rectangle too small to offer. One page of A4, no bookmark; the bytes of the existing reports are untouched."""
    from pypdf.generic import StreamObject
    writer = PdfWriter()
    page = writer.add_blank_page(WIDTH, HEIGHT)
    form = DecodedStreamObject()
    form.set_data(b"0 0 120 80 re f")
    form.update({NameObject("/Type"): NameObject("/XObject"), NameObject("/Subtype"): NameObject("/Form"),
                 NameObject("/BBox"): ArrayObject([NumberObject(0), NumberObject(0), NumberObject(200), NumberObject(200)]),
                 NameObject("/Matrix"): ArrayObject([NumberObject(1), NumberObject(0), NumberObject(0), NumberObject(1), NumberObject(100), NumberObject(500)])})
    form_ref = writer._add_object(form)
    loop = DecodedStreamObject()
    loop.set_data(b"q 0.5 0 0 0.5 0 0 cm /Fm2 Do Q 400 600 60 40 re S")
    loop.update({NameObject("/Type"): NameObject("/XObject"), NameObject("/Subtype"): NameObject("/Form"),
                 NameObject("/BBox"): ArrayObject([NumberObject(0), NumberObject(0), NumberObject(600), NumberObject(800)])})
    loop_ref = writer._add_object(loop)
    loop[NameObject("/Resources")] = DictionaryObject({NameObject("/XObject"): DictionaryObject({NameObject("/Fm2"): loop_ref})})
    stream = DecodedStreamObject()
    stream.set_data(b"\n".join([
        b"30 30 400 400 re W n",                                 # a clip, ended unpainted: no frame
        b"q 2 0 0 2 10 10 cm 20 20 50 30 re S Q",                 # (50, 50)-(150, 110) in the page's space
        b"300 300 m 380 300 l 380 360 l 300 360 l h S",          # four sides closed by h
        b"q /Fm1 Do Q",                                           # (100, 500)-(220, 580), filled inside a form
        b"/Fm2 Do",                                               # a form that calls itself: (400, 600)-(460, 640) once
        b"200 200 m 250 260 260 300 300 200 c h S",              # a curve: no frame
        b"500 100 5 5 re S",                                      # too small to offer
    ]))
    page[NameObject("/Contents")] = writer._add_object(stream)
    page[NameObject("/Resources")] = DictionaryObject({NameObject("/XObject"): DictionaryObject({NameObject("/Fm1"): form_ref, NameObject("/Fm2"): loop_ref})})
    buffer = io.BytesIO()
    writer.write(buffer)
    return buffer.getvalue()
