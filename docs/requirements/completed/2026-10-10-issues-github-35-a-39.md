---
id: 2026-10-10-issues-github-35-a-39
titre: Charges (poids propre et surcharge, neige, vent) calculées dans Woodcore, flambement, déversement et effort tranchant, résultat toujours affiché
status: completed
cree: 2026-10-10
mis_a_jour: 2026-10-11
source: issues GitHub #35, #36, #37, #38, #39 (message écrit « implémente les issues 35, 36, 37, 38, 39 »)
docs: [docs/domain/loads.md, docs/domain/member-checks.md, docs/ui/window.md, docs/typst/report-engine.md, docs/architecture/principles.md, docs/decisions.md]
---

# Issues #35 à #39 — Spécification

## 1. Objectif

Faire calculer par Woodcore lui-même, dans des onglets de la fenêtre, les trois charges que l'ingénieur calcule aujourd'hui dans l'Excel *Belastungsannahmen* — poids propre et surcharge (avec le dessin de la composition, à la Ubakus), neige (avec la toiture cylindrique que l'Excel n'a pas), vent (toutes les formes de bâtiment de la SIA 261) — en suivant la SIA 261 et non l'Excel. Ajouter aux vérifications enregistrées le flambement, le déversement et l'effort tranchant (SIA 265). Corriger le mode «Affichage» : le résultat d'une vérification est toujours affiché.

## 2. Source

Les cinq issues, mot pour mot (titre, contexte, demandes).

> **T1** — #35 « Charges permanentes et d'exploitation » — « Nouvel onglet pour le poids propre et la surcharge, inspiré de l'Excel *Belastungsannahmen* (dossier Offline). »
>
> **T2** — #35, #36, #37, #38 (contexte commun) — « Les normes SIA du dossier Normen-Florian font foi; l'Excel peut contenir des fautes (par exemple le facteur d'état W, lié à la classe d'humidité, parfois oublié). »
>
> **T3** — #35, #36, #37 (contexte commun) — « Calcul en Python (`calc/domains/`, sans Qt), l'Excel ne sert que de référence. »
>
> **T4** — #35 — « Un seul onglet pour le poids propre et la surcharge; pour chaque variable, l'ingénieur choisit s'il s'agit d'un poids propre ou d'une surcharge. »
>
> **T5** — #35 — « Afficher automatiquement la structure (composition), à la manière d'Ubakus (https://www.ubakus.de/en/r-value-calculator/). »
>
> **T6** — #35 — « Coter la hauteur des éléments sur cette structure, et leur largeur quand il y a des carrelets espacés entre eux. »
>
> **T7** — #36 « Neige » — « Nouvel onglet pour la neige, inspiré de l'Excel *Belastungsannahmen*. La SIA 261 (dossier Normen-Florian) fait foi »
>
> **T8** — #36 — « Calculer la neige d'après l'Excel *Belastungsannahmen*, en suivant la SIA 261. »
>
> **T9** — #36 — « Ajouter le cas de charge absent de l'Excel: la 3e colonne de la figure 3 de la SIA 261 (le modèle avec l'hémisphère). À lire dans l'édition de Normen-Florian avant de coder. L'ingénieur avait d'abord écrit «SIA 265», puis corrigé en «SIA 261». »
>
> **T10** — #37 « Vent » — « Nouvel onglet pour le vent, inspiré de l'Excel *Belastungsannahmen*. »
>
> **T11** — #37 — « Calculer le vent d'après l'Excel *Belastungsannahmen*, en suivant la SIA 261. »
>
> **T12** — #37 — « Couvrir toutes les formes de bâtiment de la SIA 261, y compris celles que l'Excel ne traite pas. »
>
> **T13** — #38 « Vérifications — flambement, déversement, effort tranchant » — « Suite de #12. Vérifications de membrure à ajouter (voir `docs/domain/member-checks.md`). »
>
> **T14** — #38 — « Implémenter le flambement, le déversement et l'effort tranchant. »
>
> **T15** — #38 — « Des Excel de Offline les calculent sans doute: les chercher, puis les confronter aux normes. »
>
> **T16** — #39 « Affichage — niveau de détail » — « Suite de #20. Mode «Affichage», volet de droite, options d'une commande. Le résultat d'une commande doit toujours être affiché. »
>
> **T17** — #39 — « **Observé:** dans le volet de droite, sous les options de la commande (par exemple la traction), la case du résultat peut être décochée. Le résultat disparaît, et le niveau de détail «sélection manuelle» ne se règle pas correctement. »
>
> **T18** — #39 — « **Attendu:** pour la traction, le résultat σt,0,d / ft,0,d est toujours affiché. Sa case est toujours cochée, légèrement grisée, non décochable. »
>
> **T19** — #39 — « Le niveau de détail reste au choix entre 1, 2 et 3 (pas 0), et fonctionne sans problème. »

## 3. Exigences fonctionnelles

### REQ-001 — Poids propre et surcharge calculés en Python depuis une composition saisie dans Woodcore
- **Exigence** : Woodcore doit calculer, dans `calc/domains/` sans Qt, la charge d'une composition (une source par élément de construction : toiture, plancher, paroi…) couche par couche, `charge [kN/m²] = ρ · épaisseur · largeur / entraxe` (et ρ seul pour un matériau en kg/m², g = 10 m/s² comme SIA 261 Anhang A et l'Excel), sommer les couches en g_k et a_k et garder la valeur choisie arrondie (« Gewählt ») avec le refus existant d'une valeur choisie inférieure à la somme (§3.3ter).
- **Source** : T1, T3, D-07
- **Priorité** : doit
- **Critère d'acceptation** : une composition reproduisant l'onglet `Flachdach` de l'Excel donne la même somme (à 1e-9) ; un test `tests/test_dead_load_source.py` la tient ; une valeur choisie inférieure à la somme stoppe l'export en nommant le fichier et le champ.

### REQ-002 — Chaque couche est poids propre ou surcharge, au choix
- **Exigence** : Woodcore doit laisser l'ingénieur choisir pour chaque couche (« variable ») si elle compte au poids propre g_k ou à la surcharge a_k, dans le même onglet.
- **Source** : T4
- **Priorité** : doit
- **Critère d'acceptation** : basculer une couche de g_k à a_k dans l'onglet déplace sa charge d'une somme à l'autre, au même instant dans les résultats et après export dans `data/calculations.json`.

### REQ-003 — Neige calculée en Python selon la SIA 261
- **Exigence** : Woodcore doit calculer la neige (SIA 261:2020 ch. 5) à partir des entrées de l'onglet : altitude h₀ et correction de l'annexe D → h_ref ; s_k = max(0.9 ; 0.4·(1+(h_ref/350)²)) (5.2) ; C_e, C_T ; forme de toiture et modèle de charge 1 et 2 de la figure 3 avec μ₁(α), μ₂, μ₂m de la figure 2 ; toit plat > 20 m de la figure 4 (5.3.5) ; glissement empêché μ₁ = 0.8 (5.3.4) **appliqué à toutes les branches** (l'Excel l'oublie dans les demi-charges du modèle 2, N37/N38) ; toit à un pan comme demi-toit symétrique (5.3.2) ; pente > 60° sans neige si le glissement n'est pas empêché (5.3.3). Chaque valeur de la norme est lue d'un fichier de `calc/norms/` transcrit de `SIA261-2020-FR.pdf`, aucune ne vient de l'Excel.
- **Source** : T7, T8, T2
- **Priorité** : doit
- **Critère d'acceptation** : les cinq modèles de l'Excel (Flachdach, Giebeldach LM1/LM2, Sheddach LM1/LM2) donnent les valeurs de la norme recalculées à la main dans un test ; le cas « glissement empêché, modèle 2 » donne μ ≥ 0.8 sur les deux demi-pans (écart documenté avec l'Excel).

### REQ-004 — Toiture cylindrique (3e colonne de la figure 3)
- **Exigence** : Woodcore doit ajouter le cas de charge absent de l'Excel, la 3e colonne de la figure 3 de la SIA 261:2020 (p. 28) — la toiture courbe, que l'issue nomme « l'hémisphère » — avec ses modèles de charge 1 et 2 et le coefficient μ₃ de la figure 2, lus dans `SIA261-2020-FR.pdf` (et vérifiés sur l'édition allemande) avant le code.
- **Source** : T9
- **Priorité** : doit
- **Critère d'acceptation** : une toiture cylindrique donne les charges des deux modèles de la figure 3 avec μ₃ de la figure 2 ; le test cite la page et la figure ; le fichier `calc/norms/` qui porte μ₃ nomme l'édition.

### REQ-005 — Vent calculé en Python selon la SIA 261
- **Exigence** : Woodcore doit calculer le vent (SIA 261:2020 ch. 6 et annexe des coefficients) : q_p0 au lieu, catégorie de terrain (z_g, α_r), z (≥ 5 m, ≥ 10 m en catégorie IV), c_h = 1.6·((z/z_g)^α_r + 0.375)², q_p = c_h·q_p0, c_red **calculé** (et non lu sur une barre de défilement comme l'Excel), c_d, les forces globales q_k = c_red·c_d·c_f·q_p par surface de référence, et les pressions locales q_p·(c_pe − c_pi) avec leur enveloppe sur les directions (le tableau de §3.3quater). Les coefficients sont lus de `calc/norms/`.
- **Source** : T10, T11, T2
- **Priorité** : doit
- **Critère d'acceptation** : pour une des figures de l'Excel et les mêmes entrées, Woodcore reproduit les forces globales et locales de l'Excel corrigé (v3.2) ; c_red suit la formule de la norme ; test `tests/test_wind_source.py`.

### REQ-006 — Toutes les formes de bâtiment de la SIA 261
- **Exigence** : Woodcore doit couvrir toutes les formes de bâtiment pour lesquelles la SIA 261:2020 donne des coefficients de pression et de force, y compris celles que l'Excel ne traite pas (l'Excel porte les figures 31 à 45, 59a et 59b, et n'en trouve pas 42 à 45 à cause d'un VLOOKUP approché). Périmètre : D-06.
- **Source** : T12
- **Priorité** : doit
- **Critère d'acceptation** : chaque figure du périmètre est un enregistrement de `calc/norms/` portant son numéro et sa page ; un test parcourt la liste et calcule un cas par figure.

### REQ-007 — Flambement enregistré (SIA 265 4.2.8)
- **Exigence** : Woodcore doit offrir le flambement comme vérification enregistrée (`kind: buckling`) : effort normal de compression, longueurs de flambement l_k,y et l_k,z (ou l et β), calculé en Python (`member_check.compute`) et imprimé par `#verify-compression(stability: true)` ; E_0,05 multiplié par η_w,E (Tabelle 4) — l'Excel *Stabilität Stützen* calcule η_w,S sans l'appliquer, du côté de l'insécurité.
- **Source** : T14, T15, T2
- **Priorité** : doit
- **Critère d'acceptation** : `tests/test_member_check.py` tient l'égalité Python/Typst à 1e-6 pour des flambements en classes d'humidité 1, 2 et 3, bois massif et lamellé-collé, λ_rel de part et d'autre de 0.3 ; un cas de l'Excel en classe 1 est reproduit.

### REQ-008 — Déversement enregistré (SIA 265 4.2.9)
- **Exigence** : Woodcore doit offrir le déversement (`kind: lateral-torsional`) : moments, distance a entre appuis latéraux (ou σ_m,crit donné), effort normal éventuel ((37)/(38)), calculé en Python et imprimé par `#verify-bending` / `#verify-bending-normal` avec `stability: true` ; une section ronde est refusée comme non calculable (pas de déversement, §3.3undecies).
- **Source** : T14, T15
- **Priorité** : doit
- **Critère d'acceptation** : égalité Python/Typst à 1e-6 sur les trois branches de k_m (39) ; un cas de l'Excel *Stabilität Stützen Rechteckquerschnitte* reproduit.

### REQ-009 — Effort tranchant enregistré (SIA 265 4.2.5)
- **Exigence** : Woodcore doit offrir l'effort tranchant (`kind: shear`) : V_z, V_y (additionnés vectoriellement) et le facteur de la moelle, τ = 1.5·V/A ⩽ f_v,d, calculé en Python et imprimé par `#verify-shear`.
- **Source** : T14
- **Priorité** : doit
- **Critère d'acceptation** : égalité Python/Typst à 1e-6 ; un cas du livre Bemessungsbeispiele (p. 114 déjà dans les oracles) reproduit.

### REQ-010 — Le résultat d'une vérification est toujours imprimé
- **Exigence** : au niveau de détail −1 (sélection manuelle), Woodcore doit toujours imprimer le résultat d'une vérification (pour la traction σ_t,0,d et le rapport σ_t,0,d / f_t,0,d), quel que soit `shown:` ; son niveau se règle entre 1, 2 et 3, jamais 0. Fenêtre et Typst (D-05).
- **Source** : T16, T18, T19
- **Priorité** : doit
- **Critère d'acceptation** : `shown: (:)` imprime σ_t,0,d ; `shown: (sigma_t_0_d: 0)` est refusé ou ramené à 1 ; un test de `tests/test_timber.py` par vérification enregistrée.

## 4. Exigences d'interface (fenêtre, rapport, site)

### UI-001 — Onglet « Poids propre et surcharge »
- **Exigence** : un seul onglet liste les compositions (à gauche, dossiers et ordre comme les autres onglets), et pour la composition choisie un tableau de couches (niveau/Ebene, matériau, épaisseur, largeur, entraxe, g_k ou a_k), les sommes et la valeur choisie, avec la page du rapport en aperçu.
- **Source** : T1, T4
- **Langues** : fr / de / en
- **Critère d'acceptation** : `tests/test_dead_load_tab.py` crée une composition, ajoute trois couches, en bascule une en a_k, enregistre, et relit le fichier source.

### UI-002 — Dessin de la composition, à la Ubakus
- **Exigence** : l'onglet dessine automatiquement la composition en coupe, couche sur couche à l'échelle, chaque matériau avec sa hachure ou sa couleur de `calc/tools/theme.json`, les carrelets ou chevrons espacés dessinés comme des sections répétées à leur entraxe ; le même dessin (SVG) est imprimable dans le rapport.
- **Source** : T5
- **Langues** : fr / de / en (légendes des matériaux)
- **Critère d'acceptation** : changer une épaisseur redessine la coupe ; le SVG produit est tenu par un test (nombre de couches, hauteurs proportionnelles).

### UI-003 — Cotes de la composition
- **Exigence** : le dessin cote la hauteur (épaisseur) de chaque couche et, pour une couche de carrelets espacés, leur largeur (et leur entraxe).
- **Source** : T6
- **Langues** : —
- **Critère d'acceptation** : le SVG d'une composition avec un lattis 60/40 e = 500 porte les cotes 40, 60 et 500 ; une couche continue porte sa seule hauteur.

### UI-004 — Onglet « Neige »
- **Exigence** : un onglet saisit le lieu (altitude, correction), C_e, C_T, la forme de toiture (dont la toiture cylindrique), les pentes ou dimensions, le glissement, et montre les charges des modèles 1 et 2 avec un croquis de la disposition de la figure 3.
- **Source** : T7, T9
- **Langues** : fr / de / en
- **Critère d'acceptation** : `tests/test_snow_tab.py` saisit un toit à deux pans et lit q_k,11 et q_k,12 calculés.

### UI-005 — Onglet « Vent »
- **Exigence** : un onglet saisit q_p0, b, d, h, la catégorie de terrain, la forme de bâtiment (figure) et l'ouverture, et montre q_p, les forces globales et le tableau des pressions locales.
- **Source** : T10, T12
- **Langues** : fr / de / en
- **Critère d'acceptation** : `tests/test_wind_tab.py` choisit une figure, saisit les dimensions et lit les forces globales.

### UI-006 — Onglets « Flambement », « Déversement », « Effort tranchant »
- **Exigence** : les trois onglets `SoonTab` correspondants deviennent des onglets de vérification (`MemberCheckTab`), chacun avec ses champs d'action (N et longueurs de flambement ; moments, a ou σ_m,crit, N ; V_z, V_y, moelle), le résultat instantané Python et l'aperçu Typst.
- **Source** : T14
- **Langues** : fr / de / en
- **Critère d'acceptation** : `tests/test_member_check_tab.py` crée une vérification de chaque genre, lit η instantané et le compare à l'export.

### UI-007 — Case du résultat verrouillée
- **Exigence** : dans « Affichage », volet de droite, au niveau « sélection manuelle », la ligne du résultat d'une vérification a sa case toujours cochée, légèrement grisée, non décochable ; sa boîte de niveau offre 1, 2, 3 (pas 0) ; la sélection manuelle se règle sans perte (les autres cases gardent leur état après un rafraîchissement).
- **Source** : T17, T18, T19
- **Langues** : fr / de / en (infobulle de la case verrouillée)
- **Critère d'acceptation** : `tests/test_member_check_tab.py` : la case de σ_t,0,d est cochée et désactivée, sa boîte de niveau n'a pas 0, `options()["shown"]` contient toujours `sigma_t_0_d` ≥ 1.

## 5. Exigences d'architecture

### ARCH-001 — Calcul des charges dans `calc/domains/`, sans Qt
- **Exigence** : les trois calculs vivent dans `calc/domains/` (modules sans Qt) ; les onglets montrent, éditent et appellent, ne recalculent jamais ; Typst imprime l'export.
- **Source** : T3 ; principes (docs/architecture/principles.md) — inféré
- **Critère d'acceptation** : aucun import Qt dans les modules de domaine (test d'import existant étendu).

### ARCH-002 — Valeurs de la norme dans `calc/norms/`, transcrites de l'édition nommée
- **Exigence** : s_k, μ (figures 2–4), corrections de l'annexe D, C_e, catégories de terrain, c_pe/c_pi/c_f de chaque figure, c_red, valeurs de η_w, β_c… sont lus de fichiers `calc/norms/sia261-2020-*.json` (ou existants de la SIA 265), chacun nommant l'édition et la page ; aucune n'est copiée de l'Excel.
- **Source** : T2, T15 ; CLAUDE.md « One source of truth », « No hardcoding » — inféré
- **Critère d'acceptation** : grep des modules de domaine : aucun nombre de la norme en dur ; chaque fichier `norms` a `edition` et `page`.

### ARCH-003 — Sources versionnées, schémas
- **Exigence** : chaque charge saisie est un fichier source dans le dossier du projet (`Woodcore-Datei/<dossier>/<id>.json`), décrit par un schéma avec `schema_version`, validé avant écriture ; les instances entrent dans `data/calculations.json` sous la forme `vars`/`steps`/`checks` habituelle (§3.3) avec leur provenance `python:` et `norm:`. Le schéma des vérifications enregistrées (`member-check-source` 1.0, `checks` 1.0) gagne les champs des trois nouveaux genres (additif → mineure, ou 1.1 ; à trancher dans la revue).
- **Source** : principes règles 4–5 — inféré
- **Critère d'acceptation** : `tests/test_schemas.py` (ou équivalent) valide un exemple de chaque source ; un fichier malformé stoppe l'export en nommant fichier et champ.

### ARCH-004 — Cohabitation avec la lecture des classeurs existants
- **Exigence** : les domaines `snow-load`, `wind-load`, `dead-load` lus des classeurs (§3.3bis/ter/quater) cohabitent avec les sources de Woodcore (D-04) ; la décision est écrite dans `docs/decisions.md` (§13) avec son prix — elle renverse « Snow is calculated in Excel, not in Python ».
- **Source** : T3 ; CLAUDE.md « Preserve the architecture » — inféré
- **Critère d'acceptation** : une entrée de §13 dans `docs/decisions.md` ; les projets existants (`tests/projet-exemple/`) s'exportent toujours.

## 6. Contraintes

- **CON-001** — Les normes du dossier Normen-Florian font foi (SIA 261:2020 FR/DE, SIA 265:2021 FR/DE) ; une valeur est lue sur l'édition nommée, jamais de mémoire ; l'Excel n'est que référence et peut être faux. Source : T2, T3, T9, T15.
- **CON-002** — Le facteur d'état η_w (classe d'humidité, SIA 265 Tabelle 4), et η_w,E sur la rigidité, sont appliqués partout où la norme les demande ; c'est le défaut type que l'ingénieur signale dans les Excel. Source : T2.
- **CON-003** — Trois langues (de, fr, en) pour toute chaîne de la fenêtre et du rapport (`calc/i18n/`). Inféré (CLAUDE.md).
- **CON-004** — Une commande Typst nouvelle ou changée a son bloc `///`, deux exemples qui compilent et sa traduction dans `calc/i18n/commands.json` ; `CHANGELOG.md` et la page « Nouveautés » en trois langues. Inféré (CLAUDE.md).
- **CON-005** — Les clés imprimables d'une nouvelle commande ou d'un nouveau genre entrent dans `lib/shown-variables.json` et prennent le niveau −1 (`docs/open-questions.md`, issue #20). Inféré.
- **CON-006** — Les tests travaillent sur `tests/projet-exemple/`, jamais sur un projet de l'ingénieur. Inféré (CLAUDE.md).

## 7. Décisions prises

- **D-01** — La 3e colonne de la figure 3 de la SIA 261:2020 (p. 28) est la toiture courbe (cylindrique), coefficient μ₃ de la figure 2 : c'est le « modèle avec l'hémisphère » de l'issue (lecture de la norme, 10.10.2026 ; à confirmer par l'ingénieur à l'approbation).
- **D-02** — Où la norme et l'Excel divergent, la norme l'emporte et l'écart est écrit dans `docs/domain/loads.md` ou `member-checks.md` (T2). Écarts relevés : neige — μ ≥ 0.8 oublié dans N37/N38 (modèle 2, glissement empêché) ; vent — c_red lu sur une barre, VLOOKUP approché qui perd les figures 42–45 ; flambement — η_w,S calculé mais non appliqué à E_0,05 (insécurité), résistance mise à 0 au-delà de λ = 150 alors que 4.2.8.5 admet 200 pour les contreventements et éléments secondaires, E_0,05 dérivé de E_0,mean au lieu de l'Anhang B.
- **D-04** — Cohabitation (Q-001) : les onglets Poids propre et surcharge, Neige et Vent écrivent leurs sources dans `Woodcore-Datei/`, calculées en Python sous les domaines existants `snow-load`, `wind-load`, `dead-load` (une instance par source) ; les feuilles `SL-*`, `WL-*`, `EL+AL-*` d'un classeur restent lues ; un même identifiant dans les deux est refusé à l'export. Prix : deux chemins vers un même domaine à tenir cohérents ; renverse en partie « snow and wind are calculated in Excel » (§13), à écrire dans `docs/decisions.md`.
- **D-05** — Résultat toujours imprimé (Q-002) : au niveau −1, chaque `verify-*` imprime toujours son résultat (contrainte de la vérification et rapport), à un niveau de 1 à 3, jamais 0 ; `shown:` qui le met à 0 est ramené à 1 ou refusé (à trancher dans la revue) ; la fenêtre verrouille la case. Renverse D-12 de l'issue #20 pour les vérifications.
- **D-06** — Vent (Q-003) : toutes les figures de la SIA 261:2020 qui donnent les coefficients d'un bâtiment (toitures plates, à un et deux pans, en croupe, sheds, courbes, toitures isolées/auvents) ; panneaux, treillis, cheminées, ponts exclus.
- **D-07** — Matériaux (Q-004) : Woodcore livre une bibliothèque de base réunissant les poids de la SIA 261 (annexe) et la bibliothèque `Material (hier ergänzen)` de l'Excel 3.2, chaque entrée gardant sa source (`Quelle`) ; l'ingénieur ajoute des poids volumiques à la main, dans une bibliothèque du projet. Une entrée de l'Excel qui contredit la norme suit la norme et l'écart est noté.
- **D-08** — Un seul onglet « Poids propre et surcharge » remplace les deux onglets réservés `tab_ac_selfweight` et `tab_ac_superimposed` (l'ingénieur, 11.10.2026, ARCH-RISK-006) ; ses clés, `NAV_GROUPS`, `MODE_TABS` et les glossaires suivent.
- **D-09** — Le déversement prend N complet, (37) compris (l'ingénieur, 11.10.2026, ARCH-RISK-103) : avec une compression, la source porte aussi les longueurs de flambement, et la carte « longueurs de flambement » est une seule classe partagée par les onglets Flambage et Déversement (les mêmes champs `l_k_y`, `l_k_z`, `l`, `beta_y`, `beta_z` dans les deux genres, un seul code de saisie et de contrôle).
- **D-03** — « Surcharge » est l'a_k (Auflast) de l'Excel, non la charge utile q_k de la Tabelle 8, déjà dans Woodcore (§3.3septies).

## 8. Hors périmètre

- Les combinaisons de charges (SIA 260 4.4.2.1, `combinations.py`) et les ψ — non demandés.
- Le séisme, la torsion, la déformation, la vibration (genres restant `SoonTab`).
- Lier une charge à une position (interdit, §8 de loads.md).

## 9. Idées non retenues comme exigences

- Les autres dispositions de la SIA 261 ch. 5 que l'Excel signale sans calculer (décrochements de toiture fig. 5, corniche 5.3.7) — pas demandées par #36 ; candidates à une issue suivante.
- L'effort tranchant aux entailles (SIA 265 5.2.2, k_red, Excel *Ausklinkung*) et le cisaillement des chevrons à entaille (Excel *Sparren*, sans k_red) — #38 dit « effort tranchant » ; à proposer en issue séparée.
- La valeur U (Ubakus est un calculateur de résistance thermique) — l'issue n'en cite que le dessin.

## 10. Questions

### Q-001 — Que deviennent les classeurs Belastungsannahmen ?
- **Pourquoi elle compte** : la doc (§3.3bis, §3.3quater, §13) fait de l'Excel la source de la neige et du vent ; l'issue demande le calcul en Python. Selon la réponse, les projets existants gardent ou perdent leurs charges, et les noms de domaine changent ou non.
- **Options** : A (recommandée) cohabitation — les nouveaux onglets écrivent leurs sources dans `Woodcore-Datei/`, calculées en Python sous les mêmes domaines `snow-load`, `wind-load`, `dead-load` (une instance par source, `engine: python`) ; les feuilles `SL-*`, `WL-*`, `EL+AL-*` d'un classeur restent lues, un même identifiant dans les deux étant refusé ; B remplacement — la lecture des classeurs est retirée ; C import — Woodcore lit une fois les entrées d'un classeur dans des sources, puis ignore le classeur.
- **Réponse** : A, cohabitation (l'ingénieur, 11.10.2026).

### Q-002 — Le résultat toujours affiché : dans la fenêtre seulement, ou aussi dans Typst ?
- **Pourquoi elle compte** : renverse la décision D-12 de l'issue #20 (un résultat non choisi disparaît au niveau −1). Verrouiller la case seulement laisse un `shown:` écrit à la main faire disparaître le résultat.
- **Options** : A (recommandée) les deux — `verify-*` impriment toujours leur résultat au niveau −1 (niveau 1 par défaut, jamais 0) et la fenêtre verrouille la case ; B la fenêtre seulement.
- **Réponse** : A, fenêtre et Typst (l'ingénieur, 11.10.2026).

### Q-003 — « Toutes les formes de bâtiment » du vent : quel périmètre ?
- **Pourquoi elle compte** : chaque figure est une table de coefficients à transcrire et tester ; le travail varie du simple au triple.
- **Options** : A (recommandée) toutes les figures de la SIA 261:2020 qui donnent les coefficients d'un **bâtiment** (plans rectangulaires, toitures plates, à un et deux pans, en croupe, sheds, courbes, toitures isolées/auvents) — les ouvrages qui ne sont pas des bâtiments (panneaux, treillis, cheminées, ponts) exclus ; B toutes les figures du chapitre, bâtiments ou non ; C celles de l'Excel (31–45, 59a/b) d'abord, le reste dans une issue suivante.
- **Réponse** : A, tous les bâtiments (l'ingénieur, 11.10.2026).

### Q-004 — Bibliothèque des matériaux du poids propre
- **Pourquoi elle compte** : le poids volumique de chaque couche vient d'une liste ; elle est une source de vérité nouvelle.
- **Options** : A (recommandée) Woodcore livre une bibliothèque `calc/norms/` des poids de la SIA 261 Anhang A (ce que la norme donne), complétée par une bibliothèque du projet que l'ingénieur édite dans l'onglet ; B reprendre la bibliothèque de l'Excel (199 + 37 matériaux, sources mêlées) comme bibliothèque de Woodcore ; C seulement la bibliothèque du projet.
- **Réponse** : « SIA 261 + Bibliothèque de l'Excel (de base dans woodcore). L'ingénieur peut ajouter des poids volumiques manuellement » (l'ingénieur, 11.10.2026) — A et B réunies.

## 11. Critères d'acceptation

- [x] REQ-001 — somme des couches = Excel `Flachdach` ; valeur choisie < somme refusée
- [x] REQ-002 — basculer g_k/a_k déplace la charge
- [x] REQ-003 — cinq modèles de neige, μ ≥ 0.8 sur toutes les branches
- [x] REQ-004 — toiture cylindrique, μ₃, deux modèles
- [x] REQ-005 — vent : q_p, c_red calculé, forces globales et locales
- [x] REQ-006 — chaque figure du périmètre calculée par un test
- [x] REQ-007 — flambement Python = Typst, η_w,E appliqué
- [x] REQ-008 — déversement Python = Typst, trois branches de k_m
- [x] REQ-009 — effort tranchant Python = Typst
- [x] REQ-010 — résultat imprimé à −1 quel que soit `shown:`
- [x] UI-001 — onglet poids propre/surcharge, couches, enregistrement
- [x] UI-002 — dessin de la composition
- [x] UI-003 — cotes hauteur, largeur et entraxe des carrelets
- [x] UI-004 — onglet neige
- [x] UI-005 — onglet vent
- [x] UI-006 — trois onglets de vérification
- [x] UI-007 — case du résultat cochée, grisée, niveau 1–3
- [x] ARCH-001 — domaines sans Qt
- [x] ARCH-002 — valeurs de la norme dans `calc/norms/` avec édition et page
- [x] ARCH-003 — sources et schémas versionnés, validation
- [x] ARCH-004 — décision écrite, projet exemple exporté
- [x] Documentation : `docs/domain/loads.md`, `member-checks.md`, `docs/ui/window.md`, `docs/typst/report-engine.md`, `docs/decisions.md`, `CHANGELOG.md`, « Nouveautés » fr/de/en, `///` + exemples + traductions des commandes touchées.
- [x] Tests : fichiers `tests/test_*.py` ajoutés ou étendus, et passent.

## 12. Traçabilité

| Source | Élément | Statut |
|---|---|---|
| T1 | REQ-001, UI-001 | capturé |
| T2 | CON-001, CON-002, D-02 | capturé |
| T3 | ARCH-001, ARCH-004, D-04 | capturé (Q-001 répondue) |
| T4 | REQ-002, UI-001 | capturé |
| T5 | UI-002 | capturé |
| T6 | UI-003 | capturé |
| T7 | REQ-003, UI-004 | capturé |
| T8 | REQ-003 | capturé |
| T9 | REQ-004, D-01 | capturé |
| T10 | REQ-005, UI-005 | capturé |
| T11 | REQ-005 | capturé |
| T12 | REQ-006, D-06 | capturé (Q-003 répondue) |
| T13 | REQ-007–009 | capturé |
| T14 | REQ-007, REQ-008, REQ-009, UI-006 | capturé |
| T15 | D-02, REQ-007, REQ-008 | capturé |
| T16 | REQ-010 | capturé |
| T17 | UI-007 | capturé |
| T18 | UI-007, REQ-010, D-05 | capturé (Q-002 répondue) |
| T19 | UI-007, REQ-010 | capturé |

### Points de la source non résolus

Aucun : les quatre questions sont répondues (11.10.2026).

## 13. Revue d'architecture

Trois revues indépendantes (`architecture-reviewer`, 11.10.2026), une par volet. Verdict d'ensemble : **APPROUVER AVEC RÉSERVES**.

### 13.1 Charges (#35, #36, #37)

**Modules concernés** : `calc/registry.py:22,99-121` (un `ENGINE`/`SHEET_PREFIX` par domaine, instances préfixées du classeur), `calc/validation.py:25,350-364` (toute instance non-`norm` exige `workbook` et `sheet`), `schemas/calculations.schema.json:13` (`const "1.4"`), `calc/domains/snow.py`, `wind.py` (`_local_force`, `_envelope` l.162-178), `dead_load.py` (`MaterialLibrary`, `_layer_table` l.239, `_check_chosen` l.287, `read_instance` l.307-372), `calc/norms/sia261.py:190-205` (Anhang A déjà transcrit : `table_28/29/30`), `calc/project.py:102` (`SOURCE_FOLDERS`), `calc/tools/woodcore_gui.py:2040-2044` (`tab_ac_selfweight`, `tab_ac_superimposed`, `tab_ac_snow`, `tab_ac_wind` sont des `FutureTab`), `calc/tools/member_check_tab.py:503-760`.

**À réutiliser** : `sia261.table_28/29/30` (ne pas recopier) ; `dead_load` découpé en `build_instance(layers, chosen, source_ref)` appelé par les deux chemins ; `wind._local_force`/`_envelope` partagés ; le patron de source de `member_check` (`check_source`, `read_source`, `new_source`, `ID_PATTERN`) ; `grouped_list`, `source_archive`, `cards` ; un `dead_load_svg.py` sans Qt calqué sur `connector_svg.py`/`schema_svg.py` avec `figure_style` et `theme.json` ; `show-calc` générique.

**Risques** :
- **ARCH-RISK-001 (bloquant)** — un domaine ne sait aujourd'hui porter qu'un moteur et des instances de classeur. Correctif : `calculations` **1.5** additif, `engine` et `source_file` par instance (`workbook`/`sheet` requis pour `excel` seulement), 1.4 toujours lu ; `build_calculations` reçoit les sources du projet ; un id pris par une feuille et une source est refusé en nommant les deux fichiers ; l'avertissement « no sheet named SL… » et l'arrêt « classeur disparu » ne valent plus qu'en l'absence de sources ; ordre déterministe (feuilles, puis sources dans l'ordre de `list_order`). Suivent `variable_sources.py:70`, `build_reference.py:1120,1211`, `shown_variables.py:91`.
- **ARCH-RISK-002 (important)** — trois sources nouvelles `dead-load-source`, `snow-source`, `wind-source` 1.0 (`additionalProperties: false`), validées avant écriture ; dossiers dans `SOURCE_FOLDERS` (archive, partage, migration les suivent).
- **ARCH-RISK-003 (important)** — la bibliothèque de l'Excel n'est pas une norme : `calc/libraries/materials-library.json` (chaque entrée avec `ebene`, `material`, `mass`, `unit`, `quelle`), lue et contrôlée ; les poids de la SIA 261 restent dans `norms/`, référencés ; les ajouts de l'ingénieur dans `Woodcore-Datei/materials.json` (schéma versionné) ; précédence projet > norme > Excel, la logique d'ambiguïté de `MaterialLibrary` réutilisée. Noms : la donnée garde son nom allemand ; seules les entrées de la norme ont fr/de/en.
- **ARCH-RISK-004 (important)** — vent : ~40 figures ; un fichier `norms/sia261-2020-figNN-*.json` par figure (`edition`, `page`), un lecteur `sia261_wind.py` qui contrôle la structure ; figures 31–45, 59a/b comparées à l'Excel comme oracle de transcription ; le test vérifie aussi la complétude contre la liste des figures de la norme.
- **ARCH-RISK-005 (important)** — le dessin de la composition est fait une fois en Python (SVG) et imprimé tel quel ; couleurs et hachures en jetons de `theme.json` ; une commande Typst nouvelle pour l'imprimer apporte `///`, deux exemples, `commands.json`, `shown-variables.json`.
- **ARCH-RISK-006 (important)** — la fenêtre a deux onglets « Poids propre » et « Surcharge » (choix de l'ingénieur du 08.10) ; T4 en demande un → **question à l'approbation**.
- **ARCH-RISK-007 (mineur)** — extraire une base `SourceTab` (liste groupée, archive, enregistrement, aperçu) dont héritent `MemberCheckTab` et les onglets de charges.
- **ARCH-RISK-008 (mineur)** — décision §13 écrite dès l'étape d'infrastructure.
- **ARCH-RISK-009 (mineur)** — le chemin Python lit la norme, jamais les `Dropdowns` de l'Excel (`wind.py` `TERRAIN_TABLE`).

### 13.2 Vérifications (#38)

**Modules concernés** : `calc/domains/member_check.py:40-41` (`KINDS` a déjà `shear`, `buckling`, `lateral-torsional` ; `IMPLEMENTED` testé à 5 endroits), `resolve` l.266-380, `draft_typst` l.395-442, `_compute`/`_compute_bending` l.501-731 ; `calc/shown_variables.py:47` `check_command` ; `lib/timber.typ` (`verify-compression` l.695, `timber-kc` l.586, `timber-km` l.617, `verify-bending(-normal)`, `verify-shear` l.1179, `show-check-member` l.1414) ; `calc/norms/sia265.py:1047` `buckling()`, `:1052` `lateral_buckling()` ; schémas `member-check-source`/`checks` ; `member_check_tab.py` (`SOON`, `CompressionTab`, `BendingTab`).

**Risques** :
- **ARCH-RISK-101 (important)** — le choix de commande est écrit quatre fois (Python, `draft_typst`, Typst, test) : un seul `shown_variables.check_command` appelé partout côté Python ; le test compare au domaine présent dans le registre compilé.
- **ARCH-RISK-102** — `buckling` reste un genre à part (`verify-compression(stability: true)`), `compression` reste la section seule ; pas de drapeau `stability` dans la source.
- **ARCH-RISK-103 (important)** — déversement avec effort normal : (37) en compression exige les longueurs de flambement → **question à l'approbation**.
- **ARCH-RISK-104 (important)** — 1.5 (rectangle) et 4/3 (rond) du cisaillement sont en dur dans Typst : les porter dans `calc/norms/` (le 4/3 marqué « mécanique ») et lus des deux côtés ; la torsion (série de Saint-Venant, Typst seul) reste hors périmètre, `shear` appelle `verify-shear` sans `T`.
- **ARCH-RISK-105 (important)** — `verify-shear` n'a ni `shown:` ni −1 et n'est pas dans `shown-variables.json` : à ajouter, avec `///`, exemples, `commands.json`.
- **ARCH-RISK-106 (important)** — `IMPLEMENTED` dispersé (5 fonctions, 3 tests, `///` de `show-check-member`) : tout dans le même pas.
- **ARCH-RISK-107 (mineur)** — `_compute_buckling`, `_compute_lateral`, `_compute_shear` ; extraire `_bending_values` de `_compute_bending` au lieu de le copier.
- **ARCH-RISK-108 (mineur)** — champs additifs (`l_k_y`, `l_k_z`, `l`, `beta_y`, `beta_z`, `a`, `sigma_m_crit`, `V_z`, `V_y`, `pith`), `schema_version` 1.0 inchangé, ajoutés au record pour leur genre seulement (exports antérieurs identiques à l'octet). `N` devient facultatif pour `shear` (relâchement : tout fichier valide le reste).
- **ARCH-RISK-109 (mineur)** — mots fr/de/en dans `STRINGS`, clés `mc_what_*` des trois onglets retirées ; l'onglet français existant s'appelle « Flambage » : il garde ce nom.

### 13.3 Résultat toujours affiché (#39)

**Modules concernés** : `lib/shown-variables.json` (`keys`, `parts`), `lib/calc-engine.typ:52-93` (`check-shown` refuse déjà un niveau hors 1..3, donc `(sigma_t_0_d: 0)` panique ; `level-plan`, `plan-at` rendent 0 à une clé non choisie), `lib/timber.typ:228-238` (le verdict est déjà toujours imprimé), `:526` (la ligne de contrainte disparaît), `calc/tools/display_view.py:120-250` `LevelControl`, `member_check_tab.py:925,1176-1183,1227`, `member_check.shown_keys` l.472.

**Risques** :
- **ARCH-RISK-201 (important)** — une liste `"results"` par commande dans `lib/shown-variables.json`, lue par Typst et par `shown_variables.results()` ; test : `results ⊂ keys`.
- **ARCH-RISK-202** — résultats : tension `sigma_t_0_d`, `sigma_t_90_d`, `sigma_t_alpha_d` ; compression `sigma_c_0_d` ; compression-perp `sigma_c_90_d`, `sigma_c_alpha_d` ; bending `sigma_m_y_d`, `sigma_m_z_d`, `sigma_m_90_d`, `sigma_m_alpha_d` ; bending-normal ses contraintes ; shear `tau_d`. Les résistances `f_*_d` ne sont pas verrouillées (le rapport σ/f est le verdict, déjà toujours imprimé).
- **ARCH-RISK-203** — une clé de résultat absente de `shown:` est imprimée au niveau 1 ; un 0 écrit à la main est refusé (c'est déjà le cas), le message nomme le résultat.
- **ARCH-RISK-204** — des états de fenêtre enregistrés sans le résultat sont relus avec le résultat forcé à ≥ 1.
- **ARCH-RISK-205 (important)** — connecteurs et moment polaire : leurs clés viennent de l'export, aucune liste statique ; D-12 y reste (périmètre : les vérifications de membrure, dont l'issue donne l'exemple σt,0,d / ft,0,d).
- **ARCH-RISK-206 (important, bug trouvé)** — `LevelControl.set_keys` (`display_view.py:159-198`) vide `wanted` puis ne reconstruit que les clés de la nouvelle liste : un brouillon un instant non calculable, ou un changement d'α, de section ou de M_z, efface la sélection manuelle sans retour. C'est la cause probable de « ne se règle pas correctement » : garder les clés absentes dans `wanted`, ne pas reconstruire si la liste est la même.
- **ARCH-RISK-207..210 (mineurs)** — infobulle `ds_shown_locked` en trois langues ; grisé tiré de `theme.json` ; un seul chemin de ligne `_row(locked=)` ; `///` des `verify-*` et `commands.json` disent la règle.

## 14. Plan d'implémentation

Ordre : du plus petit au plus gros, chaque étape testée avant la suivante ; §16 mis à jour après chacune.

1. **#39 — résultat verrouillé** (REQ-010, UI-007, D-05). `lib/shown-variables.json` (`results`), `calc/shown_variables.py` (`results()`), `lib/calc-engine.typ` (`level-plan(…, results:)`, message de refus), les cinq `verify-*` de `lib/timber.typ` passent `results:` ; `calc/tools/display_view.py` `LevelControl.set_keys(keys, locked=)` (case cochée désactivée, boîte 1–3, `picked()` les inclut) et correction de la perte d'état (RISK-206) ; `member_check.locked_keys(record)` ; `member_check_tab.py`. Mot `ds_shown_locked`. Tests : `test_timber.py`, `test_display_view.py`, `test_member_check_tab.py`. Décision §13 renversant D-12 pour les vérifications.
2. **#38 — socle** (RISK-101, 104, 105). Un `check_command` unique ; facteurs de cisaillement dans `calc/norms/sia265-*` lus par Typst et Python ; `verify-shear(shown:, level: -1)` et son entrée JSON, `///`, exemples, `commands.json`.
3. **#38 — flambement, effort tranchant, déversement** (REQ-007/008/009). `member_check.py` (`IMPLEMENTED`, `check_source`, `resolve`, `_compute_buckling`, `_compute_shear`, `_compute_lateral`, `_bending_values`, `draft_typst`), schémas additifs, `validation.validate_checks_business`, `show-check-member` et son `///`. Tests : `test_member_check.py` (égalité Python/Typst à 1e-6, branches, η_w,E, oracles, cas Excel classe 1), `test_timber.py`.
4. **#38 — onglets** (UI-006). `BucklingTab`, `ShearTab`, `LateralTab` dans `member_check_tab.py`, enregistrés dans `woodcore_gui.py` ; `test_member_check_tab.py` (3 `SoonTab` restants, η instantané = export).
5. **Charges — infrastructure** (ARCH-003/004, RISK-001/002/007/008). `calculations` 1.5 (`engine`, `source_file` par instance), `validation.py`, `registry.build_calculations` avec les sources du projet et refus des ids doublons, avertissements adaptés, `project.SOURCE_FOLDERS` (`loads/dead`, `loads/snow`, `loads/wind`), base `SourceTab` extraite de `MemberCheckTab`. Décision §13 (D-04). Tests : `test_calculations_mixed.py`, `projet-exemple` exporté à l'identique.
6. **Poids propre et surcharge** (REQ-001/002, UI-001/002/003, D-07). `dead_load.build_instance` partagé ; `calc/libraries/materials-library.json` + lecteur ; `Woodcore-Datei/materials.json` ; schéma `dead-load-source` 1.0 ; `dead_load_svg.py` (coupe, hachures de `theme.json`, cotes hauteur/largeur/entraxe) ; impression du dessin dans le rapport (par la table de l'instance si elle peut porter une figure, sinon commande `show-dead-load` documentée) ; onglet. Tests : `test_dead_load_source.py`, `test_dead_load.py`, `test_materials.py`, `test_dead_load_svg.py`, `test_dead_load_tab.py`.
7. **Neige** (REQ-003/004, UI-004). `calc/norms/sia261-2020-*` (fig. 2, 3, 4, annexe D, C_e, lus page par page dans `SIA261-2020-FR.pdf` et vérifiés sur la DE) ; `snow_calc.py` (les cinq modèles, toit à un pan, > 60°, glissement empêché partout, toiture cylindrique μ₃) ; schéma `snow-source` ; onglet avec croquis de la disposition. Tests : `test_snow_source.py`, `test_snow_tab.py`.
8. **Vent** (REQ-005/006, UI-005, D-06). `sia261_wind.py` + un JSON par figure (lot 1 : figures de l'Excel, comparées à l'Excel ; lot 2 : les autres figures de bâtiment) ; q_p, c_h, c_red calculé, c_d, forces globales, enveloppe locale partagée avec `wind.py` ; schéma `wind-source` ; onglet. Tests : `test_wind_source.py` (un cas par figure, complétude), `test_wind_tab.py`, `test_norms.py`.
9. **Documentation et fin** : `docs/domain/loads.md`, `member-checks.md`, `calculation-domains.md`, `docs/ui/window.md`, `docs/typst/report-engine.md`, `docs/decisions.md`, `docs/open-questions.md`, `CHANGELOG.md`, « Nouveautés » fr/de/en ; suite complète ; vérification indépendante ; `finish`.

## 15. Vérification

Vérificateur indépendant (`requirements-verifier`, Sonnet), deux passes le 11.10.2026, arbre de travail contre HEAD 6634cd8. Première passe : 13 ✅, 9 ⚠️, 0 ❌ ; les ⚠️ levés (oracles Excel recalculés, Bemessungsbeispiele p. 114, tests d'import sans Qt et de schémas, documentation nuancée), seconde passe : tout ✅.

| Élément | Verdict | Preuve |
|---|---|---|
| REQ-001 | ✅ | `test_dead_load_source.test_a_flat_roof_gives_what_the_workbooks_flachdach_sheet_gives` (feuille «Flachdach» recalculée par Excel : g_k 0.397, a_k 0.407, 0.804 kN/m², à 1e-9) ; refus de la valeur choisie, fichier et champ nommés |
| REQ-002 | ✅ | `test_dead_load_source` (g_k → a_k), `test_load_tab` (bascule dans l'onglet, `calculations.json` relu) |
| REQ-003 | ✅ | `test_snow_source` : cinq modèles recalculés à la main, μ ≥ 0.8 sur les deux demi-pans, figure 4, pente > 60° |
| REQ-004 | ✅ | `test_snow_source` : toiture cylindrique, μ₃, deux modèles ; fichier de norme avec édition et pages |
| REQ-005 | ✅ | `test_wind_source.test_the_forces_and_the_local_pressures_are_the_workbooks` (figure 33 recalculée par Excel : q_p, six forces, enveloppes locales ouverture A, à 1e-12) ; c_h, c_red |
| REQ-006 | ✅ | `test_wind_source` : 37 tableaux, un cas par figure |
| REQ-007 | ✅ | `test_member_check` : Python = Typst à 1e-6 (classes 1, 2, 3, massif et BSH, λ_rel des deux côtés de 0.3, η_w,E) ; classeur *Stützen* recalculé reproduit à E_0,05 près (écart D-02 documenté) |
| REQ-008 | ✅ | `test_member_check` : trois branches de k_m, section ronde refusée, (37) du classeur reproduit à E_0,05 près |
| REQ-009 | ✅ | `test_member_check.test_a_shear_reproduces_the_bemessungsbeispiele` (τ_d 0.88, f_v,d 1.8) ; Python = Typst |
| REQ-010 | ✅ | `test_timber.test_a_result_is_always_printed_at_minus_one_and_never_left_out` : six commandes, `shown: (:)` imprime le résultat, 0 refusé |
| UI-001 | ✅ | `test_load_tab` (onglet, couches, enregistrement, export) |
| UI-002 | ✅ | `test_dead_load_source` (dessin, une bande par couche ; `show-calc` au niveau 2) |
| UI-003 | ✅ | `test_dead_load_source` (cotes de hauteur, largeur et entraxe dans le SVG) |
| UI-004 | ✅ | `test_load_tab` : toiture cylindrique, toit plat, toit à deux pans (q_k,11, q_k,12) |
| UI-005 | ✅ | `test_load_tab` : 37 tableaux, q_p et forces, enregistrement |
| UI-006 | ✅ | `test_member_check_tab` : trois onglets, résultat instantané = export |
| UI-007 | ✅ | `test_member_check_tab`, `test_display_view` : case cochée, grisée, niveaux 1–3, infobulle fr/de/en |
| ARCH-001 | ✅ | `test_dead_load_source.test_the_load_modules_import_without_qt` |
| ARCH-002 | ✅ | `test_norms` : fichiers `sia261-2020-*` avec édition et page, lecteurs déclarés |
| ARCH-003 | ✅ | `test_dead_load_source.test_each_load_source_is_its_schemas_and_versioned` ; `calculations` 1.5, 1.4 lu |
| ARCH-004 | ✅ | `docs/decisions.md` (7 entrées) ; id en double refusé ; projet exemple exporté |
| CON-001 à CON-006 | ✅ | η_w,E appliqué ; `test_i18n` vert ; `verify-shear` dans `shown-variables.json` ; tests sur `tests/projet-exemple/` |
| Documentation | ✅ | `loads.md`, `member-checks.md`, `calculation-domains.md`, `window.md`, `report-engine.md`, `layout.md`, `testing.md`, `decisions.md` (anciennes décisions annotées), `open-questions.md`, `CHANGELOG.md`, «Nouveautés» fr/de/en, `///` et `commands.json` (`test_commands` vert) |
| §8 hors périmètre | ✅ | ni combinaisons, ni séisme, torsion, déformation, vibration, ni lien charge–position |

## 16. Journal d'avancement

| Date | Statut | Fait / reste |
|---|---|---|
| 2026-10-10 | draft | spécification extraite des issues #35–#39 ; Excel Belastungsannahmen, Stabilität Stützen, Ausklinkung inventoriés ; SIA 261:2020 fig. 3 lue ; 4 questions ouvertes |
| 2026-10-11 | specified | Q-001 à Q-004 répondues → D-04 à D-07 ; reste : revue d'architecture et plan |
| 2026-10-11 | reviewed | trois revues (APPROUVER AVEC RÉSERVES), §13 et plan §14 en 9 étapes ; reste : l'approbation (onglet unique ou deux, déversement avec N) |
| 2026-10-11 | approved | approuvé par l'ingénieur ; D-08 (un onglet), D-09 (déversement avec N complet, (37)) ; reste : étapes 1 à 9 |
| 2026-10-11 | implementation | étape 1 faite (REQ-010, UI-007) : `results` dans `lib/shown-variables.json`, `shown-results`/`level-plan(results:)`/`check-shown(results:)` dans `calc-engine.typ`, les cinq `verify-*` et `show-check-member` ; `shown_variables.results`, `member_check.locked_keys` ; `LevelControl.set_keys(locked=)` (case cochée grisée, niveaux 1–3) et sélection conservée (RISK-206) ; `ds_shown_locked` fr/de/en ; tests `test_timber` (46 ✔), `test_member_check_tab` (39 ✔). Docs et décision à l'étape 9. Reste : étapes 2 à 9 |
| 2026-10-11 | implementation | étapes 2 et 3 faites (REQ-007/008/009) : `IMPLEMENTED` + `shear`, `buckling`, `lateral-torsional` ; source (champs additifs `l_y`, `l_z`, `beta_y`, `beta_z`, `a`, `sigma_m_crit`, `V_z`, `V_y`, `pith` ; N facultatif pour `shear`), `resolve`, `draft_typst`, `_compute_shear/_buckling/_lateral`, `_bending_values` extrait ; un seul `shown_variables.check_command` ; `show-check-member` étendu ; `verify-shear(shown:, level: -1)` ; schémas `member-check-source`/`checks` additifs (1.0) ; `validate_checks_business`. **Constat norme** : SIA 265 (23) est τ_d ⩽ f_v,d sans facteur — 1.5 (rectangle) et 4/3 (cercle) sont de la mécanique : `SHEAR_FACTORS` dans `member_check.py`, tenu égal à Typst par un test, pas dans `calc/norms/` ; la note imprimée qui attribuait 1.5 à (23) est corrigée fr/de/en. **D-10** (choix de forme) : les longueurs de flambement sont `l_y`, `l_z` (longueurs du système) et `beta_y`, `beta_z`, l_k = β·l. Tests : `test_member_check` 76 ✔ (égalité Python/Typst 1e-6 sur 16 nouveaux cas, trois branches de k_m), `test_timber` 46 ✔. Reste : étapes 4 à 9 |
| 2026-10-11 | implementation | étape 4 faite (UI-006) : `BucklingTab` (KN-), `LateralTab` (KI-), `ShearTab` (SC-) sur `MemberCheckTab`, carte partagée `BucklingLengths` (D-09), `SoonTab` réduits à trois ; mots fr/de/en ; exemples KN-01, KI-01, KI-02, SC-01 dans `tests/projet-exemple` et son `data/checks.json` régénéré ; traduction de `show-check-member`. Tests liés : 1533 ✔, reste `test_commands.test_a_level_0_pins_no_page` (pages d'exemple de `verify-shear` à régénérer, étape 9). Note : `engine.write_json` écrit en CRLF sous Windows — tâche séparée proposée. Reste : étapes 5 à 9 |
| 2026-10-11 | implementation | étapes 5 et 6 faites (ARCH-003/004, REQ-001/002, UI-001/002/003, D-04, D-07, D-08) : `calculations` 1.5 (`engine`, `source_file`, `figures` par instance ; 1.4 lu), `registry.build_calculations(workbooks, here, files)` avec `SOURCE_MODULES`, refus d'un id feuille + source, `registry.export`/`write_files` (`data/calculations/*.svg`, LF), `project.SOURCE_FOLDERS` + `loads`, `validation` ; `show-calc` imprime les `figures` (clé `figure-N` à −1) ; `dead_load.instance_from_layers` partagé ; `materials.py` (SIA 261 tab. 28/29, `calc/libraries/materials-library.json` 236 entrées, `Woodcore-Datei/materials.json`) ; `dead_load_source.py`, `dead_load_svg.py` ; schémas `dead-load-source`, `materials` ; onglet `load_tab.DeadLoadTab` (« Poids propre et surcharge » remplace les deux onglets) ; note du tableau fr/de/en. **Constat Excel** : la bibliothèque 3.2 donne « Fassade / Glas » 5000 kg/m³ (SIA 261 : 25 kN/m³) et « Scobalit » 0 kg/m³ (refusé à l'usage). **Écart au plan** : pas d'extraction d'une base `SourceTab` hors de `MemberCheckTab` (refonte risquée d'un onglet stable de 1700 lignes) ; `LoadTab` réutilise les mêmes composants (`grouped_list`, `source_archive`, `identity`, `cards`, `display_view`). Tests : `test_dead_load_source` 8 ✔, `test_load_tab` 1 ✔, `test_action_tabs` 4 ✔, `test_dead_load` 10 ✔. Reste : étapes 7 à 9 |
| 2026-10-11 | implementation | étape 7 faite (REQ-003/004, UI-004, D-01) : `calc/norms/sia261-2020-5.2-schnee.json` (5.1.4, 5.2.2–5.2.6, 5.3.1–5.3.5, figures 2–4 lues sur rendu, annexe D ; pp. 26–29, 115) et son lecteur `sia261_snow.py` ; `snow_source.py` (toit plat + figure 4, à un pan 5.3.2, deux pans, sheds μ₂m, toiture courbe μ₃ — 3e colonne de la figure 3 confirmée sur le rendu de la p. 28 : demi-cercle, α₀ = 60°, μ₃ = min(0.2 + 0.09 α ; 2.0)) ; μ₁ = 0.8 si glissement empêché avant la demi-charge (écart Excel N37/N38) ; refus au-dessus de 2000 m ; `snow_svg.py` (croquis sans mots) ; schéma `snow-source` ; onglet `SnowTab` ; termes fr/en. **Constat** : `domains/snow.py` (lecture Excel) cite 5.3.6 pour le glissement et 5.3.5 pour les décrochements — numéros de l'ancienne édition ; SIA 261:2020 : 5.3.4 et 5.3.6. Tests : `test_snow_source` 7 ✔, `test_load_tab` 2 ✔, `test_norms` 80 ✔. Reste : étapes 8 et 9 |
| 2026-10-11 | implementation | étape 8 faite (REQ-005/006, UI-005, D-06) : 37 tableaux de l'annexe C (31–56, 57a–d, 58, 59a/b, 60a/b, 63, 64 ; ponts, cylindres, parois, passerelle, profilés exclus) transcrits de la couche texte de SIA261-2020-FR.pdf pp. 82–105 par un script qui compte les colonnes, contrôlés sur rendu des pages, un fichier `calc/norms/sia261-2020-tabNN-wind[-x].json` chacun (facteurs de surface de c_f2 « 0,96·d·h » relevés sur rendu) ; `sia261-2020-6.2-wind.json` (tableau 4, éq. 11–12, c_red de la figure 9 lu sur les **tracés vectoriels** du PDF, c_d 6.3.5) ; lecteur `sia261_wind.py` ; `wind_source.py` (q_p, c_red calculé, forces globales par surface de référence, pressions locales extérieures, nettes par ouverture ou par surface ; « * » nommé, non calculé) ; schéma `wind-source` ; onglet `WindTab` ; modèles de glossaire fr/en. **Oracle** : la feuille « Wind Tabellen Werte » de l'Excel 3.2 figée dans `tests/fixtures/wind-tables-reference.json` ; plus de 1000 valeurs concordent ; **5 erreurs de l'Excel** (35 0° c_pi D, 39 90° c_pe C, 40 90° c_pe F, 41 180° c_pi A, 42 0° c_pe F) et directions mal libellées (40, 42, 43), vérifiées sur rendu. Tests : `test_wind_source` 7 ✔, `test_load_tab` 3 ✔, `test_norms` 80 ✔. Reste : étape 9 |
| 2026-10-11 | testing | étape 9 faite : `docs/domain/loads.md` (§3.3bis, §3.3ter, §3.3quater), `member-checks.md` (§3.3unvicies), `calculation-domains.md` (§3.3), `docs/typst/report-engine.md` (§4), `docs/ui/window.md`, `docs/architecture/layout.md`, `docs/conventions/testing.md`, `docs/decisions.md` (§13 : sept entrées), `docs/open-questions.md` (§14), `CHANGELOG.md`, « Nouveautés » 0.117 fr/de/en ; `///` des `verify-*`, `show-check-member`, `verify-shear`, `show-calc` et `commands.json` ; exemples régénérés et instantané figé (`build_examples --freeze`, 417 exemples). **Bug trouvé** : le champ `figures` d'une instance de connecteur est un dictionnaire — `show-calc` et `shown_variables` ne lisent plus que les listes. `build_examples` et `engine.write_json` écrivent en CRLF sous Windows (fichiers remis en LF ; tâche séparée proposée). Reste : suite complète, vérification indépendante, `finish` |
| 2026-10-11 | completed | vérification en deux passes, tout ✅ (§15) ; trois échecs de la suite complète réparés (i18n, vues, garde lecture seule de `load_tab`) ; oracles ajoutés : Excel «Flachdach», «Wind» fig. 33, *Stützen*, Bemessungsbeispiele p. 114 ; spec déplacée dans `completed/` |
