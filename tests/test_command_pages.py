"""calc/i18n/command-pages.json, the condensed page of every public command: its shape, its three languages, its agreement with lib/, the quotes of its fine values, and that every command has one (spec 2026-10-24-onglet-commandes-pages, REQ-001, REQ-002, REQ-003, REQ-004, REQ-006, REQ-013; docs/typst/command-docs.md §10sexies).

The page is written by hand beside the `///` block, which stays the source of the signature: what is held here is that the two name the same arguments and the same values, so that an argument renamed in lib/, or a fine value added to lib/display-presets.json, fails a test naming the command rather than leaving a page that describes another command.
"""

import copy
import json
import sys
from concurrent.futures import ThreadPoolExecutor

import conftest
from conftest import ROOT, Skip

sys.path.insert(0, str(ROOT / "calc" / "tools"))

import build_reference as ref  # noqa: E402
import command_pages as pages  # noqa: E402

TIER = "fast"

BINDINGS = ref.lib_bindings(ROOT)
PUBLIC = [r for r in BINDINGS if r["category"] != ref.INTERNAL]
BY_NAME = {r["name"]: r for r in PUBLIC}
TABLE = pages.load()


def _write(data, name="command-pages.json"):
    path = conftest.tmpdir("command_pages") / name
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return path


def test_the_file_reads_against_its_schema():
    """REQ-001, ARCH-004: the file carries its schema_version and fits schemas/command-pages.schema.json."""
    assert TABLE["schema_version"] == pages.SCHEMA_VERSION
    assert (ROOT / "schemas" / "command-pages.schema.json").is_file()


def test_a_malformed_file_stops_naming_the_file_and_the_field():
    """A file Woodcore cannot read as written stops, and says which file and which field (principle «a malformed file stops»)."""
    broken = copy.deepcopy(TABLE)
    del broken["commands"]["var"]["lead"]
    try:
        pages.load(_write(broken))
    except pages.PagesError as exc:
        assert "command-pages.json" in str(exc) and "var" in str(exc) and "lead" in str(exc), exc
    else:
        raise AssertionError("a page without its lead was read")
    bad = conftest.tmpdir("command_pages") / "bad.json"
    bad.write_text("{not json", encoding="utf-8")
    try:
        pages.load(bad)
    except pages.PagesError as exc:
        assert "bad.json" in str(exc), exc
    else:
        raise AssertionError("a file that is not JSON was read")


def test_a_language_missing_is_named_with_its_command_and_argument():
    """REQ-001: one language left out of one argument's sentence names the command, the argument and the language -- no silent fallback to another language."""
    broken = copy.deepcopy(TABLE)
    del broken["commands"]["var"]["arguments"]["display"]["text"]["de"]
    try:
        pages.load(_write(broken))
    except pages.PagesError as exc:
        message = str(exc)
        assert "var" in message and "display" in message and "de" in message, message
    else:
        raise AssertionError("a sentence without its German was read")
    broken = copy.deepcopy(TABLE)
    broken["commands"]["var"]["arguments"]["level"]["values"][2]["call"]["en"] = ""
    try:
        pages.load(_write(broken))
    except pages.PagesError as exc:
        assert "level" in str(exc) and "call" in str(exc) and "en" in str(exc), exc
    else:
        raise AssertionError("a call without its English was read")


def test_lib_and_the_pages_name_the_same_arguments_and_values():
    """REQ-003: for every command with a page, every argument of its /// block has a row or a place among the names written by name, no row names an argument lib/ no longer has, the statuses agree with the signature, and every fine argument lists exactly lib/display-presets.json's values."""
    assert pages.disagreements(PUBLIC, TABLE) == []


def test_an_argument_renamed_in_lib_fails_naming_the_command_and_the_argument():
    """REQ-003, planted: `display` of #var renamed `shown` in its /// block, the page left as it was."""
    record = dict(BY_NAME["var"])
    record["doc_lines"] = [line.replace("- display (", "- shown (") for line in record["doc_lines"]]
    found = pages.disagreements([record], TABLE)
    assert ("var", "argument 'shown' of lib/ has no row in command-pages.json") in found, found
    assert ("var", "argument 'display' of command-pages.json is not an argument of lib/ any more") in found, found


def test_a_fine_value_added_to_lib_without_its_page_fails():
    """REQ-003, planted: a value added to `display` in lib/display-presets.json, with no sentence and no call on the page."""
    real = pages.fine_values
    try:
        values = real()
        values["display"] = values["display"] + ["value-name"]
        pages.fine_values = lambda: values
        found = pages.disagreements([BY_NAME["var"]], TABLE)
    finally:
        pages.fine_values = real
    assert any(command == "var" and "'display'" in what and "value-name" in what for command, what in found), found


def test_every_fine_value_is_written_between_quotes():
    """REQ-006: a fine value is a string -- the engine refuses `display: none` -- so every call, set-up line and example writes it quoted, `"none"` included, `auto` alone bare."""
    assert pages.quoting_errors(TABLE) == []
    planted = copy.deepcopy(TABLE)
    planted["commands"]["var"]["arguments"]["display"]["values"][1]["call"] = '#var("M_d", 14.06, "kNm", display: none)'
    assert any(where.startswith("display.values[1]") for _c, where, _code in pages.quoting_errors(planted))


def test_no_page_carries_an_internal_reference():
    """REQ-013, D-6: no «spec …», «REQ-», «(v0.» in a page meant for a reader."""
    assert pages.internal_references(TABLE) == []
    planted = copy.deepcopy(TABLE)
    planted["commands"]["var"]["lead"]["fr"] += " (spec 2026-10-21-commandes-typst-refonte, REQ-002)"
    assert pages.internal_references(planted)


def _prose(table):
    """Every sentence of the pages, as (command, where, lang, text): the code they quote taken out."""
    import re
    def texts(node, where):
        if isinstance(node, dict):
            if set(pages.LANGS) <= set(node) and all(isinstance(node[l], str) for l in pages.LANGS):
                yield where, node
                return
            for key, child in node.items():
                if key in ("call", "setup", "code", "context"):
                    continue
                yield from texts(child, f"{where}.{key}")
        elif isinstance(node, list):
            for i, child in enumerate(node):
                yield from texts(child, f"{where}[{i}]")
    for name, page in table["commands"].items():
        for where, text in texts(page, name):
            for lang in pages.LANGS:
                yield name, where, lang, re.sub(r"`[^`]*`", "", text[lang])
    for where, text in texts(table["value-texts"], "value-texts"):
        for lang in pages.LANGS:
            yield "value-texts", where, lang, re.sub(r"`[^`]*`", "", text[lang])


def test_the_german_is_swiss_and_the_french_spaced():
    """As calc/i18n/reference.json beside it: the German never writes ß, the French sets a narrow no-break space before «:», «;», «?» and «!» and inside «guillemets» -- outside the code a sentence quotes."""
    import re
    sharp = [(c, w) for c, w, lang, text in _prose(TABLE) if lang == "de" and "ß" in text]
    unspaced = [(c, w, text) for c, w, lang, text in _prose(TABLE)
                if lang == "fr" and (re.search(r"(?<! )[:;?!](?=\s|$)", text) or re.search(r"«(?! )|(?<! )»", text))]
    assert not sharp, sharp
    assert not unspaced, unspaced[:5]


# The categories whose pages are written (REQ-013), one more at each step of the spec's plan; the last step names them all and every public command must then have its page (REQ-004).
WRITTEN = ("formula", "display", "data", "format", "document")


def test_every_command_of_a_written_category_has_its_page_complete():
    """REQ-002, REQ-013: for every command of a category written -- a lead, three or four key points, two or three examples an argument, no two arguments saying the same thing --, in fr, de and en."""
    names = [name for key, members in ref.CATEGORIES if key in WRITTEN for name in members]
    assert pages.gaps(names, TABLE) == []
    for name in names:
        assert name in TABLE["commands"], name


def test_every_whole_call_of_a_page_compiles():
    """REQ-007 (T36): every example of an argument written as a whole call -- `#var("b", 100, "mm")` -- compiles, with the lines it assumes above it (`context`), in each language; a fragment (`display: "none"`) is a part of a call and is held by the quotes' rule instead."""
    import build_examples as examples
    if not conftest.have_typst() or not (examples.EXAMPLES / "commands.typ").exists():
        raise Skip("typst is not on the path, or examples/ has no engine copy -- run build_examples.py")
    jobs = []
    for name, page in TABLE["commands"].items():
        for arg, spec in page["arguments"].items():
            for i, example in enumerate(spec["examples"]):
                for lang in pages.LANGS:
                    code = pages.tr(example["code"], lang)
                    if code.startswith("#") and (lang == "fr" or isinstance(example["code"], dict)):
                        jobs.append((name, arg, str(i), lang, example.get("context", ""), code))
    examples.VALUES_WORK.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=8) as pool:
        failed = [f"{job[0]}.{job[1]}.examples[{job[2]}] ({job[3]}): {error.splitlines()[0]}" for job, _png, error in pool.map(examples._compile_value, jobs) if error]
    assert not failed, "\n".join(failed)


def test_every_public_command_has_its_page_and_no_page_names_another():
    """REQ-004, REQ-013, the last step: every public command of build_reference.CATEGORIES has its condensed page -- no long page survives -- and the file holds no page of a command that is not public. Planted: `find` taken out is named."""
    public = [name for _key, members in ref.CATEGORIES for name in members]
    assert sorted(set(public) - set(TABLE["commands"])) == []
    assert sorted(set(TABLE["commands"]) - set(public)) == []
    planted = copy.deepcopy(TABLE)
    del planted["commands"]["find"]
    assert ("find", "no page in command-pages.json") in pages.gaps(public, planted)
