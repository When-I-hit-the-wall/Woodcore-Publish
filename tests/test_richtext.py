"""What the window sets as rich text (calc/tools/richtext.py; v0.92, docs/ui/window.md §10quater): a symbol of the data as mathematics, a Typst call coloured as the website colours its code, the field a call is shown in and the button it is copied with.

What is held here: a symbol's subscripts, groups, quoted words and Greek names set as the report sets them, and its words escaped; a sentence's words left alone where its symbols take their subscripts; every kind of Typst token taking the site's own syntax colour, an angle bracket escaped; a call field giving back the call as it is pasted, not its HTML; the copy button saying «Copié ✓» and coming back; an example of several lines coloured the same way; the loads tree's Symbole column set as mathematics while its item keeps the source the search reads; and, in every tab that offers a call -- Plan de position, Charges, Modèles statiques, Schémas, Moyens d'assemblage, Moments polaires, Commandes -- every call a coloured field or a coloured block and none a plain line edit; and the connectors tab setting its results with richtext's own helpers rather than the copies it carried.

⚠️ Built off-screen; the colours asserted are the light scheme's, which conftest seeds -- a scheme changed in this process would re-polish every window the suite has left alive (test_theme.py runs those in a process of its own).
"""

import os
import sys
import time

import conftest
from conftest import ROOT

TOOLS = ROOT / "calc" / "tools"
_WINDOW = {}


def _qt():
    if str(TOOLS) not in sys.path:
        sys.path.insert(0, str(TOOLS))
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError as exc:
        raise conftest.Skip(f"PySide6 is not installed ({exc})")
    return QApplication.instance() or QApplication([])


def _window():
    if "window" not in _WINDOW:
        _qt()
        conftest.exported("calculations.json")
        import woodcore_gui
        _WINDOW["window"] = woodcore_gui.MainWindow()
    return _WINDOW["window"]


def _pump(app, rounds=6):
    from PySide6.QtCore import QCoreApplication, QEvent
    for _ in range(rounds):
        app.processEvents()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)


def test_a_symbol_is_set_as_the_report_sets_it():
    _qt()
    import richtext
    cases = {
        'q_(k,"max","b·h")': "q<sub>k,max,b·h</sub>",
        '(g_k + a_k)_"gew"': "(g<sub>k</sub> + a<sub>k</sub>)<sub>gew</sub>",
        "k_(beta,1)": "k<sub>β,1</sub>",
        "gamma_M": "γ<sub>M</sub>",
        "f_(h,alpha,k)": "f<sub>h,α,k</sub>",
        "I_p": "I<sub>p</sub>",
        "m^2": "m<sup>2</sup>",
        "F_Ed dot l": "F<sub>Ed</sub> · l",
        '"Lastmodell"': "Lastmodell",
    }
    for source, expected in cases.items():
        assert richtext.math_html(source) == expected, (source, richtext.math_html(source))
    assert "&lt;" in richtext.math_html('"a<b"'), "a word of the data went into rich text unescaped"
    assert richtext.prose_html("$c_\"red\"$ ist der Faktor") == "c<sub>red</sub> ist der Faktor"
    assert richtext.prose_html("5$ pro Stück") == "5$ pro Stück", "an unpaired dollar is not math (render-prose's rule)"


def test_a_sentence_keeps_its_words_and_its_symbols_take_their_subscripts():
    _qt()
    import richtext
    line = richtext.subscripts("F_max = 3 kN — moyen(s) d'assemblage 1–4\nβ_1 = 12° · I_(p,x) < 5")
    assert "F<sub>max</sub>" in line and "β<sub>1</sub>" in line and "I<sub>p,x</sub>" in line, line
    assert "moyen(s) d'assemblage" in line and "<br>" in line and "&lt; 5" in line, line
    table = richtext.results_html([("I_p", "28800 mm²", True), ("n", "4", False)])
    assert "I<sub>p</sub>" in table and "28800 mm²" in table and table.count("font-weight:600") == 2, table


def test_every_kind_of_typst_token_takes_the_sites_colour():
    _qt()
    import richtext
    import theme
    code = '#let x = 3mm // note\n#show-calc("snow-load", "SL", level: 3) $q_k$ `F <= R` a < b'
    html_ = richtext.typst_html(code)
    expected = {
        "keyword": "#let", "call": "#show-calc", "string": '"snow-load"', "named": "level",
        "number": "3mm", "comment": "// note", "math": "$q_k$", "raw": "`F &lt;= R`",
    }
    for kind, text in expected.items():
        colour = theme.colour(richtext.SYNTAX[kind])
        assert f'color:{colour}' in html_ and text in html_, (kind, text, html_)
        start = html_.index(text)
        span = html_.rfind("<span", 0, start)
        assert colour in html_[span:start], f"{kind} {text!r} is not in its colour"
    assert "a &lt; b" in html_, "a bracket of the call went into rich text unescaped"
    assert f'<span style="color:{theme.colour("syn-call")}">#show-calc</span>' in html_, "`#show` read as a keyword inside `#show-calc`"
    assert set(richtext.SYNTAX.values()) <= set(theme.tokens("light")), "a syntax colour theme.json does not carry"


def test_the_website_cuts_its_code_with_the_same_tokeniser():
    """The site carried its own copy of the pattern until v0.92, and that copy coloured `#show` as a keyword inside every `#show-*` call of the reference -- found when the window's copy was tested. One pattern now, typst_syntax.py's, Qt-free for the site's build."""
    _qt()
    import typst_syntax
    source = (ROOT / "website" / "build.py").read_text(encoding="utf-8")
    assert "import typst_syntax" in source and "re.compile(r\"\"\"\n    (?P<comment>" not in source, "the website has its own tokeniser again"
    imports = [line for line in (ROOT / "calc" / "tools" / "typst_syntax.py").read_text(encoding="utf-8").splitlines() if line.startswith(("import ", "from "))]
    assert all("PySide6" not in line and "richtext" not in line for line in imports), f"the site's build runs where no Qt is installed: {imports}"
    cut = lambda code: [(code[a:b], kind) for a, b, kind in typst_syntax.tokens(code)]
    assert cut("#show-calc(x)") == [("#show-calc", "call")], cut("#show-calc(x)")
    assert cut("#show: woodcore-document")[0] == ("#show", "keyword")
    assert cut("#set-report-language(\"fr\")")[0] == ("#set-report-language", "call")
    assert cut("#set text(size: 11pt)")[:2] == [("#set", "keyword"), ("text", "func")], cut("#set text(size: 11pt)")
    assert set(typst_syntax.SITE_CLASS) == set(typst_syntax.THEME_TOKEN) == set(typst_syntax.KINDS)
    import re
    css = (ROOT / "website" / "assets" / "site.css").read_text(encoding="utf-8")
    for cls in set(typst_syntax.SITE_CLASS.values()):
        assert re.search(rf"\.{cls}\b", css), f"site.css colours no .{cls}"


def test_the_call_field_gives_back_the_call_not_its_html():
    app = _qt()
    import richtext
    from PySide6.QtGui import QFont
    call = '#show-calc("snow-load", "SL", level: 2)'
    field = richtext.CodeField(call, QFont("Consolas"))
    assert field.text() == call and field.toolTip() == call and field.objectName() == "code"
    assert "<span" in field.property("text"), "the field shows the call uncoloured"   # Qt's own text property: the HTML it sets
    button_copied = []
    button = richtext.copy_button("Copier", "Copié ✓", lambda: button_copied.append(call))
    button.click()
    _pump(app, 2)
    assert button_copied == [call] and button.text() == "Copié ✓" and button.property("done") is True
    deadline = time.monotonic() + 3
    while button.text() != "Copier" and time.monotonic() < deadline:
        app.processEvents()
        time.sleep(0.05)
    assert button.text() == "Copier" and button.property("done") is False, "the button kept saying it had copied"
    assert button.minimumWidth() >= button.fontMetrics().horizontalAdvance("Copié ✓"), "the button changes width when it says Copié ✓"


def test_an_example_of_several_lines_is_coloured_the_same_way():
    _qt()
    import richtext
    import theme
    from PySide6.QtGui import QTextDocument
    doc = QTextDocument('#var("R_k", 7, "kN")\n#eq("R_d", `k dot R_k`)')
    highlighter = richtext.TypstHighlighter(doc)
    highlighter.rehighlight()
    block = doc.firstBlock()
    colours = {r.format.foreground().color().name(): block.text()[r.start:r.start + r.length] for r in block.layout().formats()}
    assert colours.get(theme.colour("syn-call")) == "#var", colours
    assert colours.get(theme.colour("syn-string")) in ('"R_k"', '"kN"'), colours
    second = {block.next().text()[r.start:r.start + r.length] for r in block.next().layout().formats()}
    assert "`k dot R_k`" in second, second


def test_the_symbols_of_the_loads_are_set_as_mathematics():
    """The loads are the Variables tab's since v0.117 (issue 13), their symbols set as the page sets them there."""
    window = _window()
    import richtext
    import variables_tab
    tab = next(t for t in window.tabs if isinstance(t, variables_tab.VariablesTab))
    column = variables_tab.SYMBOL
    assert isinstance(tab.tree.itemDelegateForColumn(column), richtext.MathDelegate), "the Symbole column shows Typst's source"
    tab.all_domains_box.setChecked(True)
    try:
        rows = [tab.tree.topLevelItem(n) for n in range(tab.tree.topLevelItemCount())]
        assert rows, "the export lists no variable"
        assert any("_" in row.text(column) for row in rows), "the item lost the source the search reads"
    finally:
        tab.all_domains_box.setChecked(False)


def _calls(tab):
    from PySide6.QtWidgets import QLineEdit
    import richtext
    fields = tab.findChildren(richtext.CodeField)
    plain = [w for w in tab.findChildren(QLineEdit) if w.isReadOnly() and w.text().lstrip().startswith("#")]
    return fields, plain


def test_every_call_of_the_rewritten_tabs_is_a_coloured_field():
    window = _window()
    app = _qt()
    import woodcore_gui
    import commands_tab
    import connectors_tab
    import plan_tab
    import schema_tab
    import statics_tab
    for tab in window.tabs:
        if hasattr(tab, "dirty"):
            tab.dirty = False
    import variables_tab
    found = next(t for t in window.tabs if isinstance(t, variables_tab.VariablesTab))
    domain = next(d for d in found.export.domains if d.variables)
    found.select_key(("export", domain.name, domain.variables[0].key))
    _pump(app)
    commands = next(t for t in window.tabs if isinstance(t, commands_tab.CommandsTab))
    commands.tree.setCurrentItem(commands.nodes["cmd|eq"])
    _pump(app)
    kinds = (plan_tab.PlanTab, variables_tab.VariablesTab, woodcore_gui.PolarTab, statics_tab.StaticsTab, connectors_tab.ConnectorsTab, commands_tab.CommandsTab)
    for kind in kinds:
        tab = next(t for t in window.tabs if isinstance(t, kind))
        if hasattr(tab, "update_display"):
            tab.update_display(force=True)     # the calls are the «Affichage» view's since v0.117, its field filled once it is told what is chosen
        fields, plain = _calls(tab)
        fields = [field for field in fields if field.text()]   # a field of a view not shown yet is empty, which is no call
        assert fields, f"{kind.__name__} shows no call as a coloured field"
        assert not plain, f"{kind.__name__} still shows calls as plain line edits: {[w.text() for w in plain][:3]}"
        for field in fields:
            # a call pasted as it is shown -- one line; the commands tab's signature is a wrapped block of its own since v0.94, not a call field
            assert field.text().strip() and "\n" not in field.text(), field.text()
            assert field.text().startswith("#"), field.text()
    from PySide6.QtWidgets import QPlainTextEdit
    examples = [w for w in commands.findChildren(QPlainTextEdit) if w.objectName() == "code"]
    assert examples, "the examples of the commands tab are not set on the site's code ground"
    signature = dict(commands.parts)["signature"]
    assert signature.objectName() == "code" and "#eq" in signature.text() and "color:" in signature.text(), "the commands tab's signature is not coloured on the site's code ground"
    schema = next(t for t in window.tabs if isinstance(t, schema_tab.SchemaTab))
    # the schemas' block of calls is the «Affichage» view's coloured field since v0.117
    import richtext
    schema.update_display(force=True)
    assert isinstance(schema.display.field, richtext.CodeField) and schema.display.field.text().startswith("#figure(image-schema("), "the schemas' call is not a coloured field"
    assert connectors_tab._math_html is richtext.math_html and connectors_tab._prose_html is richtext.prose_html, "the connectors tab carries its own copy of the math helpers again"


def test_the_polar_moments_results_carry_their_subscripts():
    window = _window()
    import woodcore_gui
    from PySide6.QtCore import Qt
    tab = next(t for t in window.tabs if isinstance(t, woodcore_gui.PolarTab))
    assert tab.results.textFormat() == Qt.TextFormat.RichText and tab.trial_result.textFormat() == Qt.TextFormat.RichText
    if tab.results.text():
        assert "<sub>p</sub>" in tab.results.text() or "<sub>p,x</sub>" in tab.results.text(), tab.results.text()
