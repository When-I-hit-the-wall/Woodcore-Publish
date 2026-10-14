# Rapport de la phase 5 — chaque bouton du Typst-Katalog fonctionne et fait ce qu'il annonce

Agent « p5 », audit 260916-2326, commit audité `997570db`, bac à sable `AUDIT/projet-phase5`, scripts et sorties brutes dans `AUDIT/p5/` (et `AUDIT/p5/out/`). Travail interrompu vers 23h52 par la limite de session de l'API, repris le 17.09 vers 07h00 sur le même bac à sable.

## ⚠️ État git du projet réel

`git status --short` du projet réel était **vide** au début de la phase et encore vide à la reprise (07h17). Au moment de rendre la main, **37 fichiers sont modifiés** dans l'arbre réel (27 à 07h45, 37 à 07h52, le nombre augmente pendant que j'écris : `CLAUDE.md`, `README.md`, `calc/domains/schema.py`, `connection.py`, `connector.py`, `dowel.py`, `plan.py`, `export_all.py`, `validation.py`, `build_reference.py`, `i18n/strings.json`, `lib/*.typ`, 4 schémas JSON, `tests/*`…, aucun fichier non suivi). **Ils ne viennent pas de cet agent** : (1) tous mes scripts importent `calc/` depuis le bac à sable et vérifient `catalog_gui.ROOT == <bac>/000-TypstRapport/000-Python` et `MAIN_TYP`/`REPORT_PDF` dans le bac à sable avant toute action (assertions dans `p5/common.py`) ; (2) les modifications portent le commentaire « periodic audit 260916 » et citent AUD-1-3, c'est-à-dire la phase 9 de la session principale ; (3) aucune des chaînes de mes corrections proposées (« never the kind of an aid », « the form holds a draft never saved », « A change that changes nothing », `along * ux - across * uz`) n'est présente dans l'arbre réel (`grep -rn` vide) ; (4) le dernier `000-Archives` réel date de 260916-11h00, avant mes exports (23h48 et suivants, tous dans le bac à sable) ; (5) `%LOCALAPPDATA%\typst-katalog\stalls.log` réel n'a pas été touché depuis 22h33 (mes processus Qt avaient `LOCALAPPDATA`, `APPDATA` et `TYPST_KATALOG_SETTINGS` dans le bac à sable dès le premier lancement, `p5/run.py`).

⚠️ **Conséquence pour la phase 9** : `calc/domains/schema.py` est déjà modifié dans l'arbre réel ; mes corrections proposées ont été rédigées et validées sur la version du commit `997570db` (copie du bac à sable). Le remplacement de AUD-5-1 est d'une ligne et reste applicable tel quel (la ligne visée n'était pas touchée par le diff observé).

## Bilan chiffré

- Inventaire : **810 éléments** relevés (270 à l'ouverture et avec la première entrée chargée, 540 dans les états cachés : panneaux de sélection, exemples ouverts, dialogues, menus contextuels ; 457 distincts). **0 bouton mort** (1 faux positif expliqué). 5 éléments désactivés sans infobulle.
- Clic et effet vérifié : **≈ 430 contrôles** (barre du haut 81, éditeurs 105 + 10 cas « Supprimer sur un brouillon », canevas 160, confirmations 19, formulaires 22, charges/commandes/états cachés/langue 29, derniers contrôles 3).
- Appels copiés : **1 245 appels distincts compilés** dans le bac à sable (182 documents) ; **15 ne compilent pas** (+1 artefact de ma collecte, écarté).
- Constats : **A = 6**, **B = 3**, **C = 4**, **NON FAIT = 7**.
- Tests de non-régression proposés : **6**, tous exécutés contre le `tests/` du bac à sable : les 6 **échouent sur le code du commit** ; 5 **passent avec la correction proposée** appliquée dans le bac à sable (AUD-5-1 à AUD-5-5 ; celle de AUD-5-6 n'est pas appliquée, ses phrases restant à écrire) ; les suites existantes concernées (`test_schema_edit` 32, `test_schema_tab` 32, `test_editor_buttons` 1, `test_groups` 15, `test_schema_consumers` 18, `test_katalog_identity` 13, `test_fit` 7, `test_polar_tab` 13) passent avec les corrections appliquées dans le bac à sable.

## Méthode

Tout script Qt tourne par `p5/run.py` : sous-processus, délai 300 s, `QT_QPA_PLATFORM=offscreen`, `QT_QPA_FONTDIR`, `TYPST_KATALOG_SETTINGS`, `LOCALAPPDATA` et `APPDATA` dans le bac à sable. `p5/common.py` construit `catalog_gui.Catalog()` directement (jamais `main()`), remplace `install_error_box` par un enregistreur d'exceptions (`sys.excepthook`), bouchonne `QMessageBox.warning/critical/information` (OK), `question` (Oui ; « Enregistrer / Ignorer / Annuler » → Ignorer), `QFileDialog`, `QInputDialog.getText/getDouble`, `QDesktopServices.openUrl` et `os.startfile` (appels enregistrés). ⚠️ Piège découvert : `QMenu.exec` et `QDialog.exec` **ne peuvent pas être remplacés sur la classe Shiboken** (le vrai `exec` modal s'exécute et bloque, vérifié par `p5/probe_menu.py`) ; il faut remplacer le nom `QMenu` dans les modules (`grouped_list`, `commands_tab`, `catalog_gui`) par une sous-classe Python et `PageDialog.exec` / `GridDialog.exec` sur les sous-classes. Les clics sur les canevas passent par `QTest.mouseClick` sur le viewport (vrai chemin souris), les glisser-déposer de liste par `GroupedList.dropEvent` avec un `QDropEvent` construit. Récepteurs : `receivers(SIGNAL(...))` sur `clicked()`, `toggled(bool)`, `pressed()`, `released()`, `triggered()`, les signaux du `QButtonGroup` / `QActionGroup` ; un `QToolButton` porte 2 récepteurs internes à Qt (pressed/released vers son propre minuteur de menu), soustraits.

Scripts : `inventory.py` (5.1), `calls.py` + `compile_calls.py` (5.3), `top.py` (barre du haut), `editors.py` (Nouveau, Enregistrer, Dupliquer, Supprimer, Restaurer, Supprimer définitivement, Annuler les modifications, dossiers), `unsaved_delete.py`, `canvas.py` (outils, clics réels, Annuler/Rétablir, Ajuster, listes, Trancher/Fusionner/Grille…/Effacer les lignes/Cadrage), `confirm.py`, `forms.py` (Connecteurs, Moments polaires), `misc.py` (Charges, Commandes, états cachés, langue), `final_checks.py`, `proposed_tests.py`, `apply_patches.py`, `sandbox_suites.py`. Journaux : `p5/out/*.log`, données : `p5/out/*.json`, diff proposé : `p5/out/proposed.diff`.

## 5.1 Inventaire

| Onglet | éléments (ouverture + 1re entrée) | actifs | désactivés | dans un groupe exclusif | morts |
|---|---|---|---|---|---|
| Barre du haut | 17 (Recharger, 2 boutons partagés, 14 actions de menu) | 17 | 0 | 11 (menu PDF) | 0 |
| Plan de position | 50 | 47 | 3 | 18 (outils) | 0 |
| Charges | 10 | 9 | 1 | 0 | 0 |
| Combinaisons de charges | 0 (FutureTab : un texte, aucun bouton) | — | — | — | — |
| Modèles statiques | 51 | 51 | 0 | 20 | 0 |
| Schémas | 57 | 57 | 0 | 26 | 0 |
| Connecteurs | 47 | 40 | 7 | 0 | 0 |
| Moments polaires | 24 | 23 | 1 | 0 | 0 |
| Commandes | 14 | 14 | 0 | 6 (sélecteur de niveau) | 0 |

États cachés inventoriés (`p5/out/misc.json`, clé `inventory`) : panneaux de sélection des modèles statiques (point, barre, appui, articulation, charge ponctuelle, charge linéaire, cotation), des schémas (élément, repère, aide, cotation, sur SD_01 et VU-Skizze), du plan (élément, axe) ; un exemple ouvert de l'onglet Commandes ; `PageDialog` (plusieurs pages et une seule) et `GridDialog` ; les menus contextuels des cinq listes (entrée, dossier, « Archives », entrée archivée — cette dernière dans `editors.py`) et des arbres Charges et Commandes. Chaque action de menu a au moins un récepteur.

- **Désactivés, tous avec infobulle** : les 7 types de connecteur non implémentés (« Clou : le calcul n'est pas encore implémenté. Seule la broche l'est. »), conforme à la règle v0.47.
- **Désactivés sans infobulle** (constat AUD-5-6) : « Calibrer… » et « Longueurs des murs (V, H, W) » (Plan, tant que le mode d'échelle n'est pas « calibration » ou qu'il n'y a pas d'échelle), « Annuler les modifications » (Plan et Moments polaires, tant que rien n'est modifié ; les trois autres éditeurs le laissent actif), « Ouvrir le classeur » (Charges, rien de sélectionné ou cas lu d'une norme).
- Désactivés sans infobulle mais expliqués à côté (C, AUD-5-13) : sélecteur 1 · 2 · 3 d'un exemple qui fixe son niveau (relevé sur les exemples ouverts de `show-calc` ; le texte « fixé à 3 par l'appel lui-même… » est affiché à droite) ; « Créer (0) » / « Choisir » de `PageDialog` tant qu'aucune page n'est cochée.
- Faux positif écarté : le bouton radio « Variables » du panneau d'une charge n'a aucun récepteur propre, mais il est auto-exclusif avec « Valeur », dont `toggled` porte le récepteur ; cliqué, il bascule bien la grandeur (`{"value": 0.55, "unit": "kN"}` → `{"domain": "dead-load", …}`, `final_checks.py`).

## 5.2 Clic et effet, par famille

| Famille | Onglets | Résultat |
|---|---|---|
| Recharger | haut | reconstruit les onglets, garde l'onglet courant et la recherche des Charges — conforme |
| Importer Excel (bouton et entrée du menu) | haut | lance `export_all.py` du bac à sable, désactive les deux boutons pendant l'export, code 0 (13,5 à 18,6 s), `data/calculations.json` réécrit, statut « Export terminé, données rechargées. », boutons réactivés — conforme ; une boîte d'avertissement s'ouvre à chaque export (C, AUD-5-10) |
| Exporter PDF, les 11 entrées du menu | haut | 7 exécutions couvrant Tel qu'écrit, Niveau 1/2/3, Uniforme 1/2/3, Langue du document, Français, Deutsch, English : export puis `typst compile`, arguments `--input` exactement ceux du réglage (`[]`, `level=1 lang=fr`, `level=2 lang=de`, `level=3 lang=en`, `uniform=1`, `uniform=2 lang=fr`, `uniform=3 lang=de`), `Statischer Rapport.pdf` **du bac à sable** écrit (dernier : 4 085 793 octets, taille du PDF de référence de-u3 de la phase 1), `openUrl` bouchonné reçoit ce chemin, `000-Archives/` du bac à sable reçoit une archive de plus avec `archive-info.json` portant les mêmes drapeaux (`260916-23h50-2`, `-3`, `23h51-2` : le suffixe de même minute fonctionne) — conforme |
| Nouveau | 5 éditeurs | une ligne de plus, fiche modifiée, point sur le titre de l'onglet, identifiant libre (P02, S01, D01, SD_01, calcul polaire) — conforme sauf Connecteurs : le brouillon n'apparaît pas dans la liste (B, AUD-5-8) |
| Enregistrer | 5 éditeurs | `<dossier>/<id>.json` écrit dans le bac à sable, `check_source` passe, l'export du domaine a tourné (`data/*.json` plus récent et contenant l'id), point effacé — conforme |
| Dupliquer | 5 éditeurs | nouvel id libre, contenu enregistré identique à l'original hors identité (et hors numéros des éléments pour un plan, voulu) — conforme |
| Supprimer | 5 éditeurs | sur une entrée enregistrée : source déplacée dans `archives/` sans `id` (`"archived": {"id": …, "at": …}`), absente de l'export et ses figures supprimées (ex. `SD_02-kbeta-1.svg` … `SD_02-section.svg`), question de confirmation — conforme. **Sur un brouillon non enregistré (après Nouveau ou Dupliquer) : archive l'entrée enregistrée encore surlignée dans Plan de position et Connecteurs** (A, AUD-5-3) |
| Restaurer / Supprimer définitivement (menu d'une entrée archivée) | 5 éditeurs | Restaurer réécrit la source sous un id (fait du nom, ex. `Velo_Unterstand` pour VU-SD-10, ou l'ancien) et l'exporte ; Supprimer définitivement demande puis efface — conforme |
| Annuler les modifications | 5 éditeurs | la fiche égale de nouveau le fichier (toutes les clés du fichier comparées) — conforme ; dans Moments polaires le bouton ne s'active qu'au rafraîchissement différé (≈ 200 ms), sans conséquence |
| Annuler / Rétablir (canevas) | Plan, Modèles statiques, Schémas | une étape de moins puis de plus, dessin changé puis rétabli — conforme ; **une modification refusée laisse une étape dans Modèles statiques** (A, AUD-5-4) |
| Outils de canevas | Plan (18), Modèles statiques (20), Schémas (26) | chaque bouton : `canvas.tool` change, bouton coché, texte d'aide affiché — conforme. Clics réels : Modèles statiques 18 outils (point, barre, câble, ressort, 3 appuis, 4 articulations, charge ponctuelle en 2 clics, 2 charges linéaires, 4 cotations dont angle) ; Schémas : linéaire, surfacique, 5 aides, 3 cotations ; Plan : 3 axes, T, S, refus V/H/W/A/D/M/L (une alerte « Aucune position V dans Positionen.xlsx… », rien dessiné), Ö et B sans numéro commencent un tracé — chaque entrée passe `check_source` |
| Déplacer / Dupliquer / Tourner (clics réels) | Schémas | une étape, sélection transformée, `check_source` passe — conforme |
| **Symétrie** | Schémas | **ne déplace aucun point** (une étape d'annulation, dessin inchangé) — A, AUD-5-1 |
| Trancher / Fusionner | Schémas | une poutre coupée sur une ligne verticale donne deux pièces de même position ; fusionnées, les points d'origine `[[0,0],[400,0]]` reviennent ; sans sélection : aucune étape, rien levé — conforme |
| **Grille…** | Schémas | **KeyError: 'kind' avec « Sélection » (l'outil à l'ouverture), Linéaire, Surfacique, Déplacer…** ; avec un outil d'aide ou de cotation, repères de sorte `point` / `horizontal` que `check_source` refuse ; avec un outil de fixation : 6 repères, Annuler du dialogue remet les repères — A, AUD-5-2 |
| Effacer les lignes | Schémas | lignes de construction retirées, points gardés, une étape — conforme |
| Cadrage (glisser), Dessiner, Feuille entière / Tout le dessin | Plan, Schémas | Plan : glisser pose le cadrage et rend l'outil Sélection, « Feuille entière » l'ôte, « Dessiner » choisit l'outil — conforme ; Schémas : « Tout le dessin » et « Dessiner » conformes, le glisser n'est pas reproductible hors écran (`mouseMoveEvent` exige `event.buttons() & LeftButton`, que `QTest.mouseMove` n'envoie pas) → liste manuelle |
| Ajuster | 3 canevas | depuis une vue à 0,01 px/unité décentrée : transformation changée, figure (ou cadrage, ou feuille) entièrement visible — conforme |
| Accrocher, Accrocher aux axes / aux éléments | 3 canevas | pilotent `canvas.snap_on` / `snap_axes` / `snap_elements` — conforme |
| Ajouter / Retirer sous les listes | Modèles statiques (5), Schémas (6) | une ligne de plus puis de moins — conforme (sauf refus silencieux AUD-5-4) |
| Plan : Choisir…, Retirer (fond), Pages…, Calibrer…, Longueurs des murs, Effacer (sélection), Ajouter (axe parallèle) | Plan | fond choisi et retiré, page 2 choisie sur les vignettes (dialogue bouchonné), étalonnage en 2 clics + longueur saisie (`{"mode": "calibration", "length_m": 2.5}`), `show_lengths` écrit, élément effacé, axe parallèle ajouté — conforme |
| Connecteurs : Broche, Changer de type…, Reprendre ×2, Tout cocher / décocher, Reprendre du dessin, cases à cocher | Connecteurs | barre repliée puis dépliée ; classe écrasée (C16 sur T001) → ligne orange + Reprendre → suit de nouveau C24, `material: null` ; classe d'humidité idem ; fixations vidées puis `A12…A15` ; n = 9 / a₁ = 1 mm remplacés par 2 / 120 mm ; séisme, treillis (R_d,Verb,Fachwerk affiché), n_tot écrasé, pré-percé écrits dans le brouillon — conforme |
| Moments polaires : Ajouter / Retirer un élément, Tout cocher / décocher, 3 boutons radio | Moments polaires | 2 → 3 → 2 membres, aucun « Retirer » actif au minimum de 2, fixations vidées puis cochées, `center.mode` manual / aid / centroid — conforme |
| Copier (chaque appel) | tous | presse-papiers = appel (via `app.copy`, statut « Copié ») ; Schémas copie tout le bloc directement sans statut (C, AUD-5-11) ; compilation : voir 5.3 |
| Ouvrir le classeur | Charges | chacun des cas lus d'un classeur ouvre son classeur du bac à sable (bouchon) ; cas de norme : bouton désactivé — conforme (infobulle manquante, AUD-5-6) |
| Menu contextuel, double-clic, Ctrl+C | Charges, Commandes | une entrée par appel, chacune copie son appel ; double-clic et Ctrl+C copient le premier — conforme |
| Nouveau dossier (bouton du titre), Renommer / Supprimer le dossier (menu), glisser vers un dossier et hors du dossier | 5 éditeurs | dossier listé et écrit dans `settings.json` du bac à sable, renommé partout, champ `group` écrit dans la source par le dépôt et retiré au retour à la racine, dossier vidé conservé après reconstruction et dans les réglages, suppression du dossier retirée des réglages — conforme |
| Langue fr → de → en → fr | haut + 5 éditeurs | brouillons non enregistrés (description modifiée) conservés à chaque bascule, même entrée, point conservé, onglet courant gardé — conforme |
| Onglet Commandes : flèches, sélecteur de niveau | Commandes | 133 exemples ouverts : 131 pages figées « fresh » affichées, 2 `typ-dry` (show-check) annoncés comme non rendus, aucun rendu relancé ni erreur ; niveau changé à chaque clic sur un exemple non fixé, 3 boutons désactivés sur les exemples qui fixent leur niveau — conforme |

## 5.3 Appels copiés, compilés en masse

Collecte en cliquant chaque bouton Copier (`calls.py`) : Charges 1 036 appels (toutes les variables, cas et domaines), Plan 43 (4 plans, chaque élément et axe sélectionné), Modèles statiques 24 (chaque entrée sélectionnée), Schémas 42 (chaque entrée), Connecteurs 8, Moments polaires 7, Commandes 85 (complet et minimal de chaque commande publique, import). Compilation (`compile_calls.py`) : un document par appel contenant `#var`, `#unit`, `#var-unit` ou `#var-domain`, les autres par lots de 40, un lot en échec recompilé appel par appel ; `--root <bac>/000-TypstRapport`, en-tête `#import "../commands.typ": *`. 1 245 appels, 182 documents, 0 avertissement Typst, **16 échecs** : 1 artefact (j'avais découpé en lignes le bloc copié par Schémas ; le bloc entier compile, vérifié `p5probe/fix1.typ`), et 15 réels :

- 5 appels de lecture de la langue sans `context` : `#report-lang()`, `#t-str("governing")`, `#tl-str("Bezugshöhe")`, `#t-label("governing")`, `#t-pattern("connection.caption")` → « can only be used when context is known » (A, AUD-5-5) ;
- 8 appels du registre qui nomment des variables non déclarées : `#var-unit("R_k", "N")`, `#eq("R_d", `k_dens dot R_k`)`, `#val("R_d")`, `#verify(`F_Ed <= R_d`)`, en complet et minimal (B, AUD-5-7) ;
- 2 appels `#show-check("snow-load", "SL", "<check-name>")` (complet et minimal) : aucun `checks[]` exporté, exemption connue du §14 (C, AUD-5-12).

## Constats

**AUD-5-1 | A | `000-TypstRapport/000-Python/calc/domains/schema.py:1332` | « Symétrie » (onglet Schémas) ne déplace aucun point : `reflection()` renvoie le point lui-même, et seuls les angles des lignes de construction sont repliés et les cotes changées de côté.** Preuve : `python -c "from domains import schema as m; p,_,_=m.reflection((0,600),(100,600)); print(p(0,0), p(50,100))"` → `(0.0, 0.0) (50.0, 100.0)` au lieu de `(0, 1200) (50, 1100)` ; axe vertical x = 0 : `p(30, 5)` → `(30.0, 5.0)` au lieu de `(-30, 5)` ; par clics réels (`canvas.py`) et par `place()` (`confirm.py`) : une étape d'annulation, éléments identiques. Le seul test existant, `test_mirroring_twice_gives_back_the_coordinates_it_started_from`, passe aussi pour l'identité. Aucune source du projet n'a été symétrisée (le bouton ne faisait rien aux points), donc aucun nombre imprimé n'en dépend. Correction : remplacer `return (ax + along * ux + across * uz, az + along * uz - across * ux)` par `return (ax + along * ux - across * uz, az + along * uz + across * ux)` ; test : `test_a_mirror_moves_a_point_to_the_other_side_of_its_axis` (code ci-dessous) dans `tests/test_schema_edit.py`. Validé dans le bac à sable : le test échoue avant (`AssertionError: (0.0, 0.0)`), passe après ; `test_schema_edit` 32/32 et `test_schema_tab` 32/32 passent après.

**AUD-5-2 | A | `000-TypstRapport/000-Python/calc/tools/schema_canvas.py:804` | « Grille… » lève `KeyError: 'kind'` dès que l'outil actif n'a pas de sorte — dont « Sélection », l'outil avec lequel l'onglet s'ouvre — et, avec un outil d'aide ou de cotation, pose des repères de sorte `point` / `horizontal` que l'export refuse.** Cause : précédence Python, `kind = kind or TOOLS[self.tool]["kind"] if self.tool in TOOLS else …` se lit `(kind or TOOLS[self.tool]["kind"]) if …`, et `schema_tab.place_grid` passe la sorte de n'importe quel outil. Preuve (`final_checks.py`, fenêtre neuve) : « schema tab opens with tool: select » puis « Grille… in a fresh window: exception: KeyError: 'kind' markers: 4 » ; `confirm.py` : `aid-point` → sortes `['point']`, `check_source` → `ValidationError("… connector C1's kind is 'point' -- expected Stabdübel, …")` ; `connector:Nagel` → 6 repères `Nagel`, valide. Sous pythonw, `install_error_box` affiche la trace ; le bouton ne fait rien d'autre. Correction : remplacer la ligne par `if kind not in model.CONNECTOR_KINDS:` / `tool_kind = TOOLS.get(self.tool, {}).get("kind")` / `kind = tool_kind if tool_kind in model.CONNECTOR_KINDS else "Stabdübel"` (la règle déjà écrite dans `add_default`, ligne 709) ; test : `test_grille_places_valid_markers_whatever_tool_is_in_force` dans `tests/test_schema_tab.py`. Validé : échoue avant (`KeyError: 'kind'`), passe après.

**AUD-5-3 | A | `000-TypstRapport/000-Python/calc/tools/source_archive.py:165-177` et `connectors_tab.py:1941-1943` | « Supprimer » sur un brouillon jamais enregistré (juste après Nouveau ou Dupliquer) archive, dans Plan de position et Connecteurs, l'entrée enregistrée encore surlignée dans la liste, et laisse le brouillon dans la fiche.** Preuve (`unsaved_delete.py`) : Plan, après Nouveau : `"list_selection_with_draft": ["Fluchttreppe"], "archived": ["260917-072036-Fluchttreppe.json"]`, question « « Fluchttreppe » ira dans « Archives »… » ; idem après Dupliquer ; Connecteurs après Nouveau et après Dupliquer : `VU-SD-10` archivé. Modèles statiques, Schémas, Moments polaires : rien archivé (leur liste sélectionne la ligne du brouillon). La question nomme la mauvaise entrée, mais l'intention du bouton est écrite dans la docstring de `plan_tab.delete` (« A plan never saved is simply discarded ») et dans celle de `Actions.delete` (« False where there is nothing saved to act on, so the tab discards its unsaved draft »). Réversible (Restaurer), mais l'id restauré est fait du nom (VU-SD-10 revient en `Velo_Unterstand`) et le dossier `group` est perdu. Correction : dans `Actions.delete`, après le traitement des `keys`, insérer `if getattr(self.tab, "current_id", None) is None and getattr(self.tab, "dirty", False): return False` ; dans `ConnectorsTab.delete`, remplacer `self.archive.delete()` par `if self.archive.delete(): return` puis `self.dirty = False`, `self.reload_list()`, ouvrir `self.ids[0]` s'il existe, sinon `self.new()` (diff complet ci-dessous). Test : `test_supprimer_on_an_unsaved_draft_archives_nothing` dans `tests/test_editor_buttons.py`. Validé : échoue avant (« ConnectorsTab before duplicate: no saved entry left to open »), passe après ; `test_editor_buttons`, `test_groups`, `test_katalog_identity`, `test_polar_tab` passent après.

**AUD-5-4 | A | `000-TypstRapport/000-Python/calc/tools/statics_tab.py:1531-1538` (via `add_row`, 1721) | Dans Modèles statiques, « Ajouter » sous Barres, Charges ponctuelles, Charges linéaires ou Cotations d'un modèle sans points ni barres n'ajoute rien, mais pousse une étape d'« Annuler », marque le modèle modifié et ne dit rien.** Preuve (`confirm.py`) : `{'members': 0, 'undo_steps': 1, 'dirty': True, 'events': [], 'status': ''}` ; après « Annuler », `dirty` reste `True`. Contredit la règle du §13 (v0.73) « a refusal leaves no step ». Correction : `edit()` copie la source avant `apply()`, et si rien n'a changé retire l'étape et renvoie `False` sans `on_changed()` (diff ci-dessous) ; ajouter dans `add_row` un statut « rien à quoi l'attacher » (`if not self.edit(apply): self.app.set_status(...)`, trois langues à écrire). Test : `test_a_refused_ajouter_leaves_no_undo_step_and_no_dot` dans un nouveau `tests/test_statics_tab.py`. Validé : échoue avant (« «Ajouter» members refused and still took 1 step(s) »), passe après.

**AUD-5-5 | A | `000-TypstRapport/000-Python/calc/tools/build_reference.py:543-548` | L'onglet Commandes copie pour `report-lang`, `t-str`, `tl-str`, `t-label` et `t-pattern` un appel qui ne compile pas collé tel quel : ces commandes lisent la langue du rapport et exigent `context`.** Preuve : `typst compile` de `#report-lang()` → « error: can only be used when context is known » (5 appels, complet = minimal) ; `#context report-lang()` etc. compilent (`p5probe/fix1.typ`, code 0). CLAUDE.md §10sexies promet qu'un appel copié « compiles as pasted » et `WRITTEN_CALLS` porte déjà le précédent `"report-language": ("#context report-language.get()",) * 2`. Correction : ajouter à `WRITTEN_CALLS` les cinq entrées `"report-lang": ("#context report-lang()",) * 2`, `"t-str": ('#context t-str("governing")',) * 2`, `"tl-str": ('#context tl-str("Bezugshöhe")',) * 2`, `"t-label": ('#context t-label("governing")',) * 2`, `"t-pattern": ('#context t-pattern("connection.caption")',) * 2`. Test : `test_the_calls_the_commands_tab_copies_compile` dans `tests/test_commands.py` (chaque appel complet et minimal compilé seul, exemptés `show-check`, `var-unit`, `eq`, `val`, `verify` en attendant AUD-5-7) ; passe avec la correction (56 s). ⚠️ `build_reference.py` est en CRLF : conserver les fins de ligne ; `docs/typst-reference.xlsx` changera en conséquence (colonnes `call_*`).

**AUD-5-6 | A | `plan_tab.py:1188`, `plan_tab.py:1197`, `plan_tab.py:1541` et `1953`, `catalog_gui.py:2222`, `catalog_gui.py:1105-1107` | Cinq éléments s'affichent désactivés sans infobulle qui dise pourquoi : « Calibrer… » et « Longueurs des murs (V, H, W) » (Plan), « Annuler les modifications » (Plan, Moments polaires), « Ouvrir le classeur » (Charges).** Preuve : `test_a_disabled_button_says_why` (code ci-dessous) sur le commit → « disabled with nothing to say why: LoadsTab: Ouvrir le classeur; PlanTab: Annuler les modifications; PlanTab: Calibrer…; PlanTab: Longueurs des murs (V, H, W); PolarTab: Annuler les modifications ». Correction : poser l'infobulle là où l'état est décidé (`self.calibrate_button.setToolTip("" if mode == 2 else self.t("plan_calibrate_why"))`, `self.lengths_box.setToolTip("" if per_m else self.t("plan_lengths_why"))`, `self.revert_button.setToolTip("" if self.dirty else self.t("…_revert_why"))`, `self.open_button.setToolTip(...)` dans `show_selection`), avec des phrases à écrire en fr/de/en (« Choisir d'abord le mode d'échelle « Calibration » », « Le plan n'a pas d'échelle », « Rien n'a été modifié », « Sélectionner un cas lu d'un classeur »). Variante équivalente : laisser « Annuler les modifications » toujours actif comme dans les trois autres éditeurs. Test : `test_a_disabled_button_says_why` dans `tests/test_catalog.py` (exécuté : échoue sur le commit ; correction non appliquée dans le bac à sable).

**AUD-5-7 | B | `000-TypstRapport/000-Python/calc/tools/build_reference.py:553-574` (`POSITIONAL_TAILS`, `ARGUMENT_LITERALS`) | Les appels complet et minimal copiés pour `var-unit`, `eq`, `val` et `verify` ne compilent pas collés seuls : ils nomment `R_k`, `k_dens`, `R_d`, `F_Ed`, qu'aucun `#var` n'a déclarés.** Preuve : « panicked with: "eq: no variable named "k_dens", "R_k" here -- declare it with #var(...) above this line… » (8 appels) ; le même contenu précédé de `#var("R_k", 7, "kN")`, `#var("k_dens", 0.806)`, `#var("F_Ed", 2, "kN")` compile (`p5probe/fix2.typ`, code 0). Contredit la phrase de CLAUDE.md §10sexies « a copied call … compiles as pasted ». Options : (a) copier pour ces quatre commandes les `#var` nécessaires avant l'appel (bloc de 2 à 4 lignes, `WRITTEN_CALLS`) ; (b) garder l'appel seul et corriger §10sexies en nommant l'exception (les commandes du registre supposent des variables déclarées) ; (c) exempter ces commandes du test de compilation proposé, comme `show-check`.

**AUD-5-8 | B | `000-TypstRapport/000-Python/calc/tools/connectors_tab.py:1906-1933` et `540-548` | Dans Connecteurs, « Nouveau » et « Dupliquer » n'ajoutent pas de ligne « (nouveau) » à la liste et laissent le connecteur précédent surligné, alors que les quatre autres éditeurs listent le brouillon et le sélectionnent.** Preuve (`editors-cp.log`) : « rows 1->1 dirty=True id='SD_01' » ; `unsaved_delete.py` : `"list_selection_with_draft": ["VU-SD-10"]`. C'est ce qui rend possible AUD-5-3 dans cet onglet ; le Plan liste le brouillon mais ne le sélectionne pas (`plan_tab.reload_list` passe `select=None`). Options : (a) aligner Connecteurs sur les autres (ligne `NEW_ROW` sélectionnée) et faire sélectionner `NEW_ROW` par `plan_tab.reload_list` quand `current_id is None`, comme `statics_tab.reload_list` ; (b) garder la liste des seuls fichiers et se contenter de la garde de AUD-5-3.

**AUD-5-9 | B | `000-TypstRapport/000-Python/calc/tools/statics_tab.py:2004-2010` (`set_magnitude_kind`) | Dans le panneau d'une charge, passer de « Valeur » à « Variables » puis revenir à « Valeur » perd la valeur saisie.** Preuve (`final_checks.py`, Bankli-Fall1, première charge ponctuelle) : `{"value": 0.55, "unit": "kN"}` → « Variables » → `{"domain": "dead-load", "instance": "EL+AL-Dach mit Wasser", "var": "gk"}` → « Valeur » → `{"value": 1.0, "unit": "kN"}`. CLAUDE.md §10quater dit que la variable est mémorisée pendant qu'on essaie une valeur, « so changing one's mind twice does not lose it » ; le cas inverse perd le nombre, et un enregistrement change la charge imprimée sur la figure. Options : (a) mémoriser aussi la valeur littérale par charge, symétriquement ; (b) accepter et le dire dans §10quater.

**AUD-5-10 | C | `000-TypstRapport/000-Python/calc/tools/catalog_gui.py:2985-2988` | Tant que l'export émet des avertissements (ici ceux de AUD-1-5 : feuilles retirées de Positionen.xlsx, VU-SD-10, Bankli-Fall2), chaque « Importer Excel » et chaque « Exporter PDF » ouvre une boîte « Export terminé avec des avertissements » ; pour le PDF elle bloque avant la compilation.** Preuve : 9 exports sur 9 dans `top.log` (`('warning', "Typst-Katalog | Export terminé avec des avertissements :…")`). Comportement voulu ; disparaît quand AUD-1-5 est traité.

**AUD-5-11 | C | `000-TypstRapport/000-Python/calc/tools/schema_tab.py:1623-1625` | « Copier » de l'onglet Schémas écrit le bloc entier directement dans le presse-papiers, sans passer par `app.copy` : pas de statut « Copié : … », contrairement aux six autres onglets.** Preuve : `calls.py`, 32 clics où `app.copy` n'est pas appelé et le presse-papiers contient le bloc. Suggestion : `self.app.copy(self.calls_view.toPlainText())`.

**AUD-5-12 | C | `000-TypstRapport/000-Python/calc/tools/build_reference.py` (appels de `show-check`) | Les deux appels copiés de `show-check` portent `"<check-name>"` et ne compilent pas (aucun `checks[]` exporté).** Exemption connue (§14, `test_commands.test_every_public_command_offers_two_calls_that_name_real_things`) ; rappelée pour le bilan de 5.3.

**AUD-5-13 | C | `commands_tab.py:212-225`, `plan_tab.py:748-755` | Le sélecteur 1 · 2 · 3 d'un exemple qui fixe son niveau et les boutons OK de `PageDialog` sont désactivés sans infobulle ; le premier est expliqué par un texte visible à côté, le second tant qu'aucune page n'est choisie.** Information ; une infobulle reprenant le texte serait cohérente avec AUD-5-6.

## Artefacts de mon harnais (non retenus)

Pour la transparence : premier export de `canvas.py` — 4 échecs « Ajouter / Retirer » Schémas (je prenais les boutons dans l'ordre de `findChildren`, pas de leur page ; refait par page dans `confirm.py` : 6/6 conformes), 2 échecs « Ajuster » (mauvais rectangle de référence ; refait : figure visible), Plan Ö et B « sans alerte » (ces types ne portent pas de numéro, `plan.labelled` → False : conforme), « Effacer la recherche (×) » (`trigger()` sur l'action de la ligne de saisie ne vide pas : Qt branche le bouton, pas l'action → vérification manuelle), Cadrage glissé dans Schémas (limite de `QTest.mouseMove`), `test_polar_tab.test_an_empty_folder_survives_the_window_being_closed` en échec seulement quand mon lanceur impose `TYPST_KATALOG_SETTINGS` (passe sans, 13/13).

## NON FAIT

- Bouton « Installer » de la bannière des mises à jour et installation des dépendances : non cliqués (appel à pip et téléchargement, interdits sans accord ; la bannière n'apparaît qu'après une réponse de PyPI).
- Glisser-déposer à la souris, survol (boîtes éclairées de Connecteurs, ligne survolée des listes), molette (zoom autour du pointeur), bouton du milieu (panoramique), poignées et étiquettes déplacées à la souris, Cadrage glissé dans Schémas : non automatisables hors écran de façon fidèle → liste manuelle.
- Rendu réel des PDF d'architecte et des vignettes (qualité, netteté) : visuel → liste manuelle.
- « Nouveau » plan sur un PDF de plusieurs pages avec plusieurs pages cochées (`create_plans`) : non exécuté (temps), seule la sélection d'une page par « Pages… » l'a été.
- Fermeture de la fenêtre pendant un export ou une compilation (`closeEvent` avec `close_requested`) : non exécuté.
- Chemin d'échec d'« Importer Excel » / « Exporter PDF » (export ou compilation en erreur) : non provoqué (il faudrait casser un classeur ou `lib/` du bac à sable).
- Rendu de repli d'un exemple périmé ou manquant de l'onglet Commandes : aucun n'est périmé (131 « fresh »), chemin non atteint.

## Liste de vérification manuelle pour l'ingénieur (≈ 8 minutes)

1. Schémas, ouvrir SD_01, laisser « Sélection » actif, cliquer « Grille… » : aujourd'hui une boîte d'erreur `KeyError: 'kind'` (AUD-5-2). Choisir l'outil « Broche », recliquer : le dialogue s'ouvre, OK pose 6 repères, Annuler les retire.
2. Schémas : sélectionner la poutre, outil « Symétrie », cliquer deux points d'un axe horizontal sous la pièce : aujourd'hui rien ne bouge (AUD-5-1) ; après correction la pièce passe de l'autre côté.
3. Plan de position : cliquer Fluchttreppe, « Nouveau », annuler le choix du fond, « Supprimer » : la question nomme « Fluchttreppe » (AUD-5-3) — répondre **Non**. Même essai dans Connecteurs avec « Nouveau ».
4. Schémas : outil « Cadrage », glisser un rectangle sur le dessin : le cadre pointillé et le voile apparaissent ; « Tout le dessin » l'ôte.
5. Glisser à la souris une entrée de la liste d'un éditeur dans un dossier, puis vers « Archives », puis hors d'« Archives » : l'entrée suit, la question d'archivage apparaît, la restauration la remet.
6. Survoler les boîtes de « Connecteurs » (une seule s'éclaire, sa pièce s'allume sur le schéma à droite) et une ligne des listes de « Schémas » (l'entrée s'éclaire sur le dessin).
7. Molette sur les trois canevas : le zoom se fait autour du pointeur ; bouton du milieu : la vue se déplace ; sur Plan de position, zoomer fort sur Pavillon : le trait de l'architecte reste net après l'arrêt.
8. Plan de position : glisser le numéro d'une colonne loin d'elle : un trait de rappel apparaît ; « Remettre à sa place » dans le panneau le ramène.
9. Charges : taper « s_k » dans la recherche puis cliquer le petit × : la recherche se vide et les lignes reviennent.
10. « Exporter PDF » avec « Uniforme 2 » et « Français » cochés : la boîte d'avertissements de l'export s'affiche (AUD-5-10), OK, puis le PDF s'ouvre en français, niveau 2 partout, et `000-Archives/` reçoit une archive.

## Contrôles qui pourraient devenir des tests

- Les six tests ci-dessous (AUD-5-1 à AUD-5-6).
- La compilation de **tous** les appels copiés de l'onglet Charges (1 036, 55 s en 6 processus parallèles avec lots de 40) : garde que `var_commands`/`instance_commands`/`domain_commands` restent compilables après un changement de signature.
- Le pilotage de « Exporter PDF » par une sous-classe de `QProcess` qui enregistre les arguments sans lancer Typst (le test existant lit `pdf_input_args()` mais pas l'argument réellement passé à `process.start`).
- Les outils des canevas par `QTest.mouseClick` sur le viewport (chaque outil de Modèles statiques produit une entrée valide), qui couvrent le vrai chemin souris que `place()` contourne.
- Un harnais commun de bouchons pour les tests Qt : `QMenu`/`QDialog` sous-classés par module, puisque `QMenu.exec = …` sur la classe n'a aucun effet (le test bloque sans rien dire).

## Tests de non-régression proposés (code complet)

Chaque test ci-dessous a été exécuté contre le `tests/` du bac à sable (`p5/proposed_tests.py`, jamais l'arbre réel). Les imports supposent l'emplacement indiqué (fichier existant : `conftest`, `ROOT`, `Skip`, `model` y sont déjà importés ; voir l'en-tête de chaque fichier).

### AUD-5-1 — `test_a_mirror_moves_a_point_to_the_other_side_of_its_axis` → `tests/test_schema_edit.py`

import math

```python
def test_a_mirror_moves_a_point_to_the_other_side_of_its_axis():
    """`reflection()` returned the point itself (audit 260916, AUD-5-1): «Symétrie» folded the construction lines' angles and flipped the dimensions' sides while leaving every point where it was -- and mirroring twice, the one check it had, cannot tell a mirror from the identity."""
    from domains import schema as model

    def same(p, q):
        return all(math.isclose(a, b, abs_tol=1e-9) for a, b in zip(p, q))

    place, _bearing, _flips = model.reflection((0, 600), (100, 600))
    assert same(place(0, 0), (0, 1200)), place(0, 0)
    place, bearing, _flips = model.reflection((0, 0), (0, 100))
    assert same(place(30, 5), (-30, 5)), place(30, 5)
    place, _bearing, _flips = model.reflection((0, 0), (100, 100))
    assert same(place(10, 0), (0, 10)), place(10, 0)
    source = model.new_source("D99")
    source["elements"] = [{"id": "E1", "kind": "linear", "position": "T001", "view": "h", "h": 40, "points": [[0, 0], [100, 0]]}]
    model.modify(source, ["E1"], model.reflection((0, 50), (100, 50)))
    assert [list(map(float, p)) for p in source["elements"][0]["points"]] == [[0.0, 100.0], [100.0, 100.0]], source["elements"][0]["points"]
```

### AUD-5-2 — `test_grille_places_valid_markers_whatever_tool_is_in_force` → `tests/test_schema_tab.py`

(uses _tab_75 of the same file: replace `t._tab_75()` by `_tab_75()` and drop `import test_schema_tab as t`)

```python
def test_grille_places_valid_markers_whatever_tool_is_in_force():
    """«Grille…» raised `KeyError: 'kind'` with «Sélection» in force -- the tool the tab opens with -- or any tool without a kind, and wrote markers of kind 'point' or 'horizontal' with an aid or a dimension tool, which `check_source` then refuses (audit 260916, AUD-5-2). The grid's kind is the fastener tool in force, else a Stabdübel."""
    import test_schema_tab as t
    from domains import schema as model
    tab = t._tab_75()
    import schema_tab
    original = schema_tab.GridDialog.exec
    schema_tab.GridDialog.exec = lambda self: 1          # accepted, off-screen: a modal never comes back
    try:
        for tool, kind in (("select", "Stabdübel"), ("linear", "Stabdübel"), ("aid-point", "Stabdübel"),
                           ("dimension-horizontal", "Stabdübel"), ("connector:Nagel", "Nagel")):
            tab.choose_tool(tool)
            tab.place_grid()
            markers = tab.canvas.source.get("connectors", [])
            assert len(markers) == 6, f"{tool}: {len(markers)} markers, the default grid is 3 x 2"
            assert {m["kind"] for m in markers} == {kind}, f"{tool}: {sorted({m['kind'] for m in markers})}"
            model.check_source(tab.canvas.source, "D99.json")
    finally:
        schema_tab.GridDialog.exec = original
```

### AUD-5-3 — `test_supprimer_on_an_unsaved_draft_archives_nothing` → `tests/test_editor_buttons.py`

(uses FOLDERS and EDITORS of the same file: replace `eb.` by nothing and drop `import test_editor_buttons as eb`; needs `import shutil`)

```python
def test_supprimer_on_an_unsaved_draft_archives_nothing():
    """«Supprimer» after «Nouveau» or «Dupliquer», before «Enregistrer», archived the SAVED entry still highlighted in the list -- Fluchttreppe in «Plan de position», VU-SD-10 in «Connecteurs» -- and left the draft on the form (audit 260916, AUD-5-3). The list keeps its selection when a draft is opened, and `source_archive.Actions.delete` read the list's selection before the form's."""
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    tools = str(ROOT / "calc" / "tools")
    if tools not in sys.path:
        sys.path.insert(0, tools)
    try:
        from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox
    except ImportError as exc:
        raise Skip(f"PySide6 is not installed ({exc})")
    import importlib
    import test_editor_buttons as eb
    modules = {name: importlib.import_module(name) for name in eb.FOLDERS}
    copy = conftest.tmpdir("unsaved_delete")
    for folder in {f for spec in eb.FOLDERS.values() for f in spec.values()}:
        shutil.copytree(ROOT / folder, copy / folder) if (ROOT / folder).exists() else (copy / folder).mkdir()
    saved = {}
    for name, spec in eb.FOLDERS.items():
        for constant, folder in spec.items():
            saved[(name, constant)] = getattr(modules[name], constant)
            setattr(modules[name], constant, copy / folder)
    listers = ((modules["plan_tab"].list_plans, (copy / "plans",)), (modules["catalog_gui"].list_connections, (copy / "connections",)))
    saved_defaults = [(fn, fn.__defaults__) for fn, _v in listers]
    for fn, value in listers:
        fn.__defaults__ = value
    stubs = {
        (QMessageBox, "question"): staticmethod(lambda *a, **k: QMessageBox.StandardButton.Yes if len(a) < 4 else QMessageBox.StandardButton.Discard),
        (QMessageBox, "warning"): staticmethod(lambda *a, **k: QMessageBox.StandardButton.Ok),
        (QFileDialog, "getOpenFileName"): staticmethod(lambda *a, **k: ("", "")),    # «Nouveau» plan: no background chosen
    }
    originals = {k: k[0].__dict__[k[1]] for k in stubs}
    for (owner, attr), stub in stubs.items():
        setattr(owner, attr, stub)
    wrong = []
    try:
        app = QApplication.instance() or QApplication([])
        window = modules["catalog_gui"].Catalog()
        for tab in window.tabs:
            if type(tab).__name__ not in eb.EDITORS:
                continue
            folder = {"PlanTab": "plans", "StaticsTab": "statics", "SchemaTab": "details", "ConnectorsTab": "connectors", "PolarTab": "connections"}[type(tab).__name__]
            for verb in ("new", "duplicate"):
                tab.dirty = False
                if hasattr(tab, "load_first"):
                    tab.load_first()
                else:
                    tab.reload_list()
                    if not tab.ids:
                        wrong.append(f"{type(tab).__name__} before {verb}: no saved entry left to open")
                        break
                    tab.load(tab.ids[0])
                    tab.reload_list(tab.ids[0])
                app.processEvents()
                before = sorted(p.name for p in (copy / folder).glob("*.json"))
                getattr(tab, verb)()
                app.processEvents()
                tab.delete()
                app.processEvents()
                after = sorted(p.name for p in (copy / folder).glob("*.json"))
                if after != before:
                    wrong.append(f"{type(tab).__name__} after {verb}: {sorted(set(before) - set(after))} archived")
                tab.dirty = False
        window.close()
    finally:
        for (owner, attr), original in originals.items():
            setattr(owner, attr, original)
        for (name, constant), value in saved.items():
            setattr(modules[name], constant, value)
        for fn, value in saved_defaults:
            fn.__defaults__ = value
    assert not wrong, "«Supprimer» on an unsaved draft archived a saved entry:\n  " + "\n  ".join(wrong)
```

### AUD-5-4 — `test_a_refused_ajouter_leaves_no_undo_step_and_no_dot` → nouveau fichier `tests/test_statics_tab.py` (en-tête : `import os`, `import sys`, `from conftest import ROOT, Skip`)



```python
def test_a_refused_ajouter_leaves_no_undo_step_and_no_dot():
    """«Ajouter» under «Barres», «Charges ponctuelles», «Charges linéaires» or «Cotations» of a model with nothing to hang it on added nothing, and still pushed a step of «Annuler» and marked the model modified -- with no word said (audit 260916, AUD-5-4). A refusal leaves no step (CLAUDE.md section 13, v0.73's rule)."""
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    tools = str(ROOT / "calc" / "tools")
    if tools not in sys.path:
        sys.path.insert(0, tools)
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError as exc:
        raise Skip(f"PySide6 is not installed ({exc})")
    QApplication.instance() or QApplication([])
    import catalog_gui
    window = catalog_gui.Catalog()
    tab = next(t for t in window.tabs if type(t).__name__ == "StaticsTab")
    from domains import statics as model
    tab.open_source(model.new_source("S99"), None, False)
    for collection in ("members", "point_loads", "line_loads", "dimensions"):
        steps = len(tab.undo_stack)
        tab.add_row(collection)
        assert not tab.source.get(collection), collection
        assert len(tab.undo_stack) == steps, f"«Ajouter» {collection} refused and still took {len(tab.undo_stack) - steps} step(s)"
        assert not tab.dirty, f"«Ajouter» {collection} refused and marked the model modified"
    window.close()
```

### AUD-5-5 / AUD-5-7 — `test_the_calls_the_commands_tab_copies_compile` → `tests/test_commands.py`

(uses PUBLIC and ref of the same file: replace `tc.PUBLIC` by `PUBLIC`, drop the two imports)

```python
def test_the_calls_the_commands_tab_copies_compile():
    """Every «Copier» of the commands tab, compiled as pasted, one document each (CLAUDE.md section 10sexies: «a copied call names a sheet, a plan or a connection that exists and compiles as pasted»). Five read the report's language and need `context`, which their calls did not carry (audit 260916, AUD-5-5). show-check has nothing to name (section 14); var-unit, eq, val and verify name variables a report declares first (AUD-5-6, the engineer's decision)."""
    if not conftest.have_typst():
        raise Skip("typst is not on PATH")
    import subprocess
    import test_commands as tc
    import build_reference as ref
    samples = ref.sample_arguments(ROOT / "data")
    exempt = {"show-check", "var-unit", "eq", "val", "verify"}
    probe = conftest.tmpdir("copied_calls")
    root = ROOT.parent
    prefix = "/" + probe.relative_to(root).as_posix()
    failures = []
    for record in tc.PUBLIC:
        if record["name"] in exempt:
            continue
        for kind, call in (("complete", ref.call_complete(record, samples)), ("minimal", ref.call_minimal(record, samples))):
            doc = probe / f"{record['name']}-{kind}.typ"
            doc.write_text('#import "/commands.typ": *\n' + call + "\n", encoding="utf-8")
            r = subprocess.run(["typst", "compile", "--root", str(root), str(doc), str(doc.with_suffix(".pdf"))],
                               capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300)
            if r.returncode != 0:
                failures.append(f"{record['name']} ({kind}): {call!r} -- {r.stderr.strip().splitlines()[0] if r.stderr.strip() else r.returncode}")
    assert not failures, "copied calls that do not compile:\n  " + "\n  ".join(failures)
```

### AUD-5-6 — `test_a_disabled_button_says_why` → `tests/test_catalog.py`



```python
def test_a_disabled_button_says_why():
    """A button shown disabled with no tooltip cannot be told from a broken one: every disabled element says why (v0.47's rule, prompt-audit phase 5). «Calibrer…», «Longueurs des murs», «Annuler les modifications» (plans, polar moments) and «Ouvrir le classeur» said nothing (audit 260916, AUD-5-6)."""
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    tools = str(ROOT / "calc" / "tools")
    if tools not in sys.path:
        sys.path.insert(0, tools)
    try:
        from PySide6.QtWidgets import QAbstractButton, QApplication, QTabBar
    except ImportError as exc:
        raise Skip(f"PySide6 is not installed ({exc})")
    app = QApplication.instance() or QApplication([])
    import catalog_gui
    window = catalog_gui.Catalog()
    window.show()
    bare = set()
    for tab in window.tabs:
        window.tab_widget.setCurrentWidget(tab)
        for opened in (False, True):
            if opened and hasattr(tab, "load_first"):
                tab.dirty = False
                tab.load_first()
            app.processEvents()
            for button in tab.findChildren(QAbstractButton):
                if isinstance(button.parent(), QTabBar) or not button.isVisibleTo(tab) or button.isEnabled():
                    continue
                if not button.toolTip():
                    bare.add(f"{type(tab).__name__}: {button.text() or button.objectName()}")
        tab.dirty = False
    window.close()
    assert not bare, "disabled with nothing to say why: " + "; ".join(sorted(bare))
```

## Corrections proposées (diff sur le commit 997570db, validé dans le bac à sable)

⚠️ `build_reference.py`, `schema_canvas.py` et `statics_tab.py` sont en CRLF dans l'arbre : conserver les fins de ligne. `calc/domains/schema.py` a déjà été modifié par la phase 9 dans l'arbre réel ; la ligne visée par AUD-5-1 n'en fait pas partie.

```diff
--- a/000-TypstRapport/000-Python/calc/domains/schema.py
+++ b/000-TypstRapport/000-Python/calc/domains/schema.py
@@ -1329,7 +1329,7 @@
         dx, dz = x - ax, z - az
         along = dx * ux + dz * uz
         across = dx * uz - dz * ux          # the signed distance to the axis
-        return (ax + along * ux + across * uz, az + along * uz - across * ux)
+        return (ax + along * ux - across * uz, az + along * uz + across * ux)
 
     # A reflection reverses orientation, so a signed offset changes side and a direction is
     # folded about the axis rather than turned by a constant.

--- a/000-TypstRapport/000-Python/calc/tools/schema_canvas.py
+++ b/000-TypstRapport/000-Python/calc/tools/schema_canvas.py
@@ -801,7 +801,10 @@
         so replacing them renumbers what those calculations point at. That is the same exposure as deleting
         a marker by hand, and it is reported the same way -- by the export, as a warning naming the ids.
         """
-        kind = kind or TOOLS[self.tool]["kind"] if self.tool in TOOLS else model.CONNECTOR_KINDS[0]
+        # the fastener tool in force, else a Stabdübel -- never the kind of an aid or a dimension tool, and no KeyError for a tool without one (audit 260916)
+        if kind not in model.CONNECTOR_KINDS:
+            tool_kind = TOOLS.get(self.tool, {}).get("kind")
+            kind = tool_kind if tool_kind in model.CONNECTOR_KINDS else "Stabdübel"
         self.begin_change()
         if replace:
             for marker in list(self.source.get("connectors", [])):

--- a/000-TypstRapport/000-Python/calc/tools/source_archive.py
+++ b/000-TypstRapport/000-Python/calc/tools/source_archive.py
@@ -168,6 +168,8 @@
         if keys:
             self.purge(keys)
             return True
+        if getattr(self.tab, "current_id", None) is None and getattr(self.tab, "dirty", False):
+            return False    # the form holds a draft never saved: «Supprimer» discards it, never a saved entry still highlighted in the list (audit 260916)
         present = {p.stem for p in Path(self.source_dir()).glob("*.json")}
         ids = [i for i in self.tab.list.selected_ids() if i in present]
         current = getattr(self.tab, "current_id", None)

--- a/000-TypstRapport/000-Python/calc/tools/connectors_tab.py
+++ b/000-TypstRapport/000-Python/calc/tools/connectors_tab.py
@@ -1939,8 +1939,16 @@
             self.new()
 
     def delete(self):
-        """«Supprimer»: what is selected goes to «Archives», its ID removed (source_archive.py, v0.77) -- or, an archived entry selected, is deleted for good."""
-        self.archive.delete()
+        """«Supprimer»: what is selected goes to «Archives», its ID removed (source_archive.py, v0.77) -- or, an archived entry selected, is deleted for good. A connector never saved is simply discarded, as in the other editor tabs."""
+        if self.archive.delete():
+            return
+        self.dirty = False
+        self.reload_list()
+        if self.ids:
+            self.load(self.ids[0])
+            self.reload_list(self.ids[0])
+        else:
+            self.new()
 
     def _after_archive(self):
         """The connector the form showed was archived: a new one opens, as deleting always did here."""

--- a/000-TypstRapport/000-Python/calc/tools/statics_tab.py
+++ b/000-TypstRapport/000-Python/calc/tools/statics_tab.py
@@ -1529,13 +1529,18 @@
         self.loading = False
 
     def edit(self, apply):
-        """One change to the model: pushed onto the history, applied, redrawn."""
+        """One change to the model: pushed onto the history, applied, redrawn. A change that changes nothing -- «Ajouter» with nothing to hang the entry on -- leaves no step and marks nothing (audit 260916). True when something changed."""
         if self.loading:
-            return
+            return False
+        before = copy.deepcopy(self.source)
         self.push_history()
         apply()
+        if self.source == before:
+            self.undo_stack.pop()
+            return False
         self.canvas.invalidate()
         self.on_changed()
+        return True
 
     def on_identity(self):
         """Nom, Description or ID left after typing: one step of «Annuler». The description is the source's `label`, which is what the report's caption prints."""

--- a/000-TypstRapport/000-Python/calc/tools/build_reference.py
+++ b/000-TypstRapport/000-Python/calc/tools/build_reference.py
@@ -545,6 +545,12 @@
     "uniform-level": ("#uniform-level.update(2)",) * 2,
     "number-digits": ("#number-digits.update(3)",) * 2,
     "report-language": ("#context report-language.get()",) * 2,
+    # read the report's language, so only inside `context` (audit 260916)
+    "report-lang": ("#context report-lang()",) * 2,
+    "t-str": ('#context t-str("governing")',) * 2,
+    "tl-str": ('#context tl-str("Bezugshöhe")',) * 2,
+    "t-label": ('#context t-label("governing")',) * 2,
+    "t-pattern": ('#context t-pattern("connection.caption")',) * 2,
 }
 
 # The positional arguments of the three commands whose positional *tail* is variadic. Typst has no optional positional parameter, so `var`, `eq` and `val` take theirs through a `..rest` that no signature can describe -- the doc block names its slots instead.

```

## Fichiers produits

- `AUDIT/p5/*.py` : scripts ; `AUDIT/p5/out/inventory.json` et `misc.json` (inventaire complet), `calls.json` (1 245 appels et où ils ont été copiés), `compile-calls.json`, `top.json`/`top.log`, `editors*.log`, `canvas*.log`, `confirm.json`, `forms.json`, `unsaved_delete.json`, `proposed.diff`.
- Bac à sable : `AUDIT/projet-phase5/Statischer Rapport.pdf` (dernier Exporter PDF, Uniforme 3 + Deutsch), `000-TypstRapport/000-Archives/` (7 archives), `p5probe/` (documents de compilation). Les six fichiers corrigés du bac à sable ont leurs originaux dans `AUDIT/p5/originals/`.
