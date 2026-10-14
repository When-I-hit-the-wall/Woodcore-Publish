"""Typst's diagnostics read once (calc/typst_diagnostics.py; spec docs/requirements/completed/2026-10-07-performance-erreurs-plans-legendes.md, REQ-011, ARCH-007): the file, the line and the column a notice opens, and Typst's own text kept as it was."""

import subprocess

import conftest
from conftest import Skip

import typst_diagnostics as td

HUMAN = """error: unknown variable: foo
  ┌─ \\\\?\\C:\\Users\\x\\bad.typ:3:1
  │
3 │ #foo
  │  ^^^
  = hint: if you meant to display multiple letters as is, try adding spaces

warning: unknown font family: nosuchfont
  ┌─ report.typ:12:7
  │
12 │ #text(font: "NoSuchFont")[a]
  │       ^^^^^^^^^^^^
"""

PANIC = """error: panicked with: "show-calc: no calculation named \\"x\\""
   ┌─ lib/calc-engine.typ:400:4
   │
400│     panic("show-calc: no calculation named ...")
   │     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
help: error occurred in this call of function `show-calc`
   ┌─ 3_Statischer Bericht/report.typ:22:1
   │
22 │ #show-calc("x")
   │ ^^^^^^^^^^^^^^^
"""


def test_the_human_format_gives_severity_message_place_and_hints():
    found = td.parse(HUMAN)
    assert [d.severity for d in found] == ["error", "warning"]
    error, warning = found
    assert error.message == "unknown variable: foo"
    assert (error.file, error.line, error.column) == ("C:\\Users\\x\\bad.typ", 3, 1), "the long-form prefix is dropped"
    assert error.hints and error.hints[0].startswith("if you meant")
    assert "#foo" in error.raw, "Typst's own text is kept"
    assert (warning.file, warning.line, warning.column) == ("report.typ", 12, 7)
    assert td.errors(HUMAN) == [error] and td.warnings(HUMAN) == [warning]


def test_a_panic_keeps_its_place_and_the_call_it_happened_in():
    (panic,) = td.parse(PANIC)
    assert panic.message.startswith("panicked with:")
    assert (panic.file, panic.line) == ("lib/calc-engine.typ", 400)
    assert panic.trace == [("3_Statischer Bericht/report.typ", 22, 1, "error occurred in this call of function `show-calc`")]
    assert panic.where() == "lib/calc-engine.typ:400:4"


def test_the_short_format_is_read_the_same():
    text = "\\\\?\\C:\\p\\bad.typ:3:1: error: unknown variable: foo\nC:\\p\\bad.typ:3:1: hint: try this\nwarn.typ:2:5: warning: unknown font family: x\n"
    error, warning = td.parse(text)
    assert (error.severity, error.file, error.line, error.column, error.message) == ("error", "C:\\p\\bad.typ", 3, 1, "unknown variable: foo")
    assert error.hints == ["try this"]
    assert (warning.severity, warning.file, warning.line) == ("warning", "warn.typ", 2)


def test_nothing_to_read_is_no_diagnostic():
    assert td.parse("") == [] and td.parse(None) == [] and td.parse("compiled in 2.1 s\n") == []


def test_a_real_compile_of_typst_is_read_at_its_line():
    if not conftest.have_typst():
        raise Skip("typst is not on the path")
    folder = conftest.tmpdir("typst-diagnostics")
    source = folder / "bad.typ"
    source.write_text("= Titre\n\n#foo\n", encoding="utf-8")
    import project
    done = subprocess.run([project.typst_executable(), "compile", str(source), str(folder / "bad.pdf")], capture_output=True, text=True, encoding="utf-8")
    (error,) = td.errors(done.stderr)
    assert error.line == 3 and error.message == "unknown variable: foo", done.stderr
    assert error.file.endswith("bad.typ")
