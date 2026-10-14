---
id: 2026-10-12-section-acier
titre: Section d'onglets «Acier» — profilés, vérifications de barres, assemblages (issues #50, #51, #52)
status: implementation
cree: 2026-10-12
mis_a_jour: 2026-10-12
source: message écrit (/issue du 12.10.2026, réponses aux questions 1–7) et issues GitHub #50, #51, #52 ; demande «implémente les issues 50, 51, 52»
docs: [docs/ui/window.md, docs/ui/tab-member-checks.md, docs/domain/member-checks.md, docs/domain/positions.md, docs/architecture/principles.md, docs/architecture/reference-library.md]
---

# Section d'onglets «Acier» — Spécification

## 1. Objectif

L'ingénieur veut dimensionner dans Woodcore les éléments en acier d'un projet bois, comme il le fait aujourd'hui avec les classeurs de référence d'acier et le cours de F. Graber (BFH, StahlBetonBau1 HS26) : une section d'onglets «Acier» qui donne les profilés (bibliothèque SZS C5 et profilés libres), la classe de section, les vérifications de barres de SIA 263:2013 et les assemblages acier (boulons, soudures, joint de cisaillement), imprimés dans le rapport de statique comme les vérifications bois.

## 2. Source

Message du 12.10.2026 (`/issue`) :

> **T1** — « Je souhaite ajouter une section d'onglets "Acier". »
>
> **T2** — « Comme aide pour toi, regarde le cours 001-Stahl-Graber. »
>
> **T3** — « Tu dois créé plusieurs onglet (e.g. un onglet pour définir la classe de section). »
>
> **T4** — « Aide-toi également des classeurs de référence sur l'acier (également toutes les valeurs extraites du livre C5). »

Réponses aux questions de `/issue` (12.10.2026) :

> **T5** — Q1, découpage : « Par vérification, comme le bois ».
>
> **T6** — Q2, familles : « I doublement symétriques, Tubes rectangulaires, Autres profilés, Profilé défini par l'utilisateur ».
>
> **T7** — Q2, profilé libre : « profilé défini par l'utilisateur: dessiné par lui de manière paramétrique ou par dessin (s'inspirer légèrement du fichier python dans le cours de l'acier). L'utilisateur peut charger des profils modèles et ensuite les modifier pour arriver à son profil personnel ».
>
> **T8** — Q3, source des valeurs : « Relire SZS C5, Excel en contrôle ».
>
> **T9** — Q4, profilé et nuance : « depuis la position. Au besoin, saisi dans l'onglet acier (comme pour les autres onglets bois) ».
>
> **T10** — Q5, assemblages acier : « Dans la section «Acier» ».
>
> **T11** — Q6, feu des profilés acier : « Hors périmètre ».
>
> **T12** — Q7, norme : « SIA 263:2013 seule ».
>
> **T13** — Demande du 12.10.2026 : « implémente les issues 50, 51, 52 ».

Points des issues (rédigés le 12.10.2026 à partir de T1–T12 et validés par l'ingénieur) :

> **T14** (#50) — Transcrire les tables de profilés SZS C5 dans `calc/norms/` (A, I, W_el, W_pl, K, h1/tw, (a−r)/tf, kg/m…), lues sur l'édition SZS C5 nommée ; les «Hilfstabelle Stahl-Profile» de référence servent de contrôle croisé en test. Lève la décision «aucune table de profilés n'est transcrite».
>
> **T15** (#50) — Nuances S235…S460 (f_y, f_u, τ_y selon l'épaisseur) lues dans SIA 263:2013 Tab. 1.
>
> **T16** (#51) — Onglets Classe de section, Traction, Compression, Flexion (simple, biaxiale, avec effort normal), Effort tranchant (avec interaction M–V), Flambement, Déversement (linéaire selon la norme ou non linéaire selon Hirt comme les classeurs de référence ; laminé ou soudé), Interaction N‑M (N‑My, N‑Mz, N‑My‑Mz, éq. (49) classes 1–2, (54) classe 3). Chaque étape cite son article SIA 263 ; les exemples de référence servent de cas de test.
>
> **T17** (#52) — Onglets Boulons (cisaillement, traction, pression diamétrale, précontraints, dispositions constructives, section affaiblie), Soudures (angle, pleine pénétration), Joint de cisaillement (éclisses d'âme boulonnées, attache par cornières, section brute et affaiblie). Voir #48 (pression diamétrale de la tôle, éq. 76).

## 3. Exigences fonctionnelles

### REQ-001 — Bibliothèque de profilés SZS C5
- **Exigence** : Woodcore doit lire, depuis `calc/norms/szs-c5-…-<famille>.json`, les valeurs statiques de chaque profilé des familles IPE, HEA, HEB, HEM, HHD, HL, INP, PEA, UPE, UNP, LNP (cornières), IPET, HEAT, HEBT, ROR, RND, VKT, RRW, RRK : m, A, A_v, A_w, I_y, W_el,y, W_pl,y, i_y, I_z, W_el,z, W_pl,z, i_z, K, h, b, t_w, t_f, r, h_1 (selon la famille), chacune avec sa page C5.
- **Source** : T4, T6, T8, T14
- **Priorité** : doit
- **Critère d'acceptation** : un test lit chaque famille ; pour chaque profilé présent dans une «Hilfstabelle Stahl-Profile» de référence, toutes les valeurs communes concordent (tolérance d'arrondi d'impression C5) ; chaque fichier a un `_source` qui nomme `SZS-C5-2021.pdf` et ses pages.

### REQ-002 — Nuances d'acier
- **Exigence** : Woodcore doit donner f_y, f_u, τ_y d'une nuance S235…S460 selon la bande d'épaisseur de SIA 263 Tab. 1 (t ≤ 40 mm, 40 < t ≤ 100 mm), la bande étant tirée de l'épaisseur maximale du profilé, et E, G de SIA 263 3.2.
- **Source** : T15 (`sia263-2013-tab01-baustaehle.json` existe)
- **Priorité** : doit
- **Critère d'acceptation** : test : HEB 400 (t_f 24) S355 → f_y 355 ; HEM 1000 (t_f > 40, si présent) → bande épaisse.

### REQ-003 — Profilé libre
- **Exigence** : Woodcore doit permettre de définir un profilé libre, paramétrique ou dessiné, à partir d'un profilé modèle chargé puis modifié, et en calculer A, centre de gravité, I_y, I_z, W_el, axes plastiques, W_pl (méthode du `Querschnittsrechner.py` du cours, reprise légèrement).
- **Source** : T6, T7
- **Priorité** : doit
- **Critère d'acceptation** : test : un I composé de trois rectangles reproduit A, I_y, W_el,y, W_pl,y calculés à la main ; un profilé modèle chargé puis modifié est enregistré comme profilé libre et une position peut le nommer.

### REQ-004 — Profilé et nuance depuis la position
- **Exigence** : chaque vérification acier doit lire profilé et nuance de la position nommée, et accepter une valeur saisie dans l'onglet qui la remplace (règle «suivi / écrit par-dessus» des onglets bois, v0.70/v0.77).
- **Source** : T9
- **Priorité** : doit
- **Critère d'acceptation** : test : une vérification sans valeur saisie prend `IPE 360` / `S355` de sa position ; une valeur saisie reste après un *Import données*.

### REQ-005 — Classe de section
- **Exigence** : Woodcore doit déterminer la classe de l'âme et des ailes (compression pure ; compression et flexion), et la classe du profilé, selon SIA 263 4.5 Tab. 5a/5b.
- **Source** : T3, T16
- **Priorité** : doit
- **Critère d'acceptation** : test : les cas de la feuille «Hilfstabelle Querschnittsklasse» de l'Excel I (IPE 360 S355) donnent la même classe.

### REQ-006 — Résistances en section
- **Exigence** : Woodcore doit vérifier la traction, la compression (sans stabilité), la flexion simple et biaxiale, la flexion avec effort normal, l'effort tranchant et l'interaction flexion–effort tranchant, élastique ou plastique selon la classe, selon SIA 263 4.5 / 4.6 (articles exacts lus dans l'édition).
- **Source** : T5, T16 ; cours 005
- **Priorité** : doit
- **Critère d'acceptation** : un test par équation contre un calcul à la main ou un exemple du cours (901-TeamsLösungen).

### REQ-007 — Flambement
- **Exigence** : Woodcore doit vérifier le flambement selon SIA 263 4.5.1 (longueurs de flambement, courbes Fig. 7 / Tab. 8, χ).
- **Source** : T16
- **Priorité** : doit
- **Critère d'acceptation** : la feuille «Knicken» de l'Excel I (exemple IPE 360 S355) est reproduite.

### REQ-008 — Déversement
- **Exigence** : Woodcore doit vérifier le déversement selon SIA 263 4.5.2 (laminé/soudé, moment linéaire par η(ψ) Fig. 41 ; cas non linéaire selon Q-007).
- **Source** : T16
- **Priorité** : doit
- **Critère d'acceptation** : la feuille «Kippen» de l'Excel I est reproduite pour le cas linéaire.

### REQ-009 — Interaction N‑M
- **Exigence** : Woodcore doit vérifier N‑My, N‑Mz, N‑My‑Mz, éq. (49) pour les classes 1–2 et (54) pour la classe 3.
- **Source** : T16
- **Priorité** : doit
- **Critère d'acceptation** : les feuilles N‑My, N‑Mz, N‑My‑Mz de l'Excel I sont reproduites.

### REQ-010 — Boulons
- **Exigence** : Woodcore doit vérifier un groupe de boulons : cisaillement, traction, interaction, pression diamétrale (SIA 263 éq. (76)), boulons précontraints, dispositions constructives (e1, e2, p1, p2), section affaiblie — classes de Tab. 2.
- **Source** : T10, T17 ; cours 007
- **Priorité** : doit
- **Critère d'acceptation** : les exemples du cours 007 / Übungen sont reproduits.

### REQ-011 — Soudures
- **Exigence** : Woodcore doit vérifier les soudures d'angle et à pleine pénétration selon SIA 263.
- **Source** : T10, T17 ; cours 008
- **Priorité** : doit
- **Critère d'acceptation** : un exemple du cours 008 est reproduit.

### REQ-012 — Joint de cisaillement
- **Exigence** : Woodcore doit vérifier un joint de cisaillement (éclisses d'âme boulonnées, attache par cornières), boulons et section brute/affaiblie.
- **Source** : T10, T17 ; cours 009
- **Priorité** : doit
- **Critère d'acceptation** : l'exemple «Gerbergelenk» du cours 009 est reproduit.

### REQ-013 — Rapport
- **Exigence** : chaque vérification acier enregistrée doit pouvoir s'imprimer dans le rapport de statique par une commande Typst qui la nomme par son ID, avec niveaux de détail, citations SIA 263 et verdict, comme `#show-check-member`.
- **Source** : T5 («comme le bois»), principe 2 (inféré)
- **Priorité** : doit
- **Critère d'acceptation** : le document d'exemple compile un appel par onglet ; `///`, deux exemples et traduction dans `calc/i18n/commands.json` par commande.

## 4. Exigences d'interface

### UI-001 — Section «Acier» de la navigation
- **Exigence** : un groupe «Acier» / «Stahl» / «Steel» dans `NAV_GROUPS`, au rapport de statique seul, un onglet par vérification (cf. Q-006 pour l'ordre et les sous-titres).
- **Source** : T1, T3, T5, T10
- **Langues** : fr / de / en
- **Critère d'acceptation** : `tests/test_chrome.py` / le test de comptage des modules connaissent les nouveaux onglets ; chaque onglet a son icône `chrome.ICONS`.

### UI-002 — Onglet «Profilés»
- **Exigence** : parcourir la bibliothèque C5 (famille, taille, valeurs), créer/éditer un profilé libre (paramétrique ou dessiné), charger un modèle, voir la section dessinée et ses valeurs.
- **Source** : T6, T7
- **Langues** : fr / de / en
- **Critère d'acceptation** : test hors écran : charger HEA 200 comme modèle, changer t_f, enregistrer → fichier source valide, valeurs recalculées.

### UI-003 — Onglets de vérification acier
- **Exigence** : chaque onglet suit le modèle `MemberCheckTab` (liste à dossiers, formulaire en cartes, résultat Python instantané, vues Calcul/Affichage, champs liables à une variable).
- **Source** : T5, T9
- **Langues** : fr / de / en
- **Critère d'acceptation** : `tests/test_editor_buttons.py` clique les boutons de liste des nouveaux onglets.

## 5. Exigences d'architecture

### ARCH-001 — Domaines sans Qt
- **Exigence** : calculs dans `calc/domains/` (sans Qt) ; les onglets montrent et appellent.
- **Source** : principes (règle «Domain logic is independent of the UI»)
- **Critère d'acceptation** : aucun import Qt dans les nouveaux modules de domaine (test existant d'imports).

### ARCH-002 — Valeurs de norme dans `calc/norms/`
- **Exigence** : chaque valeur SIA 263 / SZS C5 lue d'un fichier JSON de `calc/norms/` avec `_source`, lu dans l'édition (`ExternalFiles/000-Normes`) ; rien de mémoire.
- **Source** : T8, T12, CLAUDE.md
- **Critère d'acceptation** : tests de cohérence des normes étendus aux nouveaux fichiers.

### ARCH-003 — Contrats versionnés
- **Exigence** : sources (profilés libres, vérifications acier, assemblages acier) et exports avec schéma `schemas/*.schema.json` et `schema_version`.
- **Source** : principes (inféré)
- **Critère d'acceptation** : validation des schémas dans les tests ; fichier malformé → arrêt nommant fichier et champ.

## 6. Contraintes

- **CON-001** — SIA 263:2013 seule (T12) ; SIA 263-1:2020 seulement pour les données matériaux qu'elle porte. Pas d'EN 1993.
- **CON-002** — Valeurs C5 relues dans `SZS-C5-2021.pdf` (réimpression de la révision 2018) ; le PDF est un scan OCR bruité : chaque table est lue et contrôlée contre le classeur de référence (T8).
- **CON-003** — Trois langues pour toute chaîne visible (inféré, CLAUDE.md).
- **CON-004** — Plusieurs sessions modifient le dépôt (la session «Onglet calcul résistance au feu», #46, ajoute `tab_mc_fire` dans `nav_safety`) : coordonner `woodcore_gui.py` et les tests de comptage (inféré).
- **CON-005** — Ne pas écrire dans les projets de l'ingénieur ; exemples dans `tests/projet-exemple/` (CLAUDE.md).

## 7. Décisions prises

- **D-01** (T5) — Un onglet par vérification, comme le bois.
- **D-02** (T6) — Familles : I doublement symétriques, tubes rectangulaires, autres profilés, profilé libre.
- **D-03** (T7) — Profilé libre paramétrique ou dessiné, à partir d'un modèle chargé puis modifié ; inspiré légèrement de `Querschnittsrechner.py`.
- **D-04** (T8) — Tables C5 relues dans l'édition, le classeur de référence en contrôle croisé. Lève la décision «aucune table de profilés n'est transcrite» (`docs/domain/positions.md` §7, `calc/domains/section.py`) → `docs/decisions.md`.
- **D-05** (T9) — Profilé et nuance depuis la position, saisissables dans l'onglet.
- **D-06** (T10) — Assemblages acier dans la section «Acier».
- **D-07** (T12) — SIA 263:2013 seule.
- **D-08** (Q-001) — Une spec, trois lots commités : lot 1 profilés, nuances, classe de section, résistances en section ; lot 2 flambement, déversement, interaction N‑M ; lot 3 assemblages.
- **D-09** (Q-002) — Calcul acier en Python seul : le domaine calcule, l'export écrit chaque valeur intermédiaire (lignes `{key, symbol, value, unit, formula, clause}`), Typst imprime. Pas de commande `verify-steel-*` qui recalcule ; pas d'appel acier à la main sans vérification enregistrée.
- **D-10** (Q-003) — Profilé libre en rectangles assemblés ; modèles I, U, T, L, tube générés en rectangles sans congés.
- **D-11** (Q-004) — Classe d'un profilé libre par rôle de paroi (interne / console / aucune), posé par le modèle, modifiable.
- **D-12** (Q-005) — Profilé libre : `Woodcore-Datei/profiles/<id>.json`, type de section `USR`, dimension = ID. Vérifications acier : `Woodcore-Datei/steel/<id>.json` → `data/steel.json`, domaine séparé du bois.
- **D-13** (Q-006) — Groupe «Acier» avant «Référence», sous-titres Section · Sécurité structurale · Assemblages.
- **D-14** (Q-007) — Déversement : SIA 263 seule ; pour un moment non linéaire, η ou M_cr donné par l'ingénieur.
- **D-15** (Q-008) — Assemblage acier défini au choix par formulaire ou par schéma («Schémas»), choisi à sa création ; la suite du formulaire dépend du choix.
- **D-16** (revue, ARCH-RISK-103) — Un profilé libre cité par une position ne peut être ni renommé ni supprimé ; le refus nomme les positions qui le citent.
- **D-17** (revue, ARCH-RISK-202) — Une seule commande Typst, `#show-check-steel(id, level:, shown:, title:, unit:)`, pour toute vérification et tout assemblage acier, imprimée par `show-calc` (l'aspect des connecteurs).
- **D-18** (revue, ARCH-RISK-304) — La soudure est ajoutée aux schémas de détail (outil «Soudure» dans «Schémas» : gorge a, longueur, type ; schéma de détail en version 1.3, additif), de sorte que les trois assemblages acier se définissent par formulaire ou par schéma.

## 8. Hors périmètre

- Résistance au feu des profilés acier («Brandwiderstand Stahlprofil») — T11.
- EN 1993 — T12.
- Profilés inoxydables, tôles minces formées à froid (SIA 263-1 ou C5 hors familles listées).

## 9. Idées non retenues comme exigences

- (aucune pour l'instant)

## 10. Questions

### Q-001 — Livraison en lots
- **Pourquoi elle compte** : le périmètre (≈ 13 onglets, 20 familles C5, éditeur de profilés, 3 domaines) est plusieurs fois celui des issues bois #35–#39 ; un lot vérifié et commité limite ce qu'une interruption perd.
- **Options** : A (recommandée) une spec, trois lots commités l'un après l'autre (1 : profilés + nuances + classe + résistances en section ; 2 : flambement, déversement, interaction ; 3 : assemblages) · B tout en un seul commit · C trois specs séparées, une approbation chacune.
- **Réponse** : A — une spec, trois lots commités l'un après l'autre (2026-10-12).

### Q-002 — Où le calcul est fait
- **Pourquoi elle compte** : le bois calcule deux fois (Typst `lib/timber.typ` pour le rapport, Python pour la fenêtre, tenus égaux par un test) — exception acceptée au principe «une source».
- **Options** : A (recommandée) Python seul : le domaine calcule, l'export écrit chaque valeur intermédiaire, Typst imprime formules et valeurs (une source ; pas d'appel acier écrit à la main sans vérification enregistrée) · B comme le bois : commandes `verify-steel-*` dans `lib/steel.typ` + duplicata Python tenu égal par test.
- **Réponse** : A — Python seul ; l'export écrit chaque valeur intermédiaire, Typst imprime (2026-10-12).

### Q-003 — Géométrie du profilé libre
- **Options** : A (recommandée) rectangles assemblés (comme le cours) ; modèles I, U, T, L, tube générés en rectangles, sans congés · B polygones quelconques · C rectangles + arcs (congés, tubes ronds).
- **Réponse** : A — rectangles assemblés ; modèles générés en rectangles, sans congés (2026-10-12).

### Q-004 — Classe de section d'un profilé libre
- **Options** : A (recommandée) chaque rectangle porte un rôle (paroi interne / en console / aucune), posé par le modèle et modifiable ; c/t calculé · B classe donnée à la main · C toujours élastique (classe 3).
- **Réponse** : A — rôle par paroi (interne / console / aucune), posé par le modèle, modifiable (2026-10-12).

### Q-005 — Profilé libre dans une position, et rangement des vérifications acier
- **Options** : A (recommandée) source `Woodcore-Datei/profiles/<id>.json`, nouveau type de section `USR` dont la dimension est l'ID ; vérifications acier dans `Woodcore-Datei/steel/<id>.json` → `data/steel.json` (domaine séparé du bois) · B même dossier `checks/` et `checks.json` que le bois, genres `steel-*`.
- **Réponse** : A — `Woodcore-Datei/profiles/<id>.json` + type de section `USR` ; vérifications acier dans `Woodcore-Datei/steel/<id>.json` → `data/steel.json` (2026-10-12).

### Q-006 — Organisation de la navigation
- **Options** : A (recommandée) un groupe «Acier» avant «Référence», trois sous-titres (`NAV_SECTIONS`) : Section (Profilés, Classe de section) · Sécurité structurale (Traction, Compression, Flexion, Effort tranchant, Flambement, Déversement, Interaction N‑M) · Assemblages (Boulons, Soudures, Joint de cisaillement) · B trois groupes de navigation.
- **Réponse** : A — un groupe «Acier» avant «Référence», trois sous-titres Section · Sécurité structurale · Assemblages (2026-10-12).

### Q-007 — Déversement, moment non linéaire
- **Pourquoi elle compte** : Le classeur de référence prend η pour un moment non linéaire dans Hirt, *Stahlbau*, p. 394 — livre absent de `ExternalFiles/000-Normes/Litteratur` : une valeur ne peut pas être citée d'une édition non disponible.
- **Options** : A (recommandée) SIA 263 seule (η(ψ) Fig. 41 pour le linéaire) ; pour un autre diagramme l'ingénieur donne η ou M_cr · B ajouter Hirt à la bibliothèque et transcrire son tableau.
- **Réponse** : A — SIA 263 seule ; autre diagramme : η ou M_cr donné par l'ingénieur (2026-10-12).

### Q-008 — Définition des assemblages acier
- **Options** : A (recommandée) formulaire (nombre de boulons, rangées, e1, e2, p1, p2, épaisseurs, effort) avec figure générée, comme les classeurs de référence et le cours · B dessinés dans l'onglet «Schémas» et lus de là.
- **Réponse** : « les deux (possibilité de choisir au début quelle méthode utiliser). Cela change la suite de l'affichage » (2026-10-12) : un assemblage acier choisit à sa création formulaire ou schéma, et le formulaire qui suit dépend de ce choix.

## 11. Critères d'acceptation

- [ ] REQ-001 — 20 familles C5 transcrites, concordance avec les trois Hilfstabellen de référence.
- [ ] REQ-002 — nuance et bande d'épaisseur de Tab. 1.
- [ ] REQ-003 — profilé libre calculé, enregistré, nommable par une position.
- [ ] REQ-004 — profilé et nuance suivis ou écrits par-dessus.
- [ ] REQ-005 — classe de section = Excel I.
- [ ] REQ-006 — résistances en section testées équation par équation.
- [ ] REQ-007 — feuille Knicken reproduite.
- [ ] REQ-008 — feuille Kippen reproduite (linéaire).
- [ ] REQ-009 — feuilles N‑My, N‑Mz, N‑My‑Mz reproduites.
- [ ] REQ-010 — exemples boulons du cours reproduits.
- [ ] REQ-011 — exemple soudure reproduit.
- [ ] REQ-012 — exemple Gerbergelenk reproduit.
- [ ] REQ-013 — commandes Typst documentées, deux exemples chacune, traduites.
- [ ] UI-001 — groupe «Acier» en trois langues, icônes, tests de navigation.
- [ ] UI-002 — onglet Profilés testé hors écran.
- [ ] UI-003 — onglets acier sur le modèle `MemberCheckTab`, boutons testés.
- [ ] ARCH-001 — domaines sans Qt.
- [ ] ARCH-002 — normes avec `_source`, tests de cohérence.
- [ ] ARCH-003 — schémas versionnés, fichier malformé arrêté.
- [ ] Documentation : `docs/domain/steel.md` (nouveau), `docs/ui/tab-steel.md` (nouveau), `docs/ui/window.md`, `docs/domain/positions.md`, `docs/decisions.md` (D-04), `CHANGELOG.md`, «Nouveautés» fr/de/en, catalogue des tests.
- [ ] Tests : nouveaux fichiers `tests/test_steel_*.py` ajoutés au catalogue, suite complète verte.

## 12. Traçabilité

| Source | Élément | Statut |
|---|---|---|
| T1 | UI-001 | capturé |
| T2 | REQ-006…012 (cas de test) | capturé |
| T3 | UI-001, REQ-005 | capturé |
| T4 | REQ-001, CON-002 | capturé |
| T5 | D-01, UI-003 | décision |
| T6 | D-02, REQ-001, REQ-003 | décision |
| T7 | D-03, REQ-003, UI-002, Q-003, Q-004 | décision + questions |
| T8 | D-04, REQ-001 | décision |
| T9 | D-05, REQ-004 | décision |
| T10 | D-06, REQ-010…012, Q-008 | décision + question |
| T11 | §8 | hors périmètre |
| T12 | D-07, CON-001, Q-007 | décision + question |
| T13 | Q-001 | ambigu → question (lots) |
| T14 | REQ-001, D-04 | capturé |
| T15 | REQ-002 | capturé |
| T16 | REQ-005…009, Q-007 | capturé |
| T17 | REQ-010…012 | capturé |

### Points de la source non résolus

- aucun (Q-001…Q-008 répondues le 2026-10-12).

## 13. Revue d'architecture

Trois revues `architecture-reviewer` en parallèle (12.10.2026) : profilés et normes, vérifications et rapport, assemblages. Verdict des trois : **APPROUVER AVEC RÉSERVES**. Les réserves qui demandaient un choix de l'ingénieur sont tranchées (D-16, D-17, D-18).

### Modules concernés

- `calc/norms/szs_c5.py` (codes EDV seuls aujourd'hui), `calc/norms/sia263.py` (Tab. 1, Tab. 2, `band_for`, `steel`), `calc/domains/section.py` (`FORMS`, `CODES`, `kind_of`, `_steel`, `parse`, `area_mm2`, `sides`), `calc/tools/section_fields.py`, `calc/project.py` (`SOURCE_FOLDERS`, `*_dir`), `calc/renumbering.py:172`, `calc/export_all.py` (préparation des domaines, graines vides), `schemas/position.schema.json` (`section_type` libre).
- `calc/domains/member_check.py` (bois seul ; forme de ligne `{key, symbol, value, unit, formula}` réutilisable), `calc/tools/member_check_tab*.py` (`MemberCheckTab`), `calc/tools/woodcore_gui.py` (`TABS`, `NAV_GROUPS`, `NAV_SECTIONS`, `WRITERS`), `calc/tools/chrome.py` (`ICONS`).
- `lib/calc-engine.typ` (`show-calc`, `show-connector-resistance`, `instance-ids`/`resolve-source`), `lib/summary.typ:142-167` (Nachweisübersicht par domaines `<membre>-verify-<check>`), `lib/shown-variables.json`.
- `calc/domains/schema.py`, `schema_geometry.py` (`fastener_places`, `element_section`, `element_bbox`), `calc/domains/connection.py` (`polar_moments`, `fastener_forces`), `calc/domains/connector.py` (#48 : tôle non vérifiée).

### Existant à réutiliser

- Le chargeur de `sia263.py` (cache, contrôle d'édition entre fichiers, `check_all`) pour les tables C5, en étendant `szs_c5.py` sur place.
- `section.FORMS` comme seule table des dimensions ; `sia263.band_for`/`steel` pour la nuance.
- La chaîne des connecteurs, déjà «Python une fois, Typst imprime» : export `vars`/`steps` lu par `show-calc` (niveaux 1/2/3, −1 et `shown:`, formules en lettres puis en nombres, citations).
- `MemberCheckTab` (liste à dossiers, cartes, liens aux variables, vues Calcul/Affichage, `view_state`), `source_archive`, `identity`, `cards`, `grouped_list`, `links.check_links`.
- `schema_geometry.fastener_places`, `connection.polar_moments`/`fastener_forces` pour un groupe de boulons excentré ; `schema_svg` pour la figure d'un assemblage saisi par formulaire (schéma en mémoire, jamais écrit dans `details/`).

### Risques et suite donnée

| Risque | Gravité | Suite |
|---|---|---|
| ARCH-RISK-101 — `USR` casse le modèle de `section.py` (tout code non bois y est un code C5 à dimensions numériques) | bloquant | Troisième genre `"user"`, champ `id` textuel dans `FORMS`, `parse` reste pur ; l'export résout l'ID dans `profiles_dir` et s'arrête en nommant position et fichier ; revue des consommateurs de `kind == "steel"` (étape 3). |
| ARCH-RISK-102 — contrats | important | `schemas/profile-source.schema.json` 1.0 ; `position.schema.json` 1.5 additif ; propriétés calculées à l'export, jamais stockées dans la source. |
| ARCH-RISK-103 — profilé cité renommé/supprimé | important | D-16 : refus tant qu'il est cité ; un ID de profilé ne peut pas être une désignation C5. |
| ARCH-RISK-104 — tables C5 en double / OCR bruité | important | Valeurs seulement dans `calc/norms/szs-c5-2021-<famille>.json` ; le classeur de référence seulement dans les tests ; contrôle interne par ligne (A recalculé depuis h, b, t_w, t_f, r) ; `FORMS` et tables tenus égaux par test. |
| ARCH-RISK-105 — limite 40 mm, rôles des parois | important | Bande lue dans Tab. 1 (`band_for`) ; énumération des rôles définie une fois (domaine + schéma, tenus égaux). |
| ARCH-RISK-106, 208 — `WRITERS`, chaînes, couleurs | mineur | Nouveaux noms d'écriture dans `WRITERS`, testés en lecture seule ; mots dans `calc/i18n`, couleurs dans `theme.json`. |
| ARCH-RISK-201 — D-09 face au «calculé deux fois» du bois | important | Pas de contradiction (précédent : connecteurs, neige, vent) ; entrée `docs/decisions.md` qui le dit et nomme ce qui est perdu (le rapport ne recalcule pas une valeur modifiée à la main). |
| ARCH-RISK-202 — pas de second moteur d'impression | important | D-17 : `#show-check-steel` mince au-dessus de `show-calc`. |
| ARCH-RISK-203 — Nachweisübersicht et registre | important | `show-check-steel` publie η et les résultats dans `"<id>-verify-steel-<genre>"` (modèle `timber-store`) ; mots `summary.verify.steel-*` ; export reproductible octet pour octet. |
| ARCH-RISK-204 — i18n des lignes | important | L'export porte des clés de glossaire (libellés, articles), jamais du texte ; Typst les résout ; symboles mathématiques tels quels. |
| ARCH-RISK-205 — `MemberCheckTab` propre au bois | important | Généralisation unique (domaine, dossier, `new_source`/`check_source`/`compute`/`export` en attributs) derrière les tests existants, avant les onglets acier ; pas d'aperçu Typst du brouillon pour l'acier. |
| ARCH-RISK-206 — classe → autres vérifications | important | `steel_section.classify` est la seule fonction ; toutes les vérifications l'appellent. |
| ARCH-RISK-207, 309 — navigation, session «feu» concurrente | important | Tuple `("nav_steel", …)` avant `nav_reference`, `nav_safety` non touché ; tests de comptage mis à jour en coordination (SendMessage). |
| ARCH-RISK-209 — `USR`, `renumbering`, `SOURCE_FOLDERS` | important | `steel/` et `profiles/` dans `SOURCE_FOLDERS` ; `renumbering` couvre `steel_dir`. |
| ARCH-RISK-210 — obligations de la commande Typst | mineur | `///`, deux exemples, `commands.json`, `shown-variables.json`, `docs/typst/command-docs.md`. |
| ARCH-RISK-211 — η ou M_cr donnés (D-14) | mineur | Un champ optionnel exclusif, validé comme `a`/`sigma_m_crit`. |
| ARCH-RISK-301 — éq. (76) planifiée deux fois (#48 et REQ-010) | bloquant | Une seule fonction `bearing_resistance` et un seul fichier `calc/norms/sia263-2013-6.1.4-lochleibung.json` ; la spec `2026-10-12-audit-issues-47-48-49` (*specified*) la construit pour les connecteurs bois ; le lot 3 l'utilise si elle a abouti, la crée sinon sous ce nom et le dit à l'autre session. |
| ARCH-RISK-302 — deux sources de géométrie | important | `method` immuable ; bloc `form` (rangées, e1, e2, p1, p2, d, d0, t) ou bloc `schema` (`{schema, plate_elements, bolt_markers, welds}`) ; espacements dérivés des coordonnées, jamais stockés ; un `Layout` commun après l'entrée. |
| ARCH-RISK-303 — données de boulon hors du schéma | important | Classe, d, d0, précontrainte dans la source acier ; un marqueur sans diamètre avertit et rend la vérification non calculable. |
| ARCH-RISK-304 — soudure absente des schémas | important | D-18 : entité soudure ajoutée (schéma de détail 1.3, additif, `check_source` étendu). |
| ARCH-RISK-305 — figure d'un formulaire | important | Schéma en mémoire rendu par `schema_svg`, pas de nouveau moteur SVG. |
| ARCH-RISK-306 — renommer un schéma cité | important | Le renommage d'un schéma réécrit les sources acier qui le nomment (modèle `schema.rename`). |
| ARCH-RISK-307 — d0 | mineur | Saisi ou `bolt.d0` ; jamais de jeu implicite hors `calc/norms/`. |
| ARCH-RISK-308 — variantes du joint | mineur | Un champ `variant` (éclisses / cornières), vérifications communes partagées. |

### Approche recommandée

Domaines sans Qt : `profile.py` (rectangles, modèles, `properties(section)` commun C5/USR), `steel_section.py` (classes), `steel_check.py` (source, résolution, export, lignes), `steel_resistance.py`, `steel_stability.py`, `steel_joint.py`. Export `data/steel.json` au format de `show-calc`. Une commande `#show-check-steel`. `MemberCheckTab` généralisé une fois, puis des sous-classes minces.

### Verdict

**APPROUVER AVEC RÉSERVES** — réserves intégrées au plan (§14).

## 14. Plan d'implémentation

Trois lots (D-08), chacun testé puis commité ; « Pousser ? » n'est demandé qu'à la fin du lot 3. Articles et équations relus dans `SIA263-2013-DE.pdf` à chaque étape ; valeurs C5 lues sur un rendu des pages de `SZS-C5-2021.pdf`, contrôlées contre le classeur de référence.

**Lot 1 — profilés, nuances, classe de section, résistances en section (#50, une partie de #51)**

1. **Normes.** `calc/norms/szs-c5-2021-<famille>.json` pour les 19 familles ; `szs_c5.py` étendu (`families`, `sizes`, `profile`, `edition`). E, G (3.2), limites Tab. 5a/5b, γ_M1/γ_M2 relus et transcrits ; `sia263.py` étendu. → REQ-001, REQ-002, ARCH-002. Tests : `tests/test_steel_profiles.py`, tests des normes.
2. **Profilé libre.** `calc/domains/profile.py` : rectangles, rôles (énumération unique), modèles I/U/T/L/tube, A, centre, I, W_el, axes plastiques, W_pl ; `properties(section)` commun. `schemas/profile-source.schema.json` 1.0 ; `profiles` dans `SOURCE_FOLDERS`. → REQ-003, ARCH-001, ARCH-003.
3. **Section `USR`.** Genre `"user"` dans `section.py`, export qui résout l'ID, `position.schema.json` 1.5, refus D-16, consommateurs de `kind == "steel"`, `area_mm2`/`sides`, docstrings. → REQ-003, REQ-004. Tests : `tests/test_section.py`.
4. **Domaine des vérifications.** `steel_check.py` (source `steel/<id>.json`, `steel-source` 1.0, résolution depuis la position ou saisie, `calculable`/`reason`, export `data/steel.json` `steel` 1.0, graine vide, `renumbering`), `steel_section.py` (`classify`), `steel_resistance.py` (traction, compression, flexion simple et biaxiale, M+N (44)–(48), V (41), M+V (43)/(53), classes 1–2 / 3). → REQ-004…006. Tests : `tests/test_steel_check.py`, `tests/test_steel_export.py`.
5. **Rapport.** `#show-check-steel` (sur `show-calc`, η publié, Nachweisübersicht), trois langues, `///`, deux exemples, `commands.json`, `shown-variables.json`, exemples dans `tests/projet-exemple/`. → REQ-013. Tests : `tests/test_steel_report.py`.
6. **Fenêtre.** Généralisation de `MemberCheckTab` (tests existants verts d'abord) ; groupe `nav_steel` avant `nav_reference`, trois sous-titres, en coordination avec la session «feu» ; onglets Profilés (bibliothèque + éditeur : saisie, dessin à la souris, modèle chargé), Classe de section, Traction, Compression, Flexion, Effort tranchant ; icônes, `WRITERS`. → UI-001…003. Tests : `tests/test_steel_tab.py`, `test_chrome.py`, `test_editor_buttons.py`, lecture seule.
7. **Documentation et commit du lot 1.** `docs/domain/steel.md`, `docs/ui/tab-steel.md`, index, `window.md`, `positions.md` §7, `decisions.md` (D-04, D-09), catalogue des tests, `CHANGELOG.md`, «Nouveautés» fr/de/en ; suite complète ; commit.

**Lot 2 — stabilité (#51)**

8. `steel_stability.py` : flambement 4.5.1 (Fig. 7 / Tab. 8, χ), déversement 4.5.2 (laminé/soudé, η(ψ) Fig. 41, ou η / M_cr donnés), N‑M (49)–(51) et (54) ss. ; tables transcrites dans `calc/norms/`. → REQ-007…009. Tests : feuilles Knicken, Kippen (linéaire), N‑My, N‑Mz, N‑My‑Mz de l'Excel I.
9. Onglets Flambement, Déversement, Interaction N‑M ; docs ; suite ; commit du lot 2.

**Lot 3 — assemblages (#52)**

10. **Soudure dans les schémas** (D-18) : entité soudure (a, longueur, type, entre deux éléments), outil «Soudure» de «Schémas», schéma de détail 1.3 additif, dessin `schema_svg`. Tests `tests/test_schema*.py`.
11. `steel_joint.py` : `layout_from_form` / `layout_from_schema` → `Layout` commun ; `method` immuable ; boulons 6.2 (dont éq. (76) par la fonction unique coordonnée avec la spec #47–#49), soudures 6.3, joint de cisaillement (`variant`, forces par `connection.fastener_forces`) ; figure d'un formulaire par schéma en mémoire ; renommage d'un schéma cité. → REQ-010…012. Tests : `tests/test_steel_joint.py` (cours 007, 008, 009 dont le Gerbergelenk ; formulaire et schéma donnent le même résultat).
12. Onglets Boulons, Soudures, Joint de cisaillement (choix formulaire / schéma à la création) ; docs ; `verify-requirements` ; `finish` (suite, commit, « Pousser ? »).

## 15. Vérification

_(à venir)_

## 16. Journal d'avancement

| Date | Statut | Fait / reste |
|---|---|---|
| 2026-10-12 | draft | spécification extraite des issues #50–#52 et des réponses de `/issue` ; 8 questions ouvertes |
| 2026-10-12 | specified | Q-001…Q-008 répondues → D-08…D-15 |
| 2026-10-12 | reviewed | trois revues d'architecture (APPROUVER AVEC RÉSERVES), réserves tranchées D-16…D-18, plan en trois lots |
| 2026-10-12 | approved | approuvée par l'ingénieur ; lot 1 commence |
| 2026-10-12 | implementation | lot 1 étape 1 : 15 tables SZS C5 (1038 profilés) dans calc/norms/szs-c5-2018-profile-*.json, lecteur szs_c5.profile(), 7 anomalies du livre listées ; SIA 263 3.2.2.3, 4.1.3, Tab. 5 ; tests/test_steel_profiles.py (8) → REQ-001, REQ-002, ARCH-002 |
| 2026-10-12 | implementation | lot 1 étapes 2-3 : calc/domains/profile.py (rectangles, modèles I/U/T/L/RHS/plaque, rôles, propriétés élastiques et plastiques, from_c5, source profiles/<id>.json, cited_by) ; schemas/profile-source.schema.json 1.0 ; section USR (genre user) et IPE h×m ; position 1.5 pour USR, export qui résout le profilé ; project profiles_dir, steel_dir ; tests/test_steel_free_profile.py (6), test_section.py mis à jour → REQ-003, REQ-004 (partie), ARCH-RISK-101/102 |
| 2026-10-12 | implementation | lot 1 étapes 4-5 : calc/domains/steel_section.py (parois, aires de cisaillement, classify selon Tab. 5a/5b, classe 4 refusée), steel_resistance.py ((38)–(48), (52)–(54)), steel_check.py (source steel/<id>.json 1.0/1.1, export data/steel.json 1.0) ; lib/steel.typ `#show-check-steel`, `check-steel-ids` ; libellés allemands dans le glossaire ; tests/test_steel_check.py (8) → REQ-004…REQ-006, REQ-013, ARCH-001, ARCH-003 |
| 2026-10-12 | implementation | lot 1 étape 6 : groupe «Acier» (Section · Sécurité structurale), ProfileTab (rectangles, rôles par délégué, dessin, C5, refus d'un profilé cité), SteelCheckTab ×5 sur MemberCheckTab généralisé (DOMAIN, NORM_PREFIX, POSITION_HINT_KEY) ; IPE 360 S355 en classe 4 confirmé par l'ingénieur ; tests/test_steel_tab.py (8) → UI-001…UI-003, REQ-003, REQ-004 |
| 2026-10-12 | implementation | lot 1 étape 7 : docs/domain/steel.md (§3.3quatervicies), docs/ui/tab-steel.md, positions.md §7, decisions.md (D-04, D-09 ; v0.94 partiellement remplacée), api-conventions, catalogue des tests, CHANGELOG, Nouveautés 0.118 fr/de/en ; exemples regelés ; reste : suite complète, commit du lot 1 |
