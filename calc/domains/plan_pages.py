"""The drawings made on a page of an imported document -- position plans and fire-protection plans alike (docs/domain/position-plans.md §3.3sexies, docs/domain/fire-plans.md §3.3vicies, v0.115).

A document of plans/documents/ (domains/plan_documents.py) is shared by two kinds of plan: the «Plan de positions» tab and the «Plan de protection incendie» tab each list it, each tick of a page there makes a plan of its own kind, and turning a page turns **both** kinds drawn on it. This module is what both tabs ask, so that neither knows how the other kind is stored. No Qt in it.

- `drawings_on(here, docid, page=None)`: the plans on a document, or on one of its pages -- the position plans whose background is that page, and the fire plans that are drawn on it themselves or that follow a position plan that is.
- `rotate_page(here, docid, page, delta)`: the page turned in its document, and every drawing on it turned with it (plan.rotate_source, fire.rotate_source), each written as its file; the ids of both kinds are returned.
- `export_drawings(here)`: the part of the export both kinds are in, run on its own: data/plans.json and data/fire.json, as a save in either tab runs it.
- `document_usage(here)` and `document_owner(doc, usage)`: which tab a document belongs to (v0.116) -- the one that imported it, its `owner`; for a document written before, the fire tab where only fire plans with a frame of their own are drawn on it, the position plans' otherwise. Each tab lists its own documents only; a fire plan may still follow a position plan, and turning that plan's page still turns it.

Reading is lenient, as the tabs' own lists are: a source that cannot be read is passed over, since a page's drawings are what the tab can show, not what the export would accept. Writing is not: every source is checked before the first file is written, so a refusal leaves the page and its drawings as they were.
"""

import json
from pathlib import Path

import engine
import positions_store
from domains import fire, plan, plan_documents


def _read(path):
    """A source file as a dictionary, or None where it cannot be read."""
    try:
        source = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return source if isinstance(source, dict) else None


def _on_page(background, docid, page):
    background = background or {}
    if background.get("document") != docid:
        return False
    return page is None or int(background.get("page", 1)) == int(page)


def position_plans_on(here, docid, page=None):
    """[(id, source)] of the position plans drawn on document `docid` -- on its page `page` where one is named --, in id order."""
    out = []
    for path in plan.source_paths(here.plans_dir):
        source = _read(path)
        if source is not None and _on_page(source.get("background"), docid, page):
            out.append((path.stem, source))
    return out


def fire_plans_on(here, docid, page=None):
    """[(id, source, frame)] of the fire-protection plans on document `docid` -- on its page `page` where one is named --, in id order: those drawn on the page themselves, and those that follow a position plan that is. `source` is the plan as it is read (upgraded to the current schema, nothing written), `frame` fire.frame_of()'s: what it is drawn over, the position plan's frame for one that follows."""
    frames = fire.plan_frames(here.plans_dir)
    out = []
    for path in fire.source_paths(here.fire_dir):
        source = fire.upgrade(_read(path))
        if not isinstance(source, dict) or "id" not in source:
            continue
        frame, problem = fire.frame_of(source, frames)
        if problem is None and _on_page(frame.get("background"), docid, page):
            out.append((path.stem, source, frame))
    return out


def drawings_on(here, docid, page=None):
    """{"position": [(id, source)], "fire": [(id, source, frame)]}: every plan on document `docid` -- on its page `page` where one is named. What the document view ticks and draws the crops of, what unticking a page archives and what turning it turns."""
    return {"position": position_plans_on(here, docid, page), "fire": fire_plans_on(here, docid, page)}


def _write_position(here, source):
    # the version the plan needs, as every writer of a plan asks it (plan.version_of): 1.6 was written here whatever the plan held until issue #54, so the page of a plan that holds a text could not be turned -- «holds a text at schema_version '1.6'»
    source = dict(source)
    source["schema_version"] = plan.version_of(source)
    target = here.plans_dir / f"{source['id']}.json"
    plan.check_source(source, target.name)
    return target, source


def _write_fire(here, source):
    source = dict(source)
    source["schema_version"] = fire.version_of(source)   # as a position plan's: 2.1 where it holds a text
    target = here.fire_dir / f"{source['id']}.json"
    fire.check_source(source, target.name)
    return target, source


def _dump(target, source):
    target.parent.mkdir(parents=True, exist_ok=True)
    engine.write_json(target, source)


def rotate_page(here, docid, page, delta):
    """Page `page` of document `docid` turned by `delta` degrees (a quarter turn, or several): the document written, and every plan drawn on that page, of either kind, turned with it so that the drawing stays on the architecture -- its sheet the turned page. Returns {"position": [ids], "fire": [ids]}.

    Everything is read, turned and checked before the first file is written, so a plan that would no longer pass its own checks -- or a document that cannot be read -- leaves the page and every drawing as they were. Raises plan_documents.DocumentError, validation.ValidationError or OSError, which the tab says in its own words."""
    doc = plan_documents.read(here, docid)
    plan_documents.set_rotation(doc, page, plan_documents.rotation(doc, page) + delta)
    quarters = int(delta) // 90
    drawings = drawings_on(here, docid, page)
    writes = []
    for _pid, source in drawings["position"]:
        sheet = source.get("sheet") or plan.BLANK_SHEET
        turned = plan.rotate_source(source, quarters, (float(sheet["width"]), float(sheet["height"])))
        writes.append(_write_position(here, turned))
    for _fid, source, frame in drawings["fire"]:
        # a plan that follows a position plan is drawn on that plan's sheet, which turns with the page by itself
        sheet = frame["sheet"]
        turned = fire.rotate_source(source, quarters, (float(sheet["width"]), float(sheet["height"])), frame=frame)
        writes.append(_write_fire(here, turned))
    plan_documents.write(here, doc)
    for target, source in writes:
        _dump(target, source)
    return {"position": [pid for pid, _s in drawings["position"]], "fire": [fid for fid, _s, _f in drawings["fire"]]}


def document_usage(here):
    """{docid: {"position": n, "fire_own": n, "fire_follow": n}}: how many plans of each kind are drawn on each document -- the position plans whose background names it, the fire plans drawn on it with a frame of their own, and those that follow a position plan drawn on it. Read once for every document, which is what listing the documents of a tab asks."""
    usage = {}

    def count(docid, key):
        if docid:
            usage.setdefault(docid, {"position": 0, "fire_own": 0, "fire_follow": 0})[key] += 1

    on_document = {}
    for path in plan.source_paths(here.plans_dir):
        source = _read(path)
        if source is not None:
            docid = (source.get("background") or {}).get("document")
            on_document[path.stem] = docid
            count(docid, "position")
    for path in fire.source_paths(here.fire_dir):
        source = _read(path)
        if source is None:
            continue
        followed = fire.follows(source)
        if followed is not None:
            count(on_document.get(followed), "fire_follow")
        else:
            count((source.get("background") or {}).get("document"), "fire_own")
    return usage


def document_owner(doc, usage=None):
    """The tab document `doc` belongs to (plan_documents.OWNERS, v0.116): the `owner` it names -- the tab that imported it --, else, for a document written before 1.1, `fire` where every plan drawn on it is a fire plan with a frame of its own (and there is one), and `plan` otherwise -- a document nothing is drawn on yet included. `usage` is document_usage's, for a document written before."""
    owner = (doc or {}).get("owner")
    if owner in plan_documents.OWNERS:
        return owner
    counts = (usage or {}).get((doc or {}).get("id"), {})
    return "fire" if counts.get("fire_own") and not counts.get("position") else "plan"


def export_drawings(here):
    """The export both kinds of plan are in, run on its own: the position plans (data/plans.json and data/plans/), then the fire-protection plans, which may follow them (data/fire.json and data/fire/). Returns the warnings of both, in that order. A failure -- a source that no longer validates, a background that was moved -- is raised before anything of the failing kind is written, as each kind's own export does."""
    rows = positions_store.read(here)
    positions = [row["position"] for row in rows]
    notes = list(plan.export(here.plans_dir, here.root, here.data_dir, positions, sections=positions_store.section_types(rows)))
    notes += fire.export(here.fire_dir, here.plans_dir, here.root, here.data_dir)
    return notes
