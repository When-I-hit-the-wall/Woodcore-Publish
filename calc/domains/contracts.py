"""What a domain of calc/domains/ offers the rest of Woodcore, written down (spec docs/requirements/active/2026-10-19-base-saine-nettoyage.md, C5).

A domain is a module, not a class: the window, `export_all` and the tests call its functions by name. Two shapes recur, and each is a `typing.Protocol` here -- documentation a type checker reads, and what tests/test_domain_contracts.py holds every domain to, in a table where a new domain takes its row:

* **a source domain** reads the engineer's files of one folder (`connectors/`, `plans/`, `details/`…): `read_source(path)` gives a source checked, `check_source(src, where)` refuses a malformed one naming the file and the field, `SOURCE_SCHEMA_VERSION` is the version a new source is written at;
* **an export domain** writes one file of `data/` for the report: `prepare(...)` builds it in memory and writes nothing, so a failed export leaves `data/` as it was; `write(...)` is its only writer; `export(...)` is the two, run by the window when a source is saved; `EXPORT_SCHEMA_VERSION` is the version of the plainest export it writes.

The arguments differ from one domain to another -- what an export needs (the positions, the values of the variables, where its figures go) is the domain's -- so a protocol names the functions and not their signatures. Qt-free, importing nothing of the domains.
"""

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
