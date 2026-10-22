"""Calculation primitives shared by every domain module.

Mirrors the JSON shape documented in docs/architecture/data-contracts.md §3.1: a domain is a dict of {"vars": {...}, "steps": [...], "checks": [...]}. Every var/step/ check must carry a norm reference -- enforced here so a missing citation fails loudly at build time instead of silently reaching a report. The reference (`norm`) is always required; its clause (`norm_ref`) may be empty, for a document cited as a whole -- a connection's design aid has no clause to give (docs/domain/connections.md §3.3quinquies) -- and is then printed without one.
"""

import json
import os
import shutil
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
    """A line's level, where one is still given: since v0.120 a line carries none, lib/line-levels.json saying the level each line is printed from (spec 2026-10-20-indices-et-niveaux, UI-002, D-13) -- a level given is still checked."""
    if level is not None and level not in _VALID_LEVELS:
        raise EngineError(f"{label}: level must be 1, 2, or 3, got {level!r}")


def var(value, unit, symbol, label, source, norm, norm_ref,
        description=None, choices=None, group=None, group_label=None, keep=None, heading=None, level=None):
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
        "source": source,
        "norm": norm,
        "norm_ref": norm_ref,
    }
    # the level each line is printed from is lib/line-levels.json's, read by Typst when it prints (UI-002): a var carries one only where a caller still states it
    if level is not None:
        v["level"] = level
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


def step(name, result, uses, norm, norm_ref, formula=None,
         description=None, bold=None, inline=None, level=None):
    """`description` explains the step itself -- what its formula's symbols stand for, which rows of a source table it sums. It is shown as a footnote on the formula, the way a var's description is shown on the var: a step's result var is never printed with notes (it is a result, not an input), so an explanation of the working belongs here.

    `inline` sets the formula, its numbers and the answer on **one** row -- `M_(u,k) = 0.3 dot f_(u,k) dot d^2.6 = 0.3 dot 510 dot 10^2.6 = 60910.397 Nmm` -- instead of the two the display gives by default. It is the engineer's own request for a chain of short formulas (v0.84), and it is a property of the formula rather than of the report: a step short enough to be read across one line says so, a long one (the wind load's, the layer sums) does not. A bounded formula is never set inline -- it has no numbers line to join (docs/typst/api-conventions.md §10bis).

    `bold` says this step's numbers line is an *answer* even though its result is not one of the calculation's `results` -- the wind load's Staudruck q_p, which every global wind force is built from and which its own sheet sets apart. It is read exactly like `results` membership: the numbers line is set bold, and the step's operands keep their own rows instead of being absorbed into its substituted formula (docs/typst/api-conventions.md §10bis). Presentation, like a var's `group`, and decided here for the same reason -- which value a calculation puts its weight on is a property of the calculation.
    """
    _check_citation(norm, norm_ref, f"step '{name}'")
    _check_level(level, f"step '{name}'")
    s = {
        "name": name,
        "result": result,
        "uses": list(uses),
        "norm": norm,
        "norm_ref": norm_ref,
    }
    if level is not None:
        s["level"] = level
    if formula is not None:
        s["formula"] = formula
    if description is not None:
        s["description"] = description
    if bold is not None:
        s["bold"] = bold
    if inline:
        s["inline"] = True
    return s


def check(name, eta, status, norm, norm_ref, unit="", level=None):
    _check_citation(norm, norm_ref, f"check '{name}'")
    _check_level(level, f"check '{name}'")
    out = {
        "name": name,
        "eta": eta,
        "unit": unit,
        "status": status,
        "norm": norm,
        "norm_ref": norm_ref,
    }
    if level is not None:
        out["level"] = level
    return out


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


    def to_dict(self):
        return {"vars": self.vars, "steps": self.steps, "checks": self.checks}


def source_bytes(data):
    """`data` as every JSON file of a project is written: two spaces, the keys in their order, accents as they are, a last line ending, UTF-8 and LF on every platform. The one serialisation of a source and of an export (spec 2026-10-19-base-saine-nettoyage, G1, G2): a tab, a domain and the export all write a file through it, so a source saved by the window and the same source saved by woodcore-cli are the same bytes."""
    return (json.dumps(data, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def digest(*parts):
    """The SHA-256 of `parts` written as canonical JSON (keys sorted): a fingerprint that does not move when a dict is built in another order -- an annex's inputs, the reference sheets' rows, a node of the graph of dependencies (spec 2026-10-21-graphe-dependances, ARCH-RISK-1106; two copies of this until v0.120). An annex's digest is the same bytes as before; the reference sheets' rows, written until then with `ensure_ascii=False`, are digested once more -- their cache in the window's folder, never the project's."""
    import hashlib
    return hashlib.sha256(json.dumps(list(parts), sort_keys=True, default=str).encode("utf-8")).hexdigest()


def write_json(path, data):
    """Writes `data` to `path` (`source_bytes`), beside it first and moved into place, so that a reader never sees half a file and a failure leaves the old one."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    part = p.with_name(p.name + ".part")
    part.write_bytes(source_bytes(data))
    os.replace(part, p)
    return p


def _payload(content):
    """`content` as the bytes a generated file holds: text encoded UTF-8 with LF line ends whatever the platform (spec 2026-10-15 ARCH-RISK-C11), bytes as they are."""
    if isinstance(content, bytes):
        return content
    return content.replace("\r\n", "\n").encode("utf-8")


def write_managed(base, files, previous=()):
    """Writes `files` ({path relative to `base`: text or bytes}) under the folder `base`, each moved into place whole (a reader never sees half a file), and removes what `previous` lists -- the paths the last export wrote there -- and `files` no longer does. **Nothing else of `base` is touched**: a folder the engineer sees (a tab's Exports/Figures/) may hold files of his own, which no glob of it may sweep away (spec 2026-10-15 D-17, ARCH-RISK-C01). A file whose bytes have not changed is left alone, so Git sees a change only where there is one. A path that leaves `base` is refused. Returns the paths written."""
    base = Path(base)
    root = base.resolve()

    def inside(rel):
        target = (base / rel).resolve()
        if target != root and root not in target.parents:
            raise ValueError(f"{rel!r} leaves {base}")
        return target

    written = []
    for rel, content in files.items():
        target = inside(rel)
        payload = _payload(content)
        if target.is_file() and target.read_bytes() == payload:
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        partial = target.with_name(f"{target.name}.{os.getpid()}.part")
        partial.write_bytes(payload)
        os.replace(partial, target)
        written.append(rel)
    wanted = {Path(rel).as_posix() for rel in files}
    for rel in previous:
        if Path(rel).as_posix() in wanted:
            continue
        target = inside(rel)
        if target.is_file():
            target.unlink()
    return written


def _strings(data):
    """Every string `data` holds, at any depth."""
    if isinstance(data, str):
        yield data
    elif isinstance(data, dict):
        for value in data.values():
            yield from _strings(value)
    elif isinstance(data, (list, tuple)):
        for value in data:
            yield from _strings(value)


class Figures:
    """Where the export writes the figures of one kind (project.FIGURE_KINDS) and how its JSON names them.

    In a project laid out by folders a figure lies in its tab's `Exports/Figures/` -- its one copy (D-10) -- and the JSON names it from the Typst root, `/Plans/Position-plan/Exports/Figures/P01.svg`, the spelling Typst reads at any depth; lib/calc-engine.typ `figure-path` reads that name as it stands. In a project laid out before, or a folder no project owns (a test's), it lies in `data/<sub>/` as it always has and the JSON names it `<sub>/P01.svg` from data/, which `figure-path` reads as `../data/<sub>/P01.svg` -- so an export written by an older Woodcore is read as it was.
    """

    def __init__(self, data_dir, kind, here=None):
        """`data_dir` the export's data/ -- None for a prepare() that only names its figures, as one that writes nothing does in a test --, `kind` one of project.FIGURE_KINDS, `here` the project laid out by folders whose Exports/Figures/ they go into, or None."""
        import project  # project reads validation, which reads this module's neighbours; nothing here is needed at import
        self.kind = kind
        self.data_dir = Path(data_dir) if data_dir is not None else None
        self.sub = project.FIGURE_KINDS[kind]
        self.here = here if here is not None and here.has_folders else None
        if self.here:
            self.data_dir = self.data_dir or self.here.data_dir
            self.folder = self.here.figures_dir(kind)
        else:
            self.folder = self.data_dir / self.sub if self.data_dir is not None else None

    def name(self, file):
        """The JSON's name of the figure `file` (`P01.svg`)."""
        if self.here:
            return self.here.from_root(self.folder / file)
        return f"{self.sub}/{file}"

    def path(self, name):
        """The file a JSON's name stands for -- either spelling, so that a record an older export wrote is found too."""
        if name.startswith("/"):
            return (self.here.typst_root if self.here else self.data_dir) / name[1:]
        return self.data_dir / name

    def rel(self, name):
        """`name`'s path inside this kind's folder, or None where it lies elsewhere."""
        target = self.path(name).resolve()
        folder = self.folder.resolve()
        return target.relative_to(folder).as_posix() if folder in target.parents else None

    def listed(self, data):
        """The figures of this kind a JSON names -- the manifest of what the export that wrote it put in the folder."""
        return sorted({rel for rel in (self.rel(s) for s in _strings(data) if s.endswith(tuple(FIGURE_SUFFIXES))) if rel})

    def write(self, files, previous):
        """Writes `files` ({JSON name: content}) into this kind's folder and removes what `previous` -- the JSON the last export wrote, or {} -- named there and `files` no longer does (`write_managed`). In a project laid out before, data/<sub>/ is Woodcore's alone and every file of it the export did not write is removed, as it always was. In one laid out by folders, the data/<sub>/ an older export left behind goes with it: data/ keeps only the JSON."""
        by_rel = {}
        for name, content in files.items():
            rel = self.rel(name)
            if rel is None:
                raise ValueError(f"{name!r} does not lie in {self.folder}")
            by_rel[rel] = content
        if self.here:
            old = self.listed(previous)
        else:
            old = [p.relative_to(self.folder).as_posix() for p in self.folder.iterdir() if p.is_file()] if self.folder.is_dir() else []
        self.folder.mkdir(parents=True, exist_ok=True)
        write_managed(self.folder, by_rel, old)
        if self.here:
            left = self.data_dir / self.sub
            if left.is_dir():
                shutil.rmtree(left)


# The files a figure is written as: the export's SVGs, a plan's background reduced to its page, an annex's PDF.
FIGURE_SUFFIXES = (".svg", ".pdf", ".png", ".jpg", ".jpeg")


def figures(data_dir, kind):
    """The Figures of `kind` for the export folder `data_dir`: in the tab's Exports/Figures/ where `data_dir` is the export of a project laid out by folders (project.owning), in data/ otherwise. A `data_dir` of None names the figures as data/ does and writes nothing."""
    import project
    return Figures(data_dir, kind, project.owning(data_dir) if data_dir is not None else None)


def previous_json(path):
    """The JSON an earlier export wrote at `path`, or {} -- the manifest `Figures.write` removes by."""
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
