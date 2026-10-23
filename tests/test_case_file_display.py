"""A load's file set line by line in «Affichage», and kept through the exports (spec 2026-10-22-onglet-neige-type, REQ-011 to REQ-018, ARCH-012, D-17, D-18, D-23, D-29, D-30; calc/domains/unfold.py, calc/line_display.py).

What is held, on a snow case made in a new project and exported as the window does (export_all):

* **the elements of the file** -- the header, the figure at its head, each `#var` and `#eq` -- as «Affichage» lists them;
* **a line's display is the engineer's** (D-17): an argument of its display set on a line leaves it in step with the export, and the next export refreshes its value and keeps the argument -- for every kind a file is written for, the polar moment's `level: 0` of an earlier base read without a false conflict (ARCH-RISK-F04);
* **what the export writes itself** -- an `#eq`'s label -- set by hand makes the line the engineer's (`local`), never written over;
* **the figure** (D-23, D-29): its width, caption and label set, the line found by its image; masked by commenting it out, which no export undoes, shown again;
* **the domain's level** (D-30): `level:` written into the header, every other argument of it kept;
* **a file of the snow's old form** (D-18): it says so, and «Régénérer» writes s_k as the `#eq` of equation (10), never keeping the old `#var` as the engineer's (ARCH-RISK-F01);
* **it compiles**, the figure masked.
"""

TIER = "fast"  # tests/run_tests.py --fast

import json

import conftest
from conftest import Skip
from domains import unfold, unfold_display


def _need_typst():
    if not conftest.have_typst():
        raise Skip("typst is not on the path")


def _case(name, **change):
    """A new project with one snow case, `SN-01`, exported as the window does: (project, the case's file, its source's path)."""
    import export_all
    import project
    import project_template
    from domains import snow_source
    here = project_template.create(conftest.tmpdir(name) / "Halle", "Halle")
    path = snow_source.folder(here) / "SN-01.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    src = snow_source.new_source("SN-01")
    src.update(change)
    path.write_text(json.dumps(src, indent=2) + "\n", encoding="utf-8")
    with project.using(here):
        export_all.run()
    return here, here.root / "Variable-loads" / "Snow" / "SN-01.typ", path


def _export(here):
    import export_all
    import project
    with project.using(here):
        export_all.run()


def _states(here):
    return {line.id: line.state for line in unfold.status(here, "SN-01", kind="snow-load").lines}


def test_the_file_lists_its_header_its_figure_and_its_lines():
    here, file, _src = _case("case_elements")
    found = unfold_display.elements(here, "SN-01", "snow-load")
    ids = [e["id"] for e in found]
    assert ids[0] == "domain" and found[0]["level"] is None
    assert ids[1] == "figure:SN-01-fig3.svg" and found[1]["width"] == "80%" and found[1]["label"] == "SN-01-figure-1" and not found[1]["masked"]
    assert {"var:h_0", "eq:h_ref", "eq:s_k", "eq:q_k11"} <= set(ids), ids
    assert "var:schneeueberhang" not in ids and "var:s_k" not in ids
    assert set(_states(here).values()) == {"in_sync"}, _states(here)


def test_a_display_set_on_a_line_survives_the_next_export_which_refreshes_its_value():
    here, file, src_path = _case("case_display")
    unfold_display.set_display(here, "SN-01", "eq:q_k11", {"style": "bold", "display-formula": "none"}, "snow-load")
    unfold_display.set_display(here, "SN-01", "var:h_0", {"label-position": "after"}, "snow-load")
    text = file.read_text(encoding="utf-8")
    assert 'style: "bold"' in text and 'display-formula: "none"' in text and 'label-position: "after"' in text
    assert set(_states(here).values()) == {"in_sync"}, "an argument of a line's display is no change of it (D-17)"
    src = json.loads(src_path.read_text(encoding="utf-8"))
    src["h_0"] = 900
    src_path.write_text(json.dumps(src, indent=2) + "\n", encoding="utf-8")
    _export(here)
    text = file.read_text(encoding="utf-8")
    h0 = next(line for line in text.split("\n") if '#var("h_0"' in line)
    q = next(line for line in text.split("\n") if '#eq("q_k11"' in line)
    assert h0.startswith('  #var("h_0", 900,') and 'label-position: "after"' in h0, h0
    assert 'style: "bold"' in q and 'display-formula: "none"' in q, q
    assert set(_states(here).values()) == {"in_sync"}, _states(here)
    # a name that is no argument of a line's display, nor one «Affichage» writes, is refused
    try:
        unfold_display.set_display(here, "SN-01", "var:h_0", {"value": 3}, "snow-load")
    except unfold.UnfoldError as exc:
        assert exc.code == "not_writable"
    else:
        raise AssertionError("value: was written")


def test_a_label_typed_on_an_eq_makes_the_line_the_engineers():
    here, file, _src = _case("case_label")
    unfold_display.set_display(here, "SN-01", "eq:q_k11", {"label": "Charge de neige du pan 1"}, "snow-load")
    assert _states(here)["eq:q_k11"] == "local"
    _export(here)
    assert 'label: "Charge de neige du pan 1"' in file.read_text(encoding="utf-8"), "never written over by an export"


def test_the_figure_is_set_masked_and_shown_and_stays_woodcores():
    here, file, _src = _case("case_figure")
    line_id = "figure:SN-01-fig3.svg"
    unfold_display.set_figure(here, "SN-01", line_id, width="60%", caption="Toit du hangar", label="fig-toit")
    line = next(l for l in file.read_text(encoding="utf-8").split("\n") if "SN-01-fig3.svg" in l)
    assert line == '#figure(image("/Variable-loads/Snow/Exports/Figures/SN-01-fig3.svg", width: 60%), caption: [Toit du hangar]) <fig-toit>', line
    assert _states(here)[line_id] == "local", "found by its image, its label changed (D-29)"
    unfold_display.set_figure(here, "SN-01", line_id, shown=False)
    line = next(l for l in file.read_text(encoding="utf-8").split("\n") if "SN-01-fig3.svg" in l)
    assert line.startswith("// #figure(") and "<fig-toit>" in line, line
    assert _states(here)[line_id] == "masked"
    _export(here)
    assert next(l for l in file.read_text(encoding="utf-8").split("\n") if "SN-01-fig3.svg" in l).startswith("// "), "no export shows it again"
    [element] = [e for e in unfold_display.elements(here, "SN-01", "snow-load") if e["id"] == line_id]
    assert element["masked"] and element["caption"] == "Toit du hangar" and element["width"] == "60%"
    unfold_display.set_figure(here, "SN-01", line_id, shown=True)
    assert next(l for l in file.read_text(encoding="utf-8").split("\n") if "SN-01-fig3.svg" in l).startswith("#figure(")


def test_the_domains_level_is_written_in_its_header_and_nothing_else_of_it_changes():
    here, file, _src = _case("case_level")
    text = file.read_text(encoding="utf-8")
    header = next(l for l in text.split("\n") if l.startswith("#domain("))
    hand = header[:-2] + ', norm: "SIA 261")['
    file.write_text(text.replace(header, hand), encoding="utf-8", newline="\n")
    unfold_display.set_domain_level(here, "SN-01", 2, "snow-load")
    header = next(l for l in file.read_text(encoding="utf-8").split("\n") if l.startswith("#domain("))
    assert header == hand[:-2] + ", level: 2)[", header
    assert unfold_display.domain_level(file.read_text(encoding="utf-8")) == 2
    unfold_display.set_domain_level(here, "SN-01", None, "snow-load")
    assert next(l for l in file.read_text(encoding="utf-8").split("\n") if l.startswith("#domain(")) == hand


def test_a_file_of_the_old_form_says_so_and_is_regenerated_with_s_k_an_eq():
    """D-18, ARCH-RISK-F01: s_k written as the `#var` an earlier Woodcore wrote, the base recording it and the form before «-fig3»."""
    import sync
    from domains import formula_domain as fd
    here, file, _src = _case("case_old_form")
    text = file.read_text(encoding="utf-8")
    eq = next(l for l in text.split("\n") if '#eq("s_k"' in l)
    old = '  #var("s_k", 2.759184, "kN/m²", domain: ("snow-load", "SN-01"), label: "Charakteristischer Wert der Schneelast auf horizontalem Gelände", norm: "SIA 261", norm-section: "5.2.6", id: "s_k")'
    file.write_text(text.replace(eq, old), encoding="utf-8", newline="\n")
    where = unfold.base_path(here, "snow-load")
    base = json.loads(where.read_text(encoding="utf-8"))
    entry = base["domains"]["SN-01"]
    entry["gen"]["form"] = entry["gen"]["form"].removesuffix("-fig3")
    entry["lines"].pop("eq:s_k")
    item = fd.read(file).commands
    digest = sync.digest(unfold.comparable_text(next(c for c in item if not c.is_text and c.key == "s_k")))
    entry["lines"]["var:s_k"] = [digest, digest]
    where.write_text(json.dumps(base, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    status = unfold.status(here, "SN-01", kind="snow-load")
    assert not status.matches and _states(here)["eq:s_k"] == "missing", _states(here)
    assert unfold.regenerate(here, "SN-01", kind="snow-load") == {"conflicts": []}
    after = file.read_text(encoding="utf-8")
    assert '#eq("s_k"' in after and '#var("s_k"' not in after and after.count('id: "s_k"') == 1, after
    assert unfold.status(here, "SN-01", kind="snow-load").matches


def test_a_base_written_before_reads_a_level_on_a_line_without_a_false_conflict():
    """ARCH-RISK-F04: a base recorded the digest of the whole call, `level: 0` with it (a member's lines, a polar moment's); read now without the arguments of its display, the line is still in step."""
    import sync
    from domains import formula_domain as fd
    here, file, _src = _case("case_old_digest")
    unfold_display.set_display(here, "SN-01", "var:h_0", {"level": 0}, "snow-load")
    where = unfold.base_path(here, "snow-load")
    base = json.loads(where.read_text(encoding="utf-8"))
    whole = sync.digest(fd.to_call(next(c for c in fd.read(file).commands if not c.is_text and c.key == "h_0")).strip())
    base["domains"]["SN-01"]["lines"]["var:h_0"] = [whole, whole]
    where.write_text(json.dumps(base, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    assert _states(here)["var:h_0"] == "in_sync"


def test_the_file_set_in_affichage_compiles():
    import subprocess
    import documents
    import project
    _need_typst()
    here, file, _src = _case("case_compile")
    unfold_display.set_display(here, "SN-01", "eq:s_k", {"display-formula": "variable-value-unit", "style": "double"}, "snow-load")
    unfold_display.set_domain_level(here, "SN-01", 3, "snow-load")
    unfold_display.set_figure(here, "SN-01", "figure:SN-01-fig3.svg", shown=False)
    run = subprocess.run([project.typst_executable(), *documents.compile_args(here, "rs")], capture_output=True, text=True, encoding="utf-8", errors="replace")
    assert run.returncode == 0, run.stderr[-2000:]
