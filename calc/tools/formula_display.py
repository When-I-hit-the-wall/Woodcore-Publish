"""«Affichage» of the «Domaines» tab: the engineer's `Domains/<id>.typ` compiled as the report prints it, and set line by line (issue #113, spec docs/requirements/completed/2026-10-24-onglet-domaines-formulaire-code.md, UI-020, UI-021, UI-022, ARCH-007, ARCH-009, D-19).

The view is the snow's and the wind's (calc/tools/domain_file_display.py: the page compiled on an A4, `show-masked`, the card of the file, the command to copy, the domain's level, each line's 0 1 2 3 and arguments, «Voir le fichier entier») -- not a second one --, given this **source**: the file is the domain's own, its elements read off `formula_domain` (one per command, its id `<kind>:<index of the item>`), and every write goes through the tab's guarded writers, which write the file by `formula_domain.save` -- never through the base of unfold, which a domain of the engineer's has not (ARCH-009).

The card gains what a domain of the tab has and a case has not (UI-021): «lire une valeur ailleurs dans le rapport» (`#var("eta", domain: "panne-p2", display: "value-unit")`), and **the domain's options**, each ticked or not -- `presets: "block"`, the positions and the style, written on the one `#calc-defaults(…, scope: "domain")` line (calc/domains/formula_defaults.py). A line clicked opens **all** its arguments (calc/domains/formula_args.py) and «Rétablir la ligne». The renders are compiled when shown, never committed (D-15). The hovers of the lines (UI-018) are those of the list of elements, the page having no rectangle per line (D-19).
"""


from PySide6.QtWidgets import QCheckBox, QComboBox, QHBoxLayout, QLabel, QLineEdit, QPushButton, QWidget

import build_reference as ref
import line_display
import richtext
from domains import formula_args, formula_defaults


class FormulaSource:
    """The source domain_file_display.DomainFileDisplay reads a domain of the tab by -- see the module's docstring. `view.tab` is the FormulaTab."""

    def __init__(self, view):
        self.view = view

    @property
    def tab(self):
        return self.view.tab

    def path(self):
        domain = self.tab.domain
        if domain is None or domain.path is None or not domain.path.is_file() or self.tab.current_id is None:
            return None
        return domain.path

    def elements(self):
        """The header {id: "domain", level}, then each command of the domain {id: "<kind>:<index>", kind, key, symbol, label, level, options, line}."""
        tab = self.tab
        domain = tab.domain
        if domain is None or domain.state == "unreadable":
            return []
        out = [{"id": "domain", "kind": "domain", "level": formula_args.domain_level(domain)}]
        results = tab.results or []
        for i, c in enumerate(domain.commands):
            if c.is_text or c.kind not in ("var", "eq", "verify"):
                continue
            r = results[i] if i < len(results) else None
            shown = {k: v for k, v in c.options.items() if k in line_display.display_args(c.kind)}
            symbol = c.formula if c.kind == "verify" else (c.symbol or (r.symbol if r is not None else "") or c.key)
            out.append({"id": f"{c.kind}:{i}", "kind": c.kind, "key": c.key, "symbol": symbol, "label": str(c.options.get("label") or ""),
                        "level": c.options.get("level"), "options": shown, "line": formula_args.written(c)})
        return out

    def matches(self):
        return True

    def lit(self):
        """Each element's row of the list lights its line, and is lit with it (UI-018: the page has no rectangle per line, D-19) -- called once the card is built."""
        for lid, row in getattr(self.view, "rows", {}).items():
            kind, _sep, index = lid.partition(":")
            if kind in ("var", "eq", "verify") and index.isdigit():
                self.tab.hover(row, int(index), "display")

    def extra(self, body, header):
        """«Lire une valeur ailleurs» and the domain's options, under the domain's level (UI-021)."""
        tab, t = self.tab, self.tab.t
        domain = tab.domain
        key = read_key(domain, tab.results)
        if key:
            body.addWidget(QLabel(t("fm_d_read")))
            call = ref.call_command("var", key, domain=domain.id, display="value-unit")
            field = richtext.CodeField(call, tab.app.mono_font)
            row = QHBoxLayout()
            row.addWidget(field, 1)
            row.addWidget(richtext.copy_button(t("ds_copy"), t("ds_copied"), lambda: self.view.copy_text(call)))
            body.addLayout(row)
            self.read_call = call
        title = QLabel(t("fm_d_opts"))
        title.setStyleSheet("font-weight: 600; margin-top: 8px;")
        title.setToolTip(t("fm_d_opts_tip"))
        body.addWidget(title)
        current = formula_defaults.options(domain)
        self.option_boxes = {}
        for name in formula_defaults.OPTIONS:
            row = QHBoxLayout()
            tick = QCheckBox(name)
            tick.setChecked(name in current)
            row.addWidget(tick)
            if name == "presets":
                row.addWidget(QLabel(t("fm_d_presets")), 1)
                tick.toggled.connect(lambda on: tab.write_domain_option("presets", "block" if on else None))
                combo = None
            else:
                combo = QComboBox()
                for value in formula_defaults.values(name):
                    combo.addItem(value, value)
                combo.setCurrentIndex(max(0, combo.findData(current.get(name, formula_defaults.PROPOSED[name]))))
                combo.setEnabled(name in current)
                row.addWidget(combo, 1)
                tick.toggled.connect(lambda on, n=name, c=combo: tab.write_domain_option(n, c.currentData() if on else None))
                combo.activated.connect(lambda _i, n=name, c=combo, k=tick: k.isChecked() and tab.write_domain_option(n, c.currentData()))
            self.option_boxes[name] = (tick, combo)
            holder = QWidget()
            holder.setLayout(row)
            body.addWidget(holder)

    def arguments(self, element, form):
        """Every argument of the line clicked (UI-012: in «Affichage», all), written into the line; «Rétablir la ligne»."""
        tab, t = self.tab, self.tab.t
        if element["kind"] not in ("var", "eq", "verify"):
            return False
        index = int(element["id"].partition(":")[2])
        command = tab.domain.commands[index]
        result = tab.results[index] if index < len(tab.results or ()) else None
        table = tab.symbol_table(index)
        for argument in formula_args.arguments(command, True, result, table):
            if argument.kind in ("choice", "unit"):
                combo = QComboBox()
                combo.addItem(t("fm_a_auto"), "")
                for value in argument.choices:
                    combo.addItem(str(value), str(value))
                if argument.value and combo.findData(argument.value) < 0:
                    combo.addItem(argument.value, argument.value)
                combo.setCurrentIndex(max(0, combo.findData(argument.value)))
                combo.activated.connect(lambda _i, n=argument.name, c=combo: tab.write_argument(index, n, c.currentData()))
                form.addRow(argument.name, combo)
            else:
                line = QLineEdit(argument.value)
                line.setPlaceholderText("—")
                line.editingFinished.connect(lambda n=argument.name, l=line: tab.write_argument(index, n, l.text()))
                form.addRow(argument.name, line)
        reset = QPushButton(t("fm_d_reset"))
        reset.clicked.connect(lambda: tab.write_reset_line(index))
        form.addRow("", reset)
        return True


def read_key(domain, results):
    """The key «lire une valeur ailleurs» offers: the domain's result (`role: "result"`), else its last line that computes, else its last variable."""
    commands = [] if domain is None else domain.commands
    for c in reversed(commands):
        if c.kind == "eq" and c.options.get("role") == "result":
            return c.key
    for kind in ("eq", "var"):
        for c in reversed(commands):
            if c.kind == kind:
                return c.key
    return ""


def failure_text(t, state_messages, typst_error):
    """What «Affichage» says of a domain Typst does not compile (UI-022): the state's own fault where it says the same, else Typst's -- one message, never two."""
    if state_messages:
        return state_messages[0]
    return t("fm_d_stops") + " " + (typst_error or "")
