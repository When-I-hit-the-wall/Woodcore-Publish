"""The force arrows on a connection's figure, drawn twice.

`connection_svg.py` draws them in Python for the window's preview; `lib/calc-engine.typ` draws them in Typst for the report, because only the report knows N, V and M (docs/decisions.md §13). The two are the one place in this project where the same thing is written in two languages, and `docs/domain/connections.md` (§3.3quinquies) says they are kept "rule for rule alike" -- four constants, five colours and the whole geometry of an arrow, in two files that no compiler ever compares.

This is the comparison. Both sides are handed the same figure, the same forces and the same shares, and their SVG must come out the same element for the same element. A constant changed on one side and not the other fails here instead of six months later, on a figure whose blue arrow no longer adds up to its yellow one.

⚠️ Skipped where `typst` is not on the path, or before the first export -- it needs a real connection record to draw.
"""

import json
import re
import subprocess

import conftest
from conftest import ROOT, Skip
from domains import connection, connection_svg

# Enough force to make every arrow non-zero: a normal force, a shear force and a moment, none of them along the same line.
TRIALS = (
    ("N, V and M together", 20.0, 16.0, 20.0),
    ("no moment", 12.0, 8.0, 0.0),
    ("moment alone", 0.0, 0.0, 7.5),
    ("a share too small to make out", 0.06 * 4, 0.31 * 4, 18.0),
)


def _a_connection():
    data = conftest.exported("connections.json")["connections"]
    if not data:
        raise Skip("no connection exported -- save one in Woodcore's polar moments tab")
    # the one with the most fasteners, which exercises the most arrows
    cid = max(data, key=lambda k: len(data[k]["fasteners"]))
    return cid, data[cid]


def _shares(record, n_total, v_total):
    n = record["vars"]["n"]["value"]
    import math
    a_n = math.radians(record["vars"]["alpha_N"]["value"])
    a_v = math.radians(record["vars"]["alpha_V"]["value"])
    return (
        (n_total / n * math.cos(a_n), n_total / n * math.sin(a_n)),
        (v_total / n * math.cos(a_v), v_total / n * math.sin(a_v)),
    )


def _typst_side(cid, n_total, v_total, m_total, what):
    """What lib/calc-engine.typ draws, read back out of Typst.

    The forces are computed once, in Python, and handed to Typst as JSON: this test compares the two *drawings*, not the two distributions (test_connection.py compares those). Typst hands the string back through `typst query` on a metadata element, which is the only way to get a plain string out of a document.
    """
    record = conftest.exported("connections.json")["connections"][cid]
    geometry = {
        "n": record["vars"]["n"]["value"],
        "I_p": record["vars"]["I_p"]["value"],
        "center": (record["vars"]["x_c"]["value"], record["vars"]["z_c"]["value"]),
        "points": [(f["x"], f["z"]) for f in record["fasteners"]],
    }
    directions = {"N": record["vars"]["alpha_N"]["value"], "V": record["vars"]["alpha_V"]["value"]}
    rows, _ = connection.fastener_forces(geometry, directions, n_total, v_total, m_total)
    n_share, v_share = _shares(record, n_total, v_total)

    python_svg = connection_svg.force_arrows(record["figure"], rows, n_share, v_share)
    python_note = connection_svg.share_note(record["figure"], rows, n_share, v_share)

    d = conftest.probe_dir("arrows")
    (d / "forces.json").write_text(json.dumps({
        "forces": [{"nr": r["nr"], "dx": r["dx"], "dz": r["dz"], "fx": r["fx"], "fz": r["fz"], "f": r["f"]} for r in rows],
        "n_share": list(n_share),
        "v_share": list(v_share),
    }), encoding="utf-8")
    probe = d / "probe.typ"
    probe.write_text(
        f'#import "{conftest.import_path(conftest.PROJECT.generated_dir / "lib" / "calc-engine.typ")}": *\n'
        f'#let c = json("{conftest.import_path(conftest.PROJECT.data_dir / "connections.json")}").connections.at("' + cid + '")\n'
        '#let given = json("forces.json")\n'
        '#context [\n'
        '  #metadata(fastener-arrows(c.figure, given.forces, given.n_share, given.v_share)) <arrows>\n'
        '  #metadata(share-note(c.figure, given.forces, given.n_share, given.v_share)) <note>\n'
        ']\n',
        encoding="utf-8",
    )
    typst_root = conftest.TYPST_ROOT  # the report's folder of the project the tests work on, which both paths above resolve under

    def query(tag):
        out = subprocess.run(
            ["typst", "query", "--root", str(typst_root), str(probe), f"<{tag}>", "--field", "value", "--one"],
            capture_output=True, text=True, encoding="utf-8",
        )
        assert out.returncode == 0, f"typst query <{tag}> failed for {what}:\n{out.stderr}"
        return json.loads(out.stdout)

    return python_svg, query("arrows"), python_note, query("note")


def _elements(svg):
    """The SVG broken into its elements, numbers rounded the way both sides round them, so a comparison reports the element that differs rather than a wall of text."""
    return [e.strip() for e in re.findall(r"<[^>]+>", svg)]


def test_typst_and_python_draw_the_same_arrows():
    if not conftest.have_typst():
        raise Skip("typst is not on the path")
    cid, _ = _a_connection()
    for what, n_total, v_total, m_total in TRIALS:
        py, ty, _, _ = _typst_side(cid, n_total, v_total, m_total, what)
        a, b = _elements(py), _elements(ty)
        assert len(a) == len(b), (
            f"{cid}, {what}: Python draws {len(a)} SVG elements, Typst draws {len(b)}.\n"
            f"  connection_svg.force_arrows and calc-engine.typ's fastener-arrows have "
            f"come apart -- compare ACTION_WIDTH / RESULTANT_WIDTH / SHARE_HEAD / "
            f"SHARE_SHOWN and the five colours on both sides."
        )
        for i, (x, y) in enumerate(zip(a, b)):
            assert x == y, (
                f"{cid}, {what}: SVG element {i} differs.\n"
                f"  Python : {x}\n"
                f"  Typst  : {y}"
            )


def test_typst_and_python_write_the_same_note():
    """The legend's last line, which names a share too small to read with its value."""
    if not conftest.have_typst():
        raise Skip("typst is not on the path")
    cid, _ = _a_connection()
    for what, n_total, v_total, m_total in TRIALS:
        _, _, py_note, ty_note = _typst_side(cid, n_total, v_total, m_total, what)
        assert py_note == ty_note, (
            f"{cid}, {what}: the legend's note differs.\n"
            f"  Python : {py_note!r}\n"
            f"  Typst  : {ty_note!r}"
        )


def test_the_four_shared_constants_agree():
    """The four numbers written on both sides, read out of each file rather than restated here.

    A text comparison, not an import: Typst cannot be imported into Python. It is coarse on purpose -- it catches the case that actually happens, someone editing one file and not the other.
    """
    typ = (ROOT / "lib" / "calc-engine.typ").read_text(encoding="utf-8")

    def typst_let(name):
        m = re.search(rf"^#let {re.escape(name)} = ([0-9.]+)\s*$", typ, re.M)
        assert m is not None, f"lib/calc-engine.typ no longer declares `{name}`"
        return float(m.group(1))

    pairs = (
        ("action-width", "ACTION_WIDTH", connection_svg.ACTION_WIDTH),
        ("share-shown", "SHARE_SHOWN", connection_svg.SHARE_SHOWN),
        ("share-head", "SHARE_HEAD", connection_svg.SHARE_HEAD),
    )
    for typst_name, py_name, py_value in pairs:
        assert typst_let(typst_name) == py_value, (
            f"{typst_name} in lib/calc-engine.typ is {typst_let(typst_name)}, "
            f"connection_svg.{py_name} is {py_value}"
        )

    # the resultant is written as a multiple of the action on both sides, so that it can never end up the thinner of the two
    m = re.search(r"^#let resultant-width = ([0-9.]+) \* action-width\s*$", typ, re.M)
    assert m is not None, "lib/calc-engine.typ no longer ties resultant-width to action-width"
    assert float(m.group(1)) * connection_svg.ACTION_WIDTH == connection_svg.RESULTANT_WIDTH, (
        f"the resultant is {m.group(1)}x the action in Typst and "
        f"{connection_svg.RESULTANT_WIDTH / connection_svg.ACTION_WIDTH}x in Python"
    )


def test_the_five_colours_agree():
    """The colours of the four arrows and the resultant's outline, on both sides."""
    typ = (ROOT / "lib" / "calc-engine.typ").read_text(encoding="utf-8")
    for name, value in (
        ("COLOR_F", connection_svg.COLOR_F),
        ("COLOR_F_EDGE", connection_svg.COLOR_F_EDGE),
        ("COLOR_M", connection_svg.COLOR_M),
        ("COLOR_N", connection_svg.COLOR_N),
        ("COLOR_V", connection_svg.COLOR_V),
    ):
        assert value.lower() in typ.lower(), (
            f"connection_svg.{name} is {value}, which lib/calc-engine.typ does not "
            f"mention -- the report would draw that arrow in another colour than "
            f"the window's preview"
        )
