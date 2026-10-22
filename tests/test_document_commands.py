"""The parametric objects of a project's documents (lib/document.typ, the three document modes, phase 3): the ten commands Woodcore writes between the tags of a section of the convention d'utilisation, the base de projet and the report.

What is held, command by command, is what each one decides and nothing `render-table` is already held to:

* a table prints its rows, and **a hidden column is absent** from the page while its cells stay in the call;
* **the engineer's words are never translated** -- a cell, a title, a caption that happens to be a term of the glossary («Schneelast») or to match a template of it («Element 3») prints as it is written, in a French report as in a German one;
* a live-load cell left to `auto` **is the export's own q_k and Q_k** for the row's category, a number written there **is printed in orange** with the line saying what orange means, and category E -- which SIA 261 8.2.2 leaves to the project -- is refused at `auto`;
* **no ψ column, ever** (the engineer, 01.10.2026: the Reduktionsbeiwerte are never shown for live loads): the default columns are the six, a column of the id `psi_0` is no known column and is refused, and a planted export that still carries ψ vars prints none of them;
* the load column of the non-structural self-weight takes a `#val(...)`, printed as the export's value;
* the field's placeholder, the ticked boxes, the chosen answer, the picture's frame, the plan's frame, the signature rows and the norms listed in full -- and registered for the bibliography;
* **every malformed argument is refused with a panic naming the command**, read with `conftest.panic_message`;
* and the file is where the engine says it is: `project.ENGINE_FILES`, `build_reference.LIB_FILES`, the `objects` category, and imported by name, so a helper never reaches a section.

⚠️ Every compiled check is skipped where `typst` is not on the path. Where a probe needs an export the example project does not carry -- a planted one -- it works on a copy of the report folder and the generated folder of its own (`_root`), test_display.py's own arrangement, so nothing the rest of the suite reads changes under it.
"""

import json
import re
import shutil
import subprocess
import sys
import unicodedata

import conftest
from conftest import ROOT, Skip
import project

PROJECT = conftest.PROJECT
DOCUMENT_TYP = ROOT / "lib" / "document.typ"
# What is left of the documents' parametric objects once they were written in raw Typst (spec 2026-10-21-commandes-typst-refonte, REQ-019): the list of the norms
COMMANDS = ("show-norm-list",)
def _guard():
    if not conftest.have_typst():
        raise Skip("typst is not on the path")


def _root(name):
    """A copy of the example project's top files and its generated folder -- the engine and the export: a Typst root of this test's own."""
    d = conftest.tmpdir(name)
    for f in ("commands.typ", "config.typ"):   # where the project keeps them: 000-Typst-Config/ laid out by folders (issue #64)
        source = PROJECT.config_dir / f
        target = d / source.relative_to(PROJECT.typst_root)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    relative = PROJECT.generated_dir.relative_to(PROJECT.typst_root)
    shutil.copytree(PROJECT.generated_dir, d / relative,
                    copy_function=shutil.copyfile, ignore=shutil.ignore_patterns("out", "docs"))
    images = PROJECT.typst_root / "Images"
    if images.is_dir():
        shutil.copytree(images, d / "Images", copy_function=shutil.copyfile)
    return d, d / relative / "data"


def _run(root, body, name, fmt="pdf", lang="de"):
    _guard()
    d = root / ".probe" / name
    d.mkdir(parents=True, exist_ok=True)
    probe = d / "probe.typ"
    probe.write_text('#import "/000-Typst-Config/config.typ": conf\n#import "/000-Typst-Config/commands.typ": *\n#report-level.update(2)\n#show: conf\n'
                     f'#set-report-language("{lang}")\n' + body + "\n", encoding="utf-8")
    out = d / f"probe.{fmt}"
    run = subprocess.run(["typst", "compile", "--root", str(root), "--format", fmt, str(probe), str(out)],
                         capture_output=True, text=True, encoding="utf-8", errors="replace")
    return run.returncode, run.stderr, out


def _text(body, name, lang="de", root=None):
    """The probe's text, as pypdf reads it back. NFKC: math's letters read as letters, «…» as «...», ² as 2."""
    root = root or PROJECT.typst_root
    code, err, out = _run(root, body, name, lang=lang)
    assert code == 0, err
    from pypdf import PdfReader
    return unicodedata.normalize("NFKC", "\n".join(p.extract_text() for p in PdfReader(str(out)).pages))


def _live(category):
    return conftest.exported("calculations.json")["domains"]["live-load"]["instances"][category]["vars"]


# --- where the file is -----------------------------------------------------------------------

def test_the_file_is_where_the_engine_says_it_is():
    """lib/document.typ is copied into every project (`project.ENGINE_FILES`), catalogued (`build_reference.LIB_FILES`) and its one command is in the `document` category -- a file one of them forgets is a report that fails on «file not found» in a project and nowhere in the checkout."""
    sys.path.insert(0, str(ROOT / "calc" / "tools"))
    import build_reference as ref
    assert "lib/document.typ" in project.ENGINE_FILES
    assert "document.typ" in ref.LIB_FILES
    assert set(COMMANDS) <= set(dict(ref.CATEGORIES)["document"])
    formula = (ROOT / "lib" / "formula.typ").read_text(encoding="utf-8")
    line = next(l for l in formula.splitlines() if l.startswith('#import "document.typ":'))      # relative on purpose: the line of lib/formula.typ that is looked for, not an import a probe writes
    assert sorted(n.strip() for n in line.split(":", 1)[1].split(",")) == sorted(COMMANDS), line


def test_a_helper_does_not_reach_a_section():
    """formula.typ imports the ten commands by name, so `doc-refuse` and the other helpers are the file's own -- a section that names one is refused as an unknown variable."""
    code, err, _ = _run(PROJECT.typst_root, '#doc-refuse("x", "y")', "helper")
    assert code != 0 and "unknown variable: doc-refuse" in err, err


def test_the_file_reads_no_norm_file_of_its_own():
    """The live loads come out of the export and the norms out of norms.json through bibliography.typ: document.typ names no file of calc/norms/, which test_distance.py holds equal to ENGINE_FILES."""
    source = DOCUMENT_TYP.read_text(encoding="utf-8")
    assert "calc/norms" not in re.sub(r"//.*", "", source), "lib/document.typ reads a norm file of its own"
    assert "json(" not in re.sub(r"//.*", "", source)


# --- doc-table --------------------------------------------------------------------------------

# --- live-load-table --------------------------------------------------------------------------

def test_no_live_load_instance_of_the_export_carries_a_psi():
    """The ψ vars left `calc/domains/live_load.py` (and the frozen export of the example project): a category carries its load and nothing else."""
    for category in ("A1", "B", "E", "H"):
        assert not [k for k in _live(category) if k.startswith("psi")], category


# --- dead-load-table --------------------------------------------------------------------------

# --- doc-field, doc-checklist, doc-choice ------------------------------------------------------

# --- doc-image, doc-plan -----------------------------------------------------------------------

def test_the_annexes_object_prints_the_annex_pages_of_the_excerpts_the_document_shows():
    """`show-annexes`: the pages of a source come only from the excerpts THIS document shows -- an excerpt shown by `image-extract` in a figure --, so a document that shows none prints no annex page, and `heading:` is the level of the annex's name."""
    excerpts = conftest.exported("annexes.json")["excerpts"]
    if not excerpts:
        raise Skip("the example project carries no excerpt")
    excerpt = sorted(excerpts)[0]
    shown = _text(f'#figure(image-extract("{excerpt}"), kind: image, caption: [A])\n#show-annexes(heading: 3)', "annexes-shown")
    assert "Anhang A" in shown, shown
    not_shown = _text('#show-annexes(heading: 3)', "annexes-not-shown")
    assert "Anhang A" not in not_shown, not_shown


# --- doc-signatures, show-norm-list -------------------------------------------------------------

def test_the_norms_a_section_names_are_listed_in_full_and_registered():
    norms = json.loads((ROOT / "calc" / "norms" / "norms.json").read_text(encoding="utf-8"))["references"]
    sia260 = next(e for e in norms if e["key"] == "SIA 260")
    body = ('#show-norm-list(keys: ("SIA 260:2013", "SIA 999 (unbekannt)", [Eine Zeile von Hand], "SIA 260"))\n'
            "Weiter.\n#show-bibliography(data: false)")
    text = _text(body, "norms")
    head, tail = text.split("Weiter.")
    assert sia260["title"]["de"] in head and head.count(sia260["designation"]) == 1, head   # an alias, listed once
    assert "SIA 999 (unbekannt)" in head and "Eine Zeile von Hand" in head, head
    assert tail.count(sia260["designation"]) == 1 and "SIA 999 (unbekannt)" in tail, "the keys are registered for the bibliography, a document and its alias once"
    assert "Eine Zeile von Hand" not in tail, "content is registered nowhere"
    # an empty selection prints nothing between the two words -- the page's own number comes after them
    assert _text("Vorher\n#show-norm-list()\nNachher", "norms-empty").split()[:3] == ["Vorher", "Nachher", "1"]


# --- refusals -----------------------------------------------------------------------------------
