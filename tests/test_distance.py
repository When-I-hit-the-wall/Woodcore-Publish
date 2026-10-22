"""`#distance` -- the minimum distances and timber thicknesses of SIA 265, computed in the report with a diameter (lib/distance.typ, v0.87).

The multiples of d live in `calc/norms/` (one JSON per table, read and checked by `calc/norms/sia265.py`, whose own tests are in test_norms.py) and the arithmetic that turns them into millimetres lives twice: in Typst, where the report prints it, and in `sia265.distance`, where a test can reach it. Three things are held here and nowhere else:

* **one list of files, named in four places** -- lib/distance.typ reads them, sia265.py checks them, calc/project.py copies them into every project beside the engine, calc/tools/build_examples.py into the frozen examples. A file one of them forgets is a report that fails on «file not found» in a project and nowhere in the checkout;
* **the Typst arithmetic is the Python arithmetic**, cell by cell, over diameters on both sides of every split and at three angles;
* **what a call prints and what it refuses**, compiled against the example project's own commands.typ, as a section would.

⚠️ The compiled checks are skipped where `typst` is not on the path.
"""

import json
import re
import subprocess

import conftest
from conftest import ROOT, Skip
from norms import sia265
import project

DISTANCE_TYP = ROOT / "lib" / "distance.typ"


def _typst_source():
    return DISTANCE_TYP.read_text(encoding="utf-8")


def _files_named_in_typst():
    return set(re.findall(r'"(sia265-2021-[a-z0-9.-]+)"', _typst_source()))


def test_one_list_of_files_in_four_places():
    """lib/distance.typ, sia265.py, project.ENGINE_FILES and the examples' fixture name the same norm files."""
    typst = _files_named_in_typst()
    python = set(sia265.DISTANCE_TABLES + sia265.DIAMETER_SCOPES)
    engine = {name[len("calc/norms/"):-len(".json")] for name in project.ENGINE_FILES if name.startswith("calc/norms/")}
    assert typst == python, "lib/distance.typ names %s, sia265.py %s" % (sorted(typst - python), sorted(python - typst))
    # since v0.99 the engine also carries the catalogue lib/bibliography.typ reads (tests/test_bibliography.py holds that) -- and nothing else: the norm files lib/timber.typ read went with it (spec 2026-10-21-commandes-typst-refonte, the member checks written out by Python)
    bib = {m[:-len(".json")] for m in re.findall(r'#let bib-file = "([^"]+)"', (ROOT / "lib" / "bibliography.typ").read_text(encoding="utf-8"))}
    assert bib, "lib/bibliography.typ names no catalogue file"
    assert engine == python | bib, "project.ENGINE_FILES lacks %s, carries %s besides" % (sorted((python | bib) - engine), sorted(engine - python - bib))
    assert "lib/distance.typ" in project.ENGINE_FILES
    for number in (24, 27, 28, 32, 33, 36, 37, 38, 39, 40, 41):
        for entry in sia265.distance_table(number)["fasteners"]:
            assert entry.get("scope", sia265.K_ALPHA) in typst, "Tabelle %d names a scope lib/distance.typ does not read" % number
    fixture = ROOT / "examples" / "calc" / "norms"
    missing = sorted(n for n in python if not (fixture / (n + ".json")).is_file())
    assert not missing, "examples/calc/norms/ lacks %s -- run calc/tools/build_examples.py --freeze" % missing


def test_the_german_names_are_the_windows_kinds_of_fastener():
    """`#distance(12, "Stabdübel")`: every kind calc/domains/connector.py's TYPES names is a name the command reads, and no other."""
    from domains import connector
    block = re.search(r"#let distance-types = \((.*?)\n\)", _typst_source(), re.S).group(1)
    german = set(re.findall(r'"([^"]+)":', block))
    assert german == set(connector.TYPES), "lib/distance.typ reads %s; connector.TYPES is %s" % (sorted(german), sorted(connector.TYPES))
    kinds = set(re.findall(r'"([a-z-]+)"', re.search(r"#let distance-kinds = \((.*?)\)", _typst_source()).group(1)))
    assert set(sia265.DISTANCE_FASTENERS) <= kinds, "a table names a kind the command does not take"


def test_an_engine_copy_written_before_the_distance_tables_is_stale_not_edited():
    """A project's VERSION written before v0.87 names no lib/distance.typ and no norm table: the copy is replaced as another build of this version, never refused as edited by hand."""
    folder = conftest.tmpdir("distance_engine")
    here = project.write(folder / "D.woodcore", "D")
    project.sync_engine(here)
    stamp_file = here.generated_dir / project.ENGINE_STAMP
    stamp = json.loads(stamp_file.read_text(encoding="utf-8"))
    for name in list(stamp["files"]):
        if name == "lib/distance.typ" or name.startswith("calc/norms/"):
            del stamp["files"][name]
            path = here.generated_dir / name
            path.chmod(0o666)
            path.unlink()
    stamp_file.write_text(json.dumps(stamp), encoding="utf-8")
    assert project.engine_state(here)[0] == "stale"
    written = project.sync_engine(here)
    assert "lib/distance.typ" in written and project.engine_state(here)[0] == "current"


# --- compiled -----------------------------------------------------------------

def _compile(body, name, query=None):
    """Compiles `body` in the example project's report, as a section would; returns (ok, text or the refusal, queried value)."""
    if not conftest.have_typst():
        raise Skip("typst is not on the path")
    d = conftest.probe_dir(name)
    probe = d / "probe.typ"
    probe.write_text('#import "/000-Typst-Config/commands.typ": *\n#report-level.update(2)\n' + body + "\n", encoding="utf-8")
    if query:
        out = subprocess.run(["typst", "query", "--root", str(conftest.TYPST_ROOT), str(probe), query, "--field", "value", "--one"],
                             capture_output=True, text=True, encoding="utf-8")
        assert out.returncode == 0, out.stderr
        return json.loads(out.stdout)
    out = subprocess.run(["typst", "compile", "--root", str(conftest.TYPST_ROOT), str(probe), str(d / "probe.pdf")],
                         capture_output=True, text=True, encoding="utf-8")
    if out.returncode != 0:
        message = conftest.panic_message(out.stderr)
        return False, message if message is not None else out.stderr
    from pypdf import PdfReader
    raw = "\n".join(page.extract_text() for page in PdfReader(str(d / "probe.pdf")).pages)
    return True, re.sub(r"\s+", " ", raw)


def test_the_typst_arithmetic_is_the_pythons():
    """Every cell of every table, at diameters either side of the 4 mm split and at three angles, printed by lib/distance.typ's own distance-cell and computed by sia265.distance."""
    diameters = (3, 4, 4.2, 8, 12, 80)
    angles = (None, 30, 90)
    engine = conftest.import_path(conftest.PROJECT.generated_dir / "lib" / "distance.typ")
    ds = "(" + ", ".join(map(str, diameters)) + ",)"
    # the helpers are imported from the project's engine copy by a path computed from where it is (tests/test_harness.py), commands.typ exporting `distance` alone
    body = (f'#import "{engine}": distance-cell, distance-table, distance-files\n'
            '#metadata(distance-files.keys().map(n => {\n'
            '  let t = distance-table(n)\n'
            f'  (n, t.rows.map(r => t.columns.map(c => {ds}.map(d => (none, 30, 90).map(a => distance-cell(r.at(c.id), d, a).at(0))))))\n'
            '})) <out>')
    got = _compile(body, "distance_arithmetic", "<out>")
    for number, rows in got:
        table = sia265.distance_table(number)
        for row, printed in zip(table["rows"], rows):
            for column, by_d in zip(table["columns"], printed):
                for d, by_a in zip(diameters, by_d):
                    for alpha, value in zip(angles, by_a):
                        want = sia265.distance(row[column["id"]], d, alpha or 0)
                        assert abs(value - want) < 1e-9, "Tabelle %s %s %s d=%s alpha=%s: Typst %s, Python %s" % (
                            number, row["id"], column["id"], d, alpha, value, want)


def test_a_nail_table_prints_its_millimetres_and_its_case():
    ok, text = _compile('#distance(3.1, "nail", table: 28)', "distance_nail")
    assert ok, text
    for number in ("31", "15.5", "46.5", "21.7"):
        assert number in text, (number, text)
    assert "SIA 265 Tabelle 28" in text and "von Nagel zu Nagel" in text and "= 3.1 mm" in text, text
    assert "Minimale Abstände bei Nagelung ohne Vorbohrung" in text, text


def test_auto_prints_the_tables_that_hold_for_d():
    """A screw of 8 mm: Tabellen 36 to 40; of 4 mm: 38 to 40, Tabellen 36 and 37 holding for 6 to 12 mm (6.5.2.3.1); 28 and 33 only when asked for."""
    ok, text = _compile('#distance(8, "screw")', "distance_screw8")
    assert ok, text
    assert [n for n in ("24", "27", "28", "32", "33", "36", "37", "38", "39", "40", "41") if "Tabelle " + n in text] == ["36", "37", "38", "39", "40"], text
    ok, text = _compile('#distance(4, "Vollgewindeschraube")', "distance_screw4")
    assert ok, text
    assert "Tabelle 36" not in text and "Tabelle 37" not in text and "Tabelle 38" in text and "Tabelle 40" in text, text
    ok, text = _compile('#distance(8, "screw", table: 28)', "distance_screw28")
    assert ok and "6.5.2.3.3" in text, text


def test_the_thickness_tables_are_a_row_per_thickness():
    ok, text = _compile('#distance(8, "screw", table: 37)', "distance_thickness")
    assert ok, text
    assert "72" in text and "32" in text and "min. 24 mm" in text, text
    assert "Baustoff" in text and "Vollholz, keilgezinktes Vollholz" in text, text


def test_a_ring_is_read_at_its_angle():
    ok, text = _compile('#distance(80, "ring", alpha: 30)', "distance_ring30")
    assert ok and "142.222" in text and "106.667" in text, text
    ok, text = _compile('#distance(80, "ring")', "distance_ring0")
    assert ok and "160" in text, text


def test_a_diameter_declared_with_var_carries_its_unit():
    ok, text = _compile('#var("d", 1.6, "cm")\n#distance("d", "dowel")', "distance_var")
    assert ok and "= 16 mm" in text and "112" in text, text


def test_the_label_the_descr_and_the_citation():
    """REQ-016: `label:` is each table's title -- auto the norm's, a string replacing it, none none --, `descr:` a footnote on it (`title:` until the spec 2026-10-21-commandes-typst-refonte)."""
    ok, text = _compile('#distance(12, "dowel", label: "Anschluss Pfette", descr: "Zwei Reihen.", norm-section: "6.2.1.2")', "distance_label")
    assert ok, text
    assert "Anschluss Pfette" in text and "Zwei Reihen." in text and "SIA 265 6.2.1.2" in text and "Minimale Abstände für Stabdübel" not in text, text
    ok, text = _compile('#distance(12, "dowel", label: none, norm: none)', "distance_bare")
    assert ok and "SIA 265" not in text and "Minimale Abstände für Stabdübel" not in text, text


def test_a_french_report_prints_the_norms_french():
    ok, text = _compile('#set-report-language("fr")\n#distance(3.1, "nail", table: 28)', "distance_fr")
    assert ok, text
    assert "Espacements minimaux des clous sans préperçage" in text and "SIA 265 tableau 28" in text and "de clou à clou" in text, text


def test_what_distance_refuses_it_names():
    cases = (
        ('#distance(8, "staple")', "SIA 265/1"),
        ('#distance(8, "Klammer")', "SIA 265/1"),
        ('#distance(8, "rivet")', "or its German name"),
        ('#distance(10, "nail")', "1.9 to 8.5 mm"),
        ('#distance(5, "dowel")', "6 to 30 mm"),
        ('#distance(4, "screw", table: 36)', "6.5.2.3.1"),
        ('#distance(8, "nail", table: 24)', "27, 28, 32, 33"),
        ('#distance(8, "nail", table: 99)', "24, 27, 28"),
        ('#distance(8, "screw", label: "X")', "table:"),
        ('#distance(12, "dowel", tab: 24)', "unexpected argument"),
        ('#distance(8, "nail", alpha: 30)', "Tabelle 41"),
        ('#distance(80, "ring", alpha: 120)', "0 to 90"),
        ('#distance(0, "nail")', "positive"),
        ('#var("e", 12, "kN")\n#distance("e", "dowel")', "mm, cm, m"),
    )
    for i, (body, words) in enumerate(cases):
        ok, message = _compile(body, "distance_refuse_%d" % i)
        assert not ok, "%s compiled -- it should have been refused" % body
        assert words in message, "%s: %s" % (body, message)


def test_the_uniform_names_take_a_list_and_the_old_ones_are_said():
    """Spec 2026-10-21-commandes-typst-refonte, REQ-016, REQ-020: `table:` takes a list of tables, printed in its order; `tab:`, `title:` and `norm-ref:`, the names before, are no argument of it any more (the engineer, 22.10.2026) and are said at the project's opening and by the export, naming the new name."""
    from domains import commands_migrate
    ok, text = _compile('#distance(8, "screw", table: (37, 36))', "distance_list")
    assert ok and text.index("37") < text.index("36"), text
    found = commands_migrate.argument_calls('#distance(3.1, "nail", tab: 28, norm-ref: "Tabelle 28")\n')
    assert {(name, argument) for name, argument, _hint, _at in found} == {("distance", "tab"), ("distance", "norm-ref")}, found
    assert all(("table:" in hint) if argument == "tab" else ("norm-section:" in hint) for _name, argument, hint, _at in found)
