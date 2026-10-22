"""The steel checks saved in Woodcore's «Acier» tabs: their source, what the project gives them, their calculation and data/steel.json (issues #50, #51; spec 2026-10-12-section-acier REQ-004 to REQ-006, REQ-013, D-05, D-09, D-12, D-17; docs/domain/steel.md).

**Source.** `Woodcore-Datei/steel/<id>.json` (`Project.steel_dir`), one file per check, schema `steel-source` 1.0 (schemas/steel-source.schema.json), read by this module alone: `id` (its file name), optional `name`, `label`, `group`, the `kind` (`KINDS`), the optional `position`, then `profile` -- null to follow the position's section, or `{type, dimension}` stated, an SZS C5 code and its size («IPE», «360») or USR and a free profile's id --, `grade` (null follows the position's strength class, else a grade of SIA 263 Tabelle 1), and the design forces `{value, unit}`, signed, tension positive: `N`, `M_y`, `M_z`, `V_z`, `V_y`, and for a tension the net area `A_net` (mm², optional). A field may follow a variable of the export (`links`, docs/domain/variable-links.md), schema 1.1.

**What the project lacks never stops** (the v0.33 rule): `resolve` gives the record of one source against the positions -- the profile and the grade each followed or stated (`profile_from`, `grade_from`), the section's values (domains/steel_section.py), `calculable` and its `reason`. A position gone, a section that is no steel one, a free profile not drawn, a designation the tables do not carry, a grade Tabelle 1 does not give: the record is exported `calculable: false` with its reason, and `#show-check-steel` prints it. **A malformed source stops**, naming the file and the field.

**Computed once, in Python** (D-09). `compute` is the check of domains/steel_resistance.py, and its rows are what the export writes and Typst prints (`#show-check-steel`, lib/steel.typ): no second calculation, no test holding two equal -- the timber checks' arrangement reversed for steel, the connectors' kept (docs/decisions.md).
"""

import json
import re
from pathlib import Path

import engine
import project
import validation
from domains._common import fail as _fail, is_number as _number  # one copy of the domains' helpers (spec 2026-10-19-base-saine-nettoyage, G4)
from domains import links, profile as free_profile, section as position_section, steel_resistance, steel_section
from norms import sia263

SOURCE_SCHEMA = "steel-source"
EXPORT_SCHEMA = "steel"
SOURCE_SCHEMA_VERSION = "1.0"
LINKED_SCHEMA_VERSION = "1.1"
SOURCE_SCHEMA_VERSIONS = (SOURCE_SCHEMA_VERSION, LINKED_SCHEMA_VERSION)
# 1.1 (v0.120, spec 2026-10-19-base-saine-nettoyage C1, C2): the rows built by engine.Calculation, and a value entered citing the clause it serves -- 1.0 is still read
EXPORT_SCHEMA_VERSION = "1.2"   # 1.2: no level on a line, lib/line-levels.json saying it (spec 2026-10-20-indices-et-niveaux, UI-002); 1.0 and 1.1 still read
EXPORT_FILE = "steel.json"
DOMAIN = "steel"

# Every kind a source may name -- lot 1 built, the others refused as «not implemented yet» rather than unknown (spec D-08).
KINDS = ("class", "tension", "compression", "bending", "shear", "buckling", "lateral-torsional", "interaction", "bolts", "welds", "splice")
IMPLEMENTED = steel_resistance.KINDS

ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.+-]*$")
FORCES = ("N", "V_z", "V_y")
MOMENTS = ("M_y", "M_z")
FORCE_UNITS = {"kN": 1e3, "N": 1.0, "MN": 1e6}
MOMENT_UNITS = {"kNm": 1e6, "Nm": 1e3, "MNm": 1e9}
# the fields each kind reads, besides the profile and the grade
FIELDS = {
    "class": ("N", "M_y", "M_z"),
    "tension": ("N",),
    "compression": ("N",),
    "bending": ("N", "M_y", "M_z"),
    "shear": ("V_z", "V_y", "M_y"),
}
# The fields a variable of the export may fill, with the unit each is written in -- None where the field's own {value, unit} says it.
LINKABLE = {"N": None, "M_y": None, "M_z": None, "V_z": None, "V_y": None, "A_net": "mm²"}


# --- the source ---------------------------------------------------------------

def _dir(here=None):
    return (here or project.current()).steel_dir


def source_paths(here=None):
    directory = _dir(here)
    return sorted(directory.glob("*.json")) if directory.is_dir() else []


def _quantity(src, key, units, where):
    value = src.get(key)
    if value is None:
        return
    if not isinstance(value, dict) or not _number(value.get("value")) or value.get("unit") not in units:
        _fail(where, "%s is %r -- expected {value, unit} with the unit %s" % (key, value, " or ".join(units)))


def check_source(src, where="steel"):
    """Everything that makes a source malformed, as a ValidationError naming `where` and the field. Nothing about the project is checked here: that is `resolve`'s, and never a stop."""
    if not isinstance(src, dict):
        _fail(where, "is not a JSON object")
    version = src.get("schema_version")
    if version not in SOURCE_SCHEMA_VERSIONS:
        _fail(where, "schema_version %r -- expected one of %s" % (version, ", ".join(SOURCE_SCHEMA_VERSIONS)))
    # the contract first, schemas/steel-source.schema.json, as every other domain reads its own (v0.120, C3); the checks below say in the engineer's words what it leaves out
    validation.validate_structure(src, "steel-source", where)
    cid = src.get("id")
    if not isinstance(cid, str) or not ID_PATTERN.match(cid):
        _fail(where, "id %r -- letters, digits and _ . + - only" % (cid,))
    kind = src.get("kind")
    if kind not in KINDS:
        _fail(where, "kind %r -- one of %s" % (kind, ", ".join(KINDS)))
    if kind not in IMPLEMENTED:
        _fail(where, "kind %r is not implemented yet -- %s are" % (kind, ", ".join(IMPLEMENTED)))
    for key in ("name", "label", "group"):
        if src.get(key) is not None and not isinstance(src[key], str):
            _fail(where, "%s is %r -- expected text" % (key, src[key]))
    pos = src.get("position")
    if pos is not None and (not isinstance(pos, str) or not pos.strip()):
        _fail(where, "position is %r -- a position's id, or null" % (pos,))
    prof = src.get("profile")
    if prof is not None:
        if not isinstance(prof, dict) or not isinstance(prof.get("type"), str) or not isinstance(prof.get("dimension"), str):
            _fail(where, "profile is %r -- {type, dimension}, or null to follow the position" % (prof,))
        code = position_section.code_of(prof["type"])
        if code is None or position_section.kind_of(code) == "timber":
            _fail(where, "profile type %r is not a steel one -- an SZS C5 code (IPE, HEA, ROR ...) or USR" % prof["type"])
        try:
            position_section.parse(code, prof["dimension"], "", where="%s: profile" % where)
        except validation.ValidationError as exc:
            _fail(where, str(exc))
    grade = src.get("grade")
    if grade is not None and grade not in sia263.grades():
        _fail(where, "grade %r is not a grade of SIA 263 Tabelle 1 -- %s, or null to follow the position" % (grade, ", ".join(sia263.grades())))
    for key in FORCES:
        _quantity(src, key, FORCE_UNITS, where)
    for key in MOMENTS:
        _quantity(src, key, MOMENT_UNITS, where)
    if src.get("A_net") is not None and (not _number(src["A_net"]) or src["A_net"] <= 0):
        _fail(where, "A_net is %r -- the net area in mm², above 0, or null" % (src["A_net"],))
    if links.LINKS in src and version == SOURCE_SCHEMA_VERSION:
        _fail(where, "links needs schema_version %s" % LINKED_SCHEMA_VERSION)
    links.check_links(src, LINKABLE, lambda message: _fail(where, message), "the check")
    return src


def read_source(path):
    path = Path(path)
    where = "steel/%s" % path.name
    try:
        src = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        _fail(where, "cannot be read as JSON -- %s" % exc)
    check_source(src, where)
    if src["id"] != path.stem:
        _fail(where, "id %r is not its file name %r -- the id is the file name" % (src["id"], path.stem))
    return src


def stamp_version(src):
    """The schema_version a source is saved at: 1.1 with a link, 1.0 without."""
    if not links.links_of(src):
        src.pop(links.LINKS, None)
    src["schema_version"] = LINKED_SCHEMA_VERSION if links.links_of(src) else SOURCE_SCHEMA_VERSION
    return src


def list_sources(here=None):
    out = []
    for path in source_paths(here):
        try:
            src = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if isinstance(src, dict):
            src.setdefault("id", path.stem)
            out.append(src)
    return out


def new_source(cid, kind="tension"):
    """A new source: no position, profile and grade to follow one or to be stated, and the forces of its kind -- a tension of 100 kN, a compression of −100 kN, a bending of 50 kNm, a shear of 100 kN."""
    src = {"schema_version": SOURCE_SCHEMA_VERSION, "id": cid, "name": "", "label": "", "group": "", "kind": kind,
           "position": None, "profile": None, "grade": None}
    defaults = {
        "class": {"N": {"value": 0, "unit": "kN"}, "M_y": {"value": 0, "unit": "kNm"}, "M_z": None},
        "tension": {"N": {"value": 100, "unit": "kN"}, "A_net": None},
        "compression": {"N": {"value": -100, "unit": "kN"}},
        "bending": {"N": {"value": 0, "unit": "kN"}, "M_y": {"value": 50, "unit": "kNm"}, "M_z": None},
        "shear": {"V_z": {"value": 100, "unit": "kN"}, "V_y": None, "M_y": None},
    }
    src.update(defaults.get(kind, {}))
    return src


# --- what the project gives it ---------------------------------------------------

def _value(src, key):
    """A force or a moment of the source in N or Nmm, 0 where absent."""
    q = src.get(key)
    if not q:
        return 0.0
    return float(q["value"]) * (MOMENT_UNITS if key in MOMENTS else FORCE_UNITS)[q["unit"]]


def section_of(section_record, here=None):
    """The steel section a position's or a source's section record gives -- (section, None) or (None, reason): an SZS C5 designation out of its table, a free profile out of Woodcore-Datei/profiles/."""
    if not section_record:
        return None, "no section"
    kind = section_record.get("kind")
    if kind == "steel":
        sec = steel_section.of_c5(section_record["type"], section_record["dims"])
        if sec is None:
            return None, "%s is not in the tables of SZS C5:2018 this program carries" % section_record["text"]
        return sec, None
    if kind == "user":
        resolved = free_profile.resolve(section_record["id"], here)
        if resolved is None:
            return None, "the free profile %s is not drawn -- Woodcore-Datei/profiles/ has no %s.json (the «Profilés» tab)" % (section_record["id"], section_record["id"])
        return steel_section.of_free(resolved), None
    return None, "%s is not a steel section" % section_record.get("text", "")


def resolve(src, positions, values=None, here=None):
    """The record of one checked source against `positions` ({id: position record}): its forces in N and Nmm, its section and grade, each followed or stated, `calculable` and `reason`, and the warnings it earned. Nothing stops but a malformed free profile's file."""
    cid = src["id"]
    where = "steel/%s.json" % cid
    warnings, provenance = [], {}
    if values is not None:
        src, provenance, notes = links.apply_links(src, values, LINKABLE, where)
        warnings.extend(notes)
    by_id = {k.lower(): v for k, v in (positions or {}).items()}
    pid = src.get("position")
    position = None
    if pid is not None:
        position = by_id.get(pid.lower())
        if position is None:
            warnings.append(engine.Note("steel_position_missing", "%s: position %s is not a position of the project -- the values it would give are not there" % (where, pid),
                                        check=cid, position=pid))
    reason = None
    section_record, profile_from = None, None
    if src.get("profile"):
        code = position_section.code_of(src["profile"]["type"])
        section_record = position_section.parse(code, src["profile"]["dimension"], "", where=where)
        profile_from = "stated"
    elif position is not None and position.get("section"):
        section_record = position["section"]
        profile_from = "position"
    sec = None
    if section_record is None:
        reason = "no profile -- state one, or name a position whose section is a steel profile"
    else:
        sec, why = section_of(section_record, here)
        if why:
            reason = why
    grade, grade_from = src.get("grade"), "stated" if src.get("grade") else None
    if grade is None and position is not None:
        grade = (position.get("strength_class") or "").strip() or None
        grade_from = "position" if grade else None
    if reason is None and grade is None:
        reason = "no steel grade -- state one, or give the position a strength class of SIA 263 Tabelle 1"
    elif reason is None and grade not in sia263.grades():
        reason = "%s is not a grade of SIA 263 Tabelle 1 (%s)" % (grade, ", ".join(sia263.grades()))
    record = {
        "id": cid, "name": src.get("name") or "", "label": src.get("label") or "", "group": src.get("group") or "",
        "kind": src["kind"], "position": pid, "position_found": position is not None,
        "profile": src.get("profile"), "profile_from": profile_from,
        "designation": sec["designation"] if sec else (section_record or {}).get("text", ""),
        "grade": grade, "grade_from": grade_from,
        "N": _value(src, "N"), "M_y": _value(src, "M_y"), "M_z": _value(src, "M_z"), "V_z": _value(src, "V_z"), "V_y": _value(src, "V_y"),
        "A_net": src.get("A_net"),
        "section": sec, "section_source": ("norm:SZS C5:2018, %s" % sec["norm_ref"].split(", ", 1)[1]) if sec and sec["source"] == "c5" else "woodcore:profiles/%s.json" % (section_record or {}).get("id", ""),
        "calculable": reason is None, "reason": reason or "", "warnings": warnings,
    }
    if reason is None:
        record.update(_kind_reason(record))
    if provenance:
        record["links"] = provenance
    if sec and sec["anomalies"]:
        for key, why in sec["anomalies"].items():
            warnings.append(engine.Note("steel_c5_anomaly", "%s: %s -- %s" % (where, sec["designation"], why), check=cid, designation=sec["designation"], value=key))
    if not record["calculable"]:
        warnings.append(engine.Note("steel_not_calculable", "%s: not calculable -- %s" % (where, record["reason"]), check=cid, reason=record["reason"]))
    return record


def _kind_reason(record):
    """What a kind needs that the record does not give: a tension N > 0, a compression N < 0, a bending a moment, a shear a shear force."""
    kind = record["kind"]
    if kind == "tension" and record["N"] <= 0:
        return {"calculable": False, "reason": "a tension needs N above 0 (tension positive)"}
    if kind == "compression" and record["N"] >= 0:
        return {"calculable": False, "reason": "a compression needs N below 0 (tension positive)"}
    if kind == "bending" and not (record["M_y"] or record["M_z"]):
        return {"calculable": False, "reason": "a bending needs M_y or M_z"}
    if kind == "shear" and not (record["V_z"] or record["V_y"]):
        return {"calculable": False, "reason": "a shear needs V_z or V_y"}
    return {}


def compute(record):
    """The check of a calculable record -- {"calc": {vars, steps}, "eta", "ok", "relation", "ratio", "results", "classification", "tables", "notes"} -- or {"reason"} where the norm offers no way through (class 4 ...)."""
    if not record["calculable"]:
        return {"reason": record["reason"]}
    out = steel_resistance.check(record)
    if "reason" in out:
        return out
    out["ok"] = out["eta"] is None or out["eta"] <= 1 + 1e-9
    return out


# --- the export ---------------------------------------------------------------------

def _public_section(sec):
    """What the export carries of a section: its designation and where it came from, its values in mm, and its walls' sizes -- what the page's level-3 lines and the window read."""
    if not sec:
        return None
    keep = ("source", "code", "shape", "designation", "norm_ref", "A", "A_v", "A_v_z", "A_v_y", "A_w", "I_y", "I_z", "W_el_y", "W_el_z",
            "W_pl_y", "W_pl_z", "i_y", "i_z", "K", "h", "b", "t_w", "t_f", "t", "r", "D", "h_1", "t_max")
    return {k: sec.get(k) for k in keep if sec.get(k) is not None}


def exported(record):
    """The record as data/steel.json holds it: its fields, and for a calculable one its calculation -- vars, steps, tables, results, eta, ok, relation, ratio, class."""
    out = {k: v for k, v in record.items() if k not in ("section", "section_source", "warnings")}
    for key in ("N", "V_z", "V_y"):
        out[key] = round(record[key] * 1e-3, 10)
    for key in MOMENTS:
        out[key] = round(record[key] * 1e-6, 10)
    out["section"] = _public_section(record["section"])
    out["warnings"] = [str(n) for n in record["warnings"]]
    if record["calculable"]:
        result = compute(record)
        if "reason" in result:
            out["calculable"], out["reason"] = False, result["reason"]
        else:
            out.update(result["calc"])
            out["results"] = result["results"]
            out["tables"] = result.get("tables", [])
            out["eta"] = result["eta"]
            out["ok"] = result["ok"]
            out["relation"] = result["relation"]
            out["ratio"] = result["ratio"]
            out["notes"] = result.get("notes", [])
            if result.get("classification"):
                out["class"] = result["classification"]["class"]
    return out


def empty():
    return {"schema_version": EXPORT_SCHEMA_VERSION, "checks": {}}


def prepare(here, positions, values=None):
    """Every steel check of `here`, read, checked, resolved and computed, as data/steel.json holds it. Nothing is written."""
    checks, seen = {}, {}
    for path in source_paths(here):
        src = read_source(path)
        lower = src["id"].lower()
        if lower in seen:
            _fail("steel/%s" % path.name, "id %r is also %s's -- ids differ by more than their case" % (src["id"], seen[lower]))
        seen[lower] = path.name
        checks[src["id"]] = exported(resolve(src, positions, values, here))
    data = {"schema_version": EXPORT_SCHEMA_VERSION, "checks": checks}
    validation.validate_structure(data, EXPORT_SCHEMA)
    for cid, record in checks.items():
        if record.get("calculable"):
            validation._check_calculation(record, "steel.json.checks.%s" % cid)
    return data


def warnings_of(data):
    return [w for record in data["checks"].values() for w in record.get("warnings", [])]


def write(data, data_dir):
    engine.write_json(Path(data_dir) / EXPORT_FILE, data)


def export(here=None):
    """prepare() then write(), against the positions the last export wrote -- what Woodcore runs when a check is saved."""
    from domains import connector
    here = here or project.current()
    import variable_sources
    data = prepare(here, connector.known_positions(here.data_dir), variable_sources.known_values(here.data_dir))
    write(data, here.data_dir)
    # a steel check is written out when it is first saved, as a member check is (spec 2026-10-21-commandes-typst-refonte, REQ-017), and the index of the domains lists it
    from domains import formula_domain, unfold
    if unfold.unfold_domains(here, "steel", data):
        formula_domain.export(here)
    return data


def references(record):
    """What an exported steel check names, [(kind, id, field)]: its position, and the profile it is computed with (domains/dependency_graph.py, spec 2026-10-21-graphe-dependances, ARCH-RISK-1103)."""
    out = [("position", record["position"], "position")] if record.get("position") else []
    if record.get("profile"):
        out.append(("profile", record["profile"], "profile"))
    return out


# --- written out as a domain of its own (spec 2026-10-21-commandes-typst-refonte, REQ-017, ARCH-011) ----------------------

def is_unfolded(record):
    """Whether the exported steel check `record` is written out as a domain of its own, `Steel-checks/<Kind>/<id>.typ` (calc/domains/unfold.py): every one the export computed -- one that cannot be computed is said by its reason and printed by nothing."""
    return bool(record.get("calculable")) and bool(record.get("vars"))


def form_of(record):
    """The form an unfolded steel check is written for, {kind, form, version} -- what the base keeps and `#domain` compares (REQ-012): its kind, and the rows it computes, which a branch of SIA 263 changes (a bending with a normal force, a shear beyond 0.5 V_Rd, the class of the section), named by their digest; None where it is not written out."""
    import sync
    from domains import unfold
    if not is_unfolded(record):
        return None
    rows = sync.digest(",".join(record["vars"]))[:6]
    return {"kind": "steel-" + record["kind"], "form": "%s %s" % (record["kind"], rows), "version": unfold.GENERATOR_VERSION}


def unfolded_lines(record):
    """The vars of an exported steel check as the unfolded file writes them (calc/domains/line_keys.py `calc_lines`): each worked out an `#eq` where its step's formula computes it in the registry's keys, every other a literal checked by `domain: ("steel", id)`."""
    from domains import line_keys
    return line_keys.calc_lines(record)


def ratio_keys(record):
    """The utilisation's formula in the registry's keys where it computes the check's η as `#eq` computes it -- the export writes it in keys already (`ratio`) --, else None, and the unfolded file writes η as a literal."""
    from domains import line_keys
    values = {line["key"]: (line["value"], line.get("unit") or "") for line in unfolded_lines(record) if isinstance(line["value"], (int, float))}
    if record.get("eta") is None or not record.get("ratio"):
        return None
    return record["ratio"] if line_keys.computes(record["ratio"], values, "eta", record["eta"], "") else None
