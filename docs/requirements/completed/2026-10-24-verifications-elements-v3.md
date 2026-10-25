---
id: 2026-10-24-verifications-elements-v3
titre: Vérifications d'éléments — quatre onglets, cisaillement en trois figures, matériau de la bibliothèque (prototype V3 validé)
status: completed
cree: 2026-10-24
mis_a_jour: 2026-10-25
source: issue GitHub #112 (prototype « Vérifications d'éléments, troisième version », validé par l'ingénieur le 24.10.2026, variante A du matériau)
docs: [docs/domain/member-checks.md, docs/domain/materials.md, docs/ui/tab-member-checks.md, docs/ui/building-a-tab.md, docs/ui/calc-tab.md, docs/ui/window.md, docs/architecture/principles.md, docs/decisions.md]
---

# Vérifications d'éléments — V3 — Spécification

## 1. Objectif

Refaire les quatre onglets de vérification d'éléments de la SIA 265 chapitre 4 (Traction, Compression, Flexion, Cisaillement) d'après le prototype V3 validé : accordéons, en-tête compact avec une bulle de matériau, résultats dans l'ordre du calcul, schéma SIA de la flexion, cisaillement en trois figures au lieu d'une liste déroulante, vue Affichage qui montre le rendu Typst réel. Le matériau d'une vérification n'est plus une classe de la liste fixe de la SIA 265 mais un matériau de la bibliothèque de l'onglet Matériaux (#110) — bois massif, lamellé-collé, bois personnel, **panneaux** (SIA 265/1) —, choisi dans un menu, la sollicitation étant toujours dite dessous (variante A).

Le calcul existe en Python (`calc/domains/member_check.py`) et le prototype n'est qu'une traduction de celui-ci : cette spécification décrit ce que la fenêtre montre et ce que la source enregistre, et ce qui s'ajoute au calcul (le matériau de la bibliothèque, les panneaux).

## 2. Source

La source, mot pour mot et coupée en points T, est dans [docs/history/2026-10-24-verifications-elements-v3-source.md](../../history/2026-10-24-verifications-elements-v3-source.md) (déplacée le 25.10.2026 pour tenir la spec sous 100 KB ; rien n'y est changé).

## 3. Exigences fonctionnelles

**État actuel relevé dans le code (arbre de travail, master `a9cae26` plus des modifications non commitées d'autres sessions).**
- Les **quatre onglets existent déjà comme onglets séparés** : `tab_registry.SPECS` porte `tab_mc_tension`, `tab_mc_compression`, `tab_mc_bending`, `tab_mc_shear`, mais aussi `tab_mc_buckling` (Flambage) et `tab_mc_ltb` (Déversement), plus `tab_mc_fire`. Les mots d'`tab_mc_shear` disent encore « Effort tranchant / Schub ».
- `MemberCheckTab` (`calc/tools/member_check_tab.py`, 853 lignes) dérive de `SourceEditorTab` : ce n'est **pas** encore l'onglet type « Calcul » (`docs/ui/building-a-tab.md`, « Where the tabs stand »). La neige, le poids propre et le vent y sont ; `docs/ui/calc-tab.md` annonce les vérifications d'éléments comme « `CalcTab` avec une carte « Position » et un verdict, chacune un service » (D-05 de la spec de l'issue #95).
- `ShearTab` choisit entre `shear`, `shear-off`, `shear-perp` par `variant_box` (`SHEAR_VARIANTS`, Q-010 de `docs/requirements/completed/2026-10-21-commandes-typst-refonte.md`) ; la source et `compute` connaissent déjà les trois (`_compute_shear_v`, `_compute_shear_off`, `_compute_shear_perp`).
- Le matériau est `grade` dans la source (`member-check-source` 1.0 ; 1.1 avec `links` ; 1.2 avec `fire`), une classe de `sia265.grades()` (C16 à GL32h), `grade_box` dans `member_check_tab_form.py` ; `resolve` le suit depuis la position (`strength_class`, sinon `material`) ; `compute` lit `sia265.grade(record["grade"])` pour les résistances, les facteurs η_w et η_t, la famille (k_a, β_c, moelle) et les valeurs de la stabilité (`f_c_0_k`, `E_0_05`, Anhang B).
- L'export `checks` va jusqu'à 1.6 (`checks.schema.json`). Le projet d'exemple compte 13 vérifications (`tests/projet-exemple/000-Woodcore/sources/checks/` : BI-01 à 03, DR-01/02, FE-01/02, KI-01/02, KN-01, SC-01, ZT-01/02).
- Le fichier de la vérification (`Timber-checks/<Sorte>/<id>.typ`, dossier par genre) est écrit par `unfold._generate_member`, hors de `AUTO_REGENERATE` : une ligne que l'ingénieur n'a pas modifiée suit l'export, une ligne modifiée se règle par « Régénérer ». L'Affichage du type « Calcul » (`calc_display.DomainDisplay`, `domain_file_display`) écrit les options d'une ligne **dans le fichier** (`unfold_display.set_display`).
- La bibliothèque (#110, commit `a9cae26`) : `materials_contract` (types `member`, `panel`, `other`), `materials_catalogue` (ids `sia265:<classe>`, `sia265-1:<produit>`), `materials_derive` (`member_design`, `panel_design`, `panel_factors`, `unavailable`, `missing`), `materials_search`, `materials_user` (`u-<8 hex>`), `materials_project` (copie du projet ; `used_ids` ne lit aujourd'hui que le poids propre). `materials_derive.available_in` dit **« à venir »** pour `tab_mc` d'un bois personnel et ne cite **aucun** usage `tab_mc` pour un panneau (seulement `tab_plates`, « à venir »).
- SIA 265/1 : `calc/norms/sia265_1.py` et un fichier par tableau (`sia265-1-2018-tab19-osb3.json` : Tableaux 19a et 19b, colonnes d'épaisseur `(t_min, t_max]`, `from_inclusive`, grille `plate | shear | axial` × `par | perp`, valeurs `_k` et `_d`).

### REQ-001 — Contrat de la source : `material`, `loading`, `display`
- **Exigence** : Woodcore doit lire et écrire, dans `member-check-source`, un champ `material` (l'identifiant d'un matériau de la bibliothèque, `null` pour suivre la position), un champ `loading` (la sollicitation d'un panneau : `plaque`, `voile` ou `tc` — traction/compression —, et la direction `par` ou `perp`), pour un panneau seulement `kled` (durée de chargement, absent = moyenne) et `accidental` (booléen, absent = faux) — les options de REQ-006 — et un objet `display` (les options de l'Affichage, REQ-010). Un champ vide **est absent** (pas de `null` écrit) : « suit la position » = pas de `material`. `impact` (η_t, déjà là) reste le champ de la barre. `schema_version` **monte à 1.3** (la source, `schemas/member-check-source.schema.json`) ; les sources 1.0, 1.1 et 1.2 sont lues telles quelles, `grade` restant lu. Selon la convention de `stamp_version` (la plus basse version qui porte ce que la source contient), 1.3 n'est écrite que là où la source porte `material`, `loading` ou `display`. Une source qui porte `grade` et `material` à la fois est refusée en nommant le fichier et le champ ; `loading`, `kled` et `accidental` ne sont admis que pour un panneau, `impact` que pour une barre.
- **Source** : T56, T57, T69
- **Priorité** : doit
- **Critère d'acceptation** : `tests/test_member_check.py` lit les 13 sources du projet d'exemple sans les modifier (version inchangée) ; une source 1.3 valide s'écrit et se relit ; `grade` + `material`, `loading` sur une barre, une version inconnue sont refusés en citant fichier et champ ; le schéma JSON valide les trois cas.

### REQ-002 — Identifiant stable et copie dans le projet
- **Exigence** : le matériau d'une vérification est nommé par l'identifiant de la bibliothèque (`sia265:C24`, `sia265-1:osb3`, `u-xxxxxxxx`), jamais par son nom. Un matériau **personnel** nommé par une vérification est copié dans le projet à l'enregistrement, comme pour les couches du poids propre (D-11 de #110) : `materials_project.used_ids` lit aussi les sources des vérifications, et la vérification se calcule depuis la copie du projet seule, à l'identique sur un autre poste. Un matériau livré n'est pas copié (il se lit du Woodcore qui calcule). Un identifiant inconnu (matériau supprimé de la bibliothèque, copie absente) rend la vérification non calculable avec une raison nommant l'identifiant. L'avertissement « la bibliothèque a changé » de #110 s'applique aux vérifications comme aux couches.
- **Source** : T69, T56, principe « une seule source » (CLAUDE.md règle 1)
- **Priorité** : doit
- **Critère d'acceptation** : test : une vérification nommant un bois personnel fait entrer sa copie dans `Woodcore-Datei/materials.json` à l'enregistrement et se calcule, la bibliothèque de l'ingénieur absente ; un identifiant inconnu donne la raison ; un test de `tests/test_materials_*` garde la liste des identifiants livrés (ceux qu'une source peut nommer).

### REQ-003 — Résistances d'un bois en barre, lues de la bibliothèque
- **Exigence** : `compute` doit lire les résistances d'un bois en barre du **matériau choisi** : pour une classe livrée (`sia265:<classe>`), comme aujourd'hui depuis `sia265` (Tabellen 8 et 9, y compris les cinq valeurs de f_c,90,d, les valeurs d'Anhang B de la stabilité) ; pour un bois personnel, par ses valeurs de dimensionnement (`materials_derive.member_design` : saisies, fixées par la norme ou déduites) et sa famille (`softwood`, `hardwood`, `glulam`), qui donne k_a, β_c et l'effet de la moelle. Les 13 vérifications du projet d'exemple restent **inchangées au bit près**.
- **Source** : T18, T58, T61
- **Priorité** : doit
- **Critère d'acceptation** : `tests/test_member_check.py` : C24 et GL24h par `material` donnent les mêmes lignes et les mêmes taux que par `grade` ; un bois personnel complet se calcule, avec la provenance (« saisie », « fixée par la norme », « déduite ») dans la ligne de la clause ; les 13 taux du projet d'exemple sont identiques avant et après.

### REQ-004 — Résistances d'un panneau, selon sa sollicitation et la plage de son épaisseur
- **Exigence** : `compute` doit lire les résistances d'un panneau de SIA 265/1 (`calc/norms/sia265_1.py`, les tableaux a et b du produit — « 19a et 19b » pour l'OSB/3, 11 à 23 pour les autres) selon la sollicitation (`plaque`, `voile`, `tc` × `par`, `perp`) et la **plage d'épaisseur** : la colonne dont `(t_min, t_max]` contient l'épaisseur (`from_inclusive` pour la première borne ; 18 mm est dans 10–18, 10 mm dans 6–10, 6 mm dans 6–10, 25 mm dans 18–25). La ligne de la clause cite la norme, le tableau, la page et la plage.
- **Source** : T18, T35, T37, T38, T58
- **Priorité** : doit
- **Critère d'acceptation** : tests pour l'OSB/3 en flexion : plaque ∥ 9,6 / ⊥ 4,8, voile ∥ 5,5 / ⊥ 4,1 (10–18 mm), les autres plages (10,5 / 5,3 / 5,8 / 4,2 et 8,6 / 4,3 / 5,3 / 4,0), les trois épaisseurs limites 6, 10, 18, 25 mm ; le calcul de BI-04 (OSB/3 1000 × 18 mm, M_y,d = 0,4 kNm, classe d'humidité 1, KLED moyenne) donne 77,2 % (σ = 7,407 / 9,6), la valeur du tableau b.

### REQ-005 — Ce que chaque vérification lit, et la raison d'un refus
- **Exigence** : le domaine doit déclarer, par genre de vérification et par sollicitation, **les grandeurs de matériau qu'elle lit** (tableau à écrire à l'implémentation : par ex. traction f_t,0,d et f_t,90,d à un angle ; compression f_c,0,d, f_c,90,d et ses cinq cas ; flexion f_m,d, et f_t,0,d / f_c,0,d avec un effort normal ; cisaillement f_v,d ; cisaillement d'about f_v,d et k_a de la famille ; avec contrainte ⊥ f_v,d, f_t,90,d, f_c,90,d ; stabilité f_c,0,k et E_0,05). Une vérification dont le matériau n'en donne pas une — ou dont le produit n'admet pas la classe d'humidité choisie (SIA 265/1 tableau 9 : OSB/3 n'a pas de classe 3) — est **non calculable**, avec sa raison : le nom du matériau, la sollicitation, la grandeur qui manque (« OSB/3 en plaque ∥ ne donne pas toutes les résistances de cette vérification (compression) : … »). Ce tableau sert aussi à la ligne de chaque entrée du menu (UI-005), à la grisure d'une bulle sans valeur (UI-006) et à `available_in` (REQ-012) : il est écrit une fois, côté domaine, sans Qt.
- **Source** : T34, T35, T39, T59, T67
- **Priorité** : doit
- **Critère d'acceptation** : tests : un panneau en compression ⊥ au fil (angle > 0), en stabilité ou en cisaillement d'about n'est pas calculable et dit pourquoi ; un bois personnel sans f_t,90,d (non fixé, non déduit) refuse le cisaillement avec contrainte ⊥ ; un bois personnel sans E_0,05 refuse la stabilité ; la raison cite matériau, sollicitation et grandeur dans les trois langues.

### REQ-006 — η_t, η_w, γ_M : options de toute vérification, règle de la norme
- **Exigence** : l'ingénieur (Q-002, 24.10.2026) veut que η_t, η_w et γ_M multiplient les résistances de **toute** vérification, barre ou panneau, et se **choisissent dans des listes déroulantes** (UI-015). Leurs valeurs et leur manière d'entrer dans f_d sont celles que les normes lues prescrivent (`ExternalFiles/000-Normes/`, SIA 265:2021 et SIA 265/1:2018), lues de `calc/norms/`, jamais écrites ici :
  - **barre** — f_d = η_M·η_t·η_w/γ_M · f_k (SIA 265 2.2.2, éq. 3). γ_M et η_M ne sont pas séparés : le Tableau 1 (2.2.5) donne leur rapport par matériau, 1,7 (bois massif, entures multiples, balkenschichtholz) ou 1,5 (lamellé-collé), **déjà contenu** dans les valeurs des Tableaux 8 et 9, établies « pour η_w = 1,0 et η_t = 1,0 » (3.3.2.1, 3.4.2.2). η_w : Tableau 4 (3.2.1.3), résistance 1,0 / 0,8 / 0,6 aux classes d'humidité 1 / 2 / 3 (Tableau 3). η_t : 1,0, ou 1,4 pour des actions assimilées à des chocs (2.2.6). f_d = valeur du tableau × η_w × η_t, comme aujourd'hui.
  - **panneau** — f_d = η_mod · f_k / γ_M, avec η_mod = η_M·η_t·η_w (SIA 265/1 6.1.2.1, éq. 5). η_t et η_w de la SIA 265 **n'existent pas** pour un panneau (SIA 265 2.2.6, Tableaux 1 et 4 renvoient à la SIA 265/1). η_mod est **un seul facteur** du Tableau 9 (6.2.1.1), par produit, classe d'humidité (seules celles que le produit admet) et KLED permanente / longue / moyenne / courte / très courte (Tableaux 7 et 8 ; chocs et séisme : très courte ; 6.2.1.4 : l'action la plus courte du cas de charge). γ_M : Tableau 6, par groupe de produit (OSB 1,2), **1,0 en situation accidentelle sauf séisme** (note 1). Le tableau b d'un produit donne la valeur de calcul pour la classe 1, la KLED moyenne et γ_M normal.
  - La ligne de chaque facteur dit sa valeur et sa clause ; **aucun k_h** pour un panneau (SIA 265/1 n'en contient pas, tenu par un test) ; E et G × 0,9 / 0,75 (6.2.1.2) sont hors lot (§8).
- **Source** : T65, T68, T37, Q-002
- **Priorité** : doit
- **Critère d'acceptation** : tests : barre inchangée (13 taux) ; η_t 1,4 et η_w 0,8 / 0,6 multiplient la valeur du tableau ; panneau classe 1, KLED moyenne, normale = valeur du tableau b (OSB/3 10–18 mm, f_m,d plaque ∥ 9,6) ; classe 2 ou KLED courte = η_mod · f_k / γ_M avec le η_mod du fichier de norme (Tableau 9 : OSB/3, classe 2, moyenne : 0,55) ; accidentelle : γ_M = 1,0 ; OSB/3 en classe 3 non calculable ; aucun k_h ; la clause citée est celle de SIA 265/1.

### REQ-007 — Épaisseur d'un panneau hors des plages
- **Exigence** : l'épaisseur d'un panneau (Q-003) hors des colonnes du tableau rend la vérification non calculable, avec la raison qui nomme l'épaisseur et **les plages du produit** ; la même erreur rouge est dite dans la rangée « Sollicitation » et dans l'état du calcul. Le plus petit côté n'est pas toujours celui que la sollicitation suppose (h en plaque, b en voile, T66) : une **note orange**, rien n'est refusé (Q-003).
- **Source** : T38, T59
- **Priorité** : doit
- **Critère d'acceptation** : test : OSB/3 de 5 mm et de 26 mm → non calculable, raison « plages 6–10, 10–18, 18–25 mm » ; 6, 10, 18 et 25 mm calculables.

### REQ-008 — σ₉₀,d hors de l'intervalle : une note orange
- **Exigence** : pour le cisaillement avec contrainte ⊥ (4.2.7.1), `compute` ou le domaine doit signaler σ_90,d hors de −f_c,90,d … f_t,90,d par une **note** (gravité « orange »), la vérification étant calculée quand même ; la note est un message (code, champ `sigma_90`, paramètres), comme les messages des domaines de l'onglet type.
- **Source** : T12, T49, T55, T60
- **Priorité** : doit
- **Critère d'acceptation** : test : σ_90,d = +5 N/mm² sur C24 (f_t,90,d bien inférieur) donne la note et un taux ; σ_90,d dans l'intervalle n'en donne pas.

### REQ-009 — Le fichier de la vérification cite la norme et le nom du matériau
- **Exigence** : `unfold._generate_member` doit écrire dans la ligne de l'élément le **nom du matériau** (dans la langue du document) et, dans les lignes de résistance, la norme et le tableau de ce matériau (SIA 265 tableau 8 ou 9 comme aujourd'hui ; SIA 265/1 tableau b du produit pour un panneau ; « bois personnel » pour un bois de l'ingénieur, avec sa source). Le nom du 4.2.6 imprimé reste « Cisaillement » (titre de la norme) ; la fenêtre dit « Cisaillement d'about ».
- **Source** : T11, T60
- **Priorité** : doit
- **Critère d'acceptation** : test : le fichier de BI-04 contient « SIA 265/1 » et « OSB/3 » ; celui de BI-01 reste identique à l'actuel ; le titre imprimé du 4.2.6 est « Cisaillement » dans les trois langues du rapport.

### REQ-010 — Les options de l'Affichage dans la source
- **Exigence** : les options de l'Affichage — le niveau du rapport (auto, 0 à 3), la ligne de l'élément (aucune, 1, 2, 3), le verdict en rapport ou en pourcent, imprimer la description, le titre — s'enregistrent dans `display` de la source (REQ-001) ; le générateur du fichier les lit. **Woodcore réécrit le fichier tant que l'ingénieur ne l'a pas modifié** (le mécanisme existant : une ligne que l'ingénieur n'a pas changée suit l'export) ; une ligne qu'il a modifiée à la main reste telle quelle et se règle par « Régénérer » (comportement actuel des vérifications, hors de `AUTO_REGENERATE`). Cela diffère de l'Affichage actuel des domaines de charges, qui écrit ses options dans le fichier (voir ARCH-005).
- **Source** : T13, T53, T54
- **Priorité** : doit
- **Critère d'acceptation** : test : changer le niveau écrit `display.level` dans la source et réécrit un fichier non modifié ; un fichier dont une ligne a été modifiée à la main n'est pas écrasé et signale l'écart ; sans `display`, le fichier est celui d'aujourd'hui.

### REQ-011 — La stabilité est l'accordéon de la compression et de la flexion (genre inchangé)
- **Exigence** (Q-001, réponse A) : l'accordéon « Stabilité » de la Compression (flambage, 4.2.8) et de la Flexion (déversement, 4.2.9) est le dernier, à option, désactivé par défaut (« vérifier la stabilité au flambage » pour la compression) ; le flambage affiche sa courbe, β est saisissable ou choisi par ses appuis (dont glissant et fixe à rotation seule). **Le genre reste** (`buckling`, `lateral-torsional`) : la case le fait passer de `compression` à `buckling` (de `bending` à `lateral-torsional`) **à l'enregistrement**, et la décocher le ramène ; l'id, la position, le matériau, la section et les efforts communs restent ; les longueurs et β sont gardés dans le brouillon tant que l'onglet est ouvert. L'onglet Compression liste `compression` et `buckling`, Flexion `bending` et `lateral-torsional` ; `tab_mc_buckling` et `tab_mc_ltb` quittent la navigation. Le **fichier de la vérification suit son genre** (dossier `Timber-checks/<Genre>/`) : il est **déplacé**, avec son entrée de la base de régénération, les lignes de l'ingénieur gardées — il n'en reste pas deux (ARCH-RISK-003). Un panneau ne se vérifie pas à la stabilité (T67), un bois personnel sans E_0,05 non plus (REQ-005).
- **Source** : T21, T24, T42, T45, T55, Q-001
- **Priorité** : doit
- **Critère d'acceptation** : KN-01 (flambage) et KI-01/02 (déversement) gardent leurs taux et leurs fichiers ; cocher la case sur DR-01 donne un `buckling`, un seul fichier (`Timber-checks/Buckling/DR-01.typ`), une ligne modifiée à la main gardée, et la décocher revient ; aucun avertissement « la stabilité n'est pas vérifiée » nulle part.

### REQ-012 — La bibliothèque dit que la vérification d'éléments lit ses bois et ses panneaux
- **Exigence** : `materials_derive.available_in` doit donner l'usage `tab_mc` (Vérifications d'éléments) **« oui »** pour un bois personnel complet et pour un panneau dont le tableau donne au moins une vérification possible (REQ-005), au lieu de « à venir » ; l'onglet Matériaux dit « à venir » seulement pour ce qui l'est encore (plaques et voiles de la structure, assemblages). Les mots de #110 qui disaient « les vérifications ne lisent que les classes de la SIA 265 » (Q-004 de #110) sont mis à jour.
- **Source** : T18, T72 (#110)
- **Priorité** : doit
- **Critère d'acceptation** : `tests/test_materials_domain.py` : `available_in` d'`osb3` et d'un bois personnel complet donne `tab_mc` « yes » ; d'un bois incomplet « no » avec la raison ; la fiche de l'onglet Matériaux n'écrit plus « à venir » pour les vérifications d'éléments.

### REQ-013 — Suivre la position, l'écraser, « Reprendre »
- **Exigence** : une vérification dont `material` est `null` **suit la position** : la classe de résistance de la position (`strength_class`, sinon `material` du classeur) est résolue en matériau livré `sia265:<classe>` ; une classe que la bibliothèque ne livre pas garde la raison actuelle (« la classe … n'est pas une classe de SIA 265 tableau 8 ou 9 »). Un `material` écrit **écrase** la position ; l'état du calcul le dit en orange (« Classe de résistance est écrasée (GL24h) alors que T001 dit C24. ») ; « Reprendre » remet `material` à `null`. La position **ne nomme pas** un panneau ni un bois personnel dans ce lot (§9).
- **Source** : T29, T30, T70
- **Priorité** : doit
- **Critère d'acceptation** : test : DR-01 sans `material` suit la position T001 (C24) ; avec `sia265:GL24h` il l'écrase et l'état le dit ; « Reprendre » rend `null` ; une position à classe inconnue garde le refus actuel.

### REQ-014 — Les lignes de résultat dans l'ordre du calcul, le cadre pointillé
- **Exigence** : `compute` doit rendre les lignes dans l'ordre où le rapport les imprime (déjà celui de `_lines`), η en dernier, et **marquer la ou les lignes qui gouvernent** un maximum (un côté, un axe : `governing_ratio`) pour que la fenêtre les cadre en pointillé ; la fenêtre ne recalcule ni ne réordonne rien.
- **Source** : T6, T51, T55
- **Priorité** : doit
- **Critère d'acceptation** : test sur BI-01 (flexion biaxiale) et KN-01 : la dernière ligne est η, la ligne marquée est celle qui porte le maximum ; test de fenêtre : le cadre pointillé est sur elle.

### REQ-015 — Ce que l'export garde du matériau (pour la Synthèse)
- **Exigence** : l'enregistrement de la vérification dans `checks.json` doit porter l'identifiant et le nom du matériau, la famille ou le produit, la sollicitation d'un panneau (`plaque ∥`…), l'épaisseur et la plage retenues, et d'où vient le matériau (position / écrasé), pour que l'onglet « Synthèse » (hors de cette spécification) puisse dire « OSB/3 en plaque ∥ ». `checks.schema.json` **monte à 1.7** (l'export), les versions 1.0 à 1.6 restant lues ; `grade` et `grade_from` restent écrits pour les lecteurs actuels (`build_reference`, `list_files`, `quantities`).
- **Source** : T71, T56
- **Priorité** : doit
- **Critère d'acceptation** : l'export des 13 vérifications reste valide au schéma ; celui de BI-04 porte le matériau et sa sollicitation ; les lecteurs actuels de `grade` passent leurs tests.

### REQ-016 — Le feu ne lit que les classes de SIA 265
- **Exigence** : une vérification en situation d'incendie (`fire`, issue #46) dont le matériau n'est pas une classe livrée de SIA 265 (un panneau, un bois personnel) est non calculable avec une raison nommant le matériau (SIA 265 4.5 ne s'applique qu'à ces classes dans ce lot) ; les FE-01/02 gardent leurs taux.
- **Source** : T72 (#46), principe « un matériau qui ne donne pas… » (T39) — inférée
- **Priorité** : doit
- **Critère d'acceptation** : test : FE-01 inchangée ; la même vérification avec `sia265-1:osb3` donne la raison.

## 4. Exigences d'interface (fenêtre, rapport, site)

### UI-001 — Quatre onglets, la barre ne nomme que l'onglet
- **Exigence** : la navigation de Sécurité structurale porte Traction, Compression, Flexion, Cisaillement, chacun sa liste à gauche, ses accordéons au centre, ses modules à droite ; la barre de la fenêtre ne nomme que l'onglet ouvert (« Sécurité structurale › Cisaillement ») ; `tab_mc_shear` s'appelle **« Cisaillement » / « Schub » / « Shear »** ; Flambage et Déversement quittent la navigation (Q-001 A, REQ-011). La synthèse n'est pas dans la barre.
- **Source** : T4, T10, T25, T26, T55
- **Langues** : fr / de / en
- **Critère d'acceptation** : `tests/test_tab_registry.py` et `test_i18n.py` : les clés, les trois langues ; un test de fenêtre : le titre de la barre est « Sécurité structurale › Cisaillement ».

### UI-002 — L'onglet est de l'onglet type « Calcul »
- **Exigence** : chacun des quatre onglets est une classe de paramètres sur le type « Calcul » (`calc_tab.CalcTab`) : liste, identité, formulaire déclaré en accordéons (sections), liens aux variables (bouton 𝑥 à droite de chaque valeur saisie, `LINKABLE`), modules du volet droit, « Calcul | Affichage ». Le domaine déclare (Qt-free) sa `declaration()`, ses `messages`, ses `results` ; les champs propres à la vérification d'éléments — la carte « Position », la bulle du matériau, la rangée « Sollicitation », le dessin — sont des services ou des types de champ écrits une fois, jamais copiés d'un onglet à l'autre.
- **Source** : T20, T23, T25, T27, principe « un onglet se construit à partir d'un type » (`docs/ui/building-a-tab.md`) — inférée
- **Langues** : fr / de / en
- **Critère d'acceptation** : `tests/test_tab_overrides.py` : les classes des quatre onglets ne portent que leurs paramètres ; `tests/test_calc_tab_base.py` passe ; chaque champ numérique ancien (`LINKABLE` : N, V_z, V_y, M_y, M_z, α, b, h, d, l, w, l_y, l_z, β_y, β_z, a, σ_m,crit) reste lié à une variable.

### UI-003 — La liste de gauche
- **Exigence** : les vérifications de l'onglet, **groupées par position** (« T001 · Poutre », « Sans position »), chacune avec son taux en pourcent, vert à 100 % ou moins, rouge au-delà, sans orange ; triées par position ou par taux ; les archives en bas ; « Nouveau » et « Dupliquer ». Un id reste unique tous genres confondus (un seul dossier de sources).
- **Source** : T22, T28
- **Langues** : fr / de / en
- **Critère d'acceptation** : test de fenêtre sur le projet d'exemple : DR-01 sous sa position, taux coloré, tri par taux ; une vérification non calculable n'a pas de taux et le dit.

### UI-004 — L'en-tête « Élément » et ses bulles qui suivent ou écrasent
- **Exigence** : le nom, l'id, « + description », la position (liste), puis la rangée de bulles — le matériau, la section, la classe d'humidité, la case « chocs ou séisme · η_t = 1,4 » avec son ⓘ (2.2.6). Une bulle qui suit la position est **grise** avec l'id de la position à droite ; écrasée elle est **orange** avec « Reprendre ». Le résumé de l'accordéon fermé : « T001 · C24 · 100 × 200 · classe d'humidité 2 ».
- **Source** : T29, T30, T31, T62
- **Langues** : fr / de / en
- **Critère d'acceptation** : test de fenêtre : la bulle du matériau de DR-01 est grise « C24 · T001 », orange après un choix, « Reprendre » la rend grise ; le résumé fermé est celui du texte.

### UI-005 — La bulle du matériau et son menu
- **Exigence** : la bulle montre le **nom court** (« C24 », « GL24h », « OSB/3 en plaque ∥ ») ; un clic ouvre, sous la rangée, le menu de la bibliothèque (#110) : un champ de recherche (`materials_search.search` : noms fr/de/en, groupe, source) ; en tête le matériau de la position (« suit T001 ») ; puis les groupes de l'onglet Matériaux — Bois massif · SIA 265 tableau 8, Lamellé-collé · SIA 265 tableau 9, Panneaux · SIA 265/1, Personnel — et **Bois sans résistance : un poids seulement**, grisé, non choisissable. Chaque ligne montre la résistance que l'onglet ouvert lit (f_m,d en Flexion, f_t,0,d en Traction, f_c,0,d en Compression, f_v,d en Cisaillement) ; un panneau montre ses valeurs par sollicitation (« p∥ 9,6 · p⊥ 4,8 · v∥ 5,5 · v⊥ 4,1 ») et la source (SIA 265, SIA 265/1, Perso). Une ligne dont le matériau ne donne pas la résistance de l'onglet l'indique (REQ-005) au lieu d'un nombre. Les regroupements et les noms viennent de `materials_*`, rien n'est recopié.
- **Source** : T32, T33, T34, T62
- **Langues** : fr / de / en
- **Critère d'acceptation** : test de fenêtre : la recherche « OSB » trouve `sia265-1:osb3` ; « panneau » trouve les panneaux (en fr, de, en) ; les groupes sont dans l'ordre du texte ; la ligne d'`osb3` en Flexion porte « p∥ 9,6 · p⊥ 4,8 · v∥ 5,5 · v⊥ 4,1 » ; un matériau `other` est grisé et non choisissable ; une capture visuelle est comparée au prototype.

### UI-006 — La rangée « Sollicitation » et la ligne « La vérification lit »
- **Exigence** : sous la bulle, la rangée « Sollicitation » est **toujours là**. Un panneau : ses bulles **telles que validées pour l'OSB/3 — elles ne changent pas** : en Flexion « en plaque ∥ 9,6 », « en plaque ⊥ 4,8 », « en voile ∥ 5,5 », « en voile ⊥ 4,1 » ; en Traction et en Compression « en traction / compression ∥ » et « ⊥ » ; en Cisaillement « en plaque ∥ », « en voile ∥ » ; une bulle sans valeur est grisée. Un bois en barre : une seule bulle, cochée, non cliquable, « flexion f_m,d = 14,1 » (et sa grandeur pour l'onglet). Dessous, une ligne : « La vérification lit f_m,d = 9,6 N/mm² · SIA 265/1:2018, tableaux 19a et 19b, plage 10–18 mm · épaisseur 18 mm, le plus petit côté de la section · × η_w · η_t », la fin selon REQ-006 (barre : « × η_w · η_t » avec leurs valeurs ; panneau : « η_mod 0,70 (Tableau 9, classe 1, KLED moyenne) · γ_M 1,2 (Tableau 6) », ou le tableau b seul à la classe 1, KLED moyenne, situation normale) ; une valeur déduite dans l'onglet Matériaux est marquée « (déduite) ». La rangée et l'état disent en rouge l'épaisseur hors des plages avec les plages (REQ-007). Un clic sur une bulle écrit `loading` ; pour un panneau, **α n'est pas proposé** (la direction remplace l'angle) et un effort à angle sur panneau n'existe pas (REQ-005).
- **Source** : T2, T19, T35, T36, T37, T38, T40
- **Langues** : fr / de / en
- **Critère d'acceptation** : test de fenêtre : le texte des bulles d'`osb3` en Flexion, Traction, Compression et Cisaillement est exactement celui de T35 ; pour C24 une seule bulle cochée non cliquable ; l'épaisseur 5 mm affiche l'erreur rouge avec les plages ; la ligne « La vérification lit » reprend la ligne de la clause de `compute` (même source, jamais recomposée).

### UI-007 — L'état du calcul et ses refus en rouge
- **Exigence** : le module « État du calcul » est vert (tout est là et calculé), orange (ce qui n'est que dit : une classe écrasée, σ_90,d hors intervalle, une valeur déduite) ou rouge (ce qui arrête : un matériau sans la résistance, une épaisseur hors plages, un bois personnel incomplet, un identifiant inconnu) ; un clic mène au champ. **Plus d'avertissement de stabilité.**
- **Source** : T5, T30, T39, T49, T51
- **Langues** : fr / de / en
- **Critère d'acceptation** : test de fenêtre : le message de T39 pour l'OSB/3 en compression ⊥ (mot pour mot, trois langues) ; aucun message « stabilité » sur DR-01 sans case cochée ; le clic sur un message ouvre le bon accordéon.

### UI-008 — Traction et Compression
- **Exigence** : la Traction est inchangée (N_t,d, la case « à un angle α du fil » (4.2.1.3), le dessin de la barre). La Compression est inchangée sauf l'avertissement de stabilité : les trois cas dessinés (∥ (10), ⊥ (11) (12), à un angle (13)), l'appui dessiné, l et w, les cinq valeurs de f_c,90,d en cartes (une valeur absente grisée), la stabilité en dernier accordéon (REQ-011).
- **Source** : T5, T8, T41, T42
- **Langues** : fr / de / en
- **Critère d'acceptation** : test de fenêtre : les cinq cartes de DR-02 et l'état grisé de la carte « avec grössere Eindrückungen » de D30 ; les taux de ZT-01/02 et DR-01/02 inchangés.

### UI-009 — Flexion : efforts signés et schéma SIA
- **Exigence** : les efforts sur une ligne et signés (N_d traction | compression, M_y,d, M_z,d, la case de l'angle α) ; dans l'accordéon Efforts le **schéma dans le style de la SIA**, noir et blanc, traits fins, lettres en italique : la barre, M_y,d, l'effort normal, le fil hachuré à l'angle α ; la section avec y, z, b, h, M_z,d en double flèche ; la répartition de σ_m,y,d (+ σ_c,d ou σ_t,d) sur la hauteur **avec les valeurs aux deux bords, en nombres**. Le dessin est produit par le domaine (`figure_svg`, un code, aucun mot dans l'impression du rapport) et **lit les contraintes de `compute`** ; il n'en calcule aucune. Le déversement est le dernier accordéon, sur sa figure 11 (REQ-011).
- **Source** : T9, T15, T43, T44, T45
- **Langues** : fr / de / en (les lettres sont des symboles ; aucun mot dans le dessin)
- **Critère d'acceptation** : test sans Qt : les valeurs aux bords du schéma de BI-01 sont celles de `compute` (σ_m,y,d, σ_c,d) ; le dessin ne contient ni couleur ni mot ; test de fenêtre : le schéma suit une saisie de M_y,d.

### UI-010 — Cisaillement en trois figures
- **Exigence** : l'onglet « Cisaillement » montre **trois figures côte à côte, de gauche à droite**, au lieu de `variant_box` : « Effort tranchant » (4.2.5.1), « Cisaillement d'about » (4.2.6) et « Avec contrainte ⊥ au fil » (4.2.7.1) ; la figure choisie change ce qu'on saisit dessous (V_z,d, V_y,d et la moelle ; F_a,d, l_a, w_a ; V_z,d et σ_90,d en compression ⊥ ou en traction ⊥). La figure interactive du volet droit de la troisième est le diagramme de la figure 8 de la norme avec le point de la vérification. La source ne change pas (`variant`, `F`, `l`, `w`, `sigma_90`) ; sous 150 mm de l_a, le cisaillement d'about n'est pas calculable, comme aujourd'hui ; σ_90,d hors de l'intervalle : note orange (REQ-008). Pour un panneau, seules les figures 1 « en plaque ∥ / en voile ∥ » sont offertes : la figure du cisaillement d'about est grisée (REQ-005).
- **Source** : T10, T11, T46, T47, T48, T49, T50, T67
- **Langues** : fr / de / en
- **Critère d'acceptation** : test de fenêtre : SC-01 (76,0 %), SC-02 (138,9 %), SC-03 (20,5 %) donnent leurs taux par la figure correspondante ; la liste déroulante n'existe plus ; le titre de la figure 2 est « Cisaillement d'about / Abscheren / Shear-off »… (mots à fixer en revue) et celui du rapport « Cisaillement ».

### UI-011 — Le module « Résultats »
- **Exigence** : le verdict (vert ou rouge) en tête, puis les lignes **dans l'ordre du calcul**, η en dernier ; la ligne qui gouverne a un cadre pointillé (REQ-014) ; un clic déplie la formule et ses nombres ; la clause à droite ; le taux en pourcent.
- **Source** : T6, T22, T51
- **Langues** : fr / de / en
- **Critère d'acceptation** : test de fenêtre : la dernière ligne de DR-01 est η ; le verdict est vert à 100 %, rouge à 100,1 % ; un clic sur une ligne la déplie.

### UI-012 — La figure interactive et la norme
- **Exigence** : le module « Figure interactive » montre la figure de la SIA 265 de la vérification (diagramme d'interaction, courbe de flambage, figure 8…) avec le point de la vérification ; le module « La norme » donne la clause mot pour mot et son extrait, les extraits épinglés comme pour la neige. Tout extrait est lu de `calc/norms/` et tenu au PDF par un test ; aucun n'est recopié.
- **Source** : T23, T51
- **Langues** : fr / de / en (la norme dans la langue de la fenêtre, l'allemand à défaut)
- **Critère d'acceptation** : test : chaque clause citée par une ligne de `compute` a son extrait ; `tests/test_norm_excerpts.py` passe pour les extraits ajoutés (figure 8 du 4.2.7.1, tableau 19a/19b de SIA 265/1).

### UI-013 — La vue Affichage
- **Exigence** : un bouton **Calcul | Affichage** au-dessus de la fenêtre. Au centre l'**aperçu compilé par Typst** du fichier de la vérification (jamais une esquisse) ; à droite le niveau (0 rien, 1 les verdicts, 2 les contraintes et la relation, 3 chaque formule en nombres), les options (REQ-010), la **commande à copier** `#include domain-file("check", "<id>")` (jamais `#show-check-member`) et le **fichier** `Timber-checks/<Sorte>/<id>.typ` tel que Woodcore l'écrit. Les défauts de rendu du prototype ne sont pas des exigences.
- **Source** : T7, T14, T16, T17, T27, T52, T53, T54
- **Langues** : fr / de / en
- **Critère d'acceptation** : test de fenêtre : la commande copiée est `#include domain-file("check", "BI-04")` ; le niveau 0 ne montre rien, le 3 chaque formule ; changer une option écrit `display` (REQ-010) ; la page est compilée, aucune esquisse.

### UI-014 — Les mots
- **Exigence** : toute chaîne visible nouvelle existe en de, fr et en (`tests/test_i18n.py`), celles qui ne servent plus sont retirées (`mc_shear_variant`, `mc_shear_*` de la liste, les mots de l'avertissement de stabilité, `mc_grade` si la bulle le remplace) ; les mots des onglets sont ceux de `member_check_tab_words.py` ou de leur module, jamais écrits dans un widget.
- **Source** : T63, principe « pas de hardcoding » (CLAUDE.md)
- **Langues** : fr / de / en
- **Critère d'acceptation** : `tests/test_i18n.py` passe ; grep : plus aucune clé morte des mots retirés.

### UI-015 — Les listes déroulantes de η_t, η_w et γ_M
- **Exigence** : une rangée « Facteurs » (sous « Sollicitation », sa place à confirmer à l'approbation) offre, dans des **listes déroulantes** et selon REQ-006 : pour une **barre**, « Classe d'humidité » (1, 2, 3, avec η_w en face : 1,0 / 0,8 / 0,6 — la liste de la bulle d'en-tête, une seule) et « Action » (η_t : « 1,0 · général » ou « 1,4 · chocs, séisme · 2.2.6 », à la place de la case, qui écrit toujours `impact`), γ_M/η_M **montré** (1,7 / 1,5, Tableau 1) mais non choisi : la norme n'en offre qu'une valeur par matériau ; pour un **panneau**, « Classe d'humidité » (celles du produit), « Durée de chargement » (KLED, défaut moyenne, le Tableau 8 au survol) et « Situation » (normale : γ_M du Tableau 6 ; accidentelle : γ_M = 1,0), avec η_mod et γ_M montrés ; ni η_t ni η_w pour un panneau. Les valeurs viennent de `calc/norms/`, les mots (trois langues) du module de l'onglet.
- **Source** : Q-002, T29, T37
- **Langues** : fr / de / en
- **Critère d'acceptation** : test de fenêtre : pour DR-01 les trois valeurs de η_w et les deux de η_t, γ_M/η_M non cliquable ; pour BI-04 les classes 1 et 2 seulement et les cinq KLED ; un choix écrit `moisture_class`, `impact`, `kled`, `accidental` et le taux suit.

## 5. Exigences d'architecture

### ARCH-001 — Le domaine reste hors de Qt, et ne grossit pas `member_check.py`
- **Exigence** : tout ce qui est calcul ou choix — la lecture des résistances d'un matériau (REQ-003, REQ-004), le tableau des grandeurs lues par vérification (REQ-005), les raisons de refus, les messages (REQ-008), les valeurs du schéma de la flexion (UI-009), la liste des matériaux offerts à un onglet avec la ligne de chacun (UI-005) — vit dans `calc/domains/`, sans Qt. `member_check.py` fait déjà 1443 lignes : la lecture du matériau s'écrit dans un module voisin (par ex. `member_check_material.py`, nom à fixer en revue) que `member_check.compute` appelle ; un onglet montre, édite et appelle, il ne recalcule rien.
- **Source** : principes (CLAUDE.md : « Domain logic is independent of the UI »)
- **Critère d'acceptation** : aucun import Qt dans `calc/domains/` (test existant) ; `tests/test_member_check*.py` testent REQ-003 à REQ-008 sans fenêtre.

### ARCH-002 — Une seule lecture des valeurs, la bibliothèque et la norme
- **Exigence** : aucune résistance n'est copiée : une classe livrée se lit de `calc/norms/sia265*.json` (comme aujourd'hui), un panneau de `calc/norms/sia265_1.py` et des fichiers de ses tableaux, un bois personnel de `materials_derive.member_design`. Les facteurs η_mod, γ_M viennent de `sia265_1`. **Toute valeur de norme est lue d'une édition nommée dans `ExternalFiles/000-Normes/` ou de `calc/norms/`, jamais de mémoire** ; une valeur manquante est lue du PDF, transcrite dans le fichier de norme et tenue au PDF par un test, comme #110.
- **Source** : principes 1 et « SIA calculations stay traceable » (CLAUDE.md), T65
- **Critère d'acceptation** : un test garde que `member_check*.py` ne contient aucune table de résistance ; le tableau 19a/19b de l'OSB/3 n'a qu'une copie dans le dépôt.

### ARCH-003 — Le contrat versionné et sa lecture ancienne
- **Exigence** : source 1.3 et export 1.7 (REQ-001, REQ-015), schémas dans `schemas/`, validés avant toute écriture ; lecture des versions antérieures, aucune migration forcée ; `stamp_version` écrit la plus basse version qui porte ce que la source contient ; `docs/domain/member-checks.md` dit les versions.
- **Source** : T56, T57, principe « explicit, versioned data models »
- **Critère d'acceptation** : `tests/test_domain_contracts.py` et `test_member_check.py` : chaque version se lit, l'export des 13 vérifications valide.

### ARCH-004 — Le type « Calcul », sans copier d'onglet
- **Exigence** : les quatre onglets se construisent des services du type (UI-002) ; ce qui sert à un autre onglet — **le menu d'un matériau de la bibliothèque** (aussi la cellule « Matériau » d'une couche de #111), la rangée de bulles de sollicitation, le dessin d'une figure choisie — est un service ou une brique écrite une fois, jamais deux fois (D-19 de #95). `tab_registry.py` reste la seule déclaration des onglets ; `tests/test_tab_services.py` (aucun service n'en importe un autre) passe.
- **Source** : principe « on ne copie plus des onglets » (`docs/ui/building-a-tab.md`)
- **Critère d'acceptation** : les tests de types passent ; aucune classe des quatre onglets ne définit de méthode hors de ses paramètres ; le menu de matériau est dans un module et non dans l'onglet.

### ARCH-005 — Où vivent les options de l'Affichage
- **Exigence** : les options d'Affichage d'une vérification vivent dans sa **source** (`display`, REQ-010) ; le service d'Affichage du type « Calcul » écrit aujourd'hui les siennes dans le **fichier** (`unfold_display.set_display`, tenues par les exports, pour la neige, le poids propre et le vent). La revue (ARCH-RISK-004, ARCH-010) : `display` est la seule mémoire d'une option d'une vérification ; le service d'Affichage l'y écrit pour le genre `check`, le générateur la lit, et le comportement des domaines de charges ne change pas.
- **Source** : T13, T54, T56 ; principe « one source of truth »
- **Critère d'acceptation** : une option se change à un seul endroit ; un test montre le même résultat après un enregistrement, un export et un « Régénérer ».

### ARCH-006 — La décision Q-010 est remplacée et reportée
- **Exigence** : `docs/decisions.md` §13 reçoit à la fin : la fin de Q-010 (« le user choisit dans un menu déroulant » est remplacé par les trois figures ; `SHEAR_VARIANTS` ne cite plus Q-010), le matériau de la bibliothèque (variante A, rangée de sollicitation, épaisseur, facteurs d'un panneau selon Q-002), la stabilité en accordéon (Q-001), les options d'Affichage dans la source.
- **Source** : T55, T63 ; CLAUDE.md « Preserve the architecture… docs/decisions.md says why and what it costs »
- **Critère d'acceptation** : les entrées de §13 et de `docs/decisions-index.md` existent ; `tests/test_docs_coherence.py` passe.

### ARCH-007 — Dépendances sur #110 et #111
- **Exigence** : la spécification lit `materials_*` tel que **commité** (`a9cae26`) : `materials_search.search`, `materials_derive`, `materials_catalogue`, `materials_project`. La session de #111 modifie en ce moment, sans commit, `materials.py`, `materials_catalogue.py` (champ `includes_battens`), `materials_search.py` (`ranked`), `materials_migrate.py`, `usersettings.py` et `calc/libraries/materials-*.json` : l'implémentation de #112 ne dépend d'aucune de ces modifications, et **les identifiants livrés (`sia265:*`, `sia265-1:*`) ne doivent pas changer** (REQ-002) ; elle se rebase sur l'état commité de #111 avant de toucher `materials_project.used_ids` et `materials_derive.available_in`.
- **Source** : consigne de la session ; T72 (#110, #111)
- **Critère d'acceptation** : `tests/test_materials_catalogue.py` (les identifiants livrés écrits) passe après le travail de #111 et de #112 ; aucun fichier de #111 n'est édité par #112 hors `materials_project.used_ids` et `materials_derive.available_in`.

### ARCH-008 — Le matériau est figé dans l'enregistrement (revue)
- **Exigence** : `resolve` lit la bibliothèque et la copie du projet **une fois** et pose dans l'enregistrement de `checks.json` ce que `compute` lit (`resistance` : les valeurs du genre et de la sollicitation, leur provenance, la plage, les facteurs) ; `compute` reste une fonction de l'enregistrement et des normes, sans lire la bibliothèque (palette, `utilisations`, tests). Une classe de SIA 265 produit les mêmes nombres qu'aujourd'hui.
- **Source** : revue (ARCH-RISK-007)
- **Critère d'acceptation** : `compute` ne s'appelle sur aucun fichier de la bibliothèque (test) ; le même enregistrement donne le même taux sur un autre poste.

### ARCH-009 — Le genre change, le fichier suit (revue)
- **Exigence** : `unfold.move_domain(here, rid, old_kind, new_kind)` déplace le fichier et son entrée de la base ; appelé par l'enregistrement avant l'export (REQ-011).
- **Source** : revue (ARCH-RISK-003)
- **Critère d'acceptation** : voir REQ-011.

### ARCH-010 — Un seul magasin des options d'Affichage pour une vérification (revue)
- **Exigence** : voir ARCH-005 ; `unfold_display` reçoit un magasin par genre de domaine (le fichier pour les charges, la source pour `check`) et la règle de priorité de `_with_display` (D-17) ne reporte pas les arguments du fichier sur une vérification.
- **Source** : revue (ARCH-RISK-004)
- **Critère d'acceptation** : voir ARCH-005 ; `tests/test_domain_file_display.py` et `test_unfold.py` inchangés pour la neige, le poids propre et le vent.

## 6. Contraintes

- **CON-001** — **Les valeurs de norme viennent de `calc/norms/` ou des PDF de `ExternalFiles/000-Normes/` (`norm-library/`), d'une édition nommée, jamais de mémoire** : SIA 265:2021 tableaux 8 et 9, SIA 265/1:2018 tableaux 6, 9 et les tableaux a/b de chaque produit, 6.1.2.1, 6.2.1.4. Source : T65, CLAUDE.md. (Les passages de SIA 265/1 lus pour cette spécification : 6.1.2.1, 6.2.1.2 à 6.2.1.4, tableau 9, note 1 des tableaux b ; ils sont cités en REQ-006.)
- **CON-002** — Les **13 vérifications du projet d'exemple** (`tests/projet-exemple/`) gardent leurs taux et leurs fichiers (hors le nom du matériau ajouté à la ligne de l'élément, REQ-009, s'il change leur texte : à constater, pas à supposer). Source : T61.
- **CON-003** — La source est compatible vers l'avant : 1.0, 1.1, 1.2 se lisent ; `grade` reste lu (T56). La source du cisaillement ne change pas : `variant`, `F`, `l`, `w`, `sigma_90` (T50).
- **CON-004** — Le vert/rouge du taux est celui de la décision antérieure : vert à 100 % ou moins, rouge au-delà, pas d'orange pour le taux ; le taux en pourcent (T22).
- **CON-005** — **Les bulles d'un panneau « ne changent pas »** : les textes de T35 pour l'OSB/3 sont la référence (T2, T19, T35).
- **CON-006** — Aucune valeur n'est copiée à la main (principe 1) : le prototype contient des copies (tableau `GRADES`, tables de l'OSB/3) ; elles ne sont **pas** reprises (T3).
- **CON-007** — Le rapport imprime les mots du titre de la norme (« Cisaillement » pour le 4.2.6) ; la fenêtre dit « Cisaillement d'about » (T11). Les trois langues partout.
- **CON-008** — Édition du prototype : celle de l'artefact « troisième version » ; les versions 1 et 2 à la même adresse gardent les variantes B et C, écartées (T40). Les modules et les briques valent pour la **vue Calcul** ; la vue Affichage est le rendu Typst réel, pas l'esquisse du prototype (T14, T17).
- **CON-009** — Plusieurs sessions Claude éditent le dépôt : aucune opération destructive de git, des modifications ciblées (CLAUDE.md).

## 7. Décisions prises

Toutes sont de l'ingénieur (issue #112, 23–24.10.2026) ; aucune n'est reposée. Celles qui sont déduites de l'issue sans l'avoir été explicitement sont marquées « proposée » et se confirment à l'approbation.

- **D-1** — **Quatre onglets séparés**, la barre ne nomme que l'onglet ; la Synthèse est un onglet à part (T4, T26).
- **D-2** — **Pas d'avertissement de stabilité** : la case de l'accordéon suffit (T5).
- **D-3** — **Résultats dans l'ordre du calcul**, η en dernier, verdict en tête, cadre pointillé de la ligne qui gouverne (T6).
- **D-4** — **Calcul | Affichage** au-dessus de la fenêtre (T7).
- **D-5** — **Traction inchangée** (T8).
- **D-6** — **Schéma SIA de la flexion**, dans l'accordéon Efforts, avec les contraintes aux bords en nombres (T9, T15). Prix : un dessin de plus à tenir d'accord avec `compute`.
- **D-7** — **« Cisaillement »** : trois figures au lieu de la liste déroulante ; **remplace Q-010** (T10, T55). Prix : la décision de la spec de refonte des commandes Typst est renversée.
- **D-8** — **« Cisaillement d'about »** dans la fenêtre, « Cisaillement » dans le rapport (T11).
- **D-9** — **σ_90,d hors de l'intervalle : un avertissement orange**, calcul fait (T12).
- **D-10** — **Les options de l'Affichage dans la source**, le fichier réécrit tant qu'il n'est pas modifié (T13).
- **D-11** — **L'Affichage est toujours le rendu Typst réel** ; la question ne se repose plus (T14). La commande est `#include domain-file("check", "<id>")` (T16).
- **D-12** — **Les défauts de rendu du prototype ne sont pas à reproduire** (T17).
- **D-13** — **Matériau : variante A, un menu puis la sollicitation**, tout le bois de la bibliothèque, panneaux compris ; les variantes B et C écartées (T18, T19, T40). Prix : un menu et une rangée de plus dans l'en-tête, un contrat de source qui change.
- **D-14** — **Les bulles de sollicitation d'un panneau restent telles que validées pour l'OSB/3** ; un bois en barre : une bulle cochée non cliquable (T2, T35, T36).
- **D-15** — **L'épaisseur d'un panneau est le plus petit côté de la section** (T38) ; une note orange si ce n'est pas le côté que la sollicitation suppose, rien de refusé (Q-003 A, 24.10.2026).
- **D-16** — **Un matériau sans la résistance nécessaire : non calculable, avec la raison** ; hors des plages de l'épaisseur : idem (T39, T59).
- **D-17** — **Décisions antérieures conservées** : valeurs liées à une variable (bouton à droite), accordéons, stabilité en dernier accordéon à option et désactivée, vert/rouge à 100 %, taux en pourcent, en-tête compact, liste qui dit l'état, état du calcul et norme au survol, pas de jauge ni de section à l'échelle ni de chaîne résistance/contrainte, β saisissable avec appuis glissants et fixes (T20 à T24).
- **D-18** — **Flambage et déversement sont l'accordéon « Stabilité » de la Compression et de la Flexion** (T21, T42, T45, T55) ; **le genre reste** : la case le change à l'enregistrement, les onglets listent les deux genres (Q-001 A, 24.10.2026). Prix : un fichier change de dossier quand on coche la case (ARCH-009).
- **D-19** — *(proposée)* Les panneaux, dans ce premier lot (T67) : flexion en plaque et en voile, traction et compression ∥ et ⊥ dans le plan, cisaillement en plaque et en voile ; **ni compression ⊥ au fil (angle > 0), ni stabilité, ni cisaillement d'about**. L'angle α n'existe pas pour un panneau : la direction `par`/`perp` du tableau le remplace.
- **D-20** — *(proposée)* La position garde une classe de résistance texte (`strength_class`/`material` du classeur) ; « suit la position » résout cette classe en matériau livré `sia265:<classe>`. La position ne nomme ni panneau ni bois personnel dans ce lot (T70 ; §9).
- **D-21** — *(proposée)* Un matériau personnel d'une vérification est copié dans le projet comme celui d'une couche (REQ-002, D-11 de #110).

- **D-22** — **η_t, η_w, γ_M sont des options de chaque vérification, dans des listes déroulantes ; leurs valeurs et leur règle sont celles de la norme lue** (Q-002, 24.10.2026) : barre, η_w du Tableau 4 et η_t de 2.2.6 sur les valeurs des Tableaux 8 et 9, γ_M/η_M du Tableau 1 montré et non choisi ; panneau, η_mod du Tableau 9 (classe d'humidité × KLED) et γ_M du Tableau 6 (normal ou accidentel, note 1), ni η_t ni η_w. Écarts avec la demande : voir Q-002, « à confirmer à l'approbation ». Prix : deux champs de plus pour un panneau (`kled`, `accidental`), un taux de panneau différent de celui du prototype hors classe 1 / KLED moyenne.
- **D-23** — *(proposée)* La valeur de calcul d'un panneau à la classe 1, KLED moyenne, situation normale est celle du tableau b (imprimée, arrondie au dixième) ; dans tout autre cas η_mod · f_k / γ_M **non arrondi**, f_k du tableau a (un panneau personnel sans f_k : sa valeur de calcul saisie mise à l'échelle du rapport des η_mod / γ_M, la ligne le disant).
- **D-24** — *(proposée)* `impact` (η_t) reste le champ de la barre, affiché en liste ; un panneau range les chocs dans la KLED « très courte » (SIA 265/1 Tableau 8) et refuse `impact`.

À reporter dans `docs/decisions.md` §13 à la fin : D-7 (fin de Q-010), D-10, D-13/D-14/D-15, D-18, D-22 et D-23 (Q-002).

## 8. Hors périmètre

- L'onglet **Synthèse** (artefact « Synthèse du projet ») : seule la donnée qu'il lira est exigée (REQ-015).
- Les vérifications **Torsion, Déformations, Vibrations** (restent « à venir »), la **vérification au feu** (`tab_mc_fire`, issue #46) hors de la règle de REQ-016, les **vérifications de l'acier** (`steel_tab`).
- Les **autres onglets** : Matériaux (#110, hors `available_in`), Poids propre (#111), Commandes (#115), Variables (#114), Domaines (#113), le type Éditeur/Données (#105, #106).
- Le **module de glissement et les modules E et G des classes d'humidité 2 et 3** (SIA 265/1 6.2.1.2, E et G × 0,9 / 0,75) : utiles à la stabilité et aux déformations d'un panneau, qui ne sont pas dans ce lot.
- La compression **⊥ au fil** d'un panneau, la **stabilité** d'un panneau, le **cisaillement d'about** d'un panneau (D-19).
- Le moteur JavaScript du prototype : il n'est pas repris (T3).
- Un changement de la **sémantique des commandes Typst** (`#verify`, `#include domain-file`) ou de `lib/calc-engine-core.typ`.
- La **copie du prototype** dans `docs/requirements/prototypes/2026-10-24-verifications-elements/` (T64) est une tâche de documentation de l'implémentation (§11), pas une exigence du produit.

## 9. Idées non retenues comme exigences

- **La position qui nomme un matériau de la bibliothèque** (et une sollicitation) : « Dit-elle demain… ? » (T70) est une question posée à l'étude, pas une demande ; elle touche `Positionen.xlsx`, l'onglet Positions et les connecteurs, et sort de cette issue. D-20 la laisse à une issue à part.
- **Une épaisseur de panneau saisie à part** (T66, seconde branche) : écartée par D-15 si Q-003 est tranchée comme recommandé.
- **Le menu de matériaux partagé avec la cellule « Matériau » du poids propre (#111)** : la brique est exigée écrite une fois (ARCH-004) ; son adoption par #111 est l'affaire de cette session.
- **L'en-tête de la bulle de valeurs et la brique de bulle de #115** : réutilisation possible, non exigée.
- **Un bois personnel dont E_0,05 se déduit de E_0,mean** : #110 dit qu'un module n'est jamais déduit ; la stabilité d'un bois personnel reste donc refusée tant que la bibliothèque ne porte pas E_0,05.

## 10. Questions

### Q-001 — Flambage et déversement dans la source : le genre change-t-il, ou un objet s'ajoute-t-il ?
- **Options** : A — le genre reste, la case le change à l'enregistrement ; B — un objet `stability` ; C — garder les onglets Flambage et Déversement.
- **Réponse** : A — le genre reste ; la case de la stabilité coche/décoche le genre à l'enregistrement ; les onglets listent les deux genres (ingénieur, 24.10.2026). → D-18, REQ-011.

### Q-002 — Quels facteurs pour la valeur de dimensionnement (humidité, durée, résistance) ?
- **Contexte** : le prototype applique η_w · η_t de la barre aux valeurs de l'OSB/3 ; SIA 265/1:2018 prescrit autre chose.
- **Réponse** (ingénieur, 24.10.2026, hors des options A/B/C proposées) : « pour toutes les vérifications, il y a le eta_t, eta_w et gamma_m qui influencent la résistance. Ces valeurs doivent multiplier les résistances lors de la vérification. Ces résistances peuvent être différentes pour un panneau ou une barre si je me rappelle bien de la norme. Ce sont des options à choisir en drop down list lors de la vérification. » → REQ-006, UI-015, D-22.
- **Ce que la norme dit (lue dans SIA265-2021-DE.pdf et SIA265-1-2018-FR.pdf)** :

| | Barre (SIA 265:2021) | Panneau (SIA 265/1:2018) |
|---|---|---|
| f_d | η_M·η_t·η_w/γ_M · f_k (2.2.2, éq. 3, p. 19) ; Tableaux 8 et 9 = valeurs « pour η_w = 1,0 et η_t = 1,0 » | η_mod · f_k / γ_M, η_mod = η_M·η_t·η_w (6.1.2.1, éq. 5, p. 25) |
| η_t | 1,0 ; 1,4 pour des chocs (2.2.6, p. 19) | n'existe pas séparément : dans η_mod ; chocs et séisme = KLED très courte (Tableau 8, p. 27) |
| η_w | Tableau 4 (3.2.1.3) : 1,0 / 0,8 / 0,6 (classes 1 à 3) | n'existe pas séparément : dans η_mod, par classe d'humidité (Tableau 9, p. 28) |
| γ_M | rapport γ_M/η_M du Tableau 1 (2.2.5) : 1,7 / 1,5, déjà dans les tableaux 8 et 9 | Tableau 6 (p. 26) par produit (OSB 1,2) ; 1,0 en situation accidentelle sauf séisme (note 1) |
| durée | dans η_M (« Einwirkungsdauer », 2.2.4) | KLED à choisir (Tableau 9 : 5 colonnes) |

- **Écarts avec la demande — à confirmer à l'approbation** : (1) **γ_M n'est pas un choix pour une barre** : un rapport par matériau, déjà dans les tableaux (Tableau 1) ; il est montré, non proposé en liste ; pour un panneau l'unique alternative de la norme est γ_M = 1,0 en situation accidentelle (liste « Situation »). (2) **η_t et η_w ne s'appliquent pas à un panneau** : η_mod (humidité × durée) les remplace ; les listes d'un panneau sont la classe d'humidité, la KLED et la situation, non « η_t / η_w / γ_M ». (3) **η_t est une liste de deux valeurs (1,0 | 1,4)**, la classe d'humidité une liste de trois qui fixe η_w : η_w ne se choisit pas indépendamment de la classe (Tableau 4). (4) le **taux d'un panneau hors classe 1, KLED moyenne** diffère du prototype, qui lui appliquait η_w · η_t de la barre.

### Q-003 — L'épaisseur d'un panneau : toujours le plus petit côté, ou selon la sollicitation ?
- **Options** : A — toujours le plus petit côté, une note orange si ce n'est pas le côté supposé ; B — b en voile et h en plaque, refus rouge ; C — une épaisseur saisie à part.
- **Réponse** : A — toujours le plus petit côté, une note orange si ce n'est pas le côté attendu (ingénieur, 24.10.2026). → D-15, REQ-007.

## 11. Critères d'acceptation

- [x] REQ-001 — la source 1.3 (`material`, `loading`, `display`) s'écrit et se relit ; 1.0 à 1.2 se lisent ; les 13 sources du projet d'exemple ne changent pas
- [x] REQ-002 — un bois personnel nommé est copié dans le projet et la vérification se calcule sans la bibliothèque ; un identifiant inconnu donne sa raison
- [x] REQ-003 — C24/GL24h par `material` = par `grade` ; un bois personnel complet se calcule ; les 13 taux sont inchangés
- [x] REQ-004 — l'OSB/3 en chaque sollicitation et chaque plage, dont 6, 10, 18, 25 mm
- [x] REQ-005 — le tableau des grandeurs lues par vérification ; compression ⊥ au fil, stabilité, cisaillement d'about d'un panneau non calculables avec leur raison ; bois personnel incomplet idem
- [x] REQ-006 — η_t, η_w, γ_M selon la norme lue : barre = tableau × η_w × η_t ; panneau = tableau b (classe 1, KLED moyenne, normale) ou η_mod · f_k / γ_M ; aucun k_h
- [x] REQ-007 — épaisseur hors plages : non calculable avec les plages
- [x] REQ-008 — σ_90,d hors de −f_c,90,d … f_t,90,d : note orange, taux calculé
- [x] REQ-009 — le fichier cite la norme et le nom du matériau ; « Cisaillement » imprimé
- [x] REQ-010 — `display` dans la source ; le fichier non modifié est réécrit, le fichier modifié est gardé
- [x] REQ-011 — la stabilité est un accordéon à option, désactivé par défaut ; le genre change à l'enregistrement, le fichier est déplacé ; KN-01, KI-01/02 inchangés
- [x] REQ-012 — `available_in` donne `tab_mc` « oui » à un panneau et à un bois personnel complet
- [x] REQ-013 — suivre la position, écraser en orange, « Reprendre »
- [x] REQ-014 — lignes dans l'ordre du calcul, η en dernier, ligne qui gouverne marquée
- [x] REQ-015 — l'export porte le matériau et sa sollicitation ; `checks.schema.json` 1.7 ; 1.0 à 1.6 lus
- [x] REQ-016 — le feu refuse un matériau hors des classes de SIA 265 ; FE-01/02 inchangées
- [x] UI-001 — quatre onglets, barre « Sécurité structurale › Cisaillement », `tab_mc_shear` renommé en trois langues
- [x] UI-002 — chaque onglet est une classe de paramètres sur le type « Calcul »
- [x] UI-003 — liste groupée par position, taux vert/rouge, tri par position ou taux, archives, Nouveau, Dupliquer
- [x] UI-004 — en-tête et bulles qui suivent (grises) ou écrasent (orange, « Reprendre »), résumé fermé
- [x] UI-005 — la bulle et le menu de la bibliothèque, recherche fr/de/en, groupes, résistance lue, source
- [x] UI-006 — la rangée « Sollicitation » toujours là, textes de l'OSB/3 inchangés, la ligne « La vérification lit… »
- [x] UI-007 — l'état du calcul vert/orange/rouge, les refus en rouge, plus d'avertissement de stabilité
- [x] UI-008 — Traction inchangée ; Compression inchangée sauf l'avertissement ; les cinq cartes de f_c,90,d, chacune sa valeur du tableau 8 ou 9, la carte sans valeur de D30 grisée avec sa raison (lot 3)
- [x] UI-009 — flexion signée et schéma SIA aux valeurs des contraintes de `compute`
- [x] UI-010 — Cisaillement en trois figures, SC-01 76,0 %, SC-02 138,9 %, SC-03 20,5 %
- [x] UI-011 — Résultats : verdict, ordre du calcul, cadre pointillé, taux en pourcent
- [x] UI-012 — figure interactive et extraits de la norme lus de `calc/norms/` : les clauses et figures de la SIA 265 (dont la figure 8) sous chaque ⓘ, le tableau du matériau (tableaux 19a et 19b de l'OSB/3) dans la rangée « Sollicitation », épinglables (lot 3)
- [x] UI-013 — Affichage : aperçu Typst, niveau, options, `#include domain-file("check", id)`, fichier
- [x] UI-014 — mots en de, fr, en ; mots retirés supprimés
- [x] UI-015 — listes déroulantes de la classe d'humidité (η_w), de η_t, de la KLED et de la situation ; γ_M/η_M montré
- [x] ARCH-001 à ARCH-010 — domaine sans Qt, module de lecture du matériau, une seule lecture des valeurs, contrats versionnés, type « Calcul », options d'Affichage à une seule source, décisions de §13, dépendances de #110/#111, matériau figé dans l'enregistrement, déplacement du fichier au changement de genre
- [x] Documentation : `docs/domain/member-checks.md`, `docs/domain/materials.md` (`available_in`, copie du projet), `docs/ui/tab-member-checks.md`, `docs/ui/window.md`, `docs/ui/building-a-tab.md` / `calc-tab.md` (l'état des onglets), `docs/decisions.md` §13 et `docs/decisions-index.md`, entrée `CHANGELOG.md`, page « Nouveautés » fr/de/en ; la copie du prototype dans `docs/requirements/prototypes/2026-10-24-verifications-elements/` (T64) ; pas de commande Typst nouvelle (donc ni `///` ni `commands.json`).
- [x] Tests : `tests/test_member_check.py`, `test_member_check_tab.py` (ou leurs successeurs), `test_materials_domain.py`, `test_tab_registry.py`, `test_i18n.py`, `test_norm_excerpts.py` étendus ou ajoutés ; une ligne au catalogue des tests pour tout fichier nouveau ; les 13 vérifications du projet d'exemple inchangées ; suite complète à la fin.

## 12. Traçabilité

| Source | Élément | Statut |
|---|---|---|
| T1 | D-13, §1 | capturé |
| T2 | D-14, CON-005, UI-006 | capturé |
| T3 | CON-006, §8 | capturé |
| T4 | D-1, UI-001 | capturé |
| T5 | D-2, UI-007, UI-008 | capturé |
| T6 | D-3, REQ-014, UI-011 | capturé |
| T7 | D-4, UI-013 | capturé |
| T8 | D-5, UI-008 | capturé |
| T9 | D-6, UI-009 | capturé |
| T10 | D-7, UI-010, UI-001 | capturé |
| T11 | D-8, REQ-009, UI-010, CON-007 | capturé |
| T12 | D-9, REQ-008 | capturé |
| T13 | D-10, REQ-010, ARCH-005 | capturé |
| T14 | D-11, UI-013, CON-008 | capturé |
| T15 | D-6, UI-009 | capturé |
| T16 | D-11, UI-013 | capturé |
| T17 | D-12, CON-008 | capturé |
| T18 | D-13, REQ-003, REQ-004, REQ-012 | capturé |
| T19 | D-13, D-14, UI-006 | capturé |
| T20 | D-17, UI-002 | capturé |
| T21 | D-17, D-18, REQ-011 | capturé (Q-001 A) |
| T22 | D-17, CON-004, UI-003, UI-011 | capturé |
| T23 | D-17, UI-002, UI-012 | capturé |
| T24 | D-17, REQ-011 | capturé |
| T25 | UI-001, UI-002 | capturé |
| T26 | D-1, UI-001 | capturé |
| T27 | D-4, UI-002, UI-013 | capturé |
| T28 | UI-003 | capturé |
| T29 | UI-004, REQ-013 | capturé |
| T30 | UI-004, UI-007, REQ-013 | capturé |
| T31 | UI-004 | capturé |
| T32 | UI-005 | capturé |
| T33 | UI-005 | capturé |
| T34 | UI-005, REQ-005 | capturé |
| T35 | D-14, UI-006, REQ-005, CON-005 | capturé |
| T36 | D-14, UI-006 | capturé |
| T37 | UI-006, REQ-004, REQ-006 | capturé ; la fin de la ligne selon REQ-006 (Q-002) |
| T38 | D-15, REQ-007, UI-006 | capturé (Q-003 A) |
| T39 | D-16, REQ-005, UI-007 | capturé |
| T40 | D-13, CON-008 | capturé (variantes écartées) |
| T41 | UI-008 | capturé |
| T42 | UI-008, REQ-011 | capturé |
| T43 | UI-009 | capturé |
| T44 | UI-009 | capturé |
| T45 | D-18, UI-009, REQ-011 | capturé |
| T46 | D-7, UI-010 | capturé |
| T47 | UI-010 | capturé |
| T48 | D-8, UI-010 | capturé |
| T49 | D-9, REQ-008, UI-007 | capturé |
| T50 | CON-003, UI-010 | capturé |
| T51 | UI-007, UI-011, UI-012 | capturé |
| T52 | D-11, UI-013 | capturé |
| T53 | UI-013, REQ-010 | capturé |
| T54 | D-10, REQ-010, ARCH-005 | capturé |
| T55 | D-7, D-18, ARCH-006, UI-001, REQ-014 | capturé |
| T56 | REQ-001, REQ-015, ARCH-003 | capturé |
| T57 | REQ-001 | capturé |
| T58 | REQ-003, REQ-004 | capturé |
| T59 | REQ-005, REQ-007 | capturé |
| T60 | REQ-008, REQ-009 | capturé |
| T61 | REQ-003, REQ-004, CON-002 | capturé |
| T62 | UI-004, UI-005, UI-006 | capturé |
| T63 | UI-014, §11 | capturé |
| T64 | §8, §11 | capturé (tâche de documentation) |
| T65 | REQ-006, UI-015, CON-001, Q-002 | capturé ; lu dans la norme, écarts → Q-002 |
| T66 | D-15, REQ-007, Q-003 | résolu (Q-003 A) |
| T67 | D-19, REQ-005, UI-010 | capturé (proposé) |
| T68 | REQ-006 | capturé |
| T69 | REQ-001, REQ-002 | capturé |
| T70 | D-20, §9 | capturé (proposé) ; extension → idée |
| T71 | REQ-015, §8 | capturé |
| T72 | REQ-012, REQ-016, ARCH-007 | capturé |

### Points de la source non résolus

Aucun : Q-001 (A), Q-002 (règle de la norme, quatre écarts à confirmer à l'approbation), Q-003 (A) sont répondues ; T70 (la position qui nomme un matériau) est laissée à une autre issue (D-20, §9).

## 13. Revue d'architecture

*Faite le 24.10.2026 par la session de spécification, sur le code (arbre de travail, master `be5b85f`) ; les numéros de ligne sont ceux d'aujourd'hui.* **Verdict : APPROUVER AVEC RÉSERVES** — rien ne bloque ; les réserves importantes sont devenues des exigences (ARCH-008 à 010, REQ-011) ou des étapes (§14).

**Modules concernés.** `calc/domains/member_check.py` (1443 l.) : `KINDS` 70, `check_source` 127, `stamp_version` 303, `resolve` 489, `compute` 684, `_compute_section` 800 (η_w, η_t 806-807 ; `design` 818 multiplie `k_fi·η_w·η_t`), `_compute_bending` 935 (reçoit `factor`), `published_vars` 1379. `calc/norms/sia265.py` (`eta_w` 892, `eta_t` 921, `gamma_m` 954) et `sia265_1.py` (`gamma_m` 72, `eta_mod` 95 : classe 1, KLED moyenne par défaut). `materials_derive.py` : `panel_factors` 81, `panel_design` 89, `available_in` 198 ; `materials_project.used_ids` 57 (ne lit que le poids propre) ; `tools/layer_table.py:35` `MaterialCombo` (#111). `unfold.py` : `member_line` 198, `_generate_member` 224, `domain_path` 619, `_with_display` 723, `AUTO_REGENERATE` 762 ; `unfold_display.py` `set_display` 106 ; `calc_display.py` (4 `WRITERS`). Fenêtre : `tab_registry.py:87-93`, `member_check_tab.py` (853 l., `MemberCheckTab` 89 sur `SourceEditorTab`, `ShearTab` 761 et son Q-010), `member_check_tab_form.py:112` (`grade_box`), `:130` (`impact_box`), `chrome.py:56`, `tests/test_views.py`.

**À réutiliser.** `sia265.eta_w/eta_t/gamma_m`, `sia265_1.eta_mod`, `materials_derive.member_design`, `materials_search.search`, `materials_project.sync`, `contracts.CalcTabDomain` et `wind_view.py` (modèle d'un domaine Qt-free qui déclare formulaire, messages, résultats, dessin), le champ `tiles` de `calc_form`, `DomainDisplay`, `unfold.refresh/regenerate/status`, `line_display.display_args`.

**Risques.**
- **ARCH-RISK-001 — important — trop gros pour un seul lot.** Le contrat, la bibliothèque, les panneaux, les facteurs, le déplacement de fichier, l'Affichage, le schéma SIA, les trois figures et la migration des quatre onglets sur `CalcTab` (docs/ui/calc-tab.md, D-05 de #95 ; aujourd'hui trois onglets seulement y sont). Correctif : deux lots dans une approbation — **lot 1, le domaine** (étapes 1 à 6, testable sans fenêtre, les anciens onglets lisent encore `grade`), **lot 2, les onglets** (7 à 11) ; une suite complète à la fin de chacun.
- **ARCH-RISK-002 — important — Python seul calcule un panneau.** `lib/timber.typ` ne connaît que les classes de SIA 265 ; mais tout genre est imprimé déplié (`UNFOLDED_KINDS`, unfold.py:27), le fichier est fait des lignes de `compute` : aucune commande Typst ne change. Correctif : un test compile le fichier d'une vérification de panneau (`unfold.query_state`) et compare η de Typst à celui de `compute`.
- **ARCH-RISK-003 — important — le changement de genre laisse deux fichiers.** `domain_path` (619) donne le dossier du genre de l'enregistrement ; le fichier de l'ancien genre reste, l'id est dans deux dossiers (#114 : « aucun identifiant n'est dans deux sortes »). Le « mécanisme de déplacement » de Q-001 n'existe pas. Correctif : ARCH-009, `unfold.move_domain`, appelé à l'enregistrement avant l'export.
- **ARCH-RISK-004 — important — deux mémoires pour une option d'Affichage.** `set_display` écrit dans le **fichier** (D-17) et `_with_display` reporte les arguments du fichier sur une nouvelle écriture ; `comparable_text` ignore ces arguments, donc l'ingénieur ne « modifie » jamais le fichier par l'Affichage. Mettre `display` dans la source sans règle ferait deux vérités. Correctif : ARCH-010 — pour le genre `check`, le service écrit dans la source, le générateur écrit les arguments depuis l'enregistrement, `_with_display` ne reporte rien ; `display` voyage dans l'export (`checks` 1.7). Les charges ne changent pas.
- **ARCH-RISK-005 — important — `factor = η_w·η_t` passé partout.** `_compute_bending` et `_compute_lateral` reçoivent un produit (831, 837) : un panneau (η_mod, γ_M, pas de k_h) n'y entre pas. Correctif : un objet `Factors` du module de lecture du matériau, qui dit ses lignes (`eta_w`, `eta_t` ou `eta_mod`, `gamma_M`), remplace `factor` ; la barre garde ses clés et ses formules (13 fichiers inchangés).
- **ARCH-RISK-006 — important — contrat.** `stamp_version` (303) doit écrire 1.3 seulement si `material`, `loading`, `kled`, `accidental` ou `display` est présent, et `checks` 1.7 seulement pour un enregistrement qui porte ces champs ; un champ vide est absent (REQ-001), sinon « Reprendre » laisserait un 1.3 sans raison. Les schémas, `docs/architecture/data-contracts.md` et `test_domain_contracts.py` suivent.
- **ARCH-RISK-007 — important — `compute` lirait la bibliothèque.** `compute` est pur (palette, `utilisations` 1405, tests) ; lire la bibliothèque ou la copie du projet à ce moment le rendrait dépendant du poste. Correctif : ARCH-008, `resolve` fige `resistance` dans l'enregistrement ; une classe de SIA 265 y passe par le même chemin (`sia265:<classe>`), donc les mêmes nombres (test des 13 : instantané pris avant l'étape 2).
- **ARCH-RISK-008 — important — coordination #114, #113.** #114 : `buckling` et `lateral-torsional` pointent sur `tab_mc_buckling` / `tab_mc_ltb` (variable_calc, ARCH-RISK-012 de #114) ; l'étape 9 les change en `tab_mc_compression` / `tab_mc_bending` (le test « chaque clé est une `TabSpec` » le voit) et lit `member_check.RESULT_KEY` (`"eta"`) au lieu de `row["key"] == "eta"` (unfold.py:252, 279). #113 : les lignes ajoutées (η_mod, γ_M, tableau a) sont des `#var`/`#eq` ordinaires, les états « modifiée hors de Woodcore » s'appliquent sans changement ; la ligne de l'élément ne change pas pour une classe de SIA 265 (CON-002).
- **ARCH-RISK-009 — important — le menu de matériau est écrit une fois.** `layer_table.MaterialCombo` est privé au service de #111 ; le menu de #112 (recherche, groupes, résistance lue, source) est un autre contrôle : un module `tools/material_menu.py` que #111 pourra adopter, aucune copie dans `member_check_tab*`. Les listes (groupes, résistance lue par onglet, grisé) viennent du domaine (`member_check_material.offered`).
- **ARCH-RISK-010 — mineur — mots et clés mortes.** `mc_grade`, `mc_impact`, `mc_shear_variant`, les clés des onglets repliés et l'avertissement de stabilité sortent (UI-014, `test_i18n.py`, grep).
- **ARCH-RISK-011 — mineur — arrondi.** `materials_derive.panel_design` arrondit au dixième ; une vérification hors classe 1 / KLED moyenne ne doit pas arrondir (D-23) : la lecture du matériau part du tableau a et des facteurs.

**Approche.** Un module Qt-free `member_check_material.py` : `offered(kind)` (REQ-005), `read(...)` → `Resistance` et `Factors` ; `resolve` l'appelle et fige le résultat ; `compute` ne change que par `design` et `factor`. Un `member_check_view.py` (modèle `wind_view.py`) déclare le reste. Norme : Tableaux 7 et 8 de SIA 265/1 et γ_M accidentel (Tableau 6, note 1) à transcrire en JSON, tenus au PDF.

**Tests.** Ceux de chaque étape du §14 ; le catalogue reçoit une ligne par fichier nouveau.

## 14. Plan d'implémentation

Deux lots, chacun clos par la suite complète (en arrière-plan) et un commit par le skill `finish` ; rien ne se publie sans le mot de l'ingénieur. Avant tout : un instantané des 13 vérifications (lignes, η, fichiers) comme garde « inchangé » (CON-002).

**Lot 1 — le domaine, sans fenêtre**

| # | Étape | Fichiers | Exigences | Test qui la prouve |
|---|---|---|---|---|
| 1 | Normes : Tableaux 7 et 8 de SIA 265/1 (JSON, p. 27), γ_M accidentel (Tableau 6, note 1), `sia265_1.kled_ids/admitted_classes/gamma_m(accidental)` | `calc/norms/sia265-1-2018-tab07-08-kled.json`, `-tab06-gamma-m.json`, `sia265_1.py` | REQ-006, ARCH-002 | `test_sia265_1.py`, `test_norm_excerpts.py` (tenus au PDF) |
| 2 | Contrat : source 1.3, export 1.7, `stamp_version`, champs vides absents, refus (`grade`+`material`, `loading` sur barre, `impact` sur panneau) | `schemas/member-check-source.schema.json`, `checks.schema.json`, `member_check.py` | REQ-001, ARCH-003, RISK-006 | `test_member_check.py`, `test_domain_contracts.py`, `test_schema_consumers.py` ; 13 sources relues sans changement |
| 3 | Lecture du matériau : `offered`, `read`, `Resistance`, `Factors`, plages, raisons de refus ; copie du projet des bois personnels | `calc/domains/member_check_material.py`, `materials_project.used_ids` | REQ-002 à 005, 007, 016, ARCH-001, 002, 008 | `test_member_check_material.py` (OSB/3 par sollicitation et plage, 5/6/10/18/25/26 mm, bois personnel complet/incomplet, identifiant inconnu) |
| 4 | `resolve` fige `resistance` ; `compute` : `design`/`factor` → `Factors` ; lignes η_mod, γ_M ; note σ₉₀ ; ligne qui gouverne ; feu refuse un panneau | `member_check.py` | REQ-003, 006, 008, 014, 013, RISK-005, 007 | `test_member_check.py` : 13 taux identiques ; barre η_w/η_t ; panneau classe 1 = tableau b, classe 2 = η_mod·f_k/γ_M ; BI-04 77,2 % |
| 5 | Export 1.7 et fichier : nom et norme du matériau, titre « Cisaillement » ; `unfold.move_domain` (changement de genre) ; magasin `display` du genre `check` | `unfold.py`, `unfold_display.py`, `member_check.py` | REQ-009, 010, 011, 015, ARCH-009, 010, RISK-003, 004 | `test_unfold.py` (BI-01 identique, panneau compilé : η Typst = `compute`, déplacement avec ligne modifiée), `test_domain_file_display.py` (charges inchangées) |
| 6 | La bibliothèque dit « oui » ; mots de l'onglet Matériaux | `materials_derive.available_in`, `materials_tab_words.py` | REQ-012 | `test_materials_domain.py`, `test_materials_tab.py` |

**Lot 2 — les onglets**

| # | Étape | Fichiers | Exigences | Test |
|---|---|---|---|---|
| 7 | Domaine déclaré : formulaire en accordéons, messages (rouge, orange), résultats (η en dernier), dessins (flexion SIA aux valeurs de `compute`, figures du cisaillement) | `calc/domains/member_check_view.py` | UI-007, 009, 011, 012, ARCH-001 | `test_member_check_view.py` (sans Qt ; dessin sans couleur ni mot) |
| 8 | Services : bulle et menu de matériau, rangée « Sollicitation », rangée « Facteurs » ; champ `material` dans `FIELD_KINDS` | `calc/tools/material_menu.py`, `load_row.py`, `factors_row.py`, `contracts.py` | UI-004 à 006, 015, ARCH-004, RISK-009 | `test_material_menu.py`, `test_tab_services.py` |
| 9 | Les quatre onglets sur `CalcTab` ; Flambage et Déversement repliés ; « Cisaillement » en trois figures (fin de Q-010) ; `RESULT_KEY` ; table de #114 | `member_check_tab.py` (scindé), `tab_registry.py`, `member_check_tab_words.py`, `chrome.py`, `variable_calc.py` | UI-001 à 003, 008, 010, 014, REQ-011, 013, RISK-008 | `test_tab_registry.py`, `test_tab_overrides.py`, `test_member_check_tab.py`, `test_views.py`, `test_chrome.py`, `test_i18n.py` |
| 10 | Affichage de la vérification : aperçu Typst, niveau, options dans la source, commande à copier | `calc_display.py` (magasin), `domain_file_display.py` | UI-013, REQ-010, ARCH-005 | `test_domain_file_display.py`, `test_display_view.py` |
| 11 | Figure interactive et extraits (figure 8 du 4.2.7.1, tableaux 19a/19b) | `calc/norms/` extraits, `member_check_view.py` | UI-012 | `test_norm_excerpts.py` |

**Étape 12 — documentation** : `docs/domain/member-checks.md` (1.3, 1.7, facteurs), `materials.md`, `docs/ui/tab-member-checks.md`, `window.md`, `calc-tab.md` et `building-a-tab.md`, `docs/decisions.md` §13 (fin de Q-010, D-10, D-13 à 15, D-18, D-22, D-23) et `decisions-index.md`, `CHANGELOG.md`, la page « Nouveautés » fr / de / en (`website/content/<lang>/changes/`), les lignes du catalogue des tests, la copie du prototype (T64). **Étape 13** : suite complète, puis `verify-requirements`.

**Réserves reprises** : toutes (RISK-001 aux lots, 002 à 009 aux étapes 2 à 9, 010 à 011 aux étapes 9 et 3).

## 15. Vérification

*Vérification indépendante (agent `requirements-verifier`, 25.10.2026, sur le diff depuis `792b348`), puis corrections.*

- **REQ-001 à REQ-016, ARCH-001 à 003, 005, 007 à 010** : ✅ — `tests/test_member_check_material.py` (24), `test_member_check_view.py` (4), `test_sia265_1.py`, `test_materials_domain.py`, `test_member_check.py` ; les 13 vérifications du projet d'exemple identiques au bit près (instantané avant/après).
- **UI-001, UI-002, UI-004, UI-005, UI-006, UI-007, UI-009 à UI-011, UI-013 à UI-015, ARCH-004** : ✅ — `tests/test_member_check_tab.py` (16), `test_tab_registry.py`, `test_tab_overrides.py`, `test_tab_services.py`, `test_i18n.py`, `test_linkable_spin.py` ; captures d'écran. Ajoutés après la vérification : le verdict rouge au-delà de 100 %, l'épaisseur de 5 mm dite en rouge avec les plages, T39 dans les trois langues.
- **UI-003** : ✅ par la liste du type (dossiers, archives, Nouveau, Dupliquer) ; ⚠️ le groupement par position et le tri par taux ne sont pas ceux du prototype — la liste est celle de tous les onglets du type « Calcul » (dossiers), sans taux coloré. *(Levé au lot 3, ci-dessous.)*
- **UI-008** : ⚠️ les cinq résistances f_c,90,d sont trois boutons (en général, avec bois en saillie, appui d'extrémité) et une case pour la valeur entre parenthèses ; la raison d'une valeur absente (D30) est dite par le refus de la vérification. *(Levé au lot 3, ci-dessous.)*
- **UI-012** : ⚠️ partiel — la figure interactive (k_c sur λ_rel, k_m sur λ_rel,m, l'équation (28) de la figure 8) est faite ; les extraits épinglables de la figure 8 du 4.2.7.1 et des tableaux 19a/19b sur les champs restent à relever dans les PDF (suite proposée). *(Levé au lot 3, ci-dessous.)*
- **ARCH-004** : les rangées « Sollicitation » et « Facteurs » vivent dans le service `check_member.py`, non dans `load_row.py` / `factors_row.py` ; le menu de matériau est la brique `material_menu.py`. *(Levé au lot 3, ci-dessous.)*
- **ARCH-006, documentation** : ✅ — deux entrées de `docs/decisions.md` §13 et de `decisions-index.md`, `docs/ui/tab-member-checks.md` réécrit (l'ancien dans `docs/history/`), `calc-tab.md`, `building-a-tab.md`, `window.md`, `layout.md`, `member-checks.md` §3.3unvicies-bis, `materials.md`, `CHANGELOG.md`, « Nouveautés » 0.125 fr/de/en, prototype copié.
- Échec indépendant constaté : `test_formula_form.test_the_hovers_light…` plante aussi au commit `792b348` (#113).

*Lot 3 (25.10.2026, à la demande de l'ingénieur : l'issue terminée, non partielle) — les réserves ci-dessus levées :*

- **UI-003** : ✅ — `check_list.CheckList` (une `CaseList` à la place de celle du type) : les vérifications groupées par position (« T001 · … », « Sans position »), chacune son taux en pourcent vert ≤ 100 %, rouge au-delà, « — » et sa raison si elle n'est pas calculable ; « Par position » / « Par taux » ; le taux calculé par `member_check.utilisations` sur le dernier export (`CheckDomain.list_rows`). Test : `test_member_check_tab.test_the_list_groups_by_position_colours_the_rates_and_sorts_by_rate`.
- **UI-008** : ✅ — les cinq cartes (`support`, champ propre au brouillon, écrit `case` et `larger` dans le fichier par `_apply_support`), chacune sa valeur de `member_check.f_c_90_table`, la carte sans valeur grisée avec « SIA 265 ne donne pas de valeur entre crochets pour D30 » ; crochet optionnel `choice_values` du type. Tests : `test_member_check_view.test_the_five_cards…`, `test_member_check_tab.test_the_five_cards…` (DR-02, D30). Corrigé au passage : une compression à un angle sans longueur d'appui l n'est plus « calculable » (elle plantait `compute`), elle dit sa raison.
- **UI-012** : ✅ — `calc/norms/sia265-2021-checks-excerpts.json` (4.2.1.1 à 4.2.9, 2.2.6, figures 7 à 11 et 46, fr et de, relevés dans les PDF avec leurs cadres) et `sia265-1-2018-checks-excerpts.json` (6.1.2.1), tenus aux PDF par `tests/test_norm_excerpts.py` (18) ; chaque champ et chaque figure du cisaillement épingle les siens (`EXCERPTS`) ; la rangée « Sollicitation » porte le ⓘ du tableau du matériau (tableaux 19a et 19b de l'OSB/3). Test : `test_osb3_s_loading_bubbles…` épingle « Tableaux 19a et 19b ».
- **ARCH-004** : ✅ — trois services : `check_member.CheckMember` (position, matériau et menu, section), `load_row.LoadRow` (« Sollicitation », ⓘ du matériau, « La vérification lit »), `factors_row.FactorsRow` (« Facteurs ») ; ce qu'ils lisent pareil dans `check_rows.py` ; aucun ne lit l'autre, chacun prend le matériau du brouillon.
- **UI-001** : ✅ — la barre de la fenêtre « Exemple — Sécurité structurale › Cisaillement — Woodcore » (`SideNav.path`, `update_title` à chaque changement d'onglet). Test : `test_home.test_the_window_s_bar_names_the_tab_open_alone_in_its_group`.

## 16. Journal d'avancement

| Date | Statut | Fait / reste |
|---|---|---|
| 2026-10-24 | draft | spécification extraite de l'issue #112 : 72 points de la source, 16 REQ, 14 UI, 7 ARCH, 9 CON, 21 décisions (3 proposées), 5 idées, 3 questions ; normes lues : SIA 265/1:2018 6.1.2.1, 6.2.1.2 à 6.2.1.4, tableau 9, tableau 19a/19b ; prototype V3 lu (page) |
| 2026-10-24 | specified | réponses de l'ingénieur enregistrées : Q-001 A, Q-003 A, Q-002 hors options (η_t, η_w, γ_M en listes ; règle de la norme lue : barre η_w·η_t sur les Tableaux 8 et 9, panneau η_mod du Tableau 9 et γ_M du Tableau 6 ; quatre écarts à confirmer à l'approbation) ; REQ-006 réécrite, UI-015, ARCH-008 à 010, D-22 à D-24 |
| 2026-10-24 | reviewed | revue d'architecture : APPROUVER AVEC RÉSERVES (11 risques, aucun bloquant), plan en deux lots et 13 étapes ; en attente de l'approbation |
| 2026-10-24 | approved | approbation unique des huit specs du 24.10.2026 par l'ingénieur (AskUserQuestion) : plan approuvé tel quel ; toutes les propositions « à confirmer » des revues acceptées comme recommandées ; ordre d'implémentation #108 → #115 → #114 → #113 → #112 → #109 → #107 → #106, un agent par issue ; commits et push autorisés au fil du travail ; écarts et questions notés en §16 et posés à la fin |
| 2026-10-25 | implementation | étape 1 : Tableaux 7 et 8 de SIA 265/1 (`sia265-1-2018-tab07-08-kled.json`, p. 27), γ_M accidentel (note 1 du Tableau 6), `sia265_1.kled_classes/kled_actions/admitted_classes/admitted_kled/accidental_gamma_m/design_gamma_m`, tenus au PDF (`test_sia265_1.py`) — REQ-006, ARCH-002 |
| 2026-10-25 | implementation | étapes 2 à 4 : source 1.3 et export 1.7 (schémas, `stamp_version`, refus nommés), `member_check_material.py` (`check_fields`, `needs`, `resistance`, `Strengths`, `offered`, `usable_in_checks`), `resolve` qui fige `resistance`, `compute` par `Strengths` (13 vérifications identiques au bit près), lignes η_mod/γ_M, note σ₉₀, `governing`, feu refusé pour un panneau, `used_ids` et `sync_materials` — REQ-001 à 008, 013 à 016, ARCH-001, 002, 003, 008 |
| 2026-10-25 | implementation | étapes 5 et 6 : la ligne de l'élément nomme le matériau et sa sollicitation, `unfold.check_header`/`check_title`, `display` lu par le générateur et `unfold_display.apply_check_display` (crochet `after_unfold`), `unfold.move_domain`, `member_check.change_kind`/`save_kind_change`/`export(moved=)` ; `available_in` dit « oui » — REQ-009 à 012, ARCH-005, 009, 010 ; `tests/test_member_check_material.py` (24 tests) |
| 2026-10-25 | testing | lot 1 commité et poussé (`571f5a7`) ; étapes 7 à 10 : `member_check_view.py` (le domaine des quatre onglets), services `check_member.py`, `check_results.py`, `check_display.py`, brique `material_menu.py`, `check_tabs.py`, crochets du type (`owns`, `save_case`, `export_cases`, `graph_id`, `message_params`, `Field.block`, `zero_none`), Flambage et Déversement repliés, mots `vc_`, 58 mots morts retirés ; tests réécrits — UI-001 à 011, 013 à 015, REQ-011, ARCH-004, 005, 009, 010 |
| 2026-10-25 | completed | étape 12 : documentation, décisions, Nouveautés, prototype ; étape 13 : vérification indépendante (§15), corrections, suite complète ; UI-012 partiel (extraits de la norme) et UI-008 simplifié, notés en §15 |
| 2026-10-25 | completed | lot 3, à la demande de l'ingénieur : UI-012 (extraits de la SIA 265 et du tableau du matériau, relevés dans les PDF), UI-003 (liste par position, taux coloré, tri), UI-008 (cinq cartes de f_c,90,d), ARCH-004 (« Sollicitation » et « Facteurs » services propres), UI-001 (barre de la fenêtre) ; tests, documentation, CHANGELOG, Nouveautés ; vérification (§15) |
