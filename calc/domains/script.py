"""A script of the project: Python the engineer writes, run by Woodcore, whose named results the report reads (docs/domain/scripts.md §3.3sexdecies, v0.100).

The engineer asked for «un onglet dans woodcore, où le user peut écrire du code python et le run», to solve an equation or a system of them -- and, of the three ways a result could reach the report, chose the one that keeps it **traceable**: the script declares its results, they are exported into `data/scripts.json`, and the report reads one with `#val("x", domain: ("script", "<id>"))`. Nothing is copied by hand, and every value carries the source that produced it (`python:scripts/<id>.py`), which is section 2 rule 5 applied to a calculation the engineer wrote himself.

**One script is one file**: `Woodcore-Datei/scripts/<id>.py`, the id being the file name, as it is for every other thing Woodcore's window draws. Its identity is three `@` comment keys at the top -- `@name`, `@label`, `@group` -- which is the convention an RFEM comment already uses (section 3.3duodecies) and, like there, the sigil is `@` and never `#`, a `#` being Python's own comment marker. Everything else in the file is Python.

**What a script may do** is the engineer's own answer: it reads the project -- `DATA` and `PROJECT` are paths, `value()` reads a var of the export -- and writes nothing but the results it declares. ⚠️ That is a **guard against an accident and not a sandbox**: `open` is replaced in the child by one that refuses a write mode, which covers `open`, `io.open`, `Path.open`, `Path.write_text` and `Path.write_bytes` because all of them are the same function underneath -- and a script that reaches for `os.open` or `subprocess` gets round it. It is said here rather than promised, because a promise of safety nobody can keep is worse than a guard somebody understands.

**It runs in a process of its own**, and never in the window's: a script that loops for ever, exhausts the memory or segfaults must not take Woodcore with it, which is the same reason the export runs in its own process. The child is `woodcore-cli run-script`, so an installed Woodcore -- which carries no `python.exe` to spawn -- relaunches itself exactly as «Import données» does (project.cli_command).

**Every export runs every script**, as every other domain is recalculated at every export: that is what keeps the number in the report the number the current data gives (section 2 rule 1). A script that fails, or that takes longer than `TIMEOUT`, is a **warning and never a stop** -- its record carries `calculated: false` and the reason, the report refuses to print what it names, and the rest of the export goes through (the v0.33 rule).
"""

import json
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import engine
import proc
import project
import validation

DOMAIN = "script"
SOURCES = "scripts"          # the folder of the project's sources this domain reads (project.SOURCE_FOLDERS)
EXPORT_SCHEMA_VERSION = "1.1"   # 1.1 a result carries the line of its call, which cites it where it names no norm (spec 2026-10-20-indices-et-niveaux, REQ-002); 1.0 is still read   # data/scripts.json; named as every other domain names its export's (v0.120, C5: SCHEMA_VERSION until then)
EXPORT_FILE = "scripts.json"   # the file of data/ this domain is exported to, named once (write() and calc/variable_sources.py)
SUFFIX = ".py"
# How long a script may run before it is given up on, in seconds. A script of this project solves a system of a few dozen equations, which is milliseconds; a minute is room for a bad loop to be caught rather than waited out.
TIMEOUT = 60
# The identity a script carries, in `@key value` comment lines at its top -- `@name`, `@label` (its description, the word every other source of Woodcore uses for one) and `@group` (the folder of the tab's left pane). The sigil is `@`, never `#`, which is Python's own comment marker.
KEYS = ("name", "label", "group")
_KEY = re.compile(r"^[ \t]*#[ \t]*@[ \t]*(" + "|".join(KEYS) + r")[ \t]*[:=]?[ \t]*(.*?)[ \t]*$", re.M)
# What a file may be called: letters, digits and `_ . + -`, the rule every other id of this project follows (connector.ID_PATTERN), so that an id is a file name and a Typst string alike.
ID_PATTERN = re.compile(r"^[A-Za-z0-9_.+-]+$")


class ScriptError(validation.ValidationError):
    """A script source that cannot be read: its name, or its identity. A defect in the data, reported like any other -- the export prints it and exits 1."""


def sources_dir(here=None):
    """The folder of the project's scripts, whether or not it exists yet: `Scripts/` at the top of a project laid out by folders, beside the `.typ` that prints each (issue #64, D-12), its sources' `scripts/` before."""
    here = here or project.current()
    return here.domain_dir(DOMAIN) if here.has_folders else here.sources_dir / SOURCES


def source_paths(here=None):
    """Every script of the project, in file-name order. `archives/` is not reached, as no other source's glob reaches it (source_archive.py)."""
    folder = sources_dir(here)
    return sorted((p for p in folder.glob("*" + SUFFIX) if p.is_file()), key=lambda p: p.name.lower()) if folder.is_dir() else []


def read_source(path):
    """One script read: its id (the file name), its `@name`, `@label` and `@group`, and its code. A key the file does not carry comes back as "" -- an identity is the engineer's to fill in, not something to stop an export over."""
    path = Path(path)
    return read_source_text(path.read_text(encoding="utf-8"), path.stem)


def read_source_text(code, script_id=""):
    """The identity `code` states, without a file: what Woodcore's Python tab shows while the engineer is still typing, so that the `@` keys in the buffer and the ones a save will write are never two different things."""
    found = {key: "" for key in KEYS}
    for key, value in _KEY.findall(code):
        if not found[key]:
            found[key] = value.strip()
    return {"id": script_id, "code": code, **found}


def check_source(source, path=None):
    """Refuses a script whose id is not one (ScriptError). What is *in* the code is not checked here at all: Python says what is wrong with Python, and it says it when the script is run -- where the reason reaches the record and the window rather than stopping every other script's export."""
    where = f"{Path(path).name}: " if path else ""
    if not ID_PATTERN.match(source["id"]):
        raise ScriptError(f"{where}a script's name is its id, so it is kept to letters, digits and _ . + - -- {source['id']!r} is not")
    return source


# --- running one ---------------------------------------------------------------------

def run(path, timeout=TIMEOUT, results_only=False, calculations=None):
    """Runs the script at `path` in a process of its own and gives back what it did:

        {"ok": bool, "reason": str, "seconds": float, "results": [...], "variables": [...], "output": str}

    `results` is what the script declared with `result()`, in the order it declared them; `variables` is what its globals held when it ended, for the tab's inspector (`results_only` leaves them out, which is what the export asks for -- the report has no use for a local). `output` is everything the script printed, stdout and stderr together, which is what the tab's terminal shows.

    ⚠️ It never raises for anything the *script* did: a syntax error, an exception, a timeout and a child that died all come back as `ok: False` with the reason, because one script must not stop the export of the others (the v0.33 rule).
    """
    path = Path(path)
    here = project.current()
    program, arguments = project.cli_command(["run-script", str(path), "--project", str(here.file)])
    with tempfile.TemporaryDirectory(prefix="woodcore-script-") as tmp:
        report_file = Path(tmp) / "report.json"
        arguments += ["--report", str(report_file)]
        if results_only:
            arguments.append("--results-only")
        if calculations is not None:
            # the calculations of the export being made, which a script's value() reads in place of the last ones on the disk (ARCH-RISK-804)
            held = Path(tmp) / "calculations.json"
            engine.write_json(held, calculations)
            arguments += ["--calculations", str(held)]
        started = time.monotonic()
        try:
            done = proc.run([program, *arguments], capture_output=True, text=True, encoding="utf-8",
                                  errors="replace", timeout=timeout, cwd=tmp)
        except subprocess.TimeoutExpired as expired:
            output = (expired.stdout or "") + (expired.stderr or "")
            return {"ok": False, "reason": f"the script was still running after {timeout} s and was given up on",
                    "seconds": float(timeout), "results": [], "variables": [], "output": output if isinstance(output, str) else ""}
        seconds = round(time.monotonic() - started, 3)
        output = done.stdout + done.stderr
        if report_file.is_file():
            try:
                report = json.loads(report_file.read_text(encoding="utf-8"))
            except ValueError as exc:
                return {"ok": False, "reason": f"the run wrote a report that cannot be read ({exc})",
                        "seconds": seconds, "results": [], "variables": [], "output": output}
            report.setdefault("results", [])
            report.setdefault("variables", [])
            report["seconds"], report["output"] = seconds, output
            report["ok"] = not report.get("reason")
            return report
        return {"ok": False, "seconds": seconds, "results": [], "variables": [], "output": output,
                "reason": f"the run wrote no report and ended with {done.returncode}"}


# --- the export ----------------------------------------------------------------------

def record(source, report, path=None):
    """One script's entry of `data/scripts.json`: its identity, whether it ran, and the `{vars, steps, checks, results}` shape every calculation of this engine has (section 2 rule 2), so that `show-calc`, `val` and `find` read it like any other.

    A result's `source` names the file that produced it -- `python:scripts/<id>.py` -- which is the provenance convention `domains/dead_load.py` already follows.
    """
    # ⚠️ How long the run took is deliberately **not** exported, though `run` reports it and the tab's status line shows it:
    # a wall-clock duration differs at every export, and `data/` must stay unchanged to the byte when nothing else changed
    # (docs/conventions/build-and-release.md §12, which is why `data/project.json` carries no date either). Exporting it broke
    # `test_export.test_the_export_is_reproducible` for any project carrying a script.
    where = f"{SOURCES}/{Path(path).name}" if path else f"{SOURCES}/{source['id']}{SUFFIX}"
    vars_out, results = {}, []
    for item in report.get("results", []):
        name = item["name"]
        vars_out[name] = {
            "value": item["value"],
            "unit": item.get("unit", ""),
            "symbol": item.get("symbol") or name,
            "label": item.get("label") or "",
            "source": f"python:{where}",   # no level: a result is printed from lib/line-levels.json's `*` of the script, 1 (spec 2026-10-20-indices-et-niveaux, UI-002)
        }
        # `norm` and `norm_ref` are always written, "" where the script cites nothing: `get-norm(v)` is a plain field access in Typst, and an empty citation prints nothing (norm-text).
        vars_out[name]["norm"] = item.get("norm", "") or ""
        vars_out[name]["norm_ref"] = item.get("norm_ref", "") or ""
        # where it names none, the line of its result() call cites it -- «script <id>.py, l. 12» in the right-hand column (REQ-002, Q-005): never written into `norm`, which `_check_citation` and the bibliography read as a document
        if item.get("line") is not None and not vars_out[name]["norm"]:
            vars_out[name]["line"] = item["line"]
        if item.get("descr"):
            vars_out[name]["description"] = item["descr"]
        results.append(name)
    return {
        "id": source["id"],
        "name": source.get("name") or source["id"],
        "label": source.get("label", ""),
        "group": source.get("group", ""),
        "calculated": bool(report.get("ok")) and bool(results),
        "reason": report.get("reason", "") or ("" if results else "the script declared no result -- call result(\"name\", value, \"unit\") for every value the report is to read"),
        "vars": vars_out,
        "steps": [],
        "checks": [],
        "results": results,
    }


def prepare(timeout=TIMEOUT, calculations=None, reads=None):
    """Reads and runs every script of the project. Returns (records, notes) -- the notes being engine.Note, the window writing each in its own language (section 4bis). `calculations`, the export's own being made, is what a script's value() reads (`run`); `reads`, a dict, is given what each script read, {id: [[domain, instance, name]]} -- the graph of dependencies' (spec 2026-10-21-graphe-dependances, ARCH-RISK-1105), never written into data/scripts.json."""
    records, notes = {}, []
    for path in source_paths():
        source = check_source(read_source(path), path)
        if source["id"] in records:
            raise ScriptError(f"two scripts are called {source['id']!r} -- a script's name is its id")
        report = run(path, timeout=timeout, results_only=True, calculations=calculations)
        if reads is not None:
            reads[source["id"]] = report.get("reads") or []
        entry = record(source, report, path)
        records[source["id"]] = entry
        if not entry["calculated"]:
            notes.append(engine.Note("script_failed", f"The script {source['id']} produced nothing: {entry['reason']}",
                                     script=source["id"], reason=entry["reason"]))
    return records, notes


def document(records):
    """The whole of `data/scripts.json`, for a caller that validates it without writing it -- `woodcore-cli check`, which reads, builds and validates everything and writes nothing."""
    return {"schema_version": EXPORT_SCHEMA_VERSION, "scripts": records}


def write(records):
    """Writes `data/scripts.json`, validated against its contract, and returns the file."""
    data = document(records)
    validation.validate_structure(data, "scripts")
    validation.validate_scripts_business(data)
    out = project.current().data_dir / EXPORT_FILE
    out.parent.mkdir(parents=True, exist_ok=True)
    engine.write_json(out, data)
    return out


def export(timeout=TIMEOUT):
    """Runs every script and writes `data/scripts.json`. Returns (file, notes) -- what export_all.py calls, and what Woodcore's Python tab calls when a script is saved, so that the report sees its results without the load workbooks being read again (the connectors' own arrangement)."""
    records, notes = prepare(timeout=timeout)
    return write(records), notes
