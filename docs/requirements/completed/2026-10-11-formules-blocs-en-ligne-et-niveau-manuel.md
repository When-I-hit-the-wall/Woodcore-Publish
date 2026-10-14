---
id: 2026-10-11-formules-blocs-en-ligne-et-niveau-manuel
titre: Onglet Formules — blocs réduits et en ligne ; niveau −1 en colonnes et boutons 0|1|2|3
status: completed
cree: 2026-10-11
mis_a_jour: 2026-10-11
source: issues GitHub #40 et #41 (dictée du 11.10.2026, triée par /issue)
docs: [docs/ui/tab-formulas.md, docs/typst/formulas.md, docs/ui/window.md, docs/ui/tab-member-checks.md]
---

# Onglet Formules — blocs réduits et en ligne ; niveau −1 en colonnes et boutons — Spécification

## 1. Objectif

Dans l'onglet «Formules», l'ingénieur veut voir le volet du milieu comme Typst imprimera le domaine : chaque commande validée réduite à une pastille (variable affichée, valeur, unité), posée **dans** le texte quand la commande s'imprime en ligne et seule sur sa ligne quand elle s'imprime à part, et qu'il peut déplacer par glisser-déposer. La saisie d'un `var` commence par ce qu'il voit (la variable affichée), la clé de calcul suivant d'elle-même. Dans le mode «Affichage», la sélection manuelle du niveau −1 doit tenir en moins de place et se régler en un clic : plusieurs variables par ligne, et un sélecteur segmenté `0 | 1 | 2 | 3` à la place de la case et du menu déroulant.

## 2. Source

Dictée du 11.10.2026, mot pour mot (issue #40 pour T1–T8, issue #41 pour T9–T14).

> **T1** — « dans l'onglet formule, dans le volet du milieu, lorsqu'une commande est validée, elle doit s'afficher de manière réduite avec le nom de la variable, la valeur et l'unité. »
>
> **T2** — « Et si la commande autorise dans dipst l'affichage en ligne, grâce à l'argument, eh bien cette commande doit également s'afficher en ligne dans le volet central. »
>
> **T3** — « Donc il doit pouvoir y avoir du texte à gauche, puis ce bloc par un petit qui est en fait un petit rectangle au coin arrondi et à l'intérieur le nom de la variable affichée, la valeur et l'unité, et à gauche à nouveau du texte. »
>
> **T4** — « Lorsque l'argument de la commande passe à, de manière à ce que la commande s'affiche toute seule sur sa ligne dans dipst, et bien automatiquement ce bloc doit se trouver toute seule sur sa ligne. »
>
> **T5** — « Il doit être possible de drag and drop les blocs dans le texte afin de les déplacer. »
>
> **T6** — « Lorsque l'on est dans l'édition bloc, première case que l'on doit pouvoir remplir, c'est la variable affichée, et en remplissant une valeur dedans, la prochaine case qui est la variable enregistrée pour les calculs, donc la variable calculée, doit s'écrire automatiquement. »
>
> **T7** — « Et il doit être possible avec tab de passer dans cette cellule et de l'écraser manuellement. »
>
> **T8** — « Et ensuite, dans la cellule d'après, eh bien c'est la valeur et ensuite l'unité. »
>
> **T9** — « Pour les onglets qui possèdent dans le mode d'affichage, dans le volet de droite, pour le level, un level moins 1, donc un level manuel, dans le listing de toutes les variables à activer ou désactiver et à choisir le niveau pour l'affichage dans TYPST, ce n'est pas assez ergonomique. »
>
> **T10** — « En fonction de la largeur du volet, il doit y avoir plusieurs variables qui peuvent s'écrire les unes à côté des autres et pas uniquement une par ligne. »
>
> **T11** — « De plus, le choix du niveau doit se faire non pas par un menu déroulant, mais par quatre petits boutons côte à côte fusionnés ensemble. Donc visuellement c'est comme un unique rectangle, mais dedans c'est écrit 0, séparation 1, séparation 2, séparation 3. »
>
> **T12** — « Et en cliquant sur le numéro qui nous intéresse, eh bien visuellement, ce numéro est légèrement mis en valeur afin qu'on sache quel niveau on a choisi. »
>
> **T13** — « Cela signifie également que la case à cocher n'est plus nécessaire. On peut l'enlever. Il suffit d'avoir ces quatre boutons fusionnés ensemble en cliquant sur le 0 pour avoir le comportement équivalent. »
>
> **Réponses du tri (/issue, 11.10.2026)** :
>
> **T14** — Question 1 « quelles commandes validées prennent la forme réduite ? » → « Toutes » : `var`, `val`, `var-unit`, `eq` et `verify` ; l'`#eq` perd dans le volet son affichage sur deux lignes, visible au double-clic et dans «Affichage».
>
> **T15** — Question 2 « une variable verrouillée (issue #39) » → « 0 masqué » : seuls `1 | 2 | 3`.

## 3. Exigences fonctionnelles

### REQ-001 — Un bloc validé est une pastille
- **Exigence** : Woodcore doit afficher toute commande validée du volet du milieu (`var`, `val`, `var-unit`, `eq`, `verify`) comme une pastille — un petit rectangle aux coins arrondis — contenant la variable affichée (en mathématiques), `=`, la valeur et l'unité ; pour `verify`, la relation, ses deux valeurs et ✔/✘ ; pour une commande en erreur, la variable affichée et la raison, en couleur `danger`. Les lettres et les chiffres d'un `eq` ne sont plus montrés dans le volet (double-clic, «Affichage»).
- **Source** : T1, T3, T14
- **Priorité** : doit
- **Critère d'acceptation** : `tests/test_formula_tab.py` — un domaine `var F = 5 kN`, `eq M = F * 2 m`, `verify M <= 20 kNm` ouvert : chaque commande est une pastille dont le texte (sans balises) est `F = 5 kN`, `M = 10 kNm`, et pour le `verify` contient `✔` ; aucun `<br>` dans le HTML d'une pastille d'`eq`.

### REQ-002 — En ligne ou seule sur sa ligne, selon l'argument `note:`
- **Exigence** : Woodcore doit poser la pastille **dans** le texte, entre le texte qui la précède et celui qui la suit, quand la commande s'imprime en ligne dans Typst (`var`, `var-unit`, `eq` sans `note:` ou avec `note: "footnote"`, et toujours `val` — son `note: "line"` reste dans la phrase — et `verify`, sans `note:`, que Typst imprime aussi dans la phrase, « Avant 2 ⩽ 3 ✔ Après », constaté par le test compilé), et **seule sur sa ligne** quand elle s'imprime à part (`var`, `var-unit`, `eq` avec `note: "line"`). Ce placement est **dérivé** de l'argument : changer `note:` dans «Affichage» déplace la pastille au prochain affichage du volet, sans rien réécrire d'autre dans le fichier.
- **Source** : T2, T3, T4
- **Priorité** : doit
- **Critère d'acceptation** : test — un domaine « Kraft », `var F`, « und danach » : la pastille de `F` est sur la même ligne visuelle que « Kraft » et « und danach » ; `note: "line"` écrit sur ce `var` : la pastille est seule sur sa ligne, le texte avant et après sur les lignes voisines ; le corps du fichier ne diffère que par `note: "line"`.

### REQ-003 — Le volet du milieu suit le source et le fichier se relit tel quel
- **Exigence** : Woodcore doit garder le fichier `Formules/<id>.typ` dans sa forme actuelle — une commande seule sur sa ligne, le texte de l'ingénieur entre elles — et l'afficher de façon que ce que montre le volet soit ce que Typst imprime : un texte et une pastille en ligne qui se suivent dans le fichier sans ligne vide sont sur la même ligne du volet ; une ligne vide (paragraphe, conservée à la lecture, D-05), un titre `= …` ou une pastille seule sur sa ligne coupent la ligne ; un retour à la ligne tapé à côté d'une pastille en ligne écrit une ligne vide. Ce que le volet écrit se relit en les mêmes éléments (`formula_domain.check_body`).
- **Source** : T2, T3 ; inféré (principe « une seule source de vérité », docs/architecture/principles.md ; D-06 du fichier de domaine, docs/typst/formulas.md)
- **Priorité** : doit
- **Critère d'acceptation** : test aller-retour — un domaine écrit par le volet (texte, pastille en ligne au milieu d'une phrase, titre, pastille seule) se relit en les mêmes éléments ; un fichier existant de `tests/projet-exemple/` s'ouvre et se réécrit sans changement d'octet (hors `hand_edited`).

### REQ-004 — Déplacer une pastille par glisser-déposer
- **Exigence** : Woodcore doit permettre de saisir une pastille à la souris et de la déposer ailleurs dans le texte du domaine ; elle quitte sa place et prend celle du dépôt, le fichier est écrit aussitôt, les résultats recalculés (une variable déposée avant ce dont elle dépend est refusée avec la raison du calcul, comme à la validation, et revient à sa place). Un dépôt là où le fichier ne se relirait pas (dans une équation `$…$`, un bloc brut ou un appel — une chaîne n'existe que dans un appel : des guillemets dans le texte sont des mots) ou au milieu d'un titre `= …` est refusé avec sa raison, la pastille restant à sa place (D-06).
- **Source** : T5
- **Priorité** : doit
- **Critère d'acceptation** : test — glisser la pastille `F` d'après « und danach » entre « Kraft » et « und » : l'ordre des éléments du fichier devient texte, `var F`, texte ; un dépôt dans `$ a + b $` laisse le fichier inchangé et dit pourquoi.

### REQ-005 — Saisie d'un `var` : la variable affichée d'abord, la clé suit
- **Exigence** : Woodcore doit ouvrir l'édition d'un `var` dans l'ordre : variable affichée, variable de calcul, valeur, unité. Pendant la saisie de la variable affichée, la variable de calcul s'écrit d'elle-même (`formula_domain.key_from_symbol`, `M_(y,d)` → `M_y_d`) ; Tab y entre, et ce que l'ingénieur y tape la remplace et cesse d'être recalculé. À la réouverture d'un bloc dont la clé n'est pas celle que donnerait sa variable affichée, la clé est tenue pour écrite à la main.
- **Source** : T6, T7, T8
- **Priorité** : doit
- **Critère d'acceptation** : test — nouveau `var`, focus dans « Variable affichée », taper `M_(y,d)` : le champ « Variable de calcul » vaut `M_y_d` ; Tab, taper `My` ; revenir à la variable affichée et taper `M_(z,d)` : la clé reste `My` ; Tab, Tab mènent à « Valeur » puis « Unité ».

### REQ-006 — Niveau −1 : plusieurs variables par ligne
- **Exigence** : Woodcore doit disposer les variables de la sélection manuelle (`display_view.LevelControl`) en une grille qui met autant de variables côte à côte que la largeur du volet de droite le permet, et se réarrange quand le volet change de largeur.
- **Source** : T9, T10
- **Priorité** : doit
- **Critère d'acceptation** : test hors écran — 6 variables, le contrôle large de 600 px : au moins deux variables sur la même ligne (même `y`) ; large de 200 px : une par ligne.

### REQ-007 — Niveau −1 : sélecteur segmenté `0 | 1 | 2 | 3`, sans case à cocher
- **Exigence** : Woodcore doit régler le niveau de chaque variable par quatre boutons accolés `0 | 1 | 2 | 3`, exclusifs, le choisi légèrement mis en valeur ; la case à cocher disparaît, `0` valant la case décochée (la variable n'est pas dans `shown:`). Une variable verrouillée (résultat d'une vérification, issue #39) n'offre que `1 | 2 | 3`. L'appel écrit reste le même qu'aujourd'hui (`level: -1, shown: (…)`).
- **Source** : T11, T12, T13, T15
- **Priorité** : doit
- **Critère d'acceptation** : tests `test_display_view.py` et `test_member_check_tab.py` adaptés — clic sur `2` de `F_max` : `values()["shown"] == {"F_max": 2}` ; clic sur `0` : `F_max` sort de `shown` ; une clé verrouillée n'a pas de bouton `0` ; aucune `QCheckBox` dans le contrôle.

## 4. Exigences d'interface

### UI-001 — La pastille
- **Exigence** : rectangle aux coins arrondis, fond et bord pris dans `calc/tools/theme.json` (une couleur nouvelle y est ajoutée en clair et en sombre si aucune ne convient), hauteur d'une ligne de texte, la variable affichée en mathématiques (`richtext`), l'infobulle « Double-cliquer pour modifier » ; la pastille choisie est marquée (bord accentué) et ses options s'affichent à droite, comme un bloc aujourd'hui.
- **Source** : T1, T3
- **Langues** : aucune chaîne nouvelle prévue ; toute chaîne ajoutée existe en fr/de/en.
- **Critère d'acceptation** : capture hors écran de l'onglet ; aucune couleur codée en dur (`tests/test_theme*`).

### UI-002 — Le sélecteur segmenté
- **Exigence** : quatre boutons accolés sans espace, qui se lisent comme un seul rectangle aux coins arrondis aux deux extrémités, séparés par un trait fin ; le bouton choisi a le fond d'accent léger du thème ; une variable verrouillée garde la même place (trois boutons).
- **Source** : T11, T12, T15
- **Langues** : l'infobulle existante `ds_shown_tip` / `ds_shown_locked`, fr/de/en.
- **Critère d'acceptation** : capture hors écran du volet «Affichage» d'une vérification d'élément au niveau −1.

## 5. Exigences d'architecture

### ARCH-001 — Le volet du milieu devient un seul document
- **Exigence** : les zones de texte entre blocs (`TextZone`) et la pile de `Block` cèdent la place à un seul éditeur de texte (Qt `QTextEdit`/`QTextDocument`) dans lequel chaque commande est un objet en ligne dessiné en pastille (`QTextObjectInterface`), la commande portée par le format du caractère. La conversion document ↔ éléments du domaine (`Command` texte et commandes) est une fonction pure, testée sans fenêtre.
- **Source** : T2, T3, T5 (inféré : une pastille ne peut se poser au milieu d'une ligne de texte avec des widgets empilés)
- **Critère d'acceptation** : la conversion est dans un module sans Qt-widgets ou testée par aller-retour ; `TextZone` n'est plus utilisé par l'onglet.

### ARCH-002 — Rien n'est calculé dans l'onglet
- **Exigence** : valeurs, unités, erreurs et ✔/✘ des pastilles viennent de `formula_domain.compute` ; la clé tirée de la variable affichée de `formula_domain.key_from_symbol` ; le placement en ligne/à part se lit des options de la commande et des défauts de la signature (`build_reference.signature_defaults`), jamais d'une liste recopiée.
- **Source** : principes 1–3 (docs/architecture/principles.md), CLAUDE.md
- **Critère d'acceptation** : revue de code ; test qui change le défaut lu de la signature (monkeypatch) et voit le placement suivre.

### ARCH-004 — La mise en page du volet, Qt-free
- **Exigence** : un module `calc/domains/formula_layout.py`, sans Qt, possède : `placement(command)` (en ligne / à part, `note` lu dans les options puis dans `build_reference.signature_defaults`), `to_paragraphs(items)` / `from_paragraphs(paragraphs, commands)` (un paragraphe du volet = des lignes source qui se joignent ; une frontière de paragraphe à côté d'une pastille en ligne s'écrit ligne vide ; un titre `= …`, une ligne hors markup de tête, un commentaire `//` ou une ligne de liste `- `/`+ ` ne se joignent jamais à une pastille) et `drop_refusal(...)` ; le lexer de `_top_level_lines` est exposé par une fonction publique `formula_domain.plain_spans(markup)`.
- **Source** : revue (ARCH-RISK-001, 002, 003)
- **Critère d'acceptation** : `tests/test_formula_domain.py` — aller-retour `from_paragraphs(to_paragraphs(x)) == x` ; `placement` suit un défaut monkeypatché ; `val` jamais à part ; un test compilé tient l'exception de `val` égale à Typst ; `drop_refusal` refuse `$…$`, titre, bloc brut, appel (une chaîne en est une partie ; des guillemets en markup sont des mots).

### ARCH-003 — Un seul contrôle de niveau pour tous les onglets
- **Exigence** : le sélecteur segmenté (`chrome.SegmentedSwitch`, existant, avec une variante de style « accent léger » ajoutée au thème) et la grille fluide (`flowbar.FlowLayout`, existant) sont dans `display_view.LevelControl`, de sorte que le panneau «Affichage» générique et celui des vérifications d'éléments changent ensemble (règle 16).
- **Source** : T9 (« les onglets qui possèdent … un level moins 1 »), docs/ui/window.md (issue #20)
- **Critère d'acceptation** : `member_check_tab_actions.py` n'a pas de code propre au sélecteur ; les deux tests passent.

## 6. Contraintes

- **CON-001** — Le format du fichier de domaine ne change pas de version : une commande seule sur sa ligne, `#var-domain(…)[…]`, les balises `// woodcore:` (docs/typst/formulas.md, D-06). La ligne vide entre texte et commande, désormais conservée (D-05), est une précision de la lecture, documentée, qui relit les fichiers existants à l'identique. Source : inféré.
- **CON-002** — Les comportements acquis de l'onglet restent : Entrée/clic ailleurs valide, Échap abandonne, un bloc refusé reste ouvert avec sa raison, un clic sur une variable à droite l'écrit dans le calcul en cours, la commande de la palette s'insère au curseur, « Affichage » d'une ligne choisie, projet en lecture seule. Source : inféré (issues #15, #19).
- **CON-003** — Trois langues pour toute chaîne nouvelle ; couleurs dans `theme.json`. Source : CLAUDE.md.
- **CON-004** — Documentation : `docs/ui/tab-formulas.md`, `docs/ui/window.md` (niveau −1), `docs/ui/tab-member-checks.md` si touché, `CHANGELOG.md`, «Nouveautés» fr/de/en. Source : CLAUDE.md.

## 7. Décisions prises

- **D-01** — Toutes les commandes deviennent des pastilles, `eq` et `verify` compris (T14, réponse du 11.10.2026). Prix accepté : les lettres et chiffres d'un `eq` ne sont plus lisibles dans le volet sans double-clic ni «Affichage».
- **D-02** — Une variable verrouillée n'a que `1 | 2 | 3` (T15). Prix : sa ligne est plus étroite que les autres.
- **D-03** — Le placement en ligne / à part n'est pas une donnée du volet mais se déduit de `note:` (T4 « automatiquement ») : aucun nouveau champ dans le fichier.
- **D-04** — Un bloc ouvert (double-clic, commande ajoutée) devient sa rangée de champs **sur sa propre ligne**, à la place de la pastille ; le texte autour s'écarte et se referme à la validation (Q-001). Prix : le texte bouge pendant l'édition.
- **D-05** — Le volet montre ce que Typst imprime : un retour à la ligne avant ou après une pastille en ligne écrit une **ligne vide** dans le fichier (nouveau paragraphe), et `formula_domain.split_items` **garde** désormais une ligne vide entre un texte et une commande au lieu de l'effacer (Q-002). Prix : précision de la lecture du fichier de domaine (documentée, décision dans `docs/decisions.md`) ; un fichier écrit par v0.117 n'en contient pas et se relit à l'identique.
- **D-07** — Dans la liste des éléments du domaine, le saut de paragraphe est porté **par le texte** : un texte garde au plus une ligne vide en tête et en queue, et un texte vide (`Command(TEXT, raw="")`) entre deux commandes vaut une ligne vide ; aucun nouveau genre d'élément (réponse du 11.10.2026 à ARCH-RISK-002). Les lignes vides au tout début ou à la toute fin du corps ne sont pas des sauts.
- **D-06** — Un dépôt à un endroit où la commande changerait de sens ou rendrait le fichier illisible (dans `$…$`, un titre `= …`, un bloc brut, une chaîne, un appel) est refusé avec sa raison, la pastille reste à sa place (Q-003).

## 8. Hors périmètre

- La forme de l'impression Typst des commandes (aucune commande ni argument nouveau).
- Les onglets autres que «Formules» pour les pastilles ; le niveau −1 seul pour le sélecteur (le menu `auto / 0 / 1 / 2 / 3 / −1` du niveau de la commande reste un menu déroulant).

## 9. Idées non retenues comme exigences

- Aucune.

## 10. Questions

### Q-001 — Où s'ouvre l'édition d'un bloc ?
- **Pourquoi elle compte** : dans un document de texte, une rangée de champs ne peut pas vivre au milieu d'une ligne ; l'endroit de l'éditeur change l'architecture et l'ergonomie.
- **Options** : A (recommandée) — l'éditeur s'ouvre sur sa propre ligne à la place de la pastille (le texte autour s'écarte, comme aujourd'hui), et redevient pastille à la validation ; B — un petit panneau flottant sous la pastille, le texte ne bouge pas ; C — une barre d'édition fixe en bas du volet du milieu.
- **Réponse** : A — à la place, sur sa propre ligne (11.10.2026) → D-04.

### Q-002 — Que fait Entrée (un saut de ligne) à côté d'une pastille en ligne ?
- **Pourquoi elle compte** : Typst lit un saut de ligne simple comme une espace et une ligne vide comme un nouveau paragraphe ; aujourd'hui la lecture du fichier efface les lignes vides autour d'une commande.
- **Options** : A (recommandée) — ce que montre le volet est ce que Typst imprime : un retour à la ligne avant ou après une pastille en ligne écrit une ligne vide dans le fichier (nouveau paragraphe), et la lecture garde ces lignes vides ; B — un retour à la ligne reste un simple saut du source : la pastille peut paraître à la ligne dans le volet alors que Typst l'imprime dans la même phrase.
- **Réponse** : A — nouveau paragraphe ; la lecture garde les lignes vides autour d'une commande (11.10.2026) → D-05.

### Q-003 — Un dépôt à un endroit interdit (dans `$…$`, un titre `= …`)
- **Pourquoi elle compte** : déposer une commande au milieu d'un titre la sortirait du titre à l'impression (le titre finit à la fin de sa ligne) ; dans une équation, le fichier ne se relirait pas.
- **Options** : A (recommandée) — refusé avec sa raison, la pastille revient à sa place ; B — la pastille va à la fin de la ligne visée.
- **Réponse** : A — refusé avec sa raison, la pastille revient à sa place (11.10.2026) → D-06.

## 11. Critères d'acceptation

- [x] REQ-001 — chaque commande validée est une pastille `symbole = valeur unité` (verify : relation et ✔/✘).
- [x] REQ-002 — en ligne par défaut, seule sur sa ligne avec `note: "line"` ou pour `verify`, sans autre écriture.
- [x] REQ-003 — aller-retour fichier ↔ volet identique ; fichiers existants inchangés.
- [x] REQ-004 — glisser-déposer d'une pastille, fichier écrit ; dépôt interdit refusé.
- [x] REQ-005 — ordre variable affichée → clé auto (écrasable par Tab) → valeur → unité.
- [x] REQ-006 — plusieurs variables par ligne selon la largeur.
- [x] REQ-007 — sélecteur `0|1|2|3`, plus de case ; verrouillée `1|2|3`.
- [x] UI-001, UI-002 — pastille et sélecteur aux couleurs du thème.
- [x] ARCH-001 — un document unique, conversion pure testée.
- [x] ARCH-002 — rien calculé dans l'onglet.
- [x] ARCH-003 — un contrôle partagé.
- [x] Documentation : `docs/ui/tab-formulas.md`, `docs/ui/window.md`, `CHANGELOG.md`, «Nouveautés» fr/de/en.
- [x] Tests : `tests/test_formula_tab.py`, `tests/test_formula_domain.py`, `tests/test_display_view.py`, `tests/test_member_check_tab.py` étendus et verts ; suite complète verte.

## 12. Traçabilité

| Source | Élément | Statut |
|---|---|---|
| T1 | REQ-001, UI-001 | capturé |
| T2 | REQ-002, REQ-003, ARCH-001 | capturé |
| T3 | REQ-001, REQ-002, UI-001 | capturé |
| T4 | REQ-002, D-03 | capturé |
| T5 | REQ-004, D-06 | capturé |
| T6 | REQ-005 | capturé |
| T7 | REQ-005 | capturé |
| T8 | REQ-005 | capturé |
| T9 | REQ-006, ARCH-003 | capturé |
| T10 | REQ-006 | capturé |
| T11 | REQ-007, UI-002 | capturé |
| T12 | REQ-007, UI-002 | capturé |
| T13 | REQ-007 | capturé |
| T14 | D-01 | décision |
| T15 | D-02 | décision |
| — | D-04, D-05 | questions inférées Q-001, Q-002, tranchées |

### Points de la source non résolus

- Aucun point de la source ; Q-001 à Q-003 sont des choix que la source ne tranche pas.

## 13. Revue d'architecture

Revue du 11.10.2026 (agent `architecture-reviewer`) — **APPROUVER AVEC RÉSERVES**, réserves levées dans cette spec.

- **Modules** : `formula_tab_widgets.py` (`Block`, `TextZone`, `FIELDS`, `_trim`), `formula_tab_domains.py` (`show_domain`, `items`, `variables_before`), `formula_tab_blocks.py` (`add_block`, `command_from`, `on_validated`, `remove_block`, `write_text`, `pressed_on`, `on_block_chosen`), `formula_tab.py` (`display_entries`, `ref_of`, `write_display`), `formula_domain.py` (`split_items`, `check_body`, `read`, `_top_level_lines`), `display_view.LevelControl`.
- **À réutiliser** : `chrome.SegmentedSwitch` (chrome.py:106), `flowbar.FlowLayout`/`FlowWidget`, `richtext.math_html` et le modèle de peinture de `richtext.MathDelegate`, `Block.view_html` (devient le contenu de la pastille), `Block.show_editor`/`_Keys`/`command_from`, `fd.key_from_symbol`, `check_body` comme garde-fou final ; couleurs existantes `accent-soft`, `line-strong`, `accent`, `danger`, `ok`.
- **ARCH-RISK-001 (bloquant → levé)** : `val` avec `note: "line"` reste en ligne → REQ-002 corrigée, test compilé.
- **ARCH-RISK-002 (bloquant → levé)** : la ligne vide entre deux commandes manquait → D-05 complété par D-07 ; `split_items.flush`, `check_body` (textes vides sautés, comparaison `.strip()`), `items()` et `_trim` à adapter ; un fichier v0.117 se relit à l'identique ; `docs/decisions.md` et `docs/typst/formulas.md` reçoivent la précision.
- **ARCH-RISK-003 (important → levé)** : l'invariant paragraphe ↔ lignes source → ARCH-004, module `formula_layout.py`.
- **ARCH-RISK-004 (important)** : faisabilité `QTextObjectInterface` en PySide6 (handler gardé en référence, `uid` entier dans le format, dictionnaire `uid → Command`, hit-test, double-clic redéfini, `QDrag` maison, copier/coller filtrant U+FFFC, Retour arrière sur une pastille = supprimer la commande, historique d'annulation vidé à l'ouverture, `refresh_results` qui ne reconstruit pas le document) → un essai jetable en tête de l'étape 4 du plan.
- **ARCH-RISK-005 (important)** : D-04 réalisé par trois zones empilées pendant l'édition — éditeur avant, rangée `Block` (widget réel : tabulation, `_Keys`, `pressed_on` inchangés), éditeur après — rejointes à la validation.
- **ARCH-RISK-006 (important)** : une seule vérité, `domain.commands` + `uid → Command` ; un accesseur `entries()` ; `Block` réduit à l'éditeur, `TextZone` retiré.
- **ARCH-RISK-007 (important)** : le segment coché de `SegmentedSwitch` a un fond `ink` fort → variante de propriété `segment-soft` dans `theme.py`, sans toucher la langue ni la vue.
- **ARCH-RISK-008 (mineur)** : `LevelControl.rows[key]` devient le sélecteur seul ; tests adaptés.
- **ARCH-RISK-009 (mineur)** : `FIELDS["var"]` réordonné ; clé suivie par `textEdited` du symbole, « à la main » par son propre `textEdited`.
- **ARCH-RISK-010 (mineur)** : comportements acquis (clic ailleurs, palette au curseur, lecture seule, options de la ligne choisie) repris sur le document.

## 14. Plan d'implémentation

1. **Niveau −1 (#41)** — `theme.py` : variante `segment-soft` ; `display_view.LevelControl` : un `SegmentedSwitch` `0..3` (ou `1..3` verrouillée) par variable dans un `FlowLayout`, case et menu retirés, `picked`/`set_state`/`set_keys` sur le segment. Réalise REQ-006, REQ-007, UI-002, ARCH-003. Tests : `test_display_view.py`, `test_member_check_tab.py` adaptés, test de grille 600/200 px.
2. **Lecture des lignes vides** — `formula_domain.split_items`/`flush`, `check_body`, `plain_spans` public. Réalise D-05, D-07, CON-001. Tests : `test_formula_domain.py` (lignes vides autour et entre commandes, fichier v0.117 inchangé, double ligne vide `hand_edited`).
3. **`formula_layout.py`** — `placement`, `to_paragraphs`, `from_paragraphs`, `drop_refusal`. Réalise ARCH-004, REQ-002, REQ-003 (côté données), D-06. Tests : aller-retour, placement monkeypatché, `val`, test compilé de l'exception, refus de dépôt.
4. **Volet du milieu** — essai Qt jetable (ARCH-RISK-004), puis `formula_tab_widgets.py` : `PillHandler` (peinture, `view_html` réutilisé) et l'éditeur unique (`FormulaText(QTextEdit)` : clic, double-clic, `QDrag`, dépôt refusé, copier/coller, Retour arrière) ; `Block` réduit à l'éditeur, `FIELDS["var"]` réordonné et clé automatique ; `formula_tab_domains.py`/`formula_tab_blocks.py`/`formula_tab.py` sur `entries()` et trois zones pendant l'édition. Réalise REQ-001 à REQ-005, UI-001, ARCH-001, ARCH-002, CON-002. Tests : `test_formula_tab.py` réécrit sur le document (pastilles, placement, dépôt simulé, clé auto, comportements acquis).
5. **Documentation** — `docs/ui/tab-formulas.md`, `docs/ui/window.md` (niveau −1), `docs/typst/formulas.md` (lignes vides du fichier de domaine), `docs/decisions.md` (D-05/D-07), `docs/conventions/testing-catalogue*.md` si un fichier de test est créé, `CHANGELOG.md`, «Nouveautés» fr/de/en.
6. **Tests ciblés puis suite complète**, vérification indépendante.

## 15. Vérification

Vérification indépendante du 11.10.2026 (agent `requirements-verifier`, base a49eb6a) : aucun ❌ ; les ⚠️ levés le même jour, puis les tests relancés (test_formula_tab 19, test_formula_domain 24, test_display_view 17, test_member_check_tab 40, test_i18n 22, test_docs_coherence 7, test_theme 11 — tous verts).

| Élément | Verdict | Preuve |
|---|---|---|
| REQ-001 | ✅ | `formula_tab_widgets.Block.view_html`, `PillPainter` ; `test_a_command_validated_is_a_pill_inline_in_its_sentence_or_on_a_line_of_its_own` |
| REQ-002 | ✅ | `formula_layout.placement` ; même test (note line → seule, retour footnote, fichier ne diffère que par `note:`) ; `test_the_commands_that_leave_their_line_are_those_typst_prints_apart` (compilé) |
| REQ-003 | ✅ | `test_the_pane_joins_a_command_printed_inline_into_its_sentence_and_reads_back`, `test_the_example_project_s_domain_reads_back_to_its_own_bytes`, `test_a_blank_line_beside_a_command_is_a_paragraph_and_is_kept` |
| REQ-004 | ✅ (⚠️ levé) | `test_a_pill_is_chosen_by_a_click_moved_by_a_drop_and_deleted_with_its_text` : dépôt, refus dans `$…$`, dans un titre avec le mot `fm_drop_apart`, au-dessus d'une dépendance ; le `QDrag` souris lui-même n'est pas simulé (bloquant hors écran), `dropEvent` appelle `pill_dropped` testé |
| REQ-005 | ✅ (⚠️ levé) | `test_a_variable_is_typed_shown_variable_first_its_key_following_until_written_by_hand` suit le critère (`M_(z,d)` retapé, clé « à la main » détectée à la réouverture) |
| REQ-006 | ✅ (⚠️ levé) | `test_minus_one_sets_its_variables_side_by_side_as_the_width_allows` : redimensionnement réel 600 / 200 px |
| REQ-007 | ✅ | `test_minus_one_shows_a_level_switch_for_every_variable_and_writes_shown`, `test_member_check_tab` (clé verrouillée `1|2|3`) |
| UI-001 | ✅ (⚠️ levé) | couleurs du thème ; infobulle `fm_double_click` sur une pastille (`FormulaText.event`) ; capture hors écran faite pendant l'implémentation (pastilles dans la phrase, bloc ouvert sur sa ligne) |
| UI-002 | ✅ | variante `soft` (theme.py) ; capture hors écran du panneau «Affichage» au niveau −1 |
| ARCH-001 à ARCH-004 | ✅ | `TextZone`/`_trim` retirés ; `formula_layout.py` sans Qt (`test_the_domain_modules_import_without_qt`) ; placement monkeypatché ; `LevelControl` seul porteur du sélecteur |
| CON-001 à CON-004 | ✅ (⚠️ levé) | format inchangé ; comportements acquis (19 tests de l'onglet) ; trois langues ; docs, CHANGELOG, Nouveautés, catalogue des tests complété |
| D-01 à D-07 | ✅ | voir REQ ci-dessus |

## 16. Journal d'avancement

| Date | Statut | Fait / reste |
|---|---|---|
| 2026-10-11 | draft | spécification extraite des issues #40 et #41 ; 7 REQ, 2 UI, 3 ARCH, 4 CON, 3 questions |
| 2026-10-11 | specified | Q-001 à Q-003 répondues (A, A, A) → D-04, D-05, D-06 |
| 2026-10-11 | reviewed | revue APPROUVER AVEC RÉSERVES ; réserves levées (REQ-002 corrigée, D-07, ARCH-004) ; plan §14 écrit |
| 2026-10-11 | approved | approuvée par l'ingénieur ; implémentation lancée, #41 d'abord |
| 2026-10-11 | implementation | étape 1 (#41) : `LevelControl` en `SegmentedSwitch` doux (`soft`, theme.py) dans un `FlowLayout`, infobulles fr/de/en ; tests display_view, member_check_tab verts — REQ-006, REQ-007, UI-002, ARCH-003 |
| 2026-10-11 | implementation | étape 2 : `formula_domain.tidy_items`, `plain_spans`, lignes vides gardées — D-05, D-07, CON-001 ; test_formula_domain vert |
| 2026-10-11 | implementation | étape 3 : `calc/domains/formula_layout.py` (`placement`, `to_paragraphs`, `from_paragraphs`, `drop_refusal`) et ses tests ; le test compilé a montré que `verify` s'imprime en ligne → REQ-002 corrigée (verify en ligne) — ARCH-004 |
| 2026-10-11 | implementation | étape 4 : volet du milieu en un seul texte (`FormulaText`, `PillPainter` sur `QPyTextObject` — l'essai a montré qu'un `QObject`+`QTextObjectInterface` ne dessine rien en PySide6), pastilles, ouverture en place (D-04), glisser-déposer, clé automatique ; `TextZone`/`_trim` retirés ; mots `fm_drop_*` fr/de/en ; test_formula_tab 19/19 — REQ-001 à REQ-005, UI-001, ARCH-001, ARCH-002, CON-002 |
| 2026-10-11 | testing | étape 5 : docs (tab-formulas, window, formulas, decisions + index), CHANGELOG, Nouveautés 0.117 fr/de/en ; tests liés lancés |
| 2026-10-11 | verification | vérification indépendante : aucun ❌, ⚠️ levés (infobulle des pastilles, tests REQ-004/005/006 au plus près du critère, catalogue, mention « chaîne ») |
| 2026-10-11 | completed | spécification déplacée dans completed/ |
