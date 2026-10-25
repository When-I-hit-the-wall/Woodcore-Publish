"""The words of the six tabs of the «Actions» group, still empty (v0.117; docs/ui/window.md §10quater, spec docs/requirements/active/2026-10-08-schema-actions-positions-affichage.md).

The engineer's request of 08.10.2026: in the left pane, under «Actions», two sections -- **Actions permanentes** (Poids propre, Surcharge) and **Actions variables** (Charge utile, Neige, Vent, Séisme) -- whose tabs «sont vides pour l'instant». The two sections are sub-titles of the group (`woodcore_gui.NAV_SECTIONS`, `chrome.SideNav`'s «section» row); «Combinaisons de charges» stays below them, after a thin line (decision D-005); «Charges» stood there too until v0.117, when issue 13 retired it into «Variables», which lists every one of its values.

**What a tab says is `reserved_tab.ReservedTab`'s** (`reserved_tab.future`; `woodcore_gui.FutureTab` until v0.120): its name, «Implémentation future.» and what it will hold. Nothing is calculated here.

**The names come from the norms, not from memory** (docs/architecture/principles.md): SIA 260:2013 writes «Actions permanentes» and «Actions variables» in French, «Ständige Einwirkungen» and «Veränderliche Einwirkungen» in German, `Permanent actions` and `Variable actions` in English; SIA 260 and 261 «Charges utiles», «Séisme» and «Neige» / «Nutzlasten», «Erdbeben» and «Schnee» (SIA 261:2020 §«Eigenlast» for the self-weight, «Auflast» for what the glossary calls «Poids propre non-structural» -- `document.superimposed`, whose English words this follows). «Surcharge» is the engineer's own word for the permanent load that is not the structure's (D-013).

**«Poids propre» and «Surcharge» became one tab, «Poids propre et surcharge»** (issue #35, D-08, calc/tools/dead_load_tab.py), which is no longer here. **Each tab and the domain it will hold are listed by the Variables tab meanwhile** (calc/domains/dead_load.py, live_load.py, snow.py, wind.py), the Loads tab having been retired into it in v0.117 (issue 13): until the tabs have their content they do not duplicate it (docs/decisions.md).
"""

# Tab key -> (the key of what the tab will hold). The keys are literals on purpose: tests/test_i18n.py finds a key by the code that names it.
SOON = {
    "tab_ac_imposed": "ac_what_imposed",
    "tab_ac_seismic": "ac_what_seismic",
}

STRINGS = {
    "fr": {
        # the two sections of the group «Actions» (SIA 260:2013)
        "nav_permanent": "Actions permanentes",
        "nav_variable": "Actions variables",
        # the six tabs
        "tab_ac_selfweight": "Poids propre et surcharge",
        "tab_ac_imposed": "Charge utile",
        "tab_ac_snow": "Neige",
        "tab_ac_wind": "Vent",
        "tab_ac_seismic": "Séisme",
        # what each will hold
        "ac_what_imposed": "Cet onglet est vide pour l'instant : il réunira les charges utiles selon l'affectation des locaux. En attendant, elles se consultent dans « Variables ».",
        "ac_what_seismic": "Cet onglet est vide pour l'instant : il réunira l'action sismique. Aucun module ne la calcule encore.",
    },
    "de": {
        "nav_permanent": "Ständige Einwirkungen",
        "nav_variable": "Veränderliche Einwirkungen",
        "tab_ac_selfweight": "Eigen- und Auflasten",
        "tab_ac_imposed": "Nutzlast",
        "tab_ac_snow": "Schnee",
        "tab_ac_wind": "Wind",
        "tab_ac_seismic": "Erdbeben",
        "ac_what_imposed": "Dieses Register ist vorerst leer: es wird die Nutzlasten je nach Nutzung der Räume enthalten. Bis dahin sind sie unter «Variablen» einzusehen.",
        "ac_what_seismic": "Dieses Register ist vorerst leer: es wird die Erdbebeneinwirkung enthalten. Kein Modul berechnet sie bisher.",
    },
    "en": {
        "nav_permanent": "Permanent actions",
        "nav_variable": "Variable actions",
        "tab_ac_selfweight": "Self-weight and superimposed load",
        "tab_ac_imposed": "Imposed load",
        "tab_ac_snow": "Snow",
        "tab_ac_wind": "Wind",
        "tab_ac_seismic": "Earthquake",
        "ac_what_imposed": "This tab is empty for now: it will hold the imposed loads by the use of the rooms. Until then, they are looked up in «Variables».",
        "ac_what_seismic": "This tab is empty for now: it will hold the seismic action. No module calculates it yet.",
    },
}
