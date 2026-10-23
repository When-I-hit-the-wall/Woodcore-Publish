# Spec 2026-10-22-onglet-neige-type — the review's risks and what the spec made of them

> §13.3 of the spec `docs/requirements/completed/2026-10-22-onglet-neige-type.md` (issue #94): the risks W01–W16, D01–D10 and F01–F16 of its three architecture reviews and the answer to each, moved verbatim on 2026-10-22 so that the spec stays under 100 KB.

### 13.3 Risques et ce que la spec en fait

**Revue A — la fenêtre**

| Risque | Gravité | Réponse |
|---|---|---|
| W01 la neige mêlée à la base (`load_tab.py:35,39,114-130,552-555`) | bloquant | `SnowTab` sort dans `snow_tab.py` + `snow_tab_words.py` (préfixe `sn_`), la base dans des modules neufs ; test `grep` snow/neige/toit sur les modules de la base (plan 6, 7). |
| W02 une erreur ne nomme pas son champ (`validation.py:42`) | bloquant | `problems(src)` extrait de `check_fields` rend `Message(code, field, "error", params)` ; `check_fields` lève sur le premier, phrase inchangée (plan 2). |
| W03 `layout_store` ne garde que des fractions | important | `get_state/put_state` (JSON) ; l'état des modules est **par poste**, pas par signature d'écrans (D-26) ; `Store` injectable dans les tests. |
| W04 épingles non persistées | important | Les épingles sont de session, gardées dans `view_state()` à travers une reconstruction ; l'ordre retenu ne nomme que les modules fixes, un id inconnu est ignoré (D-27). |
| W05 champs liés à une variable oubliés | important | `Field.linkable` lu de `LINKABLE` ; `calc_fields` construit un `LinkableSpin` ; `draft_links`/`fill_links` restent dans `LoadTab`. |
| W06 écrivains nouveaux hors garde lecture seule | important | Méthodes `write_*` ajoutées à `tab_guard.WRITERS` ; l'épinglage et l'état des modules ne sont pas gardés (réglages du poste). |
| W07 collision silencieuse de clés `STRINGS` | important | Test dans `test_i18n.py` : clés disjointes entre modules fusionnés. |
| W08 le SVG dépend de la langue | important | Réglé par Q-007 : le SVG du rapport n'a pas de mots ; il est déterministe, mêmes entrées → mêmes octets. |
| W09 règle 15 : la fenêtre ne montre pas de Typst | important | L'ingénieur demande la ligne écrite et le fichier entier (T61) : décision D-28 qui précise la règle 15 (l'Affichage montre, en lecture seule, la ligne et le fichier qu'il écrit, comme il montre déjà la commande à copier). |
| W10 le lecteur ne doit pas être un `PdfPane` | important | `FramedPdfView(ZoomablePdfView)` + `page_rect_in_view` pure et testée, dans `norm_reader.py` ; `pdf_pane.py` non modifié. |
| W11 bulle flottante sans fin de vie | important | Cachée sur `hideEvent` de l'onglet, `WindowDeactivate`, changement de vue ; garde `RuntimeError` ; sa propre `QScrollArea`. |
| W12 `load_tab.py` à 1130 lignes | mineur | Réglé par W01. |
| W13 `next_free_id` importé de `member_check_tab` | mineur | Pris de `source_editor` au passage. |
| W14 extraits du vent sur ~50 JSON | mineur | `calc/norms/excerpts.py` prend une liste de fichiers. |
| W15 quatre genres de champs ne suffisent pas | mineur | `select` et `custom` dans le contrat dès maintenant (seul `select` est construit ici, la neige n'en a pas besoin : le test du domaine inventé le couvre). |
| W16 couleurs du dessin | mineur | Test : le SVG du rapport n'a que `#000`/`#fff`/`none`. |

**Revue B — le domaine et les normes**

| Risque | Gravité | Réponse |
|---|---|---|
| D01 ~170 Mo de PDF dans le dépôt, installateur ~230 Mo public, `test_no_third_party_name` lit tous les octets | important | Accepté par l'ingénieur (D-22, D-24), coût écrit dans la décision ; dossier racine `norm-library/` (pas sous `calc/`), `*.pdf binary` déjà dans `.gitattributes`, fichiers LFS de `norms` copiés en contenu réel, aucun > 50 Mo (le plus gros : 14 Mo) ; `woodcore.spec` `tree("norm-library")` et son test ; `test_no_third_party_name` saute les `*.pdf` avec sa raison. |
| D02 mots dans le SVG du rapport | bloquant | Q-007 : pas de mots dans le SVG ; `render(src, …, words=None)` donne le rapport, `words` (glossaire) l'onglet ; les mots « Modèle de charge 1 et 2 » dans la légende Typst. |
| D03 trois décisions « le rapport n'imprime pas de dessin de la neige » ; pas de genre « snow » dans `FIGURE_KINDS` | important | Décisions marquées *superseded* dans `decisions.md` ; `FIGURE_KINDS["snow-load"]`, `structure_folders`, `registry.write_files` par genre ; `test_figure_golden.py` : nouveaux hash et `CHANGES` ; jetons `snow`/`snow-edge` de `lib/figure-palette.json` retirés s'ils ne servent plus. |
| D04 messages : API du vent, deux tables de mots | important | Type commun `Message` dans `contracts.py` ; `messages(src)` dans neige et vent (`field=None` pour le vent) ; `warnings(src)` reste un alias mince. |
| D05 schéma 1.3 : planchers, L/B | important | L et B n'appellent pas 1.3 (déjà `number|null` en 1.0). 1.3 = C_e libre seulement. `stamp_version` : le plus haut plancher exigé ; contrôles `links ≥ 1.1`, `height_step ≥ 1.2` sur des tuples. REQ-021 corrigé. |
| D06 « exporté à l'octet près » contradictoire | important | Le critère vaut pour le **fichier source** relu et réécrit ; l'export de SN-01 change, dit au CHANGELOG. REQ-021 corrigé. |
| D07 texte copié hors glossaire ; `_source` nomme un dossier de poste | important | D-21 le dit : le texte d'une norme est une donnée de norme, pas un mot de fenêtre ; test texte↔PDF normalisé (espaces, césures, μ et indices) ; `_source` corrigé en `SIA261-2020-FR.pdf`. |
| D08 phrase des 2000 m à trois endroits | mineur | Les trois (`load_tab` → `snow_tab_words`, `woodcore_gui_words` note d'export, `notes_of`) disent la même chose, sans « calculé quand même » ; seuils et clauses lus du JSON. |
| D09 `FIELD_NORM` | mineur | Un champ cite des ids d'extraits ; le var du rapport et le champ lisent la même constante `norm_ref` ; test d'existence. |
| D10 défauts du français | mineur | Par le glossaire (`docs/typst/language.md` §4bis), pas de table dans `snow_source.py`. |

**Revue C — le fichier du cas et l'Affichage**

| Risque | Gravité | Réponse |
|---|---|---|
| F01 « Régénérer » garde l'ancien `#var s_k` comme ligne de l'ingénieur (`_own_line`, `unfold.py:747-757`) | bloquant | L'alias var↔eq ne vaut que si l'ancienne ligne n'est pas une ligne que Woodcore a écrite (absente de la base, ou digest différent). Test dédié. |
| F02 D-17 « ôter de `line_digests` » inopérant (`_line_text`, `_forget`) | bloquant | Une seule fonction `comparable_text(item)` aux trois endroits ; `_replace_line` et la branche « non changée » de `regenerate` fusionnent : options fraîches, sans leurs arguments d'affichage, plus ceux du fichier. « Reprendre » ne rend pas les arguments d'affichage. |
| F03 le jeu « affichage » ne peut pas être la liste du panneau | bloquant | Jeu gardé = `fine-keys[commande]` + `style` + `role` + `level`, lu d'un JSON `lib/display-vocabulary.json` que Typst lit aussi (`fine-values`/`fine-keys` y déménagent). `equation`, `unit`, `as-unit`, `label`, `descr` restent réglables mais rendent la ligne « locale » (gardée, jamais gelée en silence). D-17 réécrit. |
| F04 anciennes empreintes avec `level=0` (membres, moments polaires) | important | Normalisation en lecture (si `own`/`seen` égale le digest de la ligne entière, il est remplacé par celui de la ligne comparable). |
| F05 la forme ne change pas toute seule ; changements communs aux charges | important | Suffixe de forme propre à `snow-load` ; `GENERATOR_VERSION` inchangé ; corniche ôtée de l'export neige (pas une clé codée dans `_calc_body`) ; les traductions de `norm-section`/symboles touchent aussi Vent et Poids propre : leurs lignes passent en « data » et sont rafraîchies sans question, dit au CHANGELOG. Coût : tous les cas neige disent « forme changée » jusqu'au « Régénérer » (l'export ne s'arrête pas). |
| F06 s_k n'est `#eq` que si sa formule s'évalue | important | Formule `max(...)` qui s'imprime comme (10) et s'évalue, à toute altitude (test bas et haut). |
| F07 chemin du SVG hors convention | important | `Variable-loads/Snow/Exports/Figures/<id>-fig3.svg` via `FIGURE_KINDS["snow-load"]` ; une `figure_line(file, width, caption, label)` factorisée (trois écrivains aujourd'hui). |
| F08 le label de la figure est son identité | important | La ligne de la figure est retrouvée par son fichier d'image (`figure:<fichier>`) et non plus par son label : le label devient réglable sans détacher la ligne (T65) (D-29). |
| F09 `figure: false` dans la source | important | Q-008 : masquer la figure **commente sa ligne** dans le `.typ` (`// #figure(…)`) ; l'état de la ligne est « masquée », ni « missing » ni « own » ; l'export ne la décommente pas ; « Afficher » la décommente (D-23 remplacée). Pas de champ dans la source. |
| F10 aucun moyen Typst de montrer le masqué en pâle | important | Un état « montrer le masqué » dans `lib/` (patron `uniform-level`), posé par l'en-tête de l'aperçu : une ligne qui ne s'imprimerait pas s'imprime au préréglage 3, pâle, marquée « masquée » ; `///`, deux exemples, traductions. La figure commentée est composée par l'aperçu (`Entry.snippet_fn`). Aperçu à vraie hauteur de page (notes en bas), `keep_place=True`. |
| F11 la colonne de droite n'est pas `DisplayView.right` | important | Composant `calc/tools/domain_file_display.py` ; API sans Qt `unfold.elements(...)`, `unfold.set_display(...)` ; `display_preset`/`merged_options` remontés dans `display_options.py` ; `FormulaTab.write_display` et le nouvel écrivain appellent la même fonction. |
| F12 `#domain(level:)` non modélisé | important | `Domain.level` lu par `parse_domain`, en-tête écrit par `patched` (un `norm:` écrit à la main reste). |
| F13 le sens des niveaux et l'« auto » du domaine | important | Niveaux = préréglages d'affichage (`display-presets.json`) ; le domaine a quatre états : auto (suit le rapport, montré en pointillé), 1, 2, 3 (D-30) ; docs `report-engine.md` et `line-levels.json` corrigées. |
| F14 `display_options` | important | Les arguments fins deviennent des `Option(view="display")` ; `Option.views` en tuple ; panneau propre pour la figure (`width`, `caption`, `label`, afficher), déclaré comme `OWN_PANELS`. |
| F15 docstrings `show-calc` | mineur | Mis à jour ; le test « aucune référence à `show-calc` » exclut `LEGACY_STUBS` en le disant. |
| F16 ARCH-012 en pratique | mineur | Test sur le poids propre (figure et lignes) et un moment polaire. |
