"""What an RFEM import becomes in Woodcore: each structure a **static model**, written straight into the export.

The engineer's rule, and the one thing about this file that is a decision rather than a translation: the models an import makes go into **`data/statics.json`** and **never** into `Woodcore-Datei/statics/`. They are generated, regenerated at every import, and a model he drew by hand must not be overwritten by one a re-import produced. `statics.prepare(..., generated=…)` is where they join the drawn ones, and an id both claim is refused naming both.

**Only a structure somebody named becomes a model.** A structure's id is what a report addresses it by — `#show-static-model("VU-gunstig")` — and `member-24` is a placeholder, not a name. The unnamed ones are reported with the comment to write (`validation.structures_named`), which is the whole purpose of `@model`.

⚠️ **The frame needs no flip, and that is measured rather than assumed.** RFEM's global Z points **down** in this model (the API says so: «Z-axis: DOWN, gravity_sign=1»; node 1 is at z = 0 and node 2, 2.95 m above it, at z = −2.95), and a Woodcore static model is drawn x right and **z down** (docs/domain/static-models.md §3.3octies). So a coordinate is carried across as it is. A model set up the other way round would need its sign changed here, and nothing in the export says which way it is set up — so a structure whose supports come out above its loads is the sign to look at.

**What is translated, and what is refused rather than guessed:**

- **A node becomes a point**, a member a **bar**. RFEM's member type is its own localised word («Poutre», «Träger», «Beam»), so a type that is not one this module knows is carried as a bar **and reported** — a cable read as a bar is a system that carries compression it cannot, and guessing from a translated word is how that would happen silently.
- ⚠️ **An RFEM support is one definition applied to a set of nodes; a Woodcore support holds one point.** So one support is written per node of it that this structure holds — which is also why a support may appear in two structures (`structure_detection`).
- **A hinge is a release at one end of one member**, its degree of freedom read from the hinge definition's own stiffnesses — where `inf` means *not released*, the opposite of a support (`model_tables.Restraint`). A rotational spring keeps its stiffness, which only a moment release may carry.
- **A load becomes one load per member or node it acts on**, its `@be` becoming the load's own influence width, which is exactly what that key was for. RFEM's direction is a word like «ZL»; the axis is read out of it and anything else is **reported**.
- **Nothing is computed.** No reaction, no internal force, no check: a static model is a drawing (§3.3octies), and what the solver found is `results.py`'s and stays in the import's JSON.
"""

import engine
from i18n import strings
from domains import rfem as rfem_domain
from domains import statics_view
from rfem_import.structure_detection import ELEMENT_KINDS

# The three sliders every drawn model carries; an imported one is drawn at the same size as one drawn by hand.
STYLE = {"line": 1.0, "point": 1.0, "text": 1.0}

# What a load writes beside itself on the figure. Its name and its value, which is what an imported load has to say: where it came from and how big it is.
SHOW = "name+value"

# The member types RFEM writes for an ordinary beam, in the three languages this project has an export in. A type outside this is carried as a bar and reported -- never read as a cable or a spring, which would change what the system can carry.
BEAM_TYPES = ("poutre", "traeger", "trager", "beam", "girder", "balken")

# The load distributions RFEM writes for a constant load, likewise.
UNIFORM = ("uniforme", "konstant", "uniform", "constant")

# A Woodcore support holds a point and takes one of three types; an RFEM restraint may also be a spring or free.
SUPPORT_FROM = {"fixed": "fixed", "pinned": "pinned", "roller": "roller"}

# What a rotational spring's stiffness is stated in, as a static model states it.
ROTATIONAL_STIFFNESS_UNIT = "kNm/rad"

# A hinge's own kind, read into the degree of freedom a Woodcore release sets free.
RELEASE_FROM = {"moment": "moment", "shear": "shear", "normal": "normal", "rotational-spring": "moment"}


def _id(prefix, *parts):
    """An entity id of the shape `statics.ENTITY_ID` allows: a letter, then letters, digits and underscores."""
    return prefix + "_".join(str(part) for part in parts)


def _fold(text):
    from rfem_import.csv_tables import fold
    return fold(text)


def _case_part(case):
    """The load case's id as an entity id may carry it: its letters and digits, «CC1» -> «CC1».

    ⚠️ **A load's number is per load case**, so an id made of the number alone collides: this model has a load 4 on member 26 in two cases, and `statics.check_source` refused the pair by name -- which is what says the id has to carry the case.
    """
    return "".join(ch for ch in str(case or "") if ch.isalnum())


def _direction(word, where, problems):
    """RFEM's own load direction read into Woodcore's: «ZL», «Z» -> vertical; «XL», «X» -> horizontal.

    Anything else is reported and taken as vertical, which is what nearly every load on a timber structure is -- and reported so that the one that is not is looked at rather than drawn wrongly in silence.
    """
    folded = _fold(word)
    if folded.startswith("z"):
        return "vertical"
    if folded.startswith("x"):
        return "horizontal"
    problems.append(engine.Note(
        "rfem_import_direction",
        f"{where}: RFEM gives the load direction «{word}», which this import does not read -- drawn as vertical",
        where=where, value=word,
    ))
    return "vertical"


def _magnitude(load):
    """A load's magnitude as a static model states one: `{value, unit}`, or nothing where the export had none.

    ⚠️ **A value and never a reference.** A drawn model may name a var of `data/calculations.json` and follow it at every export (§3.3octies); an imported load's number is RFEM's own, and saying it came from the workbook would be false. What ties the two together is the `@load` key of the comment, which `validation.loads_resolve` checks and which a later version may turn into that reference.
    """
    if load.magnitude is None:
        return None
    return {"value": load.magnitude, "unit": load.unit or ""}


def _width(load):
    """The influence width the comment stated, as a static model states one. This is what `@be` was for."""
    width = load.meta.get("be")
    if width is None:
        return None
    stated = {"value": width, "shown": True}
    if load.meta.get("note"):
        stated["description"] = load.meta["note"]
    return stated


def _points(structure, model, problems):
    points, placed = [], {}
    for number in structure.nodes:
        node = model.node(number)
        if node is None or node.x is None or node.z is None:
            problems.append(engine.Note(
                "rfem_import_no_coordinates",
                f"Node {number} has no coordinates in the export -- the structure is drawn without it",
                where=f"Node {number}", number=number,
            ))
            continue
        pid = _id("P", number)
        points.append({"id": pid, "x": float(node.x), "z": float(node.z)})
        placed[number] = pid
    return points, placed


def _members(structure, model, placed, problems):
    members, drawn = [], {}
    by_number = {member.no: member for member in model.members}
    for number in structure.numbers("member"):
        member = by_number.get(number)
        if member is None or len(member.nodes) < 2:
            continue
        first, last = member.nodes[0], member.nodes[-1]
        if first not in placed or last not in placed or first == last:
            problems.append(engine.Note(
                "rfem_import_no_member",
                f"Member {number} joins nodes {first} and {last}, which the structure cannot be drawn between -- left out",
                where=f"Member {number}", number=number,
            ))
            continue
        if _fold(member.type) not in BEAM_TYPES:
            problems.append(engine.Note(
                "rfem_import_member_type",
                f"Member {number} is of RFEM's type «{member.type}», which this import does not read -- "
                f"drawn as a bar; a cable or a spring has to be drawn by hand",
                where=f"Member {number}", value=member.type,
            ))
        mid = _id("B", number)
        label = member.meta.get("position") or None
        entry = {"id": mid, "kind": "bar", "p1": placed[first], "p2": placed[last]}
        if label:
            entry["label"] = label
        members.append(entry)
        drawn[number] = mid
    return members, drawn


def _supports(structure, model, placed, problems):
    """One Woodcore support per node an RFEM support holds in this structure.

    ⚠️ An RFEM support is a definition applied to a set — this model's support 2 holds 23 nodes — so a set becomes as many supports as it has nodes here, and the same definition appears in every structure it reaches.
    """
    supports = []
    for support in model.supports:
        kind = SUPPORT_FROM.get(support.kind)
        for number in support.nodes:
            if number not in placed:
                continue
            where = f"Support {support.no}, node {number}"
            if kind is None:
                problems.append(engine.Note(
                    "rfem_import_support_kind",
                    f"{where} is «{support.kind}», which a static model has no symbol for -- left out; "
                    f"a spring is drawn by hand",
                    where=where, value=support.kind,
                ))
                continue
            supports.append({"id": _id("A", support.no, number), "point": placed[number], "type": kind})
    return supports


def _releases(structure, model, drawn, problems):
    """A release per hinged member end: the member's own `hinge_start`/`hinge_end` names the definition, and the definition says which freedom it sets free."""
    releases, by_number = [], {hinge.no: hinge for hinge in model.hinges}
    members = {member.no: member for member in model.members}
    for number, mid in sorted(drawn.items()):
        member = members[number]
        for end, named in (("start", member.hinge_start), ("end", member.hinge_end)):
            if not named:
                continue
            hinge = by_number.get(named)
            where = f"Member {number}, {end}"
            if hinge is None:
                problems.append(engine.Note(
                    "rfem_import_no_hinge",
                    f"{where} names hinge {named}, which the export does not hold -- left out",
                    where=where, number=named,
                ))
                continue
            dof = RELEASE_FROM.get(hinge.kind)
            if dof is None:
                continue                                    # «rigid»: nothing is released, so there is nothing to draw
            entry = {"id": _id("G", number, end[0]), "member": mid, "end": end, "dof": dof}
            if hinge.kind == "rotational-spring" and hinge.phi is not None:
                # {value, unit} and not a bare number, and only a moment release may carry one (statics.SPRING_UNITS). ⚠️ The fixture found this where the engineer's own export could not: his member 24 carries hinge 1, which is a plain moment release with no stiffness, so `statics.check_source` accepted the record -- the spring is on member 34, in a structure nobody has named.
                entry["stiffness"] = {"value": float(hinge.phi), "unit": ROTATIONAL_STIFFNESS_UNIT}
            releases.append(entry)
    return releases


def _loads(structure, model, placed, drawn, problems):
    """Every load of the structure, as a static model states them: a member load one line load per member, a nodal load one point load per node."""
    point_loads, line_loads = [], []
    for load in structure.loads:
        where = f"{load.case} {load.kind.replace('_', ' ')} {load.number}"
        record = model
        original = next((one for one in record.loads if one.kind == load.kind and one.no == load.number
                         and one.case == load.case), None)
        if original is None:
            continue
        direction = _direction(original.direction, where, problems)
        magnitude, width = _magnitude(original), _width(original)
        label = original.meta.get("load") or f"{load.case}"
        if original.kind.endswith("nodal_load") or (original.nodes and not original.members):
            for number in original.nodes:
                if number not in placed:
                    continue
                entry = {"id": _id("F", _case_part(load.case), load.number, number), "point": placed[number],
                         "direction": direction, "show": SHOW, "label": label}
                if magnitude:
                    entry["magnitude"] = magnitude
                if width:
                    entry["width"] = width
                point_loads.append(entry)
            continue
        if original.distribution and _fold(original.distribution) not in UNIFORM:
            problems.append(engine.Note(
                "rfem_import_distribution",
                f"{where} is distributed «{original.distribution}», which this import does not read -- "
                f"drawn as uniform; a triangular or trapezoidal load has to be drawn by hand",
                where=where, value=original.distribution,
            ))
        for number in original.members:
            if number not in drawn:
                continue
            entry = {"id": _id("q", _case_part(load.case), load.number, number), "member": drawn[number],
                     "shape": "uniform", "direction": direction, "show": SHOW, "label": label}
            if magnitude:
                entry["magnitude"] = magnitude
            if width:
                entry["width"] = width
            line_loads.append(entry)
    return point_loads, line_loads


def model_id(structure):
    """The id the static model of this structure takes: the slug of the name `@model` gave it.

    ⚠️ Made by `connection.id_from_name`, the one slug this project has (docs/domain/connections.md §3.3quinquies) — imported here and not at the top of the module, since that module reaches the whole domain chain and this one is meant to be readable from the import alone.
    """
    from domains.connection import id_from_name

    return id_from_name(structure.name or structure.key)


def source_of(structure, model, problems=None):
    """One structure as a `statics-source` record (schema 1.1) — what `statics.prepare(generated=…)` takes.

    Nothing is written; the record is returned, and `statics.check_source` is what says it is well formed. `problems` collects what could not be translated, each an `engine.Note`.
    """
    problems = problems if problems is not None else []
    points, placed = _points(structure, model, problems)
    members, drawn = _members(structure, model, placed, problems)
    point_loads, line_loads = _loads(structure, model, placed, drawn, problems)
    source = {
        "schema_version": "1.1",
        "id": model_id(structure),
        "name": structure.statics_name or structure.name or structure.key,
        "label": structure.statics_descr or structure.statics_name or "",
        "style": dict(STYLE),
        "points": points,
        "members": members,
        "supports": _supports(structure, model, placed, problems),
        "releases": _releases(structure, model, drawn, problems),
        "point_loads": point_loads,
        "line_loads": line_loads,
        "dimensions": [],
    }
    return source


def models_of(model, structures, named_only=True, problems=None):
    """The static models one import makes: one per structure, in the order the structures come.

    `named_only` leaves out a structure nobody named, which is the default and the rule: a model's id is what a report addresses it by, and «member-24» is a placeholder. The unnamed ones are reported by `validation.structures_named` rather than here, once each, so that a list of twenty-one is one list and not twenty-one repetitions.
    """
    problems = problems if problems is not None else []
    made = []
    for structure in structures:
        if named_only and not structure.named:
            continue
        source = source_of(structure, model, problems)
        # ⚠️ Kept beside the source rather than looked up again by id afterwards: an id is a *slug* of the
        # structure's name (`_refuse_duplicates`), so two names may give one id and a lookup would pick the
        # wrong structure to draw a diagram for.
        source["_structure"] = structure
        made.append(source)
    _refuse_duplicates(made, problems)
    return made


def _refuse_duplicates(made, problems):
    """Two structures whose names slug to one id: reported, and the second left out -- «Velo Unterstand» and «Velo-Unterstand» are one id and two structures."""
    seen = {}
    for source in list(made):
        if source["id"] in seen:
            problems.append(engine.Note(
                "rfem_import_id_taken",
                f"Two structures give the id «{source['id']}» -- «{seen[source['id']]}» and «{source['name']}»; "
                f"the second is left out, so give them names that differ by more than their punctuation",
                value=source["id"], first=seen[source["id"]], second=source["name"],
            ))
            made.remove(source)
            continue
        seen[source["id"]] = source["name"]


def prepare(here, position_records=None, calculations=None, read_results=False):
    """Every RFEM export the project names, read: `(sources, records, domain, warnings)`.

    The one entry point `export_all.py` calls. `sources` go to `statics.prepare(generated=…)`, `records` are the import's own JSON for `write` to put in `data/rfem/`, `domain` is the `rfem` domain's instances -- one per named structure, carrying what the solver found for its bars (`calc/domains/rfem.py`) -- and `warnings` are every note the reading, the detection, the validation and the translation produced.

    ⚠️ **The design situations' envelopes are read at every import**, which is the engineer's own decision and a measurement: RFEM's four result-combination tables cost about six seconds where the 48 combinations' own cost twelve for the forces alone. They are what the `rfem` domain and the report are made of; a single combination's distribution is read on demand instead, to draw its curve in the window.

    ⚠️ **`read_results` is off by default, and that is a measurement and not a preference**: reading the result sheets of one of the engineer's workbooks takes **105 s** -- 58 loadings, and 115 sheets that answer to a member-forces table -- against 1.1 s for the model tables alone. A normal export must not pay it, and the forces are not what a static model needs; `woodcore-cli import --results` is what asks for them, and then the import's JSON carries them.

    **Nothing is written here** — the split every other domain makes (`statics.prepare`/`write`), so that an export which fails leaves `data/` as it was. And **nothing refuses**: an export that is gone, or that cannot be read, is a warning naming it. An RFEM file the engineer has not synced yet must not stop the positions' own export.
    """
    from rfem_import import json_export, validation as rfem_validation
    from rfem_import.csv_tables import RfemCsvError
    from rfem_import.model_tables import read_model
    from rfem_import.structure_detection import detect

    records_by_id = dict(position_records or {})
    sources, records, warnings, gathered = [], {}, [], []
    # The engineer's own presentation of the models an import makes: which diagram is drawn over each, and the
    # size factors it is drawn at. The geometry stays RFEM's; only this is his (`domains/statics_view.py`).
    views, view_notes = statics_view.read_all(here.statics_dir)
    warnings += view_notes
    named = here.rfem_models()
    for name, path in zip(named, here.rfem_model_paths()):
        if not path.exists():
            warnings.append(engine.Note(
                "rfem_import_gone",
                f"The RFEM export «{name}» is not there -- its structures are left out of this export; "
                f"point at it again in Woodcore's «RFEM» tab, or take it off the list",
                where=name,
            ))
            continue
        try:
            model = read_model(path)
        except (RfemCsvError, OSError, ValueError) as exc:
            warnings.append(engine.Note(
                "rfem_import_unreadable",
                f"The RFEM export «{name}» could not be read -- {exc}",
                where=name,
            ))
            continue
        structures = detect(model.items(), combinations=model.combination_cases())
        problems = list(model.problems)
        problems += rfem_validation.problems(
            model, structures,
            known_positions=sorted(records_by_id),
            sections_of=_sections_of(records_by_id),
            instances=_instances_of(calculations),
        )
        made = models_of(model, structures, problems=problems)
        made = _presented(made, views, model, path, name, problems)
        # ⚠️ A duplicate id is refused **across** the exports too, and not only inside one: the engineer may name two exports of the same building -- this project names an .xlsx and a re-export of it -- and each would make «VU-gunstig». `statics.prepare` keys its models by id, so the second would have overwritten the first in silence, which is the very failure the check inside one export exists to stop.
        taken = {source["id"]: from_export for from_export, source in sources}
        for source in list(made):
            if source["id"] in taken:
                warnings.append(engine.Note(
                    "rfem_import_id_taken",
                    f"«{name}» makes the static model «{source['id']}», which «{taken[source['id']]}» makes too -- "
                    f"it is left out; two exports of one building are one model, so keep the one you read from",
                    value=source["id"], where=name, first=taken[source["id"]],
                ))
                made.remove(source)
        sources += [(name, source) for source in made]
        situations, situation_labels = _situations_of(model)
        envelopes, envelope_notes = _envelopes_of(path, name, situations)
        problems += envelope_notes
        gathered.append((name, model, structures, envelopes, situation_labels))
        results = None
        if read_results:
            results, notes = _results_of(path, name)
            problems += notes
        records[_record_name(name)] = json_export.build(
            model, structures,
            source={"path": name, "format": "csv" if path.is_dir() else "xlsx", "producer": "gui"},
            results=results,
            problems=problems,
        )
        warnings += problems
    labels = {}
    for _name, _model, _structures, _envelopes, situation_labels in gathered:
        labels.update(situation_labels)
    domain, domain_notes = rfem_domain.build(
        [(name, model, structures, envelopes) for name, model, structures, envelopes, _labels in gathered],
        situation_labels=labels,
    )
    warnings += domain_notes
    return [source for _from_export, source in sources], records, domain, warnings


def _situations_of(model):
    """The design situations this model's combinations name: `({"SP1", …}, {"SP1": "SP1 - ELU …"})`.

    Read off the combinations rather than off the sheet names, which is what keeps the envelope reading cheap:
    nothing in a sheet's *name* says whether its loading is a result combination, so without this every one of
    an export's 466 result sheets would be opened to find out (`envelopes.read_workbook_envelopes`).
    """
    from rfem_import.envelopes import situation_of

    ids, labels = set(), {}
    for combination in model.combinations:
        if not combination.situation:
            continue
        key = situation_of(combination.situation)[0]
        ids.add(key)
        labels.setdefault(key, combination.situation)
    return ids, labels


def _envelopes_of(path, name, situations):
    """The design situations' envelopes of one export, or `{}` with a note where they cannot be read.

    Never a refusal: an export calculated but exported without its result combinations is a model Woodcore can
    still draw, and the report then says the structure carries no result rather than failing to build.
    """
    from rfem_import.envelopes import read_export_envelopes

    if not situations:
        return {}, [engine.Note(
            "rfem_import_no_situation",
            f"«{name}» names no design situation, so no envelope is read -- its structures carry no result; "
            f"calculate the model in RFEM and export the tables again with its result combinations",
            where=name,
        )]
    try:
        found, problems = read_export_envelopes(path, situations)
    except Exception as exc:                                  # noqa: BLE001 -- an unreadable envelope must not stop the model's own import
        return {}, [engine.Note(
            "rfem_import_no_envelope",
            f"The design situations of «{name}» could not be read -- {exc}; its structures carry no result",
            where=name,
        )]
    if not found:
        problems = list(problems) + [engine.Note(
            "rfem_import_no_envelope_table",
            f"«{name}» carries no result-combination table -- its structures carry no result; in RFEM, tick "
            f"the design situations in Fichier -> Exporter -> Tableaux and export again",
            where=name,
        )]
    return found, list(problems)


def _presented(made, views, model, path, export, problems):
    """Each imported source with the engineer's own view applied: its size factors, and its diagram drawn.

    ⚠️ **The diagram is rendered here and nowhere else**, because here is the only place that has RFEM's own
    distribution along the members. `statics.prepare` takes the rendered SVG out into `data/statics/` and puts
    what it is -- the quantity, the loading -- into the record; nothing downstream reads an RFEM file.

    ⚠️ **A loading a view names and the export has not got is a note, never a refusal**: a combination deleted
    in RFEM, or a table not ticked at the export, must not stop the positions' own export. The model is then
    drawn as the bare system, which is what it looked like before the view existed.
    """
    from rfem_import import diagram_svg

    tables = {}
    out = []
    for source in made:
        structure = source.pop("_structure", None)
        view = views.get(source["id"])
        source = statics_view.apply_style(source, view)
        diagram = (view or {}).get("diagram")
        if diagram and structure is not None:
            loading = str(diagram["loading"]).strip()
            if loading not in tables:
                tables[loading] = _forces_of(path, export, loading, problems)
            table = tables[loading]
            if table is None:
                problems.append(engine.Note(
                    "rfem_import_no_loading",
                    f"«{export}» carries no internal forces for «{loading}», which the view of «{source['id']}» "
                    f"asks to draw -- the model is drawn as the bare system; tick that loading's table in "
                    f"Fichier -> Exporter -> Tableaux, or choose another in Woodcore's static models tab",
                    where=source["id"], value=loading,
                ))
            else:
                source["diagram"] = {
                    "quantity": diagram["quantity"],
                    "loading": loading,
                    "show": diagram.get("show", "value"),
                    "labels": diagram.get("labels", True),
                    "files": {
                        lang: diagram_svg.render(
                            model, structure, table=table, key=diagram["quantity"],
                            labels=diagram.get("labels", True), caption=None)
                        for lang in strings.LANGUAGES
                    },
                }
        out.append(source)
    return out


def _forces_of(path, export, loading, problems):
    """One loading's member forces, read on demand, or None with a note where they cannot be read."""
    from rfem_import.results import read_loading

    try:
        return read_loading(path, loading)
    except Exception as exc:                                  # noqa: BLE001 -- one unreadable sheet must not stop the import
        problems.append(engine.Note(
            "rfem_import_loading_unreadable",
            f"The forces of «{loading}» in «{export}» could not be read -- {exc}",
            where=export, value=loading,
        ))
        return None


def _results_of(path, name):
    """The Schnittgrössen the same export holds, where it holds any: the result sheets of a workbook, or the member-forces CSVs of a folder.

    ⚠️ **The two formats spell the forces differently** -- the CSV writes «V_y», the XLSX «Vy» -- which `results.FORCE_ALIASES` reads both of. Where the export carries no result table at all this is `None` and the JSON carries no `results` key, so «no results were exported» and «this model has no forces» stay two different things.
    """
    from rfem_import.results import read_results, read_workbook_results

    try:
        found = read_results(path) if path.is_dir() else read_workbook_results(path)
    except Exception as exc:                                  # noqa: BLE001 -- an unreadable result sheet must not stop the model's own import
        return None, [engine.Note(
            "rfem_import_no_results",
            f"The results of «{name}» could not be read -- {exc}; the model is imported without them",
            where=name,
        )]
    if not found.tables:
        return None, [engine.Note(
            "rfem_import_no_results",
            f"«{name}» carries no table of member internal forces -- the model is imported without results; "
            f"tick the internal forces in RFEM's export dialog to have them",
            where=name,
        )]
    return found, list(found.problems)


def write(records, data_dir):
    """Writes each import's JSON into `data/rfem/`, and sweeps the records of exports the project no longer names."""
    from rfem_import import json_export

    for name, record in sorted(records.items()):
        json_export.write(record, data_dir, name)
    return json_export.sweep(data_dir, records)


def _record_name(named):
    """The file name one export's record takes under `data/rfem/`: its own path, made into one word."""
    stem = str(named).replace("\\", "/").rsplit("/", 1)[-1]
    stem = stem[:-5] if stem.lower().endswith(".xlsx") else stem
    return "".join(ch if (ch.isalnum() or ch in "_.+-") else "_" for ch in stem) or "rfem"


def _sections_of(records_by_id):
    """A position's b and h in millimetres, out of the `section` its record carries (docs/domain/positions.md §7, v0.94).

    Only a section that states both -- a rectangle, or a round one whose d stands for both -- is compared: a plate, a CLT panel and a steel profile state no pair, and comparing one against RFEM's b/h would report a disagreement that is a difference of kind.
    """
    found = {}
    for name, record in records_by_id.items():
        section = (record or {}).get("section") or {}
        b, h = section.get("b"), section.get("h")
        if b is None and section.get("d") is not None:
            b = h = section["d"]
        if b is not None and h is not None:
            found[str(name)] = (float(b), float(h))
    return found


def _instances_of(calculations):
    """`{domain: [instance, …]}` out of a `calculations.json` record, for the `@load` check."""
    domains = (calculations or {}).get("domains") or {}
    return {domain: sorted((body.get("instances") or {}).keys()) for domain, body in domains.items()}


def counts(made):
    """What was made, for the line an import prints: `{"models": 1, "points": 7, "members": 6, …}`."""
    return {
        "models": len(made),
        "points": sum(len(source["points"]) for source in made),
        "members": sum(len(source["members"]) for source in made),
        "supports": sum(len(source["supports"]) for source in made),
        "releases": sum(len(source["releases"]) for source in made),
        "loads": sum(len(source["point_loads"]) + len(source["line_loads"]) for source in made),
    }
