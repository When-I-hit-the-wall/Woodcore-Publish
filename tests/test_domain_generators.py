"""The domains Woodcore writes out as Typst files of their own, one generator per kind (spec docs/requirements/completed/2026-10-21-commandes-typst-refonte.md, REQ-017, ARCH-003, ARCH-011; calc/domains/unfold.py `GENERATORS`).

Each generator is held to the export it writes from: the file compiles, every value Python worked out is in its registry -- an `#eq` computing it again, or a literal checked by `domain:` and not stale --, the verdict holding as Python says. Once the `#show-*` and `#verify-*` are gone this is what holds Python and the report equal. The member checks have theirs in tests/test_unfold.py.
"""

TIER = "fast"  # tests/run_tests.py --fast

import json

import conftest
from conftest import Skip
from domains import unfold


def _need_typst():
    if not conftest.have_typst():
        raise Skip("typst is not on the path")


# --- steel checks (lot 10) ----------------------------------------------------------------------------------------------

def _steel(kind, cid, **fields):
    from domains import steel_check
    src = steel_check.new_source(cid, kind)
    src.update(profile={"type": "IPE", "dimension": "360"}, grade="S355")
    src.update(fields)
    record = steel_check.exported(steel_check.resolve(steel_check.check_source(src), {}))
    assert record["calculable"], (cid, record["reason"])
    return record


# every kind, and the branches that change the rows: (39) with a net area, (48) of an I and of a rolled RHS, (44) of a U, (43) beyond 0.5 V_Rd, a tube's note, the class with its table
STEEL_CASES = (
    ("tension", "S-TE", {"N": {"value": 1000, "unit": "kN"}, "A_net": 6000}),
    ("compression", "S-CO", {"N": {"value": -500, "unit": "kN"}, "profile": {"type": "HEB", "dimension": "200"}}),
    ("bending", "S-BE", {"M_y": {"value": 200, "unit": "kNm"}}),
    ("bending", "S-BN", {"N": {"value": -300, "unit": "kN"}, "M_y": {"value": 150, "unit": "kNm"}, "M_z": {"value": 10, "unit": "kNm"}}),
    ("bending", "S-BR", {"N": {"value": -100, "unit": "kN"}, "M_y": {"value": 20, "unit": "kNm"}, "M_z": {"value": 5, "unit": "kNm"}, "profile": {"type": "RRW", "dimension": "200x100x10"}}),
    ("bending", "S-BU", {"N": {"value": -100, "unit": "kN"}, "M_y": {"value": 30, "unit": "kNm"}, "profile": {"type": "UPE", "dimension": "200"}}),
    ("shear", "S-SH", {"V_z": {"value": 500, "unit": "kN"}, "M_y": {"value": 150, "unit": "kNm"}}),
    ("shear", "S-ST", {"V_z": {"value": 50, "unit": "kN"}, "profile": {"type": "ROR", "dimension": "101.6x10"}}),
    ("class", "S-CL", {"N": {"value": -500, "unit": "kN"}, "M_y": {"value": 100, "unit": "kNm"}}),
)


def _steel_state(records):
    """Each record of `records` written out into the session project and read back through Typst: {id: (text, {key or id: metadata})} -- data/steel.json carrying the records, as the export would."""
    import project
    from domains import steel_check
    _need_typst()
    here = conftest.PROJECT
    exported = here.data_dir / steel_check.EXPORT_FILE
    before = exported.read_bytes()
    data = {"schema_version": steel_check.EXPORT_SCHEMA_VERSION, "checks": {r["id"]: r for r in records}}
    steel_check.write(data, here.data_dir)
    out = {}
    folder = here.formulas_dir
    folder.mkdir(parents=True, exist_ok=True)
    try:
        for record in records:
            with project.using(here):
                text = unfold.generate(record, "de", "steel")
            path = folder / f"{record['id']}.typ"
            path.write_text(text, encoding="utf-8", newline="\n")
            try:
                entries, _ = unfold.query_state(here, path)
            finally:
                path.unlink()
            out[record["id"]] = (text, {e.get("key") or e.get("id") or "domain": e for e in entries})
    finally:
        exported.write_bytes(before)   # the session project's export as it was, for the tests after this one
    return out


def test_every_kind_of_steel_check_written_out_computes_what_the_export_holds():
    """REQ-017 (acier), ARCH-003: every kind of steel check and each branch that changes its rows is written out, compiles, and every var of the export is in its registry within 1e-6 -- each worked out an `#eq` where its formula computes it, the others literals checked against the export and never stale --, η in percent, the verdict the export's; its tables and notes printed, and no `#show-check-steel` left."""
    records = [_steel(kind, cid, **fields) for kind, cid, fields in STEEL_CASES]
    states = _steel_state(records)
    computed = 0
    for record in records:
        text, state = states[record["id"]]
        assert "#show-check-steel" not in text and text.startswith("#import") and f'#domain("{record["id"]}"' in text, text[:300]
        for key, var in record["vars"].items():
            got = state.get(key)
            assert got is not None, (record["id"], key, sorted(state))
            assert abs(got["value"] - var["value"]) <= 1e-6 * max(1, abs(var["value"])), (record["id"], key, got["value"], var["value"])
            assert not got.get("stale"), (record["id"], key, got)
            computed += got["kind"] == "eq"
        if record["eta"] is None:
            # the section's class is a classification with no verdict: no relation, no η
            assert "eta" not in state and not any(e["kind"] == "verify" for e in state.values()), record["id"]
        else:
            assert abs(state["eta"]["value"] / 100 - record["eta"]) <= 1e-6, (record["id"], state["eta"]["value"], record["eta"])
            verdict = next(e for e in state.values() if e["kind"] == "verify")
            assert verdict["holds"] == record["ok"], record["id"]
        for i, _table in enumerate(record.get("tables", []), 1):
            assert f"<{record['id']}-table-{i}>" in text, record["id"]
        for i, _note in enumerate(record.get("notes", []), 1):
            assert f"<{record['id']}-note-{i}>" in text, record["id"]
    assert computed >= 2 * len(records), "the resistances are computed again by #eq, not written as numbers"
    assert any(r.get("tables") for r in records) and any(r.get("notes") for r in records)


def test_a_steel_check_s_form_names_the_rows_it_computes():
    """REQ-012: a steel check's form changes with the rows a branch of SIA 263 gives -- a shear beyond 0.5 V_Rd adds M_V,Rd --, and not with a force alone; the generator's version is in it."""
    from domains import steel_check
    low = steel_check.form_of(_steel("shear", "F-1", V_z={"value": 100, "unit": "kN"}, M_y={"value": 150, "unit": "kNm"}))
    other = steel_check.form_of(_steel("shear", "F-2", V_z={"value": 120, "unit": "kN"}, M_y={"value": 150, "unit": "kNm"}))
    high = steel_check.form_of(_steel("shear", "F-3", V_z={"value": 500, "unit": "kN"}, M_y={"value": 150, "unit": "kNm"}))
    assert low == other and low != high and low["kind"] == "steel-shear" and low["version"] == unfold.GENERATOR_VERSION, (low, high)


def test_the_example_s_steel_checks_are_written_out_with_their_base_state_and_files():
    """REQ-017, ARCH-007, ARCH-008: the example project's steel checks are written out into Steel-checks/<Kind>/<id>.typ over their stubs, their base beside them, data/domain-state.json and data/domain-files.json listing them under `steel` -- what `domain-file("steel", id)` reads --, and the summary knows each as a steel check of its kind."""
    here = conftest.PROJECT
    files = json.loads((here.data_dir / unfold.FILES_FILE).read_text(encoding="utf-8"))["files"]
    state = json.loads((here.data_dir / unfold.STATE_FILE).read_text(encoding="utf-8"))["domains"]
    steel = json.loads((here.data_dir / "steel.json").read_text(encoding="utf-8"))["checks"]
    written = [cid for cid, record in steel.items() if record.get("calculable")]
    assert written and set(files.get("steel", {})) == set(written), files
    base = unfold.read_base(here, "steel")["domains"]
    for cid in written:
        path = here.typst_root / files["steel"][cid].lstrip("/")
        assert unfold.is_domain_file(path) and cid in base, cid
        assert state[cid]["kind"] == "steel" and state[cid]["check"] == "steel-" + steel[cid]["kind"] and state[cid]["matches"], state[cid]
    assert unfold.kind_of(here, written[0]) == "steel"


# --- loads (lot 11) -----------------------------------------------------------------------------------------------------

def test_every_load_of_the_example_written_out_computes_what_the_export_holds():
    """REQ-017 (charges), ARCH-003: every case of data/calculations.json -- the permanent loads, the snow, the wind and the live loads of SIA 261 Tabelle 8 -- is written out, compiles, and every var of the export is in its registry -- a number within 1e-6, a text as it is --, each worked out an `#eq` where its formula computes it, the others literals checked by `domain: (<kind>, id)` and never stale; its tables on labelled lines, no `#show-calc` left."""
    import project
    _need_typst()
    here = conftest.PROJECT
    calculations = json.loads((here.data_dir / "calculations.json").read_text(encoding="utf-8"))
    folder = here.formulas_dir
    folder.mkdir(parents=True, exist_ok=True)
    seen, computed = set(), 0
    for kind in unfold.LOAD_KINDS:
        for rid, record in sorted(unfold._module(kind).records(calculations).items()):
            seen.add(kind)
            with project.using(here):
                text = unfold.generate(record, "de", kind)
            assert "#show-calc" not in text and f'#domain("{rid}"' in text, text[:300]
            path = folder / f"{rid}.typ"   # query_state reads the domain named as its file
            path.write_text(text, encoding="utf-8", newline="\n")
            try:
                entries, _ = unfold.query_state(here, path)
            finally:
                path.unlink()
            state = {e.get("key") or e.get("id") or "domain": e for e in entries}
            for key, var in record["vars"].items():
                if var.get("value") is None:
                    continue
                got = state.get(key)
                assert got is not None, (kind, rid, key, sorted(state))
                if isinstance(var["value"], (int, float)):
                    assert abs(got["value"] - var["value"]) <= 1e-6 * max(1, abs(var["value"])), (kind, rid, key, got["value"], var["value"])
                else:
                    assert got["value"] == var["value"], (kind, rid, key, got["value"])
                assert not got.get("stale"), (kind, rid, key, got)
                computed += got["kind"] == "eq"
            for i, _table in enumerate(record.get("tables", []), 1):
                assert unfold._label(rid, f"table-{i}") in text, (kind, rid)
    assert seen == set(unfold.LOAD_KINDS), seen
    assert computed > 0, "the derived values are computed again by #eq"


def test_a_snow_load_made_in_its_tab_is_written_out_over_its_stub_and_kept_at_the_next_export():
    """REQ-017, ARCH-007, ARCH-008: the snow load `neige` made in the «Neige» tab is written out by the export into Variable-loads/Snow/neige.typ, its base beside it, listed by data/domain-files.json under `snow-load`; a second export leaves the file as it is and says no orphan of it; the new report's loads section includes it and compiles."""
    import subprocess
    import documents
    import export_all
    import project
    import project_template
    from domains import domain_file, snow_source
    _need_typst()
    here = project_template.create(conftest.tmpdir("generators_snow") / "Halle", "Halle")
    path = snow_source.folder(here) / "neige.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snow_source.new_source("neige"), indent=2) + "\n", encoding="utf-8")
    with project.using(here):
        export_all.run()
    written = here.root / "Variable-loads" / "Snow" / "neige.typ"
    text = written.read_text(encoding="utf-8")
    assert '#domain("neige"' in text and "#show-calc" not in text, text[:300]
    assert "neige" in unfold.read_base(here, "snow-load")["domains"]
    files = json.loads((here.data_dir / unfold.FILES_FILE).read_text(encoding="utf-8"))["files"]
    assert files["snow-load"]["neige"] == "/Variable-loads/Snow/neige.typ", files
    _archived, notes = domain_file.sync(here)
    assert not notes and written.read_text(encoding="utf-8") == text, notes
    # the report's loads section includes every case written out, `include domain-file("snow-load", case)` (lot 18): the new report prints it as it is
    loads = (here.document_dir("rs") / "Sections" / "004-einwirkungen.typ").read_text(encoding="utf-8")
    assert 'include domain-file("snow-load", case)' in loads, loads
    run = subprocess.run([project.typst_executable(), *documents.compile_args(here, "rs")], capture_output=True, text=True, encoding="utf-8", errors="replace")
    assert run.returncode == 0, run.stderr[-2000:]


# --- connectors (lot 12) ------------------------------------------------------------------------------------------------

def test_every_connector_of_the_example_written_out_computes_what_the_export_holds():
    """REQ-017 (connecteurs), ARCH-003: every connector the export calculated is written out -- its line as `#show-connector` printed it, its description, its figures, its resistance and its tables (k_beta's figures, the spacings with their math and their totals) --, compiles, and every var of the export is in its registry within 1e-6, R_d computed again by `#eq`, the others literals never stale."""
    import project
    _need_typst()
    here = conftest.PROJECT
    data = json.loads((here.data_dir / "connectors.json").read_text(encoding="utf-8"))
    records = unfold._module("connector").records(data)
    assert records
    folder = here.formulas_dir
    folder.mkdir(parents=True, exist_ok=True)
    for rid, record in sorted(records.items()):
        if not record.get("calculated"):
            continue
        with project.using(here):
            text = unfold.generate(record, "de", "connector")
        assert "#show-connector" not in text and f'#domain("{rid}"' in text and unfold._label(rid, "member") in text, text[:300]
        assert all(unfold._label(rid, f"table-{i}-title") in text for i in range(1, len(record.get("tables", [])) + 1)), rid
        path = folder / f"{rid}.typ"
        path.write_text(text, encoding="utf-8", newline="\n")
        try:
            entries, _ = unfold.query_state(here, path)
        finally:
            path.unlink()
        state = {e.get("key") or e.get("id") or "domain": e for e in entries}
        for key, var in record["vars"].items():
            got = state.get(key)
            assert got is not None, (rid, key, sorted(state))
            assert abs(got["value"] - var["value"]) <= 1e-6 * max(1, abs(var["value"])), (rid, key, got["value"], var["value"])
            assert not got.get("stale"), (rid, key, got)
        assert state["R_d"]["kind"] == "eq", "the resistance is computed again"


# --- polar moments (lot 13) ---------------------------------------------------------------------------------------------

def test_a_polar_moment_written_out_distributes_the_forces_as_python_does():
    """REQ-017 (moments polaires): the example's polar moment is written out -- its geometry checked against the export, N, V and M written for the engineer --, and once he gives them the file computes, by `#eq`, every fastener's force along x and z, its resultant and F_max as `connection.fastener_forces` does, within 1e-6; at 0 every force is 0."""
    import project
    from domains import connection
    _need_typst()
    here = conftest.PROJECT
    data = json.loads((here.data_dir / "connections.json").read_text(encoding="utf-8"))
    records = unfold._module("connection").records(data)
    rid, record = next((k, r) for k, r in sorted(records.items()) if r.get("calculated", True))
    with project.using(here):
        text = unfold.generate(record, "de", "connection")
    assert "#show-polar-moment" not in text and '#var("N", 0, "kN"' in text, text[:400]
    geometry = {"n": len(record["fasteners"]), "I_p": record["vars"]["I_p"]["value"], "center": (record["center"]["x"], record["center"]["z"]),
                "points": [(f["x"], f["z"]) for f in record["fasteners"]]}
    folder = here.formulas_dir
    folder.mkdir(parents=True, exist_ok=True)
    for N, V, M in ((0, 0, 0), (25, -12, 3.5)):
        given = text.replace('#var("N", 0, "kN"', f'#var("N", {N}, "kN"').replace('#var("V", 0, "kN"', f'#var("V", {V}, "kN"').replace('#var("M", 0, "kNm"', f'#var("M", {M}, "kNm"')
        path = folder / f"{rid}.typ"
        path.write_text(given, encoding="utf-8", newline="\n")
        try:
            entries, _ = unfold.query_state(here, path)
        finally:
            path.unlink()
        state = {e.get("key") or e.get("id") or "domain": e for e in entries}
        rows, _governing = connection.fastener_forces(geometry, record["directions"], N, V, M)
        for row in rows:
            i = row["nr"]
            for key, want in ((f"F_x_{i}", row["fx"]), (f"F_z_{i}", row["fz"]), (f"F_{i}", row["f"])):
                assert abs(state[key]["value"] - want) <= 1e-6 * max(1, abs(want)), (N, V, M, key, state[key]["value"], want)
        assert abs(state["F_max"]["value"] - max(r["f"] for r in rows)) <= 1e-6, (N, V, M)
        for key, var in record["vars"].items():
            assert not state[key].get("stale"), key


def test_a_polar_moment_written_out_draws_its_figure_from_its_forces():
    """Spec 2026-10-22-image-polar-moment, REQ-003, D-02: the file of a polar moment holds one figure, no longer at its head but right after N, V and M -- `#figure(image-polar-moment("<id>", N: "N", V: "V", M: "M", width: 60%), kind: image, caption: [...]) <id-polar-figure>`, a blank line on each side, its caption #show-polar-moment's --, and the arrows follow a value changed in the file: at 0 no fastener carries a force, with N = 7.5 each carries N/n along x. A group with no lever arm writes the call without `M:`."""
    import project
    import subprocess
    _need_typst()
    here = conftest.PROJECT
    data = json.loads((here.data_dir / "connections.json").read_text(encoding="utf-8"))
    records = unfold._module("connection").records(data)
    rid, record = next((k, r) for k, r in sorted(records.items()) if r.get("calculated", True))
    with project.using(here):
        text = unfold.generate(record, "de", "connection")
    lines = text.split("\n")
    figure = next(i for i, l in enumerate(lines) if "image-polar-moment" in l)
    assert text.count("#figure(") == 1 and f"<{rid}-figure>" not in text, text[:800]
    assert lines[figure] == (f'#figure(image-polar-moment("{rid}", N: "N", V: "V", M: "M", width: 60%), kind: image, caption: [Anschluss {rid}'
                             + (": " + record["label"] if record.get("label") else "") + f" – Verbindungsmittel und Kräfte je Verbindungsmittel]) <{rid}-polar-figure>"), lines[figure]
    assert lines[figure - 1] == "" and lines[figure + 1] == "" and lines[figure - 2].strip().startswith('#var("M", 0, "kNm"') and lines[figure + 2].strip().startswith('#eq("N_x"'), lines[figure - 2:figure + 3]
    folder = here.formulas_dir
    folder.mkdir(parents=True, exist_ok=True)
    n = len(record["fasteners"])
    for N, want in ((0, 0.0), (7.5, 7.5 / n)):
        path = folder / f"{rid}.typ"
        path.write_text(text.replace('#var("N", 0, "kN"', f'#var("N", {N}, "kN"'), encoding="utf-8", newline="\n")
        try:
            out = subprocess.run(["typst", "query", "--root", str(conftest.TYPST_ROOT), str(path), "<woodcore-polar-arrows>", "--field", "value", "--one"],
                                 capture_output=True, text=True, encoding="utf-8")
        finally:
            path.unlink()
        assert out.returncode == 0, out.stderr
        drawn = json.loads(out.stdout)
        assert abs(drawn["n-share"][0] - want) <= 1e-9 and all(abs(f["fx"] - want) <= 1e-9 and abs(f["fz"]) <= 1e-9 for f in drawn["forces"]), (N, drawn)
    flat = dict(record, vars=dict(record["vars"], I_p=dict(record["vars"]["I_p"], value=0)))
    with project.using(here):
        flat_text = unfold.generate(flat, "de", "connection")
    call = next(l for l in flat_text.split("\n") if "image-polar-moment" in l)
    assert f'image-polar-moment("{rid}", N: "N", V: "V", width: 60%)' in call and '#var("M"' not in flat_text, call
