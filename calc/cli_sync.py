"""`woodcore-cli sync status|share|import|move`: what the «Structure du document» tab does with the sections the three documents share, from a terminal (docs/domain/documents.md §3.3octodecies, docs/conventions/build-and-release.md §12; v0.117, issue #33).

    woodcore-cli sync status [--document cu|bp|rs]                       what is shared, and where each block stands -- writing nothing
    woodcore-cli sync share  --document cu --section <id> --to bp [rs]   a section shared into one or more other documents
    woodcore-cli sync import --document bp [--item <id>[/<object>] ...] [--choice <item>=<choice> ...] [--choice-all <choice>]
                                                                         what the other documents changed, taken into this one
    woodcore-cli sync move   --document cu --section <id> [--parent <group>] [--position <n>]
                                                                         a section moved in its document's tree

**Nothing here decides anything** -- the domain does, the very functions the window calls: `sync.status` (with `settle=False`: a status is a read, and settling writes the records), `sharing.share`, `sync.import_changes` and `structure.move_node`. A file written is written by them, in their own commit; this module reads the arguments, calls, and says what came of it. So the files a command writes are the files the window's action writes (tests/test_cli_sync.py).

**A conflict is never settled by default.** `sync.import_changes` given no items imports what is incoming and leaves a conflict without a choice as it stands, naming it -- right for a window that asked first, wrong for a terminal, where a partial import would pass for a whole one. So `import` reads the status first and, where an item it would import is in conflict without a choice (`--choice <item>=mine|theirs|cu|bp|rs`, or `--choice-all` for every one), it refuses before anything is written, listing them, and exits 1. It never asks a question: a command a script runs must not wait on a keyboard.

**Its words** are in calc/i18n/cli.json, in the three languages (`--lang`; by default the language the project's documents are written in, positions_store.project_language). A refusal's own sentence is the domain's, in English, its code naming it in every language.

Qt-free.
"""

import json
import sys
from pathlib import Path

import project
import sharing
import structure
import sync
import validation

WORDS_FILE = Path(__file__).resolve().parent / "i18n" / "cli.json"
LANGUAGES = ("fr", "de", "en")


def words(lang):
    """The command's words in `lang`."""
    data = json.loads(WORDS_FILE.read_text(encoding="utf-8"))
    return data[lang if lang in LANGUAGES else "en"]


class Say:
    """The command's words in one language, with the stream they go to."""

    def __init__(self, lang):
        self.table = words(lang)

    def __call__(self, key, **values):
        return self.table[key].format(**values)

    def state(self, state):
        return self.table.get("state_" + state, state)


def language(args, here):
    if getattr(args, "lang", None):
        return args.lang
    import positions_store
    return positions_store.project_language(here, fallback="en")


def _documents(here, which):
    shared = [m for m in sync.SHARE_MODES if m in here.modes]
    if which in (None, "all"):
        return shared
    return [which]


def _refused(say, exc):
    print(say("refused", code=getattr(exc, "code", None) or type(exc).__name__, message=exc), file=sys.stderr)
    return 1


def status(args, here, say):
    for mode in _documents(here, args.document):
        found = sync.status(here, mode, settle=False)
        if not found.blocks:
            print(say("status_nothing", document=mode))
        else:
            print(say("status_head", document=mode, n=len(found.blocks)))
        for block in found.blocks:
            others = ", ".join(m for m in block.modes if m != mode) or "—"
            print(say("status_block", id=block.shared_id, state=say.state(block.state), file=block.rel, modes=others))
            for item in block.objects:
                if item.state != "in_sync":
                    print(say("status_object", id=item.id, state=say.state(item.state)))
        for problem in found.problems:
            print(say("status_problem", message=problem))
    return 0


def share(args, here, say):
    result = sharing.share(here, args.document, args.section, args.to, section_id=args.id)
    copies = ", ".join(f"{mode} ({here.rel(path)})" for mode, path in result.copies)
    print(say("shared", file=here.rel(result.source), targets=copies))
    return 0


def _choices(args, say):
    found = {}
    for value in args.choice or ():
        item, sep, choice = value.partition("=")
        if not sep or not item or not choice:
            raise ValueError(say("bad_choice_arg", value=value))
        found[item] = choice
    return found


def _covers(item, wanted):
    """Whether a conflict `item` is one of the `wanted` items, or inside one of the blocks named."""
    return wanted is None or item in wanted or item.split("/", 1)[0] in wanted


def import_(args, here, say):
    mode = args.document
    try:
        choices = _choices(args, say)
    except ValueError as exc:
        print(exc, file=sys.stderr)
        return 1
    wanted = list(args.item) if args.item else None
    conflicts = [c for c in sync.status(here, mode, settle=False).conflicts if _covers(c, wanted)]
    if args.choice_all:
        for item in conflicts:
            choices.setdefault(item, args.choice_all)
    undecided = [c for c in conflicts if c not in choices and c.split("/", 1)[0] not in choices]
    if undecided:
        print(say("needs_choice", document=mode, n=len(undecided)), file=sys.stderr)
        for item in undecided:
            print(f"  {item}", file=sys.stderr)
        return 1
    result = sync.import_changes(here, mode, wanted, choices)
    if not result.imported and not result.kept:
        print(say("nothing_to_import", document=mode))
        return 0
    files = ", ".join(here.rel(p) for p in result.written) or "—"
    print(say("imported", document=mode, n=len(result.imported), kept=len(result.kept), files=files))
    return 0


def move(args, here, say):
    edit = structure.move_node(here, args.document, args.section, args.parent, args.position)
    if not getattr(edit, "changed", True):
        print(say("not_moved", node=args.section))
        return 0
    written = [here.rel(here.document_dir(args.document) / "structure.json")] if edit.structure else []
    if edit.entry:
        written.append(here.rel(here.document_typ(args.document)))
    print(say("moved", node=args.section, files=", ".join(written) or "—"))
    return 0


ACTIONS = {"status": status, "share": share, "import": import_, "move": move}


def add_parser(sub):
    """`sync` and its four sub-commands, added to woodcore-cli's parser."""
    s = sub.add_parser("sync", help="the sections the three documents share: status, share, import, move -- what the «Structure du document» tab does")
    actions = s.add_subparsers(dest="action", required=True)
    st = actions.add_parser("status", help="what is shared and where each block stands, writing nothing")
    st.add_argument("--document", choices=(*sync.SHARE_MODES, "all"), default="all", help="the document; all of the project's by default")
    sh = actions.add_parser("share", help="a section shared into one or more other documents")
    sh.add_argument("--document", choices=sync.SHARE_MODES, required=True, help="the document the section lies in")
    sh.add_argument("--section", required=True, help="the section's id, as the tree gives it")
    sh.add_argument("--to", nargs="+", choices=sync.SHARE_MODES, required=True, help="the documents it is shared into")
    sh.add_argument("--id", help="the id of the copies, for a section of the report only (its file's stem otherwise)")
    im = actions.add_parser("import", help="what the other documents changed, taken into this one -- a conflict refused without a choice")
    im.add_argument("--document", choices=sync.SHARE_MODES, required=True, help="the document that takes the changes")
    im.add_argument("--item", action="append", help="a shared block «<id>» or an object «<id>/<object id>»; everything incoming if left out")
    im.add_argument("--choice", action="append", metavar="ITEM=CHOICE", help="for an item in conflict: mine, theirs, or a document's version (cu, bp, rs)")
    im.add_argument("--choice-all", metavar="CHOICE", help="the choice for every conflict no --choice names")
    mv = actions.add_parser("move", help="a section moved in its document's tree")
    mv.add_argument("--document", choices=sync.SHARE_MODES, required=True, help="the document")
    mv.add_argument("--section", required=True, help="the section's or the group's id")
    mv.add_argument("--parent", help="the group it goes under; the top if left out (the report has no groups)")
    mv.add_argument("--position", type=int, help="its place among that group's children, 0 first; the end if left out")
    for p in (st, sh, im, mv):
        p.add_argument("--project", help="the project's .woodcore file; else WOODCORE_PROJECT's, else the one beside the checkout")
        p.add_argument("--lang", choices=LANGUAGES, help="the language of what is said; the project's documents' by default")
    return s


def run(args):
    here = project.current()
    say = Say(language(args, here))
    try:
        return ACTIONS[args.action](args, here, say)
    except validation.ValidationError as exc:   # sync.SyncError, sharing.SharingError, structure.StructureError, project.ProjectError: each a ValidationError, said with its code
        return _refused(say, exc)


def check(here, lang=None, out=print, err=None):
    """What `woodcore-cli check` adds about the shared sections: a sync.json that cannot be read stops it -- the file and the field named, exit 1 -- and a document out of step with another is a warning. Reads, never settles: nothing is written. Returns 1 or 0."""
    err = err or (lambda text: print(text, file=sys.stderr))
    say = Say(lang or language(None, here))
    code, out_of_step, said = 0, False, set()
    for mode in _documents(here, None):
        found = sync.status(here, mode, settle=False)
        for problem in found.problems:
            # every document's status names every record that does not read: said once, by its file
            if problem.code == "state_unreadable" and problem.values.get("file") not in said:
                said.add(problem.values.get("file"))
                err(say("check_unreadable", file=here.rel(Path(problem.values["file"])), message=problem.values.get("error", problem)))
                code = 1
        incoming, conflicts = len(found.incoming), len(found.conflicts)
        if incoming or conflicts:
            out_of_step = True
            err(say("check_out_of_step", document=mode, incoming=incoming, conflicts=conflicts))
            # the blocks themselves, by their ids, each with its state in the window's words, as `sync status` says it
            err("    " + ", ".join([f"{item} ({say.state('incoming')})" for item in found.incoming] + [f"{item} ({say.state('conflict')})" for item in found.conflicts]))
    if code == 0 and not out_of_step and _documents(here, None):
        out(f"woodcore-cli: {say('check_in_step')}")
    return code
