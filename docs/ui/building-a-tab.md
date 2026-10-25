# Building a tab: a type and its services

> How a tab is built from a type and from services written once, never copied (issue #95, spec `docs/requirements/completed/2026-10-23-onglets-types-et-services.md`; `docs/decisions.md` §13, «A tab is built from a type and its services»). The frame of the window is `window.md`; the type «Calcul» is `calc-tab.md`.

## 10quater. Building a tab

The engineer, 22.10.2026: «on ne copie plus des onglets. Un nouvel onglet se construit à partir de paramètres de base», and 23.10.2026: the features of a tab are grouped «dans des gros blocs, et ensuite on peut créer un nouvel onglet et le fabriquer en fonction des fonctionnalités que l'on souhaite… si on souhaite modifier un comportement des onglets, il suffit de modifier le bloc en question». A tab built this way is **a thin class of parameters on a type**; the type names the **services** every tab of its kind has; a service is one feature, written once and tested alone. Changing a feature of every tab is changing one service; changing what every tab of a kind has is changing its type.

### The parts (calc/tools/tab_frame.py, tab_host.py)

| Part | What it is |
|---|---|
| `TabFrame` | **The frame** every tab built from services stands on (`tab_frame.py`, issue #107): it builds the services in the order of `SERVICES`, checks what each `NEEDS` (of its `NEEDS_MODULE`, else of the tab's `MODULE`), mounts them on the context its type names (`CONTEXT`, a subclass of `FrameContext`), runs the phases every tab has -- `shown`, `mode_changed`, `revealed` (`showEvent`), `hidden` (`hideEvent`), `flush`, `leave` --, finds a service (`service(name)`), answers `on_shown`, `on_mode`, `confirm_leave` (phase `leave`, then `True`), `view_state` and `restore` (each named service's `state()`, the splitter's sizes), and lays nothing out: each type places its services' widgets in `frame_body(widgets)`, with `frame_prepare` before the services are mounted and `frame_finish` after (`FRAME_API`). It defines no `dirty`, `save`, `current_id`, `current`, `id_edit` nor `list`, the names by which the window and the autosave tell an editor. `TabHost`, `DocumentTab` and `DataTab` (issue #106) stand on it; `LibraryTab` will in an issue of its own. Its context offers `provide(name)`: the one service's method that names it in `PROVIDES` (moved from `DocumentContext` in issue #106). |
| `Service` | One feature with a place on the screen: a plain class -- no ABC, no common base with a QWidget, whose metaclass mixes with neither -- saying where it goes (`ZONE`: `"left"`, `"centre"`, `"right"`, or `None` for one with no pane), in which views it shows (`IN_VIEWS`), what it asks of the domain (`NEEDS`), which of its methods write (`WRITERS`), which it offers the others through the context (`PROVIDES`), which widget it wraps whole (`WIDGET`, whose writers the registry guards where they are defined: `tab_registry.GUARDED_WIDGETS`), and how it is found (`NAME`, `tab.service(name)`). Moved to `tab_frame.py` in issue #107 and re-exported by `tab_host`. `mount(ctx)` gives its widget; `state()` / `restore(state)` what it keeps across a rebuild of the window. |
| `TabContext` | All a service knows of its tab, one a tab: the domain, the case as it is saved (`source`), the id open (`current_id`), the dot (`dirty`), whether the form is being filled (`loading`), the store of the cases (`store`, `source_store.SourceStore`), the linkable numbers (`links`, `field_links.LinkSet`), the bubbles of the norm (`bubbles`), and what the domain said of the draft (`messages`, `instance`, `drawing`, `chart`, `edges`). |
| `TabHost` | The host of a tab of cases, on the frame: its `frame_body` puts the services' widgets in the zones (the centre in a column that scrolls, above «Annuler les modifications» and «Enregistrer»), gives «Affichage» the panes every tab has (`display_view.ViewPanes`), binds Ctrl+S, and answers once what the window, the autosave and the palette call on a tab of cases (`TAB_API` = `FRAME_API` + the cases' names). |
| a type | A thin subclass of `TabHost` -- or, for a tab without cases, of the frame -- naming its `SERVICES`, its `VIEWS` and its `HOOKS`: `calc_tab.CalcTab` the first, `document_tab.DocumentTab` the second, `data_tab.DataTab` the third. |
| a tab | A subclass of its type naming only its parameters (`PARAMS`: `KEY`, `MODULE`, `ID_PREFIX`, `LIST_KEY`, `EMPTY_KEY`, `WORDS`, `PREFIX`, `SERVICES` where it differs from its type, and for a data tab `EXPOSES`). |

**No service calls another** (D-06). What joins them goes through the context, in three ways only:

* **the draft by contributions** -- a service of the centre says `fill(src)` and `collect(src)`; `ctx.fill(src)` and `ctx.draft()` call them in the order of `SERVICES`, the links last, with `loading` set while the form is filled;
* **phases** for what must happen in order, run by the host, service after service in the order of `SERVICES`: `computed` (the domain has said what it says of the draft: the form's sections, the modules, «Affichage»), `saved`, `before_display` (the case saved before «Affichage» shows its file), `reload_list`, `update_marks`, `select_row`, `hidden`. A case loaded, a tab shown, a draft made are the host's (`draft_logic`): it fills the form (`ctx.fill`) and computes, so that every service hears of it in `computed`;
* **signals** of the context for what needs no order: `lit` (a field and the results it goes into), `focusRequested` (a message clicked), `excerptPinned`, `excerptUnpinned`, `pinsChanged`.

A capability several services use without a place of their own is offered by the context: the linkable numbers (`ctx.links`), the bubbles (`ctx.bubbles`, put there by the service `Bubbles`). `tests/test_tab_services.py` holds that no service module imports another and that no service holds another.

**The rules of a list, a draft and a save are written once and without Qt** -- `case_list_logic.py`, `draft_logic.py`, `source_store.py` --, and called both by the services and by `source_editor.SourceEditorTab`, which every tab not yet on a type still derives from: no rule of a list is written twice (`confirm_leave`, the dot, the list filled, a row chosen, a drop into a folder).

**The guard.** A tab built on a type writes nothing itself: its writers are its services' and its store's, each guarded where it is defined by the `WRITERS` it declares (`tab_guard.guard_service`, `tab_registry.GUARDED_SERVICES`), the window found through the context. A save is one guarded writer, `SourceStore.save` -- the case written, `calculations.json` rebuilt, the cases' files of its kind written or refreshed --, followed by the domains' files where the tab says `SYNC_STORE`: «write → export → unfold → sync», once. `TabHost.save` and `TabHost.delete` refuse a project open read-only before they ask anything. A class several tabs build that writes -- the card of a list written once, `list_file_card.ListFileCard`, in «Métré», «Journal» and «Positions» -- declares its own `WRITERS` and is guarded where it is defined by the registry (`tab_guard.guard_service`, issue #106, D-09), never by adding names as common as `write` or `add` to `tab_guard.WRITERS`.

**The words.** A service's generic words live at the level of a module it names (`WORDS_MODULE`: the calculation services' is `calc_tab_words.py`, `ct_`), which `woodcore_gui_words.py` merges from its registry `SERVICE_WORDS`, a key shared by two modules refused by `tests/test_i18n.py`; the sentences that name a tab's object, whole -- «Nouveau», «(nouvelle, non enregistrée)», «{id} enregistré» -- are the tab's (`<WORDS>_<suffix>`), never composed, a French or German noun changing the sentence round it.

### The five types

| Type | Tabs | Services by default | State |
|---|---|---|---|
| **Calcul** (`calc_tab.CalcTab`) | Neige; Poids propre et surcharge (the table of its layers and the project's library in place of the declared form); Vent (its right pane declared, `Declaration.modules`); the four member checks since issue #112 (Traction, Compression, Flexion, Cisaillement: the head «Élément», «Résultats» and «Affichage» of their own, docs/ui/tab-member-checks.md); Séisme, Charges utiles to come | the list, the bubbles, the identity, the declared form, the right pane of modules, «Affichage» of the case's file | written (v0.125) |
| **Dessin** | Plan de positions, Plan feu, Schémas, Statique | the list, the identity, the canvas -- one service, not cut further --, the properties of the object, «Affichage»; the imported documents and the export sheets where a tab has them | described; its own issue (`DrawTab`) |
| **Éditeur** | Formules, Journal, Positions, Annexes, Python, Profils acier | the list, the text or code editor, «Affichage» | described; its own issue |
| **Données** (`data_tab.DataTab`) | Variables, Métré, Dépendances, Commandes -- browsers, which keep no draft and save nothing | the banner of the state of the export (`ExportBanner`, the zone «top»): a `callout` line the browser tells through the context (`ctx.say(text, kind)`, «warning» or «danger»), reading nothing itself; «Commandes», which reads `lib/` and not the export, mounts none. Each tab adds its browser, **one whole service** (`tab.service("browser")`) that builds its own splitter -- the type lays none (D-08 of the spec 2026-10-24-type-donnees), the tab's `splitter` is its browser's -- and is filled once as it is mounted, with the state the window kept (`ctx.kept(name)`). No table of the export and no «Affichage»: no data tab asks for one; a tab that will adds its service by `SERVICES + (…,)`. No `dirty`, `save`, `current_id` nor `source`: the window tells an editor by `dirty`; `confirm_leave` is the frame's (phase `leave`, a reading in a thread waited for, then `True`) | written (issue #106), on the frame |
| **Document** (`document_tab.DocumentTab`) | Projet (three services: «Informations», «Templates», the acts), Structure du document (one whole service wrapping its widget, `StructureView`) | none (D-07 of the spec 2026-10-24-type-document): what they share is the type's context -- one draft flag a tab (`touch`), the project read-only, the files read again (`reload`: phases `loaded`, `lock`), a service's method offered to the others (`provide`) -- and its answers: `dirty`, `save`, `discard`, `flush_pending`, `confirm_leave` (the one question of `autosave.confirm` with the tab's `UNSAVED_WORDS` where a draft is unsaved), `set_view` (phase `view_set`), `on_properties_changed` | written (v0.125, issue #107), on the frame rather than on `TabHost`: a document has no case |
| **Bibliothèque** (`library_tab.LibraryTab`) | Matériaux | the list (searched, filtered, by category), the sheet in folds, the right pane of modules -- the engineer's own files, not the project's: no store of cases, no «Affichage», no Ctrl+S, no `save` the autosave would call; its domain is its `STORE` | written (v0.125, issue #110); beside `TabHost` rather than on it (Q-005): one base for both is a later step |

A type is a recipe by default, not a cage: a tab takes another service in place of one (`swap(SERVICES, old, new)`) or one more (`SERVICES + (…,)`). **A feature that could serve a second tab is a service**, even where one tab uses it today (D-19): the drawing of a build-up of layers, a big piece of work to come, will be one, reading the model of layers its domain gives without Qt (`contracts.Layer`, `dead_load_source.layers`; `NEEDS = ("layers",)`, D-14).

### A complete example: a tab of calculation

The snow is all of it (`calc/tools/snow_tab.py`):

```python
class SnowTab(calc_tab.CalcTab):
    KEY = "tab_ac_snow"
    MODULE = snow_source
    ID_PREFIX = "SN-"
    LIST_KEY = "sn_list"
    EMPTY_KEY = "sn_empty"
```

To add a tab of calculation -- the wind is the next:

1. **Its domain** (`calc/domains/<topic>_source.py`, Qt-free) gives what its type's services ask (`NEEDS`): `declaration()` -- its sections and fields (`contracts.Declaration`, `Field`, `Choice`), the norm file its excerpts are read from --, `visible_fields(src)`, `messages(src)` (`contracts.Message`: an error stops the calculation, an info is only said), `results(instance)`, and its source's functions (`new_source`, `check_source`, `read_source`, `build_instance`, `stamp_version`, `LINKABLE`, `FOLDER`, `DOMAIN`, `ID_PATTERN`); optionally `figure_svg`, `tile_svg`, `chart`, `extra_dependencies`. Results in tables are the instance's `tables`, which «Résultats» shows after the values. A domain that lacks a function a service needs stops the tab as it is built, naming the tab, the service and the function.
2. **The excerpts of its norm** in its norm file (`calc/norms/<norm>.json`), each held to the shipped PDF by a test.
3. **The generator of its file** (`calc/domains/unfold.py` `GENERATORS`) and, the file following its case, its kind in `unfold.AUTO_REGENERATE`.
4. **Its class**, parameters only, on `CalcTab`; **its `TabSpec`** in `tab_registry.SPECS`; **its icon** in `chrome.ICONS`; **its words** (`<topic>_tab_words.py`: its title, its list's words, `<prefix>s_…`, `<prefix>f_…`, `<prefix>msg_…`, `<prefix>x_…`) merged by `woodcore_gui_words.py`.
5. **Its tests**: its domain's, and its tab's through `tab.service("form")`, `tab.service("modules")`, `tab.ctx`.

`tests/test_calc_tab_base.py` mounts the type on a domain invented for it (`tests/fake_domain.py`) by a class of parameters alone, and finds no word of a domain in the type and its services; `tests/test_tab_overrides.py` refuses any method -- or any other name -- a tab on a type writes beyond its parameters and its type's `HOOKS` (none for «Calcul»).

### A complete example: a tab of a document

«Projet» is all of it (`calc/tools/project_tab.py`; its services in `project_services.py`):

```python
class ProjectTab(DocumentTab):
    KEY = KEY
    VIEWS = ("details", "templates")
    SERVICES = (ProjectActions, ProjectDetails, ProjectTemplates)
    UNSAVED_WORDS = ("tab_project", "pj_title_card")
```

`ProjectActions` (no pane) writes -- `WRITERS = ("write_apply_form", "write_create_document")` -- and offers its acts and what both pages list (`PROVIDES`); `ProjectDetails` (the view `details`) is the title page, its draft and its `save`; `ProjectTemplates` (the view `templates`) the preview built off the window's thread, delivered to a `QObject` of the page (ARCH-009), and the tab's splitter. Their buttons call `ctx.provide("write_apply_form")(ref)`: no service holds another. «Structure du document» is `SERVICES = (DocumentStructure,)`: the tab of before, renamed `StructureView` with its three mixins, mounted whole (`WIDGET`), the service forwarding the phases to it; cutting it into the tree, the page and the options is an issue of its own. `tests/test_document_tab.py` mounts the type on invented services, `tests/test_tab_frame.py` the bare frame.

### A complete example: a tab of data

«Dépendances» is all of it (`calc/tools/dependencies_tab.py`):

```python
class DependenciesTab(DataTab):
    KEY = KEY
    MODULE = graph_model
    SERVICES = DataTab.SERVICES + (DependenciesBrowser,)
```

`DependenciesBrowser` (`NEEDS = ("read", "newer_sources", "upstream", "downstream")` of `graph_model`) builds the filter, the splitter of two panes and its lists in `mount(ctx)`, reads the graph again in the phase `shown`, keeps the filter and the object chosen in `state()`, and says to the banner whether the graph is missing or older than its sources (`ctx.say`). «Variables» adds **`EXPOSES`**: what the window (`begin_variable_pick`), «Domaines», the linked fields and the command palette call on the tab by name -- `begin_pick`, `select_key`, `search`… -- is its browser's, and the tab declares those names, `EXPOSES = {name: "browser" …}`; the type sets on its class, for each, an `Exposed` descriptor that reads a bound method or an attribute of the service and writes on it, so no caller changes (D-06). A name the service lacks is an `AttributeError`, so `hasattr` stays true; `tests/test_tab_overrides.py` admits an exposed name only where the type set the descriptor. `tests/test_data_tab.py` mounts the type on invented services.

### Where the tabs stand

The snow, the permanent loads, the wind and the four member checks are on the type «Calcul», «Projet» and «Structure du document» on the type «Document», «Variables», «Métré», «Dépendances» and «Commandes» on the type «Données» (issue #106), since v0.125 (`snow_tab.py`, `dead_load_tab.py`, `wind_tab.py`; `load_tab.LoadTab` removed with the wind's issue #100, its list's words in `load_words.py`). Every other tab still derives from `source_editor.SourceEditorTab` or `canvas_editor.CanvasEditorTab`, which call the same rules of a list and a draft, and moves onto its type in its own issue. Whether a tab will one day be a line of its `TabSpec` rather than a class is decided once every tab is thin (D-17).
