"""The type «Calcul»: a tab of calculation, described by its domain and built from services (spec docs/requirements/completed/2026-10-23-onglets-types-et-services.md, issue #95; spec 2026-10-22-onglet-neige-type, issue #94; docs/ui/calc-tab.md).

The engineer, 22.10.2026: «la façon dont l'onglet Neige est construit doit être un onglet type… Un futur onglet ne doit pas réinventer sa base», and 23.10.2026: a tab is built from features written once, chosen like bricks. `CalcTab` is a type -- a thin base of the host (tab_host.TabHost) that names the services every tab of calculation has by default, in the order they are mounted and run:

* the list of the cases (case_list.CaseList), on the left;
* the bubbles of the norm (calc_bubbles.Bubbles), before the form that attaches its ⓘ to them;
* the identity «Nom · Description · ID» (case_list.Identity) and the form its domain declares (calc_form.DeclaredForm), in the centre;
* the right pane of modules (calc_modules.Modules): the state of the calculation, the results, the domain's drawing and chart where it has them, the excerpts pinned;
* «Affichage» of the case's file, line by line (calc_display.DomainDisplay).

A tab of calculation is a subclass of `CalcTab` that names its parameters -- `KEY`, `MODULE`, `ID_PREFIX`, `LIST_KEY`, `EMPTY_KEY`, `WORDS`, and `PREFIX` where its domain declares no form -- and, where it differs from its type, its `SERVICES` (`swap`, `+`). It defines no method: `HOOKS` is empty (tests/test_tab_overrides.py). What the domain must give is its services' `NEEDS`, checked when the tab is built.

**What the domain says, the services draw**: no word, no number and no rule of a domain in these modules (tests/test_calc_tab_base.py mounts the type on an invented domain and greps them for the snow). The domain's words are its tab's (`<prefix>s_<section>`, `<prefix>f_<key>`, `<prefix>msg_<code>`, `<prefix>x_<excerpt>`), the services' `ct_` (calc_tab_words.py).
"""

import views
from calc_bubbles import Bubbles
from calc_display import DomainDisplay
from calc_form import DeclaredForm
from calc_modules import Modules
from case_list import CaseList, Identity
from tab_host import TabHost, excerpt_module_id, excerpt_of_module  # noqa: F401 -- re-exported: a pinned excerpt's module id, read by the tests


def before(services, anchor, *new):
    """`services` with `new` just before `anchor` -- a service that gives the right pane a module mounts before the pane (the permanent loads' section, issue #111), one of the left zone stands above the list."""
    at = services.index(anchor)
    return services[:at] + tuple(new) + services[at:]


def swap(services, old, new):
    """`services` with `new` in the place of `old` -- a tab whose form is not the declared one (the permanent loads' table of layers)."""
    return tuple(new if s is old else s for s in services)


class CalcTab(TabHost):
    """The type «Calcul» -- see the module's docstring."""

    SERVICES = (CaseList, Bubbles, Identity, DeclaredForm, Modules, DomainDisplay)
    HOOKS = ()
    VIEWS = views.CALC_VIEWS
    WORDS = "ld"           # the sentences that name a case (`ld_new`, `ld_saved`…): a tab names its own where it has them
    GRAPH_KIND = "load"    # a case of a load in the graph of dependencies, `<domain>/<id>` (issue #71)
