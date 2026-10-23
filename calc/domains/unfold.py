"""A check unfolded into a domain of the «Formules» tab: what its file holds, read from the compiler (spec docs/requirements/completed/2026-10-15-calculs-deplies-balises-figures-natives.md).

The engineer, 15.10.2026: a check saved in Woodcore is printed **unfolded** -- `Formules/<id>.typ`, its `#var`, `#eq` and `#verify` written out, read and edited in VS Code as in Woodcore -- and no value of it may age unseen. Its inputs are literals checked by `domain:` (lib/formula.typ, `literal-stale`), its form is named by `#var-domain(..., gen:)`, and each line is found by its key or its `id:`, never by a comment.

**What a domain holds is read from Typst, not parsed** (REQ-004, D-04): every `#var`, `#eq`, `#verify` and `#var-domain` emits a `metadata` labelled `<woodcore-var>` from its context -- its domain, key or id, value, unit, what `domain:` read, whether it is stale -- and `query_state` asks the compiler for them. The parser (calc/typst_paths.py's lexer, through formula_domain) only *locates* the call a write touches. Nothing here imports Qt.
"""

import json
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

import proc
import project
import validation

# The label every command's metadata carries (lib/formula.typ, `wc-meta`), held equal by tests/test_unfold.py
META_LABEL = "woodcore-var"
# The relative gaps under which a literal agrees with the value domain: reads (lib/formula.typ, `literal-tolerance` and `literal-rounding`): Python writes the values it unfolds at full precision, so they agree within the first; a value typed by hand to the decimals it is printed at agrees within the second. Held equal to Typst's by tests/test_unfold.py.
LITERAL_TOLERANCE = 1e-6
LITERAL_ROUNDING = 1e-3
TIMEOUT_S = 60
# The version of the writer of an unfolded check: kept in the base and in the export's `gen`, so that a file written by an older writer says it no longer matches (REQ-003, REQ-010). 2 since the spec 2026-10-21-commandes-typst-refonte (REQ-012, Q-006, Q-014): `#domain(id, label:)` and no `gen:` in the file, `#calc-defaults(presets: "block", scope: "domain")` at its head, an `id:` on every line -- what Woodcore finds a line by, a line without one being the engineer's. A line the writer stops writing without the form changing (the `eta_s` of a simple compression or bending, spec 2026-10-22-retrait-niveau-manuel D-4) keeps the version: a domain written before keeps the line, inert, so two domains of one `gen` need not hold the same lines.
GENERATOR_VERSION = 2
# The kinds of check printed unfolded (D-11): every kind member_check computes, in the fire situation too, since the spec 2026-10-21-commandes-typst-refonte (REQ-017) -- member_check.IMPLEMENTED, held equal by tests/test_unfold.py
UNFOLDED_KINDS = ("tension", "compression", "bending", "shear", "buckling", "lateral-torsional")
# The kinds of domain Woodcore writes out (spec 2026-10-21-commandes-typst-refonte, ARCH-011): a member check, `check`, a steel check, `steel`, and the loads -- the permanent loads, the snow, the wind and the live loads, each case of data/calculations.json, a workbook's sheet or a tab's source --; the next generators add theirs. Each is read through `_module` (its export, its records, which of them are written out, the form each is written for), has the folder of its files (project.DOMAIN_FOLDERS), its base beside them and its writer (`GENERATORS`); one base, one state and one mechanism of lines for all (ARCH-RISK-104).
LOAD_KINDS = ("dead-load", "snow-load", "wind-load", "live-load")
DOMAIN_KINDS = ("check", "steel") + LOAD_KINDS + ("connector", "connection", "script")


class _Kind:
    """How the mechanism reads the domains of one kind: `EXPORT_FILE` under data/, `records(data)` {id: record, `id` in it}, `is_unfolded(record)`, `form_of(record)`."""

    def __init__(self, export_file, records, is_unfolded, form_of):
        self.EXPORT_FILE, self.records, self.is_unfolded, self.form_of = export_file, records, is_unfolded, form_of


def _calc_form(kind):
    """The form a calculation of `kind` is written for, {kind, form, version}: the vars it computes, named by their digest -- a branch of the norm changes it, a value does not."""
    def form_of(record):
        import sync
        if not record.get("vars"):
            return None
        return {"kind": kind, "form": sync.digest(",".join(record["vars"]))[:6], "version": GENERATOR_VERSION}
    return form_of


def _instances(kind):
    """The cases of `kind` in data/calculations.json, each given its id and its domain's label (what its title says)."""
    def records(data):
        domain = (data or {}).get("domains", {}).get(kind, {})
        return {rid: dict(r, id=rid, kind=kind, domain_label=domain.get("label")) for rid, r in domain.get("instances", {}).items()}
    return records


def _module(kind):
    """How the domains of a kind Woodcore writes out are read: what it exports, which of its records are written out, and the form each is written for."""
    from domains import member_check, steel_check
    if kind in ("check", "steel"):
        module = member_check if kind == "check" else steel_check
        return _Kind(module.EXPORT_FILE, lambda data: (data or {}).get("checks", {}), module.is_unfolded, module.form_of)
    if kind in LOAD_KINDS:
        form_of = _calc_form(kind)
        if kind == "snow-load":
            # the snow's file since the spec 2026-10-22-onglet-neige-type (D-18, ARCH-RISK-F05): the column of Figur 3 at its head, s_k an `#eq` of equation (10), no cornice -- the last "-fig3" says a file written before it is of another form, which «Régénérer» writes again line by line, never in place; GENERATOR_VERSION, every kind's, stays
            plain = form_of

            def form_of(record):
                found = plain(record)
                return None if found is None else dict(found, form=found["form"] + "-fig3")
        return _Kind("calculations.json", _instances(kind), lambda record: bool(record.get("vars")), form_of)
    if kind == "connector":
        # a connector the export calculated (data/connectors.json): one that cannot be is said by its reason, and written out by nothing
        return _Kind("connectors.json", lambda data: {rid: dict(r, id=rid) for rid, r in (data or {}).get("connectors", {}).items()},
                     lambda record: bool(record.get("calculated")) and bool(record.get("vars")), _calc_form("connector"))
    if kind == "connection":
        # a polar moment the export could draw (data/connections.json): its form also names its number of fasteners and whether it can take a moment, which change its lines -- and, by its last "-a", the figure drawn with its arrows after the forces (spec 2026-10-22-image-polar-moment, ARCH-003), so that a file written with the figure at its head shows the red «forme» line and is regenerated, never rewritten in place
        def form_of(record):
            base = _calc_form("connection")(record)
            if base is None:
                return None
            return dict(base, form=base["form"] + "-%d%s-a" % (len(record.get("fasteners", [])), "" if _lever(record) else "-0"))
        return _Kind("connections.json", lambda data: {rid: dict(r, id=rid) for rid, r in (data or {}).get("connections", {}).items()},
                     lambda record: bool(record.get("calculated", True)) and bool(record.get("vars")), form_of)
    if kind == "script":
        # a Python script the export ran (data/scripts.json): its vars and their lines, as a load's; one that produced nothing is said by its reason, and written out by nothing
        return _Kind("scripts.json", lambda data: {rid: dict(r, id=rid) for rid, r in (data or {}).get("scripts", {}).items()},
                     lambda record: bool(record.get("calculated")) and bool(record.get("vars")), _calc_form("script"))
    raise UnfoldError(f"unfold: no domain of kind {kind!r} is written out -- {', '.join(DOMAIN_KINDS)}", "no_kind", kind=kind)


def kind_of(here, rid):
    """The kind of the domain `rid` Woodcore wrote: the base that lists it, else the export that holds it (a member check before a steel check), else a member check -- what a caller that knows the domain by its id alone, the «Formules» tab, reads it by."""
    for kind in DOMAIN_KINDS:
        try:
            if rid in read_base(here, kind)["domains"]:
                return kind
        except validation.ValidationError:
            continue
    for kind in DOMAIN_KINDS:
        try:
            module = _module(kind)
            if rid in module.records(json.loads((here.data_dir / module.EXPORT_FILE).read_text(encoding="utf-8"))):
                return kind
        except (OSError, ValueError, AttributeError):
            continue
    return "check"


class UnfoldError(validation.ValidationError):
    """A refusal of this module, with a code the window says in its own words and the values it is about. A ValidationError (v0.120, spec 2026-10-19-base-saine-nettoyage C7): an export it stops reports it as a defect of the input -- «export failed: …» -- and not as a traceback."""

    def __init__(self, message, code, **values):
        super().__init__(message)
        self.code = code
        self.values = values


def expression():
    """The Typst expression one read evaluates: every `<woodcore-var>` metadata of the document, in document order. `typst eval --in` evaluates it against the compiled document (`typst query` being deprecated, the way calc/variables.py reads the registry)."""
    return f"query(<{META_LABEL}>).map(it => it.value)"


def _eval(here, main, timeout):
    command = [project.typst_executable(), "eval", "--in", str(main), "--root", str(here.typst_root), "--format", "json", expression()]
    try:
        done = proc.run(command, capture_output=True, cwd=str(here.typst_root), timeout=timeout)
    except FileNotFoundError as exc:
        raise UnfoldError(f"unfold: typst was not found -- {exc}", "no_typst") from exc
    except subprocess.TimeoutExpired as exc:
        raise UnfoldError(f"unfold: reading {main.name} took longer than {timeout} s", "timeout", seconds=timeout) from exc
    if done.returncode != 0:
        output = (done.stderr or done.stdout or b"").decode("utf-8", "replace").strip()
        raise UnfoldError(f"unfold: {main.name} does not compile\n" + "\n".join(output.splitlines()[-30:]), "does_not_compile", path=str(main))
    try:
        found = json.loads(done.stdout.decode("utf-8"))
    except ValueError as exc:
        raise UnfoldError(f"unfold: the answer of typst for {main.name} is not JSON", "bad_answer", path=str(main)) from exc
    if not isinstance(found, list):
        raise UnfoldError(f"unfold: the answer of typst for {main.name} is not a list", "bad_answer", path=str(main))
    return found


def query_state(here, path, timeout=TIMEOUT_S, mode="rs"):
    """What the domain file `path` holds, as Typst computed it: (entries, where), `entries` the metadata of every command of the domain in file order -- `kind` var, eq, verify or domain, with its domain, key or id, value, unit, `from`, `stale`, `own`, `gen` -- and `where` "file" or "report".

    A domain is compiled **alone** first: every `Formules/<id>.typ` imports `/commands.typ` from the Typst root, so it compiles without the report. One written by hand may read a `var-domain` of the report (`domain: "Ende"`), and then does not compile alone: the report is read instead, and what it holds of this domain kept (spec §13, ARCH-RISK-104). A domain the report does not include either is said, by the alone compile's error.
    """
    path = Path(path)
    domain_id = path.stem
    try:
        entries = _eval(here, path, timeout)
        return [e for e in entries if isinstance(e, dict) and e.get("domain") == domain_id], "file"
    except UnfoldError as alone:
        if alone.code != "does_not_compile":
            raise
        main = here.document_typ(mode)
        if not main.is_file():
            raise
        try:
            entries = _eval(here, main, timeout)
        except UnfoldError:
            raise alone
        mine = [e for e in entries if isinstance(e, dict) and e.get("domain") == domain_id]
        if not mine:
            raise alone
        return mine, "report"


# --- the writer: a check's domain, written from its record (spec 2026-10-15, REQ-002, ARCH-002) ---------------------------

# The words an unfolded check's title is printed with: SIA 265's own headings, the ones the `#verify-*` of lib/timber.typ print, read in the document's language off the glossary's terms -- by its form where the form names one, else by its kind
_FORM_WORDS = {"(6)": "Zug parallel zur Faserrichtung", "(7)": "Zug rechtwinklig zur Faserrichtung", "(8)/(9)": "Zug unter einem Winkel zur Faserrichtung",
               "(10)": "Druck parallel zur Faserrichtung", "(11)": "Druck rechtwinklig zur Faserrichtung", "(12)/(13)": "Druck unter einem Winkel zur Faserrichtung",
               "(26)": "Abscheren", "(27)": "Abscheren", "(28)": "Schub und Normalkraft rechtwinklig zur Faserrichtung"}
_KIND_WORDS = {"tension": "Zug parallel zur Faserrichtung", "compression": "Druck parallel zur Faserrichtung", "bending": "Biegung", "shear": "Schub",
               "buckling": "Stabilität", "lateral-torsional": "Kippen"}
_PART = "Tragsicherheit"
# The member's own values, which come first (#member's order); every other row -- the action, the stresses, the factors of stability, the utilisations -- is the verdict's part, after its heading
_MEMBER_KEYS = {"A", "eta_w", "eta_t", "eta_w_E", "f_c_0_k", "E_0_05", "k_fi", "t_fi", "beta_n", "d_char_n", "d_red", "d_ef", "b", "h", "d"}


def _member_row(key):
    """Whether a row of `compute` is the member's -- its section, its moduli, its factors and its design values -- rather than the verdict's: what `#member` prints, before the part's heading."""
    if key in _MEMBER_KEYS or key.startswith(("W_", "I_", "i_", "k_h")) or key.endswith("_tab"):
        return True
    return key.startswith("f_") and key.endswith("_d") and "alpha" not in key


def _label(record_id, what):
    """A Typst label of a line of text the writer owns -- `<ZT-01-member>` --: what Woodcore finds the line by (D-04, labels), its characters those a label takes."""
    import re
    return "<" + re.sub(r"[^A-Za-z0-9_.:-]", "-", record_id) + "-" + what + ">"


def member_line(record, lang):
    """The member's line an unfolded check opens with, as `#member` prints it (D-15): the position's type, its material and strength class, its section and its moisture class -- or the check's id where it names no position the export carries."""
    import json as _json
    import positions_store
    from i18n import strings
    here = project.current()
    head, kind = record["id"], None
    material = record["grade"]
    if record.get("position") and record.get("position_found"):
        head = record["position"]
        try:
            pos = _json.loads((here.data_dir / "positions" / f"{record['position']}.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            pos = {}
        kind = positions_store.type_label(pos.get("type", ""), lang) if pos.get("type") else None
        if pos.get("material"):
            material = strings.term(pos["material"], lang) + " " + record["grade"]
    parts = ([kind] if kind else []) + [material, record["section"].get("text") or "", strings.text("moisture_class", lang) + " " + str(record["moisture_class"])]
    return f"*{head}*: " + ", ".join(p for p in parts if p) + " " + _label(record["id"], "member")


def generate(record, lang="de", kind="check"):
    """The whole file of the domain `record` of `kind` written out -- the generator of its kind (`GENERATORS`, spec 2026-10-21-commandes-typst-refonte, ARCH-011)."""
    return GENERATORS[kind](record, lang)


def _generate_member(record, lang="de"):
    """The whole file of the check `record` unfolded (REQ-002): its `#var-domain(id, title:, gen:)`, the member's line, the member's values -- the section's sides and every input as a literal checked by `domain: ("check", id)`, every derived value an `#eq` with its clause --, the part's heading, then the check: the force, the stress, the relation with its `id:`, and the utilisation in percent. Written from `member_check.compute`'s rows alone, its formulas in keys (ARCH-002, ARCH-008): no arithmetic of SIA 265 4.2.1 is restated here. Pure -- no date, LF, the same record giving the same bytes (ARCH-RISK-211)."""
    from domains import member_check
    from i18n import strings
    import build_reference as ref
    if not member_check.is_unfolded(record):
        raise UnfoldError(f"unfold: {record.get('id')!r} is not a check printed unfolded", "not_unfolded", id=record.get("id"))
    result = member_check.compute(record)
    gen = member_check.form_of(record)
    rid = record["id"]
    where = ("check", rid)
    published = member_check.published_vars(record)

    def var(key, symbol, value, unit, **options):
        head = [key] + ([symbol] if symbol and symbol != key else [])
        # each value on a line of its own, its citation in the right-hand column -- the domain's `block` presets (Q-014), #member's form at its full detail; its `id:` what Woodcore finds it by (Q-006)
        return "  " + ref.call_command("var", *head, value, *([unit] if unit else []), domain=list(where), **{**options, "id": key})

    def eq(row, **options):
        head = [row["key"]] + ([row["symbol"]] if row["symbol"] != row["key"] else [])
        clause = row.get("clause")
        cite = {"norm": row.get("norm", member_check.NORM), "norm_section": clause} if clause else {}   # the row's own norm (C2, v0.120)
        return "  " + ref.call_command("eq", *head, ref.Raw("`" + row["keys"] + "`"), **({"unit": row["unit"]} if row["unit"] else {}), **cite, **options, id=row["key"])

    member, check = [], []
    for key, symbol, value in member_check.section_sides(record):
        member.append(var(key, symbol, value, "mm", level=0))
    for row in result["rows"]:
        if row["key"] == "eta":
            continue
        target = member if _member_row(row["key"]) else check
        table = row.get("table")
        if table:
            target.append(var(table["key"], table["symbol"], table["value"], table["unit"]))
        if row.get("keys"):
            target.append(eq(row))
        else:
            target.append(var(row["key"], row["symbol"], published[row["key"]]["value"], row["unit"]))
    words = strings.term(_FORM_WORDS.get(gen["form"], _KIND_WORDS[record["kind"]]), lang)
    title = f"{words} – {rid}"
    relation = result["relation"]
    import documents
    try:
        here = project.current()
    except project.ProjectError:
        here = None
    # the domain and its presets (spec 2026-10-21-commandes-typst-refonte, REQ-008, Q-014): the form the file is written from is kept in the base, not in the file
    lines = [documents.root_import_line(here), "",
             "#domain(" + ref.typst_str(rid) + ", label: " + ref.typst_str(title) + ")[",
             '#calc-defaults(presets: "block", scope: "domain") ' + _label(rid, "presets"),
             member_line(record, lang), ""]
    lines += member
    lines += ["", "_" + strings.term(_PART, lang) + "_ " + _label(rid, "part"), ""]
    lines += check
    lines.append("  " + ref.call_command("verify", ref.Raw("`" + relation + "`"), id="v-" + re.sub(r"[^0-9a-z]+", "-", gen["form"].lower()).strip("-")))
    eta = next(row for row in result["rows"] if row["key"] == "eta")
    if eta.get("keys"):
        lines.append("  " + ref.call_command("eq", "eta", ref.Raw("`" + eta["keys"] + "`"), unit="%", id="eta"))
    else:
        # η the largest of several utilisations (max(…)): a literal in percent, checked against the export's
        lines.append("  " + ref.call_command("var", "eta", published["eta"]["value"] * 100, "%", domain=list(where), id="eta"))
    lines += ["]", ""]
    return "\n".join(lines)


def _calc_body(record, lang, where):
    """The body of a calculation record written out -- a steel check's, a load's: each value as the export worked it out (line_keys.calc_lines), an `#eq` with its clause where its formula computes it in the registry's keys, a literal checked by `domain: where` otherwise; its tables and what it leaves to the engineer, each on a labelled line, which the export takes again where it changes and the file does not (REQ-008); the checks of a calculation, each a literal η."""
    from domains import line_keys
    from i18n import strings
    import build_reference as ref
    rid = record["id"]

    def words(text):
        return strings.translate(text, lang) if text else None   # a term or a template of the glossary, as tl-str reads the export

    def section(ref):
        """A clause named by a word of its edition -- «Figur 3», «Anhang D», «Tabelle 8» -- in the report's language, its number as it is (REQ-019 of spec 2026-10-22-onglet-neige-type: «Figur 3» was printed in a French report)."""
        found = re.match(r"^(Figur|Anhang|Tabelle)\s+(.+)$", ref or "")
        if not found:
            return ref
        word = strings.translate(found.group(1), lang)
        return word[:1].upper() + word[1:] + " " + found.group(2)

    def cite(line):
        if not line.get("norm"):
            if line.get("line") is not None:
                # a script's result that names no norm is cited by its call -- «script beam.py, l. 12» (spec 2026-10-20-indices-et-niveaux, REQ-002), its file the last part of its source
                return {"norm": strings.template("script.line", lang, file=str(line.get("source") or "").split("/")[-1], line=str(line["line"]))}
            return {}
        return {"norm": line["norm"], **({"norm_section": section(line["norm_ref"])} if line.get("norm_ref") else {})}

    body = []
    for line in line_keys.calc_lines(record):
        symbol = line["symbol"]
        if len(symbol) > 2 and symbol[0] == symbol[-1] == '"':
            symbol = '"' + strings.translate(symbol[1:-1], lang) + '"'   # a symbol written as a word -- «Dachform» -- is a word of the report's language (REQ-019)
        head = [line["key"]] + ([symbol] if line["symbol"] != line["key"] else [])
        unit = line.get("unit") or ""
        shown = {"label": words(line.get("label")), "descr": words(line.get("description"))}
        shown = {k: v for k, v in shown.items() if v}
        if line.get("keys"):
            body.append("  " + ref.call_command("eq", *head, ref.Raw("`" + line["keys"] + "`"), **({"unit": unit} if unit else {}), **shown, **cite(line), id=line["key"]))
        elif isinstance(line["value"], str):
            # a text of the export (a roof's form, a category): read from it by `domain:` -- #var takes no text as a value, and a reading never ages
            # a symbol written as a word (`"Dachform"`) is printed in the report's language, written here by name -- read off the export it would be the German one (REQ-019)
            visible = {"name_visible": symbol} if symbol != line["symbol"] else {}
            body.append("  " + ref.call_command("var", line["key"], domain=where, **visible, **shown, **cite(line), id=line["key"]))
        else:
            body.append("  " + ref.call_command("var", *head, line["value"], *([unit] if unit else []), domain=where, **shown, **cite(line), id=line["key"]))
    # each table of the calculation (the walls of a section's class, a connector's spacings): its lines labelled, what the export says of it taken again where it changes and the file does not (REQ-008)
    for i, table in enumerate(record.get("tables", []), 1):
        body += [""] + _table_lines(table, rid, i, words)
    for i, note in enumerate(record.get("notes", []), 1):
        body += ["", _prose(words(note)) + " " + _label(rid, f"note-{i}")]
    # a check of a calculation (engine.Calculation `checks`: {name, eta, unit, status}): its utilisation, a literal the export takes again where it changes
    for i, check in enumerate(record.get("checks", []), 1):
        body.append("  " + ref.call_command("var", f"eta_{i}", "eta_" + str(i), check["eta"], *([check["unit"]] if check.get("unit") else []),
                                            label=words(check.get("name")), **cite(check), id=f"check-{i}"))
    return body


def _calc_file(rid, title, what, body, tail):
    """A calculation's file: the engine imported from the root, its `#domain(id, label:)` and the domain's presets (Q-014), the line of what it is about where it has one, its body, then `tail` -- a verdict."""
    import build_reference as ref
    import documents
    try:
        here = project.current()
    except project.ProjectError:
        here = None
    lines = [documents.root_import_line(here), "",
             "#domain(" + ref.typst_str(rid) + ", label: " + ref.typst_str(title) + ")[",
             '#calc-defaults(presets: "block", scope: "domain") ' + _label(rid, "presets")]
    if what:
        lines.append("*" + _cell(what) + "* " + _label(rid, "member"))
    lines += [""] + body + tail + ["]", ""]
    return "\n".join(lines)


def figure_line(file, caption, label, width="80%", written=None):
    """A figure of a domain's file, on one labelled line: `#figure(image("<file>", width: 80%), caption: [<caption>]) <label>` -- the line a load's drawing, a connector's, a steel section's are written with, and what «Affichage» changes the width, the caption and the label of (spec 2026-10-22-onglet-neige-type, ARCH-RISK-F07)."""
    # `written`: a caption as the file already holds it, written back as it stands -- never escaped twice
    caption_part = ", caption: [" + written + "]" if written else ", caption: [" + _cell(caption) + "]" if caption else ""
    return "#figure(image(" + _typst_string(file) + ", width: " + width + ")" + caption_part + ") <" + label + ">"


def _generate_load(record, lang="de"):
    """The whole file of a load written out (spec 2026-10-21-commandes-typst-refonte, REQ-017): a case of data/calculations.json -- a permanent load, a snow load, a wind load, a live load, a workbook's sheet or a tab's source --, its title its domain's and its id, its drawings, each value as the export worked it out (`_calc_body`), literals checked by `domain: (<kind>, id)`. Written from the export alone (ARCH-002). Pure."""
    from i18n import strings
    rid = record["id"]
    kind = record["kind"]
    title = (strings.translate(record["domain_label"], lang) + " – " if record.get("domain_label") else "") + rid
    # its drawings -- a permanent load's build-up, entered in Woodcore --, each a figure on a labelled line with its caption, as #show-calc printed them (a load is written out in a project laid out by folders only, where a figure's file is named from the Typst root)
    head = []
    for i, figure in enumerate(record.get("figures") or [], 1):
        head += [figure_line(figure["file"], strings.translate(figure["title"], lang) if figure.get("title") else "", _label(rid, f"figure-{i}")[1:-1]), ""]
    return _calc_file(rid, title, None, head + _calc_body(record, lang, [kind, rid]), [])


def _generate_script(record, lang="de"):
    """The whole file of a Python script written out (spec 2026-10-21-commandes-typst-refonte, REQ-017): its title its label, else its name, each var as the export worked it out (`_calc_body`), literals checked by `domain: ("script", id)`. Pure."""
    rid = record["id"]
    return _calc_file(rid, record.get("label") or record.get("name") or rid, None, _calc_body(record, lang, ["script", rid]), [])


def connector_line(record, lang):
    """What a connector is, on one line as `#show-connector` printed it: «SD-10: Stabdübel, Holz-Holz zweischnittig, Ø 10 mm, L = 100 mm, 8/200, vorgebohrt (Bauteile: …)» -- the engine's words in the document's language, what the source leaves empty left out."""
    from i18n import strings
    parts = [strings.translate(s, lang) for s in (record.get("type"), record.get("assembly")) if s]
    if record.get("diameter"):
        parts.append("Ø\u00a0" + _number(record["diameter"]["value"]) + "\u00a0" + record["diameter"]["unit"])
    if record.get("length"):
        parts.append("L\u00a0=\u00a0" + _number(record["length"]["value"]) + "\u00a0" + record["length"]["unit"])
    parts += [p for p in (record.get("dimension"), record.get("steel")) if p]
    if record.get("predrilled") is not None:
        parts.append(strings.text("predrilled" if record["predrilled"] else "not_predrilled", lang))
    line = record["id"] + ": " + ", ".join(parts)
    if record.get("elements"):
        line += " (" + strings.text("members_joined", lang) + ": " + ", ".join(record["elements"]) + ")"
    return line


# The caption of each figure of a connector, by its name in the export (calc/domains/connector.py `figures`): the engine's words
CONNECTOR_CAPTIONS = {"pattern": "connector.pattern_caption", "section": "connector.section_caption"}


def _generate_connector(record, lang="de"):
    """The whole file of a connector written out (spec 2026-10-21-commandes-typst-refonte, REQ-017): its `#domain`, its line (`connector_line`) and its description, its section and its pattern as the export drew them -- each figure on a labelled line, with its caption --, then its resistance as the export worked it out (`_calc_body`), literals checked by `domain: ("connector", id)`, its tables (k_beta, the spacings). Written from the export alone (ARCH-002): no arithmetic of SIA 265 6 here. Pure."""
    from i18n import strings
    rid = record["id"]
    title = (strings.translate(record["type"], lang) + " – " if record.get("type") else "") + rid
    head = []
    if record.get("description"):
        head += [_prose(record["description"]) + " " + _label(rid, "description"), ""]
    for name, by_lang in sorted((record.get("figures") or {}).items()):
        path = (by_lang or {}).get(lang) or (by_lang or {}).get("de")
        if path:
            # its caption the glossary's, as #show-connector-resistance printed it
            caption = ", caption: [" + _cell(strings.template(CONNECTOR_CAPTIONS[name], lang)) + "]" if name in CONNECTOR_CAPTIONS else ""
            head += ["#figure(image(" + _typst_string(path) + ", width: 60%)" + caption + ") " + _label(rid, "figure-" + name), ""]
    return _calc_file(rid, title, connector_line(record, lang), head + _calc_body(record, lang, ["connector", rid]), [])


def _lever(record):
    """Whether a polar moment's fasteners have a lever arm about its centre (I_p > 0): only then does it take a moment."""
    return ((record.get("vars") or {}).get("I_p") or {}).get("value", 0) > 0


def _generate_connection(record, lang="de"):
    """The whole file of a polar moment written out (spec 2026-10-21-commandes-typst-refonte, REQ-017, lot 13): its `#domain`, the members it joins, its geometry as the export worked it out (`_calc_body`: the centre, the angles, n, I_p, the table of the fasteners), then **the forces, written for the engineer** -- N, V and M at 0 for him to give, the lines his own once he changes them (REQ-009) -- and, from them, by `#eq`, their components along the directions, each fastener's distance to the centre (literals the export takes again where they change), its force along x and z and its resultant, and F_max: `connection.fastener_forces`' distribution (N and V shared equally, M in proportion to the distance and at right angles to it), computed by Typst and held equal to Python's by tests/test_domain_generators.py. The moment's terms are left out of a group with no lever arm (I_p = 0), which cannot take one. Right after N, V and M, on a line of its own (`polar-figure`), the connection's figure with the arrows of the forces in each fastener, `#figure(image-polar-moment("<id>", N: "N", V: "V", M: "M", width: 60%), …)` -- it names the lines above, so the arrows follow the values the engineer writes there (spec 2026-10-22-image-polar-moment, REQ-003, D-02); without a lever arm the call has no `M:`."""
    from i18n import strings
    import build_reference as ref
    rid = record["id"]
    title = strings.template("connection.caption", lang, id=rid) + (": " + record["label"] if record.get("label") else "")   # what #show-polar-moment headed it with
    members = ", ".join(f"{m.get('element') or '?'} ({m['position']})" if m.get("position") else (m.get("element") or "?") for m in record.get("members", []))
    body = _calc_body(record, lang, ["connection", rid])
    n = len(record.get("fasteners", []))
    lever = _lever(record)
    xc, zc = (record.get("center") or {}).get("x", 0.0), (record.get("center") or {}).get("z", 0.0)

    def line(*args, **options):
        return "  " + ref.call_command(*args, **options)

    forces = ["", "$N$, $V$" + (", $M$" if lever else "") + " " + _label(rid, "forces"),
              line("var", "N", 0, "kN", label=_term("Normalkraft", lang), id="N"),
              line("var", "V", 0, "kN", label=_term("Querkraft", lang), id="V")]
    if lever:
        forces.append(line("var", "M", 0, "kNm", label=_term("Biegemoment", lang), id="M"))
    if (record.get("figure") or {}).get("files"):
        # the figure drawn from the lines above, its caption #show-polar-moment's (connection.caption, connection.figure_caption), its label new so that a file of the old form is regenerated (ARCH-003)
        caption = title + " – " + strings.template("connection.figure_caption", lang)
        named = {"N": "N", "V": "V", **({"M": "M"} if lever else {})}
        forces += ["", ref.call_image_figure("image-polar-moment", rid, caption, label=_label(rid, "polar-figure")[1:-1], **named, width="60%"), ""]
    forces += [line("eq", "N_x", ref.Raw("`N dot cos(alpha_N)`"), unit="kN", id="N_x"),
               line("eq", "N_z", ref.Raw("`N dot sin(alpha_N)`"), unit="kN", id="N_z"),
               line("eq", "V_x", ref.Raw("`V dot cos(alpha_V)`"), unit="kN", id="V_x"),
               line("eq", "V_z", ref.Raw("`V dot sin(alpha_V)`"), unit="kN", id="V_z")]
    for i, fastener in enumerate(record.get("fasteners", []), 1):
        dx, dz = fastener["x"] - xc, fastener["z"] - zc
        moment_x = f" + M dot Delta_z_{i} / I_p" if lever else ""
        moment_z = f" - M dot Delta_x_{i} / I_p" if lever else ""
        forces += [line("var", f"Delta_x_{i}", f"Delta x_{i}", dx, "mm", level=0, id=f"Delta_x_{i}"),
                   line("var", f"Delta_z_{i}", f"Delta z_{i}", dz, "mm", level=0, id=f"Delta_z_{i}"),
                   line("eq", f"F_x_{i}", f"F_(x,{i})", ref.Raw(f"`(N_x + V_x) / n{moment_x}`"), unit="kN", id=f"F_x_{i}"),
                   line("eq", f"F_z_{i}", f"F_(z,{i})", ref.Raw(f"`(N_z + V_z) / n{moment_z}`"), unit="kN", id=f"F_z_{i}"),
                   line("eq", f"F_{i}", ref.Raw(f"`sqrt(F_x_{i}^2 + F_z_{i}^2)`"), unit="kN", id=f"F_{i}")]
    if n:
        forces.append(line("eq", "F_max", ref.Raw("`max(" + ", ".join(f"F_{i}" for i in range(1, n + 1)) + ")`"), unit="kN", id="F_max"))
    return _calc_file(rid, title, members or None, body + forces, [])


def _term(source, lang):
    from i18n import strings
    return strings.translate(source, lang)


def _typst_string(text):
    import build_reference as ref
    return ref.typst_str(text)


def _generate_steel(record, lang="de"):
    """The whole file of the steel check `record` written out (spec 2026-10-21-commandes-typst-refonte, REQ-017): its `#domain(id, label:)` and the domain's presets, the line of what it checks -- the profile, the grade, the position --, then each value as the export worked it out (`_calc_body`), literals checked by `domain: ("steel", id)`; the relation with its `id:`, and the utilisation in percent. Written from the export alone (ARCH-002): no arithmetic of SIA 263 here. Pure -- the same record giving the same bytes."""
    from domains import steel_check
    from i18n import strings
    import build_reference as ref
    if not steel_check.is_unfolded(record):
        raise UnfoldError(f"unfold: the steel check {record.get('id')!r} is not written out -- it cannot be calculated", "not_unfolded", id=record.get("id"))
    rid = record["id"]
    title = strings.text("steel.kind." + record["kind"], lang) + " – " + rid
    what = ", ".join(p for p in (record.get("designation"), record.get("grade")) if p)
    if record.get("position"):
        what += ", " + strings.text("steel.position", lang) + " " + record["position"]
    lines = []
    if record.get("relation"):
        lines += ["", "  " + ref.call_command("verify", ref.Raw("`" + record["relation"] + "`"), id="v-steel-" + record["kind"])]
        ratio = steel_check.ratio_keys(record)
        if ratio:
            lines.append("  " + ref.call_command("eq", "eta", ref.Raw("`" + ratio + "`"), unit="%", id="eta"))
        elif record.get("eta") is not None:
            # η the export computed and no formula of the file gives: a literal, taken again by the export where it changes (REQ-008)
            lines.append("  " + ref.call_command("var", "eta", record["eta"] * 100, "%", id="eta"))
    return _calc_file(rid, title, what, _calc_body(record, lang, ["steel", rid]), lines)


def _table_lines(table, rid, i, words):
    """A table of the export written in raw Typst, each line labelled: its title, its figures (a connector's k_beta), the `#table` on one line -- the columns' groups over their labels and units, the rows, the totals in bold --, its note. A cell of kind `math` is set as math, a text keeps the math it carries (`$7 d$`)."""
    translated = words

    def words(text):
        return translated(text) or ""   # an empty label or cell is an empty cell

    out = []
    if table.get("title"):
        out.append("_" + _prose(words(table["title"])) + "_ " + _label(rid, f"table-{i}-title"))
    for j, fig in enumerate(table.get("figures", []), 1):
        caption = " – ".join(words(x) for x in (fig.get("label"), fig.get("role")) if x)
        out.append("#figure(image(" + _typst_string(fig["file"]) + ", width: 45%)" + (", caption: [" + _prose(caption) + "]" if caption else "") + ") "
                   + _label(rid, f"table-{i}-figure-{j}"))
    columns = table.get("columns", [])
    if columns:
        def cell(value, column):
            if isinstance(value, str):
                return "[$" + value + "$]" if column.get("kind") == "math" and value else "[" + _prose(words(value) if column.get("kind") != "math" else value) + "]"
            text = _number(value)
            # a negative number with its minus sign, never a hyphen (the engineer, v0.87): a cell is text, where `-` stays a hyphen
            return "[" + ("\u2212" + text[1:] if text.startswith("-") else text) + "]"

        header = []
        if any(c.get("group") for c in columns):
            k = 0
            while k < len(columns):
                n = 1
                while k + n < len(columns) and columns[k + n].get("group") == columns[k].get("group"):
                    n += 1
                group = _prose(words(columns[k].get("group") or ""))
                text = "[*" + group + "*]" if group else "[]"   # a column under no group: an empty cell, never `[**]`
                header.append(f"table.cell(colspan: {n}, {text})" if n > 1 else text)
                k += n
        for c in columns:
            label = "$" + c["label_math"] + "$" if c.get("label_math") else _prose(words(c.get("label") or ""))
            unit = (" " if label else "") + "[" + c["unit"] + "]" if c.get("unit") else ""
            header.append("[*" + label + unit + "*]" if label or unit else "[]")
        rows = [cell(v, c) for row in table.get("rows", []) for v, c in zip(row, columns)]
        totals = ["[*" + cell(v, c)[1:-1] + "*]" if cell(v, c) != "[]" else "[]" for row in table.get("totals", []) for v, c in zip(row, columns)]
        out.append(f"#table(columns: {len(columns)}, table.header({', '.join(header)}), {', '.join(rows + totals)}) " + _label(rid, f"table-{i}"))
    if table.get("note"):
        out.append(_prose(words(table["note"])) + " " + _label(rid, f"table-{i}-note"))
    return out


def _prose(text):
    """`text` set as Typst markup, the math it carries between `$` kept as math and the rest escaped (`_cell`)."""
    parts = re.split(r"(\$[^$]*\$)", str(text))
    return "".join(part if part.startswith("$") and part.endswith("$") and len(part) > 1 else _cell(part) for part in parts)


def _cell(text):
    """`text` set as Typst markup: the characters markup reads as syntax escaped."""
    return re.sub(r"([\\#*_`$<>@\[\]~])", r"\\\1", str(text))


def _number(value):
    """A number of a table as the report prints it: an integer without its decimals, a float to three decimals, trailing zeros dropped."""
    if value is None:
        return "–"
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return str(value)
    if float(value).is_integer():
        return str(int(value))
    return ("%.3f" % value).rstrip("0").rstrip(".")


# One generator per kind of domain Woodcore writes (ARCH-011): a member check of every kind is written by one, `compute`'s rows in the registry's keys, a steel check by another, the export's vars and steps in those keys; the kinds the next generators bring are added here
GENERATORS = {"check": _generate_member, "steel": _generate_steel, **{kind: _generate_load for kind in LOAD_KINDS}, "connector": _generate_connector, "connection": _generate_connection, "script": _generate_script}


def preview_body(record, lang="de"):
    """The domain of a draft as the «Traction» tab's page compiles it (UI-003): the writing without its import line, its literals no longer checked by `domain:` and no `gen:` -- a draft is in no export yet, and its own values are the ones to see."""
    text = generate(record, lang)
    text = text.split("\n", 2)[2]
    text = re.sub(r', domain: \("check", "[^"]*"\)', "", text)
    return re.sub(r', gen: \(kind: "[^"]*", form: "[^"]*", version: \d+\)', "", text)


# --- the base: what Woodcore last wrote of each unfolded check (REQ-007, ARCH-RISK-205) -----------------------------------

BASE_FILE = "unfold.json"
BASE_FORMAT = "woodcore-unfold"
BASE_SCHEMA = "unfold"
BASE_SCHEMA_VERSION = "1.0"


def base_path(here, kind="check"):
    """`Timber-checks/unfold.json` in a project laid out by folders (issue #64), `Formules/unfold.json` before -- `Steel-checks/unfold.json` for the steel checks, which only a project laid out by folders writes out: beside the domains it describes, so that an archive and a copy of the project carry it with them (it is no `.typ`, so no domain is read from it)."""
    if kind == "check" or not here.has_folders:
        folder = here.domain_dir("check") if here.has_folders else here.formulas_dir
        return folder / (BASE_FILE if kind == "check" else f"unfold-{kind}.json")
    return here.domain_dir(kind) / BASE_FILE   # Steel-checks/unfold.json, Variable-loads/Snow/unfold.json …


def domain_path(here, rid, record=None, kind=None):
    """The file the domain `rid` of `kind` (`kind_of` where None) is written out into: its record's kind's folder under its domain's folder in a project laid out by folders -- `Timber-checks/Tension/`, `Steel-checks/Bending/` -- the kind `record`'s, else the last export's, else the folder of a kind that holds such a file --, `Formules/` before (project.Project.unfolded_dir)."""
    if not here.has_folders:
        return here.formulas_dir / f"{rid}.typ"
    kind = kind or kind_of(here, rid)
    if kind not in project.KIND_FOLDERS:
        return here.domain_dir(kind) / f"{rid}.typ"   # a load: one folder for its kind, Variable-loads/Snow/<id>.typ
    folders = project.KIND_FOLDERS[kind]
    sub = (record or {}).get("kind")
    if sub is None:
        try:
            sub = (_record_of(here, rid, kind) or {}).get("kind")   # a domain gone from the export has none
        except UnfoldError:
            sub = None
    if sub in folders:
        return here.domain_dir(kind, sub) / f"{rid}.typ"
    for sub in folders:
        path = here.domain_dir(kind, sub) / f"{rid}.typ"
        if path.is_file():
            return path
    return here.domain_dir(kind, next(iter(folders))) / f"{rid}.typ"


def empty_base():
    return {"format": BASE_FORMAT, "schema_version": BASE_SCHEMA_VERSION, "domains": {}}


def read_base(here, kind="check"):
    """The base of the domains of `kind`, checked against its schema; an empty one where the project has none yet. A file that does not read stops, naming the file and the field (a malformed file Woodcore wrote stops)."""
    import validation
    path = base_path(here, kind)
    if not path.is_file():
        return empty_base()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except ValueError as exc:
        raise validation.ValidationError(f"{here.rel(path)}: is not JSON ({exc})") from exc
    validation.validate_structure(data, BASE_SCHEMA, where=here.rel(path))
    return data


def write_base(here, data, kind="check"):
    """The base of the domains of `kind` written whole: LF, two spaces, its keys sorted, no date -- two writes of the same base are the same bytes."""
    import validation
    path = base_path(here, kind)
    validation.validate_structure(data, BASE_SCHEMA, where=here.rel(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def line_name(c, legacy):
    """The name a command of an unfolded domain is found by: its `id:` (spec 2026-10-21-commandes-typst-refonte, REQ-012, Q-006) -- a command without one is the engineer's own --, or, in a file written before (`legacy`, a `#var-domain(…, gen:)`), its key, `#verify` its `id:` (spec 2026-10-15). None where it has none."""
    if "id" in c.options:
        return c.options["id"]
    if legacy:
        return c.options.get("id") if c.kind == "verify" else c.key
    return None


FIGURE_IMAGE = re.compile(r'#figure\(\s*image\(\s*"([^"]+)"')


def text_lines(raw):
    """[(line id, its line)] of a text item of a domain's file: a figure by its image -- `figure:<file name>`, so that its label may be changed in «Affichage» and the line stay Woodcore's (D-29) --, every other labelled line by its label, `label:<label>`. A figure commented out, `// #figure(…)`, is the same line, masked (D-23)."""
    out = []
    for line in raw.split("\n"):
        image = FIGURE_IMAGE.search(line)
        if image:
            out.append(("figure:" + image.group(1).rsplit("/", 1)[-1], line))
            continue
        for found in re.finditer(r"<([A-Za-z0-9_.:-]+)>", line):
            out.append(("label:" + found.group(1), line))
    return out


def is_masked(line):
    """Whether a figure's line is commented out -- masked in «Affichage» (D-23)."""
    return line.lstrip().startswith("//")


def _display_free(item):
    """`item` without the arguments its display is set by (calc/line_display.py): what the base compares and the export writes (D-17)."""
    import line_display
    from domains import formula_domain as fd
    if item.is_text:
        return item
    args = set(line_display.display_args(item.kind))
    if not args & set(item.options):
        return item
    return fd.replace(item, options={k: v for k, v in item.options.items() if k not in args})


def comparable_text(item):
    """The text a command of a domain's file is compared by -- what the base records and the states read, everywhere the same (ARCH-RISK-F02): its call as Woodcore writes it, without the arguments its display is set by, which are the engineer's (D-17)."""
    from domains import formula_domain as fd
    return fd.to_call(_display_free(item)).strip()


def _with_display(fresh_item, old):
    """The writing's line `fresh_item` with the display the file's `old` was given -- its arguments of `line_display.display_args` --, written over the file's lines as they stand: what an export keeps of a line set in «Affichage» (D-17)."""
    import line_display
    from domains import formula_domain as fd
    args = set(line_display.display_args(fresh_item.kind))
    options = {k: v for k, v in fresh_item.options.items() if k not in args}
    options.update({k: v for k, v in old.options.items() if k in args})
    return fd.replace(fresh_item, options=options, written=old.written, read_call=old.read_call)


def line_digests(text):
    """{line id: digest} of an unfolded domain's file: each command by its `id:` -- by its key in a file written before --, each line of text the writer owns by its label, as written. What the base records and the states compare (REQ-007)."""
    import re
    import sync
    from domains import formula_domain as fd
    out = {}
    span, _why = fd._body_span(text)
    if span is None:
        return out
    from structure import _split
    body = "".join(_split(text)[span[0]:span[1]])
    _declared, _title, items, gen, _header = fd.parse_domain(body)
    for c in items:
        if c.is_text:
            for line_id, line in text_lines(c.raw):
                out[line_id] = sync.digest(line.strip())
            continue
        name = line_name(c, gen is not None)
        if name:
            out[f"{c.kind}:{name}"] = sync.digest(comparable_text(c))
    return out


def unfold_checks(here, checks, lang=None, notes=None):
    """`unfold_domains` for the member checks of the export `checks`."""
    return unfold_domains(here, "check", checks, lang, notes)


def unfold_domains(here, kind, data, lang=None, notes=None):
    """Writes, for each check of the export `checks` printed unfolded whose domain the project does not hold yet, its file -- `Timber-checks/<Kind>/<id>.typ` laid out by folders, `Formules/<id>.typ` before -- and its base -- what saving a check and an export run (REQ-002) --, and refreshes the domains already there: their lines whose export changed and not their file (REQ-008). Returns the ids written.

    A file already there that holds no domain is written over where it is a stub an earlier Woodcore wrote (`LEGACY_STUBS`), and left as it is and said in `notes` where the engineer wrote it (`unfold_stub_edited`, spec 2026-10-15 D-16, ARCH-RISK-B01). The same for every kind Woodcore writes out (`DOMAIN_KINDS`, spec 2026-10-21-commandes-typst-refonte, ARCH-011): a steel check into `Steel-checks/<Kind>/<id>.typ`, in a project laid out by folders only."""
    import engine
    import positions_store
    module = _module(kind)
    if kind != "check" and not here.has_folders:
        return []
    lang = lang or positions_store.project_language(here)
    base = read_base(here, kind)
    written = []
    for rid, record in sorted(module.records(data).items()):
        if not module.is_unfolded(record):
            continue
        path = domain_path(here, rid, record, kind)
        if path.exists():
            if not here.has_folders or not is_legacy_stub(here, kind, rid, path):
                if notes is not None and here.has_folders and not is_domain_file(path):
                    notes.append(engine.Note("unfold_stub_edited", f"{here.rel(path)}: the check {rid} is printed unfolded, and its file holds what you wrote in place of the stub Woodcore made -- it is left as it is, and the check printed folded until you empty it or write its domain there",
                                             file=here.rel(path), id=rid))
                continue
        with project.using(here):
            text = generate(record, lang, kind)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")
        base["domains"][rid] = {"check": rid, "gen": module.form_of(record), "lines": {k: [v, v] for k, v in line_digests(text).items()}}
        written.append(rid)
    if written:
        write_base(here, base, kind)
    # a domain already there: the lines whose export changed, and not their file, follow it (REQ-008)
    for rid, record in sorted(module.records(data).items()):
        if module.is_unfolded(record) and rid not in written and is_domain_file(domain_path(here, rid, record, kind)):
            try:
                refresh(here, rid, lang, kind)
            except UnfoldError:
                pass   # a domain that cannot be read or compared is left as it is, and the tab says why
    return written


# --- the states of an unfolded domain's lines, and what Woodcore does with them (REQ-006 to REQ-010) ---------------------
#
# Each line Woodcore wrote -- a command by its kind and key or `id:`, a line of text by its label -- is compared three ways (sync.three_way, the rule of calc/sync.py): the line in the file (`mine`), the line a new writing from the export gives (`fresh`), and what Woodcore last wrote or took of it, a pair recorded in the base -- `own`, the file's line then, and `seen`, the writing's line then. In step where the two are the same; else `mine` changed and not the writing: **local**, written in VS Code or in the tab; the writing changed and not the file: **data**, the export moved; both: **conflict**. A line of the writing the file no longer holds is **missing** (REQ-006); one written `own: true` is the engineer's (D-13) and in step. A line of the file that is no line of the writing -- a sentence, a command added by hand -- is the engineer's own and never compared.

STATES = ("in_sync", "own", "data", "local", "conflict", "missing", "masked")   # masked: a figure commented out in «Affichage» (D-23), the engineer's choice, never written over


@dataclass
class LineState:
    """One line of an unfolded domain: its id (`var:N_t_d`, `verify:v-6`, `label:ZT-01-member`), its state, its text in the file and in a new writing (None where it is not there)."""
    id: str
    state: str
    mine: str = None
    fresh: str = None


@dataclass
class Status:
    """An unfolded domain's standing: its lines in the writing's order, whether its form is the export's (`matches`), the check it is written from and whether that check is still unfolded (`unfolded`)."""
    id: str
    lines: list = field(default_factory=list)
    matches: bool = True
    unfolded: bool = True

    def of(self, state):
        return [line for line in self.lines if line.state == state]


def _items_by_line(items, legacy=False):
    """{line id: (index, item)} of a domain's items: commands by kind and `id:` -- by key in a file written before (`legacy`) --, texts by every label they carry."""
    out = {}
    for i, c in enumerate(items):
        if c.is_text:
            for line_id, _line in text_lines(c.raw):
                out[line_id] = (i, c)
            continue
        name = line_name(c, legacy)
        if name:
            out[f"{c.kind}:{name}"] = (i, c)
    return out


def _own_line(items, line_id, ours=None):
    """(index, item) of the engineer's own line in place of the writing's `line_id` -- the same command and key, its `id:` taken away (Q-006: a value kept against the export), or the line written again by the other of `#var` and `#eq` under the writing's `id:` (`#var("N", 0, …, id: "N")` made `#eq("N", `N_Ed`, …, id: "N")`, a polar moment's force read from the report; spec 2026-10-22-image-polar-moment) --, or None."""
    kind, _, name = line_id.partition(":")
    for i, c in enumerate(items):
        if c.is_text:
            continue
        if c.kind == kind and "id" not in c.options and c.key == name:
            return i, c
        if {c.kind, kind} == {"var", "eq"} and c.options.get("id") == name:
            # a line Woodcore wrote and the engineer left as it was is no line of his: the writing now gives the other command for it (s_k a `#var` before the spec 2026-10-22-onglet-neige-type, an `#eq` since), which «Régénérer» writes in its place (ARCH-RISK-F01)
            written = (ours or {}).get(f"{c.kind}:{name}")
            if written is not None:
                import sync
                if sync.digest(comparable_text(c)) == _pair(written)[0]:
                    continue
            return i, c
    return None


def _legacy(domain):
    """Whether `domain` is a file written before the generator of the spec 2026-10-21 -- its `#var-domain(…, gen:)` --, whose lines are found by their keys."""
    return domain.gen is not None


def _line_text(line_id, item):
    """The text a line is compared by: a command as Woodcore writes its call, without the arguments of its display (`comparable_text`, D-17) -- so that a form of the engineer's own, arguments over two lines or a comment after the call, is no change of it --, a labelled line or a figure its own line of its text."""
    if item.is_text:
        return next(line for lid, line in text_lines(item.raw) if lid == line_id).strip()
    return comparable_text(item)


# The stubs an earlier Woodcore wrote into a domain's file before it was written out (calc/domains/domain_file.py until the spec 2026-10-21-commandes-typst-refonte): the call each kind was printed by, its id in `{id}`. Recognised byte for byte -- the engine's import above it -- and written over by the domain, the commands they call being retired; never written any more.
LEGACY_STUBS = {
    "snow-load": '#show-calc("snow-load", {id})',
    "wind-load": '#show-calc("wind-load", {id})',
    "dead-load": '#show-calc("dead-load", {id})',
    "connector": "#show-connector({id})",
    "connection": "// the forces the connection carries: N:, V: (kN) and M: (kNm), as `#show-polar-moment(…, N: \"25 kN\")`\n#show-polar-moment({id})",
    "check": "#show-check-member({id})",
    "steel": "#show-check-steel({id})",
    "script": '#show-calc("script", {id})',
}


def is_legacy_stub(here, kind, domain_id, path):
    """Whether the file at `path` is, byte for byte, the stub an earlier Woodcore wrote for `domain_id` of `kind` (`LEGACY_STUBS`) -- a file Woodcore may still write over or archive."""
    import documents
    import structure
    if kind not in LEGACY_STUBS:
        return False
    call = LEGACY_STUBS[kind].replace("{id}", structure.typst_string(domain_id))
    try:
        return Path(path).read_bytes() == f"{documents.root_import_line(here)}\n\n{call}\n".encode("utf-8")
    except OSError:
        return False


def is_domain_file(path):
    """Whether `path` holds a domain written out whole -- its `#domain` or, written before, its `#var-domain` -- and not a stub that prints it folded (domains/domain_file.py)."""
    try:
        text = Path(path).read_text(encoding="utf-8", errors="replace")
        return "#var-domain(" in text or "#domain(" in text
    except OSError:
        return False


def unfolded_files(here, checks, kind="check"):
    """{id: the file from the Typst root} of every domain of `kind` of the export `checks` written out whose file holds its domain written out -- what the export records on a member check (`file`), and what #show-check-member includes (lib/timber.typ). A domain whose file is still a stub, or one the engineer wrote in, has none and is printed folded."""
    module = _module(kind)
    out = {}
    for rid, record in module.records(checks).items():
        if module.is_unfolded(record):
            path = domain_path(here, rid, record, kind)
            if is_domain_file(path):
                out[rid] = here.from_root(path)
    return out


def _read_domain(here, rid, kind="check"):
    from domains import formula_domain as fd
    path = domain_path(here, rid, kind=kind)
    if not path.is_file():
        raise UnfoldError(f"unfold: {here.rel(path)} is not there", "no_domain", id=rid)
    domain = fd.read(path)
    if domain.state == "unreadable":
        raise UnfoldError(f"unfold: {here.rel(path)} cannot be read -- {domain.problem}", "unreadable", id=rid, reason=domain.problem)
    return domain


def _fresh(here, record, lang, kind="check"):
    """The items of a new writing of `record` (its `#domain` body parsed as the file's is)."""
    from domains import formula_domain as fd
    with project.using(here):
        text = generate(record, lang, kind)
    span, _why = fd._body_span(text)
    from structure import _split
    _declared, _title, items, _gen, _header = fd.parse_domain("".join(_split(text)[span[0]:span[1]]))
    return items


def _record_of(here, rid, kind="check"):
    """The record of the domain `rid` of `kind` as the last export resolved it (data/checks.json, data/steel.json) -- what a writing is made from."""
    module = _module(kind)
    name = module.EXPORT_FILE
    try:
        checks = module.records(json.loads((here.data_dir / name).read_text(encoding="utf-8")))
    except (OSError, ValueError, KeyError, AttributeError) as exc:
        raise UnfoldError(f"unfold: data/{name} cannot be read ({exc}) -- export the project", "no_export") from exc
    return checks.get(rid)


def status(here, rid, lang=None, kind=None):
    """The standing of the domain `rid` Woodcore wrote out (of `kind`, `kind_of` where None): each line of a new writing of its record against the file and the base (REQ-007), the lines missing from the file (REQ-006), whether its form is still the export's (REQ-003)."""
    import positions_store
    import sync
    kind = kind or kind_of(here, rid)
    module = _module(kind)
    lang = lang or positions_store.project_language(here)
    domain = _read_domain(here, rid, kind)
    record = _record_of(here, rid, kind)
    out = Status(id=rid)
    if record is None or not module.is_unfolded(record):
        out.unfolded, out.matches = False, False
        return out
    entry = read_base(here, kind)["domains"].get(rid, {"lines": {}})
    # the form the file was written from: its header's `gen:` in a file written before, the base's since (REQ-012, ARCH-007)
    out.matches = module.form_of(record) == (domain.gen if _legacy(domain) else entry.get("gen"))
    mine_items = _items_by_line(domain.commands, _legacy(domain))
    for line_id, (_i, item) in _items_by_line(_fresh(here, record, lang, kind)).items():
        fresh = _line_text(line_id, item)
        held = mine_items.get(line_id)
        if held is None:
            own = None if _legacy(domain) else _own_line(domain.commands, line_id, entry["lines"])
            if own is not None:
                # the line with its `id:` taken away: the engineer's value, kept against the export (Q-006)
                out.lines.append(LineState(line_id, "own", _line_text(line_id, own[1]), fresh))
            else:
                out.lines.append(LineState(line_id, "missing", None, fresh))
            continue
        mine = _line_text(line_id, held[1])
        if not held[1].is_text and held[1].options.get("own") is True:
            out.lines.append(LineState(line_id, "own", mine, fresh))
            continue
        if line_id.startswith("figure:") and is_masked(mine):
            out.lines.append(LineState(line_id, "masked", mine, fresh))
            continue
        recorded = entry["lines"].get(line_id)
        if recorded is None and line_id.startswith("figure:"):
            # a figure an earlier Woodcore recorded by its label (D-29 finds it by its image since)
            label = re.search(r"<([A-Za-z0-9_.:-]+)>", mine)
            recorded = entry["lines"].get("label:" + label.group(1)) if label else None
        own, seen = _normalised(recorded, held[1], item)
        state = sync.three_way(sync.digest(mine), sync.digest(fresh), own, seen)
        out.lines.append(LineState(line_id, {"incoming": "data"}.get(state, state), mine, fresh))
    return out


def _normalised(recorded, mine, fresh):
    """(own, seen) of a line, read the way the base records it since D-17: a digest written before, of the whole call with the arguments of its display (a member's `level: 0`, a polar moment's), is taken as the digest of the call without them, so that a base written by an earlier Woodcore reads no false conflict (ARCH-RISK-F04). The next write records the new digests."""
    import sync
    from domains import formula_domain as fd
    own, seen = _pair(recorded)
    if not mine.is_text and own is not None and own == sync.digest(fd.to_call(mine).strip()):
        own = sync.digest(comparable_text(mine))
    if not fresh.is_text and seen is not None and seen == sync.digest(fd.to_call(fresh).strip()):
        seen = sync.digest(comparable_text(fresh))
    return own, seen


def _pair(recorded):
    """(own, seen) of a line in the base: a pair since a line may be taken as the engineer wrote it (own) while the writing says otherwise (seen); a bare digest is both -- what a line just written records."""
    if recorded is None:
        return None, None
    if isinstance(recorded, list):
        return recorded[0], recorded[1]
    return recorded, recorded


# --- writing: every operation reads, checks, then writes its files at once ------------------------------------------------

def _write(here, domain, items, base, rid, record_lines, gen=None, kind="check"):
    """The domain written with `items` -- only what changed, formula_domain's targeted write (ARCH-006) --, and its base entry, at once: the domain's file and the base, each beside itself and moved into place, the first put back where the second fails (CON-005, `sharing._commit`). The file is checked unchanged on the disk first."""
    import sharing
    from domains import formula_domain as fd
    fd.check_unchanged(domain)
    changed = fd.replace(domain, commands=items, gen=None if gen is False else gen if gen is not None else domain.gen)
    text = fd.write_text(changed)
    base["domains"][rid] = record_lines
    import validation
    where = base_path(here, kind)
    validation.validate_structure(base, BASE_SCHEMA, where=here.rel(where))
    payload = json.dumps(base, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    sharing._commit([(domain.path, text.encode("utf-8"), domain.text.encode("utf-8")),
                     (where, payload.encode("utf-8"), where.read_bytes() if where.is_file() else None)])
    return text


def _entry(record, base, rid, kind="check"):
    entry = base["domains"].get(rid)
    if entry is None:
        entry = {"check": rid, "gen": _module(kind).form_of(record), "lines": {}}
    return {"check": entry["check"], "gen": dict(entry["gen"]), "lines": dict(entry["lines"])}


def _replace_line(items, index, line_id, fresh_item):
    """`items` with the line `line_id` of item `index` replaced by the writing's: a command's arguments that differ, written over its lines as they stand, the arguments of its display kept (D-17); the labelled line of a text, or its figure, alone (the rest of the text is the engineer's)."""
    items = list(items)
    old = items[index]
    if old.is_text:
        new_line = _line_text(line_id, fresh_item)
        lines = old.raw.split("\n")
        lines = [(l[:len(l) - len(l.lstrip())] + new_line) if any(lid == line_id for lid, _l in text_lines(l)) else l for l in lines]
        from domains import formula_domain as fd
        items[index] = fd.Command(old.kind, raw="\n".join(lines))
    else:
        from domains import formula_domain as fd
        # the file's lines kept with it: formula_domain writes only the arguments the writing changed (ARCH-003)
        items[index] = _with_display(fresh_item, old) if old.kind == fresh_item.kind else fresh_item
    return items


def refresh(here, rid, lang=None, kind=None):
    """Takes every line whose export changed and not its file (`data`) as the writing now gives it -- what an export does, without a question (REQ-008): only those lines are rewritten, everything else of the file kept byte for byte. Nothing is done where the form changed (that is «Régénérer», REQ-010) or nothing is `data`. Returns the line ids refreshed."""
    import positions_store
    import sync
    lang = lang or positions_store.project_language(here)
    kind = kind or kind_of(here, rid)
    st = status(here, rid, lang, kind)
    if not st.unfolded or not st.matches:
        return []
    todo = [line for line in st.lines if line.state == "data"]
    if not todo:
        return []
    domain = _read_domain(here, rid, kind)
    record = _record_of(here, rid, kind)
    base = read_base(here, kind)
    entry = _entry(record, base, rid, kind)
    fresh = _items_by_line(_fresh(here, record, lang, kind))
    items = list(domain.commands)
    for line in todo:
        index, _item = _items_by_line(items, _legacy(domain))[line.id]
        items = _replace_line(items, index, line.id, fresh[line.id][1])
        digest = sync.digest(line.fresh)
        entry["lines"][line.id] = [digest, digest]
    _write(here, domain, items, base, rid, entry, kind=kind)
    return [line.id for line in todo]


# The fields of a check's source a line of its unfolded domain comes from (REQ-009 a): what «Importer» writes back into Woodcore-Datei/checks/<id>.json. A line not listed -- a value of a table, a factor of the norm -- cannot be written back and becomes the engineer's own (D-13).
SOURCE_FIELDS = {"var:N_t_d": "N", "var:alpha": "alpha", "var:b": "b", "var:h": "h", "var:d": "d", "var:eta_t": "impact"}


def _to_source(here, rid, line_id, item):
    """Writes the value of `item` -- a line of the domain changed in VS Code -- into the check's source, through `member_check.write_source` (validated, atomic). Returns True where the value had somewhere to go, False where it cannot be written back (then the caller makes it the engineer's own)."""
    import units
    from domains import member_check
    field_name = SOURCE_FIELDS.get(line_id)
    if field_name is None or item.is_text or item.kind != "var" or not isinstance(item.value, (int, float)):
        return False
    path = here.checks_dir / f"{rid}.json"
    src = json.loads(path.read_text(encoding="utf-8"))
    value, unit = item.value, item.unit or ""
    if field_name == "N":
        if unit not in ("kN", "N", "MN"):
            return False
        src["N"] = {"value": value, "unit": unit}
    elif field_name == "alpha":
        src["alpha"] = value
    elif field_name == "impact":
        from norms import sia265
        block = sia265.eta_t_block()
        if value == block["impact"]:
            src["impact"] = True
        elif value == block["normal"]:
            src["impact"] = False
        else:
            return False
    else:
        q = units.quantity(float(value), units.written_unit(unit or "mm"))
        if q is None:
            return False
        mm = q.base * 1000
        record = _record_of(here, rid)
        section = dict(src.get("section") or record["section"])
        section = {k: section[k] for k in section if k in ("type", "b", "h", "d")}
        section[field_name] = mm
        src["section"] = section
    member_check.write_source(here, src)
    return True


def import_lines(here, rid, ids=None, choices=None, lang=None, kind=None):
    """«Importer» a line, or «Tout importer» (`ids` None): every line changed in the file (`local`) is taken into Woodcore -- a value of the check's source written back there (REQ-009 a), any other value made the engineer's own, `own: true` (b, D-13), a formula or a line of text taken as the engineer wrote it --; a conflict is imported only with a choice, `choices` {line id: "mine" | "theirs"} -- «mine» keeps the file's line as above, «theirs» takes the writing's. Returns {"imported": [...], "conflicts": [...]}: the conflicts left without a choice."""
    import positions_store
    import sync
    from domains import formula_domain as fd, member_check
    lang = lang or positions_store.project_language(here)
    kind = kind or kind_of(here, rid)
    choices = choices or {}
    st = status(here, rid, lang, kind)
    asked = [line for line in st.lines if line.state in ("local", "conflict") and (ids is None or line.id in ids)]
    domain = _read_domain(here, rid, kind)
    record = _record_of(here, rid, kind)
    base = read_base(here, kind)
    entry = _entry(record, base, rid, kind)
    items = list(domain.commands)
    fresh = _items_by_line(_fresh(here, record, lang, kind))
    imported, conflicts, to_source = [], [], []
    for line in asked:
        choice = "mine" if line.state == "local" else choices.get(line.id)
        if choice is None:
            conflicts.append(line.id)
            continue
        index, item = _items_by_line(items, _legacy(domain))[line.id]
        if choice == "theirs":
            items = _replace_line(items, index, line.id, fresh[line.id][1])
            digest = sync.digest(line.fresh)
            entry["lines"][line.id] = [digest, digest]
        elif kind == "check" and line.id in SOURCE_FIELDS and not item.is_text and item.kind == "var":
            to_source.append((line.id, item))
        elif not item.is_text and item.kind == "var" and item.source and item.value is not None:
            items[index] = _made_own(domain, item)
            _forget(entry, line.id, domain, items[index], line.fresh)
        else:
            entry["lines"][line.id] = [sync.digest(line.mine), sync.digest(line.fresh)]
        imported.append(line.id)
    # the values that go back into the check's source: written there, the check exported again, and the lines then in step with their new writing
    for line_id, item in to_source:
        if not _to_source(here, rid, line_id, item):
            index, item = _items_by_line(items, _legacy(domain))[line_id]
            items[index] = _made_own(domain, item)
            _forget(entry, line_id, domain, items[index], fresh[line_id][1].written or fd.to_call(fresh[line_id][1]))
    if to_source:
        data = member_check.export(here)
        record = data["checks"][rid]
        fresh = _items_by_line(_fresh(here, record, lang))
        for line_id, item in to_source:
            if line_id in fresh:
                digest = sync.digest(_line_text(line_id, fresh[line_id][1]))
                entry["lines"][line_id] = [sync.digest(_line_text(line_id, _items_by_line(items, _legacy(domain))[line_id][1])), digest]
    if imported:
        _write(here, domain, items, base, rid, entry, kind=kind)
    return {"imported": imported, "conflicts": conflicts}


def _made_own(domain, item):
    """A line made the engineer's own (D-13, Q-006): its `id:` taken away -- what keeps a value against the export since the spec 2026-10-21 --, or `own: true` in a file written before."""
    from domains import formula_domain as fd
    if _legacy(domain):
        return fd.replace(item, options={**item.options, "own": True})
    return fd.replace(item, options={k: v for k, v in item.options.items() if k != "id"})


def _forget(entry, line_id, domain, mine, fresh_text):
    """The base's record of a line made the engineer's own: in a file of the generator 2 the line is no longer Woodcore's and leaves the base; written before, it keeps its pair (own, seen)."""
    import sync
    from domains import formula_domain as fd
    if _legacy(domain):
        entry["lines"][line_id] = [sync.digest(comparable_text(mine)), sync.digest(fresh_text)]
    else:
        entry["lines"].pop(line_id, None)


def take_back(here, rid, line_id, lang=None, kind=None):
    """«Reprendre» (D-13): an engineer's own value goes back to the export's -- the writing's line written in its place, `own: true` gone."""
    import positions_store
    import sync
    lang = lang or positions_store.project_language(here)
    kind = kind or kind_of(here, rid)
    domain = _read_domain(here, rid, kind)
    record = _record_of(here, rid, kind)
    base = read_base(here, kind)
    entry = _entry(record, base, rid, kind)
    fresh = _items_by_line(_fresh(here, record, lang, kind))
    held = _items_by_line(domain.commands, _legacy(domain)).get(line_id)
    if held is None and not _legacy(domain):
        held = _own_line(domain.commands, line_id)   # the engineer's own line, its `id:` taken away (Q-006)
    if held is None or line_id not in fresh:
        raise UnfoldError(f"unfold: {rid} holds no line {line_id!r} to take back", "no_line", id=rid, line=line_id)
    items = _replace_line(domain.commands, held[0], line_id, fresh[line_id][1])
    digest = sync.digest(_line_text(line_id, fresh[line_id][1]))
    entry["lines"][line_id] = [digest, digest]
    _write(here, domain, items, base, rid, entry, kind=kind)


def reinsert(here, rid, line_id, lang=None, kind=None):
    """«Réinsérer» (REQ-006): a line of the writing the file no longer holds is put back where the writing has it -- after the nearest line before it that the file still holds, or holds as the engineer's own (`_own_line`), else at the head of the body."""
    import positions_store
    import sync
    lang = lang or positions_store.project_language(here)
    kind = kind or kind_of(here, rid)
    domain = _read_domain(here, rid, kind)
    record = _record_of(here, rid, kind)
    base = read_base(here, kind)
    entry = _entry(record, base, rid, kind)
    fresh_items = _fresh(here, record, lang, kind)
    fresh = _items_by_line(fresh_items)
    held = _items_by_line(domain.commands, _legacy(domain))
    if line_id not in fresh or line_id in held:
        raise UnfoldError(f"unfold: {rid} misses no line {line_id!r}", "no_line", id=rid, line=line_id)
    order = list(fresh)
    at = 0
    for previous in reversed(order[:order.index(line_id)]):
        found = held.get(previous) or (None if _legacy(domain) else _own_line(domain.commands, previous))
        if found is not None:
            at = found[0] + 1
            break
    items = list(domain.commands)
    items.insert(at, fresh[line_id][1])
    digest = sync.digest(_line_text(line_id, fresh[line_id][1]))
    entry["lines"][line_id] = [digest, digest]
    _write(here, domain, items, base, rid, entry, kind=kind)


def regenerate(here, rid, choices=None, lang=None, kind=None):
    """«Régénérer» (REQ-010): the domain written again from its check's form now, line by line against the file and the base: a line the engineer did not change takes the new writing; one he changed is kept where the new writing has it, and one the new writing changes too is a conflict asked line by line (`choices` {line id: "mine" | "theirs"}); a line the new form adds is put in its place, one it drops is taken out unless the engineer changed it; his own items -- a sentence, a command of his -- stay after the line they followed. The header takes the new `gen:`. Returns {"conflicts": [...]}: nothing is written while one is left without a choice."""
    import positions_store
    import sync
    lang = lang or positions_store.project_language(here)
    kind = kind or kind_of(here, rid)
    module = _module(kind)
    choices = choices or {}
    domain = _read_domain(here, rid, kind)
    record = _record_of(here, rid, kind)
    if record is None or not module.is_unfolded(record):
        raise UnfoldError(f"unfold: the check {rid} is no longer printed unfolded -- nothing to write it from", "not_unfolded", id=rid)
    base = read_base(here, kind)
    ours = base["domains"].get(rid, {"lines": {}})["lines"]
    fresh_items = _fresh(here, record, lang, kind)
    fresh = _items_by_line(fresh_items)
    held = _items_by_line(domain.commands, _legacy(domain))
    changed, conflicts = set(), []
    for line_id, (_i, item) in held.items():
        own, _seen = _pair(ours.get(line_id))
        if own is None or sync.digest(_line_text(line_id, item)) == own:
            continue
        changed.add(line_id)
        # a conflict where the new writing changed that line too since it was last seen, and differs from the engineer's
        if line_id in fresh and line_id not in choices:
            now = _line_text(line_id, fresh[line_id][1])
            if sync.digest(now) != _pair(ours.get(line_id))[1] and now != _line_text(line_id, item):
                conflicts.append(line_id)
    if conflicts:
        return {"conflicts": conflicts}
    # the engineer's own line in place of a line of the writing the file no longer holds (`_own_line`): kept in that line's place, never doubled by the writing's -- which would declare its id twice and stop the compile (spec 2026-10-22-image-polar-moment)
    owned = {}
    if not _legacy(domain):
        for lid in fresh:
            own = None if lid in held else _own_line(domain.commands, lid, ours)
            if own is not None:
                owned[lid] = own[1]
    owner = {id(item): lid for lid, item in owned.items()}
    # the engineer's own items, and the lines the new form drops but he changed, after the last line of the writing they followed
    extras, previous = {}, None
    for c in domain.commands:
        if id(c) in owner:
            previous = owner[id(c)]
            continue
        ids = list(_items_by_line([c], _legacy(domain)))
        lid = ids[0] if ids else None
        if lid is not None and lid in fresh:
            previous = lid
            continue
        if lid is not None and lid in ours and lid not in changed:
            continue
        extras.setdefault(previous, []).append(c)
    items = list(extras.get(None, []))
    entry = {"check": rid, "gen": module.form_of(record), "lines": {}}
    for c in fresh_items:
        ids = list(_items_by_line([c]))
        lid = ids[0] if ids else None
        if lid is not None and lid in changed and choices.get(lid, "mine") == "mine":
            mine = held[lid][1]
            items.append(mine)
            entry["lines"][lid] = [sync.digest(_line_text(lid, mine)), sync.digest(_line_text(lid, c))]
        elif lid in owned:
            items.append(owned[lid])
            digest = sync.digest(_line_text(lid, c))
            entry["lines"][lid] = [digest, digest]
        else:
            # a line the engineer left as it was takes the writing's, the display he gave it kept (D-17, ARCH-RISK-F02)
            items.append(_with_display(c, held[lid][1]) if lid in held and not c.is_text and not held[lid][1].is_text and held[lid][1].kind == c.kind else c)
            # every line of the writing it holds -- a text carries several labels, each a line of its own (spec 2026-10-22-image-polar-moment: the first alone was recorded)
            for each in ids:
                digest = sync.digest(_line_text(each, c))
                entry["lines"][each] = [digest, digest]
        items += extras.get(lid, []) if lid is not None else []
    # the header the generator writes now -- `#domain`, no `gen:` (REQ-012) --, the form kept in the base
    _write(here, domain, items, base, rid, entry, gen=False, kind=kind)
    return {"conflicts": []}


# --- what the export tells Typst of the domains Woodcore wrote (spec 2026-10-21-commandes-typst-refonte, REQ-012, ARCH-007, ARCH-008) ---

STATE_FILE = "domain-state.json"
STATE_SCHEMA = "domain-state"
FILES_FILE = "domain-files.json"
FILES_SCHEMA = "domain-files"
DATA_SCHEMA_VERSION = "1.0"


def empty_state():
    return {"schema_version": DATA_SCHEMA_VERSION, "domains": {}}


def empty_files():
    return {"schema_version": DATA_SCHEMA_VERSION, "files": {}}


def _exports(checks, steel, calculations, connectors=None, connections=None, scripts=None):
    """[(kind, export)] of every kind Woodcore writes out: the member checks, the steel checks, each load of data/calculations.json, the connectors, the polar moments, the scripts."""
    return [("check", checks), ("steel", steel)] + [(kind, calculations) for kind in LOAD_KINDS] + [("connector", connectors), ("connection", connections), ("script", scripts)]


def domain_files(here, checks, steel=None, calculations=None, connectors=None, connections=None, scripts=None):
    """data/domain-files.json: the file of each domain Woodcore wrote, by kind and id, from the Typst root -- what `domain-file(kind, id)` reads (ARCH-008): the member checks of the export `checks`, the steel checks of `steel`, the loads of `calculations`."""
    out = {}
    for kind, data in _exports(checks, steel, calculations, connectors, connections, scripts):
        files = unfolded_files(here, data, kind) if data else {}
        if files:
            out[kind] = dict(sorted(files.items()))
    # each document's journal, written once beside its entry file (domains/list_files.py): `domain-file("journal", document)`
    from domains import list_files
    journals = list_files.journal_files(here)
    if journals:
        out["journal"] = journals
    return {"schema_version": DATA_SCHEMA_VERSION, "files": out}


def domain_state(here, checks, lang=None, steel=None, calculations=None, connectors=None, connections=None, scripts=None):
    """data/domain-state.json: for each domain Woodcore wrote from a check, the form it was written for against the one its data asks for now, and the lines it could not apply (missing, conflict) -- what `#domain` prints in red at its head (REQ-012), the file being the engineer's and never rewritten for it. A domain whose check left the export, or is no longer written out, is `gone`. One that cannot be compared is left out: the window says why."""
    import positions_store
    lang = lang or positions_store.project_language(here)
    out = {}
    for kind, data in _exports(checks, steel, calculations, connectors, connections, scripts):
        if kind != "check" and not here.has_folders:
            continue
        module = _module(kind)
        base = read_base(here, kind)
        records = module.records(data or {})
        for rid, entry in sorted(base["domains"].items()):
            path = domain_path(here, rid, records.get(rid), kind)
            if not is_domain_file(path):
                continue
            record = records.get(rid)
            written = entry.get("gen")
            # what the summary of the checks names the check by: a member check's kind, `steel-<kind>` for a steel check (lib/summary.typ, `summary.verify.*`)
            prefix = "" if kind == "check" else "steel-" if kind == "steel" else None   # a load is no check
            if record is None or not module.is_unfolded(record):
                gone_kind = (written or {}).get("kind") if prefix is not None else None
                out[rid] = {"kind": kind, "check": gone_kind, "written": written, "form": None, "matches": False, "gone": True,
                            "missing": [], "conflict": [], "file": here.from_root(path)}
                continue
            try:
                with project.using(here):
                    st = status(here, rid, lang, kind)
            except (UnfoldError, validation.ValidationError):
                continue
            out[rid] = {"kind": kind, "check": None if prefix is None else prefix + record.get("kind"), "written": written, "form": module.form_of(record), "matches": st.matches, "gone": False,
                        "missing": [line.id for line in st.of("missing")], "conflict": [line.id for line in st.of("conflict")], "file": here.from_root(path)}
    return {"schema_version": DATA_SCHEMA_VERSION, "domains": dict(sorted(out.items()))}
