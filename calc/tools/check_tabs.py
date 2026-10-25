"""The four tabs of the member checks of SIA 265 4.2 on the type «Calcul»: Traction, Compression, Flexion, Cisaillement (spec docs/requirements/completed/2026-10-24-verifications-elements-v3.md, UI-001, UI-002, ARCH-004; issue #112; docs/ui/tab-member-checks.md).

Each is a class of parameters (tests/test_tab_overrides.py): its key, its domain -- `member_check_view.DOMAINS[<tab>]`, which lists its kinds in the folder the four share --, the prefix of a new id and its list's words. Its services are the type's, with the list grouped by position and its rates (check_list.CheckList), the head «Élément» and its rows «Sollicitation» and «Facteurs» before the declared form (check_member.CheckMember, load_row.LoadRow, factors_row.FactorsRow), the check's «Résultats» given to the right pane (check_results.CheckResults) and «Affichage» keeping its options in the check's source (check_display.CheckDisplay). The stability is the last accordion of the compression and of the bending (REQ-011): «Flambage» and «Déversement» are no tabs of their own any more. The other tabs of the group -- torsion, the serviceability, the fire -- are member_check_tab's and fire_check_tab's.
"""

import calc_tab
import member_check_tab_words
from calc_display import DomainDisplay
from check_display import CheckDisplay
from check_member import CheckMember
from check_results import CheckResults
from calc_form import DeclaredForm
from case_list import CaseList
from check_list import CheckList
from factors_row import FactorsRow
from load_row import LoadRow
from calc_modules import Modules
from domains import member_check_view

# The words of the list's own menus and dialogs, which the list reads off the tab's module: the member checks' (mc_)
STRINGS = member_check_tab_words.STRINGS

SERVICES = calc_tab.swap(calc_tab.before(calc_tab.CalcTab.SERVICES, DeclaredForm, CheckMember, LoadRow, FactorsRow), DomainDisplay, CheckDisplay)
SERVICES = calc_tab.swap(calc_tab.before(SERVICES, Modules, CheckResults), CaseList, CheckList)


class TensionTab(calc_tab.CalcTab):
    """«Traction», SIA 265 4.2.1 (UI-008: unchanged)."""

    KEY = "tab_mc_tension"
    MODULE = member_check_view.DOMAINS["tension"]
    ID_PREFIX = "Z_"
    LIST_KEY = "mc_list"
    EMPTY_KEY = "mc_empty"
    WORDS = "mc"
    GRAPH_KIND = "check"
    SERVICES = SERVICES


class CompressionTab(calc_tab.CalcTab):
    """«Compression», SIA 265 4.2.2, and its stability 4.2.8 in its last accordion (REQ-011)."""

    KEY = "tab_mc_compression"
    MODULE = member_check_view.DOMAINS["compression"]
    ID_PREFIX = "DR-"
    LIST_KEY = "mc_list_compression"
    EMPTY_KEY = "mc_empty_compression"
    WORDS = "mc"
    GRAPH_KIND = "check"
    SERVICES = SERVICES


class BendingTab(calc_tab.CalcTab):
    """«Flexion», SIA 265 4.2.3 and 4.2.4, and its lateral torsional buckling 4.2.9 in its last accordion (REQ-011); the scheme in the style of SIA (UI-009)."""

    KEY = "tab_mc_bending"
    MODULE = member_check_view.DOMAINS["bending"]
    ID_PREFIX = "BI-"
    LIST_KEY = "mc_list_bending"
    EMPTY_KEY = "mc_empty_bending"
    WORDS = "mc"
    GRAPH_KIND = "check"
    SERVICES = SERVICES


class ShearTab(calc_tab.CalcTab):
    """«Cisaillement», SIA 265 4.2.5, 4.2.6 and 4.2.7.1 in three figures (UI-010, D-7: in place of Q-010's list)."""

    KEY = "tab_mc_shear"
    MODULE = member_check_view.DOMAINS["shear"]
    ID_PREFIX = "SC-"
    LIST_KEY = "mc_list_shear"
    EMPTY_KEY = "mc_empty_shear"
    WORDS = "mc"
    GRAPH_KIND = "check"
    SERVICES = SERVICES
