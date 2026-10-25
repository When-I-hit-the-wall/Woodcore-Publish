"""The engineer's own library of materials, for every project of his computer (spec docs/requirements/active/2026-10-24-onglet-materiaux.md, REQ-001 to REQ-003, REQ-006, REQ-007, REQ-012; issue #110).

It lives in `usersettings.materials_dir()` -- `%APPDATA%\\Woodcore\\materials\\` -- and not in a project: `materials.json` (schemas/user-materials.schema.json) and the PDFs of its sources in `sources/`, each a copy, never the file the engineer chose. Every write is checked first and written whole (`engine.write_json`); the file is read again just before, so that two windows of Woodcore lose nothing of each other's. A file this module cannot read is never written over: it stops, naming the file and the field, and the tab shows it read only.

A material's shape is `materials_contract`'s. Its id is drawn once (`u-<8 hex>`) and never changed by a rename, so that a project's copy and a layer keep naming it. No Qt here.
"""

import hashlib
import json
import re
import secrets
import shutil
import unicodedata
from pathlib import Path

import engine
import usersettings
import validation
from domains import materials_contract as contract

SCHEMA = "user-materials"
SCHEMA_VERSION = "1.0"
FILE = "materials.json"
SOURCES = "sources"


def folder():
    return usersettings.materials_dir()


def library_file():
    return folder() / FILE


def sources_dir():
    return folder() / SOURCES


def empty():
    return {"schema_version": SCHEMA_VERSION, "materials": []}


def _products():
    from norms import sia265_1
    return set(sia265_1.products())


def check(data, where=FILE):
    """The library's shape (its schema), then each material's rules (`materials_contract.check_material`) and one id each -- a defect stops, naming the file and the field."""
    if not isinstance(data, dict) or data.get("schema_version") != SCHEMA_VERSION:
        found = data.get("schema_version") if isinstance(data, dict) else data
        raise validation.ValidationError("%s: schema_version is %r -- expected %r" % (where, found, SCHEMA_VERSION))
    validation.validate_structure(data, SCHEMA, where)
    products = _products()
    for m in data["materials"]:
        contract.check_material(m, where + ": materials", products)
        if not contract.USER_ID.match(m["id"]):
            raise validation.ValidationError("%s: materials[%s]: an id of the engineer's library is u-<8 hex>" % (where, m["id"]))
    contract.check_ids_unique(data["materials"], where)


def read():
    """The library, checked -- empty where there is none yet. A file that cannot be read stops, naming it."""
    path = library_file()
    if not path.exists():
        return empty()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise validation.ValidationError("%s: cannot be read as JSON -- %s" % (path, exc))
    check(data, str(path))
    return data


def materials():
    return read()["materials"]


def find(material_id):
    return next((m for m in materials() if m["id"] == material_id), None)


def new_id(taken=()):
    """A fresh id, `u-<8 hex>`, none of `taken`."""
    taken = set(taken)
    while True:
        candidate = "u-" + secrets.token_hex(4)
        if candidate not in taken:
            return candidate


def _write(data):
    check(data, str(library_file()))
    return engine.write_json(library_file(), data)


def save(material):
    """`material` written into the library -- in place of the one of its id, or added. The library is read again first: another window's save is kept. Refuses a shipped material (its id is not `u-…`). Returns the material as written."""
    if not contract.USER_ID.match(str(material.get("id") or "")):
        raise validation.ValidationError("%s: a material shipped with Woodcore is read only -- duplicate it into your library" % material.get("id"))
    data = read()
    others = [m for m in data["materials"] if m["id"] != material["id"]]
    index = next((i for i, m in enumerate(data["materials"]) if m["id"] == material["id"]), len(others))
    others.insert(index, material)
    data["materials"] = others
    _write(data)
    return material


def save_all(new):
    """Several materials added at once (a project's 1.0 poured in, materials_migrate): one read, one write."""
    data = read()
    ids = {m["id"] for m in data["materials"]}
    data["materials"] = data["materials"] + [m for m in new if m["id"] not in ids]
    _write(data)


def delete(material_id):
    """The material taken out of the library, and its PDF with it where no other material names it. The projects' copies are not touched. Returns the material removed, or None."""
    data = read()
    gone = next((m for m in data["materials"] if m["id"] == material_id), None)
    if gone is None:
        return None
    data["materials"] = [m for m in data["materials"] if m["id"] != material_id]
    _write(data)
    pdf = (gone.get("source") or {}).get("file")
    if pdf and not any((m.get("source") or {}).get("file") == pdf for m in data["materials"]):
        try:
            (folder() / pdf).unlink()
        except OSError:
            pass  # a PDF that cannot be removed costs some room, nothing else
    return gone


def blank(kind, category=None):
    """A new material of `kind` (member, panel, other), not yet saved: an id, an empty name, the category its kind most often has."""
    if kind not in contract.TYPES:
        raise validation.ValidationError("type %r -- %s" % (kind, ", ".join(contract.TYPES)))
    m = {"id": new_id(m["id"] for m in materials()), "type": kind, "names": {"fr": "", "de": "", "en": ""},
         "category": category or {"member": "wood", "panel": "board", "other": "ins"}[kind], "comment": "", "source": {"kind": "none"}}
    if kind == "member":
        m.update(family="softwood", values={})
    if kind == "panel":
        m.update(product=None, isotropic=False, columns=[], thickness=None, rho_k=[None], grid={})
    return m


def duplicate(material, label):
    """A copy of `material` -- shipped or the engineer's -- as a material of the engineer's own, under a new id: the same values, its comment saying where it comes from («← SIA 265», `label`), a shipped material's source kept as the reference it was (REQ-006). Not saved."""
    import copy
    m = copy.deepcopy(material)
    m["id"] = new_id(x["id"] for x in materials())
    note = "← %s" % label
    m["comment"] = note + ("\n" + m["comment"] if m.get("comment") else "")
    source = m.get("source") or {"kind": "none"}
    if source.get("kind") in ("norm", "book"):
        m["source"] = {"kind": "book", "ref": source.get("ref") or label}
    m.pop("example", None)
    return m


def _clean(stem):
    """A file's name made safe for any disk: ASCII, lower case, words joined by «-»."""
    text = unicodedata.normalize("NFKD", stem).encode("ascii", "ignore").decode("ascii").lower()
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text or "source"


def _digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def import_pdf(path):
    """A PDF chosen by the engineer, **copied** into the library's `sources/` under a clean name (REQ-012): `sources/<name>.pdf`, `-2`, `-3`… where another file has the name, the same file again where its bytes are already there. Returns the path relative to the library's folder, what a source names; the original is never read again."""
    path = Path(path)
    if path.suffix.lower() != ".pdf" or not path.is_file():
        raise validation.ValidationError("%s: not a PDF file" % path)
    target_dir = sources_dir()
    target_dir.mkdir(parents=True, exist_ok=True)
    stem, digest, n = _clean(path.stem), _digest(path), 1
    while True:
        name = "%s.pdf" % stem if n == 1 else "%s-%d.pdf" % (stem, n)
        target = target_dir / name
        if not target.exists():
            partial = target.with_name(target.name + ".part")
            shutil.copyfile(path, partial)
            partial.replace(target)
            break
        if _digest(target) == digest:
            break
        n += 1
    return "%s/%s" % (SOURCES, name)


def source_path(material):
    """The absolute path of a material's PDF in the library, or None."""
    rel = (material.get("source") or {}).get("file")
    return folder() / rel if rel else None
