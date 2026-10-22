"""What runs inside the child process when a script of the project is run (calc/domains/script.py, v0.100).

It is reached only as `woodcore-cli run-script`, never imported by the window or by the export: the whole point of it is to be in a process of its own, so that a script which loops for ever, exhausts the memory or segfaults takes nothing with it.

**What the script is given**, and nothing else:

* `result(name, value, unit="", symbol=None, label=None, descr=None, norm=None, norm_ref="")` -- declares a value the report may read. This is the one thing a script writes.
* `value(domain, instance, name)` -- a number out of the project's export: a load, a connector's resistance, a connection's polar moment. What `var-of` reads in Typst, read here instead.
* `PROJECT`, `DATA` -- the project's folder and its export, as `pathlib.Path`, to read whatever else it needs.
* `numpy` where it is installed, imported by the script itself (`import numpy as np`); it is pinned and frozen into the installed program for exactly this (requirements.txt, v0.100). ⚠️ SciPy deliberately is **not**: the engineer chose numpy alone, so a non-linear equation is solved with `numpy.linalg` or by Newton or bisection written out -- twenty lines, and the examples of the tab show them.

**The write guard.** `builtins.open` and `io.open` are replaced by one that refuses a write mode. They are the same function underneath, so this also covers `Path.open`, `Path.write_text` and `Path.write_bytes`, which is nearly every way a script writes a file by accident. ⚠️ It is **a guard and not a sandbox**: `os.open`, `os.remove`, `shutil`, `subprocess` and a C extension all get round it, and a script that means to write can. It is here to catch the accident -- a stray `open(..., "w")` inside the project -- and it is documented as that rather than promised as safety.
"""

import builtins
import io
import json
import sys
import traceback
from pathlib import Path

import project

# What a repr is cut to in the inspector: enough to recognise a value, never enough to fill the pane with an array of ten thousand.
REPR_MAX = 300
# The names the harness itself puts into the script's globals, which are therefore not the engineer's variables and are left out of the inspector.
INJECTED = ("result", "value", "PROJECT", "DATA", "__builtins__", "__name__", "__file__", "__doc__")


class Refused(Exception):
    """A script that tried to write. Raised by the guard, caught like any other exception the script raises."""


def _guarded_open(real):
    """`open`, refusing a mode that writes -- and saying which file it refused, which is what makes it a message and not a mystery."""
    def opener(file, mode="r", *args, **kwargs):
        if any(ch in str(mode) for ch in "wxa+"):
            raise Refused(
                f"a script reads the project and writes nothing but the results it declares: "
                f"opening {file!s} for writing ({mode!r}) is refused -- call result(\"name\", value, \"unit\") instead"
            )
        return real(file, mode, *args, **kwargs)
    return opener


def _load(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _reader(here, calculations_file=None):
    """`value(domain, instance, name)`: a var of the export, looked up where `find-calculation` looks in Typst -- the calculation domains first, then the connectors and the connections. The calculation domains are `calculations_file`'s where the export names one -- the calculations it is making, in memory, and not the last ones on the disk, whose names may be another version's (spec 2026-10-21-restes-issue-69, ARCH-RISK-804) --, data/calculations.json's otherwise."""
    data = here.data_dir

    def value(domain, instance, name):
        value.reads.append([domain, instance, name])   # what the script read, for the graph of dependencies (spec 2026-10-21-graphe-dependances, ARCH-RISK-1105)
        doms = _load(calculations_file or data / "calculations.json").get("domains", {})
        if domain in doms:
            insts = doms[domain].get("instances", {})
            if instance not in insts:
                raise KeyError(f"domain {domain!r} has no instance {instance!r} -- valid: {', '.join(sorted(insts))}")
            found = insts[instance].get("vars", {})
        elif domain in ("connector", "connection"):
            file = "connectors.json" if domain == "connector" else "connections.json"
            known = _load(data / file).get(domain + "s", {})
            if instance not in known:
                raise KeyError(f"no {domain} {instance!r} -- valid: {', '.join(sorted(known))}")
            found = known[instance].get("vars", {})
        else:
            raise KeyError(f"no calculation domain {domain!r} -- valid: "
                           f"{', '.join(sorted([*doms, 'connector', 'connection']))}")
        if name not in found:
            raise KeyError(f"{domain}/{instance} carries no {name!r} -- valid: {', '.join(sorted(found))}")
        return found[name]["value"]
    value.reads = []
    return value


def _inspected(name, held):
    """One line of the tab's inspector: what the variable is, and its value where it has one a pane can show."""
    kind = type(held).__name__
    try:
        shown = repr(held)
    except Exception:                                    # broad: a repr of the engineer's own object may raise anything
        shown = f"<{kind}: its repr raised>"
    if len(shown) > REPR_MAX:
        shown = shown[:REPR_MAX] + " …"
    out = {"name": name, "type": kind, "repr": shown, "value": None}
    if isinstance(held, bool) or held is None:
        out["value"] = held
    elif isinstance(held, (int, float)):
        out["value"] = held
    elif isinstance(held, str):
        out["value"] = held[:REPR_MAX]
    shape = getattr(held, "shape", None)               # a numpy array says how big it is, which is what one wants of it
    if shape is not None and not callable(shape) and tuple(shape):
        # a numpy *scalar* has shape (), and «float64()» reads as a call rather than as a size
        out["type"] = f"{kind}{tuple(shape)}"
    return out


def execute(path, project_file=None, results_only=False, calculations_file=None):
    """Runs the script at `path` and gives back its report: `{"reason", "results", "variables", "reads"}` -- `reads` what its value() calls read, [[domain, instance, name]] (spec 2026-10-21-graphe-dependances).

    `reason` is "" where it ran through. It never raises for anything the script did -- a syntax error, an exception, a refused write all come back as a reason, because the export must go on running the other scripts (the v0.33 rule).
    """
    path = Path(path)
    if project_file:
        project.use(project_file)
    here = project.current()
    results = []

    def result(name, value, unit="", symbol=None, label=None, descr=None, norm=None, norm_ref=""):
        """Declares a value the report may read with `#val(name, domain: ("script", "<id>"))`."""
        if not isinstance(name, str) or not name.strip():
            raise ValueError("result(): the first argument is the name the report reads the value by")
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            # a numpy scalar is neither, and is exactly what a solver gives back
            try:
                value = float(value)
            except (TypeError, ValueError):
                raise ValueError(f"result({name!r}): a result is a number, not {type(value).__name__}") from None
        if not isinstance(unit, str):
            raise ValueError(f"result({name!r}): the unit is a string -- \"\" where the value has none")
        # the line of the script's own call, which a result without a norm is cited by (spec 2026-10-20-indices-et-niveaux, REQ-002): the first frame up the stack that is the script's file -- result() may be called from a function of the script, or from a module it imports
        frame = sys._getframe(1)
        while frame is not None and frame.f_code.co_filename != str(path):
            frame = frame.f_back
        results.append({"name": name.strip(), "value": float(value), "unit": unit,
                        "symbol": symbol or name.strip(), "label": label or "", "descr": descr or "",
                        "norm": norm or "", "norm_ref": norm_ref or "", "line": frame.f_lineno if frame is not None else None})

    reader = _reader(here, calculations_file)
    scope = {
        "__name__": "__woodcore_script__",
        "__file__": str(path),
        "__doc__": None,
        "result": result,
        "value": reader,
        "PROJECT": here.root,
        "DATA": here.data_dir,
    }
    real_open = builtins.open
    builtins.open, io.open = _guarded_open(real_open), _guarded_open(real_open)
    reason = ""
    try:
        code = compile(real_open(path, encoding="utf-8").read(), str(path), "exec")
        exec(code, scope)                                # noqa: S102 -- running the engineer's own script is the point
    except SyntaxError as exc:
        reason = f"line {exc.lineno}: {exc.msg}"
        traceback.print_exc()
    except Refused as exc:
        reason = str(exc)
        traceback.print_exc()
    except BaseException as exc:                         # broad: SystemExit and KeyboardInterrupt included: the report says what ended it
        reason = f"{type(exc).__name__}: {exc}"
        traceback.print_exc()
    finally:
        builtins.open, io.open = real_open, real_open
    variables = [] if results_only else [
        _inspected(name, held) for name, held in scope.items()
        if name not in INJECTED and not name.startswith("_") and not callable(held)
        and type(held).__name__ != "module"
    ]
    return {"reason": reason, "results": results, "variables": variables, "reads": reader.reads}


def main(argv):
    """`woodcore-cli run-script <source> --report <file> [--project P] [--results-only] [--calculations F]`."""
    import argparse
    ap = argparse.ArgumentParser(prog="woodcore-cli run-script")
    ap.add_argument("source")
    ap.add_argument("--report", required=True)
    ap.add_argument("--project")
    ap.add_argument("--results-only", action="store_true")
    ap.add_argument("--calculations")
    args = ap.parse_args(argv)
    report = execute(args.source, args.project, results_only=args.results_only, calculations_file=args.calculations)
    Path(args.report).write_text(json.dumps(report, ensure_ascii=False, default=str), encoding="utf-8", newline="\n")
    return 0 if not report["reason"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
