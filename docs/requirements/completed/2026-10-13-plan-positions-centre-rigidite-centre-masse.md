---
id: 2026-10-13-plan-positions-centre-rigidite-centre-masse
titre: Plan de positions — centre de rigidité S et centre de masse M
status: completed
cree: 2026-10-13
mis_a_jour: 2026-10-14
source: issue GitHub #54 «Plan de positions — centre de rigidité et centre de masse» (corps du 2026-10-13, aucun commentaire)
docs: [docs/domain/position-plans.md, docs/ui/tab-plans.md, docs/architecture/principles.md, docs/architecture/data-contracts.md, docs/domain/positions.md, docs/domain/fire-plans.md, docs/typst/api-conventions.md]
---

# Plan de positions — centre de rigidité S et centre de masse M — Spécification

## 1. Objectif

Sur un plan de positions, Woodcore calcule le **centre de rigidité S** de l'étage à partir des parois de contreventement qui y sont dessinées (H et W), et le **centre de masse M** comme centre géométrique d'un contour du bâtiment que l'ingénieur dessine avec un nouvel outil. Les deux points et le contour sont dessinés dans la fenêtre, et sur le plan imprimé dans le rapport quand l'ingénieur le demande par une case du plan. Pour cela chaque paroi reçoit, sur le plan, son mode de construction (ossature bois, CLT, béton), dont dépend la rigidité prise pour elle : sa longueur à une puissance. But : voir d'un coup d'œil si le contreventement est disposé de façon symétrique (S proche de M), sans calcul à la main.

## 2. Source

La demande telle qu'elle a été donnée, **mot pour mot** (issue #54, corps du 2026-10-13), découpée en points. L'annexe de l'issue (T15) est reproduite telle quelle à la fin de ce fichier, en **Annexe A** ; ses sections sont citées «A§n».

> **T1** — « Onglet «Plan de positions» (`docs/ui/tab-plans.md` §10quater, `docs/domain/position-plans.md` §3.3sexies). Demande de Gian du 2026-10-12 : calculer et dessiner le centre de rigidité S et le centre de masse M sur le plan de positions. »
>
> **T2** — « La méthode de calcul de S est celle du document «Centre de rigidité d'un étage — calcul mécanique général» (12.10.2026), reproduit tel quel en annexe. »
>
> **T3** — « Suite de #18 (même onglet ; #4, #9 et #18 sont fermées). »
>
> **T4** — « Périmètre : S et M seulement. L'excentricité entre M et S, les excentricités de dimensionnement (SIA 261:2020, chiffre 16.5.2.7) et la répartition des efforts sur les parois (sections 6 à 8 du document) ne font pas partie de cette demande. »
>
> **T5** — « Calculer le centre de rigidité S d'un plan à partir des parois qui y sont dessinées, selon la méthode du document en annexe (sections 5 et 9 : barycentre des rigidités, cas général des parois inclinées). »
>
> **T6** — « Prendre en compte comme parois les éléments H (parois de contreventement) et W (parois porteuses et de contreventement) ; les éléments V et B «wand» ne comptent pas. »
>
> **T7** — « Donner à chaque mur dessiné son mode de construction sur le plan : ossature bois, CLT ou béton. »
>
> **T8** — « ⚠️ Contredit la règle actuelle «le plan ne porte ni matériau, ni section, ni charge» (`docs/domain/position-plans.md` §3.3sexies) : changement d'architecture décidé par Gian, à justifier dans `docs/decisions.md`. »
>
> **T9** — « Ne calculer le centre de rigidité que si toutes les parois prises en compte ont le même mode de construction (par exemple uniquement de l'ossature bois). »
>
> **T10** — « Prendre pour rigidité d'une paroi sa longueur élevée à une puissance qui dépend du mode de construction : ossature bois, longueur puissance 1 (linéaire) ; CLT, longueur puissance 1,5 ou 2 ; béton, longueur puissance 3. »
>
> **T11** — « Pour le CLT, c'est l'ingénieur qui choisit entre 1,5 et 2 dans Woodcore. »
>
> **T12** — « Ajouter un outil pour dessiner le contour du bâtiment (un polygone) sur le plan. »
>
> **T13** — « Calculer le centre de masse M comme le centre géométrique du contour dessiné, et le dessiner sur le plan. »
>
> **T14** — « Dessiner S, M et le contour dans la fenêtre ; une case à cocher sur le plan, enregistrée avec lui, décide s'ils apparaissent aussi sur le plan imprimé dans le rapport. »
>
> **T15** — Annexe de l'issue : le document «Centre de rigidité d'un étage — calcul mécanique général (12.10.2026)», treize sections — voir **Annexe A**.

## 3. Exigences fonctionnelles

### REQ-001 — Mode de construction d'une paroi
- **Exigence** : Woodcore doit permettre de donner à une paroi dessinée sur un plan de positions son mode de construction — ossature bois, CLT ou béton —, enregistré avec l'élément dans le fichier du plan (`Woodcore-Datei/plans/<id>.json`). Le champ est porté par les parois H et W (D-011) ; il est absent tant qu'il n'a pas été donné : aucun mode par défaut (D-016).
- **Source** : T7, T8
- **Priorité** : doit
- **Critère d'acceptation** : une paroi W mise en «CLT», le plan enregistré puis rouvert : le fichier porte le mode sur cet élément et le volet de droite le montre ; un mode inconnu, ou un mode sur un élément qui ne le porte pas (un poteau S, une poutre T), fait refuser le fichier par `plan.check_source` avec le nom du fichier et de l'élément.

### REQ-002 — Parois prises en compte
- **Exigence** : Woodcore doit calculer S à partir des éléments **H** et **W** du plan, et d'eux seuls : un élément V, un B «wand» et tout autre élément ne comptent pas.
- **Source** : T6
- **Priorité** : doit
- **Critère d'acceptation** : sur un plan dont S est calculé, ajouter un V, un B «wand», une poutre T ou un poteau S ne déplace pas S (test du domaine) ; ajouter un H le déplace.

### REQ-003 — Une paroi est un tronçon droit
- **Exigence** : Woodcore doit prendre chaque tronçon droit d'un élément H ou W comme une paroi : sa longueur, son angle, et un point de sa ligne d'action (son milieu). Une paroi qui tourne un coin compte donc pour autant de parois qu'elle a de tronçons ; des tronçons successifs **alignés** du même élément (un point intermédiaire posé sur une paroi droite) comptent pour une seule paroi, de la longueur totale. Deux éléments distincts restent deux parois, même bout à bout.
- **Source** : T5, A§2 hypothèse 3 («Une paroi ne reprend des efforts que dans son propre plan»), A§9, A§12 (parois en L ou en U) — *déduit du document, D-009*
- **Priorité** : doit
- **Critère d'acceptation** : une paroi en L de deux tronçons donne les deux mêmes parois que deux éléments droits ; une paroi droite dessinée en trois points alignés donne, en béton (puissance 3), le même S que la même paroi dessinée en deux points.

### REQ-004 — Rigidité d'une paroi
- **Exigence** : Woodcore doit prendre pour rigidité d'une paroi sa longueur `l` élevée à une puissance `n` qui dépend du mode de construction : ossature bois `n = 1` ; CLT `n = 1,5` ou `n = 2` ; béton `n = 3`. Seul le rapport des rigidités fixe S (A§4) : la longueur est prise dans les unités du plan, et S se calcule aussi sur un plan **sans échelle**.
- **Source** : T10, A§4
- **Priorité** : doit
- **Critère d'acceptation** : sur un plan de 12 × 8 avec quatre parois — verticales en x = 0 (longueur 1) et x = 12 (longueur 3), horizontales en y = 0 et y = 8 (longueur 2 chacune) —, S vaut (9,0 ; 4,0) en ossature bois, (10,8 ; 4,0) en CLT puissance 2, (10,063 ; 4,0) en CLT puissance 1,5 et (11,571 ; 4,0) en béton ; le même plan avec et sans échelle donne le même S.

### REQ-005 — Choix de la puissance du CLT
- **Exigence** : Woodcore doit laisser l'ingénieur choisir, pour le CLT, entre les puissances 1,5 et 2, et enregistrer ce choix **avec le plan** (D-015). Tant que le choix n'est pas fait sur un plan dont les parois sont en CLT, S n'est pas calculé et Woodcore le dit.
- **Source** : T11
- **Priorité** : doit
- **Critère d'acceptation** : sur un plan en CLT, passer de 1,5 à 2 déplace S comme au critère de REQ-004, le choix est retrouvé après enregistrement et réouverture, et une valeur autre que 1,5 ou 2 dans le fichier le fait refuser.

### REQ-006 — Un seul mode de construction par calcul
- **Exigence** : Woodcore ne doit calculer S que si toutes les parois prises en compte (REQ-002) ont le même mode de construction. Sinon S n'est ni calculé ni dessiné, et la fenêtre dit pourquoi : les modes trouvés, et les parois H ou W qui n'ont pas de mode — une seule paroi sans mode suffit à ne pas calculer S (D-016).
- **Source** : T9
- **Priorité** : doit
- **Critère d'acceptation** : un plan avec trois parois en ossature bois et une en béton : pas de S, et la raison nomme les deux modes ; la paroi en béton passée en ossature bois : S apparaît ; une des quatre parois sans mode : pas de S, et la raison nomme son numéro.

### REQ-007 — Calcul du centre de rigidité S
- **Exigence** : Woodcore doit calculer S par la méthode du document, cas général des parois inclinées (A§9) : `K_xx`, `K_yy`, `K_xy`, `K_xθ`, `K_yθ`, `D = K_xx·K_yy − K_xy²`, `x_S = (K_xx·K_yθ − K_xy·K_xθ) / D`, `y_S = (K_xy·K_yθ − K_yy·K_xθ) / D`, qui se réduit au barycentre des rigidités (A§5) pour des parois parallèles aux axes. S n'est enregistré nulle part : il est recalculé du dessin à chaque affichage et à chaque export.
- **Source** : T5, T2, A§5, A§9, A§11
- **Priorité** : doit
- **Critère d'acceptation** : (a) les quatre parois de l'exemple A§10 (rigidités 10, 30, 20, 20) donnent S = (9,0 ; 4,0) ; (b) tout le plan tourné de 30° autour de l'origine : S tourne de 30° et reste à la même distance de l'origine (le contrôle du document, A§11) ; (c) le plan retourné (y vers le bas, le repère de la feuille) donne le S retourné ; (d) un plan de parois inclinées donne le même S que le code de référence A§11.

### REQ-008 — Cas où S n'existe pas
- **Exigence** : Woodcore ne doit pas dessiner S, et doit en dire la raison, quand le plan n'a aucune paroi H ou W, ou quand toutes ses parois ont la même direction (`D` nul : «il faut des parois dans au moins deux directions», A§5, A§11). Quand les lignes d'action de toutes les parois passent par un même point, S est ce point et Woodcore doit signaler que l'étage n'a alors aucune rigidité en torsion (A§5).
- **Source** : T5, A§5, A§11 — *déduit du document*
- **Priorité** : doit (les deux premiers cas), devrait (le troisième)
- **Critère d'acceptation** : trois parois parallèles : pas de S, raison «une seule direction» ; deux parois en croix : S à leur croisement et la remarque sur la torsion ; aucune exception Python dans aucun de ces cas, dans la fenêtre comme à l'export.

### REQ-009 — Contour du bâtiment
- **Exigence** : Woodcore doit offrir, sur le plan de positions, un outil qui dessine le contour du bâtiment : **un** polygone par plan, enregistré dans le fichier du plan. Le contour se sélectionne, se déplace, se modifie sommet par sommet et se supprime comme les autres objets du plan, chaque geste étant une étape d'«Annuler» ; il tourne avec sa page. Dessiner un contour sur un plan qui en a déjà un remplace l'ancien, en une étape d'«Annuler» (D-010).
- **Source** : T12
- **Priorité** : doit
- **Critère d'acceptation** : un contour de cinq sommets dessiné, enregistré, rouvert : les cinq sommets sont dans le fichier ; un sommet déplacé déplace M ; «Annuler» rend l'ancien contour ; un contour de moins de trois sommets dans le fichier le fait refuser.

### REQ-010 — Centre de masse M
- **Exigence** : Woodcore doit calculer M comme le centre géométrique de la surface du contour (le barycentre de l'aire, pas la moyenne des sommets), sans masse ni charge. Sans contour, ou avec un contour d'aire nulle, M n'est ni calculé ni dessiné. M n'est enregistré nulle part.
- **Source** : T13
- **Priorité** : doit
- **Critère d'acceptation** : un contour rectangulaire 12 × 8 donne M = (6,0 ; 4,0) ; un contour en L donne le barycentre de l'aire du L, qui n'est pas la moyenne de ses six sommets ; le même contour parcouru dans l'autre sens donne le même M.

### REQ-011 — Plans concernés
- **Exigence** : S, M et le contour sont ceux d'une **coupe en plan** et d'un **plan de descente de charges**. Une coupe en élévation n'a ni l'outil ni le calcul, et passer un plan en coupe en élévation retire son contour (la règle existante : «changer le type retire ce que le nouveau type ne porte pas», en une étape d'«Annuler»). Le plan de protection incendie n'a rien de tout cela.
- **Source** : T1 — *déduit : une élévation n'a pas de centre de rigidité en plan ; `docs/architecture/principles.md` règle 16*
- **Priorité** : doit
- **Critère d'acceptation** : sur une coupe en élévation l'outil «Contour» est absent et refusé, et aucun S n'est dessiné même avec des parois H ; l'onglet «Protection incendie» n'a ni l'outil ni la carte.

### REQ-012 — Impression dans le rapport
- **Exigence** : une case à cocher du plan, enregistrée avec lui, décide si S, M et le contour apparaissent sur le plan imprimé : décochée (l'état d'un plan nouveau et de tout plan existant), le plan exporté ne porte aucun des trois ; cochée, il les porte tous les trois — ceux qui existent.
- **Source** : T14
- **Priorité** : doit
- **Critère d'acceptation** : la case cochée puis le plan enregistré : le fichier porte le drapeau, le dessin exporté (`data/plans/<id>.svg`) contient S, M et le contour, et `#show-plan` les imprime ; décochée : le dessin exporté est, octet pour octet, celui d'avant cette fonctionnalité.

### REQ-013 — Avertissement quand le mode contredit la section de la position
- **Exigence** : le mode de construction reste un champ du plan, indépendant de la position ; Woodcore doit avertir — sous le plan et à l'export, sans rien arrêter — quand une paroi H ou W dont la position a une section de type `clt` porte un autre mode que CLT. Une paroi sans mode n'est pas concernée (REQ-006 la signale déjà), et l'autre sens n'est pas contrôlé : une paroi CLT dont la position a une section `pla` ou aucune section n'est pas une contradiction.
- **Source** : T8, Q-004 (réponse du 2026-10-13)
- **Priorité** : doit
- **Critère d'acceptation** : la paroi W101, dont la position a une section `clt`, mise en «ossature bois» : un avertissement nomme W101 et les deux énoncés, sous le plan et à l'export ; remise en «CLT», ou sa section passée en `rec` : plus d'avertissement.

## 4. Exigences d'interface (fenêtre, rapport, site)

### UI-001 — Champ «Mode de construction»
- **Exigence** : le volet de droite montre «Mode de construction» (ossature bois, CLT, béton) pour une paroi H ou W sélectionnée, et pour l'outil H ou W dès qu'il est choisi — la paroi suivante prend alors le mode de l'outil (la règle de l'issue #9 : un outil montre les options de son objet). Un changement est une étape d'«Annuler». Pas de bouton nouveau : une liste déroulante.
- **Source** : T7
- **Langues** : fr / de / en
- **Critère d'acceptation** : outil W choisi, «CLT» réglé, deux parois dessinées : les deux sont en CLT ; une paroi sélectionnée passée en «béton» puis «Annuler» : elle revient en CLT.

### UI-002 — Outil «Contour du bâtiment»
- **Exigence** : un outil de la barre du plan de positions, dans la vue «Dessin», qui se dessine comme une surface (un clic par sommet ; fin sur un clic sur le premier sommet, Entrée ou un double-clic ; Échap annule ; Retour arrière retire le dernier point ; Maj garde l'horizontale, la verticale ou 45° ; accrochage et repérage comme les autres outils).
- **Source** : T12
- **Langues** : fr / de / en (nom, bulle, indication sous le plan)
- **Critère d'acceptation** : test de la fenêtre hors écran : l'outil choisi, quatre clics et un clic sur le premier sommet créent le contour ; l'indication sous le plan est celle de l'outil dans les trois langues.
- **Écart à l'implémentation (2026-10-13), relevé par la vérification** : le bouton de la barre s'intitule «Contour» («Umriss», «Outline»), sa bulle et l'indication sous le plan disant «Contour du bâtiment» — un bouton de la barre porte un mot court, comme «Texte» ou «Copier».

### UI-003 — Carte «Centre de rigidité et centre de masse»
- **Exigence** : avec rien de sélectionné, le volet de droite du plan montre une carte qui porte : la case «Imprimer S, M et le contour dans le rapport» (REQ-012) ; le choix de la puissance du CLT (1,5 ou 2, D-015), visible seulement quand des parois du plan sont en CLT ; et une ligne d'état — S calculé (combien de parois, quel mode, quelle puissance) ou la raison pour laquelle il ne l'est pas (REQ-005, REQ-006, REQ-008), de même pour M (REQ-010).
- **Source** : T14, T11, T9
- **Langues** : fr / de / en
- **Critère d'acceptation** : sur un plan aux modes mélangés la carte nomme les modes trouvés ; sur un plan en CLT sans puissance choisie elle demande de la choisir ; la largeur minimale du volet de droite ne dépasse pas celle d'aujourd'hui (`tests/test_panes.py`).
- **Écart à l'implémentation (2026-10-13), à confirmer par l'ingénieur** : la carte s'intitule «Centres S et M» et sa case «Imprimer dans le rapport» (bulle : «Le centre de rigidité S, le centre de masse M et le contour du bâtiment sont toujours dessinés ici…»), ses deux lignes d'état commençant par «Centre de rigidité S :» et «Centre de masse M :». Raison : le titre d'une carte ne se replie pas, et le titre long faisait de cette carte la plus large du volet — 599 px de largeur minimale contre 495 mesurés en français —, contre le dernier critère ci-dessus.

### UI-004 — Dessin dans la fenêtre
- **Exigence** : dans la vue «Dessin», S, M et le contour sont toujours dessinés quand ils existent, quelle que soit la case d'impression : le contour en trait fin, S et M par un symbole chacun avec sa lettre «S» et «M» (D-014). S et M suivent le dessin à chaque modification (une paroi déplacée, un mode changé, un sommet du contour déplacé).
- **Source** : T14, T13
- **Langues** : — (les lettres S et M sont les mêmes dans les trois langues)
- **Critère d'acceptation** : test de la fenêtre hors écran : le dessin de la vue contient S et M ; une paroi déplacée, S a changé de place sans enregistrement.

### UI-005 — Plan imprimé
- **Exigence** : case cochée, le plan imprimé (`#show-plan`, `#doc-plan`, les feuilles d'export) porte S, M et le contour, et la légende une ligne pour chacun de ceux qui sont dessinés («Centre de rigidité», «Centre de masse», «Contour du bâtiment»). Un appel peut les retirer (UI-007).
- **Source** : T14
- **Langues** : fr / de / en (la légende suit la langue du document)
- **Critère d'acceptation** : le rapport de `tests/projet-exemple/` compilé avec un plan dont la case est cochée montre les trois et leurs lignes de légende en allemand, en français et en anglais ; case décochée, ni symbole ni ligne de légende.

### UI-006 — Avertissement quand l'impression est demandée et que rien ne peut être dessiné
- **Exigence** : case cochée, si S ou M ne peut pas être calculé, l'export et la ligne d'avertissements sous le plan le disent avec la raison (un avertissement, jamais un arrêt : «une entrée manquante avertit»).
- **Source** : T14 — *déduit, principe du CLAUDE.md*
- **Langues** : fr / de / en dans la fenêtre
- **Critère d'acceptation** : un plan à la case cochée et aux modes mélangés : `plan.warnings` rend un avertissement qui nomme le plan et la raison ; l'export aboutit.

### UI-007 — Argument `centres:` des commandes Typst
- **Exigence** : `#show-plan`, `#doc-plan` et `sheet-viewport` reçoivent `centres:`, vrai par défaut, comme `dimensions:` et `lengths:` : la case du plan décide si l'export dessine S, M et le contour, et `centres: false` les retire d'un appel. `calc-block` ne les imprime pas dans ses détails. Le constructeur de commande de la vue «Affichage» et la vue en plan d'une feuille d'export offrent ce réglage là où ils offrent déjà les cotes et les longueurs.
- **Source** : T14, Q-003 (réponse du 2026-10-13)
- **Langues** : fr / de / en (`calc/i18n/commands.json`, les mots du constructeur et de la feuille)
- **Critère d'acceptation** : sur un plan à la case cochée, `#show-plan("P01")` imprime les trois et `#show-plan("P01", centres: false)` aucun ; un `calc-block(plan: auto)` n'en imprime aucun ; chaque commande porte son `///`, la ligne `- centres (bool):` et deux exemples qui compilent ; `tests/test_commands.py` passe.

## 5. Exigences d'architecture

### ARCH-001 — Le calcul est dans `calc/domains/`, sans Qt
- **Exigence** : les parois tirées du plan, leur rigidité, S, M et les raisons d'un non-calcul sont calculés par un module de `calc/domains/` sans Qt ; la fenêtre, le dessin (`plan_svg`) et l'export appellent la même fonction et ne recalculent rien.
- **Source** : principe «la logique métier est indépendante de l'interface» (CLAUDE.md), T5
- **Critère d'acceptation** : le module s'importe et ses tests passent sans PySide6 ; aucune formule de A§9 dans `calc/tools/`.

### ARCH-002 — Une seule source : S et M ne sont jamais enregistrés
- **Exigence** : le fichier du plan porte les entrées (mode de chaque paroi, puissance du CLT, contour, case d'impression) et jamais S ni M, comme une cote ne porte pas sa valeur. M réutilise `plan_geometry.centroid`, qui existe.
- **Source** : `docs/architecture/principles.md` règle 1
- **Critère d'acceptation** : `schemas/plan-source.schema.json` n'a aucun champ pour la position de S ou de M ; une paroi déplacée dans le fichier à la main, l'export dessine S à sa nouvelle place.

### ARCH-003 — Contrat de données versionné, additif
- **Exigence** : `plan-source` passe à une nouvelle version, écrite seulement par un plan qui porte un des champs nouveaux (la règle de la version 1.7 pour les textes) ; un fichier 1.0 à 1.7 est lu tel quel, sans migration ; `schemas/plan-source.schema.json` et `plan.check_source` décrivent et contrôlent les champs nouveaux (un fichier mal formé arrête, en nommant le fichier et le champ). Ce que l'export ajoute à `data/plans.json` est additif et écrit seulement où un plan l'utilise.
- **Source** : `docs/architecture/principles.md` règles 8 et 10 ; `docs/domain/position-plans.md` §3.3sexies
- **Critère d'acceptation** : un plan sans champ nouveau est enregistré à la version d'avant ; les quatre plans de `tests/projet-exemple/` et les empreintes figées de `tests/test_plan_style.py` sont inchangés.

### ARCH-004 — Rien en dur, méthode citée
- **Exigence** : les modes de construction et leurs puissances sont dits une fois, à un seul endroit du domaine ; les mots sont dans les glossaires (trois langues) ; les couleurs là où le plan tient les siennes. Le calcul cite sa source — le document «Centre de rigidité d'un étage — calcul mécanique général» (12.10.2026), sections 5 et 9, mécanique générale, aucune norme — dans le code, dans `docs/domain/` et dans ce que l'export écrit.
- **Source** : `docs/architecture/principles.md` règles 5 et 7 ; A (statut)
- **Critère d'acceptation** : `grep` ne trouve les puissances 1,5 et 3 qu'à un endroit de `calc/` ; `docs/domain/position-plans.md` décrit la méthode, ses hypothèses (A§2) et ses limites (A§12).

### ARCH-005 — Décision d'architecture consignée
- **Exigence** : `docs/decisions.md` (§13) reçoit la décision «le plan porte le mode de construction d'une paroi», avec sa raison et son prix (T8) ; `docs/domain/position-plans.md` corrige la phrase «le plan ne porte ni matériau, ni section, ni charge» ; `docs/domain/fire-plans.md` dit pourquoi le plan d'incendie ne prend pas cette fonction (règle 16).
- **Source** : T8, `docs/architecture/principles.md` règle 16
- **Critère d'acceptation** : les trois fichiers portent ces passages ; `tests/test_docs_coherence.py` passe.

### ARCH-006 — Les versions du fichier d'un plan se composent
- **Exigence** : `plan.version_of` rend la plus haute version dont le plan a besoin — 1.6, 1.7 s'il porte un texte, 1.8 s'il porte un champ de cette fonctionnalité (un seul prédicat, `plan_centres.uses_centres`) —, 1.8 contenant 1.7. Tout ce qui écrit un plan passe par `version_of`, y compris `plan_pages._write_position`, qui force aujourd'hui 1.6 (défaut existant relevé par la revue : tourner la page d'un plan qui porte un texte est refusé). `check_texts` accepte les versions qui peuvent porter un texte.
- **Source** : revue (ARCH-RISK-001)
- **Critère d'acceptation** : un plan avec un texte et un contour s'enregistre en 1.8 et se relit ; un plan avec un texte seul reste en 1.7 et un plan sans rien en 1.6 ; la page d'un plan qui porte un texte, ou un contour, se tourne sans refus.

### ARCH-007 — Forme du contour
- **Exigence** : `outlines`, liste de premier niveau d'au plus un `{points}` de trois points au moins, sans `style` propre, refusée sur une coupe en élévation ; une sorte de sélection à elle dans `plan.ENTRY_LISTS` ; pris à la souris par son **arête seulement** (un clic à l'intérieur du bâtiment ne le sélectionne pas) ; ses sommets sont des points d'accrochage ; il ne se copie pas.
- **Source** : revue (ARCH-RISK-002), D-010, D-019
- **Critère d'acceptation** : `plan.check_source` refuse deux contours, un contour de deux points, un `style` sur un contour, un contour sur une coupe en élévation ; test de la fenêtre : un clic au milieu du contour ne le sélectionne pas, un clic sur son arête oui ; «Copier» et «Dupliquer» ne font pas de second contour.

### ARCH-008 — La légende suit `centres:`
- **Exigence** : les lignes de légende de S, de M et du contour sont marquées dans les données de l'export, et `plan-legend` les retire quand la commande reçoit `centres: false` — aucune liste de clés recopiée en Typst. Case cochée mais rien de calculable ni de dessiné : ni marqueur ni ligne de légende, l'avertissement seul.
- **Source** : revue (ARCH-RISK-003, ARCH-RISK-010)
- **Critère d'acceptation** : `#show-plan("P01", centres: false)` n'imprime ni les symboles ni leurs lignes de légende ; un test tient le marqueur écrit par Python égal à l'expression que Typst retire.

### ARCH-009 — Les sections des positions arrivent jusqu'aux avertissements
- **Exigence** : `plan.warnings`, `plan.prepare` et `plan.export` reçoivent `sections=` (numéro de position → type de section) de chacun de leurs appelants (`export_all.py`, `plan_pages.py`, `plan_tab.py`, `plan_tab_selection.py`) ; sans lui l'avertissement de REQ-013 n'est pas évalué.
- **Source** : revue (ARCH-RISK-004)
- **Critère d'acceptation** : l'avertissement de REQ-013 sort par l'export et par la fenêtre, chacun prouvé par un test.

### ARCH-010 — Tolérances numériques dites une fois
- **Exigence** : «même direction» et «tronçons alignés» se jugent par une tolérance d'angle nommée ; «lignes concourantes» et «aire nulle» par une tolérance relative à la taille du dessin — jamais par un seuil absolu, les longueurs étant en unités de la feuille (`l³` atteint 10⁸). L'aire du contour est contrôlée avant `centroid`, qui retombe sinon sur la moyenne des sommets.
- **Source** : revue (ARCH-RISK-005)
- **Critère d'acceptation** : le plan 12 × 8 de REQ-004 multiplié par 1000, puis divisé par 1000, donne le même S à l'échelle près ; deux parois que l'arrondi au centième d'unité écarte de 0,01° du parallèle comptent pour une seule direction.

### ARCH-011 — Une phrase par raison, un mot par réglage
- **Exigence** : chaque raison (aucune paroi, paroi sans mode, modes mélangés, puissance à choisir, une seule direction, aucune rigidité en torsion, pas de contour, contour d'aire nulle, section `clt` contredite) est une `engine.Note` d'un code, traduite une fois dans les trois langues (`warn_*`), que la carte et les avertissements lisent toutes deux. Le mot du réglage `centres:` n'est pas recopié d'un module à l'autre sans un test qui tienne les copies égales.
- **Source** : revue (ARCH-RISK-006)
- **Critère d'acceptation** : chaque code a son `warn_` en français, en allemand et en anglais ; `tests/test_i18n.py` passe.

## 6. Contraintes

- **CON-001** — La méthode est celle du document en annexe, sections 5 et 9 : de la mécanique générale, aucune valeur de norme. Les puissances 1 ; 1,5 ou 2 ; 3 sont le choix de l'ingénieur (T10), pas une norme. Source : T2, T10, A (statut).
- **CON-002** — Le repère de la feuille a y vers le bas, celui du document y vers le haut et les angles en sens anti-horaire : le résultat ne doit pas en dépendre (REQ-007 c). Source : A§3 — *déduit*.
- **CON-003** — Toute chaîne visible existe en français, en allemand et en anglais. Source : CLAUDE.md — *déduit*.
- **CON-004** — Un plan enregistré avant cette version s'ouvre, se dessine et s'exporte exactement comme avant. Source : `docs/domain/position-plans.md` §3.3sexies — *déduit*.
- **CON-005** — Le dessin exporté reste dans ce que QtSvg et Typst lisent de la même façon (ni motif, ni découpe, ni marqueur, ni CSS). Source : `docs/domain/position-plans.md` §3.3sexies — *déduit*.

## 7. Décisions prises

Dans la source :

- **D-001** (T8) — Le plan porte désormais le mode de construction d'une paroi. *Prix : la règle «le plan ne porte ni matériau, ni section, ni charge» a une exception ; le mode du plan et la section de la position (son type `clt`) sont deux énoncés sur la même paroi (Q-004). À consigner dans `docs/decisions.md`.*
- **D-002** (T4) — S et M seulement : ni excentricité, ni excentricités de dimensionnement, ni répartition des efforts.
- **D-003** (T2, T5) — La méthode est celle du document, sections 5 et 9.
- **D-004** (T6) — Seuls H et W sont des parois pour ce calcul.
- **D-005** (T9) — Un seul mode de construction par calcul, sinon pas de S. *Prix : un étage mixte (noyau béton et parois à ossature) n'a pas de S dans Woodcore.*
- **D-006** (T10, T11) — Rigidité = longueur à la puissance 1 (ossature bois), 1,5 ou 2 au choix (CLT), 3 (béton).
- **D-007** (T13) — M est le centre géométrique du contour, pas un barycentre de masses. *Prix : M est faux pour un étage dont les masses ne sont pas réparties uniformément.*
- **D-008** (T14) — Une seule case pour les trois (S, M, contour), enregistrée avec le plan.

*Par défaut, à confirmer à l'approbation* (déduites, pas dites par la source) :

- **D-009** — Une paroi est un tronçon droit (REQ-003). Raison : A§2 hypothèse 3, une paroi ne travaille que dans son plan. *Prix : une paroi en L n'est pas un noyau ; le couplage de ses ailes est ignoré (A§12).*
- **D-010** — Un seul contour par plan ; en dessiner un autre remplace le premier. Raison : T12 dit «un polygone». *Prix : pas de bâtiment en deux corps séparés, pas de trou.*
- **D-011** — Le champ «Mode de construction» est offert sur H et W seulement. Raison : sur un V il ne servirait à rien, et un champ sans effet est un champ que personne ne contrôle (la règle de v0.99 sur `style`). *Prix : un V n'a pas de mode.*
- **D-012** — S se calcule sans échelle (seuls les rapports comptent) ; les positions de S et de M ne sont pas des variables du rapport et ne sont imprimées nulle part en chiffres.
- **D-013** — La case d'impression est décochée par défaut.
- **D-014** — Symboles : S, un cercle barré d'une croix, dans le violet des parois de contreventement, avec la lettre «S» ; M, un cercle à deux quartiers pleins (le symbole du centre de gravité), en gris foncé, avec la lettre «M» ; le contour, un trait fin interrompu gris foncé. Tailles réglées par les trois curseurs du plan.

En répondant aux questions (2026-10-13) :

- **D-015** (Q-001) — La puissance du CLT est un champ **du plan**, choisi dans sa carte et enregistré avec lui. *Prix : à régler sur chaque plan en CLT ; deux plans du même bâtiment peuvent porter deux puissances.*
- **D-016** (Q-002) — **Aucun mode par défaut** : une paroi H ou W sans mode empêche le calcul de S, et la carte nomme ces parois ; l'outil garde le dernier mode choisi pour les parois suivantes. *Prix : les parois déjà dessinées sont à régler une fois, une par une.*
- **D-017** (Q-003) — Les commandes Typst reçoivent **`centres:`** (vrai par défaut) ; `calc-block` ne les imprime pas dans ses détails. *Prix : un argument de plus à documenter sur trois commandes (`///`, deux exemples, trois langues).*
- **D-018** (Q-004) — Le mode du plan et la section de la position restent **indépendants**, et Woodcore **avertit** quand une section `clt` porte un autre mode que CLT. *Prix : un avertissement de plus ; l'autre sens n'est pas contrôlé.*

Après la revue d'architecture (2026-10-13), *par défaut, à confirmer à l'approbation* :

- **D-019** (ARCH-RISK-002) — Le contour est une liste `outlines` d'au plus une entrée, et non un type d'élément de plus. Raison : avec un type d'élément, un oubli d'exclusion fait fuir le contour en silence dans l'export, la légende ou les métrés ; avec la liste, un oubli se voit à l'écran. *Prix : plus de code dans la fenêtre (sélection, glissement de sommet).*
- **D-020** — Pour un plan dont la case est cochée, l'export écrit dans son enregistrement de `data/plans.json` un bloc `centres` (S, M, le contour, le mode, la puissance, le nombre de parois, la source du calcul et la méthode citée), en unités de la feuille comme le reste de l'enregistrement ; `plans.json` passe en 1.5 seulement quand un plan en porte un (le précédent des textes, 1.4). *Prix : une version d'export de plus.*
- **D-021** (ARCH-RISK-009) — Le mode de l'outil se règle dans le volet de l'outil et vaut pour la session ; changer le mode d'une paroi sélectionnée ne change pas celui de l'outil.

À l'approbation (2026-10-13) : l'ingénieur approuve la spécification, la revue et le plan, avec D-009 à D-014 et D-019 à D-021 telles qu'elles sont écrites.

- **D-022** (Q-005) — `#show-plan-legend` et `sheet-legend` ne reçoivent pas `centres:` : une légende imprimée à part liste ce que le plan imprime, d'après sa case. *Prix : sur une feuille d'export, une vue en plan à `centres: false` à côté d'une légende laisse trois lignes de légende sans symbole ; inscrit dans `docs/open-questions.md`.*

## 8. Hors périmètre

- L'excentricité entre M et S (A§6), les excentricités de dimensionnement de la SIA 261:2020, chiffre 16.5.2.7 (A§8), la rigidité en torsion affichée et la répartition des efforts sur les parois (A§7) — T4.
- Un centre de masse tiré de masses ou de charges (A§6) : M est géométrique (T13).
- La rigidité absolue d'une paroi (kN/mm), sa hauteur, sa composition, ses ouvertures (A§4) : seule la longueur compte (T10).
- Un calcul sur plusieurs étages (A§12) : un plan, un étage.
- Le plan de protection incendie et la coupe en élévation (REQ-011).
- Les positions de S et de M comme variables du rapport ou dans un tableau (D-012).

## 9. Idées non retenues comme exigences

- A§12 — «Une étude de sensibilité (par exemple ±30 % sur les parois dont la rigidité est mal connue)» : une piste du document, pas une demande.
- A§13 — Les pistes pour la rigidité des parois en bois (cours de M. Geiser, Lignatec 32/2020, documentation Lignum) : contexte, non demandé ; à lire avant de remplacer un jour `l^n` par une rigidité calculée.
- A§7, A§8, A§10 — La répartition des efforts et son exemple chiffré : hors périmètre (T4), mais l'exemple sert de valeur de contrôle pour S (REQ-007 a).

## 10. Questions

### Q-001 — Où l'ingénieur choisit-il la puissance du CLT (1,5 ou 2) ?
- **Pourquoi elle compte** : c'est un champ de données nouveau ; sa place fixe le fichier qui le porte et ce qui se passe quand deux plans du même bâtiment sont en CLT.
- **Options** : A (recommandée) — sur le plan, dans la carte «Centre de rigidité et centre de masse», enregistrée avec lui ; sans choix, S n'est pas calculé. *Prix : à régler sur chaque plan.* B — un réglage du projet, valable pour tous ses plans. *Prix : un fichier de plus à lire pour dessiner un plan, et pas deux hypothèses dans un même projet.* C — sur chaque paroi CLT. *Prix : un champ par paroi, et des parois d'un même étage à des puissances différentes.*
- **Réponse** : A — sur le plan (réponse de l'ingénieur, 2026-10-13) → D-015.

### Q-002 — Une paroi H ou W qui n'a pas de mode de construction (toutes celles déjà dessinées, et une paroi nouvelle tant que rien n'est choisi)
- **Pourquoi elle compte** : elle décide si S apparaît sur les plans existants sans rien faire, ou seulement après un choix explicite.
- **Options** : A (recommandée) — pas de mode par défaut : S n'est pas calculé tant qu'une paroi H ou W est sans mode, et la carte dit lesquelles ; l'outil garde le dernier mode choisi pour les parois suivantes. *Prix : il faut régler les parois déjà dessinées, une par une.* B — «ossature bois» par défaut pour toute paroi sans mode. *Prix : un S calculé sur une hypothèse que personne n'a choisie, par exemple pour un mur en béton dessiné en W.*
- **Réponse** : A — pas de mode par défaut (réponse de l'ingénieur, 2026-10-13) → D-016.

### Q-003 — Les commandes Typst reçoivent-elles un argument pour masquer S, M et le contour dans un appel ?
- **Pourquoi elle compte** : c'est la surface des commandes, que l'ingénieur décide. `calc-block` imprime un détail du plan autour de ses positions : sans argument, le contour y apparaît le long de chaque paroi de façade.
- **Options** : A (recommandée) — `#show-plan`, `#doc-plan` et `sheet-viewport` reçoivent `centres:` (vrai par défaut), comme `dimensions:` et `lengths:` ; la case du plan décide si l'export les dessine, `centres: false` les retire d'un appel, et `calc-block` ne les imprime pas dans ses détails. *Prix : un argument de plus à documenter sur trois commandes (`///`, deux exemples, trois langues).* B — aucun argument : la case seule décide, partout. *Prix : les détails de `calc-block` montrent le contour et, s'ils tombent dans le cadre, S et M.*
- **Réponse** : A — oui, `centres:` (réponse de l'ingénieur, 2026-10-13) → D-017, UI-007.

### Q-004 — Le mode du plan et la section de la position disent-ils la même chose ?
- **Pourquoi elle compte** : le volet du plan montre déjà la *Section* de la position d'une paroi, dont le type peut être `clt` (issue #9). Avec le mode sur le plan, une paroi peut être «CLT» d'un côté et «ossature bois» de l'autre : deux sources (règle 1).
- **Options** : A (recommandée) — le mode reste un champ du plan, indépendant, et Woodcore **avertit** quand une paroi dont la position a une section de type `clt` porte un autre mode que CLT. *Prix : un avertissement de plus.* B — indépendants, sans contrôle. *Prix : la contradiction ne se voit pas.* C — le mode est proposé d'après la section (type `clt` → CLT) quand il n'est pas encore donné, par copie, sans lien ni avertissement. *Prix : la copie peut vieillir sans le dire.*
- **Réponse** : A — avertir (réponse de l'ingénieur, 2026-10-13) → D-018, REQ-013.

### Q-005 — Les commandes de légende seule reçoivent-elles aussi `centres:` ?
- **Pourquoi elle compte** : c'est la surface des commandes. `#show-plan` filtre sa propre légende (ARCH-008), mais `#show-plan-legend` et `sheet-legend` impriment une légende à part : avec `centres: false` sur le plan à côté, elles listeraient S, M et le contour, qui n'y sont pas dessinés (ARCH-RISK-003).
- **Options** : A (recommandée) — non : les trois commandes de D-017 seulement ; une légende seule liste ce que le plan imprime, d'après sa case. *Prix : sur une feuille d'export, une vue en plan à `centres: false` à côté d'une légende laisse trois lignes de légende sans symbole ; inscrit dans `docs/open-questions.md`.* B — oui : `#show-plan-legend` et `sheet-legend` reçoivent `centres:` elles aussi. *Prix : cinq commandes à documenter au lieu de trois, et une case de plus dans le volet de la légende d'une feuille.*
- **Réponse** : A — non, les trois commandes de D-017 seulement (réponse de l'ingénieur, 2026-10-13) → D-022.

## 11. Critères d'acceptation

- [x] REQ-001 — le mode d'une paroi H ou W est enregistré avec le plan et relu ; un mode inconnu ou mal placé fait refuser le fichier.
- [x] REQ-002 — seuls H et W déplacent S.
- [x] REQ-003 — un tronçon droit est une paroi ; des tronçons alignés d'un élément en sont une seule.
- [x] REQ-004 — les quatre valeurs de S du plan 12 × 8 (9,0 ; 10,8 ; 10,063 ; 11,571), avec et sans échelle.
- [x] REQ-005 — la puissance du CLT se choisit entre 1,5 et 2, est enregistrée, et S attend ce choix.
- [x] REQ-006 — modes mélangés : pas de S, la raison nomme les modes.
- [x] REQ-007 — exemple A§10, rotation de 30°, repère retourné, parois inclinées contre le code de référence.
- [x] REQ-008 — aucune paroi, une seule direction, lignes concourantes : pas d'exception, la raison dite.
- [x] REQ-009 — le contour se dessine, s'enregistre, se modifie, se supprime, s'annule ; un second remplace le premier.
- [x] REQ-010 — M du rectangle et du L ; pas de M sans contour.
- [x] REQ-011 — ni outil ni calcul sur une coupe en élévation ni sur le plan d'incendie.
- [x] REQ-012 — la case décide de l'impression ; décochée, l'export est identique à l'octet.
- [x] REQ-013 — l'avertissement section `clt` / autre mode.
- [x] UI-001 — «Mode de construction» pour la paroi sélectionnée et pour l'outil.
- [x] UI-002 — l'outil «Contour du bâtiment» dans la barre, dessiné comme une surface.
- [x] UI-003 — la carte et sa ligne d'état, sans élargir le volet *(sous le titre court «Centres S et M», écart gardé, §15)*.
- [x] UI-004 — S, M et le contour dans la vue «Dessin», à jour à chaque modification.
- [x] UI-005 — le plan imprimé et sa légende dans les trois langues.
- [x] UI-006 — l'avertissement quand l'impression est demandée et que S ou M manque.
- [x] UI-007 — `centres:` sur `#show-plan`, `#doc-plan` et `sheet-viewport` ; rien dans les détails de `calc-block`.
- [x] ARCH-001 — le module du domaine sans Qt, appelé par la fenêtre, le dessin et l'export.
- [x] ARCH-002 — ni S ni M dans le fichier du plan.
- [x] ARCH-003 — nouvelle version de `plan-source` écrite seulement où elle sert ; empreintes figées inchangées.
- [x] ARCH-004 — modes et puissances dits une fois ; méthode citée.
- [x] ARCH-005 — `docs/decisions.md`, `position-plans.md` et `fire-plans.md` à jour.
- [x] ARCH-006 — 1.6 / 1.7 / 1.8 se composent ; la page d'un plan avec un texte se tourne.
- [x] ARCH-007 — `outlines` d'au plus un, arête seule, pas de copie, refusé sur une coupe.
- [x] ARCH-008 — `centres: false` retire aussi les lignes de légende ; marqueur Python égal à l'expression Typst.
- [x] ARCH-009 — `sections=` de l'export et de la fenêtre.
- [x] ARCH-010 — tolérances nommées ; même S à l'échelle près.
- [x] ARCH-011 — un code `warn_*` par raison, trois langues.
- [x] Documentation : `docs/domain/position-plans.md`, `docs/ui/tab-plans.md`, `docs/decisions.md` et son index, `docs/open-questions.md` (ce qui reste : excentricité, répartition), entrée `CHANGELOG.md`, page «Nouveautés» fr/de/en ; `///`, deux exemples et traductions pour l'argument `centres:` (UI-007), et la table de `docs/typst/api-conventions.md`. *(sauf un exemple figé propre à `centres:`, écart gardé, §15)*
- [x] Tests : un fichier `tests/test_*.py` pour le domaine et un pour la fenêtre, chacun avec sa ligne dans `docs/conventions/testing-catalogue*.md`, et la suite complète.

## 12. Traçabilité

| Source | Élément | Statut |
|---|---|---|
| T1 | §1 Objectif, REQ-011 | capturé |
| T2 | REQ-007, CON-001, D-003 | capturé |
| T3 | — | contexte (suite de #18) |
| T4 | §8 Hors périmètre, D-002 | capturé |
| T5 | REQ-007, REQ-003, REQ-008, ARCH-001 | capturé |
| T6 | REQ-002, D-004 | capturé |
| T7 | REQ-001, UI-001, D-016 | capturé (Q-002 répondue) |
| T8 | D-001, ARCH-005, REQ-013, D-018 | décision (Q-004 répondue) |
| T9 | REQ-006, D-005 | capturé |
| T10 | REQ-004, D-006 | capturé |
| T11 | REQ-005, UI-003, D-015 | capturé (Q-001 répondue) |
| T12 | REQ-009, UI-002 | capturé |
| T13 | REQ-010, D-007 | capturé |
| T14 | REQ-012, UI-003, UI-004, UI-005, UI-006, UI-007, D-008, D-017 | capturé (Q-003 répondue) |
| T15 (A§2, A§3) | REQ-003, CON-002 | capturé |
| T15 (A§4) | REQ-004 | capturé |
| T15 (A§5, A§9, A§11) | REQ-007, REQ-008 | capturé |
| T15 (A§6, A§7, A§8) | §8 Hors périmètre | exclu (T4) |
| T15 (A§10) | REQ-007 a | valeur de contrôle |
| T15 (A§12, A§13) | §9 | idées ; les limites vont dans la doc (ARCH-004) |

### Points de la source non résolus

- Aucun : Q-001 à Q-004 ont reçu leur réponse le 2026-10-13.

## 13. Revue d'architecture

Revue indépendante du 2026-10-13 (agent `architecture-reviewer`, lecture seule ; le code a été lu, pas seulement la doc). Verdict : **APPROUVER AVEC RÉSERVES**.

### Modules concernés

- **Source et contrat** — `calc/domains/plan.py` : les versions et `version_of` (l.110–127) ; `check_source` (l.347–488), qui refuse déjà `angle` et `show_length` hors de leurs types (l.444–452), le modèle de REQ-001 ; `check_texts` (l.494) ; `ENTRY_LISTS` (l.565) ; `translate_entry` et `copy_entry` (l.574–597) ; `apply_defaults` (l.763) ; `warnings` (l.816) ; `build_record` (l.855) ; `prepare` (l.996) ; `_turn_quarter` (l.1185). `schemas/plan-source.schema.json` (enum 1.0–1.7), `schemas/plans.schema.json` (export 1.3/1.4), `calc/validation.py:645` (`PLAN_KINDS`).
- **Géométrie** — `calc/domains/plan_geometry.py` : `TYPES` (l.13), `ring_area` (l.113), `quantities` (l.130, itère tous les éléments), `centroid` (l.181), `segments_of` (l.441), `hit_element` (l.475), `SnapIndex` (l.547) ; `calc/domains/plan_tracking.py:57` (`PlanSnapIndex`).
- **Dessin** — `calc/domains/plan_svg.py` : couleurs (l.19–40), marqueurs (l.44–62), `LEGEND` (l.68), `render` (l.772), appelé par l'export (`plan.py:1032` et `:1040`), par la fenêtre (`plan_canvas_view.py:497`) et pour la superposition (`:597`) ; `legend_keys` (l.955), `_swatch_body` (l.981), `legend_items` (l.1014).
- **Fenêtre** — `plan_canvas_editing.py` (`finish_drawing` l.431, `add_element` l.452, `delete_selection` l.310), `plan_canvas_input.py` (`press_select` l.252, glissements l.366–476), `plan_tab_build.py` (`on_plan_type` l.474, `tool_shown` l.498), `plan_tab_selection.py:386` (`element_properties`), `plan_properties.py:85` (`tool_rows`), `drawing_tab_panes.py:352` (`add_module`).
- **Typst** — `lib/calc-engine.typ` : `plan-legend` (l.1151), `plan-figure` (l.1200), `show-plan` (l.1260), `calc-block` (l.1926, l.1928) ; `lib/document.typ:768` (`doc-plan`) ; `lib/sheet.typ:237` (`sheet-viewport`) et `:371` (`sheet-legend`).
- **Trois écrivains de `schema_version`** — `plan_tab.py:294`, `drawing_tab_documents.py:291`, `plan_pages.py:65–69`.

### Existant à réutiliser

- **M** : `plan_geometry.centroid` et `ring_area`.
- **Les parois** : `segments_of` donne les tronçons ; seule la fusion des tronçons alignés est nouvelle.
- **Contrôle des champs** : le patron par rappel de `figure_style.check` et `figure_text.check` (`plan.py:420`, `:509`), qui évite l'import circulaire `plan` ↔ `plan_svg`.
- **Raisons et avertissements** : `engine.Note(code, anglais, **args)`, traduite par `note_text` (`woodcore_gui.py:334`, clés `warn_*` de `woodcore_gui_words.py`) — la carte (UI-003) et les avertissements (UI-006) lisent la même `Note`. `plan_dimensions_no_scale` n'a pas de `warn_` : ne pas copier cette omission.
- **Marqueurs** : le patron de `DIMENSIONS_OPEN/CLOSE` (`plan_svg.py:57`) et son retrait par expression dans `plan-figure` (l.1212–1217).
- **Mode de l'outil** : `tool_defaults` et `apply_defaults`. **Carte** : `add_module(when="plan")`, comme `plan_superposition.py`.
- **Ligne de légende** : `plan.legend.<clé>` dans `calc/i18n/strings.json` (l.440–565), avec repli sur le texte allemand de `LEGEND` (`calc-engine.typ:1158–1163`).
- **Constructeur de commande** : `build_reference_calls.signature_defaults` (l.129) lit le défaut dans `lib/`. **Précédent de version** : `texts` en 1.7, écrit seulement quand il sert.

### Forme des données recommandée

- **Contour** : une liste de premier niveau `outlines` d'au plus un `{points}`, inscrite dans `ENTRY_LISTS` — et non un type d'élément de plus. Un élément de plus donnerait gratuitement le dessin, le glissement de sommet, le déplacement, l'accrochage et la rotation, mais le contour deviendrait un «élément» qui n'est ni STE ni position, à exclure à une dizaine d'endroits (`render`, `legend_keys`, `quantities`, `build_record`, `PLAN_KINDS`, `TYPE_ORDER`, la barre d'outils, le changement de type, `hit_element`) : un oubli y fait fuir le contour en silence dans l'export, alors qu'un oubli avec la liste se voit à l'écran. Dans les deux cas il faut un test d'**arête seule** : `hit_element` (l.489) prend un clic à l'intérieur d'une surface.
- **Mode de paroi** : `construction` ∈ `timber_frame` | `clt` | `concrete`, sur H et W seulement, contrôlé par le patron de `show_length` ; gardé par `deepcopy` à la copie ; rien n'itère les clés d'un élément. `TOOL_DEFAULT_KEYS` (l.760) n'est lu nulle part : le vrai registre est le corps de `apply_defaults`.
- **Champs du plan** : `clt_power` (1,5 ou 2) et `print_centres`, optionnels, écrits seulement s'ils servent.
- **Version** : un seul prédicat `plan_centres.uses_centres(source)` ; 1.8 contient 1.7, qui contient 1.6 ; `version_of` rend la plus haute version dont le plan a besoin ; `check_texts` accepte un tuple de versions (`fire.py:248` à suivre).
- **Dessin** : `render(..., centres=False)` — la fenêtre passe `True`, l'export `bool(source.get("print_centres"))` à ses deux appels ; le bloc `<!-- centres -->…<!-- /centres -->` n'est écrit que si quelque chose est dessiné ; par défaut `False`, donc la superposition ne montre pas les centres de l'autre plan.
- **Légende** : trois clés spéciales dans `LEGEND`, comme `Achse` ; marquer ces lignes dans les données et filtrer dans `plan-legend`.
- **Calcul** : un module `calc/domains/plan_centres.py`, sans Qt, qui porte la table mode → puissance, une fois. La forme de calcul `{vars, steps, checks}` n'est pas nécessaire : S est une donnée de dessin dérivée, comme `quantities` ou la valeur d'une cote. Garder une `source` et une unité dans le résultat.

### Risques

- **ARCH-RISK-001 — bloquant** — La version ne se compose pas : `check_texts` exige exactement 1.7 (`plan.py:499`), `version_of` ne connaît que 1.6 et 1.7, et un 1.8 «seulement où il sert» ne dit pas ce qu'est un plan qui a un texte et un contour. Défaut **déjà présent** : `plan_pages._write_position` (l.65–69) force 1.6, donc tourner la page d'un plan qui porte un texte est refusé. → ARCH-006.
- **ARCH-RISK-002 — important** — Forme du contour ; test d'arête seule, accrochage à ses sommets, refus de copie, et `FireCanvas`, qui hérite de `press_select`, doit rester inerte. → ARCH-007, D-019.
- **ARCH-RISK-003 — important** — `centres: false` retire le dessin mais pas les lignes de légende : c'est la première fonction retirable qui a une ligne de légende. `show-plan-legend` et `sheet-legend` listeraient des symboles absents. → ARCH-008, Q-005.
- **ARCH-RISK-004 — important** — REQ-013 a besoin du type de section, or `warnings`, `prepare` et `export` ne reçoivent que des numéros. Appelants : `export_all.py:226`, `plan_pages.py:148`, `plan_tab.py:278` et `:419`, `plan_tab_selection.py:169`. → ARCH-009.
- **ARCH-RISK-005 — important** — Numérique : `centroid` retombe sur la moyenne des sommets pour une aire nulle ; le code de l'annexe coupe `D` à 10⁻¹² en absolu, alors que les longueurs sont en points de la feuille (`l³` ≈ 10⁸) ; les tronçons «alignés» demandent une tolérance d'angle nommée. La formule A§9 est équivariante par symétrie `y → −y` : aucune conversion de repère, CON-002 se réduit à un test. → ARCH-010.
- **ARCH-RISK-006 — important** — Le mot «Longueurs des éléments» est déjà écrit trois fois (`plan_command_builder.py:51`, `sheet_editor_words.py:34`, `object_panes_words.py:127`) ; `centres` en ajouterait une quatrième copie. → ARCH-011.
- **ARCH-RISK-007 — important** — Les surfaces de `centres:` sont nombreuses et chacune est tenue par un test : `typst_objects_parse.py:20` et `:33` (`SIGNATURES`), `typst_objects_models.py:846`, `typst_objects_sheets.py:243`, `object_panes_media.py:157`, `sheet_editor_options.py:384`, `sheet_editor.py:517`, `plan_command_builder.py:173, 235, 385`, `build_reference_calls.py:299`, `calc/i18n/commands.json`, `docs/typst/api-conventions.md`, les `///`. → étape 5 du plan.
- **ARCH-RISK-008 — mineur** — Les trois modes et les puissances sont redits dans le schéma : `tests/test_constants.py` doit les tenir égaux. S prend le violet existant, une seule constante neuve près de `AXIS_COLOUR` ; aucun code de couleur dans `calc/tools/` (`tests/test_theme.py:143`). Le contour n'a pas de `style` propre : le refuser.
- **ARCH-RISK-009 — mineur** — `tool_defaults` ne vit que le temps de la session. → D-021.
- **ARCH-RISK-010 — mineur** — La description de `plan-source.schema.json` dit encore «schema 1.3» ; case cochée sans rien de calculable : ni marqueur ni ligne de légende ; un test du marqueur Python contre l'expression Typst (patron de `test_sheets.py:213`). → ARCH-008.

### Approche recommandée

`plan_centres.py` (calcul et raisons), puis `plan.py` (contrôle, version, défauts, rotation, copie), `plan_svg.py` (`render`, légende), les schémas et `validation.py` ; ensuite la fenêtre (outil, carte, volet de paroi) ; puis Typst, les constructeurs et `commands.json` ; enfin `docs/`, le CHANGELOG et les pages «Nouveautés».

### Tests

- **Nouveaux** : `tests/test_plan_centres.py` (domaine et contrat) et `tests/test_plan_centres_window.py` (fenêtre hors écran).
- **À étendre** : `test_plan_style.py` (empreintes figées, marqueurs), `test_plan_texts.py` (versions 1.6/1.7/1.8, rotation de page), `test_plan_edit_tools.py`, `test_plan_types_v0116.py`, `test_plan_documents.py`, `test_constants.py`, `test_commands.py`, `test_typst_objects.py`, `test_plan_command_builder.py`, `test_sheets.py`, `test_panes.py`, `test_fire_tab.py`, `test_i18n.py`.

### Non vérifié par la revue

La suite n'a pas été lancée ni aucun Typst compilé ; `docs/typst/command-docs.md`, `display_view.py` et les pages du site n'ont pas été lus ; le détail de `plan_canvas_input` (relâchement de la souris, «Annuler») et ce que `FireCanvas` hérite n'ont été lus que par recherche ; la largeur minimale de `test_panes.py` n'a pas été mesurée.

### Suites données

Les quatre réserves du verdict sont écrites dans cette spécification avant tout code : la composition des versions (ARCH-006), la forme du contour et son test d'arête seule (ARCH-007, D-019), le filtrage de la légende sous `centres:` (ARCH-008, Q-005), la signature `sections=` (ARCH-009). Le constat sur `plan_pages.py:67` a été vérifié dans le code par l'auteur de la spécification.

## 14. Plan d'implémentation

Sept étapes, dans l'ordre ; chacune se termine par ses tests, lancés par `python tests/run_tests.py -k <nom>`, et par une ligne du §16. Les noms des champs : `construction` (`timber_frame`, `clt`, `concrete`) sur un élément H ou W ; `outlines`, `clt_power` et `print_centres` sur le plan.

1. **Le calcul** — nouveau `calc/domains/plan_centres.py`, sans Qt, qui n'importe que `plan_geometry` et `engine` : la table mode → puissances (dite une fois), les types de parois, les tolérances nommées (ARCH-010), `walls(source)` (tronçons droits, alignés fusionnés), `stiffness_centre(walls)` (A§9), `state(source)` (S, M, le contour, et pour chacun sa raison en `engine.Note`), `uses_centres(source)`, `check(source, fail)`, la citation de la méthode. Réalise REQ-002 à REQ-008, REQ-010, ARCH-001, ARCH-002, ARCH-004, ARCH-010, CON-001, CON-002. *Preuve* : nouveau `tests/test_plan_centres.py` — exemple A§10, les quatre valeurs du plan 12 × 8, rotation de 30°, repère retourné, parois inclinées contre le code de référence A§11 recopié dans le test, alignés, une seule direction, lignes concourantes, changement d'échelle ×1000 ; le module s'importe sans PySide6.
2. **Le contrat** — `calc/domains/plan.py` : version 1.8 et `version_of` composé, `check_texts` sur un tuple (et son appel de `fire.py:248`), `check_source` (mode sur H et W seulement, `outlines` d'au plus un, trois points au moins, sans `style`, refusé sur une coupe en élévation, `clt_power` ∈ {1,5 ; 2}, `print_centres` booléen), `ENTRY_LISTS["outline"]`, `copy_entry` qui refuse un contour, `_turn_quarter`, `apply_defaults`, `warnings(..., sections=)` (REQ-013, UI-006), `build_record` et `prepare` (le bloc `centres`, l'export en 1.5 où un plan en porte un, D-020) ; `calc/domains/plan_pages.py` (les deux écrivains par `version_of`) ; `schemas/plan-source.schema.json`, `schemas/plans.schema.json` ; `calc/validation.py` ; les appelants de `warnings`/`prepare`/`export` (`export_all.py`, `plan_pages.py`). Réalise REQ-001, REQ-009 (données), REQ-011 (données), REQ-013, UI-006, ARCH-003, ARCH-006, ARCH-007 (données), ARCH-009. *Preuve* : `test_plan_centres.py` (contrat, avertissements), `test_plan_texts.py` (1.6/1.7/1.8, composition, page tournée), `test_plan_documents.py`, `test_constants.py`, `test_plan_types_v0116.py`.
3. **Le dessin** — `calc/domains/plan_svg.py` : `render(..., centres=False)`, le bloc entre marqueurs `<!-- centres -->`, les symboles de S et de M et le trait du contour (D-014), trois lignes dans `LEGEND` avec leurs échantillons, `legend_items` qui ne les donne que si le plan les imprime et les marque (ARCH-008) ; `calc/i18n/strings.json` (`plan.legend.*`, trois langues) ; l'export passe la case du plan à `render`. Réalise REQ-012, UI-005 (dessin et légende), ARCH-008 (données), CON-004, CON-005. *Preuve* : `test_plan_style.py` — les empreintes figées inchangées, un plan à la case cochée porte le bloc, décochée il est identique à l'octet ; `test_i18n.py`.
4. **La fenêtre** — `plan_canvas_editing.py`, `plan_canvas_input.py`, `plan_canvas_view.py` : l'outil «Contour» (dessiné comme une surface, `add_outline` qui remplace l'ancien en une étape), la sélection `outline` (arête seule, glissement de sommet et de l'ensemble, suppression, contour de sélection), ses sommets dans `PlanSnapIndex`, le dessin avec `centres=True` ; `plan_tab_build.py` : le bouton de l'outil, la carte «Centre de rigidité et centre de masse» (`add_module(when="plan")` : la case, la puissance du CLT, l'état), le retrait du contour au passage en coupe ; `plan_properties.py` et `plan_tab_selection.py` : «Mode de construction» pour l'outil et pour la paroi ; `plan_tab_words.py` et `woodcore_gui_words.py` (`warn_plan_centres_*`), trois langues ; `plan_tab.py` et `plan_tab_selection.py` passent `sections=`. Le plan d'incendie n'a ni l'outil ni la carte. Réalise REQ-009, REQ-011, UI-001 à UI-004, ARCH-007, ARCH-011, D-021. *Preuve* : nouveau `tests/test_plan_centres_window.py` (hors écran : outil, arête seule, sommet déplacé, «Annuler», carte et ses raisons, mode de l'outil, passage en coupe) ; `test_panes.py` ; `test_fire_tab.py` ; `test_plan_edit_tools.py`.
5. **Typst** — `lib/calc-engine.typ` : `plan-figure(centres:)`, le filtre de `plan-legend`, `show-plan(centres:)`, `centres: false` dans les deux appels de `calc-block` ; `lib/document.typ` (`doc-plan`) ; `lib/sheet.typ` (`sheet-viewport`, et les commandes de légende selon Q-005) ; les `///` (la ligne `- centres (bool):` et deux exemples qui compilent) ; `calc/typst_objects_parse.py` (`SIGNATURES`, `SHEET_SIGNATURES`), `typst_objects_models.py`, `typst_objects_sheets.py` ; `calc/tools/object_panes_media.py`, `sheet_editor_options.py`, `sheet_editor.py`, `plan_command_builder.py`, `build_reference_calls.py` ; `calc/i18n/commands.json` (fr, de) ; les exemples figés. Réalise UI-005, UI-007, ARCH-008. *Preuve* : `test_commands.py`, `test_typst_objects.py`, `test_plan_command_builder.py`, `test_sheets.py` (le marqueur écrit par Python contre l'expression que Typst retire), et une compilation du rapport de `tests/projet-exemple/` avec un plan à la case cochée, dans les trois langues.
6. **La documentation** — `docs/domain/position-plans.md` (la méthode, ses hypothèses A§2 et ses limites A§12, les champs, la version 1.8, la phrase «ni matériau, ni section, ni charge» corrigée), `docs/ui/tab-plans.md`, `docs/domain/fire-plans.md` (pourquoi le plan d'incendie ne prend pas la fonction, règle 16), `docs/decisions.md` et `docs/decisions-index.md` (D-001, D-005, D-007, D-019, D-020), `docs/open-questions.md` (l'excentricité, la répartition des efforts, un M tiré des masses, les légendes seules si Q-005 les laisse de côté), `docs/typst/api-conventions.md`, `docs/architecture/layout.md` (le module nouveau), les lignes des deux fichiers de tests dans `docs/conventions/testing-catalogue*.md`, `CHANGELOG.md`, `website/content/{fr,de,en}/changes/0.118.0.md`. Réalise ARCH-004 (doc), ARCH-005. *Preuve* : `test_docs_coherence.py`, `test_site.py`.
7. **Vérification et fin** — les fichiers de tests qui gardent ce qui a changé, puis la vérification indépendante (`verify-requirements`), puis `finish` : la suite complète, un commit, la question «Pousser et fermer l'issue #54 ?».

**Ce qui ne sera pas fait** : l'excentricité entre M et S, les excentricités de la SIA 261 et la répartition des efforts (T4) ; un M tiré de masses ; un mode de construction sur les V ; plusieurs contours ou un contour à trous ; les coordonnées de S et de M en chiffres dans le rapport ; quoi que ce soit sur le plan de protection incendie ou sur une coupe en élévation.

## 15. Vérification

Vérification indépendante du 2026-10-13 (agent `requirements-verifier`, lecture seule), sur le commit `9943767` contre `3177a22` : la spécification, le différentiel, le code, les tests gardiens lancés par le vérificateur et des contrôles qu'il a écrits lui-même. **Premier passage : 33 ✅, 3 ⚠️, 0 ❌, aucune régression.**

| Élément | Verdict | Preuve |
|---|---|---|
| REQ-001 | ✅ | `plan_centres.py:50-59` ; `test_a_plans_file_states_the_modes…` ; sonde : une paroi W en CLT sélectionnée, la liste montre `clt` |
| REQ-002 | ✅ | `WALL_TYPES` `plan_centres.py:22` ; `test_only_the_bracing_walls_count` |
| REQ-003 | ✅ | `walls()` `:117-135` ; `test_a_wall_is_a_straight_run` ; sonde : un L égale deux éléments, trois points alignés donnent le même S en béton |
| REQ-004 | ✅ | recalculé par le vérificateur : (9,0 ; 4,0), (10,8 ; 4,0), (10,0633 ; 4,0), (11,5714 ; 4,0) ; avec échelle = sans échelle |
| REQ-005 | ✅ | `power_of` `:97`, `check` `:82` ; `test_one_construction_mode_and_no_default` |
| REQ-006 | ✅ | `_stiffness` `:162-180` : comptes par mode, numéros des parois sans mode |
| REQ-007 | ✅ | (a) A§10 : (9,0 ; 4,0) ; (b) rotation de 30° : même distance à l'origine ; (c) y retourné : (9,0 ; −4,0) ; (d) parois inclinées : égal au code A§11 à 10⁻¹⁵ près |
| REQ-008 | ✅ | notes `no_walls`, `one_direction`, `no_torsion` ; `test_no_stiffness_centre_is_said_and_never_raised` |
| REQ-009 | ✅ | `plan_canvas_outline.py` ; `test_the_tool_draws_one_outline…`, `test_a_corner_is_dragged…` ; `_turn_quarter` ; le double-clic n'est pas testé pour le contour |
| REQ-010 | ✅ | recalculé : rectangle (6,0 ; 4,0), L (3,875 ; 3,875) dans les deux sens ; aire contrôlée avant `centroid` |
| REQ-011 | ✅ | `applies()` `:38` ; `test_the_tool_has_its_button…`, `test_the_fire_protection_plan_has_none_of_it`, `test_fire_tab` (50) |
| REQ-012 | ✅ | export du projet exemple identique à l'octet entre `3177a22` et `9943767` (8 fichiers, `plans.json` 1.3, avertissements), contrôle du vérificateur ; case cochée : `test_the_report_prints_them…` |
| REQ-013 | ✅ | `plan_centres.warnings` `:232-247` ; deux tests |
| UI-001 | ✅ | sonde : outil W en CLT, deux parois `clt` ; béton puis «Annuler» : `clt` |
| UI-002 | ✅ | clics, Entrée, retour arrière testés ; trois langues ; écart de libellé consigné sous UI-002 |
| UI-003 | ⚠️ | écart de libellé consigné, **à confirmer par l'ingénieur** ; largeur du volet identique avec et sans la carte (mesure du vérificateur en anglais) ; `test_panes` |
| UI-004 | ✅ | `test_the_window_draws_s_and_m…` |
| UI-005 | ✅ | compilé en de, fr, en : lignes de légende présentes ; case décochée : aucune |
| UI-006 | ✅ | `warnings` `:238-241` ; `prepare` aboutit |
| UI-007 | ✅ | `///` et `- centres (bool):` ×3, `commands.json` en/fr/de ×3, `centres: false` ×2 dans `calc-block` ; `test_commands` (34), `test_typst_objects` (56), `test_sheets` (22) |
| ARCH-001 | ✅ | `plan_centres`, `plan`, `plan_svg` importés avec PySide6 bloqué ; aucune formule A§9 dans `calc/tools/` |
| ARCH-002 | ✅ | aucun champ pour S ou M dans le schéma de source |
| ARCH-003 | ✅ | `test_the_versions_nest`, `test_plan_style` (20) ; réserve (a) ci-dessous, corrigée |
| ARCH-004 | ✅ | `POWERS` à `plan_centres.py:25` seulement ; méthode citée dans le code, l'export et la doc |
| ARCH-005 | ✅ | quatre décisions, phrase corrigée, `fire-plans.md` ; `test_docs_coherence` |
| ARCH-006 | ✅ | `plan.py:132-137`, `plan_pages.py:68` ; `test_a_page_turns…` |
| ARCH-007 | ✅ | `check` `:60-85`, `hit_outline`, `SINGLE_ENTRIES` |
| ARCH-008 | ✅ | la marque `centres`, le filtre de `plan-legend` ; marqueur Python contre expression Typst |
| ARCH-009 | ⚠️ | les cinq appelants passent `sections` ; au premier passage aucun test ne gardait les appelants eux-mêmes — test ajouté, voir second passage |
| ARCH-010 | ✅ | essai ×1000 et ×0,001 : même S ; 0,01° d'écart : une seule direction |
| ARCH-011 | ✅ | `test_every_reason_has_its_one_sentence…` ; `test_i18n` (22) |
| CON-001 à CON-005 | ✅ | document cité, repère retourné vérifié, trois langues, export inchangé, SVG lu par QtSvg et par Typst |
| Documentation | ⚠️ | faite ; réserves (b) et (c) |
| Tests | ⚠️ | réserve (d) |

**Réserves du premier passage et suites.**
- **(a)** Supprimer le contour laissait `"outlines": []` dans le fichier. → Corrigé : `delete_selection` retire la clé, `save` aussi ; tenu par `test_a_corner_is_dragged…`.
- **(b)** Aucun exemple `///` n'illustre `centres:`. → **Laissé, à dire à l'ingénieur** : un exemple demande sa page figée (`test_every_example_has_a_committed_page`), et les données figées n'ont aucun plan qui imprime ses centres — la page serait celle du plan sans l'argument ; chaque commande garde ses exemples, qui compilent.
- **(c)** Le code et la doc citent cette spécification dans `completed/` alors qu'elle est dans `active/`. → Résolu au déplacement, quand UI-003 sera confirmé.
- **(d)** Les deux échecs dits antérieurs à la tâche n'avaient pas été contrôlés par le vérificateur. → Second passage.
- **ARCH-009** → test `test_the_exports_that_read_the_project_hand_its_positions_sections_to_the_plans` (par `plan_pages.export_drawings` et `export_all.run`).
- **Hors périmètre (§8)** : rien d'implémenté ; un ajout hors liste, dit au CHANGELOG : `plan_pages._write_fire` écrit `fire.version_of`, ce qui répare aussi la rotation de page d'un plan d'incendie qui porte un texte.

**Second passage (2026-10-13, même vérificateur, sur l'arbre de travail au-dessus de `9943767`) : ARCH-003 ✅, ARCH-009 ✅, «Tests» ✅.**
- **(a)** `plan_canvas_editing.py:323-324` et `plan_tab.py:294-295` ; sonde : dessiner un contour, le supprimer, enregistrer — le fichier est identique à celui d'avant le dessin, en 1.6. Reste : aucun test ne garde le retrait dans `save` (seul le chemin de suppression l'est).
- **ARCH-009** : le test passe réellement par `plan_pages.export_drawings` puis `export_all.run` ; par mutation, il échoue dès que l'un des deux cesse de transmettre `sections`. Reste relu seulement : `plan_tab.py:278` et `:420`. Dans le dossier OneDrive ce test s'arrête sur un «Accès refusé» sous `tests/.tmp` ; il passe sur la copie hors OneDrive (32 passés).
- **(d)** Sur un checkout propre de `3177a22`, `test_links.test_a_project_without_a_link_exports_its_checks_and_models_as_before` et `test_site.test_no_manifest_is_written_before_an_installer_is` échouent avec les mêmes messages et les mêmes comptes que sur l'arbre de la tâche : ils ne dépendent pas du changement.
- Régressions : `test_plan_edit_tools` 14 passés, `test_plan_centres` 32 passés hors OneDrive.

**Bilan des deux passages : 35 ✅, 2 ⚠️, 0 ❌.** UI-003 attend la confirmation de l'ingénieur sur le titre court de la carte ; «Documentation» garde la réserve (b), laissée et dite, et la réserve (c), qui tombe au déplacement de ce fichier dans `completed/`.

**Clôture (2026-10-14).** L'ingénieur, à qui les deux ⚠️ avaient été présentés avec leurs options, a demandé «règle les problème et fait un merge request» : ils sont **gardés comme écarts**, dits ici et à lui, et réversibles.
- **UI-003** : le titre court «Centres S et M» et la case «Imprimer dans le rapport» restent — c'est la forme qui tient le critère d'UI-003 (le titre long faisait passer la largeur minimale du volet de 495 à 599 px en français) ; les deux lignes de la carte disent «Centre de rigidité S» et «Centre de masse M» en toutes lettres.
- **Documentation, réserve (b)** : aucun exemple figé n'illustre `centres:` ; la ligne `- centres (bool):` est dans les trois `///` et ses traductions dans `commands.json`. Un exemple demanderait des données figées où un plan imprime ses centres, donc un `build_examples.py --freeze`, que le projet réserve à un acte délibéré.
- **Réserve (c)** : levée par le déplacement de ce fichier dans `completed/`.

## 16. Journal d'avancement

| Date | Statut | Fait / reste |
|---|---|---|
| 2026-10-13 | draft | spécification extraite de l'issue #54 : 12 REQ, 6 UI, 5 ARCH, 5 CON, 14 décisions (8 de la source, 6 par défaut), 4 questions ; reste : poser Q-001 à Q-004 |
| 2026-10-13 | clarification | Q-001 à Q-004 posées à l'ingénieur ; reste : consigner les réponses, puis la revue d'architecture |
| 2026-10-13 | specified | réponses consignées (les quatre options recommandées) : D-015 à D-018, REQ-013 et UI-007 ajoutés ; reste : revue d'architecture, plan, approbation |
| 2026-10-13 | reviewed | revue d'architecture : APPROUVER AVEC RÉSERVES, dix risques (un bloquant : les versions) ; ARCH-006 à ARCH-011, D-019 à D-021 et Q-005 ajoutés ; plan d'implémentation en sept étapes écrit ; reste : l'approbation de l'ingénieur |
| 2026-10-13 | approved | «Approuver et implémenter» ; Q-005 : trois commandes (D-022) ; reste : les sept étapes du §14 |
| 2026-10-13 | implementation | étape 1 faite : `calc/domains/plan_centres.py` et `tests/test_plan_centres.py` (REQ-002 à REQ-008, REQ-010, ARCH-001, ARCH-002, ARCH-004, ARCH-010) |
| 2026-10-13 | implementation | étape 2 faite, hors appelants de la fenêtre (étape 4) : `plan.py` (1.8, `version_of`, `check_source`, `ENTRY_LISTS`, `apply_defaults`, `warnings(sections=)`, `build_record`, `prepare`, `export`), `plan_pages.py`, `export_all.py`, `positions_store.section_types`, les deux schémas (REQ-001, REQ-009 et REQ-011 côté données, REQ-013, UI-006, ARCH-003, ARCH-006, ARCH-007 côté données, ARCH-009 côté export) ; 16 tests verts, `test_plan_texts`, `test_plan_style`, `test_plan_types_v0116`, `test_constants` verts |
| 2026-10-13 | implementation | étape 3 faite : `plan_svg.py` (`render(centres=)`, marqueurs `<!-- centres -->`, symboles de S et de M, trait du contour, trois lignes de légende marquées), `calc/i18n/strings.json` (`plan.legend.*` ×3), l'export passe la case du plan (REQ-012, UI-005 côté Python, ARCH-008 côté données, CON-004, CON-005) ; 18 tests verts, empreintes figées de `test_plan_style` inchangées, `test_i18n` et `test_plan_overlay_v0116` verts ; reste : étapes 4 à 7 |
| 2026-10-13 | implementation | étape 4 faite : nouveaux `calc/tools/plan_canvas_outline.py` (outil, arête seule, sommet, déplacement) et `plan_centres_card.py` (carte, liste «Mode de construction») ; accroches dans `plan_canvas_editing.py`, `plan_canvas_input.py`, `plan_canvas_view.py` (`centres=True`), `plan_tab_build.py`, `plan_tab_selection.py`, `plan_properties.py`, `plan_tab.py` (`sections=`) ; mots ×3 dans `plan_tab_words.py` et `woodcore_gui_words.py` (`warn_plan_centres_*`, `warn_plan_construction_*`) ; `plan_centres.hit_outline` (REQ-009, REQ-011, UI-001 à UI-004, ARCH-007, ARCH-009 côté fenêtre, ARCH-011, D-021). **Écarts à signaler** : la carte s'intitule «Centres S et M» et sa case «Imprimer dans le rapport» (le titre long en faisait la carte la plus large et élargissait le volet : 599 px contre 495 mesurés en français, contre le critère d'UI-003) ; les messages sous le plan contrôlent désormais le brouillon à la version où il sera écrit (un texte posé sur un plan lu en 1.6 affichait «holds a text at schema_version '1.6'» jusqu'à l'enregistrement) ; `tests/test_plan_panes_v0116.py` : la liste attendue des cartes reçoit la nouvelle. Nouveau `tests/test_plan_centres_window.py` (9 tests) ; `test_panes`, `test_plan_panes_v0116`, `test_plan_tabs_v0117`, `test_plan_edit_tools`, `test_plan_canvas_rework`, `test_plan_tracking`, `test_window`, `test_module_imports` verts ; reste : étapes 5 à 7 |
| 2026-10-13 | implementation | étape 5 faite : `lib/calc-engine.typ` (`plan-figure(centres:)`, filtre de `plan-legend`, `show-plan(centres:)` et son `///`, `centres: false` dans les deux appels de `calc-block`), `lib/document.typ` (`doc-plan`), `lib/sheet.typ` (`sheet-viewport`) ; `calc/typst_objects_parse.py` (signatures), `typst_objects_models.py` et `typst_objects_sheets.py` (`set_centres`), `object_panes_media.py`, `sheet_editor_options.py`, `sheet_editor.py`, `plan_command_builder.py` (case, masquée pour le plan d'incendie), `build_reference_calls.py`, trois tables de mots (un seul libellé, tenu égal par un test), `calc/i18n/commands.json` (en, fr, de ×3 commandes) (UI-005, UI-007, ARCH-008). Pas de nouvel exemple figé : chaque commande garde ses exemples, qui compilent avec la nouvelle signature (`test_commands` vert après `refresh_engine`). Tests : rapport compilé dans les trois langues, `centres: false`, `doc-plan`, détail de `calc-block`, plan à la case décochée (`test_plan_centres.py`, 20 tests) ; marqueur Python contre expression Typst ; `test_sheets.py` (vue en plan d'une feuille) ; `test_typst_objects`, `test_plan_command_builder` verts. **Constat hors tâche** : dans le dossier OneDrive, `test_structure_tab` échoue 4 fois (accès refusé, fichier modifié non détecté) ; sur un arbre propre hors OneDrive il passe 72/72 avec et sans les changements de cette tâche. Reste : étapes 6 et 7 |
| 2026-10-13 | testing | étape 6 faite : `docs/domain/position-plans.md` (la méthode, ses hypothèses et ses limites, les champs, les versions ; la phrase «ni matériau, ni section, ni charge» corrigée), `docs/ui/tab-plans.md`, `docs/domain/fire-plans.md` (pourquoi le plan d'incendie ne prend pas la fonction), `docs/decisions.md` (quatre décisions) et `docs/decisions-index.md`, `docs/open-questions.md`, `docs/typst/api-conventions.md` (signatures de `show-plan` et `doc-plan` mises à jour, `dimensions:` et `lengths:` compris, qui y manquaient depuis l'issue #9), `docs/architecture/layout.md`, `docs/README.md`, les deux catalogues de tests, `CHANGELOG.md`, `website/content/{fr,de,en}/changes/0.118.0.md` (ARCH-004 côté doc, ARCH-005) ; `test_docs_coherence` vert. **Constat hors tâche** : `test_site.test_no_manifest_is_written_before_an_installer_is` échoue sur un arbre propre de HEAD (3177a22) sans aucun changement — il suppose la 0.117.0 non publiée. Reste : étape 7 (vérification indépendante, puis `finish`) |
| 2026-10-13 | testing | tests liés aux modules modifiés (`run_tests.py --related`, 135 fichiers, arbre de travail hors OneDrive) : **2588 passés, 11 ignorés, 2 échecs en 851 s**. Les deux échecs existent à l'identique sur un arbre propre de HEAD (3177a22), sans cette tâche : `test_links.test_a_project_without_a_link_exports_its_checks_and_models_as_before` («checks.json changed although nothing follows a variable») et `test_site.test_no_manifest_is_written_before_an_installer_is`. Après cette série : «Copier» refusé au premier clic sur le contour, sans étape d'«Annuler» vide (`plan_canvas_edit.click`, `single_selected`) et un test des phrases dans les trois langues ; `test_plan_centres_window` (11) et `test_plan_edit_tools` (14) verts. **À la demande de l'ingénieur («commit puis push et faire une merge request»), commit, push et pull request avant la vérification indépendante.** Reste : la vérification (§15), le déplacement de ce fichier dans `completed/` (le code et la doc le citent déjà à cet endroit) |
| 2026-10-13 | verification | commit `9943767` poussé sur `origin/gian-0.117`, pull request When-I-hit-the-wall/Woodcore#55 vers `master` (six fichiers en conflit avec les trois commits que `master` a reçus depuis). Vérification indépendante, premier passage : 33 ✅, 3 ⚠️, 0 ❌ ; corrections : la clé `outlines` retirée quand le contour est supprimé (`delete_selection`, `save`), un test qui garde les appelants de l'export (`plan_pages.export_drawings`, `export_all.run`), l'écart de libellé du bouton «Contour» consigné sous UI-002. Second passage : ARCH-003, ARCH-009 et «Tests» ✅. §11 coché sauf UI-003 et «Documentation». **Reste** : la réponse de l'ingénieur sur le titre de la carte (UI-003) et sur la fusion de `master` ; puis le commit de ces corrections poussé, la suite complète, et ce fichier dans `completed/` |
| 2026-10-14 | verification | «règle les problème et fait un merge request» (l'ingénieur) : `origin/master` fusionné deux fois dans `gian-0.117` (`73c414d` : résistance au feu, audit des classeurs de contrôle, acier lot 1 ; `3a1066a` : niveau −1 des charges et des verdicts, `master` ayant avancé entre-temps), conflits résolus en gardant les deux côtés (CHANGELOG, `docs/open-questions.md`, `docs/decisions.md`, `tests/test_connectors.py`, les pages 0.118.0) ; `test_docs_coherence`, `test_plan_centres`, `test_plan_centres_window`, `test_connectors`, `test_commands`, `test_i18n`, `test_constants` verts sur l'arbre fusionné |
| 2026-10-14 | completed | les deux ⚠️ gardés comme écarts (§15, clôture) ; §11 coché ; fichier déplacé dans `docs/requirements/completed/` ; reste : la suite complète, le push et la pull request mise à jour |

## Annexe A — document de contexte de l'issue #54 (T15), mot pour mot

> # Centre de rigidité d'un étage — calcul mécanique général
>
> Document de contexte, rédigé le 12.10.2026 pour être donné tel quel à une autre discussion. Il explique comment trouver le centre de rigidité d'un étage de bâtiment contreventé par des parois, puis comment répartir une force horizontale sur ces parois en tenant compte de la torsion.
>
> **Statut.** Les sections 2 à 7 et 9 sont de la **mécanique générale** : elles ne viennent d'aucune norme. Seule la section 8 cite une norme (SIA 261:2020, chapitre 16), relue dans l'édition française. Aucune norme SIA ne donne la méthode de calcul du centre de rigidité : la SIA 261 l'utilise en le supposant connu, et la SIA 265:2021 ne le mentionne pas. L'exemple chiffré de la section 10 a été recalculé par le code de la section 11.
>
> ## 1. À quoi ça sert
>
> Une force horizontale (séisme, vent) qui passe par le **centre de rigidité S** d'un étage déplace le plancher en translation pure, sans le faire tourner. Si elle passe ailleurs, le plancher tourne aussi, et cette torsion charge davantage certaines parois. Le séisme agit au **centre de masse M** ; l'écart entre M et S est l'excentricité, qui crée la torsion.
>
> ## 2. Hypothèses
>
> 1. Le plancher est **rigide dans son plan** (diaphragme rigide) : il se déplace comme un corps rigide, avec trois degrés de liberté par étage (deux translations, une rotation).
> 2. Les parois sont **élastiques linéaires**.
> 3. Une paroi ne reprend des efforts que **dans son propre plan** ; sa rigidité hors plan et sa rigidité propre en torsion sont négligées.
> 4. Le calcul se fait **étage par étage**.
>
> Si le plancher est souple (hypothèse 1 non tenue), la notion de centre de rigidité ne s'applique pas : les forces se répartissent plutôt selon les surfaces d'influence.
>
> ## 3. Conventions
>
> - Repère : origine O quelconque, axes x et y dans le plan de l'étage.
> - Rotation θ positive dans le sens **anti-horaire** (de x vers y). Un moment est positif dans le même sens.
> - Une paroi « en direction y » est une paroi dont le plan est parallèle à y : elle reprend des forces en y et sa position est donnée par son abscisse `x_i`. Une paroi « en direction x » reprend des forces en x et sa position est son ordonnée `y_j`.
> - `k_y,i` : rigidité de la paroi i en direction y ; `k_x,j` : rigidité de la paroi j en direction x.
> - `V` : effort repris par une paroi, positif dans le sens de l'axe correspondant (+y ou +x). C'est la force que le plancher exerce sur la paroi.
> - Unités cohérentes. Avec les positions en m, les forces en kN et les rigidités en kN/mm, les déplacements sortent en mm, `K_θ` en kN·m²/mm et θ en mm/m (soit 10⁻³ rad).
>
> ## 4. Rigidité d'une paroi
>
> La rigidité d'une paroi est la force horizontale en tête qui produit un déplacement unitaire en tête :
>
> ```
> k = F / u
> ```
>
> Le déplacement `u` est la somme de toutes les déformations de la paroi, donc la rigidité est l'inverse de la somme des souplesses :
>
> ```
> k = 1 / (u_1/F + u_2/F + …)
> ```
>
> Pour une paroi pleine, homogène, encastrée à sa base (console de hauteur h), la mécanique donne la flexion plus le cisaillement :
>
> ```
> u = F·h³ / (3·E·I) + F·h / (G·A_s)        A_s = aire de cisaillement (A/1,2 pour une section rectangulaire)
> ```
>
> Pour une paroi en bois (ossature, panneaux), les contributions sont typiquement : le cisaillement du panneau, le glissement des moyens d'assemblage du panneau, le soulèvement des ancrages en traction, la compression perpendiculaire au fil de la lisse et l'allongement des montants. **Leurs formules dépendent du système constructif et ne sont pas reproduites ici** : il faut les prendre dans la littérature (documentation Lignum, fabricant) ou dans un calcul dédié.
>
> Deux simplifications courantes, chacune avec son domaine de validité :
>
> - **`k` proportionnel à la longueur `l` de la paroi** : acceptable quand toutes les parois ont la même composition et la même hauteur et que la déformation de cisaillement et d'assemblage domine (parois à ossature bois semblables, pas trop élancées).
> - **`k` proportionnel à `l³`** (à l'inertie) : quand la flexion domine (parois élancées en béton ou en maçonnerie).
>
> Seul le **rapport** entre les rigidités compte pour la position de S et pour la répartition des efforts. Les valeurs absolues ne comptent que pour les déplacements.
>
> ## 5. Centre de rigidité (parois parallèles aux axes)
>
> ```
> x_S = Σ (k_y,i · x_i) / Σ k_y,i
> y_S = Σ (k_x,j · y_j) / Σ k_x,j
> ```
>
> C'est le barycentre des rigidités : `x_S` se calcule avec les parois en direction y, `y_S` avec les parois en direction x.
>
> **D'où ça vient.** Si le plancher se déplace de `u` en direction y sans tourner, chaque paroi i reprend `k_y,i · u`. La résultante de ces efforts vaut `u · Σ k_y,i` et passe par l'abscisse où son moment égale la somme des moments : `x_S · Σ k_y,i = Σ k_y,i · x_i`. Une force appliquée exactement là produit donc cette translation pure.
>
> Il faut au moins des parois dans deux directions, et leurs lignes d'action ne doivent pas toutes passer par un même point, sinon l'étage n'a aucune rigidité en torsion.
>
> ## 6. Centre de masse et excentricité
>
> ```
> x_M = Σ (m_k · x_k) / Σ m_k
> y_M = Σ (m_k · y_k) / Σ m_k
> ```
>
> Les masses sont celles des charges permanentes et quasi permanentes de l'étage (SIA 261:2020, chiffres 16.5.2.3 et 16.5.2.4).
>
> ```
> e_x = x_M − x_S        (sert pour une action en direction y)
> e_y = y_M − y_S        (sert pour une action en direction x)
> ```
>
> L'excentricité qui compte est toujours celle mesurée **perpendiculairement** à la direction de l'action.
>
> ## 7. Rigidité en torsion et répartition des efforts
>
> Rigidité en torsion de l'étage autour de S :
>
> ```
> K_θ = Σ k_y,i · (x_i − x_S)² + Σ k_x,j · (y_j − y_S)²
> ```
>
> Pour une force `(F_x, F_y)` appliquée au point `(x_F, y_F)` :
>
> ```
> T_S   = F_y · (x_F − x_S) − F_x · (y_F − y_S)        moment de torsion autour de S
> u_x,S = F_x / Σ k_x,j                                 translation de S
> u_y,S = F_y / Σ k_y,i
> θ     = T_S / K_θ                                     rotation du plancher
> ```
>
> Efforts dans les parois (translation + torsion) :
>
> ```
> paroi i en direction y :   V_i = k_y,i · [ F_y / Σ k_y  +  T_S · (x_i − x_S) / K_θ ]
> paroi j en direction x :   V_j = k_x,j · [ F_x / Σ k_x  −  T_S · (y_j − y_S) / K_θ ]
> ```
>
> **Contrôles.** `Σ V_i = F_y`, `Σ V_j = F_x`, et `Σ V_i · (x_i − x_S) − Σ V_j · (y_j − y_S) = T_S`.
>
> Pour une action en y seule, les parois en direction x ne reprennent que de la torsion : elles travaillent par paires, en sens opposés.
>
> ## 8. Excentricités de dimensionnement (SIA 261:2020, chapitre 16)
>
> C'est la seule partie tirée d'une norme. Relue dans l'édition française, pages 73 et 74.
>
> **Méthode des forces de remplacement, chiffre 16.5.2.7, équations (43) et (44) :**
>
> ```
> e_d,sup = 1,5 · e + 0,05 · b
> e_d,inf = 0,5 · e − 0,05 · b
> ```
>
> `e` est l'excentricité, par rapport au centre de rigidité de l'étage considéré, de la résultante des forces de remplacement agissant sur les étages situés au-dessus. `b` est la largeur du bâtiment mesurée perpendiculairement à l'action sismique.
>
> **Méthode du spectre de réponse, chiffre 16.5.3.4, équations (45) et (46) :**
>
> ```
> e_d,sup = e + 0,05 · b
> e_d,inf = e − 0,05 · b
> ```
>
> Ici `e` est l'excentricité effective du centre de gravité des masses par rapport au centre de rigidité de l'étage, et `b` la largeur de l'étage perpendiculaire à l'action.
>
> **Mise en œuvre** (mon interprétation, pas le texte de la norme) :
>
> - Pour un bâtiment à plusieurs étages, la position de la résultante au-dessus de l'étage considéré est `x_R = Σ (F_d,j · x_M,j) / Σ F_d,j`, la somme portant sur les planchers situés au-dessus ; puis `e = |x_R − x_S|`.
> - Les deux excentricités se mesurent depuis S, du côté où se trouve la résultante. `e_d,inf` peut être négative quand `e` est petite : la force passe alors de l'autre côté de S.
> - On calcule la répartition de la section 7 pour **les deux** excentricités et pour **les deux** directions principales, et on retient pour chaque paroi l'effort le plus grand en valeur absolue.
>
> Le tableau 27 de la même norme (chiffre 16.4.1) demande par ailleurs de répartir les éléments de contreventement de la manière la plus symétrique possible en plan, ce qui revient à garder S proche de M.
>
> ## 9. Cas général : parois inclinées
>
> Chaque paroi i a une rigidité `k_i` le long de son plan, un angle `α_i` mesuré depuis l'axe x, et un point `(x_i, y_i)` quelconque sur sa ligne d'action. Son bras de levier signé par rapport à l'origine est :
>
> ```
> r_i = x_i · sin α_i − y_i · cos α_i
> ```
>
> Rigidités de l'étage :
>
> ```
> K_xx = Σ k_i · cos² α_i
> K_yy = Σ k_i · sin² α_i
> K_xy = Σ k_i · sin α_i · cos α_i
> K_xθ = Σ k_i · cos α_i · r_i
> K_yθ = Σ k_i · sin α_i · r_i
> ```
>
> Centre de rigidité :
>
> ```
> D   = K_xx · K_yy − K_xy²
> x_S = (K_xx · K_yθ − K_xy · K_xθ) / D
> y_S = (K_xy · K_yθ − K_yy · K_xθ) / D
> ```
>
> Rigidité en torsion autour de S, avec le bras de levier pris depuis S :
>
> ```
> r_i,S = (x_i − x_S) · sin α_i − (y_i − y_S) · cos α_i
> K_θ   = Σ k_i · r_i,S²
> ```
>
> Translation de S, rotation et effort de chaque paroi (positif dans le sens `(cos α_i, sin α_i)`) :
>
> ```
> u_x = (K_yy · F_x − K_xy · F_y) / D
> u_y = (K_xx · F_y − K_xy · F_x) / D
> θ   = T_S / K_θ                                  T_S comme à la section 7
> V_i = k_i · (u_x · cos α_i + u_y · sin α_i + θ · r_i,S)
> ```
>
> Avec des parois parallèles aux axes (α = 0° ou 90°), `K_xy = 0` et on retrouve exactement les formules des sections 5 et 7.
>
> ## 10. Exemple chiffré (vérifié par le code de la section 11)
>
> Plan rectangulaire de 12 m (en x) par 8 m (en y). Centre de masse M = (6,0 ; 4,0).
>
> | Paroi | Direction | Position | Rigidité |
> |---|---|---|---|
> | W1 | y | x = 0 m | 10 kN/mm |
> | W2 | y | x = 12 m | 30 kN/mm |
> | W3 | x | y = 0 m | 20 kN/mm |
> | W4 | x | y = 8 m | 20 kN/mm |
>
> **Centre de rigidité.**
>
> ```
> x_S = (10·0 + 30·12) / (10 + 30) = 9,0 m
> y_S = (20·0 + 20·8) / (20 + 20) = 4,0 m
> ```
>
> **Excentricité.** `e_x = 6,0 − 9,0 = −3,0 m`, soit `e = 3,0 m` ; `e_y = 0`.
>
> **Rigidité en torsion.**
>
> ```
> K_θ = 10·(0−9)² + 30·(12−9)² + 20·(0−4)² + 20·(8−4)² = 810 + 270 + 320 + 320 = 1720 kN·m²/mm
> ```
>
> **Force F_y = 100 kN appliquée en M** (sans majoration d'excentricité).
>
> ```
> T_S   = 100 · (6 − 9) = −300 kNm
> u_y,S = 100 / 40 = 2,5 mm
> θ     = −300 / 1720 = −0,17442 mm/m
> W1 = 10 · [2,5 + (−0,17442)·(0 − 9)]  = 40,70 kN
> W2 = 30 · [2,5 + (−0,17442)·(12 − 9)] = 59,30 kN
> W3 = 20 · [0 − (−0,17442)·(0 − 4)]    = −13,95 kN
> W4 = 20 · [0 − (−0,17442)·(8 − 4)]    = +13,95 kN
> ```
>
> Contrôles : `40,70 + 59,30 = 100` ; moment autour de S : `40,70·(−9) + 59,30·3 − [(−13,95)·(−4) + 13,95·4] = −300 kNm`.
>
> **Avec les excentricités de la SIA 261:2020, chiffre 16.5.2.7** (un seul étage, action en y, donc b = 12 m) :
>
> ```
> e_d,sup = 1,5·3,0 + 0,05·12 = 5,1 m   →   x_F = 9,0 − 5,1 = 3,9 m
> e_d,inf = 0,5·3,0 − 0,05·12 = 0,9 m   →   x_F = 9,0 − 0,9 = 8,1 m
> ```
>
> | Cas | T_S | W1 | W2 | W3 | W4 |
> |---|---|---|---|---|---|
> | Force en M (e = 3,0 m) | −300 kNm | 40,70 | 59,30 | −13,95 | +13,95 |
> | e_d,sup = 5,1 m | −510 kNm | **51,69** | 48,31 | **−23,72** | **+23,72** |
> | e_d,inf = 0,9 m | −90 kNm | 29,71 | **70,29** | −4,19 | +4,19 |
>
> Efforts en kN ; en gras, la valeur déterminante de chaque paroi pour l'action en y. La paroi souple éloignée (W1) est gouvernée par la grande excentricité, la paroi rigide proche de S (W2) par la petite.
>
> ## 11. Code Python de référence
>
> Implémente la section 9 (cas général). Une paroi est `(nom, x, y, alpha_en_degrés, k)`.
>
> ```python
> from math import cos, radians, sin
>
>
> def centre_rigidite(parois):
>     kxx = sum(k * cos(radians(a)) ** 2 for _, _, _, a, k in parois)
>     kyy = sum(k * sin(radians(a)) ** 2 for _, _, _, a, k in parois)
>     kxy = sum(k * sin(radians(a)) * cos(radians(a)) for _, _, _, a, k in parois)
>     kxt = sum(k * cos(radians(a)) * (x * sin(radians(a)) - y * cos(radians(a))) for _, x, y, a, k in parois)
>     kyt = sum(k * sin(radians(a)) * (x * sin(radians(a)) - y * cos(radians(a))) for _, x, y, a, k in parois)
>     det = kxx * kyy - kxy ** 2
>     if abs(det) < 1e-12:
>         raise ValueError("système instable : il faut des parois dans au moins deux directions")
>     xs = (kxx * kyt - kxy * kxt) / det
>     ys = (kxy * kyt - kyy * kxt) / det
>     return xs, ys, (kxx, kyy, kxy)
>
>
> def repartition(parois, fx, fy, xf, yf):
>     """Force (fx, fy) appliquée au point (xf, yf) : centre de rigidité, K_theta, déplacements et effort de chaque paroi."""
>     xs, ys, (kxx, kyy, kxy) = centre_rigidite(parois)
>     bras = {n: (x - xs) * sin(radians(a)) - (y - ys) * cos(radians(a)) for n, x, y, a, _ in parois}
>     k_theta = sum(k * bras[n] ** 2 for n, _, _, _, k in parois)
>     if k_theta < 1e-12:
>         raise ValueError("aucune rigidité en torsion : toutes les lignes d'action passent par un même point")
>     det = kxx * kyy - kxy ** 2
>     ux = (kyy * fx - kxy * fy) / det
>     uy = (kxx * fy - kxy * fx) / det
>     moment = fy * (xf - xs) - fx * (yf - ys)          # autour de S, positif en sens anti-horaire
>     theta = moment / k_theta
>     efforts = {n: k * (ux * cos(radians(a)) + uy * sin(radians(a)) + theta * bras[n]) for n, _, _, a, k in parois}
>     return {"S": (xs, ys), "K_theta": k_theta, "u": (ux, uy), "theta": theta, "T_S": moment, "V": efforts}
>
>
> # L'exemple de la section 10 : m, kN, kN/mm
> parois = [("W1", 0.0, 4.0, 90, 10.0), ("W2", 12.0, 4.0, 90, 30.0), ("W3", 6.0, 0.0, 0, 20.0), ("W4", 6.0, 8.0, 0, 20.0)]
> print(repartition(parois, 0.0, 100.0, 6.0, 4.0))
> # S = (9.0, 4.0), K_theta = 1720, theta = -0.17442, V = W1 40.70, W2 59.30, W3 -13.95, W4 13.95
> ```
>
> Contrôle supplémentaire effectué : en faisant tourner tout le plan de 30° autour de l'origine, le centre de rigidité calculé tourne lui aussi de 30° et reste à la même distance de l'origine.
>
> ## 12. Limites
>
> - **Plancher souple** : la méthode ne s'applique pas (section 2).
> - **Plusieurs étages** : le calcul étage par étage est une approximation. Pour un bâtiment à plusieurs étages, le centre de rigidité n'est en général pas un point unique indépendant du chargement ; un modèle spatial est alors plus juste.
> - **Comportement non linéaire** : la rigidité d'une paroi en bois dépend du niveau de charge (glissement des assemblages). Le résultat dépend de la rigidité retenue.
> - **Rigidités des parois** : c'est la donnée d'entrée la plus incertaine. Une étude de sensibilité (par exemple ±30 % sur les parois dont la rigidité est mal connue) montre vite si la position de S est robuste.
> - **Noyaux et parois en L ou en U** : leur rigidité propre en torsion et le couplage entre leurs ailes ne sont pas pris en compte par ce modèle de parois planes indépendantes.
>
> ## 13. Sources
>
> | Élément | Source | Vérifié |
> |---|---|---|
> | Sections 2 à 7 et 9 | Mécanique générale (diaphragme rigide, ressorts élastiques) ; aucune norme | Formules contrôlées par l'exemple, les trois contrôles d'équilibre et l'essai de rotation du plan |
> | Équations (43) à (46), définition de `e` et de `b` | SIA 261:2020, édition française, chiffres 16.5.2.7 et 16.5.3.4, p. 73–74 | Relu dans le PDF |
> | Masses à considérer | SIA 261:2020, chiffres 16.5.2.3 et 16.5.2.4, p. 73 | Relu dans le PDF |
> | Disposition symétrique | SIA 261:2020, tableau 27, chiffre 16.4.1, p. 71 | Relu dans le PDF |
> | Absence du terme dans la SIA 265 | SIA 265:2021, édition française : aucune occurrence de « centre de rigidité » | Recherche plein texte |
> | Rigidité des parois en bois | Non traitée ici. Pistes : cours « Aussteifung von Holzgebäuden – Entwurfsgrundlagen » (M. Geiser, BFH), dont la p. 46 traite de la position du centre de rigidité et renvoie au Lignatec 32/2020 ; documentation Lignum sur les bâtiments en bois parasismiques | Cours : page repérée. Documentation Lignum : citée de mémoire, non vérifiée |
