"""The six drawings as images for a native `#figure` (spec docs/requirements/completed/2026-10-21-commandes-typst-refonte.md, REQ-013, REQ-014, ARCH-012, D-13; image-polar-moment, spec 2026-10-22-image-polar-moment; lib/calc-engine-drawings.typ, lib/image-vocabulary.json, calc/build_reference_calls.py `call_image_figure`)."""

TIER = "fast"  # tests/run_tests.py --fast

import json

import conftest
from conftest import ROOT
import build_reference as ref
import test_position_list as base


def test_each_image_compiles_in_a_native_figure_numbered_and_cited():
    """REQ-013, REQ-014: `#figure(image-…("<id>", …), kind: image, caption: […]) <label>` compiles for a position plan, a fire-protection plan, a static model and a schema of the example; each is numbered as a figure and cited by `@label`."""
    here = base._project("image_figures")
    calls = [
        ref.call_image_figure("image-positions-plan", "Velo-Unterstand", "Positionsplan", label="pl1", detail_legend=("length", "objects")),
        ref.call_image_figure("image-fire-plan", "Pavillon-EG", "Brandschutz", label="fp1", detail_legend="objects"),
        ref.call_image_figure("image-static-model", "Bankli-Fall1", "System", label="sm1", detail_figure="dimensions"),
        ref.call_image_figure("image-schema", "VU-Skizze", "Detail", label="sc1", highlight="E1"),
    ]
    body = "\n\n".join(calls) + "\n\nSiehe @pl1, @fp1, @sm1 und @sc1."
    text = base._text(here, body, "image_figures")
    for n, caption in enumerate(("Positionsplan", "Brandschutz", "System", "Detail"), 1):
        assert f"Abbildung {n}: {caption}" in text, (n, caption, text[:600])
    assert "Siehe Abbildung 1, Abbildung 2, Abbildung 3 und Abbildung 4." in text, text[-400:]


def test_a_word_outside_the_vocabulary_is_refused_by_both_sides():
    """ARCH-012: the one vocabulary (lib/image-vocabulary.json) refuses a word in Typst, naming the valid ones, and in Python before a call is written; the defaults are not written."""
    vocabulary = json.loads((ROOT / "lib" / "image-vocabulary.json").read_text(encoding="utf-8"))["commands"]
    assert set(vocabulary) == {"image-positions-plan", "image-fire-plan", "image-static-model", "image-schema", "image-extract", "image-polar-moment"}
    assert ref.call_image("image-positions-plan", "P", detail_legend=vocabulary["image-positions-plan"]["detail-legend-default"]) == 'image-positions-plan("P")'
    try:
        ref.call_image("image-static-model", "M", detail_figure="axes")
        raise AssertionError("a word of another command is written")
    except ValueError as exc:
        assert "loads" in str(exc) and "dimensions" in str(exc)
    here = base._project("image_refused")
    message = base._refusal(here, '#image-positions-plan("Velo-Unterstand", detail-figure: "colour")', "image_refused")
    assert "detail-figure" in message and "axes" in message, message


def test_a_polar_moment_draws_its_forces_given_as_numbers_or_names():
    """REQ-001, REQ-002, UI-001 (spec 2026-10-22-image-polar-moment): `#figure(image-polar-moment("VU-MP-1", …))` compiles with the forces given as numbers and as the names of variables declared above, numbered as a figure; a name nothing declared, or a variable in another unit, is refused naming the argument."""
    here = base._project("image_polar")
    body = ('#figure(image-polar-moment("VU-MP-1", N: 7.5, V: 25, M: 6.6), kind: image, caption: [Kräfte]) <mp1>\n\n'
            '#domain("VU-MP-1-probe")[\n#var("N", 4, "kN")\n#var("V", 12, "kN")\n#var("M", 2.5, "kNm")\n'
            '#figure(image-polar-moment("VU-MP-1", N: "N", V: "V", M: "M", width: 60%), kind: image, caption: [Anschluss])\n]\n\n'
            '#figure(image-polar-moment("VU-MP-1", detail-figure: ()), kind: image, caption: [Ohne Pfeile])\n\nSiehe @mp1.')
    text = base._text(here, body, "image_polar")
    for n, caption in enumerate(("Kräfte", "Anschluss", "Ohne Pfeile"), 1):
        assert f"Abbildung {n}: {caption}" in text, (n, caption, text[:600])
    assert "Siehe Abbildung 1." in text, text[-400:]
    message = base._refusal(here, '#image-polar-moment("VU-MP-1", V: "V_d")', "image_polar_name")
    assert "V" in message and "V_d" in message, message
    message = base._refusal(here, '#var("M", 2.5, "kN")\n#image-polar-moment("VU-MP-1", M: "M")', "image_polar_unit")
    assert "M" in message and "kNm" in message, message
    message = base._refusal(here, '#image-polar-moment("VU-MP-9")', "image_polar_id")
    assert "VU-MP-1" in message, message
