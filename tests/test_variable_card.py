"""The card of a variable or a domain, and the command to copy (calc/variable_card.py; spec 2026-10-24-onglet-variables-groupes, REQ-006, UI-010, UI-011, UI-012).

⚠️ **The command depends on the source**: the export's is read live and needs nothing above it; a file's
needs its file included higher up; a document's must stand below the domain it names. The calls are
`build_reference`'s -- this module spells none.
"""

TIER = "fast"  # tests/run_tests.py --fast

import conftest

import build_reference as ref
import variable_calc as calc
import variable_card as card
import variable_sources as sources
import variables as model


def _var(key, value=1.0, unit="kN", domain=""):
    return model.Variable(key=key, domain=domain, value=value, unit=unit, symbol=key)


_CACHE = {}


def _assembly():
    if "a" not in _CACHE:
        export = sources.read_export(conftest.PROJECT)
        reg = model.Registry(stamp="pinned", domains={"SL": [_var("s_k", 1.394, "kN/m²", "SL"), _var("q_k1", 1.115, "kN/m²", "SL")],
                                                       "S10 - 1 kN Mitte": [_var("M", 0.75, "kNm", "S10 - 1 kN Mitte")]})
        domains = list(export.domains) + sources.registry_domains("rs", reg)
        assembly = calc.assemble(domains, export.index, documents_read=True)
        _CACHE["a"] = (assembly, {(d.origin, d.name): d for d in domains})
    return _CACHE["a"]


def _names(mode):
    return {"rs": "Rapport de statique"}.get(mode, mode)


def test_the_command_of_the_export_is_read_live_and_includes_nothing():
    assembly, by = _assembly()
    domain = by[("export", "snow-load · SL")]
    found = card.command("s_k", domain, assembly)
    assert found.call == ref.call_var_domain("snow-load", "SL", "s_k") == '#var("s_k", domain: ("snow-load", "SL"))'
    assert found.note == "vr_inc_export" and found.values == {}


def test_the_command_of_a_file_says_which_file_to_include():
    assembly, by = _assembly()
    load = card.command("s_k", by[("formulas", "SL")], assembly, conftest.PROJECT)
    assert load.call == '#var("s_k", domain: "SL")'
    assert load.note == "vr_inc_file" and load.values["include"] == '#include domain-file("snow-load", "SL")'
    check = card.command("eta", by[("formulas", "BI-01")], assembly, conftest.PROJECT)
    assert check.values["include"] == '#include domain-file("check", "BI-01")'
    domains_tab = card.command("q", by[("formulas", "poutre-p1")], assembly, conftest.PROJECT)
    assert domains_tab.values["include"] == '#include "/Domains/poutre-p1.typ"', "the «Domaines» tab's own include (formula_domain.include_call)"


def test_the_command_of_a_document_stands_below_its_domain():
    assembly, by = _assembly()
    found = card.command("M", by[("rs", "S10 - 1 kN Mitte")], assembly, document_name=_names)
    assert found.call == '#var("M", domain: "S10 - 1 kN Mitte")'
    assert found.note == "vr_inc_document" and found.values == {"document": "Rapport de statique"}


def test_a_variable_of_no_named_domain_has_no_command():
    assembly, _by = _assembly()
    root = sources.Domain(name="", origin="rs", variables=[_var("R_d")])
    assert card.command("R_d", root, assembly) is None


def test_three_variables_copied_in_the_order_given_one_line_each():
    assembly, by = _assembly()
    keys = [("formulas", "SL", "q_k1"), ("export", "snow-load · SL", "s_k"), ("rs", "SL", "s_k")]
    lines = card.copy_lines(keys, by, assembly, conftest.PROJECT)
    assert lines == ['#var("q_k1", domain: "SL")', '#var("s_k", domain: ("snow-load", "SL"))', '#var("s_k", domain: "SL")']
    assert not any(line.startswith("#include") for line in lines), "no line to include in a copy of several"
    assert card.copy_lines([("export", "gone · X", "a"), ("rs", "SL", "zz")], by, assembly) == []


def test_the_card_of_a_variable_of_the_export():
    assembly, by = _assembly()
    domain = by[("export", "snow-load · SL")]
    var = domain.variable("h_0")
    found = card.variable_card(var, domain, assembly, path=("Actions", "Actions variables", "Neige"), here=conftest.PROJECT, document_name=_names)
    assert found.path == ("Actions", "Actions variables", "Neige", "SL")
    assert found.tab == "tab_ac_snow" and found.node == "load:snow-load/SL"
    assert found.came_from == ("vr_from_woodcore", {}), "typed in the snow tab (issue #109: the example's cases are sources)"
    assert ("vr_key", "h_0") in found.fields and ("vr_level", "3") in found.fields
    assert all(text for _k, text in found.fields), "an empty row is hidden"
    assert found.computed_in == ("vr_computed_here", {})
    assert [(s.domain.origin, s.computes) for s in found.siblings] == [("formulas", False), ("rs", False)]
    assert found.siblings[0].key == "h_0" and found.siblings[1].key is None, "the report's SL has no h_0: its button leads to the domain"
    assert not found.result
    q = card.variable_card(domain.variable("q_k1"), domain, assembly)
    assert q.result


def test_the_card_of_a_document_s_variable_opens_the_tab_of_the_export():
    """REQ-009: chosen in the document that recalls it, the value's tab is the computing source's."""
    assembly, by = _assembly()
    domain = by[("rs", "SL")]
    found = card.variable_card(domain.variable("q_k1"), domain, assembly, document_name=_names)
    assert found.tab == "tab_ac_snow" and found.node == "load:snow-load/SL"
    assert found.computed_in == ("vr_computed_in", {"source": by[("export", "snow-load · SL")]})
    assert found.came_from == ("vr_from_document", {"document": "Rapport de statique"})
    assert found.result, "q_k1, a result of the export, is one here too (REQ-004)"
    sib = found.siblings[0]
    assert sib.domain is by[("export", "snow-load · SL")] and sib.computes and sib.value == "1.115"


def test_a_label_written_in_german_in_the_workbook_is_shown_as_written():
    """D-3: the workbook's labels as written."""
    assembly, by = _assembly()
    domain = by[("export", "snow-load · SL")]
    var = domain.variable("h_0")
    assert var.label and card.variable_card(var, domain, assembly).var.label == var.label


def test_the_card_of_a_domain_chosen_alone():
    """UI-012: its count of variables and of results, the whole domain to copy, no «Valeur» nor «Désignation»."""
    assembly, by = _assembly()
    domain = by[("export", "snow-load · SL")]
    found = card.domain_card(domain, assembly, path=("Actions", "Actions variables", "Neige"))
    assert found.command.call == '#include domain-file("snow-load", "SL")' and found.command.note == "vr_inc_whole"
    assert found.variables == len(domain.variables) and found.results == len([v for v in domain.variables if v.key in domain.results]) >= 1
    assert not hasattr(found, "value") and not hasattr(found, "label")
    declared = card.domain_card(by[("rs", "S10 - 1 kN Mitte")], assembly)
    assert declared.command is None and declared.tab is None


def test_where_a_value_comes_from_in_words():
    domain = sources.Domain(name="x · y", origin="export", address=("x", "y"))
    assert card.came_from(_var("a"), domain)[0] == "vr_from_unknown"
    assert card.came_from(model.Variable(key="a", domain="", value=1, unit="", symbol="a", source="python:domains/dead_load.py"), domain)[0] == "vr_from_woodcore"
    assert card.came_from(model.Variable(key="a", domain="", value=1, unit="", symbol="a", source="norm:SIA 261 Tabelle 8"), domain) == ("vr_from_norm", {"norm": "SIA 261 Tabelle 8"})
