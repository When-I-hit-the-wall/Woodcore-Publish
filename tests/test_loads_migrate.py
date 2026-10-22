"""A project's files taken to the names the snow and wind sheets give since v0.120 (spec 2026-10-21-restes-issue-69, CON-002, D-06, ARCH-RISK-801 to 805; calc/domains/loads_names.py, calc/domains/loads_migrate.py).

The renames are read off the export a project last wrote: tests/fixtures/calculations-before-loads.json is the example project's before v0.120 -- a flat roof `SL` (`q_k11`, `mu_11`, `lastmodell`, «Grosse Höhensprünge: Nein») and three wind sheets of Tableaux 31 and 59a. What is held, on a copy of the example project given that export:

* **the table**: a flat roof's `q_k11` is `q_k1`, `lastmodell` is `dachform`, «Nein» has no equivalent; the six global forces are named by the table's force coefficients, those of a table without one per area have none; an export already in the new names renames nothing;
* **every form a load value is named in** -- `var-of`, `value-of`, `show-input`, `val(…, domain:)`, `show-calc(…, shown:)`, a script's `value(…)`, a source's link `{domain, instance, var}` -- rewritten; a `#var("q_k11", …)` of the document's own left alone;
* **what cannot be rewritten safely is refused**, naming the file, the line or the field: a name with no equivalent, a value read by a name or an instance the section computes, a source that is not Woodcore's bytes;
* **the migration**: every file saved into the archives first -- a source outside the Typst root under its path in the project --, run once, the export refusing until it is, and `woodcore-cli loads migrate`.
"""

import json
import shutil

import conftest
from conftest import ROOT

import project
from domains import loads_migrate, loads_names

BEFORE = ROOT / "tests" / "fixtures" / "calculations-before-loads.json"


def _project(name):
    """A copy of the example project whose last export is the one before v0.120."""
    here = conftest.project_copy(name)
    shutil.copy2(BEFORE, here.data_dir / "calculations.json")
    return here


def test_the_renames_are_read_off_the_last_export():
    old = json.loads(BEFORE.read_text(encoding="utf-8"))
    flat = loads_names.renamed("snow-load", old["domains"]["snow-load"]["instances"]["SL"])
    assert flat == {"lastmodell": "dachform", "hoehenspruenge": None, "mu_11": "mu_1", "q_k11": "q_k1"}, flat
    velo = loads_names.renamed("wind-load", old["domains"]["wind-load"]["instances"]["WL-Velo"])
    assert velo["qk_max_bh"] == "qk_max_cf1" and velo["qk_min_db"] == "qk_min_cf3", velo
    assert loads_names.wind_forces("51") == {"bh": None, "dh": None, "db": "cf3"}, "Tableau 51's facades are b·h1 and d·h1: no equivalent; its roof d·b is cf3"
    assert loads_names.renamed("snow-load", {"vars": {"dachform": {"value": "Flachdach"}}}) == {}, "an export in the new names renames nothing"
    here = conftest.project_copy("loads_renames_new")
    with project.using(here):
        assert loads_migrate.renames(here) == {}, "the example's own export is in the new names"


def test_every_form_a_load_value_is_named_in_is_rewritten():
    table = {("snow-load", "SL"): {"q_k11": "q_k1", "mu_11": "mu_1", "lastmodell": "dachform", "hoehenspruenge": None},
             ("wind-load", "WL-Velo"): {"qk_max_bh": "qk_max_cf1"}}
    text = ('#val("q_k11", domain: ("snow-load", "SL"), level: 1)\n'
            '#show-calc("snow-load", "SL", level: -1, shown: (ce: 2, mu_11: 2, s_k: 3))\n'
            '#let q = var-of("snow-load", "SL", "q_k11") + value-of("wind-load", "WL-Velo", "qk_max_bh")\r\n'
            '#show-input("snow-load", "SL", "lastmodell", level: 3)\n'
            '#var("q_k11", "q_(k,11)", 1.729, "kN/m²")\n')
    after, notes, unresolved = loads_migrate.rewrite_typst(text, table)
    assert after == ('#val("q_k1", domain: ("snow-load", "SL"), level: 1)\n'
                     '#show-calc("snow-load", "SL", level: -1, shown: (ce: 2, mu_1: 2, s_k: 3))\n'
                     '#let q = var-of("snow-load", "SL", "q_k1") + value-of("wind-load", "WL-Velo", "qk_max_cf1")\r\n'
                     '#show-input("snow-load", "SL", "dachform", level: 3)\n'
                     '#var("q_k11", "q_(k,11)", 1.729, "kN/m²")\n'), after
    assert len(notes) == 5 and not unresolved, (notes, unresolved)
    script, notes, unresolved = loads_migrate.rewrite_python('q = value("snow-load", "SL", "q_k11")\n', table)
    assert script == 'q = value("snow-load", "SL", "q_k1")\n' and notes and not unresolved
    source = {"links": {"N": {"domain": "snow-load", "instance": "SL", "var": "q_k11", "factor": 1.5}},
              "loads": [{"magnitude": {"domain": "wind-load", "instance": "WL-Velo", "var": "qk_max_bh"}}],
              "texts": [{"text": "{1}", "vars": {"1": {"domain": "snow-load", "instance": "SL", "var": "mu_11", "show": "symbol"}}}]}
    notes, unresolved = loads_migrate.rewrite_json(source, table)
    assert source["links"]["N"]["var"] == "q_k1" and source["loads"][0]["magnitude"]["var"] == "qk_max_cf1" and not unresolved
    assert source["texts"][0]["vars"]["1"]["var"] == "mu_1" and len(notes) == 3, "a figure's text names its variables in `vars` (figure_text)"


def test_what_cannot_be_rewritten_safely_is_refused_naming_where():
    table = {("snow-load", "SL"): {"q_k11": "q_k1", "hoehenspruenge": None}}
    _after, _notes, unresolved = loads_migrate.rewrite_typst('#show-input("snow-load", "SL", "hoehenspruenge")\n', table)
    assert unresolved == [(1, "hoehenspruenge", "no equivalent in snow-load SL")], unresolved
    _after, _notes, unresolved = loads_migrate.rewrite_typst('\n#for n in ("h_ref", "q_k11") [ #var-of("snow-load", "SL", n) ]\n', table)
    assert [(line, name) for line, name, _why in unresolved] == [(2, "q_k11")], unresolved
    _after, _notes, unresolved = loads_migrate.rewrite_typst('#var-of("snow-load", sheet, "q_k11")\n', table)
    assert [name for _l, name, _w in unresolved] == ["q_k11"], unresolved
    _after, _notes, unresolved = loads_migrate.rewrite_python('v = value("snow-load", sheet, "q_k11")\n', table)
    assert [name for _l, name, _w in unresolved] == ["q_k11"], unresolved
    source = {"links": {"N": {"domain": "snow-load", "instance": "SL", "var": "hoehenspruenge"}}}
    notes, unresolved = loads_migrate.rewrite_json(source, table)
    assert not notes and unresolved == [("/links/N", "hoehenspruenge", "no equivalent in snow-load SL")], unresolved


def test_the_migration_saves_first_runs_once_and_the_export_waits_for_it():
    import cli
    here = _project("loads_migrate")
    section = here.typst_root / "Sections" / "loads-read.typ"   # the copy carries no report: a section of its own
    section.parent.mkdir(parents=True, exist_ok=True)
    section.write_text('#import "/000-Typst-Config/commands.typ": *\n#val("q_k11", domain: ("snow-load", "SL"))\n', encoding="utf-8", newline="\n")
    script = here.root / "Scripts" / "dreigelenk.py"
    script.write_text(script.read_text(encoding="utf-8") + 'q = value("snow-load", "SL", "q_k11")\n', encoding="utf-8", newline="\n")   # a script that reads a renamed value
    check = sorted(here.checks_dir.glob("*.json"))[0]
    src = json.loads(check.read_text(encoding="utf-8"))
    src["links"] = {"N": {"domain": "snow-load", "instance": "SL", "var": "q_k11"}}
    if src.get("schema_version") == "1.0":
        src["schema_version"] = "1.1"
    import engine
    engine.write_json(check, src)
    with project.using(here):
        refused = loads_migrate.refusal(here)
        assert refused and "open the project once in Woodcore" in refused, refused
        assert cli.main(["loads", "migrate", "--dry-run", "--project", str(here.file)]) == 0
        assert "q_k11" in section.read_text(encoding="utf-8"), "--dry-run writes nothing"
        changes = loads_migrate.migrate(here)
        rewritten = {here.rel(c.path) for c in changes}
        assert {here.rel(section), here.rel(script), here.rel(check)} <= rewritten, rewritten
        assert '#val("q_k1", domain: ("snow-load", "SL"))' in section.read_text(encoding="utf-8")
        assert json.loads(check.read_text(encoding="utf-8"))["links"]["N"]["var"] == "q_k1"
        assert 'value("snow-load", "SL", "q_k1")' in script.read_text(encoding="utf-8")
        # every file saved first, a source outside the Typst root under its path in the project
        archive = sorted(p for p in here.archives_dir.glob(loads_migrate.LABEL + "-*"))[-1]
        for change in changes:
            kept = archive / loads_migrate.commands_migrate._relative(here, change.path)
            assert kept.read_text(encoding="utf-8") == change.before, kept
        assert "q_k11 -> q_k1" in (archive / "notes.txt").read_text(encoding="utf-8")
        assert loads_migrate.migrate(here) == [] and loads_migrate.refusal(here) is None, "once"


def test_a_name_with_no_equivalent_stops_the_export_naming_the_file_and_the_line():
    import export_all
    import validation
    here = _project("loads_refused")
    section = here.typst_root / "Sections" / "loads-refused.typ"
    section.parent.mkdir(parents=True, exist_ok=True)
    section.write_text('#import "/000-Typst-Config/commands.typ": *\n\n#var("hoehenspruenge", domain: ("snow-load", "SL"))\n', encoding="utf-8", newline="\n")
    with project.using(here):
        loads_migrate.migrate(here)
        refused = loads_migrate.refusal(here)
        assert refused.startswith(here.rel(section) + " (line 3): 'hoehenspruenge'"), refused
        try:
            export_all.run(dry=True)
        except validation.ValidationError as exc:
            assert "hoehenspruenge" in str(exc), exc
        else:
            raise AssertionError("the export went on with a name that has no equivalent")
