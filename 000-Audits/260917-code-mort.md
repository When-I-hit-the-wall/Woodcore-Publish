# Définitions Python jamais appelées — liste pour décision

Audit périodique du 16.09.2026, constat AUD-6-11. Vous avez autorisé les corrections A, **sauf la suppression de ces définitions** : rien n'a été supprimé. Cette liste sert à décider, cas par cas.

**Vérifié le 17.09.2026, après les corrections du jour.** Chaque nom a été cherché, mot entier, dans tous les `.py` de `000-Python/` (tests compris) et dans `lib/*.typ`. On a aussi cherché les appels construits par `getattr(self, "set_" + …)` : il n'y en a aucun. Aucun de ces noms n'apparaît ailleurs que sur sa ligne de définition. Les deux `TOOL_ORDER` portent le même nom dans deux modules, et aucun des deux n'est lu.

La colonne « Constat » ne dit que ce qui a été vérifié. Elle ne devine pas pourquoi la définition est restée.

## Constantes

| Fichier:ligne | Nom | Ce que c'est | Constat |
|---|---|---|---|
| `calc/domains/connection_svg.py:19` | `MEMBER_FILLS` | alias de `schema_svg.ELEMENT_FILLS` | aucune lecture ; `MEMBER_STROKE`, deux lignes plus bas, est lu (`connection_svg.py:465`) |
| `calc/domains/connection_svg.py:20` | `MEMBER_OPACITY` | alias de `schema_svg.ELEMENT_OPACITY` | aucune lecture |
| `calc/domains/connector.py:62` | `ALL_ASSEMBLIES` | assemblages couverts + non couverts | aucune lecture |
| `calc/domains/connector.py:66` | `VIEWS` | `("h", "b")` | aucune lecture |
| `calc/domains/dowel.py:59` | `TIMBER_ASSEMBLIES` | assemblages bois-bois | aucune lecture ; le code lit `ASSEMBLIES[…]["family"]` directement (`connector.py:281`) |
| `calc/domains/dowel.py:60` | `STEEL_ASSEMBLIES` | assemblages acier-bois | idem |
| `calc/tools/build_reference.py:73` | `PUBLIC_NAMES` | tous les noms de `CATEGORIES` | aucune lecture |
| `calc/tools/schema_canvas.py:99` | `TOOL_ORDER` | ordre des outils de la barre « Schémas » | aucune lecture |
| `calc/tools/statics_canvas.py:85` | `TOOL_ORDER` | ordre des outils de la barre « Modèles statiques » | aucune lecture |

## Fonctions et méthodes

| Fichier:ligne | Nom | Ce que ça fait (d'après sa docstring) | Constat |
|---|---|---|---|
| `calc/domains/connection_svg.py:72` | `_over_white(colour, opacity)` | couleur d'un remplissage vu sur fond blanc, pour un halo d'étiquette | aucun appel |
| `calc/domains/connection_svg.py:96` | `_quarter(u)` | direction tournée d'un quart de tour | aucun appel |
| `calc/domains/connection_svg.py:101` | `_placed(point, ex, ez)` | point exprimé dans un repère (ex, ez) | aucun appel |
| `calc/domains/plan.py:559` | `axis_orientation(axis)` | « vertical », « horizontal » ou « oblique » | aucun appel |
| `calc/domains/statics_svg.py:156` | `_to_model(p, k)` | coordonnées de la figure → modèle, pour le pointeur du Katalog | aucun appel ; le canevas convertit par `mapToScene` de Qt (`statics_canvas.py:438`) |
| `calc/tools/build_reference.py:180` | `parse_doc_comments(typ_path)` | liaisons documentées d'un fichier `.typ` | aucun appel ; le module passe par `parse_bindings` |
| `calc/tools/build_reference.py:198` | `lib_records(root)` | liaisons documentées de `lib/` | aucun appel ; le module passe par `lib_bindings` |
| `calc/tools/build_reference.py:260` | `parse_param_docs(doc_lines)` | résumé et paramètres d'un bloc `///` | aucun appel ; le module passe par `parse_doc_block` |
| `calc/tools/command_preview.py:242` | `render_blocking(code, …)` | compile un exemple et rend le PNG | aucun appel |
| `calc/tools/grouped_list.py:89` | `GroupedList.set_strings(strings, lang)` | change les mots du widget | aucun appel ; les onglets passent leurs mots et `lang=` au constructeur (`schema_tab.py:682`) |
| `calc/tools/grouped_list.py:264` | `GroupedList.clear_marks()` | efface les icônes des entrées | aucun appel ; la méthode voisine pose les marques (`grouped_list.py:262`) |
| `calc/tools/schema_tab.py:1091` | `SchemaTab.set_field(key, value)` | écrit un champ du schéma lui-même | aucun appel ; l'identité passe par `identity.IdentityRows` (`schema_tab.py:920`) |

## Si vous décidez de supprimer

- **Sans risque apparent** : les constantes, les trois fonctions privées de `connection_svg.py`, `_to_model` et les trois lecteurs de `build_reference.py`. Un nom privé (`_…`) n'est pas fait pour être importé, et aucune de ces constantes n'est importée.
- **À regarder d'abord** : `render_blocking`, `set_strings`, `clear_marks` et `set_field`. Ce sont des méthodes publiques : un script à vous, hors du dépôt, pourrait s'en servir. Rien dans le dépôt ne le fait.
- Après suppression, lancer `python tests/run_tests.py` seul : `test_editor_buttons.py` clique tous les boutons des cinq onglets, et `test_commands.py` reconstruit le classeur de référence.
