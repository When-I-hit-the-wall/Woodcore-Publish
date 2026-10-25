"""A check unfolded into a domain of the «Formules» tab (calc/domains/unfold.py; spec docs/requirements/completed/2026-10-15-calculs-deplies-balises-figures-natives.md).

What is held here, step by step of the spec's plan: what a domain holds is read from the compiler -- every command's `<woodcore-var>` metadata (REQ-004) --, including a line written by hand that no parser of Woodcore was taught; and the constants Python and Typst share are equal.

⚠️ Skipped where `typst` is not on the path.
"""

TIER = "fast"  # tests/run_tests.py --fast

import re

import conftest
from conftest import ROOT, Skip

from domains import unfold

FORMULA_TYP = ROOT / "lib" / "formula.typ"


def _need_typst():
    if not conftest.have_typst():
        raise Skip("typst is not on the path")


def _domain_file(name, body):
    """A domain file written into the session project's Formules/, as the tab writes one: the import line, then the body."""
    folder = conftest.PROJECT.formulas_dir
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{name}.typ"
    path.write_text('#import "/000-Typst-Config/commands.typ": *\n\n' + body + "\n", encoding="utf-8")
    return path


def test_the_shared_constants_are_typst_s():
    """The label every command's metadata carries and the two tolerances of a checked literal are written in lib/formula.typ and here, and must agree: a Python that wrote values at another precision than Typst compares them at would turn every unfolded line stale."""
    text = FORMULA_TYP.read_text(encoding="utf-8")
    assert f"<{unfold.META_LABEL}>" in text
    assert float(re.search(r"#let literal-tolerance = ([0-9.e-]+)", text).group(1)) == unfold.LITERAL_TOLERANCE
    assert float(re.search(r"#let literal-rounding = ([0-9.e-]+)", text).group(1)) == unfold.LITERAL_ROUNDING


def test_a_domain_says_what_it_holds_through_typst():
    """REQ-004: `query_state` reads the metadata of a domain compiled alone -- the domain itself, each var with its value, what domain: read and whether it is stale, each eq with its answer, each verify with its id and whether it holds -- in file order."""
    _need_typst()
    path = _domain_file("unfold-probe-state", '''#domain("unfold-probe-state", label: "Probe")[
#var("F", 7, "kN")
#var("s_k", 1.5, "kN/m²", domain: ("snow-load", "SL"))
#var("A", 2, "m²", level: 0)
#eq("q", `F / A`, unit: "kN/m²")
#verify(`q <= 5 "kN/m²"`, id: "v1")
]''')
    try:
        entries, where = unfold.query_state(conftest.PROJECT, path)
    finally:
        path.unlink()
    assert where == "file"
    kinds = [(e["kind"], e.get("key") or e.get("id")) for e in entries]
    assert kinds == [("domain", None), ("var", "F"), ("var", "s_k"), ("var", "A"), ("eq", "q"), ("verify", "v1")], kinds
    head, f, s_k, a, q, v = entries
    assert f["value"] == 7 and f["unit"] == "kN" and f["stale"] is None
    assert s_k["from"] == ["snow-load", "SL"] and s_k["stale"]["unit"] == "kN/m²", s_k
    assert a["level"] == 0, "a line at level 0 prints nothing and still says what it holds"
    assert abs(q["value"] - 3.5) < 1e-9 and q["unit"] == "kN/m²", q
    assert v["holds"] is True


def test_a_line_written_by_hand_is_read_without_a_parser():
    """REQ-004: what the engineer adds in VS Code -- here an eq inside a sentence's paragraph, after a blank line -- is listed as Typst computed it, and no code of Woodcore's had to learn its form."""
    _need_typst()
    path = _domain_file("unfold-probe-hand", '''#domain("unfold-probe-hand")[
Die Kraft beträgt
  #var("F", 2, "kN",
       label: "Kraft")   // a comment Woodcore's own writer would not keep

und das Moment #eq("M", `F dot 3 "m"`, unit: "kNm").
]''')
    try:
        entries, _ = unfold.query_state(conftest.PROJECT, path)
    finally:
        path.unlink()
    assert [(e["kind"], e.get("key")) for e in entries] == [("domain", None), ("var", "F"), ("eq", "M")]
    assert abs(entries[2]["value"] - 6) < 1e-9


def test_a_domain_that_does_not_compile_is_said_with_its_code():
    """A domain whose own Typst is wrong, and which no report prints, is refused with `does_not_compile` and Typst's message -- never an empty state that would read as «nothing here»."""
    _need_typst()
    path = _domain_file("unfold-probe-broken", '#domain("unfold-probe-broken")[\n#var("F", 2, "kN"\n]')
    try:
        try:
            unfold.query_state(conftest.PROJECT, path)
        except unfold.UnfoldError as exc:
            assert exc.code == "does_not_compile", exc.code
        else:
            raise AssertionError("a domain that does not compile was read")
    finally:
        path.unlink()


def _probe(body):
    """Compiles `body` against the session project's commands: ("ok", what it put in `<out>`) or ("error", the panic)."""
    import test_formula
    return test_formula._run(body)


def test_a_check_printed_unfolded_is_read_by_domain():
    """ARCH-007: `#var(key, value, domain: ("check", id))` checks a literal against the `vars` the export publishes for an unfolded check, the record's provenance kept; a check that is not unfolded publishes nothing and says so."""
    _need_typst()
    kind, got = _probe('#var("N_t_d", 25, "kN", domain: ("check", "ZT-01"))\n#context [#metadata(var-lookup(var-registry.get(), "N_t_d").source) <out>]')
    assert (kind, got) == ("ok", "python:domains/member_check.py"), got
    kind, got = _probe('#var("N_t_d", 26, "kN", domain: ("check", "ZT-01"))\n#context [#metadata(query(<woodcore-var>).first().value.stale) <out>]')
    assert kind == "ok" and got["value"] == 25 and got["unit"] == "kN", got
    # every check of the example is printed unfolded since the spec 2026-10-21-commandes-typst-refonte (REQ-017): a check gone from the export publishes nothing
    kind, got = _probe('#var("N", 2, domain: ("check", "ZZ-99"))')
    assert kind == "error" and "ZZ-99" in got, got


# --- the writer (REQ-002, ARCH-002) ------------------------------------------------------------

def _record(**change):
    """A tension resolved against the session project's positions -- ZT-01's own, with `change` written over it."""
    import json
    from domains import connector, member_check
    src = json.loads((conftest.PROJECT.checks_dir / "ZT-01.json").read_text(encoding="utf-8"))
    src.update(change)
    return member_check.resolve(src, connector.known_positions(conftest.PROJECT.data_dir))


def _unfolded_state(record, name):
    """The domain `record` unfolds to, written into the session project under `name` and read back through Typst: {key or id: metadata}."""
    import project
    from domains import connector, member_check
    _need_typst()
    with project.using(conftest.PROJECT):
        text = unfold.generate(record, "de").replace(f'"{record["id"]}"', f'"{name}"')
    # the export the literals are checked against carries this very record, under the probe's name
    data = member_check.prepare(conftest.PROJECT, connector.known_positions(conftest.PROJECT.data_dir))
    data["checks"][name] = dict(record, id=name, vars=member_check.published_vars(record), gen=member_check.form_of(record))
    member_check.write(data, conftest.PROJECT.data_dir)
    path = _domain_file(name, text.split("\n", 2)[2])
    try:
        entries, _ = unfold.query_state(conftest.PROJECT, path)
    finally:
        path.unlink()
    return text, {e.get("key") or e.get("id") or "domain": e for e in entries}


def test_an_unfolded_tension_computes_what_compute_computes():
    """REQ-002, ARCH-002: the domain written for a tension along the grain, across it and at an angle compiles, and every row of `member_check.compute` is in its registry within 1e-6 -- η in percent --, no literal stale, the relation holding as compute says, each derived value citing SIA 265 and its clause, and no tag."""
    from domains import member_check
    for alpha in (0, 30, 90):
        record = _record(alpha=alpha)
        text, state = _unfolded_state(record, f"ZT-T{alpha}")
        assert "// woodcore:" not in text
        result = member_check.compute(record)
        for row in result["rows"]:
            got = state[row["key"]]
            value = got["value"] / 100 if row["key"] == "eta" else got["value"]
            assert abs(value - row["value"]) <= 1e-6 * max(1, abs(row["value"])), (alpha, row["key"], value, row["value"])
            assert not got.get("stale"), (alpha, row["key"], got)
        verdict = next(e for e in state.values() if e["kind"] == "verify")
        assert verdict["holds"] == result["ok"]
        # the form is the base's, not the file's (spec 2026-10-21-commandes-typst-refonte, REQ-012): the file is a #domain without gen:
        assert state["domain"]["matches"] is True and "gen:" not in text and member_check.form_of(record)["form"] == result["equation"]
        for row in result["rows"]:
            if row.get("clause") and row.get("keys") and row["key"] != "eta":
                assert f'norm-section: "{row["clause"]}"' in text, (alpha, row["key"])


def test_the_writer_is_pure_and_writes_a_check_once_with_its_base():
    """ARCH-RISK-211, REQ-007: the same record gives the same bytes; `unfold_checks` writes the domain of each unfolded check the project does not hold yet, with its base -- a second run writes nothing --, and the base holds its schema."""
    import project
    from domains import connector, member_check
    here = conftest.project_copy("unfold_writer")
    with project.using(here):
        import json
        record = member_check.resolve(json.loads((here.checks_dir / "ZT-01.json").read_text(encoding="utf-8")), connector.known_positions(here.data_dir))
        assert unfold.generate(record, "de") == unfold.generate(record, "de")
        # the example project carries its tensions unfolded: taken out, so that the writer has them to write
        for rid in ("ZT-01", "ZT-02"):
            unfold.domain_path(here, rid).unlink(missing_ok=True)
        unfold.base_path(here).unlink(missing_ok=True)
        data = member_check.prepare(here, connector.known_positions(here.data_dir))
        written = unfold.unfold_checks(here, data, lang="de")
        assert "ZT-01" in written and unfold.domain_path(here, "ZT-01").is_file()
        assert unfold.unfold_checks(here, data, lang="de") == []
        base = unfold.read_base(here)
        entry = base["domains"]["ZT-01"]
        assert entry["gen"] == member_check.form_of(record)
        assert {"var:N_t_d", "eq:sigma_t_0_d", "verify:v-6", "label:ZT-01-member"} <= set(entry["lines"]), sorted(entry["lines"])
        before = unfold.base_path(here).read_bytes()
        unfold.write_base(here, base)
        assert unfold.base_path(here).read_bytes() == before


# --- the states of the lines, and what Woodcore does with them (REQ-006 to REQ-010) ---------------------------

def _unfolded_project(name):
    """A copy of the example project with ZT-01 unfolded the way a save does it: (project, path of Formules/ZT-01.typ)."""
    import project
    from domains import member_check
    here = conftest.project_copy(name)
    with project.using(here):
        member_check.export(here)
    path = unfold.domain_path(here, "ZT-01")   # Timber-checks/Tension/ laid out by folders (issue #64)
    assert path.is_file()
    return here, path


def _states(here):
    return {line.id: line.state for line in unfold.status(here, "ZT-01", "de").lines}


def _set_source(here, **change):
    import json
    import project
    from domains import member_check
    src = json.loads((here.checks_dir / "ZT-01.json").read_text(encoding="utf-8"))
    src.update(change)
    with project.using(here):
        member_check.write_source(here, src)
        member_check.export(here)


def test_a_line_whose_data_changed_follows_it_and_nothing_else_of_the_file_moves():
    """REQ-007, REQ-008: just written, every line is in step; N changed in the check's source makes N's line `data` -- and the export that follows rewrites that one argument, a comment and a sentence written by hand elsewhere in the file kept byte for byte."""
    here, path = _unfolded_project("unfold_data")
    assert set(_states(here).values()) == {"in_sync"}, _states(here)
    text = path.read_text(encoding="utf-8")
    hand = text.replace("  #var(\"b\"", "Ein Satz des Ingenieurs.\n  #var(\"b\"").replace('level: 0)\n  #var("h"', 'level: 0)   // mein Kommentar\n  #var("h"')
    path.write_text(hand, encoding="utf-8")
    import json
    import project
    from domains import connector, member_check
    src = json.loads((here.checks_dir / "ZT-01.json").read_text(encoding="utf-8"))
    src["N"] = {"value": 28, "unit": "kN"}
    with project.using(here):
        member_check.write_source(here, src)
        data = member_check.prepare(here, connector.known_positions(here.data_dir))
        member_check.write(data, here.data_dir)
        assert _states(here)["var:N_t_d"] == "data"
        unfold.unfold_checks(here, data, lang="de")
    after = path.read_text(encoding="utf-8")
    assert after == hand.replace('#var("N_t_d", "N_(t,d)", 25, "kN"', '#var("N_t_d", "N_(t,d)", 28, "kN"'), after
    assert set(_states(here).values()) == {"in_sync"}


def test_a_line_the_engineer_laid_out_keeps_its_layout_when_its_value_is_refreshed_or_made_his_own():
    """ARCH-003 (spec 2026-10-15): N written over two lines with a comment inside the call, and the value of the norm's table with a comment after it -- the export's new N replaces that one argument, «Importer» takes its `id:` away (spec 2026-10-21-commandes-typst-refonte, Q-006: a line without one is the engineer's), «Reprendre» puts it back; every other byte of the two lines kept."""
    here, path = _unfolded_project("unfold_layout")
    text = path.read_text(encoding="utf-8")
    n_line = '  #var("N_t_d", "N_(t,d)", 25, "kN", domain: ("check", "ZT-01"), id: "N_t_d")'
    n_laid = '  #var("N_t_d", "N_(t,d)", 25, "kN",   // aus dem Statikmodell\n       domain: ("check", "ZT-01"), id: "N_t_d")'
    assert n_line in text
    f_line = next(line for line in text.split("\n") if '#var("f_t_0_d_tab"' in line)
    hand = text.replace(n_line, n_laid).replace(f_line, f_line + "  // Tabelle 7")
    path.write_text(hand, encoding="utf-8")
    assert set(_states(here).values()) == {"in_sync"}, _states(here)
    _set_source(here, N={"value": 28, "unit": "kN"})
    refreshed = hand.replace('25, "kN",   // aus', '28, "kN",   // aus')
    assert path.read_text(encoding="utf-8") == refreshed, path.read_text(encoding="utf-8")
    import project
    mine = f_line.replace(", 8.5,", ", 9,")
    assert mine != f_line
    path.write_text(refreshed.replace(f_line, mine), encoding="utf-8")
    with project.using(here):
        unfold.import_lines(here, "ZT-01", ["var:f_t_0_d_tab"], lang="de")
        assert path.read_text(encoding="utf-8") == refreshed.replace(f_line + "  // Tabelle 7", mine.replace(', id: "f_t_0_d_tab"', "") + "  // Tabelle 7")
        unfold.take_back(here, "ZT-01", "var:f_t_0_d_tab", lang="de")
    assert path.read_text(encoding="utf-8") == refreshed
    assert set(_states(here).values()) == {"in_sync"}, _states(here)


def test_a_value_changed_in_vs_code_goes_back_into_the_check_s_source():
    """REQ-009 (a): N changed in the file is `local`; «Importer» writes it into checks/ZT-01.json -- the «Traction» tab then shows it -- and the line is in step with the export written again."""
    import json
    here, path = _unfolded_project("unfold_import_source")
    path.write_text(path.read_text(encoding="utf-8").replace('"N_(t,d)", 25, "kN"', '"N_(t,d)", 30, "kN"'), encoding="utf-8")
    assert _states(here)["var:N_t_d"] == "local"
    import project
    with project.using(here):
        done = unfold.import_lines(here, "ZT-01", ["var:N_t_d"], lang="de")
    assert done == {"imported": ["var:N_t_d"], "conflicts": []}
    assert json.loads((here.checks_dir / "ZT-01.json").read_text(encoding="utf-8"))["N"] == {"value": 30, "unit": "kN"}
    assert _states(here)["var:N_t_d"] == "in_sync"
    assert '"N_(t,d)", 30, "kN"' in path.read_text(encoding="utf-8")


def test_a_value_of_the_norm_changed_in_vs_code_becomes_the_engineer_s_own_and_is_taken_back():
    """REQ-009 (b), D-13: a value of the norm's table cannot go back into the source: «Importer» takes its `id:` away -- the line is then the engineer's, never refreshed (spec 2026-10-21-commandes-typst-refonte, Q-006, where `own: true` was written until then) --, and «Reprendre» puts the export's value and the `id:` back."""
    here, path = _unfolded_project("unfold_own")
    path.write_text(path.read_text(encoding="utf-8").replace('"f_(t,0,d,\\"Tab\\")", 8.5', '"f_(t,0,d,\\"Tab\\")", 9'), encoding="utf-8")
    assert _states(here)["var:f_t_0_d_tab"] == "local"
    import project
    with project.using(here):
        unfold.import_lines(here, "ZT-01", None, lang="de")
        text = path.read_text(encoding="utf-8")
        line = next(l for l in text.split("\n") if '#var("f_t_0_d_tab"' in l)
        assert 'id: "f_t_0_d_tab"' not in line and ', 9, "N/mm²"' in line and "own:" not in line, line
        assert _states(here)["var:f_t_0_d_tab"] == "own"
        assert unfold.refresh(here, "ZT-01", "de") == []
        unfold.take_back(here, "ZT-01", "var:f_t_0_d_tab", lang="de")
    text = path.read_text(encoding="utf-8")
    assert "own: true" not in text and '8.5, "N/mm²", domain: ("check", "ZT-01"), id: "f_t_0_d_tab")' in text, text
    assert _states(here)["var:f_t_0_d_tab"] == "in_sync"


def test_a_formula_changed_in_vs_code_is_taken_as_written_and_a_conflict_waits_for_a_choice():
    """REQ-009, REQ-010: an `#eq` changed in the file is imported as the engineer wrote it and stays so; a line changed in the file and by the export is a conflict, imported only with a choice -- «theirs» writes the export's."""
    here, path = _unfolded_project("unfold_conflict")
    path.write_text(path.read_text(encoding="utf-8").replace("`N_t_d / A`", "`N_t_d / (A)`"), encoding="utf-8")
    import project
    with project.using(here):
        assert unfold.import_lines(here, "ZT-01", lang="de")["imported"] == ["eq:sigma_t_0_d"]
        assert _states(here)["eq:sigma_t_0_d"] == "in_sync"
        path.write_text(path.read_text(encoding="utf-8").replace('"N_(t,d)", 25, "kN"', '"N_(t,d)", 31, "kN"'), encoding="utf-8")
    _set_source(here, N={"value": 27, "unit": "kN"})
    assert _states(here)["var:N_t_d"] == "conflict"
    with project.using(here):
        assert unfold.import_lines(here, "ZT-01", lang="de") == {"imported": [], "conflicts": ["var:N_t_d"]}
        unfold.import_lines(here, "ZT-01", choices={"var:N_t_d": "theirs"}, lang="de")
    assert '"N_(t,d)", 27, "kN"' in path.read_text(encoding="utf-8") and _states(here)["var:N_t_d"] == "in_sync"
    assert "`N_t_d / (A)`" in path.read_text(encoding="utf-8"), "the formula taken as written was lost"


def test_a_line_taken_out_is_said_and_put_back_where_it_was():
    """REQ-006: the line of f_t,0,d deleted in VS Code is `missing`; «Réinsérer» puts it back before σ_t,0,d, where the writing has it. A line set to level 0 is no deletion."""
    here, path = _unfolded_project("unfold_missing")
    text = path.read_text(encoding="utf-8")
    line = next(l for l in text.split("\n") if l.strip().startswith('#eq("f_t_0_d"'))
    path.write_text(text.replace(line + "\n", ""), encoding="utf-8")
    assert _states(here)["eq:f_t_0_d"] == "missing"
    import project
    with project.using(here):
        unfold.reinsert(here, "ZT-01", "eq:f_t_0_d", lang="de")
    lines = path.read_text(encoding="utf-8").split("\n")
    assert lines.index(line) < next(i for i, l in enumerate(lines) if '#eq("sigma_t_0_d"' in l)
    assert _states(here)["eq:f_t_0_d"] == "in_sync"
    path.write_text(path.read_text(encoding="utf-8").replace('#var("eta_t", 1, domain: ("check", "ZT-01"), note: "line")', '#var("eta_t", 1, domain: ("check", "ZT-01"), note: "line", level: 0)'), encoding="utf-8")
    assert _states(here)["var:eta_t"] != "missing"


def test_regenerate_follows_a_new_form_and_keeps_what_the_engineer_wrote():
    """REQ-010, REQ-003: α moved from 0 to 30° in the check -- the domain says it no longer matches; «Régénérer» writes (8)/(9) -- f_t,α,d and σ_t,α,d in, σ_t,0,d out --, keeps a sentence and an #eq the engineer added and his own η_t, and keeps the new form in the base (spec 2026-10-21-commandes-typst-refonte, REQ-012: no `gen:` in the file)."""
    here, path = _unfolded_project("unfold_regenerate")
    text = path.read_text(encoding="utf-8")
    text = text.replace('  #var("eta_t", 1, domain: ("check", "ZT-01"), id: "eta_t")', '  #var("eta_t", 1, domain: ("check", "ZT-01"), id: "eta_t", level: 3)')
    text = text.replace('  #verify(', 'Mein eigener Satz.\n  #eq("k_extra", `2 * eta_t`)\n  #verify(', 1)
    path.write_text(text, encoding="utf-8")
    _set_source(here, alpha=30)
    status = unfold.status(here, "ZT-01", "de")
    assert not status.matches
    import project
    with project.using(here):
        assert unfold.regenerate(here, "ZT-01", lang="de") == {"conflicts": []}
    after = path.read_text(encoding="utf-8")
    assert unfold.read_base(here)["domains"]["ZT-01"]["gen"]["form"] == "(8)/(9)" and "gen:" not in after
    assert '#eq("f_t_alpha_d"' in after and '#eq("sigma_t_alpha_d"' in after
    assert '#eq("sigma_t_0_d"' not in after
    assert "Mein eigener Satz." in after and '#eq("k_extra", `2 * eta_t`)' in after
    assert 'id: "eta_t", level: 3)' in after, "the engineer's eta_t was not kept"
    assert unfold.status(here, "ZT-01", "de").matches


def test_an_import_that_cannot_finish_writes_nothing():
    """CON-005, ARCH-RISK-206: the domain and its base are written at once -- a failure writing the second puts the first back."""
    import sharing
    here, path = _unfolded_project("unfold_atomic")
    path.write_text(path.read_text(encoding="utf-8").replace("`N_t_d / A`", "`N_t_d / (A)`"), encoding="utf-8")
    before = (path.read_bytes(), unfold.base_path(here).read_bytes())
    put, calls = sharing._put, []

    def failing(where, data):
        calls.append(where)
        if len(calls) == 2:
            raise OSError("disk full")
        put(where, data)
    sharing._put = failing
    try:
        import project
        with project.using(here):
            try:
                unfold.import_lines(here, "ZT-01", lang="de")
            except Exception:
                pass
    finally:
        sharing._put = put
    assert (path.read_bytes(), unfold.base_path(here).read_bytes()) == before


def test_the_command_line_says_and_does_what_the_tab_does():
    """ARCH-005: `woodcore-cli unfold status` lists a changed line in the project's language, and `import` refuses a conflict without a choice -- exit 1, nothing written -- and imports a local line, the very functions the tab calls."""
    import argparse
    import contextlib
    import io
    import cli_unfold
    import project
    here, path = _unfolded_project("unfold_cli")
    path.write_text(path.read_text(encoding="utf-8").replace("`N_t_d / A`", "`N_t_d / (A)`"), encoding="utf-8")
    out = io.StringIO()
    with project.using(here), contextlib.redirect_stdout(out):
        assert cli_unfold.run(argparse.Namespace(action="status", check=None, lang="fr")) == 0
    assert "ZT-01" in out.getvalue() and "eq:sigma_t_0_d : modifiée dans le fichier" in out.getvalue(), out.getvalue()
    with project.using(here), contextlib.redirect_stdout(io.StringIO()):
        assert cli_unfold.run(argparse.Namespace(action="import", check="ZT-01", line=None, choice=None, lang="en")) == 0
    assert _states(here)["eq:sigma_t_0_d"] == "in_sync"


# --- the migration (REQ-011, REQ-012, D-09, CON-004) ----------------------------------------------------------

def test_each_state_of_a_line_and_a_base_that_does_not_read():
    """REQ-007: on ZT-01's N line, the four states one after the other -- nothing changed `in_sync`, the export alone `data`, the file alone `local`, both `conflict` --; and a base Woodcore wrote that does not read stops, naming the file and the field (a malformed file stops)."""
    import json
    import validation
    here, path = _unfolded_project("unfold_states")
    assert _states(here)["var:N_t_d"] == "in_sync"

    def export_checks_only(**change):
        # the check's export written, not yet the refresh an export runs after it (REQ-008): what `data` is between the two
        from domains import connector, member_check
        src = json.loads((here.checks_dir / "ZT-01.json").read_text(encoding="utf-8"))
        src.update(change)
        with project.using(here):
            member_check.write_source(here, src)
            member_check.write(member_check.prepare(here, connector.known_positions(here.data_dir)), here.data_dir)
    import project
    export_checks_only(N={"value": 27, "unit": "kN"})
    assert _states(here)["var:N_t_d"] == "data"
    with project.using(here):
        unfold.refresh(here, "ZT-01", "de")
    path.write_text(path.read_text(encoding="utf-8").replace('"N_(t,d)", 27, "kN"', '"N_(t,d)", 31, "kN"'), encoding="utf-8")
    assert _states(here)["var:N_t_d"] == "local"
    export_checks_only(N={"value": 29, "unit": "kN"})
    assert _states(here)["var:N_t_d"] == "conflict"
    base = json.loads(unfold.base_path(here).read_text(encoding="utf-8"))
    base["domains"]["ZT-01"]["lines"]["var:N_t_d"] = "not a pair"
    unfold.base_path(here).write_text(json.dumps(base), encoding="utf-8")
    try:
        unfold.read_base(here)
    except validation.ValidationError as exc:
        assert "Timber-checks/unfold.json" in str(exc) and "var:N_t_d" in str(exc), str(exc)
    else:
        raise AssertionError("a base that does not read was read")


def test_the_example_projects_unfolded_checks_are_written_byte_for_byte_as_held():
    """ARCH-RISK-204 (spec 2026-10-19-base-saine-nettoyage, lot 7): the rows of member_check now name their norm and the values entered cite the clause they serve -- what `generate` writes for every unfolded check of the example project is still, to the byte, the file Timber-checks/ holds."""
    from domains import member_check
    import json
    import project
    # the committed example's own export and files: a test of this process may have added checks to its copy
    sample = project.Project.load(conftest.SAMPLE)
    checks = json.loads((sample.data_dir / member_check.EXPORT_FILE).read_text(encoding="utf-8"))["checks"]
    seen = 0
    for rid, record in checks.items():
        if not member_check.is_unfolded(record):
            continue
        path = unfold.domain_path(sample, rid, record)
        assert path.is_file(), path
        assert unfold.generate(record) == path.read_text(encoding="utf-8"), f"{rid}: the unfolded file is no longer written as the project holds it"
        seen += 1
    assert seen >= 2, "the example project unfolds fewer checks than it did -- the test would hold nothing"


def test_a_domain_that_keeps_a_line_the_writer_no_longer_writes_is_in_step():
    """Spec 2026-10-22-retrait-niveau-manuel, REQ-007, CON-001, D-4: a compression along the grain written before the writer stopped writing its `eta_s` row keeps that line, inert -- its form still matches, no line is missing or in conflict, an export refreshes nothing and says nothing in red; `regenerate` -- «Régénérer», which the window offers only once the form changes -- takes the line out since he did not change it."""
    import json
    import project
    from domains import member_check
    here = conftest.project_copy("unfold_stale_line")
    with project.using(here):
        member_check.export(here)   # the copy holds no domain's file: the export writes them
        record = json.loads((here.data_dir / member_check.EXPORT_FILE).read_text(encoding="utf-8"))["checks"]["DR-02"]
        path = unfold.domain_path(here, "DR-02", record)
        text = path.read_text(encoding="utf-8")
        assert 'id: "eta_s"' not in text, "the writer no longer writes the line"
        # the file as a Woodcore before this spec wrote it: the section's verdict once more before the check, recorded in the base
        text = text.replace("  #verify(", '  #eq("eta_s", `sigma_c_0_d / f_c_0_d`, id: "eta_s")\n  #verify(', 1)
        path.write_text(text, encoding="utf-8")
        base = unfold.read_base(here)
        digest = unfold.line_digests(text)["eq:eta_s"]
        base["domains"]["DR-02"]["lines"]["eq:eta_s"] = [digest, digest]
        unfold.write_base(here, base)
        st = unfold.status(here, "DR-02")
        assert st.unfolded and st.matches and not st.of("missing") and not st.of("conflict"), st
        assert unfold.refresh(here, "DR-02") == []
        data = member_check.export(here)
        entry = unfold.domain_state(here, data, "de")["domains"]["DR-02"]
        assert entry["matches"] is True and entry["missing"] == [] and entry["conflict"] == [], entry
        assert path.read_text(encoding="utf-8") == text, "the export does not touch the file"
        assert unfold.regenerate(here, "DR-02") == {"conflicts": []}
        after = path.read_text(encoding="utf-8")
        assert 'id: "eta_s"' not in after and 'id: "eta"' in after, after


def test_a_domain_that_no_longer_matches_its_data_says_so_in_red_and_is_not_rewritten():
    """Spec 2026-10-21-commandes-typst-refonte, REQ-012, ARCH-007, ARCH-008: α moved to 30° in the check's source -- its domain was written for (6) and its data now asks for (8)/(9). The export computes where the domain stands (`domain_state`: the two forms, `matches` false), lists its file (`domain_files`), and `#domain` prints the red line at its head from data/domain-state.json, included by `domain-file("check", id)`; the file, the engineer's, is not rewritten for it."""
    import json
    import subprocess
    import engine
    import project
    from domains import member_check
    here, path = _unfolded_project("unfold_state")
    before = path.read_text(encoding="utf-8")
    _set_source(here, alpha=30)
    with project.using(here):
        data = member_check.export(here)
        state = unfold.domain_state(here, data, "de")
        files = unfold.domain_files(here, data)
    entry = state["domains"]["ZT-01"]
    assert entry["matches"] is False and entry["written"]["form"] == "(6)" and entry["form"]["form"] == "(8)/(9)" and entry["check"] == "tension", entry
    assert files["files"]["check"]["ZT-01"] == here.from_root(path)
    assert path.read_text(encoding="utf-8") == before, "the file is the engineer's: the export does not rewrite it for a new form"
    # printed: the state put in the report's own copy of the example (which holds the engine and ZT-01 as written), and taken back after
    if not conftest.have_typst():
        return
    report = conftest.PROJECT
    held = (report.data_dir / unfold.STATE_FILE).read_bytes()
    try:
        engine.write_json(report.data_dir / unfold.STATE_FILE, {"schema_version": "1.0", "domains": {"ZT-01": dict(entry, file="/Timber-checks/Tension/ZT-01.typ")}})
        d = conftest.probe_dir("unfold_state")
        probe = d / "probe.typ"
        probe.write_text('#import "/000-Typst-Config/commands.typ": *\n#include domain-file("check", "ZT-01")\n', encoding="utf-8")
        out = subprocess.run(["typst", "compile", "--root", str(conftest.TYPST_ROOT), str(probe), str(d / "probe.pdf")], capture_output=True, text=True, encoding="utf-8")
        assert out.returncode == 0, out.stderr
        from pypdf import PdfReader
        text = " ".join(" ".join(page.extract_text() for page in PdfReader(str(d / "probe.pdf")).pages).split())
        assert "entspricht nicht mehr den Daten" in text and "(6) (tension, v2) statt (8)/(9) (tension, v2)" in text, text[:400]
    finally:
        (report.data_dir / unfold.STATE_FILE).write_bytes(held)
    json.loads(held.decode("utf-8"))


def test_every_kind_of_member_check_unfolded_computes_what_compute_computes():
    """Spec 2026-10-21-commandes-typst-refonte, REQ-017, ARCH-003, ARCH-RISK-209: every check of the example project -- tension, compression, bending, shear, buckling, lateral torsional buckling, and in the fire situation -- is written unfolded, compiles, and every row of `member_check.compute` is in its registry within 1e-6 (η in percent), no literal stale, the relation holding as compute says. Once the `#verify-*` are gone this is what holds Python and the report equal: the compiled file against the rows."""
    import json
    from domains import member_check
    assert set(unfold.UNFOLDED_KINDS) == set(member_check.IMPLEMENTED)
    checks = json.loads((conftest.PROJECT.data_dir / "checks.json").read_text(encoding="utf-8"))["checks"]
    seen = set()
    for rid, record in sorted(checks.items()):
        if not record.get("calculable"):
            continue
        seen.add((record["kind"], bool(record.get("fire"))))
        result = member_check.compute(record)
        text, state = _unfolded_state(record, f"U-{rid}")
        for row in result["rows"]:
            got = state.get(row["key"])
            assert got is not None, (rid, row["key"], sorted(state))
            value = got["value"] / 100 if row["key"] == "eta" else got["value"]
            assert abs(value - row["value"]) <= 1e-6 * max(1, abs(row["value"])), (rid, row["key"], value, row["value"])
            assert not got.get("stale"), (rid, row["key"], got)
        verdict = next(e for e in state.values() if e["kind"] == "verify")
        assert verdict["holds"] == result["ok"], rid
    assert {kind for kind, _fire in seen} == set(member_check.IMPLEMENTED) and (("bending", True) in seen or ("buckling", True) in seen), seen


def test_a_shear_off_and_a_shear_across_the_grain_unfolded_compute_what_python_computes():
    """REQ-021, ARCH-RISK-209: the two shear variants Python now computes are written unfolded, compile, and their every row is in the registry within 1e-6, the verdict compute's."""
    from domains import connector, member_check
    for name, change in (("SO", {"variant": "shear-off", "F": {"value": 20, "unit": "kN"}, "l": 200, "w": None}),
                         ("SP", {"variant": "shear-perp", "V_z": {"value": 12, "unit": "kN"}, "sigma_90": -1.2})):
        src = member_check.new_source("X-" + name, "shear")
        src.update(position="T001", **change)
        record = member_check.resolve(src, connector.known_positions(conftest.PROJECT.data_dir))
        result = member_check.compute(record)
        _text, state = _unfolded_state(record, "U-" + name)
        for row in result["rows"]:
            value = state[row["key"]]["value"] / 100 if row["key"] == "eta" else state[row["key"]]["value"]
            assert abs(value - row["value"]) <= 1e-6 * max(1, abs(row["value"])), (name, row["key"], value, row["value"])
            assert not state[row["key"]].get("stale"), (name, row["key"])
        assert next(e for e in state.values() if e["kind"] == "verify")["holds"] == result["ok"], name


def _polar_of_the_old_form(here):
    """The example's VU-MP-1 written back as Woodcore wrote a polar moment before the spec 2026-10-22-image-polar-moment -- its figure at its head, a plain image, no figure after the forces, its form without its last "-a" in the base --: the file of a project exported before, N, V and M the engineer's `#eq` as the example has them."""
    import json
    path = unfold.domain_path(here, "VU-MP-1", kind="connection")
    lines = path.read_text(encoding="utf-8").split("\n")
    figure = next(i for i, l in enumerate(lines) if "image-polar-moment" in l)
    del lines[figure - 1:figure + 2]
    member = next(i for i, l in enumerate(lines) if l.endswith("<VU-MP-1-member>"))
    lines[member + 2:member + 2] = ['#figure(image("/Connections/Exports/Figures/VU-MP-1-de.svg", width: 60%)) <VU-MP-1-figure>', ""]
    text = "\n".join(lines)
    path.write_text(text, encoding="utf-8", newline="\n")
    where = unfold.base_path(here, "connection")
    held = json.loads(where.read_text(encoding="utf-8"))
    entry = held["domains"]["VU-MP-1"]
    entry["gen"]["form"] = entry["gen"]["form"].removesuffix("-a")
    entry["lines"].pop("label:VU-MP-1-polar-figure")
    digest = unfold.line_digests(text)["figure:VU-MP-1-de.svg"]   # a figure of an image is found by its file since the spec 2026-10-22-onglet-neige-type (D-29)
    entry["lines"]["figure:VU-MP-1-de.svg"] = [digest, digest]
    where.write_text(json.dumps(held, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    return path


def test_a_polar_moment_of_the_old_form_is_regenerated_with_its_figure_after_the_forces():
    """Spec 2026-10-22-image-polar-moment, ARCH-003, REQ-003: the example's VU-MP-1.typ written back as an earlier Woodcore wrote it, its figure at its head, and N, V and M made the engineer's own `#eq` of N_Ed, V_Ed and M_Ed, no longer matches the polar moment's form -- the figure's line `missing`, N, V and M `own`. The export does not rewrite it, and it still compiles; «Régénérer» takes the head figure out and writes the one figure, drawn with its arrows, after the forces, the engineer's three `#eq` kept and never doubled by the writing's `#var`; «Réinsérer» puts the figure's line back there once deleted."""
    import json
    import project
    import test_position_list as base
    _need_typst()
    here = base._project("unfold_polar")
    path = _polar_of_the_old_form(here)
    before = path.read_text(encoding="utf-8")
    assert "<VU-MP-1-figure>" in before and "image-polar-moment" not in before, before[:600]

    def states():
        return {line.id: line.state for line in unfold.status(here, "VU-MP-1", "de", kind="connection").lines}

    status = unfold.status(here, "VU-MP-1", "de", kind="connection")
    assert not status.matches
    assert states()["label:VU-MP-1-polar-figure"] == "missing" and {states()[f"var:{k}"] for k in "NVM"} == {"own"}, states()
    data = json.loads((here.data_dir / "connections.json").read_text(encoding="utf-8"))
    with project.using(here):
        unfold.unfold_domains(here, "connection", data, lang="de")
        entry = unfold.domain_state(here, {}, "de", connections=data)["domains"]["VU-MP-1"]
    assert entry["matches"] is False, entry
    assert path.read_text(encoding="utf-8") == before, "the file is the engineer's: the export does not rewrite it for a new form"
    forces = '#var("N_Ed", 7.5, "kN")\n#var("V_Ed", 25, "kN")\n#var("M_Ed", 6.6, "kNm")\n#include domain-file("connection", "VU-MP-1")'
    base._text(here, forces, "unfold_polar_old")
    with project.using(here):
        assert unfold.regenerate(here, "VU-MP-1", lang="de", kind="connection") == {"conflicts": []}
    after = path.read_text(encoding="utf-8")
    lines = after.split("\n")
    figure = next(i for i, l in enumerate(lines) if "image-polar-moment" in l)
    assert after.count("#figure(") == 1 and "<VU-MP-1-figure>" not in after, after[:800]
    assert lines[figure].startswith('#figure(image-polar-moment("VU-MP-1", N: "N", V: "V", M: "M", width: 60%), kind: image, caption: [') and lines[figure].endswith("<VU-MP-1-polar-figure>"), lines[figure]
    m = next(i for i, l in enumerate(lines) if l.strip().startswith('#eq("M", `M_Ed`'))
    nx = next(i for i, l in enumerate(lines) if l.strip().startswith('#eq("N_x"'))
    assert m < figure < nx and lines[figure - 1] == "" and lines[figure + 1] == "", lines[m:nx + 1]
    assert not any(l.strip().startswith(('#var("N", 0', '#var("V", 0', '#var("M", 0')) for l in lines), "the writing's #var doubled the engineer's #eq"
    assert unfold.status(here, "VU-MP-1", "de", kind="connection").matches
    recorded = unfold.read_base(here, "connection")["domains"]["VU-MP-1"]["lines"]
    assert {"label:VU-MP-1-member", "label:VU-MP-1-forces", "label:VU-MP-1-table-1-note", "label:VU-MP-1-polar-figure"} <= set(recorded) and "figure:VU-MP-1-de.svg" not in recorded, sorted(recorded)
    text = base._text(here, forces, "unfold_polar_new")
    # numbered as a figure, and drawn from the file's N = N_Ed = 7.5 kN: its share N/n too small to make out, named in the legend's note (UI-001)
    assert "Abbildung 1: Anschluss VU-MP-1" in text and "Zu klein zum Erkennen: N/n = 1.88 kN" in text, text[:1600]
    path.write_text(after.replace(lines[figure] + "\n", ""), encoding="utf-8", newline="\n")
    assert states()["label:VU-MP-1-polar-figure"] == "missing"
    with project.using(here):
        unfold.reinsert(here, "VU-MP-1", "label:VU-MP-1-polar-figure", lang="de", kind="connection")
    again = path.read_text(encoding="utf-8").split("\n")
    assert m < again.index(lines[figure]) < next(i for i, l in enumerate(again) if l.strip().startswith('#eq("N_x"')), again[m:nx + 2]
    assert states()["label:VU-MP-1-polar-figure"] == "in_sync"


# --- the wind's file (spec 2026-10-23-onglet-vent-briques, V1: REQ-013 to REQ-016, REQ-020, ARCH-013)

# German words the French and English files must not print: the clauses' and the domain's words of always (REQ-016), matched as words and with their case -- the var ids «gelaendekategorie» and «tabelle», which sections cite, are no words of the page
GERMAN = ("Geländekategorie", "Tabelle", "Anhang", "Figur", "Windkraft", "Windlast", "Bezugsfläche", "Öffnung", "gleichmässig", "Sog", "Staudruck", "Gebäude", "lokale", "Fläche")


def _wind_case(name, lang, **change):
    """A new project in `lang` with one wind case, `WL-01` -- Tableau 36's hall, b 24, d 12, h 6 m --, exported as the window does: (project, the case's file)."""
    import json
    import export_all
    import project
    import project_template
    from domains import wind_source
    here = project_template.create(conftest.tmpdir(name) / "Halle", "Halle", document_language=lang, report_language=lang)
    src = wind_source.new_source("WL-01")
    src.update(table="36", b=24.0, d=12.0, h=6.0, **change)
    path = wind_source.folder(here) / "WL-01.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(src, indent=2) + "\n", encoding="utf-8")
    with project.using(here):
        export_all.run()
    return here, here.root / "Variable-loads" / "Wind" / "WL-01.typ"


def test_the_wind_file_prints_the_forces_in_kn_and_the_openings_chosen_transposed_in_french_alone():
    """REQ-013, REQ-014, REQ-016: Tableau 36's hall written in a French project -- the global forces' table in Q_k [kN] with the numbers the window shows (103.5 kN on b·h), never a variable's name, no load per m² called a force; the q_k per m² kept as lines; the local pressures of the openings chosen alone, a column a surface, `(auto,) + (1fr,) * 11`; no German word; and the report compiles."""
    import subprocess
    import documents
    import project
    here, file = _wind_case("wind_file_fr", "fr")
    text = file.read_text(encoding="utf-8")
    forces = next(l for l in text.split("\n") if l.endswith("<WL-01-table-1>"))
    assert "[*Force globale du vent [kN]*]" in forces and "[103.5]" in forces and "[−121.1]" in forces and "qk_" not in forces and "Qk_" not in forces
    assert '#var("qk_max_cf1"' in text and all("Force globale du vent" not in l for l in text.split("\n") if "kN/m²" in l and "#var(" in l)
    local = next(l for l in text.split("\n") if l.endswith("<WL-01-table-2>"))
    assert local.startswith("#table(columns: (auto,) + (1fr,) * 11,") and "Ouvertures réparties de façon homogène" in local and "prépondérante" not in local
    assert "[*max*], [0.685]" in local, "wall A's largest pressure, the prototype's"
    for word in GERMAN:
        assert not re.search(r"(?<![\w-])" + word + r"(?![\w-])", text), (word, [l for l in text.split("\n") if word in l][:2])
    if conftest.have_typst():
        run = subprocess.run([project.typst_executable(), *documents.compile_args(here, "rs")], capture_output=True, text=True, encoding="utf-8", errors="replace")
        assert run.returncode == 0, run.stderr[-2000:]


def test_the_wind_file_is_in_its_projects_language_and_follows_its_case():
    """REQ-016, ARCH-013: the same hall in German and in English, each in its words; `wind-load` follows its case (AUTO_REGENERATE) -- another openings' case written again at the next export, c_d 1.2 in the pressures of the file as in the window (REQ-015)."""
    import json
    import export_all
    import project
    from domains import wind_forces, wind_source
    assert "wind-load" in unfold.AUTO_REGENERATE
    _here, de = _wind_case("wind_file_de", "de")
    assert "Globale Windkraft [kN]" in de.read_text(encoding="utf-8") and "Öffnungen gleichmässig verteilt" in de.read_text(encoding="utf-8")
    here, en = _wind_case("wind_file_en", "en")
    text = en.read_text(encoding="utf-8")
    assert "Global wind force [kN]" in text and "Openings distributed uniformly" in text
    for word in GERMAN:
        assert not re.search(r"(?<![\w-])" + word + r"(?![\w-])", text), word
    path = wind_source.folder(here) / "WL-01.json"
    src = json.loads(path.read_text(encoding="utf-8"))
    src.update(openings="C", c_d=1.2)
    path.write_text(json.dumps(src, indent=2) + "\n", encoding="utf-8")
    with project.using(here):
        export_all.run()
    local = next(l for l in en.read_text(encoding="utf-8").split("\n") if l.endswith("<WL-01-table-2>"))
    assert "Dominant opening in wall C" in local and "uniformly" not in local
    wall_a = next(s for s in wind_forces.analysis(src)["local"] if s["surface"] == "A")
    assert "[*max*], [" + unfold._number(round(wall_a["max"]["q"], 3)).replace("-", "−") + "]" in local, "c_d in the file's numbers, the window's"


def test_a_wide_building_s_pressures_are_cut_into_balanced_blocks_of_at_most_twelve():
    """REQ-014, REQ-020 (ARCH-RISK-009, ARCH-RISK-016): ⌈surfaces / 12⌉ blocks, as equal as can be -- 12 surfaces one block, 13 two (7 and 6, Tableau 43), Tableau 60a's 29 three (10, 10, 9) --, each a table of the instance, the title over the first, the note under the last."""
    from domains import wind_source
    assert [len(b) for b in wind_source.surface_blocks(list(range(12)))] == [12] and [len(b) for b in wind_source.surface_blocks(list(range(13)))] == [7, 6]
    for number, sizes in (("43", [7, 6]), ("60a", [10, 10, 9]), ("36", [11])):
        src = wind_source.new_source("WL-01")
        src["table"] = number
        local = wind_source.build_instance(src)["tables"][1:]
        assert [len(t["columns"]) - 1 for t in local] == sizes, number
        assert [bool(t["title"]) for t in local] == [True] + [False] * (len(sizes) - 1) and ["note" in t for t in local] == [False] * (len(sizes) - 1) + [True], number
        assert all(len(t["rows"]) == 2 for t in local), "wide and low: a row max, a row min"


def test_every_building_s_file_is_low_and_a_canopy_s_french_carries_no_german():
    """REQ-014, REQ-016, REQ-020 (the verification of V1): every one of the 37 tables -- no block of more than twelve surfaces, two rows each --; a canopy of the platforms (Tableau 51, a «*» force) and its file in French without a German word, c_d among its values (REQ-015)."""
    from domains import wind_source
    for number in wind_source.sia261_wind.NUMBERS:
        src = wind_source.new_source("WL-01")
        src["table"] = number
        for table in wind_source.build_instance(src)["tables"][1:]:
            assert len(table["columns"]) - 1 <= wind_source.BLOCK_SURFACES and len(table["rows"]) == 2, number
    src = wind_source.new_source("WL-01")
    src.update(table="51", b=24, d=12, h=6)
    text = unfold.generate(dict(wind_source.build_instance(src), id="WL-01", kind="wind-load", domain_label="Windlast"), "fr", "wind-load")
    assert '#var("cd"' in text
    for word in GERMAN:
        assert not re.search(r"(?<![\w-])" + word + r"(?![\w-])", text), (word, [l for l in text.split(chr(10)) if word in l][:2])


# --- «Affichage» completed for every tab (spec 2026-10-23-onglet-vent-briques, V2: ARCH-008, UI-024, UI-025, D-26, D-29)

def test_a_figure_from_level_three_is_printed_at_three_alone_and_its_line_read_back():
    """D-29: `#from-level(3)[#figure(…) <label>]` prints its figure in a domain at level 3 and nothing at level 2 -- the uniform level over the domain's, the preview of «Affichage» printing it pale --; its line is written by `figure_line(level=3)` and read back, width, caption, label and level kept by `set_figure`'s reading (UI-025: the figure's setting is every domain's)."""
    from domains import unfold_display
    line = unfold.figure_line("/Variable-loads/Wind/Exports/Figures/WL-01.png", "Tableau 36", "WL-01-figure-1", "50%", level=3)
    assert line == '#from-level(3)[#figure(image("/Variable-loads/Wind/Exports/Figures/WL-01.png", width: 50%), caption: [Tableau 36]) <WL-01-figure-1>]'
    parts = unfold_display.figure_parts(line)
    assert parts["level"] == 3 and parts["width"] == "50%" and parts["caption"] == "Tableau 36" and not parts["masked"]
    assert unfold_display.figure_parts("// " + line)["masked"] and unfold_display.figure_parts(unfold.figure_line("/a.png", "", "x"))["level"] is None
    assert unfold.text_lines(line) == [("figure:WL-01.png", line)], "found by its image, as every figure"
    _need_typst()
    figure = '#from-level(3)[#figure(rect(width: 1cm, height: 1cm), caption: [F]) <f-probe>]'
    count = '\n#context [#metadata(query(figure).len()) <out>]'
    for level, wanted in ((3, 1), (2, 0), (1, 0)):
        kind, got = _probe('#domain("probe-%d", level: %d)[%s]' % (level, level, figure) + count)
        assert (kind, got) == ("ok", wanted), (level, kind, got)
    assert _probe('#uniform-level.update(3)\n#domain("probe-u", level: 1)[%s]' % figure + count) == ("ok", 1), "the uniform level over the domain's"
    assert _probe('#show-masked.update(true)\n#domain("probe-m", level: 2)[%s]' % figure + count) == ("ok", 1), "pale in the preview of «Affichage»"


def test_a_table_is_an_element_shown_or_not_with_or_without_its_title_and_note_and_kept_so():
    """UI-024, ARCH-008: the wind's two tables are elements of its file -- shown, a title and a note each, no level --; the note of the second masked, then the whole first, written into the file as commented lines; an export keeps them masked and takes a masked table's numbers again where they change, so that shown again it says what the export says."""
    import json
    import export_all
    import project
    from domains import unfold_display, wind_source
    here, file = _wind_case("wind_tables", "fr")
    found = [e for e in unfold_display.elements(here, "WL-01", "wind-load") if e["kind"] == "table"]
    assert [e["id"] for e in found] == ["table:1", "table:2"] and all(e["shown"] and e["title"] and e["note"] for e in found)
    assert found[0]["label"] == "Forces globales du vent" and "level" not in found[0]
    with project.using(here):
        unfold_display.set_table(here, "WL-01", "2", "wind-load", note=False)
        unfold_display.set_table(here, "WL-01", "1", "wind-load", shown=False)
    text = file.read_text(encoding="utf-8")
    assert "\n// Valeur la plus grande" in text and "\n// #table(columns: 5," in text and "\n_Forces globales du vent_" in text
    second = next(e for e in unfold_display.elements(here, "WL-01", "wind-load") if e["id"] == "table:2")
    assert second["shown"] and second["title"] and second["note"] is False
    path = wind_source.folder(here) / "WL-01.json"
    src = json.loads(path.read_text(encoding="utf-8"))
    src["q_p0"] = 1.3
    path.write_text(json.dumps(src, indent=2) + "\n", encoding="utf-8")
    with project.using(here):
        export_all.run()
    text = file.read_text(encoding="utf-8")
    assert "\n// Valeur la plus grande" in text, "the note stays masked"
    masked = next(l for l in text.split("\n") if l.endswith("<WL-01-table-1>"))
    assert masked.startswith("// #table(") and "[103.5]" not in masked, "the masked table's numbers taken again: q_p0 1.3"
    with project.using(here):
        unfold_display.set_table(here, "WL-01", "1", "wind-load", shown=True)
        assert unfold.status(here, "WL-01", kind="wind-load").matches
    shown = next(l for l in file.read_text(encoding="utf-8").split("\n") if l.endswith("<WL-01-table-1>"))
    assert shown.startswith("#table(") and shown == unfold.unmasked(masked)
    try:
        unfold_display.set_table(here, "WL-01", "9", "wind-load", shown=False)
    except unfold.UnfoldError as exc:
        assert exc.code == "no_line"
    else:
        raise AssertionError("a table the file does not hold was set")
