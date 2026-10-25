"""What a material's values give: its design values -- typed, set by the norm or deduced --, its state and the tabs it is offered in (spec docs/requirements/active/2026-10-24-onglet-materiaux.md, REQ-008 to REQ-010; issue #110).

**A design value typed always wins.** One left empty is, for a member, the value SIA 265 sets for shear and tension perpendicular to the grain (3.3.2.2 solid timber, 3.4.2.2 glulam: `sia265.set_design_value`), else f_d = f_k / (γ_M/η_M) -- SIA 265 (3) and Tabelle 1, η_t = η_w = 1 --; for a panel, f_d = η_mod · f_k / γ_M -- SIA 265/1 Tableaux 6 and 9, moisture class 1, medium duration. Rounded half up to 0.1 N/mm², as the norm's tables print theirs (`round_tenth`). η_w and η_t are not applied here: the check that reads the material applies them, as it does to Tabellen 8 and 9's values (T37).

**The limit the prototype showed** (T36): for a class the tables do not list, the general rule does not always give a table's value -- f_c,90,k = 2.5 N/mm² gives 2.5 / 1.7 = 1.5 where Tabelle 8 prints 1.8 for C24. That is what 3.3.2.2 asks («gemäss 2.2.2»); Woodcore applies the norm, and the rule a deduced value carries says so.

The state counts what a material lacks (T42): a strength lacks when neither its characteristic nor its design value -- typed, set or deduced -- is there; a modulus and ρ_k when they are empty. A cell the norm itself gives no value for (SIA 265/1, «valeurs non disponibles») is not counted as missing: it is said apart. Words are the tab's: a state and a rule are codes with their numbers. No Qt here.
"""

from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal

from domains import materials_contract as contract
from norms import sia265, sia265_1

# The levels of a state, in the order the pane shows them: what is complete, what blocks a use, what is wrong, what is only said.
LEVELS = ("ok", "warn", "error", "info")


@dataclass(frozen=True)
class Design:
    """A design value and how it was had: `how` is typed, set (by a clause of the norm) or deduced; `rule` the code of its rule (general, set, panel), `params` its numbers."""
    value: float
    how: str
    rule: str = ""
    params: dict = field(default_factory=dict)


@dataclass(frozen=True)
class State:
    """One thing the pane says of a material: its code -- the tab's words are `mat_st_<code>` --, its level (`LEVELS`) and the numbers its words are filled with."""
    code: str
    level: str
    params: dict = field(default_factory=dict)


@dataclass(frozen=True)
class Use:
    """Whether a material is offered in a tab: `tab` the tab's key, `status` yes / no / soon, `need` the code of what it lacks."""
    tab: str
    status: str
    need: str = ""


def round_tenth(x):
    """`x` rounded half up to 0.1 -- 12.35 is 12.4 --, as the norm prints a design value; binary rounding would take a half down."""
    return float(Decimal(repr(float(x))).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))


def _num(value):
    return value if isinstance(value, (int, float)) and not isinstance(value, bool) else None


# --- a member -----------------------------------------------------------------------

def member_design(m, strength):
    """The design value f_<strength>_d of a member, or None: typed, else set by the norm, else deduced from f_<strength>_k."""
    values = m.get("values") or {}
    typed = _num(values.get("f_%s_d" % strength))
    if typed is not None:
        return Design(typed, "typed")
    family = m.get("family")
    set_value = sia265.set_design_value(family, "f_%s_d" % strength)
    if set_value is not None:
        value, clause, _page = set_value
        return Design(value, "set", "set", {"clause": clause})
    k = _num(values.get("f_%s_k" % strength))
    if k is None:
        return None
    gamma = sia265.family_gamma_m(family)
    return Design(round_tenth(k / gamma), "deduced", "general", {"k": k, "gamma": gamma})


# --- a panel -----------------------------------------------------------------------

def cell(m, loading, key, direction, column):
    values = (((m.get("grid") or {}).get(loading) or {}).get(key) or {}).get(direction) or []
    return _num(values[column]) if column < len(values) else None


def panel_factors(m):
    """(γ_M, η_mod) of a panel's product -- SIA 265/1 Tableau 6 through its group, Tableau 9 for moisture class 1 and medium duration --, or None where it names no product."""
    product = m.get("product")
    if product not in sia265_1.products():
        return None
    return sia265_1.product_gamma_m(product), sia265_1.eta_mod(product)


def panel_design(m, loading, row, direction, column):
    """The design value of `row` (f_m, f_c_90…) under `loading`, in `direction` and `column`, or None: typed, else η_mod · f_k / γ_M."""
    typed = cell(m, loading, row + "_d", direction, column)
    if typed is not None:
        return Design(typed, "typed")
    k = cell(m, loading, row + "_k", direction, column)
    factors = panel_factors(m)
    if k is None or factors is None:
        return None
    gamma, eta = factors
    return Design(round_tenth(eta * k / gamma), "deduced", "panel", {"k": k, "gamma": gamma, "eta": eta})


def unavailable(m, loading, row):
    return "%s.%s_k" % (loading, row) in (m.get("unavailable") or ()) or "%s.%s" % (loading, row) in (m.get("unavailable") or ())


def panel_cells(m):
    """Every cell of a panel's grid the norm's shape asks: (loading, row, direction, column)."""
    for loading, rows in contract.PANEL_GRID.items():
        for row in rows:
            for direction in contract.directions(m):
                for column in range(contract.column_count(m)):
                    yield loading, row, direction, column


# --- what a material lacks -----------------------------------------------------------

def missing(m):
    """How many values a material lacks (T42): a strength without its characteristic nor its design value, an empty modulus or ρ_k. A cell the norm gives no value for is not counted (`not_given`)."""
    if m.get("type") == "member":
        values = m.get("values") or {}
        n = sum(1 for s in contract.MEMBER_STRENGTHS if member_design(m, s) is None)
        return n + sum(1 for key in contract.MEMBER_STIFFNESS if _num(values.get(key)) is None)
    if m.get("type") == "panel":
        n = sum(1 for v in (m.get("rho_k") or [None]) if _num(v) is None)
        for loading, row, direction, column in panel_cells(m):
            if unavailable(m, loading, row):
                continue
            if contract.is_strength(row):
                if cell(m, loading, row + "_k", direction, column) is None and panel_design(m, loading, row, direction, column) is None:
                    n += 1
            elif cell(m, loading, row, direction, column) is None:
                n += 1
        return n
    return 0


def not_given(m):
    """How many cells of a panel the norm marks «valeurs non disponibles»."""
    if m.get("type") != "panel":
        return 0
    return sum(1 for loading, row, _d, _c in panel_cells(m) if unavailable(m, loading, row))


def deduced(m):
    """How many design values Woodcore filled in -- deduced, or set by the norm -- rather than the engineer typed: the ones written in italics."""
    if m.get("type") == "member":
        return sum(1 for s in contract.MEMBER_STRENGTHS if (member_design(m, s) or Design(0, "typed")).how != "typed")
    if m.get("type") == "panel":
        return sum(1 for loading, row, direction, column in panel_cells(m)
                   if contract.is_strength(row) and (panel_design(m, loading, row, direction, column) or Design(0, "typed")).how != "typed")
    return 0


def has_source(m):
    source = m.get("source") or {}
    kind = source.get("kind")
    return (kind == "url" and bool(str(source.get("url") or "").strip())) or (kind == "pdf" and bool(source.get("file"))) or kind in ("norm", "book")


def is_shipped(m):
    return bool(m.get("origin"))


def status(m, others=(), lang="fr"):
    """What the pane says of a material (T42), most serious first, «complete» where nothing but information is said. `others` are the materials its name is compared with -- a shipped material is not."""
    out = []
    if m.get("example"):
        out.append(State("example", "warn"))
    if not m.get("weight"):
        out.append(State("no_weight", "warn"))
    n = missing(m)
    if n:
        out.append(State("missing", "warn", {"n": n}))
    if not is_shipped(m) and not has_source(m):
        out.append(State("no_source", "warn"))
    if not is_shipped(m):
        name = contract.name(m, lang).strip().casefold()
        if name and any(o.get("id") != m.get("id") and contract.name(o, lang).strip().casefold() == name for o in others):
            out.append(State("same_name", "error"))
    if m.get("type") == "panel" and not m.get("columns") and _num(m.get("thickness")) is None:
        out.append(State("no_thickness", "info"))
    given = not_given(m)
    if given:
        out.append(State("not_given", "info", {"n": given}))
    d = deduced(m)
    if d:
        out.append(State("deduced", "info", {"n": d}))
    if not any(s.level in ("warn", "error") for s in out):
        out.insert(0, State("ok", "ok"))
    return out


def summary(m):
    """The summary of the «Résistances» accordion: 0 for complete, else the number of values missing."""
    return missing(m)


def available_in(m):
    """Where a material is offered (T44, Q-004 answer A): the permanent loads need a weight; the member checks a member complete in what they read and a panel giving one of their resistances (issue #112, REQ-012: `member_check_material.usable_in_checks`); the connectors a class's ρ_k -- a member of the engineer's own «soon»; plates and diaphragms are to come."""
    from domains import member_check_material
    out = [Use("tab_ac_selfweight", "yes" if m.get("weight") else "no", "" if m.get("weight") else "weight")]
    if m.get("type") == "member":
        usable = member_check_material.usable_in_checks(m)
        if m.get("origin") == "sia265":
            rho = _num((m.get("values") or {}).get("rho_k"))
            out.append(Use("tab_mc", "yes" if usable else "no", "" if usable else "design"))
            out.append(Use("tab_connections", "yes" if rho else "no", "" if rho else "rho"))
        else:
            out.append(Use("tab_mc", "yes" if usable else "no", "" if usable else "design"))
            out.append(Use("tab_connections", "soon", "" if _num((m.get("values") or {}).get("rho_k")) else "rho"))
    if m.get("type") == "panel":
        usable = member_check_material.usable_in_checks(m)
        out.append(Use("tab_mc", "yes" if usable else "no", "" if usable else "design"))
        out.append(Use("tab_plates", "soon", "" if missing(m) == 0 else "design"))
        out.append(Use("tab_connections", "soon", "" if any(_num(v) for v in (m.get("rho_k") or ())) else "rho"))
    return out
