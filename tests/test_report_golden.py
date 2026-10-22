"""Every page of the example project's documents, held to the byte at every level (spec 2026-10-20-indices-et-niveaux, lot 0, CON-003, ARCH-RISK-611).

The spec moves how a subscript is written in every formula (UI-001), who decides the level of a calculation's line (UI-002: a table read by Typst instead of a `level` the export writes) and gives a `level:` to every command that prints (UI-003, where level 2 must stay what the documents print today). Each of those promises "nothing else changes" at some level, and until now no test held a document's pages: `test_report` compiles them and reads nothing back. This one compiles the three documents of the example project to SVG -- the report at the levels 1, 2, 3 and at the uniform levels 1, 2, 3, the agreement and the basis of design at the levels 1, 2, 3 -- and a witness sheet carrying a plan, its legend, the position list and the quantities, and keeps the SHA-256 of every page in `tests/fixtures/report-golden.json`.

`SOURCE_DATE_EPOCH` is fixed, so the date a title page or a title block writes is the same on every run. A change that is meant is accepted by writing the new hashes -- `WOODCORE_UPDATE_GOLDEN=1 python tests/run_tests.py -k test_report_golden` -- with its reason kept in `CHANGES`, as `test_figure_golden` does.

⚠️ Skipped where `typst` is not on the path; some twenty compilations, so it is in the whole suite only.
"""

import hashlib
import json
import os
import subprocess

import conftest
from conftest import ROOT, Skip

import project
import sheets

GOLDEN = ROOT / "tests" / "fixtures" / "report-golden.json"
UPDATE = os.environ.get("WOODCORE_UPDATE_GOLDEN") == "1"
EPOCH = "1767225600"  # 2026-01-01 00:00 UTC: a fixed day for datetime.today()

# What each document is compiled at: the report at every level and every uniform level, the two others at every level.
VARIANTS = {
    "rs": [("level", 1), ("level", 2), ("level", 3), ("uniform", 1), ("uniform", 2), ("uniform", 3)],
    "cu": [("level", 1), ("level", 2), ("level", 3)],
    "bp": [("level", 1), ("level", 2), ("level", 3)],
}

# Why pages changed on purpose: {"<document> <variant>" or "every page": "version -- reason"}.
CHANGES = {
    "rs every variant, the pages of the polar moment VU-MP-1 and after it; rs uniform=1, pages 2-3": "spec 2026-10-22-image-polar-moment, REQ-003, D-02: the figure of VU-MP-1 no longer at the head of its domain but after N, V and M, drawn by #image-polar-moment with the arrows of the forces in each fastener and the note of the shares too small to make out, in a numbered figure with its caption (Abbildung 13) -- the pages after it move by its height, and the list of figures names it; nothing else changed",
    "rs every variant, page 8": "spec 2026-10-21-commandes-typst-refonte, lot 19: #position, the line of a position, joins a dimension and its unit (100/200 mm) and never prints a unit without its dimension; nothing else on the page moved",
    "rs, the pages of the domains written out": "spec 2026-10-21-commandes-typst-refonte, lot 18 (fix): a domain's heading one level below the document's heading above it, the headings of the domains before it left out -- the example's 38 domains in a row no longer nest one inside the other, and Typst converges",
    "every page of the three documents and the sheet B01": "spec 2026-10-21-commandes-typst-refonte, lots 10-18, REQ-017, REQ-019: the templates and the example written in raw Typst -- the documents' tables raw #table set by doc-tables (rules above, under the header, under the last row), the journals written once and included by domain-file(\"journal\", document), every load, connector, polar moment and script written out into its file and printed whole at every level (#domain, #var, #eq, no show-calc), the plans native figures, the sheet's objects raw #place; levels 1, 2 and 3 print more pages now that a domain written out is the engineer's file and not a call that drops lines by level",
    "every page with a citation": "spec 2026-10-21-commandes-typst-refonte, lot 1, UI-001: every norm cited beside a calculation, on its line or in a sentence is set in the palette's ink-soft grey and without the § before its clause (SIA 265 4.2.1); the pages that cite nothing are unchanged, and nothing else on the changed pages moved.",
    "rs every variant, from the loads on": "v0.120 -- restes of issue #69, REQ-001, REQ-002: the snow and wind sheets computed by Woodcore from their inputs -- c_red of Figur 9, the global forces of the table's force coefficients, the local forces of Annexe C, the names q_k1, dachform, qk_max_cf1 --, the pages after them moved (one page more at levels 2 and 3); the table of contents (page 2) follows",
    "rs level=1, rs uniform=1, bp level=1, cu level=1": "v0.120 -- lot 5, UI-003: at level 1 a figure, a table or a list prints alone -- a plan without its legend, caption, scale bar, lengths and centres; a table without its caption; a summary without its «Bezeichnung» --, so the figures after it renumber and the report is a page shorter. Level 2 and 3, the uniform 2 and 3 and the witness sheet did not move (CON-002), checked by this file before the update.",
    "every page with a subscript": "v0.120 -- lot 1, UI-001: every subscript upright, one quoted block in the norm's form (N_Rd, gamma_M1, f_m,y,d); the pages that print no subscript are unchanged, and nothing else on the changed pages moved (checked on the report's page 10 at level 3).",
}


def _guard():
    if not conftest.have_typst():
        raise Skip("typst is not on the path")


def _env():
    env = dict(os.environ)
    env["SOURCE_DATE_EPOCH"] = EPOCH
    return env


def _digest(text):
    return hashlib.sha256(text.replace("\r\n", "\n").encode("utf-8")).hexdigest()


def _pages(folder, stem):
    """[SHA-256] of the pages Typst wrote as `<stem>-<n>.svg`, in page order."""
    found = sorted(folder.glob(stem + "-*.svg"), key=lambda p: int(p.stem.rsplit("-", 1)[1]))
    return [_digest(p.read_text(encoding="utf-8")) for p in found]


def _compile(args, folder, stem):
    out = subprocess.run([project.typst_executable(), *args[:-1], str(folder / (stem + "-{p}.svg"))],
                         capture_output=True, text=True, encoding="utf-8", errors="replace", env=_env())
    assert out.returncode == 0, f"{stem} does not compile:\n{out.stderr}"
    pages = _pages(folder, stem)
    assert pages, f"{stem} wrote no page"
    return pages


def _documents():
    """{"<mode> <key>=<n>": [page hashes]} of the example project's three documents."""
    import documents
    here = conftest.PROJECT
    folder = conftest.tmpdir("report_golden")
    out = {}
    for mode, variants in VARIANTS.items():
        for key, value in variants:
            stem = f"{mode}-{key}{value}"
            args = documents.compile_args(here, mode, ["--input", f"{key}={value}"])
            out[f"{mode} {key}={value}"] = _compile(args, folder, stem)
    return out


def _sheet():
    """{"sheet B01": [page hashes]} of a witness sheet: a plan of the example at 1:100, its legend, the position list and the quantities -- the sheet commands UI-003 gives a level, compiled as a sheet compiles (no --input)."""
    import test_sheets
    here = test_sheets._project("report_golden_sheet")
    sheets.new_sheet(here)
    sheets.add_viewport(here, "B01", "Pavillon", 20, 35, scale=100)
    sheets.add_legend(here, "B01", 300, 20)
    sheets.add_position_list(here, "B01", 300, 120)
    sheets.add_quantities(here, "B01", 300, 220)
    folder = conftest.tmpdir("report_golden_sheet_out")
    return {"sheet B01": _compile(sheets.compile_args(here, "B01"), folder, "B01")}


def test_every_page_of_the_documents_is_the_one_held():
    _guard()
    found = {**_documents(), **_sheet()}
    if UPDATE or not GOLDEN.is_file():
        GOLDEN.parent.mkdir(parents=True, exist_ok=True)
        GOLDEN.write_text(json.dumps(found, indent=1, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
        return
    held = json.loads(GOLDEN.read_text(encoding="utf-8"))
    changed = []
    for name in sorted(held.keys() & found.keys()):
        if held[name] != found[name]:
            pages = [i + 1 for i, (a, b) in enumerate(zip(held[name], found[name])) if a != b]
            changed.append(f"{name}: pages {pages}" + (f", {len(held[name])} pages held, {len(found[name])} now" if len(held[name]) != len(found[name]) else ""))
    gone = sorted(held.keys() - found.keys())
    new = sorted(found.keys() - held.keys())
    assert not (changed or gone or new), (
        f"pages changed: {changed}; no longer compiled: {gone}; compiled and not held: {new} -- "
        "a change meant is written with WOODCORE_UPDATE_GOLDEN=1 and its reason kept in CHANGES")
