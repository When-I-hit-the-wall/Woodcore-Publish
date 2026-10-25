"""A translation that was never made, in either glossary.

There are two, and v0.59 settled that they stay two (docs/typst/language.md §4bis, docs/ui/window.md §10quater): `calc/i18n/strings.json` is what the *report* prints, read by Python and by Typst; the `STRINGS` dicts of the window's tab modules are what the *window* says. Measured against each other they share seven German strings out of 730 — the window says "Click an element to select it", the report says "Massgebend", and those are not the same words. Merging them would move 1 572 translations to save seven.

What neither had was a check that a translation *is* one. The window verifies that its three languages carry the same **keys**; nothing verifies that they carry different **text**. A block copied and half translated — the way this actually goes wrong — passes every check there is and is found by the engineer, in the window, in front of a client.

**Calibrating it is the whole difficulty**, and §14 said so before this existed: a naive comparison reports 107 entries, of which essentially all are words that are the same by nature ("Norm", "Position", "Plan", "Type", "Angle", "horizontal", "variable") or format strings with no words at all ("{w} × {h} {unit}"). A check whose output is 96 % noise is a check nobody runs twice.

So the signal is narrowed to where it is real: **a string of more than one word, and more than `MIN_WORDS` characters once its holes are removed, identical in two languages.** A single word is a cognate; a sentence is not. On the current tree that gives four hits, all four genuinely the same in both languages, and they are listed below — which is the point of a whitelist that has to be written by hand: an exception is one somebody looked at.
"""

import json
import re
import sys

import conftest
from conftest import ROOT
from i18n import strings as glossary

# Below this many characters of actual words, a string identical in two languages is a cognate rather than a missed translation. Calibrated against the tree as it stands (v0.59): 0 gives 31 hits, 12 gives 4, 25 gives none. 12 keeps every real sentence in range while dropping every one-word cognate.
MIN_WORDS = 12

# Strings that really are the same in two of the three languages. Each was looked at; add to it only after looking.
SAME_IN_TWO_LANGUAGES = {
    "vertical + horizontal",          # fr/en
    "x = {x} m   z = {z} m",          # a coordinate readout: no words at all
    "Compression ∥",                  # fr/en: a strength of a member, the «Matériaux» tab (issue #110)
    "Compression ⊥",
    "γ_M = {g} · η_mod = {e}",        # SIA 265/1's two factors: symbols alone
}

_HOLE = re.compile(r"\{\w+\}")


def _words(text):
    """The text with its {holes} removed -- what is left is what a translator would have had to translate."""
    return _HOLE.sub("", text).strip()


def _twins(table, languages):
    """[(key, a, b, text), ...] for every entry whose text is the same in two languages and long enough to be a sentence."""
    out = []
    for key, entry in table.items():
        for i, a in enumerate(languages):
            for b in languages[i + 1:]:
                if a not in entry or b not in entry or entry[a] != entry[b]:
                    continue
                text = entry[a]
                if text in SAME_IN_TWO_LANGUAGES:
                    continue
                bare = _words(text)
                if len(bare) > MIN_WORDS and " " in bare:
                    out.append((key, a, b, text))
    return out


def _report(twins, where):
    if not twins:
        return
    lines = [f"  {key!r} — the {a} and the {b} are word for word the same:\n      {text!r}"
             for key, a, b, text in twins]
    raise AssertionError(
        f"{where}: {len(twins)} entries look like a translation that was never made.\n"
        + "\n".join(lines)
        + "\n\nTranslate it, or -- if it really is the same sentence in both languages -- "
          "add the text to SAME_IN_TWO_LANGUAGES in this file."
    )


def _glossary():
    return json.loads((ROOT / "calc" / "i18n" / "strings.json").read_text(encoding="utf-8"))


def _window_module():
    sys.path.insert(0, str(ROOT / "calc" / "tools"))
    try:
        import woodcore_gui
    except ImportError as exc:
        raise conftest.Skip(f"the window cannot be imported here ({exc})")
    return woodcore_gui


def test_the_reports_glossary_is_translated():
    """strings.json's `engine` and `templates` blocks: what the engine prints of its own accord."""
    data = _glossary()
    languages = list(data["languages"])
    _report(_twins(data["engine"], languages) + _twins(data["templates"], languages), "strings.json")


def test_the_reports_terms_are_translated():
    """The `terms` block is keyed by the German the export carries, so a French entry equal to its own key is a term copied rather than translated.

    Held to the same threshold: `Kerto-Q` and `gk` are the same word in every language, a sentence is not.
    """
    data = _glossary()
    bad = []
    for german, entry in data["terms"].items():
        bare = _words(german)
        if len(bare) <= MIN_WORDS or " " not in bare or german in SAME_IN_TWO_LANGUAGES:
            continue
        for lang, text in entry.items():
            if text == german:
                bad.append(f"  {german!r}\n      the {lang} is still the German")
    assert not bad, (
        "strings.json, terms: entries left in German.\n" + "\n".join(bad)
        + "\n\nTranslate it, or add it to SAME_IN_TWO_LANGUAGES here."
    )


def test_the_window_is_translated():
    """The window's own STRINGS, merged from its tab modules."""
    woodcore_gui = _window_module()
    languages = list(woodcore_gui.LANGUAGES)
    table = {
        key: {lang: woodcore_gui.STRINGS[lang][key] for lang in languages}
        for key in woodcore_gui.STRINGS[languages[0]]
    }
    _report(_twins(table, languages), "the window's STRINGS")


def test_the_window_carries_the_same_keys_in_every_language():
    """The window checks this at import; restated here so a run of the suite says so, rather than the window failing to open in front of somebody."""
    woodcore_gui = _window_module()
    languages = list(woodcore_gui.LANGUAGES)
    reference = set(woodcore_gui.STRINGS[languages[0]])
    for lang in languages[1:]:
        keys = set(woodcore_gui.STRINGS[lang])
        assert keys == reference, (
            f"STRINGS[{lang!r}] differs: missing {sorted(reference - keys)}, "
            f"extra {sorted(keys - reference)}"
        )


def test_every_glossary_entry_carries_every_language():
    """No entry is short of a language -- which would surface as a KeyError the day someone switches to it."""
    data = _glossary()
    languages = set(data["languages"])
    for block in ("engine", "templates"):
        for key, entry in data[block].items():
            missing = languages - set(entry)
            assert not missing, f"strings.json, {block}.{key}: no {', '.join(sorted(missing))}"
    for german, entry in data["terms"].items():
        # terms are keyed by their German, so that language is the key and not a field
        missing = (languages - {"de"}) - set(entry)
        assert not missing, f"strings.json, terms.{german!r}: no {', '.join(sorted(missing))}"


def test_every_phrase_typst_translates_is_a_term():
    """Every literal phrase lib/*.typ hands to `tl-str` is a key of `terms`: a phrase missing there prints its German in a French or English report, silently (v0.117, the review of the module «Flexion»). A phrase built at run time -- `tl-str(words)` -- is not seen here; the literal it comes from is."""
    terms = _glossary()["terms"]
    for typ in sorted((ROOT / "lib").glob("*.typ")):
        for literal in re.findall(r'tl-str\("((?:[^"\\]|\\.)*)"\)', typ.read_text(encoding="utf-8")):
            phrase = literal.replace('\\"', '"')
            assert phrase in terms, f"lib/{typ.name}: tl-str({phrase!r}) is no term of calc/i18n/strings.json -- it prints in German in every language"


def test_the_glossary_holds_what_python_and_typst_expect():
    """Both readers declare the language list; strings.json must agree with both."""
    data = _glossary()
    typ = (ROOT / "lib" / "i18n.typ").read_text(encoding="utf-8")
    assert list(data["languages"]) == list(glossary.LANGUAGES), (
        f"strings.json declares {data['languages']}, calc/i18n/strings.py expects {list(glossary.LANGUAGES)}"
    )
    for lang in data["languages"]:
        assert f'"{lang}"' in typ, f"lib/i18n.typ does not know the language {lang!r}"


def test_the_export_checks_the_glossary_before_it_reads_anything():
    """A defect in strings.json stops the export whatever the project holds. It was checked only when a figure asked the glossary for a word, so a project with no connector, connection, plan, model or schema exported a broken glossary without a word (periodic audit 260916, AUD-7-210).

    Nothing is read or written: the workbook reader is replaced by one that says it was reached, and the glossary by a copy with one French term emptied.
    """
    import export_all
    import positions_store
    import validation
    broken = json.loads(glossary.STRINGS_FILE.read_text(encoding="utf-8"))
    first = next(iter(broken["terms"]))
    broken["terms"][first]["fr"] = ""
    copy = conftest.tmpdir("glossary") / "strings.json"
    copy.write_text(json.dumps(broken, ensure_ascii=False), encoding="utf-8")

    class Reached(Exception):
        pass

    def reader(*_args, **_kwargs):
        raise Reached()

    # the first thing the export reads after the glossary is the project's positions (calc/positions_store.py, v0.114; Positionen.xlsx through io_excel until then)
    saved = (glossary.STRINGS_FILE, glossary._cache, positions_store.migrate)
    glossary.STRINGS_FILE, glossary._cache, positions_store.migrate = copy, None, reader
    try:
        export_all.run()
    except validation.ValidationError as exc:
        assert "is empty" in str(exc), exc
    except Reached:
        raise AssertionError("the export read the positions before checking the glossary")
    else:
        raise AssertionError("the export ran on a defective glossary")
    finally:
        glossary.STRINGS_FILE, glossary._cache, positions_store.migrate = saved


# --- what a connector says, in the three languages (periodic audit 260916) -------------

GERMAN_WORDS = ("gilt", "unterschritten", "Gleichung", "Tabelle", "Scherfuge", "Bauteil", "vorhanden", "verlangt")


def test_a_connectors_warnings_and_k_beta_rows_are_translated():
    """Four warnings of a Stabdübel connection and one of a connector had no template, so a French or English report printed them in German from level 2; and the k_beta rows of a steel-to-timber joint read «Scherfuge A (2×)», or «Scherfuge Scherfuge (2×)» for outer plates, in every language (AUD-3-3, AUD-3-4). Each is produced here by the code that writes it."""
    from domains import connector, dowel
    from test_dowel import HOLZ_HOLZ, STAHL_HOLZ, _member

    pattern = [{"x": -60, "z": -60}, {"x": 60, "z": -60}, {"x": -60, "z": 60}, {"x": 60, "z": 60}]
    texts = list(dowel.check_spacings(pattern, 45.0, 0)["warnings"])                  # both directions
    texts += dowel.analyse(dict(HOLZ_HOLZ, d=36.0))["warnings"]                        # d outside 6..30 mm
    for ratio in (0.9, 0.2):                                                           # equations (130), (131)
        texts += dowel.analyse(dict(STAHL_HOLZ, steel=dict(STAHL_HOLZ["steel"], ratio=ratio)))["warnings"]
    source = connector.new_source("X_1")
    source["assembly"], source["diameter"] = "Holz-Holz zweischnittig", {"value": 12, "unit": "mm"}
    for member in source["members"]:
        member["element"], member["material"] = "", None
    texts += connector.build_record(source, {}, None)[0]["warnings"][:1]                 # a member with no element, as the record carries it
    # v0.84: the k_beta table is gone -- what names a shear plane on the page now is the label under
    # each curve of the plate of figures, so that is what has to translate. The step *names* are checked
    # for the doubled word too and for nothing else: no surface prints a step's name (show-calc renders
    # its formula, section 10bis), so they carry no glossary entry and none is expected of them.
    rows, internal = [], []
    for assembly in ("Stahl-Holz, Schlitzbleche", "Stahl-Holz, Bleche aussen"):
        inputs = dict(STAHL_HOLZ, assembly=assembly)
        if assembly.endswith("aussen"):
            inputs["members"] = [_member(alpha=90, t=44, n=3, a_1=60)]
        result = dowel.analyse(inputs)
        rows += [curve["label"] for curve in dowel._k_beta_figures(result)["curves"]]
        internal += [st["name"] for st in dowel.record("X_1", result, inputs["members"])["steps"]
                     if "Scherfuge" in st["name"]]
    assert len(texts) >= 6 and rows and internal, (texts, rows, internal)
    assert not [r for r in rows + internal if r.count("Scherfuge") > 1], rows + internal
    for text in texts + rows:
        for lang in ("fr", "en"):
            translated = glossary.translate(text, lang)
            assert not any(word in translated for word in GERMAN_WORDS), f"{lang}: {text!r} -> {translated!r}"


def test_the_exposure_choices_are_the_norms_words():
    """The three C_e choices are SIA 261:2020 5.2.4's own words, and its French edition gives them (p. 26): a French report printed «dem Wind stark ausgesetzte Lage» (AUD-3-5)."""
    for german in ("normale Windexposition", "dem Wind stark ausgesetzte Lage", "vor Wind geschützte Lage"):
        assert glossary.translate(german, "fr") != german, german


def test_the_french_and_english_wording_is_consistent():
    """SIA 265 FR says «moyen d'assemblage», never «organe» (AUD-3-10); English writes «predrilled» one way (AUD-3-11); and a French colon or semicolon takes the narrow no-break space `t-label` already sets (AUD-3-12)."""
    data = json.loads(glossary.STRINGS_FILE.read_text(encoding="utf-8"))
    entries = [entry for block in ("engine", "templates", "terms") for entry in data[block].values()]
    french = [e["fr"] for e in entries]
    english = [e["en"] for e in entries]
    assert not [t for t in french if re.search(r"organes? d.assemblage", t, re.IGNORECASE)]
    assert not [t for t in english if "pre-drill" in t.lower()]
    # \u00ab\u00c9ch. env. 1:\u00bb is a scale the number follows, not a colon
    glued = [t for t in french if re.search(r"[^\s\u202f\u00a0][;:](\s|$)", re.sub(r"\d:$", "", re.sub(r"\$[^$]*\$", "", t)))]
    assert not glued, glued


def test_the_windows_labels_carry_no_norm_value_and_name_an_id_one_way():
    """η_t = 1,4 and × 0,75 were written into the labels of «Connecteurs» in three languages, SIA 265's values a second time (AUD-6-12); «Moments polaires» called its ID «Identifiant / Kennung / Id» beside every other tab's «ID» (AUD-4-8), and refused one naming a «Variante» that left in v0.76 (AUD-6-9). Periodic audit 260916."""
    woodcore_gui = _window_module()
    for lang in woodcore_gui.LANGUAGES:
        s = woodcore_gui.STRINGS[lang]
        assert not re.search(r"1[.,]4|0[.,]75", s["cn_seismic"] + s["cn_truss"]), (lang, s["cn_seismic"], s["cn_truss"])
        assert s["polar_id"] == s["idn_id"], (lang, s["polar_id"], s["idn_id"])
        assert "Variant" not in s["polar_id_invalid"], (lang, s["polar_id_invalid"])


def test_a_connectors_reasons_and_uncovered_assemblies_are_translated():
    """A connector of a kind with no module, one with no marker ticked, and the three assemblies SIA 265 gives no k_beta for said so in German in every language of the window (periodic audit 260916, AUD-4-4, AUD-4-5)."""
    from domains import connector, dowel
    texts = list(dowel.UNCOVERED_ASSEMBLIES.values())
    source = connector.new_source("X_2")
    source["type"] = "Nagel"
    texts.append(connector.build_record(source, {}, None)[0]["reason"])
    source = connector.new_source("X_3")
    source["assembly"], source["fasteners"] = "Holz-Holz zweischnittig", []
    texts.append(connector.build_record(source, {}, None)[0]["reason"])
    for text in texts:
        for lang in ("fr", "en"):
            translated = glossary.translate(text, lang)
            assert translated != text and "für" not in translated and "gibt" not in translated, f"{lang}: {text!r} -> {translated!r}"


def _window(lang):
    """The window, off-screen, in `lang`. None where PySide6 is not installed."""
    import os
    tools = str(ROOT / "calc" / "tools")
    if tools not in sys.path:
        sys.path.insert(0, tools)
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError as exc:
        raise conftest.Skip(f"PySide6 is not installed ({exc})")
    QApplication.instance() or QApplication([])
    import woodcore_gui
    window = woodcore_gui.MainWindow()
    window.lang = lang
    return window


def test_an_unreadable_schema_and_the_plan_background_dialog_speak_the_window_s_language():
    """A schema file that cannot be read put Python's raw message in the status line, with no sentence and no file name, where the other editors say «<name> est illisible» (periodic audit 260916, AUD-4-6); and the background dialog's filter read «Plans (*.pdf …)» in a German window (AUD-4-7)."""
    window = _window("fr")
    from PySide6.QtWidgets import QFileDialog
    import schema_tab
    tab = next(t for t in window.tabs if type(t).__name__ == "SchemaTab")
    import project
    root = conftest.tmpdir("unreadable_schema")
    (root / "details").mkdir()
    (root / "details" / "P4-Bad.json").write_text("{ not json", encoding="utf-8")
    with project.using(project.write(root / "Bad.woodcore", "Bad", {"sources": "."})):
        tab.load("P4-Bad")
        assert window.status.text().startswith("P4-Bad.json est illisible"), window.status.text()
    plan = next(t for t in window.tabs if type(t).__name__ == "PlanTab")
    seen = []
    original = QFileDialog.__dict__["getOpenFileName"]
    QFileDialog.getOpenFileName = staticmethod(lambda *a, **k: (seen.append(a[3]), ("", ""))[1])
    try:
        window.lang = "de"
        plan.import_document()     # the plan tab's «Importer…» (v0.114), whose dialog was «Choisir…»'s
    finally:
        QFileDialog.getOpenFileName = original
    assert seen and seen[0].startswith("Plandokumente"), seen
    conftest.dispose(window)
def test_qt_s_own_buttons_speak_the_window_s_language():
    """No QTranslator was installed, so every «unsaved changes» question read Save / Discard / Cancel and every confirmation &Yes / &No in a French or German window (periodic audit 260916, AUD-4-2). PySide6 ships qtbase_<lang>.qm; the window installs it at start and at each change of language."""
    window = _window("en")
    from PySide6.QtWidgets import QMessageBox
    import woodcore_gui
    buttons = QMessageBox.StandardButton
    try:
        for lang, save, cancel in (("fr", "Enregistrer", "Annuler"), ("de", "Speichern", "Abbrechen"), ("en", "Save", "Cancel")):
            window.language.setCurrentIndex(list(woodcore_gui.LANGUAGES).index(lang))
            box = QMessageBox(QMessageBox.Icon.Question, "", "", buttons.Save | buttons.Discard | buttons.Cancel)
            got = (box.button(buttons.Save).text(), box.button(buttons.Cancel).text())
            assert got == (save, cancel), f"{lang}: {got}"
    finally:
        conftest.dispose(window)
def _window_strings_named():
    """(defined, dead): every key the window's STRINGS dicts define, by module, and those no code of calc/tools names -- neither as a string literal outside a STRINGS dict, nor as the start of one composed (`"st_snap_" + kind`, `f"cn_type_{kind}"`)."""
    import ast
    tools = ROOT / "calc" / "tools"
    defined, literals, prefixes = {}, set(), set()
    for path in sorted(tools.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        ranges = []
        for node in tree.body:
            if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "STRINGS" for t in node.targets):
                ranges.append((node.lineno, node.end_lineno))
                if isinstance(node.value, ast.Dict):
                    for per_language in node.value.values:
                        if isinstance(per_language, ast.Dict):
                            for key in per_language.keys:
                                if isinstance(key, ast.Constant):
                                    defined.setdefault(key.value, path.name)
        for node in ast.walk(tree):
            line = getattr(node, "lineno", 0)
            if any(a <= line <= b for a, b in ranges):
                continue
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                literals.add(node.value)
            elif isinstance(node, ast.JoinedStr) and node.values and isinstance(node.values[0], ast.Constant):
                prefixes.add(node.values[0].value)
            elif isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add) and isinstance(node.left, ast.Constant) and isinstance(node.left.value, str):
                prefixes.add(node.left.value)
    # the Qt-free models of a tab under calc/ name the keys of its words the tab then says (the «Variables» tab's card and tags, issue #114, ARCH-001: «Vient de» and what to include, in keys of the window's words)
    for path in sorted((ROOT / "calc").glob("variable_*.py")):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                literals.add(node.value)
            elif isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add) and isinstance(node.left, ast.Constant) and isinstance(node.left.value, str):
                prefixes.add(node.left.value)
    # a tab of sources names its list's words by its prefix and the suffixes of its base (source_editor.WORD_SUFFIXES, spec 2026-10-19-base-saine-nettoyage)
    editor = ast.parse((tools / "source_editor.py").read_text(encoding="utf-8"))
    suffixes = next(ast.literal_eval(n.value) for n in editor.body if isinstance(n, ast.Assign) and any(getattr(t, "id", None) == "WORD_SUFFIXES" for t in n.targets))
    for path in sorted(tools.glob("*.py")):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Assign) and any(getattr(t, "id", None) == "WORDS" for t in node.targets) and isinstance(node.value, ast.Constant) and node.value.value:
                literals.update(f"{node.value.value}_{suffix}" for suffix in suffixes)
            elif isinstance(node, ast.Assign) and isinstance(node.value, ast.Tuple) and any(isinstance(t, ast.Tuple) and any(getattr(e, "id", None) == "WORDS" for e in t.elts) for t in node.targets):
                for target in node.targets:
                    for name, value in zip(target.elts, node.value.elts):
                        if getattr(name, "id", None) == "WORDS" and isinstance(value, ast.Constant) and value.value:
                            literals.update(f"{value.value}_{suffix}" for suffix in suffixes)
    # a tab of calculation names its domain's words by the prefix the domain declares (calc/domains/contracts.py `Declaration.prefix`), composed by the base -- `<prefix>f_<key>`, `<prefix>msg_<code>` (spec 2026-10-22-onglet-neige-type, ARCH-002)
    for path in sorted((ROOT / "calc" / "domains").glob("*.py")):
        for node in ast.parse(path.read_text(encoding="utf-8")).body:
            if isinstance(node, ast.Assign) and any(getattr(t, "id", None) == "PREFIX" for t in node.targets) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                prefixes.add(node.value.value)
    # a tab that names its own prefix (`PREFIX = "ld_"`, the dead load's, whose domain declares none) gets the words the base composes with it -- `ctx.prefix() + "module_drawing"` (calc_modules) -- and those only (spec 2026-10-23-onglet-vent-briques, V5: load_tab.py, which named them, gone)
    tab_prefixes, composed, tab_words, named = set(), set(), set(), set()
    for path in sorted(tools.glob("*.py")):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.ClassDef):
                tab_prefixes.update(n.value.value for n in node.body if isinstance(n, ast.Assign) and any(getattr(t, "id", None) == "PREFIX" for t in n.targets) and isinstance(n.value, ast.Constant) and isinstance(n.value.value, str))
                tab_words.update(n.value.value for n in node.body if isinstance(n, ast.Assign) and any(getattr(t, "id", None) == "WORDS" for t in n.targets) and isinstance(n.value, ast.Constant) and isinstance(n.value.value, str) and n.value.value)
            elif isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add) and isinstance(node.right, ast.Constant) and isinstance(node.right.value, str) and isinstance(node.left, ast.Call) and getattr(node.left.func, "attr", None) == "prefix":
                composed.add(node.right.value)
            elif isinstance(node, ast.Call) and getattr(node.func, "attr", None) == "word" and node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                named.add(node.args[0].value)
    literals.update(p + suffix for p in tab_prefixes for suffix in composed)
    # and the sentences that name its object, `self.word("saved")` read as `<WORDS>_saved` (tab_host.TabHost.word, D-12): CalcTab's `WORDS = "ld"`
    literals.update(f"{w}_{suffix}" for w in tab_words for suffix in named)
    dead = sorted((module, key) for key, module in defined.items()
                  if key not in literals and not any(len(p) >= 3 and key.startswith(p) for p in prefixes))
    return defined, dead


def test_every_window_string_is_named_by_code():
    """A key of the window's STRINGS that no code names is a sentence translated three times for nothing, and one somebody will correct in the wrong place: 40 of them were left by the forms v0.70 to v0.77 retired (periodic audit 260916, AUD-6-10)."""
    defined, dead = _window_strings_named()
    assert defined, "no STRINGS dict was found under calc/tools"
    assert not dead, f"{len(dead)} key(s) of STRINGS named by no code:\n  " + "\n  ".join(f"{m}: {k}" for m, k in dead)


def test_the_window_never_says_katalog():
    """«Katalog» is German, and the window is Woodcore in all three languages since v0.96, the engineer's decision: no sentence of a STRINGS dict under calc/tools, no title of a message box and no message of the launcher names the Katalog -- eleven boxes were still titled «Typst-Katalog». What is left of the word is never shown: the folder `typst-katalog` and the project file's `katalog` key, both still read (usersettings.OLD_NAME, project.KATALOG_KEY)."""
    import ast
    said = []
    for path in sorted((ROOT / "calc" / "tools").glob("*.py")):
        text = path.read_text(encoding="utf-8")
        for node in ast.parse(text).body:
            if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "STRINGS" for t in node.targets):
                said += [f"{path.name}:{sub.lineno}: {sub.value[:90]}" for sub in ast.walk(node.value)
                         if isinstance(sub, ast.Constant) and isinstance(sub.value, str) and "katalog" in sub.value.lower()]
        said += [f"{path.name}:{number}: {line.strip()[:90]}" for number, line in enumerate(text.splitlines(), 1)
                 if re.search(r'QMessageBox\b.*"[^"]*Katalog', line)]
    if str(ROOT / "packaging") not in sys.path:
        sys.path.insert(0, str(ROOT / "packaging"))
    import launcher
    said += [f"launcher.MESSAGES[{lang}][{key}]" for lang, table in launcher.MESSAGES.items() for key, text in table.items() if "katalog" in text.lower()]
    assert not said, "the window still says «Katalog»:\n  " + "\n  ".join(said)


def test_a_choice_the_norm_names_is_translated_inside_the_sentence_that_quotes_it():
    """«Gewählte Windexposition: normale Windexposition.» printed «Exposition au vent choisie : normale Windexposition.» in a French report: the template was matched, and its hole, which holds SIA 261's own word for the exposure, was put back in German (periodic audit 260916, AUD-3-9). A template names in `translate` the holes that carry a norm's word, and both readers pass those through the glossary's terms -- a sheet's name or a number in another hole is left as it is."""
    import subprocess
    german = "Gewählte Windexposition: normale Windexposition."
    french = "Exposition au vent choisie\u202f: exposition au vent normale."
    wanted = glossary.template("snow.exposure_desc", "fr", exposure="exposition au vent normale")
    assert glossary.translate(german, "fr") == wanted, glossary.translate(german, "fr")
    assert glossary.translate(german, "en") == "Chosen wind exposure: normal wind exposure."
    assert glossary.translate("Gewählte Windexposition: SL-Dach1.", "fr").endswith("SL-Dach1."), "a capture the glossary does not carry must be left as it is"
    assert wanted.replace("\u202f", " ") == french.replace("\u202f", " ")
    if not conftest.have_typst():
        return
    probe = conftest.probe_dir("i18n") / "probe.typ"
    probe.write_text('#import "/000-Typst-Config/commands.typ": *\n#metadata(tl-of("fr", "%s")) <out>\n' % german, encoding="utf-8")
    out = subprocess.run(["typst", "query", "--root", str(conftest.TYPST_ROOT), str(probe), "<out>", "--field", "value", "--one"],
                         capture_output=True, text=True, encoding="utf-8")
    assert out.returncode == 0, out.stderr
    assert json.loads(out.stdout) == wanted, "lib/i18n.typ's tl-of does not translate the hole as strings.py does: %s" % out.stdout


def test_where_a_members_strength_class_came_from_is_translated_sentence_by_sentence():
    """The note under «Lochleibungsfestigkeit» was one string whose template kept a hole for where each piece's strength class came from -- «Bauteil 1: C24, aus Position T001; Bauteil 2: GL32h, im Verbindungsmittel festgelegt (Position S001: GL24h)» -- and a hole is put back as it is, so a French report printed that half in German (periodic audit 260916, AUD-3-7). It became a list of sentences, each a term or a template.

    v0.84: that table is gone, its numbers written out as Tabelle 22's own formulas, and each sentence is now the description of the member's own rho_k -- one sentence about one var, which is where it belonged. The rule it was written for is unchanged and is what is checked here: every one of them translates whole.
    """
    from domains import connector
    from test_connectors import DETAIL, _detail, _record, _source
    positions = {"T001": {"material": "C24", "moisture_class": 2}, "S001": {"material": "GL24h", "moisture_class": 1}}
    blank = dict(positions, S001={"strength_class": "", "material": "Fichte", "moisture_class": 1})
    follow = _source()
    follow["members"][0]["material"] = None                      # C24, aus Position T001
    follow["members"][1]["material"] = {"grade": "GL32h"}        # im Verbindungsmittel festgelegt (Position S001: GL24h)
    empty = _source()
    empty["members"][1]["material"] = {"grade": "GL32h"}         # ... (Position S001: ohne Festigkeitsklasse)
    stated = _source()                                           # no position on either element
    notes = []
    for source, positions_, detail in ((follow, positions, DETAIL), (empty, blank, DETAIL), (stated, {}, _detail(positions=(None, None)))):
        record, _warnings = _record(source, positions_, detail)
        said = [v["description"] for name, v in record["vars"].items()
                if name.startswith("rho_k_") and "description" in v]
        assert len(said) >= 2, said
        notes += said
    assert any("aus Position" in n for n in notes) and any("(Position" in n for n in notes) and any(n.endswith("festgelegt.") for n in notes) and any("ohne Festigkeitsklasse" in n for n in notes), notes
    for sentence in notes:
        for lang in ("fr", "en"):
            translated = glossary.translate(sentence, lang)
            assert translated != sentence and not any(word in translated for word in GERMAN_WORDS + ("aus Position", "festgelegt", "ohne Festigkeitsklasse")), f"{lang}: {sentence!r} -> {translated!r}"


def test_auflast_is_sia_261_s_non_structural_self_weight():
    """«Auflast» was translated «Charge permanente» and «Superimposed load»; SIA 261:2020 names it in its own Tabelle 80 (p. 131) «Poids propre non-structural» and «Non-structural self-weight», and its chapter 2 is headed «Poids propres de la structure porteuse et des éléments non-structuraux» (periodic audit 260916, AUD-3-9)."""
    assert glossary.term("Auflast", "fr") == "Poids propre non-structural"
    assert glossary.term("Auflast", "en") == "Non-structural self-weight"
    assert glossary.term("Auflast (Flächenlast)", "fr").startswith("Poids propre non-structural")
    assert glossary.term("Eigen- und Auflasten", "fr") == "Poids propres de la structure porteuse et des éléments non-structuraux"
    assert "non-structural self-weight" in glossary.term("Eigen- und Auflasten", "en")


def test_the_editors_warnings_speak_the_window_s_language():
    """The warnings under a plan, a static model, a schema and a polar moment were the export's English sentences in all three languages of the window (periodic audit 260916, AUD-4-11). Each is a `engine.Note` now -- the English sentence the export prints, and a code with its values -- and the window writes its own sentence for the code, the arrangement `schema.Refused` has for a refusal. A `ValidationError` stays English: it is a defect in a file, for whoever repairs the file."""
    import engine
    from domains import connection, plan, schema, statics
    woodcore_gui = _window_module()

    notes = []
    p = plan.new_source("P1")
    p["crop"] = {"x": 0, "y": 0, "w": 400, "h": 400}
    p["elements"] = [
        {"type": "T", "label": "", "points": [[10, 10], [60, 10]]},
        {"type": "T", "label": "T999", "points": [[10, 20], [60, 20]]},
        {"type": "T", "label": "S001", "points": [[10, 30], [60, 30]]},
        {"type": "T", "label": "T001", "points": [[900, 900], [960, 900]]},
        {"type": "T", "label": "T001", "points": [[10, 40], [60, 40]], "label_offset": [2000, 0]},
    ]
    notes += plan.warnings(p, ["T001", "S001"])

    s = statics.new_source("R1")
    s["points"] = [{"id": "P1", "x": 0, "z": 0}, {"id": "P2", "x": 4, "z": 0}, {"id": "P3", "x": 9, "z": 9}]
    s["members"] = [{"id": "B1", "kind": "bar", "p1": "P1", "p2": "P2"}]
    s["releases"] = [{"id": "G1", "member": "B1", "end": "start", "dof": "shear", "stiffness": 5}]
    s["line_loads"] = [{"id": "q1", "member": "B1", "from": 0, "to": 1, "shape": "uniform", "direction": "vertical",
                        "magnitude": {"domain": "snow-load", "instance": "NOPE", "var": "q_k"}, "label": "q", "show": "value"}]
    notes += statics.drop_release_stiffness(s, "model R1")
    notes += statics.warnings(s, {})

    d = schema.new_source("S1")
    d["crop"] = {"x": 1000, "z": 1000, "w": 10, "h": 10}
    d["elements"] = [{"id": "E1", "kind": "linear", "points": [[0, 0], [100, 0]], "view": "h", "position": "D001"},
                     {"id": "E2", "kind": "linear", "points": [[0, 50], [100, 50]], "view": "h"},
                     {"id": "E3", "kind": "linear", "points": [[0, 90], [100, 90]], "view": "h", "position": "X404"}]
    d["connectors"] = [{"id": "C1", "kind": "Stabdübel", "x": 0, "z": 0}]
    notes += schema.warnings(d, {"D001": {"dimension": "180", "units": "mm", "strength_class": "C24"}})

    c = connection.new_source("A1")
    notes += connection.schema_warnings(c, None, {}, "A1")
    c["schema"] = "GONE"
    notes += connection.schema_warnings(c, None, {"S1": d}, "A1")

    codes = {getattr(n, "code", None) for n in notes}
    assert None not in codes, [n for n in notes if not isinstance(n, engine.Note)]
    assert len(codes) >= 14, sorted(codes)
    for note in notes:
        for lang in woodcore_gui.LANGUAGES:
            text = woodcore_gui.note_text(note, lang)
            assert "{" not in text and " -- " not in text, (lang, note.code, text)
            if lang != "en":
                assert text != str(note), (lang, note.code, text)
        assert not any(w in woodcore_gui.note_text(note, "fr") for w in (" is ", " the ", " not ", " of ")), (note.code, woodcore_gui.note_text(note, "fr"))


# The labels that name the level of detail -- `level:` --, by module and key: issue #20 has the French call it «Niveau de détail» everywhere. A «Niveau» that is not the level of detail stays (the storey, a heading's level, the level a load is carried at).
DETAIL_LEVEL_LABELS = {
    "display_options.py": ("ds_opt_level",),
    "variables_words.py": ("vr_level",),
    "journal_tab.py": ("jo_levels",),
    "woodcore_gui.py": ("pdf_base_level", "pdf_uniform_level"),
}


def _module_strings(name):
    """The STRINGS dict of calc/tools/<name>, read off its source -- no Qt imported."""
    import ast
    tree = ast.parse(conftest.module_source(ROOT / "calc" / "tools" / name))   # with the parts split out of it (issue #30)
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "STRINGS" for t in node.targets):
            return ast.literal_eval(node.value)
    raise AssertionError(f"{name} has no STRINGS")


def test_the_level_of_detail_is_niveau_de_detail_in_french_everywhere():
    """Issue #20: «Niveau de détail» in French wherever the window or the commands' reference names the level of detail -- «Detailstufe» and «Level of detail» beside it --, and the storey, which the issue's own pointer named, is still «Niveau»."""
    wrong = []
    for module, keys in DETAIL_LEVEL_LABELS.items():
        table = _module_strings(module)
        for key in keys:
            if not table["fr"][key].startswith("Niveau de détail") and "niveau de détail" not in table["fr"][key]:
                wrong.append(f"{module} {key}: {table['fr'][key]!r}")
            if "Detailstufe" not in table["de"][key]:
                wrong.append(f"{module} {key} (de): {table['de'][key]!r}")
            if "level of detail" not in table["en"][key].lower():
                wrong.append(f"{module} {key} (en): {table['en'][key]!r}")
    reference = json.loads((ROOT / "calc" / "i18n" / "reference.json").read_text(encoding="utf-8"))
    level = next(value for key, value in _walk(reference) if key == "level")
    if level != {"fr": "Niveau de détail", "de": "Detailstufe", "en": "Level of detail"}:
        wrong.append(f"reference.json level: {level}")
    assert not wrong, "the level of detail is not named so:\n  " + "\n  ".join(wrong)
    assert glossary.text("document.storey", "fr") == "Niveau", "the storey is a «Niveau», not a level of detail"


def _walk(node):
    """(key, value) of every entry of a nested JSON object."""
    if isinstance(node, dict):
        for key, value in node.items():
            yield key, value
            yield from _walk(value)


def test_the_words_of_a_calculation_tab_take_no_key_of_another_module():
    """ARCH-RISK-W07 of spec 2026-10-22-onglet-neige-type: woodcore_gui_words merges every module's STRINGS by `update`, the last one winning without a word -- the calculation tabs' base (ct_) and the snow's (sn_), and every tab built on the base after them, take no key another module of the window already has."""
    import importlib
    tools = ROOT / "calc" / "tools"
    if str(tools) not in sys.path:
        sys.path.insert(0, str(tools))
    source = (tools / "woodcore_gui_words.py").read_text(encoding="utf-8")
    names = {n for n in re.findall(r"for _lang, _texts in (\w+)\.STRINGS\.items\(\)", source) if not n.startswith("_")}   # a loop's own variable is no module
    for group in re.findall(r"for _module in \(([^)]*)\)", source):
        names |= {n.strip() for n in group.split(",") if n.strip()}
    words = importlib.import_module("woodcore_gui_words")
    names |= {m.__name__ for m in words.SERVICE_WORDS}   # the registry of the services' words (spec 2026-10-23-onglets-types-et-services, ARCH-008)
    new = {"calc_tab_words", "snow_tab_words"} | {m.__name__ for m in words.SERVICE_WORDS}
    assert new <= names, names
    own = {name: set(getattr(words, name).STRINGS["fr"]) for name in names if hasattr(getattr(words, name, None), "STRINGS")}   # each as woodcore_gui_words names it
    base = set(words.STRINGS["fr"]) - set().union(*own.values())
    for name in new:
        others = base.union(*(keys for other, keys in own.items() if other != name))
        assert not own[name] & others, (name, sorted(own[name] & others))
