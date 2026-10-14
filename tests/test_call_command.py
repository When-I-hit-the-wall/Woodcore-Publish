"""One builder of every call Woodcore copies (v0.117, calc/tools/build_reference.py `call_command`; review B02 of the spec docs/requirements/active/2026-10-07-vues-onglets-slider-et-volets.md).

Until v0.117 each `call_*` wrote its own named arguments and decided by itself which of them to leave out -- the default of every argument written a second time in Python, beside the signature in lib/. Two had drifted: `show-schema`'s `aids` defaults to true in the engine, so the window's «aids: true» call changed nothing and `aids: false` could not be written at all; and a caption or a journal title was written raw, so a caption typed in a panel would not compile. Since v0.117 every `call_*` goes through `call_command`, which reads each default off the signature and writes only what differs from it -- the option panels of the «Affichage» views too (display_view.py).
"""

import sys

from conftest import ROOT

sys.path.insert(0, str(ROOT / "calc" / "tools"))

import build_reference as ref  # noqa: E402

# What the `call_*` wrote before they went through call_command, and still write: byte for byte.
UNCHANGED = [
    (lambda: ref.call_show_calc("snow-load", "SL"), '#show-calc("snow-load", "SL")'),
    (lambda: ref.call_show_calc("snow-load", "SL", level=2), '#show-calc("snow-load", "SL", level: 2)'),
    (lambda: ref.call_show_calc("d", "i", level=3, title=False), '#show-calc("d", "i", level: 3, title: none)'),
    (lambda: ref.call_val("s_k", "snow-load", "SL"), '#val("s_k", domain: ("snow-load", "SL"))'),
    (lambda: ref.call_val("x", "T001"), '#val("x", domain: "T001")'),
    (lambda: ref.call_val("x", "d", "i", "expression"), '#val("x", domain: ("d", "i"), type: "expression")'),
    (lambda: ref.call_var_registry("M", "S10"), '#var("M", domain: "S10")'),
    (lambda: ref.call_find("T001", "name"), '#find(object: "variable", domain: "T001", type: "name")'),
    (lambda: ref.call_var("d", "i", "qk11", "q_k11"), '#var("q_k11", var-of("d", "i", "qk11"))'),
    (lambda: ref.call_show_live_load("A1", level=2, title="Nutzlast"), '#show-live-load("A1", level: 2, title: "Nutzlast")'),
    (lambda: ref.call_show_polar_moment("C1"), '#show-polar-moment("C1", N: 0, V: 0, M: 0)'),
    (lambda: ref.call_show_polar_moment("C1", N=1.5, V=-2, M=3.25, level=2), '#show-polar-moment("C1", N: 1.5, V: -2, M: 3.25, level: 2)'),
    (lambda: ref.call_show_connector("V1", True), '#show-connector("V1", description: true)'),
    (lambda: ref.call_show_connector_resistance("V1", 2), '#show-connector-resistance("V1", level: 2)'),
    (lambda: ref.call_show_check_member("T1", 2, False, True, "Titre", "kN"),
     '#show-check-member("T1", level: 2, member-level: none, description: true, title: "Titre", unit: "kN")'),
    (lambda: ref.call_show_check_member("T1", title=False, member_level=2), '#show-check-member("T1", member-level: 2, title: none)'),
    (lambda: ref.call_show_plan("P01", ["A1", "B2"], True, False, "60%", False, 2, False, "Cap"),
     '#show-plan("P01", width: 60%, legend: false, highlight: ("A1", "B2"), detail: true, zoom: 2, axes: false, scale-bar: false, caption: "Cap")'),
    (lambda: ref.call_show_plan("P01", "A1", caption=False), '#show-plan("P01", highlight: "A1", caption: none)'),
    (lambda: ref.call_show_fire_plan("F1", False, "50%", False, "x"), '#show-fire-plan("F1", width: 50%, legend: false, scale-bar: false, caption: "x")'),
    (lambda: ref.call_show_static_model("S1", "70%", False, ["a", "b"]), '#show-static-model("S1", width: 70%, loads: false, highlight: ("a", "b"))'),
    (lambda: ref.call_show_schema("D1", "70%", "n1"), '#show-schema("D1", width: 70%, highlight: "n1")'),
    (lambda: ref.call_show_journal(form="grid", level=3), '#show-journal(form: "grid", level: 3)'),
    (lambda: ref.call_show_extract("E1", "80%"), '#show-extract("E1", width: 80%)'),
    (lambda: ref.call_show_annexes(), '#show-annexes()'),
    # the calls with no named option, which do not go through call_command: held as they are all the same
    (lambda: ref.call_show_input("d", "i", "s_k"), '#show-input("d", "i", "s_k")'),
    (lambda: ref.call_var_of("d", "i", "h"), '#let h-var = var-of("d", "i", "h")'),
    (lambda: ref.call_value_of("d", "i", "x"), '#let x = value-of("d", "i", "x")'),
    (lambda: ref.call_show_check("d", "i", "c"), '#show-check("d", "i", "c")'),
    (lambda: ref.call_instance_loop("snow-load"), '#for sheet in instance-ids("snow-load") {\n  show-calc("snow-load", sheet)\n}'),
    (lambda: ref.call_calc_block_plan("T001"), '#calc-block("T001", plan: auto)[\n  \n]'),
    (lambda: ref.call_calc_block_plan("T001", "P01"), '#calc-block("T001", plan: "P01")[\n  \n]'),
    (lambda: ref.call_show_plan_legend("P01"), '#show-plan-legend("P01")'),
    (lambda: ref.call_check_member_loop(), '#for id in check-member-ids() {\n  show-check-member(id)\n}'),
    (lambda: ref.call_connector_loop(), '#for c in connector-ids() {\n  show-connector-resistance(c)\n}'),
    (lambda: ref.call_plan_loop(), '#for p in plan-ids() {\n  show-plan(p)\n}'),
    (lambda: ref.call_fire_plan_loop(), '#for p in fire-plan-ids() {\n  show-fire-plan(p)\n}'),
    (lambda: ref.call_static_model_loop(), '#for s in static-model-ids() {\n  show-static-model(s)\n}'),
    (lambda: ref.call_schema_loop(), '#for id in schema-ids() {\n  show-schema(id)\n}'),
    (lambda: ref.call_extract_loop(), '#for id in extract-ids() {\n  show-extract(id)\n}'),
    # new in the window since v0.117
    (lambda: ref.call_show_load_summary(), '#show-load-summary()'),
    (lambda: ref.call_show_load_summary("Lasten"), '#show-load-summary(title: "Lasten")'),
    (lambda: ref.call_show_line_load_summary(False), '#show-line-load-summary(title: none)'),
    (lambda: ref.call_show_position_list(), '#show-position-list()'),
]


def test_the_calls_come_out_as_they_always_did():
    for make, expected in UNCHANGED:
        assert make() == expected, (make(), expected)


def test_a_default_is_read_off_the_signature_and_left_out():
    assert ref.signature_defaults("show-schema")["aids"] == "true"
    assert ref.call_show_schema("D1", aids=True) == '#show-schema("D1")', "aids: true is show-schema's default"
    assert ref.call_show_schema("D1", aids=False) == '#show-schema("D1", aids: false)', "aids: false could not be written until v0.117"
    assert ref.call_show_journal(form="table") == "#show-journal()", "table is show-journal's default"
    assert ref.call_command("show-plan", "P01", width=ref.Raw("100%"), zoom=1) == '#show-plan("P01")'


def test_a_text_is_a_string_and_none_is_none():
    assert ref.call_show_static_model("S1", caption="Système") == '#show-static-model("S1", caption: "Système")', "a caption was written raw until v0.117"
    assert ref.call_show_schema("D1", caption=False) == '#show-schema("D1", caption: none)'
    assert ref.call_show_journal(title="Historique") == '#show-journal(title: "Historique")'
    assert ref.call_show_journal(title=False) == "#show-journal(title: none)"
    assert ref.call_journal_entries() == "#let revisions = journal-entries()"
    assert ref.call_journal_entries("cu") == '#let revisions = journal-entries(document: "cu")', "the journal of the document the window shows"
    assert ref.call_show_position_list(scope="plans", plans=["P01"]) == '#show-position-list(scope: "plans", plans: ("P01",))', "an array of one keeps its comma"


def test_an_argument_the_command_does_not_take_is_refused_by_name():
    try:
        ref.call_command("show-plan", "P01", colour="red")
    except ValueError as exc:
        assert "colour" in str(exc) and "show-plan" in str(exc), exc
    else:
        raise AssertionError("an argument show-plan does not take was written")
