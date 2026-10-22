"""A table written in raw Typst, read into a model and written back (spec docs/requirements/completed/2026-10-21-commandes-typst-refonte.md, ARCH-004, Q-012; calc/typst_raw_table.py)."""

TIER = "fast"  # tests/run_tests.py --fast

import subprocess

import conftest
from conftest import Skip
import project
from typst_raw_table import RawTableError, RawTableModel

BODY = """#figure(
  table(
    columns: (auto, 1fr),
    stroke: 0.5pt,
    table.header([*Bauteil*], [*Last*]),
    [Dach], [$g_k$ = 2.5 kN/m²],
    table.hline(),
    [Decke], [3.0 kN/m²],
  ),
  caption: [Lasten],
) <lasten>"""


def test_a_raw_table_read_and_written_back_unchanged_is_the_same_bytes():
    """ARCH-004: read, nothing changed, written back: every byte."""
    model = RawTableModel(BODY)
    assert model.to_body() == BODY
    assert [c.width for c in model.columns] == ["auto", "1fr"] and model.header and model.row_count == 2
    assert [c.title for c in model.columns] == ["*Bauteil*", "*Last*"]
    assert model.cell(0, "c2") == "$g_k$ = 2.5 kN/m²" and model.get("caption") == "Lasten"


def test_a_cell_set_rewrites_its_brackets_alone_and_the_caption_its_own():
    """ARCH-004: a cell edited is its brackets' content replaced, nothing else of the body; the figure's caption likewise."""
    model = RawTableModel(BODY)
    model.set_cell(1, "c2", "3.2 kN/m²")
    assert model.to_body() == BODY.replace("[3.0 kN/m²]", "[3.2 kN/m²]")
    model.set_cell(0, "c1", "Flachdach")
    model.set_caption("Ständige Lasten")
    assert model.to_body() == BODY.replace("[3.0 kN/m²]", "[3.2 kN/m²]").replace("[Dach]", "[Flachdach]").replace("caption: [Lasten]", "caption: [Ständige Lasten]")


def test_a_hidden_column_is_kept_in_a_comment_and_comes_back_with_its_alignment():
    """Q-012: a column hidden leaves `columns:` and its cells go into the comment at the end of each line -- read back, it is the same column, hidden; shown again, its cells are where they were; an alignment set is written into `align:`; the other named arguments and the lines stay."""
    model = RawTableModel(BODY)
    model.set_align("c2", "right")
    model.set_hidden("c1", True)
    written = model.to_body()
    assert "columns: (1fr,)," in written and "align: (right,)," in written and "stroke: 0.5pt," in written and "table.hline()," in written
    assert "[$g_k$ = 2.5 kN/m²],  // woodcore:hidden 1=[Dach]" in written and "table.header([*Last*]),  // woodcore:hidden 1=[*Bauteil*]" in written
    assert written.startswith("#figure(\n  table(") and written.endswith("caption: [Lasten],\n) <lasten>")
    again = RawTableModel(written)
    assert again.is_hidden("c1") and again.cell(0, "c1") == "Dach" and again.column("c1").title == "*Bauteil*"
    again.set_hidden("c1", False)
    shown = RawTableModel(again.to_body())
    assert [shown.cell(r, "c1") for r in range(2)] == ["Dach", "Decke"] and not shown.is_hidden("c1")
    try:
        shown.set_hidden("c1", True)
        shown.set_hidden("c2", True)
        raise AssertionError("the last column printed is hidden")
    except RawTableError as exc:
        assert exc.code == "last_column"


def test_rows_and_columns_added_moved_and_removed_write_one_row_a_line():
    model = RawTableModel(BODY)
    model.add_row()
    model.set_cell(2, "c1", "Boden")
    model.move_row(2, 0)
    model.add_column("col3", title="Bemerkung")
    model.remove_row(1)
    again = RawTableModel(model.to_body())
    assert again.row_count == 2 and again.cell(0, "c1") == "Boden" and len(again.columns) == 3 and again.columns[2].title == "Bemerkung"


def test_a_table_out_of_the_subset_is_read_only():
    """ARCH-004: a spread, a cell spanning columns, a computed `columns:`, cells that do not fill the rows -- refused, `not_editable`: never rewritten."""
    for body in ("#table(columns: 2, ..rows)", "#table(columns: 2, table.cell(colspan: 2)[x])",
                 "#table(columns: n, [a], [b])", "#table(columns: 2, [a], [b], [c])",
                 "#table(columns: 2, ..for r in rows { r })"):
        try:
            RawTableModel(body)
            raise AssertionError(f"edited: {body}")
        except RawTableError as exc:
            assert exc.code == "not_editable", (body, exc.code)


def test_a_table_with_a_hidden_column_compiles_without_it():
    """Q-012: the comment holding a hidden column's cells is nothing to Typst: the table compiles, the hidden column not printed."""
    if not conftest.have_typst():
        raise Skip("typst is not on the path")
    model = RawTableModel(BODY)
    model.set_hidden("c1", True)
    probe = conftest.tmpdir("raw_table") / "t.typ"
    probe.write_text(model.to_body() + "\n", encoding="utf-8")
    run = subprocess.run([project.typst_executable(), "compile", str(probe), str(probe.with_suffix(".pdf"))], capture_output=True, text=True, encoding="utf-8", errors="replace")
    assert run.returncode == 0, run.stderr
    from pypdf import PdfReader
    text = " ".join(page.extract_text() for page in PdfReader(str(probe.with_suffix(".pdf"))).pages)
    assert "Last" in text and "Bauteil" not in text and "Dach" not in text, text


def test_the_structure_tab_s_pane_edits_a_raw_table_without_showing_code():
    """ARCH-004, Q-012: the pane of a `table` object -- the doc-table's cards -- writes a cell typed into its brackets alone, hides a column and aligns another into `columns:` and `align:`, and leaves a table out of the subset read only, emitting nothing."""
    import test_object_panes as panes
    import typst_objects
    op = panes._panes()
    context = panes._context()
    text = f"// woodcore:object table t\n{BODY}\n// woodcore:/object t\n"
    found = typst_objects.find(text, "t")
    assert found.type == "table" and found.state == "canonical"
    pane = op.pane_for("table", context)
    emitted = []
    pane.changed.connect(emitted.append)
    pane.load(found, context)
    assert pane.ready() and pane.row_list.count() == 2 and pane.current() == BODY and not emitted
    pane.row_list.setCurrentRow(1)
    pane.cell_edited("c2", "3.2 kN/m²", immediate=True)
    assert emitted and emitted[-1] == BODY.replace("[3.0 kN/m²]", "[3.2 kN/m²]"), emitted[-1:]
    pane.column_list.setCurrentRow(1)
    pane.align_box.setCurrentIndex(pane.align_box.findData("right"))
    assert "align: (auto, right)," in emitted[-1], emitted[-1]
    pane.column_list.item(0).setCheckState(_unchecked())
    assert "// woodcore:hidden 1=[Dach]" in emitted[-1] and "columns: (1fr,)," in emitted[-1], emitted[-1]
    assert typst_objects.write_object(text, "t", emitted[-1]).startswith("// woodcore:object table t\n#figure(")
    # out of the subset: read only, nothing emitted
    other, said = op.pane_for("table", context), []
    other.changed.connect(said.append)
    other.load("#table(columns: 2, ..rows)", context)
    assert not other.ready() and not said


def _unchecked():
    from PySide6.QtCore import Qt
    return Qt.CheckState.Unchecked
