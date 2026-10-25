"""What a domain of calc/domains/ offers the rest of Woodcore, written down (spec docs/requirements/active/2026-10-19-base-saine-nettoyage.md, C5).

A domain is a module, not a class: the window, `export_all` and the tests call its functions by name. Two shapes recur, and each is a `typing.Protocol` here -- documentation a type checker reads, and what tests/test_domain_contracts.py holds every domain to, in a table where a new domain takes its row:

* **a source domain** reads the engineer's files of one folder (`connectors/`, `plans/`, `details/`…): `read_source(path)` gives a source checked, `check_source(src, where)` refuses a malformed one naming the file and the field, `SOURCE_SCHEMA_VERSION` is the version a new source is written at;
* **an export domain** writes one file of `data/` for the report: `prepare(...)` builds it in memory and writes nothing, so a failed export leaves `data/` as it was; `write(...)` is its only writer; `export(...)` is the two, run by the window when a source is saved; `EXPORT_SCHEMA_VERSION` is the version of the plainest export it writes.

* **a calculation tab's domain** (spec 2026-10-22-onglet-neige-type, ARCH-002) describes the form a calculation tab draws for it, and says what the tab shows beside it, so that a tab is described and never copied: `declaration()` -- its sections and fields (`Declaration`, `Field`, `Choice`), the norm file its excerpts are read from --, `visible_fields(src)`, `messages(src)` -- what blocks the calculation and what is only said (`Message`) --, `results(instance)` -- the values computed, never an input. A drawing (`figure_svg`, `tile_svg`), a chart (`chart`) and the dependencies no step of its instance records (`extra_dependencies(instance)`, {result: [names]}, read by calc/domains/dependencies.py) are optional: calc/tools/calc_tab.py asks for them where they are. The snow is the first (`snow_source`); tests/test_calc_tab_base.py holds the base to an invented one.

The arguments differ from one domain to another -- what an export needs (the positions, the values of the variables, where its figures go) is the domain's -- so a protocol names the functions and not their signatures. Qt-free, importing nothing of the domains.
"""

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable


@runtime_checkable
class SourceDomain(Protocol):
    """A domain that reads the engineer's source files of one folder."""

    SOURCE_SCHEMA_VERSION: str

    def read_source(self, path): ...

    def check_source(self, src, where): ...


@runtime_checkable
class ExportDomain(Protocol):
    """A domain that writes one file of `data/` for the report."""

    EXPORT_SCHEMA_VERSION: str

    def prepare(self, *args, **kwargs): ...

    def write(self, *args, **kwargs): ...

    def export(self, *args, **kwargs): ...


# --- a calculation tab's domain (spec 2026-10-22-onglet-neige-type, ARCH-002) ---------------------------------------

# What a message is: an error blocks the calculation (red), an info is said beside a calculation made (orange); a warning is a value the engineer replaced or a layer that asks a look (orange, spec 2026-10-24-poids-propre-repense, REQ-007), an ok that every layer has its weight (green). A check's verdict will be another, when the member checks join (§13 of the spec).
SEVERITIES = ("error", "info", "warning", "ok")
# The kinds of field the declared form draws: a number with its unit; buttons that say what they are worth, a free value beside them where `free` names its key; tiles, each a drawing; a check box; a drop-down list. A form that is not declared (the layers of a permanent load) is a service of its tab's own in place of the declared form, no kind of field (spec 2026-10-23-onglets-types-et-services, ARCH-006).
FIELD_KINDS = ("number", "buttons", "tiles", "checkbox", "select")
# What a section holds besides its fields (spec 2026-10-23-onglet-vent-briques, ARCH-003, ARCH-RISK-001): a text; a drawing (svg); a table of numbers coloured by their value (heat_table); a formula; a 3D model (model3d, brought by calc/domains/model3d.py); a field of kind select set on the line of a text (row_select); an excerpt of a norm, its words and its image (excerpt: a figure of the norm in a section, the wind's building); several blocks shown one at a time under a segmented button (views: the wind's «Norme / Modèle 3D», D-35). Their data come from the domain's `blocks(src, instance)`, their widgets from calc/tools/calc_blocks.py
BLOCK_KINDS = ("text", "svg", "heat_table", "formula", "model3d", "row_select", "excerpt", "views")


@dataclass(frozen=True)
class Message:
    """One thing the domain says of a source: its code -- the tab's words are `<prefix>msg_<code>` --, the field it is about (None for the source as a whole), its severity (`SEVERITIES`) and the values its words are filled with."""
    code: str
    field: object
    severity: str
    params: dict = field(default_factory=dict)


@dataclass(frozen=True)
class Choice:
    """One choice of a `buttons`, `tiles` or `select` field: the value written into the source, the words that name it -- a glossary term, or a word of the tab where it begins with the declaration's prefix (`sn_c_…`, a button's short word); None: the base writes `value` and the field's unit --, the number it stands for (C_e's 1.2) and the excerpts its bubble shows."""
    id: object
    word: object = None
    value: object = None
    excerpts: tuple = ()


@dataclass(frozen=True)
class Field:
    """One datum of the form: the source's key, its kind (`FIELD_KINDS`), its unit, its choices, the excerpts of the norm its ⓘ shows, a number's range, decimals and step, whether it may follow a variable of the export (the domain's `LINKABLE`), and for buttons with a free value the id that means «free» and the key the free number is written under (C_e: `custom`, `c_e`); `var`, the variable of the instance it fills (`correction` fills `korrektur`), what the tab lights up with the results computed from it (spec 2026-10-23-neige-correctifs-issues-96-99, UI-004)."""
    key: str
    kind: str
    unit: str = ""
    choices: tuple = ()
    excerpts: tuple = ()
    minimum: float = 0.0
    maximum: float = 1e6
    decimals: int = 2
    step: float = 1.0
    linkable: bool = False
    free_id: object = None
    free_key: str = ""
    var: str = ""
    special_word: str = ""
    block: bool = False       # the source writes the number as a {value, unit} block, its unit the field's (a member check's forces and moments, issue #112)
    zero_none: bool = False   # 0 is written as null: no moment, no shear force, no length stated (issue #112)


@dataclass(frozen=True)
class Block:
    """What a section holds that is no field (`BLOCK_KINDS`, ARCH-003): its `key` -- what the section names it by, and what the domain's `blocks(src, instance)` gives its data under --, its `kind`, the field a `row_select` sets on its line (`field`, a select declared among the fields), whether it may be pinned into the right pane as a module of its own (`pinnable`) and whether it takes the section's whole width with a horizontal scroll below `min_width` pixels (`wide`), and for a `views` the blocks it shows one at a time (`children`, declared among the blocks and placed in no section, D-35)."""
    key: str
    kind: str
    field: str = ""
    pinnable: bool = False
    wide: bool = False
    min_width: int = 0
    children: tuple = ()


@dataclass(frozen=True)
class Declaration:
    """A calculation tab's form: the prefix of the tab's words (`sn_`: `sn_s_<section>`, `sn_f_<key>`, `sn_msg_<code>`), the norm file its excerpts are read from (calc/norms/excerpts.py), its sections in order, each (id, keys) -- a key a field's or a block's, a tuple of field keys the fields of one line (b · d · h, ARCH-RISK-014) --, its fields, its blocks, and what the right pane shows of them (`modules`, D-34): each (id, block keys), «results» the blocks under the values of «Résultats» in place of the instance's tables, another id a module of its own, titled `<prefix>m_<id>`; empty, the pane is the type's."""
    prefix: str
    norm: str
    sections: tuple
    fields: tuple
    blocks: tuple = ()
    modules: tuple = ()

    def field(self, key):
        return next(f for f in self.fields if f.key == key)

    def block(self, key):
        return next((b for b in self.blocks if b.key == key), None)

    def section_keys(self, keys):
        """The field and block keys of a section's entries, a line's fields one by one."""
        return [k for entry in keys for k in (entry if isinstance(entry, tuple) else (entry,))]


@dataclass(frozen=True)
class Layer:
    """One layer of a build-up as a drawing reads it (spec 2026-10-23-onglets-types-et-services, ARCH-007; spec 2026-10-24-poids-propre-repense, ARCH-003): its stable `id` (its rank from the top, "1"…, also its `number` in the drawing's legend), its `kind` (g_k or a_k), its `pose` (dead_load_layers.POSES), its `thickness`, `width` and `spacing` in mm -- `width` and `spacing` None but for a spaced layer --, whether it is `link`ed to the one below (the two share a level: the pieces and what fills between them), the width it fills on 1 m (`fill_width`, mm, None for a spaced or typed layer) and the air above it (`air`, mm), its `role` (dead_load_layers.ROLES, or None), and the words that name it (`label`, `ebene`). Neither a hatch nor whether it is shown, a state of the screen and never of the case (D-16). A domain gives them through `layers(src, here)`, Qt-free; a service that draws them asks it by `NEEDS = ("layers",)`."""
    id: str
    kind: str
    thickness: object
    width: object = None
    spacing: object = None
    link: bool = False
    label: str = ""
    ebene: str = ""
    pose: str = "continuous"
    fill_width: object = None
    air: float = 0.0
    role: object = None
    number: int = 0


# --- a table of an instance (`instance["tables"]`), read by the domain's file (domains/unfold.py `_table_lines`) and by the window (tools/calc_modules.py `tables_html`) alike ---

# How a table's columns share its width (spec 2026-10-23-onglet-vent-briques, REQ-014): "first-auto", the first column as wide as it needs and the others sharing the rest -- a wide, low table, `columns: (auto,) + (1fr,) * n`; absent, one column each as wide as it needs
TABLE_WIDTHS = ("first-auto",)


def table_cell(value, column, vars_):
    """What a cell of an instance's table shows (spec 2026-10-23-onglet-vent-briques, T127, ARCH-RISK-009): a cell of a `value` column naming a variable of the instance its value -- never its name --, a number rounded to the column's `decimals` where it gives them, any other cell as it is. One rule, written once, for the file and the window."""
    if column.get("kind") == "value" and isinstance(value, str) and value in vars_:
        value = vars_[value]["value"]
    if column.get("decimals") is not None and isinstance(value, (int, float)) and not isinstance(value, bool):
        value = round(value, column["decimals"])
    return value


@runtime_checkable
class CalcTabDomain(Protocol):
    """A domain a calculation tab is built on (calc/tools/calc_tab.py): described, never copied."""

    def declaration(self): ...

    def visible_fields(self, src): ...

    def messages(self, src): ...

    def results(self, instance): ...
