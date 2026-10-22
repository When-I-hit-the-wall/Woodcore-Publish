---
id: 2026-10-22-image-polar-moment
titre: Les flèches de forces sur la figure d'un moment polaire — #image-polar-moment
status: completed
cree: 2026-10-22
mis_a_jour: 2026-10-22
source: message écrit (session du 2026-10-22, après la refonte des commandes Typst) et réponse à une question
docs: [docs/domain/connections.md, docs/typst/api-conventions.md, docs/typst/formulas.md, docs/domain/detail-schemas.md]
---

# Les flèches de forces sur la figure d'un moment polaire — Spécification

## 1. Objectif

La figure d'un moment polaire imprimait, jusqu'à la refonte des commandes Typst (spec `docs/requirements/completed/2026-10-21-commandes-typst-refonte.md`, lot 19), les flèches des efforts dans chaque moyen d'assemblage — N/n, V/n, la part de M et la résultante F_i — dessinées par Typst à partir des N, V, M donnés à `#show-polar-moment`. Cette commande a été retirée et le moment polaire est désormais un fichier écrit par Woodcore (`Connections/<id>.typ`), dont la figure est fixe : les flèches ont disparu. L'ingénieur veut les retrouver, par une nouvelle commande image, `#image-polar-moment`, que Woodcore écrit dans le fichier après les lignes des forces, de sorte que les flèches suivent les valeurs que l'ingénieur y met.

## 2. Source

> **T1** — « La flèche de force sur les moments polaires, pourquoi est-ce que ça ne fonctionne plus? Ça a toujours fonctionné avant. Donc je vois pas pourquoi ça ne fonctionnerait plus, il faut bien m'expliquer. »
>
> **T2** — Réponse à la question « Flèches de forces sur la figure d'un moment polaire : que fait-on ? » (2026-10-22) : « Nouvelle #image-polar-moment (Recommandé) », l'option disant : « Une sixième commande image, #figure(image-polar-moment("VU-MP-1", N: "N", V: "V", M: "M")), écrite par Woodcore dans le fichier après les lignes des forces : les flèches suivent les valeurs que tu y mets. Ça reprend l'ancien dessin. Nouvelle commande = spec (big-feature) avant implémentation. »

## 3. Exigences fonctionnelles

### REQ-001 — Une commande `#image-polar-moment`
- **Exigence** : `lib/` doit offrir `#image-polar-moment(connection, N:, V:, M:, …)`, qui rend la figure du moment polaire exportée par Woodcore avec, dessinées par-dessus, les flèches des efforts dans chaque moyen d'assemblage : la résultante F_i (jaune, bord ocre, étiquetée F1, F2, …), la part de M (verte), N/n (bleue) et V/n (rouge), toutes à une même échelle — le dessin de `#show-polar-moment` avant sa retraite, repris tel quel (`svg-arrow`, `fastener-shares`, `fastener-arrows`, `share-note`, `polar-distribution`, `lib/calc-engine-connections.typ` à `8310c82^`). Elle rend le dessin seul, à placer dans un `#figure(…, kind: image, caption: […]) <label>` natif, comme les cinq autres `image-*`.
- **Source** : T1, T2
- **Priorité** : doit
- **Critère d'acceptation** : un test compile `#figure(image-polar-moment("VU-MP-1", N: 7.5, V: 25, M: 6.6), kind: image, caption: [X])` sur le projet exemple, et le SVG embarqué contient les flèches (éléments `<line>`/`<polygon>` aux couleurs de la palette `yellow`, `green`, `blue`, `red`) et les étiquettes `F1`… ; avec N = V = M = 0, aucune flèche.

### REQ-002 — Les forces données par nombre ou par le nom d'une variable
- **Exigence** : `N:`, `V:` et `M:` doivent accepter un nombre (kN, kN, kNm) ou le nom d'une variable déclarée plus haut (`N: "N"`), lu dans le registre — dans le domaine où l'appel se trouve d'abord — avec l'unité attendue ; un nom inconnu ou une unité autre arrête la compilation en le disant (la règle de `#show-polar-moment`).
- **Source** : T2 (« N: "N", V: "V", M: "M" … les flèches suivent les valeurs que tu y mets »)
- **Priorité** : doit
- **Critère d'acceptation** : un test : dans un `#domain`, `#var("N", 7.5, "kN")` puis `image-polar-moment(id, N: "N", …)` dessine les mêmes flèches que `N: 7.5` ; `N: "nope"` et une variable en N (et non kN) sont refusés avec un message qui nomme l'argument.

### REQ-003 — Woodcore écrit la figure fléchée dans le fichier du moment polaire
- **Exigence** : le générateur d'un moment polaire (`calc/domains/unfold.py` `_generate_connection`) doit écrire — à la place de la figure fixe qu'il met aujourd'hui en tête (D-02) —, après les lignes des forces (`#var("N", …)`, `#var("V", …)`, `#var("M", …)`), la figure `#figure(image-polar-moment("<id>", N: "N", V: "V", M: "M"), kind: image, caption: […]) <…>` sur une ligne étiquetée, que la base de régénération suit comme les autres lignes (REQ-008 de la refonte) ; un moment polaire sans bras de levier (pas de `M`) écrit l'appel sans `M:`.
- **Source** : T2
- **Priorité** : doit
- **Critère d'acceptation** : `test_domain_generators` (ou `test_unfold`) : le fichier généré de VU-MP-1 contient l'appel après les lignes des forces et compile ; en remplaçant `0` par `7.5` dans la ligne `N` du fichier, le PDF dessine des flèches bleues.

## 4. Exigences d'interface (fenêtre, rapport, site)

### UI-001 — La légende de la figure dans la langue du rapport
- **Exigence** : la figure garde la légende que la figure exportée porte, et sa dernière ligne (`<!-- note -->`) nomme, avec leur valeur, les parts trop petites pour être lues à l'échelle de la figure (`figure.too_small`), comme avant ; la légende du `#figure` écrite par Woodcore vient du glossaire (`connection.caption`, `connection.figure_caption`).
- **Source** : inféré (T1 : « ça a toujours fonctionné avant »)
- **Langues** : fr / de / en (les mots existent déjà dans `calc/i18n/strings.json`)
- **Critère d'acceptation** : un test : une part plus petite que le seuil est nommée dans la note, en allemand et en français.

## 5. Exigences d'architecture

### ARCH-001 — Un dessin, écrit deux fois et tenu égal
- **Exigence** : le dessin des flèches existe en Python pour la fenêtre (`calc/domains/connection_svg.py` `force_arrows`, `share_note`) et en Typst pour le rapport ; les deux doivent rester élément pour élément identiques, tenus par un test qui compare les deux SVG pour les mêmes forces (le `tests/test_arrows.py` retiré au lot 19, rétabli), et les constantes partagées (épaisseurs, seuils, couleurs) lues de chaque côté.
- **Source** : inféré — principe 1 (une source de vérité), `docs/decisions.md` (« the one place in this project where the same thing is written in two languages »)
- **Critère d'acceptation** : `tests/test_arrows.py` passe : mêmes éléments SVG et même note pour quatre jeux de forces (N, V et M ensemble ; sans moment ; moment seul ; une part trop petite), constantes égales.

### ARCH-002 — Une commande image comme les cinq autres
- **Exigence** : `#image-polar-moment` doit suivre la convention des `image-*` (REQ-013/014 et ARCH-012 de la refonte) : une entrée dans `lib/image-vocabulary.json` (ce qu'elle dessine — `detail-figure`, au moins `"forces"` — et sa légende), son bloc `///` avec deux exemples qui compilent, sa traduction dans `calc/i18n/commands.json`, sa catégorie (`display`), sa règle dans `calc/domains/dependency_graph.py` (`("id", "connection", 0)`), son générateur d'appel (`call_image`/`call_image_figure`).
- **Source** : inféré — principe 14 (toute commande documentée), conventions de la refonte
- **Critère d'acceptation** : `test_commands`, `test_doc_comments`, `test_dependency_graph.test_every_public_command_of_lib_is_classified`, `test_image_figures` passent avec la nouvelle commande.

### ARCH-003 — Un fichier déjà écrit passe par « Régénérer », jamais par une réécriture en place
- **Exigence** : la figure fléchée doit porter une étiquette neuve (`polar-figure`), et la forme d'un moment polaire (`unfold.form_of`) changer, de sorte qu'un fichier écrit avant affiche la ligne rouge « forme » à la tête du domaine, que l'export ne le réécrive pas, et que « Régénérer » retire l'ancienne figure de tête et place la figure fléchée après les forces ; une figure de tête modifiée à la main reste, comme texte de l'ingénieur.
- **Source** : revue (ARCH-RISK-001)
- **Critère d'acceptation** : `test_unfold` : un `VU-MP-1.typ` de l'ancienne forme s'exporte et compile, sa tête dit « forme », `regenerate` donne une seule figure, après les forces, et `reinsert` remet la ligne à sa place.

### ARCH-004 — La commande ne publie rien
- **Exigence** : `#image-polar-moment` ne fait aucun `var-registry.update` : `F_max`, `F_i` restent ceux des `#eq` du fichier.
- **Source** : revue (ARCH-RISK-003)
- **Critère d'acceptation** : un test : après la figure, `F_max` du registre est celui de l'`#eq` (valeurs différentes données à la commande et au fichier).

### ARCH-005 — La répartition recalculée par la commande tenue égale à Python et au fichier
- **Exigence** : `polar-distribution` (Typst), `connection.fastener_forces` (Python) et les `#eq F_i` du fichier doivent donner les mêmes efforts pour les mêmes N, V, M.
- **Source** : revue (ARCH-RISK-004) ; option A, soumise à l'approbation
- **Critère d'acceptation** : un test compile la commande avec N = 7.5, V = 25, M = 6.6, relit les F_i de `polar-distribution` par `typst query` et les compare à `fastener_forces` et aux `#eq` du fichier (1e-6).

## 6. Contraintes

- **CON-001** — Les forces ne sont pas des données de Woodcore : elles restent dans le rapport, écrites par l'ingénieur dans le fichier du moment polaire (décision de la refonte : « the forces are the engineer's to write »). Rien n'est ajouté à la source `connections/<id>.json` ni à `data/connections.json` (pas de version de schéma). Source : inféré (T2).
- **CON-002** — Aucun calcul de SIA ni de répartition n'est fait dans la fenêtre pour le rapport : la répartition est celle que le fichier écrit déjà (`F_x_i`, `F_z_i`, `F_i`) et que `polar-distribution` recalcule pour le dessin, comme avant ; les trois chemins tenus égaux par un test (ARCH-005). Source : principe 2.

## 7. Décisions prises

- **D-01** — Une sixième commande image plutôt que des forces saisies dans l'onglet ou l'abandon des flèches (l'ingénieur, 2026-10-22, T2). Prix : une commande de plus dans `lib/`, et le dessin des flèches de nouveau écrit en deux langues.
- **D-02** — Une seule figure par moment polaire : la figure fixe écrite en tête du fichier est remplacée par la figure fléchée, écrite après les lignes des forces (Q-001).
- **D-03** — `image-polar-moment(connection, N: 0, V: 0, M: 0, width: 100%, detail-figure: auto)` : N, V, M un nombre (kN, kN, kNm) ou le nom d'une variable déclarée plus haut ; `detail-figure` du vocabulaire, `"forces"` par défaut, `()` la figure sans flèches (Q-002).
- **D-04** — Pas de bouton « Copier » dans l'onglet Moment polaire : la figure vient avec le fichier inclus (Q-003). Rien ne change dans `calc/tools/`.

## 8. Hors périmètre

- Saisir N, V, M dans l'onglet « Moment polaire » (option écartée en T2).
- Rétablir `#show-polar-moment` ou son calcul imprimé : le calcul reste celui du fichier écrit (REQ-017 de la refonte).
- Un bouton « Copier » de la figure dans l'onglet Moment polaire (D-04).

## 9. Idées non retenues comme exigences

_(aucune)_

## 10. Questions

### Q-001 — Où va la figure fléchée dans le fichier ?
- **Pourquoi elle compte** : le fichier écrit aujourd'hui la figure fixe en tête ; la figure fléchée ne peut venir qu'après les forces, dont elle lit les valeurs.
- **Options** : A (recommandée) la figure fixe en tête est remplacée par la figure fléchée, écrite après les lignes des forces — une seule figure ; B on garde la figure fixe en tête et on ajoute la figure fléchée après les forces — deux figures.
- **Réponse** : A — une seule figure, après les forces (l'ingénieur, 2026-10-22).

### Q-002 — Ce que prend la commande
- **Pourquoi elle compte** : c'est la surface de la commande (règle : l'ingénieur la conçoit).
- **Options** : A (recommandée) `image-polar-moment(connection, N: 0, V: 0, M: 0, width: 100%, detail-figure: auto)` — N, V, M un nombre ou le nom d'une variable, `detail-figure: "forces"` par défaut (`detail-figure: ()` la figure sans flèches) ; B la même sans `detail-figure` ; C les forces par nom seulement.
- **Réponse** : A (l'ingénieur, 2026-10-22).

### Q-003 — Un bouton « Copier » dans l'onglet Moment polaire ?
- **Pourquoi elle compte** : les autres figures ont un « Copier » qui copie leur `#figure(image-…)`. Ici le fichier l'écrit déjà.
- **Options** : A (recommandée) non : le fichier écrit la figure, la section inclut le fichier ; B oui, un « Copier » de la figure fléchée.
- **Réponse** : A — pas de bouton (l'ingénieur, 2026-10-22).

## 11. Critères d'acceptation

- [x] REQ-001 — `image-polar-moment` dessine les flèches et les étiquettes ; aucune pour N = V = M = 0
- [x] REQ-002 — N, V, M par nombre ou nom de variable ; nom inconnu ou unité autre refusés
- [x] REQ-003 — le fichier généré écrit la figure fléchée après les forces ; elle suit une valeur changée à la main
- [x] UI-001 — note des parts trop petites, dans la langue du rapport
- [x] ARCH-001 — `tests/test_arrows.py` rétabli : Python et Typst dessinent les mêmes éléments
- [x] ARCH-002 — vocabulaire, `///`, exemples, traductions, catégorie, liste sans `level:`, graphe, générateur d'appel
- [x] ARCH-003 — un fichier ancien : ligne rouge « forme », pas de réécriture en place, « Régénérer » donne une seule figure après les forces
- [x] ARCH-004 — rien de publié dans le registre
- [x] ARCH-005 — `polar-distribution` égale `fastener_forces` et les `#eq` du fichier
- [x] Documentation : `docs/domain/connections.md`, `docs/typst/api-conventions.md` §10bis, `CHANGELOG.md`, « Nouveautés » fr/de/en, catalogue des tests (`test_arrows.py`).
- [x] Tests : `test_arrows` (rétabli), `test_domain_generators`, `test_image_figures`, `test_commands`, `test_dependency_graph`, `test_report_golden` (page du moment polaire re-gelée si elle change, raison dans `CHANGES`).

## 12. Traçabilité

| Source | Élément | Statut |
|---|---|---|
| T1 | REQ-001, UI-001 | capturé (l'explication donnée dans la session : la commande retirée dessinait les flèches) |
| T2 | REQ-001, REQ-002, REQ-003, D-01, Q-001, Q-002, Q-003 | capturé ; trois points de surface → questions |
| revue | ARCH-003, ARCH-004, ARCH-005 | ajoutés par la revue d'architecture |

### Points de la source non résolus

_(aucun : Q-001 à Q-003 répondues le 2026-10-22)_

## 13. Revue d'architecture

Revue par `architecture-reviewer` (2026-10-22), lecture du code et de l'ancien dessin (`8310c82^`). **Verdict : APPROUVER AVEC RÉSERVES.**

**Modules concernés.** `lib/calc-engine-connections.typ` (ne garde que les constantes de `verify` ; son en-tête décrit encore le dessin des flèches : c'est là que les helpers reviennent, sans cycle, `image-details` étant visible depuis `drawings`) ; `lib/calc-engine-drawings.typ` (les `image-*`, `image-details`) ; `lib/image-vocabulary.json` ; `lib/calc-engine-core.typ` (`figure-colour`, `svg-number`, `figure-path`, `load-connections`, `var-lookup`, `var-names`) ; `lib/formula.typ` (`#domain` empile son id) ; `calc/domains/connection_svg.py` (`force_arrows`, `share_note`, constantes) ; `calc/domains/connection.py` (`fastener_forces`) ; `calc/domains/unfold.py` (`_generate_connection`, `form_of`, `line_digests`, `status`, `refresh`, `regenerate`, `reinsert`) ; `calc/build_reference_calls.py` (`call_image`) ; `calc/build_reference_lib.py` (`CATEGORIES`, la liste des commandes sans `level:`) ; `calc/domains/dependency_graph.py` ; `calc/i18n/commands.json`.

**Existant à réutiliser.** Le dessin, repris tel quel de `8310c82^` (`svg-arrow` … `share-note`, `polar-distribution`) ; la lecture d'une force par nombre ou par nom, l'ancien `magnitude` (`var-lookup`, `var-names`, `assert` qui nomme l'argument) — pas de troisième helper de lecture ; la forme d'`image-schema` ; `call_image` ; `_label`, `_cell`, `strings.template` côté générateur ; `force_arrows`, `share_note`, `fastener_forces` comme référence du test. Aucun mot nouveau : `figure.too_small`, `connection.caption`, `connection.figure_caption` existent dans les trois langues.

**Risques.**
- **ARCH-RISK-001 (bloquant) — un projet déjà écrit.** La figure de tête d'un fichier existant porte l'étiquette `<…-figure>`. Garder cette étiquette ferait voir à `refresh` une ligne « donnée changée », remplacée **à sa place**, en tête, avant la déclaration de N : le rapport ne compilerait plus (« no variable named N ») sur tout projet déjà exporté. Correction : une **nouvelle étiquette** (`polar-figure`) et un `form_of` de `connection` changé, pour que les fichiers existants passent par la ligne rouge « forme » et « Régénérer », qui retire l'ancienne figure de tête et place la nouvelle après les forces → ARCH-003.
- **ARCH-RISK-002 (important) — N, V, M par nom dans un `#domain`.** `var-lookup` lit le domaine courant puis le document : lu **dans le `context` de la commande**, placé après les `#var`, le N du domaine est trouvé. Refus par `assert` qui nomme l'argument.
- **ARCH-RISK-003 (important) — ne rien publier.** L'ancien `#show-polar-moment` écrivait `F_max`, `F_i`, `beta_j` dans le registre ; le fichier les écrit déjà par ses `#eq`. La commande doit être pure, comme les autres `image-*` → ARCH-004.
- **ARCH-RISK-004 (important) — une troisième écriture de la répartition.** `polar-distribution` (Typst), `fastener_forces` (Python) et les `#eq` du fichier calculent les mêmes F_i ; plus rien ne tient `polar-distribution` à Python depuis le lot 19 (CON-002 citait `test_connection`, qui ne touche pas Typst). Option A : recalculer dans la commande et le tenir égal par un test ; option B : lire les `F_x_i`, `F_z_i` des `#eq` du fichier (la figure devrait venir après eux, et ne marcherait pas avec des nombres) → ARCH-005, choix soumis à l'approbation.
- **ARCH-RISK-005 (important) — Python et Typst dessinent pareil.** `tests/test_arrows.py` rétabli (quatre jeux de forces et un cinquième sans moment, les constantes lues des deux côtés) ; en-têtes de `connection_svg.py` et `docs/domain/connections.md` mis à jour.
- **ARCH-RISK-006 (important) — le vocabulaire.** Entrée complète (`replaces: "show-polar-moment"`, `id: "connection"`, `detail-figure: ["forces"]`, `detail-legend: ["none"]`, `options: ["N","V","M","width"]`) ; `tests/test_image_figures.py` affirme cinq commandes : à changer ; `call_image` laisse un nombre en nombre et un nom en chaîne.
- **ARCH-RISK-007 (important) — enregistrements.** La liste des commandes sans `level:` (`build_reference_lib.py`, sinon `test_command_levels`), `CATEGORIES`, `COMMAND_REFERENCES`, la ligne de `show-polar-moment` dans la table « ce que devient un appel », `///` avec deux exemples, traductions, catalogue des tests.
- **ARCH-RISK-008 (important) — la place dans `lib/`.** Les helpers et la commande dans `calc-engine-connections.typ` ; aucun import dans un corps ; aucun nouveau fichier de `lib/`.
- **ARCH-RISK-009 (important) — pages d'or.** La figure de VU-MP-1 change de place et prend une vraie légende : régénérer `report-golden.json`, raison dans `CHANGES` ; écrire `width: 60%` dans l'appel pour garder sa taille.
- **ARCH-RISK-010 (mineur) — langues.** Le fichier est écrit dans la langue du projet ; la note `figure.too_small` est résolue à la compilation (langue du rapport) : le test UI-001 force la langue.
- **ARCH-RISK-011 (mineur) — place de la ligne.** La figure est du texte étiqueté (suivi par `line_digests`), écrite entre `#var M` et les `#eq N_x` avec une ligne vide avant et après, pour que `reinsert` la remette au bon endroit ; un test de `reinsert`.
- **ARCH-RISK-012 (mineur) — textes périmés.** `connection.py`, `connection_svg.py`, `polar_tab.py` (une docstring), `unfold.py`, l'en-tête de `calc-engine-connections.typ` citent encore `show-polar-moment`.

Aucun risque de schéma : rien n'est ajouté aux sources ni à l'export (CON-001) ; la base de régénération reste valide, seul le `form` d'un moment polaire change.

## 14. Plan d'implémentation

1. **Typst — le dessin et la commande** (REQ-001, REQ-002, UI-001, ARCH-002, ARCH-004, ARCH-008) : dans `lib/calc-engine-connections.typ`, les helpers de `8310c82^` (`svg-arrow`, `share-shown`, `share-head`, `action-width`, `resultant-width`, `moment-parts`, `fastener-shares`, `fastener-arrows`, `share-note`, `polar-distribution`) et `image-polar-moment(connection, N: 0, V: 0, M: 0, width: 100%, detail-figure: auto)` : vérifie `connection` et `calculated`, `image-details`, lit N, V, M dans son `context` (nombre ou nom, unité vérifiée, `assert` qui nomme l'argument), dessine, remplace `<!-- forces -->` et `<!-- note -->` dans le SVG exporté ; aucune écriture au registre ; en-tête du fichier à jour. `///` avec deux exemples (nombres ; `#var` puis noms). Test : `tests/test_image_figures.py`.
2. **Contrats** (ARCH-002) : `lib/image-vocabulary.json` (entrée complète, `_comment`), `calc/build_reference_lib.py` (`CATEGORIES`, liste sans `level:`), `calc/domains/dependency_graph.py` (`("id", "connection", 0)`), `calc/i18n/commands.json` (paragraphes et arguments fr/de/en), `calc/renamed-commands.json` (le remplacement de `show-polar-moment` nomme aussi la nouvelle commande). Tests : `test_commands`, `test_doc_comments`, `test_command_levels`, `test_dependency_graph`, `test_call_command`.
3. **Le dessin tenu égal** (ARCH-001, ARCH-005) : `tests/test_arrows.py` rétabli de `8310c82^` (quatre jeux et un cinquième sans moment, la note, les constantes), plus la comparaison de `polar-distribution` à `fastener_forces` et aux `#eq` ; ligne du catalogue `docs/conventions/testing-catalogue-typst.md`.
4. **Le générateur** (REQ-003, ARCH-003) : `calc/domains/unfold.py` `_generate_connection` — plus de figure de tête ; après `#var M` (ou `V` sans bras de levier), une ligne étiquetée `polar-figure` : `#figure(image-polar-moment("<id>", N: "N", V: "V", M: "M", width: 60%), kind: image, caption: […]) <…>`, la légende du glossaire, une ligne vide avant et après ; `form_of` de `connection` changé. Tests : `test_domain_generators` (place, compile, une valeur changée à la main dessine des flèches, pas de `M:` sans bras de levier), `test_unfold` (un fichier ancien : « forme », pas de réécriture, `regenerate`, `reinsert`).
5. **Le projet exemple et les pages** : le fichier `Connections/VU-MP-1.typ` de l'exemple régénéré, `report-golden.json` re-gelé (`WOODCORE_UPDATE_GOLDEN=1`, raison dans `CHANGES`), les exemples reconstruits (`build_examples.py`).
6. **Documentation** : `docs/domain/connections.md`, `docs/typst/api-conventions.md` §10bis (ligne de la table et ligne « ce que devient `show-polar-moment` »), textes périmés (ARCH-RISK-012), `docs/decisions.md` (la décision et le dessin de nouveau écrit en deux langues), `CHANGELOG.md`, « Nouveautés » 0.121 fr/de/en.
7. **Vérification** : la suite liée puis la suite complète ; `verify-requirements`.

## 15. Vérification

_(écrite par `verify-requirements` : vérificateur indépendant, arbre de travail contre HEAD, 22.10.2026 ; deux tours)_

**Premier tour** : 8 ✅, 5 ⚠️ — `test_commands` rouge (la copie locale `examples/lib`, ignorée par git, pas reconstruite après la dernière modification de `lib/`) ; REQ-001 sans test sur le SVG ni cas à zéro ; REQ-002 sans `N: "nope"` ni comparaison nom/nombre ; UI-001 sans le français ; ARCH-004 sans test. **Corrigé** : la métadonnée `<woodcore-polar-arrows>` porte aussi les flèches et la note posées dans la figure ; quatre tests ajoutés à `tests/test_arrows.py` ; exemples reconstruits. **Second tour** (preuves relues par l'implémenteur, tests relancés) :

| Élément | Verdict | Preuve |
|---|---|---|
| REQ-001 | ✅ | `lib/calc-engine-connections.typ` `image-polar-moment` ; `test_arrows.test_the_figure_carries_its_arrows_in_the_palette_s_colours_and_none_at_zero` (`<line>`, `<polygon>`, jaune, vert, bleu, rouge de la palette, F1 … F4 ; aucune flèche à N = V = M = 0) — passed |
| REQ-002 | ✅ | lecture par nombre ou nom dans le `context`, refus par `panic` qui nomme l'argument ; `test_arrows.test_a_force_named_draws_what_the_same_number_draws` (`N: "N"` = `N: 7.5`, `N: "nope"` et N en « N » refusés) et `test_image_figures.test_a_polar_moment_draws_its_forces_given_as_numbers_or_names` — passed |
| REQ-003 | ✅ | `calc/domains/unfold.py` `_generate_connection` ; `test_domain_generators.test_a_polar_moment_written_out_draws_its_figure_from_its_forces` (place, ligne exacte, N = 7.5 → N/n sur chaque moyen, pas de `M:` sans bras de levier) — passed |
| UI-001 | ✅ | légende du glossaire (`connection.caption`, `connection.figure_caption`) ; `test_arrows.test_the_note_of_a_share_too_small_is_in_the_report_s_language` (« Zu klein zum Erkennen: N/n = 1.88 kN », « Trop petit pour être lu : N/n = 1.88 kN ») — passed |
| ARCH-001 | ✅ | `tests/test_arrows.py` rétabli, cinq jeux, SVG et note élément par élément, constantes et couleurs — passed |
| ARCH-002 | ✅ | `lib/image-vocabulary.json`, `build_reference_lib.py` (`CATEGORIES`, sans `level:`), `dependency_graph.py`, `commands.json` fr/de/en, `renamed-commands.json`, `///` et deux exemples (`examples/image-polar-moment-1/2`) ; `test_commands` (44 passed), `test_doc_comments`, `test_command_levels`, `test_call_command`, `test_dependency_graph`, `test_i18n` (clés de cette spec) |
| ARCH-003 | ✅ | forme `…-a` ; `test_unfold.test_a_polar_moment_of_the_old_form_is_regenerated_with_its_figure_after_the_forces` (« forme », pas de réécriture, compile, une figure après les forces, les `#eq` de l'ingénieur gardés, base complète, `reinsert`) — passed |
| ARCH-004 | ✅ | aucun `var-registry.update` dans la commande ; `test_arrows.test_the_command_publishes_nothing` (F_max déclaré avant garde sa valeur, aucune clé ajoutée) — passed |
| ARCH-005 | ✅ | `test_arrows.test_the_command_distributes_the_forces_as_python_does`, `test_the_file_s_lines_and_its_figure_give_the_same_forces` (1e-9) — passed |
| CON-001, CON-002 | ✅ | aucun schéma ni source de connexion modifiés par cette spec (`schemas/woodcore-project.schema.json` est d'une autre session) |
| §8 hors périmètre | ✅ | pas de saisie des forces dans l'onglet, pas de `show-polar-moment`, pas de « Copier » ; `polar_tab.py` : une docstring |
| Documentation | ✅ | `docs/domain/connections.md`, `docs/typst/api-conventions.md` §10bis, `docs/decisions.md` et son index, `CHANGELOG.md`, « Nouveautés » 0.121 fr/de/en, catalogue `testing-catalogue-typst.md` |
| Tests | ✅ | suite liée (119 fichiers, 1998 passed) : `test_commands` corrigé depuis ; les 11 autres échecs (`test_i18n` clés `pj_*` de `project_tab.py`, `test_linkable_spin`, `test_light_refresh`, `test_docs_coherence` `test_template_preview.py`, `test_tab_overrides` `ProjectTab`) sont dans les fichiers d'une autre session en cours, aucun ne touche ceux de cette spec |

## 16. Journal d'avancement

| Date | Statut | Fait / reste |
|---|---|---|
| 2026-10-22 | draft | spécification extraite de la question de l'ingénieur sur les flèches et de sa réponse (option « Nouvelle #image-polar-moment ») ; existant relu : l'ancien dessin (`lib/calc-engine-connections.typ` à `8310c82^`), l'ancien `tests/test_arrows.py`, `connection_svg.force_arrows`, le générateur `_generate_connection`, les marqueurs `<!-- forces -->` et `<!-- note -->` toujours présents dans la figure exportée |
| 2026-10-22 | specified | Q-001 à Q-003 répondues (options recommandées) : une seule figure fléchée après les forces, la signature avec `detail-figure`, pas de « Copier » ; D-02 à D-04 |
| 2026-10-22 | reviewed | revue d'architecture : APPROUVER AVEC RÉSERVES (ARCH-RISK-001 bloquant, un projet déjà écrit ; 003-009 importants) ; ARCH-003 à ARCH-005 ajoutés ; plan §14 en sept étapes |
| 2026-10-22 | approved | approuvée par l'ingénieur avec les deux choix de la revue : la répartition recalculée par la commande et tenue égale par un test (ARCH-005), un projet déjà exporté régénéré par « Régénérer » (ARCH-003) |
| 2026-10-22 | implementation | étapes 1 à 3 : les helpers du dessin rétablis et `#image-polar-moment` dans `lib/calc-engine-connections.typ` (refus par `panic` qui nomment l'argument, aucune écriture au registre, métadonnée `<woodcore-polar-arrows>`) ; les contrats (vocabulaire, `CATEGORIES`, liste sans `level:`, `COMMAND_REFERENCES`, `commands.json` fr/de/en, `renamed-commands.json`) ; `tests/test_arrows.py` rétabli avec cinq jeux et la comparaison de `polar-distribution` à `fastener_forces` (le test du fichier attend l'étape 5) ; `test_image_figures` étendu ; lignes du catalogue — REQ-001, REQ-002, UI-001, ARCH-001, ARCH-002, ARCH-004 faits, ARCH-005 en partie |
| 2026-10-22 | implementation | étapes 4 et 5 : `_generate_connection` écrit la figure fléchée après N, V, M (étiquette `polar-figure`, légende du glossaire, sans `M:` sans bras de levier), plus de figure de tête ; forme `…-a` ; trois défauts de la base de régénération trouvés sur l'exemple et corrigés — « Régénérer » doublait une ligne que l'ingénieur avait réécrite (`#var("N")` devenu `#eq("N", `N_Ed`)`, même `id:`) et le fichier ne compilait plus : `_own_line` reconnaît cette ligne comme la sienne (état « own » au lieu de « missing »), `regenerate` la garde à la place de celle de l'écriture, `reinsert` place une ligne après elle ; `regenerate` n'enregistrait que la première étiquette d'un texte ; `VU-MP-1.typ` de l'exemple régénéré (sa base, son entrée de `domain-state.json`), `report-golden.json` re-gelé (raison dans `CHANGES`), exemples reconstruits ; tests `test_domain_generators`, `test_unfold` (forme ancienne écrite par le test), `test_arrows` (le fichier) — REQ-003, ARCH-003, ARCH-005 faits |
| 2026-10-22 | testing | étape 6 : `docs/domain/connections.md` (le fichier et sa figure aujourd'hui), `docs/typst/api-conventions.md` §10bis (ligne de la commande, ligne de `show-polar-moment`), textes périmés de `connection.py`, `connection_svg.py`, `polar_tab.py`, de l'en-tête de `calc-engine-connections.typ` (ARCH-RISK-012), `docs/decisions.md` §13 et son index, `CHANGELOG.md`, « Nouveautés » 0.121 fr/de/en ; reste l'étape 7 (suite liée, vérification indépendante, suite complète) |
| 2026-10-22 | completed | vérification indépendante : premier tour 8 ✅ 5 ⚠️, corrigés (métadonnée des flèches, quatre tests, exemples reconstruits) ; second tour tout ✅ ; §11 coché |
