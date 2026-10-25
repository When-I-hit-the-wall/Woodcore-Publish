"""Single entry point for the whole data pipeline (docs/architecture/layout.md §11-12).

Reads the project's positions -- Woodcore's own positions.json since v0.114 (calc/positions_store.py), Positionen.xlsx until then -- the loads entered in Woodcore's tabs (Woodcore-Datei/loads/, one source per case, docs/domain/calculation-domains.md §3.3) -- and the connections and position plans saved in Woodcore's window (connections/<id>.json, section 3.3quinquies; plans/<id>.json, section 3.3sexies), builds the calculation domains, one descriptive record per element, one per connector, one record and figure per connection and one record, symbol drawing and background per plan, validates every artifact against schemas/ before writing, and fails loudly (non-zero exit) if anything doesn't validate. Typst is only ever compiled against data that passed here.

Loads come from no position file at all: they are entered and calculated in Woodcore's tabs of loads -- no load workbook is read since issue #109 (D-33) --, so the positions carry what the elements are and nothing else (docs/domain/loads.md §8).
"""

import json
import os
import shutil
import sys

import notifications

import engine
import journal
import positions_store
import project
import renumbering
from domains import quantities   # the plans' quantities by material and section (issue #9)
import validation
import variable_sources                            # the values a linked field follows, built from this export in memory (spec 2026-10-11-variables-liees-champs-et-textes)
from domains import annex, connection, connector, fire, plan, schema, section, statics
from domains import plan_documents                 # the documents the plans are drawn on, read again where replaced (issue #64)
from domains import member_check                   # the member checks: resolved here, calculated in the report (#show-check-member)
from domains import steel_check                    # the steel checks of the «Acier» tabs: resolved and computed here, printed by #show-check-steel (issues #50-#52)
from domains import unfold                         # the member checks printed unfolded as domains of the «Formules» tab (spec 2026-10-15-calculs-deplies-balises-figures-natives)
from domains import commands_migrate              # a section that still calls a command renamed or taken away stops the export, naming its replacement (spec 2026-10-19-base-saine-nettoyage, REQ-002)
from domains import loads_migrate                 # a file that still names a snow or wind value by its name before v0.120 stops the export, naming it (spec 2026-10-21-restes-issue-69, CON-002)
from domains import dependency_graph              # which object reads which, data/dependencies.json, and what a change touches (spec 2026-10-21-graphe-dependances, issue #71)
from domains import domain_file                    # one .typ per domain of a specialised tab, in a project laid out by folders (issue #64)
from domains import formula_domain                 # the calculation domains of the «Formules» tab: their index, data/formulas.json, which the «Variables» tab reads (v0.117, 2.0 by id since issue #15)
from domains import script as script_domain        # the `script` domain: one instance per script of the project
from i18n import strings
import registry
from registry import build_calculations
from build_reference import build_reference_workbook

# Every path this pipeline reads or writes is the project's, named by its .woodcore file (calc/project.py, v0.81): the sources Woodcore's window writes -- connectors/, connections/, plans/, statics/ and details/ (not `schemas/`, the contracts' own folder, docs/domain/detail-schemas.md §3.3decies) -- in its `sources`; and the export, data/, in its `generated`. No load workbook is read (issue #109): registry.py only names one found in the project's folder. Until v0.80 all of it was derived from this file's own location, which tied one copy of the code to one project.

# The version of a position record: 1.3 (v0.94) adds `section`, the dimension read once; 1.4 (v0.114) is the record of a position Woodcore keeps itself (calc/positions_store.py), every field but the id and the type blank where the Positions tab leaves it so, and a section that does not read written `null` with a warning rather than stopping the export.
POSITION_SCHEMA_VERSION = "1.4"
# 1.5 (issue #50): a section may be a free steel profile, `{type: "USR", kind: "user", id}` -- written only where a position's section is one, so that every other record stays byte for byte what 1.4 wrote (the lowest version that holds what a record carries, member_check.stamp_version's rule).
USER_POSITION_SCHEMA_VERSION = "1.5"


def _positions(rows):
    """Every position record, in the order of positions.json, checked -- nothing written yet -- and the warnings it gives: (records, notes).

    A position is a descriptive record and nothing more (docs/domain/positions.md §7-8): its fields as the Positions tab keeps them (calc/positions_store.py), carried through verbatim, and the section its `section_type` and `dimension` state, read once here (domains/section.py, v0.94) so that nothing downstream -- the report, #member, a schema element -- reads the text again. The moisture class is the one field read as a number, a condition the element is used in rather than a load on it. No span, no influence width, no load id -- `domains` stays empty until a mechanism that does not link a position to a load is settled on (docs/open-questions.md §14).

    ⚠️ **Only the id and the type stop the export** (v0.114, the engineer: Woodcore's tab is the one source of positions and a value left blank is never a blocking error). A section that does not read -- a type the list does not carry, a type with no dimension, a dimension that does not fit it -- is a warning naming the position, and the position is written with `section: null`, its dimension descriptive text; a moisture class that is not 1, 2 or 3 is a warning and left blank.
    """
    positions, notes = [], []
    for row in rows:
        row = positions_store.normalise(row)
        position_id = row["position"]
        where = f"position {position_id}"
        try:
            shape = section.parse(row["section_type"], row["dimension"], row["units"], where=where)
        except validation.ValidationError as exc:
            shape = None
            notes.append(engine.Note("position_section", f"{exc} -- {position_id} is exported without a section", position=position_id, error=str(exc)))
        if shape and shape.get("kind") == "user":
            # a free profile (issue #50): its file is read here -- a malformed one stops the export naming it, a missing one is a warning and the position keeps its section, the steel checks that read it saying they cannot
            from domains import profile as free_profile
            if free_profile.resolve(shape["id"]) is None:
                notes.append(engine.Note("position_profile_missing", f"{where}: section USR {shape['id']} -- Woodcore-Datei/profiles/ has no profile {shape['id']}; "
                                         f"draw it in the «Profilés» tab", position=position_id, profile=shape["id"]))
        if shape and shape.get("deduced"):
            notes.append(engine.Note("position_deduced", f"{where}: no section type -- its dimension {row['dimension']!r} is read as rec (b/h); "
                                     f"choose rec in its section type to say so", position=position_id, dimension=row["dimension"]))
        moisture = row["moisture_class"]
        if moisture is not None and (isinstance(moisture, bool) or moisture not in validation.moisture_classes()):
            notes.append(engine.Note("position_moisture", f"{where}: moisture class {moisture!r} is not "
                                     f"{', '.join(map(str, validation.moisture_classes()))} -- exported without one", position=position_id, value=str(moisture)))
            moisture = None
        position = {
            "schema_version": USER_POSITION_SCHEMA_VERSION if shape and shape.get("kind") == "user" else POSITION_SCHEMA_VERSION,
            "position": position_id,
            "type": row["type"],
            "material": row["material"],
            "strength_class": row["strength_class"],
            "section_type": row["section_type"],
            "dimension": row["dimension"],
            "units": row["units"],
            # the dimension read: {type, kind, text, and b/h, d, t, layers or dims in mm}, or None where the type is empty and the dimension is descriptive text, or where it does not read
            "section": shape,
            "moisture_class": moisture,
            "description": row["description"],
            "domains": {},
        }
        validation.validate_structure(position, "position")
        validation.validate_positions_business(position)
        positions.append(position)
    return positions, notes


def _warn(message):
    # Started by the window, a warning goes to it as a structured line -- its code and arguments kept, so the window writes it in its own language (notifications.emit, ARCH-008 of spec 2026-10-07-performance-erreurs-plans-legendes); run by hand, the sentence as it always was.
    if os.environ.get(notifications.STRUCTURED_ENV):
        notifications.emit(message, source="export")
        return
    print(f"export_all: WARNING {message}", file=sys.stderr)


def _sweep_positions(kept):
    """Removes the record of a position Positions Element no longer has.

    A position deleted or renamed in Excel would otherwise leave its data/positions/<id>.json behind, and #member("D001") would go on printing an element the project does not carry -- a ghost no one can see is gone, which is exactly the silently wrong page this pipeline exists to stop. The connections, the plans and the static models have swept their own stale files since they were written (connection.write, plan.write, statics.write); the positions were the one artifact that did not.

    Only files this exporter writes are touched: everything in data/positions/ is generated, and the folder is named by the project, never by the working directory.
    """
    folder = project.current().data_dir / "positions"
    if not folder.is_dir():
        return
    keep = set(kept)
    for stale in sorted(folder.glob("*.json")):
        if stale.stem not in keep:
            stale.unlink()
            _warn(
                f"removed data/positions/{stale.name}: '{stale.stem}' is no longer "
                f"a position of the project -- a report still calling "
                f"#member(\"{stale.stem}\") will now fail instead of printing it"
            )


def _sweep_retired(data_dir):
    """Removes what the export wrote for a feature Woodcore no longer has, and says so (v0.117).

    The RFEM import was retired in 0.117 (archive/rfem/): nothing writes `data/rfem.json` or `data/rfem/` any more, and a file no writer sweeps is a copy that ages without saying so -- the defect this pipeline fears most. Both are the export's own, generated and never edited, so they are removed rather than left behind; a project's RFEM-Export/ folder, which the engineer filled, is not touched.
    """
    for stale in (data_dir / "rfem.json", data_dir / "rfem"):
        if stale.is_dir():
            shutil.rmtree(stale)
        elif stale.is_file():
            stale.unlink()
        else:
            continue
        print(f"export_all: removed data/{stale.name}{'/' if stale.suffix == '' else ''} -- the RFEM import was retired in 0.117 (archive/rfem/)")


def run(update_engine=False, dry=False):
    here = project.current()
    data_dir = here.data_dir
    # The engine is copied into the project beside the export, and the two must not part: an export another version of the engine cannot read, or one that overwrites an engine edited by hand, is refused before anything is written, unless the engineer said to replace it (docs/architecture/layout.md §11, v0.82).
    state, detail = project.engine_state(here)
    # project.ASKED, the states sync_engine refuses without `update`: the export named `older` and `edited` and let `unknown` through, so it wrote data/ and then stopped at the engine, the two parted (v0.87)
    if state == "newer" or (state in project.ASKED and not update_engine):
        raise project.EngineDecision(state, project.engine_message(state, detail))
    # The glossary first, whatever the project holds: it was checked only when a figure asked it for a word, so a project with no figure exported a broken one without a word (docs/typst/language.md §4bis; periodic audit 260916).
    strings.check()
    # A section that still calls a report command renamed in v0.120 (`position-ids()`, `get-value(v)`, …) or taken away stops here, naming the file and what to write: the window rewrites them when the project is opened (commands_migrate.migrate), never the export, which writes data/ and nothing of the engineer's own (spec 2026-10-19-base-saine-nettoyage, ARCH-RISK-406).
    refused = commands_migrate.refusal(here)
    if refused:
        raise validation.ValidationError(refused)
    # So does a section, a script or a source that still names a value of a snow or wind sheet by its name before v0.120 (`q_k11` of a flat roof, `qk_max_bh`…): the window rewrites them when the project is opened (loads_migrate.migrate), and what cannot be rewritten safely is named here (spec 2026-10-21-restes-issue-69, CON-002, ARCH-RISK-805).
    refused = loads_migrate.refusal(here)
    if refused:
        raise validation.ValidationError(refused)
    # The positions are Woodcore's own since v0.114 (calc/positions_store.py): a project made before is given its positions.json here, its Positionen.xlsx imported and moved into its archives, so its first export is its migration too. A project with no position is exported with none -- never an error.
    # `woodcore-cli check` writes nothing, so it reads the workbook a migration would read, and moves nothing.
    if dry and not positions_store.path(here).exists() and positions_store.workbook(here).is_file():
        rows, notes = positions_store.import_workbook(here)
        for note in notes:
            _warn(note)
    else:
        migrated = positions_store.migrate(here)
        if migrated is not None:
            print(f"export_all: {migrated}")
            for note in getattr(migrated, "notes", ()):
                _warn(note)
        rows = positions_store.read(here)
    # A load workbook in the project folder is read no more (issue #109, D-33): found by its name alone, never opened, it is said at every full export -- its cases are entered in the tabs now, and a report must not lose them without the engineer knowing (REQ-003, UI-001). A tab's save (registry.export) says nothing.
    workbook_warning = registry.workbook_note(here.root)
    # `woodcore-cli check` writes nothing, so a data/calculations.json of an earlier Woodcore stays as it is: said, with its remedy (REQ-007, C-1) -- a full export replaces it, and never reads it against the schema
    old_export_warning = registry.old_export_note(data_dir) if dry else None

    # Everything is built and checked before anything is written, so an export that fails leaves data/ as it was.
    calculation_files = {}
    # the warnings of the load sources whose fields follow a variable: one gone keeps its last value (issue #42, D-06)
    load_link_warnings = []
    calculations = build_calculations(here, calculation_files, load_link_warnings)
    validation.validate_structure(calculations, "calculations")
    validation.validate_calculations_business(calculations)

    positions, position_warnings = _positions(rows)
    # Typst cannot list a directory, so which positions exist has to be exported explicitly for the report to loop over them all instead of naming each one by hand (Sections/003-baustoffe.typ). Same single source as the position files themselves -- positions.json, in its order -- so the two can never disagree.
    index = {"schema_version": "1.0", "positions": [p["position"] for p in positions]}
    # The positions deleted with their values kept («Copier les valeurs», issue #9, calc/renumbering.py): exported as positions, each carrying `archived` -- the id it had and the day it went --, so a call that still names «S110-old» prints the values it had and says so in orange; listed apart in the index, so that no list of the project's positions shows them. Each is a warning at every export, until nothing calls it any more and the engineer takes it out of positions-archive.json.
    archived_rows = renumbering.read_archive(here)
    archived, archived_warnings = _positions([{key: value for key, value in row.items() if key not in ("was", "deleted")} for row in archived_rows])
    for record, row in zip(archived, archived_rows):
        record["archived"] = {"was": row["was"], "deleted": row["deleted"]}
        validation.validate_structure(record, "position")
        position_warnings.append(engine.Note("position_archived", f"{record['position']}: the values of the former position {row['was']}, deleted on {row['deleted']} -- every call of it says so in the report",
                                             position=record["position"], was=row["was"], deleted=row["deleted"]))
    position_warnings += archived_warnings
    if archived:
        index["archived"] = [record["position"] for record in archived]
    validation.validate_structure(index, "positions-index")
    validation.validate_positions_index_business(index)

    # The detail schemas come FIRST since v0.74: a connector and a polar-moment calculation each name one and
    # read their pieces and their fastener coordinates off it, so one joint is drawn once (docs/domain/detail-schemas.md
    # §3.3decies). The sources are read once here and the same dictionary is handed to both consumers, so a
    # schema is parsed and checked once per export however many calculations are drawn on it, and all of them
    # see exactly the same geometry.
    details = schema.read_sources(here.details_dir)
    position_records = {p["position"]: p for p in positions + archived}
    # A schema element's `position` is checked against the positions just exported, the v0.33 pattern applied to a fourth editor (docs/decisions.md §13): unresolved, it warns rather than stops. Since v0.75 the records themselves are handed over and not their ids: an element's b and h follow its position's dimension, and its label reads «T001 C24 100/200».
    # The scripts of the project, run here as every other domain is recalculated at every export -- which is what keeps
    # the number in the report the number the current data gives (docs/architecture/principles.md §2 rule 1, 3.3sexdecies). One that
    # fails, is given up on or declares nothing is a warning and never a stop, and its record carries the reason.
    # Run before the connectors, the polar moments, the member checks and the static models since v0.117 (issue #42): a field of theirs may follow a script's variable (spec 2026-10-11-variables-liees-champs-et-textes, ARCH-005).
    script_reads = {}   # what each script read, for the graph of dependencies (spec 2026-10-21-graphe-dependances)
    script_records, script_warnings = script_domain.prepare(calculations=calculations, reads=script_reads)   # a script reads the calculations of this export, not the last one's (ARCH-RISK-804)
    # The calculation domains written in the «Formule» tab, one .typ each in the Typst root's Formules/ (calc/domains/formula_domain.py, v0.117): only their index is exported -- each file is its own source, and a section prints it with #include "/Formules/<id>.typ" where it lies (issue #15). One that cannot be read stops the export naming it; one written by hand in another form is a warning.
    formula_index, formula_warnings = formula_domain.prepare(here)
    # A value kept in step with `#sync` and written as a literal that no longer says what the export holds: said at its file and line, never overwritten -- the refresh is the engineer's (spec 2026-10-21-commandes-typst-refonte, ARCH-010, calc/typst_sync.py)
    import typst_sync
    formula_warnings += [engine.Note("sync_stale", f"{here.rel(path)}, line {line}: #sync({ident!r}) writes {content!r}, and the export holds {value!r} -- refresh the value, or take #sync away to keep it as it is",
                                     file=here.rel(path), line=line, id=ident, written=content, held=value)
                         for path, line, ident, content, value in typst_sync.check(here, calculations)]
    # What a connector and a polar moment may follow: the loads, the scripts and the «Formule» domains computed against these loads -- never a joint, a joint giving variables of its own (ARCH-005) --, from this export in memory and never from the last one on the disk (ARCH-RISK-003). A field whose variable is gone keeps its last value with a warning, never a stop (D-06).
    script_document = script_domain.document(script_records)
    joint_values = variable_sources.export_values(here, calculations, scripts=script_document, formulas=formula_index)
    # A connector's timber is a reference to a position -- its member's element names one -- resolved afresh here, so «Import données» is all it takes for a strength class changed in the workbook to reach the resistance (docs/domain/connectors.md §3.3nonies). One that no longer resolves is a warning: stopping would stop the positions' own export with it.
    connector_data, connector_figures, warnings = connector.prepare(here.connectors_dir, position_records, details, joint_values, place=engine.figures(data_dir, "connector"))
    # A polar moment names a schema and no connector since v0.76, so the connectors are not handed over.
    connections, figures, link_warnings = connection.prepare(here.connections_dir, details, position_records, joint_values, place=engine.figures(data_dir, "connection"))
    # Every variable a member check or a static model may follow: the joints' too, now that they are built.
    values = variable_sources.export_values(here, calculations, connections, connector_data, script_document, formula_index)
    # The schemas' records and figures, once every variable is built: a text placed on one prints a variable of the export (issue #43). Their sources were read above, before the joints that are drawn on them.
    schemas, schema_files, schema_warnings = schema.prepare(here.details_dir, position_records, values, place=engine.figures(data_dir, "details"))
    # A member check names a position and follows its strength class, section and moisture class unless it states them, resolved here against the positions just built -- the connector's reference pattern (domains/member_check.py). Nothing is computed: #show-check-member computes the check in the report. One the project cannot give a value for is exported `calculable: false` with its reason, never a stop.
    check_data = member_check.prepare(here, position_records, values)
    check_warnings = member_check.warnings_of(check_data)
    # A steel check follows a position's profile and grade unless it states them, as a member check does; it is computed here, once (spec 2026-10-12-section-acier D-09), and #show-check-steel prints what it holds. One the project cannot give a value for is exported `calculable: false` with its reason, never a stop.
    steel_data = steel_check.prepare(here, position_records, values)
    check_warnings = check_warnings + steel_check.warnings_of(steel_data)
    # A plan's labels are checked against the positions exported with it: one the Positions tab does not have is a warning, never a reason to stop the report (docs/domain/position-plans.md §3.3sexies).
    # A document still lying where the engineer keeps it is copied into its tab's Imported Plans/, and an annex's PDF into Appendix/ -- a project migrated before Woodcore copied them (issue #64, D-09, D-11); then a document written over in Imported Plans/ by a file of the same name is read again before the plans drawn on it are: its pages, its layers and its SHA-256 brought up to date. Not by `woodcore-cli check`, which writes nothing; nothing in a project laid out before
    if not dry:
        for record, made in plan_documents.adopt(here) + annex.adopt(here):
            print(f"export_all: {here.rel(record)} names {here.rel(made)} now" if made else f"export_all: {here.rel(record)} names its copy now")
    refreshed, refresh_notes = plan_documents.refresh_all(here) if not dry else ([], [])
    for docid in refreshed:
        print(f"export_all: the document {docid} was read again from its file")
    plans, plan_files, plan_warnings = plan.prepare(here.plans_dir, here.root, data_dir, index["positions"], values, positions_store.section_types(rows))
    plan_warnings = refresh_notes + plan_warnings
    # The quantities of what the position plans draw, by material and section (issue #9): measured here, with the plans' own lengths and the positions' sections, and printed by show-plan-quantities and sheet-quantities, which compute nothing again. A section is no plan of positions.
    plan_sources = plan.position_plan_sources(here.plans_dir)
    quantity_data, quantity_notes = quantities.document(plan_sources, rows)
    validation.validate_structure(quantity_data, "quantities")
    # The fire-protection plans, after the position plans they may follow: one that follows a position plan is set over that plan's own exported background, so it is handed the plans just built rather than reading the last export's off the disk (docs/domain/position-plans.md §3.3sexies; domains/fire.py). The documents a plan is drawn on live under the position plans' folder.
    fire_plans, fire_files, fire_warnings = fire.prepare(here.fire_dir, here.plans_dir, here.root, data_dir, plans["plans"], values)
    # A load drawn on a static model may name a var of the calculations instead of stating a number, so the figure follows the load by itself. It is resolved against the record just built above -- nothing is read back off disk -- and a name that is no longer there is a warning, never a stop (docs/domain/static-models.md §3.3octies).
    models, model_files, model_warnings = statics.prepare(here.statics_dir, values, place=engine.figures(data_dir, "statics"))
    # The report's revision journal, one file rather than a folder of them (calc/journal.py, docs/domain/journal.md §3.3terdecies): a project that has never been revised carries none, which is an empty journal and never an error. A project laid out in three documents has one per document, each printing its own (Project.journal_file_for), and each is exported beside the report's -- data/journal-cu.json and data/journal-bp.json, which their entry files read at every compile.
    journals, journal_warnings = {}, []
    for mode in here.modes:
        journals[mode], notes = journal.prepare(here.journal_file_for(mode))
        journal_warnings += notes
    journal_data = journals["rs"]
    # The documents the report draws on from outside and the excerpts it shows of them (docs/domain/annexes.md §3.3undevicies, v0.115): every excerpt found again in its source's current version -- by the bookmark it is anchored on -- and cropped to its frame here, since Typst cannot crop such a page itself. One that cannot be found is a warning here and a refusal in the report, which is where the engineer asked for it to stop.
    # an annex's PDF written over in Appendix/ by a file of the same name is read again first (issue #64, D-11) -- not by `woodcore-cli check`, which writes nothing
    _refreshed, annex_refresh_notes = annex.refresh_sources(here) if not dry else ([], [])
    annex_data, annex_files, annex_warnings = annex.prepare(here, annex.previous_export(data_dir))
    annex_warnings = annex_refresh_notes + annex_warnings
    # The graph of dependencies (spec 2026-10-21-graphe-dependances, issue #71): which object reads which, built from what was just built -- nothing computed again --, compared with the last export's, and what changed since said with what depends on it downstream, and a circle through objects of different kinds. Built before anything is written, and by `woodcore-cli check` too.
    previous_graph = dependency_graph.read(data_dir / dependency_graph.EXPORT_FILE)
    graph = dependency_graph.build(here, calculations, position_records, script_records, script_reads, formula_domain.list_domains(here),
                                   check_data, steel_data, connector_data, connections, schemas, plans, fire_plans, models, annex_data)
    validation.validate_structure(graph, dependency_graph.EXPORT_SCHEMA)
    graph_warnings = dependency_graph.notes(previous_graph, graph)
    # A key of the project file that names a feature Woodcore no longer has is read, ignored and said -- at every export, until the engineer takes it out (project.RETIRED_KEYS); the file is his and is not rewritten.
    for message in here.retired_keys() + [w for w in (workbook_warning, old_export_warning) if w] + load_link_warnings + position_warnings + quantity_notes + warnings + check_warnings + link_warnings + plan_warnings + fire_warnings + model_warnings + schema_warnings + journal_warnings + script_warnings + annex_warnings + formula_warnings + (graph_warnings if dry else []):
        _warn(message)

    # What produced this export, beside it: the project as its file describes it, the program's version and revision, Typst's (data/project.json, v0.82; the workbooks' digests until issue #109) -- what the one git repository proved until the code and the project came apart. Since v0.99 also the report's own latest revision, which the PDF's keywords name.
    info = project.record(here, revision=journal.latest(journal_data))
    validation.validate_structure(info, "project")
    validation.validate_structure(script_domain.document(script_records), "scripts")
    if dry:
        return  # `woodcore-cli check`: everything read, built and validated, nothing written

    # The file of a domain that is gone archived where it is an untouched stub of an earlier Woodcore, said where it is the engineer's (domains/domain_file.py, issue #64) -- every domain's own file is written out below (calc/domains/unfold.py); nothing in a project laid out before
    _archived, domain_notes = domain_file.sync(here)
    for message in domain_notes:
        _warn(message)
    # the workbook beside positions.json, never read (issue #64, D-24): written at every change of the positions, and here where it is missing -- a project unpacked, a workbook deleted
    if here.has_folders and not positions_store.workbook_path(here).is_file():
        positions_store.write_workbook(here)

    previous_calculations = engine.previous_json(data_dir / "calculations.json")
    engine.write_json(data_dir / "calculations.json", calculations)
    registry.write_files(calculation_files, data_dir, previous_calculations)
    _sweep_retired(data_dir)
    # The scripts beside them, keyed by their file name (docs/domain/scripts.md §3.3sexdecies).
    script_domain.write(script_records)
    for position in positions + archived:
        engine.write_json(data_dir / "positions" / f"{position['position']}.json", position)
    engine.write_json(data_dir / "positions-index.json", index)
    _sweep_positions(index["positions"] + index.get("archived", []))
    connector.write(connector_data, connector_figures, data_dir)
    member_check.write(check_data, data_dir)
    steel_check.write(steel_data, data_dir)
    # Before the domains are written out, which read each record back from data/; and before the reference workbook, which catalogues the connections' calls along with everything else.
    connection.write(connections, figures, data_dir)
    # A check printed unfolded gets its domain the first time it is exported, its file written from its record -- Timber-checks/<Kind>/<id>.typ laid out by folders, over its stub where the stub is Woodcore's own (issue #64, D-16), Formules/<id>.typ before (REQ-002) --, and the index of the domains is built again so that it lists it; a steel check too, into Steel-checks/<Kind>/<id>.typ (spec 2026-10-21-commandes-typst-refonte, REQ-017)
    unfold_notes = []
    for kind, data in [("check", check_data), ("steel", steel_data)] + [(kind, calculations) for kind in unfold.LOAD_KINDS] + [("connector", connector_data), ("connection", connections), ("script", script_domain.document(script_records))]:
        for rid in unfold.unfold_domains(here, kind, data, notes=unfold_notes):
            print(f"export_all: the {kind} {rid} written out into {here.rel(unfold.domain_path(here, rid, kind=kind))}")
    for message in unfold_notes:
        _warn(message)
    # what #show-check-member includes for a check printed unfolded: its file, where it holds the domain written out -- none where it is still a stub, or one the engineer wrote in, which is then printed folded (lib/timber.typ)
    if member_check.mark_unfolded_files(check_data, unfold.unfolded_files(here, check_data)):
        member_check.write(check_data, data_dir)
    # where each domain Woodcore wrote stands against its data, and its file (spec 2026-10-21-commandes-typst-refonte, REQ-012, ARCH-007, ARCH-008): what `#domain` prints in red at its head and what `domain-file(kind, id)` reads -- computed here, never by Typst
    for name, payload, contract in ((unfold.STATE_FILE, unfold.domain_state(here, check_data, steel=steel_data, calculations=calculations, connectors=connector_data, connections=connections, scripts=script_domain.document(script_records)), unfold.STATE_SCHEMA),
                                    (unfold.FILES_FILE, unfold.domain_files(here, check_data, steel_data, calculations, connector_data, connections, script_domain.document(script_records)), unfold.FILES_SCHEMA)):
        validation.validate_structure(payload, contract, where=f"data/{name}")
        engine.write_json(data_dir / name, payload)
    formula_index, _notes = formula_domain.prepare(here)
    # the graph built again now that the domains Woodcore writes out are on the disk (spec 2026-10-21-commandes-typst-refonte, REQ-017): built before, an export that writes one would draw another graph at the next export and say a change nobody made
    graph = dependency_graph.build(here, calculations, position_records, script_records, script_reads, formula_domain.list_domains(here),
                                   check_data, steel_data, connector_data, connections, schemas, plans, fire_plans, models, annex_data)
    validation.validate_structure(graph, dependency_graph.EXPORT_SCHEMA)
    for message in dependency_graph.notes(previous_graph, graph):
        _warn(message)
    plan.write(plans, plan_files, data_dir)
    engine.write_json(data_dir / "quantities.json", quantity_data)
    fire.write(fire_plans, fire_files, data_dir)
    statics.write(models, model_files, data_dir)
    schema.write(schemas, schema_files, data_dir)
    annex.write(annex_data, annex_files, data_dir)
    formula_domain.write(formula_index, data_dir)
    dependency_graph.write(graph, data_dir)
    for mode, data in journals.items():
        journal.write(data, data_dir, mode)
    write_project_info(here, info)
    # the engine beside the export, as one: after the data, so a failed export leaves the old pair together
    for name in project.sync_engine(here, update=update_engine):
        print(f"export_all: engine {name} written to {here.rel(here.generated_dir)}/")

    print(
        f"export_all: wrote calculations, {len(positions)} position(s), "
        f"{len(connector_data['connectors'])} connector(s), "
        f"{len(connections['connections'])} connection(s), "
        f"{len(plans['plans'])} plan(s), "
        f"{len(models['models'])} static model(s) and "
        f"{len(schemas['schemas'])} schema(s) to data/"
    )

    try:
        ref_path = build_reference_workbook(data_dir, here.docs_dir / "typst-reference.xlsx")
    except PermissionError as exc:
        _warn(
            f"could not write docs/typst-reference.xlsx (close it in Excel "
            f"and rerun to refresh it): {exc}"
        )
    else:
        print(f"export_all: wrote {ref_path.relative_to(here.generated_dir)}")


# --- data/project.json --------------------------------------------------------------------

def write_project_info(here, info):
    """data/project.json written: `info` (project.record) checked against its contract first, then written -- the one writer of the file, the export's and the «Projet» tab's (issue #87)."""
    validation.validate_structure(info, "project")
    engine.write_json(here.data_dir / "project.json", info)


def refresh_project_info(here):
    """The title page's fields of data/project.json brought into step with the project file at once, without an export (issue #87, the engineer: «une donnée modifiée est reportée tout de suite pour le prochain PDF»).

    Only the name and DETAILS are taken from the project file: what produced the last export -- Woodcore's and Typst's versions, the journal's revision -- is kept as that export wrote it, since nothing was exported now. No stamp is touched: data/project.json is an input of every document, so the next compile and the next export see a document changed, as they should. A file that is missing or does not hold to its contract is written as a new project's (project.record). Returns whether the file was written."""
    path = here.data_dir / "project.json"
    try:
        info = json.loads(path.read_text(encoding="utf-8"))
        validation.validate_structure(info, "project")
    except (OSError, ValueError, validation.ValidationError):
        info = None
    fresh = project.record(here) if info is None else {**info, "name": here.name, **project.details_of(here)}
    if info == fresh:
        return False
    write_project_info(here, fresh)
    return True


# --- the export a project starts with --------------------------------------------------

def seed(here=None):
    """Writes each file of data/ a report reads that is missing -- empty, and nowhere else (v0.86.1) -- and returns their names relative to data/.

    A new project had no data/ at all, and its report reads six files of it at every compile: project.json for the title page, positions-index.json, calculations.json, connectors.json, plans.json and statics.json for the loops of its sections. A full export needed a load workbook until v0.89.1, which a new project has not got, and the window's own saves each write one file: so Tinymist stopped on «file not found … data/project.json» until the office's workbook was copied in and exported. These are the export of a project that holds nothing yet -- no position, no load case, no drawing -- save the one thing nothing is entered for: the live loads of SIA 261 Tabelle 8, which every export carries. A file already there, written by an export or by a save in Woodcore's window, is never touched, so seeding a project twice, or a project already exported, writes nothing. A project laid out in three documents is seeded the journals of its two other documents as well, `journal-cu.json` and `journal-bp.json`, which their entry files read at every compile.
    """
    here = here or project.current()
    data_dir = here.data_dir
    # name in data/ -> (the contract it is checked against, what it holds): each built only where missing -- project.record asks git and Typst for their versions
    empty = {
        "project.json": ("project", lambda: project.record(here)),
        "calculations.json": ("calculations", lambda: build_calculations()),
        "domain-state.json": ("domain-state", lambda: unfold.empty_state()),   # spec 2026-10-21-commandes-typst-refonte, ARCH-007: what #domain reads
        "domain-files.json": ("domain-files", lambda: unfold.empty_files()),   # ARCH-008: what domain-file(kind, id) reads
        "positions-index.json": ("positions-index", lambda: {"schema_version": "1.0", "positions": []}),
        "quantities.json": ("quantities", lambda: {"schema_version": "1.0", "rows": [], "all": {"groups": [], "totals": []}, "plans": {}}),
        connector.EXPORT_FILE: ("connectors", lambda: {"schema_version": connector.EXPORT_SCHEMA_VERSION, "connectors": {}}),
        "connections.json": ("connections", lambda: {"schema_version": connection.EXPORT_SCHEMA_VERSION, "connections": {}}),
        "plans.json": ("plans", lambda: {"schema_version": plan.EXPORT_SCHEMA_VERSION, "plans": {}}),
        "statics.json": ("statics", lambda: {"schema_version": statics.EXPORT_SCHEMA_VERSION, "models": {}}),
        "schemas.json": ("schemas", lambda: {"schema_version": schema.EXPORT_SCHEMA_VERSION, "schemas": {}}),
        # The revision journal a new project's Sections/008-journal.typ reads: empty, since a project made this morning has not been revised (v0.99).
        journal.EXPORT_FILE: ("journal", lambda: {"schema_version": journal.EXPORT_SCHEMA_VERSION, "entries": []}),
        # The `script` domain, empty: a project with no script must still let `script-ids()` give an array and
        # `find-calculation` read the file rather than stop the compile on a missing one (v0.100).
        "scripts.json": ("scripts", lambda: script_domain.document({})),
        # The annexes, empty: a project with no annex must still let `extract-ids()` give an array and `show-annexes()` print nothing rather than stop the compile on a missing file (v0.115).
        annex.EXPORT_FILE: ("annexes", annex.empty),
        # The fire-protection plans, empty: a project that has drawn none must still let `fire-plan-ids()` give an array rather than stop the compile on a missing file.
        fire.EXPORT_FILE: ("fire", fire.empty),
        # The member checks, empty: a project with no check must still let `check-member-ids()` give an array rather than stop the compile on a missing file.
        member_check.EXPORT_FILE: ("checks", member_check.empty),
        # The steel checks, empty: a project with none must still let `check-steel-ids()` give an array rather than stop the compile on a missing file (issue #51).
        steel_check.EXPORT_FILE: ("steel", steel_check.empty),
        # The calculation domains of the «Formules» tab, none: a project with none must still let the «Variables» tab read an index rather than stop on a missing file (v0.117).
        formula_domain.EXPORT_FILE: ("formulas", formula_domain.empty),
        # The graph of dependencies, empty: what the «Dépendances» tab reads before a first export (spec 2026-10-21-graphe-dependances, D-07) -- Typst never reads it.
        dependency_graph.EXPORT_FILE: ("dependencies", dependency_graph.empty),
    }
    # A project laid out in three documents: the journals of the convention d'utilisation and of the base de projet too, empty -- each document prints its own, Typst cannot ask whether a file is there, and so a document's compile stops on a missing one (lib/calc-engine.typ, `journal-files`). A project laid out as a report alone has neither document, and is seeded exactly as it always was.
    if here.has_modes:
        for mode in ("cu", "bp"):
            empty[journal.EXPORT_FILES[mode]] = ("journal", lambda: {"schema_version": journal.EXPORT_SCHEMA_VERSION, "entries": []})
    missing = {}
    for name, (contract, build) in empty.items():
        if not (data_dir / name).is_file():
            data = build()
            validation.validate_structure(data, contract)
            missing[name] = data
    for name, data in missing.items():   # every one built and checked before the first is written
        engine.write_json(data_dir / name, data)
    # each document's journal, written once in raw Typst beside its entry file where it has none (spec 2026-10-21-commandes-typst-refonte, Q-008): what its journal section includes, `#include domain-file("journal", document)` -- listed in data/domain-files.json here, an export lists it again --, so the document compiles from the moment the project exists -- the templates carry none, the file being the project's (domains/list_files.py)
    from domains import list_files
    for mode in here.created_modes:   # a document not made yet has no journal: it is written as the document is made (project_template.create_document, issue #90)
        if not list_files.path(here, "journal", mode).is_file():
            list_files.write(here, "journal", mode)
    list_files.list_journals(here)
    return list(missing)


def main():
    try:
        # The project to export: `--project <file>.woodcore`, else the one project.current() finds (calc/project.py).
        named, rest = project.take_argument(sys.argv[1:])
        if named:
            project.use(named)
        run(update_engine="--update-engine" in rest)
    except (validation.ValidationError, engine.EngineError) as exc:
        # both are "the input is wrong", not a bug: report the message alone rather than a traceback, and never leave data/ half-written behind
        print(f"export failed: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
