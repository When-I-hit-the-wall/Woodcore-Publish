"""The force arrows on a connection's figure, drawn twice, and the forces they draw, worked out three times.

`connection_svg.py` draws them in Python for the window's preview; `lib/calc-engine-connections.typ` draws them in Typst for the report, through `#image-polar-moment`, because only the report knows N, V and M (docs/decisions.md §13; spec docs/requirements/completed/2026-10-22-image-polar-moment.md, ARCH-001). The two are the one place in this project where the same drawing is written in two languages, and `docs/domain/connections.md` (§3.3quinquies) says they are kept "rule for rule alike" -- four constants, five colours and the whole geometry of an arrow, in two files that no compiler ever compares.

This is the comparison. Both sides are handed the same figure, the same forces and the same shares, and their SVG must come out the same element for the same element. A constant changed on one side and not the other fails here instead of six months later, on a figure whose blue arrow no longer adds up to its yellow one.

The forces themselves are worked out by Python (`connection.fastener_forces`, the window), by the command (`polar-distribution`, for its arrows) and by the `#eq` lines of the file Woodcore writes for the connection (`F_x_i`, `F_z_i`, `F_i`, what the report prints): the last two tests hold the three equal (ARCH-005).

⚠️ Skipped where `typst` is not on the path, or before the first export -- it needs a real connection record to draw.
"""

TIER = "fast"  # tests/run_tests.py --fast

import json
import math
import re
import subprocess

import conftest
from conftest import ROOT, Skip
from domains import connection, connection_svg

# Enough force to make every arrow non-zero: a normal force, a shear force and a moment, none of them along the same line -- and two sets with no moment at all, the case of a group whose fasteners have no lever arm.
TRIALS = (
    ("N, V and M together", 20.0, 16.0, 20.0),
    ("no moment", 12.0, 8.0, 0.0),
    ("moment alone", 0.0, 0.0, 7.5),
    ("a share too small to make out", 0.06 * 4, 0.31 * 4, 18.0),
    ("normal force alone, no moment", 9.0, 0.0, 0.0),
)

# The tolerance on a force worked out twice: the same formula in two languages, in floating point.
TOLERANCE = 1e-9


def _a_connection():
    data = conftest.exported("connections.json")["connections"]
    if not data:
        raise Skip("no connection exported -- save one in Woodcore's polar moments tab")
    # the one with the most fasteners, which exercises the most arrows
    cid = max(data, key=lambda k: len(data[k]["fasteners"]))
    return cid, data[cid]


def _shares(record, n_total, v_total):
    n = record["vars"]["n"]["value"]
    a_n = math.radians(record["vars"]["alpha_N"]["value"])
    a_v = math.radians(record["vars"]["alpha_V"]["value"])
    return (
        (n_total / n * math.cos(a_n), n_total / n * math.sin(a_n)),
        (v_total / n * math.cos(a_v), v_total / n * math.sin(a_v)),
    )


def _python_forces(record, n_total, v_total, m_total):
    """What the window works out: `connection.fastener_forces` on the exported geometry."""
    geometry = {
        "n": record["vars"]["n"]["value"],
        "I_p": record["vars"]["I_p"]["value"],
        "center": (record["vars"]["x_c"]["value"], record["vars"]["z_c"]["value"]),
        "points": [(f["x"], f["z"]) for f in record["fasteners"]],
    }
    directions = {"N": record["vars"]["alpha_N"]["value"], "V": record["vars"]["alpha_V"]["value"]}
    rows, _ = connection.fastener_forces(geometry, directions, n_total, v_total, m_total)
    return rows


def _query(probe, tag, what):
    """One metadata element of a probe, read back out of Typst: `typst query` is the only way to get a plain value out of a document."""
    out = subprocess.run(
        ["typst", "query", "--root", str(conftest.TYPST_ROOT), str(probe), f"<{tag}>", "--field", "value", "--one"],
        capture_output=True, text=True, encoding="utf-8",
    )
    assert out.returncode == 0, f"typst query <{tag}> failed for {what}:\n{out.stderr}"
    return json.loads(out.stdout)


def _typst_side(cid, n_total, v_total, m_total, what):
    """What lib/calc-engine-connections.typ draws, read back out of Typst.

    The forces are computed once, in Python, and handed to Typst as JSON: this test compares the two *drawings*, not the distributions (the tests below compare those).
    """
    record = conftest.exported("connections.json")["connections"][cid]
    rows = _python_forces(record, n_total, v_total, m_total)
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
    return python_svg, _query(probe, "arrows", what), python_note, _query(probe, "note", what)


def _elements(svg):
    """The SVG broken into its elements, so a comparison reports the element that differs rather than a wall of text."""
    return [e.strip() for e in re.findall(r"<[^>]+>", svg)]


def _assert_same_forces(rows, forces, what):
    assert len(rows) == len(forces), f"{what}: Python works out {len(rows)} fasteners, Typst {len(forces)}"
    for r, t in zip(rows, forces):
        for key in ("fx", "fz", "f"):
            assert abs(r[key] - t[key]) <= TOLERANCE * max(1.0, abs(r[key])), (
                f"{what}: fastener {r['nr']}, {key}: Python {r[key]!r}, Typst {t[key]!r} -- "
                f"connection.fastener_forces and calc-engine-connections.typ's polar-distribution have come apart"
            )


def test_typst_and_python_draw_the_same_arrows():
    if not conftest.have_typst():
        raise Skip("typst is not on the path")
    cid, _ = _a_connection()
    for what, n_total, v_total, m_total in TRIALS:
        py, ty, _, _ = _typst_side(cid, n_total, v_total, m_total, what)
        a, b = _elements(py), _elements(ty)
        assert len(a) == len(b), (
            f"{cid}, {what}: Python draws {len(a)} SVG elements, Typst draws {len(b)}.\n"
            f"  connection_svg.force_arrows and calc-engine-connections.typ's fastener-arrows have "
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
    typ = conftest.engine_source()

    def typst_let(name):
        m = re.search(rf"^#let {re.escape(name)} = ([0-9.]+)\s*$", typ, re.M)
        assert m is not None, f"lib/calc-engine-connections.typ no longer declares `{name}`"
        return float(m.group(1))

    pairs = (
        ("action-width", "ACTION_WIDTH", connection_svg.ACTION_WIDTH),
        ("share-shown", "SHARE_SHOWN", connection_svg.SHARE_SHOWN),
        ("share-head", "SHARE_HEAD", connection_svg.SHARE_HEAD),
    )
    for typst_name, py_name, py_value in pairs:
        assert typst_let(typst_name) == py_value, (
            f"{typst_name} in lib/calc-engine-connections.typ is {typst_let(typst_name)}, "
            f"connection_svg.{py_name} is {py_value}"
        )

    # the resultant is written as a multiple of the action on both sides, so that it can never end up the thinner of the two
    m = re.search(r"^#let resultant-width = ([0-9.]+) \* action-width\s*$", typ, re.M)
    assert m is not None, "lib/calc-engine-connections.typ no longer ties resultant-width to action-width"
    assert float(m.group(1)) * connection_svg.ACTION_WIDTH == connection_svg.RESULTANT_WIDTH, (
        f"the resultant is {m.group(1)}x the action in Typst and "
        f"{connection_svg.RESULTANT_WIDTH / connection_svg.ACTION_WIDTH}x in Python"
    )


def test_the_five_colours_agree():
    """The colours of the four arrows and the resultant's outline, on both sides: each the same token of lib/figure-palette.json (v0.120, D5), which connection_svg reads and the report's arrows name."""
    from domains import svg_draw
    typ = conftest.engine_source()
    for name, token in (
        ("COLOR_F", "yellow"),
        ("COLOR_F_EDGE", "ochre-dark"),
        ("COLOR_M", "green"),
        ("COLOR_N", "blue"),
        ("COLOR_V", "red"),
    ):
        assert getattr(connection_svg, name) == svg_draw.colour(token), f"connection_svg.{name} is not the palette's {token}"
        assert f'figure-colour("{token}")' in typ, (
            f"lib/calc-engine-connections.typ draws no arrow in the palette's {token} -- the report would draw "
            f"connection_svg.{name}'s arrow in another colour than the window's preview"
        )


def test_the_command_distributes_the_forces_as_python_does():
    """ARCH-005: `#image-polar-moment` works out its arrows' forces itself (`polar-distribution`), and they are `connection.fastener_forces`'s, fastener for fastener -- read from the metadata the command leaves beside its drawing, for every set of TRIALS."""
    if not conftest.have_typst():
        raise Skip("typst is not on the path")
    cid, record = _a_connection()
    d = conftest.probe_dir("arrows_command")
    probe = d / "probe.typ"
    for what, n_total, v_total, m_total in TRIALS:
        probe.write_text(
            '#import "/000-Typst-Config/commands.typ": *\n'
            f'#image-polar-moment("{cid}", N: {n_total!r}, V: {v_total!r}, M: {m_total!r})\n',
            encoding="utf-8",
        )
        drawn = _query(probe, "woodcore-polar-arrows", what)
        _assert_same_forces(_python_forces(record, n_total, v_total, m_total), drawn["forces"], f"{cid}, {what}")
        n_share, v_share = _shares(record, n_total, v_total)
        for got, want in ((drawn["n-share"], n_share), (drawn["v-share"], v_share)):
            assert all(abs(g - w) <= TOLERANCE * max(1.0, abs(w)) for g, w in zip(got, want)), (what, got, want)


def test_the_file_s_lines_and_its_figure_give_the_same_forces():
    """ARCH-005, REQ-003: the file Woodcore writes for a connection draws its figure from the N, V and M written in it, and the arrows' forces are the file's own `F_x_i`, `F_z_i` and `F_i` -- and Python's. The example's VU-MP-1 reads N, V and M from N_Ed, V_Ed and M_Ed, declared here before the file is included."""
    if not conftest.have_typst():
        raise Skip("typst is not on the path")
    cid, record = _a_connection()
    source = (conftest.TYPST_ROOT / "Connections" / f"{cid}.typ")
    if not source.is_file() or "image-polar-moment" not in source.read_text(encoding="utf-8"):
        raise Skip(f"Connections/{cid}.typ draws no #image-polar-moment -- regenerate it")
    n_total, v_total, m_total = 7.5, 25.0, 6.6
    d = conftest.probe_dir("arrows_file")
    probe = d / "probe.typ"
    probe.write_text(
        '#import "/000-Typst-Config/commands.typ": *\n'
        f'#var("N_Ed", {n_total!r}, "kN")\n#var("V_Ed", {v_total!r}, "kN")\n#var("M_Ed", {m_total!r}, "kNm")\n'
        f'#include domain-file("connection", "{cid}")\n'
        f'#context [#metadata(var-registry.final().domains.at("{cid}").pairs().filter(p => p.at(0).starts-with("F_")).map(p => (p.at(0), get(p.at(1), "value"))).to-dict()) <file-forces>]\n',
        encoding="utf-8",
    )
    drawn = _query(probe, "woodcore-polar-arrows", "the file's figure")
    lines = _query(probe, "file-forces", "the file's lines")
    rows = _python_forces(record, n_total, v_total, m_total)
    _assert_same_forces(rows, drawn["forces"], f"{cid}, the file's figure")
    written = [{"fx": lines[f"F_x_{r['nr']}"], "fz": lines[f"F_z_{r['nr']}"], "f": lines[f"F_{r['nr']}"]} for r in rows]
    _assert_same_forces(rows, written, f"{cid}, the file's #eq lines")


def _drawn(name, body):
    """The metadata `#image-polar-moment` left beside its drawing, for a probe of `body`."""
    d = conftest.probe_dir(name)
    probe = d / "probe.typ"
    probe.write_text('#import "/000-Typst-Config/commands.typ": *\n' + body + "\n", encoding="utf-8")
    return _query(probe, "woodcore-polar-arrows", name), probe


def test_the_figure_carries_its_arrows_in_the_palette_s_colours_and_none_at_zero():
    """REQ-001: the arrows set in the figure are lines and polygon heads in the palette's yellow, green, blue and red, the resultants labelled F1, F2, …; with N = V = M = 0 no arrow is drawn."""
    from domains import svg_draw
    if not conftest.have_typst():
        raise Skip("typst is not on the path")
    cid, record = _a_connection()
    drawn, _ = _drawn("arrows_svg", f'#image-polar-moment("{cid}", N: 7.5, V: 25, M: 6.6)')
    svg = drawn["arrows"]
    assert "<line" in svg and "<polygon" in svg, svg[:400]
    for token in ("yellow", "green", "blue", "red"):
        assert svg_draw.colour(token).lower() in svg.lower(), (token, svg[:400])
    for i in range(1, len(record["fasteners"]) + 1):
        assert f">F{i}<" in svg, (i, svg[:400])
    drawn, _ = _drawn("arrows_zero", f'#image-polar-moment("{cid}", N: 0, V: 0, M: 0)')
    assert "<line" not in drawn["arrows"] and "<polygon" not in drawn["arrows"], drawn["arrows"][:400]


def test_a_force_named_draws_what_the_same_number_draws():
    """REQ-002: `N: "N"`, a variable declared above in kN, draws exactly what `N: 7.5` draws; `N: "nope"` and a variable N in N instead of kN are refused naming N."""
    import test_position_list as base
    if not conftest.have_typst():
        raise Skip("typst is not on the path")
    cid, _ = _a_connection()
    by_number, _ = _drawn("arrows_number", f'#image-polar-moment("{cid}", N: 7.5, V: 25, M: 6.6)')
    by_name, _ = _drawn("arrows_name", f'#domain("probe")[\n#var("N", 7.5, "kN")\n#var("V", 25, "kN")\n#var("M", 6.6, "kNm")\n#image-polar-moment("{cid}", N: "N", V: "V", M: "M")\n]')
    assert by_name == by_number
    here = base._project("arrows_refused")
    message = base._refusal(here, f'#image-polar-moment("{cid}", N: "nope")', "arrows_nope")
    assert "N: no variable named" in message and "nope" in message, message
    message = base._refusal(here, f'#var("N", 7500, "N")\n#image-polar-moment("{cid}", N: "N")', "arrows_unit")
    assert message.startswith("image-polar-moment: N is a variable in") and "kN" in message, message


def test_the_note_of_a_share_too_small_is_in_the_report_s_language():
    """UI-001: the legend's last line names a share too small to make out, with its value, in the report's language -- German and French."""
    import test_position_list as base
    if not conftest.have_typst():
        raise Skip("typst is not on the path")
    cid, _ = _a_connection()
    here = base._project("arrows_note")
    call = f'#image-polar-moment("{cid}", N: 7.5, V: 25, M: 6.6)'
    assert "Zu klein zum Erkennen: N/n = 1.88 kN" in base._text(here, call, "arrows_note_de", lang="de")
    assert "Trop petit pour être lu : N/n = 1.88 kN" in base._text(here, call, "arrows_note_fr", lang="fr")


def test_the_command_publishes_nothing():
    """ARCH-004: the command writes nothing into the registry -- an F_max declared before it keeps its value, and no F_i appears, whatever forces the figure is given."""
    if not conftest.have_typst():
        raise Skip("typst is not on the path")
    cid, _ = _a_connection()
    _, probe = _drawn("arrows_pure", f'#domain("probe")[\n#var("F_max", 1, "kN")\n#image-polar-moment("{cid}", N: 7.5, V: 25, M: 6.6)\n]\n'
                                     '#context [#metadata(var-registry.final().domains.at("probe").keys()) <keys> #metadata(get(var-registry.final().domains.at("probe").at("F_max"), "value")) <f-max>]')
    assert _query(probe, "f-max", "F_max") == 1
    assert _query(probe, "keys", "the registry") == ["F_max"]
