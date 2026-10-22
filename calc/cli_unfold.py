"""`woodcore-cli unfold status|import|reinsert|take-back|regenerate`: what the «Formules» tab does with a member check printed unfolded, from a terminal (calc/domains/unfold.py; spec docs/requirements/completed/2026-10-15-calculs-deplies-balises-figures-natives.md, ARCH-005).

    woodcore-cli unfold status     [--check <id>]                                   each line of each unfolded check and where it stands -- writing nothing
    woodcore-cli unfold import     --check <id> [--line <line> ...] [--choice <line>=mine|theirs ...]
                                                                                    the lines changed in the file taken into Woodcore («Importer», «Tout importer»)
    woodcore-cli unfold reinsert   --check <id> --line <line>                       a line taken out of the file put back («Réinsérer»)
    woodcore-cli unfold take-back  --check <id> --line <line>                       an engineer's own value back to the export's («Reprendre»)
    woodcore-cli unfold regenerate --check <id> [--choice <line>=mine|theirs ...]   the domain written again from its check's form («Régénérer»)

**Nothing here decides anything**: the very functions the window calls. A conflict is never settled by default -- an import or a regeneration that meets one without a `--choice` names it and writes nothing. Its words are in calc/i18n/cli.json, in the three languages (`--lang`; by default the language of the project's documents). Qt-free.
"""

import sys

import project
import validation
from cli_sync import LANGUAGES, Say, language
from domains import unfold


def _ids(here, which):
    if which:
        return [which]
    return sorted(rid for rid in unfold.read_base(here)["domains"] if unfold.domain_path(here, rid).is_file())   # its kind's folder under Timber-checks/ laid out by folders (issue #64)


def _choices(values, say):
    found = {}
    for value in values or ():
        line, sep, choice = value.partition("=")
        if not sep or not line or choice not in ("mine", "theirs"):
            raise ValueError(say("unfold_bad_choice", value=value))
        found[line] = choice
    return found


def status(args, here, say):
    ids = _ids(here, args.check)
    if not ids:
        print(say("unfold_nothing"))
    for rid in ids:
        found = unfold.status(here, rid)
        print(say("unfold_head", id=rid, form=say("unfold_matches") if found.matches else say("unfold_no_match")))
        for line in found.lines:
            if line.state != "in_sync":
                print(say("unfold_line", line=line.id, state=say("unfold_state_" + line.state)))
    return 0


def import_(args, here, say):
    try:
        choices = _choices(args.choice, say)
    except ValueError as exc:
        print(exc, file=sys.stderr)
        return 1
    done = unfold.import_lines(here, args.check, args.line, choices)
    for line in done["conflicts"]:
        print(say("unfold_needs_choice", line=line), file=sys.stderr)
    print(say("unfold_imported", id=args.check, n=len(done["imported"])))
    return 1 if done["conflicts"] else 0


def reinsert(args, here, say):
    unfold.reinsert(here, args.check, args.line)
    print(say("unfold_reinserted", id=args.check, line=args.line))
    return 0


def take_back(args, here, say):
    unfold.take_back(here, args.check, args.line)
    print(say("unfold_taken_back", id=args.check, line=args.line))
    return 0


def regenerate(args, here, say):
    try:
        choices = _choices(args.choice, say)
    except ValueError as exc:
        print(exc, file=sys.stderr)
        return 1
    done = unfold.regenerate(here, args.check, choices)
    if done["conflicts"]:
        for line in done["conflicts"]:
            print(say("unfold_needs_choice", line=line), file=sys.stderr)
        return 1
    print(say("unfold_regenerated", id=args.check))
    return 0


ACTIONS = {"status": status, "import": import_, "reinsert": reinsert, "take-back": take_back, "regenerate": regenerate}


def add_parser(sub):
    """`unfold` and its sub-commands, added to woodcore-cli's parser."""
    s = sub.add_parser("unfold", help="the member checks printed unfolded in Formules/: status, import, reinsert, take-back, regenerate -- what the «Formules» tab does")
    actions = s.add_subparsers(dest="action", required=True)
    st = actions.add_parser("status", help="each line of each unfolded check and where it stands, writing nothing")
    st.add_argument("--check", help="one check's id; every unfolded check by default")
    im = actions.add_parser("import", help="the lines changed in the file taken into Woodcore -- a conflict refused without a choice")
    im.add_argument("--check", required=True, help="the check's id, its domain's")
    im.add_argument("--line", action="append", help="a line «var:N_t_d», «eq:sigma_t_0_d», «verify:v-6»…; every changed line if left out")
    im.add_argument("--choice", action="append", metavar="LINE=CHOICE", help="for a line in conflict: mine or theirs")
    ri = actions.add_parser("reinsert", help="a line taken out of the file put back where the writing has it")
    ri.add_argument("--check", required=True)
    ri.add_argument("--line", required=True)
    tb = actions.add_parser("take-back", help="an engineer's own value (own: true) back to the export's")
    tb.add_argument("--check", required=True)
    tb.add_argument("--line", required=True)
    rg = actions.add_parser("regenerate", help="the domain written again from its check's form, the engineer's own lines kept")
    rg.add_argument("--check", required=True)
    rg.add_argument("--choice", action="append", metavar="LINE=CHOICE", help="for a line in conflict: mine or theirs")
    for p in (st, im, ri, tb, rg):
        p.add_argument("--project", help="the project's .woodcore file; else WOODCORE_PROJECT's, else the one beside the checkout")
        p.add_argument("--lang", choices=LANGUAGES, help="the language of what is said; the project's documents' by default")
    return s


def run(args):
    here = project.current()
    say = Say(language(args, here))
    try:
        with project.using(here):
            return ACTIONS[args.action](args, here, say)
    except (unfold.UnfoldError, validation.ValidationError) as exc:
        print(say("refused", code=getattr(exc, "code", None) or type(exc).__name__, message=exc), file=sys.stderr)
        return 1
