"""The condensed page of a command as data, without Qt: what the commands tab and the website both show (calc/tools/command_page.py; spec 2026-10-24-onglet-commandes-pages, ARCH-001, ARCH-008, REQ-011, UI-003 to UI-007, UI-010).

The page is composed once, here, and turned into widgets by the tab and into HTML by the site: so its assertions are made on the data, in each language, and the module must not bring Qt with it.
"""

import sys

import conftest
from conftest import ROOT

sys.path.insert(0, str(ROOT / "calc" / "tools"))

import build_examples as examples  # noqa: E402
import build_reference as ref  # noqa: E402
import command_docs as docs  # noqa: E402
import command_page as page  # noqa: E402
import command_pages as pages  # noqa: E402
import command_usage as usage  # noqa: E402

TIER = "fast"

QT_FREE = "PySide6" not in sys.modules   # read before any test runs: the modules above, and nothing else, are imported
RECORDS = {r["name"]: {**r, **ref.parse_doc_block(r["doc_lines"])} for r in ref.lib_bindings(ROOT) if r["category"] != ref.INTERNAL}
TABLE = pages.pages()


def test_the_page_is_composed_without_qt():
    """ARCH-008: command_page, command_pages, command_usage and build_examples import no Qt, so the site's build can read them."""
    assert QT_FREE, "a module of the page model imports PySide6"


def test_the_line_of_var_is_the_prototype_s():
    """UI-003: the positional arguments first, then the named ones a line per group in the order of the table, each default read from the signature."""
    text = page.line_text(page.line(RECORDS["var"]))
    assert text == (
        "#var(key, symbol, value, unit,\n"
        "  domain: none,\n"
        "  display: auto, style: auto,\n"
        "  label: none, label-position: auto, descr: none, descr-position: auto,\n"
        "  norm: none, norm-section: none, norm-position: auto,\n"
        "  role: auto, id: none, level: auto\n"
        ")"), text
    segments = [s for row in page.line(RECORDS["var"]) for s in row]
    assert [s["arg"] for s in segments if s["kind"] == "arg" and s["required"]] == ["key"], "the required argument is marked, and only it"
    values = {s["arg"]: s["text"] for s in segments if s["kind"] == "value"}
    defaults = pages.signature_defaults(RECORDS["var"])
    assert all(values[name] == defaults[name] for name in values), values


def test_the_table_of_var_in_groups():
    """UI-005: the groups in their order with their words, a status and a default for each argument, two or three examples each, the names written by name last."""
    for lang in pages.LANGS:
        view = page.view(RECORDS["var"], lang)
        assert [g["key"] for g in view["groups"]] == ["pos", "show", "text", "cite", "other"]
        assert [g["label"] for g in view["groups"]] == [docs.word(f"group_{g}", lang) for g in ("pos", "show", "text", "cite", "other")]
        rows = {row["name"]: row for g in view["groups"] for row in g["rows"]}
        assert rows["key"]["required"] and rows["key"]["status"] == docs.word("required", lang) and rows["key"]["default"] is None
        assert rows["display"]["default"] == "auto" and rows["domain"]["default"] == "none"
        assert all(2 <= len(row["examples"]) <= 3 for row in rows.values()), [n for n, r in rows.items() if not 2 <= len(r["examples"]) <= 3]
        assert view["named"]["members"] == ["..rest", "name-calc", "name-visible", "norm-ref"]
        assert view["named"]["label"] == docs.word("group_named", lang)
        assert 3 <= len(view["keys"]) <= 4 and view["lead"] == TABLE["commands"]["var"]["lead"][lang]
        assert rows["label"]["text"] != rows["label-position"]["text"], "each argument says what it does itself"


def test_the_bubble_of_an_argument():
    """UI-006: its name, then on the same line «optionnel · par défaut auto» or «obligatoire», then its sentence, in the window's language."""
    bubble = page.argument_bubble(RECORDS["var"], "display", "fr")
    assert bubble == {"name": "display", "status": "optionnel · par défaut auto", "text": TABLE["commands"]["var"]["arguments"]["display"]["text"]["fr"]}
    assert page.argument_bubble(RECORDS["var"], "key", "de")["status"] == docs.word("required", "de")


def test_the_bubble_of_display_lists_every_value_with_its_call_and_print():
    """UI-007, `var.display`: every value with what it does, the default lit, each its call and where its print stands; `"none"` prints nothing and says so."""
    bubble = page.value_bubble(RECORDS["var"], "display", "fr")
    assert [v["value"] for v in bubble["values"]] == ["auto", '"none"', '"variable"', '"value"', '"value-unit"', '"variable-value-unit"']
    assert bubble["current"] == "auto"
    none = bubble["values"][1]["preview"]
    assert none["blank"] and none["rect"] is None and none["call"].endswith('display: "none")')
    shown = bubble["values"][2]["preview"]
    assert shown["state"] == "fresh" and shown["file"] == "fr-var.png" and len(shown["rect"]) == 3
    assert bubble["foot"] == docs.word("frozen", "fr")


def test_the_bubble_of_level_says_which_values_print_alike():
    """UI-007, `var.level`: `auto` prints what level 2 prints, and the bubble says so; level 0 prints nothing."""
    values = {v["value"]: v["preview"] for v in page.value_bubble(RECORDS["var"], "level", "en")["values"]}
    assert values["auto"]["same"] == ["2"] and values["auto"]["note"] == docs.word("same_as", "en", n="2")
    assert values["0"]["blank"]


def test_the_bubble_of_role_says_the_role_does_not_change_the_line():
    """UI-007, `var.role`: the role prints nothing of its own -- the bubble says what it is for instead of «the same as»."""
    for value in page.value_bubble(RECORDS["var"], "role", "de")["values"]:
        assert value["preview"]["note"] == docs.word("role_note", "de"), value


def test_the_bubble_of_a_free_text_gives_an_example():
    """UI-007, `var.label`: no list and no print, an example of a text instead."""
    bubble = page.value_bubble(RECORDS["var"], "label", "fr")
    assert bubble["values"] == [] and bubble["free"]["text"] == docs.word("free_text", "fr")
    assert bubble["free"]["example"].startswith("label: ")


def test_a_print_whose_call_changed_is_said_stale():
    """REQ-012: a call edited and not compiled again is never compiled behind the reader's back: the bubble says the print is stale."""
    import copy
    table = copy.deepcopy(TABLE)
    table["commands"]["var"]["arguments"]["display"]["values"][2]["call"] = '#var("M_d", 14.07, "kNm", display: "variable")'
    bubble = page.value_bubble(RECORDS["var"], "display", "fr", table)
    assert bubble["values"][2]["preview"]["state"] == "stale"


def test_the_search_reads_the_name_and_the_lead_alone():
    """REQ-011: a word of the lead finds the command in the window's language, a name of an argument alone finds nothing."""
    var = RECORDS["var"]
    assert page.matches(var, "var", "fr")
    assert page.matches(var, TABLE["commands"]["var"]["lead"]["fr"].split()[1], "fr")
    assert not page.matches(var, "label-position", "fr"), "an argument is not searched"
    assert not page.matches(var, "Notiert", "fr"), "the lead of another language is not searched"


def test_the_calls_of_a_command_in_a_project():
    """UI-010: the calls of #var in the example project, twelve at most, each with its file and its line -- and #var-table's are not #var's."""
    hits, total = usage.calls_in("var", conftest.SAMPLE.parent)
    assert hits and len(hits) <= usage.LIMIT and total >= len(hits)
    for file, line, text in hits:
        assert "#var(" in text.replace(" (", "("), text
        source = (conftest.SAMPLE.parent / file).read_text(encoding="utf-8").splitlines()[line - 1]
        assert source.strip().startswith(text.rstrip("…")[:40])
    assert usage.call_pattern("var").search("#var-table(role: auto)") is None


def test_an_example_whose_levels_print_alike_says_it():
    """REQ-008: an example of #distance prints the same page at levels 2 and 3 (LEVELS_CONFOUNDED), measured on its pages: the note says it, the buttons stay."""
    manifest = examples.index()
    assert examples.levels_same("distance", 0, manifest) == "23"
    assert page.levels_note("distance", 0, "fr", manifest) == docs.word("same23", "fr")
    assert page.shown_levels("distance", 0, (1, 2, 3), manifest) == (1, 2, 3)
