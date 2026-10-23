"""Every tab of the window, declared once (spec docs/requirements/active/2026-10-19-base-saine-nettoyage.md, ARCH-001, ARCH-RISK-106).

Until v0.120 a tab was added by hand in eight places: `TABS`, `NAV_GROUPS`, `NAV_SECTIONS`, `MODE_TABS`/`DOCUMENT_TABS`, `MODE_BOUND`, `GUARDED_TABS`, `DOMAIN_TABS` -- and a tab forgotten in one of them half joined the window. Now a tab is **one `TabSpec`** in `SPECS`, in the order the navigation shows it: its key, how it is built, its group in the side navigation and the sub-title it stands under, the documents that show it, and whether it holds one document's own work. Everything the window reads is derived from that one list, under the names it always read (woodcore_gui re-exports them, and a dozen tests read `woodcore_gui.TABS` and `NAV_GROUPS`); and every tab class is guarded here, its writers refused in a project opened read-only (tab_guard.py).

To add a tab: write its module, give its class a `KEY`, and add its `TabSpec` here -- its icon in `chrome.ICONS` and its title in the window's words, which `tests/test_tab_registry.py` checks.
"""

from dataclasses import dataclass

import action_tabs
import annex_tab
import commands_tab
import connectors_tab
import dependencies_tab
import fire_check_tab
import fire_tab
import formula_tab
import journal_tab
import metre_tab
import load_tab
import snow_tab
import member_check_tab
import plan_tab
import positions_tab
import profile_tab
import project_tab
import python_tab
import reserved_tab
import schema_tab
import source_archive
import statics_tab
import steel_tab
import structure_tab
import tab_guard
import variables_tab
from polar_tab import PolarTab

ALL = ("rs", "cu", "bp")   # the three documents: the statical report, the convention d'utilisation, the base de projet
REPORT = ("rs",)


@dataclass(frozen=True)
class TabSpec:
    key: str                 # its title key in the window's words, and the key its view and sizes are kept under
    factory: object          # how it is built: its class, or a function of the window
    group: str               # the key of its group in the side navigation (the site's sidebar's arrangement, v0.91)
    section: str = None      # the sub-title it stands under (v0.117): the key of its words, "" for a thin line only, None for none
    documents: tuple = REPORT  # the documents that show it (the engineer's request of 30.09.2026): the report every tab, the two others what they are written from
    mode_bound: bool = False   # it holds one document's own work: asked what to do with what is unsaved before another document is shown (`confirm_leave`)


SPECS = (
    # The project's basic data, its templates and its documents (issues #87, #88, #90): the first row, where the window opens and where every change of document brings it back -- it compiles nothing.
    TabSpec("tab_project", project_tab.ProjectTab, "nav_document_group", documents=ALL),
    # What the document shown is made of: its chapters, its sections and the objects of each -- the one tab a document is written in, in the three documents alike (the rework of 01.10.2026).
    TabSpec("tab_structure", structure_tab.StructureTab, "nav_document_group", documents=ALL, mode_bound=True),
    TabSpec("tab_plan", plan_tab.PlanTab, "nav_project", documents=ALL),
    # The fire protection plans right under the position plans they are drawn beside (v0.115) -- the base de projet's and the report's, not the convention d'utilisation's (the engineer's answer of 06.10.2026).
    TabSpec("tab_fire", fire_tab.FireTab, "nav_project", documents=("rs", "bp")),
    TabSpec("tab_positions", positions_tab.PositionsTab, "nav_project", documents=ALL),
    # What the position plans draw, read from the export (spec 2026-10-21-commandes-typst-refonte, UI-003, Q-003): the card «Métrés» of «Positions» made a tab of its own, and its file.
    TabSpec("tab_metre", metre_tab.MetreTab, "nav_project", documents=ALL),
    # The report's revision journal: what the project itself says of the report, written by hand (v0.99) -- each document its own.
    TabSpec("tab_journal", journal_tab.JournalTab, "nav_project", documents=ALL, mode_bound=True),
    # The annexes: the documents the report draws on from outside and the excerpts it shows of them (v0.115).
    TabSpec("tab_annexes", annex_tab.AnnexTab, "nav_project", documents=ALL),
    # The scripts: what the engineer writes into the project himself, read by the report like any other calculation (v0.100).
    TabSpec("tab_python", python_tab.PythonTab, "nav_project"),
    # «Actions» (action_tabs.py, v0.117): the permanent actions, then the variable ones, then the combinations below a line. Three are reserved for a calculation to come (D-04).
    TabSpec("tab_ac_selfweight", load_tab.DeadLoadTab, "nav_actions", section="nav_permanent"),
    TabSpec("tab_ac_imposed", lambda app: reserved_tab.future(app, "tab_ac_imposed", action_tabs.SOON["tab_ac_imposed"], "tab_ac_imposed"), "nav_actions", section="nav_variable"),
    TabSpec("tab_ac_snow", snow_tab.SnowTab, "nav_actions"),
    TabSpec("tab_ac_wind", load_tab.WindTab, "nav_actions"),
    TabSpec("tab_ac_seismic", lambda app: reserved_tab.future(app, "tab_ac_seismic", action_tabs.SOON["tab_ac_seismic"], "tab_ac_seismic"), "nav_actions"),
    TabSpec("tab_combinations", lambda app: reserved_tab.future(app, "tab_combinations", "future_combinations"), "nav_actions", section=""),
    TabSpec("tab_statics", statics_tab.StaticsTab, "nav_structure"),
    # The schemas before the two tabs that name one: the detail is drawn first, then calculated (periodic audit 260916).
    TabSpec("tab_schema", schema_tab.SchemaTab, "nav_structure"),
    TabSpec("tab_connections", connectors_tab.ConnectorsTab, "nav_connections"),
    TabSpec("tab_polar", PolarTab, "nav_connections"),
    # The member checks of SIA 265 chapter 4: 4.2 the structural safety, then 4.3 and 4.4 the serviceability. Torsion and the serviceability are reserved (D-04).
    TabSpec("tab_mc_tension", member_check_tab.TensionTab, "nav_safety"),
    TabSpec("tab_mc_compression", member_check_tab.CompressionTab, "nav_safety"),
    TabSpec("tab_mc_bending", member_check_tab.BendingTab, "nav_safety"),
    TabSpec("tab_mc_shear", member_check_tab.ShearTab, "nav_safety"),
    TabSpec("tab_mc_torsion", lambda app: member_check_tab.soon_tab(app, "tab_mc_torsion"), "nav_safety"),
    TabSpec("tab_mc_buckling", member_check_tab.BucklingTab, "nav_safety"),
    TabSpec("tab_mc_ltb", member_check_tab.LateralTab, "nav_safety"),
    # issue #46: the same checks in the design situation fire, last of «Sécurité structurale»
    TabSpec("tab_mc_fire", fire_check_tab.FireCheckTab, "nav_safety"),
    TabSpec("tab_sls_deformation", lambda app: member_check_tab.soon_tab(app, "tab_sls_deformation"), "nav_service"),
    TabSpec("tab_sls_vibration", lambda app: member_check_tab.soon_tab(app, "tab_sls_vibration"), "nav_service"),
    # The steel of SIA 263 (issues #50-#52, D-13): what the section is, then what it resists.
    TabSpec("tab_st_profiles", profile_tab.ProfileTab, "nav_steel", section="nav_steel_section"),
    TabSpec("tab_st_class", steel_tab.SteelClassTab, "nav_steel"),
    TabSpec("tab_st_tension", steel_tab.SteelTensionTab, "nav_steel", section="nav_steel_safety"),
    TabSpec("tab_st_compression", steel_tab.SteelCompressionTab, "nav_steel"),
    TabSpec("tab_st_bending", steel_tab.SteelBendingTab, "nav_steel"),
    TabSpec("tab_st_shear", steel_tab.SteelShearTab, "nav_steel"),
    # The reference: «Formule» what to write -- its domains lie at the Typst root the three documents share (spec 2026-10-08 D-16) --, «Variables» what there is to name in it, «Commandes» what there is to call.
    TabSpec("tab_formula", formula_tab.FormulaTab, "nav_reference", documents=ALL),
    TabSpec("tab_variables", variables_tab.VariablesTab, "nav_reference", documents=ALL),
    # Which object reads which (issue #71): the graph the export writes, read here -- a browser, like «Variables».
    TabSpec("tab_dependencies", dependencies_tab.DependenciesTab, "nav_reference", documents=ALL),
    TabSpec("tab_commands", commands_tab.CommandsTab, "nav_reference", documents=ALL),
)

# --- what the window reads, derived ---------------------------------------------------------

TABS = tuple((spec.key, spec.factory) for spec in SPECS)

NAV_GROUPS = tuple((group, tuple(spec.key for spec in SPECS if spec.group == group))
                   for group in dict.fromkeys(spec.group for spec in SPECS))

NAV_SECTIONS = {spec.key: spec.section for spec in SPECS if spec.section is not None}

DOCUMENT_TABS = tuple(spec.key for spec in SPECS if "cu" in spec.documents)
MODE_TABS = {
    "rs": tuple(spec.key for spec in SPECS if "rs" in spec.documents),
    "cu": DOCUMENT_TABS,
    "bp": DOCUMENT_TABS + tuple(spec.key for spec in SPECS if "bp" in spec.documents and "cu" not in spec.documents),
}

MODE_BOUND = tuple(spec.key for spec in SPECS if spec.mode_bound)

# Every tab class the window builds, guarded (tab_guard.guard): its writers -- where they are defined, its own class, a mixin or a base it shares -- refused in a project opened read-only, and followed by the domains' files where the class says SYNC_DOMAIN.
GUARDED_TABS = tuple(spec.factory for spec in SPECS if isinstance(spec.factory, type) and any(name in dir(spec.factory) for name in tab_guard.WRITERS))
for _cls in GUARDED_TABS:
    tab_guard.guard(_cls)
tab_guard.guard_actions(source_archive.Actions)
