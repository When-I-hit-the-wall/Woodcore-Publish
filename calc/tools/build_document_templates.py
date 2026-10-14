"""Writes the two builtin document templates -- `templates/documents/cu/standard/` and `templates/documents/bp/standard/`, the convention d'utilisation and the base de projet in French, German and English -- from the section catalogue of the three document modes (phase 3, work package 3.2).

    python calc/tools/build_document_templates.py <catalogue.json> [--dry-run]

The catalogue is the maintainers' own file and is not shipped: it holds, for each mode, the groups and the lowest-level sections of the document in SIA 260's order, and for each section its blocks -- text, table, list to tick, single choice, picture, the norms it names, the signatures -- in the three languages (its `_about` says how). What this script makes of it is **exactly what `calc/doc_templates.py` reads**: for each mode and each language a folder that is the document's own folder -- the entry `.typ`, its `structure.json` and one `Sections/<id>.typ` per lowest-level section -- and the `template.json` beside the three.

- A section file is `#import "/commands.typ": *`, its heading `= <title>` and its blocks in order: a text as the Typst markup it is written in, every other block as the parametric object of `lib/document.typ` that prints it, between its two tags (`// woodcore:object <command> <id>` … `// woodcore:/object <id>`) and written in the canonical form the editor writes back -- one named argument per line, two spaces in, a trailing comma everywhere, the arguments in the order of the command's signature, a column, a row, an option on a line of its own. **Every heading and every paragraph is an object too** (the engineer's rework of 01.10.2026): `typst_objects.tag_file` wraps them in `// woodcore:object heading title` … and `// woodcore:object text p1` … once the file is written out -- the ids `title`, `h2`, `h3` and `p1`, `p2` …, the same in the three languages, so that a shared section has the same ids in both documents. The import line, the journal's `#show-journal()` and every other line of code are not paragraphs and stay as they are.
- A section the catalogue shares between the two documents by default has **the same file** in both, its body after the import line between `// woodcore:shared <id>` and `// woodcore:/shared <id>`, and `shared_with` naming the other document in both structure.json files. What the catalogue marks shareable with the report is not shared here: the report's structure is its own.
- The structure says which section is printed by default (the catalogue's `enabled_default`); a section switched off keeps its file.
- The entry file keeps the form it has -- the title page, the outline, the language and the level settings, `#show: woodcore-document.with(document: …)` -- and only its generated structure block is written again, by `structure.sync_entry`.

What the template adds to the catalogue, or takes from it, is said in `amend` below, each change with its reason; a rerun on the same catalogue writes the same bytes.

Nothing here is read at run time: the templates are committed, and `tests/test_doc_templates.py` holds what they must be.
"""

import argparse
import copy
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "calc") not in sys.path:
    sys.path.insert(0, str(ROOT / "calc"))

import structure  # noqa: E402
import typst_objects  # noqa: E402

LANGS = ("fr", "de", "en")
MODES = ("cu", "bp")
OTHER = {"cu": "bp", "bp": "cu"}
TEMPLATES = ROOT / "templates" / "documents"
FOLDER = "standard"
IMPORT = '#import "/commands.typ": *'
NNBSP = "\u202f"

# The journal: every document prints its own revision history (the engineer's answer), a leaf of its own at the end, as the report's 008-journal is. The catalogue lists it among the front matter the engine generates; it is kept a section so that it can be switched off like any other.
JOURNAL = {"fr": "Historique des versions", "de": "Änderungsverzeichnis", "en": "Revision history"}

# What the norms section selects by default: the catalogue's six, and the norms the chapters switched on by default rest on -- the materials and the ground (SIA 262, 263, 267), the building physics (SIA 180, SIA 380/1), the sound insulation and the room acoustics (SIA 181, SIA 181/1) and the fire protection (the VKF / AEAI Brandschutznorm and its directives) -- each by its key in calc/norms/norms.json, which carries its current edition (SIA 262:2025, not 2013).
NORM_KEYS = ("SIA 260", "SIA 261", "SIA 261/1", "SIA 262", "SIA 263", "SIA 265", "SIA 265/1", "SIA 267",
             "SIA 180", "SIA 380/1", "SIA 181", "SIA 181/1",
             "VKF 1-15", "VKF 13-15", "VKF 14-15", "VKF 15-15")


PSI_IDS = ("psi_0", "psi_1", "psi_2")


def T(fr, de, en):
    return {"fr": fr, "de": de, "en": en}


# The names of the three unit weights the catalogue's table picks from SIA 261 Tabelle 28 by id (calc/norms/sia261-2020-tab28-raumlasten-baustoffe.json, whose names are German): the norm's words, and its French and English.
UNIT_WEIGHT_NAMES = {
    "baustahl": T("Acier de construction", "Baustahl", "Structural steel"),
    "beton_bewehrt": T("Béton armé", "Beton, bewehrt", "Reinforced concrete"),
    "holz_nadelhoelzer_allgemein": T("Bois résineux, en général", "Holz, Nadelhölzer allgemein", "Softwood, in general"),
}


# --- the catalogue, amended -------------------------------------------------------------------

def walk(nodes):
    for node in nodes:
        yield node
        yield from walk(node.get("children", ()))


def node_of(cat, mode, node_id):
    for node in walk(cat["modes"][mode]["sections"]):
        if node["id"] == node_id:
            return node
    raise KeyError(f"{mode}: no section {node_id!r} in the catalogue")


def block_of(node, block_id):
    for block in node.get("content", ()):
        if block["id"] == block_id:
            return block
    raise KeyError(f"{node['id']}: no block {block_id!r}")


def cite(norm):
    return f'#cite-norm(norm: "{norm}")'


def _french_names(obj):
    """The French strings of `obj` naming the base de projet by the document's own name (spec: «Base de projet»), where the catalogue quoted SIA 260 FR's «base du projet»."""
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key == "fr" and isinstance(value, str):
                obj[key] = value.replace("base du projet", "base de projet").replace("Base du projet", "Base de projet")
            else:
                _french_names(value)
    elif isinstance(obj, list):
        for value in obj:
            _french_names(value)


def amend(cat):
    """The catalogue as the templates carry it. Every change is one the engineer asked for or a norm that has moved, and is said here."""
    cat = copy.deepcopy(cat)
    # 1. The base de projet is called by the document's own name in French, as its folder and its title page call it.
    _french_names(cat["modes"])

    # 1b. ψ is never shown for the live loads (the engineer, 01.10.2026): the catalogue's table carries the three Reduktionsbeiwerte of SIA 260 Tabelle 2 as optional columns, and the template does not.
    for mode in MODES:
        block = block_of(node_of(cat, mode, "live-loads"), "live-loads-table")
        block["columns"] = [c for c in block["columns"] if c["id"] not in PSI_IDS]
        for row in block["rows"]:
            for key in PSI_IDS:
                row.pop(key, None)

    # 2. The norms section selects, by default, what the chapters switched on by default rest on -- with their current editions, which norms.json carries (section «Normen»).
    for mode in MODES:
        block_of(node_of(cat, mode, "norms"), "norms-selection")["default_keys"] = list(NORM_KEYS)

    # 3. SIA 262:2013 is superseded by SIA 262:2025 (valid from 01.11.2025), which is not in the library: the design values the catalogue read off the 2013 edition (f_cd, τ_cd, f_sd, E_s) are left for the engineer to write from the current edition, and the table says which edition. What a class names -- f_ck of a C25/30, f_sk of a B500B -- and the unit weights of SIA 261 Tabelle 28 stay.
    concrete = block_of(node_of(cat, "bp", "concrete"), "concrete-table")
    for row in concrete["rows"]:
        row["fcd"] = row["taucd"] = "[…]"
    steel = block_of(node_of(cat, "bp", "reinforcing-steel"), "reinforcing-steel-table")
    for row in steel["rows"]:
        row["fsd"] = row["Es"] = "[…]"
    note_262 = T("Valeurs de calcul selon la norme SIA 262:2025.", "Bemessungswerte nach der Norm SIA 262:2025.",
                 "Design values in accordance with SIA 262:2025.")
    concrete["notes"] = [note_262] + list(concrete.get("notes", []))
    steel["notes"] = [note_262] + list(steel.get("notes", []))
    #    and a clause number of the 2013 edition is not cited against the 2025 one.
    cracking = block_of(node_of(cat, "cu", "cracking-requirements"), "cracking-text")
    for lang in LANGS:
        cracking["text"][lang] = re.sub(r" \((?:art|Art)\. 4\.4\.2\.2\.3\)", "", cracking["text"][lang])

    # 4. Fire protection, building physics and noise stay switched on (the engineer's second answer) and name the norms they rest on with their current editions: SIA 180:2014, SIA 380/1:2016, SIA 181:2020, SIA 181/1:2026 and the VKF / AEAI directives -- listed in full by `show-norm-list`, cited in the text by `cite-norm`.
    fire = node_of(cat, "bp", "fire-protection-bases")
    text = block_of(fire, "fire-bases-text")
    lead = T(f"Les prescriptions et documents suivants s'appliquent en particulier{NNBSP}:",
             "Es gelten insbesondere die folgenden Vorschriften und Dokumente:",
             "The following regulations and documents apply in particular:")
    for lang in LANGS:
        text["text"][lang] = text["text"][lang].split("\n\n")[0] + "\n\n" + lead[lang]
    fire["content"].append({"kind": "norms", "id": "fire-protection-norms",
                            "default_keys": ["VKF 1-15", "VKF 13-15", "VKF 14-15", "VKF 15-15"],
                            "lines": [T("Documentation Lignum Protection incendie", "Lignum-Dokumentation Brandschutz",
                                        "Lignum fire protection documentation")]})

    physics = node_of(cat, "bp", "building-physics")
    physics["children"].insert(0, {
        "id": "building-physics-bases",
        "title": T("Bases de la physique du bâtiment", "Grundlagen der Bauphysik", "Bases of building physics"),
        "shared": [], "enabled_default": True,
        "content": [
            {"kind": "text", "id": "building-physics-bases-text", "text": T(
                "Les exigences relatives à la protection thermique, à la protection contre l'humidité, à l'étanchéité à l'air et aux besoins de chaleur pour le chauffage se fondent sur les normes suivantes ainsi que sur la réglementation cantonale sur l'énergie [canton, ordonnance]" + NNBSP + ":",
                "Die Anforderungen an den Wärmeschutz, den Feuchteschutz, die Luftdichtheit und den Heizwärmebedarf richten sich nach den folgenden Normen sowie nach der kantonalen Energiegesetzgebung [Kanton, Verordnung]:",
                "The requirements for thermal insulation, moisture protection, airtightness and the heating demand follow the standards below and the cantonal energy legislation [canton, ordinance]:")},
            {"kind": "norms", "id": "building-physics-norms", "default_keys": ["SIA 180", "SIA 380/1"], "lines": []},
        ],
    })
    for node_id, block_id in (("thermal-and-moisture-protection", "thermal-text"), ("airtightness", "airtightness-text")):
        block = block_of(node_of(cat, "bp", node_id), block_id)
        for lang in LANGS:
            assert block["text"][lang].count("SIA 180") == 1, (node_id, lang)
            block["text"][lang] = block["text"][lang].replace("SIA 180", cite("SIA 180"))
    heating = block_of(node_of(cat, "bp", "heating"), "heating-text")
    lead = T(f"Les besoins de chaleur pour le chauffage sont justifiés selon la norme {cite('SIA 380/1')}.",
             f"Der Heizwärmebedarf wird nach der Norm {cite('SIA 380/1')} nachgewiesen.",
             f"The heating demand is verified in accordance with {cite('SIA 380/1')}.")
    for lang in LANGS:
        heating["text"][lang] = lead[lang] + " " + heating["text"][lang]

    noise = node_of(cat, "bp", "noise-protection-bases")
    block_of(noise, "noise-bases-text")["text"] = T(
        f"Les exigences de protection contre le bruit se fondent sur les normes et documents suivants{NNBSP}:",
        "Die Anforderungen an den Schallschutz stützen sich auf die folgenden Normen und Grundlagen:",
        "The noise protection requirements are based on the following standards and documents:")
    noise["content"].append({"kind": "norms", "id": "noise-protection-norms", "default_keys": ["SIA 181", "SIA 181/1"],
                             "lines": [T("Ordonnance sur la protection contre le bruit (OPB)", "Lärmschutz-Verordnung (LSV)",
                                         "Noise Abatement Ordinance (LSV / OPB)"),
                                       T("Plans de l'architecte", "Pläne der Architektur", "Architect's drawings")]})
    return cat


# --- the canonical call grammar ------------------------------------------------------------------

def tr(value, lang):
    """A catalogue value in `lang`: a {fr, de, en} dict read in it, anything else as it is (language-neutral)."""
    if isinstance(value, dict) and set(value) >= set(LANGS):
        return value[lang]
    return value


def string(text):
    """A Typst string literal, with the three escapes the grammar knows."""
    return structure.typst_string(text)


def content(markup):
    """`markup` as a content block, `[…]`. Its brackets must balance, or the block would end early -- a catalogue text that does not is refused here rather than written."""
    depth = 0
    for i, ch in enumerate(markup):
        if ch == "\\":
            continue
        if ch == "[" and (i == 0 or markup[i - 1] != "\\"):
            depth += 1
        elif ch == "]" and (i == 0 or markup[i - 1] != "\\"):
            depth -= 1
            if depth < 0:
                raise ValueError(f"unbalanced ] in {markup!r}")
    if depth:
        raise ValueError(f"unbalanced [ in {markup!r}")
    if "\n" in markup:
        raise ValueError(f"a line break in a value written on one line: {markup!r}")
    return "[" + markup + "]"


def number(x):
    return str(x) if isinstance(x, int) and not isinstance(x, bool) else repr(float(x))


def inline_dict(pairs):
    return "(" + ", ".join(f"{key}: {value}" for key, value in pairs) + ")"


def inline_array(items):
    if not items:
        return "()"
    if len(items) == 1:
        return "(" + items[0] + ",)"
    return "(" + ", ".join(items) + ")"


def call(command, arguments):
    """`#command(` one named argument a line `)`, each value either one line or a list of lines (an array written one item a line)."""
    lines = [f"#{command}("]
    for name, value in arguments:
        if isinstance(value, list):
            if not value:
                lines.append(f"  {name}: (),")
            else:
                lines.append(f"  {name}: (")
                lines += [f"    {item}," for item in value]
                lines.append("  ),")
        else:
            lines.append(f"  {name}: {value},")
    lines.append(")")
    return lines


def tagged(command, object_id, arguments):
    if not structure.ID_PATTERN.match(object_id):
        raise ValueError(f"{object_id!r} is not an object id")
    return [f"// woodcore:object {command} {object_id}", *call(command, arguments), f"// woodcore:/object {object_id}"]


# --- the math a column heading is written with ---------------------------------------------------

def math_source(source):
    """A heading symbol in the math the engine writes: a subscript of several letters an upright word (`f_(c k)` -> `f_"ck"`, `E_(0,m e a n)` -> `E_(0,"mean")`, `w_(max)` -> `w_"max"`) -- the catalogue spelt them as letters apart, which math sets as a product of italic letters."""
    def part(p):
        p = p.strip()
        if " " in p and all(len(tok) == 1 for tok in p.split()):
            return '"' + p.replace(" ", "") + '"'
        if re.fullmatch(r"[A-Za-z]{2,}", p) and p not in ("psi", "phi", "rho", "tau", "gamma", "mu", "eta", "beta"):
            return '"' + p + '"'
        return p

    def group(m):
        parts = [part(p) for p in m.group(1).split(",")]
        return "_" + (parts[0] if len(parts) == 1 else "(" + ",".join(parts) + ")")
    return re.sub(r"_\(([^()]*)\)", group, source)


PSI = {"ψ₀": "$psi_0$", "ψ₁": "$psi_1$", "ψ₂": "$psi_2$"}


def heading(column, lang):
    """A column's heading as content: its word, and the symbol it is written with after it where the catalogue gives one (the word staying the word)."""
    word = tr(column["title"], lang)
    replaced = False
    for glyph, math in PSI.items():
        if glyph in word:
            word, replaced = word.replace(glyph, math), True
    if column.get("title_math") and not replaced:
        word = f"{word} ${math_source(column['title_math'])}$"
    return content(word)


# --- the blocks ------------------------------------------------------------------------------------

KIND = {"number": "number", "math": "math", "category": "math"}


def cell_text(value, column, lang):
    """What a cell prints, as markup: the text a column's heuristics measure, and what `cell` wraps."""
    value = tr(value, lang)
    if isinstance(value, str) and column.get("type") == "choice":
        options = column.get("options") or []
        for option in options:
            if isinstance(option, dict) and option.get("id") == value:
                return tr(option["label"], lang)
        if column["id"] == "material" and value in UNIT_WEIGHT_NAMES:
            return UNIT_WEIGHT_NAMES[value][lang]
    return value


def cell(value, column, lang):
    printed = cell_text(value, column, lang)
    if isinstance(printed, bool) or printed is None:
        raise ValueError(f"cell {column['id']}: {value!r}")
    if isinstance(printed, (int, float)):
        return number(printed)
    if printed == "":
        return "[]"
    if column.get("type") == "math":
        return content(f"${printed}$")
    return content(printed)


def wide_column(block, hidden):
    """The column that takes the width left over, or None: a key-value table's value; in a table with a heading row, the one text column whose cells run long, and only where every other text column is short -- a `wide` column gets what the others leave it, so beside a column of middling words it is squeezed below its own longest word. Where no column is so clearly the long one, none is wide and Typst shares the width out itself."""
    columns = [c for c in block["columns"] if c["id"] not in hidden]
    if block.get("header") is False:
        return columns[-1]["id"]
    cells, natural = {}, {}
    for column in columns:
        if column.get("type") not in ("text", "choice"):
            continue
        longest = 0
        for row in block["rows"]:
            if column["id"] in row:
                for lang in LANGS:
                    printed = cell_text(row[column["id"]], column, lang)
                    if isinstance(printed, str):
                        longest = max(longest, len(printed))
        cells[column["id"]] = longest
        natural[column["id"]] = max([longest] + [len(tr(column["title"], lang)) for lang in LANGS])
    long = [cid for cid, n in cells.items() if n >= 30]
    if len(long) == 1 and all(natural[cid] < 20 for cid in natural if cid != long[0]):
        return long[0]
    return None


def rows_of(block, lang, columns, auto=()):
    rows = []
    for row in block["rows"]:
        pairs = []
        for column in columns:
            key = column["id"]
            if key in auto:
                pairs.append((key, "auto"))
            elif key in row:
                if column.get("type") == "category":
                    pairs.append((key, string(row[key])))
                else:
                    pairs.append((key, cell(row[key], column, lang)))
        rows.append(inline_dict(pairs))
    return rows


def caption_and_notes(block, lang):
    out = []
    if block.get("caption"):
        out.append(("caption", content(tr(block["caption"], lang))))
    if block.get("notes"):
        out.append(("notes", [content(tr(note, lang)) for note in block["notes"]]))
    return out


def table(block, lang):
    if block["id"] == "live-loads-table":
        return live_loads(block, lang)
    if block["id"] == "superimposed-table":
        return superimposed(block, lang)
    hidden = [c["id"] for c in block["columns"] if c.get("optional")]
    wide = wide_column(block, hidden)
    columns = []
    for column in block["columns"]:
        pairs = [("id", string(column["id"])), ("title", heading(column, lang))]
        if column.get("unit"):
            pairs.append(("unit", string(column["unit"])))
        kind = "wide" if column["id"] == wide else KIND.get(column.get("type"), "text")
        if kind != "text":
            pairs.append(("kind", string(kind)))
        columns.append(inline_dict(pairs))
    arguments = [("columns", columns), ("hidden", inline_array([string(h) for h in hidden])),
                 ("rows", rows_of(block, lang, block["columns"]))]
    arguments += caption_and_notes(block, lang)
    if block.get("header") is False:
        arguments.append(("header", "false"))
    return tagged("doc-table", block["id"], arguments)


def live_loads(block, lang):
    """The live loads (SIA 261 Tabelle 8): the six columns the command knows by id, headed in the report's language by the engine; the category a row's own, q_k and Q_k `auto` -- read from the export, so they follow the norm table. **No ψ column**: the Reduktionsbeiwerte are never shown for live loads."""
    ids = [c["id"] for c in block["columns"]]
    assert ids == ["zone", "storey", "use", "category", "q_k", "Q_k"], ids
    hidden = [c["id"] for c in block["columns"] if c.get("optional")]
    arguments = [("columns", [inline_dict([("id", string(i))]) for i in ids]),
                 ("hidden", inline_array([string(h) for h in hidden])),
                 ("rows", rows_of(block, lang, block["columns"], auto=("q_k", "Q_k")))]
    arguments += caption_and_notes(block, lang)
    return tagged("live-load-table", block["id"], arguments)


def superimposed(block, lang):
    """The non-structural self-weight: the four columns the command knows by id, the load column the one a value of the Variables tab goes into."""
    ids = [c["id"] for c in block["columns"]]
    assert ids == ["zone", "storey", "buildup", "load"], ids
    arguments = [("columns", [inline_dict([("id", string(i))]) for i in ids]), ("hidden", "()"),
                 ("rows", rows_of(block, lang, block["columns"]))]
    arguments += caption_and_notes(block, lang)
    return tagged("dead-load-table", block["id"], arguments)


def checklist(block, lang):
    options = []
    for option in block["options"]:
        pairs = [("id", string(option["id"])), ("label", content(tr(option["label"], lang))),
                 ("checked", "true" if option.get("checked_default") else "false")]
        if option.get("text"):
            pairs.append(("text", content(tr(option["text"], lang))))
        options.append(inline_dict(pairs))
    arguments = [("label", content(tr(block["label"], lang))), ("options", options)]
    if block.get("prints_option_text"):
        # a list whose point is what was chosen, each ticked option printed with the paragraph that explains it
        arguments.append(("only-checked", "true"))
    return tagged("doc-checklist", block["id"], arguments)


def choice(block, lang):
    options = [inline_dict([("id", string(o["id"])), ("label", content(tr(o["label"], lang)))]) for o in block["options"]]
    selected = block.get("default")
    arguments = [("label", content(tr(block["label"], lang))), ("options", options),
                 ("selected", string(selected) if selected else "none")]
    return tagged("doc-choice", block["id"], arguments)


def image(block, lang):
    arguments = [("file", "none"), ("caption", content(tr(block["caption"], lang)))]
    if block.get("placeholder"):
        arguments.append(("placeholder", content(tr(block["placeholder"], lang))))
    return tagged("doc-image", block["id"], arguments)


def norms(block, lang):
    keys = [string(k) for k in block["default_keys"]] + [content(tr(line, lang)) for line in block.get("lines", ())]
    return tagged("show-norm-list", block["id"], [("keys", keys)])


def signatures(block, lang):
    rows = []
    for group in block["groups"]:
        for signer in group["signers"]:
            if signer.get("default"):
                rows.append(inline_dict([("group", content(tr(group["title"], lang))), ("role", content(tr(signer["role"], lang)))]))
    return tagged("doc-signatures", block["id"], [("rows", rows), ("place-date", "true" if block.get("place_date", True) else "false")])


RENDER = {"table": table, "checklist": checklist, "choice": choice, "image": image, "norms": norms, "signatures": signatures}


def section_text(node, lang, shared):
    """The whole file of the lowest-level section `node` in `lang`."""
    body = [f"= {tr(node['title'], lang)}"]
    for block in node["content"]:
        if block["kind"] == "text":
            body.append(tr(block["text"], lang).rstrip("\n"))
        else:
            body.append("\n".join(RENDER[block["kind"]](block, lang)))
    text = "\n\n".join(body)
    if shared:
        text = f"// woodcore:shared {node['id']}\n{text}\n// woodcore:/shared {node['id']}"
    return tag(f"{IMPORT}\n\n{text}\n")


def journal_text(lang):
    return tag(f"{IMPORT}\n\n= {JOURNAL[lang]}\n\n#show-journal()\n")


def tag(text):
    """`text` with its headings and paragraphs wrapped in object tags (`typst_objects.tag_file`, the ids the templates carry) -- and checked: nothing is left untagged but code and comments, a second run changes nothing, and every object is canonical."""
    tagged = typst_objects.tag_file(text, ids="plain")
    assert typst_objects.untagged(tagged) == [], "a heading or a paragraph is left outside every object tag"
    assert typst_objects.tag_file(tagged, ids="plain") == tagged, "tagging a tagged file changed it"
    for obj in typst_objects.objects(tagged):
        assert obj.state == "canonical", (obj.type, obj.id, obj.error)
    return tagged


# --- a mode --------------------------------------------------------------------------------------

def structure_of(mode, nodes):
    def out(node):
        if "children" in node:
            # a group whose every section is off by default is off too, or the document would print its heading over nothing (the annexes of the convention d'utilisation)
            on = bool(node.get("enabled_default", True)) and any(leaf.get("enabled_default", True) for leaf in walk(node["children"]) if "children" not in leaf)
            return {"id": node["id"], "title": {lang: node["title"][lang] for lang in LANGS}, "enabled": on,
                    "children": [out(child) for child in node["children"]]}
        leaf = {"id": node["id"], "file": structure.section_file(node["id"]), "enabled": bool(node.get("enabled_default", True))}
        if OTHER[mode] in node.get("shared", ()):
            leaf["shared_with"] = [OTHER[mode]]
        return leaf
    source = structure.blank(mode)
    source["sections"] = [out(node) for node in nodes] + [{"id": "journal", "file": structure.section_file("journal"), "enabled": True}]
    return structure.check_source(source)


def files_of(mode, nodes, lang):
    files = {}
    for node in walk(nodes):
        if "children" in node:
            continue
        files[structure.section_file(node["id"])] = section_text(node, lang, OTHER[mode] in node.get("shared", ()))
    files[structure.section_file("journal")] = journal_text(lang)
    return files


def _write(path, text):
    """Writes `text` (LF) where it differs from what is there, beside itself and moved into place. Returns whether it wrote."""
    data = text.encode("utf-8")
    if path.is_file() and path.read_bytes() == data:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".part")
    temporary.write_bytes(data)
    os.replace(temporary, path)
    return True


def template_meta(mode, source):
    leaves = [n for n, _d in structure.leaves(source)]
    groups = [n for n, _d, _p in structure.walk(source) if "children" in n]
    on = sum(1 for n in leaves if n.get("enabled", True))
    shared = sum(1 for n in leaves if n.get("shared_with"))
    n, g = len(leaves), len(groups)
    if mode == "cu":
        name = T("Convention d'utilisation — standard", "Nutzungsvereinbarung — Standard", "Service criteria agreement — standard")
        description = T(
            f"Convention d'utilisation complète selon SIA 260{NNBSP}: {g} chapitres et {n} sections, dont {on} imprimées par défaut, des objectifs d'utilisation aux signatures. Les charges utiles et {shared - 1} autres sections sont partagées avec la base de projet.",
            f"Vollständige Nutzungsvereinbarung nach SIA 260: {g} Kapitel und {n} Abschnitte, davon {on} standardmässig gedruckt, von den Nutzungszielen bis zu den Unterschriften. Die Nutzlasten und {shared - 1} weitere Abschnitte sind mit der Projektbasis geteilt.",
            f"Complete service criteria agreement in accordance with SIA 260: {g} chapters and {n} sections, {on} of them printed by default, from the use objectives to the signatures. The live loads and {shared - 1} other sections are shared with the basis of design.")
    else:
        name = T("Base de projet — standard", "Projektbasis — Standard", "Basis of design — standard")
        description = T(
            f"Base de projet complète selon SIA 260{NNBSP}: {g} chapitres et {n} sections, dont {on} imprimées par défaut, du concept structural à la protection contre le bruit. Les charges utiles et {shared - 1} autres sections sont partagées avec la convention d'utilisation.",
            f"Vollständige Projektbasis nach SIA 260: {g} Kapitel und {n} Abschnitte, davon {on} standardmässig gedruckt, vom Tragwerkskonzept bis zum Schallschutz. Die Nutzlasten und {shared - 1} weitere Abschnitte sind mit der Nutzungsvereinbarung geteilt.",
            f"Complete basis of design in accordance with SIA 260: {g} chapters and {n} sections, {on} of them printed by default, from the structural concept to noise protection. The live loads and {shared - 1} other sections are shared with the service criteria agreement.")
    meta = {"schema_version": "1.0", "format": "woodcore-document-template", "mode": mode, "name": name,
            "description": description, "languages": list(LANGS)}
    return json.dumps(meta, ensure_ascii=False, indent=2) + "\n"


def build(catalogue, dry_run=False, log=print):
    cat = amend(catalogue)
    written = removed = 0
    for mode in MODES:
        nodes = cat["modes"][mode]["sections"]
        source = structure_of(mode, nodes)
        folder = TEMPLATES / mode / FOLDER
        for lang in LANGS:
            where = folder / lang
            entries = sorted(where.glob("*.typ"))
            if len(entries) != 1:
                raise SystemExit(f"{where}: expected exactly one entry .typ to keep, found {[p.name for p in entries]}")
            files = files_of(mode, nodes, lang)
            if dry_run:
                log(f"{mode}/{lang}: {len(files)} section files")
                continue
            for rel, text in files.items():
                written += _write(where / rel, text)
            for path in sorted((where / structure.SECTIONS_DIR).glob("*.typ")):
                if f"{structure.SECTIONS_DIR}/{path.name}" not in files:
                    path.unlink()
                    removed += 1
            before = (where / structure.FILE).read_bytes() if (where / structure.FILE).is_file() else None
            structure.write(where / structure.FILE, source)
            written += before != (where / structure.FILE).read_bytes()
            written += structure.sync_entry(entries[0], where / structure.FILE, lang)
            # The headings at the level they print at, each chapter a file of its own (the engineer's request of 06.10.2026): the catalogue writes every section's heading as `=`, and the document is converted once it is written -- so that a rerun gives the same bytes.
            structure.make_absolute_folder(where, lang)
        if not dry_run:
            written += _write(folder / "template.json", template_meta(mode, source))
    log(f"document templates: {written} files written, {removed} removed")
    return cat


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("catalogue", help="the section catalogue, a JSON file the maintainers keep (not shipped)")
    parser.add_argument("--dry-run", action="store_true", help="build everything in memory and write nothing")
    args = parser.parse_args(argv)
    with open(args.catalogue, encoding="utf-8") as handle:
        catalogue = json.load(handle)
    build(catalogue, dry_run=args.dry_run)
    return 0


if __name__ == "__main__":
    sys.exit(main())
