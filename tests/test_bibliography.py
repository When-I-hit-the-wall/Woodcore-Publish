"""The bibliography -- every norm and document the report cites, listed in full at the end of it (lib/bibliography.typ, calc/norms/norms.json, v0.99).

The engineer's own rule for it was that **no existing page moves**: a citation in the right-hand column stays «SIA 265 §4.2.1», and what is new is that the document behind it is named in full once, at the end. So the first thing held here is that registering a citation prints nothing at all -- the same body compiled with and without `bib-note` gives the same pages, to the text and to the millimetre.

What else is held, and nowhere else:

* **the catalogue is checked before anything is taken out of it** (`calc/norms/norms.py`), each rule against a planted defect -- and every entry names the edition its title was read off, which is docs/architecture/principles.md §2 rule 13 given teeth;
* **one catalogue, named in four places** -- lib/bibliography.typ reads it, norms.py checks it, calc/project.py copies it into every project beside the engine, and the examples' fixture carries it. A file one of them forgets is a report that fails on «file not found» in a project and nowhere in the checkout (the rule tests/test_distance.py already holds for the distance tables);
* **the three blocks**, their order, their sorting, and that a citation no entry names is printed as it was cited;
* **`state.final()`**, which is what lets the list be printed before the citations it lists;
* **the .bib reader**: what it reads, that a project's entry wins over the engine's, and that every one of its refusals names the line.

⚠️ The compiled checks are skipped where `typst` is not on the path.
"""

import json
import re
import subprocess

import conftest
from conftest import ROOT, Skip
from norms import norms
import project

BIB_TYP = ROOT / "lib" / "bibliography.typ"
BLOCKS = ("norm", "literature", "other")


def _typst_source():
    return BIB_TYP.read_text(encoding="utf-8")


# --- the catalogue ------------------------------------------------------------

def _read_with(entries, extra=None):
    """The reader run over a catalogue of this test's own: (ok, the refusal's message)."""
    import validation
    folder = conftest.tmpdir("bibliography_catalogue")
    path = folder / "norms.json"
    data = {"_source": "a test's own", "_note": "a test's own", "references": entries}
    if extra:
        data.update(extra)
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    was, cache = norms.PATH, dict(norms._cache)
    norms.PATH, norms._cache = path, {}
    try:
        norms.references()
        return True, None
    except validation.ValidationError as exc:
        return False, str(exc)
    finally:
        norms.PATH, norms._cache = was, cache


def _entry(**over):
    sound = {
        "key": "SIA 999",
        "kind": "norm",
        "designation": "SIA 999:2026",
        "title": {"de": "Ein Titel", "fr": "Un titre", "en": "A title"},
        "edition": "2026",
        "publisher": "SIA",
        "_source": "a title page",
    }
    sound.update(over)
    return sound


def test_a_sound_catalogue_is_read():
    ok, message = _read_with([_entry()])
    assert ok, message


def test_what_the_catalogue_reader_refuses_it_names():
    """Each rule fired on a planted defect: a guard that has never fired is a guard nobody has tested."""
    planted = (
        ({"kind": "both"}, "kind"),
        ({"kind": None}, "kind"),
        ({"designation": ""}, "designation"),
        ({"edition": None}, "edition"),
        ({"title": ""}, "title"),
        ({"title": {"it": "Un titolo"}}, "title"),
        ({"title": {"de": ""}}, "title"),
        ({"publisher": {}}, "publisher"),
        ({"_source": ""}, "_source"),
        ({"key": ""}, "key"),
        ({"aliases": "SIA 999:2026"}, "aliases"),
    )
    for over, word in planted:
        ok, message = _read_with([_entry(**over)])
        assert not ok, "a catalogue with %r was read" % (over,)
        assert word in message, (over, message)
        assert "calc/norms/norms.json" in message, (over, message)
    # no 'references' list at all
    ok, message = _read_with([])
    assert not ok and "references" in message, message


def test_one_citation_reaches_one_entry():
    """A key or an alias two entries claim is refused naming both: a citation that could mean two documents is a citation nobody can check."""
    ok, message = _read_with([_entry(), _entry(key="SIA 998", aliases=["SIA 999"])])
    assert not ok, "two entries claimed one citation"
    assert "SIA 999" in message and "SIA 998" in message, message


def test_every_entry_names_the_edition_its_title_was_read_off():
    """docs/architecture/principles.md §2 rule 13: a value taken from a norm is read from the norm itself, at a page that can be turned to. The `_source` is where the entry says which -- and it is never printed."""
    for entry in norms.references():
        assert entry["_source"].strip(), entry["key"]
    # and the report prints the four fields and not that sentence
    assert "_source" not in _typst_source(), "lib/bibliography.typ reads the _source, which is never printed"


def test_the_catalogue_names_what_the_engine_already_cites():
    """Every document the engine's own code and data cite has an entry, so that none of them lands in «Weitere Dokumente»."""
    from domains import connection
    for citation in ("SIA 260", "SIA 261", "SIA 261/1", "SIA 263", "SIA 265", "SIA 265/1",
                     "SN EN 14592", "SZS C5", "STE Compact 02", connection.DEFAULT_NORM):
        assert norms.reference(citation) is not None, "the catalogue does not name %r" % citation
    # the engineer's own example of #cite-norm
    assert norms.reference("VKF14-15") is not None


def test_the_export_cites_nothing_the_catalogue_lacks():
    """Every `norm` the example project's export carries resolves -- which is what keeps its bibliography's third block empty of the engine's own citations."""
    found = set()

    def walk(node):
        if isinstance(node, dict):
            if isinstance(node.get("norm"), str):
                found.add(node["norm"])
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    for name in ("calculations.json", "connections.json", "connectors.json"):
        walk(conftest.exported(name))
    assert found, "the export cites nothing at all -- has it been run?"
    missing = sorted(n for n in found if norms.reference(n) is None)
    assert not missing, "the export cites %s, which calc/norms/norms.json does not name" % missing


def test_the_kinds_are_the_two_the_reader_and_the_engine_agree_on():
    typst = re.search(r"#let bib-kinds = \((.*?)\)", _typst_source()).group(1)
    assert set(re.findall(r'"([a-z]+)"', typst)) == set(norms.KINDS)
    blocks = re.search(r"#let bib-blocks = \((.*?)\)", _typst_source()).group(1)
    assert tuple(re.findall(r'"([a-z]+)"', blocks)) == BLOCKS


def test_one_catalogue_in_four_places():
    """lib/bibliography.typ reads it, calc/norms/norms.py checks it, project.ENGINE_FILES copies it into every project, and the examples' fixture carries it."""
    named = re.findall(r'#let bib-file = "([^"]+)"', _typst_source())
    assert named == [norms.NAME + ".json"], named
    assert "lib/bibliography.typ" in project.ENGINE_FILES
    assert "calc/norms/" + norms.NAME + ".json" in project.ENGINE_FILES
    fixture = ROOT / "examples" / "calc" / "norms" / (norms.NAME + ".json")
    assert fixture.is_file(), "examples/calc/norms/ lacks %s -- an example of #show-bibliography cannot compile" % fixture.name
    # the same file, so a frozen example lists what the engine lists
    assert json.loads(fixture.read_text(encoding="utf-8")) == json.loads(norms.PATH.read_text(encoding="utf-8"))


def test_the_glossary_carries_the_three_blocks():
    """The block names are the engine's own words, in three languages -- and the examples' copy has them too, or an example of #show-bibliography fails on a glossary key."""
    for path in (ROOT / "calc" / "i18n" / "strings.json", ROOT / "examples" / "calc" / "i18n" / "strings.json"):
        glossary = json.loads(path.read_text(encoding="utf-8"))["engine"]
        for name in BLOCKS:
            key = "bibliography." + name
            assert key in glossary, "%s lacks %s" % (path.name, key)
            for lang in ("de", "fr", "en"):
                assert glossary[key][lang].strip(), (key, lang)


# --- compiled ----------------------------------------------------------------

def _compile(body, name):
    """Compiles `body` in the example project's report, as a section would; returns (ok, text or the refusal)."""
    if not conftest.have_typst():
        raise Skip("typst is not on the path")
    return _compile_in(conftest.probe_dir(name), body)


def _pages(body, name):
    """The probe's pages as (text, width, height) -- what says a page has not moved."""
    if not conftest.have_typst():
        raise Skip("typst is not on the path")
    d = conftest.probe_dir(name)
    probe = d / "probe.typ"
    probe.write_text('#import "/000-Typst-Config/commands.typ": *\n#report-level.update(2)\n' + body + "\n", encoding="utf-8")
    out = subprocess.run(["typst", "compile", "--root", str(conftest.TYPST_ROOT), str(probe), str(d / "probe.pdf")],
                         capture_output=True, text=True, encoding="utf-8")
    assert out.returncode == 0, out.stderr
    from pypdf import PdfReader
    return [(p.extract_text(), round(float(p.mediabox.width), 3), round(float(p.mediabox.height), 3))
            for p in PdfReader(str(d / "probe.pdf")).pages]


def test_registering_a_citation_prints_nothing():
    """The engineer's acceptance criterion, held as the property it rests on: `bib-note` is a state update and puts nothing on the page, so a page that carried no bibliography before carries the same page now -- to the text and to the millimetre.

    ⚠️ This is what makes the 276 frozen example pages safe: every command that gained a registration gained exactly this and nothing else.
    """
    plain = "Ein Satz mit #var(\"F\", 7, \"kN\") darin, und noch einer.\n"
    noted = ("Ein Satz mit #var(\"F\", 7, \"kN\", norm: \"SIA 265\") darin, "
             "#bib-note(\"SIA 260\")#bib-note(\"STE Compact 02\") und noch einer.\n")
    # the same sentence, once with three registrations in it and once without: `norm:` prints no citation at
    # level 1, so the two bodies differ only in what they register
    a = _pages("#report-level.update(1)\n" + plain, "bibliography_plain")
    b = _pages("#report-level.update(1)\n" + noted, "bibliography_noted")
    assert [p[1:] for p in a] == [p[1:] for p in b], "a registration moved the page: %s against %s" % (a, b)
    assert [p[0] for p in a] == [p[0] for p in b], "a registration printed something: %r against %r" % (a[0][0], b[0][0])


def test_the_three_blocks_in_their_order():
    """The example project's own citations: SIA 261 and SIA 265 out of its export, bauforumstahl's Arbeitshilfe on its connections, and «Sherpa», which Sections/005 cites with `norm:` and no entry names."""
    ok, text = _compile('#show-bibliography()\n#bib-note("Sherpa")', "bibliography_blocks")
    assert ok, text
    for word in ("Normen", "Einwirkungen auf Tragwerke", "Holzbau",
                 "Literatur", "Tragwerksplanung im Stahlbau",
                 "Weitere Dokumente", "Sherpa"):
        assert word in text, (word, text)
    assert text.index("Normen") < text.index("Literatur") < text.index("Weitere Dokumente"), text
    # the four fields, and never the file it was read from
    assert "Schweizerischer Ingenieur- und Architektenverein" in text
    assert "ExternalFiles" not in text and ".pdf" not in text, "the bibliography names the library's file"


def test_a_citation_without_an_entry_is_printed_as_it_was_cited():
    """Nothing is invented around it, and nothing is lost: it stands in the third block under the very string that cited it."""
    ok, text = _compile('#bib-note("Hilti, ETA-19/0604")\n#show-bibliography(data: false)', "bibliography_other")
    assert ok, text
    assert "Weitere Dokumente" in text and "Hilti, ETA-19/0604" in text, text
    assert "Normen" not in text and "Literatur" not in text, "an empty block was printed: %s" % text


def test_the_list_holds_what_the_whole_document_cited_wherever_it_is_printed():
    """`state.final()`: a bibliography set before the citations it lists still lists them -- which is what lets Sections/007 stand where the engineer puts it."""
    ok, text = _compile('#show-bibliography(data: false)\n\n#pagebreak()\n#bib-note("SIA 263")', "bibliography_final")
    assert ok, text
    assert "Stahlbau" in text and "SIA 263:2013" in text, text


def test_a_norm_the_report_never_cites_is_never_listed():
    ok, text = _compile('#bib-note("SIA 263")\n#show-bibliography(data: false)', "bibliography_only_cited")
    assert ok, text
    assert "SIA 263:2013" in text, text
    for never in ("SIA 260:2013", "SZS C5", "VKF"):
        assert never not in text, (never, text)


def test_the_edition_is_not_said_twice():
    """«SIA 261:2020 — Einwirkungen auf Tragwerke. …, 2020.» says the year twice; the designation already carries it."""
    ok, text = _compile('#bib-note("SIA 261")\n#show-bibliography(data: false)', "bibliography_edition")
    assert ok, text
    line = [l for l in text.splitlines() if "SIA 261:2020" in l][0]
    assert not line.rstrip().endswith("2020."), line
    # one whose edition is not in its designation keeps it
    ok, text = _compile('#bib-note("VKF 14-15")\n#show-bibliography(data: false)', "bibliography_edition2")
    assert ok, text
    assert "01.01.2017" in text, text


def test_a_block_is_sorted_by_its_designations():
    ok, text = _compile('#bib-note("SIA 265")#bib-note("SIA 260")#bib-note("SIA 263")#bib-note("SIA 261")\n'
                        '#show-bibliography(data: false)', "bibliography_sorted")
    assert ok, text
    order = [text.index(d) for d in ("SIA 260:2013", "SIA 261:2020", "SIA 263:2013", "SIA 265:2021")]
    assert order == sorted(order), text


def test_a_norm_comes_before_its_supplement_and_the_case_is_ignored():
    """Two things codepoint order gets wrong and a reader notices: `/` sorts before `:`, which put «SIA 261/1:2020» above «SIA 261:2020»; and a lowercase initial sorts after every capital, which put «bauforumstahl» after «STE Compact 02»."""
    ok, text = _compile('#bib-note("SIA 261/1")#bib-note("SIA 261")#bib-note("SIA 265/1")#bib-note("SIA 265")\n'
                        '#show-bibliography(data: false)', "bibliography_sorted_supplement")
    assert ok, text
    order = [text.index(d) for d in ("SIA 261:2020", "SIA 261/1:2020", "SIA 265:2021", "SIA 265/1:2018")]
    assert order == sorted(order), text
    ok, text = _compile('#bib-note("STE Compact 02")#bib-note("bauforumstahl")\n'
                        '#show-bibliography(data: false)', "bibliography_sorted_case")
    assert ok, text
    assert text.index("bauforumstahl,") < text.index("STE Compact 02"), text


def test_the_blocks_printed_are_the_call_s_to_choose():
    ok, text = _compile('#bib-note("SIA 265")#bib-note("STE Compact 02")\n'
                        '#show-bibliography(data: false, blocks: ("literature",))', "bibliography_pick")
    assert ok, text
    assert "Plans dans la construction en bois" in text and "Holzbau" not in text, text
    ok, message = _compile('#show-bibliography(blocks: ("zork",))', "bibliography_pick_bad")
    assert not ok and "zork" in message and "literature" in message, message


def test_it_follows_the_report_s_language():
    ok, text = _compile('#set-report-language("fr")\n#bib-note("SIA 265")#bib-note("bauforumstahl")\n'
                        '#show-bibliography(data: false)', "bibliography_fr")
    assert ok, text
    assert "Normes" in text and "Construction en bois" in text, text
    assert "Société suisse des ingénieurs et des architectes" in text, text
    # a document printed in one language only says its title once, and that one is printed (section 4bis)
    assert "Littérature" in text and "Tragwerksplanung im Stahlbau" in text, text


def test_cite_norm_prints_in_the_prose_and_registers():
    ok, text = _compile('Die Baustoffe sind nach #cite-norm(norm: "VKF 14-15", norm-ref: "2.5.3") zu verwenden.\n\n'
                        '#show-bibliography(data: false)', "bibliography_cite")
    assert ok, text
    assert "VKF 14-15 2.5.3" in text and "VKF 14-15 §" not in text, text
    # the directive gained its German title (v0.111): a German report prints it, and the French one is in the French report (below)
    assert "Verwendung von Baustoffen" in text, text
    # a table and an annex take the report's own word and no §, as norm-text sets them
    ok, text = _compile('#cite-norm(norm: "SIA 265", norm-ref: "Tabelle 8")\n'
                        '#cite-norm(norm: "SIA 261", norm-ref: "Anhang D")\n'
                        '#cite-norm(norm: "SIA 265")', "bibliography_cite_forms")
    assert ok, text
    assert "SIA 265 Tabelle 8" in text and "SIA 261 Anhang D" in text, text
    assert "SIA 265 §Tabelle" not in text, text


def test_what_cite_norm_refuses_it_names():
    for body, word in (('#cite-norm()', "norm"),
                       ('#cite-norm(norm: 265)', "norm"),
                       ('#cite-norm(norm: "SIA 265", norm-ref: 8)', "norm-ref")):
        ok, message = _compile(body, "bibliography_cite_refuse")
        assert not ok, body
        assert word in message and "cite-norm" in message, (body, message)


def test_a_norm_written_at_a_call_is_registered_from_outside_its_context():
    """⚠️ The panne of v0.85 (docs/domain/connections.md §3.3quinquies), held from the outside: a state written inside a command's own context is not read back the same way, so every command that takes a `norm:` emits its registration before its context. A regression shows up here as a document missing from the list.

    `var` at level 0 prints nothing at all, and its norm is registered all the same: whether the clause is printed is a matter of level, whether the document is a source is not. The four commands that take a `norm:` since the spec 2026-10-21-commandes-typst-refonte: `var`, `eq`, `verify` and `domain`.
    """
    body = ('#var("R_k", 7, "kN", norm: "SIA 265", norm-section: "6.2.1.1", level: 0)\n'
            '#eq("R_d", `R_k / 2`, norm: "SIA 260", level: 0)\n'
            '#var("a", 3, "mm", norm: "SIA 261/1", level: 0)\n'
            '#verify(`R_d <= R_k`, norm: "SIA 263", level: 0)\n'
            '#domain("trag", norm: "SZS C5", level: 0)[#var("b", 100, "mm")]\n'
            '#show-bibliography(data: false)')
    ok, text = _compile(body, "bibliography_registered")
    assert ok, text
    for designation in ("SIA 260:2013", "SIA 261/1:2020", "SIA 263:2013", "SIA 265:2021", "SZS C5"):
        assert designation in text, (designation, text)


def test_distance_registers_the_norm_its_tables_come_out_of():
    ok, text = _compile('#distance(12, "dowel", table: 24, norm: none, label: none)\n'
                        '#show-bibliography(data: false)', "bibliography_distance")
    assert ok, text
    # printed with no citation beside the table, and the document behind it is still named
    assert "SIA 265 Tabelle 24" not in text, text
    assert "SIA 265:2021" in text and "Holzbau" in text, text


# --- the project's own references.bib -----------------------------------------

SOUND_BIB = """% the project's own documents
@comment{ passed over }

@misc{Sherpa,
  title        = {SHERPA Verbindungssysteme},
  designation  = {Sherpa, ETA-12/0197},
  aliases      = {Sherpa XS},
  publisher    = {ETA-Danmark A/S},
  year         = 2019,
  url          = {https://example.invalid/eta},
}

@book{HBT,
  title     = "Lignum Holzbautabellen HBT 1",
  publisher = {Lignum},
  edition   = {2021},
}

@standard{SIA 265,
  title       = {Construction en bois, édition du projet},
  designation = {SIA 265:2021 (projet)},
  publisher   = {SIA},
  edition     = {2021},
}
"""


def _with_bib(body, name, text=SOUND_BIB):
    """Compiles `body` beside a references.bib of this test's own, in the probe's own folder -- so no test writes into the project's report folder, and two of them never share a file.

    `@BIB@` in the body is replaced by the path `project:` takes: the file's path from the report's own folder, which is the Typst root (tests/test_harness.py's rule -- computed, never written down).
    """
    if not conftest.have_typst():
        raise Skip("typst is not on the path")
    folder = conftest.probe_dir(name)
    (folder / "references.bib").write_text(text, encoding="utf-8")
    where = conftest.import_path(folder / "references.bib").lstrip("/")
    return _compile_in(folder, body.replace("@BIB@", where))


def _compile_in(folder, body):
    probe = folder / "probe.typ"
    probe.write_text('#import "/000-Typst-Config/commands.typ": *\n#report-level.update(2)\n' + body + "\n", encoding="utf-8")
    out = subprocess.run(["typst", "compile", "--root", str(conftest.TYPST_ROOT), str(probe), str(folder / "probe.pdf")],
                         capture_output=True, text=True, encoding="utf-8")
    if out.returncode != 0:
        message = conftest.panic_message(out.stderr)
        return False, message if message is not None else out.stderr
    from pypdf import PdfReader
    return True, re.sub(r"[ \t]+", " ", "\n".join(p.extract_text() for p in PdfReader(str(folder / "probe.pdf")).pages))


def test_a_project_bib_is_read():
    ok, text = _with_bib('#bib-note("Sherpa")#bib-note("HBT")\n#show-bibliography(data: false, project: "@BIB@")',
                         "bibliography_bib")
    assert ok, text
    assert "Sherpa, ETA-12/0197" in text and "SHERPA Verbindungssysteme" in text and "ETA-Danmark A/S" in text, text
    assert "Lignum Holzbautabellen HBT 1" in text and "2021" in text, text
    # an entry with no designation is opened by the key that cited it, and an unread field is not printed
    assert "HBT" in text and "example.invalid" not in text, text


def test_an_alias_of_a_project_entry_is_found():
    ok, text = _with_bib('#bib-note("Sherpa XS")\n#show-bibliography(data: false, project: "@BIB@")',
                         "bibliography_bib_alias")
    assert ok, text
    assert "Sherpa, ETA-12/0197" in text, text


def test_a_project_entry_wins_over_the_engine_s():
    """A project knows which edition it was calculated against."""
    ok, text = _with_bib('#bib-note("SIA 265")\n#show-bibliography(data: false, project: "@BIB@")',
                         "bibliography_bib_wins")
    assert ok, text
    assert "SIA 265:2021 (projet)" in text and "édition du projet" in text, text
    assert "Holzbau." not in text, text


def test_the_entry_type_says_the_block_and_kind_overrides_it():
    text = SOUND_BIB + "\n@techreport{Kurs, title = {Ein Kursdokument}, publisher = {BFH}, year = {2026}, kind = {literature}}\n"
    ok, out = _with_bib('#bib-note("Kurs")#bib-note("Sherpa")\n#show-bibliography(data: false, project: "@BIB@")',
                        "bibliography_bib_kind", text)
    assert ok, out
    # @techreport would be a norm; kind = {literature} puts it with the Sherpa approval
    assert "Literatur" in out and "Ein Kursdokument" in out and "Normen" not in out, out


def test_a_value_is_printed_as_the_bib_writes_it():
    """No TeX is interpreted: a string reaches the page as it stands, which is what keeps a title from changing the page around it."""
    text = '@book{X, title = {Ein {Titel} mit -- und $a$}, publisher = {P}, year = {2026}}\n'
    ok, out = _with_bib('#bib-note("X")\n#show-bibliography(data: false, project: "@BIB@")',
                        "bibliography_bib_literal", text)
    assert ok, out
    assert "Ein Titel mit -- und $a$" in out, out


def test_what_the_bib_reader_refuses_it_names_with_its_line():
    """Nothing is swallowed in silence: every shape this reader does not understand is refused, with the file and the line."""
    planted = (
        ("@book{A, title = {A}}\n\n@zork{B,\n  title = {B}\n}\n", 3, "@zork"),
        ("@book{A,\n  publisher = {P}\n}\n", 1, "title"),
        ("% head\n@string{sia = \"SIA\"}\n@book{A, title={A}}\n", 2, "@string"),
        ("@preamble{ \\newcommand }\n", 1, "@preamble"),
        ("@book(A,\n  title = {A}\n)\n", 1, "braces"),
        ("@book{A,\n  title = {A\n}\n", 1, "never closed"),
        ("@book{A,\n  title = {A},\n  kind = {both}\n}\n", 1, "kind"),
        ("@book{A,\n  title {A}\n}\n", 2, "="),
        ("@book{,\n  title = {A}\n}\n", 1, "key"),
    )
    for text, line, word in planted:
        ok, message = _with_bib('#show-bibliography(data: false, project: "@BIB@")',
                                "bibliography_bib_bad", text)
        assert not ok, "a .bib with %r was read" % text[:30]
        assert "references.bib" in message and ("line %d" % line) in message, (text[:30], message)
        assert word in message, (word, message)


def test_a_commented_out_entry_is_not_read():
    """`%` comments to the end of the line, as BibTeX's own does: a commented-out entry is the one way this scanner could find something nobody wrote."""
    text = "% @book{Ghost, title = {Nicht da}}\n@book{Real, title = {Da}, publisher = {P}, year = {2026}}\n"
    ok, out = _with_bib('#bib-note("Ghost")#bib-note("Real")\n#show-bibliography(data: false, project: "@BIB@")',
                        "bibliography_bib_comment", text)
    assert ok, out
    assert "Da" in out and "Nicht da" not in out, out
    # the ghost is still listed, as the citation it was, since no entry names it
    assert "Weitere Dokumente" in out and "Ghost" in out, out


def test_an_empty_bib_is_read_as_no_entry():
    """The template ships a references.bib of comments alone: a project that has written none still compiles."""
    ok, out = _with_bib('#bib-note("SIA 265")\n#show-bibliography(data: false, project: "@BIB@")',
                        "bibliography_bib_empty", "% nothing yet\n")
    assert ok, out
    assert "SIA 265:2021" in out, out


def test_the_template_ships_a_bib_and_names_it():
    """A new project's Sections/007 calls the command, and the file it names is there -- `read()` on a file that is not there is a report that does not compile."""
    report = ROOT / "templates" / "projet" / "Statischer Bericht (typst)"
    section = (report / "Sections" / "007-literatur.typ").read_text(encoding="utf-8")
    assert "show-bibliography" in section, "the template's Sections/007 does not print the bibliography"
    named = re.search(r'project:\s*"([^"]+)"', section)
    assert named, "the template's Sections/007 names no references.bib"
    assert (report / named.group(1)).is_file(), "the template names %s and does not ship it" % named.group(1)


def test_what_show_bibliography_refuses_it_names():
    for body, word in (('#show-bibliography(data: 1)', "data"),
                       ('#show-bibliography(project: 7)', "project"),
                       ('#show-bibliography(heading: "2")', "heading"),
                       ('#show-bibliography(blocks: "norm")', "blocks")):
        ok, message = _compile(body, "bibliography_refuse")
        assert not ok, body
        assert word in message and "show-bibliography" in message, (body, message)


def test_the_block_names_may_be_headings():
    ok, text = _compile('#bib-note("SIA 265")\n#show-bibliography(data: false, heading: 2)', "bibliography_heading")
    assert ok, text
    assert "Normen" in text and "SIA 265:2021" in text, text


# --- the documents the report templates cite and the library lacks (v0.111) --------------

# Thirteen SIA documents and seventeen VKF / AEAI directives, researched off the SIA shop's preview PDFs and the VKF's own covers, beside the three VKF directives that gained a German title: the catalogue now names forty-three documents.
ADDED_SIA = ("SIA 118", "SIA 180", "SIA 181", "SIA 181/1", "SIA 232/1", "SIA 262", "SIA 264", "SIA 266", "SIA 267",
             "SIA 271", "SIA 380/1", "SIA 414/2", "SIA 500")
ADDED_VKF = tuple("VKF %d-15" % n for n in (1, 10, 11, 12, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28))
REPLACED_VKF = ("VKF 13-15", "VKF 14-15", "VKF 15-15")
# what those three were cited by before they gained a German title: every one of these must still reach them
OLD_ALIASES = {
    "VKF 13-15": ("VKF13-15", "AEAI 13-15", "AEAI13-15"),
    "VKF 14-15": ("VKF14-15", "AEAI 14-15", "AEAI14-15"),
    "VKF 15-15": ("VKF15-15", "AEAI 15-15", "AEAI15-15"),
}


def test_the_catalogue_names_forty_three_documents_each_reached_by_its_key_and_its_alias():
    keys = [r["key"] for r in norms.references()]
    assert len(keys) == len(set(keys)) == 43, len(keys)
    for key in ADDED_SIA + ADDED_VKF + REPLACED_VKF:
        entry = norms.reference(key)
        assert entry is not None and entry["key"] == key, key
        assert entry["aliases"], "%s names no alias -- a citation may write its designation" % key
        for alias in entry["aliases"]:
            assert norms.reference(alias)["key"] == key, (key, alias)
    # what the engine already named is still there
    for key in ("SIA 260", "SIA 261", "SIA 261/1", "SIA 263", "SIA 265", "SIA 265/1", "SN EN 14592", "SZS C5", "STE Compact 02"):
        assert key in keys, key


def test_the_three_vkf_entries_that_were_replaced_gained_a_german_title_and_kept_everything_else():
    for key in REPLACED_VKF:
        entry = norms.reference(key)
        assert set(entry["title"]) == {"de", "fr"}, (key, entry["title"])
        assert entry["title"]["de"].strip() and entry["title"]["fr"].strip(), key
        # every way a citation could reach the old entry still does
        for alias in OLD_ALIASES[key]:
            assert norms.reference(alias)["key"] == key, (key, alias)
        assert entry["designation"] == "VKF / AEAI " + key.split(" ")[1], key
    assert norms.text(norms.reference("VKF 13-15"), "title", "fr") == "Matériaux et éléments de construction – Classification"
    assert norms.text(norms.reference("VKF 14-15"), "title", "fr") == "Utilisation des matériaux de construction"
    assert norms.text(norms.reference("VKF 15-15"), "title", "fr") == "Distances de sécurité incendie, systèmes porteurs et compartiments coupe-feu"
    assert norms.text(norms.reference("VKF 14-15"), "title", "de") == "Verwendung von Baustoffen"
    # the editions the library's French covers print are unchanged
    assert norms.reference("VKF 13-15")["edition"] == "01.01.2017 (état 14.12.2017)"
    assert norms.reference("VKF 14-15")["edition"] == "01.01.2017 (état 01.06.2023)"
    assert norms.reference("VKF 15-15")["edition"] == "01.01.2017 (état 18.09.2019)"


def test_every_added_entry_is_a_norm_with_its_four_fields_in_the_languages_the_document_has():
    for key in ADDED_SIA + ADDED_VKF:
        entry = norms.reference(key)
        assert entry["kind"] == "norm", key
        prefix = "SIA " if key.startswith("SIA") else "VKF / AEAI "
        assert entry["designation"].startswith(prefix), key
        assert entry["edition"].strip(), key
        # the publisher is given in the three languages, as every SIA entry and the VKF ones before them
        assert set(entry["publisher"]) == {"de", "fr", "en"}, (key, entry["publisher"])
        # a document printed in German and French at least says its title in both; English only where the edition exists (section 4bis)
        assert {"de", "fr"} <= set(entry["title"]), (key, entry["title"])
    for key in ADDED_VKF:
        assert set(norms.reference(key)["title"]) == {"de", "fr"}, "no English edition of a VKF directive exists"
    # SIA 262 is the 2025 edition, which replaces 2013: the old edition is deliberately no alias, so a template still citing it lands in «Weitere Dokumente» and is looked at
    assert norms.reference("SIA 262")["designation"] == "SIA 262:2025"
    assert norms.reference("SIA 262:2013") is None and norms.reference("SIA 262:2025") is not None


def test_every_source_names_a_page_to_turn_to_and_one_outside_the_library_says_where():
    """docs/architecture/principles.md §2 rule 13, read from the next most authoritative place where the library lacks the edition: a file of the library, or the publisher's own address -- never a bare «from the shop»."""
    for entry in norms.references():
        source = entry["_source"]
        assert ".pdf" in source or "ExternalFiles/" in source or "http" in source,             "%s: the _source names neither a file of the library nor an address" % entry["key"]
        if "Not in the reference library" in source:
            assert "http" in source, "%s is not in the library and its _source gives no address to read it from" % entry["key"]
    # what is outside the library is named as such, so that nothing passes for a page that can be turned to in the office's own copy
    outside = [e["key"] for e in norms.references() if "Not in the reference library" in e["_source"]]
    assert "SIA 118" in outside and "VKF 1-15" in outside, outside


def test_a_source_that_is_a_web_address_is_accepted_by_the_reader():
    """The reader asks that a `_source` be there and leaves its words to whoever checks: a publisher's own page is as good a page to turn to as a file name."""
    ok, message = _read_with([_entry(_source="https://shop.sia.ch/3131563f/D/DownloadAnhang, title page (p. 2)")])
    assert ok, message
    ok, message = _read_with([_entry(_source="   ")])
    assert not ok and "_source" in message, message


def test_a_german_report_prints_the_german_title_and_a_french_one_the_french():
    ok, text = _compile('#bib-note("VKF 14-15")#bib-note("VKF 13-15")\n#show-bibliography(data: false)', "bibliography_vkf_de")
    assert ok, text
    assert "Verwendung von Baustoffen" in text and "Baustoffe und Bauteile – Klassifikation" in text, text
    assert "Utilisation des mat" not in text, text
    ok, text = _compile('#set-report-language("fr")\n#bib-note("VKF 14-15")#bib-note("VKF 13-15")\n'
                        '#show-bibliography(data: false)', "bibliography_vkf_fr")
    assert ok, text
    assert "Utilisation des matériaux de construction" in text and "Matériaux et éléments de construction" in text, text
    assert "Verwendung von Baustoffen" not in text, text


def test_a_new_sia_entry_is_listed_in_three_languages_where_the_edition_has_them():
    ok, text = _compile('#bib-note("SIA 262")#bib-note("SIA 118")\n#show-bibliography(data: false)', "bibliography_sia_de")
    assert ok, text
    assert "SIA 262:2025" in text and "Betonbau" in text and "SIA 118:2013" in text, text
    assert "Allgemeine Bedingungen für Bauarbeiten" in text, text
    ok, text = _compile('#set-report-language("en")\n#bib-note("SIA 262")#bib-note("SIA 180")\n#show-bibliography(data: false)',
                        "bibliography_sia_en")
    assert ok, text
    assert "Concrete structures" in text and "Swiss Society of Engineers and Architects" in text, text
    # SIA 180 has no English edition: an English report prints the German title
    assert "Wärmeschutz, Feuchteschutz und Raumklima in Gebäuden" in text, text


def test_the_added_designations_are_sorted_with_their_supplements():
    """SIA 181/1 comes after SIA 181 and SIA 380/1 after SIA 271, as the colon-first sort key already puts SIA 261/1 after SIA 261 (section 13)."""
    body = "".join('#bib-note("%s")' % k for k in ("SIA 500", "SIA 181/1", "SIA 181", "SIA 118", "SIA 380/1"))
    ok, text = _compile(body + "\n#show-bibliography(data: false)", "bibliography_sia_order")
    assert ok, text
    order = [text.index(d) for d in ("SIA 118:2013", "SIA 181:2020", "SIA 181/1:2026", "SIA 380/1:2016", "SIA 500:2009")]
    assert order == sorted(order), order
