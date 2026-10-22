---
id: 2026-10-14-commandes-en-ligne-domaine
titre: Commandes de calcul écrites en ligne dans un domaine
status: verification
cree: 2026-10-14
mis_a_jour: 2026-10-14
source: message écrit
docs: [docs/typst/formulas.md, docs/ui/tab-formulas.md]
---

# Commandes de calcul écrites en ligne dans un domaine — Spécification

## 1. Objectif

L'ingénieur modifie ses domaines `Formules/<id>.typ` à la main et y écrit des commandes de calcul au milieu d'une ligne : après le texte d'un élément de liste (`- $0°$ bis $30°$: #var(…)`), ou suivies d'un texte (`#var(…) --- Auflast`). Depuis la v0.117, Woodcore refuse ces lignes (`text_trailing`, `text_command`), le domaine devient illisible et l'export échoue. Il veut que Woodcore lise toujours ce qu'il écrit à la main, et que les domaines restent à jour avec ses modifications.

## 2. Source

> **T1** — « il y a une erreurs lors de l'import des données: [critical] Échec de l'export (export_failed) … export failed: Formules/eingenlast-auflast.typ: the calculation domain cannot be read -- '#var("ak", domain: ("dead-load", "EL+AL-Dome")) --- Auflast': '--- Auflast' after #var(...) on the same line is refused … Woodcore: 0.118.0 Project: …\<projet>\<projet>.woodcore »
>
> **T2** — « Le problème apparaît à plusieurs endroits: Lorsque je modifie à la main un domaine et que j'écris des choses en ligne, woodcore ne peut plus importer. Règle ce problème. »
>
> **T3** — « Les domaines dans woodcore devrait toujours rester à jour avec les modifications manuelles que je fais. »

Relevé dans le projet de l'ingénieur (4 domaines) : `#var(…) --- Auflast`, `#var(…) $=>$ on pourrait descendre à -0.8 au besoin` (texte après l'appel) ; `- $0°$ bis $30°$: #eq(…)`, `    - #var(…)` (texte avant l'appel, dans des listes imbriquées).

## 3. Exigences fonctionnelles

### REQ-001 — Lire une commande de calcul écrite au milieu d'une ligne
- **Exigence** : `formula_domain.read` doit lire comme un bloc de commande chaque `#var`, `#eq`, `#var-unit`, `#verify` (et `#val`) écrit dans le balisage de premier niveau du corps, quel que soit ce qui le précède ou le suit sur sa ligne (texte, élément de liste, indentation). Le texte autour reste un texte, tel qu'écrit.
- **Source** : T1, T2
- **Priorité** : doit
- **Critère d'acceptation** : les quatre domaines du projet de l'ingénieur se lisent (`state` ≠ `unreadable`), chaque commande en ligne est un élément de commande, et ses résultats sont calculés ; un test reprend les formes `#var(…) --- texte`, `- texte: #eq(…)`, `    - #var(…) $=>$ texte`, deux commandes sur une ligne.

### REQ-002 — L'export n'échoue plus sur ces domaines
- **Exigence** : l'export du projet doit réussir sur un domaine qui ne contient que des commandes en ligne de premier niveau.
- **Source** : T1
- **Priorité** : doit
- **Critère d'acceptation** : un test d'export avec un domaine écrit ainsi passe ; l'export du projet de l'ingénieur (copie, jamais en place) ne lève plus `export_failed` pour ce motif.

### REQ-003 — Une écriture par Woodcore garde la mise en page en ligne
- **Exigence** : quand l'onglet «Formules» réécrit un domaine (enregistrement, renommage), une commande lue en ligne reste sur la ligne où elle était, avec le texte qui la précède et la suit ; la lecture de ce qui est écrit redonne les mêmes éléments.
- **Source** : T3
- **Priorité** : doit
- **Critère d'acceptation** : test aller-retour `read → write_text → read` sur les formes de REQ-001 : mêmes éléments, mêmes lignes (le texte d'un élément de liste et sa commande restent sur une ligne, donc dans l'élément).

### REQ-004 — Ce qui reste refusé
- **Exigence** : une commande de calcul que Python ne peut pas isoler sans changer le texte (dans un bloc de contenu `[…]` d'un autre appel, dans les arguments d'un appel) reste refusée (`text_command`), avec son motif.
- **Source** : principe ARCH-RISK-108
- **Priorité** : doit
- **Critère d'acceptation** : `#box[#var("a", 1)]` est toujours refusé.

## 4. Exigences d'interface (fenêtre, rapport, site)

### UI-001 — Le volet central montre la commande en ligne dans sa phrase
- **Exigence** : dans l'onglet «Formules», une commande lue en ligne apparaît comme une pastille dans le paragraphe du texte qui l'entoure (y compris un élément de liste), et une modification du texte de ce paragraphe ne la sort pas de sa ligne.
- **Source** : T3
- **Langues** : aucune chaîne nouvelle prévue
- **Critère d'acceptation** : `formula_layout.to_paragraphs` / `from_paragraphs` aller-retour sur les formes de REQ-001 (test sans fenêtre).

## 5. Exigences d'architecture

### ARCH-001 — Une seule lecture, sans Qt
- **Exigence** : le découpage reste dans `formula_domain.split_items` (lexer de `typst_paths`, jamais une regex sur `#var(`) ; `formula_layout` reste sans Qt ; l'onglet ne recalcule rien.
- **Source** : principes 1–2 (docs/architecture/principles.md)
- **Critère d'acceptation** : aucun import Qt ajouté dans `calc/domains/` ; revue.

### ARCH-002 — Le principe d'ARCH-RISK-108 tient
- **Exigence** : Typst et Python calculent toujours les mêmes commandes : toute commande de calcul que Typst exécute est un élément que Python calcule, ou le fichier est refusé.
- **Source** : décision v0.117 (ARCH-RISK-108)
- **Critère d'acceptation** : REQ-004 ; `check_text` refuse toujours une commande de calcul restée dans un texte.

## 6. Contraintes

- **CON-001** — Les domaines déjà écrits par Woodcore (une commande par ligne, deux espaces devant) se lisent et s'écrivent exactement comme avant : aucun fichier canonique ne devient `hand_edited`.
- **CON-002** — Ne jamais écrire dans le projet de l'ingénieur : le test travaille sur une copie.

## 7. Décisions prises

- **D-01** — Le refus `text_trailing` (v0.117, 2026-10-11) est levé : le texte après une commande sur sa ligne est un texte comme un autre. Le message reste pour une commande non isolable (REQ-004) via `text_command`. Raison : T2/T3 ; le principe ARCH-RISK-108 tient puisque Python lit désormais la commande.
- **D-02** — (Q-001) Une commande lue en ligne est réécrite sur sa ligne : l'élément de commande porte s'il est collé à ce qui le précède et à ce qui le suit. Prix : deux champs au modèle `Command`, pris en compte par l'écriture, le rangement des textes et le volet central.
- **D-03** — (Q-002) Le dépôt d'une pastille dans un élément de liste ou un titre reste refusé ; à reprendre plus tard.

## 8. Hors périmètre

- Déposer (glisser) une pastille dans un élément de liste ou un titre depuis le volet central (`drop_refusal`) : inchangé, (D-03).
- Garder l'indentation d'une commande seule sur sa ligne (`      #var(…)`) : Woodcore la réécrit avec deux espaces, comme aujourd'hui.

## 9. Idées non retenues comme exigences

—

## 10. Questions

### Q-001 — À l'enregistrement depuis l'onglet, une commande lue en ligne reste-t-elle sur sa ligne ?
- **Pourquoi elle compte** : décide si le modèle d'un élément porte « collé à ce qui le précède / le suit ».
- **Options** : A (recommandée) elle reste sur sa ligne, avec son texte (sinon une commande dans un élément de liste indenté en sortirait au rendu) ; B Woodcore la remet seule sur sa ligne (plus simple, mais change le rendu des listes).
- **Réponse** : A — rester sur sa ligne (2026-10-14).

### Q-002 — Le volet central doit-il aussi permettre de déposer une pastille dans un élément de liste ?
- **Pourquoi elle compte** : élargit `drop_refusal` et le travail de l'onglet.
- **Options** : A (recommandée) pas maintenant — lire et garder ce que vous écrivez à la main d'abord ; B oui, la pastille déposée est collée à la ligne.
- **Réponse** : A — pas maintenant (2026-10-14).

## 11. Critères d'acceptation

- [ ] REQ-001 — les quatre domaines du projet de l'ingénieur se lisent, commandes en ligne calculées
- [ ] REQ-002 — export réussi sur un domaine à commandes en ligne
- [ ] REQ-003 — aller-retour lecture/écriture garde les lignes
- [ ] REQ-004 — `#box[#var(…)]` toujours refusé
- [ ] UI-001 — aller-retour des paragraphes du volet central
- [ ] ARCH-001 — pas de Qt dans `calc/domains/`, lexer réutilisé
- [ ] ARCH-002 — `check_text` refuse toujours une commande de calcul restée dans un texte
- [ ] CON-001 — fichiers canoniques inchangés (tests existants verts)
- [ ] Documentation : `docs/typst/formulas.md`, `docs/ui/tab-formulas.md` si concerné, `docs/decisions.md`, `CHANGELOG.md`, «Nouveautés» fr/de/en.
- [ ] Tests : `tests/test_formula_domain.py` étendu, et passe.

## 12. Traçabilité

| Source | Élément | Statut |
|---|---|---|
| T1 | REQ-001, REQ-002 | capturé |
| T2 | REQ-001, D-01 | capturé |
| T3 | REQ-003, UI-001, Q-001 | capturé, question |

## 13. Revue d'architecture

Revue `architecture-reviewer` du 2026-10-14 — **APPROUVER AVEC RÉSERVES**.

- Modules : `formula_domain` (`Command`, `_top_level_lines`, `split_items`, `tidy_items`, `body_of`, `check_text`, `check_body`), `formula_layout` (`_tokens`, `to_paragraphs`, `from_paragraphs`), `formula_tab_blocks.py:77` (nouvelle `Command` à la validation d'un bloc), `formula_tab.py` (chaînes `fm_text_trailing`). Aucun schéma JSON touché.
- ARCH-RISK-001 — un seul champ `glued` plutôt que deux. **Non retenu tel quel** : les textes sont reconstruits par le volet central à partir de chaînes (`from_paragraphs`), un drapeau porté par un texte s'y perdrait ; seules les commandes gardent leur identité (`id(c)`). Retenu : deux drapeaux sur la **commande** seule (`glued_before`, `glued_after`), les textes n'en portent pas ; l'écriture et le rangement les lisent sur la commande voisine.
- ARCH-RISK-002 (bloquant) — `tidy_items` ne retire rien du côté collé d'un texte et ne jette pas un texte collé fait de blancs (`" "` entre deux commandes) ; la fusion de deux textes est inchangée.
- ARCH-RISK-003 (bloquant) — `formula_tab_blocks.py:77` recopie les deux drapeaux.
- ARCH-RISK-004 — un appel suivi immédiatement de `.x`, `[` ou `(` reste refusé (`text_command`).
- ARCH-RISK-005 — le crochet `hashed` note si le `#` est au premier niveau (pile du lexer de longueur 1, profondeur 0) ; seul celui-là coupe.
- ARCH-RISK-006 — `#val` : n'est coupé en milieu de ligne que ce que Python calcule (`COMPUTING`) ; `#val` dans une phrase reste du texte, comme aujourd'hui (option recommandée, sans désaccord Python/Typst).
- ARCH-RISK-007 — `to_paragraphs` impose la jointure d'un élément collé ; `from_paragraphs` efface le drapeau en bord de paragraphe et garde les mêmes objets.
- ARCH-RISK-008 — `text_trailing`, `_after_call`, `SEPARATED`, `_PUNCTUATION` et les trois chaînes `fm_text_trailing` deviennent inatteignables : supprimés.
- ARCH-RISK-009 — un commentaire `//` après un appel seul sur sa ligne : inchangé.
- ARCH-RISK-010 — le refus v0.117 n'est pas dans `docs/decisions.md` : nouvelle entrée pour D-01…D-03 ; `docs/typst/formulas.md` (l. 88, 164) réécrit.

## 14. Plan d'implémentation

1. `formula_domain` : `Command.glued_before/glued_after` ; `_top_level_lines` rend aussi les `#` de premier niveau ; `split_items` coupe à chaque commande de `COMPUTING` de premier niveau (une commande seule sur sa ligne : comme avant) ; refus d'une suite d'appel ; `tidy_items`, `body_of`, `check_body` tiennent compte des drapeaux ; code `text_trailing` retiré. → REQ-001, REQ-003, REQ-004, ARCH-002, CON-001.
2. `formula_layout` : `_tokens`/`to_paragraphs`/`from_paragraphs` avec les drapeaux. → UI-001.
3. Onglet : `formula_tab_blocks.py:77` recopie les drapeaux ; clés `same()` avec les drapeaux ; chaînes `fm_text_trailing` retirées. → ARCH-RISK-003, -008.
4. Tests `tests/test_formula_domain.py` : formes de REQ-001, aller-retour, `#box[#var()]` et `#var(…)[x]` refusés, fichier canonique inchangé, copie des 4 domaines du projet de l'ingénieur lue et calculée (sautée si le dossier manque), export d'un domaine en ligne ; volet central aller-retour. → REQ-001…004, UI-001.
5. Docs : `docs/typst/formulas.md`, `docs/ui/tab-formulas.md` si concerné, `docs/decisions.md`, `CHANGELOG.md`, «Nouveautés» fr/de/en.

## 15. Vérification

_(à venir)_

## 16. Journal d'avancement

| Date | Statut | Fait / reste |
|---|---|---|
| 2026-10-14 | draft | spécification extraite du message ; deux questions ouvertes |
| 2026-10-14 | specified | Q-001 → A, Q-002 → A ; D-02, D-03 |
| 2026-10-14 | reviewed | revue d'architecture (avec réserves) et plan |
| 2026-10-14 | approved | approuvée par l'ingénieur |
| 2026-10-14 | testing | plan 1–5 fait : formula_domain (glued_before/after, split, tidy, body_of, item_key), formula_layout, onglet (drapeaux recopiés, fm_text_trailing retiré), tests test_formula_domain (34 ok) et test_formula_tab (20 ok), docs, décision, CHANGELOG, pages 0.119.0 fr/de/en |
