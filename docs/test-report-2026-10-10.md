# Bilan de la suite de tests — 10.10.2026

Instantané daté de l'issue [When-I-hit-the-wall/Woodcore#24](https://github.com/When-I-hit-the-wall/Woodcore/issues/24) : ce document n'est pas tenu à jour. La référence durable est `tests/README.md` et `docs/conventions/testing.md`. Commande : `python tests/run_tests.py --times`, depuis la racine, sur le poste de l'ingénieur (Windows 11, Python 3.14, 8 fichiers à la fois).

## En bref

| Run | Réussis | Sautés | Échecs | Durée (horloge) | Temps cumulé des fichiers |
|---|--:|--:|--:|--:|--:|
| 1er run, avant corrections (commit `ba7ab95`) | 2578 | 12 | **64** | 1971 s (33 min) | 5762 s |
| Run final, après corrections | 2642 | 12 | **0** | 531 s (9 min) | 4150 s |

143 fichiers de test, 2654 tests. Le run final est aussi bien plus court parce que `run_tests.py` découpe un fichier lent d'après les temps du run précédent : au 1er run, `test_fire_tab` tournait seul pendant 1766 s, alors qu'au run final il était réparti sur plusieurs processus (683 s cumulées).

## Où étaient les échecs, et pourquoi

Les 64 échecs du 1er run venaient de cinq causes. Les deux premières concernaient la machine et le programme livré, pas seulement les tests.

| Cause | Échecs | Fichiers | Correction |
|---|--:|---|---|
| **Checkout en CRLF.** Le dépôt a été cloné le 07.10.2026 sous Git pour Windows, qui fixe `core.autocrlf=true` au niveau du système. Les 1942 fichiers texte en sont sortis en CRLF, alors que le dépôt les tient en LF. Étaient touchés le projet exemple, les templates de documents, et donc aussi un installeur construit ici. | 41 | `test_structure` (4), `test_structure_tab` (2), `test_doc_import` (6), `test_sync` (5), `test_sharing` (3), `test_doc_templates` (9), `test_content_switch` (6), `test_content_switch_dialog` (5), `test_migrate` (1) | `.gitattributes` : `* text=auto eol=lf` (les `.bat` restent en CRLF, les binaires sont inchangés). Le checkout a été remis en LF sur place, sans changement de contenu. `CLAUDE.md` est corrigé (il disait ces fichiers « en CRLF »). |
| **Pillow absent.** L'extension de dessin d'ezdxf, utilisée par `calc/domains/cad.py` pour rendre un plan DXF/DWG, importe `PIL` sans le déclarer. | 9 | `test_cad` (5), `test_plan_documents` (2), `test_position_list` (1), `test_document_view` (1, une page DXF jamais rendue : « nothing after 60 s ») | `requirements.txt` : `Pillow==12.3.0`, installé sur le poste. Le build de l'installeur installe `requirements.txt` et le livrera donc. |
| **Défauts des fonctions #10–#18** (corrigés par la session parallèle qui vérifie ces issues) | 13 | `test_left_pane_fold` (2), `test_notice_bar` (2), `test_annex` (2), `test_positions_tab` (2), `test_plan_edit_tools` (1), `test_plan_types_v0116` (1), `test_plan_sections` (1), `test_plan_metres` (1), `test_fire_tab` (1) | Code : `calc/tools/flowbar.py` (un élément plus large que sa ligne y est ramené), `cards.py` (les champs numériques se resserrent aussi), `annex_tab.py` (espacement de la ligne « de / à »), `calc/domains/annex.py` (un cadre tracé un peu au-dessus de son titre s'accroche à ce titre). Tests remis à jour : colonne « Longueur », version 1.6 de la source d'un plan, outils déplacer/copier dans `test_fire_tab`. |
| **Liste d'échelles refermée par une compilation** (apparue après le 1er run) | — | `test_sheet_editor` (1) | `calc/tools/sheet_editor.py` `_shown` : une compilation qui se terminait pendant que la liste d'échelles était ouverte reconstruisait le volet de droite et refermait la liste. C'est le « s'ouvre et se ferme instantanément » du 07.10.2026, par un autre chemin que REQ-017. Le volet attend désormais qu'aucune de ses listes ne soit ouverte. |
| **Test resté sur l'ancienne disposition** | 1 | `test_views` (1) | Depuis l'issue #11, les notices sont placées entre les vues et les langues. Le test n'admet plus que `notice_bar` à cet endroit. |
| **Import selon l'ordre des tests** (apparu au run de pré-commit) | — | `test_fire_tab` (1) | `test_a_drag_renders_the_overlay…` importait `fire_canvas` avant que `calc/tools` ne soit sur le chemin. Il ne passait que si un test précédent de la même partie du fichier l'y avait mis. Il appelle désormais `_qt()` d'abord. |

41 + 9 + 13 + 1 = 64. L'échec de `test_sheet_editor` n'est apparu qu'aux runs suivants : la compilation finissait parfois avant l'ouverture de la liste, et le test passait. Le détail, fichier par fichier, se trouve dans les tableaux ci-dessous (colonne « Échecs 1er run »).

### Les 12 tests sautés (normal sur ce poste)

- 5 attendent le projet de l'ingénieur, désigné par `WOODCORE_REAL_PROJECT` : `test_migrate`, `test_dead_load`, `test_export`, `test_dowel`, `test_project`.
- 2 attendent les templates du bureau, à côté du programme : `test_title_page`.
- 1 attend la bibliothèque des normes `ExternalFiles/000-Normes` : `test_sia260`.
- 3 attendent des connecteurs enregistrés que le projet exemple n'a pas : `test_connectors`.
- 1 concerne la casse des noms de fichiers, que Windows ne distingue pas : `test_connectors`.

## Catégories : ce qu'elles couvrent, leurs temps et leurs échecs

Le « temps » est celui d'un fichier, import compris, en additionnant ses parties s'il est découpé. Les fichiers tournent à 8 en parallèle, donc la somme des temps dépasse la durée à l'horloge.

| Catégorie | Ce qu'elle couvre | Fichiers | Tests | Temps (run final) | Échecs (1er run) | Échecs (run final) |
|---|---|--:|--:|--:|--:|--:|
| Pipeline, projet, données et normes | le projet `.woodcore`, l'export et ses schémas, les normes `calc/norms/`, les glossaires, les templates de projet, les positions, la migration | 20 | 362 | 380 s | 1 | 0 |
| Calculs (domaines) | `calc/domains/` : charges, assemblages, broches, connecteurs, formules, vérifications d'élément, distances, scripts, quantités, modèles statiques | 14 | 376 | 300 s | 0 | 0 |
| Schémas de détail | les schémas (source, dessin, édition, sections) et leur onglet | 6 | 182 | 265 s | 0 | 0 |
| Plans : positions, incendie, CAD, feuilles d'export | `plan.py`, `plan_svg.py`, `fire*.py`, `cad.py`, `sheets.py` et les onglets de plans, l'éditeur de feuilles | 25 | 389 | 948 s | 13 | 0 |
| Documents CU / BP / RS | la structure d'un document, ses objets Typst, le partage et la synchronisation entre documents, l'import, les templates de contenu, page de titre, formulaires, annexes | 18 | 572 | 748 s | 42 | 0 |
| Rapport Typst et commandes | `lib/*.typ` : compilation du rapport, commandes documentées, affichage, légendes, bibliographie, résumés, journal, liste des positions, variables, éditeur (tinymist) | 15 | 287 | 339 s | 1 | 0 |
| Fenêtre Woodcore (PySide6) | `calc/tools/` : page d'accueil, cadre, cartes, thème, onglets, vues, notices, volets, sauvegarde, démarrage | 40 | 394 | 1027 s | 7 | 0 |
| Installation, site, outillage | lanceur et installeur, site et publication, mises à jour, licences, le banc de tests lui-même | 5 | 92 | 142 s | 0 | 0 |
| **Total** | | **143** | **2654** | **4149 s** | **64** | **0** |

### Pipeline, projet, données et normes

| Fichier | Tests | Temps final | Temps 1er run | Échecs 1er run | Sautés |
|---|--:|--:|--:|--:|--:|
| `test_new_project` | 34 | 134.1 s | 179.3 s |  |  |
| `test_templates` | 25 | 51.3 s | 50.4 s |  |  |
| `test_i18n` | 22 | 43.4 s | 43.9 s |  |  |
| `test_migrate` | 15 | 42.8 s | 51.5 s | 1 | 1 |
| `test_cli_documents` | 7 | 32.9 s | 36.2 s |  |  |
| `test_stamps` | 23 | 23.5 s | 25.8 s |  |  |
| `test_position_type_i18n` | 5 | 12.1 s | 14.0 s |  |  |
| `test_project` | 23 | 8.3 s | 12.0 s |  | 1 |
| `test_retired_features` | 4 | 7.2 s | 5.7 s |  |  |
| `test_positions_store` | 15 | 6.2 s | 5.8 s |  |  |
| `test_sia260` | 25 | 4.6 s | 4.0 s |  | 1 |
| `test_units` | 5 | 2.9 s | 4.5 s |  |  |
| `test_positions_workbook` | 3 | 1.6 s | 1.4 s |  |  |
| `test_list_order` | 8 | 1.6 s | 1.3 s |  |  |
| `test_archive` | 9 | 1.5 s | 1.9 s |  |  |
| `test_section` | 13 | 1.5 s | 1.3 s |  |  |
| `test_export` | 12 | 1.4 s | 1.7 s |  | 1 |
| `test_constants` | 23 | 1.4 s | 1.4 s |  |  |
| `test_documents` | 11 | 1.2 s | 1.4 s |  |  |
| `test_norms` | 80 | 1.0 s | 1.7 s |  |  |

### Calculs (domaines)

| Fichier | Tests | Temps final | Temps 1er run | Échecs 1er run | Sautés |
|---|--:|--:|--:|--:|--:|
| `test_timber` | 45 | 67.1 s | 65.0 s |  |  |
| `test_formula` | 83 | 63.9 s | 61.1 s |  |  |
| `test_statics` | 27 | 43.5 s | 47.7 s |  |  |
| `test_member_check` | 35 | 41.5 s | 47.6 s |  |  |
| `test_renumbering` | 15 | 24.4 s | 26.5 s |  |  |
| `test_connectors` | 70 | 22.8 s | 24.8 s |  | 4 |
| `test_distance` | 12 | 11.3 s | 19.1 s |  |  |
| `test_script` | 10 | 9.2 s | 10.4 s |  |  |
| `test_quantities` | 7 | 5.3 s | 8.3 s |  |  |
| `test_formula_domain` | 18 | 4.3 s | 4.9 s |  |  |
| `test_arrows` | 4 | 3.0 s | 2.9 s |  |  |
| `test_dead_load` | 11 | 1.8 s | 3.0 s |  | 1 |
| `test_connection` | 9 | 1.1 s | 1.3 s |  |  |
| `test_dowel` | 30 | 0.8 s | 0.8 s |  | 1 |

### Schémas de détail

| Fichier | Tests | Temps final | Temps 1er run | Échecs 1er run | Sautés |
|---|--:|--:|--:|--:|--:|
| `test_schema_tab` | 43 | 250.0 s | 311.2 s |  |  |
| `test_schema_edit` | 33 | 8.0 s | 7.6 s |  |  |
| `test_schema_consumers` | 21 | 2.7 s | 4.1 s |  |  |
| `test_schema` | 43 | 2.6 s | 3.7 s |  |  |
| `test_figure_style` | 17 | 1.1 s | 0.9 s |  |  |
| `test_schema_section` | 25 | 1.0 s | 1.2 s |  |  |

### Plans : positions, incendie, CAD, feuilles d'export

| Fichier | Tests | Temps final | Temps 1er run | Échecs 1er run | Sautés |
|---|--:|--:|--:|--:|--:|
| `test_fire_tab` | 50 | 682.6 s | 1766.5 s | 1 |  |
| `test_sheet_editor` | 23 | 51.4 s | 60.1 s |  |  |
| `test_fire_print` | 11 | 27.0 s | 39.6 s |  |  |
| `test_plan_tab_rework` | 17 | 24.9 s | 25.9 s |  |  |
| `test_sheets` | 21 | 24.7 s | 29.5 s |  |  |
| `test_doc_frames_v0116` | 10 | 17.4 s | 20.5 s |  |  |
| `test_document_view` | 14 | 16.7 s | 102.6 s | 1 |  |
| `test_plan_command_builder` | 13 | 14.5 s | 16.9 s |  |  |
| `test_plan_types_v0116` | 15 | 12.5 s | 14.3 s | 1 |  |
| `test_sheet_bundles_tab` | 9 | 10.9 s | 10.6 s |  |  |
| `test_plan_edit_tools` | 14 | 9.5 s | 7.8 s | 1 |  |
| `test_plan_style` | 20 | 9.0 s | 10.3 s |  |  |
| `test_plan_panes_v0116` | 10 | 8.7 s | 7.0 s |  |  |
| `test_plan_overlay_v0116` | 12 | 8.4 s | 8.9 s |  |  |
| `test_plan_tabs_v0117` | 7 | 8.2 s | 7.8 s |  |  |
| `test_plan_metres` | 9 | 3.1 s | 3.4 s | 1 |  |
| `test_plan_documents` | 20 | 3.0 s | 2.8 s | 2 |  |
| `test_fire` | 57 | 3.0 s | 2.8 s |  |  |
| `test_cad` | 10 | 2.7 s | 2.1 s | 5 |  |
| `test_plan_canvas_rework` | 8 | 1.9 s | 1.7 s |  |  |
| `test_plan_dimension_tools` | 4 | 1.8 s | 1.8 s |  |  |
| `test_plan_rotation_ruler` | 3 | 1.8 s | 1.6 s |  |  |
| `test_plan_tracking` | 16 | 1.8 s | 1.4 s |  |  |
| `test_plan_dimensions` | 5 | 1.5 s | 1.1 s |  |  |
| `test_plan_sections` | 11 | 0.8 s | 1.0 s | 1 |  |

### Documents CU / BP / RS

| Fichier | Tests | Temps final | Temps 1er run | Échecs 1er run | Sautés |
|---|--:|--:|--:|--:|--:|
| `test_structure_tab` | 72 | 190.7 s | 222.2 s | 2 |  |
| `test_doc_templates` | 41 | 92.1 s | 141.4 s | 9 |  |
| `test_forms` | 14 | 58.0 s | 61.3 s |  |  |
| `test_title_page` | 11 | 52.1 s | 62.4 s |  | 2 |
| `test_sync` | 21 | 51.7 s | 62.3 s | 5 |  |
| `test_content_switch` | 9 | 50.4 s | 26.7 s | 6 |  |
| `test_structure` | 99 | 50.0 s | 51.1 s | 4 |  |
| `test_sharing` | 16 | 45.0 s | 50.8 s | 3 |  |
| `test_annex` | 28 | 33.8 s | 44.5 s | 2 |  |
| `test_doc_import` | 45 | 32.3 s | 34.4 s | 6 |  |
| `test_pdf_pane` | 21 | 19.6 s | 21.1 s |  |  |
| `test_document_commands` | 29 | 19.1 s | 25.9 s |  |  |
| `test_typst_objects` | 56 | 14.4 s | 13.8 s |  |  |
| `test_content_switch_dialog` | 7 | 13.3 s | 6.9 s | 5 |  |
| `test_structure_preview` | 14 | 9.0 s | 9.4 s |  |  |
| `test_typst_paths` | 27 | 8.5 s | 9.6 s |  |  |
| `test_object_panes` | 56 | 6.7 s | 7.1 s |  |  |
| `test_removed_objects` | 6 | 1.3 s | 1.5 s |  |  |

### Rapport Typst et commandes

| Fichier | Tests | Temps final | Temps 1er run | Échecs 1er run | Sautés |
|---|--:|--:|--:|--:|--:|
| `test_commands` | 34 | 100.8 s | 119.4 s |  |  |
| `test_editor` | 3 | 41.2 s | 46.2 s |  |  |
| `test_position_list` | 18 | 39.9 s | 40.5 s | 1 |  |
| `test_variables` | 56 | 33.8 s | 41.8 s |  |  |
| `test_summary` | 18 | 31.4 s | 44.1 s |  |  |
| `test_display` | 15 | 25.1 s | 31.5 s |  |  |
| `test_report` | 12 | 17.8 s | 20.1 s |  |  |
| `test_journal` | 29 | 16.5 s | 17.4 s |  |  |
| `test_bibliography` | 43 | 13.0 s | 15.1 s |  |  |
| `test_command_review` | 17 | 7.9 s | 11.4 s |  |  |
| `test_captions` | 1 | 5.9 s | 5.3 s |  |  |
| `test_variable_sources` | 16 | 2.1 s | 2.3 s |  |  |
| `test_typst_check` | 14 | 1.5 s | 1.9 s |  |  |
| `test_doc_comments` | 6 | 1.0 s | 1.0 s |  |  |
| `test_typst_diagnostics` | 5 | 0.8 s | 0.7 s |  |  |

### Fenêtre Woodcore (PySide6)

| Fichier | Tests | Temps final | Temps 1er run | Échecs 1er run | Sautés |
|---|--:|--:|--:|--:|--:|
| `test_modes_window` | 18 | 259.5 s | 313.7 s |  |  |
| `test_editor_buttons` | 5 | 61.8 s | 56.4 s |  |  |
| `test_polar_tab` | 13 | 60.5 s | 54.3 s |  |  |
| `test_engine_check` | 11 | 59.8 s | 51.6 s |  |  |
| `test_cards` | 10 | 47.8 s | 47.5 s |  |  |
| `test_startup` | 3 | 43.5 s | 49.3 s |  |  |
| `test_no_console` | 7 | 42.1 s | 52.6 s |  |  |
| `test_home` | 11 | 41.8 s | 37.9 s |  |  |
| `test_theme` | 10 | 40.7 s | 26.4 s |  |  |
| `test_notice_bar` | 9 | 30.2 s | 32.5 s | 2 |  |
| `test_busy` | 12 | 28.1 s | 26.9 s |  |  |
| `test_member_check_tab` | 38 | 27.3 s | 27.8 s |  |  |
| `test_chrome` | 9 | 26.5 s | 26.9 s |  |  |
| `test_views` | 9 | 22.8 s | 26.8 s | 1 |  |
| `test_positions_tab` | 12 | 20.6 s | 21.8 s | 2 |  |
| `test_pdf_button` | 9 | 18.9 s | 21.3 s |  |  |
| `test_window` | 8 | 17.6 s | 19.9 s |  |  |
| `test_formula_tab` | 16 | 16.9 s | 20.9 s |  |  |
| `test_settings_dialog` | 15 | 16.6 s | 18.0 s |  |  |
| `test_panes` | 7 | 16.3 s | 17.4 s |  |  |
| `test_stallwatch` | 4 | 15.8 s | 16.0 s |  |  |
| `test_light_refresh` | 6 | 15.0 s | 17.1 s |  |  |
| `test_left_pane_fold` | 4 | 13.5 s | 12.9 s | 2 |  |
| `test_toolbar` | 16 | 12.4 s | 14.2 s |  |  |
| `test_autosave` | 11 | 11.0 s | 11.3 s |  |  |
| `test_project_dialog` | 9 | 10.4 s | 16.0 s |  |  |
| `test_richtext` | 9 | 10.0 s | 9.9 s |  |  |
| `test_display_view` | 16 | 8.9 s | 10.0 s |  |  |
| `test_identity` | 13 | 8.3 s | 8.4 s |  |  |
| `test_tasks` | 6 | 5.4 s | 5.7 s |  |  |
| `test_notices` | 11 | 4.3 s | 6.6 s |  |  |
| `test_action_tabs` | 4 | 2.7 s | 2.3 s |  |  |
| `test_no_message_boxes` | 2 | 2.0 s | 2.1 s |  |  |
| `test_wheel` | 5 | 1.3 s | 1.3 s |  |  |
| `test_layout_store` | 4 | 1.3 s | 1.7 s |  |  |
| `test_groups` | 26 | 1.2 s | 1.5 s |  |  |
| `test_fit` | 7 | 1.2 s | 1.8 s |  |  |
| `test_lock` | 4 | 1.0 s | 1.1 s |  |  |
| `test_section_fields` | 1 | 0.9 s | 1.2 s |  |  |
| `test_call_command` | 4 | 0.8 s | 1.0 s |  |  |

### Installation, site, outillage

| Fichier | Tests | Temps final | Temps 1er run | Échecs 1er run | Sautés |
|---|--:|--:|--:|--:|--:|
| `test_site` | 36 | 77.5 s | 97.5 s |  |  |
| `test_packaging` | 18 | 35.9 s | 40.7 s |  |  |
| `test_harness` | 12 | 16.9 s | 18.5 s |  |  |
| `test_legal` | 9 | 7.9 s | 8.0 s |  |  |
| `test_updates` | 17 | 4.0 s | 9.4 s |  |  |

## Les tests les plus lents (run final)

| Temps | Test |
|--:|---|
| 61.4 s | `test_modes_window.test_a_remembered_document_is_kept_the_report_and_the_base_de_projet_included` |
| 50.1 s | `test_commands.test_the_calls_the_commands_tab_copies_compile` |
| 45.8 s | `test_polar_tab.test_an_empty_folder_survives_the_window_being_closed` |
| 42.0 s | `test_new_project.test_the_three_documents_compile_with_every_builtin_form_in_the_three_languages` |
| 40.7 s | `test_fire_tab.test_the_wall_tool_draws_a_wall_of_the_class_chosen_in_the_combo_and_one_undo_removes_it` |
| 40.7 s | `test_commands.test_every_example_compiles` |
| 35.3 s | `test_no_console.test_an_export_and_a_compilation_of_a_windowless_woodcore_open_no_console_window` |
| 34.9 s | `test_fire_tab.test_the_right_pane_asks_for_no_more_width_than_the_position_plans_whatever_is_selected` |
| 34.4 s | `test_modes_window.test_a_project_laid_out_as_one_report_stays_on_its_report` |
| 31.4 s | `test_theme.test_the_file_menu_offers_the_three_appearances_in_every_language` |

## Constats

- **`test_fire_tab` pèse le plus lourd** : 683 s cumulées au run final (16 % du total), 1766 s au 1er run, quand il tournait en un seul bloc. Chacun de ses tests construit la fenêtre et son canevas hors écran, entre 35 et 90 s par test. C'est la première piste si la durée de la suite redevient un problème (objectif de #22 : 20 minutes au plus).
- **Les tests de la fenêtre (PySide6)** représentent le quart du temps cumulé (1027 s), et ceux des plans un autre quart (948 s). Les calculs, eux, sont rapides : 14 fichiers et 376 tests en 300 s.
- **`tests/README.md` n'est plus complet** : il annonce que chaque fichier y a sa ligne, mais seuls 37 des 143 fichiers y figurent. Les catégories de ce bilan peuvent servir de base pour le compléter. Ce n'est pas fait ici : c'est hors du périmètre de #24.
- **Sur un nouveau poste Windows**, le dépôt sort désormais en LF quel que soit `core.autocrlf`. Un clone antérieur au commit de #24 doit être remis en LF une fois (`git add --renormalize .` ne suffit pas, car l'index est déjà en LF : il faut réécrire les fichiers du checkout, comme ce fut fait ici).
