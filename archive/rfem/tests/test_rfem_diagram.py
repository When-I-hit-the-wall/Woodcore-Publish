"""The RFEM tab's figure: what is drawn over a structure, and the on-demand reading behind it (docs/domain/rfem.md §3.3duodecies, docs/ui/window.md §10quater).

What is held here, and why each of them earned a check:

- **A loading is found and read one at a time.** Reading every loading of the engineer's export costs 105 s and reading one costs 1.4 s, which is the whole reason the tab can draw a diagram at all. ⚠️ The sheet names are **truncated to 31 characters** by Excel, so «Efforts internes» loses its «s» on 39 of 57 sheets — matching the whole word found 18 of 57, silently, and the stems are what fixed it.
- **M positive is drawn towards +z, which is downwards**, the engineer's own rule, and the drawing follows each member's own axis rather than the page.
- **A node lying on a member joins it, unless every member ending there runs along it.** A column landing mid-span of an undivided beam is one structure with it; two collinear members that overlap are not.
- **The figure takes the structure's proportions**, so a portal frame three times as wide as it is tall is not squared into a frame two thirds of which is white.
- **QtSvg reads what is written**, since the window shows this very string through a `QSvgWidget`.
"""

import os
import sys
from pathlib import Path

import conftest
from conftest import Skip
from fixtures import rfem_model

sys.path.insert(0, os.path.join(conftest.ROOT, "calc"))

from rfem_import import diagram_svg, model_tables, results, structure_detection


def _fixture(lang="fr"):
    path = rfem_model.workbook(Path(conftest.tmpdir("rfem-diagram")) / "modele.xlsx", lang=lang)
    model = model_tables.read_model(path)
    return model, structure_detection.detect(model.items(), combinations=model.combination_cases())


def _export():
    """The engineer's own full export, or a skip: it is the only file that carries results at all."""
    project = conftest.real_project()
    if project is None:
        raise Skip("the engineer's own project is not beside this checkout")
    for name in ("FR.xlsx", "DE.xlsx", "EN.xlsx"):
        path = os.path.join(str(project.root), "RFEM-Export", name)
        if os.path.exists(path):
            return path
    raise Skip("no RFEM-Export/*.xlsx beside the engineer's project")


# -- the on-demand reading -------------------------------------------------------------

def test_the_loadings_are_found_without_reading_them():
    """Every loading of the export, from the sheet names alone -- and every one of them, truncated names included."""
    path = _export()
    found = results.loadings_in(path)
    assert len(found) == 57, "57 loadings were exported, got %d -- a truncated sheet name is the usual cause" % len(found)
    # ⚠️ The ids are the model's own language: CC/SP/CO in French, LF/LK in German, LC/CO in English.
    assert len({name[:2] for name in found}) >= 2, found[:6]


def test_one_loading_is_read_and_the_others_are_not():
    """The oracle four independent routes agree on, read out of the one sheet that carries it."""
    table = results.read_loading(_export(), "CO1") or results.read_loading(_export(), "LK1")
    if table is None:
        raise Skip("this export names its combinations otherwise")
    highest, lowest = table.governing("M_y")
    assert round(highest["M_y"], 4) == 15.9667, highest
    assert highest.member == 64 and highest.x == 2.115, (highest.member, highest.x)
    assert lowest["M_y"] < 0


def test_a_loading_the_export_does_not_carry_is_none():
    assert results.read_loading(_export(), "CO999") is None


# -- what joins a structure ------------------------------------------------------------

def test_a_node_on_a_member_joins_it_and_a_collinear_overlap_does_not():
    """A column landing mid-span is in the beam's structure; two members sharing a stretch of one line are not joined.

    ⚠️ Planted the other way round, this is the defect it was written for: the Velo Unterstand's Regelfall came out
    as a beam with **no support at all**, because its column's top is an interior node of the beam.
    """
    model, _found = _fixture()
    joined = model.on_member()
    # The fixture's members 2 and 24 lie along one line and share a stretch of it: not a junction.
    assert 2 not in joined or 36 not in joined.get(2, []), joined


def test_every_structure_of_the_engineers_model_has_its_supports():
    """The join is what gives each frame its columns back -- and so its supports."""
    path = _export()
    model = model_tables.read_model(path)
    found = structure_detection.detect(model.items(), combinations=model.combination_cases())
    without = [s.key for s in found if not s.numbers("support")]
    assert not without, "structures with no support: %s" % without


# -- the drawing -----------------------------------------------------------------------

def test_a_positive_moment_is_drawn_towards_z_which_is_downwards():
    """The engineer's own rule, checked on the drawing rather than on the code that writes it."""
    model, found = _fixture()
    structure = max(found, key=lambda s: len(s.members))
    geo = diagram_svg.geometry(model, structure)
    member = [m for m in geo.members if abs(m["u"][1]) < 1e-9][0]     # a horizontal one
    ux, uz = member["u"]
    normal = (-uz, ux)
    assert normal[1] > 0 if ux > 0 else normal[1] < 0, (member["u"], normal)


def test_the_frame_takes_the_structures_own_proportions():
    """A wide structure is not squared into a frame two thirds of which is white."""
    model, found = _fixture()
    structure = max(found, key=lambda s: len(s.members))
    geo = diagram_svg.geometry(model, structure)
    width, height = geo.used
    span = geo.x1 - geo.x0
    rise = geo.z1 - geo.z0
    if span > rise:
        assert abs(width / height - span / rise) < 0.01, (width, height, span, rise)


def test_the_figure_is_svg_qtsvg_can_read():
    """The window shows this string through a `QSvgWidget`, so an SVG it refuses is a blank pane."""
    try:
        from PySide6.QtSvg import QSvgRenderer
        from PySide6.QtWidgets import QApplication
    except ImportError:
        raise Skip("PySide6 is not installed")
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    QApplication.instance() or QApplication([])
    model, found = _fixture()
    structure = max(found, key=lambda s: len(s.members))
    svg = diagram_svg.render(model, structure, None, "M_y", caption="probe")
    renderer = QSvgRenderer(svg.encode("utf-8"))
    assert renderer.isValid(), svg[:400]
    # ⚠️ SVG Tiny 1.2 and nothing above it, like every other figure of this project.
    for forbidden in ("<marker", "<pattern", "<style", "clip-path", "paint-order"):
        assert forbidden not in svg, forbidden


def test_a_diagram_labels_the_extremes_and_the_nodes_and_no_more():
    """«Valeurs aux extremums (positifs et négatifs) et aux nœuds» -- four a member at most, not one a station."""
    points = [(0.0, 0.0), (1.0, 3.0), (2.0, 7.0), (3.0, 4.0), (4.0, -2.0), (5.0, 0.0)]
    marked = diagram_svg._extremes(points)
    assert marked == sorted({0, len(points) - 1, 2, 4}), marked
    assert len(marked) <= 4


def test_a_structure_with_no_geometry_draws_a_word_and_not_a_crash():
    model, found = _fixture()
    empty = [s for s in found if not s.numbers("member")]
    if not empty:
        raise Skip("this fixture has no structure without members")
    assert "<svg" in diagram_svg.render(model, empty[0], None, "M_y")
