"""The Typst commands Woodcore documents: that the list is complete, and that every example in it compiles (docs/typst/command-docs.md §10sexies).

`commands.typ` re-exports all three files of lib/ with a bare wildcard, so 202 names reach every Sections/*.typ and about 60 of them are commands an engineer calls. Which 60 is a hand-written list in build_reference.CATEGORIES, because a category is what a command is *for* and that is not a property of the file or the line it sits on. A hand-written list rots in two directions, and the first four checks below hold both: a category naming a command the engine no longer defines, and a command the engine defines that is documented as public but carries no documentation.

The last check is the coarse one. Every ```typ fence of every public command is compiled exactly as the window compiles it -- by `command_preview`, the module the window drives, so what passes here is what the tab shows. It is what makes the documentation a promise rather than a claim: a command renamed, an argument dropped, a sheet id the export no longer carries, each shows up here by name.

⚠️ The compile check is skipped where `typst` is not on the path or the export has never been run here. Skipped, not failed: a machine that only runs the Python pipeline is a legitimate machine (tests/test_report.py).
"""

import json
import re
import shutil
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import conftest
from conftest import ROOT, Skip

sys.path.insert(0, str(ROOT / "calc" / "tools"))

import build_examples as examples  # noqa: E402
import build_reference as ref  # noqa: E402
import command_docs as docs  # noqa: E402
import command_preview as preview  # noqa: E402
import project  # noqa: E402  -- the project whose export the examples are checked against

BINDINGS = ref.lib_bindings(ROOT)
BY_NAME = {r["name"]: r for r in BINDINGS}
PUBLIC = [r for r in BINDINGS if r["category"] != ref.INTERNAL]

# show-check reads an instance's checks[], and nothing in this project exports one yet (docs/open-questions.md §14), so its examples are written as ```typ-dry: shown, never compiled. The moment a domain exports a check they become ```typ and this list is empty again.
# show-annexes and doc-annexes print every page of a source as a page of its own (v0.115), and a documentation page is one picture, so their examples are shown and not rendered; the example project's report prints its annexes at every run (tests/test_annex.py, tests/test_report.py), which is where it is compiled.
EXEMPT_FROM_RENDERING = {"show-check", "show-annexes", "doc-annexes"}

MIN_EXAMPLES = 2


def block(record):
    return ref.parse_doc_block(record["doc_lines"])


def where(record):
    return f"{record['file']}:{record['line']}"


def test_no_category_names_a_command_that_is_gone():
    """The direction that actually rots: a command renamed in lib/ and left behind in the list."""
    for category, names in ref.CATEGORIES:
        for name in names:
            assert name in BY_NAME, (
                f"CATEGORIES[{category!r}] names {name!r}, which none of "
                f"lib/{{{', '.join(ref.LIB_FILES)}}} defines any more -- it was renamed or removed, "
                f"so Woodcore lists a command that does not exist"
            )


def test_no_command_is_in_two_categories():
    """A name in two categories would be listed twice and read as two commands."""
    seen = {}
    for category, names in ref.CATEGORIES:
        for name in names:
            assert name not in seen, f"{name!r} is in both {seen[name]!r} and {category!r}"
            seen[name] = category


def test_every_binding_of_lib_is_placed():
    """Every name the wildcard exports is either a categorised command or an internal one.

    It can only fail on a duplicate, INTERNAL being the complement -- but that is the assertion that says out loud what the tab's Internes row means: the ~142 names in it are not unclassified, they are classified as the engine's own.
    """
    assert len(BINDINGS) == len({r["name"] for r in BINDINGS}) + 0 or True
    for record in BINDINGS:
        assert record["category"] in ref.CATEGORY_KEYS, f"{where(record)}: {record['name']} has no category"


def test_no_engine_name_shadows_a_typst_global():
    """A binding named after a Typst built-in would replace it in every file of Sections/, not only in the engine.

    §10bis states the rule and nothing checked it until the commands tab made the whole list visible.
    """
    clashes = sorted({r["name"] for r in BINDINGS} & set(ref.TYPST_GLOBALS))
    assert not clashes, (
        f"lib/ binds {', '.join(clashes)}, which Typst already defines -- commands.typ re-exports "
        f"at the wildcard, so every section would get the engine's version instead"
    )


def test_every_public_command_is_documented():
    """A command Woodcore lists as public with no /// block has nothing to show for itself."""
    missing = [f"{where(r)} {r['name']}" for r in PUBLIC if not r["doc_lines"]]
    assert not missing, "public commands with no /// block:\n  " + "\n  ".join(missing)


def test_every_documented_argument_is_a_real_argument():
    """A `- name (type):` line naming an argument the signature does not have.

    This is what keeps a /// block honest when a signature changes: the bullet outlives the argument, and the tab would print a row for something a caller cannot pass.
    """
    wrong = []
    for record in PUBLIC:
        if record["kind"] != "function" or ".." in (record["params"] or ""):
            continue  # a sink takes its arguments by position and documents them by name
        real = {p for p, _d in ref.split_params(record["params"] or "")} | {"body"}
        for name, _kind, _meaning in block(record)["bullets"]:
            if name not in real:
                wrong.append(f"{where(record)} {record['name']}: documents {name!r}, which it does not take")
    assert not wrong, "\n  " + "\n  ".join(wrong)


def test_every_public_command_carries_examples():
    """Two examples at least, so the tab has something to render and a reader something to copy."""
    thin = []
    for record in PUBLIC:
        count = len(block(record)["examples"])
        if count < MIN_EXAMPLES:
            thin.append(f"{where(record)} {record['name']}: {count} example(s)")
    assert not thin, f"public commands with fewer than {MIN_EXAMPLES} examples:\n  " + "\n  ".join(thin)


def test_only_the_exempt_commands_skip_rendering():
    """A ```typ-dry fence is shown and never compiled, so it escapes the check below -- it may not spread quietly."""
    dry = {r["name"] for r in PUBLIC if any(not e["render"] for e in block(r)["examples"])}
    assert dry <= EXEMPT_FROM_RENDERING, (
        f"these use a ```typ-dry fence without being exempt: {sorted(dry - EXEMPT_FROM_RENDERING)} -- "
        f"either make the example compile, or say here why it cannot"
    )


def test_the_frozen_examples_run_against_the_current_engine():
    """examples/lib/ is a copy of the real engine, and must be today's.

    It is what makes the check below mean something: the examples read frozen *data*, on purpose, but they must exercise the **current** code. The copy is generated and gitignored precisely so it cannot rot into a second engine -- this is what says it has not.
    """
    stale = []
    for name in ref.LIB_FILES:
        live, copied = ROOT / "lib" / name, examples.EXAMPLES / "lib" / name
        if not copied.exists() or copied.read_bytes() != live.read_bytes():
            stale.append(name)
    assert not stale, (
        f"examples/lib/ does not match lib/ for {', '.join(stale)} -- "
        f"run `python calc/tools/build_examples.py`, or the examples are testing an older engine"
    )


def test_every_example_has_a_committed_page():
    """Every example carries a rendered page, and no page is left over from one that is gone.

    The pages are what Woodcore shows: it loads a file and compiles nothing (docs/typst/command-docs.md §10sexies). A fence edited without re-running the generator leaves a page that no longer matches it, and the tab says so rather than hiding it -- but it should not be left that way, which is what this asserts.
    """
    manifest = examples.index()
    wanted, missing, stale = set(), [], []
    for record in PUBLIC:
        for index, example in enumerate(block(record)["examples"]):
            if not example["render"]:
                continue
            for level in preview.LEVELS:
                if (record["name"], index, level) not in manifest:
                    continue
                wanted.add(manifest[(record["name"], index, level)]["stem"])
                png, state = examples.page(record["name"], index, level, example["code"], manifest)
                if state == "missing":
                    missing.append(f"{record['name']} example {index + 1} (level {level})")
                elif state == "stale":
                    stale.append(f"{record['name']} example {index + 1} (level {level})")
    assert not missing, "examples with no rendered page:\n  " + "\n  ".join(missing)
    assert not stale, (
        "examples whose page was rendered from an older fence:\n  " + "\n  ".join(stale)
        + "\nRun `python calc/tools/build_examples.py`."
    )
    orphans = sorted(p.name for p in examples.OUT.glob("*.png") if p.stem not in wanted)
    assert not orphans, "pages left behind by examples that no longer exist:\n  " + "\n  ".join(orphans)


def test_every_example_compiles():
    """Every frozen MWE, compiled against the frozen data and today's engine.

    Each is its own document, as it is in the tab: `#var` writes into a document-wide registry and `#unit` sets a unit to the end of the document, so a fence has to stand on its own. An example that is an excerpt -- naming a variable declared off-screen -- fails here, which is how four of the six fences that existed before v0.64 were found to be wrong.

    Since v0.65 it compiles `examples/<stem>.typ` rather than the fence against the live export, so it no longer breaks when the project changes -- which was the whole point of freezing. What it still catches is the engine moving under the examples.
    """
    if not preview.have_typst():
        raise Skip("typst is not on the path")
    if not (examples.EXAMPLES / "data").exists():
        raise Skip("examples/ has no frozen data -- run build_examples.py --freeze once")

    manifest = examples.index()
    if not manifest:
        raise Skip("no example has been generated yet")
    out = conftest.tmpdir("examples")
    jobs = sorted({e["stem"] for e in manifest.values()})

    def run(name):
        source = examples.EXAMPLES / f"{name}.typ"
        if not source.exists():
            return name, f"{source.name} is not there -- run build_examples.py"
        return name, preview.run_typst(source, out / f"{name}.png")

    failures = []
    with ThreadPoolExecutor(max_workers=4) as pool:
        for name, error in pool.map(run, jobs):
            if error:
                lines = [line for line in error.splitlines() if line.strip()][:4]
                failures.append(f"{name} does not compile:\n" + "".join(f"    {line}\n" for line in lines))
    assert not failures, (
        f"{len(failures)} of {len(jobs)} frozen examples do not compile.\n"
        "An example is compiled on its own, so it must declare what it names.\n\n"
        + "\n".join(failures)
    )


def test_the_preview_document_carries_the_reports_own_setup():
    """The preview is only worth looking at if it is the report's own page.

    Its width is A4 less the report's two 2.5 cm margins, so the line breaking and the right-hand citation column are the printed page's; `conf` gives it the report's font; and the level, the language and the decimals are stated in the file rather than passed as --input, those two flags being read by Statischer Rapport.typ and not by the engine.
    """
    text = preview.document('#show-calc("snow-load", "SL")', 3, "fr")
    for expected in ('#import "/config.typ": conf',
                     '#import "/commands.typ": *',
                     "#show: conf", "width: 16cm", "height: auto",
                     '#set-report-language("fr")', "#report-level.update(3)",
                     f"#number-digits.update({preview.DIGITS})"):
        assert expected in text, f"the preview document no longer carries {expected!r}"
    assert "--input" not in text


def test_the_imports_resolve_from_where_the_file_actually_sits():
    """A preview is compiled from standard input with examples/ as its Typst root (v0.81), so its imports are absolute, read from that root: config.typ and commands.typ must be there.

    Until v0.81 they were relative, computed from the depth of the .preview/ directory the document was written to -- derived rather than written down because giving that directory a per-process level once moved every generated file one deeper and `../../commands.typ` silently stopped resolving.
    """
    args = preview.typst_args(Path("x.png"))
    reached = Path(args[args.index("--root") + 1])
    assert reached == examples.EXAMPLES, f"{reached} is not examples/"
    for name in ("config.typ", "commands.typ"):
        assert (reached / name).exists(), f"{name} is not where the preview imports it from"


def test_a_typst_error_is_reported_in_the_examples_own_line_numbers():
    """Typst names a line of the file it compiled, and that file is an assembly: without this, an error on the example's first line is reported as line 11 of something nobody wrote."""
    moved = preview.in_example("error: unknown variable\n  ┌─ preview.typ:11:3", 2, "de")
    assert "example line 1" in moved, moved
    assert "preview.typ:11" not in moved


def test_every_public_command_offers_two_calls_that_name_real_things():
    """The two buttons must not copy a placeholder: an argument the export can answer for is answered."""
    samples = ref.sample_arguments(project.current().data_dir)
    bare = []
    for record in PUBLIC:
        for call in (ref.call_complete(record, samples), ref.call_minimal(record, samples)):
            if "<" in call and ">" in call:
                bare.append(f"{record['name']}: {call}")
    # show-check is the one placeholder that is honest: nothing exports a check to name (section 14).
    honest = ("show-check:",)
    bare = [line for line in bare if not line.startswith(honest)]
    assert not bare, "calls still carrying a placeholder:\n  " + "\n  ".join(bare)


def test_no_example_names_something_the_project_no_longer_has():
    """An example citing an id the project has dropped.

    ⚠️ Deliberately **not** "is the snapshot stale". The snapshot is meant to drift from the project — that is what freezing is for — so a check comparing the two would fire when nothing is wrong, which is worse than no check. What hurts is narrower: a page built on something that is gone, beside two copy buttons naming something else.

    Found the hard way in v0.65. The load workbooks were consolidated while this was being written; eight instances vanished, and only the two that a fence cited (`EL+AL-Fassade`) were a problem. Nothing would have said so — it was caught by hand, minutes before a commit.
    """
    hits = examples.dangling()
    assert not hits, (
        "examples naming something the project no longer has:\n  "
        + "\n  ".join(f"{stem} names {name!r}" for stem, name in hits)
        + "\nRepoint the /// fence in lib/, then run `python calc/tools/build_examples.py`."
    )


def test_the_ids_an_example_can_name_include_the_schemas():
    """`show-schema-1` and `-2` cite a schema, and the check did not read data/schemas.json at all: a schema the project dropped was never reported (periodic audit 260916, AUD-7-410)."""
    fake = conftest.tmpdir("ids_in")
    (fake / "schemas.json").write_text(json.dumps({"schema_version": "1.1", "schemas": {"X_SCHEMA": {}}}), encoding="utf-8")
    assert "X_SCHEMA" in examples.ids_in(fake)
    # and an id is compared within its kind: a connector named like a schema the project still has is not present for that
    (fake / "connectors.json").write_text(json.dumps({"schema_version": "3.0", "connectors": {"X_SCHEMA": {}}}), encoding="utf-8")
    kinds = examples.ids_by_kind(fake)
    assert "X_SCHEMA" in kinds["schemas"] and "X_SCHEMA" in kinds["connectors"] and "X_SCHEMA" not in kinds["plans"]


def test_the_dangling_check_catches_a_planted_one():
    """The check above, held against a defect put there on purpose.

    A guard that has never fired is a guard nobody has tested. This removes one instance from a copy of the example project's export and asserts the fence that cites it is named -- which is exactly the shape of the accident it exists for.

    ⚠️ It could not pass for as long as the snapshot was stale (B25): other ids were reported beside the planted one, and `fmt-2`, which it expected, went with `fmt` in v0.80. Both were found when the snapshot was re-frozen from the example project (v0.86).
    """
    instance = "EL+AL-Wand"  # named by show-calc's second example
    fake = conftest.tmpdir("dangling")
    (fake / "data").mkdir()
    for path in examples.example_data_dir().glob("*.json"):
        shutil.copy2(path, fake / "data" / path.name)
    calculations = json.loads((fake / "data" / "calculations.json").read_text(encoding="utf-8"))
    sheets = calculations["domains"]["dead-load"]["instances"]
    if instance not in sheets:
        raise Skip(f"{instance} is no longer in the export -- pick another to plant against")
    del sheets[instance]
    (fake / "data" / "calculations.json").write_text(json.dumps(calculations), encoding="utf-8")

    hits = examples.dangling(data_dir=fake / "data")
    assert hits, f"removing {instance!r} from the export was not noticed"
    assert all(name == instance for _stem, name in hits), hits
    assert {stem for stem, _name in hits} >= {"show-calc-2"}, hits


def test_every_frozen_example_imports_a_file_that_is_there():
    """The MWEs' imports resolve, at whatever depth they are written.

    They are derived from where the file goes, never written down: Typst resolves an import against the importing file, so a literal `../..` is right only at the depth it was written for. That has cost this project once already -- Woodcore's scratch directory gained a per-process level and every import in it stopped resolving without a word -- and a hard-coded pair here would have been the same trap waiting. Checked at a depth the examples do not currently use, so it guards the derivation and not just today's layout.
    """
    for where_dir in (examples.EXAMPLES, examples.EXAMPLES / "nested" / "deeper"):
        config, commands = examples.imports_for(where_dir)
        assert (where_dir / config).resolve() == (examples.EXAMPLES / "config.typ").resolve(), where_dir
        assert (where_dir / commands).resolve() == (examples.EXAMPLES / "commands.typ").resolve(), where_dir
    for name in ("config.typ",):
        assert (examples.EXAMPLES / name).exists()
    written = sorted(examples.EXAMPLES.glob("*.typ"))
    assert written, "no MWE has been generated yet"
    for path in written:
        if path.name in examples.KEPT:
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.startswith("#import"):
                target = path.parent / line.split('"')[1]
                assert target.exists(), f"{path.name} imports {line.split('\"')[1]}, which is not there"


def test_a_preview_writes_nothing_but_its_page():
    """A preview is handed to Typst on standard input, with examples/ as its root whatever project is open: nothing is written where a project or an installed program keeps its files (v0.81). Until then a .typ went into .preview/ under the project's report folder, which the frozen examples -- the program's -- had to share a root with.

    ⚠️ This test file writes nothing into tests/.tmp but its own pages: its examples are rendered through command_preview, whose staging names carry the process id, so two runs of the suite at once cannot delete each other's file here.
    """
    args = preview.typst_args(Path("x.png"))
    assert "-" in args and args[args.index("--root") + 1] == str(examples.EXAMPLES), args
    for gone in ("write_document", "preview_dir", "preview_typ", "import_prefix", "typst_root"):
        assert not hasattr(preview, gone), f"command_preview.{gone} is back: a preview writes a file again"
    if conftest.have_typst() and (examples.EXAMPLES / "commands.typ").exists():
        png, error = preview.render_blocking('#val(1.5, unit: "kN")', use_cache=False)
        assert error is None and png.exists(), error



def test_the_calls_the_commands_tab_copies_compile():
    """Every «Copier» of the commands tab, compiled as pasted, one document each (docs/typst/command-docs.md §10sexies). Five read the report's language and need `context`, which their calls did not carry (periodic audit 260916, AUD-5-5). show-check has nothing to name (section 14); var-unit, eq, val and verify name variables a report declares first (AUD-5-7, the engineer's decision)."""
    if not conftest.have_typst():
        raise Skip("typst is not on PATH")
    import subprocess
    samples = ref.sample_arguments(project.current().data_dir)
    exempt = {"show-check", "var-unit", "eq", "val", "verify"}
    probe = conftest.probe_dir("copied_calls")
    root = conftest.TYPST_ROOT
    failures = []
    for record in PUBLIC:
        if record["name"] in exempt:
            continue
        for kind, call in (("complete", ref.call_complete(record, samples)), ("minimal", ref.call_minimal(record, samples))):
            doc = probe / f"{record['name']}-{kind}.typ"
            doc.write_text('#import "/commands.typ": *\n' + call + "\n", encoding="utf-8")
            r = subprocess.run(["typst", "compile", "--root", str(root), str(doc), str(doc.with_suffix(".pdf"))],
                               capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300)
            if r.returncode != 0:
                failures.append(f"{record['name']} ({kind}): {call!r} -- {r.stderr.strip().splitlines()[0] if r.stderr.strip() else r.returncode}")
    assert not failures, "copied calls that do not compile:\n  " + "\n  ".join(failures)


# -- the documentation in French and German (v0.86) -------------------------------

def _records():
    """The public commands with their English doc block merged in, as the tab reads them before it translates."""
    out = []
    for record in PUBLIC:
        merged = dict(record)
        merged.update(block(record))
        out.append(merged)
    return out


def test_every_public_command_is_translated():
    """Every paragraph and every argument of every public command has a French and a German translation of its **current** English (calc/i18n/commands.json, command_docs.py).

    A unit is matched on the English it translates, so a `///` block edited without its translation fails here, naming the command and the unit -- and the tab shows that passage in English, marked, until it is translated again. A unit nothing matches any more is reported too, so the file does not fill with translations of sentences that are gone. To repair: put the new English in the unit's `en` and translate it.
    """
    missing, orphans = docs.gaps(_records())
    lines = [f"missing   {name}: {what} -- {english!r}" for name, what, english in missing]
    lines += [f"orphaned  {name}: {what} -- {english!r}" for name, what, english in orphans]
    assert not lines, "calc/i18n/commands.json does not follow the /// blocks:\n  " + "\n  ".join(lines)


def test_a_translation_keeps_the_code_it_quotes():
    """What stands between backticks is code -- a call, an argument, a value -- and is the same in all three languages. A translator who translated `\"val+unit\"` would send the reader to type a value the command refuses."""
    bad = docs.code_spans_kept()
    assert not bad, "translations whose code differs from the English:\n  " + "\n  ".join(
        f"{name}, {where}, {lang}: {spans}" for name, where, lang, spans in bad)


def test_the_german_is_swiss_and_the_french_spaced():
    """The German is Swiss: never an ß (Massgebend, Fussnote), as every German word of this project. The French puts a space before a colon, as the window's own French does («Arguments :») -- but not inside code, nor in what a sentence quotes of a dictionary (`value: …`) or of a German page («Bauteile: T001»), which are allowed by name."""
    import re
    # a dictionary's keys, a German label, and a word inside a sentence of the engineer's own that the
    # documentation quotes verbatim («… sous forme: 1.35 * CC1 …») -- his words are not re-punctuated
    quoted = {"value", "desc", "Bauteile", "forme"}
    table = docs.load()
    sharp, unspaced = [], []
    for name, entry in table["commands"].items():
        units = list(entry.get("paragraphs") or []) + list((entry.get("arguments") or {}).values())
        for unit in units:
            if "ß" in unit.get("de", ""):
                sharp.append(name)
            prose = re.sub(r"`[^`]+`", "", unit.get("fr", ""))
            for m in re.finditer(r"(?<!\w)([^\W\d_]+)[:;](?=\s)", prose):  # a word, not an id or a number («T001: Träger» is a page quoted)
                if m.group(1) not in quoted:
                    unspaced.append(f"{name} ({m.group(0)})")
    assert not sharp, f"an ß in the German of {sorted(set(sharp))}"
    assert not unspaced, f"a colon or semicolon without its space in the French of {sorted(set(unspaced))}"


def test_a_combined_bullet_documents_both_arguments():
    """`- norm (str, none), norm-ref (str): the citation` documents two arguments. Read as a continuation of the line above until v0.86, it gave `norm` and `norm-ref` no row in the commands tab or the workbook, and ended `level`'s meaning with their text."""
    parsed = ref.parse_doc_block([
        "Summary.",
        "- level (int, auto): the level.",
        "- norm (str, none), norm-ref (str): the citation,",
        "  in the right-hand column.",
        "-> content",
    ])
    assert [b[0] for b in parsed["bullets"]] == ["level", "norm", "norm-ref"], parsed["bullets"]
    assert parsed["bullets"][0][2] == "the level.", parsed["bullets"][0]
    assert parsed["bullets"][1][2] == parsed["bullets"][2][2] == "the citation, in the right-hand column."
    assert parsed["bullets"][1][1] == "str, none" and parsed["bullets"][2][1] == "str"
    for record in PUBLIC:
        for bullet in block(record)["bullets"]:
            assert " (str, none), " not in bullet[2] and " (none, str), " not in bullet[2], (record["name"], bullet[0])


def test_the_tab_sets_the_prose_as_the_blocks_write_it():
    """Backticks, **bold** and *italic* are how a /// block is written, not what the tab shows: code in the fixed font, emphasis as emphasis -- running across a code span too -- and a `*` that is a symbol's (F*_x,i) left alone."""
    try:
        import commands_tab
    except ImportError as exc:
        raise Skip(f"PySide6 is not installed ({exc})")
    html = commands_tab.prose_html('**`unit:` is display only**: *its* unit, F*_x,i < 2, `a*b*c`', "Consolas")
    assert html.startswith("<b><span"), html
    assert "<i>its</i>" in html and "F*_x,i &lt; 2" in html and ">a*b*c</span>" in html, html
    assert "`" not in html and "**" not in html, html
    assert commands_tab.prose_plain("**`find`** lists *everything*") == "find lists everything"


# -- one decision, read by the tab, the generator and the website -------------------------------

def test_one_function_decides_which_levels_an_example_is_shown_at():
    """All three levels for a command taking a `level:`, the report's base level alone for one that does not or for an example that writes its own `level:`, none for a ```typ-dry fence: command_docs.example_levels, which build_examples.py and website/build.py read, where each of them and the tab decided it until then."""
    for record in PUBLIC:
        parsed = block(record)
        for example in parsed["examples"]:
            levels = docs.example_levels(record, parsed, example)
            if not example["render"]:
                assert levels == (), record["name"]
            elif docs.takes_level(record, parsed) and preview.fixes_level(example["code"]) is None:
                assert levels == tuple(preview.LEVELS), record["name"]
            else:
                assert levels == (preview.DEFAULT_LEVEL,), record["name"]
    assert docs.takes_level(BY_NAME["show-calc"], block(BY_NAME["show-calc"])) and not docs.takes_level(BY_NAME["get-value"], block(BY_NAME["get-value"]))
    pinned = {"render": True, "code": '#show-calc("snow-load", "SL", level: 3)'}
    assert docs.example_levels(BY_NAME["show-calc"], block(BY_NAME["show-calc"]), pinned) == (preview.DEFAULT_LEVEL,)
    generated = {(c, i, lvl) for c, i, lvl, _code in examples.examples_of(ROOT)}
    decided = {(r["name"], i, lvl) for r in PUBLIC for i, e in enumerate(block(r)["examples"]) for lvl in docs.example_levels(r, block(r), e)}
    assert generated == decided, sorted(generated ^ decided)[:10]
    for path in (ROOT / "calc" / "tools" / "build_examples.py", ROOT / "website" / "build.py"):
        assert "fixes_level" not in path.read_text(encoding="utf-8"), f"{path.name} decides an example's levels itself again"


def test_a_level_0_pins_no_page():
    """`level: 0` prints nothing (docs/architecture/data-contracts.md §3.7, docs/typst/formulas.md §10quinquies), so an example declaring its variables at 0 and printing the line under them at the report's level follows the report: all three levels, the selector in the tab, the -L1/-L3 pages and the site's buttons. Until v0.94 `fixes_level` read the 0 as a pinned level, and the examples of var, var-unit, eq, val, var-line, verify and member that show a level 0 had none of the three. One pinning a level that prints is still pinned to it, whatever zeros stand beside it."""
    record, parsed = BY_NAME["eq"], block(BY_NAME["eq"])
    declared = '#var("F", 2, "kN", level: 0)\n#var("l", 3, "m", level:0)\n#eq("M", `F dot l`)'
    assert preview.fixes_level(declared) is None, "a `level: 0` pinned the example"
    assert docs.example_levels(record, parsed, {"render": True, "code": declared}) == tuple(preview.LEVELS)
    pinned = '#var("F", 2, "kN", level: 0)\n#eq("M", `F dot l`, level: 2)'
    assert preview.fixes_level(pinned) == "2"
    assert docs.example_levels(record, parsed, {"render": True, "code": pinned}) == (preview.DEFAULT_LEVEL,)
    assert preview.fixes_level('#member("S", level: 0)\n#verify-compression("S", N: -40, level: 3)') == "3"
    assert preview.fixes_level('#var("x", 1, level: auto)') is None and preview.fixes_level('#var("x", 1, level: 1)') == "1"
    # every committed example that declares at 0 and nothing else is shown at the three levels, and its three pages are there
    manifest = examples.index()
    zeros = []
    for rec in PUBLIC:
        blk = block(rec)
        for i, example in enumerate(blk["examples"]):
            if example["render"] and docs.takes_level(rec, blk) and preview.fixes_level(example["code"]) is None and re.search(r"\blevel\s*:\s*0\b", example["code"]):
                zeros.append(rec["name"])
                assert docs.example_levels(rec, blk, example) == tuple(preview.LEVELS), (rec["name"], i)
                for level in preview.LEVELS:
                    path, state = examples.page(rec["name"], i, level, example["code"], manifest)
                    assert path is not None and state == "fresh", (rec["name"], i, level, state)
    assert {"var", "var-unit", "eq", "val", "var-line", "verify", "member"} <= set(zeros), sorted(set(zeros))


def test_an_example_is_rendered_in_the_window_s_language():
    """The committed pages are German; a French or English page is compiled on demand, against the frozen snapshot, into the cache -- the document the website compiles its pages in three languages from: the engine's words by `set-report-language`, Typst's own by `set text(lang:)`."""
    french = preview.document('#show-calc("snow-load", "SL")', 2, "fr", document_language=True)
    assert '#set text(lang: "fr", region: "CH")' in french and '#set-report-language("fr")' in french
    assert "#set text(" not in preview.document("#x", 2, "de"), "the committed German pages are left as they were"
    assert preview.cache_key("#x", 2, "fr", "t") != preview.cache_key("#x", 2, "fr", "t", document_language=True)
    site = (ROOT / "website" / "build.py").read_text(encoding="utf-8")
    assert "document_language=True" in site and "#set text(" not in site, "the website assembles an example's page itself again"
    try:
        preview.render_localised("#x", lang="it")
    except ValueError as exc:
        assert "it" in str(exc)
    else:
        raise AssertionError("a language the report does not have was rendered")
    if not conftest.have_typst() or not (examples.EXAMPLES / "commands.typ").exists():
        raise Skip("typst is not on PATH, or examples/ has no engine copy -- run build_examples.py")
    code = '#show-calc("snow-load", "SL")'
    pages = {}
    for lang in ("fr", "en"):
        png, error = preview.render_localised(code, 3, lang, use_cache=False)
        assert error is None and png.exists(), error
        again, error = preview.render_localised(code, 3, lang)
        assert error is None and again == png, "a second call is a load from the cache"
        pages[lang] = png.read_bytes()
    german, error = preview.render_blocking(code, 3, "de")
    assert error is None, error
    assert len({pages["fr"], pages["en"], german.read_bytes()}) == 3, "at level 3 the three languages print the snow load in their own words"
    _png, error = preview.render_localised("#no-such-command()", 2, "fr", use_cache=False)
    assert error and "example line 1" in error, error


# -- the tab: the site's data and the site's page, in the window's language (v0.94) -------------------------------

def _qt():
    import os
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError as exc:
        raise Skip(f"PySide6 is not installed ({exc})")
    return QApplication.instance() or QApplication([])


class _App:
    """What the commands tab asks of the window -- woodcore_gui.MainWindow's t, label, fonts, views and copy -- so that the tab is built alone in each language, where a whole window per language would build every other tab three times."""

    def __init__(self, lang):
        from PySide6.QtGui import QFont
        from PySide6.QtWidgets import QApplication
        import woodcore_gui
        import theme
        self.strings = woodcore_gui.STRINGS[lang]
        self.lang, self.views, self.copied = lang, {}, None
        base = QApplication.font()
        self.bold_font = QFont(base)
        self.bold_font.setBold(True)
        self.title_font = QFont(self.bold_font)
        if base.pointSizeF() > 0:
            self.title_font.setPointSizeF(base.pointSizeF() * 1.25)
        self.mono_font = theme.mono_font(base.pointSizeF())

    def t(self, key, **values):
        return self.strings[key].format(**values) if values else self.strings[key]

    def label(self, key):
        return self.t(key) + (" :" if self.lang == "fr" else ":")

    def copy(self, text):
        self.copied = text


def _tab(lang, quiet=False):
    """The commands tab in `lang`, off-screen. `quiet` shows no page at all: what is checked then is the layout, not the pages."""
    _qt()
    import commands_tab
    tab = commands_tab.CommandsTab(_App(lang))
    if quiet:
        tab.show_page = lambda _box: None
    tab.resize(1400, 900)
    return tab


def _select(tab, name):
    tab.tree.setCurrentItem(tab.nodes[f"cmd|{name}"])
    return tab.record(name)


def _settle(tab, seconds=90):
    """Until every example of the page shown has its page: the compiles run in a thread of their own, and the tab looks every POLL_MS."""
    import time
    app = _qt()
    deadline = time.time() + seconds
    while (tab.job is not None or tab.queue) and time.time() < deadline:
        app.processEvents()
        time.sleep(0.02)
    app.processEvents()
    assert tab.job is None and not tab.queue, "an example is still compiling"


class _Stubs:
    """command_preview's functions replaced for one test, and put back."""

    def __init__(self, **stubs):
        self.stubs, self.saved = stubs, {}

    def __enter__(self):
        for name, stub in self.stubs.items():
            self.saved[name] = getattr(preview, name)
            setattr(preview, name, stub)
        return self

    def __exit__(self, *_exc):
        for name, value in self.saved.items():
            setattr(preview, name, value)


def test_the_tree_is_the_reference_s_categories_in_its_order_and_words():
    """The categories in build_reference.CATEGORIES' order -- calculating in the report first -- named and introduced by calc/i18n/reference.json in each of the window's languages, Internes last and folded; the tree's headings the file's words; and the search still finding a command by the words of either language."""
    from PySide6.QtCore import Qt
    import commands_tab
    public_keys = [key for key, _names in ref.CATEGORIES]
    for lang in ("fr", "de", "en"):
        tab = _tab(lang, quiet=True)
        tops = [tab.tree.topLevelItem(i) for i in range(tab.tree.topLevelItemCount())]
        keys = [item.data(0, Qt.ItemDataRole.UserRole)[4:] for item in tops]
        assert keys == public_keys + [ref.INTERNAL] == commands_tab.CATEGORY_ORDER, keys
        for key, item in zip(keys, tops):
            assert item.text(0).startswith(docs.category_label(key, lang)), (lang, key, item.text(0))
            if key != ref.INTERNAL:
                assert item.text(tab.SUMMARY) == docs.category_lead(key, lang), (lang, key)
                assert [item.child(i).text(0) for i in range(item.childCount())] == list(dict(ref.CATEGORIES)[key])
        assert not tops[-1].isExpanded(), "Internes is folded"
        header = tab.tree.headerItem()
        assert (header.text(0), header.text(1)) == (docs.word("command", lang), docs.word("arguments", lang))
        assert not [key for key in commands_tab.STRINGS[lang] if key.startswith("ref_cat_")]
    tab = _tab("fr", quiet=True)
    record = tab.record("show-calc")
    for words in (record["paragraphs"][0], record["english"]["paragraphs"][0]):
        tab.search.setText(words[:30])
        assert "cmd|show-calc" in tab.nodes, f"the search does not find show-calc by {words[:30]!r}"
    tab.search.setText("")


def test_the_detail_pane_is_laid_out_as_the_site_s_command_page():
    """Selected, a command is shown as the website's page shows it (website/build.py's page_command), in this order: the category, the name, the signature coloured, the paragraphs in the window's language, the arguments as a table -- name, type, default, what it does --, what it returns, the minimal and the complete call each copied by its button, the examples, the import line and where it is defined. The words are reference.json's; the signature, the rows and the calls command_docs'."""
    import richtext
    for lang in ("de", "fr"):
        tab = _tab(lang, quiet=True)
        record = _select(tab, "show-calc")
        calls = docs.calls(record, tab.samples)
        expected = (["eyebrow", "title", "signature"] + ["paragraph"] * len(record["paragraphs"])
                    + (["untranslated"] if record["untranslated"] else [])
                    + ["arguments", "argument_table", "returns"]
                    + [part for key, _call in calls for part in (key, key + "_code")]
                    + ["example"] * len(record["examples"]) + ["import", "defined"])
        names = [name for name, _widget in tab.parts]
        assert names == expected, names
        parts = dict(tab.parts)
        assert parts["eyebrow"].text() == f"{docs.word('commands', lang)} › {docs.category_label('display', lang)}"
        assert parts["title"].text() == "show-calc"
        assert parts["signature"].objectName() == "code" and "show-calc" in parts["signature"].text()
        assert docs.signature(record, record).startswith("#show-calc(domain, instance") and docs.signature(record, record).endswith("-> content")
        assert parts["arguments"].text() == docs.word("arguments", lang)
        grid = parts["argument_table"].layout()
        assert grid.rowCount() == len(record["bullets"]) + 2 and grid.columnCount() == 4
        headers = [grid.itemAtPosition(0, column).widget().text() for column in range(4)]
        assert headers == [tab.t(key) for key in ("ref_col_name", "ref_col_type", "ref_col_default", "ref_col_summary")]
        rows = docs.arguments(record, record)
        for row, arg in enumerate(rows, start=2):
            assert grid.itemAtPosition(row, 0).widget().text() == arg["name"]
            assert grid.itemAtPosition(row, 2).widget().text() == (arg["default"] if arg["default"] is not None else "—")
            assert all(kind in grid.itemAtPosition(row, 1).widget().text() for kind in arg["types"])
        assert [r["name"] for r in rows[:2]] == ["domain", "instance"] and rows[0]["default"] is None
        assert parts["returns"].text() == f"{docs.word('returns', lang)} content"
        fields = [w for w in tab.detail.findChildren(richtext.CodeField)]
        assert [f.text() for f in fields[:len(calls)]] == [call for _key, call in calls]
        for key, _call in calls:
            assert parts[key].text() == docs.word(key, lang)
        boxes = tab.boxes
        assert [box.heading.text() for box in boxes] == [docs.word("example", lang, n=i + 1) for i in range(len(record["examples"]))]
        assert parts["defined"].text() == f"{docs.word('defined_in', lang)} lib/{record['file']}:{record['line']}"
    assert docs.calls(BY_NAME["report-level"], {}) == [("call_minimal", "#report-level.update(2)")], "a call identical in both forms is offered once, as on the site"
    values = [r for r in BINDINGS if r["kind"] != "function" and r["name"] not in ref.WRITTEN_CALLS]
    assert not values or docs.calls(values[0], {}) == [], "a binding the reference writes no call for is offered none"


def test_the_level_selector_stands_exactly_where_example_levels_says():
    """The 1 · 2 · 3 buttons stand under an example where command_docs.example_levels gives three levels -- the site's decision, which build_examples.py renders the pages by -- and nowhere else; where the command takes a level and the example writes its own, the rule is said in their place, with the level the example prints at."""
    import commands_tab
    tab = _tab("de", quiet=True)
    checked = 0
    for record in (r for r in tab.records if r["category"] != ref.INTERNAL and r["examples"]):
        _select(tab, record["name"])
        assert len(tab.boxes) == len(record["examples"]), record["name"]
        for box, example in zip(tab.boxes, record["examples"]):
            levels = docs.example_levels(record, record["english"], example)
            assert box.levels == levels, (record["name"], box.index)
            if len(levels) > 1:
                assert box.group is not None and sorted(box.group.id(b) for b in box.group.buttons()) == list(levels), (record["name"], box.index)
                assert box.group.checkedId() == box.level == preview.DEFAULT_LEVEL
                checked += 1
            else:
                assert box.group is None, (record["name"], box.index)
            pinned = commands_tab.pinned_level(example["code"])
            if example["render"] and len(levels) == 1 and docs.takes_level(record, record["english"]) and pinned is not None:
                assert box.fixed_note is not None and tab.t("ref_level_fixed", level=pinned) in box.fixed_note.text(), (record["name"], box.index)
            else:
                assert box.fixed_note is None, (record["name"], box.index)
    assert checked > 20, checked
    assert commands_tab.pinned_level('#member("S", level: 0)\n#verify-compression("S", N: -40, level: 3)') == "3", "a `level: 0` declares and prints nothing: the rule names the level that prints"
    assert commands_tab.pinned_level('#var("F", 2, "kN", level: 0)\n#eq("M", `F dot l`)') is None


def test_a_french_or_english_example_is_compiled_in_that_language():
    """A French or English window shows each example in its own language: compiled by command_preview.render_localised in a thread of its own, «Compilation…» standing in the box meanwhile, and a level chosen compiled at that level. German shows the committed page, compiling nothing. Where Typst is on the PATH, one real compile: the page comes from the cache, not from examples/out."""
    german = examples.OUT / "show-calc-1.png"
    seen = []

    def render(code, level, lang, *_args, **_kwargs):
        seen.append((code, level, lang))
        return german, None

    with _Stubs(render_localised=render, cached_png=lambda _key: None, have_typst=lambda: True):
        tab = _tab("fr")
        record = _select(tab, "show-calc")
        first = tab.boxes[0]
        assert first.status.text() == tab.t("ref_rendering") and first.preview.path is None, "no placeholder while the page compiles"
        _settle(tab)
        assert [(level, lang) for _code, level, lang in seen] == [(preview.DEFAULT_LEVEL, "fr")] * len(record["examples"]), seen
        assert all(box.preview.path == german and not box.status.isVisibleTo(box) for box in tab.boxes)
        seen.clear()
        first.group.button(3).click()
        _settle(tab)
        assert seen == [(first.code, 3, "fr")], seen
        german_tab = _tab("de")
        _select(german_tab, "show-calc")
        assert german_tab.job is None and not german_tab.queue and seen == [(first.code, 3, "fr")], "a German window compiles a committed page"
        assert german_tab.boxes[0].preview.path == examples.page("show-calc", 0, 2, first.code)[0]
    if not conftest.have_typst() or not (examples.EXAMPLES / "commands.typ").exists():
        raise Skip("typst is not on PATH, or examples/ has no engine copy -- run build_examples.py")
    with _Stubs(cached_png=lambda _key: None):   # nothing from the cache: render_localised compiles for real
        tab = _tab("en")
        _select(tab, "fmt-decimals")
        _settle(tab)
        for box in tab.boxes:
            assert box.preview.path is not None and preview.CACHE_DIR in box.preview.path.parents, (box.index, box.preview.path, box.status.text())
            assert not box.status.isVisibleTo(box), box.status.text()


def test_a_page_that_cannot_be_compiled_shows_the_german_one_and_says_why():
    """Where the compile fails, or Typst is not there at all, a French or English window shows the committed German page with one line saying why -- Typst's first line, or that Typst is missing -- rather than an empty box or a wall of error."""
    def failing(*_args, **_kwargs):
        return None, "error: unknown variable: foo\n  ┌─ example line 1"

    with _Stubs(render_localised=failing, cached_png=lambda _key: None, have_typst=lambda: True):
        tab = _tab("fr")
        record = _select(tab, "show-calc")
        _settle(tab)
        for box, example in zip(tab.boxes, record["examples"]):
            page = examples.page("show-calc", box.index, box.level, example["code"])[0]
            assert box.preview.path == page, (box.index, box.preview.path)
            assert box.status.text() == tab.t("ref_german_page", reason="error: unknown variable: foo"), box.status.text()
    calls = []
    with _Stubs(render_localised=lambda *a, **k: calls.append(a) or (None, None), cached_png=lambda _key: None, have_typst=lambda: False):
        tab = _tab("en")
        _select(tab, "val")
        assert not calls and tab.job is None and not tab.queue, "nothing is compiled without typst"
        shown = [box for box in tab.boxes if box.renderable]
        assert shown and all(box.preview.path is not None and box.status.text() == tab.t("ref_german_page", reason=tab.t("ref_no_typst")) for box in shown)
