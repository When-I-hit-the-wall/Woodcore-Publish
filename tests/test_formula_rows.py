"""The rows of the «Domaines» tab's «Formulaire», their lines, their gestures and «Annuler», without Qt (calc/domains/formula_rows.py, formula_undo.py; issue #113, spec docs/requirements/completed/2026-10-24-onglet-domaines-formulaire-code.md, REQ-003, REQ-016, UI-005, UI-007, ARCH-011, ARCH-015, D-16, D-17).

Held: a row is an item, glued items one row of text; its number is the line of the file it begins on; every domain of the example and the inline fixture is read and written back byte for byte; a group moved under a line that depends on it is refused with the sentence, elsewhere it keeps its order, one row alone is refused as before; «Annuler» gives the file back byte for byte and refuses a file changed since.
"""

TIER = "fast"

import shutil

import conftest
from conftest import ROOT

import project
from domains import formula_domain as fd, formula_rows as fr, formula_undo

FIXTURE = ROOT / "tests" / "fixtures" / "domains" / "panne-p2.typ"
_INLINE = """#import "/000-Typst-Config/commands.typ": *

#domain("inline", label: "Inline")[
  #var("b", 2, "m")

  #var("ak", 3, "kN/m") --- Auflast

- $0°$ bis $30°$: #eq("g_1", "g_(d,1)", `b*ak`)
    - Unter: #var("c", "c_(pe)", -1) $=>$ au besoin
Zwei: #var("x1", 1) #var("x2", 2) Ende
]
"""


def _panne():
    here = project.current()
    path = here.formulas_dir / "panne-p2.typ"
    shutil.copy(FIXTURE, path)
    return here, path, fd.read(path)


def test_a_row_is_an_item_its_number_the_line_it_begins_on():
    """UI-005, ARCH-011: Poutre P1 is five rows, lines 4 to 8 of its file; Panne P2's text rows begin where their words do; a row's number is the line of the file where its item begins."""
    here = project.current()
    poutre = fd.read(here.formulas_dir / "poutre-p1.typ")
    rows = fr.rows(poutre)
    assert [(r.kind, r.line) for r in rows] == [("var", 4), ("var", 5), ("eq", 6), ("var", 7), ("verify", 8)]
    _here, path, panne = _panne()
    try:
        lines = path.read_text(encoding="utf-8").split("\n")
        for row in fr.rows(panne):
            c = panne.commands[row.first]
            first = (c.written or c.raw).strip("\n").split("\n")[0]
            assert lines[row.line - 1] == first, (row, lines[row.line - 1], first)
        assert [r.line for r in fr.rows(panne)][:3] == [4, 7, 8] and fr.rows(panne)[9].line == 16
    finally:
        path.unlink()


def test_glued_items_are_one_row_of_text_and_every_file_is_written_back_byte_for_byte():
    """REQ-016, D-16: a chain of items glued on their lines is one row of text that holds its commands; every domain of the example, Panne P2 and the inline fixture read and written back unchanged, `body_pieces` the body `body_of` writes."""
    path = conftest.tmpdir("formula_rows") / "inline.typ"
    path.write_text(_INLINE, encoding="utf-8", newline="")
    inline = fd.read(path)
    assert inline.state == "canonical", inline.problem
    rows = fr.rows(inline)
    assert [r.kind for r in rows] == ["var", "text", "text"], [(r.kind, r.items) for r in rows]
    assert [c.key for _i, c in rows[1].commands(inline)] == ["ak", "g_1"] and [c.key for _i, c in rows[2].commands(inline)] == ["c", "x1", "x2"]
    here, ppath, panne = _panne()
    try:
        for domain in fd.list_domains(here) + [inline]:
            if domain.state == "unreadable":
                continue
            assert fd.write_text(domain) == domain.text, domain.id
            pieces = "\n".join(text for _i, text, _g in fd.body_pieces(domain) if True)
            joined = "".join(("" if g else "\n") + t for _i, t, g in fd.body_pieces(domain))[1:]
            assert joined == domain.body_read, domain.id
            lines = domain.text.split("\n")
            for i, line in enumerate(fr.item_lines(domain)):
                c = domain.commands[i]
                if not c.is_text and not c.glued_before:
                    assert lines[line - 1].lstrip().startswith("#" + c.kind), (domain.id, i, line, lines[line - 1])
            assert pieces
    finally:
        ppath.unlink()


def test_a_group_moved_under_a_line_that_depends_on_it_is_refused():
    """REQ-003, UI-013: e, l, γ_G (rows 3 to 5) moved under q_d, which is computed from them, are refused -- «q_d uses e, which would be below it» --, the domain unchanged; moved under b they keep their order; one row alone is refused as the pill was."""
    here, path, panne = _panne()
    try:
        results = fd.compute(panne, lambda c: fd.resolve_import(here, c, fd.list_domains(here)))
        rows = fr.rows(panne)
        group = [3, 4, 5]   # e, l, gamma_G
        assert [panne.commands[rows[r].first].key for r in group] == ["e", "l", "gamma_G"]
        target = next(k for k, r in enumerate(rows) if panne.commands[r.first].key == "M_d") + 1
        items, refusal = fr.move(panne, results, group, target)
        assert items is None and refusal[0] == "order" and refusal[2] in ("e", "l", "gamma_G") and refusal[1] in ("q_d", "M_d"), refusal
        b_row = next(k for k, r in enumerate(rows) if panne.commands[r.first].key == "W_y")
        items, refusal = fr.move(panne, results, [1, 2], 0)   # the two links above the text: allowed
        assert refusal is None and [c.key for c in items[:2]] == ["gk_ak_gew", "q_k1"]
        b = next(k for k, r in enumerate(rows) if panne.commands[r.first].key == "b")
        items, refusal = fr.move(panne, results, [b_row], b)
        assert items is None and refusal == ("order", "W_y", "b"), refusal
        h = next(k for k, r in enumerate(rows) if panne.commands[r.first].key == "h")
        items, refusal = fr.move(panne, results, [b, h], len(rows))
        assert items is None and refusal is not None
        eta_w = next(k for k, r in enumerate(rows) if panne.commands[r.first].key == "eta_w")
        items, refusal = fr.move(panne, results, [b, h], eta_w)
        assert items is None and refusal == ("order", "W_y", "b")
        gq = next(k for k, r in enumerate(rows) if panne.commands[r.first].key == "gamma_Q")
        items, refusal = fr.move(panne, results, [3, 4], gq + 1)   # e, l under gamma_Q, still above q_d
        assert refusal is None and [c.key for c in items if c.key in ("gamma_G", "gamma_Q", "e", "l")] == ["gamma_G", "gamma_Q", "e", "l"]
    finally:
        path.unlink()


def test_a_row_is_inserted_where_asked_and_deleted_with_what_is_glued_to_it():
    """UI-008, UI-007: the + between rows 3 and 4 writes the new line as row 4; deleting a row of text takes its glued commands with it."""
    here = project.current()
    poutre = fd.read(here.formulas_dir / "poutre-p1.typ")
    items, at = fr.insert_before_row(poutre, 3, [fd.Command("var", key="k", value=2)])
    assert at == 3 and [c.key for c in items] == ["q_d", "l", "M_d", "k", "M_Rd", ""]
    path = conftest.tmpdir("formula_rows_delete") / "inline.typ"
    path.write_text(_INLINE, encoding="utf-8", newline="")
    inline = fd.read(path)
    items = fr.delete(inline, [1])
    assert [c.key for c in items if not c.is_text] == ["b", "c", "x1", "x2"]


def test_undo_gives_the_file_back_byte_for_byte_and_never_writes_over_a_change():
    """UI-007, ARCH-015, D-17: b deleted, W_y fails on «b» unknown; «Annuler» writes the file back as it was; a file changed since is not written over, and the refusal says so."""
    here, path, panne = _panne()
    try:
        before = path.read_text(encoding="utf-8")
        rows = fr.rows(panne)
        b = next(k for k, r in enumerate(rows) if panne.commands[r.first].key == "b")
        panne.commands = fr.delete(panne, [b])
        saved = fd.save(here, panne)
        after = path.read_text(encoding="utf-8")
        results = fd.compute(saved, lambda c: fd.resolve_import(here, c, fd.list_domains(here)))
        wy = next(r for c, r in zip(saved.commands, results) if c.key == "W_y")
        assert wy.code == "unknown" and wy.values["names"] == ("b",)
        undo = formula_undo.Undo()
        undo.record("delete", path, before, after, line=18)
        undo.undo()
        assert path.read_text(encoding="utf-8") == before
        undo.record("move", path, before, after)
        path.write_text(after + "\n", encoding="utf-8")
        try:
            undo.undo()
        except formula_undo.UndoError as exc:
            assert exc.code == "changed"
        else:
            raise AssertionError("an undo wrote over a file changed since")
        assert path.read_text(encoding="utf-8") == after + "\n"
    finally:
        path.unlink()
