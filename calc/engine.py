"""Calculation primitives shared by every domain module.

Mirrors the JSON shape documented in docs/architecture/data-contracts.md §3.1: a domain is a dict of {"vars": {...}, "steps": [...], "checks": [...]}. Every var/step/ check must carry a norm reference -- enforced here so a missing citation fails loudly at build time instead of silently reaching a report. The reference (`norm`) is always required; its clause (`norm_ref`) may be empty, for a document cited as a whole -- a connection's design aid has no clause to give (docs/domain/connections.md §3.3quinquies) -- and is then printed without one.
"""

import json
from pathlib import Path


class Note(str):
    """A warning the export prints as it stands, in English, and Woodcore's window shows in its own language.

    `code` names the window's sentence -- `"warn_" + code` in its STRINGS -- and `args` fills that sentence's holes; an argument that is itself a Note is written in the window's language too. It is `schema.Refused`'s arrangement for a warning rather than a refusal, and for the same reason: parsing an English sentence back into its parts is the fragility a code avoids (periodic audit 260916, AUD-4-11). A Note is a `str`, so everything that prints, joins, compares or exports a warning goes on doing so unchanged.
    """

    def __new__(cls, code, text, **args):
        note = super().__new__(cls, text)
        note.code = code
        note.args = args
        return note


class EngineError(Exception):
    """Raised when a calculation is missing required provenance."""


_VALID_LEVELS = (1, 2, 3)


def _check_citation(norm, norm_ref, label):
    if not norm:
        raise EngineError(f"{label} is missing norm")
    if not isinstance(norm_ref, str):
        raise EngineError(f"{label}: norm_ref must be a string ('' for a document cited as a whole)")


def _check_level(level, label):
    if level not in _VALID_LEVELS:
        raise EngineError(f"{label}: level must be 1, 2, or 3, got {level!r}")


def var(value, unit, symbol, label, level, source, norm, norm_ref,
        description=None, choices=None, group=None, group_label=None, keep=None, heading=None):
    """`group` is a display grouping and nothing else: consecutive input vars carrying the same group are printed on one row, joined by a semicolon (C_e and C_T, L and B), instead of on a row each. `group_label` names that row when the values need saying what they are ("Gebäude Geometrie: L = 20.18 m; B = 7.8 m"); it is read off the var that opens the run, and a group without one is printed bare. Both live on the var rather than in the report because which values belong together, and what to call them, is a property of the calculation, like their order (docs/typst/api-conventions.md §10bis, docs/domain/loads.md §3.3bis).

    `keep` says this var states an *input of the calculation* and keeps its own row even where an intermediate step's substituted formula already shows its number. Without it the rule is the one show-calc has always applied -- an intermediate step's operands are not set out twice -- which is right for a value that exists only to be fed into the next line, and wrong for the ones a reader looks up first: a dowel's diameter, a member's density and its thickness, all of which now feed a formula of their own (v0.84).

    `heading` announces the run of calculations this var opens, on a line of its own above it -- «Charakteristische Lochleibungsfestigkeiten für C24», which the report sets with its own colon. It is the way the Bemessungsbeispiele zur SIA 265 set a block (p. 291) and the engineer asked for it in those words (v0.84); like `group` and `inline` it is a property of the calculation, since which runs a reader groups is something the calculation knows and the display cannot.

    ⚠️ It is printed where this var's own first row is printed, so it follows every rule that decides whether that row exists at all: a var above the report's level announces nothing, and neither does one absorbed into an intermediate step's substituted formula. Put it on a var that is certainly printed -- the first of the run, `keep` where it is an operand.
    """
    _check_citation(norm, norm_ref, f"var '{symbol}'")
    if not isinstance(unit, str):
        raise EngineError(f"var '{symbol}' unit must be a string (use '' if dimensionless)")
    _check_level(level, f"var '{symbol}'")
    v = {
        "value": value,
        "unit": unit,
        "symbol": symbol,
        "label": label,
        "level": level,
        "source": source,
        "norm": norm,
        "norm_ref": norm_ref,
    }
    if description is not None:
        v["description"] = description
    if choices is not None:
        v["choices"] = choices
    if group is not None:
        v["group"] = group
    if group_label is not None:
        v["group_label"] = group_label
    if keep:
        v["keep"] = True
    if heading:
        v["heading"] = heading
    return v


def step(name, level, result, uses, norm, norm_ref, formula=None,
         description=None, bold=None, inline=None):
    """`description` explains the step itself -- what its formula's symbols stand for, which rows of a source table it sums. It is shown as a footnote on the formula, the way a var's description is shown on the var: a step's result var is never printed with notes (it is a result, not an input), so an explanation of the working belongs here.

    `inline` sets the formula, its numbers and the answer on **one** row -- `M_(u,k) = 0.3 dot f_(u,k) dot d^2.6 = 0.3 dot 510 dot 10^2.6 = 60910.397 Nmm` -- instead of the two the display gives by default. It is the engineer's own request for a chain of short formulas (v0.84), and it is a property of the formula rather than of the report: a step short enough to be read across one line says so, a long one (the wind load's, the layer sums) does not. A bounded formula is never set inline -- it has no numbers line to join (docs/typst/api-conventions.md §10bis).

    `bold` says this step's numbers line is an *answer* even though its result is not one of the calculation's `results` -- the wind load's Staudruck q_p, which every global wind force is built from and which its own sheet sets apart. It is read exactly like `results` membership: the numbers line is set bold, and the step's operands keep their own rows instead of being absorbed into its substituted formula (docs/typst/api-conventions.md §10bis). Presentation, like a var's `group`, and decided here for the same reason -- which value a calculation puts its weight on is a property of the calculation.
    """
    _check_citation(norm, norm_ref, f"step '{name}'")
    _check_level(level, f"step '{name}'")
    s = {
        "name": name,
        "level": level,
        "result": result,
        "uses": list(uses),
        "norm": norm,
        "norm_ref": norm_ref,
    }
    if formula is not None:
        s["formula"] = formula
    if description is not None:
        s["description"] = description
    if bold is not None:
        s["bold"] = bold
    if inline:
        s["inline"] = True
    return s


def check(name, eta, level, status, norm, norm_ref, unit=""):
    _check_citation(norm, norm_ref, f"check '{name}'")
    _check_level(level, f"check '{name}'")
    return {
        "name": name,
        "eta": eta,
        "unit": unit,
        "level": level,
        "status": status,
        "norm": norm,
        "norm_ref": norm_ref,
    }


class Calculation:
    """A single domain's vars/steps/checks, built up incrementally."""

    def __init__(self):
        self.vars = {}
        self.steps = []
        self.checks = []

    def add_var(self, name, **kwargs):
        self.vars[name] = var(**kwargs)
        return self.vars[name]

    def add_step(self, **kwargs):
        s = step(**kwargs)
        self.steps.append(s)
        return s

    def add_check(self, **kwargs):
        c = check(**kwargs)
        self.checks.append(c)
        return c

    def to_dict(self):
        return {"vars": self.vars, "steps": self.steps, "checks": self.checks}


def write_json(path, data):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")
