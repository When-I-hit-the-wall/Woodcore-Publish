"""The schemas' and the static models' plane geometry, written once in calc/domains/dimension.py (spec 2026-10-20-indices-et-niveaux, ARCH-004, a leftover of the base saine's D4).

`schema_geometry` (mm) and `statics_geometry` (m) each carried a word-for-word copy of the functions a dimension and the tracking are drawn with -- the ends of a linear dimension, its direction, its line, an angle's arc, the point a typed distance lands on, the nearest tracking ray --, each reading the constants of its own module. They are now wrappers of one line around dimension.py's kernels, handing their own anchor reader and tolerance; these checks hold the two modules to the kernels on the same points, the one written in mm and the other in m, and the three copies of a label's box and the unit vector to one.
"""

TIER = "fast"  # tests/run_tests.py --fast

import ast
import math

from conftest import ROOT

from domains import dimension, plan_svg, schema_geometry, schema_svg, statics_geometry, statics_svg_layout

WRAPPED = ("fmt_number", "typed_point", "along", "dimension_ends", "dimension_direction", "dimension_line", "dimension_angle", "nearest_ray")


def test_the_two_modules_wrap_the_kernels_in_one_line():
    for module in ("schema_geometry", "statics_geometry"):
        tree = ast.parse((ROOT / "calc" / "domains" / (module + ".py")).read_text(encoding="utf-8"))
        bodies = {node.name: node.body for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in WRAPPED}
        assert set(bodies) == set(WRAPPED), (module, sorted(set(WRAPPED) - set(bodies)))
        for name, body in bodies.items():
            code = [statement for statement in body if not (isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Constant))]
            assert len(code) == 1 and isinstance(code[0], ast.Return), (module, name, "more than one line")


def test_both_units_follow_the_same_kernel():
    rays = [{"angle": 0.0, "unit": (1.0, 0.0)}, {"angle": 90.0, "unit": (0.0, 1.0)}]
    for module, scale in ((schema_geometry, 1000.0), (statics_geometry, 1.0)):
        anchor, point = (0.0, 0.0), (2.0 * scale, 0.05 * scale)
        ray, snapped = module.nearest_ray(rays, anchor, point)
        assert ray is rays[0] and math.isclose(snapped[0], 2.0 * scale) and snapped[1] == 0.0, module.__name__
        assert module.typed_point(anchor, rays[1], "1,5") == (0.0, 1.5)
        assert module.typed_point(anchor, rays[1], "abc") is None
        assert module.fmt_number(4.97881) == ("4.98" if module is schema_geometry else "4.979")
        assert module.fmt_number(-0.2666, 0) == "0" and module.fmt_number(1200, 0) == "1200" and module.fmt_number("x") == "x"


def test_a_label_box_and_a_unit_vector_are_written_once():
    assert schema_svg.label_corners is statics_svg_layout.label_corners is plan_svg.number_corners is dimension.box_corners
    assert schema_svg._unit is statics_svg_layout._unit is plan_svg._unit is dimension.unit
    assert dimension.unit((1.0, 1.0), (1.0, 1.0)) == (1.0, 0.0), "two points in one: (1, 0) (D-15)"
    assert dimension.unit((0.0, 0.0), (0.0, 2.0)) == (0.0, 1.0)
