"""One-off: the geometry a connector and a polar-moment calculation each carried is written out as a detail schema, and the two sources are left naming it (docs/domain/connectors.md §3.3nonies, docs/domain/connections.md §3.3quinquies, docs/domain/detail-schemas.md §3.3decies; plan 5 of je-souhaite-commencer-generic-valley.md).

Until v0.74 `connectors/<id>.json` and `connections/<id>.json` each held their own drawing of one physical joint -- the members with their b, h, view, angle, through, against and overhang, and a table of fastener coordinates. That is the duplication docs/architecture/principles.md §2 rule 1 forbids everywhere else, and neither form could draw what a detail actually needs. The «Schémas» module (v0.72) is the one drawing now; this script is what carries the existing sources over to it, once.

What it does, per source:

  * lays the old geometry out with `connection_svg.layout()`, the very code that drew it, **turned into the connection's own frame** (orientation = the reference member at 0 degrees, so the page's x is the reference member's grain and the page coordinates ARE the connection coordinates);
  * writes each member out as a `linear` element -- the centre line of the band that was drawn for it, its `width` the band's width, its `view` and its `position` as they stood;
  * writes each fastener out as a `connectors` marker of the source's own kind (a connection, which does not say what kind of fastener it has, gets its connector's kind, else the default);
  * writes a `centre` aid where a manual rotation centre stood, and leaves the connection turning about it by id;
  * rewrites the source at its new schema version, naming the schema, its markers and, per member, its element.

⚠️ **A connection reuses its connector's schema when the two draw the same joint.** The plan says one schema per source; writing two identical ones for `SD_01` and `SD_01-8mm` would recreate, in the new folder, exactly the duplication this refactor removes. So a connection whose geometry is equal to its connector's -- to the tenth of a millimetre, `SAME_POINT` -- points at the connector's schema, and only one that genuinely draws a different joint gets one of its own.

⚠️ **It is not idempotent and does not need to be.** A source already at the new version is left alone and reported as such, so running it twice is safe; but it reads the OLD readers, so it must be run before those are removed. Run it from 000-Python:

    python calc/tools/migrate_to_schemas.py            # say what would change
    python calc/tools/migrate_to_schemas.py --write    # do it
"""

import argparse
import copy
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "calc"))

from domains import connection, connection_svg, connector  # noqa: E402
from domains import schema as schema_model  # noqa: E402

CONNECTORS = ROOT / "connectors"
CONNECTIONS = ROOT / "connections"
DETAILS = ROOT / "details"

# The versions this script converts FROM, per folder. A file already past them is left alone.
OLD_CONNECTOR = ("1.0", "1.1")
OLD_CONNECTION = ("1.0", "2.0", "2.1")

# The versions this script converts TO. Written out rather than read off the modules' own constants: this
# script runs while the OLD readers are still in place, so it must not depend on when those are bumped.
NEW_CONNECTOR = "2.0"
NEW_CONNECTION = "3.0"

# What a marker is called when the source says nothing about its kind -- a connection names no type of
# fastener at all, by design, so one whose connector cannot be read falls back to the commonest.
DEFAULT_KIND = "Stabdübel"


def _round(value):
    """A coordinate as the schema keeps it: two decimals, -0 written 0 -- schema.round_place's own precision."""
    return schema_model.round_place(float(value))


def _elements_of(source):
    """Each member of an old source as a `linear` schema element: the centre line of the band that was drawn for it, in the connection's own frame.

    The frame is forced by laying the drawing out with the reference member at 0 degrees on the page: `page_angles` then returns each member's angle from the reference member's grain, which is the connection frame's own x, so no second conversion is needed and a fastener's (x, z) is already where it belongs.
    """
    members = source.get("members", [])
    reference = source.get("reference", 1)
    shaped = dict(source)
    shaped["orientation"] = {"member": reference, "angle": 0}
    geometry = connection.analyse(shaped)
    drawing = connection_svg.layout(shaped, geometry)

    elements = []
    for j, member in enumerate(members):
        u = drawing["u"][j]
        start, end = drawing["spans"][j][2], drawing["end"]
        element = {
            "id": "E%d" % (j + 1),
            "kind": "linear",
            "points": [[_round(u[0] * start), _round(u[1] * start)],
                       [_round(u[0] * end), _round(u[1] * end)]],
            "view": member.get("view", "h"),
            "width": _round(drawing["widths"][j]),
        }
        if member.get("position"):
            element["position"] = member["position"]
        if member.get("name", "").strip():
            element["label"] = member["name"].strip()
        elements.append(element)
    return elements


def _markers_of(source, kind):
    return [{"id": "C%d" % (i + 1), "kind": kind, "x": _round(f["x"]), "z": _round(f["z"])}
            for i, f in enumerate(source.get("fasteners", []))]


def _aids_of(source):
    """A `centre` aid where a manual rotation centre stood -- so the connection can go on turning about it, by id."""
    centre = source.get("center") or {}
    if centre.get("mode") != "manual":
        return []
    return [{"id": "A1", "kind": "centre", "x": _round(centre.get("x", 0)), "z": _round(centre.get("z", 0))}]


def build_schema(source, sid, kind=DEFAULT_KIND, label=""):
    """The detail schema one old source draws, ready to be written to details/<sid>.json."""
    return {
        "schema_version": schema_model.SOURCE_SCHEMA_VERSION,
        "id": sid,
        "label": label or source.get("label", "") or sid,
        "group": source.get("group", ""),
        "elements": _elements_of(source),
        "connectors": _markers_of(source, kind),
        "aids": _aids_of(source),
        "dimensions": [],
    }


def _geometry_key(drawn):
    """What makes two schemas the same joint: the elements' lines and widths and the markers' places, rounded as they are stored. Labels, positions and ids are not part of it -- two calculations of one connector may name their pieces differently and still be drawn on one detail."""
    def points(entry):
        return tuple((round(p[0], 1), round(p[1], 1)) for p in entry["points"])

    return (
        tuple((points(e), round(e["width"], 1), e.get("view", "h")) for e in drawn["elements"]),
        tuple((round(m["x"], 1), round(m["z"], 1)) for m in drawn["connectors"]),
    )


def _read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path, payload, write):
    if write:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def migrate_connector(source, sid):
    """An old connector source at schema 2.0: its drawing block replaced by the schema it names."""
    out = {}
    for key, value in source.items():
        if key in ("reference", "orientation", "members", "fasteners"):
            continue
        out[key] = copy.deepcopy(value)
    out["schema_version"] = NEW_CONNECTOR
    out["schema"] = sid
    out["members"] = []
    for j, member in enumerate(source.get("members", [])):
        kept = {"name": member.get("name", ""), "element": "E%d" % (j + 1)}
        for key in ("role", "predrilled", "alpha", "t", "n", "a_1", "plates"):
            kept[key] = copy.deepcopy(member.get(key))
        material = member.get("material")
        # The element is the position reference now, so `material` says only whether the class is overridden.
        kept["material"] = {"grade": material["grade"]} if isinstance(material, dict) and material.get("grade") else None
        out["members"].append(kept)
    out["fasteners"] = ["C%d" % (i + 1) for i in range(len(source.get("fasteners", [])))]
    order = ["schema_version", "id", "group", "name", "variant", "type", "assembly", "label", "description",
             "diameter", "length", "dimension", "steel", "elements", "moisture_class", "conditions", "n_tot",
             "schema", "members", "fasteners", "dowel"]
    return {k: out[k] for k in order if k in out} | {k: v for k, v in out.items() if k not in order}


def migrate_connection(source, sid):
    """An old connection source at schema 3.0: its drawing block replaced by the schema it names."""
    out = {}
    for key, value in source.items():
        if key in ("orientation", "members", "fasteners"):
            continue
        out[key] = copy.deepcopy(value)
    out["schema_version"] = NEW_CONNECTION
    out["schema"] = sid
    out["members"] = [{"name": m.get("name", ""), "element": "E%d" % (j + 1)}
                      for j, m in enumerate(source.get("members", []))]
    out["fasteners"] = ["C%d" % (i + 1) for i in range(len(source.get("fasteners", [])))]
    centre = out.get("center") or {}
    if centre.get("mode") == "manual":
        out["center"] = {"mode": "aid", "aid": "A1"}
    order = ["schema_version", "id", "group", "connector", "label", "norm", "norm_ref",
             "schema", "reference", "members", "fasteners", "center", "directions"]
    return {k: out[k] for k in order if k in out} | {k: v for k, v in out.items() if k not in order}


def run(write=False, out=print):
    """Converts every source that still carries its own geometry. Returns the number of files it changed."""
    changed = 0
    schemas = {}      # id -> the schema written
    keys = {}         # geometry key -> the id it was written under
    kinds = {}        # connector id -> its kind of fastener, for the connections drawn on it
    connector_schema = {}  # connector id -> the schema its own source names

    for path in sorted(CONNECTORS.glob("*.json")):
        source = _read(path)
        cid = source.get("id", path.stem)
        if source.get("schema_version") not in OLD_CONNECTOR:
            out("  = %-24s already at %s" % (path.name, source.get("schema_version")))
            kinds[cid] = source.get("type", DEFAULT_KIND)
            connector_schema[cid] = source.get("schema", "")
            continue
        source = connector.upgrade_source(source)
        kinds[cid] = source.get("type", DEFAULT_KIND)
        drawn = build_schema(source, cid, kind=kinds[cid])
        schemas[cid] = drawn
        keys[_geometry_key(drawn)] = cid
        connector_schema[cid] = cid
        _write(DETAILS / ("%s.json" % cid), drawn, write)
        _write(path, migrate_connector(source, cid), write)
        changed += 2
        out("  + %-24s -> details/%s.json  (%d element(s), %d marker(s))"
            % (path.name, cid, len(drawn["elements"]), len(drawn["connectors"])))

    for path in sorted(CONNECTIONS.glob("*.json")):
        source = _read(path)
        if source.get("schema_version") not in OLD_CONNECTION:
            out("  = %-24s already at %s" % (path.name, source.get("schema_version")))
            continue
        source = connection.upgrade_source(source)
        cid = source.get("id", path.stem)
        kind = kinds.get(source.get("connector", ""), DEFAULT_KIND)
        drawn = build_schema(source, cid, kind=kind)
        key = _geometry_key(drawn)
        # The same joint its connector already draws: name that schema rather than write a second copy of it.
        sid = keys.get(key)
        if sid is None:
            sid = cid
            keys[key] = sid
            schemas[sid] = drawn
            _write(DETAILS / ("%s.json" % sid), drawn, write)
            changed += 1
            out("  + %-24s -> details/%s.json  (its own joint)" % (path.name, sid))
        else:
            out("  + %-24s -> details/%s.json  (the same joint, already written)" % (path.name, sid))
        _write(path, migrate_connection(source, sid), write)
        changed += 1

    out("%s %d file(s)" % ("wrote" if write else "would write", changed))
    return changed


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--write", action="store_true", help="write the files; without it, only say what would change")
    args = parser.parse_args(argv)
    run(write=args.write)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
