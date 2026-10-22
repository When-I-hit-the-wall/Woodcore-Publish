"""`#sync(id)[content]`: the values Woodcore keeps in step inside a document written in raw Typst (spec docs/requirements/completed/2026-10-21-commandes-typst-refonte.md, REQ-011, ARCH-009, ARCH-010; calc/typst_sync.py, lib/calc-engine-core.typ `sync`).

The engineer, 20.10.2026: «les valeurs entre les balises peuvent être synchronisées. Si le user supprime une balise, alors cette valeur cesse d'être synchronisée». Held here: a content found by the lexer in a cell, a list and a sentence -- never in a comment, a string or a raw block --, rewritten without a byte changed outside its brackets; a content without its tag never rewritten; the ids `domain/instance/variable` and their escapes; a literal compared with the export and said when it differs, a reading of the export never; the sharing of a block between documents blind to a refreshed value; the number Woodcore writes the twin of `fmt-number`.
"""

TIER = "fast"  # tests/run_tests.py --fast

import json
import subprocess

import conftest
from conftest import ROOT, Skip

import sync as sharing_sync
import typst_sync as ts

TABLE = '''#table(columns: 3,
  [Nutzlast], [#sync("live-load/A1/category")[A1]], [#sync("live-load/A1/q_k")[$5 "kN"/"m"^2$]],
  [Büro], [B], [#sync("live-load/B/q_k")[3 kN/m²]],
)
// #sync("live-load/C/q_k")[not a sync: a comment]
#raw("#sync(\\"x/y/z\\")[in a string]")
```
#sync("a/b/c")[in a raw block]
```
- #sync("dead-load/D1/g_k")[1.2 kN/m²] in a list
'''


def test_a_sync_is_found_in_a_cell_a_list_and_a_sentence_and_nowhere_else():
    found = ts.syncs(TABLE)
    assert [s.id for s in found] == ["live-load/A1/category", "live-load/A1/q_k", "live-load/B/q_k", "dead-load/D1/g_k"], [s.id for s in found]
    assert [s.content for s in found] == ["A1", '$5 "kN"/"m"^2$', "3 kN/m²", "1.2 kN/m²"]
    assert [s.line for s in found] == [2, 2, 3, 10]


def test_a_content_is_rewritten_and_not_one_byte_outside_its_brackets():
    """REQ-011: «réécrit `#sync("A1.q_k")[$5 "kN"/"m"^2$]` sans toucher un octet hors des crochets»."""
    crlf = TABLE.replace("\n", "\r\n")
    after = ts.rewrite(crlf, {"live-load/A1/q_k": "4.5 kN/m²", "dead-load/D1/g_k": "1.3 kN/m²"})
    assert after == crlf.replace('$5 "kN"/"m"^2$', "4.5 kN/m²").replace("1.2 kN/m²", "1.3 kN/m²"), after
    assert ts.rewrite(crlf, {}) == crlf
    try:
        ts.rewrite(TABLE, {"live-load/Z/q_k": "1"})
    except ts.SyncError as exc:
        assert "live-load/Z/q_k" in str(exc)
    else:
        raise AssertionError("an id the file does not hold is refused")


def test_a_content_without_its_tag_is_never_rewritten():
    """Taking the tag away ends the keeping: the same value, written bare, is the engineer's."""
    untagged = TABLE.replace('#sync("live-load/B/q_k")[3 kN/m²]', "3 kN/m²")
    assert "live-load/B/q_k" not in [s.id for s in ts.syncs(untagged)]
    assert ts.rewrite(untagged, {"live-load/A1/category": "A2"}).count("3 kN/m²") == 1


def test_a_sync_that_cannot_be_read_is_refused_with_its_line():
    for text, said in (('#sync("a/b/c")', "no content"), ('#sync(1)[x]', "id first"), ('#sync("a/b/c")[x] #sync("a/b/c")[y]', "two #sync")):
        try:
            ts.syncs(text)
        except ts.SyncError as exc:
            assert said in str(exc) and "line 1" in str(exc), (text, str(exc))
        else:
            raise AssertionError(f"{text!r} is refused")


def test_an_id_names_a_value_of_the_export_its_parts_escaped():
    assert ts.split_id("live-load/A1/q_k") == ("live-load", "A1", "q_k")
    made = ts.make_id("dead-load", "EL+AL-Dach/West", "g_k")
    assert made == "dead-load/EL+AL-Dach\\/West/g_k" and ts.split_id(made) == ("dead-load", "EL+AL-Dach/West", "g_k")
    assert ts.split_id("one/two") is None


def test_a_literal_is_compared_with_the_export_and_a_reading_of_it_never_ages():
    """ARCH-010: a literal saying another value than the export is said; a content reading the export (`#var(…, domain:)`) prints the export's value at every compile and is never stale."""
    var = {"value": 3.0, "unit": "kN/m²"}
    assert not ts.stale("3 kN/m²", var) and not ts.stale("3.0 kN/m²", var)
    assert ts.stale("4 kN/m²", var)
    assert not ts.stale("2.9", {"value": 2.94, "unit": ""}), "a value written to fewer decimals agrees where the export rounds to it"
    assert not ts.stale('#var("q_k", domain: ("live-load", "A1"), display: "value-unit")', {"value": 99, "unit": ""})
    assert not ts.stale("A1", {"value": "A1", "unit": ""}) and ts.stale("A2", {"value": "A1", "unit": ""})


def test_the_export_names_every_stale_literal_with_its_file_and_line():
    here = conftest.project_copy("typst_sync_check", data=True)
    calculations = json.loads((here.data_dir / "calculations.json").read_text(encoding="utf-8"))
    domain = "live-load"
    instance, record = next(iter(calculations["domains"][domain]["instances"].items()))
    key, var = next((k, v) for k, v in record["vars"].items() if isinstance(v.get("value"), (int, float)))
    ident = ts.make_id(domain, instance, key)
    section = here.typst_root / "Sync.typ"
    section.write_text(f'= Lasten\n\n#sync("{ident}")[{ts.written(var["value"], var.get("unit") or "")}]\n\n#sync("{ident}x")[1]\n', encoding="utf-8")
    assert ts.check(here) == []
    section.write_text(f'= Lasten\n\n#sync("{ident}")[{var["value"] + 1}]\n', encoding="utf-8")
    found = ts.check(here)
    assert [(p.name, line, i) for p, line, i, _content, _value in found] == [("Sync.typ", 3, ident)], found


def test_the_number_woodcore_writes_is_the_one_the_report_prints():
    """ARCH-010: one formatter, held equal to `fmt-number` -- the decimals, the dropped zeros, the typographic minus."""
    if not conftest.have_typst():
        raise Skip("typst is not on the path")
    cases = [(1.729, "kN/m²"), (3.0, "kN/m²"), (-0.5, "kN"), (12.3456, "mm"), (1000, "")]
    d = conftest.probe_dir("typst_sync_number")
    probe = d / "probe.typ"
    probe.write_text('#import "/000-Typst-Config/commands.typ": *\n' + "".join(f'#fmt-number({v}, "{u}")\n\n' for v, u in cases), encoding="utf-8")
    out = subprocess.run(["typst", "compile", "--root", str(conftest.TYPST_ROOT), str(probe), str(d / "probe.pdf")], capture_output=True, text=True, encoding="utf-8")
    assert out.returncode == 0, out.stderr
    from pypdf import PdfReader
    printed = [line.strip() for line in PdfReader(str(d / "probe.pdf")).pages[0].extract_text().splitlines() if line.strip()]
    plain = lambda text: " ".join(text.replace(" ", " ").split())
    assert [plain(ts.written(v, u)) for v, u in cases] == [plain(x) for x in printed], (printed, [ts.written(v, u) for v, u in cases])


def test_a_refreshed_value_changes_no_state_of_a_block_shared_between_documents():
    """ARCH-009, ARCH-RISK-303: the sharing compares a block's parts with the content of their `#sync` left out -- a number Woodcore refreshed in one copy is no edit, and the copies stay in step."""
    a = '= Nutzlasten\n#sync("live-load/A1/q_k")[3 kN/m²]\n'
    b = '= Nutzlasten\n#sync("live-load/A1/q_k")[4 kN/m²]\n'
    assert sharing_sync.digest(ts.blanked(a)) == sharing_sync.digest(ts.blanked(b))
    assert sharing_sync.digest(ts.blanked(a.replace("Nutzlasten", "Lasten"))) != sharing_sync.digest(ts.blanked(a)), "an edit outside a sync is still one"
    assert ts.blanked("no sync here\n") == "no sync here\n"
