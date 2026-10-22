"""The lines of a timber member check built by the engine (calc/domains/timber_calc.py, spec 2026-10-21-restes-issue-69, REQ-003).

What is held:

* **a line is an engine var**: a line without a norm stops when it is written; every line of every check `compute` gives back is a var of a TimberCalculation, a line with a formula is a step whose `uses` are values the check holds;
* **one line, once**: a key written twice stops, naming it;
* **the projection is the old shape**: `rows()` gives `{key, symbol, value, unit, formula?, label?, keys?, clause?, norm?, table?}` in that order, only what a line carries, the table value inside the line it serves and never as a line of its own.
"""

import conftest  # noqa: F401  (paths)

import engine
from domains import member_check, timber_calc


def _records():
    import test_member_check as T
    return T._synthetic() + T._synthetic_fire()


def test_a_line_without_a_norm_stops_when_written():
    try:
        timber_calc.line("x", "x", 1.0, "", clause="4.2.1", norm="")
    except engine.EngineError:
        pass
    else:
        raise AssertionError("a line without a norm was built")


def test_a_key_written_twice_stops():
    lines = [timber_calc.line("A", "A", 1.0, "mm²"), timber_calc.line("A", "A", 2.0, "mm²")]
    try:
        timber_calc.TimberCalculation().take(lines)
    except engine.EngineError as exc:
        assert "'A'" in str(exc), exc
    else:
        raise AssertionError("a line written twice was taken")


def test_the_projection_is_the_shape_compute_has_always_returned():
    table = timber_calc.line("f_t_0_d_tab", "f_(t,0,d,\"Tab\")", 14.0, "N/mm²", clause="Tabelle 8")
    lines = [timber_calc.line("A", "A", 100.0, "mm²", "b dot h", keys="b dot h"),
             timber_calc.line("eta_w", "eta_w", 1.0, "", label="Feuchteklasse 1", clause="Tabelle 4"),
             timber_calc.line("f_t_0_d", "f_(t,0,d)", 14.0, "N/mm²", "eta_w dot 14", keys="eta_w dot f_t_0_d_tab", clause="Tabelle 8", table=table)]
    calc = timber_calc.TimberCalculation().take(lines)
    rows = calc.rows()
    assert rows == [
        {"key": "A", "symbol": "A", "value": 100.0, "unit": "mm²", "formula": "b dot h", "keys": "b dot h"},
        {"key": "eta_w", "symbol": "eta_w", "value": 1.0, "unit": "", "label": "Feuchteklasse 1", "clause": "Tabelle 4", "norm": "SIA 265"},
        {"key": "f_t_0_d", "symbol": "f_(t,0,d)", "value": 14.0, "unit": "N/mm²", "formula": "eta_w dot 14", "keys": "eta_w dot f_t_0_d_tab",
         "clause": "Tabelle 8", "norm": "SIA 265", "table": {"key": "f_t_0_d_tab", "symbol": "f_(t,0,d,\"Tab\")", "value": 14.0, "unit": "N/mm²", "clause": "Tabelle 8"}},
    ]
    assert [list(row) for row in rows][2] == ["key", "symbol", "value", "unit", "formula", "keys", "clause", "norm", "table"]
    # the table value is a var of its own, never a line; the design value's step uses it
    assert "f_t_0_d_tab" in calc.vars and "f_t_0_d_tab" not in calc.order
    step = next(s for s in calc.steps if s["result"] == "f_t_0_d")
    assert step["uses"] == ["eta_w", "f_t_0_d_tab"] and step["formula"] == "f_(t,0,d) = eta_w dot 14", step


def test_every_line_of_every_check_is_an_engine_var():
    """REQ-003: no line of `compute` is a dict built by hand -- each is a var of the check's TimberCalculation, checked by engine.var, and its rows are `compute`'s."""
    records = _records()
    assert records
    for rec in records:
        result, calc = member_check._calculation(rec)
        assert isinstance(calc, timber_calc.TimberCalculation), rec["id"]
        assert all(isinstance(item, timber_calc.Line) for item in result["rows"]), rec["id"]
        # compute's rows are the calculation's, each whose formula computes its value in the registry's keys given them (spec 2026-10-21-commandes-typst-refonte, `_with_keys`)
        assert calc.rows() == [{k: v for k, v in row.items() if k != "keys" or "keys" in mine} for row, mine in zip(member_check.compute(rec)["rows"], calc.rows())], rec["id"]
        for key in calc.order:
            var = calc.vars[key]
            assert var["norm"] and var["source"] == timber_calc.SOURCE, (rec["id"], key)
        for step in calc.steps:
            assert step["result"] in calc.vars and all(u in calc.vars for u in step["uses"]), (rec["id"], step)
            assert step["norm"] == calc.vars[step["result"]]["norm"], (rec["id"], step["result"])
