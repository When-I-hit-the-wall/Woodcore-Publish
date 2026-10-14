"""Switching a document's content template on a project that exists: the document and the template compared section by section, and what the engineer keeps, takes or drops written back -- the engineer's decision of 06.10.2026 (docs/domain/documents.md §3.3octodecies, «templates de fond»).

A content template (calc/doc_templates.py) is normally chosen when a project is created. Choosing another afterwards -- a short convention d'utilisation for a long one, a report for pre-dimensioning -- is rare and must be possible, and it must never cost the engineer what he has written: so it is not a copy but a **comparison**. `compare(here, mode, template)` unites the document's sections and the template's in one tree, each section with its `status`:

* `same` -- the two files hold the same text (line endings made LF, and for a CU or a BP the template's headings put at the depth the document has the section at);
* `differs` -- both have the section and its text is not the same;
* `document_only` -- the document has it and the template does not: something the engineer added, or a section of the template the document came from;
* `template_only` -- the template has it and the document does not.

Under each section stand its tagged objects (calc/typst_objects.py), each with a status of its own by object id -- what tells the engineer *where* two versions of a section part; it is information, and nothing is chosen object by object.

**What is chosen** is one word per section, `CHOICES[status]`, the defaults `DEFAULTS[status]`:

| status | choices | default |
|---|---|---|
| same | keep, drop | keep |
| differs | keep (the document's text), take (the template's), drop | keep |
| document_only | keep, drop | keep |
| template_only | take, skip | take |

`keep` leaves the document's section as it is (its file, its enabled flag); `take` writes the template's text in its place -- **the document's file archived first** -- or adds the template's section where the document has none; `drop` takes the document's section out of the document -- **its file archived**, never deleted; `skip` leaves a section of the template out. A CU's or a BP's chapters are nodes too (`kind == "group"`), compared by their chapter file (`Sections/<chapter>.typ`, whose heading is the chapter's title): their choice, `GROUP_CHOICES`, only says whose chapter file a chapter that differs keeps; whether a chapter is in the result at all follows its sections -- one with no section left goes, its file archived.

**The order** is the template's: the result takes the template's tree, and a section or a chapter only the document has is placed after the node that preceded it in the document, else first in its chapter where it was the first, else at the end of its chapter. For the report the nodes are its sections, compared by their name without their number (`001-einleitung.typ` and `004-einleitung.typ` are one section, `einleitung`) in the order of the `#include` lines, and the result is numbered again 001, 002 … as calc/templates.py numbers a report.

`apply(here, mode, comparison, choices)` writes the result: for a CU or a BP its structure.json, the section and chapter files -- a file kept at another depth than it had has its headings shifted to it (structure.fit_text) -- and the generated block of its entry; for the report its section files, numbered, and its `#include` lines. **All or nothing**: every file it touches is read before anything is written, and a failure puts every one back as it was, the archives it wrote removed. A file that changed on disk since the comparison was read refuses (`changed_meanwhile`), the comparison being out of date. A file it writes or moves is tried again on the PermissionError NextCloud's client gives while it holds a file it has just seen written. **Everything replaced or dropped is moved into `<document>/Sections/archives/<yymmdd-hhmmss>-<file>`**, as every «Supprimer» of Woodcore is.

After a write, what the documents share is brought to agree with the tags (calc/sharing.py `reconcile`): a section taken from a template that carries a shared block of a section another document holds is a **local edit** of this document (calc/sync.py `record_local_edit`), which the others then show as incoming -- never written into them.

A CU or a BP whose structure.json does not write its headings at the level they print at (`"headings": "absolute"`, structure.is_absolute) is refused (`legacy_headings`): its files and a template's would part at every heading. The window offers the conversion first (structure.make_absolute).

Every refusal is a ContentSwitchError -- a ValidationError -- with a `code` of CODES and the values it is about, so that a window writes its own sentence. There is no Qt in this file.
"""

import datetime
import os
import time
from dataclasses import dataclass, field
from pathlib import Path

import doc_templates
import engine
import structure
import typst_objects
import typst_paths
import validation

MODES = doc_templates.ALL_MODES
STATUSES = ("same", "differs", "document_only", "template_only")
# What a section may be given, by its status -- the first being what keeps the document as it stands where it has the section.
CHOICES = {
    "same": ("keep", "drop"),
    "differs": ("keep", "take", "drop"),
    "document_only": ("keep", "drop"),
    "template_only": ("take", "skip"),
}
DEFAULTS = {"same": "keep", "differs": "keep", "document_only": "keep", "template_only": "take"}
# What a CU's or a BP's chapter may be given: only whose chapter file it keeps where the two differ. Whether it is there at all follows its sections.
GROUP_CHOICES = {
    "same": ("keep",),
    "differs": ("keep", "take"),
    "document_only": ("keep",),
    "template_only": ("take",),
}
GROUP_DEFAULTS = {"same": "keep", "differs": "keep", "document_only": "keep", "template_only": "take"}
ARCHIVES = structure.ARCHIVES_DIR
# Every refusal of this module, by code: a window writes its own sentence for each.
CODES = (
    "bad_mode",            # a document that is none of cu, bp, rs (`mode`)
    "no_such_document",    # the project has no such document: a report laid out alone has no cu and no bp (`mode`)
    "bad_language",        # a language that is none of fr, de, en (`language`)
    "no_such_template",    # no content template of that name (`name`)
    "template_unusable",   # the template cannot be used, its own reason given (`ref`, `error`)
    "mode_mismatch",       # the template makes another document (`ref`, `mode`)
    "language_missing",    # the template does not exist in the document's language (`ref`, `language`, `languages`)
    "legacy_headings",     # a CU or a BP not laid out with its headings at their level -- the document's or the template's (`side`)
    "structure_unreadable",  # the document's structure.json cannot be read (`error`)
    "entry_unreadable",    # the document's entry file cannot be read, or its tags cannot (`file`)
    "section_unreadable",  # a section file of the document cannot be read (`file`)
    "kind_clash",          # one id is a chapter on one side and a section on the other (`id`)
    "duplicate_section",   # the report includes two sections of one name once their numbers are taken off (`name`)
    "unknown_node",        # a choice names no node of the comparison (`id`)
    "bad_choice",          # a choice its node's status does not allow (`id`, `choice`, `allowed`)
    "wrong_comparison",    # the comparison is of another document or another project (`mode`)
    "changed_meanwhile",   # a file of the document changed since the comparison was read (`file`)
    "invalid_result",      # what the choices would make is no valid structure (`error`)
    "too_deep",            # the result goes deeper than a structure may (`depth`)
    "write_failed",        # the disk refused: what was written has been put back (`error`)
)


class ContentSwitchError(validation.ValidationError):
    """A comparison or a switch that cannot be made, said by name: `code` one of CODES, `values` what it is about, beside the English sentence."""

    def __init__(self, message="", code="", **values):
        super().__init__(message)
        self.code = code
        self.values = values


def _refuse(code, message, **values):
    raise ContentSwitchError(message, code, **values)


# --- the comparison -------------------------------------------------------------------------------------

@dataclass
class ObjectNode:
    """One tagged object of a section, compared by its id: its type, its status and what each side calls it (None where that side has it not)."""
    id: str
    type: str
    status: str
    title_document: str = None
    title_template: str = None


@dataclass
class Node:
    """One node of a comparison: a chapter (`kind == "group"`, a CU's or a BP's) or a section (`"section"`).

    `id` is its key -- the section's or chapter's id for a CU or a BP, the section's name without its number for the report. `status` one of STATUSES. `title_document` / `title_template` its title on each side (a section's first heading, a chapter's heading in its file; None where that side has it not). `file_document` / `file_template` its file, relative to the document's folder and to the template's language folder. `enabled_document` / `enabled_template` whether each side prints it. `depth_document` / `depth_template` where it stands (1 at the top). `shared_with` what the document's structure.json says it is shared with. `children`: a chapter's nodes, or a section's ObjectNodes. `choices` and `default` what it may be given."""
    id: str
    kind: str
    status: str
    title_document: str = None
    title_template: str = None
    file_document: str = None
    file_template: str = None
    enabled_document: bool = None
    enabled_template: bool = None
    depth_document: int = None
    depth_template: int = None
    shared_with: tuple = ()
    children: list = field(default_factory=list)
    parent: str = None

    @property
    def choices(self):
        return (GROUP_CHOICES if self.kind == "group" else CHOICES)[self.status]

    @property
    def default(self):
        return (GROUP_DEFAULTS if self.kind == "group" else DEFAULTS)[self.status]


@dataclass
class Comparison:
    """The document `mode` of a project and the content template `template_ref`, compared in `language`: `nodes`, the tree, in the order the result takes (the template's, the document's own nodes put in). What `apply` writes from, with the texts it was read from: a file of the document that is not what it was then refuses the switch."""
    mode: str
    template_ref: str
    language: str
    nodes: list
    document_dir: Path
    template_dir: Path
    template_meta: dict = field(default_factory=dict)
    document_texts: dict = field(default_factory=dict)    # {relative path: text, None where absent} of every document file read
    template_texts: dict = field(default_factory=dict)    # {relative path: text} of every template file read
    document_structure: dict = None
    template_structure: dict = None

    def walk(self):
        """Every node, a chapter before its children, in order."""
        def visit(nodes):
            for node in nodes:
                yield node
                if node.kind == "group":
                    yield from visit(node.children)
        yield from visit(self.nodes)

    def sections(self):
        return [n for n in self.walk() if n.kind == "section"]

    def find(self, node_id):
        return next((n for n in self.walk() if n.id == node_id), None)

    def default_choices(self):
        """{id: choice} of every node at its default."""
        return {n.id: n.default for n in self.walk()}

    def counts(self):
        """{status: how many sections} -- what a window says above the tree."""
        out = {status: 0 for status in STATUSES}
        for node in self.sections():
            out[node.status] += 1
        return out


@dataclass
class Result:
    """What `apply` wrote: `written` the files written (new or rewritten), `archived` (from, to) of every file moved into archives/, `removed` the files taken away by a renumbering of the report (their text now under another name), `structure` and `entry` whether those were rewritten, `notes` what is worth knowing (engine.Notes) -- a sharing record that could not be written, a reconcile problem."""
    mode: str
    written: tuple = ()
    archived: tuple = ()
    removed: tuple = ()
    structure: bool = False
    entry: bool = False
    notes: tuple = ()

    @property
    def changed(self):
        return bool(self.written or self.archived or self.removed)


def _lf(text):
    return text.replace("\r\n", "\n").replace("\r", "\n") if text is not None else None


def _read(path):
    """A file's text with its line endings, or None where it is not there."""
    try:
        return typst_paths.read_text(path)
    except FileNotFoundError:
        return None


def _first_title(text):
    if not text:
        return None
    headings = structure.scan_headings(text)
    return headings[0].title if headings else None


def _objects(text):
    if not text or "woodcore:object" not in text:
        return []
    try:
        return typst_objects.objects(text)
    except ValueError:       # a file whose tags cannot be read (typst_objects.ParseError): nothing to compare object by object, the section's own status still says it differs
        return []


def _compare_objects(doc_text, tpl_text):
    """[ObjectNode] of two texts' objects, by id: the template's order, the document's own put after."""
    doc = {o.id: o for o in _objects(doc_text)}
    tpl = {o.id: o for o in _objects(tpl_text)}
    order = list(tpl) + [oid for oid in doc if oid not in tpl]
    out = []
    for oid in order:
        d, t = doc.get(oid), tpl.get(oid)
        if d and t:
            status = "same" if (d.type == t.type and d.written == t.written) else "differs"
        else:
            status = "document_only" if d else "template_only"
        out.append(ObjectNode(oid, (t or d).type, status,
                              typst_objects.object_title(d) if d else None, typst_objects.object_title(t) if t else None))
    return out


def _status(doc_text, tpl_text):
    if doc_text is None:
        return "template_only"
    if tpl_text is None:
        return "document_only"
    return "same" if _lf(doc_text) == _lf(tpl_text) else "differs"


def _check_project(here, mode):
    if mode not in MODES:
        _refuse("bad_mode", f"document {mode!r} -- expected one of {', '.join(MODES)}", mode=mode)
    if not (getattr(here, "has_modes", False) and mode in here.modes):
        _refuse("no_such_document", f"{here.name} has no {mode!r} document -- only a project laid out in three documents has one", mode=mode)


def _template_for(here, mode, template, language, settings):
    if isinstance(template, doc_templates.DocTemplate):
        found = template
    else:
        try:
            found = doc_templates.find(template or doc_templates.default_ref(mode), mode, settings)
        except doc_templates.DocTemplateError as exc:
            _refuse(exc.code or "no_such_template", str(exc), **exc.values)
    if found.error:
        _refuse("template_unusable", found.error, ref=found.ref, error=found.error)
    if found.mode != mode:
        _refuse("mode_mismatch", f"{found.ref} makes the document {found.mode!r}, and {mode!r} is being compared", ref=found.ref, mode=mode)
    if language not in found.languages:
        _refuse("language_missing", f"{found.ref} exists in {', '.join(found.languages)} and not in {language}",
                ref=found.ref, language=language, languages=list(found.languages))
    return found


def compare(here, mode, template=None, language=None, settings=None):
    """Document `mode` of project `here` compared with the content template `template` (a DocTemplate, or its reference -- the builtin standard one by default) in `language` (the document's own, structure.document_language, where not given). Returns a Comparison. Writes nothing.

    Refused: `bad_mode`, `no_such_document`, `bad_language`, `no_such_template`, `template_unusable`, `mode_mismatch`, `language_missing`, `legacy_headings`, `structure_unreadable`, `entry_unreadable`, `section_unreadable`, `kind_clash`, `duplicate_section`."""
    _check_project(here, mode)
    if language is None:
        language = structure.document_language(here, mode)
    if language not in structure.LANGUAGES:
        _refuse("bad_language", f"language {language!r} -- expected one of {', '.join(structure.LANGUAGES)}", language=language)
    found = _template_for(here, mode, template, language, settings)
    if mode == "rs":
        return _compare_report(here, found, language)
    return _compare_structured(here, mode, found, language)


def templates_for(here, mode, settings=None):
    """The content templates document `mode` of project `here` may be switched to: every one of every place that exists in the document's language (doc_templates.list_templates)."""
    _check_project(here, mode)
    return doc_templates.list_templates(mode, language=structure.document_language(here, mode), settings=settings)


# --- a CU or a BP ---------------------------------------------------------------------------------------

def _read_section(folder, rel, texts, code="section_unreadable"):
    try:
        text = _read(Path(folder) / rel)
    except (OSError, UnicodeDecodeError) as exc:
        _refuse(code, f"{rel}: could not be read -- {exc}", file=rel)
    texts[rel] = text
    return text


def _flat(source):
    """{id: (node, depth, parent id)} of a structure."""
    return {node["id"]: (node, depth, parent["id"] if parent else None) for node, depth, parent in structure.walk(source)}


def _merge_order(tpl_source, doc_source):
    """{parent id or None: [child ids]} of the result's tree: the template's, the document's own nodes put in after the node that preceded them in the document, first in their chapter where they were first, else at its end."""
    merged = {None: []}

    def fill(nodes, parent):
        for node in nodes:
            merged.setdefault(parent, []).append(node["id"])
            if "children" in node:
                merged.setdefault(node["id"], [])
                fill(node["children"], node["id"])

    fill(tpl_source["sections"], None)
    placed = {nid for ids in merged.values() for nid in ids}

    def visit(nodes, parent):
        previous = None
        for node in nodes:
            nid = node["id"]
            if nid not in placed:
                siblings = merged.setdefault(parent, [])
                if previous is None:
                    siblings.insert(0, nid)
                elif previous in siblings:
                    siblings.insert(siblings.index(previous) + 1, nid)
                else:
                    siblings.append(nid)
                placed.add(nid)
                if "children" in node:
                    merged.setdefault(nid, [])
            if "children" in node:
                visit(node["children"], nid)
            previous = nid

    visit(doc_source["sections"], None)
    return merged


def _compare_structured(here, mode, template, language):
    folder = here.document_dir(mode)
    tpl_folder = template.language_dir(language)
    document_texts, template_texts = {}, {}
    try:
        doc_source = structure.read(here.structure_file(mode))
    except validation.ValidationError as exc:
        _refuse("structure_unreadable", str(exc), error=str(exc))
    document_texts[structure.FILE] = _read(here.structure_file(mode))
    entry = here.document_typ(mode)
    try:
        document_texts[entry.name] = _read(entry)
    except (OSError, UnicodeDecodeError) as exc:
        _refuse("entry_unreadable", f"{entry.name}: could not be read -- {exc}", file=entry.name)
    if document_texts[entry.name] is None:
        _refuse("entry_unreadable", f"{entry.name}: is not there", file=entry.name)
    tpl_source = structure.read(template.structure_file(language))
    if not structure.is_absolute(doc_source):
        _refuse("legacy_headings", f"{mode}: its structure.json does not write its headings at the level they print at -- convert it first (structure.make_absolute)", side="document")
    if not structure.is_absolute(tpl_source):
        _refuse("legacy_headings", f"{template.ref}: its structure.json does not write its headings at the level they print at", side="template")
    doc_flat, tpl_flat = _flat(doc_source), _flat(tpl_source)
    for nid in set(doc_flat) & set(tpl_flat):
        if ("children" in doc_flat[nid][0]) != ("children" in tpl_flat[nid][0]):
            _refuse("kind_clash", f"{nid!r} is a chapter on one side and a section on the other -- the two cannot be compared", id=nid)
    order = _merge_order(tpl_source, doc_source)

    def file_of(node):
        return node["file"] if "file" in node else structure.group_file(node["id"])

    def build(parent):
        out = []
        for nid in order.get(parent, []):
            doc = doc_flat.get(nid)
            tpl = tpl_flat.get(nid)
            group = "children" in (doc or tpl)[0]
            doc_rel = file_of(doc[0]) if doc else None
            tpl_rel = file_of(tpl[0]) if tpl else None
            doc_text = _read_section(folder, doc_rel, document_texts) if doc else None
            if doc and doc_text is None and not group:
                doc_text = ""          # a section whose file nobody wrote: it is the document's all the same, and empty
            tpl_text = None
            if tpl:
                tpl_text = _read(tpl_folder / tpl_rel)
                template_texts[tpl_rel] = tpl_text
            fitted = structure.fit_text(tpl_text, doc[1]) if (doc and tpl_text is not None and doc_text) else tpl_text
            if doc and doc_text is None:      # a chapter's file missing on the document's side
                status = "differs" if tpl else "document_only"
            else:
                status = _status(doc_text if doc else None, fitted if tpl else None)
            if group:
                doc_title = (_first_title(doc_text) or structure.title_of(doc[0], language)) if doc else None
                tpl_title = (_first_title(tpl_text) or structure.title_of(tpl[0], language)) if tpl else None
            else:
                doc_title = (_first_title(doc_text) or nid) if doc else None
                tpl_title = (_first_title(tpl_text) or nid) if tpl else None
            node = Node(nid, "group" if group else "section", status, doc_title, tpl_title, doc_rel, tpl_rel,
                        bool(doc[0].get("enabled", True)) if doc else None, bool(tpl[0].get("enabled", True)) if tpl else None,
                        doc[1] if doc else None, tpl[1] if tpl else None,
                        tuple(doc[0].get("shared_with", ())) if doc else (), [], parent)
            node.children = build(nid) if group else _compare_objects(doc_text if doc else None, tpl_text if tpl else None)
            out.append(node)
        return out

    nodes = build(None)
    return Comparison(mode, template.ref, language, nodes, Path(folder), Path(tpl_folder), dict(template.meta),
                      document_texts, template_texts, doc_source, tpl_source)


# --- the report -----------------------------------------------------------------------------------------

def _report_items(text, where):
    """[(name, printed, stem)] of a report's include lines, refusing two sections of one name once their numbers are taken off."""
    items, seen = [], {}
    for name, printed in doc_templates.report_includes(text):
        stem = doc_templates.report_stem(name)
        if stem in seen:
            if seen[stem] == name:
                continue        # one file included twice: it is one section
            _refuse("duplicate_section", f"{where}: two sections are called {stem!r} once their numbers are taken off ({seen[stem]}, {name})", name=stem)
        seen[stem] = name
        items.append((name, printed, stem))
    return items


def _compare_report(here, template, language):
    folder = here.document_dir("rs")
    tpl_folder = template.language_dir(language)
    entry = here.document_typ("rs")
    document_texts, template_texts = {}, {}
    try:
        entry_text = _read(entry)
    except (OSError, UnicodeDecodeError) as exc:
        _refuse("entry_unreadable", f"{entry.name}: could not be read -- {exc}", file=entry.name)
    if entry_text is None:
        _refuse("entry_unreadable", f"{entry.name}: is not there", file=entry.name)
    document_texts[entry.name] = entry_text
    tpl_entry = template.entry_file(language)
    tpl_entry_text = _read(tpl_entry)
    template_texts[tpl_entry.name] = tpl_entry_text
    doc_items = _report_items(entry_text, entry.name)
    tpl_items = _report_items(tpl_entry_text, f"{template.ref}/{language}")
    doc_by = {stem: (name, printed) for name, printed, stem in doc_items}
    tpl_by = {stem: (name, printed) for name, printed, stem in tpl_items}
    # the template's order, the document's own put after the section that preceded them in it
    order = [stem for _n, _p, stem in tpl_items]
    previous = None
    for _name, _printed, stem in doc_items:
        if stem not in order:
            if previous is None:
                order.insert(0, stem)
            else:
                order.insert(order.index(previous) + 1, stem)
        previous = stem
    nodes = []
    for position, stem in enumerate(order, 1):
        doc = doc_by.get(stem)
        tpl = tpl_by.get(stem)
        doc_rel = f"{structure.SECTIONS_DIR}/{doc[0]}" if doc else None
        tpl_rel = f"{structure.SECTIONS_DIR}/{tpl[0]}" if tpl else None
        doc_text = _read_section(folder, doc_rel, document_texts) if doc else None
        if doc and doc_text is None:
            doc_text = ""
        tpl_text = None
        if tpl:
            tpl_text = _read(tpl_folder / tpl_rel)
            template_texts[tpl_rel] = tpl_text
        status = _status(doc_text if doc else None, tpl_text if tpl else None)
        nodes.append(Node(stem, "section", status, (_first_title(doc_text) or stem) if doc else None, (_first_title(tpl_text) or stem) if tpl else None,
                          doc_rel, tpl_rel, doc[1] if doc else None, tpl[1] if tpl else None, 1 if doc else None, 1 if tpl else None,
                          (), _compare_objects(doc_text if doc else None, tpl_text if tpl else None)))
    return Comparison("rs", template.ref, language, nodes, Path(folder), Path(tpl_folder), dict(template.meta), document_texts, template_texts)


# --- the choices ----------------------------------------------------------------------------------------

def resolve_choices(comparison, choices=None):
    """{id: choice} of every node of `comparison`: what `choices` names, its node's default for the rest. Refused: `unknown_node`, `bad_choice`."""
    choices = dict(choices or {})
    out = {}
    known = {n.id: n for n in comparison.walk()}
    for nid in choices:
        if nid not in known:
            _refuse("unknown_node", f"no section or chapter {nid!r} in the comparison", id=nid)
    for nid, node in known.items():
        choice = choices.get(nid, node.default)
        if choice not in node.choices:
            _refuse("bad_choice", f"{nid!r} is {node.status} and may be given {', '.join(node.choices)} -- not {choice!r}", id=nid, choice=choice, allowed=list(node.choices))
        out[nid] = choice
    return out


# --- writing, all or nothing ------------------------------------------------------------------------------

def _retry(action):
    for attempt in range(6):
        try:
            return action()
        except PermissionError:
            if attempt == 5:
                raise
            time.sleep(0.1 * (attempt + 1))


def _put(path, text):
    """`text` (a str, or bytes) written at `path`, line endings as they are, beside it and moved into place."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    part = path.with_name(path.name + ".switch")
    part.write_bytes(text if isinstance(text, bytes) else text.encode("utf-8"))
    _retry(lambda: os.replace(part, path))


def _remove(path):
    _retry(lambda: Path(path).unlink())


def _stamp():
    return datetime.datetime.now().strftime("%y%m%d-%H%M%S")


class _Plan:
    """What a switch writes: `writes` {path: text}, `archives` [(path, archive path)] -- each a copy of the file as it stands, the file then rewritten or removed --, `removes` the files taken away. `run` writes it all or puts everything back."""

    def __init__(self, folder):
        self.folder = Path(folder)
        self.writes = {}
        self.archives = []
        self.removes = []
        self._stamp = _stamp()
        self._taken = set()

    def archive(self, rel):
        path = self.folder / rel
        name = Path(rel).name
        archives = self.folder / structure.SECTIONS_DIR / ARCHIVES
        stem, suffix = Path(name).stem, Path(name).suffix
        target = archives / f"{self._stamp}-{name}"
        number = 2
        while target.exists() or target in self._taken:
            target = archives / f"{self._stamp}-{stem}-{number}{suffix}"
            number += 1
        self._taken.add(target)
        self.archives.append((path, target))
        return target

    def run(self):
        touched = list(dict.fromkeys([*self.writes, *[p for p, _a in self.archives], *self.removes]))
        before = {}
        for path in touched:
            before[path] = path.read_bytes() if path.exists() else None
        made = []
        new_dirs = sorted({t.parent for _p, t in self.archives if not t.parent.exists()}, key=lambda d: len(d.parts), reverse=True)
        try:
            for path, target in self.archives:
                data = before[path]
                if data is None:
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                _put(target, data)
                made.append(target)
            for path in self.removes:
                if path.exists() and path not in self.writes:
                    _remove(path)
            for path in [p for p, _a in self.archives]:
                if path.exists() and path not in self.writes:
                    _remove(path)
            for path, text in self.writes.items():
                if before.get(path) is not None and before[path] == text.encode("utf-8"):
                    continue
                _put(path, text)
        except BaseException as exc:
            for path, data in before.items():
                try:
                    if data is None:
                        if path.exists():
                            path.unlink()
                    elif not path.exists() or path.read_bytes() != data:
                        path.parent.mkdir(parents=True, exist_ok=True)
                        part = path.with_name(path.name + ".back")
                        part.write_bytes(data)
                        os.replace(part, path)
                except OSError:
                    pass
            for target in made:
                try:
                    target.unlink()
                except OSError:
                    pass
            for folder in new_dirs:       # an archives/ folder this switch made, empty again
                try:
                    folder.rmdir()
                except OSError:
                    pass
            for path in [*self.writes, *[t for _p, t in self.archives]]:
                for leftover in (path.with_name(path.name + ".switch"),):
                    try:
                        leftover.unlink()
                    except OSError:
                        pass
            if isinstance(exc, ContentSwitchError):
                raise
            if isinstance(exc, OSError):
                _refuse("write_failed", f"the switch could not be written -- {exc}; every file is as it was", error=str(exc))
            raise
        return [p for p, text in self.writes.items() if before.get(p) is None or before[p] != text.encode("utf-8")], [(p, t) for p, t in self.archives if before.get(p) is not None]


def _check_unchanged(comparison):
    for rel, text in comparison.document_texts.items():
        try:
            now = _read(comparison.document_dir / rel)
        except (OSError, UnicodeDecodeError):
            now = object()
        if now != text:
            _refuse("changed_meanwhile", f"{rel}: changed since the comparison was read -- compare again", file=rel)


def apply(here, mode, comparison, choices=None):
    """The switch `comparison` describes written into document `mode` of project `here`, with `choices` ({node id: choice}, each node's default for what it does not name -- `resolve_choices`). Returns a Result.

    Refused before anything is written: `bad_mode`, `no_such_document`, `wrong_comparison` (a comparison of another document or project), `unknown_node`, `bad_choice`, `changed_meanwhile` (a file of the document is not what the comparison read), `legacy_headings`, `invalid_result`, `too_deep`; and `write_failed` where the disk refuses midway -- every file then put back as it was, the archives written taken away."""
    _check_project(here, mode)
    if comparison.mode != mode or Path(comparison.document_dir) != Path(here.document_dir(mode)):
        _refuse("wrong_comparison", f"the comparison is of the document {comparison.mode!r} in {comparison.document_dir}, and {mode!r} of {here.name} is being switched", mode=mode)
    chosen = resolve_choices(comparison, choices)
    if mode != "rs":
        try:
            if not structure.is_absolute(structure.read(here.structure_file(mode))):
                _refuse("legacy_headings", f"{mode}: its structure.json does not write its headings at the level they print at -- convert it first (structure.make_absolute)", side="document")
        except validation.ValidationError as exc:
            if isinstance(exc, ContentSwitchError):
                raise
            _refuse("changed_meanwhile", f"{structure.FILE}: cannot be read any more -- {exc}", file=structure.FILE)
    _check_unchanged(comparison)
    plan, taken = (_plan_report if mode == "rs" else _plan_structured)(here, mode, comparison, chosen)
    written, archived = plan.run()
    notes = list(_after(here, mode, comparison, taken))
    entry = here.document_typ(mode)
    return Result(mode, tuple(written), tuple(archived), tuple(plan.removes),
                  structure=any(p.name == structure.FILE for p in written), entry=entry in written, notes=tuple(notes))


def _plan_structured(here, mode, comparison, chosen):
    """(_Plan, [(relative path, old text or None)] of the files taken from the template) of a CU's or a BP's switch."""
    folder = Path(here.document_dir(mode))
    plan = _Plan(folder)
    doc_source, tpl_source = comparison.document_structure, comparison.template_structure
    doc_flat, tpl_flat = _flat(doc_source), _flat(tpl_source)
    other_modes = {m for m in here.modes if m != mode}
    taken = []
    named_after = set()       # every file the result names

    def included(node):
        choice = chosen[node.id]
        if node.kind == "section":
            return choice in ("keep", "take")
        return any(included(child) for child in node.children)

    def write_file(rel, text):
        plan.writes[folder / rel] = text
        named_after.add(rel)

    def section_entry(node, depth):
        choice = chosen[node.id]
        rel = structure.section_file(node.id)
        doc = doc_flat.get(node.id)
        tpl = tpl_flat.get(node.id)
        old = comparison.document_texts.get(node.file_document) if node.file_document else None
        if choice == "keep":
            if old is None:
                named_after.add(rel)        # a section whose file nobody wrote: named as it was
            else:
                write_file(rel, structure.fit_text(old, depth))
            leaf = {"id": node.id, "file": rel, "enabled": bool(doc[0].get("enabled", True))}
            if doc[0].get("shared_with"):
                leaf["shared_with"] = list(doc[0]["shared_with"])
            return leaf
        # take
        text = structure.fit_text(comparison.template_texts[node.file_template], depth)
        current = _read(folder / rel)
        if current is not None and _lf(current) != _lf(text):
            plan.archive(rel)
        if node.file_document and node.file_document != rel and comparison.document_texts.get(node.file_document) is not None:
            plan.archive(node.file_document)
        write_file(rel, text)
        taken.append((rel, old))
        enabled = bool(doc[0].get("enabled", True)) if doc else bool(tpl[0].get("enabled", True))
        leaf = {"id": node.id, "file": rel, "enabled": enabled}
        shared = [m for m in tpl[0].get("shared_with", ()) if m in other_modes]
        if shared:
            leaf["shared_with"] = shared
        return leaf

    def group_entry(node, depth, children):
        choice = chosen[node.id]
        rel = structure.group_file(node.id)
        doc = doc_flat.get(node.id)
        tpl = tpl_flat.get(node.id)
        old = comparison.document_texts.get(node.file_document) if node.file_document else None
        if doc and (choice == "keep" or tpl is None):
            if old is not None:
                write_file(rel, structure.fit_text(old, depth))
            else:
                named_after.add(rel)
            title = dict(doc[0]["title"])
            enabled = bool(doc[0].get("enabled", True))
        else:
            text = structure.fit_text(comparison.template_texts[node.file_template], depth)
            current = _read(folder / rel)
            if current is not None and _lf(current) != _lf(text):
                plan.archive(rel)
            write_file(rel, text)
            title = dict(tpl[0]["title"])
            enabled = bool(doc[0].get("enabled", True)) if doc else bool(tpl[0].get("enabled", True))
        return {"id": node.id, "title": title, "enabled": enabled, "children": children}

    def build(nodes, depth):
        out = []
        for node in nodes:
            if depth > structure.MAX_DEPTH:
                _refuse("too_deep", f"the result goes {depth} levels deep and a structure goes {structure.MAX_DEPTH}", depth=depth)
            if node.kind == "section":
                if included(node):
                    out.append(section_entry(node, depth))
            elif included(node):
                children = build(node.children, depth + 1)
                out.append(group_entry(node, depth, children))
        return out

    sections = build(comparison.nodes, 1)
    # what the document had and the result no longer names: archived
    for node in comparison.walk():
        if node.file_document and node.file_document not in named_after and comparison.document_texts.get(node.file_document) is not None:
            if all(p != folder / node.file_document for p, _t in plan.archives):
                plan.archive(node.file_document)
    new_source = {key: value for key, value in doc_source.items() if key != "sections"}
    new_source["sections"] = sections
    new_source["headings"] = structure.ABSOLUTE
    try:
        structure.check_source(new_source)
    except validation.ValidationError as exc:
        _refuse("invalid_result", f"what the choices make is no valid structure -- {exc}", error=str(exc))
    plan.writes[folder / structure.FILE] = structure.dumps(new_source)
    entry = here.document_typ(mode)
    entry_text = comparison.document_texts[entry.name]
    try:
        new_entry = structure._entry_text(entry.name, entry_text, structure.block_lines(new_source, comparison.language))
    except validation.ValidationError as exc:
        _refuse("entry_unreadable", str(exc), file=entry.name)
    if new_entry is not None:
        plan.writes[entry] = new_entry
    return plan, taken


def _report_entry_text(text, items):
    """The report's entry `text` with its `#include "Sections/…"` lines given `items` [(file name, printed)] in order: each line where one stood, the ones there are too many of taken away, the ones there are too few of put after the last -- calc/templates.py sync_includes' arrangement, with the printed state the switch decides."""
    import templates
    lines = text.splitlines(keepends=True)
    ending = "\r\n" if "\r\n" in text else "\n"
    slots = [i for i, line in enumerate(lines) if templates._INCLUDE.match(line.rstrip("\r\n"))]

    def line_for(name, printed, model=None):
        indent = ""
        own = ending
        if model is not None:
            stripped = model.rstrip("\r\n")
            own = model[len(stripped):] or ending
            indent = stripped[:len(stripped) - len(stripped.lstrip(" \t"))]
        return f'{indent}{"" if printed else "// "}#include "{structure.SECTIONS_DIR}/{name}"{own}'

    out = list(lines)
    for k, index in enumerate(slots):
        out[index] = line_for(*items[k], lines[index]) if k < len(items) else None
    rest = [line_for(name, printed) for name, printed in items[len(slots):]]
    if rest:
        at = slots[-1] + 1 if slots else len(out)
        anchor = at - 1
        while anchor >= 0 and out[anchor] is None:
            anchor -= 1
        if anchor >= 0 and not out[anchor].endswith(("\n", "\r")):
            out[anchor] += ending
        out[at:at] = rest
    return "".join(line for line in out if line is not None)


def _plan_report(here, mode, comparison, chosen):
    folder = Path(here.document_dir("rs"))
    plan = _Plan(folder)
    taken = []
    final = []      # (stem, text, printed, from document file or None)
    for node in comparison.nodes:
        choice = chosen[node.id]
        if choice in ("drop", "skip"):
            if choice == "drop" and comparison.document_texts.get(node.file_document) is not None:
                plan.archive(node.file_document)
            continue
        if choice == "keep":
            final.append((node.id, comparison.document_texts[node.file_document], node.enabled_document, node.file_document, None))
        else:
            old = comparison.document_texts.get(node.file_document) if node.file_document else None
            if old is not None:
                plan.archive(node.file_document)
            printed = node.enabled_document if node.file_document else node.enabled_template
            final.append((node.id, comparison.template_texts[node.file_template], printed, None, old))
    width = max(3, len(str(len(final))))
    items, names = [], set()
    owners = {n.file_document: n for n in comparison.nodes if n.file_document}
    for number, (stem, text, printed, doc_rel, old) in enumerate(final, 1):
        name = f"{number:0{width}d}-{stem}.typ"
        rel = f"{structure.SECTIONS_DIR}/{name}"
        names.add(rel)
        items.append((name, bool(printed)))
        path = folder / rel
        plan.writes[path] = text
        if doc_rel is None:
            taken.append((rel, old))
        # a file lying where this one goes that is no section of the document -- an orphan the include lines do not name: archived before it is written over. A section of the document lying there is archived already (taken, dropped) or keeps its text under its own new name (kept).
        if rel not in owners and path.exists():
            current = _read(path)
            if current is not None and _lf(current) != _lf(text):
                plan.archive(rel)
    archived = {p for p, _t in plan.archives}
    # the kept sections' old files that no name of the result takes: their text is under a new name now
    for node in comparison.nodes:
        if node.file_document and chosen[node.id] == "keep" and node.file_document not in names:
            path = folder / node.file_document
            if path not in archived:
                plan.removes.append(path)
    entry = here.document_typ("rs")
    new_entry = _report_entry_text(comparison.document_texts[entry.name], items)
    if new_entry != comparison.document_texts[entry.name]:
        plan.writes[entry] = new_entry
    return plan, taken


# --- after a switch: what the documents share ------------------------------------------------------------

def _after(here, mode, comparison, taken):
    """The notes of what was done after the write: every `shared_with` written again from the tags (calc/sharing.py `reconcile`), and every shared block a section taken from the template carries recorded as this document's local edit (calc/sync.py `record_local_edit`). Neither can undo the switch: what fails is said, not raised."""
    import sharing
    import sync
    folder = Path(here.document_dir(mode))
    for rel, old in taken:
        text = _read(folder / rel)
        if not text or "woodcore:shared" not in text:
            continue
        before = {}
        if old:
            for block, start, end, _newline in sharing._shared_spans(old)[2]:
                before[block.id] = old[start:end]
        for block, start, end, _newline in sharing._shared_spans(text)[2]:
            if block.id in before and _lf(before[block.id]) == _lf(text[start:end]):
                continue
            try:
                sync.record_local_edit(here, mode, block.id, before=before.get(block.id))
            except validation.ValidationError as exc:
                yield engine.Note("switch_sync", f"{rel}: the shared block {block.id!r} could not be recorded as this document's edit -- {exc}", file=rel, shared_id=block.id, error=str(exc))
    try:
        found = sharing.reconcile(here, write=True)
    except validation.ValidationError as exc:
        yield engine.Note("switch_reconcile", f"what the documents share could not be written again from the tags -- {exc}", error=str(exc))
        return
    for problem in getattr(found, "problems", ()) or ():
        yield engine.Note("switch_reconcile", str(problem), error=str(problem))
