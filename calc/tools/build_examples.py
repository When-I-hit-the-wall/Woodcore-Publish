"""Writes the frozen worked examples of every Typst command, and renders them once (docs/typst/command-docs.md §10sexies).

    python calc/tools/build_examples.py            write the MWEs and render them
    python calc/tools/build_examples.py --freeze   also re-freeze the data the examples are rendered against, from the example project

**What is frozen is the example project, never the project that happens to be open (v0.86).** `tests/projet-exemple/` is a real project anonymised -- blank pages for the architect's plans, no workbook, no client -- and it is what the test suite works on. The examples are the program's documentation and are committed into the program's repository, which is shared with developers: freezing the engineer's own project would have copied his architect's plans and his client's name into it, against the v0.82 rule, and would have made the documentation name whatever ids that project had that week. `--project` still takes another one, deliberately.

**Why the examples are frozen.** An example like `#show-calc("snow-load", "SL")` reads `data/`, so until v0.65 what the documentation showed followed the project: renaming a sheet changed the picture, and deleting an id broke the example. A reference that moves when the thing it documents moves is not a reference. So the examples are rendered against a **snapshot** of `data/` kept in this folder, and their pages are rendered once and committed.

**Why the tree looks like this.** The engine finds its data by relative path -- `lib/calc-engine.typ` reads `json("../data/…")` and `lib/i18n.typ` reads `json("../calc/i18n/strings.json")` -- so *where the engine file sits* decides which data a command sees. The only way to point it at the snapshot is to put a copy of the engine beside the snapshot:

    examples/
        data/                   the snapshot, versioned; refreshed only by --freeze
        calc/i18n/strings.json  likewise, because i18n.typ reads it
        calc/norms/*.json       likewise, because distance.typ reads them (v0.87)
        lib/*.typ               a copy of the LIVE lib/, refreshed on every run, NOT versioned
        commands.typ            imports that copy, likewise
        <command>-<n>.typ       one MWE per example, written from its /// block, versioned
        out/<command>-<n>.png   its page, rendered once, versioned

⚠️ `lib/` here is a copy and is deliberately not versioned. It is refreshed from the real `lib/` at every run so an example always exercises the **current** engine -- which is the whole point of the compile check in tests/test_commands.py. A versioned copy would quietly become a second engine, and the examples would stop testing anything.

⚠️ `--freeze` is a separate flag and `export_all.py` never passes it. Freezing has to be an act somebody performs, or the snapshot would follow the project on every export and none of this would hold.

The MWEs are **generated and committed, never hand-edited**: the example is written once, in the `///` block of the command it documents (section 2 rule 14), and this script writes it out. That is the arrangement `docs/typst-reference.xlsx` already uses, and it is what keeps one text rather than two.
"""

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # calc/, for project.py

import build_reference as ref  # noqa: E402
import command_docs as docs  # noqa: E402  -- which levels an example is rendered at (example_levels)
import command_preview as preview  # noqa: E402
import project  # noqa: E402  -- the project whose export --freeze takes, and against which dangling() checks the ids (calc/project.py)

ROOT = Path(__file__).resolve().parent.parent.parent  # 000-Python/, the program: its lib/ is copied beside the snapshot
EXAMPLES = ROOT / "examples"
# The project the snapshot is taken from, and the one an example's ids are checked against (v0.86): the program's own anonymised example, which the tests work on too. Not the project that is open -- see the header.
EXAMPLE_PROJECT = ROOT / "tests" / "projet-exemple" / "Exemple.woodcore"
OUT = EXAMPLES / "out"
MANIFEST = OUT / "index.json"

# The language the pages are rendered in. One, not three: three would be ~37 MB of PNG for a gain the documentation does not need -- it is written in English, and the labels the data carries are German whatever the window is set to (docs/typst/language.md §4bis). An example that wants another language calls `set-report-language` itself, which is better than the window doing it invisibly.
LANG = "de"


def imports_for(from_dir):
    """Where a .typ written in `from_dir` finds the report's styling and the frozen engine.

    Derived from where the file actually goes, never written down. Typst resolves an import against the importing file, so a literal `../..` is correct only at the depth it was written for -- and that has already cost this project once, when Woodcore's scratch directory gained a per-process level and every import in it silently stopped resolving. Two callers sit at different depths (examples/ and Woodcore's scratch), and a third would be free to sit at a third.
    """
    from_dir = Path(from_dir).resolve()
    config = os.path.relpath(EXAMPLES / "config.typ", from_dir)
    commands = os.path.relpath(EXAMPLES / "commands.typ", from_dir)
    return Path(config).as_posix(), Path(commands).as_posix()


COMMANDS_TYP = '''// The engine, as the frozen examples see it (docs/typst/command-docs.md §10sexies).
// Generated by calc/tools/build_examples.py beside a copy of lib/ -- do not edit, do not commit.
#import "lib/calc-engine.typ": *
#import "lib/formula.typ": *
'''

SAFE_NAME = re.compile(r"[^A-Za-z0-9_.+-]")


def stem(command, index, level):
    """The file name one example is written under: `show-calc-2`, and `show-calc-2-L3` for another level."""
    name = SAFE_NAME.sub("_", command)
    base = f"{name}-{index + 1}"
    return base if level == preview.DEFAULT_LEVEL else f"{base}-L{level}"


def source_hash(code, level):
    """What says a committed page still matches the fence it was rendered from."""
    digest = hashlib.sha256()
    for part in (code, str(level), LANG):
        digest.update(part.encode("utf-8"))
        digest.update(b"\0")
    return digest.hexdigest()[:16]


def example_data_dir():
    """The export of the example project the snapshot is taken from (EXAMPLE_PROJECT)."""
    return project.Project.load(EXAMPLE_PROJECT).data_dir


def freeze(root=ROOT, source_project=None):
    """Copies an export, the program's glossary and the norm tables lib/distance.typ reads into the fixture. Deliberate, never automatic.

    The export is the example project's unless `source_project` names another (a Project): the snapshot is committed into the program's repository, so it must never be taken from a project carrying a client's data or an architect's plans (header, v0.86).
    """
    source_data = source_project.data_dir if source_project is not None else example_data_dir()
    # The engine's own data files -- the glossary, and since v0.87 the norm tables lib/distance.typ reads as `../calc/norms/` -- are frozen with the export, the way a project receives them beside its own (project.ENGINE_FILES).
    frozen = [(source_data, EXAMPLES / "data")]
    frozen += [(root / name, EXAMPLES / name) for name in project.ENGINE_FILES if name.startswith("calc/")]
    for source, target in frozen:
        if not source.exists():
            raise SystemExit(f"build_examples: {source} is not there -- run calc/export_all.py first")
        target.parent.mkdir(parents=True, exist_ok=True)
        if source.is_dir():
            shutil.rmtree(target, ignore_errors=True)
            shutil.copytree(source, target)
        else:
            shutil.copy2(source, target)
    # The figures the export names from the Typst root since issue #64 -- `/Plans/Position-plan/Exports/Figures/Pavillon.svg`, a plan's PDF beside it, a static model's drawing -- copied to the same path under examples/, which is the examples' Typst root: until v0.120 the snapshot predated issue #64 and named them `plans/…` inside data/, and a freeze taken since then compiled no plan (spec 2026-10-20-indices-et-niveaux, UI-004).
    here = source_project if source_project is not None else project.Project.load(EXAMPLE_PROJECT)
    rooted = 0
    for name in sorted(_rooted_files(EXAMPLES / "data")):
        source = Path(here.typst_root) / name.lstrip("/")
        if source.is_file():
            target = EXAMPLES / name.lstrip("/")
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            rooted += 1
    print(f"build_examples: froze {source_data}, strings.json, the norm tables and {rooted} figures named from the root into {EXAMPLES.name}/")


def _rooted_files(data_dir):
    """Every string of the JSON files of `data_dir` that names a file from the Typst root -- `/Plans/…/x.svg` -- once."""
    found = set()

    def walk(x):
        if isinstance(x, dict):
            for v in x.values():
                walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)
        elif isinstance(x, str) and x.startswith("/") and "." in x.rsplit("/", 1)[-1] and "\n" not in x:
            found.add(x)
    for path in Path(data_dir).rglob("*.json"):
        walk(json.loads(path.read_text(encoding="utf-8")))
    return found


def refresh_engine(root=ROOT):
    """Puts a copy of the live engine beside the frozen data, so an example runs against today's code."""
    lib = EXAMPLES / "lib"
    lib.mkdir(parents=True, exist_ok=True)
    for name in ref.LIB_FILES:
        shutil.copy2(root / "lib" / name, lib / name)
    # the engine's data beside its .typ files: lib/units.json, which formula.typ reads (v0.117)
    for name in project.ENGINE_FILES:
        if name.startswith("lib/") and name.endswith(".json"):
            shutil.copy2(root / name, lib / name[len("lib/"):])
    # the pictures lib/ prints -- the BFH logo of a sheet's title block (lib/sheet.typ, v0.114) -- beside the files that name them
    shutil.copytree(root / "lib" / "assets", lib / "assets", dirs_exist_ok=True)
    (EXAMPLES / "commands.typ").write_text(COMMANDS_TYP, encoding="utf-8", newline="\n")
    # where a project's own files import the engine from, `/000-Typst-Config/commands.typ`: the domains the export wrote out, which an example includes by domain-file(kind, id) (spec 2026-10-21-commandes-typst-refonte, ARCH-008), read the same engine
    config = EXAMPLES / project.CONFIG_FOLDER
    config.mkdir(exist_ok=True)
    (config / "commands.typ").write_text('// Generated by calc/tools/build_examples.py -- do not edit, do not commit.\n#import "/commands.typ": *\n', encoding="utf-8", newline="\n")


def examples_of(root=ROOT):
    """Every renderable example of every public command, with the levels it is rendered at.

    Yields (command, index, level, code). A command taking a `level:` is rendered at all three, which is what the tab's 1 / 2 / 3 selector shows; the others once; a ```typ-dry fence, which is shown and never compiled, not at all. Which is command_docs.example_levels' to say, the tab and the website reading the same answer.
    """
    for record in ref.lib_bindings(root):
        if record["category"] == ref.INTERNAL:
            continue
        block = ref.parse_doc_block(record["doc_lines"])
        for index, example in enumerate(block["examples"]):
            for level in docs.example_levels(record, block, example):
                yield record["name"], index, level, example["code"]


def write_sources(root=ROOT):
    """Writes one .typ per example and returns the entries the manifest will carry."""
    entries = []
    for command, index, level, code in examples_of(root):
        name = stem(command, index, level)
        path = EXAMPLES / f"{name}.typ"
        config, commands = imports_for(EXAMPLES)
        path.write_text(
            preview.document(code, level, LANG, config=config, commands=commands),
            encoding="utf-8", newline="\n",
        )
        entries.append({
            "command": command, "index": index, "level": level,
            "stem": name, "hash": source_hash(code, level),
        })
    return entries


def render(entries):
    """Renders every MWE to out/<stem>.png. Returns the ones that would not compile."""
    OUT.mkdir(parents=True, exist_ok=True)
    failures = []
    for entry in entries:
        source = EXAMPLES / f"{entry['stem']}.typ"
        png = OUT / f"{entry['stem']}.png"
        result = preview.run_typst(source, png)
        if result is not None:
            failures.append((entry["stem"], result))
            png.unlink(missing_ok=True)
    return failures


# The two .typ of examples/ that are not examples: the engine's import, generated, and the documentation's own styling, versioned (v0.81).
KEPT = {"commands.typ", "config.typ"}


def sweep(entries):
    """Removes a .typ or a .png left behind by an example that no longer exists."""
    keep_typ = {f"{e['stem']}.typ" for e in entries}
    keep_png = {f"{e['stem']}.png" for e in entries}
    for path in EXAMPLES.glob("*.typ"):
        if path.name not in keep_typ and path.name not in KEPT:
            path.unlink()
    for path in OUT.glob("*.png"):
        if path.name not in keep_png:
            path.unlink()


def ids_by_kind(data_dir):
    """Every id an example can name, as one export spells them, by kind: {kind: set of ids}.

    Domains and their instances, the categories of the norm table, the positions, the connections, the connectors, the plans, the static models and the schemas -- the strings a `show-*` call is addressed by. Kept apart because two kinds may share an id -- a schema `SD_02` and a connector `SD_02` -- and a connector the project dropped must not pass for present because a schema of that name remains (periodic audit 260916).
    """
    data = Path(data_dir)

    def read(name):
        try:
            return json.loads((data / name).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}

    found = {"calculations": set(), "positions": set()}
    for domain, record in read("calculations.json").get("domains", {}).items():
        found["calculations"].add(domain)
        found["calculations"].update(record.get("instances", {}))
    found["positions"].update(read("positions-index.json").get("positions", ()))
    for name, key in (("connections.json", "connections"), ("connectors.json", "connectors"),
                      ("plans.json", "plans"), ("statics.json", "models"), ("schemas.json", "schemas")):
        found[key] = set(read(name).get(key, {}))
    # the annexes' excerpts and sources (v0.115), each a kind of its own
    annexes = read("annexes.json")
    found["excerpts"] = set(annexes.get("excerpts", {}))
    found["annexes"] = set(annexes.get("sources", {}))
    try:
        found["positions"].update(p.stem for p in (data / "positions").glob("*.json"))
    except OSError:
        pass
    return found


def ids_in(data_dir):
    """Every id an example can name, whatever its kind (ids_by_kind)."""
    return set().union(*ids_by_kind(data_dir).values())


def dangling(data_dir=None):
    """Examples naming something the **example project** no longer has. Returns [(stem, id), …], sorted.

    Checked against the project the snapshot is taken from (EXAMPLE_PROJECT) unless `data_dir` names another export. Until v0.86 it was checked against whatever project was open, which since v0.81 is any project at all: the engineer's renamed its connector and every example citing the old name was reported, while the snapshot, the tests and the pages all still agreed.

    ⚠️ This is deliberately not "is the snapshot stale". The snapshot is *meant* to drift from the project — that is what freezing is for — so a check comparing the two would fire when nothing is wrong, which is worse than no check at all. What actually hurts is narrower: an example citing an id the project has dropped. The reader then reads a page built on something that is gone, and the two calls to copy beside it name something else.

    Found the hard way in v0.65: a consolidation of the workbooks removed eight instances, and only the two that a fence cited were a problem.
    """
    snapshot, current = ids_by_kind(EXAMPLES / "data"), ids_by_kind(data_dir or example_data_dir())
    gone = set().union(*(ids - current.get(kind, set()) for kind, ids in snapshot.items()))
    if not gone:
        return []
    hits = []
    for path in sorted(EXAMPLES.glob("*.typ")):
        if path.name == "commands.typ":
            continue
        text = path.read_text(encoding="utf-8")
        hits += [(path.stem, name) for name in sorted(gone) if f'"{name}"' in text]
    return hits


def load_manifest():
    """What was generated last time, or an empty record."""
    try:
        return json.loads(MANIFEST.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"schema_version": "1.0", "lang": LANG, "examples": []}


def index():
    """The manifest keyed by (command, example index, level), for a reader looking one page up."""
    return {(e["command"], e["index"], e["level"]): e for e in load_manifest().get("examples", ())}


def page(command, example_index, level, code, manifest=None):
    """The committed page for one example, and whether it can be trusted.

    Gives (path, state): **fresh** where the page is there and was rendered from this very fence, **stale** where the fence has been edited since, **missing** where it was never rendered. Woodcore shows a fresh page at once and says so for the other two rather than recompiling behind the reader's back -- a committed page silently replaced is a committed page nobody notices is out of date.
    """
    manifest = index() if manifest is None else manifest
    entry = manifest.get((command, example_index, level))
    if entry is None:
        return None, "missing"
    png = OUT / f"{entry['stem']}.png"
    if not png.exists():
        return None, "missing"
    return png, ("fresh" if entry.get("hash") == source_hash(code, level) else "stale")


def build(root=ROOT, do_freeze=False, source_project=None):
    if do_freeze:
        freeze(root, source_project)
    if not (EXAMPLES / "data").exists():
        raise SystemExit(
            "build_examples: no frozen data in examples/ -- run once with --freeze to take a snapshot"
        )
    refresh_engine(root)
    entries = write_sources(root)
    failures = render(entries)
    sweep(entries)
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(
        json.dumps({"schema_version": "1.0", "lang": LANG, "examples": entries}, indent=1, ensure_ascii=False) + "\n",
        encoding="utf-8", newline="\n",
    )
    for name, message in failures:
        first = [line for line in message.splitlines() if line.strip()][:2]
        print(f"build_examples: {name} does not compile -- {' / '.join(first)}")
    for name, missing in dangling(source_project.data_dir if source_project is not None else None):
        print(f"build_examples: WARNING {name} names {missing!r}, which the example project no longer has "
              f"-- repoint the /// fence, or re-freeze if the snapshot is meant to move")
    total = sum((OUT / f"{e['stem']}.png").stat().st_size for e in entries
                if (OUT / f"{e['stem']}.png").exists())
    print(f"build_examples: {len(entries)} example(s), "
          f"{len(entries) - len(failures)} rendered ({total // 1024} KB) in {OUT.relative_to(ROOT)}")
    return failures


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--freeze", action="store_true",
                        help="re-copy data/ and the glossary into examples/ before building")
    parser.add_argument("--project", default=None,
                        help="the .woodcore file whose export --freeze takes; the example project (tests/projet-exemple) when left out")
    args = parser.parse_args()
    source = project.Project.load(args.project) if args.project else None
    if not preview.have_typst():
        raise SystemExit("build_examples: typst is not on the path")
    raise SystemExit(1 if build(do_freeze=args.freeze, source_project=source) else 0)


if __name__ == "__main__":
    main()
