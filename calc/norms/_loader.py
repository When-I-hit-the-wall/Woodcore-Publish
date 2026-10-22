"""How every reader of calc/norms/ opens its files (spec docs/requirements/active/2026-10-19-base-saine-nettoyage.md, G3).

Ten modules read the norms' JSON, and each wrote the same few lines its own way: open the file, parse it, say that it is missing or not JSON, check its edition -- with ten wordings of one refusal. They read through here now. Each module keeps its own `_cache`, its own `_read` and its own checks, which are what it knows about its norm; what is common -- reading a file and refusing it by its name -- is written once.

A refusal is a `validation.ValidationError` naming the file, `calc/norms/<name>.json: …`, as CLAUDE.md asks of a defect in a file Woodcore reads: the export stops on it, naming the file and the field.
"""

import json
from pathlib import Path

import validation


def fail(name, what):
    """The refusal of one norm file: `calc/norms/<name>.json: <what>`. `name` is the file's stem, or its name with `.json`."""
    stem = name[:-len(".json")] if name.endswith(".json") else name
    raise validation.ValidationError("calc/norms/%s.json: %s" % (stem, what))


def load(path):
    """The JSON of one norm file (`path`), parsed -- or the refusal naming it: missing, not readable, or not JSON."""
    path = Path(path)
    try:
        with path.open(encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        fail(path.name, "not found at %s -- the values of the norms live in calc/norms/" % path)
    except json.JSONDecodeError as exc:
        fail(path.name, "is not valid JSON: %s" % exc)
    except OSError as exc:
        fail(path.name, "cannot be read -- %s" % exc)


def edition(name, data, expected=None):
    """A norm file names the edition it was read off: the one `expected` where the module reads one edition, any one otherwise."""
    if expected is None:
        if not data.get("edition"):
            fail(name, "no 'edition'")
    elif data.get("edition") != expected:
        fail(name, "edition is %r -- expected %r" % (data.get("edition"), expected))

