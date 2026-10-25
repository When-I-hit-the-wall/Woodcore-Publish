"""The window's words in its three languages -- its own, then every tab's, every view's, every pane's merged in (each module's STRINGS) -- split out of calc/tools/woodcore_gui.py (issue #30), moved verbatim with the loops that merge them. woodcore_gui.py imports every name back, so woodcore_gui.STRINGS is still the one table the window reads.
"""

import home_page  # noqa: E402  -- the start page, the project dialog, the File menu's words (v0.83)
import migrate_dialog  # noqa: E402  -- a project laid out as one report, offered its migration into three documents as it opens
import grouped_list  # the left pane of every editor tab: folders, drag and drop, Ctrl/Shift (grouped_list.py)
import identity  # the Nom · Description · ID rows the editor tabs share (identity.py)
import views  # the views of a tab and the switch in the top bar that chooses one (views.py, v0.117)
import autosave  # saving without a question when a tab, a view, a document or the window is left (autosave.py, v0.117)
import notices_ui  # noqa: E402  -- the red octagon and the orange triangle at the top right, and their panel (v0.117)
import display_options  # the option panels of the «Affichage» views, one per command (display_options.py, v0.117)
import plan_tab  # noqa: E402
import fire_tab  # noqa: E402  -- the fire protection plan tab (v0.115), the position plan's sibling on the same base: its texts join STRINGS below, its class TABS
import positions_tab
import metre_tab  # the «Métré» tab under «Positions» (spec 2026-10-21-commandes-typst-refonte, UI-003)  # noqa: E402
import list_file_card  # the card of a list written once in raw Typst (spec 2026-10-21-commandes-typst-refonte, Q-008)  # noqa: E402
import action_tabs  # the words of the six empty tabs of «Actions» (v0.117, docs/ui/window.md §10quater)  # noqa: E402
import load_words  # the loads entered in Woodcore: the list's words of «Poids propre et surcharge», «Neige», «Vent» (issues #35-#37; load_tab.py's until spec 2026-10-23-onglet-vent-briques)  # noqa: E402
import fire_check_tab_words  # the words of the «Résistance au feu» tab (issue #46)  # noqa: E402
import steel_tab_words  # the words of the «Acier» tabs (issues #50-#52)  # noqa: E402
import calc_tab_words  # the calculation tabs' base (spec 2026-10-22-onglet-neige-type)  # noqa: E402
import snow_tab_words  # the «Neige» tab (issue #94)  # noqa: E402
import wind_tab_words  # the «Vent» tab (issue #100)  # noqa: E402
import materials_tab_words  # the «Matériaux» tab (issue #110)  # noqa: E402
import member_check_tab  # the member checks of SIA 265 chapter 4 -- «Traction» and the placeholders of the two navigation groups «Sécurité structurale» and «Aptitude au service» (docs/domain/member-checks.md §3.3undecies, docs/ui/window.md §10quater)  # noqa: E402
import journal_tab  # the journal tab (v0.99): the report's revisions, written by hand (docs/domain/journal.md §3.3terdecies)  # noqa: E402
import annex_tab  # the annexes tab (v0.115): the documents the report draws on, and the excerpts it shows of them (docs/domain/annexes.md §3.3undevicies)  # noqa: E402
import structure_tab  # the «Structure du document» tab, the one tab a document is written in (the rework of 01.10.2026): its tree of chapters, sections and objects, the page of what is chosen, the options of its kind, and what is shared with the other documents (structure_tab.py)  # noqa: E402
import python_tab  # the Python tab (v0.100): the engineer writes Python, runs it and the report reads its named results (docs/domain/scripts.md §3.3sexdecies)  # noqa: E402
import formula_tab  # the «Formule» tab (v0.117): calculation domains written as blocks of var, eq, verify, val, one Formules/<id>.typ each (calc/domains/formula_domain.py)  # noqa: E402
import linkable_spin  # the button beside a field that may follow a variable, and its linked state (spec 2026-10-11-variables-liees-champs-et-textes)
import text_pane  # the right pane of a text placed with the Text tool (issue #43)
import variables_words  # the «Variables» tab's words (spec 2026-10-24-onglet-variables-groupes, ARCH-006)  # noqa: E402
import command_palette  # the command palette, Ctrl+K (issue #83)  # noqa: E402
import project_tab  # the «Projet» tab: the project's basic data, its templates and its documents (issues #87, #88, #90)  # noqa: E402
import dependencies_tab  # the «Dépendances» tab: the graph of the project's objects (issue #71)  # noqa: E402
import statics_tab  # noqa: E402
import schema_tab  # noqa: E402
import commands_tab
import connectors_tab  # noqa: E402
import bundle_view  # noqa: E402


# Every piece of text the window itself prints, in its three languages. The labels of the values stay those of the data (German, as in the workbook): they are the engineer's, not the window's.
STRINGS = {
    "fr": {
        "open_tab_picking": "Un champ attend une valeur : terminez d'abord le choix (« Importer » ou « Annuler »).",
        "open_tab_not_shown": "L'onglet {tab} n'est pas dans « {document} » : choisissez le document qui le montre.",
        "open_tab_not_made": "« {document} » n'est pas encore fait : seul l'onglet Projet s'ouvre.",
        "open_tab_reserved": "L'onglet {tab} est réservé à un calcul à venir.",
        "language": "Langue",
        "reexport": "Import données",
        "reexport_what": "les cas et les dessins de Woodcore",
        "export_pdf": "Exporter PDF",
        "pdf_as_written": "Tel qu'écrit (document)",
        "pdf_base_level": "Niveau de détail de base",
        "pdf_uniform_level": "Niveau de détail uniforme",
        "pdf_level_n": "Niveau {n}",
        "pdf_uniform_n": "Uniforme {n}",
        "pdf_doc_language": "Langue du document",
        "pdf_settings": "Réglages : {detail}",
        "pdf_document": "Exporte : {document}",
        "pdf_all": "Exporter les trois",
        "nav_document": "Le document écrit : les modules qu'il montre, son journal et son PDF",
        "doc_stamp_unchanged": "{document} : inchangé depuis son PDF",
        "reload": "Recharger",
        "nav_document_group": "Document",
        "nav_project": "Données",   # the group «Projet» until 0.122, the tab of that name first in the navigation since (issue #87); the key kept
        "nav_actions": "Actions",
        "nav_structure": "Structure",
        "nav_connections": "Assemblages",
        "nav_reference": "Référence",
        "nav_others": "Autres",   # the engineer's own files, not the project's: the «Matériaux» tab (issue #110)
        "nav_collapse": "Réduire le menu à ses icônes",
        "nav_expand": "Déplier le menu",
        "pdf_chip_tip": "Le prochain PDF sera compilé ainsi. Cliquer pour changer.",
        "meta_number": "N° {number}",
        "tab_combinations": "Combinaisons de charges",
        "tab_polar": "Moments polaires",
        "future": "Implémentation future.",
        "future_combinations": "Les combinaisons ELU/ELS seront calculées dans calc/domains/combinations.py (docs/domain/loads.md §3.5) et listées ici, avec les commandes Typst pour les afficher.",
        "polar_list": "Calculs",
        "polar_new": "Nouveau calcul",
        "polar_duplicate": "Dupliquer",
        "polar_delete": "Supprimer le calcul",
        "polar_save": "Enregistrer",
        "polar_revert": "Annuler les modifications",
        "polar_revert_tip": "Remet le calcul tel qu'il est enregistré ; grisé tant que rien n'est modifié.",
        "polar_new_item": "(nouveau, non enregistré)",
        "polar_moved": "{count} calcul(s) déplacé(s) dans « {group} ».",
        "list_write_failed": "« {id} » n'a pas pu être écrit — le déplacement s'arrête là : {error}",
        "polar_empty": "Aucun calcul : « Nouveau calcul » en crée un sur le premier schéma de l'onglet « Schémas ».",
        "polar_list_hint": "Glissez les calculs dans des dossiers (clic droit : nouveau dossier).",
        "polar_name": "Nom",
        "polar_id_auto": "Tiré du nom ; peut être écrasé.",
        "polar_id": "ID",
        "polar_label": "Description",
        "polar_member": "Élément {n}",
        "polar_member_name": "Nom",
        "polar_members": "Éléments",
        "polar_reference": "Élément de référence (angles θ)",
        "polar_reference_tip": "L’élément dont les angles θ des autres éléments sont comptés. Les axes x et z sont ceux du schéma.",
        "polar_add_member": "Ajouter un élément",
        "polar_remove_member": "Retirer cet élément",
        "polar_fasteners": "Moyens d’assemblage",
        "polar_center": "Centre de rotation",
        "polar_centroid": "Centre de gravité des moyens d’assemblage",
        "polar_identity": "Identité",
        "polar_schema": "Schéma",
        "polar_no_schema": "— aucun —",
        "polar_schema_none_notice": "Aucun schéma : choisissez-en un, ou dessinez-le dans l'onglet « Schémas ». Le rapport ne peut pas imprimer ce calcul sans dessin.",
        "polar_schema_gone": "Le schéma {sid} n'existe plus. Choisissez-en un autre.",
        "polar_schema_holds": "{n} élément(s), {m} repère(s), {p} point(s) coché(s) « moyen d’assemblage ».",
        "polar_element": "Élément du schéma",
        "polar_member_name": "Désignation",
        "polar_marker": "Repère",
        "polar_markers_note": "Les repères de moyens d’assemblage et les points de construction sont dessinés dans l'onglet « Schémas » ; cochez ici ceux que ce calcul reprend. Le type de moyen d’assemblage n'entre pas en compte : un moment polaire répartit des forces sur des points.",
        "polar_kind_marker": "Repère de moyen d’assemblage",
        "polar_kind_point": "Point de construction",
        "polar_tick_all": "Tout cocher",
        "polar_tick_none": "Tout décocher",
        "polar_aid": "Centre du schéma",
        "polar_manual": "Point fixé",
        "polar_directions": "Directions des efforts",
        "polar_directions_note": "Angles comptés de x vers z (sens horaire sur le dessin). M est positif dans l'autre sens, de z vers x (anti-horaire).",
        "polar_dir_N": "Effort normal N",
        "polar_dir_V": "Effort tranchant V",
        "polar_figure": "Graphique",
        "polar_results": "Résultats",
        "polar_trial": "Aperçu des efforts (non enregistré)",
        "polar_trial_result": "F_max = {f} kN — moyen(s) d’assemblage {k}\nF_x = {fx} kN · F_z = {fz} kN\n{betas}",
        "polar_no_moment": "I_p = 0 : les moyens d’assemblage n'ont aucun bras de levier, M ne peut pas être repris.",
        "polar_unsaved_hint": "Enregistrer d'abord : Typst ne connaît que les calculs enregistrés.",
        "polar_saved": "« {id} » enregistré, data/connections.json mis à jour.",
        "polar_save_failed_title": "Enregistrement impossible",
        "polar_export_failed": "« {id} » est enregistré, mais l'export des calculs a échoué ; Typst voit encore les données précédentes.\n\n{error}",
        "polar_id_exists": "Un calcul « {id} » existe déjà.",
        "polar_id_invalid": "Identifiant « {id} » : lettres, chiffres et _ . + - seulement, en commençant par une lettre ou un chiffre.",
        "polar_warnings_status": "{count} avertissement(s) à l'export.",
        "polar_rename": "« {old} » sera renommé « {new} » : les appels Typst qui utilisent « {old} » ne fonctionneront plus. Continuer ?",
        "polar_unsaved_title": "Modifications non enregistrées",
        "polar_unsaved": "Le calcul « {id} » a des modifications non enregistrées.",
        "polar_unreadable": "{name} est illisible : {error}",
        "search": "Recherche",
        "commands": "Commandes Typst",
        "copy": "Copier",
        "copied": "Copié : {text}",
        "copied_short": "Copié ✓",
        "exporting": "Export en cours…",
        "busy_loading": "Chargement…",
        "busy_opening": "Ouverture de « {name} »…",
        "busy_installing": "Installation des paquets…",
        "busy_switching": "Changement de document…",
        "export_ok": "Export terminé, données rechargées.",
        "export_failed_title": "Échec de l'export",
        "engine_title": "Moteur du projet",
        "engine_older": "Ce projet utilise le moteur de Woodcore {version}. Le mettre à jour vers {ours} ? Le rapport peut s'imprimer différemment ensuite.",
        "engine_edited": "Le moteur Typst copié dans ce projet a été modifié à la main ({files}). Le remplacer par le moteur de Woodcore {ours} effacerait ces modifications.\n\nSi la modification doit être gardée, reportez-la d'abord dans le programme. Les différences sont sous « Voir les différences… ».",
        "engine_newer": "Ce projet a été exporté par Woodcore {version}, plus récent que ce programme ({ours}). Ouvrez-le avec cette version, ou une plus récente : ce programme n'y écrira rien.",
        "engine_newer_open": "Le moteur de ce projet a été écrit par Woodcore {version}, plus récent que ce programme ({ours}). Cette fenêtre n'exportera rien dans ce projet : pour l'exporter, ouvrez-le avec Woodcore {version} ou une version plus récente.",
        "engine_update": "Mettre à jour et exporter",
        "engine_update_now": "Mettre à jour",
        "engine_overwrite": "Écraser et exporter",
        "engine_overwrite_now": "Écraser",
        "engine_later": "Plus tard",
        "engine_diff": "Voir les différences…",
        "engine_diff_title": "Le moteur du projet et celui de Woodcore {ours}",
        "engine_diff_none": "Aucune différence dans les fichiers du moteur.",
        "engine_synced": "Moteur Typst du projet mis à jour vers Woodcore {ours}.",
        "engine_sync_failed": "Le moteur du projet n'a pas pu être mis à jour : {error}",
        "engine_unknown": "Ce projet contient un moteur Typst qu'aucun fichier VERSION ne nomme ({files}) : celui d'un dossier organisé avant Woodcore. Le remplacer par le moteur de Woodcore {ours} ? Le rapport peut s'imprimer différemment ensuite.",
        "export_failed": "L'export a échoué (code {code}) ; les données précédentes restent affichées.\n\n{output}",
        "compiling": "Compilation en cours : {document}…",
        "pdf_ready": "{document} : PDF écrit ({name})",
        "archive_failed": "PDF non archivé : {reason}",
        "compile_failed_title": "Échec de la compilation",
        "close_after_export": "Export en cours — la fenêtre se fermera dès qu'il sera terminé.",
        "close_after_compile": "Compilation en cours — la fenêtre se fermera dès qu'elle sera terminée.",
        "loaded": "{count} valeurs · export du {date}",
        "deps_title": "Dépendances",
        "deps_mismatch": "Ce que le projet demande n'est pas ce qui est installé :\n\n{detail}\n\nLe rapport a été vérifié avec les versions de requirements.txt. Les installer maintenant ?",
        "deps_line_missing": "  • {name} {wanted} — absent",
        "deps_line_other": "  • {name} {wanted} — {found} installé",
        "deps_update": "Mise à jour disponible : {detail}.",
        "deps_update_one": "{name} {pinned} → {available}",
        "deps_update_button": "Installer",
        "deps_update_ask": "Installer {detail} et inscrire la nouvelle version dans requirements.txt ?\n\nLe rapport a été vérifié avec les versions actuelles : rebâtissez-le et relancez les tests après la mise à jour.",
        "deps_ok": "Installé. Redémarrez Woodcore pour que la nouvelle version soit chargée.",
        "deps_failed": "L'installation a échoué :\n\n{output}",
        "startup_error": "Woodcore n'a pas pu démarrer :\n\n{error}",
        "open_project_title": "Ouvrir un projet Woodcore",
        "open_project_filter": "Projets Woodcore (*.woodcore)",
        # the warnings of the editors, by the code a domain module's engine.Note carries (periodic audit 260916, AUD-4-11)
        "warn_plan_no_number": "Plan {plan}\u202f: l’élément {i} ({type}) n’a pas de numéro de position.",
        "warn_plan_unknown": "Plan {plan}\u202f: {label} n’est pas une position du projet — ajoutez-la dans l’onglet Positions.",
        "warn_formula_misnamed": "{file} : le domaine déclare un autre nom que son fichier ({domain}) ; il est exporté tel quel, et l’onglet « Domaines » réécrit son id à la prochaine sauvegarde.",
        "warn_load_workbook_not_read": "Un classeur de charges est présent dans le dossier du projet ({files}) : Woodcore ne le lit plus. Les cas de vent, de neige et de charges permanentes se saisissent dans les onglets « Vent », « Neige » et « Poids propre et surcharge ».",
        "warn_calculations_old_export": "data/calculations.json a été écrit par une version antérieure de Woodcore (schéma {version}, celle-ci écrit {current}) : le rapport ne compile pas tant que « Import données » ne l'a pas réécrit une fois.",
        "warn_sync_stale": "{file}, ligne {line} : #sync(\"{id}\") écrit {written}, et l'export tient {held} -- rafraîchir la valeur, ou retirer #sync pour la garder telle quelle.",
        "warn_plan_dimensions_no_scale": "Plan {plan} : {count} cote(s) mesurent des longueurs et le plan n’a pas d’échelle ; calibrez-le, sinon elles ne sont pas dessinées.",
        "warn_dep_changed": "{node} a changé depuis le dernier export ; en dépendent, {kind} : {ids}.",
        "warn_dep_cycle": "{chain} : ces objets se lisent en cercle ; un export ne les accorde que par hasard.",
        "warn_dep_kind_position": "positions",
        "warn_dep_kind_load": "charges",
        "warn_dep_kind_script": "scripts",
        "warn_dep_kind_formula": "domaines",
        "warn_dep_kind_check": "vérifications bois",
        "warn_dep_kind_steel": "vérifications acier",
        "warn_dep_kind_profile": "profilés",
        "warn_dep_kind_connector": "connecteurs",
        "warn_dep_kind_connection": "moments polaires",
        "warn_dep_kind_schema": "schémas",
        "warn_dep_kind_statics": "modèles statiques",
        "warn_dep_kind_plan": "plans",
        "warn_dep_kind_document": "documents",
        "warn_dep_kind_fire": "plans de protection incendie",
        "warn_dep_kind_extract": "extraits",
        "warn_dep_kind_section": "sections du rapport",
        "warn_snow_above_limit": "{where} : h_0 = {h_0} m dépasse les {limit} m de la SIA 261 {ref} ; ses dispositions ne s’y appliquent pas.",
        "warn_wind_c_red_outside": "{where} : la surface de référence {area} a h = {h} m et β = {beta}, que la SIA 261 {ref} ne trace pas ; c_red est lu au bout de la courbe la plus proche.",
        "warn_wind_no_library": "{where} : la figure du tableau {table} de la SIA 261 n’est pas découpée, {files} n’est pas dans norm-library/ ; le fichier s’écrit sans elle.",
        "warn_plan_wrong_type": "Plan {plan}\u202f: {label} est dessiné avec le symbole {type} ({name}).",
        "warn_plan_outside": "Plan {plan}\u202f: {label} est hors du cadrage et n’apparaîtra pas dans le rapport.",
        "warn_script_failed": "Le script {script}\u202f: {reason}",
        "warn_domain_file_orphan": "{file}\u202f: aucun domaine de ce dossier ne porte plus ce nom — le fichier est le vôtre et reste où il est.",
        "warn_unfold_stub_edited": "{file}\u202f: la vérification {id} est imprimée dépliée, et son fichier contient ce que vous avez écrit à la place du stub de Woodcore — il reste tel quel, et la vérification est imprimée repliée tant que vous ne le videz pas.",
        "warn_retired_key": "{file}\u202f: {key} est ignoré — l’import RFEM a été retiré en 0.117 (archive/rfem/). Retirez la clé du fichier du projet pour ne plus voir ce message.",
        "warn_plan_number_outside": "Plan {plan}\u202f: le numéro de {label} a été déplacé hors du cadrage, le rapport le couperait.",
        "warn_plan_centres_no_walls": "Plan {plan}\u202f: aucune paroi de contreventement (H, W) n’est dessinée — pas de centre de rigidité.",
        "warn_plan_centres_no_mode": "Plan {plan}\u202f: {count} paroi(s) de contreventement sans mode de construction ({labels}) — le centre de rigidité n’est pas calculé.",
        "warn_plan_centres_mixed": "Plan {plan}\u202f: les parois de contreventement n’ont pas toutes le même mode de construction (ossature bois\u202f: {timber_frame}, CLT\u202f: {clt}, béton\u202f: {concrete}) — le centre de rigidité ne se calcule que pour un seul mode.",
        "warn_plan_centres_no_power": "Plan {plan}\u202f: les parois sont en CLT et la puissance de leur longueur (1,5 ou 2) n’est pas choisie — le centre de rigidité n’est pas calculé.",
        "warn_plan_centres_one_direction": "Plan {plan}\u202f: toutes les parois de contreventement ont la même direction — le centre de rigidité demande des parois dans deux directions au moins.",
        "warn_plan_centres_no_torsion": "Plan {plan}\u202f: les lignes d’action de toutes les parois de contreventement passent par un même point — l’étage n’a aucune rigidité en torsion.",
        "warn_plan_centres_no_outline": "Plan {plan}\u202f: aucun contour du bâtiment n’est dessiné — pas de centre de masse.",
        "warn_plan_centres_flat_outline": "Plan {plan}\u202f: le contour du bâtiment n’enferme aucune surface — pas de centre de masse.",
        "warn_plan_centres_section": "Plan {plan}\u202f: la position de {label} a une section CLT et la paroi est dessinée en {mode} — corrigez l’un des deux.",
        "warn_plan_construction_timber_frame": "ossature bois",
        "warn_plan_construction_clt": "CLT",
        "warn_plan_construction_concrete": "béton",
        "warn_statics_unread": "Modèle {model}\u202f: la valeur de la charge {load} n’a pas pu être lue — {detail}.",
        "warn_statics_unread_end": "Modèle {model}\u202f: la valeur de fin de la charge {load} n’a pas pu être lue — {detail}.",
        "warn_statics_no_variable": "la variable {ref} n’existe pas dans l’export",
        "warn_link_stale": "{where} : {field} garde sa dernière valeur — {detail}.",
        "warn_text_stale": "{where} : le texte imprime la dernière valeur de {field} — {detail}.",
        "warn_link_missing": "la variable {ref} n’existe pas dans l’export",
        "warn_link_not_a_number": "{ref} vaut {value}, qui n’est pas un nombre",
        "warn_link_unit": "{ref} est en {unit}, qui ne peut pas remplir une valeur en {field_unit}",
        "warn_link_not_allowed": "{ref} ne peut pas être nommée ici — une charge ne suit qu’une autre charge ou un domaine de l’onglet « Domaines »",
        "warn_statics_not_a_number": "{ref} vaut {value}, qui n’est pas un nombre",
        "warn_statics_no_magnitude": "l’intensité n’est ni une valeur ni une variable",
        "warn_statics_width_unit": "une charge en {unit} ne se multiplie pas par une largeur d’influence, qui multiplie une charge par mètre ou par mètre carré",
        "warn_statics_no_support": "Modèle {model}\u202f: rien ne le tient — il n’a aucun appui.",
        "warn_statics_idle_point": "Modèle {model}\u202f: le point {point} ne porte rien et ne tient rien.",
        "warn_statics_release_stiffness_shear": "Modèle {model}\u202f: l’articulation {release} libère l’effort tranchant et portait une raideur, qui est supprimée — un ressort le long d’une barre est un élément de type «\xa0Ressort\xa0».",
        "warn_statics_release_stiffness_normal": "Modèle {model}\u202f: l’articulation {release} libère l’effort normal et portait une raideur, qui est supprimée — un ressort le long d’une barre est un élément de type «\xa0Ressort\xa0».",
        "warn_schema_unresolved": "Schéma {schema}\u202f: l’élément {entry} renvoie à la position {position}, que l’onglet Positions ne contient pas.",
        "warn_schema_section_unread": "Schéma {schema}\u202f: la dimension «\xa0{dimension}\xa0» de la position {position} ne se lit pas comme b/h — indiquez {view} sur l’élément {entry}\u202f; il est dessiné large de {width} mm d’ici là.",
        "warn_schema_section_none": "Schéma {schema}\u202f: l’élément {entry} n’a ni position ni {view} — choisissez sa position ou indiquez sa section\u202f; il est dessiné large de {width} mm d’ici là.",
        "warn_schema_crop_element": "Schéma {schema}\u202f: {entry} est entièrement hors du cadrage — le rapport ne le montrera pas.",
        "warn_schema_crop_marker": "Schéma {schema}\u202f: {entry} est hors du cadrage — le rapport ne le montrera pas.",
        "warn_polar_no_schema": "{connection} n’est dessiné sur aucun schéma — choisissez-en un (schémas\u202f: {schemas})\u202f; le rapport ne peut pas l’imprimer d’ici là.",
        "warn_polar_no_schema_none": "{connection} n’est dessiné sur aucun schéma, et il n’en existe encore aucun — dessinez-en un dans l’onglet «\xa0Schémas\xa0»\u202f; le rapport ne peut pas l’imprimer d’ici là.",
        "warn_polar_schema_gone": "{connection} est dessiné sur le schéma {schema}, que l’export ne contient pas — choisissez-en un parmi {schemas}\u202f; le rapport ne peut pas l’imprimer d’ici là.",
        "warn_polar_schema_gone_none": "{connection} est dessiné sur le schéma {schema}, que l’export ne contient pas, et il n’existe encore aucun schéma\u202f; le rapport ne peut pas l’imprimer d’ici là.",
        "warn_polar_markers_lost": "{connection}\u202f: le schéma {schema} ne porte plus le(s) repère(s) ou point(s) {ids} — cochez à nouveau les moyens d’assemblage\u202f; ils sont laissés hors du calcul.",
        "warn_polar_elements_lost": "{connection}\u202f: le schéma {schema} ne porte plus le(s) élément(s) {ids} — choisissez à nouveau les éléments des pièces\u202f; leurs angles sont pris à 0°.",
        "warn_polar_centre_lost": "{connection}\u202f: le schéma {schema} ne porte plus le centre {centre} — le centre de gravité des moyens d’assemblage le remplace.",
    },
    "de": {
        "open_tab_picking": "Ein Feld wartet auf einen Wert: beenden Sie zuerst die Auswahl («Importieren» oder «Abbrechen»).",
        "open_tab_not_shown": "Der Reiter {tab} gehört nicht zu «{document}»: wählen Sie das Dokument, das ihn zeigt.",
        "open_tab_not_made": "«{document}» ist noch nicht angelegt: nur der Reiter Projekt lässt sich öffnen.",
        "open_tab_reserved": "Der Reiter {tab} ist für eine künftige Berechnung reserviert.",
        "language": "Sprache",
        "reexport": "Daten importieren",
        "reexport_what": "die Fälle und die Zeichnungen aus Woodcore",
        "export_pdf": "PDF exportieren",
        "pdf_as_written": "Wie im Dokument",
        "pdf_base_level": "Basis-Detailstufe",
        "pdf_uniform_level": "Einheitliche Detailstufe",
        "pdf_level_n": "Stufe {n}",
        "pdf_uniform_n": "Einheitlich {n}",
        "pdf_doc_language": "Sprache des Dokuments",
        "pdf_settings": "Einstellungen: {detail}",
        "pdf_document": "Exportiert: {document}",
        "pdf_all": "Alle drei exportieren",
        "nav_document": "Das Dokument, das geschrieben wird: die Module, die es zeigt, sein Journal und sein PDF",
        "doc_stamp_unchanged": "{document}: seit seinem PDF unverändert",
        "reload": "Neu laden",
        "nav_document_group": "Dokument",
        "nav_project": "Daten",
        "nav_actions": "Einwirkungen",
        "nav_structure": "Tragwerk",
        "nav_connections": "Verbindungen",
        "nav_reference": "Referenz",
        "nav_others": "Weitere",
        "nav_collapse": "Menü auf seine Symbole einklappen",
        "nav_expand": "Menü ausklappen",
        "pdf_chip_tip": "Das nächste PDF wird so kompiliert. Klicken, um es zu ändern.",
        "meta_number": "Nr. {number}",
        "tab_combinations": "Lastkombinationen",
        "tab_polar": "Polare Trägheitsmomente",
        "future": "Noch nicht umgesetzt.",
        "future_combinations": "Die Lastkombinationen (Tragsicherheit/Gebrauchstauglichkeit) werden in calc/domains/combinations.py berechnet (docs/domain/loads.md §3.5) und hier aufgelistet, mit den Typst-Befehlen, die sie ausgeben.",
        "polar_list": "Berechnungen",
        "polar_new": "Neue Berechnung",
        "polar_duplicate": "Duplizieren",
        "polar_delete": "Berechnung löschen",
        "polar_save": "Speichern",
        "polar_revert": "Änderungen verwerfen",
        "polar_revert_tip": "Stellt die Berechnung wieder her, wie sie gespeichert ist; grau, solange nichts geändert ist.",
        "polar_new_item": "(neu, nicht gespeichert)",
        "polar_moved": "{count} Berechnung(en) nach «{group}» verschoben.",
        "list_write_failed": "«{id}» konnte nicht geschrieben werden — das Verschieben bricht hier ab: {error}",
        "polar_empty": "Keine Berechnung: »Neue Berechnung« legt eine auf dem ersten Schema des Reiters »Schemas« an.",
        "polar_list_hint": "Berechnungen lassen sich in Ordner ziehen (Rechtsklick: neuer Ordner).",
        "polar_name": "Name",
        "polar_id_auto": "Aus dem Namen gebildet; kann überschrieben werden.",
        "polar_id": "ID",
        "polar_label": "Beschreibung",
        "polar_member": "Element {n}",
        "polar_member_name": "Name",
        "polar_members": "Elemente",
        "polar_reference": "Bezugselement (Winkel θ)",
        "polar_reference_tip": "Das Element, von dem aus die Winkel θ der anderen Elemente gezählt werden. Die Achsen x und z sind jene des Schemas.",
        "polar_add_member": "Element hinzufügen",
        "polar_remove_member": "Dieses Element entfernen",
        "polar_fasteners": "Verbindungsmittel",
        "polar_center": "Drehpunkt",
        "polar_centroid": "Schwerpunkt der Verbindungsmittel",
        "polar_identity": "Identität",
        "polar_schema": "Schema",
        "polar_no_schema": "— keines —",
        "polar_schema_none_notice": "Kein Schema: wählen Sie eines, oder zeichnen Sie es im Reiter «Schemas». Ohne Zeichnung kann der Bericht diese Berechnung nicht drucken.",
        "polar_schema_gone": "Das Schema {sid} gibt es nicht mehr. Wählen Sie ein anderes.",
        "polar_schema_holds": "{n} Element(e), {m} Marke(n), {p} Punkt(e) als Verbindungsmittel.",
        "polar_element": "Element des Schemas",
        "polar_member_name": "Bezeichnung",
        "polar_marker": "Marke",
        "polar_markers_note": "Die Verbindungsmittel-Marken und die Konstruktionspunkte werden im Reiter «Schemas» gezeichnet; hier werden die angekreuzt, die diese Berechnung übernimmt. Die Art des Verbindungsmittels spielt keine Rolle: ein polares Trägheitsmoment verteilt Kräfte auf Punkte.",
        "polar_kind_marker": "Verbindungsmittel-Marke",
        "polar_kind_point": "Konstruktionspunkt",
        "polar_tick_all": "Alle auswählen",
        "polar_tick_none": "Auswahl aufheben",
        "polar_aid": "Zentrum aus dem Schema",
        "polar_manual": "Festgelegter Punkt",
        "polar_directions": "Kraftrichtungen",
        "polar_directions_note": "Winkel von x nach z gezählt (im Uhrzeigersinn auf der Zeichnung). M ist im anderen Sinn positiv, von z nach x (Gegenuhrzeigersinn).",
        "polar_dir_N": "Normalkraft N",
        "polar_dir_V": "Querkraft V",
        "polar_figure": "Grafik",
        "polar_results": "Ergebnisse",
        "polar_trial": "Kräftevorschau (nicht gespeichert)",
        "polar_trial_result": "F_max = {f} kN — Verbindungsmittel {k}\nF_x = {fx} kN · F_z = {fz} kN\n{betas}",
        "polar_no_moment": "I_p = 0: Die Verbindungsmittel haben keinen Hebelarm, M kann nicht aufgenommen werden.",
        "polar_unsaved_hint": "Zuerst speichern: Typst kennt nur gespeicherte Berechnungen.",
        "polar_saved": "»{id}« gespeichert, data/connections.json aktualisiert.",
        "polar_save_failed_title": "Speichern nicht möglich",
        "polar_export_failed": "»{id}« ist gespeichert, aber der Export der Berechnungen ist fehlgeschlagen; Typst sieht noch die bisherigen Daten.\n\n{error}",
        "polar_id_exists": "Eine Berechnung »{id}« existiert bereits.",
        "polar_id_invalid": "Kennung »{id}«: nur Buchstaben, Ziffern und _ . + -, beginnend mit einem Buchstaben oder einer Ziffer.",
        "polar_warnings_status": "{count} Warnung(en) beim Export.",
        "polar_rename": "»{old}« wird in »{new}« umbenannt: Typst-Aufrufe mit »{old}« funktionieren dann nicht mehr. Fortfahren?",
        "polar_unsaved_title": "Nicht gespeicherte Änderungen",
        "polar_unsaved": "Die Berechnung »{id}« hat nicht gespeicherte Änderungen.",
        "polar_unreadable": "{name} ist nicht lesbar: {error}",
        "search": "Suche",
        "commands": "Typst-Befehle",
        "copy": "Kopieren",
        "copied": "Kopiert: {text}",
        "copied_short": "Kopiert ✓",
        "exporting": "Export läuft…",
        "busy_loading": "Wird geladen…",
        "busy_opening": "«{name}» wird geöffnet…",
        "busy_installing": "Pakete werden installiert…",
        "busy_switching": "Dokument wird gewechselt…",
        "export_ok": "Export abgeschlossen, Daten neu geladen.",
        "export_failed_title": "Export fehlgeschlagen",
        "engine_title": "Engine des Projekts",
        "engine_older": "Dieses Projekt verwendet die Engine von Woodcore {version}. Auf {ours} aktualisieren? Der Bericht kann danach anders gedruckt werden.",
        "engine_edited": "Die in dieses Projekt kopierte Typst-Engine wurde von Hand geändert ({files}). Sie durch die Engine von Woodcore {ours} zu ersetzen, löscht diese Änderungen.\n\nSoll die Änderung bleiben, übertragen Sie sie zuerst ins Programm. Die Unterschiede zeigt «Unterschiede anzeigen…».",
        "engine_newer": "Dieses Projekt wurde von Woodcore {version} exportiert, neuer als dieses Programm ({ours}). Öffnen Sie es mit dieser oder einer neueren Version: dieses Programm schreibt nichts hinein.",
        "engine_newer_open": "Die Engine dieses Projekts wurde von Woodcore {version} geschrieben, neuer als dieses Programm ({ours}). Dieses Fenster exportiert nichts in dieses Projekt: um es zu exportieren, öffnen Sie es mit Woodcore {version} oder einer neueren Version.",
        "engine_update": "Aktualisieren und exportieren",
        "engine_update_now": "Aktualisieren",
        "engine_overwrite": "Überschreiben und exportieren",
        "engine_overwrite_now": "Überschreiben",
        "engine_later": "Später",
        "engine_diff": "Unterschiede anzeigen…",
        "engine_diff_title": "Die Engine des Projekts und die von Woodcore {ours}",
        "engine_diff_none": "Keine Unterschiede in den Dateien der Engine.",
        "engine_synced": "Typst-Engine des Projekts auf Woodcore {ours} aktualisiert.",
        "engine_sync_failed": "Die Engine des Projekts konnte nicht aktualisiert werden: {error}",
        "engine_unknown": "Dieses Projekt enthält eine Typst-Engine, die keine VERSION-Datei nennt ({files}): die eines vor Woodcore angelegten Ordners. Durch die Engine von Woodcore {ours} ersetzen? Der Bericht kann danach anders gedruckt werden.",
        "export_failed": "Der Export ist fehlgeschlagen (Code {code}); die bisherigen Daten bleiben angezeigt.\n\n{output}",
        "compiling": "Kompilierung läuft: {document}…",
        "pdf_ready": "{document}: PDF geschrieben ({name})",
        "archive_failed": "PDF nicht archiviert: {reason}",
        "compile_failed_title": "Kompilierung fehlgeschlagen",
        "close_after_export": "Export läuft – das Fenster schliesst sich, sobald er fertig ist.",
        "close_after_compile": "Kompilierung läuft – das Fenster schliesst sich, sobald sie fertig ist.",
        "loaded": "{count} Werte · Export vom {date}",
        "deps_title": "Abhängigkeiten",
        "deps_mismatch": "Was das Projekt verlangt, ist nicht das, was installiert ist:\n\n{detail}\n\nDer Bericht wurde mit den Versionen aus requirements.txt geprüft. Jetzt installieren?",
        "deps_line_missing": "  • {name} {wanted} — fehlt",
        "deps_line_other": "  • {name} {wanted} — {found} installiert",
        "deps_update": "Aktualisierung verfügbar: {detail}.",
        "deps_update_one": "{name} {pinned} → {available}",
        "deps_update_button": "Installieren",
        "deps_update_ask": "{detail} installieren und die neue Version in requirements.txt eintragen?\n\nDer Bericht wurde mit den jetzigen Versionen geprüft: nach der Aktualisierung neu bauen und die Tests erneut laufen lassen.",
        "deps_ok": "Installiert. Woodcore neu starten, damit die neue Version geladen wird.",
        "deps_failed": "Die Installation ist fehlgeschlagen:\n\n{output}",
        "startup_error": "Woodcore konnte nicht starten:\n\n{error}",
        "open_project_title": "Woodcore-Projekt öffnen",
        "open_project_filter": "Woodcore-Projekte (*.woodcore)",
        # the warnings of the editors, by the code a domain module's engine.Note carries (periodic audit 260916, AUD-4-11)
        "warn_plan_no_number": "Plan {plan}: Element {i} ({type}) hat keine Positionsnummer.",
        "warn_plan_unknown": "Plan {plan}: {label} ist keine Position des Projekts – ergänzen Sie sie im Register Positionen.",
        "warn_formula_misnamed": "{file}: der Bereich nennt sich anders als seine Datei ({domain}); er wird so exportiert, und der Reiter «Domaines» schreibt seine ID beim nächsten Speichern zurück.",
        "warn_load_workbook_not_read": "Im Projektordner liegt eine Lastannahmen-Arbeitsmappe ({files}): Woodcore liest sie nicht mehr. Die Fälle von Wind, Schnee und ständigen Lasten werden in den Registern «Wind», «Schnee» und «Eigen- und Auflasten» erfasst.",
        "warn_calculations_old_export": "data/calculations.json wurde von einer früheren Version von Woodcore geschrieben (Schema {version}, diese schreibt {current}): der Bericht kompiliert nicht, bis «Daten importieren» die Datei einmal neu geschrieben hat.",
        "warn_sync_stale": "{file}, Zeile {line}: #sync(\"{id}\") schreibt {written}, und der Export hält {held} -- den Wert auffrischen oder #sync entfernen, um ihn so zu behalten.",
        "warn_plan_dimensions_no_scale": "Plan {plan}: {count} Kote(n) messen Längen und der Plan hat keinen Massstab; kalibrieren Sie ihn, sonst werden sie nicht gezeichnet.",
        "warn_dep_changed": "{node} hat sich seit dem letzten Export geändert; davon hängen ab, {kind}: {ids}.",
        "warn_dep_cycle": "{chain}: diese Objekte lesen einander im Kreis; ein Export stimmt sie nur zufällig ab.",
        "warn_dep_kind_position": "Positionen",
        "warn_dep_kind_load": "Lasten",
        "warn_dep_kind_script": "Skripte",
        "warn_dep_kind_formula": "Bereiche",
        "warn_dep_kind_check": "Holznachweise",
        "warn_dep_kind_steel": "Stahlnachweise",
        "warn_dep_kind_profile": "Profile",
        "warn_dep_kind_connector": "Verbindungsmittel",
        "warn_dep_kind_connection": "polare Momente",
        "warn_dep_kind_schema": "Schemas",
        "warn_dep_kind_statics": "statische Modelle",
        "warn_dep_kind_plan": "Pläne",
        "warn_dep_kind_document": "Dokumente",
        "warn_dep_kind_fire": "Brandschutzpläne",
        "warn_dep_kind_extract": "Auszüge",
        "warn_dep_kind_section": "Abschnitte des Berichts",
        "warn_snow_above_limit": "{where}: h_0 = {h_0} m liegt über den {limit} m der SIA 261 {ref}; ihre Bestimmungen gelten dort nicht.",
        "warn_wind_c_red_outside": "{where}: die Bezugsfläche {area} hat h = {h} m und β = {beta}, was SIA 261 {ref} nicht zeichnet; c_red wird am Ende der nächsten Kurve abgelesen.",
        "warn_wind_no_library": "{where}: Die Figur der Tabelle {table} der SIA 261 ist nicht ausgeschnitten, {files} liegt nicht in norm-library/; die Datei wird ohne sie geschrieben.",
        "warn_plan_wrong_type": "Plan {plan}: {label} ist mit dem Symbol {type} ({name}) gezeichnet.",
        "warn_plan_outside": "Plan {plan}: {label} liegt ausserhalb des Ausschnitts und erscheint nicht im Bericht.",
        "warn_script_failed": "Das Skript {script}: {reason}",
        "warn_domain_file_orphan": "{file}: kein Bereich dieses Ordners trägt diesen Namen mehr — die Datei gehört Ihnen und bleibt, wo sie ist.",
        "warn_unfold_stub_edited": "{file}: der Nachweis {id} wird entfaltet gedruckt, und seine Datei enthält, was Sie an Stelle des Platzhalters von Woodcore geschrieben haben — sie bleibt, wie sie ist, und der Nachweis wird gefaltet gedruckt, bis Sie sie leeren.",
        "warn_retired_key": "{file}: {key} wird ignoriert — der RFEM-Import wurde in 0.117 entfernt (archive/rfem/). Entfernen Sie den Schlüssel aus der Projektdatei, damit diese Meldung verschwindet.",
        "warn_plan_number_outside": "Plan {plan}: Die Nummer von {label} wurde aus dem Ausschnitt geschoben; der Bericht würde sie abschneiden.",
        "warn_plan_centres_no_walls": "Plan {plan}: Keine aussteifende Wand (H, W) gezeichnet – kein Steifigkeitszentrum.",
        "warn_plan_centres_no_mode": "Plan {plan}: {count} aussteifende Wand/Wände ohne Bauweise ({labels}) – das Steifigkeitszentrum wird nicht berechnet.",
        "warn_plan_centres_mixed": "Plan {plan}: Die aussteifenden Wände haben nicht alle dieselbe Bauweise (Holzrahmenbau: {timber_frame}, Brettsperrholz: {clt}, Beton: {concrete}) – das Steifigkeitszentrum wird nur für eine einzige Bauweise berechnet.",
        "warn_plan_centres_no_power": "Plan {plan}: Die Wände sind aus Brettsperrholz und die Potenz ihrer Länge (1.5 oder 2) ist nicht gewählt – das Steifigkeitszentrum wird nicht berechnet.",
        "warn_plan_centres_one_direction": "Plan {plan}: Alle aussteifenden Wände verlaufen in derselben Richtung – das Steifigkeitszentrum braucht Wände in mindestens zwei Richtungen.",
        "warn_plan_centres_no_torsion": "Plan {plan}: Die Wirkungslinien aller aussteifenden Wände gehen durch einen Punkt – das Geschoss hat keine Torsionssteifigkeit.",
        "warn_plan_centres_no_outline": "Plan {plan}: Kein Gebäudeumriss gezeichnet – kein Massenzentrum.",
        "warn_plan_centres_flat_outline": "Plan {plan}: Der Gebäudeumriss umschliesst keine Fläche – kein Massenzentrum.",
        "warn_plan_centres_section": "Plan {plan}: Die Position von {label} hat einen Brettsperrholz-Querschnitt und die Wand ist als {mode} gezeichnet – eines von beiden korrigieren.",
        "warn_plan_construction_timber_frame": "Holzrahmenbau",
        "warn_plan_construction_clt": "Brettsperrholz",
        "warn_plan_construction_concrete": "Beton",
        "warn_statics_unread": "System {model}: Der Wert der Last {load} konnte nicht gelesen werden – {detail}.",
        "warn_statics_unread_end": "System {model}: Der Endwert der Last {load} konnte nicht gelesen werden – {detail}.",
        "warn_statics_no_variable": "die Variable {ref} gibt es im Export nicht",
        "warn_link_stale": "{where}: {field} behält seinen letzten Wert – {detail}.",
        "warn_text_stale": "{where}: der Text druckt den letzten Wert von {field} – {detail}.",
        "warn_link_missing": "die Variable {ref} gibt es im Export nicht",
        "warn_link_not_a_number": "{ref} ist {value}, keine Zahl",
        "warn_link_unit": "{ref} ist in {unit} und kann keinen Wert in {field_unit} füllen",
        "warn_link_not_allowed": "{ref} kann hier nicht verwendet werden – eine Last folgt nur einer anderen Last oder einem Bereich des Reiters «Domänen»",
        "warn_statics_not_a_number": "{ref} ist {value}, keine Zahl",
        "warn_statics_no_magnitude": "die Grösse ist weder ein Wert noch eine Variable",
        "warn_statics_width_unit": "eine Last in {unit} lässt sich nicht mit einer Einflussbreite multiplizieren, die eine Last pro Meter oder pro Quadratmeter multipliziert",
        "warn_statics_no_support": "System {model}: Nichts hält es – es hat kein Auflager.",
        "warn_statics_idle_point": "System {model}: Der Punkt {point} trägt nichts und hält nichts.",
        "warn_statics_release_stiffness_shear": "System {model}: Das Gelenk {release} gibt die Querkraft frei und trug eine Steifigkeit, die entfernt wird – eine Feder entlang eines Stabes ist ein Element der Art «Feder».",
        "warn_statics_release_stiffness_normal": "System {model}: Das Gelenk {release} gibt die Normalkraft frei und trug eine Steifigkeit, die entfernt wird – eine Feder entlang eines Stabes ist ein Element der Art «Feder».",
        "warn_schema_unresolved": "Schema {schema}: Element {entry} verweist auf die Position {position}, die das Register Positionen nicht führt.",
        "warn_schema_section_unread": "Schema {schema}: Die Abmessung «{dimension}» der Position {position} ist nicht als b/h lesbar – geben Sie {view} am Element {entry} an; bis dahin ist es {width} mm breit gezeichnet.",
        "warn_schema_section_none": "Schema {schema}: Element {entry} hat weder eine Position noch {view} – wählen Sie seine Position oder geben Sie den Querschnitt an; bis dahin ist es {width} mm breit gezeichnet.",
        "warn_schema_crop_element": "Schema {schema}: {entry} liegt ganz ausserhalb des Ausschnitts – der Bericht zeigt es nicht.",
        "warn_schema_crop_marker": "Schema {schema}: {entry} liegt ausserhalb des Ausschnitts – der Bericht zeigt es nicht.",
        "warn_polar_no_schema": "{connection} ist auf keinem Schema gezeichnet – wählen Sie eines (Schemas: {schemas}); bis dahin kann der Bericht es nicht ausgeben.",
        "warn_polar_no_schema_none": "{connection} ist auf keinem Schema gezeichnet, und es gibt noch keines – zeichnen Sie eines im Reiter «Schemas»; bis dahin kann der Bericht es nicht ausgeben.",
        "warn_polar_schema_gone": "{connection} ist auf dem Schema {schema} gezeichnet, das der Export nicht führt – wählen Sie eines von {schemas}; bis dahin kann der Bericht es nicht ausgeben.",
        "warn_polar_schema_gone_none": "{connection} ist auf dem Schema {schema} gezeichnet, das der Export nicht führt, und es gibt noch kein Schema; bis dahin kann der Bericht es nicht ausgeben.",
        "warn_polar_markers_lost": "{connection}: Das Schema {schema} trägt die Markierung(en) oder Punkt(e) {ids} nicht mehr – haken Sie die Verbindungsmittel neu an; sie bleiben ausserhalb der Berechnung.",
        "warn_polar_elements_lost": "{connection}: Das Schema {schema} trägt das/die Element(e) {ids} nicht mehr – wählen Sie die Elemente der Bauteile neu; ihre Winkel werden als 0° angenommen.",
        "warn_polar_centre_lost": "{connection}: Das Schema {schema} trägt das Zentrum {centre} nicht mehr – der Schwerpunkt der Verbindungsmittel wird verwendet.",
    },
    "en": {
        "open_tab_picking": "A field is waiting for a value: end the choice first («Import» or «Cancel»).",
        "open_tab_not_shown": "The {tab} tab is not in “{document}”: choose the document that shows it.",
        "open_tab_not_made": "“{document}” is not made yet: only the Project tab opens.",
        "open_tab_reserved": "The {tab} tab is reserved for a calculation to come.",
        "language": "Language",
        "reexport": "Import data",
        "reexport_what": "the cases and drawings of Woodcore",
        "export_pdf": "Export PDF",
        "pdf_as_written": "As written (document)",
        "pdf_base_level": "Base level of detail",
        "pdf_uniform_level": "Uniform level of detail",
        "pdf_level_n": "Level {n}",
        "pdf_uniform_n": "Uniform {n}",
        "pdf_doc_language": "Document language",
        "pdf_settings": "Settings: {detail}",
        "pdf_document": "Exports: {document}",
        "pdf_all": "Export all three",
        "nav_document": "The document being written: the modules it shows, its journal and its PDF",
        "doc_stamp_unchanged": "{document}: unchanged since its PDF",
        "reload": "Reload",
        "nav_document_group": "Document",
        "nav_project": "Data",
        "nav_actions": "Actions",
        "nav_structure": "Structure",
        "nav_connections": "Connections",
        "nav_reference": "Reference",
        "nav_others": "Others",
        "nav_collapse": "Fold the menu to its icons",
        "nav_expand": "Unfold the menu",
        "pdf_chip_tip": "The next PDF will be compiled this way. Click to change it.",
        "meta_number": "No. {number}",
        "tab_combinations": "Load combinations",
        "tab_polar": "Polar moments of inertia",
        "future": "Not implemented yet.",
        "future_combinations": "ULS/SLS load combinations will be calculated in calc/domains/combinations.py (docs/domain/loads.md §3.5) and listed here, with the Typst calls that print them.",
        "polar_list": "Calculations",
        "polar_new": "New calculation",
        "polar_duplicate": "Duplicate",
        "polar_delete": "Delete calculation",
        "polar_save": "Save",
        "polar_revert": "Discard changes",
        "polar_revert_tip": "Puts the calculation back as it is saved; greyed out while nothing has changed.",
        "polar_new_item": "(new, not saved)",
        "polar_moved": "{count} calculation(s) moved to “{group}”.",
        "list_write_failed": "“{id}” could not be written — the move stops there: {error}",
        "polar_empty": "No calculation: “New calculation” creates one on the first schema of the “Schemas” tab.",
        "polar_list_hint": "Drag calculations into folders (right click: new folder).",
        "polar_name": "Name",
        "polar_id_auto": "Made from the name; may be written over.",
        "polar_id": "ID",
        "polar_label": "Description",
        "polar_member": "Member {n}",
        "polar_member_name": "Name",
        "polar_members": "Members",
        "polar_reference": "Reference member (angles θ)",
        "polar_reference_tip": "The member the other members' angles θ are counted from. The x and z axes are the schema's.",
        "polar_add_member": "Add a member",
        "polar_remove_member": "Remove this member",
        "polar_fasteners": "Fasteners",
        "polar_center": "Rotation centre",
        "polar_centroid": "Centroid of the fasteners",
        "polar_identity": "Identity",
        "polar_schema": "Schema",
        "polar_no_schema": "— none —",
        "polar_schema_none_notice": "No schema: choose one, or draw it in the «Schemas» tab. The report cannot print this calculation without a drawing.",
        "polar_schema_gone": "Schema {sid} no longer exists. Choose another.",
        "polar_schema_holds": "{n} element(s), {m} marker(s), {p} point(s) ticked «fastener».",
        "polar_element": "Element of the schema",
        "polar_member_name": "Name",
        "polar_marker": "Marker",
        "polar_markers_note": "The fastener markers and the construction points are drawn in the «Schemas» tab; tick the ones this calculation takes. What kind of fastener they are does not enter into it: a polar moment distributes forces over points.",
        "polar_kind_marker": "Fastener marker",
        "polar_kind_point": "Construction point",
        "polar_tick_all": "Tick all",
        "polar_tick_none": "Tick none",
        "polar_aid": "Centre of the schema",
        "polar_manual": "Fixed point",
        "polar_directions": "Force directions",
        "polar_directions_note": "Angles counted from x towards z (clockwise on the drawing). M is positive the other way, from z towards x (anticlockwise).",
        "polar_dir_N": "Normal force N",
        "polar_dir_V": "Shear force V",
        "polar_figure": "Figure",
        "polar_results": "Results",
        "polar_trial": "Force preview (not saved)",
        "polar_trial_result": "F_max = {f} kN — fastener(s) {k}\nF_x = {fx} kN · F_z = {fz} kN\n{betas}",
        "polar_no_moment": "I_p = 0: the fasteners have no lever arm, M cannot be taken.",
        "polar_unsaved_hint": "Save first: Typst only knows saved calculations.",
        "polar_saved": "“{id}” saved, data/connections.json updated.",
        "polar_save_failed_title": "Cannot save",
        "polar_export_failed": "“{id}” is saved, but exporting the calculations failed; Typst still sees the previous data.\n\n{error}",
        "polar_id_exists": "A calculation “{id}” already exists.",
        "polar_id_invalid": "Identifier “{id}”: letters, digits and _ . + - only, starting with a letter or a digit.",
        "polar_warnings_status": "{count} export warning(s).",
        "polar_rename": "“{old}” will be renamed “{new}”: Typst calls using “{old}” will stop working. Continue?",
        "polar_unsaved_title": "Unsaved changes",
        "polar_unsaved": "Calculation “{id}” has unsaved changes.",
        "polar_unreadable": "{name} cannot be read: {error}",
        "search": "Search",
        "commands": "Typst commands",
        "copy": "Copy",
        "copied": "Copied: {text}",
        "copied_short": "Copied ✓",
        "exporting": "Exporting…",
        "busy_loading": "Loading…",
        "busy_opening": "Opening “{name}”…",
        "busy_installing": "Installing the packages…",
        "busy_switching": "Switching document…",
        "export_ok": "Export finished, data reloaded.",
        "export_failed_title": "Export failed",
        "engine_title": "Project engine",
        "engine_older": "This project uses the engine of Woodcore {version}. Update it to {ours}? The report may print differently afterwards.",
        "engine_edited": "The Typst engine copied into this project was edited by hand ({files}). Replacing it with the engine of Woodcore {ours} would erase those edits.\n\nIf the change is meant to stay, carry it into the program first. The differences are under “Show differences…”.",
        "engine_newer": "This project was exported by Woodcore {version}, newer than this program ({ours}). Open it with that version or a newer one: this program will write nothing into it.",
        "engine_newer_open": "This project's engine was written by Woodcore {version}, newer than this program ({ours}). This window will export nothing into this project: to export it, open it with Woodcore {version} or a newer version.",
        "engine_update": "Update and export",
        "engine_update_now": "Update",
        "engine_overwrite": "Overwrite and export",
        "engine_overwrite_now": "Overwrite",
        "engine_later": "Later",
        "engine_diff": "Show differences…",
        "engine_diff_title": "The project's engine and that of Woodcore {ours}",
        "engine_diff_none": "No differences in the engine's files.",
        "engine_synced": "The project's Typst engine was updated to Woodcore {ours}.",
        "engine_sync_failed": "The project's engine could not be updated: {error}",
        "engine_unknown": "This project carries a Typst engine no VERSION file names ({files}): that of a folder laid out before Woodcore. Replace it with the engine of Woodcore {ours}? The report may print differently afterwards.",
        "export_failed": "The export failed (code {code}); the previous data is still shown.\n\n{output}",
        "compiling": "Compiling: {document}…",
        "pdf_ready": "{document}: PDF written ({name})",
        "archive_failed": "PDF not archived: {reason}",
        "compile_failed_title": "Compilation failed",
        "close_after_export": "Exporting – the window will close as soon as it has finished.",
        "close_after_compile": "Compiling – the window will close as soon as it has finished.",
        "loaded": "{count} values · exported {date}",
        "deps_title": "Dependencies",
        "deps_mismatch": "What the project asks for is not what is installed:\n\n{detail}\n\nThe report was verified with the versions in requirements.txt. Install them now?",
        "deps_line_missing": "  • {name} {wanted} — missing",
        "deps_line_other": "  • {name} {wanted} — {found} installed",
        "deps_update": "Update available: {detail}.",
        "deps_update_one": "{name} {pinned} → {available}",
        "deps_update_button": "Install",
        "deps_update_ask": "Install {detail} and write the new version into requirements.txt?\n\nThe report was verified with the versions you have now: rebuild it and rerun the tests after updating.",
        "deps_ok": "Installed. Restart Woodcore so the new version is loaded.",
        "deps_failed": "The installation failed:\n\n{output}",
        "startup_error": "Woodcore could not start:\n\n{error}",
        "open_project_title": "Open a Woodcore project",
        "open_project_filter": "Woodcore projects (*.woodcore)",
        # the warnings of the editors, by the code a domain module's engine.Note carries (periodic audit 260916, AUD-4-11)
        "warn_plan_no_number": "Plan {plan}: element {i} ({type}) has no position number.",
        "warn_plan_unknown": "Plan {plan}: {label} is not a position of the project — add it in the Positions tab.",
        "warn_formula_misnamed": "{file}: the domain declares another name than its file ({domain}); it is exported as it stands, and the «Domaines» tab writes its own id back at the next save.",
        "warn_load_workbook_not_read": "A load workbook is in the project folder ({files}): Woodcore no longer reads it. The cases of wind, snow and permanent loads are entered in the tabs “Wind”, “Snow” and “Self-weight and superimposed load”.",
        "warn_calculations_old_export": "data/calculations.json was written by an earlier version of Woodcore (schema {version}, this one writes {current}): the report does not compile until “Import data” has written it again once.",
        "warn_sync_stale": "{file}, line {line}: #sync(\"{id}\") writes {written}, and the export holds {held} -- refresh the value, or take #sync away to keep it as it is.",
        "warn_plan_dimensions_no_scale": "Plan {plan}: {count} dimension(s) measure lengths and the plan has no scale; calibrate it, or they are not drawn.",
        "warn_dep_changed": "{node} changed since the last export; depending on it, {kind}: {ids}.",
        "warn_dep_cycle": "{chain}: these objects read each other in a circle; an export settles them only by chance.",
        "warn_dep_kind_position": "positions",
        "warn_dep_kind_load": "loads",
        "warn_dep_kind_script": "scripts",
        "warn_dep_kind_formula": "domains",
        "warn_dep_kind_check": "timber checks",
        "warn_dep_kind_steel": "steel checks",
        "warn_dep_kind_profile": "profiles",
        "warn_dep_kind_connector": "connectors",
        "warn_dep_kind_connection": "polar moments",
        "warn_dep_kind_schema": "schemas",
        "warn_dep_kind_statics": "static models",
        "warn_dep_kind_plan": "plans",
        "warn_dep_kind_document": "documents",
        "warn_dep_kind_fire": "fire plans",
        "warn_dep_kind_extract": "excerpts",
        "warn_dep_kind_section": "report sections",
        "warn_snow_above_limit": "{where}: h_0 = {h_0} m is above the {limit} m of SIA 261 {ref}; its provisions do not apply there.",
        "warn_wind_c_red_outside": "{where}: the reference area {area} has h = {h} m and β = {beta}, which SIA 261 {ref} does not draw; c_red is read at the end of the nearest curve.",
        "warn_wind_no_library": "{where}: Table {table}'s figure of SIA 261 is not cut, {files} is not in norm-library/; the file is written without it.",
        "warn_plan_wrong_type": "Plan {plan}: {label} is drawn with the symbol {type} ({name}).",
        "warn_plan_outside": "Plan {plan}: {label} lies outside the crop and will not be seen in the report.",
        "warn_script_failed": "The script {script}: {reason}",
        "warn_domain_file_orphan": "{file}: no domain of its folder bears this name any more — the file is yours and stays where it is.",
        "warn_unfold_stub_edited": "{file}: the check {id} is printed unfolded, and its file holds what you wrote in place of Woodcore's stub — it stays as it is, and the check is printed folded until you empty it.",
        "warn_retired_key": "{file}: {key} is ignored — the RFEM import was retired in 0.117 (archive/rfem/). Take the key out of the project file to stop this message.",
        "warn_plan_number_outside": "Plan {plan}: the number of {label} was moved out of the crop, which will cut it off in the report.",
        "warn_plan_centres_no_walls": "Plan {plan}: no bracing wall (H, W) is drawn — no stiffness centre.",
        "warn_plan_centres_no_mode": "Plan {plan}: {count} bracing wall(s) without a construction mode ({labels}) — the stiffness centre is not calculated.",
        "warn_plan_centres_mixed": "Plan {plan}: the bracing walls are not all built the same way (timber frame: {timber_frame}, CLT: {clt}, concrete: {concrete}) — the stiffness centre is calculated for one construction mode only.",
        "warn_plan_centres_no_power": "Plan {plan}: the walls are CLT and the power of their length (1.5 or 2) is not chosen — the stiffness centre is not calculated.",
        "warn_plan_centres_one_direction": "Plan {plan}: every bracing wall runs in the same direction — the stiffness centre needs walls in two directions at least.",
        "warn_plan_centres_no_torsion": "Plan {plan}: the lines of action of every bracing wall pass through one point — the storey has no torsional stiffness.",
        "warn_plan_centres_no_outline": "Plan {plan}: no building outline is drawn — no mass centre.",
        "warn_plan_centres_flat_outline": "Plan {plan}: the building outline encloses no area — no mass centre.",
        "warn_plan_centres_section": "Plan {plan}: the position of {label} has a CLT section and the wall is drawn as {mode} — set one of the two right.",
        "warn_plan_construction_timber_frame": "timber frame",
        "warn_plan_construction_clt": "CLT",
        "warn_plan_construction_concrete": "concrete",
        "warn_statics_unread": "Model {model}: the value of load {load} could not be read — {detail}.",
        "warn_statics_unread_end": "Model {model}: the value at the far end of load {load} could not be read — {detail}.",
        "warn_statics_no_variable": "the export has no variable {ref}",
        "warn_link_stale": "{where}: {field} keeps its last value — {detail}.",
        "warn_text_stale": "{where}: the text prints the last value of {field} — {detail}.",
        "warn_link_missing": "the export has no variable {ref}",
        "warn_link_not_a_number": "{ref} is {value}, which is not a number",
        "warn_link_unit": "{ref} is in {unit}, which cannot fill a value in {field_unit}",
        "warn_link_not_allowed": "{ref} may not be named here — a load follows only another load or a domain of the «Domains» tab",
        "warn_statics_not_a_number": "{ref} is {value}, which is not a number",
        "warn_statics_no_magnitude": "the magnitude is neither a value nor a variable",
        "warn_statics_width_unit": "a load in {unit} cannot be multiplied by an influence width, which multiplies a load per metre or per square metre",
        "warn_statics_no_support": "Model {model}: nothing holds it — it has no support.",
        "warn_statics_idle_point": "Model {model}: point {point} carries nothing and holds nothing.",
        "warn_statics_release_stiffness_shear": "Model {model}: release {release} frees the shear force and carried a stiffness, which is dropped — a spring along a member is a member of kind «Spring».",
        "warn_statics_release_stiffness_normal": "Model {model}: release {release} frees the normal force and carried a stiffness, which is dropped — a spring along a member is a member of kind «Spring».",
        "warn_schema_unresolved": "Schema {schema}: element {entry} refers to position {position}, which the Positions tab does not have.",
        "warn_schema_section_unread": "Schema {schema}: the dimension «{dimension}» of position {position} does not read as b/h — state {view} on element {entry}; it is drawn {width} mm wide until then.",
        "warn_schema_section_none": "Schema {schema}: element {entry} names no position and states no {view} — choose its position or state its section; it is drawn {width} mm wide until then.",
        "warn_schema_crop_element": "Schema {schema}: {entry} lies wholly outside the crop — the report will not show it.",
        "warn_schema_crop_marker": "Schema {schema}: {entry} lies outside the crop — the report will not show it.",
        "warn_polar_no_schema": "{connection} is drawn on no schema — choose one (schemas: {schemas}); the report cannot print it until then.",
        "warn_polar_no_schema_none": "{connection} is drawn on no schema, and there is none yet — draw one in the «Schemas» tab; the report cannot print it until then.",
        "warn_polar_schema_gone": "{connection} is drawn on schema {schema}, which the export does not list — choose one of {schemas}; the report cannot print it until then.",
        "warn_polar_schema_gone_none": "{connection} is drawn on schema {schema}, which the export does not list, and there is no schema yet; the report cannot print it until then.",
        "warn_polar_markers_lost": "{connection}: schema {schema} no longer carries the marker(s) or point(s) {ids} — tick the fasteners again; they are left out of the calculation.",
        "warn_polar_elements_lost": "{connection}: schema {schema} no longer carries the element(s) {ids} — choose the members' elements again; their angles are taken as 0°.",
        "warn_polar_centre_lost": "{connection}: schema {schema} no longer carries the centre {centre} — the fasteners' centroid is used instead.",
    },
}


def _check_strings():
    """The three languages must carry exactly the same keys -- a key missing from one would only surface as a KeyError the day someone switches to it."""
    reference = set(STRINGS["fr"])
    for lang, strings in STRINGS.items():
        missing, extra = reference - set(strings), set(strings) - reference
        if missing or extra:
            raise RuntimeError(f"STRINGS[{lang!r}]: missing {sorted(missing)}, extra {sorted(extra)}")


# The position plan tab's texts, kept in its module, checked with the rest -- and, since v0.114, those of what the tab is built of: the document view (dv_), the «Commande Typst» builder (pcb_) and the export sheets' editor (se_).
for _module in (plan_tab, plan_tab.document_view, plan_tab.plan_command_builder, plan_tab.sheet_editor):
    for _lang, _texts in _module.STRINGS.items():
        STRINGS[_lang].update(_texts)


# The fire protection plan tab's, likewise, prefixed fp_, and the warnings of calc/domains/fire.py, prefixed warn_fire_ (v0.115).
for _lang, _texts in fire_tab.STRINGS.items():
    STRINGS[_lang].update(_texts)


# The positions tab's, likewise, prefixed po_ (v0.94).
for _lang, _texts in positions_tab.STRINGS.items():
    STRINGS[_lang].update(_texts)

# The «Métré» tab's, prefixed mt_, and the card of a list's file, prefixed lf_ (spec 2026-10-21-commandes-typst-refonte, UI-003, Q-008).
for _module in (metre_tab, list_file_card):
    for _lang, _texts in _module.STRINGS.items():
        STRINGS[_lang].update(_texts)


# The member checks' tabs, likewise: the nine modules' and the two groups' titles, the placeholders' words and the tension check's form, prefixed mc_ (calc/tools/member_check_tab.py).
for _lang, _texts in member_check_tab.STRINGS.items():
    STRINGS[_lang].update(_texts)

# The «Résistance au feu» tab's, likewise, prefixed mc_fire_, mc_building_ and mc_aeai_ (calc/tools/fire_check_tab_words.py, issue #46).
for _lang, _texts in fire_check_tab_words.STRINGS.items():
    STRINGS[_lang].update(_texts)

# The «Acier» tabs', likewise, prefixed st_ and pr_, with their group's and tabs' titles (calc/tools/steel_tab_words.py, issues #50-#52).
for _lang, _texts in steel_tab_words.STRINGS.items():
    STRINGS[_lang].update(_texts)

# The tabs of loads entered in Woodcore, likewise, prefixed ld_ (calc/tools/load_words.py, issues #35-#37).
for _lang, _texts in load_words.STRINGS.items():
    STRINGS[_lang].update(_texts)

# The words of the services of the tabs built on a type, a module for a set of services -- each service names its own (`WORDS_MODULE`, tab_host.Service) and tests/test_tab_services.py holds every one listed here: the services of the type «Calcul», prefixed ct_ (spec 2026-10-23-onglets-types-et-services, ARCH-008).
SERVICE_WORDS = (calc_tab_words,)
# Those, the «Neige» tab's, prefixed sn_, and the «Vent» tab's, wi_ (calc/tools/calc_tab_words.py, snow_tab_words.py, wind_tab_words.py; specs 2026-10-22-onglet-neige-type, 2026-10-23-onglet-vent-briques).
for _module in (*SERVICE_WORDS, snow_tab_words, wind_tab_words, materials_tab_words):   # and the «Matériaux» tab's, mat_ (issue #110)
    for _lang, _texts in _module.STRINGS.items():
        STRINGS[_lang].update(_texts)


# The six tabs of «Actions» and its two sections, likewise: the names and what each will hold, prefixed ac_ (calc/tools/action_tabs.py, v0.117).
for _lang, _texts in action_tabs.STRINGS.items():
    STRINGS[_lang].update(_texts)


# The journal tab's, likewise, prefixed jo_ (v0.99).
for _lang, _texts in journal_tab.STRINGS.items():
    STRINGS[_lang].update(_texts)


# The annexes tab's, likewise, prefixed ax_, and the warnings of calc/domains/annex.py, prefixed warn_annex_ (v0.115).
for _lang, _texts in annex_tab.STRINGS.items():
    STRINGS[_lang].update(_texts)


# The views' names and the fold of a pane, prefixed view_ and pane_ (views.py, v0.117).
for _lang, _texts in views.STRINGS.items():
    STRINGS[_lang].update(_texts)


for _lang, _texts in bundle_view.STRINGS.items():
    STRINGS[_lang].update(_texts)


# The notices' words -- the indicators, their panel, a notice's title and sentence -- prefixed notice_ and activity_ (notices_ui.py, v0.117).
for _lang, _texts in notices_ui.STRINGS.items():
    STRINGS[_lang].update(_texts)


# What saving without a question says in the status line, prefixed autosave_ (autosave.py, v0.117).
for _lang, _texts in autosave.STRINGS.items():
    STRINGS[_lang].update(_texts)


# The «Affichage» views' words, prefixed ds_ (display_options.py, v0.117) -- dv_ is the document view's.
for _lang, _texts in display_options.STRINGS.items():
    STRINGS[_lang].update(_texts)


# The «Structure du document» tab's, likewise, prefixed st_ (the three documents, reworked 01.10.2026) -- its panes' own words (object_panes.py, pdf_pane.py) are theirs, read from the language they are given.
for _lang, _texts in structure_tab.STRINGS.items():
    STRINGS[_lang].update(_texts)


# The Python tab's, likewise, prefixed py_ (v0.100).
for _lang, _texts in python_tab.STRINGS.items():
    STRINGS[_lang].update(_texts)


# The «Formule» tab's, likewise, prefixed fm_, and its title (v0.117).
for _lang, _texts in formula_tab.STRINGS.items():
    STRINGS[_lang].update(_texts)


# The «Variables» tab's, likewise, prefixed vr_ -- in a module of their own since issue #114 (ARCH-006).
for _lang, _texts in variables_words.STRINGS.items():
    STRINGS[_lang].update(_texts)


# The command palette's, likewise, prefixed cp_ (issue #83).
for _lang, _texts in command_palette.STRINGS.items():
    STRINGS[_lang].update(_texts)


# The «Projet» tab's, likewise, prefixed pj_ and tpv_why_ (issues #87, #88, #90).
for _lang, _texts in project_tab.STRINGS.items():
    STRINGS[_lang].update(_texts)


# The «Dépendances» tab's, likewise, prefixed dg_ (issue #71).
for _lang, _texts in dependencies_tab.STRINGS.items():
    STRINGS[_lang].update(_texts)


for _lang, _texts in statics_tab.STRINGS.items():
    STRINGS[_lang].update(_texts)


# The detail schemas tab's, likewise. Its keys carry an `sc_` prefix of their own, for the reason the commands tab's carry `ref_`.
for _lang, _texts in schema_tab.STRINGS.items():
    STRINGS[_lang].update(_texts)


# The commands tab's, likewise. Its keys carry a `ref_` prefix of their own: a key defined in two of these modules would be silently taken by whichever merged last, which _check_strings cannot see.
for _lang, _texts in connectors_tab.STRINGS.items():
    STRINGS[_lang].update(_texts)


for _lang, _texts in commands_tab.STRINGS.items():
    STRINGS[_lang].update(_texts)


# The grouped left pane's own five words, merged once here rather than in each of the four tabs that use it: the same key defined in several modules would be taken by whichever merged last (grouped_list.py).
for _lang, _texts in grouped_list.STRINGS.items():
    STRINGS[_lang].update(_texts)


# The identity rows' own words, merged once here for the same reason (identity.py).
for _lang, _texts in identity.STRINGS.items():
    STRINGS[_lang].update(_texts)


# The start page's, the project dialog's, the lock's and the File menu's (home_page.py, v0.83): prefixed home_, proj_, lock_, read_only_ and file_.
for _lang, _texts in home_page.STRINGS.items():
    STRINGS[_lang].update(_texts)


# The migration's question, its progress and its banner (migrate_dialog.py): prefixed mg_.
for _lang, _texts in migrate_dialog.STRINGS.items():
    STRINGS[_lang].update(_texts)


# The button beside a field that may follow a variable of the export, and what it shows once linked (linkable_spin.py): prefixed lk_.
for _lang, _texts in linkable_spin.STRINGS.items():
    STRINGS[_lang].update(_texts)


# The right pane of a text placed with the Text tool, the same in the four drawing engines (text_pane.py): prefixed tx_.
for _lang, _texts in text_pane.STRINGS.items():
    STRINGS[_lang].update(_texts)
