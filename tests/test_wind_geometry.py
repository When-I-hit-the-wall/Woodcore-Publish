"""The 37 buildings of SIA 261 Annexe C as numbers (calc/norms/sia261-2020-annexc-wind-geometry.json, calc/domains/wind_geometry.py; spec 2026-10-23-onglet-vent-briques, REQ-010, ARCH-011, D-23).

What is held: every building has its geometry and no table is without one; every surface its table gives a coefficient of -- external, or internal of its own -- has its place, and the geometry places none the table does not name; the six of the prototype (31, 32, 36, 40, 59a, 59b) are its DRAWN -- the same proportions, roof, slope and strips; every family builds and renders in four views; a building whose geometry is taken away is said, not drawn.
"""

TIER = "fast"  # tests/run_tests.py --fast

import json
import re

import conftest
from domains import model3d as m3
from domains import wind_forces, wind_geometry, wind_source
from norms import sia261_wind

PROTOTYPE = conftest.ROOT / "docs" / "requirements" / "prototypes" / "2026-10-23-onglet-vent" / "index.html"


def _table_surfaces(number):
    src = wind_source.new_source("X")
    src["table"] = number
    table = sia261_wind.table(number)
    return {s["surface"] for s in wind_forces.analysis(src)["local"]} | {c["surface"] for c in table["columns"] if c["group"] == "cpi"}


# The letters a figure draws that its table gives no coefficient of: drawn too, as every letter of a figure is (D-37) -- the stand's edge strips
DRAWN_ONLY = {"50": {"m", "o"}}


def test_every_building_has_its_geometry_and_every_surface_its_place():
    assert sorted(wind_geometry.data()["buildings"]) == sorted(sia261_wind.NUMBERS)
    for number in sia261_wind.NUMBERS:
        wanted = _table_surfaces(number) | DRAWN_ONLY.get(number, set())
        assert wind_geometry.surfaces(number) == wanted, (number, sorted(wind_geometry.surfaces(number) ^ wanted))


def test_the_six_of_the_prototype_are_its_drawn():
    """REQ-010: DRAWN of the prototype's index.html -- roof, slope, h : b : d and the strips -- for Tableaux 31, 32, 36, 40, 59a, 59b."""
    html = PROTOTYPE.read_text(encoding="utf-8")
    block = html[html.index("var DRAWN = {"):html.index("};", html.index("var DRAWN = {"))]
    for number in ("31", "32", "36", "40", "59a", "59b"):
        line = re.search(r'"%s":\{(.*?)\}\s*,?\s*$' % re.escape(number), block, re.M).group(1)
        geo = wind_geometry.building(number)
        assert json.loads(re.search(r"hbd:(\[[^\]]+\])", line).group(1)) == geo["hbd"], number
        roof = re.search(r'roof:"(\w+)"', line).group(1)
        assert geo["roof"]["kind"] == roof, number
        slope = re.search(r"slope:(\d+)", line)
        assert (int(slope.group(1)) if slope else None) == geo["roof"].get("slope"), number
        strips = re.findall(r'\["(\w)","(\w+)","(\w+)"\]', line)
        laid = sorted(z[0] for z in geo["zones"] if z[1] == "strip")
        assert laid == sorted(s[0] for s in strips), (number, laid, strips)


def test_every_family_builds_and_renders_in_four_views():
    families = {}
    for number in sia261_wind.NUMBERS:
        families.setdefault(wind_geometry.building(number)["family"], []).append(number)
        sc = wind_geometry.scene(number, phi=45, forces={"f1": (10.0, "10 kN"), "f2": (-5.0, "−5 kN"), "f3": (2.0, "2 kN")})
        for name, (yaw, pitch) in wind_geometry.VIEWS.items():
            items = m3.render(sc, m3.View(yaw=yaw, pitch=pitch))
            if name == "iso":
                assert any(it["kind"] == "polygon" and it["key"] for it in items), number
    assert set(families) == {"prism", "open", "stand", "canopy", "eave", "curved"}


def test_the_drawing_follows_the_table_never_what_is_typed():
    """UI-008: the building of Tableau 36 is the same whatever b, d and h are typed -- the table's 0,5 : 2 : 1."""
    mdl = wind_geometry.model("36")
    assert (mdl.h, mdl.b, mdl.d) == (0.5, 2, 1)


def test_a_building_with_no_geometry_is_said():
    """UI-026: the safety net while a building is not drawn -- its geometry taken away, the scene refuses naming the table and the file, and the tab shows the norm's figure instead (V5)."""
    held = wind_geometry.data()["buildings"].pop("40")
    try:
        try:
            wind_geometry.scene("40")
        except KeyError as exc:
            assert "40" in str(exc) and wind_geometry.GEOMETRY in str(exc)
        else:
            raise AssertionError("a building with no geometry was drawn")
    finally:
        wind_geometry.data()["buildings"]["40"] = held
