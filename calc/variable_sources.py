"""Every variable of a project, from wherever it comes, as the Variables tab lists it (docs/ui/window.md §10quater, spec 2026-10-08-onglet-variables-trois-colonnes).

The engineer's issue 13: «Présenter toutes les variables, avec leur provenance affichée. Elles viennent de trois
sources : les Excel, Woodcore (charges, connecteurs, moments polaires, etc.) et l'export JSON des variables
calculées dans Typst.» The Typst registries are `calc/variables.py`'s, which reads them out of each document's
PDF or a compile; this module adds what the export wrote -- the four files of `data/` that carry `vars` -- and
says, for each variable, where it comes from.

⚠️ **It reads and never writes**, like `calc/variables.py`: everything here was written and validated by the
export, and is read again from disk each time the tab asks, so a polar moment saved a moment ago is listed
beside a load read at startup without the two having drifted apart (D-014). Nothing is cached: the four files
together are some tens of kilobytes.

⚠️ **Provenance is decided here and stored nowhere** (D-012): a variable read from a document's registry is
Typst's whatever its `source` says -- `#var("s_k", domain: ("snow-load", "SL"))` copies an export's var into the
registry, `excel:` source and all --, and every other one is what its `source` prefix says
(`variables.PROVENANCE`).

No Qt: the tab shows what this returns and decides nothing of it.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path

import project
import validation
import variables as model
from domains import connection, connector, formula_domain, links, script

# Where a domain was read: the export (data/), or one of the documents' registries, named by its mode ("cu", "bp", "rs").
EXPORT = "export"

# The export's calculations. Not a constant of any module yet -- export_all.py and half a dozen readers spell it out -- so it is written once here for this module's own two uses.
CALCULATIONS_FILE = "calculations.json"


@dataclass
class Domain:
    """One domain the tab lists: its variables, where it was read, and what the loads tab used to show beside them.

    `name` is what the tab shows and what a document's registry keys it by; `origin` is EXPORT or a document's mode,
    and (origin, name) is a domain's identity -- the same polar moment is `connection · VU-MP-1` in the export and
    `VU-MP-1` in a registry, and «Rapport» exists once per document. `address` is the pair a call names an export's
    calculation by (`#val("s_k", domain: ("snow-load", "SL"))`), None for a registry's domain.
    """

    name: str
    origin: str
    variables: list = field(default_factory=list)
    kind: str = "named"            # "export", or what variables.domain_kind says of a registry's domain
    address: tuple = None          # (calculation, instance) of an export's domain
    label: str = ""                # the calculation's own label, «Schneelast»
    results: tuple = ()            # the keys the calculation declares as its results
    checks: tuple = ()             # the names of its checks, one show-check each
    workbook: str = ""             # the workbook an instance was read from, relative to the project
    sheet: str = ""
    formulas: dict = field(default_factory=dict)   # result key -> the formula of the step that computes it
    file: str = ""                 # the file of data/ it was read from, "" for a registry's domain

    @property
    def calculation(self):
        return self.address[0] if self.address else None

    def variable(self, key):
        return next((var for var in self.variables if var.key == key), None)


def instance_workbook(domain, instance):
    """The workbook an instance was read from: carried per instance since a domain's sheets may come from several workbooks, per domain before that. Moved from the loads tab (v0.117); the window's staleness check reads it too."""
    return instance.get("workbook") or domain.get("workbook", "")


def _variable(key, name, v):
    return model.Variable(
        key=key, domain=name, value=v.get("value"), unit=v.get("unit") or "",
        symbol=v.get("symbol") or key, label=v.get("label") or "",
        description=v.get("description") or "", norm=v.get("norm") or "",
        norm_ref=v.get("norm_ref") or "", source=v.get("source") or "",
        level=v.get("level"), choices=tuple(v.get("choices") or ()),
    )


def _formulas(record):
    return {step["result"]: step["formula"] for step in record.get("steps") or ()
            if isinstance(step, dict) and step.get("result") and step.get("formula")}


def _domain(name, address, record, label="", workbook="", sheet=""):
    return Domain(
        name=name, origin=EXPORT, kind="export", address=address, label=label,
        variables=[_variable(key, name, v) for key, v in (record.get("vars") or {}).items() if isinstance(v, dict)],
        results=tuple(record.get("results") or ()),
        checks=tuple(c["name"] for c in record.get("checks") or () if isinstance(c, dict) and c.get("name")),
        workbook=workbook, sheet=sheet, formulas=_formulas(record),
    )


def calculation_domains(data):
    """data/calculations.json as domains, one per instance -- `snow-load · SL` -- in the order the export states them, which is the order the loads tab listed them in."""
    out = []
    for calc_id, calc in ((data or {}).get("domains") or {}).items():
        for instance_id, instance in (calc.get("instances") or {}).items():
            out.append(_domain(f"{calc_id} · {instance_id}", (calc_id, instance_id), instance, label=calc.get("label") or "",
                               workbook=instance_workbook(calc, instance), sheet=instance.get("sheet") or ""))
    return out


def _records(root, word):
    """A reader of a file holding {root: {id: {vars, steps, checks, results}}} -- the connections, the connectors, the scripts --, its domains named `<word> · <id>` and addressed (word, id), which is what `find-calculation` reads them by (lib/calc-engine.typ)."""
    def read(data):
        return [_domain(f"{word} · {record_id}", (word, record_id), record, label=record.get("label") or "")
                for record_id, record in ((data or {}).get(root) or {}).items() if isinstance(record, dict)]
    return read


# The files of data/ that carry vars, in the order the tab lists them: (file name, schema it was validated against, reader). One row more is one source more -- the Formules domains of spec 2026-10-08-onglet-formule-domaines will be one. The domains of data/positions/<id>.json are not here: the export writes them empty (D-009 of the spec), and they come in the day it fills them.
FILE_SOURCES = (
    (CALCULATIONS_FILE, "calculations", calculation_domains),
    (connection.EXPORT_FILE, "connections", _records("connections", "connection")),
    (connector.EXPORT_FILE, "connectors", _records("connectors", "connector")),
    (script.EXPORT_FILE, "scripts", _records("scripts", "script")),
    # the calculation domains of the «Formule» tab (v0.117): an index of their files, each computed when read (calc/domains/formula_domain.py), listed under an origin of their own
    (formula_domain.EXPORT_FILE, "formulas", formula_domain.variable_domains),
)


@dataclass
class Export:
    """What one reading of the export found: its domains, the files it did not find, and the files it could not read -- each a `VariablesError` coded `bad_file`, naming the file and what was wrong in it."""

    domains: list = field(default_factory=list)
    missing: list = field(default_factory=list)     # file names
    errors: list = field(default_factory=list)      # variables.VariablesError

    @property
    def count(self):
        return sum(len(domain.variables) for domain in self.domains)


def read_export(here=None):
    """Every domain of the four files, read from disk now. A file not there is a project not exported yet -- `missing`, a word in the tab and never an error --; a file there that is not JSON, or not what its schema says, is a defect of a file Woodcore wrote and is said with its name and the field at fault (`errors`), the other files being read all the same: a broken connectors.json must not hide the loads."""
    here = here or project.current()
    found = Export()
    for name, schema_name, reader in FILE_SOURCES:
        path = here.data_dir / name
        if not path.is_file():
            found.missing.append(name)
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            validation.validate_structure(data, schema_name)
            read = reader(data)
            for domain in read:
                domain.file = name
            found.domains.extend(read)
        except (OSError, ValueError, validation.ValidationError, KeyError, TypeError, AttributeError) as exc:
            # json.JSONDecodeError is a ValueError; ValidationError names the field (`connections.VU-MP-1.vars.I_p: …`)
            found.errors.append(model.VariablesError(f"variables: {path} cannot be read -- {exc}", "bad_file",
                                                     file=name, path=str(path), field=str(exc)))
    return found


def values_of_domains(domains):
    """Domains as the values a link may name (`links.index`'s shape): an export's under its address, a «Formule» domain under its id -- a document's registry never, a link naming only the export (spec 2026-10-11-variables-liees-champs-et-textes, D-02)."""
    out = {}
    for domain in domains:
        records = {var.key: {"value": var.value, "unit": var.unit, "symbol": var.symbol} for var in domain.variables}
        if domain.origin == EXPORT and domain.address:
            out.setdefault(domain.address[0], {})[domain.address[1]] = records
        elif domain.origin == formula_domain.ORIGIN:
            out.setdefault(links.FORMULAS_KEY, {})[domain.name] = records
    return out


def link_of(var, domain):
    """The link a choice of `var` in `domain` would save, or None where no link may name it -- a document's registry (D-02)."""
    return links.from_choice(domain.origin, domain.name, var.key, domain.address if domain.origin == EXPORT else None)


def linkable(var, domain, field_unit=None, consumer=links.ANY):
    """Whether the «Variables» tab offers `var` of `domain` while a field is being linked (REQ-003, UI-003): a number, of the export or a «Formule» domain, of a source the consumer may name (ARCH-005) and -- where the field has a unit, None for a text's variable (D-08) -- of the field's dimension."""
    link = link_of(var, domain)
    if link is None or not var.is_number or not links.allowed(link, consumer):
        return False
    return field_unit is None or links.compatible(var.unit, field_unit)


def export_values(here, calculations, connections=None, connectors=None, scripts=None, formulas=None):
    """The same values, from an export being built in memory -- what export_all resolves the linked fields against, so a field follows the workbooks just read and not the last export written (spec 2026-10-11-variables-liees-champs-et-textes, ARCH-005, ARCH-RISK-003): the readers of FILE_SOURCES applied to the records themselves, the «Formule» domains computed against `calculations`."""
    domains = calculation_domains(calculations)
    for data, root, word in ((connections, "connections", "connection"), (connectors, "connectors", "connector"), (scripts, "scripts", "script")):
        domains += _records(root, word)(data)
    if formulas:
        domains += formula_domain.variable_domains(formulas, here, calculations)
    return values_of_domains(domains)


def known_values(data_dir=None):
    """Every variable a link may name, read from data/ now -- what Woodcore's window resolves a linked field against. A file not there or not readable is left out quietly: the «Variables» tab is where a broken file is said, and a field whose variable cannot be read keeps its last value with a warning (D-06)."""
    data_dir = Path(data_dir) if data_dir is not None else project.current().data_dir
    domains = []
    for name, schema_name, reader in FILE_SOURCES:
        path = data_dir / name
        if not path.is_file():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            validation.validate_structure(data, schema_name)
            domains.extend(reader(data))
        except (OSError, ValueError, validation.ValidationError, KeyError, TypeError, AttributeError):
            continue
    return values_of_domains(domains)


def registry_domains(mode, registry):
    """A document's registry as domains, in the order it states them, each marked with the document it was read from."""
    if registry is None:
        return []
    return [Domain(name=name, origin=mode, variables=list(found), kind=model.domain_kind(name))
            for name, found in registry.domains.items()]


def provenance(var, origin):
    """EXCEL, WOODCORE, TYPST or UNKNOWN: TYPST for whatever a document's registry holds, else what the var's `source` says (D-012)."""
    if origin == formula_domain.ORIGIN:
        return model.provenance_of(var.source)   # computed by Woodcore from a file it wrote: woodcore:Formules/<id>.typ
    if origin != EXPORT:
        return model.TYPST
    return model.provenance_of(var.source)
