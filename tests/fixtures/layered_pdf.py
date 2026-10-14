"""A small PDF with optional content, written by pypdf, for the plan documents' tests (calc/domains/plan_documents.py) -- so they run on a clone with no architect's plan on it.

One page of 300 × 100 pt, and on it, in PDF coordinates (y up):

* a grey square at (0, 0)-(10, 10), outside any group: always drawn;
* a red square (20, 20)-(60, 60) in a marked-content section of the group «Dims», which the file hides by default;
* a green square (80, 20)-(120, 60) in a section of «Walls»;
* a form XObject whose own /OC is «Furniture», a blue square drawn at (180, 20)-(200, 40);
* a form XObject with no /OC drawn at (220, 20), holding a magenta square (220, 20)-(240, 40) in a section of «Dims» and a black one (245, 20)-(255, 30) outside it;
* a cyan square (260, 20)-(280, 40) in a section whose membership dictionary is AllOn of «Walls» and «Furniture»;
* and last a section of «Dims» that only moves the coordinates up 30 pt (`1 0 0 1 0 30 cm`) and paints nothing, then an orange square drawn at (140, 20)-(150, 30) -- which, PDF 2.0 8.11.3.2 keeping a hidden section's change of the graphics state, lands at (140, 50)-(150, 60) whatever «Dims» is.

`COLOURS` names each square's colour and the point of the page (PDF coordinates) it is checked at.
"""

from pypdf import PdfWriter
from pypdf.generic import ArrayObject, DecodedStreamObject, DictionaryObject, FloatObject, NameObject, NumberObject, TextStringObject

WIDTH, HEIGHT = 300, 100
GROUPS = ("Dims", "Walls", "Furniture")

# name: (point in PDF coordinates, its colour as r, g, b)
COLOURS = {
    "grey": ((5, 5), (128, 128, 128)),
    "red": ((40, 40), (255, 0, 0)),
    "green": ((100, 40), (0, 255, 0)),
    "blue": ((190, 30), (0, 0, 255)),
    "magenta": ((230, 30), (255, 0, 255)),
    "black": ((250, 25), (0, 0, 0)),
    "cyan": ((270, 30), (0, 255, 255)),
    "orange": ((145, 55), (255, 128, 0)),
}

CONTENT = b"""q 0.5 g 0 0 10 10 re f Q
/OC /oc1 BDC 1 0 0 rg 20 20 40 40 re f EMC
/OC /oc2 BDC 0 1 0 rg 80 20 40 40 re f EMC
q 1 0 0 1 180 20 cm /Fx Do Q
q 1 0 0 1 220 20 cm /Fy Do Q
/OC /oc3 BDC 0 1 1 rg 260 20 20 20 re f EMC
/OC /oc1 BDC 1 0 0 1 0 30 cm EMC
1 0.5 0 rg 140 20 10 10 re f
"""


def _stream(writer, data, **entries):
    stream = DecodedStreamObject()
    for key, value in entries.items():
        stream[NameObject(key)] = value
    stream.set_data(data)
    return writer._add_object(stream)


def write(path, off=("Dims",), pages=1):
    """Writes the PDF to `path`: `pages` pages alike, the groups named in `off` hidden by default. Returns the path."""
    writer = PdfWriter()
    groups = {name: writer._add_object(DictionaryObject({NameObject("/Type"): NameObject("/OCG"), NameObject("/Name"): TextStringObject(name)}))
              for name in GROUPS}
    membership = writer._add_object(DictionaryObject({
        NameObject("/Type"): NameObject("/OCMD"),
        NameObject("/OCGs"): ArrayObject([groups["Walls"], groups["Furniture"]]),
        NameObject("/P"): NameObject("/AllOn"),
    }))
    box = ArrayObject([NumberObject(0), NumberObject(0), NumberObject(40), NumberObject(40)])
    furniture = _stream(writer, b"0 0 1 rg 0 0 20 20 re f", **{"/Type": NameObject("/XObject"), "/Subtype": NameObject("/Form"), "/BBox": box, "/OC": groups["Furniture"]})
    inner = DictionaryObject({NameObject("/Properties"): DictionaryObject({NameObject("/f1"): groups["Dims"]})})
    mixed = _stream(writer, b"/OC /f1 BDC 1 0 1 rg 0 0 20 20 re f EMC 0 g 25 0 10 10 re f",
                    **{"/Type": NameObject("/XObject"), "/Subtype": NameObject("/Form"), "/BBox": box, "/Resources": inner})
    for _ in range(pages):
        page = writer.add_blank_page(WIDTH, HEIGHT)
        page[NameObject("/Resources")] = DictionaryObject({
            NameObject("/Properties"): DictionaryObject({NameObject("/oc1"): groups["Dims"], NameObject("/oc2"): groups["Walls"], NameObject("/oc3"): membership}),
            NameObject("/XObject"): DictionaryObject({NameObject("/Fx"): furniture, NameObject("/Fy"): mixed}),
        })
        page[NameObject("/Contents")] = _stream(writer, CONTENT)
    writer._root_object[NameObject("/OCProperties")] = DictionaryObject({
        NameObject("/OCGs"): ArrayObject(list(groups.values())),
        NameObject("/D"): DictionaryObject({
            NameObject("/Order"): ArrayObject(list(groups.values())),
            NameObject("/OFF"): ArrayObject([groups[name] for name in off]),
        }),
    })
    with open(path, "wb") as f:
        writer.write(f)
    return path


def render(pdf, page=0, scale=2.0):
    """The page as QtPdf (PDFium, the window's renderer) draws it: a QImage at `scale` pixels per point."""
    import os
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtCore import QSize
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtPdf import QPdfDocument
    QGuiApplication.instance() or QGuiApplication([])
    document = QPdfDocument()
    document.load(str(pdf))
    size = document.pagePointSize(page)
    image = document.render(page, QSize(round(size.width() * scale), round(size.height() * scale)))
    document.close()
    return image, (size.width(), size.height())


def colour_at(image, point, height=HEIGHT, scale=2.0):
    """The colour of the rendered page at a point given in PDF coordinates (y up), as (r, g, b), over white -- QtPdf leaves the page's ground transparent."""
    from PySide6.QtGui import QColor
    x, y = point
    colour = QColor.fromRgba(image.pixel(round(x * scale), round((height - y) * scale)))
    a = colour.alpha() / 255
    return tuple(round(c * a + 255 * (1 - a)) for c in (colour.red(), colour.green(), colour.blue()))


def shows(image, name, scale=2.0):
    """Whether the square `name` is drawn in its colour: each channel within 40 of it."""
    point, rgb = COLOURS[name]
    got = colour_at(image, point, scale=scale)
    return all(abs(a - b) <= 40 for a, b in zip(got, rgb))
