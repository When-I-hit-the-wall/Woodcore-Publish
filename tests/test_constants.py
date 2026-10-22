"""The lists of allowed values `validation.py` restates from the domain modules.

`validation.py` cannot import `domains/plan.py` or `domains/statics.py`: they import *it*. So it carries its own copy of the symbol types, member kinds, support types, release degrees of freedom and dimension kinds, and says so in a comment. The copies agree today. Nothing made them agree -- adding a member kind to `statics.py` without touching `validation.py` would pass silently, and the new kind would reach `data/statics.json` unchecked.

These are the three lines that close that: the copies are compared, and a difference names what is in one and not the other.

The real fix is a small module both import. Until then this test is the fix.
"""

TIER = "fast"  # tests/run_tests.py --fast

import conftest
from domains import plan, statics
import validation


def _diff(name, restated, original):
    a, b = set(restated), set(original)
    assert a == b, (
        f"validation.{name} has drifted from the module it was copied from.\n"
        f"  only in validation.py : {sorted(a - b) or 'nothing'}\n"
        f"  only in the module    : {sorted(b - a) or 'nothing'}\n"
        f"Add the value to both, or move the list into one place they can share."
    )


def test_static_member_kinds_match():
    _diff("STATIC_MEMBER_KINDS", validation.STATIC_MEMBER_KINDS, statics.MEMBER_KINDS)


def test_static_supports_match():
    _diff("STATIC_SUPPORTS", validation.STATIC_SUPPORTS, statics.SUPPORT_TYPES)


def test_static_release_dofs_match():
    _diff("STATIC_RELEASE_DOFS", validation.STATIC_RELEASE_DOFS, statics.RELEASE_DOFS)


def test_static_dimension_kinds_match():
    _diff("STATIC_DIMENSION_KINDS", validation.STATIC_DIMENSION_KINDS, statics.DIMENSION_KINDS)


def test_static_dimension_units_match():
    assert validation.STATIC_DIMENSION_UNITS == statics.DIMENSION_UNITS, (
        f"validation.STATIC_DIMENSION_UNITS says {validation.STATIC_DIMENSION_UNITS}, "
        f"statics.DIMENSION_UNITS says {statics.DIMENSION_UNITS} -- a length is in "
        f"metres and an angle in degrees, and the two copies must say so alike"
    )


def test_plan_symbol_types_match():
    """Every STE symbol the plan module draws is one validation.py will accept, and no more."""
    _diff("PLAN_KINDS", validation.PLAN_KINDS.keys(), plan.TYPES.keys())


def test_plan_symbol_shapes_are_accepted():
    """The shape each symbol is actually drawn as is one its validation entry allows.

    Not an equality: a type whose subtypes change its shape (M, L, drawn as a line or as a point) declares one `geo` in plan.TYPES and both shapes in validation. What must never happen is a symbol drawn as a shape validation would refuse.
    """
    for symbol, spec in plan.TYPES.items():
        geo = spec["geo"]
        drawn = {geo} if isinstance(geo, str) else set(geo)
        allowed = validation.PLAN_KINDS[symbol]
        assert drawn <= allowed, (
            f"plan.TYPES[{symbol!r}] is drawn as {sorted(drawn)}, which "
            f"validation.PLAN_KINDS[{symbol!r}] does not allow ({sorted(allowed)})"
        )


def test_moisture_classes_are_read_from_the_norm():
    """The moisture classes export_all.py and validation.py accept are SIA 265 Tabelle 3's, read from calc/norms/ -- since v0.77 no list of them is restated anywhere (the engineer's rule: no norm value twice)."""
    from norms import sia265
    assert validation.moisture_classes() == sia265.moisture_class_ids() == (1, 2, 3)
    assert not hasattr(validation, "MOISTURE_CLASSES"), "a restated copy of Tabelle 3 is back in validation.py"


def test_connection_id_pattern_is_the_same_on_both_sides():
    """A connection's id is checked by its own module and again by validation.py."""
    from domains import connection
    for probe in ("SD001-V1", "A01", "x.1+2-3", "1abc"):
        a = connection.ID_PATTERN.fullmatch(probe) is not None
        b = validation.CONNECTION_ID.fullmatch(probe) is not None
        assert a == b, (
            f"{probe!r}: connection.ID_PATTERN says {a}, validation.CONNECTION_ID "
            f"says {b} -- the id a source may carry and the id an export may carry "
            f"must be the same id"
        )


def test_every_source_id_is_checked_by_one_pattern():
    """The id of a source is its file name, and six modules check it with a pattern each: the connection's was held level with validation.py and the other five by nothing (periodic audit 260916, AUD-6-15)."""
    import importlib
    import sys
    from conftest import ROOT
    from domains import connection, connector, plan, schema, statics
    tools = str(ROOT / "calc" / "tools")
    if tools not in sys.path:
        sys.path.insert(0, tools)
    source_archive = importlib.import_module("source_archive")
    patterns = {m.__name__: m.ID_PATTERN.pattern for m in (connection, connector, plan, schema, statics, source_archive)}
    assert len(set(patterns.values())) == 1, patterns


def test_a_connectors_figures_are_drawn_in_the_glossarys_languages():
    """`connector.FIGURE_LANGUAGES` restated the three languages with no test beside it (AUD-6-14)."""
    from domains import connector
    from i18n import strings
    assert tuple(connector.FIGURE_LANGUAGES) == tuple(strings.LANGUAGES)

# --- the connectors' lists (v0.67) ------------------------------------------
# `validation.py` cannot import `domains/connector.py` or `domains/dowel.py` either: they import it.
# Since the connectors left Excel these lists have no other home, so a kind of fastener added to the
# module and not to the validator would reach data/connectors.json unchecked.

def test_connector_types_match():
    from domains import connector
    _diff("CONNECTOR_TYPES", validation.CONNECTOR_TYPES, connector.TYPES)


def test_connector_assemblies_match():
    from domains import dowel
    _diff("CONNECTOR_ASSEMBLIES", validation.CONNECTOR_ASSEMBLIES, dowel.ASSEMBLIES)


def test_connector_roles_match():
    from domains import connector
    _diff("CONNECTOR_ROLES", validation.CONNECTOR_ROLES, connector.ROLES)


def test_connector_species_are_read_from_the_norm():
    """A member's species is one of SIA 265 Tabelle 22's rows, read from calc/norms/ and restated nowhere (v0.77)."""
    from norms import sia265
    assert validation.connector_species() == sia265.species_names() == ("Nadelholz", "Laubholz")
    assert not hasattr(validation, "CONNECTOR_SPECIES"), "a restated copy of Tabelle 22's species is back in validation.py"


# --- the detail schemas' lists ----------------------------------------------
# domains/schema.py imports validation.py too, so the same restatement, and the same guard.

def test_schema_element_kinds_match():
    from domains import schema
    _diff("SCHEMA_ELEMENT_KINDS", validation.SCHEMA_ELEMENT_KINDS, schema.ELEMENT_KINDS)


def test_schema_dimension_kinds_match():
    from domains import schema
    _diff("SCHEMA_DIMENSION_KINDS", validation.SCHEMA_DIMENSION_KINDS, schema.DIMENSION_KINDS)


def test_schema_dimension_units_match():
    from domains import schema
    assert validation.SCHEMA_DIMENSION_UNITS == schema.DIMENSION_UNITS, (
        f"validation.SCHEMA_DIMENSION_UNITS says {validation.SCHEMA_DIMENSION_UNITS}, "
        f"schema.DIMENSION_UNITS says {schema.DIMENSION_UNITS} -- a schema is drawn at its "
        f"real size in millimetres, and the two copies must say so alike"
    )


def test_a_schema_marker_takes_a_connectors_own_kinds():
    """The fastener kinds a schema's markers may carry are the connectors' own -- one list, so a kind added to domains/connector.py reaches a marker with no second edit."""
    from domains import connector, schema
    _diff("SCHEMA_CONNECTOR_KINDS", validation.SCHEMA_CONNECTOR_KINDS, connector.TYPES)
    _diff("schema.CONNECTOR_KINDS", schema.CONNECTOR_KINDS, connector.TYPES)


def test_a_connectors_entity_id_is_the_schemas_own():
    """`connector.ENTITY_ID` is `schema.ENTITY_ID`, restated rather than imported.

    The two modules cannot import each other at module level -- `schema` reads `connector.TYPES`, and
    `connector` reads `schema` only inside its functions, which is what keeps the import graph acyclic
    (connector.figures' own note). So the pattern is written twice, and this is what keeps the two equal:
    a member's element id and a fastener's marker id are checked here against the very expression that
    accepts them there.
    """
    from domains import connector, schema
    assert connector.ENTITY_ID.pattern == schema.ENTITY_ID.pattern, (
        "connector.ENTITY_ID is %r and schema.ENTITY_ID is %r -- a connector would accept an id the schema "
        "refuses, or the other way about" % (connector.ENTITY_ID.pattern, schema.ENTITY_ID.pattern))

def test_every_figure_names_one_font_family():
    """QtSvg takes the whole font-family string as one name, so a list like "Arial, Helvetica, sans-serif" matches nothing and the window draws the text in a fallback face whose advances are not Arial's (docs/typst/language.md §4bis, v0.52). plan_svg still wrote the list, alone of the drawings (periodic audit 260916, AUD-6-24)."""
    import re
    from conftest import ROOT
    from domains import plan_svg, schema_svg, statics_svg
    for module in (plan_svg, schema_svg, statics_svg):
        assert module.FONT == "Arial", "%s.FONT is %r" % (module.__name__, module.FONT)
    for path in (ROOT / "calc" / "domains").glob("*_svg.py"):
        for family in re.findall(r'font-family="([^"{%]*)"', path.read_text(encoding="utf-8")):
            assert "," not in family, "%s writes font-family=%r" % (path.name, family)


def test_the_orange_of_a_value_written_over_is_one_colour():
    """A value shown otherwise than it is held is orange in the window and in the report alike: the window writes an overridden grade, moisture class or section that way (v0.70, v0.77), and since v0.80 so does the footnote `val` adds under a value printed in another unit than the one it carries.

    Two copies of one hex, in two languages -- so they are compared here rather than left to drift. Since v0.90 the window's is the light scheme's `override` in calc/tools/theme.json (theme.py), where connectors_tab.py and schema_tab.py each carried an OVERRIDE_COLOR of their own; the dark scheme's is a lighter orange, the report being printed on white whatever the window's scheme. And no module of calc/tools/ writes the orange again.
    """
    import re
    from conftest import ROOT
    import theme
    typ = conftest.engine_source()
    found = re.search(r'#let override-colour = rgb\("(#[0-9a-fA-F]{6})"\)', typ)
    assert found, "lib/calc-engine.typ no longer declares override-colour"
    ours = theme.tokens("light")["override"]
    assert ours.lower() == found.group(1).lower(), "theme.json's light override is %s, lib/calc-engine.typ writes %s" % (ours, found.group(1))
    for path in sorted((ROOT / "calc" / "tools").glob("*.py")):
        assert found.group(1).lower() not in path.read_text(encoding="utf-8").lower(), "%s writes the orange again -- read theme.colour('override')" % path.name


def test_fire_protection_lists_match():
    """validation.py restates what a fire-protection plan's entries may be, since domains/fire.py imports it."""
    from domains import fire
    _diff("FIRE_SURFACES", validation.FIRE_SURFACES, fire.SURFACES)
    _diff("FIRE_DOOR_KINDS", validation.FIRE_DOOR_KINDS, fire.DOOR_KINDS)
    _diff("FIRE_COLLECTIONS", validation.FIRE_COLLECTIONS, fire.COLLECTIONS)
