"""One builder of every call Woodcore copies (v0.117, calc/build_reference.py `call_command`; review B02 of the spec docs/requirements/active/2026-10-07-vues-onglets-slider-et-volets.md).

Until v0.117 each `call_*` wrote its own named arguments and decided by itself which of them to leave out -- the default of every argument written a second time in Python, beside the signature in lib/. Two had drifted: `show-schema`'s `aids` defaults to true in the engine, so the window's «aids: true» call changed nothing and `aids: false` could not be written at all; and a caption or a journal title was written raw, so a caption typed in a panel would not compile. Since v0.117 every `call_*` goes through `call_command`, which reads each default off the signature and writes only what differs from it -- the option panels of the «Affichage» views too (display_view.py).
"""

TIER = "fast"  # tests/run_tests.py --fast

import sys

from conftest import ROOT

sys.path.insert(0, str(ROOT / "calc" / "tools"))

import build_reference as ref  # noqa: E402

# What the `call_*` write: byte for byte. The calls of the commands retired by the spec 2026-10-21-commandes-typst-refonte went with them (UI-002); these are the forms a «Copier» button copies since.
UNCHANGED = [
    (lambda: ref.call_var_registry("M", "S10"), '#var("M", domain: "S10")'),
    (lambda: ref.call_var_registry("x", "T001", level=2), '#var("x", domain: "T001", level: 2)'),
    (lambda: ref.call_var_domain("snow-load", "SL", "s_k"), '#var("s_k", domain: ("snow-load", "SL"))'),
    (lambda: ref.call_find("T001", "name"), '#find(object: "variable", domain: "T001", type: "name")'),
    (lambda: ref.call_include_domain("check", "ZT-01"), '#include domain-file("check", "ZT-01")'),
    (lambda: ref.call_domain_loop("snow-load"), '#for id in ids("snow-load") {\n  include domain-file("snow-load", id)\n}'),
    (lambda: ref.call_domain_loop("check", "check-member"), '#for id in ids("check-member") {\n  include domain-file("check", id)\n}'),
    (lambda: ref.call_image_figure("image-positions-plan", "P01", "Plan", highlight=["A1", "B2"], width="60%"),
     '#figure(image-positions-plan("P01", highlight: ("A1", "B2"), width: 60%), kind: image, caption: [Plan]) <fig-p01>'),
    (lambda: ref.call_image_figure("image-schema", "D1", "Detail", highlight="n1", width="70%"), '#figure(image-schema("D1", highlight: "n1", width: 70%), kind: image, caption: [Detail]) <fig-d1>'),
    (lambda: ref.call_image_figure("image-static-model", "S1", None, label="fig-system"), '#figure(image-static-model("S1"), kind: image) <fig-system>'),
    (lambda: ref.call_figure_loop("image-schema", "schema"), '#for id in ids("schema") {\n  figure(image-schema(id), kind: image, caption: [#id])\n}'),
    (lambda: ref.call_show_annexes(), '#show-annexes()'),
    (lambda: ref.call_show_annexes(3), '#show-annexes(heading: 3)'),
]


def test_the_calls_come_out_as_they_always_did():
    for make, expected in UNCHANGED:
        assert make() == expected, (make(), expected)


def test_a_default_is_read_off_the_signature_and_left_out():
    assert ref.signature_defaults("image-schema")["detail-figure"] == "auto"
    assert ref.call_journal_entries("rs") == "#let revisions = journal-entries()", "the report's journal is journal-entries' default"
    assert ref.call_command("image-positions-plan", "P01", width=ref.Raw("100%"), zoom=1) == '#image-positions-plan("P01")'


def test_a_text_is_a_string_and_none_is_none():
    # a figure's caption is content, its characters of markup escaped (spec 2026-10-15, UI-001): a label typed «Detail [A] #1» compiles
    assert ref.call_image_figure("image-schema", "D1", "Detail [A] #1") == '#figure(image-schema("D1"), kind: image, caption: [Detail \\[A\\] \\#1]) <fig-d1>'
    assert ref.call_journal_entries() == "#let revisions = journal-entries()"
    assert ref.call_journal_entries("cu") == '#let revisions = journal-entries(document: "cu")', "the journal of the document the window shows"
    assert ref.call_image_figure("image-positions-plan", "P01", "Plan", highlight=["A1"]) == '#figure(image-positions-plan("P01", highlight: "A1"), kind: image, caption: [Plan]) <fig-p01>', "one position lit is a string"


def test_an_argument_the_command_does_not_take_is_refused_by_name():
    try:
        ref.call_command("image-positions-plan", "P01", colour="red")
    except ValueError as exc:
        assert "colour" in str(exc) and "image-positions-plan" in str(exc), exc
    else:
        raise AssertionError("an argument image-positions-plan does not take was written")
    try:
        ref.call_image("image-positions-plan", "P01", detail_figure="colours")
    except ValueError as exc:
        assert "colours" in str(exc) and "detail-figure" in str(exc), exc
    else:
        raise AssertionError("a word image-positions-plan's vocabulary does not have was written")
