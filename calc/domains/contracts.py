"""What a domain of calc/domains/ offers the rest of Woodcore, written down (spec docs/requirements/active/2026-10-19-base-saine-nettoyage.md, C5).

A domain is a module, not a class: the window, `export_all` and the tests call its functions by name. Two shapes recur, and each is a `typing.Protocol` here -- documentation a type checker reads, and what tests/test_domain_contracts.py holds every domain to, in a table where a new domain takes its row:

* **a source domain** reads the engineer's files of one folder (`connectors/`, `plans/`, `details/`…): `read_source(path)` gives a source checked, `check_source(src, where)` refuses a malformed one naming the file and the field, `SOURCE_SCHEMA_VERSION` is the version a new source is written at;
* **an export domain** writes one file of `data/` for the report: `prepare(...)` builds it in memory and writes nothing, so a failed export leaves `data/` as it was; `write(...)` is its only writer; `export(...)` is the two, run by the window when a source is saved; `EXPORT_SCHEMA_VERSION` is the version of the plainest export it writes.

* **a calculation tab's domain** (spec 2026-10-22-onglet-neige-type, ARCH-002) describes the form a calculation tab draws for it, and says what the tab shows beside it, so that a tab is described and never copied: `declaration()` -- its sections and fields (`Declaration`, `Field`, `Choice`), the norm file its excerpts are read from --, `visible_fields(src)`, `messages(src)` -- what blocks the calculation and what is only said (`Message`) --, `results(instance)` -- the values computed, never an input. A drawing (`figure_svg`, `tile_svg`) and a chart (`chart`) are optional: calc/tools/calc_tab.py asks for them where they are. The snow is the first (`snow_source`); tests/test_calc_tab_base.py holds the base to an invented one.

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

# What a message is: an error blocks the calculation (red), an info is said beside a calculation made (orange). A check's verdict will be a third, when the member checks join (§13 of the spec).
SEVERITIES = ("error", "info")
# The kinds of field the base draws: a number with its unit; buttons that say what they are worth, a free value beside them where `free` names its key; tiles, each a drawing; a check box; a drop-down list; a widget the tab builds itself.
FIELD_KINDS = ("number", "buttons", "tiles", "checkbox", "select", "custom")


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
    """One datum of the form: the source's key, its kind (`FIELD_KINDS`), its unit, its choices, the excerpts of the norm its ⓘ shows, a number's range, decimals and step, whether it may follow a variable of the export (the domain's `LINKABLE`), and for buttons with a free value the id that means «free» and the key the free number is written under (C_e: `custom`, `c_e`)."""
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


@dataclass(frozen=True)
class Declaration:
    """A calculation tab's form: the prefix of the tab's words (`sn_`: `sn_s_<section>`, `sn_f_<key>`, `sn_msg_<code>`), the norm file its excerpts are read from (calc/norms/excerpts.py), its sections in order, each (id, field keys), and its fields."""
    prefix: str
    norm: str
    sections: tuple
    fields: tuple

    def field(self, key):
        return next(f for f in self.fields if f.key == key)


@runtime_checkable
class CalcTabDomain(Protocol):
    """A domain a calculation tab is built on (calc/tools/calc_tab.py): described, never copied."""

    def declaration(self): ...

    def visible_fields(self, src): ...

    def messages(self, src): ...

    def results(self, instance): ...
