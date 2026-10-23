"""A domain invented for tests/test_calc_tab_base.py (spec 2026-10-22-onglet-neige-type, ARCH-003): a beam's load, a span and a load per metre, nothing of the snow -- what proves the calculation tabs' base (calc/tools/calc_tab.py) draws a domain it was never written for.

It has a field of each kind the base draws (a number that may follow a variable, buttons with a free value, tiles, a check box, a drop-down list), a red message and an orange one each on its field, results that are not its inputs, a drawing and a chart, and two excerpts of a norm -- SIA 261's, the file the snow reads, so that the bubble shows real words. Not a module of calc/: Woodcore never loads it.
"""

import re

import validation
from domains import links
from domains.contracts import Choice, Declaration, Field, Message

DOMAIN = "fake-load"
FOLDER = "loads/fake"
ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.+-]*$")
SOURCE_SCHEMA_VERSION = "1.0"
LINKABLE = {links.SELF: {"span": "m"}}
PREFIX = "fk_"
NORM = "sia261-2020-5.2-schnee"
SHAPES = ("box", "slab")


def new_source(cid):
    return {"schema_version": SOURCE_SCHEMA_VERSION, "id": cid, "name": "", "label": "", "group": "",
            "span": 4.0, "kind": "light", "factor": 1.0, "shape": "box", "braced": False, "grade": "C24"}


def stamp_version(src):
    src["schema_version"] = SOURCE_SCHEMA_VERSION
    return src


def declaration():
    return Declaration(PREFIX, NORM, (("main", ("span", "kind", "shape")), ("more", ("braced", "grade"))), (
        Field("span", "number", "m", excerpts=("5.2.2",), minimum=0.0, maximum=50.0, decimals=2, linkable=True),
        Field("kind", "buttons", "", choices=(Choice("light", PREFIX + "c_light", 0.5), Choice("heavy", PREFIX + "c_heavy", 2.0)),
              excerpts=("5.2.4",), minimum=0.0, maximum=10.0, free_id="custom", free_key="factor"),
        Field("shape", "tiles", "", choices=tuple(Choice(s, PREFIX + "c_" + s, excerpts=("fig3",)) for s in SHAPES), excerpts=("fig3",)),
        Field("braced", "checkbox", "", excerpts=("5.3.4",)),
        Field("grade", "select", "", choices=(Choice("C24", PREFIX + "c_C24"), Choice("GL24h", PREFIX + "c_GL24h"))),
    ))


def visible_fields(src):
    return [f.key for f in declaration().fields if not (f.key == "grade" and not src.get("braced"))]


def _q(src):
    return {"light": 0.5, "heavy": 2.0}.get(src.get("kind"), src.get("factor") or 0)


def messages(src):
    out = []
    if not isinstance(src.get("span"), (int, float)) or src["span"] <= 0:
        out.append(Message("span", "span", "error", {}))
    elif src["span"] > 10:
        out.append(Message("long", "span", "info", {"span": src["span"]}))
    return out


def check_source(src, where="loads/fake"):
    if messages(src) and messages(src)[0].severity == "error":
        raise validation.ValidationError("%s: span is %r" % (where, src.get("span")))


def read_source(path):
    import json
    return json.loads(open(path, encoding="utf-8").read())


def build_instance(src, here=None, inputs=None):
    q = _q(src)
    m = q * src["span"] ** 2 / 8
    vars_ = {"span": {"value": src["span"], "unit": "m", "symbol": "l"}, "q": {"value": q, "unit": "kN/m", "symbol": "q"},
             "M_d": {"value": m, "unit": "kNm", "symbol": "M_d"}}
    return {"vars": vars_, "results": ["M_d"], "steps": []}


def results(instance):
    return [name for name in instance["vars"] if name not in ("span",)]


def figure_svg(src, lang=None):
    return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 20" width="100" height="20"><line x1="0" y1="10" x2="%d" y2="10" stroke="#1f1f1f"/></svg>\n' % min(100, src["span"] * 10)


def tile_svg(shape):
    return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 98 64" width="98" height="64"><rect x="10" y="10" width="%d" height="40" fill="#ffffff" stroke="#1f1f1f"/></svg>\n' % (78 if shape == "slab" else 40)


def chart(src):
    return {"x": {"min": 0.0, "max": 10.0, "label": "l", "unit": "m", "step": 2.0}, "y": {"min": 0.0, "max": 30.0, "label": "M", "unit": "", "step": 10.0},
            "series": [{"name": "M_d", "points": [(0.0, 0.0), (10.0, _q(src) * 12.5)]}],
            "marks": [{"label": "l", "x": src["span"], "y": _q(src) * src["span"] ** 2 / 8, "series": "M_d"}]}


WORDS = {lang: {"fk_list": "Beams", "fk_empty": "No beam", "fk_s_main": "Main", "fk_s_more": "More", "fk_f_span": "Span", "fk_f_kind": "Kind",
                "fk_f_shape": "Shape", "fk_f_braced": "Braced", "fk_f_grade": "Grade", "fk_c_light": "light", "fk_c_heavy": "heavy", "fk_c_box": "box",
                "fk_c_slab": "slab", "fk_c_C24": "C24", "fk_c_GL24h": "GL24h", "fk_msg_span": "The span is missing", "fk_msg_long": "A long span: {span} m",
                "fk_module_drawing": "Beam", "fk_module_chart": "Moment", "fk_x_5.2.2": "q_k", "fk_x_5.2.4": "C_e", "fk_x_fig3": "Figure 3", "fk_x_5.3.4": "hindered"}
         for lang in ("fr", "de", "en")}
