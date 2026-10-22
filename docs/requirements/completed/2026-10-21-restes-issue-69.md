---
id: 2026-10-21-restes-issue-69
titre: Restes de l'issue #69 — lignes du bois par le moteur, neige et vent sans cellules calculées, liste des toiles dans la base
status: completed
cree: 2026-10-21
mis_a_jour: 2026-10-21
source: message écrit (réponses de l'ingénieur du 21.10.2026 aux questions sur les issues #69, #70, #71, #73)
docs: [docs/domain/member-checks.md, docs/domain/loads.md, docs/ui/window.md, docs/architecture/principles.md, docs/architecture/layout.md, docs/requirements/active/2026-10-19-base-saine-nettoyage.md, docs/requirements/completed/2026-10-20-indices-et-niveaux.md]
---

# Restes de l'issue #69 — Spécification

## 1. Objectif

Fermer l'issue #69 (homogénéité des moteurs de calcul et de dessin) en faisant les trois restes que l'ingénieur avait écartés le 20.10.2026 (Q-006, Q-007 de la spec `2026-10-20-indices-et-niveaux`) et qu'il a retenus le 21.10.2026 : les lignes d'une vérification du bois construites par le moteur comme celles de tous les autres domaines ; la neige et le vent du classeur calculés par Woodcore à partir des seules entrées du classeur ; la liste des quatre toiles (Schémas, Statique, Plan et Plan feu, Polaires) tenue par la base des éditeurs.

## 2. Source

Les réponses de l'ingénieur, le 21.10.2026, à quatre questions posées dans la conversation (AskUserQuestion), mot pour mot :

> **T1** — Question « #69 : quels restes, écartés le 20.10, voulez-vous maintenant faire ? » — réponse : « Aucun, fermer #69, Vent/neige sans cellules, Onglets, partie « tout », Lignes du bois en moteur ».
>
> **T2** — Question « #71, moteur hors des projets : quelle forme ? » — réponse : « Garder la copie ».
>
> **T3** — Question « #71, graphe de dépendances : sous quelle forme ? » — réponse : « Onglet de la fenêtre, Fichier dans data/, Avertissements à l'export ».
>
> **T4** — Question « Comment mener ce travail ? » — réponse : « Une spec par sujet ».

Les options choisies, telles qu'elles étaient proposées :

> **T1a** — « Lignes du bois en moteur : member_check._row construit des lignes engine (99 appels, unfold et ~25 tests). Aucun effet visible ; la citation est déjà vérifiée aujourd'hui. »
>
> **T1b** — « Vent/neige sans cellules : Woodcore calcule lui-même μ, s_k, q_k et les c_pe/c_pi au lieu de lire ~66 cellules calculées du classeur. Des valeurs peuvent changer ; il faut des classeurs de test. »
>
> **T1c** — « Onglets, partie « tout » : reload_list, on_list_change, on_moved dans la base pour Schémas, Statique, Plan, Polaires (~150 lignes en moins). Statique et Plan demandent d'enregistrer avant de déplacer. Risque moyen (Qt). »
>
> **T1d** — « Aucun, fermer #69 : vos choix du 20.10 restent : #69 se ferme avec ces quatre restes notés comme choix assumés. »

Lecture retenue de T1 (réponses cochées ensemble) : les trois restes sont faits, puis #69 est fermée (dit à l'ingénieur le 21.10.2026). Le quatrième reste (avertissements des connecteurs et des goujons au glossaire) n'a pas été proposé et reste un choix assumé.

## 3. Exigences fonctionnelles

### REQ-001 — Neige du classeur : le classeur ne donne que les entrées
- **Exigence** : pour une feuille `SL-*`, Woodcore lit les seules entrées que l'ingénieur tape (H10 h_0, H11 correction, E14 exposition, H15 C_T, F21 forme de toit et modèle, H23/H24 dimensions ou pentes, F19 sauts de hauteur, F29 glissement) et calcule lui-même h_ref, C_e, s_k, μ_11, μ_12, μ_2m et q_k11, q_k12, q_k2m, avec les valeurs de `calc/norms/` et le même code que le chemin des sources entrées dans Woodcore (`snow_source`). Les cellules calculées du classeur (H12, H14, H17, H26, H27, K35/F66, I37 à I39, N37/N38) ne sont plus la valeur imprimée (Q-002).
- **Source** : T1b
- **Priorité** : doit
- **Critère d'acceptation** : pour les entrées d'une feuille de test (Q-004), la neige imprimée est celle que `snow_source` calcule pour ces mêmes entrées ; la provenance d'une entrée reste `excel:<classeur>!<feuille>!<cellule>`, celle d'une valeur calculée devient `python:…` ; aucun appel ne lit plus une cellule calculée pour la valeur.

### REQ-002 — Vent du classeur : le classeur ne donne que les entrées
- **Exigence** : pour une feuille `WL-*`, Woodcore lit les seules entrées (J6 q_p0, J7 à J9 b, d, h, I11 catégorie de terrain, F40 tableau des coefficients, J60 c_d, et J19/J20 selon Q-003) et calcule lui-même z, c_h, q_p, c_red, les coefficients c_pe/c_pi de l'annexe C, les forces globales et les pressions locales, avec `calc/norms/` et le code de `wind_source`. Les 56 coefficients de C78:P81, les forces J69:L70 et les forces locales F90:F98 ne sont plus la valeur imprimée.
- **Source** : T1b
- **Priorité** : doit
- **Critère d'acceptation** : pour les entrées d'une feuille de test, le vent imprimé est celui que `wind_source` calcule ; la vérification de la feuille par ses propres forces locales (`_check_against_sheet`) disparaît ou devient un avertissement (Q-002).

### REQ-003 — Les lignes d'une vérification du bois sont construites par le moteur
- **Exigence** : `member_check` construit ses lignes par `engine` (une `TimberCalculation(engine.Calculation)`, comme `SteelCalculation` pour l'acier) : une variable par ligne, citée (norme et clause, la norme toujours écrite), une étape pour une ligne qui porte une formule ; `compute()` garde son contrat (les lignes que lisent la fenêtre, `unfold`, `published_vars`, `shown_keys` et la parité `_held_equal`), projetées depuis le calcul comme `steel_tab.window_result` le fait déjà pour l'acier.
- **Source** : T1a ; base saine ARCH-002 (C1)
- **Priorité** : doit
- **Critère d'acceptation** : plus aucune ligne n'est un dict construit à la main ; chaque variable passe `engine.var` ; les fichiers dépliés du projet exemple restent identiques à l'octet (`test_unfold`) ; `checks.json` est identique à l'octet ; la parité Python/Typst reste verte.

## 4. Exigences d'interface (fenêtre, rapport, site)

### UI-001 — Déplacer une source dans un dossier : la même règle dans tous les éditeurs
- **Exigence** : glisser une ligne de la liste dans un autre dossier demande d'abord d'enregistrer un brouillon en cours, puis écrit le dossier dans chaque source ; un fichier qui ne peut être écrit (verrouillé par OneDrive, par exemple) est dit dans la barre d'état, sans arrêter la fenêtre. Vrai pour Statique et Plan (et Plan feu), qui aujourd'hui déplacent sans demander et n'attrapent pas l'erreur, et pour la base elle-même.
- **Source** : T1c
- **Langues** : fr / de / en (le message d'échec d'écriture)
- **Critère d'acceptation** : un test fait échouer l'écriture (`engine.write_json` qui lève `OSError`) dans chacun des quatre onglets et dans la base : la fenêtre ne lève pas, la barre d'état dit l'échec en dernier (un mot commun, `list_write_failed`, fr/de/en), ce qui a été écrit avant est exporté ; un brouillon modifié est enregistré avant le déplacement, et la question n'est posée que là où il ne peut pas l'être (id renommé), « Annuler » ne déplaçant rien ; le brouillon déposé dans un dossier y reste ; la source ouverte déplacée garde son nouveau dossier en mémoire (revue ARCH-RISK-1003 à 1005).

### UI-002 — Neige et vent : ce qui change dans un rapport fait d'un classeur
- **Exigence** : les valeurs que Woodcore calcule là où la feuille disait autre chose (le glissement empêché avant la moitié de N37/N38, c_red de la figure 9 au lieu de la barre de défilement selon Q-003, la règle 6.3.3 des directions obliques, les cinq cellules fausses de la feuille « Wind Tabellen Werte ») sont dites dans « Nouveautés » en fr, de et en, et, selon Q-002, à l'export.
- **Source** : T1b
- **Langues** : fr / de / en
- **Critère d'acceptation** : « Nouveautés » 0.120.0 le dit dans les trois langues ; un avertissement de l'export nomme la cellule et les deux valeurs là où Q-002 le veut.

## 5. Exigences d'architecture

### ARCH-001 — La liste des quatre toiles tenue par la base des éditeurs
- **Exigence** : Schémas, Statique, Plan (et Plan feu) et Polaires reçoivent le contrat de liste des autres éditeurs : `reload_list`, `on_list_change` et `on_moved` sont ceux de `SourceEditorTab` ; chaque toile ne dit que ce qui lui est propre par des crochets — le texte d'une ligne (« id — libellé », « id » du Plan avec son étage), les sources qu'elle liste, la ligne « Typst » du Plan. `saved_ids` n'est plus masqué par une variable du même nom.
- **Source** : T1c ; Q-007 de `2026-10-20-indices-et-niveaux` (partie « tout »)
- **Critère d'acceptation** : `test_tab_overrides` : `reload_list`, `on_list_change` et `on_moved` ne sont plus permis en redéfinition pour Schémas, Statique, Polaires ; pour le Plan, seul ce que sa vue « Typst » demande reste, avec sa raison ; `test_schema_tab`, `test_statics_tab`, `test_plan_tab_rework`, `test_polar_tab`, `test_fire_tab` verts.

### ARCH-002 — Un seul code de calcul de la neige et du vent
- **Exigence** : le chemin classeur et le chemin des sources appellent les mêmes fonctions de calcul (`snow_source`, `wind_source`, ou un module commun qu'elles appellent) ; la provenance des entrées est un paramètre, non une chaîne écrite dans le calcul.
- **Source** : T1b ; principe « une seule source de vérité »
- **Critère d'acceptation** : `snow.py` et `wind.py` ne contiennent plus de formule ; un test compare, pour les mêmes entrées, l'instance du classeur et celle de la source.

## 6. Contraintes

- **CON-001** — Les fichiers dépliés (`Timber-checks/`) et `checks.json` du projet exemple restent identiques à l'octet (REQ-003).
- **CON-002** — Les noms des variables que les sections (`.typ` des documents, `Domains/`, `Formules/`), les scripts (`.py`) et les sources de Woodcore (les `links` des vérifications, connecteurs, liaisons et charges, les magnitudes des modèles statiques, les `vars` des textes de figure) appellent aujourd'hui (`("snow-load", "SL", "q_k11")`, `mu_11`, `lastmodell`, `qk_max_bh`…) sont migrés à l'ouverture du projet vers les noms des sources, chaque fichier sauvegardé d'abord, comme les commandes (D-06) ; un nom qui n'a pas d'équivalent sûr, ou un appel que la migration ne sait pas réécrire sûrement, arrête l'export en nommant le fichier, la ligne ou le champ, et le remplaçant (revue ARCH-RISK-801 à 805).
- **CON-003** — Aucun nom de projet de l'ingénieur dans le dépôt : une fixture tirée de ses classeurs ne garde que des cellules, anonymes.
- **CON-004** — Les classeurs de l'ingénieur sont lus, jamais écrits (CLAUDE.md).
- **CON-005** — Une valeur de norme est lue sur une édition nommée : SIA 261:2020.

## 7. Décisions prises

- **D-01** — Les trois restes de #69 sont faits, puis #69 est fermée (T1, l'ingénieur, 21.10.2026 ; il revient sur Q-006 et Q-007 du 20.10.2026).
- **D-02** — Le moteur reste copié dans les projets ; #71 le note (T2).
- **D-03** — Le graphe de dépendances aura sa propre spec, sous trois formes : onglet, `data/dependencies.json`, avertissements à l'export (T3, T4).
- **D-04** — Une spec par sujet (T4) : celle-ci ne couvre que #69.
- **D-05** — Les avertissements des connecteurs et des goujons restent des phrases traduites par le glossaire (choix assumé de la base saine, non proposé le 21.10).
- **D-06** — Une feuille de neige ou de vent donne une instance de la forme des sources ; les noms qui changent sont migrés à l'ouverture dans les sections, les scripts et les documents (Q-001 : B). Renverse CON-002 : les anciens noms ne restent valables que par la migration.
- **D-07** — Une valeur de la feuille différente de celle de Woodcore est dite à l'export, cellule et deux valeurs (Q-002 : A).
- **D-08** — c_red calculé par la figure 9 et la règle 6.3.3 (Q-003 : A).
- **D-09** — Les témoins : une fixture anonyme tirée des classeurs de l'ingénieur, en lecture seule (Q-004 : A).

## 8. Hors périmètre

- Le graphe de dépendances (D-03) et le moteur hors des projets (D-02).
- Les avertissements des connecteurs et des goujons (D-05).
- La publication (installateur, site, push) : elle attend la parole de l'ingénieur.

## 9. Idées non retenues comme exigences

- Rien.

## 10. Questions

### Q-001 — Neige et vent du classeur : sous quelle forme l'instance ?
- **Pourquoi elle compte** : le chemin des sources nomme autrement ses variables et ses résultats (`q_k1` au lieu de `q_k11` pour un toit plat, `mu_1`, `dachform` au lieu de `lastmodell`, les forces `qk_max_cf33` au lieu de `qk_max_bh`, la catégorie « IV » au lieu de « IV grossflächige Stadtgebiete ») ; des sections, des scripts et des documents appellent les noms du classeur.
- **Options** :
  - **A (recommandée)** : une instance d'une feuille garde ses noms d'aujourd'hui (variables, résultats, tableaux), mais chaque valeur calculée vient du code de `snow_source`/`wind_source` ; rien à migrer, les deux formes restent.
  - **B** : une feuille donne une instance de la forme des sources ; les noms changent, et les sections et scripts sont migrés à l'ouverture (comme les commandes) ; une seule forme, mais les rapports existants changent de noms.
- **Réponse** : **B** — une feuille donne une instance de la forme des sources ; les noms changent, et les sections, les scripts et les documents qui les appellent sont migrés à l'ouverture du projet, chaque fichier sauvegardé d'abord (l'ingénieur, 21.10.2026).

### Q-002 — Quand la feuille dit autre chose que Woodcore ?
- **Options** :
  - **A (recommandée)** : Woodcore imprime sa valeur ; un avertissement de l'export nomme la cellule de la feuille et les deux valeurs, pour que le classeur soit corrigé.
  - **B** : Woodcore imprime sa valeur, sans rien dire.
  - **C** : l'export s'arrête sur la première différence.
- **Réponse** : **A** — Woodcore imprime sa valeur ; un avertissement de l'export nomme la cellule de la feuille et les deux valeurs (l'ingénieur, 21.10.2026).

### Q-003 — c_red de la feuille de vent (barres de défilement J19/J20)
- **Pourquoi elle compte** : la feuille laisse l'ingénieur choisir c_red ; la source le calcule par la figure 9 et la règle 6.3.3.
- **Options** :
  - **A (recommandée)** : calculé par la figure 9, comme pour une source ; la valeur de la feuille n'est plus lue (selon Q-002, sa différence est dite).
  - **B** : la valeur de la feuille est une entrée et Woodcore la prend.
- **Réponse** : **A** — c_red calculé par la figure 9 et la règle 6.3.3 ; J19/J20 ne sont plus lus pour la valeur (l'ingénieur, 21.10.2026).

### Q-004 — Les classeurs de test
- **Pourquoi elle compte** : aucun test ne relit aujourd'hui une feuille `SL-*` ou `WL-*` ; il faut des entrées et les valeurs recalculées par Excel comme témoins.
- **Options** :
  - **A (recommandée)** : je lis vos deux classeurs de charges déjà comparés le 20.10, en lecture seule, et j'en tire une fixture anonyme (cellules d'entrée et valeurs d'Excel, sans nom de projet ni de feuille) pour chaque forme de toit et deux feuilles de vent.
  - **B** : vous me donnez un classeur de test dédié, que je mets dans `tests/fixtures/`.
- **Réponse** : **A** — une fixture anonyme tirée, en lecture seule, des deux classeurs de charges de l'ingénieur comparés le 20.10.2026 (l'ingénieur, 21.10.2026).

## 11. Critères d'acceptation

- [x] REQ-001 — neige d'une feuille calculée par Woodcore à partir des entrées
- [x] REQ-002 — vent d'une feuille calculé par Woodcore à partir des entrées
- [x] REQ-003 — lignes du bois par le moteur, dépliés et `checks.json` identiques à l'octet
- [x] UI-001 — déplacer demande d'enregistrer et dit l'échec d'écriture, dans les quatre onglets
- [x] UI-002 — les valeurs qui changent dites dans « Nouveautés » (et à l'export selon Q-002)
- [x] ARCH-001 — liste des quatre toiles dans la base, `test_tab_overrides` resserré
- [x] ARCH-002 — un seul code de calcul de la neige et du vent
- [x] Documentation : `docs/domain/loads.md`, `member-checks.md`, `docs/ui/window.md`, `decisions.md`, `CHANGELOG.md`, « Nouveautés » fr/de/en.
- [x] Tests : suite complète verte, niveau « Rapide » vert.

## 12. Traçabilité

| Source | Élément | Statut |
|---|---|---|
| T1a | REQ-003 | capturé |
| T1b | REQ-001, REQ-002, UI-002, ARCH-002, Q-001 à Q-004 | capturé, questions |
| T1c | UI-001, ARCH-001 | capturé |
| T1d | D-01 | décision (lecture dite à l'ingénieur) |
| T2 | D-02 | décision |
| T3 | D-03 | décision, spec suivante |
| T4 | D-04 | décision |

## 13. Revue d'architecture

Trois revues indépendantes (agent `architecture-reviewer`), le 21.10.2026, une par sujet. Verdict de chacune : **APPROUVER AVEC RÉSERVES** ; toutes les réserves sont reprises dans les exigences ou le plan.

### A. Neige et vent du classeur (REQ-001, REQ-002, UI-002, ARCH-002, CON-002)

- **Modules** : `snow.py`, `wind.py` (deviennent des adaptateurs d'entrées), `snow_source.py`, `wind_source.py` (`build_instance` écrit `entered:` en dur, l.177 / 183), `registry.py` (l.160, 190, 271), `validation.py:348-401`, `schemas/calculations.schema.json`, `commands_migrate.py` (modèle de la migration), `links.py`, `statics.py:176,296`, `figure_text.py`, `script_runner.py:53-77`, `export_all.py:159,225`, `woodcore_gui.py:962`.
- **À réutiliser** : `dead_load.instance_from_layers(..., source=…)` (provenance en paramètre), `commands_migrate` (Change, commit, plan, refusal), `snow._held`, `wind._terrain`, `engine.Note` + `warn_*`, `tests/fixtures/workbook.py`.
- **ARCH-RISK-801 (bloquant)** — les noms sont aussi dans des JSON de Woodcore (`links`, magnitudes statiques, textes de figure), et un lien orphelin ne s'arrête jamais (il fige une charge) → CON-002 étendu ; parcours structuré des JSON, réécrit seulement si l'aller-retour `dumps(loads(texte)) == texte`, sinon laissé et l'export refuse.
- **ARCH-RISK-802 (bloquant)** — la table de renommage dépend de l'instance → écrite par toit et par tableau (§14, lot 3) ; neige : plat `q_k11→q_k1`, `mu_11→mu_1` ; deux pans et shed : noms identiques (la source ajoute `q_k11h`, `q_k12h`) ; `lastmodell→dachform` (la valeur devient le mot du toit) ; `hoehenspruenge` « Ja » → `hoehensprung`, « Nein » sans équivalent → refus nommé si une section l'appelle ; `korrektur` devient un nombre. Vent : `qk_{max,min}_bh|dh|db → …_cf1|cf2|cf3`, dérivé des aires du tableau (`b·h`, `d·h`, `d·b`) pour les tableaux 31 à 49 et 58 à 60b ; tableaux 50 à 57 sans 1:1 → refus nommé ; `gelaendekategorie` garde son nom, sa valeur devient « IV ». Toit et tableau lus dans le `calculations.json` précédent.
- **ARCH-RISK-803 (important)** — réécrire le Typst par appels extraits (`val`, `var-of`, `value-of`, `show-input`, clés de `shown:`), seulement quand `domain:` est un couple littéral d'une instance connue ; un `#var("q_k11", …)` propre au document n'est pas touché ; tout autre usage d'un ancien nom dans un fichier qui cite `snow-load`/`wind-load` → refus nommé.
- **ARCH-RISK-804 (important)** — un script relit `data/calculations.json` sur disque → l'export lui passe les calculs en mémoire ; `value("snow-load","SL","q_k11")` littéral détecté par le refus.
- **ARCH-RISK-805 (important)** — `commands_migrate.commit` archive par rapport à la racine Typst (plantage hors racine) → par rapport à `here.root` ; `registry.export` branché sur le refus ; commande `woodcore-cli loads migrate`.
- **ARCH-RISK-806 (important)** — cycle `snow_source → snow` (`DOMAIN`) → `DOMAIN` défini dans la source, l'adaptateur l'en tient.
- **ARCH-RISK-807 (important)** — `check_source` refuse un nom de feuille non ASCII et parle de `loads/…json` → scindé en identité et `check_fields(src, fail)`, le `fail` de l'adaptateur nommant la cellule.
- **ARCH-RISK-808 (important)** — `ENGINE` des deux domaines `excel → python` ; la feuille garde `workbook` et `sheet` ; pas de nouvelle `schema_version` (aucune clé neuve) ; `build_instance(src, here=None, inputs=None)` pour la provenance `excel:` des entrées ; décisions `decisions.md` « Snow/Wind is calculated in Excel » marquées *superseded*.
- **ARCH-RISK-809 (important)** — D-07 sans bruit : comparer les grandeurs de résultat (h_ref, s_k, μ, q_k ; q_p, c_red, les six forces, les forces locales de la sélection) ; pour les c_pe/c_pi, seulement les lignes dont l'étiquette de direction correspond, sinon un avertissement ; un seul code `sheet_value_differs`, tolérance nommée, rien si la cellule est vide.
- **ARCH-RISK-810 (important)** — l'exemple n'a pas de classeur → un classeur anonyme construit par la fixture, aux entrées de l'exemple, régénère son `calculations.json` ; l'ancien export gardé en fixture pour tester la migration ; `examples/` re-gelé et ses appels réécrits.
- **ARCH-RISK-811 (important)** — `sia261_wind.in_range` jamais appelé (c_red borné en silence hors de la figure 9) et `snow_source.warnings` (h_0 > 2000 m) lu par l'onglet seul → deux `Note` de l'export.
- **ARCH-RISK-812 (mineur)** — d'autres changements visibles (catégorie « IV », libellés de C_e de la norme, `korrektur` nombre, modèle 2 toujours imprimé, `qp` cite 6.2 (11)) → dans « Nouveautés » ; mots du glossaire devenus orphelins retirés.
- **ARCH-RISK-813 (mineur)** — `SLIDING_*`, `HEIGHT_JUMP_VALUES` tirés de la source ; `_require_one_of` dans `_common` ; `entered` ajouté à `variables.PROVENANCE`.

### B. Lignes du bois par le moteur (REQ-003, CON-001)

- **Modules** : `member_check.py` (`_row` 754, `compute` 772, `_compute` 822-859, `design()` 881, `published_vars` 1389), `engine.py`, `steel_calc.py`, `unfold.py:133-182`, `member_check_tab_form.py:313-338`, `validation._check_calculation`.
- **ARCH-RISK-901 (important)** — l'ordre de construction n'est pas l'ordre d'affichage → les listes de lignes restent, une seule inscription dans l'ordre de la liste ; comparaison avant/après de tous les genres (non commitée), seule la traction étant gardée à l'octet.
- **ARCH-RISK-902 (important)** — `keys`, `table`, `label` hors de `engine.var` → `keys` dans le calcul, la table comme vraie variable `<key>_tab` cachée de la projection, `label` note libre.
- **ARCH-RISK-903 (important)** — la projection vit dans le domaine, pas dans l'onglet (défaut de l'acier à ne pas copier).
- **ARCH-RISK-904 (important)** — le feu : concaténation des lignes puis une seule inscription.
- **ARCH-RISK-905 (important)** — garde contre une clé en double (`take` et `add_var` de la classe).
- **ARCH-RISK-906 (important)** — une seule chaîne `SOURCE = "python:domains/member_check.py"`, inchangée (octets de `checks.json`).
- **ARCH-RISK-907 (important)** — `member_check.py` à 1436 lignes pour 1500 → module neuf `calc/domains/timber_calc.py`, ajouté à `LINE_DOMAINS`.
- **ARCH-RISK-908 (important)** — `uses` dérivés de `keys` ∩ variables déclarées, après inscription ; une ligne sans `keys` : `uses=[]`.
- **ARCH-RISK-909 (important)** — `compute()` ne reçoit pas `calc` (ensemble de clés figé par un test) ; `_calculation(record)` séparé.
- **ARCH-RISK-910 à 912 (mineurs)** — `_check_citation` redondant retiré ; les deux écritures de formule (`formula`, `keys`) restent, limite notée ; nom d'étape = clé ; documentation.

### C. Listes des quatre toiles (UI-001, ARCH-001)

- **Modules** : `source_editor.py` (reload_list 233, on_list_change 261, on_moved 274), `tab_guard.py`, `schema_tab.py`, `statics_tab.py`, `drawing_tab.py` (Plan et Plan feu), `polar_tab.py`, leurs `*_build.py`/`*_panes.py`, `tab_registry.py`.
- **ARCH-RISK-1001 (bloquant)** — `export(done)` de la base ≠ `export(id, texte)` des toiles ; `DrawingTab.WORDS` est un dict → un crochet `export_moved(ids, texte)` remplace `export_schemas`, `export_models`, `export_plans` ; le dict du Plan devient `WORD_MAP`, `word()` surchargé une fois dans `DrawingTab`.
- **ARCH-RISK-1002 (important)** — `on_moved` reste un écrivain gardé, défini une seule fois (base) ; aucun crochet n'est dans `WRITERS`, aucun `super()`.
- **ARCH-RISK-1003 (important)** — un brouillon est enregistré sans question là où il peut l'être (`autosave.confirm`) → UI-001 corrigée.
- **ARCH-RISK-1004 (important)** — le dossier d'un brouillon déposé est perdu, et la source ouverte déplacée garde l'ancien dossier en mémoire (Statique, Plan) → crochets `take_group`, `draft_group`, posés avant `confirm_leave`.
- **ARCH-RISK-1005 (important)** — l'échec dit en dernier, un mot commun `list_write_failed` ; s'arrêter à la première erreur, exporter ce qui est écrit ; tests par `OSError` simulé.
- **ARCH-RISK-1006 (important)** — `reload_list(select=None)` : la base adopte le repli sur la source ouverte, le Plan garde son exception hors vue « plan » par `list_selection`.
- **ARCH-RISK-1007 (important)** — un seul drapeau `loading` ; `blockSignals` du Plan et `list_loading` de Polaires retirés.
- **ARCH-RISK-1008 (important)** — `on_list_change` : crochets `on_row_again` (ligne déjà ouverte, vue « Typst » du Plan) et `after_row_loaded`.
- **ARCH-RISK-1009, 1010 (importants)** — `saved_ids` méthode partout ; chaque toile pose `KEY` (`VIEW_KEY` du Plan renommé), `WORDS`, `sources_dir()` ; mots `sc_moved`, `polar_moved`.
- **ARCH-RISK-1011 (mineur)** — `on_folders_changed` copié quatre fois, `build_list` de Schémas, Statique et Polaires copié de la base, `PolarTab.update_buttons` mort → retirés ; `on_folders_changed` ajouté aux méthodes gardées par `test_tab_overrides`.

## 14. Plan d'implémentation

Huit lots, chacun commité avec ses tests verts ; la suite complète au dernier. Les lots 1 et 2 sont indépendants des lots 3 à 6.

**Lot 0 — Garde-fous d'abord**
1. Comparaison avant/après de `member_check.compute` (ancien code chargé depuis `HEAD` sous un autre nom) sur une matrice de tous les genres (α 0, 45, 90 ; N signé ; rond et rectangle ; massif et lamellé-collé ; feu ; moelle), gardée dans le scratchpad, non commitée (ARCH-RISK-901).
2. La fixture anonyme `tests/fixtures/load-sheets-reference.json` (D-09) : entrées et valeurs d'Excel de quatre feuilles de neige et cinq de vent, tirées en lecture seule des classeurs de l'ingénieur, noms remplacés, h_0 arrondi ; l'ancien `calculations.json` de l'exemple gardé en `tests/fixtures/calculations-before-loads.json`.

**Lot 1 — Lignes du bois par le moteur** (REQ-003, CON-001, ARCH-RISK-901 à 912)
- `calc/domains/timber_calc.py` : `NORM`, `SOURCE`, `Line`, `line()` (ex-`_row`), `TimberCalculation(engine.Calculation)` (`keys`, `tables`, `take`, `rows`, garde de doublon) ; `member_check` l'importe (`line as _row`), `_calculation(record)` séparé de `_compute`, `published_vars` lit `SOURCE`.
- Tests : `tests/test_timber_calc.py` (neuf), `test_member_check`, `test_unfold` (octets), `test_domain_contracts`, `test_member_check_tab`, `test_line_levels` (`timber_calc` dans `LINE_DOMAINS`) ; la comparaison du lot 0 identique.

**Lot 2 — Liste des quatre toiles dans la base** (UI-001, ARCH-001, ARCH-RISK-1001 à 1011)
- `source_editor.py` : `ids` de classe ; crochets `listed`, `list_selection`, `on_row_again`, `after_row_loaded`, `take_group`, `draft_group`, `show_empty_hint`, `export_moved` ; `on_moved` écrit avant `confirm_leave` le dossier du brouillon, s'arrête à la première `OSError`, exporte ce qui est écrit, dit l'échec en dernier (`list_write_failed`, fr/de/en dans `woodcore_gui_words.py`).
- Schémas, Statique, Polaires, `DrawingTab` (Plan, Plan feu) : `KEY`, `WORDS`, `sources_dir()`, `listed()`, `export_moved` ; retrait de leurs `reload_list`, `on_list_change`, `on_moved`, `on_folders_changed`, `build_list` copiés, de `list_loading`, `update_buttons`, des `saved_ids` d'instance ; `WORD_MAP` du Plan.
- Tests : `test_tab_overrides` resserré (seul `DrawingTab.confirm_leave` permis des quatre), un test d'écriture qui échoue et de brouillon déposé dans chaque onglet (`test_schema_tab`, `test_statics`, `test_plan_tab_rework`, `test_fire_tab`, `test_polar_tab`, `test_member_check_tab` pour la base), `test_autosave`, `test_i18n`.

**Lot 3 — La table de renommage et les adaptateurs de la neige et du vent** (REQ-001, REQ-002, ARCH-002, D-08)
- `DOMAIN` dans les sources (cycle) ; `check_source` scindé (`check_fields(src, fail)`) ; `build_instance(src, here=None, inputs=None)` ; `snow.py` et `wind.py` lisent les entrées (avec leur cellule), appellent `build_instance`, `ENGINE = "python"` ; c_red par la figure 9 ; H24 vide d'une feuille à deux pans : 0°, comme le classeur (F65), dit par une `Note`.
- `calc/domains/loads_names.py` : la table unique (toit / tableau → ancien nom, nouveau nom, cellule), lue par le contrôle D-07 et par la migration.
- Tests : `tests/test_load_sheets.py` (neuf) — égalité feuille/source pour les mêmes entrées, provenance `excel:`/`python:`, aucune cellule calculée lue (espion), arrêt nommant la cellule d'une entrée invalide, F40 hors tableaux ; `test_snow_source`, `test_wind_source` (id non ASCII).

**Lot 4 — Les écarts de la feuille et les deux avertissements oubliés** (UI-002, D-07, ARCH-RISK-809, 811)
- Un code `sheet_value_differs` (feuille, cellule, valeur Excel, valeur Woodcore), tolérance nommée, rien si la cellule est vide ; c_pe/c_pi seulement par direction correspondante ; `in_range` de la figure 9 et h_0 > 2000 m en `Note` (feuille et source) ; `wind_surfaces_unchecked` retiré avec `_check_against_sheet`. Mots fr/de/en.
- Tests : `test_load_sheets` (avertissements sur la fixture, plafond de bruit), `test_domain_contracts`, `test_i18n`.

**Lot 5 — La migration des noms** (CON-002, D-06, ARCH-RISK-801 à 805)
- `calc/domains/loads_migrate.py` (`plan`, `commit`, `migrate`, `refusal`) sur le modèle de `commands_migrate` : `.typ` par appels extraits, `.py` à littéraux, JSON de sources par parcours structuré avec garde d'aller-retour ; toit et tableau lus dans le `calculations.json` précédent ; branché à l'ouverture (`woodcore_gui.py`), au refus d'export (`export_all.py`), à `registry.export`, et `woodcore-cli loads migrate`.
- `commands_migrate.commit` archive par rapport à `here.root` ; l'export passe les calculs en mémoire aux scripts (`script_runner`).
- Tests : `tests/test_loads_migrate.py` (neuf) — chaque forme Typst, `#var` propre au document intact, non-résolu qui refuse, idempotence, archives d'abord, liens, magnitudes, textes de figure, scripts, fichier hors racine Typst ; `test_script`, `test_commands_migrate`.

**Lot 6 — L'exemple et les exemples** (ARCH-RISK-810, 812, 813)
- Un classeur anonyme construit par `tests/fixtures/workbook.py` aux entrées de l'exemple régénère `calculations.json` du projet exemple ; ses sections migrées par la migration elle-même ; `examples/` re-gelé, appels et `///` réécrits (`commands.json` si le texte change) ; mots du glossaire orphelins retirés ; `variables.PROVENANCE` reçoit `entered` ; `SLIDING_*` tirés de la source, `_require_one_of` dans `_common`.
- Tests : `test_formula`, `test_display_view`, `test_command_review`, `test_document_commands`, `test_variable_sources`, `test_variables`, `test_line_levels`, `test_commands`, `test_no_duplicates` (baseline resserrée).

**Lot 7 — Documentation et clôture**
- `docs/domain/loads.md` (§3.3bis, §3.3quater, §3.3sexies-bis), `calculation-domains.md`, `member-checks.md`, `docs/ui/window.md`, `docs/architecture/principles.md` (règle de la neige), `layout.md` (`timber_calc.py`, `loads_names.py`, `loads_migrate.py`), `decisions.md` §13 (décisions « Snow/Wind is calculated in Excel » *superseded* ; la liste des toiles dans la base ; les lignes du bois), `CHANGELOG.md`, « Nouveautés » 0.120.0 fr/de/en (valeurs qui changent, noms migrés, Tinymist entre l'ouverture et l'export, déplacer enregistre d'abord), catalogue des tests.
- Vérification indépendante, puis `finish` : suite complète, commit, une question avant de pousser, #69 fermée avec un commentaire.

## 15. Vérification

Agent `requirements-verifier`, 21.10.2026, base 47c5fac, sur l'arbre de travail ; deux points ❌/⚠️ corrigés puis repris (ronde 2, par l'implémenteur, tests relancés).

| Élément | Verdict | Preuve |
|---|---|---|
| REQ-001 neige | ✅ | `snow.py` lit les seules entrées (`CELLS`) et calcule par `snow_source.build_instance(inputs=)` ; `test_load_sheets` : instance égale au calcul de la source, s_k et h_ref égaux à Excel à 1e-9, espion « entrées seulement » |
| REQ-002 vent | ✅ | `wind.py` : J6-J9, I11, F40, J60 ; c_red de la figure 9 ; `test_load_sheets` (4 feuilles, c_red hors figure 9) |
| REQ-003 lignes du bois | ✅ | `timber_calc.py` ; `test_timber_calc` 4, `test_unfold` 21 (octets), `test_member_check` 87 (parité) |
| UI-001 déplacer | ✅ | `source_editor.on_moved` ; `test_list_moves` 4 dans Schémas, Statique, Plan, Plan feu, Polaires et la base : échec d'écriture dit en dernier, brouillon enregistré d'abord, brouillon déposé gardé, « Annuler » ne déplace rien (ronde 2) |
| UI-002 Nouveautés et export | ✅ | « Nouveautés » 0.120.0 fr/de/en : c_red de la figure 9, règle 6.3.3, cinq cellules de « Wind Tabellen Werte », moitié de N37/N38 (ronde 2) ; `sheet_value_differs` pour une charge de neige et une force de vent (ronde 2) |
| ARCH-001 | ✅ | aucune méthode de liste copiée dans les quatre toiles ; `test_tab_overrides` resserré |
| ARCH-002 | ✅ | `snow.py`, `wind.py` sans formule ; égalité feuille/source testée |
| CON-001 | ✅ | `test_unfold`, `checks.json` inchangé |
| CON-002 migration | ✅ | `loads_migrate.py` branché à l'ouverture, à l'export, à `registry.export`, à `woodcore-cli loads migrate` ; `test_loads_migrate` 5 (le test d'archivage recalé sur un script qui lit encore l'ancien nom, ronde 2 ; `vars` d'un texte de figure testés) |
| CON-003 à CON-005 | ✅ | fixture anonyme ; aucun écrivain de classeur ; valeurs de `calc/norms/` |
| Documentation | ✅ | docs/, `decisions.md` et index, CHANGELOG, « Nouveautés », catalogue ; `test_docs_coherence` 7 |
| Hors périmètre §8 | ✅ | rien du graphe, du moteur, des goujons, de la publication |

Notes sans suite : la fixture tient 3 feuilles de neige et 4 de vent (les doublons des classeurs retirés), qui couvrent les trois toits du classeur et trois tableaux ; le Plan garde des `blockSignals` pour changer de vue, hors de la liste.

## 16. Journal d'avancement

| Date | Statut | Fait / reste |
|---|---|---|
| 2026-10-21 | draft | spécification extraite des réponses de l'ingénieur ; code lu (chemin classeur de la neige et du vent, lecteurs des lignes du bois, contrat de liste des éditeurs) ; quatre questions |
| 2026-10-21 | specified | réponses : Q-001 B (forme des sources, migration à l'ouverture), Q-002 A, Q-003 A, Q-004 A ; D-06 à D-09 |
| 2026-10-21 | reviewed | trois revues d'architecture (APPROUVER AVEC RÉSERVES), réserves reprises (§13, UI-001 et CON-002 corrigées) ; plan en huit lots (§14) |
| 2026-10-21 | approved | l'ingénieur approuve la spec et le plan (« Approuver et implémenter ») |
| 2026-10-21 | implementation | lot 0 commencé |
| 2026-10-21 | implementation | lot 0 : instantané avant/après de `member_check` (62 enregistrements de `test_member_check`, `compute`, `shown_keys`, `shown_choices`, `published_vars`, `form_of`) gardé dans le scratchpad |
| 2026-10-21 | implementation | lot 1 fait : `calc/domains/timber_calc.py` (`line`, `Line`, `TimberCalculation`, projection `rows()`), `member_check._lines`/`_calculation`/`_compute`, `SOURCE` unique ; instantané identique à l'octet ; `tests/test_timber_calc.py`, `timber_calc` dans `LINE_DOMAINS` ; 287 tests liés verts — REQ-003 |
| 2026-10-21 | implementation | lot 2 fait : liste des quatre toiles dans `SourceEditorTab` (crochets `listed`, `draft_text`, `draft_group`, `take_group`, `list_selection`, `show_empty_hint`, `on_row_again`, `after_row_loaded`, `export_listed`), `on_moved` enregistre d'abord, s'arrête à la première `OSError`, dit `list_write_failed` en dernier ; copies retirées ; `tests/test_list_moves.py` (5 onglets), `test_tab_overrides` resserré ; 445 + 76 tests liés verts — UI-001, ARCH-001 |
| 2026-10-21 | implementation | lots 3 et 4 faits : `snow.py`/`wind.py` lisent les entrées (`read_source`, `check_fields`), calculent par `build_instance(inputs=)`, `ENGINE = "python"` ; `loads_names.py` ; écarts `sheet_value_differs`, `snow_above_limit`, `wind_c_red_outside`, `sheet_slope_empty`, `sheet_direction_unknown` (fr/de/en) ; fixture `load-sheets-reference.json` (3 feuilles de neige, 4 de vent, anonymes) ; `tests/test_load_sheets.py` 7 verts — REQ-001, REQ-002, UI-002, ARCH-002 |
| 2026-10-21 | implementation | lot 5 fait : `loads_migrate.py` (Typst par appels, scripts, liens JSON, garde d'octets, refus nommé), ouverture (`woodcore_gui`), refus (`export_all`, `registry.export`), `woodcore-cli loads migrate`, scripts lisant les calculs en mémoire, `commands_migrate.commit` hors racine Typst ; `tests/test_loads_migrate.py` 5 verts — CON-002 |
| 2026-10-21 | implementation | lot 6 fait : `calculations.json` de l'exemple recalculé par les nouveaux lecteurs (classeur anonyme), ancien export gardé en fixture ; exemples `///` de `lib/` et `examples/` re-gelés (497) ; tests à noms migrés ; base des doublons resserrée ; niveau « Rapide » 1163 verts |
| 2026-10-21 | testing | lot 7 : `docs/` (loads §3.3bis, §3.3quater, §3.3sexies-bis, principles, layout, calculation-domains, member-checks, window), `decisions.md` et son index, `CHANGELOG.md`, « Nouveautés » 0.120.0 fr/de/en, catalogue des tests ; suite complète lancée |
| 2026-10-21 | verification | vérification indépendante : CON-002 ❌ (test d'archivage), UI-001, UI-002 ⚠️ ; corrigés (test recalé, « Annuler » et Plan feu testés, force de vent, Nouveautés complétées) ; suite complète 3097 passés, les 5 rouges de la première ronde réparés |
| 2026-10-21 | completed | spec close, déplacée dans `completed/` |
