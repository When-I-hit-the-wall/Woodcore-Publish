---
id: 2026-10-21-graphe-dependances
titre: Le graphe de dépendances du projet (issue #71)
status: completed
cree: 2026-10-21
mis_a_jour: 2026-10-21
source: message écrit (issue #71, décisions de l'ingénieur du 21.10.2026) et rapport 000-Audits/261019-audit-base-saine.md §6
docs: [docs/domain/variable-links.md, docs/architecture/data-contracts.md, docs/architecture/principles.md, docs/ui/window.md, docs/domain/loads.md, docs/domain/member-checks.md, docs/domain/connectors.md]
---

# Le graphe de dépendances du projet — Spécification

## 1. Objectif

Un projet Woodcore est un réseau : une vérification suit une position, une charge suit une autre charge, un modèle statique lit une charge, un script lit une valeur de l'export, un domaine de « Formules » lit un calcul, un connecteur suit un schéma et ses positions, le rapport imprime tout cela. Ce réseau n'est écrit nulle part : chaque objet connaît ce qu'il lit, aucun ne sait qui le lit. L'ingénieur veut le voir et en être averti : quand une valeur change en amont, savoir ce qu'elle touche en aval — « une seule source de vérité » étendue aux liens entre objets (audit 261019, §6).

## 2. Source

> **T1** — Audit 261019 §6 (« Pistes d'architecture ») : « Un graphe de dépendances du projet : positions → charges → efforts → vérifications → rapport. Une valeur changée en amont dirait ce qu'elle rend périmé en aval. C'est l'extension naturelle de « une seule source de vérité », et de la colonne « périmé » que les domaines dépliés (#62) ont commencée. »
>
> **T2** — L'ingénieur, 21.10.2026, à la question « Graphe de dépendances : sous quelle forme ? » : « Onglet de la fenêtre, Fichier dans data/, Avertissements à l'export » (les trois).
>
> **T3** — L'ingénieur, 21.10.2026, à la question « Comment avancer ? » : « Une spec par sujet » — le graphe a sa propre spécification.
>
> **T4** — L'ingénieur, 21.10.2026, « Garder la copie » du moteur dans les projets (#71, l'autre moitié de l'issue).
>
> **T5** — L'ingénieur, 21.10.2026 (téléphone) : « Lance déjà l'implémentation #71 … Fais-le pour moi ».

## 3. Exigences fonctionnelles

### REQ-001 — Un graphe calculé à chaque export, de tous les objets du projet
- **Exigence** : à chaque export, Woodcore construit le graphe des objets du projet et de leurs liens, sans rien recalculer, les sources étant lues comme l'export les lit (ARCH-RISK-1102) : un nœud par objet (position, cas de charge, script, domaine de « Formules » — un domaine déplié n'en est pas un, il est le fichier de sa vérification (ARCH-RISK-1101) —, vérification bois, vérification acier, profil acier, connecteur, assemblage/moment polaire, schéma, modèle statique, plan, plan de protection incendie, document de fond d'un plan, extrait d'annexe — et chaque section des trois documents, D-06), une arête par référence, chacune nommant le champ qui la porte et, pour un lien de variable, la variable (`domain`, `instance`, `var`). Les références connues sont celles que l'inventaire du 21.10.2026 a relevées (§13) : la position d'une vérification, d'une vérification acier, d'un élément de schéma, d'une étiquette de plan ; le schéma d'un connecteur et d'un assemblage ; le plan d'un plan incendie, son plan de coupe, son document de fond ; les `links` de toute source ; les grandeurs d'un modèle statique ; les `vars` des textes de figure ; les `value()` d'un script ; les `var-of`/`#var(…, domain:)` d'un domaine de « Formules ».
- **Source** : T1, T2
- **Priorité** : doit
- **Critère d'acceptation** : sur le projet exemple, le graphe contient chaque nœud et chaque arête de l'inventaire (test qui énumère les attentes) ; un objet ajouté qui en cite un autre ajoute une arête ; le graphe est le même que l'export soit lancé depuis la fenêtre ou `woodcore-cli export`.

### REQ-002 — `data/dependencies.json`
- **Exigence** : l'export écrit le graphe dans `data/dependencies.json`, selon un schéma versionné `schemas/dependencies.schema.json` (`schema_version` 1.0), validé avant écriture, reproductible à l'octet (ordre stable), avec pour chaque nœud une empreinte de ses valeurs (D-04) pour que l'export suivant sache ce qui a changé. Un nouveau projet est semé d'un graphe vide (`export_all.seed`).
- **Source** : T2
- **Priorité** : doit
- **Critère d'acceptation** : le fichier existe après un export du projet exemple, valide son schéma, est identique à l'octet d'un export à l'autre sans changement ; un projet neuf l'a vide.

### REQ-003 — Avertissements à l'export
- **Exigence** : l'export dit, par des `engine.Note` traduites (fr/de/en), ce que le graphe révèle, selon D-04 : ce qu'une valeur changée depuis l'export précédent touche en aval (jusqu'aux sections du rapport, D-06) ; une boucle entre objets de sortes différentes (aujourd'hui seules les charges entre elles sont refusées).
- **Source** : T1, T2
- **Priorité** : doit
- **Critère d'acceptation** : un test change une position du projet exemple, exporte, et l'avertissement nomme la position et les objets en aval ; un test crée une boucle charge → « Formules » → même charge et l'export la nomme ; aucun avertissement n'est émis sur un export sans changement.

## 4. Exigences d'interface (fenêtre, rapport, site)

### UI-001 — L'onglet « Dépendances »
- **Exigence** : un onglet de la fenêtre montre le graphe lu dans `data/dependencies.json`, en liste groupée par sorte (D-05) ; un objet choisi montre ce dont il dépend et ce qui dépend de lui, chacun cliquable pour ouvrir l'objet dans son onglet ; l'onglet n'écrit rien (lecture seule, comme « Variables ») ; il dit quand l'export qu'il montre date d'avant la dernière modification d'une source.
- **Source** : T2
- **Langues** : fr / de / en
- **Critère d'acceptation** : un test hors écran ouvre l'onglet sur une copie du projet exemple, choisit une position et lit ses dépendants (vérifications, schémas, plans) ; un clic ouvre l'objet dans son onglet ; `test_i18n` vert ; l'onglet n'est pas dans `WRITERS`.

## 5. Exigences d'architecture

### ARCH-001 — Le graphe est construit par un module de domaine, sans Qt
- **Exigence** : `calc/domains/dependencies.py` construit le graphe à partir de ce que l'export a déjà en mémoire et des lecteurs de références existants (`links.entries`, `registry._load_targets`, `figure_text`, `loads_migrate` pour les appels des scripts et des `.typ`) — une seule façon de lire chaque sorte de référence ; l'onglet ne fait que l'afficher (principes §2).
- **Source** : principes (domaine sans UI, une seule source)
- **Critère d'acceptation** : aucun import de Qt dans le module ; aucune lecture de référence recopiée (`test_no_duplicates`).

### ARCH-002 — La détection de boucle est celle du graphe
- **Exigence** : `links.find_cycle` sert au graphe entier ; la boucle charge ↔ charge (registry) reste refusée comme aujourd'hui, et le graphe dit les autres (charge → « Formules » → charge, script ↔ connecteur par l'export précédent), (D-04).
- **Source** : inventaire du 21.10.2026 (écarts 1 et 3)
- **Critère d'acceptation** : `test_links` reste vert ; un test de boucle mixte.

## 6. Contraintes

- **CON-001** — Aucun fichier de `data/` existant ne change d'octet (le graphe est un fichier de plus). Source : principes, reproductibilité de l'export.
- **CON-002** — Un projet sans export précédent, ou dont `dependencies.json` est illisible, s'exporte sans avertissement de changement (rien à comparer) — jamais un arrêt. Source : CLAUDE.md « a missing input warns ».
- **CON-003** — Le moteur reste copié dans chaque projet (T4) : ce graphe ne touche pas au moteur Typst, le rapport n'étant que lu (D-06).
- **CON-004** — L'export ne s'allonge pas de plus de quelques dixièmes de seconde sur le projet exemple (≈ 150-250 ms visés, une seule passe des `.typ`). Source : inférée (export lancé à chaque enregistrement).

## 7. Décisions prises

- **D-01** — Trois formes : un onglet, `data/dependencies.json`, des avertissements à l'export (T2, l'ingénieur, 21.10.2026).
- **D-02** — Une spécification à part (T3).
- **D-03** — Le moteur reste copié dans les projets ; #71 le note (T4).
- **D-04** — Les avertissements disent ce qui a changé depuis l'export précédent et ce que cela touche en aval, et les boucles entre sortes d'objets ; une référence cassée reste dite par l'avertissement qui existe déjà (Q-001 : A).
- **D-05** — L'onglet est une liste groupée par sorte, « dépend de » / « utilisé par », cliquable (Q-002 : A).
- **D-06** — Les sections des trois documents sont des nœuds du graphe (Q-003 : A).
- **D-07** — Proposées avec le plan (revue, ARCH-RISK-1104 à 1109), confirmées à l'approbation (l'ingénieur, 21.10.2026) : un argument calculé (`for id in ids("position")`) donne une arête joker, sans la déplier ; le fichier est semé vide dans un projet neuf ; l'empreinte prend tout l'enregistrement moins les clés de présentation ; les `value()` d'un script sont relevés à l'exécution ; une référence dont la cible manque n'est pas une arête (elle est déjà dite ailleurs).

## 8. Hors périmètre

- Le moteur hors des projets (T4 : décidé contre).
- Les écarts relevés par l'inventaire hors du graphe lui-même : la renumérotation qui ne réécrit pas la position d'une vérification acier, les avertissements des connecteurs en phrases allemandes non codées, le plan incendie retiré de `fire.json` quand son plan a disparu — notés dans `docs/open-questions.md`, sauf décision contraire.
- Une mise à jour automatique de ce qui est périmé : le graphe dit, il ne réécrit rien.

## 9. Idées non retenues comme exigences

- « positions → charges → efforts → vérifications → rapport » (T1) est un exemple de chaîne : Woodcore ne lie aujourd'hui aucune charge à une position (docs/domain/loads.md §8) ; le graphe montre les liens qui existent, il n'en crée pas.

## 10. Questions

### Q-001 — Que disent les avertissements de l'export ?
- **Pourquoi elle compte** : c'est ce qui décide de ce que le fichier doit garder d'un export à l'autre (une empreinte des valeurs) et du bruit à l'export.
- **Options** : A (recommandée) — ce qui a changé depuis l'export précédent et ce que cela touche en aval (« La position P12 a changé : ZS-01, BI-03, le schéma D02 en dépendent »), plus les boucles entre sortes d'objets ; B — seulement les références cassées et les boucles ; C — A et B.
- **Réponse** : **A** — ce qui a changé depuis l'export précédent et ce que cela touche en aval, et les boucles entre sortes d'objets (l'ingénieur, 21.10.2026).

### Q-002 — Sous quelle forme l'onglet montre-t-il le graphe ?
- **Pourquoi elle compte** : une liste se construit avec les widgets existants ; un dessin de nœuds et de flèches demande un moteur de dessin de plus.
- **Options** : A (recommandée) — une liste groupée par sorte d'objet ; un objet choisi montre « dépend de » et « utilisé par », cliquables ; B — un dessin du graphe (nœuds et flèches) ; C — les deux, le dessin plus tard.
- **Réponse** : **A** — une liste groupée par sorte ; un objet choisi montre « dépend de » et « utilisé par », cliquables (l'ingénieur, 21.10.2026).

### Q-003 — Le rapport est-il un nœud du graphe ?
- **Pourquoi elle compte** : savoir quelle section imprime une valeur demande de lire les `.typ` des trois documents (comme la migration des noms le fait déjà) ; sans cela, le graphe s'arrête aux objets de l'export.
- **Options** : A (recommandée) — oui : chaque section des documents qui appelle `show-calc`, `var-of`, `val`… est un nœud, ses appels des arêtes ; B — non, le graphe s'arrête aux objets de l'export.
- **Réponse** : **A** — oui : les sections des trois documents sont des nœuds, leurs appels des arêtes (l'ingénieur, 21.10.2026).

## 11. Critères d'acceptation

- [x] REQ-001 — graphe complet sur le projet exemple, mêmes nœuds et arêtes depuis la fenêtre et la ligne de commande
- [x] REQ-002 — `data/dependencies.json` valide, reproductible, semé vide
- [x] REQ-003 — avertissements selon D-04, aucun sur un export sans changement
- [x] UI-001 — onglet « Dépendances » en lecture seule, clic vers l'objet, fr/de/en
- [x] ARCH-001 — module de domaine sans Qt, lecteurs de références non recopiés
- [x] ARCH-002 — boucles mixtes dites, `test_links` vert
- [x] Documentation : `docs/domain/` (nouveau §), `docs/architecture/data-contracts.md`, `docs/ui/window.md`, `CHANGELOG.md`, « Nouveautés » fr/de/en.
- [x] Tests : nouveaux fichiers ajoutés au catalogue, suite complète verte.

## 12. Traçabilité

| Source | Élément | Statut |
|---|---|---|
| T1 | REQ-001, REQ-003, ARCH-002 ; §9 (exemple de chaîne) | capturé |
| T2 | REQ-002, REQ-003, UI-001, D-01 | capturé |
| T3 | D-02 | décision |
| T4 | D-03, CON-003, §8 | décision |
| T5 | — | conduite (implémenter dans cette session) |

### Points de la source non résolus

- Aucun : Q-001 à Q-003 répondues le 21.10.2026.

## 13. Revue d'architecture

Agent `architecture-reviewer`, 21.10.2026, sur la spec, `principles.md`, `layout.md`, `data-contracts.md`, `variable-links.md` et le code (inventaire `code-scout` du même jour : arêtes A à U, écarts 1 à 8). Mesures sur le projet exemple : 191 `.typ`, `commands_migrate.plan` 62 ms, `loads_migrate.plan` 99 ms. Aucune décision de `decisions.md` ne contredit le graphe. **Verdict : APPROUVER AVEC RÉSERVES** ; toutes reprises au plan (§14) ou dans les exigences.

- **ARCH-RISK-1101 (bloquant)** — une vérification dépliée et son domaine `Timber-checks/…` (`#var(…, domain: ("check", id))`, et `file` dans `checks.json`) feraient une fausse boucle à chaque export → un domaine déplié (`gen`, `unfold.json`) n'est pas un nœud : c'est le `file` de la vérification ; le résolveur d'adresses apprend le mot `check` ; test : le projet exemple n'a aucune boucle mixte.
- **ARCH-RISK-1102 (bloquant, rédaction)** — « sans relire le disque » est faux pour les modèles statiques (l'enregistrement ne garde que le texte `from`), les « Formules », les scripts et les sections → REQ-001 corrigée : rien n'est recalculé, les sources sont lues comme l'export les lit ; le graphe se construit en un bloc après les `prepare` (≈ `export_all.py:280`) et ne lève jamais une fois l'écriture commencée.
- **ARCH-RISK-1103 (important)** — cinq lecteurs de références existent (`renumbering.json_stores`, `formula_domain.cited_by`, `loads_migrate._READERS`, `registry._load_targets`, `_VAR_OF`) → une fonction `references()` par domaine, à côté de son `check_source`, tenue par `test_domain_contracts` ; `registry.load_targets` public ; un test tient les magasins de la renumérotation ⊆ arêtes de position du graphe (l'écart acier reste hors périmètre, rendu visible). Piège : `connectors.json` `position` est l'id du connecteur lui-même ; l'arête est `members[].element`/`members[].position`, et connecteur → schéma se lit sur `connector.schema` seul.
- **ARCH-RISK-1104 (important)** — lire les `.typ` : aucune table « commande → sorte → argument », les commentaires contiennent des appels, des boucles (`for id in ids("position")`) donnent des arguments calculés → une table `COMMAND_REFERENCES`, tenue contre les commandes publiques de `lib/` par un test ; appels trouvés hors commentaires et chaînes ; un argument calculé donne une arête joker `{kind, id: "*"}` ; un nom de registre de document que Python ne résout pas (`val(…, domain: "S10 - 0.55 kN Ende")`) est compté `unresolved` sur la section ; l'id d'une section est celui de `structure_nodes.tree`, `enabled` porté par le nœud ; une seule passe de fichiers partagée.
- **ARCH-RISK-1105 (important)** — les `value()` d'un script ne sont écrits nulle part → capturés à l'exécution (`script_runner._reader` les note, le rapport JSON les porte, `script.prepare(reads=)` les remplit), sans toucher un octet de `scripts.json` ; un script lit connecteurs et assemblages dans l'export précédent : arête `previous: true`.
- **ARCH-RISK-1106 (important)** — la détection du changement : empreinte `sha256` du JSON canonique (`sort_keys`) de l'enregistrement de chaque nœud, moins une liste noire de clés de présentation par sorte (`figures`, `overlay`, `style`, `label`, `name`, `warnings`, `tables`…) — tout compte par défaut ; les sections n'ont pas d'empreinte (ce sont des puits). « Changé » = même nœud, empreinte différente ; un nœud nouveau ou retiré n'est pas un changement ; un fichier précédent absent, illisible ou d'une autre version = rien à comparer. **Bruit** : seules les racines sont dites (nœud changé dont aucun amont direct n'a changé), leur aval transitif listé une fois par sorte, plafonné à 8 ids puis « (+N) ». Le fichier reste une fonction pure des sources (aucun « changé » écrit). Une `Note` par (racine, sorte en aval), ids joints, le mot de la sorte une `Note` imbriquée traduite. Une seule aide `engine.digest` (deux copies existent : `annex._digest`, `build_reference._rows_digest`).
- **ARCH-RISK-1107 (important)** — `links.find_cycle` repart de zéro à chaque appel → `links.find_cycles(graph)` (composantes fortement connexes, chacune tournée vers son plus petit nœud), `find_cycle` réécrit dessus ; boucle mixte = composante d'au moins deux sortes ; les boucles d'une seule sorte restent à leurs propriétaires (charges : refus du registre ; « Formules » : `CIRCLE`).
- **ARCH-RISK-1108 (important)** — homonyme : `calc/tools/dependencies.py` (les paquets installés) existe → module `calc/domains/dependency_graph.py`, onglet `tab_dependencies`, mots `dg_` ; `schemas/dependencies.schema.json` 1.0 ; forme : `nodes {sorte: {id: {digest, file, enabled?}}}`, `edges` liste triée `{from, to, field, variable?, previous?}` ; aucune date ; calculé avant `if dry: return` (`woodcore-cli check` avertit), écrit avec les autres fichiers ; l'état déplié lu dans `check_data` et `unfold.json` ; test de reproductibilité sur le projet exemple.
- **ARCH-RISK-1109 (important)** — sortes manquantes : documents des plans (fond), extraits/annexes (`doc-extract`), profils acier → sortes ajoutées ; une cible absente n'est jamais une erreur : l'arête est retirée (la référence cassée est déjà dite ailleurs, D-04).
- **ARCH-RISK-1110 (important)** — aucune API « ouvrir un objet » → `MainWindow.open_object(kind, id)` et `SourceEditorTab.open_object(cid)`, surchargés pour Positions, Domaines, les toiles et Structure ; la carte sorte → clé de `SPECS` à côté de `tab_registry` ; un `.typ` s'ouvre par `open_in_editor(path, line)` ; l'onglet ne définit aucun nom de `WRITERS` (test) ; navigateur comme « Variables » (pas de `dirty`, `on_shown` relit) ; bandeau « périmé » par l'heure des `file` des nœuds.
- **ARCH-RISK-1111 à 1113 (mineurs)** — trois langues (`warn_dep_*`, noms des sortes, mots `dg_`) ; budget ≈ 150-250 ms ; `layout.md`, `data-contracts.md`, `docs/ui/tab-dependencies.md`, `docs/README.md`, catalogue des tests.

## 14. Plan d'implémentation

Cinq lots, chacun avec ses tests ; la suite complète au dernier.

**Lot 1 — Les pièces partagées** (ARCH-001, ARCH-002, ARCH-RISK-1103, 1104, 1106, 1107)
- `engine.digest(data)` (sha256 du JSON canonique), `annex._digest` et `build_reference._rows_digest` en deviennent les clients.
- `links.find_cycles(graph)` (composantes fortement connexes, rotation canonique), `find_cycle` réécrit dessus.
- `calc/typst_calls.py` : `_closing`, `_split`, `_literal` déplacés de `commands_migrate`/`loads_migrate` (qui les importent), et la recherche d'appels hors commentaires et chaînes.
- `formula_domain` : la classification d'une source (`var-of`, paire, `check`, id) en une fonction, lue par `resolve_import` et par le graphe.
- Tests : `test_links` (`find_cycles`), `test_no_duplicates`, `test_commands_migrate`, `test_loads_migrate`.

**Lot 2 — Les références de chaque domaine** (REQ-001, ARCH-RISK-1101, 1103, 1105, 1109)
- `references(...)` dans `member_check`, `steel_check`, `connector`, `connection`, `schema`, `plan`, `fire`, `statics` (sources), les sources de charges (liens), `figure_text` (`texts`), au contrat de `contracts.py` ; `registry.load_targets` public.
- `script_runner` capture les `value()` (rapport `reads`), `script.prepare(reads=)` ; `scripts.json` inchangé.
- Le domaine déplié rattaché à sa vérification (`file`), jamais un nœud.
- Tests : `test_domain_contracts`, `test_script`, `test_renumbering` (magasins ⊆ arêtes de position).

**Lot 3 — Le graphe, le fichier et les avertissements** (REQ-001 à REQ-003, CON-001 à CON-004, ARCH-RISK-1102, 1104, 1106, 1108)
- `calc/domains/dependency_graph.py` : `build(...)` (enregistrements en mémoire, sources des modèles statiques, domaines « Formules », lectures des scripts, sections des trois documents par `COMMAND_REFERENCES` et `structure_nodes.tree`, arêtes joker et `unresolved`), `diff(previous, current)` (racines, aval transitif plafonné), `notes(...)` (`warn_dep_changed`, `warn_dep_cycle`, fr/de/en), `read(here)` tolérant.
- `schemas/dependencies.schema.json` 1.0 ; `export_all.run` : graphe précédent lu d'abord, construit après les `prepare`, avertissements avant `if dry`, écrit avec les autres fichiers ; `seed` l'écrit vide.
- Tests : `tests/test_dependency_graph.py` (attentes énumérées du projet exemple, octets identiques sur deux exports, pas de graphe précédent ou illisible, commentaire sans arête, joker, pas de fausse boucle dépliée, position changée → racine et aval, cascade → racine seule, aucun avertissement sans changement, boucle charge → « Formules » → charge, boucle script ↔ connecteur `previous`, `COMMAND_REFERENCES` contre `lib/`), `test_new_project`, `test_export`.

**Lot 4 — L'onglet « Dépendances »** (UI-001, ARCH-RISK-1110, 1111)
- `calc/tools/dependencies_tab.py` (liste groupée par sorte, « dépend de » / « utilisé par », bandeau « périmé », mots `dg_` fr/de/en), ligne de `SPECS` à côté de « Variables », icône ; `MainWindow.open_object(kind, id)`, `SourceEditorTab.open_object`, surcharges Positions, Domaines, toiles, Structure ; un `.typ` par `open_in_editor`.
- Tests : `tests/test_dependency_tab.py` (hors écran : une position et ses dépendants, clic qui ouvre l'objet, aucun nom de `WRITERS`, trois langues), `test_tab_registry`, `test_i18n`.

**Lot 5 — Documentation et clôture**
- `docs/domain/dependencies.md`, `docs/architecture/data-contracts.md`, `layout.md`, `docs/ui/tab-dependencies.md` et `window.md`, `docs/README.md`, `decisions.md` §13, `docs/open-questions.md` (écarts de l'inventaire hors périmètre), `CHANGELOG.md`, « Nouveautés » 0.120.0 fr/de/en, catalogue des tests.
- Vérification indépendante, puis `finish` : suite complète, commit, une question avant de pousser ; #71 fermée, #73 commentée.

## 15. Vérification

Agent `requirements-verifier`, 21.10.2026, base dc16cc0, sur l'arbre de travail. Ronde 1 : un défaut bloquant (l'onglet sans `view_state`, toute reconstruction de la fenêtre levait) et des critères réalisés sans preuve ; ronde 2 par l'implémenteur, tests relancés, suite complète verte.

| Élément | Verdict | Preuve |
|---|---|---|
| REQ-001 | ✅ | `dependency_graph.build` ; `test_the_example_project_s_references_are_edges_of_its_graph` (exemple), `test_every_kind_of_reference_is_an_edge` (chaque lecteur sur un projet synthétique, un objet ajouté ajoute son arête — ronde 2) ; fenêtre et `woodcore-cli export` passent par le même `export_all.run` (par construction) |
| REQ-002 | ✅ | `schemas/dependencies.schema.json` 1.0, validé avant écriture, mêmes octets sur deux exports, semé vide (`test_new_project`) |
| REQ-003 | ✅ | `test_a_position_changed_is_said…` (racine seule, ids nommés — ronde 2), aucun avertissement sans changement, la boucle charge → « Formules » → charge nommée par la note de l'export (ronde 2) |
| UI-001 | ✅ | `test_dependency_tab` : dépendants vérifications, schémas et plans d'une position, ouverture dans l'onglet, onglet reconstruit gardant l'objet choisi (`view_state`, `restore` — ronde 2), graphe non exporté, aucun écrivain ; `test_tab_registry` : chaque onglet a `view_state` (ronde 2) |
| ARCH-001 | ✅ | module sans Qt (test), `references()` tenu par `test_domain_contracts` (ronde 2), `registry.load_targets` déjà public, module nommé `dependency_graph` (ARCH-RISK-1108) |
| ARCH-002 | ✅ | `links.find_cycles` (Tarjan itératif, chaîne la plus courte depuis le plus petit nœud, sans récursion), testé directement dans `test_links` (ronde 2) |
| D-04 à D-07 | ✅ | racines, liste, sections, jokers, empreintes, lectures des scripts (`test_a_script_s_reads_are_recorded_as_it_runs` — ronde 2) |
| CON-001 | ✅ | aucun fichier existant de `data/` ne change ; seul le cache du classeur de référence (fenêtre, hors projet) est recalculé une fois — dit dans `engine.digest` |
| CON-002 à CON-004 | ✅ | rien à comparer sans graphe précédent ; moteur intact ; ≈ 0,2 s par export, 1,1 s au premier (mesure du vérificateur) |
| Documentation | ✅ | `docs/domain/dependencies.md`, `docs/ui/tab-dependencies.md`, README, data-contracts, layout, window, decisions et index, open-questions, CHANGELOG, « Nouveautés » fr/de/en, catalogues |
| Hors périmètre §8 | ✅ | rien de fait, noté dans `open-questions.md` |

## 16. Journal d'avancement

| Date | Statut | Fait / reste |
|---|---|---|
| 2026-10-21 | draft | spécification écrite depuis #71, l'audit §6 et les décisions du 21.10 ; inventaire des références du projet ; trois questions |
| 2026-10-21 | specified | réponses Q-001 A, Q-002 A, Q-003 A ; D-04 à D-06 |
| 2026-10-21 | reviewed | revue d'architecture (APPROUVER AVEC RÉSERVES, ARCH-RISK-1101 à 1113) reprise ; plan en cinq lots ; D-07 à confirmer |
| 2026-10-21 | approved | l'ingénieur approuve la spec, le plan et les choix D-07 (« Approuver et implémenter ») |
| 2026-10-21 | implementation | lot 1 commencé |
| 2026-10-21 | implementation | lot 1 fait : `engine.digest`, `links.find_cycles`, `calc/typst_calls.py` (les migrations y lisent), `formula_domain.reference` (lu par `resolve_import`) — ARCH-001, ARCH-002 ; `parse_call_at` non retenu : il exige le `#` qu'un appel dans une boucle n'a pas |
| 2026-10-21 | implementation | lot 2 fait : `references()` de member_check, steel_check, connector, connection, schema, plan, fire ; `links.references` ; lectures des scripts relevées (`reads`) |
| 2026-10-21 | implementation | lot 3 fait : `dependency_graph.py`, `schemas/dependencies.schema.json`, branché dans `export_all.run` et `seed`, `structure_nodes.section_files` (lecture des sections sans titres : 2,6 s → 0,6 s), mots `warn_dep_*` fr/de/en ; `tests/test_dependency_graph.py` 8 verts — REQ-001 à REQ-003 |
| 2026-10-21 | implementation | lot 4 fait : `dependencies_tab.py`, `SPECS`, icône, `MainWindow.open_object`, `GRAPH_KIND`/`lists_object`/`open_object` des onglets ; `tests/test_dependency_tab.py` 3 verts — UI-001 |
| 2026-10-21 | testing | lot 5 : `docs/domain/dependencies.md` (§3.3quinvicies), `docs/ui/tab-dependencies.md`, README, data-contracts, layout, window, decisions et index, open-questions, CHANGELOG, « Nouveautés » fr/de/en, catalogue |
| 2026-10-21 | verification | vérification indépendante : `view_state` manquant (bloquant), preuves manquantes ; corrigés (onglet, `find_cycles` sans récursion, tests synthétiques, lectures des scripts, contrats) |
| 2026-10-21 | completed | spec close, déplacée dans `completed/` |
