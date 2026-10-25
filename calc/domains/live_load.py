"""Live loads (Nutzlasten), read from Tabelle 8 of SIA 261 (docs/domain/loads.md §3.3septies).

A live load is not calculated and not entered: it is *looked up*, by the category of Nutzfläche the surface belongs to -- A1 Wohnflächen, A3 Treppen, B Büroflächen, ... H nicht begehbare Dächer -- and the norm's own table gives the two characteristic values, the Flächenlast q_k and the Einzellast Q_k. So the instances of this domain are the rows of that table, one per category, and the report addresses one by its category: `show-live-load("A1")`.

Which makes this domain's `ENGINE` not `python` but **`norm`**: nothing here computes a value. The numbers come from `calc/norms/sia261-2020-tab08-nutzlasten.json`, read through `norms/sia261.py`, the one place in the project they are written down (docs/architecture/layout.md §11), and every var's `source` says so, with the edition they belong to: `norm:SIA 261:2020, Tabelle 8`.

Two things the table itself decides, and this module only carries:

* **The footnotes.** A value of Tabelle 8 is not the whole story -- the Einzellast of category A is not combined with the Flächenlast, while on a Parkfläche the two act at once -- so each value takes its row's footnotes as its `description`, which the report sets as a footnote on the value from level 2.
* **Category E has no values.** SIA 261 8.2.2 leaves Lager- und Fabrikationsflächen to the project. Its instance therefore carries no `q_k` and no `Q_k` at all, only the note saying what has to be fixed and where; the report refuses to print it (`show-live-load`) rather than inventing a number.

Every instance also carries Tabelle 8 entire as its one `table`, shown at level 3 with that instance's own row highlighted -- the checker reads the value in the table it came from.

**No Reduktionsbeiwerte ψ0, ψ1, ψ2 here** (the engineer, 01.10.2026: ψ is never shown for live loads). SIA 260 Tabelle 2 stays transcribed in `calc/norms/sia260-2013-tab02-reduktionsbeiwerte.json`, read by `norms/sia260.py`, for the load combinations (section 3.5), which read it where the category they scale is known; an instance of this domain carries the load of its category and nothing else, and so does no live-load table of a document.
"""

import engine
from norms import sia261

DOMAIN = "live-load"
LABEL = "Nutzlasten"
# Neither entered nor calculated here: read from a norm table (docs/domain/calculation-domains.md §3.3).
ENGINE = "norm"
ACTION = "variable"  # SIA 260: a variable action (Q) -- SIA 261 8.1.1 calls the Nutzlasten free variable actions
NORM = "SIA 261"
# Tabelle 8 holds the characteristic values (8.2.1); the categorisation of the Nutzflächen is 8.1.2, and the values a project must fix itself 8.2.2.
NORM_REF_VALUES = "8.2.1"
NORM_REF_CATEGORY = "8.1.2"
NORM_REF_PROJECT = "8.2.2"

# The group that puts a category and its two values on one row where the generic show-calc renders this domain (docs/domain/calculation-domains.md §3.3); show-live-load lays the same line out itself.
GROUP = "nutzlast"


def _source():
    """Where every value of this domain comes from, edition included (docs/project/purpose.md §1bis): `norm:SIA 261:2020, Tabelle 8`."""
    table = sia261.table_8()
    return f"norm:{sia261.edition()}, Tabelle {table['number']}"


def _notes(refs):
    """The footnotes `refs` names, as one prose note -- what a value carries as its `description`."""
    texts = sia261.note_texts(refs)
    return " ".join(texts) if texts else None


def _marks(refs):
    """The footnote references of a cell, as the norm sets them: "1)", "3) 4)"."""
    return " ".join(f"{ref})" for ref in refs)


def _cell(value, refs):
    """One value of Tabelle 8 as Typst math source: the number with its footnote references in superscript.

    Where the norm gives no value (category E), the cell carries the references alone, on an empty base -- which is how the norm's own row reads. A dash in their place is set in the math font, low against the raised references, and comes out looking like a rule.
    """
    text = "\"\"" if value is None else f"{value:g}"
    marks = _marks(refs)
    return f"{text}^\"{marks}\"" if marks else text


def _table(highlight):
    """Tabelle 8 entire, with row `highlight` marked -- the same table for every instance but for that one index.

    It is the *working* behind the two values, so it keeps the default place, above them, and it is shown at level 3: a client report quotes the load, a checking report reads it off the norm's own table (docs/domain/calculation-domains.md §3.3).

    The values are plain `math` cells rather than `value` cells naming this instance's vars: eleven of the twelve rows belong to other categories, and a `value` cell would also take q_k and Q_k off their own rows in the generic show-calc.
    """
    table = sia261.table_8()
    notes = table["notes"]
    rows = []
    for row in table["categories"]:
        art = row["nutzflaeche"]
        if row["notes_category"]:
            art += " " + _marks(row["notes_category"])
        rows.append([
            row["id"],
            art,
            row["beispiel"],
            _cell(row["q_k"], row["notes_q"]),
            _cell(row["Q_k"], row["notes_Q"]),
        ])
    return {
        "title": f"Tabelle {table['number']}: {table['title']} ({sia261.edition()})",
        "level": 3,
        "place": "above",
        "source": _source(),
        "highlight": [highlight],
        "note": " ".join(f"{ref}) {notes[ref]}" for ref in sorted(notes)),
        "columns": [
            {"label": "Kategorie", "kind": "text"},
            {"label": "Art der Nutzfläche", "kind": "wide"},
            {"label": "Beispiel", "kind": "wide"},
            {"label": "qk", "label_math": "q_k", "kind": "math",
             "unit": table["units"]["q_k"]},
            {"label": "Qk", "label_math": "Q_k", "kind": "math",
             "unit": table["units"]["Q_k"]},
        ],
        "rows": rows,
    }


def _instance(row, index):
    """One category of Tabelle 8 as one instance of this domain: the {results, tables, vars, steps, checks} shape every calculation instance has (docs/domain/calculation-domains.md §3.3)."""
    table = sia261.table_8()
    source = _source()
    calc = engine.Calculation()

    def add(name, value, symbol, unit, label, norm_ref, description=None,
            source=source, norm=NORM, group=GROUP, group_label=None):
        calc.add_var(
            name=name, value=value, unit=unit, symbol=symbol, label=label,
            source=source, norm=norm, norm_ref=norm_ref,
            description=description, group=group, group_label=group_label,
        )

    # The order is the order the report prints them (docs/typst/api-conventions.md §10bis), and the levels are the split: the category and its two values from level 1, what the category *is* from level 2.
    add("kategorie", row["id"], "\"Kategorie\"", "", "Nutzungskategorie",
        NORM_REF_CATEGORY, description=_notes(row["notes_category"]))
    add("nutzflaeche", row["nutzflaeche"], "\"Nutzfläche\"", "",
        "Art der Nutzfläche", NORM_REF_CATEGORY)
    # Not every category has an example in the norm (Büroflächen has none): a var with nothing in it would print an empty value rather than say nothing.
    if row["beispiel"]:
        add("beispiel", row["beispiel"], "\"Beispiel\"", "", "Beispiel",
            NORM_REF_CATEGORY)

    if row["q_k"] is None:
        # Category E: the norm gives no value, so this instance carries none either. What it carries instead is the sentence saying so, which is what the report refuses with.
        add("hinweis", _notes([table["project_specific_note"]]), "\"Nutzlast\"",
            "", "Nutzlast", NORM_REF_PROJECT)
        results = ["hinweis"]
    else:
        add("q_k", row["q_k"], "q_k", table["units"]["q_k"], "Flächenlast",
            NORM_REF_VALUES, description=_notes(row["notes_q"]))
        add("Q_k", row["Q_k"], "Q_k", table["units"]["Q_k"], "Einzellast",
            NORM_REF_VALUES, description=_notes(row["notes_Q"]))
        results = ["q_k", "Q_k"]

    return {"results": results, "tables": [_table(index)], **calc.to_dict()}


def build_instances():
    """Every category of Tabelle 8, in the norm's own order, keyed by its id -- what the registry asks of a domain read from a norm table, in place of a source module's cases (registry.py)."""
    table = sia261.table_8()
    return {
        row["id"]: _instance(row, index)
        for index, row in enumerate(table["categories"])
    }
