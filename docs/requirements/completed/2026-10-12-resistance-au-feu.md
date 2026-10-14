---
id: 2026-10-12-resistance-au-feu
titre: Onglet « Résistance au feu » — flexion et flambement au feu (SIA 265 4.5), exigence R de l'AEAI 15-15
status: completed
cree: 2026-10-12
mis_a_jour: 2026-10-12
source: issue GitHub #46 (« Résistance au feu »), elle-même tirée de la demande /issue du 2026-10-12 et des réponses de l'ingénieur
docs: [docs/domain/member-checks.md, docs/ui/tab-member-checks.md, docs/domain/fire-plans.md, docs/ui/tab-fire-plan.md, docs/architecture/principles.md]
---

# Onglet « Résistance au feu » — Spécification

## 1. Objectif

L'ingénieur veut vérifier dans Woodcore la résistance au feu des barres en bois (flexion et flambement), comme le font aujourd'hui les classeurs de référence. Les vérifications seraient enregistrées, imprimées dans le rapport et rattachées aux exigences de protection incendie de l'AEAI : la durée R exigée et le plan de protection incendie. L'acier est repoussé à plus tard.

## 2. Source

Demande /issue du 2026-10-12 (mot pour mot) :

> **T1** — « ajoute un onglet de calcul de résistance au feu d'après le classeur de référence: »
>
> **T2** — « * «fire, bending» template »
>
> **T3** — « * «fire, buckling» template »
>
> **T4** — « * «fire, steel profile» template »
>
> **T5** — « Compare également que cela joue avec les normes VKF (AEIAI) C:\Users\Quebec\001-NextCloud\001-Documents\003-Etudes\005-BFH_Ba_Holztechnik\301-Normes »

Réponses de l'ingénieur aux questions de /issue (2026-10-12) :

> **T6** — Placement : « Onglet séparé »
>
> **T7** — Méthode : « la lignum dok 3.1 est en fait similaire à la documentation officielle AEAI. Vérifie avec elle »
>
> **T8** — Acier : « Plus tard »
>
> **T9** — Portée de la comparaison AEAI : « Méthode et valeurs, Exigence R requise, Lien au plan feu »

## 3. Exigences fonctionnelles

### REQ-001 — Flexion au feu
- **Exigence** : Woodcore doit vérifier une barre rectangulaire en flexion (avec l'effort tranchant) dans la situation de projet incendie, selon SIA 265:2021 4.5.2. Il calcule la section résiduelle idéale : d_char,n = β_n · t (50), d_ef = d_char,n + d_red (49), d_red = 7 mm jusqu'à 90 min, sur les faces exposées. Il applique ensuite les vérifications à température normale (4.2.3, 4.2.5) avec E_d,fi ⩽ R_d,fi (48) et R_d,fi = 1.8 · R_d (51), R_d étant la résistance de la section résiduelle à température normale (Q-001). Ni k_h ni k_sys (4.5.2.5).
- **Source** : T1, T2
- **Priorité** : doit
- **Critère d'acceptation** : le cas du classeur Biegung (C24, b 140, h 200, R60, 3 faces, q_d,fi 1.9375 kN/m, l 5 m) redonne b_fi 30, h_fi 145, W_y,fi 105 125 mm³, M_d,fi 6.055 kNm, σ_m,d,fi 57.6 N/mm² et un taux de 2.27 (méthode 1.8), à 1e-3 près. Un test le prouve.

### REQ-002 — Flambement au feu
- **Exigence** : Woodcore doit vérifier une barre comprimée au flambement dans la situation de projet incendie (4.5.2 avec 4.2.8), sur la section résiduelle : élancement, λ_rel et k_c de la section résiduelle, puis R_d,fi = 1.8 · R_d (Q-001).
- **Source** : T1, T3
- **Priorité** : doit
- **Critère d'acceptation** : le cas « 4 seitiger Abbrand » du classeur Knicken (D30, b 140, h 240, l 2.4 m, R30, 4 faces, N_d,fi 185 kN) redonne b_fi 96, h_fi 196, λ 86.6, λ_rel 1.408, k_c 0.4226. Le taux est celui de 1.8 · k_c · f_c,0,d · A_fi (Q-001) ; l'écart avec le 0.775 du classeur (k_fi · f_k) est consigné en REQ-008. Un test le prouve.

### REQ-003 — Vitesse de combustion et faces exposées
- **Exigence** : Woodcore doit lire β_n dans SIA 265:2021 Tabelle 13. Le choix de la ligne se fait selon le bois : résineux ou hêtre, massif 0.8 ; BLC 0.7 ; chêne ou robinier 0.5 ; revêtement en bois massif 0.9. Un résineux ou un BLC se déduit de la classe de résistance (Tabelle 8/9 `species`) ; un feuillu demande l'essence (hêtre ou chêne/robinier). Les faces exposées sont quatre cases, dessous, dessus, gauche et droite (Q-009) : b_fi = b − n_côtés · d_ef et h_fi = h − n_(dessus+dessous) · d_ef.
- **Source** : T2, T3 (inféré de SIA 265 4.5.2.3)
- **Priorité** : doit
- **Critère d'acceptation** : `calc/norms/sia265-2021-4.5-brandfall.json` (un seul fichier pour Tabelle 13 et la clause 4.5.2, selon §13 ARCH-RISK-006) existe, cite son édition et ses pages, et n'est lu que par `calc/norms/sia265.py` et, côté rapport, par `lib/timber.typ`. Un feuillu sans essence rend la vérification non calculable, avec sa raison.

### REQ-004 — Largeur minimale (4.5.2.4)
- **Exigence** : pour une exposition sur plusieurs faces, Woodcore doit refuser une largeur b < 80 mm pour R30 et b < 140 mm pour R60. La vérification devient non calculable, avec la raison et la clause. Une durée au-delà de 90 min (d_red non fixé par 4.5.2.2) est non calculable de même.
- **Source** : T5, T9 « Méthode et valeurs » (inféré de SIA 265 4.5.2.4)
- **Priorité** : doit
- **Critère d'acceptation** : un test montre b 120 / R60 / 3 faces → `calculable: false`, raison citant 4.5.2.4.

### REQ-005 — Effet des actions en situation d'incendie
- **Exigence** : Woodcore doit prendre l'effet des actions au feu tel que l'ingénieur le saisit (Q-005) : M_y,d,fi, M_z,d,fi, V_z,d,fi, V_y,d,fi pour la flexion, N_d,fi pour le flambement, la compression et la traction. Chaque champ est liable à une variable (issue #42). Ni 0.6 · E_d ni combinaison de charges dans l'onglet.
- **Source** : T2, T3, Q-005
- **Priorité** : doit
- **Critère d'acceptation** : le formulaire porte ces champs et `member_check.LINKABLE` les contient ; un test enregistre une flexion au feu avec V_z lié.

### REQ-006 — Exigence R tirée de l'AEAI 15-15
- **Exigence** : Woodcore doit proposer la résistance exigée du système porteur (R 30, R 60, R 90, R 120 ou aucune) selon la directive AEAI 15-15, tableaux 1 à 3 et notes [1], [5], [8], [9]. Les entrées sont saisies une fois par projet (Q-007) : la catégorie de hauteur, l'affectation, le concept (construction ou installation d'extinction) et la note [5] (deux niveaux, ≤ 2400 m²). Chaque vérification ajoute « dernier niveau » (notes [1], [8]). La durée t en découle ; chaque vérification peut l'écrire par-dessus, en orange avec « Reprendre ».
- **Source** : T5, T9 « Exigence R requise »
- **Priorité** : doit
- **Critère d'acceptation** : `calc/norms/vkf-2017-3.7.1-15-15-tragwerk.json` (nom du plan §14) transcrit les tableaux 1 à 3 depuis `VKF-AEAI-15-15-…pdf`, pages 12 à 15. Un test redonne au moins : habitation, faible hauteur, construction → R 30 ; moyenne hauteur → R 60 ; élevé → R 90 ; industrie > 1000 MJ/m², moyenne hauteur, installation d'extinction → R 60.

### REQ-007 — Lien au plan de protection incendie : par la position
- **Exigence** : une vérification au feu nomme sa position comme les autres vérifications ; la position est le lien avec les plans (le plan feu suit le plan de positions où elle est dessinée). Le plan feu et son schéma ne changent pas (Q-008).
- **Source** : T9 « Lien au plan feu », Q-008
- **Priorité** : doit
- **Critère d'acceptation** : la vérification porte `position` ; le rapport imprime la ligne de la position ; `schemas/fire-source.schema.json` est inchangé (diff vide).

### REQ-008 — Comparaison avec l'AEAI et les classeurs, écrite
- **Exigence** : la méthode et les valeurs de Woodcore doivent être comparées à celles des deux classeurs et aux documents AEAI. Chaque écart est consigné avec sa source dans `docs/domain/fire-resistance.md` : β_n, d_red, largeur minimale, facteur 1.8 ou k_fi, ψ₂, 0.6.
- **Source** : T5, T7, T9 « Méthode et valeurs »
- **Priorité** : doit
- **Critère d'acceptation** : la section « Comparaison » de `docs/domain/fire-resistance.md` liste chaque grandeur avec sa valeur dans SIA 265:2021, dans chaque classeur et dans l'AEAI. Les écarts relevés en §9bis y figurent.

### REQ-009 — Vérifications enregistrées et rapport
- **Exigence** : une vérification au feu doit être un objet avec un ID, enregistré dans le projet (forme : §10 Q-003). Elle est exportée par *Import données*, résolue contre les positions (section, classe, classe d'humidité suivent la position ou sont écrites par-dessus, comme les autres vérifications), puis imprimée par une commande Typst (forme : §10 Q-004) aux niveaux -1 à 3.
- **Source** : T1, T6 (inféré de §3.3unvicies)
- **Priorité** : doit
- **Critère d'acceptation** : un projet d'exemple porte une flexion et un flambement au feu. Le rapport compile et imprime la section résiduelle, la clause et le verdict. Python (fenêtre) et Typst (rapport) donnent le même η à 1e-6 près, sur tous les cas du test.

## 4. Exigences d'interface (fenêtre, rapport, site)

### UI-001 — Onglet séparé « Résistance au feu »
- **Exigence** : un onglet « Résistance au feu » (de : « Feuerwiderstand », en : « Fire resistance ») dans le groupe « Sécurité structurale », avec une icône à lui, dans le Rapport de statique seulement. Il a les trois volets des vérifications (liste, formulaire en cartes, résultat Python instantané) et les vues Calcul · Affichage. Le formulaire porte : la durée R et sa provenance (AEAI 15-15 ou écrite), les faces exposées, le bois pour β_n, puis les efforts de la vérification.
- **Source** : T1, T6
- **Langues** : fr / de / en
- **Critère d'acceptation** : `tests/test_chrome.py` trouve l'onglet dans `NAV_GROUPS`. Un test hors écran crée, enregistre et recharge une vérification de chaque genre. Chaque chaîne existe dans les trois langues (`tests/test_i18n*`).

### UI-002 — Données du bâtiment pour l'exigence R
- **Exigence** : une carte « Bâtiment (AEAI 15-15) » de l'onglet saisit, une fois pour le projet, la catégorie de hauteur, l'affectation, le concept et la note [5]. Elle les écrit dans un fichier du projet à lui, versionné. Chaque vérification affiche la durée R qui en découle, avec le tableau et la ligne ; une durée écrite par-dessus est orange, avec « Reprendre ».
- **Source** : T9
- **Langues** : fr / de / en (termes de l'AEAI en français et en allemand ; l'allemand est à vérifier, issue #34)
- **Critère d'acceptation** : un test hors écran change l'affectation et voit la durée d'une vérification qui suit changer, et celle d'une vérification écrite par-dessus rester.

## 5. Exigences d'architecture

### ARCH-001 — Le calcul reste dans `calc/domains/`, sans Qt
- **Exigence** : section résiduelle, β_n, d_ef, résistance au feu et taux sont calculés dans un module de domaine. L'onglet affiche et appelle, ne recalcule rien.
- **Source** : principes (CLAUDE.md, « Domain logic is independent of the UI »)
- **Critère d'acceptation** : aucun import Qt dans le module de domaine (`tests/test_architecture*` ou grep dans un test).

### ARCH-002 — Valeurs de norme dans `calc/norms/` seulement
- **Exigence** : β_n (Tabelle 13), d_red, largeurs minimales (4.5.2.4), 1.8 (4.5.2.5), 0.6 (4.5.2.2), k_fi s'il est retenu (EN 1995-1-2 2.3) et les tableaux AEAI 15-15 sont transcrits une fois chacun dans `calc/norms/*.json`, avec `_source` (édition, page). Python et Typst les lisent là.
- **Source** : principes règles 1, 13
- **Critère d'acceptation** : un grep des valeurs 0.7, 1.8, 140 dans le module du domaine et dans `lib/` ne trouve que des lectures de fichiers de norme (test de non-codage en dur, comme `test_theme.py`).

### ARCH-003 — Contrat versionné
- **Exigence** : la forme enregistrée (§10 Q-003) et l'export ont un schéma `schemas/*.schema.json` avec `schema_version`. Si les vérifications existantes sont étendues, les champs sont additifs et la version est montée selon la règle du projet. La validation métier précède l'écriture.
- **Source** : principes règles 8, 10
- **Critère d'acceptation** : les schémas valident les fichiers de l'exemple ; un fichier malformé arrête l'export en nommant le fichier et le champ (test).

### ARCH-004 — Python et Typst tenus égaux
- **Exigence** : comme pour les vérifications existantes (§3.3unvicies), le calcul instantané de la fenêtre et celui du rapport sont tenus égaux par un test qui compile les cas au niveau 0 et relit le registre.
- **Source** : décision de l'ingénieur du 07.10.2026 (§3.3unvicies), inférée
- **Critère d'acceptation** : `tests/test_fire_check*.py` compile au moins 8 cas (2 genres × faces × méthode) et compare chaque valeur à 1e-6 près.

## 6. Contraintes

- **CON-001** — Méthode de SIA 265:2021 4.5 (édition de la bibliothèque, `ExternalFiles/000-Normes/SIA265-2021-DE.pdf`, p. 38–40) ; les classeurs sont des oracles, pas des sources (règle 13). Source : T7, principes.
- **CON-002** — Les vérifications existantes (fichiers `checks/*.json`, `data/checks.json`, commandes `verify-*`) ne changent pas d'un octet pour un projet sans vérification au feu. Inféré.
- **CON-003** — Trois langues de, fr, en pour toute chaîne visible ; toute commande Typst nouvelle a son bloc `///`, deux exemples qui compilent et sa traduction dans `calc/i18n/commands.json` (règle 14). Inféré.
- **CON-004** — Documentation : `docs/domain/fire-resistance.md` (nouveau, < 100 KB), `docs/ui/tab-fire-resistance.md`, `docs/README.md`, `CHANGELOG.md`, page « Nouveautés » fr/de/en. Inféré (CLAUDE.md).
- **CON-005** — Rien n'est écrit dans les projets de l'ingénieur ; les tests travaillent sur `tests/projet-exemple/`. CLAUDE.md.

## 7. Décisions prises

- **D-01 (T6, 2026-10-12)** — Un onglet séparé « Résistance au feu », pas une vue des onglets de vérification. Prix accepté : la section, le matériau et les efforts sont saisis à nouveau (ou suivent la position).
- **D-02 (T8, 2026-10-12)** — L'acier («fire, steel profile» template) est repoussé ; EN 1993-1-2 manque dans la bibliothèque.
- **D-03 (T9, 2026-10-12)** — La comparaison AEAI couvre trois choses : la méthode et les valeurs, l'exigence R requise et le lien au plan feu.
- **D-04 (Q-001)** — R_d,fi = 1.8 · R_d (SIA 265:2021 4.5.2.5) ; la route k_fi · f_k du classeur Knicken n'est pas reprise. Prix : le flambement au feu donne ~15 % de résistance de moins que ce classeur.
- **D-05 (Q-002)** — La Lignum 3.1 « contient les normes AEAI » : la comparaison se fait contre les directives AEAI de la bibliothèque et SIA 265 4.5.
- **D-06 (Q-003, revue par Q-010)** — Stockage dans `checks/<id>.json`. **Les genres existants gardent leur nom** (`bending`, `shear`, `buckling`, `compression`, `tension`) ; un objet `fire` additif fait d'une vérification une vérification au feu (réponse à Q-010, 2026-10-12, sur proposition de la revue ARCH-RISK-004). La flexion et l'effort tranchant sont deux vérifications, comme à froid. Prix : les schémas des vérifications montent en 1.2 ; les six onglets existants excluent les sources qui portent `fire`.
- **D-07 (Q-004)** — `#member(…, fire: (…))` donne la barre résiduelle et les `verify-*` existants la vérifient au feu.
- **D-08 (Q-005)** — Efforts au feu saisis directement ; pas de 0.6 · E_d ni de combinaison de charges.
- **D-09 (Q-006)** — Flexion avec effort tranchant, flambement, compression et traction de la section seule ; pas de déversement au feu.
- **D-10 (Q-007)** — Données du bâtiment une fois par projet ; durée écrasable par vérification.
- **D-11 (Q-008)** — Le lien au plan feu est la position ; le plan feu ne change pas.
- **D-12 (Q-009)** — Quatre cases pour les faces exposées.

## 8. Hors périmètre

- Profilés en acier au feu (D-02) — reste un point ouvert de l'issue #46.
- Éléments initialement protégés (revêtement), assemblages au feu (4.5.3), éléments composites (4.5.4) : SIA 265 renvoie à la Lignum-Dokumentation Brandschutz 3.1, qui n'est pas dans la bibliothèque.
- Le classeur « Nachweis brandabschnittsbildende Funktion n. Lignum 3.1 » (EI des compartiments), non demandé.
- Sections rondes, panneaux, CLT : non demandés ; refusés comme « non calculable » avec raison.
- Déversement au feu (D-09) ; 0.6 · E_d et combinaison de charges dans l'onglet (D-08) ; marquage des vérifications sur le plan feu (D-11).
- La résistance du classeur Knicken (k_fi · f_k) : il sert d'oracle de géométrie, d'élancement et de k_c seulement (D-04).

## 9. Idées non retenues comme exigences

- Aucune dans la source.

### 9bis. Constats faits en lisant les sources (pour REQ-008)

- **Les directives AEAI de la bibliothèque ne contiennent aucune méthode de calcul du bois** : l'ingénieur dit que la Lignum 3.1 les contient (D-05) ; la comparaison porte donc sur ce qu'elles fixent, l'exigence R et les classes. L'AEAI 15-15 §4.1 exige que la résistance au feu soit « démontrée par le calcul, sur la base de la courbe normalisée, ou par des essais ». Ses §5, comme ceux de 13-15 et 14-15, renvoient aux « documents fixant l'état de la technique » reconnus par l'AEAI ; la Lignum-Dokumentation Brandschutz 3.1 en est un. Les valeurs à comparer sont donc celles de SIA 265 4.5 (qui renvoie elle-même à Lignum 3.1 pour le protégé et les assemblages), et l'AEAI ne fournit que l'exigence R.
- **La Lignum Dok. 3.1 n'est pas dans la bibliothèque** (ni `000-Normes`, ni `301-Normes/Litteratur`, ni le dossier `111-Resistance-REI-CompartimentsCoupeFeu`).
- **Le classeur Biegung** cite « SIA 265 Tabelle 9 (S. 31) » et « 4.5.2.5 (S. 35) », une édition antérieure ; en 2021, c'est Tabelle 13, p. 39 et 4.5.2.5, p. 40. Les valeurs de β_n concordent (C24 0.8, GL 0.7, Eiche 0.5, Buche 0.8). La largeur minimale affichée (F11) vient d'un lien externe `[1]Hilfswerte!E38` et vaut 80 pour R60, où 4.5.2.4 exige 140. La valeur f_v,k = 1.7 · f_v,d de la colonne « k_fi » est une estimation et non une valeur de la norme.
- **Le classeur Knicken** n'utilise pas 1.8 · R_d (SIA 265 4.5.2.5) mais f_d,fi = k_fi · f_k (EN 1995-1-2 2.3, k_fi 1.25 massif / 1.15 BLC, « Lignum 3.1 S.22 3.2.3 (7) »). Pour C24 : 1.25 · 21 = 26.25 contre 1.8 · 12.4 = 22.3 N/mm², soit 18 % de plus.
- **E_d,fi** : le classeur Biegung écrit G_k + ψ₂ · Q_k + ψ₂,s · S_k (SIA 260 4.4.3.5). Le classeur Knicken propose 0.6 · E_d, que SIA 265 4.5.2.2 n'admet que pour les catégories A et B, ce que le classeur ne restreint pas.

## 10. Questions

### Q-001 — Résistance au feu : 1.8 · R_d (SIA 265) ou k_fi · f_k (Knicken / EN 1995-1-2) ?
- **Pourquoi elle compte** : à section égale, le taux diffère de 15 à 20 % ; c'est le calcul lui-même.
- **Options** : A (recommandée) SIA 265:2021 4.5.2.5, R_d,fi = 1.8 · R_d, la norme suisse et l'édition de la bibliothèque ; B k_fi · f_k d'EN 1995-1-2 (la route du classeur Knicken) ; C les deux côte à côte, comme le classeur Biegung, le verdict sur A.
- **Réponse** : A — SIA 265:2021 4.5.2.5, R_d,fi = 1.8 · R_d (ingénieur, 2026-10-12). Le classeur Knicken sert d'oracle pour la géométrie, λ_rel et k_c, et sa résistance est notée comme écart.

### Q-002 — Lignum Dok. 3.1 pour « vérifier avec elle »
- **Pourquoi elle compte** : la règle 13 interdit une valeur lue ailleurs que dans une édition de la bibliothèque, et la Lignum 3.1 n'y est pas.
- **Options** : A (recommandée) tu déposes la Lignum 3.1 dans `000-Normes/Litteratur/` et la comparaison la cite ; B la comparaison se fait contre SIA 265 4.5 et EN 1995-1-2 seules, et la Lignum 3.1 est notée « non vérifiée ».
- **Réponse** : « La lignum 3.1 contient en fait les normes VKF-AEAI auxquelles tu as accès » (2026-10-12) : la comparaison se fait contre les directives AEAI de la bibliothèque et SIA 265 4.5, sans le PDF de la Lignum.

### Q-003 — Où s'enregistre une vérification au feu ?
- **Pourquoi elle compte** : c'est un contrat de données.
- **Options** : A (recommandée) dans `checks/<id>.json`, deux genres de plus (`fire-bending`, `fire-buckling`), et des champs additifs (`fire: {duration, sides, wood, …}`) : on réutilise `resolve`, positions, liens de variables et `MemberCheckTab`, avec une montée de version des schémas des vérifications ; B un dossier et un schéma à eux (`fire-checks/`, `fire-check-source` 1.0) : séparé, sans toucher aux vérifications, mais en dupliquant leur résolution.
- **Réponse** : A — `checks/<id>.json`, genres en plus, champ `fire` additif (2026-10-12).

### Q-004 — Quelle forme pour les commandes Typst ?
- **Pourquoi elle compte** : c'est la surface du rapport (l'ingénieur la décide).
- **Options** : A (recommandée) un argument `fire:` de `#member` — `#member("P1", fire: (duration: 60, sides: ("bottom", "left", "right")))` donne la barre résiduelle, et les `verify-bending`, `verify-shear`, `verify-compression` existants la vérifient avec la résistance au feu : peu de commandes nouvelles ; B une commande `#member-fire(name, of:, duration:, sides:)` qui crée une seconde barre « résiduelle », sans toucher à `#member` ; C des commandes dédiées `#verify-fire-bending` et `#verify-fire-buckling`, autonomes.
- **Réponse** : A — un argument `fire:` de `#member` ; les `verify-*` existants vérifient la barre résiduelle (2026-10-12).

### Q-005 — Comment saisir l'effet des actions au feu ?
- **Pourquoi elle compte** : saisie et traçabilité de E_d,fi.
- **Options** (non exclusives) : A (recommandée) les efforts au feu directement (M_d,fi, V_d,fi, N_d,fi), comme les autres onglets ; B les efforts à température normale et 0.6 · E_d (4.5.2.2, catégories A et B seulement) ; C les charges G_k, Q_k, S_k et la portée d'une poutre simple, comme le classeur Biegung (ψ₂ de SIA 260 Tabelle 2).
- **Réponse** : A seule — les efforts au feu saisis directement (M_d,fi, V_d,fi, N_d,fi), liables à une variable (2026-10-12).

### Q-006 — Quelles vérifications dans l'onglet ?
- **Pourquoi elle compte** : la portée.
- **Options** (non exclusives) : A (recommandée) flexion et effort tranchant (Biegung) ; B flambement (Knicken) ; C compression ou traction de la section seule ; D déversement.
- **Réponse** : A, B et C — flexion avec effort tranchant, flambement, compression ou traction de la section seule ; pas de déversement (2026-10-12).

### Q-007 — Où vivent les données du bâtiment de l'AEAI 15-15 ?
- **Pourquoi elle compte** : une source unique, ou une donnée par vérification.
- **Options** : A (recommandée) une fois pour le projet (catégorie de hauteur, affectation, concept), dans un fichier à lui lu par toutes les vérifications au feu, saisi dans l'onglet ; B dans chaque vérification ; C la durée R saisie à la main, l'AEAI 15-15 affichée comme aide seulement.
- **Réponse** : « une fois par projet, écrasable pour chaque vérification » (2026-10-12).

### Q-008 — Quel lien avec le plan de protection incendie ?
- **Pourquoi elle compte** : le plan ne connaît pas les positions (décision de §3.3vicies) et porte des classes EI/REI par mur.
- **Options** : A (recommandée) une vérification peut nommer un mur (ou une porte) d'un plan feu : sa classe (REI 60 → 60 min) fixe la durée, et le rapport le dit ; B le plan feu montre les éléments vérifiés et leur verdict, ce qui lui demande des positions ; C seulement un tableau du rapport qui croise les classes du plan et les vérifications.
- **Réponse** : « une vérification nomme une position », précisé en « Rien de plus » (2026-10-12) : le lien est la position que la vérification nomme ; le plan feu ne change pas.

### Q-010 — Genres `fire-*` ou objet `fire` sur les genres existants ? (posée après la revue)
- **Pourquoi elle compte** : quatre à six listes de genres (Python, schéma, `show-check-member`, validation, classeur de référence) s'allongeraient avec des genres `fire-*`.
- **Options** : A (recommandée) objet `fire` sur les genres existants ; B genres `fire-*` ; C un genre combiné flexion + tranchant.
- **Réponse** : A (2026-10-12).

### Q-009 — Comment choisir les faces exposées ?
- **Pourquoi elle compte** : le classeur Knicken entend « 2 faces » comme un angle (une face de b, une de h).
- **Options** : A (recommandée) quatre cases (dessous, dessus, gauche, droite), qui couvrent tous les cas ; B les quatre cas du classeur (1, 2 en angle, 3, 4 faces) ; C les deux cas de Figur 13 seulement (3 et 4 faces).
- **Réponse** : A — quatre cases : dessous, dessus, gauche, droite (2026-10-12).

## 11. Critères d'acceptation

- [x] REQ-001 — le cas Biegung reproduit (test).
- [x] REQ-002 — le cas Knicken 4 faces reproduit (test).
- [x] REQ-003 — Tabelle 13 transcrite ; un feuillu sans essence est non calculable.
- [x] REQ-004 — 4.5.2.4 et la limite de 90 min refusent avec raison (test).
- [x] REQ-005 — E_d,fi selon Q-005 (test).
- [x] REQ-006 — AEAI 15-15 tableaux 1–3 transcrits ; quatre cas redonnés (test).
- [x] REQ-007 — lien au plan feu selon Q-008 (test).
- [x] REQ-008 — section « Comparaison » écrite.
- [x] REQ-009 — export, rapport, égalité Python/Typst (test).
- [x] UI-001 — onglet, trois langues, création, enregistrement et rechargement (test hors écran).
- [x] UI-002 — données du bâtiment saisies et durée R affichée.
- [x] ARCH-001 — domaine sans Qt.
- [x] ARCH-002 — aucune valeur de norme écrite en dur.
- [x] ARCH-003 — schémas versionnés ; un fichier malformé arrête l'export en nommant le champ.
- [x] ARCH-004 — Python = Typst à 1e-6 près.
- [x] Documentation : `docs/domain/fire-resistance.md`, `docs/ui/tab-fire-resistance.md`, `docs/README.md`, `CHANGELOG.md`, « Nouveautés » fr/de/en, `///` + exemples + traductions pour toute commande Typst.
- [x] Tests : fichiers `tests/test_*.py` ajoutés, inscrits au catalogue, et passent.

## 12. Traçabilité

| Source | Élément | Statut |
|---|---|---|
| T1 | UI-001, REQ-009 | capturé |
| T2 | REQ-001, REQ-003, REQ-005 | capturé |
| T3 | REQ-002, REQ-003, REQ-005 | capturé |
| T4 | D-02, §8 | exclu (plus tard) |
| T5 | REQ-004, REQ-006, REQ-008 | capturé |
| T6 | D-01, UI-001 | décision |
| T7 | CON-001, REQ-008, Q-002 | capturé → question |
| T8 | D-02 | décision |
| T9 | D-03, REQ-006, REQ-007, REQ-008, UI-002 | capturé |

### Points de la source non résolus

- Aucun : toutes les questions ont leur réponse (§10).

## 13. Revue d'architecture

Deux `architecture-reviewer` en parallèle (domaine/contrat/Typst ; fenêtre), 2026-10-12. **Verdict : APPROUVER AVEC RÉSERVES** (les deux). Les réserves sont levées ci-dessous ou dans le plan.

**Modules concernés.** `calc/domains/member_check.py` (`KINDS` :47, `LINKABLE` :78, `check_source` :125, `stamp_version` :249, `resolve` :343, `draft_typst` :505, `compute`/`_compute*` :588-1070, `prepare` :1080) ; `lib/timber.typ` (`#member` :293, section `sec` :307-319, `meta` :365, valeurs de calcul :411-436, `timber-kc` :586 qui lit `fck`/`E005`, `show-check-member` :1420) ; `calc/validation.py:222` ; `schemas/member-check-source.schema.json`, `schemas/checks.schema.json` ; `calc/shown_variables.py:54`, `lib/shown-variables.json` ; `lib/summary.typ:139-155` ; `calc/norms/sia265.py` (`species` :806, `k_h` :1032), `calc/norms/vkf.py`, `calc/norms/norms.json` ; `calc/project.py` (:354 `lists_file`, :387 `checks_dir`) ; `calc/tools/woodcore_gui.py` (`TABS` :197, `NAV_GROUPS` :242, `WRITERS` :285, `GUARDED_TABS` :324) ; `calc/tools/member_check_tab*.py` (`MemberCheckTab` :112, `_own_ids` :269-293, `BucklingLengths` :620, motif `w_stated` :391/:538) ; `calc/tools/chrome.py:49` ; `calc/tools/build_reference.py`.

**À réutiliser.** Tout le chemin source → `resolve` → export → `show-check-member` ; `#member(k-h:)` ; `timber-kc` (lit les caractéristiques, donc ×1.8 sur les seuls `f_*_d` donne bien 1.8 · R_d au flambement) ; `_slenderness_rows`, `_stiffness`, `_bending_values` (un paramètre, pas une copie) ; `MemberCheckTab`, `BucklingLengths`, le motif « écrit par-dessus + Reprendre » ; `linked()` ; le test Python = Typst de `tests/test_member_check.py:549-705`.

**Risques et leur traitement.**
- ARCH-RISK-001 (important) — ×1.8 sur les seuls `f_*_d` ; `f_*_k`, `E_0_05` intacts ; `f_t_90_d`, `f_c_90_d` non mis à l'échelle ; k_h = 1. η_w et η_t restent dans R_d : (51) définit R_d comme la résistance de calcul de la section résiduelle « bei Normaltemperatur » (SIA 265 p. 40, lue), ce que fait le classeur (`fm,d · 1.8 · η_w`). Un cas en humidité 2 est dans le test. → plan étape 3.
- ARCH-RISK-002 (bloquant → levé) — un seul point de remplacement : `#member` publie `b_0`, `h_0`, `beta_n`, `d_char_n`, `d_red`, `d_ef`, puis `b`, `h` résiduels par `timber-eq`, de sorte que `A`, `W`, `I`, `i`, `meta` et les `verify-*` ne changent pas ; section ronde, section résiduelle ⩽ 0 → non calculable avec raison. → étape 3.
- ARCH-RISK-003/004 (important → levé par Q-010) — objet `fire` sur les genres existants.
- ARCH-RISK-005 (important) — source 1.2 si `fire` est présent (liens permis dès 1.1) ; export 1.2 seulement si au moins une vérification au feu ; `stamp_version` donne la version minimale ; un projet sans feu reste octet pour octet. → étape 2.
- ARCH-RISK-006 (important) — β_n (Tabelle 13), d_red, 90 min, 80/140 mm, 1.8 : un seul fichier `calc/norms/sia265-2021-4.5-brandfall.json`, lu par `sia265.py` et par `timber-files` ; Typst reçoit une durée résolue et ne lit jamais l'AEAI ; `wood` est une liste fermée écrite une fois et comparée entre Python et Typst. → étapes 1, 3.
- ARCH-RISK-007/103 (important) — bâtiment : `Woodcore-Datei/building.json`, chemin dans `project.py`, schéma `fire-building` 1.0, lu par `member_check.prepare` et passé à `resolve` en argument ; absent → avertissement ; malformé → arrêt qui nomme fichier et champ ; règles des notes [1], [5], [8], [9] écrites comme données ; enregistrer le bâtiment réexporte les vérifications. → étapes 1, 2, 5.
- ARCH-RISK-008 (important) — `validate_checks_business` reçoit les règles du feu ; le résumé (`lib/summary.typ`) marque une vérification au feu (« Brand » / « feu » / « fire ») pour ne pas mêler η à froid et au feu. → étapes 2, 4.
- ARCH-RISK-009 (important) — `#member(fire:)` : `///`, deux exemples, `commands.json`, nouvelles clés dans `lib/shown-variables.json` ; `sides` est un tableau de chaînes en Typst et quatre booléens en JSON, convertis dans `draft_typst` seul. → étape 4.
- ARCH-RISK-101 (bloquant → levé) — un onglet, plusieurs genres : `MemberCheckTab` lit `self.kinds()` et `self.current_kind()` (par défaut `(KIND,)` et `KIND`) et un filtre `owns(source)` ; les six onglets existants excluent `fire`, l'onglet feu ne prend que `fire` ; le genre est un combo, figé une fois la vérification enregistrée ; aucune ligne de comportement des six onglets ne change. → étape 5.
- ARCH-RISK-104/105 (important) — `save_building` dans `WRITERS` ; le bâtiment est dans le `dirty` de l'onglet et s'écrit avec Ctrl+S (option b de la revue), puis `member_check.export()`. → étape 5.
- ARCH-RISK-106/107/108/109/110 (mineurs) — la durée vient d'une fonction du domaine (`vkf.required_resistance`) ; `view_state` retient le genre ; icône `tab_mc_fire` ; `test_member_check_tab` compte les modules du groupe ; l'onglet est le dernier de « Sécurité structurale » ; mots dans `fire_check_tab_words.py` (fr/de/en, allemand de l'AEAI marqué à vérifier, issue #34).
- ARCH-RISK-010/011/012/013 (mineurs) — classeur de référence tolérant `fire` ; rien hors de `timber.typ` côté Typst (pas de cycle) ; pas de Qt dans le domaine ; test de non-codage en dur sur le domaine et `timber.typ`.

**Écart à la revue, accepté.** La revue de la fenêtre propose d'extraire `MomentsRows`/`ShearRows` de `BendingTab`/`ShearTab`/`LateralTab`. On ne touche pas aux trois onglets existants : l'onglet feu compose ses rangées avec les fabriques de la base (`linked`, `effort_card`). La duplication existante de `LateralTab` reste notée dans `docs/open-questions.md`.

## 14. Plan d'implémentation

1. **Normes.**
   - `calc/norms/sia265-2021-4.5-brandfall.json` : Tabelle 13 avec les lignes `softwood_solid` 0.8, `softwood_glulam` 0.7, `oak` 0.5, `cladding` 0.9 ; d_red 7 mm jusqu'à 90 min ; 4.5.2.4 80/140 ; (51) 1.8 ; 0.6 de 4.5.2.2 pour mémoire. Lecteur dans `sia265.py` (`fire_clause()`, `charring_rate(grade, wood)`), avec un contrôle de forme.
   - `calc/norms/vkf-2017-3.7.1-15-15-tragwerk.json` : tableaux 1 à 3, pp. 12–15, notes [1] [5] [8] [9] comme données. `vkf.required_resistance(building, top_level)` rend `(minutes|None, table, row, notes)`.
   - Entrée AEAI 15-15 dans `norms.json`.
   - Réalise REQ-003, REQ-004, REQ-006, ARCH-002. Tests : `tests/test_fire_resistance.py` (Tabelle 13, les quatre cas AEAI).
2. **Contrat et domaine.**
   - `schemas/member-check-source.schema.json` : `fire` {`duration` null | minutes, `sides` {bottom, top, left, right}, `wood` null | beech | oak | cladding, `top_level`} ; version 1.2.
   - `schemas/checks.schema.json` : le `fire` résolu, avec `duration_from` (« aeai » | « stated »), `table`, `row`, `beta_n`, `b_fi`, `h_fi` ; version 1.2.
   - `schemas/fire-building.schema.json` 1.0 ; `project.building_file`.
   - `member_check` : `check_source` (champ `fire`), `stamp_version` (version minimale), `resolve(src, positions, values, building)` (durée, raisons non calculables : rond, ⩽ 0, 4.5.2.4, > 90 min, feuillu sans essence, aucune face, pas de durée), `prepare` lit le bâtiment, `validate_checks_business` reçoit les règles du feu.
   - Réalise REQ-004, REQ-006, REQ-009, ARCH-003. Tests : `test_member_check.py` (versions 1.0/1.1/1.2, malformé qui nomme le champ, projet sans feu octet pour octet), `tests/test_fire_building.py`.
3. **Calcul Python.** `fire_context(record)` donne la section résiduelle et le facteur ; `_compute`, `_compute_bending`, `_compute_shear`, `_compute_buckling` la reçoivent par un seul paramètre, k_h = 1, ×1.8 sur les `f_*_d`. Réalise REQ-001, REQ-002. Tests : oracles Biegung et Knicken, humidité 2.
4. **Typst.**
   - `#member(fire: (duration:, sides:, wood:))` dans `lib/timber.typ` : lit le fichier de norme par `timber-files`, publie les variables, remplace b et h, ×1.8, k_h off ; la ligne du membre dit « b/h → b_fi/h_fi ».
   - `show-check-member` transmet `fire` ; `draft_typst` l'écrit.
   - `lib/shown-variables.json` et le marqueur feu de `lib/summary.typ`.
   - `///`, deux exemples, `calc/i18n/commands.json`.
   - Réalise REQ-009, ARCH-004. Tests : `test_member_check.py` étendu à ≥ 8 cas au feu à 1e-6, `test_timber.py`, `test_commands.py`, `test_summary*`.
5. **Fenêtre.**
   - Base : `MemberCheckTab.kinds()`, `current_kind()`, `owns()`.
   - `calc/tools/fire_check_tab.py` (`FireCheckTab`, ID `FE-`) : combo du genre, carte « Feu » (durée qui suit ou écrite, avec « Reprendre » ; quatre cases ; bois ; dernier niveau), carte « Bâtiment (AEAI 15-15) », rangées d'efforts par genre montrées ou masquées.
   - `fire_check_tab_words.py` ; `TABS`, `NAV_GROUPS["nav_safety"]` en dernier, `WRITERS` (`save_building`), icône `tab_mc_fire`.
   - Réalise UI-001, UI-002, REQ-005, REQ-007, ARCH-001. Tests : `tests/test_fire_check_tab.py` (hors écran), `test_member_check_tab.py`, `test_chrome.py`, `test_home.py`, `test_i18n.py`.
6. **Exemple et documentation.**
   - `tests/projet-exemple` : une flexion (FE-01, l'oracle Biegung adapté), un flambement (FE-02), un `building.json`.
   - `docs/domain/fire-resistance.md`, avec la « Comparaison » de REQ-008 ; `docs/ui/tab-fire-resistance.md` ; `docs/README.md`, `window.md`, `member-checks.md` (renvois) ; `docs/decisions.md` (D-04, D-06) ; `docs/open-questions.md` (acier, protégé, Lignum) ; catalogue des tests ; `CHANGELOG.md` ; « Nouveautés » fr/de/en.
   - Réalise REQ-008, CON-004.
7. **Suite complète**, puis vérification indépendante (§15).

## 15. Vérification

**Tour 1** (`requirements-verifier`, 2026-10-12, arbre de travail contre 311a920). Les changements d'une autre session (issues #47–#49, acier) sont dans le même arbre ; ils ne comptent ni pour ni contre la spec.

| Élément | Verdict | Preuve |
|---|---|---|
| REQ-001 | ✅ | `test_fire_resistance.test_the_biegung_workbook_is_reproduced` : b 30, h 145, W_y 105 125, σ 57.595, η 2.2693 ; `test_the_window_s_result_is_the_biegung_workbook` ; k_h = 1 |
| REQ-002 | ✅ | `test_the_knicken_workbook_s_geometry_and_k_c_are_reproduced` : 96/196, λ 86.6, λ_rel 1.408, k_c 0.4226 |
| REQ-003 | ⚠️ → corrigé | fichier unique `sia265-2021-4.5-brandfall.json` au lieu du nom écrit au critère ; critère mis à jour selon §13/§14 |
| REQ-004 | ✅ | `test_the_fire_situation_refuses_what_the_norm_does_not_give`, `test_what_the_project_lacks_makes_a_fire_check_not_calculable` (4.5.2.4, 90 min) |
| REQ-005 | ✅ | champs M_y, M_z, V_z, V_y, N ; `test_fire_check_tab.test_a_linked_force_is_saved_with_its_link` |
| REQ-006 | ✅ | `test_vkf_15_15_gives_the_spec_s_four_cases`, `test_vkf_15_15_applies_its_notes_as_the_file_states_them` (notes et exemptions 3.2.3) |
| REQ-007 | ✅ | `position` porté ; `schemas/fire-source.schema.json` inchangé |
| REQ-008 | ✅ | `docs/domain/fire-resistance.md`, section « Comparison » |
| REQ-009 | ⚠️ → corrigé | `checks.json` de l'exemple périmé (sans `exemption`) : réexporté ; test d'égalité à 298 s : scindé (`test_compute_in_the_fire_situation_is_what_the_report_computes`) |
| UI-001 | ✅ | `test_the_tab_is_last_of_safety_in_the_report_alone`, `test_a_check_of_each_kind_is_made_saved_and_read_back` |
| UI-002 | ✅ | `test_the_duration_follows_the_building_and_is_written_over`, `test_the_building_is_saved_and_the_checks_follow_it` |
| ARCH-001 | ⚠️ → corrigé | grep propre, sans test : `test_the_fire_s_domain_imports_no_qt` ajouté |
| ARCH-002 | ✅ | `test_no_value_of_the_fire_clauses_is_written_in_the_code`, `test_the_woods_and_the_faces_are_written_once` |
| ARCH-003 | ✅ | schémas 1.2 et `fire-building` 1.0 ; `test_a_malformed_fire_stops_naming_the_field`, `test_the_building_file_is_checked_and_written` |
| ARCH-004 | ⚠️ → corrigé | 10 cas + FE-01/FE-02 à 1e-6, prouvé à la main (298 s) ; scindé en deux tests |
| CON-001 à CON-005 | ✅ (CON-004 ⚠️ → corrigé) | tailles du README corrigées ; les renvois à `docs/requirements/completed/` deviennent justes au déplacement de la spec |
| §8 hors périmètre | ✅ | ni acier, ni protégé, ni déversement au feu, ni 0.6 · E_d, ni marquage du plan feu |

**Tour 2** (après les corrections) : `test_fire_resistance` 20 ✅, `test_fire_check_tab` 8 ✅, `test_member_check` + `test_member_check_tab` 82 ✅ (le test d'égalité scindé tient sous la limite), `test_links` 22 ✅, `test_i18n` 22 ✅. Tous les éléments ✅.

## 16. Journal d'avancement

| Date | Statut | Fait / reste |
|---|---|---|
| 2026-10-12 | draft | spécification extraite de l'issue #46 ; sources lues : les deux classeurs bois, SIA 265:2021 4.5, AEAI 13-15, 14-15, 15-15 ; 9 questions |
| 2026-10-12 | specified | 9 réponses (Q-008 précisée une fois) ; D-04 à D-12 ; REQ-001/002/005/006/007 et UI-002 réécrits |
| 2026-10-12 | reviewed | deux revues APPROUVER AVEC RÉSERVES ; Q-010 (objet `fire` sur les genres existants) ; §13 et §14 écrits |
| 2026-10-12 | approved | approuvé par l'ingénieur (« Approuver et implémenter ») |
| 2026-10-12 | implementation | étape 1 faite : sia265-2021-4.5-brandfall.json + sia265.fire/charring_rate/family/FIRE_WOODS/FIRE_SIDES ; vkf-2017-3.7.1-15-15-tragwerk.json + vkf.requirement/check_building/required_resistance (REQ-003, REQ-006 partiel, ARCH-002) |
| 2026-10-12 | implementation | étapes 2–5 faites : schémas 1.2 et fire-building 1.0, project.building_file, member_check (check_source/_check_fire, stamp_version, resolve/_fire_block, read/write_building, fire_duration, draft_typst/fire_typst, compute en situation d'incendie, prepare), validation, units.json (min), #member(fire:) et show-check-member, shown-variables, fire_check_tab.py (+ words, NAV, WRITERS save_building, GUARDED_TABS, icône) ; tests test_fire_resistance (18) et test_fire_check_tab (8) verts, test_timber vert ; reste : marqueur du résumé, exemple, build_reference, commands.json, docs |
| 2026-10-12 | testing | étape 6 faite : marqueur du résumé (summary.fire), exemple FE-01/FE-02 + building.json et export de l'exemple régénéré, exemptions AEAI 15-15 3.2.3 al. 2 c/d ajoutées (trouvées en relisant la directive), commands.json (fire:, paragraphe de show-check-member), exemples member-8/9, docs (fire-resistance.md, tab-fire-resistance.md, README, window, member-checks, open-questions, deux décisions), catalogue, CHANGELOG, Nouveautés 0.118.0 fr/de/en ; reste : tests liés, puis vérification indépendante |
| 2026-10-12 | verification | tour 1 du vérificateur : 1 ❌ (checks.json de l'exemple périmé) et 6 ⚠️ — corrigés (réexport, test d'égalité scindé, test ARCH-001, tailles du README, noms de fichiers des critères) |
| 2026-10-12 | completed | tour 2 vert sur les tests qui gardent la spec ; spec déplacée dans `docs/requirements/completed/` |
