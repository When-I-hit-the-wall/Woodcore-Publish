"""The permanent loads, and the two rules v0.59 added to them.

The dead load is the one domain Python *calculates* rather than reads (docs/domain/loads.md §3.3ter): Excel holds the layer build-up, Python sums it. That makes two things possible that a value read on its own cannot show, and both were found on the engineer's own workbook in v0.59:

* a **chosen** permanent load below the sum of the layers the report prints above it, so that the table does not lead to the number in bold under it;
* a **specific weight typed over** the sheet's own lookup, so that column E names one material and column I holds another material's number -- and since this exporter follows the name, the report prints a load the sheet does not show.

Both are refused now. These tests build a workbook carrying each defect, on purpose, and check that the export refuses it by name -- and that a correct workbook still passes.
"""

TIER = "fast"  # tests/run_tests.py --fast

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import conftest
import io_excel
import validation
from domains import dead_load
from fixtures import workbook as fx

# Two materials of the same Ebene: one wet, one dry. The engineer's own case, in miniature.
LIBRARY = (
    ("Beschichtung", "Dachbegrünung (nass)", 160, "kg/m2"),
    ("Beschichtung", "Dachbegrünung (trocken)", 100, "kg/m2"),
    ("Tragstruktur", "Kerto-Q", 500, "kg/m3"),
)

DRY = (
    fx.layer("ak", "Beschichtung", "Dachbegrünung (trocken)"),
    fx.layer("gk", "Tragstruktur", "Kerto-Q", d=0.06),
)


def _read(built):
    cells = io_excel.open_cells(built["path"])
    materials = dead_load.read_materials(cells)
    return dead_load.read_instance(cells, built["sheet"], materials)


def _refused(built):
    """The message the export refuses `built` with, or None if it does not refuse it."""
    try:
        _read(built)
    except validation.ValidationError as exc:
        return str(exc)
    return None


def test_a_correct_build_up_is_read():
    d = conftest.tmpdir("dead_ok")
    built = fx.build(d / "Belastungsannahmen.xlsx", layers=DRY, library=LIBRARY)
    record = _read(built)
    # 100 kg/m2 * 1 * 1 / (1 * 100) = 1.0 ; 500 kg/m3 * 0.06 / 100 = 0.3
    assert abs(record["vars"]["ak"]["value"] - 1.0) < 1e-9, record["vars"]["ak"]["value"]
    assert abs(record["vars"]["gk"]["value"] - 0.3) < 1e-9, record["vars"]["gk"]["value"]
    assert abs(record["vars"]["gk_ak"]["value"] - 1.3) < 1e-9
    assert record["results"] == ["gk_ak_gew"]


def test_a_load_typed_without_a_material_is_counted_and_printed_as_typed():
    """A row naming no material with its load typed straight into column K -- «Installationen und Innenwände», 0.5 kN/m², in the Belastungsannahmen template 3.2 -- is counted by the sheet and was skipped here: a_k came to 5.4816 where the sheet shows 5.9816, with no word (periodic audit 260916, AUD-2-2). It is a layer now, its load the one typed, and the table says it was typed."""
    d = conftest.tmpdir("dead_direct")
    layers = DRY + (fx.direct("ak", "Installationen und Innenwände", 0.5),)
    built = fx.build(d / "Belastungsannahmen.xlsx", layers=layers, library=LIBRARY)
    record = _read(built)
    assert abs(record["vars"]["ak"]["value"] - 1.5) < 1e-9, record["vars"]["ak"]["value"]
    assert abs(record["vars"]["gk_ak"]["value"] - 1.8) < 1e-9
    table = record["tables"][0]
    rows = [row for row in table["rows"] if row[1] == "Installationen und Innenwände"]
    assert len(rows) == 1, table["rows"]
    assert rows[0][2] == dead_load.DIRECT_LOAD and abs(rows[0][-1] - 0.5) < 1e-9, rows[0]
    # a row with neither a material nor a typed load is still a placeholder, and skipped
    empty = fx.build(conftest.tmpdir("dead_placeholder") / "Belastungsannahmen.xlsx", layers=DRY + (fx.layer("ak", "Leer", None, d=None, b=None, e=None),), library=LIBRARY)
    assert abs(_read(empty)["vars"]["ak"]["value"] - 1.0) < 1e-9


def test_a_chosen_value_rounded_up_passes():
    d = conftest.tmpdir("dead_round_up")
    built = fx.build(d / "Belastungsannahmen.xlsx", layers=DRY, library=LIBRARY, chosen=1.5)
    assert _refused(built) is None
    assert _read(built)["vars"]["gk_ak_gew"]["value"] == 1.5


def test_a_chosen_value_equal_to_the_sum_passes():
    d = conftest.tmpdir("dead_equal")
    built = fx.build(d / "Belastungsannahmen.xlsx", layers=DRY, library=LIBRARY, chosen=1.3)
    assert _refused(built) is None


def test_a_chosen_value_below_the_sum_is_refused():
    """v0.59, found on `EL+AL-Dach ohne Wasser`: 1.900 chosen against 2.412 summed."""
    d = conftest.tmpdir("dead_below")
    built = fx.build(d / "Belastungsannahmen.xlsx", layers=DRY, library=LIBRARY, chosen=1.0)
    message = _refused(built)
    assert message is not None, (
        "a chosen permanent load of 1.0 kN/m² against layers summing to 1.3 was "
        "accepted -- the report would print a build-up that does not lead to its "
        "own answer"
    )
    for wanted in ("1.000", "1.300", "Round up"):
        assert wanted in message, f"the message does not say {wanted!r}:\n{message}"


def test_rounding_noise_is_not_refused():
    """A sum of 1.30004 designed with 1.3 is rounding, not a defect."""
    d = conftest.tmpdir("dead_noise")
    built = fx.build(d / "Belastungsannahmen.xlsx", layers=DRY, library=LIBRARY, chosen=1.2999999)
    assert _refused(built) is None, "rounding noise must not stop an export"


def test_a_weight_typed_over_its_lookup_is_refused():
    """v0.59, found on `EL+AL-Dach ohne Wasser!I9`: 100 typed over the lookup, while E9 went on naming the wet Dachbegrünung at 160."""
    d = conftest.tmpdir("dead_typed_over")
    layers = (
        fx.layer("ak", "Beschichtung", "Dachbegrünung (nass)", weight=100),
        fx.layer("gk", "Tragstruktur", "Kerto-Q", d=0.06),
    )
    built = fx.build(d / "Belastungsannahmen.xlsx", layers=layers, library=LIBRARY, chosen=9.0)
    message = _refused(built)
    assert message is not None, (
        "a specific weight typed over the sheet's own lookup was accepted -- the "
        "name in column E and the number in column I would go on saying different "
        "things, and the report would follow the name"
    )
    for wanted in ("100", "160", "Dachbegrünung (nass)", "lookup"):
        assert wanted in message, f"the message does not say {wanted!r}:\n{message}"


def test_a_weight_that_agrees_with_the_library_passes():
    """A number in column I is only refused when it *disagrees*: a sheet that states the library's own value states nothing new."""
    d = conftest.tmpdir("dead_typed_same")
    layers = (
        fx.layer("ak", "Beschichtung", "Dachbegrünung (trocken)", weight=100),
        fx.layer("gk", "Tragstruktur", "Kerto-Q", d=0.06),
    )
    built = fx.build(d / "Belastungsannahmen.xlsx", layers=layers, library=LIBRARY, chosen=1.5)
    assert _refused(built) is None


def test_an_unknown_material_is_refused_by_name():
    d = conftest.tmpdir("dead_unknown")
    layers = (fx.layer("gk", "Tragstruktur", "Gibt es nicht"),)
    built = fx.build(d / "Belastungsannahmen.xlsx", layers=layers, library=LIBRARY, chosen=1.0)
    message = _refused(built)
    assert message is not None and "Gibt es nicht" in message, message


def test_a_distance_of_zero_is_refused():
    """Dist. divides the layer's load."""
    d = conftest.tmpdir("dead_zero_dist")
    layers = (fx.layer("gk", "Tragstruktur", "Kerto-Q", d=0.06, e=0),)
    built = fx.build(d / "Belastungsannahmen.xlsx", layers=layers, library=LIBRARY, chosen=1.0)
    message = _refused(built)
    assert message is not None and "Dist." in message, message


def test_the_engineers_own_workbooks_still_pass():
    """Every EL+AL sheet of the real project, read end to end.

    Skipped where the workbooks are not there. It is the one test that touches them, it only reads, and it is what says whether the two rules above are refusing a real sheet today.
    """
    import registry
    try:
        books = registry.open_workbooks(conftest.real_project().root)  # the engineer's own: the example project carries no workbook
    except validation.ValidationError as exc:
        raise conftest.Skip(str(exc))
    refused = []
    for cells in books:
        sheets = cells.sheet_names(dead_load.SHEET_PREFIX)
        if not sheets:
            continue
        materials = dead_load.read_materials(cells)
        for sheet in sheets:
            try:
                dead_load.read_instance(cells, sheet, materials)
            except validation.ValidationError as exc:
                refused.append(f"  {cells.path.name}!{sheet}: {exc}")
    assert not refused, (
        "the export refuses these permanent-load sheets:\n" + "\n".join(refused)
    )
