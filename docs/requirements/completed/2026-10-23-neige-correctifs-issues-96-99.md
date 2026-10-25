---
id: 2026-10-23-neige-correctifs-issues-96-99
titre: Onglet Neige — compilation d'une charge neuve, bascule de l'épingle, Δh libre, indices, surlignage et accordéon ; barre de recherche ; fenêtre de la norme dans l'écran
status: completed
cree: 2026-10-23
mis_a_jour: 2026-10-23
source: message écrit (issues GitHub #96 et #99, et les messages de l'ingénieur du 23.10.2026 qui les ont dictées)
docs: [docs/ui/calc-tab.md, docs/ui/tab-snow.md, docs/ui/window.md, docs/typst/api-conventions.md, docs/domain/loads.md]
---

# Onglet Neige, correctifs des issues #96 et #99 — Spécification

## 1. Objectif

Une charge de neige créée dans un projet neuf doit compiler : c'est aujourd'hui impossible en 0.124.0 (issue #99, bloquant). Autour de ce défaut, l'ingénieur a relevé dans l'onglet Neige ce qui manque encore à « l'onglet type » de #94 : l'épingle de la norme en bascule (#96), une valeur propre pour Δh comme pour C_e, les symboles en indice, et, comme dans la maquette du vent (troisième version), le surlignage qui relie les données aux résultats et l'accordéon du volet central. Deux défauts de la fenêtre s'y ajoutent : la barre de recherche mal placée et la fenêtre de la norme qui s'ouvre hors de l'écran.

## 2. Source

Messages de l'ingénieur, 23.10.2026, mot pour mot (dictés) ; puis « implémente les issues 96 et 99 ».

> **T1** — « J'ai un problème, je n'arrive pas à créer de charge de neige. Je viens de créer un nouveau projet dans le dossier download qui s'appelle 26-10-23-bis et la charge de neige ne fonctionne pas. »
>
> **T2** — « Je n'ai pas testé le reste, si rien ne fonctionne depuis mise à jour, en tout cas la charge de neige ne fonctionne pas. »
>
> **T3** — « Ensuite, dans le issue également, la barre recherchée, c'était RLK qu'il y a en haut à droite, en fait elle doit apparaître en haut à gauche, juste à droite du texte 58 valeurs, export du 23-10-2026-18h28. »
>
> **T4** — « Ensuite, l'onglet de charge de neige, j'ai remarqué que lorsque je clique sur un élément qui ensuite apparaît dans le volet de droite, lorsque je reclique dessus une deuxième fois, il ne disparaît pas du volet de droite et c'est pourtant quelque chose qui devait être implémenté. »
>
> **T5** — « Ensuite, il y a également le problème que lorsque un PDF est tout ouvert sans le PDF, la barre tout en haut du PDF apparaît en dehors de l'écran et c'est compliqué de la ramener vers le bas. Il faut donc t'assurer que le PDF s'ouvre, la barre du haut s'ouvre en tout cas dans l'espace qui est disponible. »
>
> **T6** — « Ensuite, pour la correction delta H annexe D, il doit y avoir, comme pour l'exposition CME, la possibilité tout à droite de mettre sur ma propre valeur manuellement. »
>
> **T7** — « De plus, il doit, pour CE et CT, le E et le T qui sont affichés dans le volet du milieu de ma tête, doit être affiché en tant qu'indice et non pas C-E. »
>
> **T8** — « Ensuite, comme pour le volet du vent, en tout cas l'artefact que tu as fait, il faut que qu'il y ait un highlighting dans le volet de droite et dans les résultats, et dans le volet central. Lorsque il y a des valeurs qui permettent de calculer des entrées, qui permettent de calculer des résultats à droite »
>
> **T9** — « et en plus il faut avoir dans le volet central le système d'accordéon qu'il y a dans l'artefact pour le vent. »
>
> **T10** — Issue #96 (22.10.2026) : « Premier clic sur un ⓘ (ou sur la bulle) : l'extrait est épinglé dans le volet droit, sous les résultats, après les épingles déjà là. Clic suivant, l'extrait étant déjà épinglé : il disparaît du volet droit, comme avec son ×. Le ⓘ d'un extrait épinglé se voit, par exemple rempli ou d'une autre couleur. La bulle dit ce que fera le clic : « Clic : épingler à droite » ou « Clic : retirer du volet droit ». Ctrl+clic ne change pas […]. Le même comportement dans tous les onglets qui ont la bulle. Il est écrit une fois, dans la brique commune de la bulle […]. Mots en de, fr, en ; un test (épingler, retirer, épingler de nouveau) ; la page docs/ui/ de la bulle. »

**Constaté en lisant le projet `C:\Users\florian.lamprecht\Downloads\261023-bis`** (à l'appui de T1, non dicté) :

> **T11** — L'aperçu échoue : `assertion failed: var: 'dachform' has a symbol but no value` (`lib/formula.typ:1471`), sur la ligne `#var("dachform", domain: ("snow-load", "charge_de_neige"), name-visible: "\"Forme de la toiture\"", …)`. Même forme pour `abgleiten`.
>
> **T12** — Le fichier `Variable-loads/Snow/charge_de_neige.typ` a été écrit à 18:29 pour un toit à deux pans (α₂, μ₁₁, μ₁₂, q_k,11…) ; le cas a été enregistré à 18:30 avec un toit cylindrique (`roof: "curved"`) : l'export porte μ₃, q_k,1, q_k,3, le fichier n'a pas suivi.

## 3. Exigences fonctionnelles

### REQ-001 — Une donnée lue de l'export et nommée par `name-visible:` compile
- **Exigence** : Woodcore doit compiler `#var(key, domain: (kind, id), name-visible: …)` sans valeur écrite : le symbole donné par `name-visible:` (ou en deuxième position) remplace celui de l'export et **ne fait pas** de la ligne une valeur écrite contrôlée par `domain:`. Seule une *valeur* écrite à côté de `domain:` en fait une valeur contrôlée (spec 2026-10-15, REQ-001).
- **Source** : T1, T11
- **Priorité** : doit
- **Critère d'acceptation** : une charge de neige neuve (toit à deux pans, puis cylindrique) d'un projet en français, en allemand et en anglais compile, l'aperçu montrant « Forme de la toiture » et « Glissement de la neige » avec la valeur de l'export ; un test Typst sur `#var(…, domain: pair, name-visible: …)` pour une valeur texte et pour un nombre ; un test qu'une valeur écrite à côté reste contrôlée.

### REQ-002 — Le fichier du cas est toujours régénéré, sans bouton
- **Exigence** : quand le cas est enregistré (ou exporté) et que la forme de son fichier n'est plus celle de l'export (le toit, donc ses pentes et ses μ), Woodcore doit réécrire le fichier dans la nouvelle forme **toujours et sans rien demander** (D-4). Ce que l'ingénieur a réglé dans « Affichage » sur une ligne que la nouvelle forme garde — son niveau, les arguments de son affichage, la largeur, la légende, le label et l'affichage de la figure, le niveau du domaine — est reporté sur la ligne réécrite ; une ligne que la nouvelle forme ne porte plus disparaît. Le bouton « Régénérer » et la ligne rouge « autre forme » d'« Affichage » sont retirés pour les onglets de calcul.
- **Source** : T12, Q-002 (réponse de l'ingénieur)
- **Priorité** : doit
- **Critère d'acceptation** : créer un cas (deux pans), régler α₁ au niveau 3 dans « Affichage », choisir « cylindrique », enregistrer : le fichier porte `mu_3`, `q_k1`, `q_k3`, plus `alpha_2` ni `mu_11`, α₁ toujours au niveau 3, et compile ; aucun « Régénérer » dans l'onglet ; test.

### REQ-005 — Passer de « Calcul » à « Affichage » enregistre le cas
- **Exigence** : basculer de la vue « Calcul » à « Affichage » enregistre le cas modifié (comme « Enregistrer ») — donc l'export et le fichier du cas régénéré (REQ-002) — avant de montrer « Affichage ». Un cas sans modification n'est pas réécrit ; un cas que le calcul refuse (erreur rouge) n'est pas enregistré et « Affichage » le dit.
- **Source** : Q-002 (réponse de l'ingénieur)
- **Priorité** : doit
- **Critère d'acceptation** : modifier h₀, cliquer « Affichage » : la source, `calculations.json` et le fichier du cas portent la nouvelle valeur, l'aperçu la montre ; test.

### REQ-003 — Le clic sur un ⓘ est une bascule (#96)
- **Exigence** : premier clic sur un ⓘ (ou sur sa bulle) : ses extraits épinglés sous « Résultats », après les épingles déjà là ; clic suivant, déjà épinglés : retirés comme par leur ×. Ctrl+clic inchangé. Écrit une fois dans `norm_bubble`/`calc_tab`, donc pour tout onglet qui a la bulle.
- **Source** : T4, T10
- **Priorité** : doit
- **Critère d'acceptation** : test : épingler, retirer, épingler de nouveau (le module présent, absent, présent, à sa place) ; le × et le second clic laissent le même état ; une tuile (choix du toit) reste choisie par son clic.

### REQ-004 — Δh accepte une valeur propre
- **Exigence** : à droite des boutons de Δh (−200, ±0, +200, +400, +500 m), un champ « autre » prend une valeur de l'ingénieur telle quelle, comme celui de C_e ; elle est écrite dans la source, calculée, exportée, et imprimée comme Δh (sans la liste des choix de l'annexe D à côté).
- **Source** : T6
- **Priorité** : doit
- **Critère d'acceptation** : Δh = 150 m saisi → h_ref = h₀ + 150, s_k suit, la source se relit identique, le rapport imprime Δh = 150 m ; une source sans valeur propre garde sa version de schéma (forme selon Q-001).

## 4. Exigences d'interface

### UI-001 — La recherche à gauche
- **Exigence** : « Rechercher… Ctrl K » est placé dans la barre du haut juste à droite du texte gris « N valeurs · export du … », et non plus entre les langues et « Recharger ».
- **Source** : T3
- **Langues** : inchangées (`cp_search_button`)
- **Critère d'acceptation** : dans la barre, l'ordre est : nom du projet, texte gris, Rechercher, espace extensible, puis le reste ; Ctrl+K inchangé.

### UI-002 — Le ⓘ épinglé se voit, la bulle dit ce que fera le clic (#96)
- **Exigence** : le ⓘ d'un extrait épinglé est rempli (fond accent, comme `.i.pinned` de la maquette du vent) ; il redevient vide au retrait, par le second clic comme par le ×. Le pied de la bulle dit « Clic : épingler à droite » ou « Clic : retirer du volet droit », et « Ctrl+clic : ouvrir la norme ».
- **Source** : T10
- **Langues** : fr / de / en
- **Critère d'acceptation** : test : l'état du ⓘ après épingler, retirer par ×, retirer par clic ; les mots dans les trois langues (`tests/test_i18n.py`).

### UI-003 — C_e et C_T en indice dans le volet central
- **Exigence** : les libellés des champs écrivent leurs symboles avec l'indice en indice (C<sub>e</sub>, C<sub>T</sub>), et non « C_e » ; la règle vaut pour tout libellé d'un onglet de calcul.
- **Source** : T7
- **Langues** : fr / de / en
- **Critère d'acceptation** : le libellé de C_e et de C_T est en texte riche, l'indice en `<sub>` ; aucun « _ » visible dans un libellé de l'onglet Neige.

### UI-004 — Surlignage entre données et résultats
- **Exigence** : au survol d'une ligne de « Résultats », les champs du volet central dont elle dépend (directement ou par un résultat intermédiaire) et les résultats intermédiaires sont surlignés ; au survol d'un champ du volet central, les résultats qu'il sert à calculer sont surlignés dans « Résultats ». Le bleu de survol de la maquette du vent (lisible en clair et en sombre, couleur de `theme.json`).
- **Source** : T8
- **Langues** : aucun mot nouveau
- **Critère d'acceptation** : neige, deux pans : survoler q_k,11 surligne h₀, Δh, C_e, C_T, α₁, glissement (et h_ref, s_k, μ₁₁ dans Résultats) ; survoler h₀ surligne h_ref, s_k et tous les q_k ; un test sur le graphe de dépendances (fonction pure) et un sur le surlignage du formulaire.

### UI-005 — Le volet central en accordéon
- **Exigence** : chaque section du formulaire (Bâtiment, Lieu, Toiture) est un accordéon comme dans la maquette du vent : en-tête avec son numéro, son titre, un résumé de ses valeurs, un point vert / orange / rouge selon les messages de ses champs, ▸/▾ ; chaque section s'ouvre et se ferme seule ; l'état est gardé par onglet sur cette machine (comme les modules). Un message cliqué dans « État du calcul » ouvre la section de son champ avant le clignotement.
- **Source** : T9
- **Langues** : fr / de / en pour les mots nouveaux (résumés)
- **Critère d'acceptation** : test : replier, rouvrir, état gardé après reconstruction ; un message d'erreur sur h₀ rend rouge le point de « Lieu » et son clic ouvre « Lieu ».

### UI-006 — La fenêtre de la norme s'ouvre dans l'écran
- **Exigence** : la fenêtre du lecteur de la norme (Ctrl+clic sur un ⓘ) et les fenêtres ⧉ d'un module s'ouvrent entièrement dans l'espace disponible de l'écran de la fenêtre de Woodcore : barre de titre visible, taille réduite à l'écran.
- **Source** : T5
- **Critère d'acceptation** : test d'une fonction pure de placement : une taille demandée 820 × 1000 sur un écran disponible de 1920 × 1032 donne une fenêtre dont le haut, cadre compris, est dans l'écran ; idem sur un second écran décalé.

## 5. Exigences d'architecture

### ARCH-001 — Les dépendances viennent du domaine, la base les dessine
- **Exigence** : le graphe « résultat ← variables » est lu dans les `steps` de l'instance (`uses`), complété par ce que le domaine déclare (les μ, que nul `step` ne relie à α et au glissement) ; le lien « champ → variable » est déclaré par le domaine (`Field.var` ou équivalent). `calc_tab.py` ne contient aucun nom de la neige.
- **Source** : principes (domaine indépendant de l'UI ; pas de logique métier dans l'onglet), `tests/test_calc_tab_base.py`
- **Critère d'acceptation** : le domaine inventé de `tests/fake_domain.py` surligne ses dépendances ; le grep du test de la base reste vide.

### ARCH-002 — Le placement d'une fenêtre dans l'écran est écrit une fois
- **Exigence** : une fonction (pure pour son calcul) borne une fenêtre à l'espace disponible de son écran ; le lecteur de la norme et `ModuleWindow` l'appellent.
- **Source** : T5, principe « une seule source »
- **Critère d'acceptation** : un seul endroit du code calcule ce placement.

## 6. Contraintes

- **CON-001** — Une source de neige existante (1.0 à 1.3) se relit sans changement ; la valeur propre de Δh ne relève la version de schéma que d'une source qui en porte une (comme C_e, 1.3). Source : principe « modèles versionnés », inféré de T6.
- **CON-002** — Le moteur Typst corrigé (`lib/formula.typ`) est copié dans chaque projet à l'export (`000-Woodcore/lib`) : la correction vaut pour les projets existants à leur prochaine export. Inféré.
- **CON-003** — Mots en de/fr/en dans les glossaires de la fenêtre (`*_words.py`). Source : CLAUDE.md.
- **CON-004** — Documentation : `docs/ui/calc-tab.md`, `docs/ui/tab-snow.md`, `docs/ui/window.md` (barre du haut), `docs/typst/api-conventions.md` si la règle de `#var` y est écrite ; `CHANGELOG.md` ; page « Nouveautés » en trois langues. Source : CLAUDE.md.

## 7. Décisions prises

- **D-1** — Le défaut de compilation se corrige dans le moteur (`#var`), pas en retirant `name-visible:` du générateur : `docs/ui/tab-snow.md` dit qu'un symbole écrit en mots passe par `name-visible:`, et la règle de la spec 2026-10-15 parle d'une *valeur* écrite à côté de `domain:`, pas d'un symbole. Raison : le générateur fait ce qui est documenté ; c'est le moteur qui confond symbole et valeur.
- **D-2** — Le libellé allemand « Dachform / Lastmodell » dans `calculations.json` n'est pas un défaut : l'export garde ses mots en allemand, la ligne du fichier les remplace (`label:`) dans la langue du rapport. Vérifié dans le projet de l'ingénieur.
- **D-3** — La valeur « Tonnendach » n'est pas une valeur par défaut fautive : le cas a été enregistré avec un toit cylindrique (`roof: "curved"`) ; le défaut est que le fichier n'a pas suivi (REQ-002).
- **D-4** — (Q-002, l'ingénieur, 23.10.2026) « le fichier est toujours automatiquement régénéré. Il n'y a donc pas besoin du bouton "Régénérer". De plus, lorsqu'on passe de "Calcul" à "Affichage", les calculs doivent être automatiquements enregistrés (et donc également générés dans l'affichage) ». Prix accepté : une ligne écrite à la main dans le fichier d'un cas de calcul, hors des réglages d'« Affichage », n'est plus protégée par la régénération — le fichier d'un onglet de calcul est l'affaire de Woodcore, réglé par « Affichage ». Le reste (texte ou commande ajoutés à la main) est gardé après la ligne qu'il suivait, comme le fait déjà `unfold.regenerate`.
- **D-5** — (Q-001) Δh propre comme C_e : `correction: "custom"` et `delta_h`, schéma 1.4 pour la seule source qui en porte une.
- **D-6** — (Q-003) Le surlignage se déclenche au survol, dans les deux sens.
- **D-7** — (revue, ARCH-RISK-006 ; approuvée avec la spec) Au passage à « Affichage », un cas dont l'ID a changé pose la question de renommage d'« Enregistrer » ; un cas neuf est créé ; un cas en erreur rouge ou un projet en lecture seule n'est pas enregistré, et « Affichage » le dit.

## 8. Hors périmètre

- Le vent : il prendra l'accordéon et le surlignage de la base quand il passera sur elle (son issue).
- Le dessin 3D, les Résultats 3D et le reste de la maquette du vent.
- Vérifier « que rien ne fonctionne depuis la mise à jour » (T2) au-delà de la neige : la suite de tests complète et l'aperçu d'un projet neuf sont lancés à la fin ; tout autre défaut trouvé devient une issue.

## 9. Idées non retenues comme exigences

- T2 « si rien ne fonctionne depuis mise à jour » : une inquiétude, pas une demande ; couverte par la suite complète et l'essai d'un projet neuf (§8).

## 10. Questions

### Q-001 — La forme de la valeur propre de Δh dans la source
- **Pourquoi elle compte** : c'est un contrat (`schemas/snow-source.schema.json`).
- **Options** : A (recommandée) comme C_e : `correction: "custom"` et le nombre dans `delta_h`, schéma 1.4 pour une source qui en porte une ; même code que C_e dans `calc_fields`, une valeur propre égale à +200 reste « propre ». B : `correction` accepte tout nombre, la liste de l'annexe D n'étant plus qu'un choix des boutons ; plus simple, mais une valeur propre égale à un bouton ne se distingue plus et le rapport ne sait plus s'il cite l'annexe D.
- **Réponse** : A, comme C_e — l'ingénieur, 23.10.2026 (D-5).

### Q-002 — Le fichier du cas quand sa forme change
- **Pourquoi elle compte** : aujourd'hui le fichier ne suit pas (T12) ; « Affichage » dit seulement « autre forme, Régénérer ».
- **Options** : A (recommandée) à l'enregistrement, si aucune ligne du fichier n'a été changée par l'ingénieur, Woodcore le réécrit dans la nouvelle forme sans rien demander ; s'il en a changé, comme aujourd'hui (« Régénérer », les lignes changées gardées). B : toujours « Régénérer » à la main.
- **Réponse** : ni A ni B — toujours régénéré, sans bouton « Régénérer » ; et passer à « Affichage » enregistre — l'ingénieur, 23.10.2026 (D-4, REQ-002, REQ-005).

### Q-003 — Le déclencheur du surlignage
- **Pourquoi elle compte** : survol ou clic change le code et l'usage.
- **Options** : A (recommandée) le survol, comme la maquette du vent, dans les deux sens (un résultat → ses données ; une donnée → ses résultats). B : un clic qui fige le surlignage jusqu'au clic suivant.
- **Réponse** : A, le survol — l'ingénieur, 23.10.2026 (D-6).

## 11. Critères d'acceptation

- [x] REQ-001 — une charge de neige neuve compile en fr/de/en ; tests Typst de `#var` avec `name-visible:` et `domain:`.
- [x] REQ-002 — un changement de toit réécrit toujours le fichier, réglages d'« Affichage » reportés, sans « Régénérer » ; test.
- [x] REQ-005 — passer à « Affichage » enregistre le cas ; test.
- [x] REQ-003 — épingler / retirer / épingler de nouveau par le ⓘ ; test.
- [x] REQ-004 — Δh libre calculé, relu, imprimé ; test du domaine et du schéma.
- [x] UI-001 — Rechercher à droite du texte gris ; test de l'ordre de la barre.
- [x] UI-002 — ⓘ rempli et pied de la bulle ; test et mots ×3.
- [x] UI-003 — C_e et C_T en indice ; test.
- [x] UI-004 — surlignage dans les deux sens ; tests.
- [x] UI-005 — accordéon, point d'état, état gardé, message qui ouvre sa section ; tests.
- [x] UI-006 — fenêtres dans l'écran ; test de la fonction de placement.
- [x] ARCH-001 — dépendances du domaine, base sans mot de la neige ; test sur le domaine inventé.
- [x] ARCH-002 — un seul placement ; vérification.
- [x] Documentation : `docs/ui/calc-tab.md`, `docs/ui/tab-snow.md`, `docs/ui/window.md`, `CHANGELOG.md`, « Nouveautés » fr/de/en.
- [x] Tests : fichiers étendus et suite complète verte.

## 12. Traçabilité

| Source | Élément | Statut |
|---|---|---|
| T1 | REQ-001, REQ-002 | capturé |
| T2 | §8, §9 | inquiétude → suite complète |
| T3 | UI-001 | capturé |
| T4 | REQ-003 | capturé |
| T5 | UI-006, ARCH-002 | capturé |
| T6 | REQ-004, D-5 | capturé, tranché (Q-001) |
| T7 | UI-003 | capturé |
| T8 | UI-004, ARCH-001, D-6 | capturé, tranché (Q-003) |
| T9 | UI-005 | capturé |
| T10 | REQ-003, UI-002 | capturé |
| T11 | REQ-001, D-1 | capturé |
| T12 | REQ-002, REQ-005, D-3, D-4 | capturé, tranché (Q-002) |

### Points de la source non résolus

Aucun.

## 13. Revue d'architecture

Revue indépendante (`architecture-reviewer`, 23.10.2026), sur le code. **Verdict : APPROUVER AVEC RÉSERVES.**

**Modules concernés** : `lib/formula.typ:1380-1482` (`#var`) ; `calc/domains/unfold.py` (`unfold_domains` :740, `refresh` :1043, `regenerate` :1236, `_with_display` :1039/1303) ; `calc/tools/calc_tab.py` (base) ; `calc/tools/domain_file_display.py:165-176` (« Régénérer ») ; `calc/tools/load_tab.py:589` `prepare_display`, `:607` `save` ; `calc/tools/norm_bubble.py` ; `calc/tools/module_pane.py` ; `calc/tools/layout_store.py:134-151` ; `calc/domains/snow_source.py`, `schemas/snow-source.schema.json` ; `calc/tools/calc_fields.py` ; `calc/domains/contracts.py` ; `calc/tools/woodcore_gui.py:436-480` ; `calc/tools/norm_reader.py:95` ; `calc/tools/theme.json`.

**À réutiliser** : `richtext.subscripts()` pour les indices ; l'en-tête de `module_pane.Module` (▸/▾, résumé) pour l'accordéon ; `unfold._with_display`, qui reporte déjà les réglages d'« Affichage » sur une ligne réécrite (D-17 : une ligne n'est « changée » qu'hors de ses arguments d'affichage) ; le code de la valeur libre de `calc_fields` (des identifiants de choix numériques y passent) ; `steps[].uses` de l'instance ; `norm_bubble.place` comme modèle de fonction pure de placement.

**Risques et leur traitement**
- ARCH-RISK-001 (important) — `controlled` doit se calculer sur la valeur écrite, avant que `name-visible` soit mis en tête ; le chemin non contrôlé d'une paire lit `(symbole, valeur de l'export)`. La forme positionnelle `#var("k", "S", domain: paire)` plante aussi : couverte. → étape 1.
- ARCH-RISK-002 (important) — D-4 renverse D-18 de la spec 2026-10-22-onglet-neige-type (« régénérer sur demande, jamais en silence ») : entrée dans `docs/decisions.md` §13 et `decisions-index.md`. → étape 2.
- ARCH-RISK-003 (important) — `unfold_domains` sert aussi aux vérifications, à l'acier, aux moyens d'assemblage, aux moments polaires, dont « Régénérer » reste manuel : une politique par genre, `AUTO_REGENERATE`, limitée aux genres des onglets de calcul (`snow-load`). `export_all` réécrira aussi le fichier de neige : dit dans le CHANGELOG. → étape 2.
- ARCH-RISK-004 (important) — `regenerate` s'arrête sur un conflit et garde les lignes changées : un mode `keep_changed=False` où toute ligne prend l'écriture (l'affichage reporté par `_with_display`), les phrases et commandes de l'ingénieur gardées après leur ligne. Pas de seconde implémentation. → étape 2.
- ARCH-RISK-005 (important) — retirer le bouton et la ligne « autre forme » de `domain_file_display`, `write_unfold_regenerate` de la base et les mots qui ne servent plus ; garder un message rouge, sans bouton, si la régénération automatique échoue. → étape 2.
- ARCH-RISK-006 (important) — l'enregistrement au passage à « Affichage » : `prepare_display` de la base, seulement si le cas est modifié, le projet non en lecture seule et l'état sans erreur rouge ; décision D-7. → étape 3.
- ARCH-RISK-007 (important) — la bascule : `is_pinned` fourni par l'onglet, une seule fonction pour l'id `x:<norme>:<ids>` (aujourd'hui écrit l.446 et relu l.471), les ⓘ remis à jour à chaque épingle et retrait (× compris) et à la restauration ; couleurs de `theme.json` ; mots `ct_*` du pied de la bulle. → étape 4.
- ARCH-RISK-008 (important) — schéma 1.4 sur le modèle de C_e : `correction` nombre ou `"custom"`, `delta_h` ajouté (`additionalProperties:false`), `stamp_version`, plancher de version dans `check_source`, message rouge nouveau, `h_ref` et plus de `choices` pour un Δh propre ; `Field.minimum` négatif pour Δh (0.0 par défaut) et l'unité sur le champ libre. Le chemin Excel (`snow.py`) n'a rien à changer. → étape 5.
- ARCH-RISK-009 (important) — `Field.var` (additif) déclare le lien champ → variable ; `extra_dependencies(instance)` optionnel du domaine pour les μ, **sans** ajouter de `steps` à l'export (la forme de chaque cas changerait) ; une fonction pure `dependencies()` dans `calc/domains/` ; `tests/fake_domain.py` étendu ; « Résultats » en une ligne par widget ; une couleur de survol nouvelle dans `theme.json`, clair et sombre. → étape 6.
- ARCH-RISK-010 (important) — l'état des sections ne doit pas écraser celui des modules dans `layout_store` : une clé `sections` à côté de `order` et `folded` ; `cards.card` gardé (les tests le trouvent par son titre), l'en-tête ajouté. → étape 7.
- ARCH-RISK-011 (important) — une seule fonction de placement, cadre compris, sur l'écran de la fenêtre de Woodcore, appelée à chaque `show_excerpt` ; les bornages existants la réutilisent là où ils font la même chose. → étape 8.
- ARCH-RISK-012, 013, 014 (mineurs) — `bind_palette` avant l'espace extensible ; les libellés et l'état du calcul passés par `richtext.subscripts` ; le catalogue des tests et la documentation. → étapes 8, 9.

**Réserves levées par le plan** : R1 (étape 2, décision écrite d'abord), R2 (étape 2), R3 (D-7), R4 (étape 6), R5 (étape 7), R6 (étape 8), R7 (étape 5).

## 14. Plan d'implémentation

1. **Moteur Typst** (REQ-001) — `lib/formula.typ` `#var` : `controlled` sur la seule valeur écrite ; symbole écrit + paire lue → `(symbole, valeur de l'export)` ; `///` de `name-visible` et `calc/i18n/commands.json` si le texte change. Tests : `tests/test_fine_display.py` (texte, nombre, symbole positionnel, valeur écrite toujours contrôlée). Vérifié aussi sur une copie du projet de l'ingénieur, jamais sur le projet lui-même.
2. **Régénération toujours** (REQ-002, D-4) — `docs/decisions.md` §13 et l'index d'abord ; `unfold.py` : `AUTO_REGENERATE = {"snow-load"}`, `regenerate(..., keep_changed=False)`, appelé dans la seconde boucle de `unfold_domains` quand la forme diffère ; `domain_file_display.py` sans bouton ni ligne « autre forme » pour les onglets de calcul, message rouge en cas d'échec ; `calc_tab.write_unfold_regenerate` et les mots retirés. Tests : `tests/test_unfold.py` (deux pans → cylindrique, niveau d'α₁ gardé, `alpha_2`/`mu_11` partis, phrase de l'ingénieur gardée, vérification non régénérée), `tests/test_case_file_display.py`.
3. **« Affichage » enregistre** (REQ-005, D-7) — `DeclaredTabMixin.prepare_display` : si modifié, non en lecture seule, sans erreur → `save()`. Test dans `tests/test_calc_tab_base.py` (modifié, erreur, lecture seule).
4. **Bascule de l'épingle** (REQ-003, UI-002) — `norm_bubble.py` (`is_pinned`, pied de la bulle, ⓘ rempli) ; `calc_tab.py` (fonction d'id unique, mise à jour sur `pane.removed`, à l'épingle et à la restauration) ; mots `ct_*` fr/de/en. Tests : `tests/test_calc_tab_base.py` (épingler, retirer, épingler ; × et clic même état ; ⓘ rempli).
5. **Δh propre** (REQ-004, D-5) — `snow_source.py` (1.4, `delta_h`, `stamp_version`, `check_source`, `_problems`, `build_instance`, Field), `schemas/snow-source.schema.json`, `calc_fields.py` (unité du champ libre), mots du message. Tests : `tests/test_snow_source.py` (1.4, 1.0–1.3 identiques, plancher, h_ref, sans `choices`), `tests/test_calc_tab_base.py` (valeur libre négative).
6. **Surlignage** (UI-004, ARCH-001) — `contracts.Field.var`, `extra_dependencies` optionnel, `calc/domains/dependencies.py` (fonction pure) ; `snow_source` déclare `var` et les dépendances des μ ; `calc_tab.py` : « Résultats » une ligne par widget, survol des lignes et des champs ; `theme.json` couleur de survol clair/sombre ; `tests/fake_domain.py` étendu. Tests : `tests/test_dependencies.py` (nouveau, ligne au catalogue), `tests/test_calc_tab_base.py`.
7. **Accordéon** (UI-005) — en-tête de section sur `cards.card` (numéro, titre, résumé, point, ▸/▾) sur le motif de `module_pane.Module` ; `layout_store` clé `sections` ; `focus_field` ouvre sa section ; mots des résumés. Tests : `tests/test_calc_tab_base.py`, test de `layout_store` (les deux états survivent l'un à l'autre).
8. **Fenêtre, barre, indices** (UI-001, UI-003, UI-006, ARCH-002) — fonction pure de placement, appelée par `norm_reader` à chaque `show_excerpt`, par `ModuleWindow` et par les bornages existants qui font la même chose ; `bind_palette` avant l'espace extensible ; libellés en `richtext.subscripts`. Tests : placement (1920 × 1032, second écran décalé, cadre), ordre de la barre, aucun « _ » visible dans un libellé.
9. **Documentation et fin** — `docs/ui/calc-tab.md`, `docs/ui/tab-snow.md`, `docs/ui/window.md`, `docs/typst/api-conventions.md`, `CHANGELOG.md`, « Nouveautés » ×3, catalogue des tests ; suite complète ; vérification indépendante ; `finish`.

## 15. Vérification

Vérification indépendante (`requirements-verifier`, 23.10.2026), sur le code, le diff depuis `110531b` et les tests lancés par elle : test_fine_display 26, test_domain_file_display 10, test_snow_source 21, test_dependencies 3, test_screen_fit 2, test_calc_tab_base 14, test_command_palette 10, test_theme 17, test_i18n 23, test_unfold 23, test_docs_coherence 7 — tous verts.

| Élément | Verdict | Preuve |
|---|---|---|
| REQ-001 | ✅ | `lib/formula.typ` `controlled = domain != none and has-value`, `written-symbol` devant la valeur de l'export ; `test_a_symbol_beside_a_pair_domain_reads_the_export_and_prints_the_symbol` (texte, nombre, positionnel, fr/de/en ajoutés après la vérification), `test_a_value_beside_a_pair_domain_stays_a_literal_checked_by_it` |
| REQ-002 | ✅ | `unfold.AUTO_REGENERATE`, `regenerate(keep_changed=False)` ; `test_a_file_of_another_form_is_regenerated_at_the_save_without_a_button` ; décision `docs/decisions.md` §13 et l'index |
| REQ-003 | ✅ | `norm_bubble._act`, `calc_tab.unpin_excerpts`, `excerpt_module_id` ; `test_a_click_on_an_info_pins_and_a_second_takes_out_as_its_cross_does` (tuile ajoutée après la vérification) |
| REQ-004 | ✅ | `snow_source` 1.4, schéma, champ libre ; `test_a_free_delta_h_is_schema_1_4_…`, `test_a_free_delta_h_is_typed_beside_the_map_s_buttons` |
| REQ-005 | ✅ | `DeclaredTabMixin.prepare_display` ; `test_switching_to_affichage_saves_the_case` |
| UI-001 | ✅ | `woodcore_gui.build` ; `test_the_search_field_stands_right_of_what_the_export_holds` |
| UI-002 | ✅ | `InfoMark.set_pinned`, pied de la bulle, mots ×3 ; même test que REQ-003, test_i18n |
| UI-003 | ✅ | `richtext.subscripts` dans les libellés et l'état ; `test_the_snow_s_labels_set_their_subscripts` |
| UI-004 | ✅ | `calc/domains/dependencies.py`, `hover_result`/`hover_field`, jetons `hover` ; `tests/test_dependencies.py`, `test_a_result_hovered_lights_its_data_and_a_datum_its_results`, contraste test_theme |
| UI-005 | ✅ | `calc_tab.Section`, `layout_store.STATE_KEYS` ; `test_the_sections_are_an_accordion_kept_beside_the_modules` |
| UI-006 | ✅ | `screen_fit.fitted`/`place` ; `tests/test_screen_fit.py` |
| ARCH-001 | ✅ | `Field.var`, `extra_dependencies` sans step ajouté ; grep de la base vide |
| ARCH-002 | ✅ | un seul calcul de placement ; les trois autres `availableGeometry` (taille mémorisée, centrage des écrans de démarrage) ne placent pas une fenêtre par son cadre — autre opération, laissée |
| CON-001…004 | ✅ | sources 1.0–1.3 inchangées (chemin de code identique), exemples reconstruits, mots ×3, documentation |
| Documentation | ✅ | CHANGELOG, « Nouveautés » ×3, `docs/ui/*`, `docs/typst/formulas.md`, `docs/domain/loads.md`, `///` + `commands.json`, catalogue |
| Tests, suite complète | — | lancée par `finish` |

## 16. Journal d'avancement

| Date | Statut | Fait / reste |
|---|---|---|
| 2026-10-23 | draft | spécification extraite des issues #96, #99 et des messages du 23.10.2026 ; cause du défaut de compilation trouvée (D-1) ; trois questions |
| 2026-10-23 | specified | Q-001 à Q-003 répondues : D-4 (toujours régénéré, sans bouton ; « Affichage » enregistre), D-5, D-6 ; REQ-005 ajouté |
| 2026-10-23 | reviewed | revue d'architecture : APPROUVER AVEC RÉSERVES (R1–R7) ; plan en 9 étapes ; D-7 |
| 2026-10-23 | approved | approuvée par l'ingénieur, D-7 comprise |
| 2026-10-23 | implementation | étape 1 faite : `#var` — `controlled` sur la seule valeur écrite, symbole écrit + paire lue (REQ-001) ; 2 tests dans `tests/test_fine_display.py` ; la copie du projet 261023-bis compile |
| 2026-10-23 | implementation | étape 2 faite : `unfold.AUTO_REGENERATE`, `regenerate(keep_changed=False)` (figure gardée, texte à plusieurs lignes), « Régénérer » retiré, `ct_regenerate_failed` ; décision dans `docs/decisions.md` et l'index (REQ-002) |
| 2026-10-23 | implementation | étape 3 faite : `DeclaredTabMixin.prepare_display` enregistre (REQ-005, D-7) ; tests `tests/test_domain_file_display.py` |
| 2026-10-23 | implementation | étape 4 faite : bascule du ⓘ (`unpinned`, `is_pinned`, `refresh_marks`, pied de la bulle, ⓘ rempli), `excerpt_module_id` unique, mots ×3 (REQ-003, UI-002) ; test dans `tests/test_calc_tab_base.py` |
| 2026-10-23 | implementation | étape 5 faite : Δh libre, schéma 1.4 (`DELTA_SCHEMA_VERSION`, `delta_h`), messages ×3, unité et valeur de départ du champ libre (REQ-004) ; tests `tests/test_snow_source.py`, `tests/test_domain_file_display.py` |
| 2026-10-23 | implementation | étape 6 faite : `calc/domains/dependencies.py`, `Field.var`, `snow_source.extra_dependencies` (μ), « Résultats » une ligne par widget, survol champ ↔ résultat, jetons `hover`/`hover-ink` de `theme.json` ; libellés en `richtext.subscripts` (UI-003) ; tests `tests/test_dependencies.py` (nouveau, catalogue), `tests/test_calc_tab_base.py`, contraste dans `tests/test_theme.py` (UI-004, ARCH-001) |
| 2026-10-23 | implementation | étape 7 faite : `calc_tab.Section` (numéro, titre, résumé, point, ▾/▸), `layout_store` clé `sections` fusionnée, `focus_field` ouvre la section et trouve le champ d'une valeur libre, mots courts `sn_fs_*` ×3 (UI-005) ; test dans `tests/test_calc_tab_base.py` |
| 2026-10-23 | implementation | étape 8 faite : `calc/tools/screen_fit.py` (`fitted`, `place`) pour le lecteur de la norme et les fenêtres ⧉ (UI-006, ARCH-002), « Rechercher… Ctrl K » à droite du texte gris (UI-001), indices dans « État du calcul » (UI-003) ; tests `tests/test_screen_fit.py` (nouveau, catalogue), `tests/test_command_palette.py`, `tests/test_domain_file_display.py` |
| 2026-10-23 | testing | étape 9 : documentation (`docs/ui/calc-tab.md`, `tab-snow.md`, `window.md`, `docs/typst/formulas.md`, `docs/domain/loads.md`, `///` de `name-visible` et `calc/i18n/commands.json`), `CHANGELOG.md`, « Nouveautés » 0.125 ×3, exemples reconstruits ; suite complète lancée |
| 2026-10-23 | verification | vérification indépendante : tout ✅ ; deux preuves ajoutées (compilation fr/de/en, clic d'une tuile) ; reste la suite complète (`finish`) |
| 2026-10-23 | completed | suite complète : 3077 passés, 10 ignorés, 2 échecs — `test_linkable_spin` (la liste des champs liables, `delta_h` ajouté) réparé, `test_no_console` vert seul (charge de la suite) ; spec déplacée dans `completed/` |
