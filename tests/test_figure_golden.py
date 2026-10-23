"""Every figure Woodcore draws, held to the byte (spec 2026-10-19-base-saine-nettoyage, lot 0, ARCH-RISK-301).

The drawing engines are about to be brought into one -- one SVG writer, one number format per figure, one palette, one plane geometry (ARCH-004, D1 to D8) --, and a figure that changes by a pixel would go unseen: no test held a figure's bytes until now. This one holds them all: every SVG the export of the example project writes into its tabs' `Exports/Figures/` (plans, fire plans, static models, detail schemas, connections, connectors), and the two drawings the example does not export -- a dead load's build-up and a snow disposition -- drawn from a fixed source.

Each figure is kept as the SHA-256 of its text, its line endings made LF, in `tests/fixtures/figure-golden.json`. A figure that changes fails here, naming it. A change that is meant (the palette merged, spec D-20) is accepted by writing the new hashes -- `WOODCORE_UPDATE_GOLDEN=1 python tests/run_tests.py -k test_figure_golden` -- and saying in the commit which figures changed and why; the map of `CHANGES` below keeps that reason beside the figure.
"""

TIER = "fast"  # tests/run_tests.py --fast

import hashlib
import json
import os

import conftest
from conftest import ROOT

import project
import test_figure_exports as fe

from domains import dead_load_source, dead_load_svg, snow_source
from test_dead_load_source import _roof

GOLDEN = ROOT / "tests" / "fixtures" / "figure-golden.json"
UPDATE = os.environ.get("WOODCORE_UPDATE_GOLDEN") == "1"

# Why a figure's bytes changed on purpose: {figure: "version -- reason"}, "every figure" for a change that touched them all.
CHANGES = {
    "<snow SN-01 …>": "v0.124 -- the snow's drawing redrawn as the column of SIA 261 Figur 3 for the case's roof, black and white, the structure under the roof, the slopes and the values written (spec 2026-10-22-onglet-neige-type, REQ-016, UI-009, D-31): the coloured sketch of issue #36 is gone, and the figure is the export's as well as the tab's.",
    "every figure": "v0.120 -- the palette merged (D5, Q-015): some sixty colours of the drawing engines became the 22 of lib/figure-palette.json (five blacks into one ink; the blues, greens, reds, oranges and greys each into one; the muted grey a neutral one, which the superposition's «grey» must be). Checked figure by figure against the commit before: with the old colours mapped onto the new, all 33 figures are the same text, byte for byte -- nothing but a colour changed.",
}


def _digest(text):
    return hashlib.sha256(text.replace("\r\n", "\n").encode("utf-8")).hexdigest()


def _figures():
    """{name: SHA-256} of every figure: the example's export, and the drawings it does not export, from a fixed source."""
    here = fe._example("figure_golden")
    fe._export(here)
    out = {}
    for kind in project.FIGURE_KINDS:
        folder = here.exports_dir(kind)
        for path in sorted(folder.rglob("*.svg")) if folder.is_dir() else ():
            out[path.relative_to(here.root).as_posix()] = _digest(path.read_text(encoding="utf-8"))
    out["<dead-load DA-01>"] = _digest(dead_load_svg.render(dead_load_source.layer_rows(_roof(), None)))
    snow = snow_source.new_source("SN-01")
    out["<snow SN-01 default>"] = _digest(snow_source.sketch(snow))
    for roof in ("flat", "mono", "duo", "curved"):
        try:
            src = dict(snow, roof=roof)
            out[f"<snow SN-01 {roof}>"] = _digest(snow_source.sketch(src))
        except Exception:  # broad: a roof form this source does not take is simply not held
            continue
    return out


def test_every_figure_is_the_one_held():
    found = _figures()
    assert len(found) >= 30, f"the example exports fewer figures than expected: {sorted(found)}"
    if UPDATE or not GOLDEN.is_file():
        GOLDEN.parent.mkdir(parents=True, exist_ok=True)
        GOLDEN.write_text(json.dumps(found, indent=1, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
        return
    held = json.loads(GOLDEN.read_text(encoding="utf-8"))
    changed = sorted(k for k in held.keys() & found.keys() if held[k] != found[k])
    gone = sorted(held.keys() - found.keys())
    new = sorted(found.keys() - held.keys())
    assert not (changed or gone or new), (
        f"figures changed: {changed}; no longer drawn: {gone}; drawn and not held: {new} -- "
        "a change meant is written with WOODCORE_UPDATE_GOLDEN=1 and its reason kept in CHANGES")
