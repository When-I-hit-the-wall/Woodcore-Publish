"""The report compiles -- in every language and at every uniform level.

Nine compilations. Slow, and last in the file order on purpose. It is the coarsest check in the folder and the one that catches the most: a command renamed in the engine, a section calling one that no longer exists, a figure a language does not have, a data file whose shape moved under `show-*`.

⚠️ Skipped where `typst` is not on the path. Skipped, not failed: a machine that only runs the Python pipeline is a legitimate machine.
"""

import subprocess

import conftest
from conftest import ROOT, Skip

TYPST_ROOT = conftest.TYPST_ROOT              # the report's folder of the example project the tests work on
ENTRY = conftest.PROJECT.report_typ
LANGUAGES = ("de", "fr", "en")
LEVELS = (1, 2, 3)


def _compile(out, *inputs):
    args = ["typst", "compile", "--root", str(TYPST_ROOT), str(ENTRY), str(out)]
    for key, value in inputs:
        args += ["--input", f"{key}={value}"]
    return subprocess.run(args, capture_output=True, text=True, encoding="utf-8")


def _guard():
    if not conftest.have_typst():
        raise Skip("typst is not on the path")
    if not ENTRY.exists():
        raise Skip(f"{ENTRY.name} is not there")


def test_the_report_compiles_as_written():
    _guard()
    d = conftest.tmpdir("report")
    out = _compile(d / "as-written.pdf")
    assert out.returncode == 0, f"the report does not compile:\n{out.stderr}"
    assert "warning" not in out.stderr.lower(), f"it compiles with warnings:\n{out.stderr}"


def test_the_report_compiles_in_every_language():
    """A figure is drawn once per language and the record names one file each (docs/typst/language.md §4bis): a language whose figure was not exported fails here."""
    _guard()
    d = conftest.tmpdir("report_lang")
    for lang in LANGUAGES:
        out = _compile(d / f"{lang}.pdf", ("lang", lang))
        assert out.returncode == 0, f"the report does not compile in {lang}:\n{out.stderr}"


def test_the_report_compiles_at_every_uniform_level():
    """--input uniform=N renders every show-* at N, per-call overrides ignored (section 4). A var, a step or a table whose level the data states wrongly shows up as a compile error at one level and not another."""
    _guard()
    d = conftest.tmpdir("report_level")
    for level in LEVELS:
        out = _compile(d / f"u{level}.pdf", ("uniform", level))
        assert out.returncode == 0, f"the report does not compile at uniform level {level}:\n{out.stderr}"


def test_an_invalid_level_is_refused():
    """The entry point's own assertion, which is what turns a typo in the build command into a message rather than a wrong report."""
    _guard()
    d = conftest.tmpdir("report_bad")
    out = _compile(d / "bad.pdf", ("level", 4))
    assert out.returncode != 0, "--input level=4 was accepted"
    assert "level" in out.stderr, out.stderr


def test_an_unknown_language_is_refused():
    _guard()
    d = conftest.tmpdir("report_bad_lang")
    out = _compile(d / "bad.pdf", ("lang", "it"))
    assert out.returncode != 0, "--input lang=it was accepted, and the glossary has no Italian"
    assert "language" in out.stderr.lower(), out.stderr


# --- what a command says, and in which language (periodic audit 260916) ---------------

def _probe(name, body):
    """Compiles `body` under the report's own setup; gives (returncode, stderr, the PDF's text with its whitespace collapsed)."""
    import re
    _guard()
    d = conftest.probe_dir(name)
    probe = d / "probe.typ"
    # absolute imports, read from the Typst root: the directory's depth is the harness's (tests/test_harness.py)
    probe.write_text('#import "/000-Typst-Config/config.typ": conf\n#import "/000-Typst-Config/commands.typ": *\n#show: conf\n' + body + "\n", encoding="utf-8")
    out = subprocess.run(["typst", "compile", "--root", str(TYPST_ROOT), str(probe), str(d / "probe.pdf")],
                         capture_output=True, text=True, encoding="utf-8")
    text = ""
    if out.returncode == 0:
        from pypdf import PdfReader
        raw = "\n".join(page.extract_text() for page in PdfReader(str(d / "probe.pdf")).pages)
        text = re.sub(r"\s+", " ", re.sub(r"-\s*\n\s*", "", raw))
    return out.returncode, out.stderr, text


def _first(file, key):
    import json
    records = json.loads((conftest.PROJECT.data_dir / file).read_text(encoding="utf-8")).get(key, {})
    if not records:
        raise Skip(f"data/{file} holds no {key}")
    return next(iter(records))


def test_an_unknown_position_is_refused_listing_the_valid_ones():
    """`show-position("NOPE")` failed on Typst's own «file not found» with no list of ids, where every other show-* lists them (AUD-7-214). `show-position` is gone since v0.94, and the two that name a position in its place refuse one the same way."""
    for name, call in (("probe_position", '#position("NOPE")'),):
        code, err, _ = _probe(name, call)
        assert code != 0
        assert "valid positions:" in err and "NOPE" in err, err[:800]


def test_an_unknown_domain_on_a_position_lists_the_calculation_domains():
    """`show-calc("dead", "T001")` named the position's domains (none) and not the calculation domains, where the typo most likely is (AUD-7-225)."""
    import json
    positions = json.loads((conftest.PROJECT.data_dir / "positions-index.json").read_text(encoding="utf-8"))["positions"]
    if not positions:
        raise Skip("no position exported")
    code, err, _ = _probe("probe_domain", f'#var("x", domain: ("dead", "{positions[0]}"))')
    assert code != 0
    assert "calculation domains:" in err and "dead-load" in err, err[:800]


def test_verify_accepts_a_double_equals_sign():
    """The alias `==` was declared but `relation-ops` did not know it, so the source was split on its first `=` and failed «cannot evaluate "= 1"» (AUD-7-224)."""
    code, err, text = _probe("probe_verify", '#var("a", 2, "kN")\n#var("b", 2, "kN")\n#verify(`a == b`, level: 2)')
    assert code == 0, err[:800]
    assert "✔" in text, text


def test_an_annex_is_cited_as_an_annex_in_the_report_s_language():
    """«SIA 261 §Anhang D» was printed as it stands in French and English: «Anhang» is a word (periodic audit 260916, AUD-3-13). Since the spec 2026-10-21-commandes-typst-refonte (UI-001) no citation takes a §, a clause no more than an annex.

    At level 3, because that is where `#var` prints a citation since v0.85.1 — 1 the value, 2 the label, 3 where it comes from. What is checked here is the wording of the reference, not the level it appears at.
    """
    for lang, word in (("de", "Anhang D"), ("fr", "annexe D"), ("en", "Annex D")):
        code, err, text = _probe("probe_annex_" + lang, f'#set-report-language("{lang}")\n#var("h_0", 438, "m", norm: "SIA 261", norm-ref: "Anhang D", level: 3)\n#var("s_k", 1, "kN/m²", norm: "SIA 261", norm-ref: "5.2.6", level: 3)')
        assert code == 0, err
        assert "SIA 261 " + word in text and "§Anhang" not in text and "§ Anhang" not in text, (lang, text)
        assert "SIA 261 5.2.6" in text and "§" not in text, (lang, text)


def test_a_french_report_sets_a_narrow_space_before_the_engine_s_colons_and_semicolons():
    """The glossary's French carried the narrow no-break space before «:» and «;», and the engine's own joints did not -- «Géométrie du bâtiment: L = …», «C_e = 1; C_T = 1» (periodic audit 260916, AUD-3-12). German and English keep theirs tight."""
    import re
    sheet = _first("calculations.json", "domains")
    data = __import__("json").loads((conftest.PROJECT.data_dir / "calculations.json").read_text(encoding="utf-8"))
    instance = next(iter(data["domains"]["snow-load"]["instances"]))
    # the engine's joints: a variable's label, description and citation, joined in its footnote at level 3
    body = f'#var("korrektur", domain: ("snow-load", "{instance}"), level: 3)\n#var("ce", domain: ("snow-load", "{instance}"), level: 3)\n'
    code, err, fr = _probe("probe_colon_fr", '#set-report-language("fr")\n' + body)
    assert code == 0, err
    glued = re.findall(r"\w{2}[:;] ", fr)
    assert not glued, glued
    code, err, de = _probe("probe_colon_de", body)
    assert code == 0, err
    assert re.search(r"\w{2}[:;] ", de), "the German page lost its tight colons: " + de[:300]
