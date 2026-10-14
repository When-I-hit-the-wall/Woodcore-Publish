"""A script of the project: Python the engineer writes, run by Woodcore, whose named results the report reads (calc/domains/script.py, calc/domains/script_runner.py, calc/tools/python_tab.py; v0.100, docs/domain/scripts.md §3.3sexdecies).

These hold what the engineer's three answers settled: a result reaches the report as a **named value** (`result("x", 1.23, "kN")` exported into `data/scripts.json`), **numpy alone** is what a script computes with, and a script is **read-only on the project** -- it writes nothing but the results it declares.

⚠️ The write guard is checked here as what it is: a guard against an accident, not a sandbox. A script that reaches for `os.open` gets round it, which the module says out loud; what is held is that the common accident -- a stray `open(..., "w")` -- is refused and **names the file**.
"""

import json

import conftest

import project
import validation
from domains import script as model


def _folder():
    folder = model.sources_dir()
    folder.mkdir(parents=True, exist_ok=True)
    return folder


# What these checks have written into the session's project, so that _clear removes those and nothing else.
_WROTE = []


def _write(code, name="essai"):
    """One script of the session's project, remembered so the caller can remove exactly it."""
    path = _folder() / (name + model.SUFFIX)
    path.write_text(code, encoding="utf-8")
    _WROTE.append(path)
    return path


def _clear():
    """Removes what these checks wrote, and **only** that.

    ⚠️ It globbed the whole folder until v0.100 and so deleted the example project's own `dreigelenk.py` with it. That
    left the Python tab listing nothing, and `tests/test_window.py` requires every editor tab to list at least one row --
    so `test_window` failed in a **full** run and passed when run alone, since `test_script` sorts before it and never ran.
    A check that writes into the shared session project removes what it wrote, never what it found.
    """
    while _WROTE:
        _WROTE.pop().unlink(missing_ok=True)
    # and data/scripts.json back in step with the files that are left, since these checks export
    try:
        model.export()
    except Exception:                      # a defect in the export is the business of the checks that watch it
        pass


def test_a_script_says_what_it_is_in_its_own_comment_keys():
    """The identity is three `@` comment keys at the top of the file -- the convention an RFEM comment already uses (section 3.3duodecies) -- so the engineer edits it in the very pane he edits the code in, and there is no second place for it."""
    try:
        path = _write('# @name Portique\n# @label La resolution\n# @group Halle\nresult("x", 1.0, "kN")\n')
        source = model.read_source(path)
        assert (source["id"], source["name"], source["label"], source["group"]) == ("essai", "Portique", "La resolution", "Halle")
        # a key the file does not carry is "", never a reason to stop an export
        bare = model.read_source(_write('result("x", 1.0, "kN")\n', "nu"))
        assert (bare["name"], bare["label"], bare["group"]) == ("", "", "")
        # and the buffer reads exactly as the file does, so what the tab shows is what a save writes
        assert model.read_source_text(path.read_text(encoding="utf-8"), "essai") == source
    finally:
        _clear()


def test_a_script_name_is_its_id():
    """A script is addressed by its file name, so the name is kept to what an id may be -- the rule every other source of Woodcore follows."""
    for bad in ("a b", "a/b", "été?"):
        try:
            model.check_source({"id": bad})
        except model.ScriptError:
            pass
        else:
            raise AssertionError(f"{bad!r} was accepted as a script's name")
    assert model.check_source({"id": "portique-2.1"})["id"] == "portique-2.1"


def test_a_run_gives_back_its_results_its_variables_and_what_it_printed():
    """What the tab's three panes show. The variables are the inspector the engineer asked for -- «afin de ne pas avoir à lire le terminal» -- and a numpy array says how big it is, which is what one wants of it."""
    try:
        _write('''# @name Essai
import numpy as np
A = np.array([[2.0, 1.0], [1.0, 3.0]])
x, y = np.linalg.solve(A, np.array([8.0, 13.0]))
note = "solved"
print("hello")
result("x", x, "kN", label="First")
result("y", y, "kN")
''')
        report = model.run(_folder() / ("essai" + model.SUFFIX))
        assert report["ok"], report["reason"]
        assert [(r["name"], round(r["value"], 6), r["unit"]) for r in report["results"]] == [("x", 2.2, "kN"), ("y", 3.6, "kN")]
        assert report["results"][0]["label"] == "First"
        held = {item["name"]: item for item in report["variables"]}
        assert held["A"]["type"] == "ndarray(2, 2)", held["A"]
        assert held["note"]["value"] == "solved"
        assert "hello" in report["output"]
        assert report["seconds"] > 0
    finally:
        _clear()


def test_a_script_that_fails_is_a_warning_and_never_a_stop():
    """The v0.33 rule, applied to a sixth kind of source: one script must not stop the export of the others. Its record carries `calculated: false` and the reason, and the report refuses to print what it names."""
    try:
        _write('# @name Casse\nresult("a", 1 / 0, "kN")\n', "casse")
        _write('# @name Bon\nresult("b", 2.0, "kN")\n', "bon")
        records, notes = model.prepare()
        assert records["bon"]["calculated"] and records["bon"]["results"] == ["b"]
        assert not records["casse"]["calculated"]
        assert "ZeroDivisionError" in records["casse"]["reason"]
        assert [note.code for note in notes] == ["script_failed"]
        assert notes[0].args["script"] == "casse"
        # a syntax error is a reason too, and names the line
        _clear()
        _write('# @name Faute\nresult("a", =\n', "faute")
        records, _notes = model.prepare()
        assert not records["faute"]["calculated"] and "line 2" in records["faute"]["reason"]
    finally:
        _clear()


def test_a_script_declaring_nothing_is_not_calculated():
    """A script that runs through and declares no result has produced nothing the report can read, and says so rather than exporting an empty record the report would print as a value."""
    try:
        _write('# @name Rien\nx = 1 + 1\n', "rien")
        records, notes = model.prepare()
        assert not records["rien"]["calculated"]
        assert "result(" in records["rien"]["reason"], records["rien"]["reason"]
        assert notes and notes[0].code == "script_failed"
    finally:
        _clear()


def test_a_script_writes_nothing_but_the_results_it_declares():
    """⚠️ A guard and not a sandbox, which is what the module says of it: what is held is that the accident -- a stray `open(..., "w")` inside the project -- is refused and **names the file**, so the engineer reads a sentence rather than wondering."""
    try:
        target = project.current().root / "vole.txt"
        _write(f'# @name Ecrit\nopen(r"{target}", "w").write("nope")\nresult("b", 1.0, "kN")\n', "ecrit")
        report = model.run(_folder() / ("ecrit" + model.SUFFIX))
        assert not report["ok"]
        assert "vole.txt" in report["reason"] and "writes nothing but the results" in report["reason"]
        assert not target.exists(), "the guard let the write through"
        # reading is what a script is for, and is not refused
        _write('# @name Lit\nresult("n", float(len(list(DATA.glob("*.json")))), "")\n', "lit")
        read = model.run(_folder() / ("lit" + model.SUFFIX))
        assert read["ok"] and read["results"][0]["value"] >= 1
    finally:
        _clear()


def test_a_script_reads_a_value_of_the_export():
    """`value(domain, instance, name)` is what `var-of` reads in Typst, read in Python instead: it is how a script computes with the project's own loads rather than with numbers retyped into it (section 2 rule 1)."""
    try:
        calculations = json.loads((project.current().data_dir / "calculations.json").read_text(encoding="utf-8"))
        domain = next(key for key, held in calculations["domains"].items() if held["instances"])
        instance = next(iter(calculations["domains"][domain]["instances"]))
        name = calculations["domains"][domain]["instances"][instance]["results"][0]
        wanted = calculations["domains"][domain]["instances"][instance]["vars"][name]["value"]
        _write(f'# @name Lit\nresult("q", value({domain!r}, {instance!r}, {name!r}), "kN/m2")\n', "lit")
        report = model.run(_folder() / ("lit" + model.SUFFIX))
        assert report["ok"], report["reason"]
        assert report["results"][0]["value"] == wanted
        # and a name the export does not carry says what it does carry
        _write(f'# @name Faux\nresult("q", value({domain!r}, {instance!r}, "pas_la"), "")\n', "faux")
        missing = model.run(_folder() / ("faux" + model.SUFFIX))
        assert not missing["ok"] and "pas_la" in missing["reason"]
    finally:
        _clear()


def test_the_export_carries_the_shape_every_calculation_has():
    """Section 2 rule 2: a script's record is the `{vars, steps, checks, results}` shape, so `#val`, `#show-calc` and `#find` read it like any other -- `steps` and `checks` empty, a script declaring values and not a working. Its provenance names the file that produced it (rule 5)."""
    try:
        _write('# @name Portique\n# @label La resolution\nresult("H_d", 2.2, "kN", symbol=\'H_"d"\', label="Reaction", descr="Pourquoi")\n')
        out, _notes = model.export()
        data = json.loads(out.read_text(encoding="utf-8"))
        assert data["schema_version"] == model.SCHEMA_VERSION
        entry = data["scripts"]["essai"]
        assert entry["results"] == ["H_d"] and entry["steps"] == [] and entry["checks"] == []
        held = entry["vars"]["H_d"]
        assert held["value"] == 2.2 and held["unit"] == "kN" and held["symbol"] == 'H_"d"'
        assert held["label"] == "Reaction" and held["description"] == "Pourquoi"
        assert held["source"] == "python:scripts/essai.py"
        # the citation is always written, "" where the script names none: get-norm(v) is a field access in Typst
        assert held["norm"] == "" and held["norm_ref"] == ""
        # ⚠️ How long the run took is not exported: a wall-clock duration differs at every export, and data/ must stay
        # unchanged to the byte when nothing else changed (section 12) -- which exporting it broke.
        assert "seconds" not in entry, entry
        validation.validate_structure(data, "scripts")
        validation.validate_scripts_business(data)
    finally:
        _clear()


def test_the_business_rules_refuse_a_record_the_report_could_not_read():
    """Each fired on a record carrying the defect, since a rule that has never refused is a rule nobody has tested."""
    sound = {"schema_version": "1.0", "scripts": {"a": {
        "id": "a", "name": "A", "label": "", "group": "", "calculated": True, "reason": "",
        "vars": {"x": {"value": 1.0, "unit": "kN", "symbol": "x", "label": "", "level": 1,
                       "source": "python:scripts/a.py", "norm": "", "norm_ref": ""}},
        "steps": [], "checks": [], "results": ["x"]}}}
    validation.validate_scripts_business(sound)

    def refused(change, why):
        import copy
        data = copy.deepcopy(sound)
        change(data["scripts"]["a"])
        try:
            validation.validate_scripts_business(data)
        except validation.ValidationError:
            return
        raise AssertionError(why)

    refused(lambda e: e.update(id="b"), "an id that is not its key")
    refused(lambda e: e.update(results=["y"]), "a result it does not declare")
    refused(lambda e: e.update(calculated=False, reason=""), "not calculated and no reason")
    refused(lambda e: e.update(results=[]), "calculated with nothing to show")
    refused(lambda e: e["vars"]["x"].update(value="deux"), "a value that is not a number")
    refused(lambda e: e["vars"]["x"].update(source="excel:Book!A1"), "a source that is not its own file")
    refused(lambda e: e.update(steps=[{"name": "n"}]), "a step, which a script never has")


def test_a_script_that_will_not_stop_is_given_up_on():
    """A run is bounded: a bad loop is caught with its reason rather than waited out, and the export goes on."""
    try:
        _write("# @name Boucle\nwhile True:\n    pass\n", "boucle")
        report = model.run(_folder() / ("boucle" + model.SUFFIX), timeout=3)
        assert not report["ok"]
        assert "still running" in report["reason"] and "3" in report["reason"]
    finally:
        _clear()
