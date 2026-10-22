"""The variables the report itself computes, read back out of a compiled report (docs/project/purpose.md §1, docs/typst/formulas.md §10quinquies, docs/ui/window.md §10quater).

`#var`, `#eq`, `#var-unit`, what `show-polar-moment` publishes and what every `verify-*` publishes all live
in **one Typst state**, `var-registry` in `lib/calc-engine.typ`, and nowhere else: none of it reaches
`data/`, which is the standing condition §1 puts on everything computed in Typst. So the one way Python can
say what a report holds is to ask Typst, and that is what this module does.

⚠️ **It is read, never written.** Nothing here writes into a project, and in particular nothing writes these
values into `data/`: `data/` is Typst's *input*, and a file the report produced sitting in it would reverse
the pipeline's own direction (§2). What is cached is cached outside the project, beside the plan renders
(`usersettings.cache_dir`), for the reason those are: the project is synced by NextCloud and versioned with
the report, and a cache is reproduced by reading again.

⚠️ **A read costs a full compile.** Measured on the example project at 8-10 s, against 9.8 s for
`typst compile` of the same report -- a state's final value is only known once the document has been laid
out to convergence, so there is no cheaper question to ask. That measurement is what decides the window's
behaviour: the tab reads **once**, when it is first opened, and then reads its cache until something that
could change the answer has changed (`stamp`). A tab that re-read on every switch would cost ten seconds a
switch, which is the argument §10quater made for the RFEM tab's `on_shown` reading nothing (a tab retired in 0.117).

⚠️ **The state's default must be exactly the one the engine declares**, and that is sharper than it looks: a
mismatched default does not merely give a wrong default, it is the value the document's own `update`
functions are handed, so the *document* fails to compile and the error surfaces inside `lib/formula.typ` --
a defect that reads as one of the engine's. `REGISTRY_DEFAULT` is therefore held equal to
`lib/calc-engine.typ`'s own declaration by `tests/test_variables.py`, the way the distance tables are held
equal to the files `lib/distance.typ` names (§11).

👉 **The level does not enter into it** and the language barely does. A level chooses what is *printed*,
never what is stored, so level 1 and level 3 give byte-identical JSON (held by a test) and one read serves
all three reports. The language reaches the four labels the glossary composes (`eta_w`'s «Feuchteklasse 2»)
and no value and no unit, so a read passes no `--input lang=` at all: what the tab shows is what the report
itself holds, and the window's own chrome follows the window -- the loads tab's rule, whose labels stay as
the workbook wrote them (§4bis, §10quater).
"""

import hashlib
import json
import os
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path

import proc
import project

# The state `lib/calc-engine.typ` declares, and the default it declares it with. Both are written here once
# and held equal to that file by tests/test_variables.py -- see the third warning above for what a mismatch
# costs, which is the document's own compile and not merely a wrong answer here.
REGISTRY_STATE = "var-registry"
REGISTRY_DEFAULT = '(stack: ("",), domains: (:))'

# The name the report's own variables travel under **inside the PDF** (v0.110): `woodcore-document` attaches
# them there (`lib/calc-engine.typ`'s `variables-attachment`), and this module reads them back out.
# ⚠️ **Matched on the BASENAME**, because Typst resolves that name as a path relative to the file that calls
# `pdf.attach` -- what actually reaches the PDF is `_woodcore/lib/woodcore-variables.json`, the engine's own
# place inside the project. Measured, not assumed; and a basename is right whatever a project calls its
# generated folder, which `layout.generated` is a project's to state (§12).
ATTACHMENT = "woodcore-variables.json"

# The report's own variables -- what `#var` writes outside every `var-domain`, and what a formula on any line
# can name without saying where from. The registry keys them by the empty string; the window gives that a
# word of its own rather than showing a blank row.
REPORT_DOMAIN = ""

# What a `verify-*` publishes is a var-domain named `"<member>-verify-<check>"` (§3.3undecies), and that name
# is a contract rather than a convention: `show-result-summary` finds every member check by exactly this
# fragment (lib/summary.typ), so recognising it here says no more than the engine already says.
CHECK_MARK = "-verify-"

# How long a read may take before it is given up on. A compile of the engineer's own report is seconds; this
# is the runaway case -- a report that cannot converge, a Typst that never returns.
TIMEOUT_S = 180

# A cached read is kept per project and carries this; a cache written by an older shape is ignored rather
# than read wrongly.
CACHE_VERSION = 1

# ⚠️ **A file another program holds is not a report that does not compile**, and saying so would be a false
# diagnosis about the engineer's own work. The whole project sits in NextCloud, whose sync client holds a file
# open while it uploads it, and Typst then fails on the *operating system's* error rather than on one of its
# own -- `os error 32` is Windows' ERROR_SHARING_VIOLATION, `33` its lock violation. Such a failure is tried
# **once more** after a moment, and where it persists it is said as what it is (`file_busy`) rather than as a
# broken report. Nothing else is retried: «file not found» is a real defect of the report (a picture the
# engineer has not put there yet) and retrying it would only say it twice.
TRANSIENT = ("os error 32", "os error 33")
RETRY_AFTER_S = 1.2

# Whether the window may read a report **by itself**, the first time its tab is opened. `WOODCORE_VARIABLES_READ=0`
# stops it, which the test suite does, for the reason it sets `WOODCORE_TYPST_CHECK=0` (typst_check.ENV): a
# reading is a full compile, and a suite that brings every tab forward to look at its buttons must not pay for
# one -- nor leave a thread running behind a window it is about to close. «Relire» is unaffected: what is turned
# off is reading without being asked, never reading.
AUTO_ENV = "WOODCORE_VARIABLES_READ"


def auto_enabled():
    """Whether this process reads a report without being asked to."""
    return os.environ.get(AUTO_ENV, "1") != "0"


def fmt_value(value, digits=3):
    """A value as the report prints it: at most `digits` decimals, trailing zeros dropped (`1.7291232` -> `1.729`, `0.8` -> `0.8`, `438` -> `438`); a word passes through unchanged.

    ⚠️ `lib/calc-engine.typ`'s `fmt-decimals` is the original and the only one that reaches a page; this is
    the same rule in Python, restated here because the tab that needs it is imported *by* `woodcore_gui`, so
    it cannot import that module's own `fmt_value` back (§10sexies). `schema.fmt_number` and
    `statics.fmt_number` are the same rule again, for the figures they draw; `tests/test_variables.py` holds
    all of them equal, which is what keeps four copies from becoming four rules.
    """
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return "" if value is None else str(value)
    text = f"{value:.{digits}f}"
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return "0" if text in ("-0", "") else text


# Where a value comes from, as the Variables tab says it (the engineer's issue 13, «les Excel, Woodcore […] et l'export JSON des variables calculées dans Typst»): what a var's `source` prefix means. A var's `source` is free text in every schema (calculations, connections, connectors), so this table is the one place its prefixes are named, and `tests/test_variable_sources.py` sweeps every source of the example project so that a prefix nobody added here fails the suite instead of being shown as unknown (docs/architecture/data-contracts.md §3.1).
EXCEL, WOODCORE, TYPST, UNKNOWN = "excel", "woodcore", "typst", "unknown"
PROVENANCE = {
    "excel": EXCEL,         # a workbook's cell: excel:<workbook>!<sheet>!<cell>
    "python": WOODCORE,     # computed by a module of calc/ or a project's script: python:domains/dead_load.py
    "norm": WOODCORE,       # read off a norm table by Woodcore: norm:SIA 261 Tabelle 8
    "woodcore": WOODCORE,   # an input saved in Woodcore's window: woodcore:connectors/SD-10.json
}


def parse_source(source):
    """A var's `source` as (kind, workbook, sheet, cell) -- `excel:<workbook>!<sheet>!<cell>` -- or (kind, "", "", rest) for every other kind (`python:domains/dead_load.py`, `norm:…`, `woodcore:…`). Moved from the loads tab (v0.117), whose detail pane the Variables tab took over."""
    kind, _, rest = (source or "").partition(":")
    if kind == "excel":
        parts = rest.split("!")
        if len(parts) >= 3:
            return kind, parts[0], "!".join(parts[1:-1]), parts[-1]
    return kind, "", "", rest


def provenance_of(source):
    """EXCEL, WOODCORE or UNKNOWN from a var's `source` alone. ⚠️ A var read out of a **document's registry** is TYPST whatever its `source` says -- `#var("s_k", domain: (…))` copies an export's var, `excel:` source and all, into the registry -- and that precedence is the assembler's (`variable_sources.provenance`), which knows where a var was read; this function only reads the string."""
    kind = parse_source(source)[0]
    return PROVENANCE.get(kind, UNKNOWN) if kind else UNKNOWN


class VariablesError(Exception):
    """A read that did not happen: `args[0]` a sentence that stands on its own in English, for a caller with no window and for a test; `code` and `detail` what Woodcore's window turns into its own three languages (the arrangement `positions_workbook.WorkbookError` and `schema.Refused` already have)."""

    def __init__(self, message, code, **detail):
        super().__init__(message)
        self.code = code
        self.detail = detail


@dataclass(frozen=True)
class Variable:
    """One variable of the registry, as `var-record` stores it (lib/formula.typ).

    `key` is what one **types into a call** and `symbol` is what the **page prints**, and the two are not the
    same word -- `q_k11` is set q_(k,11) -- which is the whole reason `#find`'s own table carries both
    columns (§10bis, v0.85). A window that showed one of them would be the wrong one half the time.
    """

    key: str
    domain: str
    value: object          # a number, or a word: a load model's name, a category of Nutzfläche
    unit: str
    symbol: str
    label: str = ""
    description: str = ""
    norm: str = ""
    norm_ref: str = ""
    source: str = ""
    # What only an export's var carries -- the level a value is printed at and, for a value chosen from a list, that list -- for the Variables tab's detail (spec 2026-10-08-onglet-variables-trois-colonnes, D-006). Never written into the cache: a registry's vars have neither, and `save` writes its fields by name.
    level: object = None
    choices: tuple = ()

    @property
    def is_number(self):
        return isinstance(self.value, (int, float)) and not isinstance(self.value, bool)

    @property
    def citation(self):
        """The norm as the report's own right-hand column sets it: «SIA 265 4.2.1» -- no §, the engineer's rule of 20.10.2026 (spec 2026-10-21-commandes-typst-refonte, UI-001) -- and a table or an annex as it is written (`norm-text`, §10)."""
        if not self.norm:
            return ""
        ref = self.norm_ref
        return f"{self.norm} {ref}" if ref else self.norm


@dataclass
class Registry:
    """Every variable one read found, kept **by domain and in the order the registry states them** -- which is the order the report declared them in, and so the order an engineer looks for them in."""

    domains: dict = field(default_factory=dict)   # name -> [Variable]
    stamp: str = ""

    @property
    def count(self):
        return sum(len(found) for found in self.domains.values())

    def variables(self):
        for found in self.domains.values():
            for var in found:
                yield var

    def units(self):
        """Every unit in it, commonest first: what the window offers as a filter. A dimensionless value's unit is the empty string, which the window names rather than offering blank."""
        counted = {}
        for var in self.variables():
            counted[var.unit] = counted.get(var.unit, 0) + 1
        return [unit for unit, _n in sorted(counted.items(), key=lambda kv: (-kv[1], kv[0]))]


def domain_kind(name):
    """What kind of domain a name is, for the window to say so beside it.

    Only two of the three are read off the name, and both are contracts rather than guesses: the empty string
    *is* the report's own default domain, and `-verify-` *is* how a member check publishes (`CHECK_MARK`).
    Everything else -- a `#member`'s own domain, a connection's published forces, a `var-domain` a column
    declares -- is `"named"`, and the window shows its name and claims nothing more: which of those three a
    name is cannot be told from the name, and a window that guessed would be wrong about somebody's column
    sooner or later.
    """
    if name == REPORT_DOMAIN:
        return "report"
    if CHECK_MARK in name:
        return "check"
    return "named"


def expression():
    """The Typst expression one read evaluates -- the one place it is written down.

    `state(key, default).final()`, rebuilt from the standard library, because `typst eval --in` evaluates in
    the **standard library's** scope and not the document's: the document's own `var-registry` binding is not
    visible there (`unknown variable: var-registry`), while a state is keyed by a string and so can be named
    again from outside. `.final()` is what makes the answer the whole document's rather than one point in it,
    exactly as `show-load-summary` reads it (§10bis).
    """
    return f'state("{REGISTRY_STATE}", {REGISTRY_DEFAULT}).final()'


def _sources(here, mode):
    """The files a reading of document `mode` reads, as far as can be said without compiling it: calc/stamps.py's own enumeration (`stamps.enumerated`) -- the .typ files of the document's folder, config.typ, commands.typ and references.bib at the Typst root, the export's lib/, calc/ and **data/**, and the pictures. **Never the whole Typst root**, which in a project of three documents is the project's own folder, and would take the other two documents, the workbooks and the archives for sources of this one's variables; and never the export's out/ or stamps/, which a build writes and a reading does not read (the stamp a compile records would otherwise make every reading stale the moment it was taken)."""
    import stamps
    return stamps.enumerated(here, mode)


def _walk(here, mode="rs"):
    """How many files document `mode` is made of, how large they are together, and the newest modification time among them -- the three `stamp` is built from, and the one `pdf_is_current` needs on its own where no stamp of a compile says more."""
    newest, total, count = 0.0, 0, 0
    for path in _sources(here, mode):
        try:
            info = path.stat()
        except OSError:      # vanished mid-walk, or a name Windows will not stat: not worth a failure
            continue
        newest = max(newest, info.st_mtime)
        total += info.st_size
        count += 1
    return count, total, newest


def stamp(here=None, mode="rs"):
    """What would change the answer, as one short string: how many files document `mode` -- the report by default -- is made of, how large they are together, and the newest modification time among them.

    That is the document's own `.typ` files -- the entry, `Sections/` -- `config.typ` and `commands.typ`, and
    everything under the engine copy: `lib/`, the glossary and the norm tables it reads, and **`data/`**,
    which counts because `var-of(...)` reads the export and a `#var` carrying a value out of it moves when
    the workbook does (`_sources`).

    ⚠️ The PDF is deliberately left out. It is written *by* the very compile a read pays for, so a stamp that
    counted it would be stale the moment it was taken -- and again after every *Exporter PDF*.
    """
    here = here or project.current()
    count, total, newest = _walk(here, mode)
    return f"{CACHE_VERSION}:{count}:{total}:{newest:.0f}"


def pdf_is_current(here=None, mode="rs"):
    """Whether document `mode`'s PDF -- the report's by default -- is still the document's own, so the registry attached to it is the one a compile would give.

    **Where a compile of it left a stamp** (calc/stamps.py), the stamp answers: its PDF is current when not one of the files that compile read has changed since, whatever the flags it was compiled with -- a level chooses what is printed and never what is stored. A digest and not a modification time, so a file saved again with the same bytes, or the export writing identical JSON, leaves it current. Where the PDF is not the one the stamp was taken of -- written since by a route that stamps nothing -- the stamp says nothing of it, and today's rule judges.

    **Where there is no stamp**, a **modification time**: the PDF carries no record of the sources it was made from, so what can be asked is whether anything has been touched since it was written. A source saved in the same second as the PDF reads as *not* current, which errs the safe way -- the tab then compiles rather than showing a value that may be one edit behind.
    """
    here = here or project.current()
    pdf = here.document_pdf(mode)
    try:
        written = pdf.stat().st_mtime
    except OSError:
        return False
    import stamps
    if stamps.read(here, mode) is not None:
        changed, why = stamps.changed(here, mode, [], ignore_flags=True)
        if why.code != "stamp_pdf_changed":
            return not changed
    return written > _walk(here, mode)[2]


def cache_file(here=None, mode="rs"):
    """Where one project's last read of document `mode` is kept: outside the project, beside the plan renders and the commands tab's example pages (`usersettings.cache_dir`, §10quater). Named after the project file's own path, so two projects never share one and a project moved is simply read again -- and, for the convention d'utilisation and the base de projet, after the document too; the report's keeps the name it has always had, so a reading made before the three documents is still found."""
    import usersettings
    here = here or project.current()
    key = hashlib.sha256(str(here.file.resolve()).encode("utf-8")).hexdigest()[:16]
    return usersettings.cache_dir("variables") / (f"{key}.json" if mode == "rs" else f"{key}-{mode}.json")


def _from_json(payload, stamp_=""):
    domains = {}
    for name, found in (payload.get("domains") or {}).items():
        variables = []
        for key, record in (found or {}).items():
            if not isinstance(record, dict):
                continue
            variables.append(Variable(
                key=key,
                domain=name,
                value=record.get("value"),
                unit=record.get("unit") or "",
                symbol=record.get("symbol") or key,
                label=record.get("label") or "",
                description=record.get("description") or "",
                norm=record.get("norm") or "",
                norm_ref=record.get("norm_ref") or "",
                source=record.get("source") or "",
            ))
        domains[name] = variables
    return Registry(domains=domains, stamp=stamp_)


def from_pdf(here=None, mode="rs"):
    """The registry out of document `mode`'s **own PDF** -- the report's by default --, where it is there and still the document's -- the free reading (v0.110, the engineer's choice of three).

    `woodcore-document` attaches it at every compile, so the PDF that was going to be written anyway carries
    what a reading would otherwise cost 8-10 s to recompute. The tab therefore opens instantly on a report that
    has just been exported, and falls back to `read()` where there is no PDF, where it is older than the
    sources, or where it was written by an engine that did not attach one yet.

    Gives back a `Registry` whose `stamp` is today's -- so `is_current` says yes -- or **None**, which means
    only «not available», never «something is wrong»: every way this can fail is a reason to compile instead,
    and none of them is worth a word to the engineer. A PDF being written as it is read, a pypdf that cannot
    parse it, an attachment from an older engine: all of them simply return None.
    """
    here = here or project.current()
    if not pdf_is_current(here, mode):
        return None
    try:
        from pypdf import PdfReader
    except ImportError:
        return None
    try:
        attachments = PdfReader(here.document_pdf(mode)).attachments
        # the basename, for the reason ATTACHMENT records
        named = [n for n in attachments if Path(str(n)).name == ATTACHMENT]
        if not named:
            return None
        raw = attachments[named[0]][0]
        payload = json.loads(bytes(raw).decode("utf-8"))
    except Exception:  # broad: a cache -- every failure here (pypdf's family, an attachment from an older engine) means «compile instead», and the compile reads the sources and stops on their defects
        return None       # every failure here means «compile instead», and none of them is the engineer's
    if not isinstance(payload, dict) or "domains" not in payload:
        return None
    return _from_json(payload, stamp_=stamp(here, mode))


def read(here=None, timeout=TIMEOUT_S, mode="rs"):
    """Compiles document `mode` -- the report by default -- and gives back everything its registry holds, caching it.

    ⚠️ This is a **full compile** and costs what one costs (8-10 s on the example project): a caller with a
    window runs it where a compile may take its time, and never on the way to painting a tab.

    Every failure is a `VariablesError` carrying a code, so the window says it in its own language: a project
    with no report, a Typst that is not on the PATH, a report that does not compile -- whose own error is
    handed on as the detail, since it is the engineer's report that is at fault and his message that says
    where -- a read that ran too long, an answer that is not the registry it should be, and a **file another
    program holds** (`file_busy`), which is tried once more first and is deliberately not called a report that
    does not compile (`TRANSIENT`).
    """
    here = here or project.current()
    main = here.document_typ(mode)
    if not main.is_file():
        raise VariablesError(f"variables: the project has no report at {main}", "no_report", path=str(main))
    root = here.typst_root
    command = [
        project.typst_executable(), "eval",
        "--in", str(main),
        "--root", str(root),
        "--format", "json",
        expression(),
    ]
    taken = stamp(here, mode)

    def run():
        try:
            return proc.run(command, capture_output=True, cwd=str(root), timeout=timeout)
        except FileNotFoundError as exc:
            raise VariablesError(f"variables: typst was not found -- {exc}", "no_typst") from exc
        except subprocess.TimeoutExpired as exc:
            raise VariablesError(
                f"variables: reading the report took longer than {timeout} s", "timeout", seconds=timeout) from exc

    done = run()
    if done.returncode != 0:
        # Typst's own message, its last lines: it names the file and the line, which nothing here could.
        output = (done.stderr or done.stdout or b"").decode("utf-8", "replace").strip()
        output = "\n".join(output.splitlines()[-30:])
        # a file another program holds for a moment, not a report that is wrong: tried once more (TRANSIENT)
        if any(marker in output for marker in TRANSIENT):
            time.sleep(RETRY_AFTER_S)
            done = run()
            if done.returncode != 0:
                again = (done.stderr or done.stdout or b"").decode("utf-8", "replace").strip()
                again = "\n".join(again.splitlines()[-30:])
                if any(marker in again for marker in TRANSIENT):
                    raise VariablesError(
                        f"variables: a file of the report is held by another program\n{again}",
                        "file_busy", output=again)
                output = again
        if done.returncode != 0:
            raise VariablesError(
                f"variables: the report did not compile (exit {done.returncode})\n{output}",
                "compile_failed", exit_code=done.returncode, output=output)
    try:
        payload = json.loads(done.stdout.decode("utf-8", "replace"))
    except json.JSONDecodeError as exc:
        raise VariablesError(f"variables: what typst gave back is not JSON -- {exc}", "not_json") from exc
    if not isinstance(payload, dict) or "domains" not in payload:
        raise VariablesError(
            "variables: what typst gave back is not the variable registry -- is this project's engine copy up to date?",
            "not_registry")
    found = _from_json(payload, stamp_=taken)
    save(found, here, mode)
    return found


def best(here=None, timeout=TIMEOUT_S, mode="rs"):
    """The registry by the **cheapest route that is still correct** -- the policy, in one place (v0.110).

    The report's own PDF carries its variables (`woodcore-document`), so where that PDF is newer than every
    source there is nothing to recompute: the compile that wrote it is the one that paid. Where it is not --
    no PDF yet, a source edited since, an engine older than the attachment -- the report is compiled, which is
    `read()` and its 8-10 s.

    ⚠️ Both routes give the **same registry**, which is not a hope: it is the same
    `var-registry.final()` serialised by the same `json.encode`, and a test compares the two field by field on
    the example project. So this function chooses a price and never an answer.
    """
    here = here or project.current()
    found = from_pdf(here, mode)
    if found is not None:
        save(found, here, mode)
        return found
    return read(here, timeout=timeout, mode=mode)


def save(found, here=None, mode="rs"):
    """Writes one read of document `mode` into the cache, beside itself and then moved into place, so a read interrupted leaves no half file. A cache that cannot be written is not worth a failure -- the values are on screen either way."""
    path = cache_file(here, mode)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "cache_version": CACHE_VERSION,
            "stamp": found.stamp,
            "domains": {
                name: {var.key: {
                    "value": var.value, "unit": var.unit, "symbol": var.symbol,
                    "label": var.label, "description": var.description,
                    "norm": var.norm, "norm_ref": var.norm_ref, "source": var.source,
                } for var in found_vars}
                for name, found_vars in found.domains.items()
            },
        }
        temporary = path.with_name(path.name + ".new")
        temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
        os.replace(temporary, path)
    except OSError:
        pass
    return path


def cached(here=None, mode="rs"):
    """The last read of document `mode` of this project, or `None` where there is none and where it cannot be read. It carries its own `stamp`, so a caller compares that with today's `stamp(here, mode)` to know whether it is still the answer."""
    path = cache_file(here, mode)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if payload.get("cache_version") != CACHE_VERSION:
        return None
    return _from_json(payload, stamp_=payload.get("stamp", ""))


def is_current(found, here=None, mode="rs"):
    """Whether a read of document `mode` still answers for the project as it stands now."""
    return bool(found) and bool(found.stamp) and found.stamp == stamp(here, mode)
