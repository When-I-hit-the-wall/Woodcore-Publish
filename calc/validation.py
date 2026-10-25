"""Structure/type/business validation against schemas/*.schema.json.

Implements the three validation levels required by docs/architecture/data-contracts.md §3.6. The structural/type check is a small hand-rolled recursive walker (our schemas only ever use type/properties/required/patternProperties/items, so pulling in the external `jsonschema` package would be overkill for this MWE). Business rules live in the validate_*_business functions below.
"""

import json
import re
from pathlib import Path

from i18n import strings

SCHEMA_DIR = Path(__file__).resolve().parent.parent / "schemas"


# What a table column may declare it holds (docs/domain/calculation-domains.md §3.3): Typst math source, the name of a var of the same instance, the one column that takes the leftover width, free text, a number. The display layer maps these to a width and a rendering, so an unknown kind would silently fall back to a plain cell.
TABLE_COLUMN_KINDS = {"math", "value", "wide", "text", "number"}

# Where a table sits relative to the values of its calculation: before them, as the working they come from (the dead load's layer build-up), or after them, as the answer they lead to (the wind load's global forces).
TABLE_PLACES = {"above", "below"}

# The kinds of action a load domain may declare (SIA 260): permanent (G) or variable (Q). A load combination picks its partial factors by this, so a misspelt one must stop the export rather than leave a load unclassified.
ACTIONS = {"permanent", "variable"}

# Where a domain's numbers come from (docs/domain/calculation-domains.md §3.3): Woodcore computed them from the cases entered in its tabs (`python`), or they are read from a norm table and computed by nobody (`norm`, the Nutzlasten of SIA 261 Tabelle 8, section 3.3septies). `excel`, a sheet of a load workbook, went with the workbooks' reading (issue #109, D-33).
ENGINES = {"python", "norm"}
NORM_ENGINE = "norm"



def moisture_classes():
    """The moisture classes a position may be given in the Positions Element sheet (Feuchteklasse, docs/domain/positions.md §7): SIA 265 Tabelle 3's, read from calc/norms/ and written nowhere here (v0.77). A timber calculation picks its factors by it, so anything else must stop the export rather than reach a calculation. Imported late: norms/sia265.py imports this module for its ValidationError."""
    from norms import sia265
    return sia265.moisture_class_ids()


def connector_species():
    """The species a connector member's timber may be: the rows of SIA 265 Tabelle 22, read from calc/norms/."""
    from norms import sia265
    return sia265.species_names()


class ValidationError(Exception):
    pass


def load_schema(name):
    path = SCHEMA_DIR / f"{name}.schema.json"
    with path.open(encoding="utf-8") as f:
        return json.load(f)


_TYPE_MAP = {
    "object": dict,
    "array": list,
    "string": str,
    "number": (int, float),
    # a whole number: a position's moisture class (docs/domain/positions.md §7)
    "integer": int,
    "boolean": bool,
    # a value a sheet may leave empty: a connector's diameter, its predrilling (docs/domain/connectors.md §7bis)
    "null": type(None),
}


def _check_type(value, expected, path):
    # a schema may list several accepted types, as a load var's `value` does: a number for a coefficient, a string for a text entry chosen from a list (docs/domain/loads.md §3.3bis)
    accepted = expected if isinstance(expected, list) else [expected]
    # a bool is an int to Python, and must not pass for a number
    if ("number" in accepted or "integer" in accepted) and isinstance(value, bool):
        raise ValidationError(f"{path}: expected {' or '.join(accepted)}, got boolean")
    py_types = ()
    for name in accepted:
        mapped = _TYPE_MAP.get(name)
        if mapped is not None:
            py_types += mapped if isinstance(mapped, tuple) else (mapped,)
    if py_types and not isinstance(value, py_types):
        raise ValidationError(
            f"{path}: expected {' or '.join(accepted)}, got {type(value).__name__}"
        )


def _older_remedy(path, value, allowed):
    """What to do with a file at a `schema_version` older than every one this code reads -- an export of an earlier Woodcore (issue #109: calculations.json at 1.8): «Import données» once writes it again. "" for any other field or version."""
    if not str(path).endswith("schema_version"):
        return ""

    def version(text):
        try:
            return tuple(int(p) for p in str(text).split("."))
        except ValueError:
            return None
    mine, known = version(value), [version(v) for v in allowed]
    if mine is None or None in known or not known or mine >= min(known):
        return ""
    return " -- written by an earlier version of Woodcore: run «Import données» (calc/export_all.py) once to write it again"


def _validate_node(value, schema, path):
    if "type" in schema:
        _check_type(value, schema["type"], path)
    # `const` and `enum` pin a field to the value(s) the code that writes it produces. They exist for one field: `schema_version` (docs/architecture/data-contracts.md §3.0, docs/architecture/principles.md §2 rule 8). Until v0.59 the walker ignored both, so the version was required to be present and never checked against anything -- a record written at an older shape passed as the current one and reached Typst, which reads the field nowhere at all. Now an export at the wrong version stops here, naming both.
    if "const" in schema and value != schema["const"]:
        raise ValidationError(
            f"{path}: is {value!r}, expected {schema['const']!r} -- the file was "
            f"written at another schema version than the one this code reads; "
            f"rerun calc/export_all.py to regenerate it"
        )
    if "enum" in schema and value not in schema["enum"]:
        allowed = ", ".join(repr(v) for v in schema["enum"])
        raise ValidationError(
            f"{path}: is {value!r}, expected one of {allowed}" + _older_remedy(path, value, schema["enum"])
        )
    declared = schema.get("type")
    accepted = declared if isinstance(declared, list) else [declared]

    if "object" in accepted and isinstance(value, dict):
        for key in schema.get("required", []):
            if key not in value:
                raise ValidationError(f"{path}: missing required field '{key}'")

        properties = schema.get("properties", {})
        for key, sub_schema in properties.items():
            if key in value:
                _validate_node(value[key], sub_schema, f"{path}.{key}")

        pattern_props = schema.get("patternProperties")
        if pattern_props:
            # our schemas only ever declare one catch-all pattern per object
            sub_schema = next(iter(pattern_props.values()))
            for key, item in value.items():
                if key in properties:
                    continue
                _validate_node(item, sub_schema, f"{path}.{key}")

    if "array" in accepted and isinstance(value, list):
        item_schema = schema.get("items")
        if item_schema:
            for i, item in enumerate(value):
                _validate_node(item, item_schema, f"{path}[{i}]")


def validate_structure(data, schema_name, where=None):
    """Raises ValidationError where `data` does not fit `schemas/<schema_name>.schema.json`, naming the field by its path -- rooted at `where` where it is given (a file's name: `sync.json.blocks.intro.text`), else at the schema's name."""
    schema = load_schema(schema_name)
    _validate_node(data, schema, where or schema_name)


def _check_choices(v, path):
    choices = v.get("choices")
    if choices is not None and v["value"] not in [c["value"] for c in choices]:
        allowed = ", ".join(str(c["value"]) for c in choices)
        raise ValidationError(f"{path}: value {v['value']} not in allowed choices ({allowed})")


def _check_calculation(data, path):
    """The business rules every {vars, steps, checks} record obeys, wherever it lives -- one domain of a position (docs/architecture/data-contracts.md §3.1) or one instance of a calculation domain (section 3.3). Both shapes are the same record, so both are checked here rather than in two places that could drift apart.
    """
    var_names = set(data.get("vars", {}).keys())
    for name, v in data.get("vars", {}).items():
        if not isinstance(v["unit"], str):
            raise ValidationError(f"{path}.{name}: unit must be a string")
        _check_choices(v, f"{path}.{name}")
    for st in data.get("steps", []):
        if st["result"] not in var_names:
            raise ValidationError(
                f"{path}: step '{st['name']}' result '{st['result']}' is not a "
                f"declared var"
            )
        for u in st["uses"]:
            if u not in var_names:
                raise ValidationError(
                    f"{path}: step '{st['name']}' uses unknown var '{u}'"
                )
    for c in data.get("checks", []):
        if c["eta"] < 0:
            raise ValidationError(f"{path}: check '{c['name']}' has negative eta")


def validate_positions_business(position):
    if not position["type"]:
        raise ValidationError(f"{position['position']}: type must not be empty")
    # everything but the id and the type is facultative (a position that has none to state leaves it blank; #member's line drops it) -- the dimension since v0.87, every field since v0.114, when Woodcore's Positions tab became the one source of positions; what they state is read once, into `section`, by domains/section.py, and a section that does not read is exported null with a warning (export_all._positions), so only a section that is there is checked here
    shape = position.get("section")
    if shape is not None:
        from domains import section  # late: domains/section.py imports this module for its ValidationError
        if shape["type"] not in section.CODES or shape["kind"] != section.kind_of(shape["type"]):
            raise ValidationError(
                f"{position['position']}: section is a {shape['kind']} {shape['type']!r} -- expected one of {', '.join(section.CODES)}")
    # the moisture class is facultative, a position that is not timber having none (a concrete wall, a support), but one that is given is one of the norm's three
    moisture = position.get("moisture_class")
    if moisture is not None and (isinstance(moisture, bool) or moisture not in moisture_classes()):
        raise ValidationError(
            f"{position['position']}: moisture_class is {moisture!r} -- expected "
            f"{', '.join(map(str, moisture_classes()))} or none"
        )

    for domain_name, domain in position.get("domains", {}).items():
        _check_calculation(domain, f"{position['position']}.{domain_name}")


def validate_positions_index_business(index):
    seen = set()
    for position_id in index["positions"]:
        if not position_id:
            raise ValidationError("positions-index: empty position id")
        if position_id in seen:
            # two Positions rows with the same id would silently overwrite each other's data/positions/<id>.json
            raise ValidationError(f"positions-index: duplicate position id '{position_id}'")
        seen.add(position_id)


def validate_scripts_business(data):
    """data/scripts.json: a script that says it was calculated produced something, one that did not says why, and every name it calls a result is a var it declared (docs/domain/scripts.md §3.3sexdecies).

    A script is the engineer's own Python, so what is checked here is the *record*, never the code: whether the export can be read back consistently by the display layer. The code says what is wrong with itself when it is run, and that reason is carried rather than raised -- one script must not stop the export of the others.
    """
    for key, entry in data["scripts"].items():
        where = f"scripts.{key}"
        if entry["id"] != key:
            raise ValidationError(f"{where}: keyed {key!r} and carries id {entry['id']!r} -- a script's id is its key")
        if entry["calculated"]:
            if not entry["results"]:
                raise ValidationError(f"{where}: calculated with no result -- a script that produced nothing is not calculated")
        elif not entry["reason"].strip():
            raise ValidationError(f"{where}: not calculated and gives no reason -- the report prints the reason in place of the value")
        for name in entry["results"]:
            if name not in entry["vars"]:
                raise ValidationError(f"{where}: names {name!r} among its results and declares no such var")
        for name, held in entry["vars"].items():
            if isinstance(held["value"], bool) or not isinstance(held["value"], (int, float)):
                raise ValidationError(f"{where}.{name}: a result is a number, not {type(held['value']).__name__}")
            if not held["source"].startswith("python:"):
                raise ValidationError(f"{where}.{name}: a script's result is produced by its own file, so its source says so -- got {held['source']!r}")
        if entry["steps"] or entry["checks"]:
            raise ValidationError(f"{where}: a script declares values and carries no step and no check")


def validate_checks_business(data):
    """data/checks.json: every member check keyed by its own id, one that can be calculated carrying what #show-check-member hands to #member and the verify-* of its kind -- a strength class, a rectangular or round section, a moisture class, a positive force (a bending's signed), for a compression at an angle its contact, and for a bending a moment -- and one that cannot carrying its reason (calc/domains/member_check.py, docs/domain/member-checks.md §3.3undecies).

    What is checked is that the record and the report agree: a check exported as calculable that the report would then refuse on a missing value is the silently wrong page this pipeline exists to stop, only the other way round.
    """
    for key, entry in data["checks"].items():
        where = f"checks.{key}"
        if entry["id"] != key:
            raise ValidationError(f"{where}: keyed {key!r} and carries id {entry['id']!r} -- a check's id is its key")
        if not entry["calculable"]:
            if not entry["reason"].strip():
                raise ValidationError(f"{where}: not calculable and gives no reason -- the report prints the reason in place of the check")
            continue
        if entry["reason"]:
            raise ValidationError(f"{where}: calculable and carries a reason {entry['reason']!r}")
        # a strength class of SIA 265, or a material of the library the export froze the resistance of (issue #112, ARCH-008)
        if not (entry["grade"] or entry.get("resistance")) or entry["section"] is None or entry["moisture_class"] is None:
            raise ValidationError(f"{where}: calculable with no strength class, section or moisture class")
        if entry["moisture_class"] not in moisture_classes():
            raise ValidationError(f"{where}: moisture class {entry['moisture_class']!r}")
        # a bending's and a lateral torsional buckling's N is signed, tension positive and 0 for none (v0.117); a tension's, a compression's and a buckling's is positive; a shear reads none (issue #38)
        if entry["kind"] in ("tension", "compression", "buckling") and entry["N"]["value"] <= 0:
            raise ValidationError(f"{where}: calculable with N = {entry['N']['value']!r} -- the force is positive, a tension's and a compression's magnitude alike")
        # a shear reads its forces by its variant (spec 2026-10-21-commandes-typst-refonte, REQ-021): V_z or V_y, a shear-off F and l, a shear across the grain V_z and sigma_90
        variant = entry.get("variant") or "shear"
        if entry["kind"] == "shear" and variant == "shear" and not entry.get("V_z") and not entry.get("V_y"):
            raise ValidationError(f"{where}: a calculable shear with no shear force")
        if entry["kind"] == "shear" and variant == "shear-off" and (not entry.get("F") or not entry.get("l")):
            raise ValidationError(f"{where}: a calculable shear-off with no force F or no sheared length l")
        if entry["kind"] == "shear" and variant == "shear-perp" and (not entry.get("V_z") or entry.get("sigma_90") is None):
            raise ValidationError(f"{where}: a calculable shear across the grain with no V_z or no sigma_90")
        if entry["kind"] == "buckling" or (entry["kind"] == "lateral-torsional" and entry["N"]["value"] < 0):
            if entry.get("l_y") is None or entry.get("l_z") is None:
                raise ValidationError(f"{where}: a calculable {entry['kind']} with no system length about both axes")
        if entry["kind"] == "lateral-torsional":
            # the moment about the strong axis -- y, or z where b > h -- with one of a and sigma_m_crit; a round section, or a rectangle wider than high bent about y alone, tips about nothing and reads a moment alone (spec 2026-10-12-audit-issues-47-48-49, D-09, D-10, D-17)
            section = entry["section"]
            strong = None if section["type"] == "cir" else ("z" if section["b"] > section["h"] else "y")
            if not entry.get("M_y") and not entry.get("M_z"):
                raise ValidationError(f"{where}: a calculable lateral torsional buckling reads a moment")
            if strong is not None and entry.get("M_" + strong):
                if (entry.get("a") is None) == (entry.get("sigma_m_crit") is None):
                    raise ValidationError(f"{where}: a calculable lateral torsional buckling about {strong} reads one of a and sigma_m_crit")
            elif strong == "y":
                raise ValidationError(f"{where}: a calculable lateral torsional buckling of a section as high as wide or higher reads M_y")
        if not 0 <= entry["alpha"] <= 90:
            raise ValidationError(f"{where}: alpha {entry['alpha']!r} -- 0 to 90")
        # a check in the fire situation (issue #46) hands #member its fire: a duration, a face at least, the wood, on a rectangle along the grain
        fire = entry.get("fire")
        if fire is not None:
            if entry["kind"] not in ("tension", "compression", "bending", "shear", "buckling") or entry["alpha"] != 0:
                raise ValidationError(f"{where}: a {entry['kind']} at {entry['alpha']!r}° is no check of the fire situation -- along the grain only")
            if entry["section"]["type"] != "rec":
                raise ValidationError(f"{where}: a calculable fire check on a {entry['section']['type']} section -- the residual section is a rectangle's")
            if not isinstance(fire.get("duration"), int) or fire["duration"] <= 0 or not fire.get("sides") or not fire.get("wood"):
                raise ValidationError(f"{where}: a calculable fire check with no duration, no face or no wood")
            if not (fire.get("b") or 0) > 0 or not (fire.get("h") or 0) > 0:
                raise ValidationError(f"{where}: a calculable fire check whose residual section is not positive")
        # a bending hands verify-bending its moments: one at least, and at an angle M_y alone
        if entry["kind"] == "bending":
            if not entry.get("M_y") and not entry.get("M_z"):
                raise ValidationError(f"{where}: a calculable bending with no moment")
            if entry["alpha"] > 0 and (entry.get("M_z") or not entry.get("M_y")):
                raise ValidationError(f"{where}: a calculable bending at an angle reads M_y alone")
        # a compression at an angle hands verify-compression-perp its contact: a length, a width, a case and the table's value for it
        if entry["kind"] == "compression" and entry["alpha"] > 0:
            for key in ("l", "w", "case", "f_c_90_table"):
                if entry.get(key) is None:
                    raise ValidationError(f"{where}: a calculable compression at an angle with no {key}")


def validate_journal_business(data):
    """data/journal.json: every revision carries a number of its own, a real day, somebody's name and short form, and a label -- and the list is **newest first**, which is the export's own promise to the report (docs/domain/journal.md §3.3terdecies).

    That last one is the rule worth checking rather than trusting: `show-journal` prints the entries in the order it is given them and never sorts, and `journal.latest` -- which the PDF's keywords name -- is simply the first of them. An export that wrote them the other way round would print the oldest revision as the current one, which is exactly the silently wrong page this pipeline exists to stop.

    A journal is a list of what the engineer wrote, not a calculation, so there is no {vars, steps, checks} record here to check.
    """
    from journal import parse_date  # late: journal.py imports this module for its ValidationError
    seen = {}
    previous = None
    for position, entry in enumerate(data["entries"], 1):
        where = f"journal.{entry.get('index', position)}"
        index = entry["index"]
        if isinstance(index, bool) or not isinstance(index, int) or index < 1:
            raise ValidationError(f"{where}: index is {index!r} -- a whole number of 1 or more")
        if index in seen:
            raise ValidationError(f"{where}: index {index} is the index of the entry {seen[index]!r} already")
        seen[index] = entry["label"]
        if previous is not None and index >= previous:
            raise ValidationError(
                f"{where}: index {index} stands after {previous} -- the entries are written newest first, "
                f"the largest index first (journal.entries)"
            )
        previous = index
        if parse_date(entry["date"]) is None:
            raise ValidationError(f"{where}: date is {entry['date']!r} -- expected a day as 2026-09-27 (ISO)")
        for field in ("name", "initials", "label"):
            if not entry[field].strip():
                raise ValidationError(f"{where}: {field} must not be empty")


def validate_annexes_business(data):
    """data/annexes.json: every excerpt names a source the export carries; a resolved one has its page, its file and a frame of positive size inside its page, an unresolved one says why; and every source's annex lists its pages ascending, with a size for each (docs/domain/annexes.md §3.3undevicies).

    The rule worth checking rather than trusting is the last half of the first: `show-extract` refuses an unresolved excerpt with its `reason`, so one marked unresolved with no reason would stop the report on an empty sentence, and one marked resolved with no file would stop it on a file that is not there.
    """
    for eid, excerpt in data["excerpts"].items():
        where = f"annexes.excerpts.{eid}"
        if excerpt["source"] not in data["sources"] and excerpt["resolved"]:
            raise ValidationError(f"{where}: its source {excerpt['source']!r} is not exported, and yet it is marked resolved")
        if excerpt["resolved"]:
            if not excerpt["file"] or excerpt["page"] is None or excerpt["rect"] is None:
                raise ValidationError(f"{where}: resolved, but its file, page or frame is missing")
            x, y, w, h = excerpt["rect"]
            if w <= 0 or h <= 0 or x < 0 or y < 0:
                raise ValidationError(f"{where}: its frame {excerpt['rect']!r} is not a region of its page")
            size = excerpt.get("page_size")
            if size and (x + w > size[0] + 0.01 or y + h > size[1] + 0.01):
                raise ValidationError(f"{where}: its frame {excerpt['rect']!r} runs past its page {size!r}")
        elif not excerpt["reason"].strip():
            raise ValidationError(f"{where}: not resolved, and nothing says why -- the report would refuse it on an empty sentence")
    for sid, source in data["sources"].items():
        annex = source["annex"]
        if annex is None:
            continue
        pages = annex["pages"]
        if pages != sorted(set(pages)) or not pages or pages[0] < 1 or pages[-1] > source["pages"]:
            raise ValidationError(f"annexes.sources.{sid}: its annex pages {pages!r} are not pages of its {source['pages']} in ascending order")
        if len(annex["sizes"]) != len(pages):
            raise ValidationError(f"annexes.sources.{sid}: {len(pages)} annex page(s) and {len(annex['sizes'])} size(s)")


def validate_calculations_business(data):
    for domain_name, domain in data["domains"].items():
        if domain["action"] not in ACTIONS:
            raise ValidationError(
                f"{domain_name}: action is {domain['action']!r} -- expected one "
                f"of {', '.join(sorted(ACTIONS))} (set ACTION in its domain module)"
            )
        if domain["engine"] not in ENGINES:
            raise ValidationError(
                f"{domain_name}: engine is {domain['engine']!r} -- expected one "
                f"of {', '.join(sorted(ENGINES))} (set ENGINE in its domain module)"
            )
        from_norm = domain["engine"] == NORM_ENGINE
        for case, instance in domain["instances"].items():
            path = f"{domain_name}.{case}"
            _check_calculation(instance, path)

            # A case entered in Woodcore (schema 1.5, D-04) names the source it was computed from; a row of a norm table names none (docs/domain/calculation-domains.md §3.3, docs/domain/loads.md §3.3septies). Since issue #109 nothing else is a case: no workbook, no sheet (1.9).
            if instance.get("source_file"):
                if from_norm:
                    raise ValidationError(f"{path}: computed from {instance['source_file']} although its domain is read from a norm table")
                if instance.get("engine") != "python":
                    raise ValidationError(f"{path}: computed from {instance['source_file']} and its engine is {instance.get('engine')!r} -- 'python'")
                # a load's drawing lies in its own Exports/Figures/ -- the build-up's under Permanent-loads/, the snow's column of Figur 3 under Variable-loads/Snow/ (spec 2026-10-22-onglet-neige-type, D-32) -- or in data/calculations/ in a project laid out before
                import project
                for figure in instance.get("figures") or ():
                    if not any(_starts_figure(str(figure.get("file", "")), kind, "") for kind in project.LOAD_FIGURE_KINDS):
                        raise ValidationError(f"{path}: a figure's file {figure.get('file')!r} is not under data/calculations/ nor " + " nor ".join(figure_names(kind, '')[1] for kind in project.LOAD_FIGURE_KINDS))
            elif not from_norm:
                raise ValidationError(f"{path}: no source_file -- a case of '{domain_name}' is computed from the source it was entered in (Woodcore-Datei/loads/)")
            elif instance.get("engine") not in (None, domain["engine"]):
                raise ValidationError(f"{path}: engine {instance['engine']!r} -- a row of a norm table is its domain's, '{NORM_ENGINE}'")

            var_names = set(instance.get("vars", {}).keys())
            if not instance["results"]:
                raise ValidationError(
                    f"{path}: no results -- an instance must name at least one "
                    f"var as its final result, that being what show-calc prints "
                    f"at level 1"
                )
            # A result is deliberately not required to be positive: a global wind force on a roof is an uplift and a wall's minimum is a suction, so its sign is part of the answer (docs/domain/loads.md §3.3quater). What is checked is that it is a value at all -- a number, or the text of a dropdown entry -- rather than something that would reach Typst and fail there.
            for result in instance["results"]:
                if result not in var_names:
                    raise ValidationError(
                        f"{path}: result '{result}' is not a declared var"
                    )
                value = instance["vars"][result]["value"]
                if not isinstance(value, (int, float, str)):
                    raise ValidationError(
                        f"{path}: result '{result}' is neither a number nor "
                        f"text ({value!r})"
                    )

            # The single `table` became a `tables` list (schema 1.3); the display layer reads only the list, so a module still emitting the old key would lose its table from the report without a word.
            if "table" in instance:
                raise ValidationError(
                    f"{path}: carries a 'table' -- an instance's tables are "
                    f"a list now, 'tables': [...]"
                )
            _check_tables(instance, path)


def _check_tables(data, path):
    """The rules every table of a {vars, steps, checks, tables} record obeys, wherever it lives -- an instance of a load domain or a connection (docs/domain/calculation-domains.md §3.3, docs/domain/connections.md §3.3quinquies). An instance may carry several tables, each with its own level and place (the wind load's global forces from level 1, its local forces at level 3) -- every one of them held to the same rules."""
    var_names = set(data.get("vars", {}).keys())
    for t, table in enumerate(data.get("tables", [])):
        where = f"{path}: table {t} ({table['title']!r})"
        width = len(table["columns"])
        for i, column in enumerate(table["columns"]):
            if column["kind"] not in TABLE_COLUMN_KINDS:
                raise ValidationError(
                    f"{where}, column {i} "
                    f"({column['label']!r}) has kind "
                    f"{column['kind']!r} -- expected one of "
                    + ", ".join(sorted(TABLE_COLUMN_KINDS))
                )
        place = table.get("place", "above")
        if place not in TABLE_PLACES:
            raise ValidationError(
                f"{where}: place is {place!r} -- expected one of "
                + ", ".join(sorted(TABLE_PLACES))
            )
        if table.get("level", 3) not in (1, 2, 3):
            raise ValidationError(
                f"{where}: level must be 1, 2, or 3, got "
                f"{table['level']!r}"
            )
        # The rows the table sets apart: the one row of a norm table the calculation actually reads (its category, in SIA 261's Tabelle 8). Counted over the body rows, from 0 -- an index past the end would silently highlight nothing, which is exactly the kind of quietly wrong page this pipeline stops for.
        highlight = table.get("highlight", [])
        if not isinstance(highlight, list):
            raise ValidationError(
                f"{where}: highlight is {highlight!r} -- expected a list of row "
                f"indices"
            )
        for index in highlight:
            if isinstance(index, bool) or not isinstance(index, int):
                raise ValidationError(
                    f"{where}: highlight holds {index!r} -- expected a row index"
                )
            if not 0 <= index < len(table["rows"]):
                raise ValidationError(
                    f"{where}: highlight names row {index}, which the table does "
                    f"not have ({len(table['rows'])} rows)"
                )
        # A formula is printed with its citation beside it, here as everywhere else -- engine.step() enforces the same thing for a step's formula, and a table carrying one must not be the way round that.
        if "formula" in table and not (table.get("norm")
                                       and table.get("norm_ref")):
            raise ValidationError(
                f"{where}: states a formula but no norm/norm_ref to "
                f"cite beside it"
            )
        # A `value` cell names a var of this instance instead of repeating its number, so the table cannot drift from the values it shows -- which only holds if the name is real. A column may also carry plain numbers in the rows whose total is a var (a connection's Δx², summed into I_p,x by its totals row), and an empty cell is an empty cell; anything else would reach Typst and fail there.
        value_columns = [
            i for i, c in enumerate(table["columns"])
            if c["kind"] == "value"
        ]
        for label, rows in (("row", table["rows"]),
                            ("totals row", table.get("totals", []))):
            for r, row in enumerate(rows):
                for i in value_columns:
                    if i >= len(row):
                        continue
                    cell = row[i]
                    if isinstance(cell, str):
                        if cell and cell not in var_names:
                            raise ValidationError(
                                f"{where}, {label} {r}, column {i} "
                                f"({table['columns'][i]['label']!r}) names "
                                f"'{cell}', which is not a declared var"
                            )
                    elif isinstance(cell, bool) or not isinstance(cell, (int, float)):
                        raise ValidationError(
                            f"{where}, {label} {r}, column {i} "
                            f"({table['columns'][i]['label']!r}) holds "
                            f"{cell!r} -- expected a var name or a number"
                        )
        # a totals row is a row like any other and must line up with the same columns; one cell short would silently shift a sum under the wrong header
        for label, rows in (("row", table["rows"]),
                            ("totals row", table.get("totals", []))):
            for i, row in enumerate(rows):
                if len(row) != width:
                    raise ValidationError(
                        f"{where}, {label} {i} has {len(row)} "
                        f"cells for {width} columns"
                    )


# A connection id is the file name of its source and the string the report addresses it by (docs/domain/connections.md §3.3quinquies) -- the pattern domains/connection.py checks a source's id against, restated here because that module imports this one. A connector's id is held to it too.
CONNECTION_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.+-]*")

# Restated from domains/connector.py and domains/dowel.py, which import this module and so cannot be imported by it. tests/test_constants.py compares the copies -- that file exists for exactly these restatements.
CONNECTOR_TYPES = {
    "Stabdübel", "Passbolzen", "Bolzen", "Vollgewindeschraube", "Teilgewindeschraube",
    "Nagel", "Klammer", "eingeklebte Gewindestange", "Dübel besonderer Bauart",
}
CONNECTOR_ASSEMBLIES = {
    "Holz-Holz einschnittig", "Holz-Holz zweischnittig",
    "Stahl-Holz, Bleche aussen", "Stahl-Holz, Schlitzbleche",
}
CONNECTOR_ROLES = {"timber", "steel"}
CONNECTOR_MEMBERS = (2, 6)


def validate_connectors_business(data):
    """data/connectors.json: the rules of a connector record a schema cannot state (docs/domain/connectors.md §7bis, §3.3nonies).

    Since 2.0 a connector carries its own calculation, so the rules are in two halves: the descriptive one, which is what the retired Positions Connectors sheet was checked for and is unchanged, and the calculation one, which is what every other calculation record is checked for. A connector that could not be calculated -- a type with no module yet, a member whose timber did not resolve -- must carry an empty record AND a reason, so that «no resistance» and «a resistance nobody produced» cannot be confused.
    """
    for cid, connector in data["connectors"].items():
        path = f"connectors.{cid}"
        if not CONNECTION_ID.fullmatch(cid):
            raise ValidationError(f"{path}: id {cid!r} -- use letters, digits and _ . + - only, starting with a letter or a digit")
        if connector["position"] != cid:
            raise ValidationError(f"{path}: position is {connector['position']!r}, not its own id")
        for key in ("type", "assembly"):
            if not connector[key]:
                raise ValidationError(f"{path}: {key} must not be empty")
        if connector["type"] not in CONNECTOR_TYPES:
            raise ValidationError(f"{path}: type {connector['type']!r} -- the kinds of fastener are {', '.join(sorted(CONNECTOR_TYPES))}")
        if connector["assembly"] not in CONNECTOR_ASSEMBLIES:
            raise ValidationError(f"{path}: assembly {connector['assembly']!r} -- SIA 265 Tabellen 45 and 46 give {', '.join(sorted(CONNECTOR_ASSEMBLIES))}")
        for key in ("diameter", "length"):
            size = connector[key]
            if size is not None and (size["unit"] != "mm" or isinstance(size["value"], bool) or size["value"] <= 0):
                raise ValidationError(f"{path}: {key} must be a number of mm greater than 0, got {size!r}")
        if connector["source"] != f"connectors/{cid}.json":
            raise ValidationError(f"{path}: source is {connector['source']!r}, not its own file")

        members = connector["members"]
        if not CONNECTOR_MEMBERS[0] <= len(members) <= CONNECTOR_MEMBERS[1]:
            raise ValidationError(f"{path}: {len(members)} member(s) -- between {CONNECTOR_MEMBERS[0]} and {CONNECTOR_MEMBERS[1]} meet at a node")
        # Since 3.0 the geometry is a schema's: a member names an element of it rather than carrying a section, and a fastener carries its marker's id beside the place that marker sits at. What the schema does not carry is a warning and never a stop (docs/decisions.md §13), so nothing here may require an element to resolve -- only that what IS there is well formed.
        for index, fastener in enumerate(connector["fasteners"], start=1):
            if not fastener["id"]:
                raise ValidationError(f"{path}.fasteners[{index}]: carries no marker id")
        for index, member in enumerate(members, start=1):
            spot = f"{path}.members[{index}]"
            if member["role"] not in CONNECTOR_ROLES:
                raise ValidationError(f"{spot}: role {member['role']!r} -- expected {' or '.join(sorted(CONNECTOR_ROLES))}")
            moisture = member.get("moisture_class")
            if moisture is not None and moisture not in moisture_classes():
                raise ValidationError(f"{spot}: moisture class {moisture!r} -- expected {', '.join(str(c) for c in moisture_classes())} or nothing")
            species = member.get("species", "")
            if species and species not in connector_species():
                raise ValidationError(f"{spot}: species {species!r} -- SIA 265 Tabelle 22 gives {', '.join(sorted(connector_species()))}")

        # ⚠️ An EMPTY fastener list is allowed since 3.0 and is not a defect in the record. The source
        # may name no marker at all -- check_source allows it since schema 2.0 -- and the coordinates are the
        # schema's, so a schema renamed or a marker deleted leaves nothing to resolve. That is a warning,
        # and `calculated` is false with its reason; refusing it here would stop the whole export over a
        # drawing Woodcore's window is the only place able to repair (docs/decisions.md §13, the v0.33 rule).
        if connector["fasteners"] and connector["calculated"] and connector["n_tot"] < 1:
            raise ValidationError(f"{path}: n_tot is {connector['n_tot']} -- at least one fastener")
        # ... and only for a connector that is calculated: one whose schema lost a marker draws fewer than it names, and says so in its reason rather than stopping the export (periodic audit 260916, AUD-8-2)
        if (connector["calculated"] and connector["fasteners"] and not connector["n_tot_override"]
                and connector["n_tot"] != len(connector["fasteners"])):
            raise ValidationError(f"{path}: n_tot is {connector['n_tot']} and the drawing has {len(connector['fasteners'])} -- only an override may part the two")

        if not connector["calculated"]:
            if not connector["reason"]:
                raise ValidationError(f"{path}: calculated is false and no reason is given -- the report prints the reason")
            for key in ("results", "tables", "steps", "checks"):
                if connector[key]:
                    raise ValidationError(f"{path}: calculated is false but {key} is not empty")
            if connector["vars"]:
                raise ValidationError(f"{path}: calculated is false but vars is not empty")
            continue

        if connector["reason"]:
            raise ValidationError(f"{path}: calculated is true and a reason is given -- a reason says why there is none")
        _check_calculation(connector, path)
        _check_tables(connector, path)
        var_names = set(connector["vars"])
        if not connector["results"]:
            raise ValidationError(f"{path}: results is empty -- a calculation ends on at least one value")
        for name in connector["results"]:
            if name not in var_names:
                raise ValidationError(f"{path}: results names {name!r}, which is not one of its vars")
        if connector["checks"]:
            raise ValidationError(f"{path}: checks must be empty -- the design force and its verification are written in the report (docs/domain/connectors.md §3.3nonies)")


def validate_connections_business(data):
    """data/connections.json: every connection's record obeys the rules every calculation does, and its geometry is what show-polar-moment can distribute forces over."""
    for cid, record in data["connections"].items():
        path = f"connections.{cid}"
        if not CONNECTION_ID.fullmatch(cid):
            raise ValidationError(f"{path}: id {cid!r} -- use letters, digits and _ . + - only, starting with a letter or a digit")
        # ⚠️ No longer bound to <connector>-<variant> since v0.75, and naming no connector at all since v0.76: the id is made from the calculation's own name and may be written over (section 3.3quinquies).
        _check_calculation(record, path)
        _check_tables(record, path)
        var_names = set(record["vars"])
        if not record["results"]:
            raise ValidationError(f"{path}: no results")
        for result in record["results"]:
            if result not in var_names:
                raise ValidationError(f"{path}: result '{result}' is not a declared var")
        # A calculation its schema no longer draws whole is exported with its reason and refused by the report (4.1; periodic audit 260916): an empty fastener list is then not a defect of the record.
        if not isinstance(record.get("calculated"), bool):
            raise ValidationError(f"{path}: calculated must be true or false")
        if record["calculated"] and record["reason"]:
            raise ValidationError(f"{path}: calculated is true and a reason is given -- a reason says why there is none")
        if not record["calculated"] and not record["reason"].strip():
            raise ValidationError(f"{path}: calculated is false and no reason is given -- the report prints the reason")
        if record["calculated"] and not record["fasteners"]:
            raise ValidationError(f"{path}: has no fastener")
        # show-polar-moment shares N and V by n, reads the fasteners' coordinates and draws an arrow on each figure point: the three must be the same count
        count = len(record["fasteners"])
        if record["vars"].get("n", {}).get("value") != count:
            raise ValidationError(f"{path}: n does not match its {count} fasteners")
        if len(record["figure"]["points"]) != count:
            raise ValidationError(f"{path}: the figure places {len(record['figure']['points'])} fasteners, the connection has {count}")
        if not 2 <= len(record["members"]) <= 6:
            raise ValidationError(f"{path}: a connection joins 2 to 6 members, got {len(record['members'])}")
        if not 1 <= record["reference"] <= len(record["members"]):
            raise ValidationError(f"{path}: reference is member {record['reference']}, which it does not have")
        # The two angles part company as soon as a detail is drawn at an angle, so the reference member's own `local` is the one thing that must still be 0: theta_(r,r) is not printed, and a non-zero one would mean the record was built against another reference than it names.
        if abs(record["members"][record["reference"] - 1]["local"]) > 1e-6:
            raise ValidationError(f"{path}: the reference member's local angle is {record['members'][record['reference'] - 1]['local']}, not 0")
        # One figure per language, each named after the connection and the language it is drawn in: its legend is five sentences, and the frame is sized from them (docs/typst/language.md §4bis).
        for lang in strings.LANGUAGES:
            want = figure_names("connection", f"{cid}-{lang}.svg")
            if record["figure"]["files"].get(lang) not in want:
                raise ValidationError(
                    f"{path}: the {lang} figure is {record['figure']['files'].get(lang)!r} -- expected {' or '.join(map(repr, want))}"
                )
        # a document is cited whole, so the clause may be empty; the reference may not
        if not record["norm"].strip():
            raise ValidationError(f"{path}: norm is empty")


# The STE symbols a plan may carry, and the shape each may be drawn as (docs/domain/position-plans.md §3.3sexies) -- restated from domains/plan.py for the reason CONNECTION_ID is: that module imports this one.
PLAN_KINDS = {
    "V": {"line"}, "H": {"line"}, "W": {"line"}, "T": {"line"}, "A": {"line"},
    "M": {"line", "point"}, "L": {"line", "point"}, "S": {"point"},
    "D": {"poly"}, "Ö": {"poly"}, "B": {"poly"},
    # a load-path plan's load symbols (v0.116): a point load and a line load
    "PL": {"point"}, "LL": {"line"},
}
PLAN_MIN_POINTS = {"point": 1, "line": 2, "poly": 3}


# What a fire-protection plan's entries may be, restated here because domains/fire.py imports this module (tests/test_constants.py holds the two equal).
FIRE_SURFACES = ("vertical", "horizontal", "clear")
FIRE_DOOR_KINDS = ("swing", "slide")
FIRE_COLLECTIONS = ("zones", "walls", "doors", "routes", "exits", "widths")
FIRE_MEASURES = ("area_m2", "length_m", "width_m")


def validate_fire_business(data):
    """data/fire.json: every plan shows a frame that is not empty, is drawn once per language of the report in a file named after it, lies over a background of its own or over the position plan's it follows, and measures nothing negative. show-fire-plan reads all of it without checking again."""
    for fid, record in data["plans"].items():
        path = f"fire.{fid}"
        if not CONNECTION_ID.fullmatch(fid):
            raise ValidationError(f"{path}: id {fid!r} -- use letters, digits and _ . + - only, starting with a letter or a digit")
        if record["source"] != f"fire/{fid}.json":
            raise ValidationError(f"{path}: source is {record['source']!r} -- expected 'fire/{fid}.json'")
        crop = record["crop"]
        if crop["w"] <= 0 or crop["h"] <= 0:
            raise ValidationError(f"{path}: its frame is empty")
        if record["unit"] <= 0:
            raise ValidationError(f"{path}: unit must be greater than 0")
        if set(record["figures"]) != set(strings.LANGUAGES):
            raise ValidationError(f"{path}: it carries the figures {sorted(record['figures'])} -- expected {list(strings.LANGUAGES)}")
        for lang, name in record["figures"].items():
            if not _is_figure(name, "fire", f"{fid}-{lang}.svg"):
                raise ValidationError(f"{path}: the {lang} figure is {name!r} -- expected 'fire/{fid}-{lang}.svg'")
        keys = [line["key"] for line in record.get("legend_lines", [])]
        if len(keys) != len(set(keys)):
            raise ValidationError(f"{path}: legend_lines lists a line twice")
        for line in record.get("legend_lines", []):
            if not line["swatch"].lstrip().startswith("<svg"):
                raise ValidationError(f"{path}: legend line {line['key']!r} has a swatch that is no SVG document")
        background = record.get("background")
        if background is not None:
            own = _starts_figure(background["file"], "fire", f"{fid}-plan.")
            followed = "plan" in record and _starts_figure(background["file"], "plan", f"{record['plan']}-plan.")
            if not (own or followed):
                raise ValidationError(f"{path}: background is {background['file']!r} -- expected fire/{fid}-plan.<format>, or the background of the position plan it follows")
            if not 0 <= background["opacity"] <= 1:
                raise ValidationError(f"{path}: background.opacity is {background['opacity']} -- from 0 to 1")
        seen = set()
        for collection in FIRE_COLLECTIONS:
            for i, entry in enumerate(record[collection], start=1):
                at = f"{path}: {collection}[{i}] ({entry['id']})"
                if entry["id"] in seen:
                    raise ValidationError(f"{at}: the id is used twice")
                seen.add(entry["id"])
                for key in FIRE_MEASURES:
                    if key in entry and entry[key] < 0:
                        raise ValidationError(f"{at}: {key} is {entry[key]} -- a measure is never negative")
                if "scale" not in record and any(key in entry for key in FIRE_MEASURES):
                    raise ValidationError(f"{at}: it states a measure on a plan without a scale")
        for i, zone in enumerate(record["zones"], start=1):
            if zone["kind"] not in FIRE_SURFACES:
                raise ValidationError(f"{path}: zones[{i}] ({zone['id']}) has kind {zone['kind']!r} -- expected one of {', '.join(FIRE_SURFACES)}")
        for i, door in enumerate(record["doors"], start=1):
            if door["kind"] not in FIRE_DOOR_KINDS:
                raise ValidationError(f"{path}: doors[{i}] ({door['id']}) has kind {door['kind']!r} -- expected one of {', '.join(FIRE_DOOR_KINDS)}")


def figure_names(kind, file):
    """The two names an export may give the figure `file` of `kind` (project.FIGURE_KINDS): under data/, `plans/P01.svg`, as every export did until 0.119 and a project laid out before still does; and from the Typst root in its tab's Exports/Figures/, `/Plans/Position-plan/Exports/Figures/P01.svg`, in a project laid out by folders (issue #64, D-10). lib/calc-engine.typ `figure-path` reads both."""
    import project  # project reads this module at its own import
    return (f"{project.FIGURE_KINDS[kind]}/{file}", f"/{project.figures_folder(kind)}/{file}")


def _is_figure(name, kind, file):
    return name in figure_names(kind, file)


def _starts_figure(name, kind, stem):
    return any(name.startswith(prefix) for prefix in figure_names(kind, stem))


def validate_plans_business(data):
    """data/plans.json: every plan shows a frame of its sheet, draws its elements with the points their shape needs, refers to files under plans/ named after it, and lists as unknown only labels it shows. show-plan reads all of it without checking again."""
    for pid, record in data["plans"].items():
        path = f"plans.{pid}"
        if not CONNECTION_ID.fullmatch(pid):
            raise ValidationError(f"{path}: id {pid!r} -- use letters, digits and _ . + - only, starting with a letter or a digit")
        crop = record["crop"]
        if crop["w"] <= 0 or crop["h"] <= 0:
            raise ValidationError(f"{path}: its frame is empty")
        if not _is_figure(record["overlay"], "plan", f"{pid}.svg"):
            raise ValidationError(f"{path}: overlay is {record['overlay']!r} -- expected 'plans/{pid}.svg'")
        # a section with a load transfer level is drawn once per language (v0.116): one figure for each, named after the plan
        if record.get("figures") and set(record["figures"]) != {"de", "fr", "en"}:
            raise ValidationError(f"{path}: drawn in {', '.join(sorted(record['figures']))} -- a figure for each of de, fr and en")
        for lang, file in (record.get("figures") or {}).items():
            if not _is_figure(file, "plan", f"{pid}-{lang}.svg"):
                raise ValidationError(f"{path}: its {lang} figure is {file!r} -- expected 'plans/{pid}-{lang}.svg'")
        if record.get("plan_type", "section" if record["role"] == "section" else "floor") not in ("floor", "section", "loadpath"):
            raise ValidationError(f"{path}: plan_type is {record.get('plan_type')!r}")
        for i, line in enumerate(record["legend"], start=1):
            if not line["swatch"].startswith("<svg"):
                raise ValidationError(f"{path}: legend line {i} ({line['key']}) has no SVG swatch")
        background = record.get("background")
        if background is not None and not _starts_figure(background["file"], "plan", f"{pid}-plan."):
            raise ValidationError(f"{path}: background is {background['file']!r} -- expected plans/{pid}-plan.<format>")
        if record["unit"] <= 0:
            raise ValidationError(f"{path}: unit must be greater than 0")
        for i, element in enumerate(record["elements"], start=1):
            kinds = PLAN_KINDS.get(element["type"])
            if kinds is None:
                raise ValidationError(f"{path}: element {i} has type {element['type']!r}")
            if element["kind"] not in kinds:
                raise ValidationError(f"{path}: element {i} ({element['type']}) is drawn as a {element['kind']!r}")
            count = len(element["points"])
            if count < PLAN_MIN_POINTS[element["kind"]] or (element["kind"] == "point" and count != 1):
                raise ValidationError(f"{path}: element {i} ({element['type']}) has {count} point(s) for a {element['kind']}")
            if any(len(p) != 2 for p in element["points"]):
                raise ValidationError(f"{path}: element {i} has a point that is not [x, y]")
            if "label_at" in element and len(element["label_at"]) != 2:
                raise ValidationError(f"{path}: element {i}'s label_at is not [x, y]")
        labels = set(record["labels"])
        for label in record["unknown"]:
            if label not in labels:
                raise ValidationError(f"{path}: lists {label!r} as unknown but does not show it")



# What a static model may be built of (docs/domain/static-models.md §3.3octies) -- restated from domains/statics.py for the reason CONNECTION_ID is: that module imports this one.
STATIC_MEMBER_KINDS = {"bar", "cable", "spring"}
STATIC_SUPPORTS = {"fixed", "pinned", "roller"}
STATIC_LOAD_KINDS = {"point", "line"}
STATIC_RELEASE_DOFS = {"moment", "shear", "normal"}
STATIC_DIMENSION_KINDS = {"horizontal", "vertical", "parallel", "angle"}
# a length is in metres and an angle in degrees: the unit is the kind's, not the engineer's to choose
STATIC_DIMENSION_UNITS = {"horizontal": "m", "vertical": "m", "parallel": "m", "angle": "\u00b0"}


def validate_statics_business(data):
    """data/statics.json: every model shows a frame with something in it, draws each member between two points, refers to a figure under statics/ named after it, and lists as unresolved only loads it carries. show-static-model reads all of it without checking again.

    A model is a drawing and not a calculation: there is deliberately no {vars, steps, checks} record here to check, and nothing addresses one with show-calc.
    """
    for sid, record in data["models"].items():
        path = f"models.{sid}"
        if not CONNECTION_ID.fullmatch(sid):
            raise ValidationError(
                f"{path}: id {sid!r} -- use letters, digits and _ . + - only, "
                f"starting with a letter or a digit"
            )
        # One figure per language, each named after the model and the language it is drawn in, and each with its own frame: the notes are drawn inside the figure and its frame is sized to hold them (docs/typst/language.md §4bis).
        if set(record["figures"]) != set(strings.LANGUAGES):
            raise ValidationError(
                f"{path}: it carries the figures {sorted(record['figures'])} -- expected {list(strings.LANGUAGES)}"
            )
        for lang, figure in record["figures"].items():
            want = figure_names("statics", f"{sid}-{lang}.svg")
            if figure["file"] not in want:
                raise ValidationError(
                    f"{path}: the {lang} figure is {figure['file']!r} -- expected {' or '.join(map(repr, want))}"
                )
            if figure["view"]["w"] <= 0 or figure["view"]["h"] <= 0:
                raise ValidationError(f"{path}: its {lang} frame is empty")
        if record["unit"] <= 0:
            raise ValidationError(f"{path}: unit must be greater than 0")
        point_ids = {p["id"] for p in record["points"]}
        for point in record["points"]:
            if len(point["at"]) != 2:
                raise ValidationError(f"{path}: point {point['id']} is not at [x, y]")
        for member in record["members"]:
            if member["kind"] not in STATIC_MEMBER_KINDS:
                raise ValidationError(
                    f"{path}: member {member['id']} is a {member['kind']!r}"
                )
            if len(member["at"]) != 2 or any(len(p) != 2 for p in member["at"]):
                raise ValidationError(
                    f"{path}: member {member['id']} is not drawn between two points"
                )
        for support in record["supports"]:
            if support["type"] not in STATIC_SUPPORTS:
                raise ValidationError(
                    f"{path}: support {support['id']} is a {support['type']!r}"
                )
            if support["point"] not in point_ids:
                raise ValidationError(
                    f"{path}: support {support['id']} holds {support['point']!r}, "
                    f"which the model does not show"
                )
        for release in record["releases"]:
            if release["dof"] not in STATIC_RELEASE_DOFS:
                raise ValidationError(
                    f"{path}: release {release['id']} frees a {release['dof']!r}"
                )
        load_ids = set()
        for load in record["loads"]:
            if load["kind"] not in STATIC_LOAD_KINDS:
                raise ValidationError(f"{path}: load {load['id']} is a {load['kind']!r}")
            load_ids.add(load["id"])
        labels = set(record["labels"])
        for entry in record["unresolved"]:
            if entry.split(":", 1)[0].strip() not in load_ids:
                raise ValidationError(
                    f"{path}: lists {entry!r} as unresolved but carries no such load"
                )
        for load in record["loads"]:
            if load["id"] not in labels:
                raise ValidationError(
                    f"{path}: load {load['id']} is not among the ids it lists"
                )
        for dim in record["dimensions"]:
            if dim["kind"] not in STATIC_DIMENSION_KINDS:
                raise ValidationError(
                    f"{path}: dimension {dim['id']} is a {dim['kind']!r}"
                )
            if dim["unit"] != STATIC_DIMENSION_UNITS[dim["kind"]]:
                raise ValidationError(
                    f"{path}: dimension {dim['id']} is a {dim['kind']} measured in {dim['unit']!r} -- "
                    f"expected {STATIC_DIMENSION_UNITS[dim['kind']]!r}"
                )
            if len(dim["at"]) != 2:
                raise ValidationError(
                    f"{path}: dimension {dim['id']} writes its value at no point of the figure"
                )
            if dim["kind"] == "angle":
                if len(dim.get("centre", [])) != 2:
                    raise ValidationError(
                        f"{path}: dimension {dim['id']} turns about no corner"
                    )
            elif len(dim.get("line", [])) != 2:
                raise ValidationError(
                    f"{path}: dimension {dim['id']} is drawn along no line"
                )
            if dim["id"] not in labels:
                raise ValidationError(
                    f"{path}: dimension {dim['id']} is not among the ids it lists"
                )


# What a detail schema may be built of (docs/domain/detail-schemas.md §3.3decies) -- restated from domains/schema.py for the reason CONNECTION_ID is: that module imports this one. A marker's kind is a connector's kind and is read off CONNECTOR_TYPES above rather than copied a second time: one list, one test (tests/test_constants.py) keeping it level with domains/connector.py.
SCHEMA_ELEMENT_KINDS = {"linear", "area"}
SCHEMA_DIMENSION_KINDS = STATIC_DIMENSION_KINDS
SCHEMA_DIMENSION_UNITS = {"horizontal": "mm", "vertical": "mm", "parallel": "mm", "angle": "°"}
SCHEMA_CONNECTOR_KINDS = CONNECTOR_TYPES


def validate_schemas_business(data):
    """data/schemas.json: every schema shows a frame with something in it, draws each element with at least the points a piece needs, refers to a figure under schemas/ named after it, and lists as unresolved only elements it carries. show-schema reads all of it without checking again.

    A schema is a drawing, like a static model: there is deliberately no {vars, steps, checks} record here to check, and nothing addresses one with show-calc.
    """
    for sid, record in data["schemas"].items():
        path = f"schemas.{sid}"
        if data["schema_version"] == "1.4" and "size" not in record:
            raise ValidationError(f"{path}: it has no size -- an export at 1.4 carries each schema's (D7)")
        if not CONNECTION_ID.fullmatch(sid):
            raise ValidationError(
                f"{path}: id {sid!r} -- use letters, digits and _ . + - only, "
                f"starting with a letter or a digit"
            )
        if set(record["figures"]) != set(strings.LANGUAGES):
            raise ValidationError(
                f"{path}: it carries the figures {sorted(record['figures'])} -- expected {list(strings.LANGUAGES)}"
            )
        for lang, figure in record["figures"].items():
            want = figure_names("details", f"{sid}-{lang}.svg")
            if figure["file"] not in want:
                raise ValidationError(
                    f"{path}: the {lang} figure is {figure['file']!r} -- expected {' or '.join(map(repr, want))}"
                )
            if figure["view"]["w"] <= 0 or figure["view"]["h"] <= 0:
                raise ValidationError(f"{path}: its {lang} frame is empty")
        labels = set(record["labels"])
        for element in record["elements"]:
            if element["kind"] not in SCHEMA_ELEMENT_KINDS:
                raise ValidationError(f"{path}: element {element['id']} is a {element['kind']!r}")
            minimum = 3 if element["kind"] == "area" else 2
            if len(element["at"]) < minimum:
                raise ValidationError(
                    f"{path}: element {element['id']} ({element['kind']}) is drawn with only {len(element['at'])} point(s)"
                )
            if element["id"] not in labels:
                raise ValidationError(f"{path}: element {element['id']} is not among the ids it lists")
        for marker in record["connectors"]:
            if marker["kind"] not in SCHEMA_CONNECTOR_KINDS:
                raise ValidationError(f"{path}: connector {marker['id']} is a {marker['kind']!r}")
            if len(marker["at"]) != 2:
                raise ValidationError(f"{path}: connector {marker['id']} sits at no point")
            if marker["id"] not in labels:
                raise ValidationError(f"{path}: connector {marker['id']} is not among the ids it lists")
        for aid in record["aids"]:
            if not aid["shown"]:
                raise ValidationError(f"{path}: aid {aid['id']} is exported unshown -- only a shown aid is ever written")
            if aid.get("at") is None and aid.get("line") is None:
                raise ValidationError(f"{path}: aid {aid['id']} is drawn at no point and along no line")
            if aid["id"] not in labels:
                raise ValidationError(f"{path}: aid {aid['id']} is not among the ids it lists")
        for dim in record["dimensions"]:
            if dim["kind"] not in SCHEMA_DIMENSION_KINDS:
                raise ValidationError(f"{path}: dimension {dim['id']} is a {dim['kind']!r}")
            if dim["unit"] != SCHEMA_DIMENSION_UNITS[dim["kind"]]:
                raise ValidationError(
                    f"{path}: dimension {dim['id']} is a {dim['kind']} measured in {dim['unit']!r} -- "
                    f"expected {SCHEMA_DIMENSION_UNITS[dim['kind']]!r}"
                )
            if len(dim["at"]) != 2:
                raise ValidationError(f"{path}: dimension {dim['id']} writes its value at no point of the figure")
            if dim["id"] not in labels:
                raise ValidationError(f"{path}: dimension {dim['id']} is not among the ids it lists")
        for entry in record["unresolved"]:
            if entry.split(":", 1)[0].strip() not in labels:
                raise ValidationError(f"{path}: lists {entry!r} as unresolved but carries no such element")
