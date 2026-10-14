"""The captions of a document: «Tableau 1 — Les documents de référence», «Figure 1 — Système statique» (lib/calc-engine.typ caption-rules, applied by woodcore-document; spec docs/requirements/completed/2026-10-07-performance-erreurs-plans-legendes.md, REQ-021).

The engineer, 07.10.2026: «tous les titres de tableaux doivent suivre le format suivant: Tableau 1 --- Les documents de référence» · «le caption des figures doit apparaître ainsi: Figure 1 --- Système statique». Compiled as a document of the project is, through its config.typ and woodcore-document, in the three languages; the words of the kinds are the glossary's (figure.supplement_table, figure.supplement_image).
"""

import subprocess
import unicodedata

import conftest
from conftest import Skip

import project

BODY = """
#figure(table(columns: 2)[A][B], caption: [Les documents de référence])
#figure(rect(width: 2cm, height: 1cm), caption: [Système statique])
#table-figure([Allgemeine Beschreibung], 100%, table(columns: 1)[x])
"""


def _compile(here, lang, name):
    folder = here.typst_root / ".probe" / name
    folder.mkdir(parents=True, exist_ok=True)
    probe = folder / "probe.typ"
    probe.write_text('#import "/config.typ": conf\n#import "/commands.typ": *\n#show: conf\n#show: woodcore-document\n'
                     f'#set-report-language("{lang}")\n' + BODY, encoding="utf-8")
    out = folder / "probe.pdf"
    run = subprocess.run([project.typst_executable(), "compile", "--root", str(here.typst_root), str(probe), str(out)],
                         capture_output=True, text=True, encoding="utf-8", errors="replace")
    assert run.returncode == 0, run.stderr
    from pypdf import PdfReader
    return unicodedata.normalize("NFKC", "\n".join(p.extract_text() for p in PdfReader(str(out)).pages))


def test_a_table_and_a_figure_are_captioned_with_their_number_a_long_dash_and_their_title_in_each_language():
    if not conftest.have_typst():
        raise Skip("typst is not on the path")
    import test_plan_types_v0116 as types
    here = types._project("captions")
    expected = {"fr": ("Tableau", "Figure"), "de": ("Tabelle", "Abbildung"), "en": ("Table", "Figure")}
    import forms
    for form in ("bfh", "compact", "neutral"):   # the rule is woodcore-document's, so every form has it: each one compiled
        forms.apply(here, form)
        for lang, (table, figure) in expected.items():
            text = " ".join(_compile(here, lang, f"captions_{form}_{lang}").split())
            assert f"{table} 1 — Les documents de référence" in text, (form, lang, text)
            assert f"{figure} 1 — Système statique" in text, (form, lang, text)
            assert f"{table} 2 — Allgemeine Beschreibung" in text, (form, lang, "the engine's own tables follow the rule", text)
            assert "Fig." not in text and ": Les documents" not in text, (form, lang, text)
