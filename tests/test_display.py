"""What lib/calc-engine.typ puts on the page, held against the engineer's v0.87 requests: a minus sign and not a hyphen, a point's halo over the pieces of a schema, a position without a dimension, the two lines of a formula that wraps -- and, after them, a formula too wide for its row stacked at its signs rather than run into the citation column.

Each test compiles a probe with Typst. Where a probe needs data the example project does not carry -- a calculation ending on a negative number, a position with no dimension, a schema export of today's schema_svg -- it works on a copy of the example project's report folder and generated folder of its own (`_root`), so nothing the rest of the suite reads is changed under it.
"""

import base64
import json
import re
import shutil
import subprocess
import unicodedata

import conftest
from conftest import Skip

PROJECT = conftest.PROJECT
MINUS = "−"
# a hyphen standing where a number's sign stands: at the start, or after a space, a bracket, `=`, `:`, `;`, `,` or `/`, and right before a digit (calc-engine.typ's `sign-hyphen`)
SIGN_HYPHEN = re.compile(r"(^|[\s(\[=:;,/])-\d")
# a colour no drawing of the project uses but the halo: schema-halo's own
HALO = "#ffd34d"


def _guard():
    if not conftest.have_typst():
        raise Skip("typst is not on the path")


def _root(name):
    """A copy of the example project's report folder -- its config.typ and commands.typ -- and of its generated folder (the engine and the export), laid out as the project lays them out: a Typst root of this test's own."""
    d = conftest.tmpdir(name)
    for f in ("commands.typ", "config.typ"):
        shutil.copyfile(PROJECT.typst_root / f, d / f)
    relative = PROJECT.generated_dir.relative_to(PROJECT.typst_root)
    shutil.copytree(PROJECT.generated_dir, d / relative, copy_function=shutil.copyfile, ignore=shutil.ignore_patterns("out", "docs"))
    return d, d / relative / "data"


def _compile(root, body, name, fmt="pdf"):
    """Compiles `body` under `root` with the report's own setup; returns (returncode, stderr, output path)."""
    _guard()
    d = root / ".probe" / name
    d.mkdir(parents=True, exist_ok=True)
    probe = d / "probe.typ"
    probe.write_text('#import "/config.typ": conf\n#import "/commands.typ": *\n#show: conf\n' + body + "\n", encoding="utf-8")
    out = d / f"probe.{fmt}"
    run = subprocess.run(["typst", "compile", "--root", str(root), "--format", fmt, str(probe), str(out)],
                         capture_output=True, text=True, encoding="utf-8", errors="replace")
    return run.returncode, run.stderr, out


def _text(root, body, name):
    code, err, out = _compile(root, body, name)
    assert code == 0, err
    from pypdf import PdfReader
    # NFKC: math's bold and italic letters read as letters, a no-break space as a space -- a minus sign is left as it is
    return unicodedata.normalize("NFKC", "\n".join(page.extract_text() for page in PdfReader(str(out)).pages))


def _query(root, body, name):
    """The value `body` puts in `metadata(...) <out>`."""
    _guard()
    d = root / ".probe" / name
    d.mkdir(parents=True, exist_ok=True)
    probe = d / "probe.typ"
    probe.write_text('#import "/config.typ": conf\n#import "/commands.typ": *\n#show: conf\n' + body + "\n", encoding="utf-8")
    run = subprocess.run(["typst", "query", "--root", str(root), str(probe), "<out>", "--field", "value", "--one"],
                         capture_output=True, text=True, encoding="utf-8", errors="replace")
    assert run.returncode == 0, run.stderr
    return json.loads(run.stdout)


def _embedded_svgs(svg_file):
    """The SVG images a page compiled to SVG carries, decoded: the figure show-schema set, as it was handed to Typst."""
    text = svg_file.read_text(encoding="utf-8")
    return [base64.b64decode(b).decode("utf-8", "replace") for b in re.findall(r"data:image/svg\+xml;base64,([A-Za-z0-9+/=]+)", text)]


# --- a negative number is printed with a minus sign -------------------------------------

def _wind_instance():
    doms = json.loads((PROJECT.data_dir / "calculations.json").read_text(encoding="utf-8"))["domains"]
    for instance, record in doms.get("wind-load", {}).get("instances", {}).items():
        for name, v in record["vars"].items():
            if isinstance(v["value"], (int, float)) and v["value"] < 0:
                return instance, name
    raise Skip("no wind-load instance of the export carries a negative value")


def test_a_negative_number_prints_a_minus_sign_and_never_a_hyphen():
    """«Les nombres négatifs s'impriment avec un trait d'union au lieu d'un signe moins» (the engineer, v0.87). `fmt-decimals` writes a hyphen, and every number calc-engine printed as text went through it: a wind suction `q_k = -0.266 kN/m²`, every cell of the local wind forces, a fastener's position `-60` in a polar moment's table, a choice `-200 m` out of the workbook's Dropdowns sheet.

    Planted back (fmt-number without `signed-text`), the wind var and the table cells come out with hyphens and this fails naming the lines.
    """
    instance, name = _wind_instance()
    connections = json.loads((PROJECT.data_dir / "connections.json").read_text(encoding="utf-8"))["connections"]
    polar = next(iter(connections), None)
    body = (f'#show-input("wind-load", "{instance}", "{name}")\n'
            f'#fmt-number(-0.25, "kN") #fmt-value(var-of("wind-load", "{instance}", "{name}"))\n'
            f'#show-calc("wind-load", "{instance}", level: 2)\n'
            '#show-input("snow-load", "SL", "korrektur", level: 2)\n'
            + (f'#show-polar-moment("{polar}", N: -7.5, V: 25, M: -6.6, level: 3)\n' if polar else ""))
    text = _text(conftest.TYPST_ROOT, body, "display_minus")
    hyphens = [line for line in text.splitlines() if SIGN_HYPHEN.search(line)]
    assert not hyphens, "a negative number printed with a hyphen:\n" + "\n".join(hyphens)
    assert MINUS + "0.25 kN" in text, text[:600]
    assert MINUS + "200 m" in text, "the Dropdowns choice «-200 m» kept its hyphen"


def test_a_negative_answer_in_a_numbers_line_prints_a_minus_sign():
    """The answer closing a numbers line is quoted text inside math (`value-text`), where a hyphen stays a hyphen: `c = (-3) + 1 = -2 kN` printed the operand with math's own minus and the answer with a hyphen. No calculation of the example ends on a negative number, so one is planted in a copy of the export."""
    root, data = _root("display_minus_answer")
    calcs = json.loads((data / "calculations.json").read_text(encoding="utf-8"))
    domain = next(iter(calcs["domains"]))
    var = lambda value, symbol, level: {"value": value, "unit": "kN", "symbol": symbol, "label": symbol, "level": level,
                                        "norm": "SIA 261", "norm_ref": "1", "source": "python:test"}
    calcs["domains"][domain]["instances"]["PROBE"] = {
        "results": ["c"],
        "vars": {"a": var(-3, "a", 3), "b": var(1, "b", 3), "c": var(-2, "c", 1)},
        "steps": [{"name": "Summe", "level": 1, "result": "c", "uses": ["a", "b"], "formula": "c = a + b", "norm": "SIA 261", "norm_ref": "1"}],
        "checks": [],
    }
    (data / "calculations.json").write_text(json.dumps(calcs, ensure_ascii=False), encoding="utf-8")
    text = re.sub(r"\s+", " ", _text(root, f'#show-calc("{domain}", "PROBE", level: 3)', "answer"))
    assert MINUS + "2 kN" in text, text
    assert not SIGN_HYPHEN.search(text), text


def test_the_primitives_that_are_parsed_again_keep_their_hyphen():
    """`fmt-decimals` builds math source and SVG coordinates, which are read back -- an SVG parser does not read U+2212 -- so the minus is set where a number becomes text and not there. A hyphen inside a word, or between two digits, is not a sign."""
    root = conftest.TYPST_ROOT
    assert _query(root, '#metadata(fmt-decimals(-0.25, 3)) <out>', "display_fmt_decimals") == "-0.25"
    assert _query(root, '#metadata(signed-text("-0.25")) <out>', "display_signed") == MINUS + "0.25"
    words = "EL+AL-Dach1, Holz-Holz, EN 1995-1-1, Δh = -200 m, (-60)"
    assert _query(root, f'#metadata(prose-minus("{words}")) <out>', "display_prose") == \
        "EL+AL-Dach1, Holz-Holz, EN 1995-1-1, Δh = " + MINUS + "200 m, (" + MINUS + "60)"


# --- a position without a dimension ----------------------------------------------------

def test_a_position_without_a_dimension_prints_neither_it_nor_its_unit():
    """Positionen.xlsx's `dimension` and `units` are facultative since v0.87 (a support, an opening). `show-position` printed `pos.dimension + " " + pos.units`, so a position with no dimension and «mm» in its units column read «T901: Träger, Fichte C24,  mm», its unit standing in for the dimension. Two positions are planted in a copy of the export: one with a unit and no dimension, one with neither, and a record written before the two keys could be empty -- with no `dimension` key at all -- is read as one with none. Since v0.94 the line is `#member`'s at level 1 -- `show-position` is gone -- and the positions have no section, which is what a blank dimension gives."""
    root, data = _root("display_position")
    base = json.loads((data / "positions" / "T001.json").read_text(encoding="utf-8"))
    planted = {"T901": {"dimension": "", "units": "mm"}, "T902": {"dimension": "", "units": ""}, "T903": {}}
    for pid, fields in planted.items():
        record = dict(base, position=pid, section=None, section_type="", **fields)
        if not fields:
            record.pop("dimension")
            record.pop("units")
        (data / "positions" / f"{pid}.json").write_text(json.dumps(record, ensure_ascii=False), encoding="utf-8")
    index = json.loads((data / "positions-index.json").read_text(encoding="utf-8"))
    index["positions"] += list(planted)
    (data / "positions-index.json").write_text(json.dumps(index), encoding="utf-8")
    body = "\n\n".join(f'#member("{pid}", level: 1)' for pid in planted) + '\n\n#calc-block("T901", axes: "Achse 1")[Body]'
    text = _text(root, body, "positions")
    lines = [line.strip() for line in text.splitlines() if line.strip().startswith("T90")]
    assert len(lines) == 4, text
    for line in lines:
        assert "mm" not in line, f"a unit printed without its dimension: {line!r}"
        assert ", ," not in line and not line.rstrip().endswith(",") and ",  " not in line, f"a dangling separator: {line!r}"
        assert "Feuchteklasse" in line, line
    assert "(Achse 1)" in lines[-1], lines[-1]
    # the dimension, where there is one, is still printed with its unit
    assert re.sub(r"\s+", " ", _text(root, '#member("T001", level: 1)', "position_t001")).count(f"{base['dimension']} {base['units']}") == 1


def test_a_position_s_line_prints_its_section_as_the_export_read_it():
    """v0.94: the line reads the `section` the export wrote -- «Ø 200 mm», «20/30/20 mm (70 mm)», «ROR 101.6×10» -- and nothing reads the dimension text again; a record exported before, with no `section`, is printed as it was, its dimension and its unit. S002 of the example project is the engineer's steel column."""
    from domains import section
    root, data = _root("display_sections")
    base = json.loads((data / "positions" / "T001.json").read_text(encoding="utf-8"))
    planted = {
        "S903": {"type": "Stütze", "section_type": "cir", "dimension": "200", "section": section.parse("cir", "200", "mm")},
        "D904": {"type": "Decke", "section_type": "clt", "dimension": "20/30/20", "section": section.parse("clt", "20/30/20", "mm")},
        "T905": {"dimension": "12/24", "units": "cm"},
    }
    for pid, fields in planted.items():
        record = dict(base, position=pid, **fields)
        if pid == "T905":
            record.pop("section")
            record.pop("section_type")
        (data / "positions" / f"{pid}.json").write_text(json.dumps(record, ensure_ascii=False), encoding="utf-8")
    index = json.loads((data / "positions-index.json").read_text(encoding="utf-8"))
    index["positions"] += list(planted)
    (data / "positions-index.json").write_text(json.dumps(index), encoding="utf-8")
    text = re.sub(r"\s+", " ", _text(root, "\n\n".join(f'#member("{pid}", level: 1)' for pid in ("S002", *planted)), "sections"))
    for want in ("S002: Stütze, Stahl S355, ROR 101.6×10, Feuchteklasse 2", "S903: Stütze, Fichte C24, Ø 200 mm", "D904: Decke, Fichte C24, 20/30/20 mm (70 mm)", "T905: Träger, Fichte C24, 12/24 cm"):
        assert want in text, (want, text)


# --- a point's halo over the pieces of a schema -----------------------------------------

def _probe_schema(details):
    """A small detail: two crossing pieces, two dowel markers, a centre and a point -- written as a source into `details`."""
    from domains import schema
    source = schema.new_source("T_HALO")
    source["elements"] = [
        {"id": "E1", "kind": "linear", "points": [[0, 0], [300, 0]], "position": "T001", "h": 140},
        {"id": "E2", "kind": "linear", "points": [[150, -150], [150, 150]], "h": 80},
    ]
    source["connectors"] = [{"id": "C1", "kind": "Stabdübel", "x": 110, "z": 0}, {"id": "C2", "kind": "Stabdübel", "x": 190, "z": 0}]
    source["aids"] = [{"id": "A1", "kind": "centre", "x": 150, "z": 30}, {"id": "A2", "kind": "point", "x": 150, "z": -30}]
    (details / "T_HALO.json").write_text(json.dumps(source, ensure_ascii=False), encoding="utf-8")


def _exported_root(name):
    """A root whose schemas are exported afresh by today's calc/domains/schema.py -- the example project's own and the probe detail above."""
    from domains import schema
    root, data = _root(name)
    details = conftest.tmpdir(name + "_details")
    for f in PROJECT.details_dir.glob("*.json"):
        shutil.copyfile(f, details / f.name)
    _probe_schema(details)
    positions = {f.stem: json.loads(f.read_text(encoding="utf-8")) for f in (data / "positions").glob("*.json")}
    schema.export(details, data, positions)
    return root, data


def _figure(root, call, name):
    code, err, out = _compile(root, call, name, fmt="svg")
    assert code == 0, err
    figures = [s for s in _embedded_svgs(out) if "<polygon" in s]
    assert figures, "no schema figure in the page"
    return figures[0]


def _halo_position(svg):
    """Where the halo stands among the drawing: after how many of the **pieces'** polygons, and how many there are.

    ⚠️ The pieces are named by their own fill opacity (`schema_svg.ELEMENT_OPACITY`) and not by «every `<polygon`»: since v0.99 a text is set over its own box, which is a polygon too, and a marker's box is drawn **with the marker** -- after the halo, which is exactly where the marker and its id belong. The proxy said «piece» and meant «polygon»; what it was written to hold, a halo that shows over a filled piece, is unchanged.
    """
    from domains import schema_svg
    at = svg.index(HALO)
    pieces = [m.start() for m in re.finditer(re.escape("<polygon") + r'[^>]*fill-opacity="'
                                             + re.escape(str(schema_svg.ELEMENT_OPACITY)) + '"', svg)]
    return sum(1 for start in pieces if start < at), len(pieces)


def test_a_point_s_halo_is_drawn_over_the_pieces():
    """«La mise en évidence d'un point dans show-schema est invisible, cachée sous les pièces. Un point doit être affiché au-dessus de tout» (the engineer, v0.87). A point's halo went in at `<!-- highlight -->`, before the pieces, which are filled at three quarters opacity: a halo under a pin inside a beam did not show. schema_svg.body writes `<!-- highlight-points -->` after the pieces and before the markers and the named points, and a marker's or a point's ring goes there; a piece's halo stays under the pieces.

    Since v0.99 it also holds the other side of the same order: a **marker's own label** is set over a white box, and that box is drawn with the marker, so it stands **after** the ring -- a ring drawn over a marker's id would hide the very number it is there to point at.
    """
    root, data = _exported_root("display_halo")
    svg_file = (data / "schemas" / "T_HALO-de.svg").read_text(encoding="utf-8")
    assert "<!-- highlight-points -->" in svg_file, "today's schema export carries no <!-- highlight-points --> marker"
    for ident in ("C1", "A1", "A2"):
        svg = _figure(root, f'#show-schema("T_HALO", highlight: "{ident}")', "halo_" + ident)
        before, total = _halo_position(svg)
        assert before == total, f"{ident}'s halo stands under {total - before} of the {total} pieces"
        assert "<circle" in svg[svg.index(HALO):] and 'fill="none"' in svg[svg.index(HALO) - 200:svg.index(HALO) + 80], f"{ident}'s halo is not a ring"
    # the marker is drawn on its halo, not under it: the halo's own element names C1's place before its colour, the marker's after
    svg = _figure(root, '#show-schema("T_HALO", highlight: "C1")', "halo_c1_marker")
    assert 'cx="110"' in svg[svg.index(HALO):], "C1's marker is drawn under its halo"
    # and so is the box its id is set over (v0.99): a ring over a marker's number would hide what it points at
    from domains import schema_svg
    grounds = [m.start() for m in re.finditer(re.escape(f'fill-opacity="{schema_svg.LABEL_GROUND_OPACITY}"'), svg)]
    assert grounds, "no text is set over a box"
    assert any(start > svg.index(HALO) for start in grounds), "a marker's own label is drawn under the halo"
    # a piece keeps its halo under the pieces
    svg = _figure(root, '#show-schema("T_HALO", highlight: "E2")', "halo_e2")
    assert _halo_position(svg)[0] == 0, "a piece's halo left its place under the pieces"


def test_a_point_s_halo_falls_back_to_the_old_marker_on_an_older_export():
    """A figure exported before v0.87 carries no `<!-- highlight-points -->`: every halo then goes where it always did, and the figure still compiles with its highlight -- under the pieces, as it was."""
    root, data = _exported_root("display_halo_old")
    for f in (data / "schemas").glob("T_HALO-*.svg"):
        f.write_text(f.read_text(encoding="utf-8").replace("<!-- highlight-points -->\n", ""), encoding="utf-8")
    svg = _figure(root, '#show-schema("T_HALO", highlight: ("A2", "E1"))', "halo_old")
    assert "highlight-points" not in svg
    assert svg.count(HALO) == 2 and svg.rindex(HALO) < svg.index("<polygon"), "an older export's halos did not go at <!-- highlight -->"


# --- the two lines of a formula that wraps ---------------------------------------------

LONG = '$B_v = ((q dot L) dot L/2 + Q_1 dot l_1 + Q_2 dot (l_1 + l_2))/L = ((2.5 "kN/m" dot 4.2 "m") dot (4.2 "m")/2 + 12 "kN" dot 1.3 "m")/(4.2 "m") = 13.536 "kN"$'
SHORT = '$C_v = (q dot L)/2 + Q_1/2 = 11.25 "kN"$'
ROOTS = '$t_(1,1) = 0.44 dot (sqrt(beta_f\\/(1+beta_f)) + 1) dot sqrt(f_(u,k)\\/f_(h,1,k)) dot d^0.8 = 0.44 dot (sqrt(1\\/(1+1)) + 1) dot sqrt(510\\/25.83) dot 10^0.8 = 21.059 "mm"$'


def test_a_wrapped_formula_with_fractions_keeps_its_lines_apart():
    """«J'ai ajouté `show math.frac: it => $display(it)$` à config.typ. Maintenant, lorsqu'un calcul est sur 2 lignes, il n'y a plus assez d'espace entre les deux lignes» (the engineer, v0.87). A line of inline math is not measured to its ink, so a built-up fraction ran into the line above or below it whatever the leading: measured at 144 ppi, 0 to 4 px of white where two rows are 11 to 16 px apart. A row taller than a line of roots and indices that wraps is now set with its lines measured to their ink; one that does not wrap, and one of roots and indices, is laid out exactly as before -- which is what the engineer asked of single-line rows."""
    root = conftest.TYPST_ROOT
    width = "9cm"

    def heights(formula, name):
        return _query(root, f'#let f = {formula}\n#context [#metadata((measure(block(width: {width}, f)).height / 1pt, measure(block(width: {width}, row-cell(f))).height / 1pt, measure(f).height / 1pt)) <out>]', name)

    plain, spaced, line = heights(LONG, "display_wrap_long")
    assert plain > line + 5, f"the probe formula does not wrap at {width}: {plain} pt against one line's {line} pt"
    assert spaced > plain + 5, f"a wrapped formula with fractions is set as before: {spaced} pt against {plain} pt"
    plain, spaced, _ = heights(SHORT, "display_wrap_short")
    assert abs(spaced - plain) < 0.01, f"a single-line row with fractions moved: {spaced} pt against {plain} pt"
    plain, spaced, line = heights(ROOTS, "display_wrap_roots")
    assert plain > line + 5 and abs(spaced - plain) < 0.01, f"a wrapped formula of roots and indices moved: {spaced} pt against {plain} pt"
    # and through annotated-rows, which every calculation line is laid out by -- #eq's among them
    got = _query(root, f'#let f = {LONG}\n#context [#metadata((measure(block(width: {width}, annotated-rows(((f, none),)))).height / 1pt, measure(block(width: {width}, f)).height / 1pt)) <out>]', "display_wrap_rows")
    assert got[0] > got[1] + 5, got


# --- a formula too wide for its row, stacked at its signs -------------------------------

# The engineer's exercise: a support reaction whose letters, numbers and answer on one line are far wider than the column left of the citation, the numbers being a display fraction no line break can enter (config.typ's `show math.frac: it => $display(it)$`, which the example project's report carries).
BEAM = ('#var("q", 20.1, "kN/m", level: 0) #var("L", 6.5, "m", level: 0) #var("Q_1", 50.1, "kN", level: 0) '
        '#var("Q_2", 40.2, "kN", level: 0) #var("l_1", 3.1, "m", level: 0) #var("l_2", 1.25, "m", level: 0)\n')
REACTION = '"((q dot L) dot L/2 + Q_1 dot l_1 + Q_2 dot (l_1 + l_2))/L"'
# the right edge of the text and of the column left of the citation, in pt from the page's left edge: an A4 with 2.5 cm margins, and calc-engine's 3.8 cm column and 0.6 cm gutter
TEXT_RIGHT = 595.28 - 70.87
COLUMN_RIGHT = TEXT_RIGHT - (3.8 + 0.6) / 2.54 * 72


def _runs(root, body, name):
    """Every text run of a probe's first page, as (baseline, x, text) in pt -- y measured up from the foot of the page, as PDF measures it."""
    code, err, out = _compile(root, body, name)
    assert code == 0, err
    from pypdf import PdfReader
    runs = []

    def visit(text, cm, tm, font, size):
        if text.strip():
            runs.append((tm[4] * cm[1] + tm[5] * cm[3] + cm[5], tm[4] * cm[0] + tm[5] * cm[2] + cm[4], text.strip()))

    PdfReader(str(out)).pages[0].extract_text(visitor_text=visit)
    return runs


def _stacked(runs, cite):
    """The `=` signs a stacked formula's lines start with, the citation's baseline, and what else stands on that line past the column left of the citation."""
    at = next(r for r in runs if r[2].startswith(cite))
    equals = sorted((r for r in runs if r[2] == "="), key=lambda r: -r[0])
    overrun = [r for r in runs if abs(r[0] - at[0]) < 12 and r[1] > COLUMN_RIGHT and not r[2].startswith(cite)]
    return equals, at, overrun


def test_a_formula_too_wide_for_its_row_is_stacked_at_its_signs():
    """«Une longue fraction qui ne peut pas passer à la ligne déborde dans la colonne des références» (the engineer's exercise, after v0.87). `B_v = <letters> = <numbers> = 116.122 kN` stood on one line far wider than the column, a display fraction being one atom no line break can enter: the numbers ran under the citation and off the page. It is set the classic way now -- `B_v = <letters>`, then `= <numbers>`, then `= 116.122 kN`, the three `=` one under the other -- as rows of one grid, the citation on the first line's baseline, and nothing of the formula on that line past the column.

    Planted back (annotated-rows laying a formula-chain out as its one line), the numbers run past the column on the citation's line and this fails naming the runs."""
    root = conftest.TYPST_ROOT
    # a line of its own: an #eq is inline by default since v0.117 (issue #19), and stacking at the signs is a line's
    runs = _runs(root, "#report-level.update(3)\n" + BEAM + f'#eq("B_v", {REACTION}, norm: "SIA 260", norm-ref: "4.4", note: "line")', "display_stack_eq")
    equals, cite, overrun = _stacked(runs, "SIA 260")
    assert not overrun, f"the formula runs into the citation column: {overrun}"
    assert len(equals) >= 3, f"the formula is not stacked at its signs: {equals}"
    xs = {round(r[1], 1) for r in equals}
    assert max(xs) - min(xs) < 0.2, f"the stacked lines' = do not stand one under the other: {equals}"
    assert abs(cite[0] - equals[0][0]) < 2.5, f"the citation ({cite[0]:.1f}) is not level with the first line ({equals[0][0]:.1f})"
    # with the label on the line and the answer ruled twice, and with the extras in a footnote: what the line ends on ends its last line
    text = re.sub(r"\s+", " ", _text(root, "#report-level.update(3)\n" + BEAM + f'#eq("B_v", {REACTION}, label: "Auflagerkraft", style: "double", norm: "SIA 260", norm-ref: "4.4", note: "line")\n'
                                     f'#eq("B_w", "B_w", {REACTION}, label: "Auflagerkraft", note: "footnote")', "display_stack_eq_extras"))
    assert text.count("Auflagerkraft") == 2, text   # once after the first answer, once in the second's footnote
    assert "— Auflagerkraft" in text, text


def test_a_formula_that_fits_is_set_exactly_as_before():
    """What fits is untouched: a formula-chain whose one line fits the width its row has is laid out as that line, the rows around it at their distance. And one that fits only the full width, carrying no citation, spans the citation column on one line where, laid out as before, it wrapped in the column."""
    root = conftest.TYPST_ROOT
    cite = '(norm: "SIA 260", norm_ref: "4.4")'
    got = _query(root, '#let line = $M = q dot L^2 / 8 = 106.153 "kNm"$\n'
                       '#let chain = formula-chain(line, $a = b$, ("c",), s => $= #s$)\n'
                       f'#context [#metadata((measure(block(width: 16cm, annotated-rows(((chain, {cite}), ([x], none))))).height / 1pt, '
                       f'measure(block(width: 16cm, annotated-rows(((line, {cite}), ([x], none))))).height / 1pt)) <out>]', "display_stack_fits")
    assert abs(got[0] - got[1]) < 0.01, f"a formula that fits moved: {got[0]} pt against {got[1]} pt"
    wide = '$x = 20.1 dot 6.5 + 50.1 dot 3.1 + 40.2 dot (3.1 + 1.25) + 20.1 dot 6.5 + 50.1 dot 3.1 + 40.2 dot 3.1$'
    width, chained, plain = _query(root, f'#let line = {wide}\n#let chain = formula-chain(line, $x = 1$, ("2",), s => $= #s$)\n'
                                         f'#context [#metadata((measure(line).width / 1pt, measure(block(width: 16cm, annotated-rows(((chain, none), ([y], {cite}))))).height / 1pt, '
                                         f'measure(block(width: 16cm, annotated-rows(((line, none), ([y], {cite}))))).height / 1pt)) <out>]', "display_stack_spans")
    assert 16 / 2.54 * 72 - (3.8 + 0.6) / 2.54 * 72 < width < 16 / 2.54 * 72, f"the probe line ({width} pt) does not fall between the column and the full width"
    assert chained < plain - 5, f"a line carrying no citation wrapped in the column rather than span it: {chained} pt against {plain} pt"


def test_a_step_of_show_calc_too_wide_for_its_row_is_stacked():
    """`show-calc` meets the same line: a step whose letters, numbers and answer stand on one row (`inline`), or whose numbers and answer do, is a formula-chain too. A step with a display fraction too wide for its row is planted in a copy of the export -- once inline, once on the two rows a step takes -- and each is stacked at its signs, the citation on its first line and nothing past the column there."""
    root, data = _root("display_stack_calc")
    calcs = json.loads((data / "calculations.json").read_text(encoding="utf-8"))
    domain = next(iter(calcs["domains"]))
    # the inputs cite another norm than the step, so the step's own citation is the one the check finds
    var = lambda value, unit, symbol, level: {"value": value, "unit": unit, "symbol": symbol, "label": symbol, "level": level,
                                              "norm": "SIA 261", "norm_ref": "1", "source": "python:test"}
    inputs = {"q": var(20.1, "kN/m", "q", 3), "L": var(6.5, "m", "L", 3), "Q_1": var(50.1, "kN", "Q_1", 3), "Q_2": var(40.2, "kN", "Q_2", 3),
              "l_1": var(3.1, "m", "l_1", 3), "l_2": var(1.25, "m", "l_2", 3)}
    formula = "B_v = ((q dot L) dot L/2 + Q_1 dot l_1 + Q_2 dot (l_1 + l_2))/L"
    for name, inline in (("INLINE", True), ("ROWS", False)):
        step = {"name": "Auflager", "level": 1, "result": "B_v", "uses": list(inputs), "formula": formula, "norm": "SIA 260", "norm_ref": "4.4"}
        if inline:
            step["inline"] = True
        calcs["domains"][domain]["instances"][name] = {
            "results": ["B_v"], "vars": dict(inputs, B_v=var(116.122, "kN", "B_v", 1)), "steps": [step], "checks": [],
        }
    (data / "calculations.json").write_text(json.dumps(calcs, ensure_ascii=False), encoding="utf-8")
    for name in ("INLINE", "ROWS"):
        runs = _runs(root, f'#show-calc("{domain}", "{name}", level: 3, title: none)', "stack_" + name)
        equals, cite, overrun = _stacked(runs, "SIA 260")
        assert not overrun, f"{name}: the step runs into the citation column: {overrun}"
        assert max(r[1] for r in runs) < TEXT_RIGHT, f"{name}: the step runs off the page"
        # the first `=` of each line from the step's own down -- the inputs' rows above it carry theirs
        starts = {}
        for y, x, _ in (r for r in equals if r[0] <= cite[0] + 1):
            starts[round(y, 1)] = min(x, starts.get(round(y, 1), x))
        if name == "INLINE":
            # the letters, the numbers and the answer are one formula: it takes more than one line, each `=` under the first
            assert len(starts) >= 2, f"the inline step is not stacked at its signs: {equals}"
            assert max(starts.values()) - min(starts.values()) < 0.2, f"the stacked lines' = do not stand one under the other: {starts}"


def test_a_relation_too_wide_for_its_line_is_stacked_and_one_that_fits_stays_in_its_sentence():
    """`#verify` at level 3 prints a side that is a formula as its letters, numbers and value, and the engineer's reaction is one: the relation ran off the page, its ✔ on a line of its own. It is stacked at its signs now, as `#eq` is -- the letters, then `= <numbers>`, then `= 116.122 kN ⩽ 200 kN`, the `=` one under the other -- double-ruled and marked. A relation that fits is left in its sentence."""
    root = conftest.TYPST_ROOT
    runs = _runs(root, BEAM + '#verify(`((q dot L) dot L/2 + Q_1 dot l_1 + Q_2 dot (l_1 + l_2))/L <= 200 "kN"`, level: 3)', "display_stack_verify")
    equals = sorted((r for r in runs if r[2] == "="), key=lambda r: -r[0])
    assert len(equals) >= 2, f"the relation is not stacked: {equals}"
    xs = {round(r[1], 1) for r in equals}
    assert max(xs) - min(xs) < 0.2, f"the stacked lines' = do not stand one under the other: {equals}"
    assert max(r[1] for r in runs) < TEXT_RIGHT, "the relation runs off the page"
    assert any("✔" in r[2] for r in runs), "the stacked relation lost its mark"
    runs = _runs(root, '#var("F_Ed", 2.037, "kN", level: 0) #var("R_d", 2.655, "kN", level: 0)\nDer Nachweis #verify(`F_Ed <= R_d`, level: 3) ist erfüllt.', "display_verify_sentence")
    lines = {round(r[0]) for r in runs if r[2].startswith(("Der", "ist erfüllt"))}
    assert len(lines) == 1, f"a relation that fits left its sentence: {runs}"


# --- the level of detail -1 (issue #20, v0.117): show-calc, show-connector-resistance, show-polar-moment --------------------

def test_a_connector_at_minus_one_prints_what_is_chosen_and_its_headline():
    """REQ-003 (D-12, D-14): a connector at -1 prints its headline as a title, and of its calculation only the vars and tables chosen -- a result not chosen goes like any other value; the keys are the export's own (calc/shown_variables.py `export_keys`), every one of them compiles, and a key it does not have is refused."""
    import shown_variables
    connectors = json.loads((PROJECT.data_dir / "connectors.json").read_text(encoding="utf-8"))["connectors"]
    cid, entry = next((k, v) for k, v in connectors.items() if v.get("calculated"))
    keys = shown_variables.export_keys(entry)
    assert "R_d" in keys and "table-1" in keys
    none = _text(conftest.TYPST_ROOT, f'#show-connector-resistance("{cid}", level: -1, shown: (:))', "minus1_connector_none")
    one = _text(conftest.TYPST_ROOT, f'#show-connector-resistance("{cid}", level: -1, shown: (R_d: 1))', "minus1_connector_one")
    assert one.count("=") > none.count("="), (none, one)
    every = "(" + ", ".join(f"{k}: 3" for k in keys) + ")"
    code, err, _ = _compile(conftest.TYPST_ROOT, f'#show-connector-resistance("{cid}", level: -1, shown: {every})', "minus1_connector_every")
    assert code == 0, err
    code, err, _ = _compile(conftest.TYPST_ROOT, f'#show-connector-resistance("{cid}", level: -1, shown: (nope: 1))', "minus1_connector_bad")
    assert code != 0 and "nope" in err and "R_d" in err, err


def test_show_calc_at_minus_one_prints_only_what_is_chosen():
    """REQ-003: show-calc at -1 prints the vars and tables `shown:` names -- the export's own keys -- and drops a result not chosen."""
    instance, name = _wind_instance()
    calcs = json.loads((PROJECT.data_dir / "calculations.json").read_text(encoding="utf-8"))
    import shown_variables
    entry = calcs["domains"]["wind-load"]["instances"][instance]
    body = f'#show-calc("wind-load", "{instance}", level: -1, shown: ({name}: 2), title: none)'
    text = _text(conftest.TYPST_ROOT, body, "minus1_calc_one")
    empty = _text(conftest.TYPST_ROOT, f'#show-calc("wind-load", "{instance}", level: -1, shown: (:), title: none)', "minus1_calc_none")
    assert "=" in text and "=" not in empty, (text, empty)
    if entry is not None:
        every = "(" + ", ".join(f"{k}: 3" for k in shown_variables.export_keys(entry)) + ")"
        code, err, _ = _compile(conftest.TYPST_ROOT, f'#show-calc("wind-load", "{instance}", level: -1, shown: {every})', "minus1_calc_every")
        assert code == 0, err


def test_a_polar_moment_at_minus_one_prints_its_groups_of_lines_as_chosen():
    """REQ-003, D-14: show-polar-moment at -1 -- its heading always; F_max at 1 its one line, at 2 its working; I_p at 3 its working; nothing of what is not chosen; every key of lib/shown-variables.json compiles at 3."""
    import shown_variables
    connections = json.loads((PROJECT.data_dir / "connections.json").read_text(encoding="utf-8"))["connections"]
    polar = next((k for k, v in connections.items() if v.get("calculated", True)), None)
    if polar is None:
        raise Skip("the example project has no polar moment")
    call = f'#show-polar-moment("{polar}", N: 7.5, V: 25, M: 6.6, level: -1, shown: %s)'
    none = _text(conftest.TYPST_ROOT, call % "(:)", "minus1_polar_none")
    assert "max" not in none and "I_p" not in none.replace(" ", ""), none
    fmax = _text(conftest.TYPST_ROOT, call % "(F_max: 1)", "minus1_polar_fmax")
    assert "max" in fmax and "sqrt" not in fmax and "√" not in fmax, fmax
    working = _text(conftest.TYPST_ROOT, call % "(F_max: 2)", "minus1_polar_working")
    assert "√" in working, working
    every = "(" + ", ".join(f"{k}: 3" for k in shown_variables.keys("show-polar-moment")) + ")"
    code, err, _ = _compile(conftest.TYPST_ROOT, call % every, "minus1_polar_every")
    assert code == 0, err
