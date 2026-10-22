# The command palette (Ctrl+K)

> Written on 2026-10-22 (issue #83, spec [`requirements/completed/2026-10-22-ergonomie-palette-onglet-projet.md`](../requirements/completed/2026-10-22-ergonomie-palette-onglet-projet.md), REQ-001 to REQ-008, UI-001). The window's frame is [`window.md`](window.md) §10quater; the graph it reads «utilisé par» from is [`domain/dependencies.md`](../domain/dependencies.md) §3.3quinvicies.

## 10quater (suite) — the command palette

**Why.** The engineer, 07.10.2026: «il y a pour l'instant trop d'informations dans les onglets. On se perd un peu». The palette finds a tab, an action, an object of the project, a variable, a norm, a Typst command or a warning in a few letters, without going through the navigation — VS Code's, Linear's, Figma's.

**Opening and closing.** **Ctrl+K**, or a click on the field «Rechercher… Ctrl K» of the top bar, opens it over the window, wide and of a fixed size; **Escape** or the **cross** at its top right closes it. It is inert while a variable is chosen for a tab (`begin_variable_pick`). Its modules: `calc/palette_index.py` (Qt-free: what it searches, read at the sources, and how a query matches) and `calc/tools/command_palette.py` (the dialog, its words `cp_`, and `PaletteWindowMixin`, which `MainWindow` names among its bases).

**Using it** (the engineer, 21.10.2026, the decisions of issue #83):

- **Categories** under the field, chosen by a click or by their character typed first: *Tout*, *Actions* `>`, *Objets du projet* `@`, *Variables* `#`, *Normes* `§`, *Avertissements* `!` — one table, `palette_index.CATEGORIES`.
- **With the mouse.** The wheel scrolls the list without choosing; **a click chooses** an entry; **a double click opens it** and closes the palette; **Enter**, while typing, opens the first entry. **Tab and the arrows do nothing**, and no row at the foot recalls the keys.
- **The list** groups the entries by kind, the letters found underlined (they are matched in their order, a case left aside: «flex» finds *Flexion*, «bi01» finds *BI-01*); a check's η is coloured by the theme's `ok` and `danger`; a tab's Ctrl+n and an action's keys stand beside it. Empty, the palette shows the entries opened lately in this session, then the tabs and the actions.
- **The panel on the right** is always there — «Cliquez sur un élément pour voir son détail et ses actions» before a click — so that nothing moves under the pointer: the entry chosen, its kind, its detail, a check's η, and for an object of the project what uses it («3 vérification(s), η max 0.91» and the list, transitively) and what can be done with it: *Ouvrir*, *Copier l'appel Typst*, *Montrer sur le plan …* for a position on a plan, *Nouvelle vérification…* for a position (the tabs where a check is made, read off their `GRAPH_KIND`, the position set in the new draft).

**What it searches, and where it reads it** — each time it opens, the project's part off the window's thread (reading the variables takes a second on a project of some size), nothing kept between two openings but the entries opened lately (Q-001 to Q-002, Q-006 of the spec):

- **The tabs** the document shown can open, in the navigation's order (`nav.order()`), and **the actions** of the window itself: every `QAction` of its menu bar, walked into every submenu, separators and actions without words left out, and the PDF button's click and menu (`PaletteWindowMixin.palette_actions`) — an action added to a menu is in the palette without anyone listing it; one that cannot run is shown greyed and not run. **The views** of the tab in front (`views.items`) and **the window's languages** (`LanguageSwitch.codes`) are entries too, as they are no `QAction`.
- **The objects**: the positions (`positions_store.read`), the checks of `data/checks.json` and `data/steel.json` — a timber check's η computed by `member_check.utilisations`, as its tab computes it, a steel check's read off its file — and every other node of the graph of dependencies of the last export (`data/dependencies.json`). Opening one is `MainWindow.open_object`: *Positions* lists the positions since 0.122 (`GRAPH_KIND = "position"`). **«Utilisé par»** is the graph's, transitively (`dependency_graph.reachable`, which «Dépendances» calls too); before a first export the panel says the graph is not written yet.
- **The variables** of the export (`variable_sources.read_export`), no Typst compiled; opened, they are shown in *Variables*, its search holding the key.
- **The norms**: the documents of `calc/norms/norms.json` (`norms.references`) and the clauses the checks cite — a timber check's computed clause, a steel check's steps' — each opening the first check that cites it.
- **The Typst commands** of `calc/i18n/commands.json`, which holds every public command; opened, *Commandes* is shown. *Copier l'appel Typst* of an object is read off `dependency_graph.COMMAND_REFERENCES`: `#position("T001")`, `#image-positions-plan("P01")`, `#include domain-file("check", "BI-01")`.
- **The warnings**, gathered from where they already are and nowhere new: the window's notices (`notifications.STORE`, the critical ones and the warnings), the checks whose η is above 1, a check that cannot be calculated and its reason, each check's own warnings, and the files of the export missing or not readable. A file that cannot be read is said by an entry of its own, never swallowed.

**Not done**: moving through the list with the keyboard, which the engineer left out on purpose.

`tests/test_palette_index.py` and `tests/test_command_palette.py` hold it.
