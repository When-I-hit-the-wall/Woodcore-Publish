"""Whether a domain of the «Domaines» tab read by its name is printed above the domain that reads it (issue #113, spec docs/requirements/completed/2026-10-24-onglet-domaines-formulaire-code.md, REQ-011, D-8, ARCH-RISK-011).

`#var("eta", domain: "poutre-p1")` reads a value of another domain of the tab. Typst finds it only where that domain was printed **above** the line, in the same document -- else the compile stops: «var: no domain "poutre-p1" is declared above this line». The window says so in orange while it is so (the engineer's answer 7), **per document** (P-2): for each document whose sections include the domain that reads, the domain read must be included before it -- in the order of the document's sections (`structure_nodes.section_files`), then of their lines. A domain included nowhere is printed nowhere and gives no warning.

Read once a domain is opened or its file written, not at every key (the sections are files of their own). No Qt.
"""

import re

_INCLUDE = re.compile(r'#include\s+"(?P<path>/[^"]+\.typ)"')


def includes(here):
    """{document: [the files of domains it includes, from the Typst root, in the order it prints them]} -- `#include "/Domains/<id>.typ"` lines of its sections, comments left out."""
    import structure_nodes
    import typst_calls
    out = {}
    for mode in here.modes:
        folder = here.document_dir(mode)
        seen = []
        for file, printed in structure_nodes.section_files(here, mode):
            path = folder / file
            if not printed or not path.is_file():
                continue
            try:
                text = typst_calls.mask_comments(path.read_text(encoding="utf-8", errors="replace"))
            except OSError:
                continue
            seen += [m.group("path") for m in _INCLUDE.finditer(text)]
        out[mode] = seen
    return out


def not_above(here, reader, read, listing=None):
    """The documents in which domain `reader` (a formula_domain.Domain) is printed while the domain `read` (another) is not printed above it: [] where every document that prints the reader prints the domain read first, or none prints the reader. `listing` is `includes(here)`, read once by a caller asking for several."""
    listing = includes(here) if listing is None else listing
    try:
        mine, theirs = here.from_root(reader.path), here.from_root(read.path)
    except (ValueError, TypeError, AttributeError):
        return []
    out = []
    for mode, files in listing.items():
        if mine not in files:
            continue
        at = files.index(mine)
        if theirs not in files[:at]:
            out.append(mode)
    return out
