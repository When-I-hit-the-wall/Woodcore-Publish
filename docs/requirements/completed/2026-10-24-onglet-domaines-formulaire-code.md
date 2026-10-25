---
id: 2026-10-24-onglet-domaines-formulaire-code
titre: Onglet Domaines — Formulaire, Code et Affichage, la fin des pastilles
status: completed
cree: 2026-10-24
mis_a_jour: 2026-10-25
source: issue GitHub #113 (prototype « Domaines de calcul » validé par l'ingénieur le 24.10.2026, version 2)
docs: [docs/ui/tab-formulas.md, docs/ui/building-a-tab.md, docs/architecture/principles.md, docs/typst/formulas.md, docs/typst/command-docs.md, docs/requirements/completed/2026-10-11-formules-blocs-en-ligne-et-niveau-manuel.md, docs/decisions.md]
---

# Onglet Domaines — Formulaire, Code et Affichage — Spécification

## 1. Objectif

Refaire l'onglet « Domaines » (`tab_formula`, groupe Référence, où l'ingénieur écrit ses propres calculs dans `Domains/<id>.typ`) d'après le prototype validé : le texte-à-pastilles de la v0.117–0.122 cède la place à trois modes sur le même fichier, **Formulaire** (une rangée par ligne du fichier), **Code** (le fichier coloré, avec les arguments de la ligne du curseur) et **Affichage** (le rendu réel de Typst, ses options). Les pastilles et le mode « Les deux » disparaissent. La spec couvre aussi les défauts relevés dans la vraie sortie de Woodcore 0.122 (messages en anglais, une faute devenue quatre erreurs, champ « Article » qui écrit `norm-ref:`, domaine imprimé en un seul paragraphe…) et remplace les décisions D-01 à D-05 de l'issue #40.

## 2. Source

La source, mot pour mot et coupée en points T, est dans [docs/history/2026-10-24-onglet-domaines-formulaire-code-source.md](../../history/2026-10-24-onglet-domaines-formulaire-code-source.md) (déplacée le 24.10.2026 pour tenir la spec sous 100 KB ; rien n'y est changé).

## 3. Exigences fonctionnelles

État actuel relevé dans le code (master `a9cae26`) : `formula_domain.py` (1366 lignes) a `parse_domain`, `patched`, `compute`, `key_from_symbol`, `typst_formula`, `display_formula`, `header_of` (`#domain("id", label:)[`), `new_domain`, `variables_of`, `resolve_import`, `variable_domains`, `DomainError(code, message, **values)` avec un `code` que la fenêtre traduit. Il n'a **ni `infer_line`, ni lecture de `#calc-defaults`** (aucune occurrence dans `formula_domain.py` ; `new_domain` n'écrit que l'en-tête), **ni traduction symbole → clé d'un calcul tapé**, ni ligne et colonne d'erreur. `units.FormulaError` est une `ValidationError` sans code traduisible. `display_options.py` : `NORM_REF = Option("norm-ref", …)`, la note `FINE` attend toujours les contrôles des arguments fins. `formula_tab_domains.py` a déjà `drop_refusal` et `fm_drop_order` (un déplacement refusé, une rangée à la fois) ; aucun `Key_Up`/`Alt` dans l'onglet (le « Alt+↑/↓ retiré » du prototype n'a rien à retirer). `views.py` : `CALC_VIEWS = ("calc", "display")` ; il n'y a pas de vue « Code » distincte (la clé `typst` s'appelle déjà « Affichage »). `formula_layout.py` (161 lignes) place les pastilles ; `richtext.TypstHighlighter`, `module_pane.ModulePane`, `norm_bubble`, `blink.py`, `grouped_list` existent. Les spécifications `2026-10-14-commandes-en-ligne-domaine` (status `verification`) et #40 (`completed`) régissent encore le texte entre les commandes.

### REQ-001 — `infer_line` : la ligne déduite de ce qu'on tape
- **Exigence** : Woodcore doit, dans `calc/domains/` sans Qt, déduire d'une saisie la commande (`verify` si la saisie contient une relation `<=`, `>=`, `<`, `>`, `!=`, `≤`, `≥` ; `var` si « symbole = nombre unité » ; `eq` si « symbole = expression » ; sinon `texte`) et la clé du symbole (`M_(y,d)` → `M_y_d` par `key_from_symbol`, rendue unique parmi les clés prises), et remplir les champs de la commande (var : symbole, valeur, unité, libellé ; eq : symbole, calcul, unité, libellé ; verify : relation, libellé ; texte : le texte).
- **Source** : T10, T33, T35, T36
- **Priorité** : doit
- **Critère d'acceptation** : `tests/test_formula_domain.py` (ou un fichier voisin) couvre « h = 240 mm » (var), « M_d = q_d * l^2 / 8 » (eq), « sigma_(m,d) <= f_(m,d) » (verify), une relation avec `≥`, un nombre sans unité, une unité inconnue, un symbole déjà pris (clé suffixée), un texte libre, et le choix explicite d'une commande qui l'emporte sur la déduction.

### REQ-002 — Le calcul tapé en symboles, écrit en clés
- **Exigence** : Woodcore doit traduire un calcul tapé avec les symboles affichés (`sigma_(m,d) / f_(m,d)`) en clés du fichier (`sigma_m_d / f_m_d`) et l'inverse pour l'affichage, selon la table symbole → clé des lignes **au-dessus** de la ligne. Un symbole est tapable s'il est un nom indicé simple (`f_(m,d,"Tab")`, `q_k`, espaces après les virgules admis : `sigma_(m, d)`) ; un symbole composé comme (g<sub>k</sub> + a<sub>k</sub>)<sub>gew</sub>, ou que porte déjà une autre clé, se tape par sa clé.
- **Source** : T12, T38, T39
- **Priorité** : doit
- **Précision (revue, ARCH-RISK-004)** : cette traduction **existe déjà** — `formula_domain.typst_formula` (symboles ou clés → clés, nombres suivis d'une unité enveloppés), `display_formula` (clés → symboles), `_names` (toutes les écritures d'une variable) et `key_from_symbol` (`M_(y,d)` → `M_y_d`, grec, clé unique) ; elles servent le champ « Calcul » de la v0.117. L'exigence est donc de les **compléter**, non d'en écrire une seconde : (a) la table symbole → clé est celle des lignes **au-dessus** de la ligne (l'appelant la donne), (b) les espaces après les virgules d'un indice sont admis (`sigma_(m, d)` = `sigma_(m,d)`), (c) un symbole porté par deux clés n'est tapable que par la clé de la **dernière** (aujourd'hui `_names` garde la première en silence) et le champ le dit, (d) un symbole composé ne se tape que par sa clé.
- **Critère d'acceptation** : test sans Qt, sur `tests/projet-exemple/Domains/poutre-p1.typ` : pour chaque `eq`, `typst_formula(display_formula(calcul, table), table)` donne un calcul **qui calcule la même valeur** que `calcul` (l'égalité d'octets n'est pas due : `12 "N"` revient `(12 "N")`) et, quand le calcul ne porte aucune unité écrite, le même texte ; cas limites `f_(m,d,"Tab")`, `sigma_(m, d)`, `gk_ak_gew`, un symbole porté par deux clés ; les tests existants de `typst_formula` et `display_formula` passent inchangés.

### REQ-003 — Le contrôle d'ordre d'un groupe déplacé
- **Exigence** : Woodcore doit refuser le déplacement d'une ligne ou d'un groupe de lignes quand une ligne passerait au-dessus de ce dont elle est calculée — pour chaque ligne du groupe et pour celles qui restent — et dire la raison : « Déplacement refusé : W<sub>y</sub> utilise b, qui serait plus bas. ». Le contrôle étend celui de `fm_drop_order` (une rangée) au groupe, dans le modèle (sans Qt).
- **Source** : T22, T52, T53
- **Priorité** : doit
- **Critère d'acceptation** : test du modèle : un groupe de trois lignes déplacé sous une ligne qui en dépend est refusé avec la phrase ; le même groupe déplacé ailleurs est accepté et garde son ordre interne ; le refus d'une rangée seule reste celui d'aujourd'hui.

### REQ-004 — `#calc-defaults` lu et écrit option par option ; `presets: "block"` pour un domaine nouveau
- **Exigence** : Woodcore doit lire et écrire une seule ligne `#calc-defaults(…, scope: "domain")` sous l'en-tête d'un domaine, option par option (`presets: "block"`, `label-position`, `descr-position`, `norm-position`, `style` — les options que `calc-default-names` de `lib/formula.typ` accepte) : cocher une option l'écrit (valeurs proposées : `label-position: "after"`, `descr-position: "footnote"`, `norm-position: "line-right"`, `style: "normal"`), la décocher la retire, plus rien de coché retire la ligne. Un domaine **nouveau** reçoit `#calc-defaults(presets: "block", scope: "domain")` ; un domaine existant garde ce qu'il a.
- **Précision (revue, ARCH-RISK-005)** : `parse_domain` n'a pas à changer : la ligne est aujourd'hui un **item de texte** (`calc-defaults` n'est pas dans `COMMANDS`, `check_text` ne la refuse pas) que `body_of` écrit tel quel ; le lecteur et l'écrivain sont un module sans Qt (`formula_defaults.py`) qui trouve la ligne **dans les items de texte**, lit ses arguments sans perte (ceux qu'il ne connaît pas — `level`, `display`, `unit` —, et l'étiquette `<ZT-01-presets>` que `unfold.py` écrit derrière, sont gardés tels quels) et la réécrit à la même place ; sans la ligne, la première option cochée en pose une comme premier item de texte, sous l'en-tête. `new_domain` en reçoit un paramètre ; `unfold.py` garde son écriture de la ligne, que ce lecteur relit.
- **Source** : T9, T73, T77
- **Priorité** : doit
- **Critère d'acceptation** : test sans Qt : `new_domain` + première écriture donne le fichier avec la ligne ; un fichier existant sans la ligne est relu et réécrit à l'identique ; cocher, décocher, tout décocher fait les trois écritures attendues ; une ligne `#calc-defaults` qu'écrit `unfold.py` ou la main de l'ingénieur est lue sans perte (ses arguments inconnus gardés tels quels). Compiler Panne P2 avec la ligne imprime une ligne par valeur, non dix-sept notes.

### REQ-005 — Les erreurs rendues comme un code et des valeurs
- **Exigence** : `units.FormulaError` et `formula_domain.DomainError` doivent rendre un **code** et ses **valeurs** (comme `DomainError` le fait déjà pour ses refus) que la fenêtre traduit en de, fr, en (`fm_e_*`) sans couper à 80 caractères ; le texte anglais reste celui que Typst et le rapport montrent. Le message d'un refus de calcul n'est plus l'anglais brut dans une fenêtre en français.
- **Source** : T61, T80
- **Priorité** : doit
- **Critère d'acceptation** : un test énumère chaque code de `FormulaError`/`DomainError` et vérifie qu'il a un mot `fm_e_*` en trois langues avec ses valeurs ; `tests/test_units.py` passe inchangé (l'algèbre ne change pas, seule l'enveloppe de l'erreur) ; « eq: no variable named 'L' here » s'affiche en français avec la liste des noms connus entière.

### REQ-006 — Une faute est dite une fois
- **Exigence** : Woodcore doit dire une faute à sa ligne **une seule fois**, avec le nombre de lignes plus bas qui en dépendent (« 3 lignes plus bas en dépendent »), et ne pas mettre en erreur chacune de ces lignes : la ligne fautive est rouge, les dépendantes sont signalées comme dépendantes (état distinct, non rouge à elles seules). Cette règle vaut pour l'état, la rangée et la marge du Code.
- **Source** : T58, T81
- **Priorité** : doit
- **Précision (revue, ARCH-RISK-006)** : `compute` continue après une erreur et une clé que la ligne fautive aurait définie est alors inconnue des suivantes — d'où les quatre erreurs. Le modèle garde la liste des clés **cassées** ; une ligne dont les seuls noms inconnus sont des clés cassées reçoit `Result.blocked_by` (l'indice de la cause) et **non** `error` ; une ligne fautive pour une autre raison (une vraie faute de plus) reste une erreur de plein droit. L'état compte les lignes `blocked_by` d'une cause.
- **Critère d'acceptation** : test sur Poutre P1 avec `L` pour `l` dans M<sub>d</sub> : l'état ne contient qu'**une** erreur rouge (M<sub>d</sub>) avec le compte « 3 lignes en dépendent » (σ<sub>m,d</sub>, la vérification, η) ; corriger la faute efface les trois ; une seconde faute indépendante dans une des trois reste une erreur.

### REQ-007 — La ligne de l'erreur est celle de Typst, et la fenêtre nomme la ligne du domaine
- **Exigence** : une erreur de lecture (parenthèse oubliée) doit être donnée à la **ligne et la colonne que Typst donne** (là où la parenthèse s'ouvre : ligne 19, colonne 5 dans l'exemple de l'issue), et non à celle où Woodcore bute (ligne 24, colonne 1) ; pour un nom inconnu ou des unités incohérentes — dont Typst ne nomme pas la ligne du domaine (« while calling `get` at lib/formula.typ:1510 ») — la fenêtre dit « ligne N de `Domains/<id>.typ` ». **Décision de la revue (ARCH-RISK-010)** : pas de `typst compile` (lent, Typst peut manquer) ; une faute de lecture se place par le **délimiteur ouvert** — au bout du texte, l'ouvrant non fermé le plus intérieur que le lexeur de `typst_paths` a vu, qui est ce que Typst nomme —, dans un module sans Qt (`formula_errors.py`), contrôlé par un test qui compare avec `typst compile` quand le moteur est là ; une erreur de calcul est placée par l'indice de l'item (`formula_rows.item_lines`), que Woodcore connaît.
- **Source** : T58, T84, T86, T98
- **Priorité** : doit
- **Critère d'acceptation** : test sur le fichier de l'issue (parenthèse oubliée de `#var(`) : ligne 19, colonne 5 ; test d'un nom inconnu à la ligne 13 : « ligne 13 de `Domains/panne-p2.typ` ».

### REQ-008 — « Article » est `norm-section:`
- **Exigence** : le champ « Article » doit lire et écrire `norm-section:` ; `norm-ref:` est lu d'un fichier ancien (et réécrit en `norm-section:` à la prochaine écriture de la ligne) ; jamais les deux à la fois. `display_options.NORM_REF` change en conséquence (ou disparaît avec `SPECS['var']` et `SPECS['eq']`, REQ-009). **Précision (revue)** : `from_call` garde `norm-section` et `norm-ref` dans `Command.options` comme des arguments nommés quelconques ; la lecture de `norm-ref` → champ et sa réécriture en `norm-section` sont dans le modèle (`formula_domain`), non dans l'onglet.
- **Source** : T17, T29, T79
- **Priorité** : doit
- **Critère d'acceptation** : test : un `#var` de γ<sub>G</sub> avec `norm-section: "Tableau 1"` montre « Tableau 1 » dans le champ ; le modifier écrit `norm-section:` seul et le fichier compile ; un fichier avec `norm-ref:` est lu, le champ est rempli, l'écriture le remplace.

### REQ-009 — Les arguments fins de la ligne
- **Exigence** : le module « Arguments de la ligne » doit offrir **tous** les arguments listés (T44) dont les valeurs viennent de `lib/display-presets.json` (`fine-values`, `fine-keys`) — ni liste en dur, ni second dictionnaire ; *auto* n'écrit rien. **Correction de la revue (ARCH-RISK-003)** : cette lecture existe — `calc/line_display.py` (`display_args(command)`, `fine_values()`) est la liste unique que l'Affichage de la neige et `unfold` emploient, et `unfold_display.set_display` accepte déjà ces noms. Le module la **réemploie** ; il ne passe pas par `display_options.SPECS`, dont les trois entrées `var`, `eq`, `verify` (et leur note `FINE`, leur `NORM_REF` et le mot `ds_opt_norm_ref`) ne servent plus que l'ancien panneau des pastilles : elles sont **retirées** si une recherche montre qu'aucun autre lecteur ne les emploie (`display_view.py:657`, `tests/test_display_view.py`), sinon seul `NORM_REF` est corrigé (REQ-008). Les champs qui ne sont pas d'affichage (clé, symbole, valeur, unité, label, descr, norm, norm-section, calcul, as-unit) viennent du modèle `Command`. `line_display.EXTRA` offre aussi `role` à `var`, que la liste de T44 omet : gardé, le moteur l'accepte (`lib/formula.typ:1380`).
- **Source** : T44, T45, T46, T48, T78
- **Priorité** : doit
- **Critère d'acceptation** : un test compare les arguments proposés par commande à `line_display.display_args` et leurs valeurs à `fine-values` (ajouter une valeur au JSON la fait apparaître sans toucher au code) ; chaque valeur écrite par le module compile (`check-fine`) ; `tests/test_display_view.py` passe.

### REQ-010 — Une variable liée s'affiche sous son vrai symbole et son vrai libellé
- **Exigence** : une variable liée doit montrer le **symbole de sa source** (g<sub>k</sub> + a<sub>k</sub>)<sub>gew</sub>, non sa clé (`gk_ak_gew`), et le libellé lu dans l'export (« Charges permanentes »), non « repris de dead-load / EL+AL-Dach ohne Wasser » ; l'origine « ↗ Neige · SL » vient du nom de l'onglet source.
- **Précision (revue, ARCH-RISK-006)** : `resolve_import` rend (valeur, unité) et **ne change pas** (CON-004) ; le symbole, le libellé et l'onglet source viennent d'un lecteur **voisin** (`formula_links.linked_info`) qui lit la même donnée (`data/calculations.json`, ou le domaine de l'onglet) ; `compute` le reçoit en paramètre facultatif et en remplit `Result.symbol`, `.label`, `.origin`, que `variables_of` et `variable_domains` emploient.
- **Source** : T28, T63, T82
- **Priorité** : doit
- **Critère d'acceptation** : test sur Panne P2 (ou son équivalent dans `tests/projet-exemple`) : la rangée liée de la charge permanente porte le symbole composé et le libellé « Charges permanentes ».

### REQ-011 — Les avertissements orange et l'état
- **Exigence** : l'état du domaine doit produire en **orange** (le fichier se compile) : une vérification qui ne passe pas ; une unité demandée qui n'est pas celle du résultat ; un domaine de l'onglet lu par son nom (`domain: "poutre-p1"`) tant qu'il n'est pas inclus plus haut dans le rapport (Typst s'arrêterait : « no domain … is declared above this line ») — **portée fixée par la revue (ARCH-RISK-011)** : pour chaque document dont une section inclut le domaine **lisant**, le domaine **lu** doit être inclus plus haut dans le même document (ordre des sections de `structure_nodes.section_files`, puis ordre des lignes) ; un domaine inclus nulle part ne donne pas cet avertissement ; un domaine sans `presets: "block"` (« l'Affichage imprime en un seul paragraphe »), qui mène aux options du domaine. Le **rouge** reste pour une erreur de lecture, un nom inconnu, des unités qui ne s'additionnent pas, un lien introuvable.
- **Source** : T13, T14, T32, T57, T58, T59
- **Priorité** : doit
- **Critère d'acceptation** : test de l'état sur h = 200 mm (vérification qui échoue : orange), sur un domaine qui en lit un autre non inclus (orange), sur un domaine sans la ligne `calc-defaults` (orange, avec renvoi aux options) ; le trait de la rangée a la couleur de son état (UI-009).

### REQ-012 — Le fichier reste la seule source ; une ligne cassée n'écrit rien
- **Exigence** : chaque mode (Formulaire, Code, Affichage) doit écrire le fichier `.typ` et le relire ; aucun état de l'onglet ne survit hors du fichier (sauf la sélection et l'annulation). Une faute de frappe en Code casse la ligne jusqu'à correction : l'état le dit et le fichier n'est écrit qu'une fois relu sans erreur de lecture.
- **Source** : T24, T68
- **Priorité** : doit
- **Critère d'acceptation** : test : une modification dans chaque mode se retrouve dans les deux autres ; un fichier édité en Code avec une parenthèse oubliée n'est pas écrit sur disque (le fichier d'avant est intact) et l'état nomme la ligne.

### REQ-013 — Lier une variable : nom tapé, fenêtre, correctif du message
- **Exigence** : Woodcore doit offrir trois entrées vers le même lien `#var("q_k1", domain: ("snow-load", "SL"))` écrit au-dessus de la ligne : (a) le **nom tapé** dans un calcul — la complétion propose les variables du domaine par clé ou par symbole (et écrit le symbole), puis celles du projet (« q<sub>k</sub> · Neige · SL · 1.115 kN/m² ») ; (b) la fenêtre « Lier une variable… » (UI-014) ; (c) le **correctif du message** d'un nom inconnu que l'export connaît : « Lier q_k1 depuis Neige · SL ». Les trois lisent la même source de variables liables que l'onglet Variables et les champs (#42, #114).
- **Source** : T11, T40, T54, T55, T56
- **Priorité** : doit
- **Critère d'acceptation** : test : taper « q_k » propose « Neige · SL » ; choisir écrit le lien au-dessus et le nom devient connu ; l'état d'un nom inconnu présent dans l'export offre le correctif, qui écrit le même lien ; les trois chemins produisent des fichiers identiques.

### REQ-014 — Extraits de la norme par clause citée
- **Exigence** : pour chaque ligne qui cite une clause relevée, Woodcore doit montrer la bulle de la norme (l'**i**), l'épingler sous les résultats au clic, la retirer au second clic (issue #96), ouvrir la partie de la norme au Ctrl+clic ; les extraits (édition, page, rectangle) sont relevés **dans l'édition nommée de `ExternalFiles/000-Normes/`**, jamais de mémoire, pour les huit clauses du prototype (SIA 260, 261, 265) ; une clause sans relevé montre son nom, sans bulle. La brique est celle des onglets de calcul (`norm_bubble.BubbleController`, `norm_reader`). **Précision (revue, ARCH-RISK-012)** : les extraits sont rangés par fichier de norme et par id (`calc/norms/excerpts.py`) ; une citation d'un `#var` (`norm: "SIA 265"`, `norm-section: "Tabelle 8"`) n'y a pas d'entrée : `norms.excerpts.for_citation(norm, section, lang)` la résout (l'édition nommée, la clause telle que l'édition la nomme), sans table à part ; plusieurs extraits pour une même clause, ou aucun : pas de bulle.
- **Source** : T28, T64, T90
- **Priorité** : doit
- **Critère d'acceptation** : test : chacune des huit clauses a un extrait dont le rectangle est contenu dans la page du PDF de l'édition nommée ; une clause hors liste n'a pas de bulle et ne lève pas d'erreur ; l'épinglage et son retrait au second clic passent par la brique existante.

### REQ-015 — Un domaine déplié d'un onglet spécialisé
- **Exigence** : un domaine que Woodcore a écrit d'une vérification (carte « Vérification dépliée », `formula_tab_unfold`) doit s'afficher dans **les mêmes rangées** ; ses états (« modifiée hors de Woodcore », « conflit », « donnée changée », « valeur de l'ingénieur », « ligne supprimée »…) paraissent sur le trait de la rangée, non plus sur le contour d'une pastille ; la carte garde ses boutons (« Meine behalten » et ses pareils).
- **Source** : T97
- **Priorité** : doit
- **Critère d'acceptation** : `tests/test_formula_tab_unfold*.py` (ou son successeur) : pour chaque état de `unfold`, la rangée correspondante a le trait et le mot attendus ; aucun état n'est perdu par rapport à la v0.122.
- **Décision de conception laissée à la revue** : la couleur de chaque état (rouge/orange/bleu…) n'est pas dans le prototype.

### REQ-016 — Le texte de l'ingénieur et ses commandes en ligne restent intacts
- **Exigence** : le texte de l'ingénieur entre les commandes doit devenir des rangées de texte « imprimées telles qu'écrites » ; une commande écrite **dans** une ligne de texte (`- $0°$ bis $30°$: #eq(…)`, spec `2026-10-14-commandes-en-ligne-domaine`) et le collage aux paragraphes (`formula_layout.from_paragraphs`) ne doivent **pas changer ce que Typst imprime** ni le contenu du fichier. **Q-001 (A), D-16** : la rangée est une rangée de texte qui contient sa commande, la commande un bloc non éditable à l'intérieur ; une chaîne d'items collés (`same_line`) est **une** rangée (ARCH-011).
- **Source** : T28, T95 ; CON-001
- **Priorité** : doit
- **Critère d'acceptation** : tous les fichiers de `tests/projet-exemple/Domains/` et des fixtures de `test_formula_domain.py` qui portent un texte avec commande en ligne sont relus et réécrits **octet pour octet** sans modification ; le PDF compilé avant/après une édition d'une autre ligne est identique.

### REQ-017 — `examples/` tient ses promesses
- **Exigence** : `examples/data/formulas.json` annonce `poutre-p1`, mais `examples/` n'a pas de dossier `Domains/` ; Woodcore doit supprimer ce désaccord (fournir le domaine à `examples/`, ou ne plus l'annoncer).
- **Source** : T87
- **Priorité** : devrait
- **Critère d'acceptation** : un test refuse toute entrée de `examples/data/formulas.json` dont le fichier de domaine n'existe pas ; `examples/` se compile comme avant.

### REQ-018 — Le domaine de l'onglet répond à « Ouvrir l'onglet » (inféré)
- **Exigence** : l'onglet Domaines devrait déclarer `GRAPH_KIND = "formula"` (le nœud `formula:<id>` existe déjà dans `dependency_graph.KINDS`) et répondre à `MainWindow.open_object` (`lists_object` et `open_object`, que `source_editor` définit déjà) pour ouvrir un domaine par son id, pour que le bouton « Ouvrir l'onglet » de l'onglet Variables (#114, REQ-009) l'ouvre sur le bon domaine. L'issue #113 ne le demande pas : l'**option A** de la Q-002 de #114 laisse Domaines sans cas ouvert « pour que #113 le fasse ».
- **Source** : inféré de la spec #114 (D-9, Q-002), principes « domain logic independent of the UI »
- **Priorité** : devrait (revue : une ligne de déclaration et son test ; sans elle, « Ouvrir l'onglet » de #114 passe devant sans ouvrir de domaine)
- **Critère d'acceptation** : `open_object("<kind>:<id>")` sur un id de domaine l'ouvre dans l'onglet ; si non retenu, #114 le laisse inactif (sans régression).

### REQ-019 — Les survols liés viennent du modèle
- **Exigence** : les dépendances des survols (jaune la ligne survolée, bleu ce dont elle se calcule, vert ce qui l'utilise, rien d'autre) doivent être lues de `formula_domain.compute` (les opérandes de chaque ligne), non recalculées dans l'onglet.
- **Source** : T65 ; principe « domain logic is independent of the UI »
- **Priorité** : doit
- **Critère d'acceptation** : test sans Qt : pour Poutre P1, `dependencies(ligne)` rend les opérandes et les utilisateurs ; l'onglet n'importe pas le parseur de formule.

## 4. Exigences d'interface (fenêtre, rapport, site)

### UI-001 — Trois modes
- **Exigence** : l'onglet doit offrir au-dessus de la fenêtre **Formulaire · Code · Affichage** ; **décision de la revue (ARCH-004, ARCH-RISK-009)** : deux clés de vue nouvelles de `views.py`, `form` (« Formulaire ») et `code` (« Code »), et la vue `display` existante ; `CALC_VIEWS` ne change pas. « Les deux », les pastilles (`PillPainter`, `FormulaText`, `formula_layout`) et le texte-à-pastilles disparaissent. Pas de raccourci Alt+↑/↓.
- **Source** : T8, T15, T24, T92
- **Langues** : fr / de / en
- **Critère d'acceptation** : `tests/test_views.py` et `tests/test_formula_tab.py` : l'onglet a ces trois vues dans cet ordre, aucune pastille n'est peinte, chaque mode écrit et relit le fichier (REQ-012).

### UI-002 — Le volet de gauche
- **Exigence** : la liste montre les domaines de l'onglet, chacun avec son état (✔ 70 %, 1 ✘), puis les groupes des onglets spécialisés (Neige, Vent, Traction…) **repliés** ; les archives en bas ; « Domaine » et « Dupliquer » ; les symboles y sont ceux de l'affichage (non le code Typst `c_("red", "b/h")`).
- **Source** : T25, T83
- **Langues** : fr / de / en
- **Critère d'acceptation** : test de l'arbre : un domaine d'un onglet spécialisé n'a pas ses lignes dépliées par défaut ; aucun item ne contient `_("` ; l'état d'un domaine est le compte de ses lignes réussies.

### UI-003 — Le centre : nom, fichier, légende
- **Exigence** : la ligne du nom et de l'id, le chemin du fichier (`Domains/panne-p2.typ`), la légende des survols, puis le mode choisi.
- **Source** : T26
- **Langues** : fr / de / en
- **Critère d'acceptation** : test du texte de l'en-tête pour Panne P2 ; capture à comparer au prototype.

### UI-004 — Les modules de droite
- **Exigence** : à droite, les modules déplaçables et repliables de la brique commune (#94, #95 : `ModulePane`), dans l'ordre **État du domaine · Arguments de la ligne · Résultats · Variables du domaine · extraits de la norme épinglés**.
- **Source** : T27
- **Langues** : fr / de / en
- **Critère d'acceptation** : test : les cinq modules existent dans cet ordre, déplaçables et repliables ; aucun module nouveau de la brique n'est dupliqué dans l'onglet.

### UI-005 — Le Formulaire : une rangée par ligne
- **Exigence** : chaque ligne du fichier est une rangée : poignée ⋮⋮, numéro de ligne, étiquette de commande (`var`, `eq`, `verify`, `texte`), puis ses champs (`var` : symbole composé, `=`, valeur, unité, **i**, libellé ; `eq` : symbole, `=`, calcul en symboles (REQ-002), unité (auto ou une unité de la dimension du résultat), `=`, résultat, **i** ; `verify` : relation en symboles, les deux valeurs, ✔ ou ✘ ; variable liée : symbole, valeur, « ↗ Neige · SL », libellé (REQ-010) ; texte : imprimé tel qu'écrit).
- **Source** : T28, T38
- **Langues** : fr / de / en
- **Précision (revue, ARCH-011)** : une rangée est **un item du domaine** (une commande, ou un texte qui peut tenir plusieurs lignes du fichier), une chaîne d'items collés (`same_line`) étant une seule rangée ; son numéro est celui de sa première ligne **dans le fichier**.
- **Critère d'acceptation** : pour Poutre P1, le nombre de rangées égale le nombre d'items regroupés par la colle, leurs numéros sont ceux des lignes du fichier (la rangée qui porte le numéro N commence à la ligne N) ; les valeurs affichées sont celles de `formula_domain.compute` ; modifier un champ réécrit la ligne.

### UI-006 — La rangée choisie
- **Exigence** : la rangée choisie montre dessous la variable de calcul (la clé), le libellé, la norme, l'article (`norm-section:`, REQ-008) et la description ; ses **autres** arguments sont dans le module « Arguments de la ligne » (UI-012).
- **Source** : T17, T29, T45
- **Langues** : fr / de / en
- **Critère d'acceptation** : test : choisir une rangée affiche ces cinq champs ; en modifier un l'écrit dans la ligne.

### UI-007 — Supprimer et « Annuler »
- **Exigence** : un petit × à droite de chaque rangée supprime la ligne ; le message qui suit offre « Annuler » (**portée : Q-002, A / D-17** — la dernière suppression et le dernier geste de plusieurs lignes, en une étape) ; les lignes qui utilisaient la variable supprimée passent en erreur dans l'état, avec leur cause (REQ-006).
- **Source** : T20, T30, T96
- **Langues** : fr / de / en
- **Critère d'acceptation** : test : supprimer b rend W<sub>y</sub> en erreur avec « nom inconnu b » ; « Annuler » rend le fichier à l'identique (octet pour octet) ; après un déplacement de groupe ou un « Valider » de liens, « Annuler » rend le fichier d'avant ; un geste plus récent remplace l'étape ; si le fichier a changé sur le disque depuis le geste, « Annuler » ne l'écrase pas et le dit.

### UI-008 — Le + entre deux rangées
- **Exigence** : au survol entre deux rangées, un + offre var, eq, verify, texte, lier une variable ; la ligne ouverte a sa pastille fixée sur la commande choisie et les champs de UI-010.
- **Source** : T10, T31
- **Langues** : fr / de / en
- **Critère d'acceptation** : test : le + entre les lignes 3 et 4 écrit la nouvelle ligne en 4 ; « lier une variable » ouvre UI-014 avec la ligne choisie pour cible.

### UI-009 — Traits d'erreur et d'avertissement
- **Exigence** : une rangée en erreur a un trait **rouge** à gauche et son message dessous ; une rangée en avertissement (unité, vérification qui ne passe pas, domaine pas inclus) un trait **orange**. La marge du Code et le module d'état suivent les mêmes couleurs.
- **Source** : T32, T66
- **Langues** : fr / de / en (les messages)
- **Critère d'acceptation** : test du modèle de l'état (couleur par rangée, un message par faute, REQ-006) ; les couleurs viennent de `calc/tools/theme.json`.

### UI-010 — La ligne nouvelle : la pastille, puis les champs
- **Exigence** : en bas du formulaire, une ligne où l'on tape (« h = 240 mm », « M_d = q_d * l^2 / 8 », « sigma_(m,d) <= f_(m,d) ») ; à gauche une **pastille** qui dit ce qu'elle déduit (« var auto », « eq auto », « verify auto ») et qui, au clic, ouvre auto · var · eq · verify · texte (un choix la fixe, sans « auto ») ; dessous, les champs de la commande, remplis depuis la saisie et modifiables (REQ-001). **Entrée** ou ✓ écrit la ligne ; **Échap** ou × l'abandonne. La même pastille et les mêmes champs servent à la ligne ouverte par le + (UI-008).
- **Source** : T19, T33, T34, T35, T37
- **Langues** : fr / de / en
- **Critère d'acceptation** : test : taper « h = 240 mm » montre « var auto » et les champs symbole/valeur/unité/libellé remplis ; fixer « eq » montre « eq » sans « auto » ; Entrée écrit la ligne au bon endroit, Échap n'écrit rien.

### UI-011 — Un clic écrit le nom dans le calcul en cours
- **Exigence** : un clic sur une variable du module « Variables » ou sur **le nom d'un résultat** du module « Résultats » (souligné en pointillé, infobulle « Clic : écrire ce nom dans le calcul en cours ») écrit son **symbole** (en Code : la **clé**) à la place du curseur, **sans lui reprendre le curseur**. L'onglet retient le champ de calcul qui a eu le curseur en dernier **tel qu'il est maintenant** (non l'ancien, retiré par le redessin) et sa position de curseur. Sans calcul en cours, un message le dit.
- **Source** : T18, T41, T42, T43
- **Langues** : fr / de / en
- **Critère d'acceptation** : test pytest-qt : curseur dans le calcul d'un `eq`, choisir une autre rangée (redessin), cliquer une variable → le symbole est inséré à la position retenue dans le champ vivant et le curseur y reste ; sans calcul en cours, le message est affiché.

### UI-012 — Le module « Arguments de la ligne »
- **Exigence** : en **Code**, il suit le curseur (« eq · Domains/panne-p2.typ:30 ») et montre **tous** les arguments de la commande reconnue (`var`, `eq`, `verify`, liste de T44) ; en **Formulaire**, **les autres** arguments de la rangée choisie (ceux que la rangée ne montre pas) ; dans l'**Affichage**, **tous** ceux de la ligne cliquée. Une valeur changée s'écrit dans la ligne du fichier (en Code, le curseur et le défilement restent) ; dessous, la ligne écrite. Les listes viennent de REQ-009 ; une ligne de texte n'a pas d'arguments ; une commande qui ne se lit pas encore le dit.
- **Source** : T16, T44, T45, T46, T47, T48, T49, T67
- **Langues** : fr / de / en
- **Critère d'acceptation** : test : placer le curseur sur la ligne 30 d'un `eq` annonce « eq · … :30 » et liste les 17 arguments de T44 ; choisir `display-formula: "value"` écrit l'argument dans la ligne sans déplacer le curseur ; *auto* retire l'argument.

### UI-013 — Réordonner : la poignée, le groupe
- **Exigence** : on glisse la rangée par sa poignée ⋮⋮, une barre montre où elle ira ; **Ctrl+clic** ajoute ou retire une rangée du groupe (cadre pointillé bleu, bandeau « 3 lignes choisies : glissez une de leurs poignées… » ; la rangée choisie avant le premier Ctrl+clic y entre) ; Échap ou un clic simple défait le groupe ; **glisser la poignée d'une rangée du groupe déplace tout le groupe**, dans son ordre, à l'endroit du dépôt ; un déplacement qui ne tient pas est refusé avec la phrase de REQ-003. Aucun raccourci clavier.
- **Source** : T22, T50, T51, T52, T53
- **Langues** : fr / de / en
- **Critère d'acceptation** : test pytest-qt : Ctrl+clic sur trois rangées puis glisser la poignée de la deuxième les déplace ensemble ; Échap défait le groupe ; un dépôt refusé laisse le fichier intact et affiche la phrase ; un groupe déplacé offre « Annuler » (D-17).

### UI-014 — La fenêtre « Lier une variable… »
- **Exigence** : ouverte par le bouton du module Variables ou par + → lier, groupée par onglet et par cas, avec recherche ; une **case à cocher à gauche** de chaque variable ; un clic choisit une variable **sans l'importer** ; **Ctrl+clic** ajoute ou retire ; **Maj+clic** choisit une plage ; un clic sur la case l'ajoute ou la retire ; **« Valider (n) »** écrit les liens de tout ce qui est coché, d'un coup, dans l'ordre de la liste, au-dessus de la ligne choisie ; Entrée valide, Échap ferme ; une variable déjà dans le domaine est grisée, « déjà dans ce domaine ».
- **Source** : T21, T56, T63
- **Langues** : fr / de / en
- **Critère d'acceptation** : test pytest-qt : cocher trois variables et valider écrit trois lignes `#var(…, domain: …)` dans l'ordre affiché, au-dessus de la ligne cible, en **une** écriture (« Annuler », D-17, les retire toutes) ; une variable déjà liée est grisée.

### UI-015 — Le module « État du domaine »
- **Exigence** : il liste les messages d'état (rouge : erreur de lecture avec ligne et colonne, nom inconnu, unités incohérentes, lien introuvable ; orange : REQ-011), une faute une fois (REQ-006), dans la langue de la fenêtre (REQ-005). Un clic sur un message va à la ligne : la rangée clignote (`blink`) et le champ prend le curseur ; en Code la ligne est sélectionnée.
- **Source** : T58, T59, T60, T61
- **Langues** : fr / de / en
- **Critère d'acceptation** : test pytest-qt : cliquer un message de la ligne 13 fait clignoter la rangée 13 et lui donne le curseur ; en Code, la ligne 13 est sélectionnée.

### UI-016 — Le module « Résultats »
- **Exigence** : chaque `eq` et chaque `verify`, rien de saisi ; un clic déplie la formule en lettres et en nombres ; la clause à droite ; « Tout déplier », « Tout replier », « Copier les valeurs ». Le nom d'un résultat s'écrit dans le calcul en cours (UI-011).
- **Source** : T62
- **Langues** : fr / de / en
- **Critère d'acceptation** : test : le nombre d'entrées égale celui des `eq` et `verify` ; « Copier les valeurs » met les valeurs de `compute` dans le presse-papiers.

### UI-017 — Le module « Variables du domaine »
- **Exigence** : symbole, valeur, origine (« ce domaine » ou « ↗ Neige · SL ») ; un clic écrit la variable dans le calcul en cours (UI-011) ; le bouton « Lier une variable… » (UI-014).
- **Source** : T63
- **Langues** : fr / de / en
- **Critère d'acceptation** : test : Panne P2 liste ses variables avec l'origine de celles de la neige et des charges permanentes.

### UI-018 — Les survols liés
- **Exigence** : survoler une ligne (rangée, ligne du code, résultat, élément de l'Affichage) l'allume en jaune ; ce dont elle se calcule en bleu ; ce qui l'utilise en vert ; rien d'autre ne s'allume. Brique des issues #94/#95.
- **Source** : T65
- **Langues** : sans objet
- **Critère d'acceptation** : test : survoler η allume η en jaune, ses opérandes en bleu, rien en vert ; survoler b allume en vert W<sub>y</sub> et ce qui s'en calcule directement.

### UI-019 — Le Code
- **Exigence** : le fichier `.typ` lui-même, coloré (`richtext.TypstHighlighter`), avec une marge des numéros de ligne (rouge à une erreur, orange à un avertissement) et une marge à droite des résultats de chaque ligne (« = 4.238 kN/m », « ✔ 9.967 ≤ 11.28 N/mm² ») et des erreurs à leur ligne ; la ligne du curseur est reconnue tout de suite et alimente UI-012.
- **Source** : T66, T67, T68
- **Langues** : fr / de / en (les messages des marges)
- **Critère d'acceptation** : test pytest-qt : placer le curseur sur une ligne `#verify` annonce `verify` dans le module des arguments ; la marge de droite porte le résultat de `compute` ; un fichier avec une erreur a le numéro de sa ligne en rouge.

### UI-020 — L'Affichage : le centre
- **Exigence** : le fichier comme Typst l'imprime, élément par élément (rendus réels), les notes en bas de page, « Montrer les éléments masqués » et le zoom.
- **Source** : T69
- **Langues** : fr / de / en
- **Critère d'acceptation** : test : l'Affichage compile le fichier avec le moteur de Woodcore et montre un élément par ligne ; un élément masqué n'apparaît qu'avec la case.

### UI-021 — L'Affichage : la droite
- **Exigence** : à droite : le fichier et **la commande à copier dans la section** (`#include "/Domains/panne-p2.typ"`) ; « lire une valeur ailleurs dans le rapport » (`#var("eta", domain: "panne-p2", display: "value-unit")`) ; le **niveau du domaine** (`#domain(level:)`, 1, 2 ou 3) ; **les options du domaine, chacune cochée ou non** (REQ-004) avec leur valeur ; les **éléments du fichier** (une rangée par ligne avec son niveau propre 0 · 1 · 2 · 3, celui du domaine en pointillé ; un second clic le rend au domaine ; un clic ouvre tous ses arguments (UI-012), « Rétablir la ligne », la ligne écrite) ; « Voir le fichier entier ».
- **Source** : T70, T71, T72, T73, T74, T75
- **Langues** : fr / de / en
- **Critère d'acceptation** : test : cocher `presets: "block"` écrit la ligne sous l'en-tête et l'Affichage recompile en bloc ; la commande à copier est celle du fichier ; un niveau propre posé puis rendu au domaine retire `level:` de la ligne.

### UI-022 — Un domaine que Typst ne compile pas
- **Exigence** : l'Affichage montre l'erreur de Typst, ou celle de l'état si c'est la même.
- **Source** : T76
- **Langues** : fr / de / en (celle de l'état) ; Typst reste en anglais
- **Critère d'acceptation** : test : un domaine avec une parenthèse oubliée montre un message et non une page vide ; si Typst et l'état disent la même chose, un seul message.

### UI-023 — Trois langues
- **Exigence** : tout mot de la fenêtre (modes, pastille, champs, bandeau, boutons, états, bulles) existe en de, fr, en ; les mots retirés (`fm_cmd_val`, `fm_cmd_var-unit`, ceux de la pastille et du texte-à-pastilles) sont ôtés ; `fm_state_misnamed` ne parle plus de `#var-domain` mais de `#domain`.
- **Source** : T88, T93
- **Langues** : fr / de / en
- **Critère d'acceptation** : `tests/test_i18n.py` passe ; `grep var-domain|fm_cmd_val|fm_cmd_var-unit` ne trouve plus les mots retirés dans `calc/tools/`.

## 5. Exigences d'architecture

### ARCH-001 — Le modèle hors de Qt, en modules à la mesure
- **Exigence** : `infer_line`, la traduction symbole ↔ clé, le contrôle d'ordre d'un groupe, la ligne `#calc-defaults`, les codes d'erreur, la dépendance des lignes et la ligne d'une erreur vivent dans `calc/domains/` sans Qt ; l'onglet n'affiche, ne calcule pas. `formula_domain.py` ayant 1366 lignes, les ajouts vont dans des modules voisins (par exemple `formula_infer.py`, `formula_symbols.py`, `formula_defaults.py`, `formula_messages.py` — noms à fixer par la revue). Le script de l'artefact (`inferLine`, `typedSym`, `orderCheck`, `defaultsLine`…) est la **référence de comportement**, non du code livré.
- **Source** : T7, T91 ; principe « domain logic is independent of the UI » (docs/architecture/principles.md)
- **Critère d'acceptation** : les tests de REQ-001 à REQ-008 et REQ-019 s'exécutent sans Qt ; aucun module de `calc/domains/` n'importe `PySide6`.

### ARCH-002 — Le widget du Formulaire (tranché par la revue)
- **Exigence** : le Formulaire doit être un widget de rangées (un `QTableView` et son modèle, ou une colonne de widgets de rangée) qui tienne : le glisser par poignée, le Ctrl+clic (groupe), le × et le + au survol, le trait de couleur, et surtout **le redessin sans perdre le champ de calcul qui a le curseur** (UI-011). Le choix est celui de la revue d'architecture, sur le coût de ces cinq points.
- **Source** : T94
- **Décision (revue, ARCH-RISK-008)** : une **colonne de widgets de rangée** (un `QScrollArea` et une `FormRow` par rangée, le glisser par poignée de la forme de `module_pane._Header`), non un `QTableView` : les rangées sont hétérogènes (champs, largeurs, message dessous, détail de la rangée choisie, + au survol) ; le champ de calcul retenu l'est par **(rangée, champ, position)** et non par widget, relu au moment d'insérer.
- **Critère d'acceptation** : la revue (§13) nomme le widget et la raison ; le test de UI-011 passe sur lui.

### ARCH-003 — Réutiliser les briques communes
- **Exigence** : l'onglet réutilise `module_pane`, les survols liés et `blink` (#94/#95), `norm_bubble`/`norm_reader` (#96), `richtext.TypstHighlighter`, `grouped_list`, la source de variables liables (`variable_domains`, l'export, #42) ; il n'en copie aucune. Le **choix multiple « comme dans Windows »** (case, Ctrl+clic, Maj+clic, plage) est le même que celui de l'onglet Variables (#114, UI-009) et devrait être une **brique unique** ; la bulle au survol de l'onglet Commandes (#115, ARCH-002) est réutilisable pour les listes de valeurs du module « Arguments » (idée, §9).
- **Source** : T27, T56, T100 ; principe « une seule source »
- **Critère d'acceptation** : revue : aucun code de choix multiple ou de bulle n'est dupliqué entre #113, #114 et #115 ; un second usage de test emploie la brique sans le contenu de l'onglet.

### ARCH-004 — La vue « Code »
- **Exigence** : `views.py` offre aujourd'hui `CALC_VIEWS = ("calc", "display")` ; pour trois modes, l'onglet ajoute les vues `form` et `code` (décision de la revue), avec leurs mots dans `views.STRINGS` en trois langues, dans `ORDER` à la place de `calc`, et sans changer les autres onglets.
- **Source** : T24
- **Critère d'acceptation** : `tests/test_views.py` passe ; les autres onglets gardent `CALC_VIEWS`.

### ARCH-005 — Le format du fichier ne change pas
- **Exigence** : le format du `.typ` (une commande seule sur sa ligne, `#domain(…)[…]`, balises `// woodcore:`) ne change **pas de version** ; la ligne `#calc-defaults` est une ligne de commande que `parse_domain` doit **lire** (aujourd'hui aucune lecture), pas un nouveau format. `formula_layout.py` (la place des pastilles) n'a plus d'usage et est retiré (ou réduit à ce que REQ-016 garde).
- **Source** : T3, T24, T73 ; CON-001
- **Critère d'acceptation** : `docs/typst/formulas.md` n'a pas de changement de format ; `tests/test_formula_domain.py` relit tous les fichiers existants sans perte ; `formula_layout` n'est plus importé par l'onglet.

### ARCH-006 — Pas de hardcoding
- **Exigence** : couleurs dans `theme.json`, valeurs fines dans `lib/display-presets.json`, mots dans les glossaires de l'onglet (`fm_`, `STRINGS`), norme dans `calc/norms/` ; la liste des arguments (T44) est dérivée de `fine-keys` et `SPECS`, pas copiée.
- **Source** : CLAUDE.md « No hardcoding »
- **Critère d'acceptation** : revue ; `tests/test_i18n.py` ; test de REQ-009.

### ARCH-007 — Pas de second dispositif de compilation pour l'Affichage
- **Exigence** : l'Affichage utilise le dispositif existant de compilation de l'onglet (même copie du moteur, mêmes données du projet) ; les ~1 200 rendus du prototype ne sont **pas** des images committées : ils sont compilés à la demande par le moteur de Woodcore (inféré : T6 décrit le prototype, pas un produit à base d'images).
- **Source** : T6, T69 (inféré)
- **Critère d'acceptation** : aucune image de rendu de domaine n'est committée dans `docs/` ou `examples/` pour cette spec, hors la copie du prototype (ARCH-008).

### ARCH-008 — Copie du prototype
- **Exigence** : une copie du prototype est rangée dans `docs/requirements/prototypes/2026-10-24-onglet-domaines/`, lue par `action: "read"` sur l'artefact (page et fichiers de script) ; aucun fichier de `docs/` ne dépasse 100 Ko.
- **Source** : T93 ; CON-005
- **Critère d'acceptation** : le dossier existe ; `tests/test_docs_coherence.py` passe.

### ARCH-009 — L'Affichage est celui de la neige et du vent, sur le fichier de l'ingénieur
- **Exigence** : le mode Affichage réemploie `domain_file_display.DomainFileDisplay` (la page du fichier compilée sur un A4, `show-masked`, la carte « fichier / commande à copier / niveau du domaine », les niveaux 0 1 2 3, les arguments, « Voir le fichier entier ») au lieu d'en écrire un second ; la vue prend une **source de fichier** (le fichier d'un cas écrit par l'export, comme aujourd'hui, ou `Domains/<id>.typ` de l'ingénieur) et un **écrivain** (celui d'`unfold_display` pour un cas, celui du modèle `formula_domain` — `save`, `check_unchanged` — pour un domaine de l'ingénieur, qui ne touche **pas** la base d'`unfold` et ne rend aucune ligne `local`). Les tests de l'Affichage de la neige et du vent passent inchangés.
- **Source** : revue ; T69, T74, T76 ; ARCH-007
- **Critère d'acceptation** : `tests/test_domain_file_display.py` inchangé et vert ; un test écrit un niveau et un argument sur un domaine de l'ingénieur : le fichier le porte, `data/unfold-base.json` (la base) n'existe pas ou n'est pas changé.

### ARCH-010 — Le choix multiple est la brique de #114, rien de recopié
- **Exigence** : la sélection de la fenêtre « Lier une variable… » **et** celle du groupe de rangées du Formulaire (Ctrl+clic, un clic simple défait le groupe, Échap) emploient le modèle sans Qt de l'issue #114 (`calc/variable_select.py` : clic, Ctrl+clic, Maj+clic, case, clavier, dernière cliquée, ordre de la liste). Si ce modèle ne tient pas d'identifiants opaques (rangées au lieu de clés de variables), il est **généralisé en place**, sans changer son contrat envers #114, non copié.
- **Source** : revue ; ARCH-003, T21, T51, T56
- **Critère d'acceptation** : `grep` ne trouve aucun second code de plage ni de Ctrl+clic dans `calc/tools/formula_*.py` ; `tests/test_variable_select.py` (de #114) passe et un second usage de test emploie le modèle avec des rangées.

### ARCH-011 — Les rangées sont les items du domaine, regroupés par la colle ; `formula_layout` s'en va
- **Exigence** : un module sans Qt (`calc/domains/formula_rows.py`) donne les **rangées** d'un domaine — chaque item, une chaîne d'items collés (`formula_domain.same_line`) étant une seule rangée de texte qui porte ses commandes (D-16) —, le numéro de la première ligne de chaque rangée **dans le fichier** (`item_lines`, calculé avec `body_of`, jamais deviné), et les gestes sur les rangées (insérer, supprimer, déplacer un ou plusieurs avec le contrôle d'ordre de REQ-003 et sa phrase). Il remplace `formula_layout.py` (pastilles) : retiré, avec ses quatre usages dans `tests/test_formula_domain.py`.
- **Source** : revue ; REQ-003, REQ-016, UI-005, D-16
- **Critère d'acceptation** : `tests/test_formula_rows.py` (sans Qt) ; `tests/test_module_imports.py` voit `formula_rows` sans PySide6 ; `formula_layout` n'est plus importé nulle part.

### ARCH-012 — `compute` en dit plus, sans changer l'algèbre ni `resolve_import`
- **Exigence** : `units.FormulaError` porte un `code` et des `values` (par défaut `formula`, le texte anglais étant inchangé : `tests/test_units.py` ne change pas), `Result` gagne `uses` (les clés lues), `blocked_by`, `symbol`, `label`, `origin`, `code`, `values`, et `compute` un paramètre facultatif qui décrit une variable liée ; `formula_links.py` (sans Qt) donne `dependencies` (REQ-019) et `linked_info` (REQ-010) ; `resolve_import` et sa garde de boucle restent tels quels (CON-004).
- **Source** : revue ; REQ-005, REQ-006, REQ-010, REQ-019
- **Critère d'acceptation** : `tests/test_units.py`, `tests/test_domain_contracts.py` (C7) inchangés et verts ; `git diff` ne touche pas `resolve_import`.

### ARCH-013 — La fenêtre, la garde et les contrats que d'autres onglets lisent
- **Exigence** : chaque méthode qui écrit (déplacer, supprimer, insérer, lier, annuler, écrire un argument, une option du domaine) est nommée dans `tab_guard.WRITERS` (un projet ouvert en lecture seule refuse) ; `FormulaTab` garde son nom, `confirm_leave()`, `reload(keep=)`, `list.select(id)` et `current_id` (lus par `member_check_tab_actions.open_in_formulas`, `tab_registry`, `variables_tab`) ; `GRAPH_KIND = "formula"` (REQ-018) ; `woodcore_gui_words` continue de lire `formula_tab.STRINGS`, que le nouveau module de mots remplit (aucune ligne changée dans ce fichier partagé).
- **Source** : revue
- **Critère d'acceptation** : le test de la garde (`tests/test_formula_tab.py` en lit déjà `WRITERS`, ou un cas de `tests/test_window.py`) voit chaque nouvel écrivain ; `tests/test_member_check_tab.py` (les deux tests qui ouvrent « Formules ») passe inchangé.

### ARCH-014 — Une citation trouve son extrait sans table de plus
- **Exigence** : `calc/norms/excerpts.py` gagne `for_citation(norm, section, lang)` qui trouve l'extrait relevé d'une citation (`norm: "SIA 265"`, `norm-section: "Tabelle 8"`) parmi les extraits **déjà** rangés par fichier de norme (son édition, sa clause telle que l'édition la nomme) ; les extraits qui manquent sont relevés dans les fichiers de norme de `calc/norms/` à l'édition nommée de `ExternalFiles/000-Normes/` (CON-003), jamais de mémoire.
- **Source** : revue ; REQ-014
- **Critère d'acceptation** : `tests/test_norm_excerpts.py` : les huit clauses du prototype se résolvent, une clause hors liste rend rien sans erreur, deux extraits pour une même clause ne donnent pas de bulle ; le rectangle de chaque extrait nouveau tient dans la page de l'édition.

### ARCH-015 — « Annuler » est un modèle d'une seule étape
- **Exigence** : `calc/domains/formula_undo.py` (sans Qt) garde **une** étape : le texte du fichier avant et après le dernier geste de suppression ou de plusieurs lignes, et son nom ; elle ne s'applique que si le fichier est encore, sur le disque, le texte d'après (sinon elle le dit et n'écrit rien) ; un geste nouveau la remplace ; aucun Ctrl+Z.
- **Source** : revue ; D-17, UI-007
- **Critère d'acceptation** : `tests/test_formula_rows.py` : suppression, déplacement de groupe, liens multiples puis annulation, octet pour octet ; fichier changé entre-temps : refus dit.

### ARCH-016 — Le Code est un tampon qui lit avant d'écrire
- **Exigence** : en Code, le **tampon** du `QPlainTextEdit` est la source tant que le mode est ouvert ; il est lu par `formula_domain.parse_text` (la lecture de `read`, sur un texte), écrit sur le disque **seulement** s'il se lit sans erreur de lecture (`save` : `check_unchanged`, puis relu), et la faute est dite à la ligne et à la colonne de Typst (REQ-007). Le module « Arguments de la ligne » y écrit par **une** édition du tampon (le curseur et le défilement restent). La gouttière (numéros, marge des résultats à droite) est une brique générique (`calc/tools/code_editor.py`), qui reçoit ses marges d'un fournisseur et que `richtext.TypstHighlighter` colore.
- **Source** : revue ; REQ-012, UI-019
- **Critère d'acceptation** : `tests/test_formula_code.py` ; un fichier à parenthèse oubliée n'est pas écrit et sa ligne est rouge.

### ARCH-017 — Pas de module de plus de 1000 lignes, `formula_domain.py` ne grossit pas
- **Exigence** : les ajouts au modèle vont dans des modules voisins (`formula_rows`, `formula_infer`, `formula_defaults`, `formula_links`, `formula_errors`, `formula_args`, `formula_state`, `formula_order`, `formula_undo`, tous sous `calc/domains/`, sans Qt) ; `formula_domain.py` (1366 lignes, sous le plafond de 1500 de `layout.md`) ne reçoit que des retouches de quelques lignes (colle des espaces d'un indice, dernière clé d'un symbole, paramètres facultatifs de `compute` et de `new_domain`, `parse_text`). Dans la fenêtre, `formula_tab.py` (799) devient la coque ; `formula_tab_widgets.py` et `formula_tab_blocks.py` sont retirés.
- **Source** : revue ; `docs/architecture/layout.md` §11
- **Critère d'acceptation** : `tests/test_module_size.py` et `tests/test_module_imports.py` verts ; `layout.md` liste les modules nouveaux.

## 6. Contraintes

- **CON-001** — Compatibilité des fichiers : tout fichier `Domains/<id>.typ` existant est relu et réécrit sans perte ; un domaine existant ne reçoit **pas** de `#calc-defaults` (« un domaine existant garde ce qu'il a ») ; un domaine qui porte des commandes en ligne dans son texte (spec 2026-10-14) garde ce que Typst imprime. Source : T9, T95.
- **CON-002** — « Chaque nombre est celui que calcule Woodcore 0.122 » : l'algèbre de `calc/units.py` reste égale à celle de `lib/formula.typ` (`tests/test_units.py`) ; les nombres de l'onglet viennent du modèle, non du prototype. Source : T2, T6.
- **CON-003** — Les extraits de la norme sont relevés d'une édition nommée de `ExternalFiles/000-Normes/`, jamais de mémoire. Source : CLAUDE.md « SIA calculations stay traceable » ; T90.
- **CON-004** — La résolution des liens à un autre domaine et la garde contre une boucle de domaines (`resolve_import`) **ne changent pas**. Source : T23, T57.
- **CON-005** — Fichiers en LF, prose sur une ligne, anglais dans le code et les docs ; aucun fichier de `docs/` au-dessus de 100 Ko hors `decisions.md` et `CHANGELOG.md` ; `docs/ui/tab-formulas.md` (11 Ko) reste sous la limite après réécriture. Source : CLAUDE.md.
- **CON-006** — Les tests travaillent sur `tests/projet-exemple/` ; aucune écriture dans `../Musterprojekt/`. Source : CLAUDE.md.
- **CON-007** — Les messages du rapport restent ceux, anglais, de Typst ; seuls ceux de la fenêtre sont traduits. Source : T61.
- **CON-008** — Plusieurs sessions Claude éditent le dépôt à la fois : modifications ciblées (`formula_tab*.py`, `display_options.py`, `views.py`), pas de réécriture des gros fichiers ; coordination avant de toucher un fichier qu'un autre lot change. Source : CLAUDE.md.
- **CON-009** — Substantiel et multi-modules, touche un contrat de données (lecture de `#calc-defaults`, `norm-section:`) et deux décisions de #40 : `/big-feature`. Source : T3, T93.

## 7. Décisions prises

Toutes sont de l'ingénieur (issue #113, 24.10.2026) ; aucune n'est reposée.

- **D-1** — Les pastilles et le mode « Les deux » **s'arrêtent** ; les décisions D-01 à D-05 de #40 sont remplacées (T3, T8). Prix : le texte d'un domaine n'est plus un seul champ continu ; le texte devient des rangées.
- **D-2** — Édition : **Formulaire et Code** sur le même fichier, et un mode **Affichage** (T8, T15).
- **D-3** — Un domaine **nouveau** reçoit `#calc-defaults(presets: "block", scope: "domain")` ; un domaine **existant garde ce qu'il a** ; la ligne s'active et se désactive dans l'Affichage (T9). Prix : un domaine ancien s'imprime toujours en un seul paragraphe, et l'état le dit en orange (REQ-011).
- **D-4** — Ajouter une ligne : le **+ entre deux lignes** et la **ligne du bas, déduite** (T10).
- **D-5** — Lier une variable : le **nom tapé**, le bouton « Lier une variable… » et le **correctif du message** (T11).
- **D-6** — Un calcul se tape **avec les symboles affichés**, traduits en clés (T12).
- **D-7** — Une vérification qui ne passe pas est **orange** : une information sur l'ouvrage, le fichier se compile (T13).
- **D-8** — Un domaine de l'onglet lu par son nom : **avertissement orange** tant qu'il n'est pas inclus plus haut (T14).
- **D-9** — Lier à un autre domaine : **ne rien changer** (T23).
- **D-10** — Le **×** supprime ; réordonner par la **poignée**, **sans raccourci** ; le groupe par **Ctrl+clic** (T20, T22).
- **D-11** — Une ligne nouvelle a une **pastille var / eq / verify** à gauche, *auto* au départ, avec les champs de la commande dessous, pour la ligne du bas aussi (T19).
- **D-12** — La fenêtre « Lier une variable… » : cases à cocher, Ctrl+clic, Maj+clic, « Valider » (T21, T56).
- **D-13** — Le Code reconnaît la commande du curseur tout de suite et montre tous ses arguments à droite (T16).
- **D-14** — La ligne de l'erreur est **celle de Typst** (T84, T98 : « → la ligne de Typst »).
- **D-15** — (inférée) Les ~1 200 rendus du prototype ne sont pas des images committées : l'Affichage compile (ARCH-007).
- **D-16** — **Q-001, A** (ingénieur, 24.10.2026) : un texte qui contient une commande dans sa ligne est **une rangée de texte qui contient sa commande**, la commande un petit bloc non éditable à l'intérieur (symbole = valeur) dont les champs et les arguments s'ouvrent dans le module de droite ; le fichier, ses octets et ce que Typst imprime ne changent pas (spec 2026-10-14-commandes-en-ligne-domaine, D-02, reste vraie). Prix : un champ de texte avec un élément enchâssé, le seul endroit où le formulaire ressemble encore à une pastille.
- **D-17** — **Q-002, A** (ingénieur, 24.10.2026) : « Annuler » défait **la dernière suppression** et **le dernier geste de plusieurs lignes** (déplacement d'un groupe, « Valider » de liens), dans le message qui le suit, en une seule étape ; pas de Ctrl+Z global. Prix : un geste plus ancien, un champ édité ou une option du domaine se corrigent à la main.
- **D-18** — **Q-003, A** (ingénieur, 24.10.2026) : la **police de `#var` et `#eq` en bloc** (défaut 9 de l'issue) est une issue à part ; ce lot ne touche pas `lib/`. Prix : l'Affichage montre, jusqu'à cette issue, la différence de police que le moteur imprime.
- **D-19** — (revue d'architecture, ARCH-009) L'Affichage est celui de la neige et du vent (`domain_file_display.DomainFileDisplay`) : la **page compilée** du fichier, non un rendu par élément ; les survols liés y sont ceux de la **liste des éléments** à droite. À confirmer à l'approbation (§13, point P-1).

À reporter dans `docs/decisions.md` §13 à la fin : la fin des pastilles (D-01 à D-05 de #40 remplacées), le formulaire et le code, `presets: "block"` par défaut d'un domaine nouveau, une faute dite une fois, la ligne d'erreur de Typst.

## 8. Hors périmètre

- **L'onglet Commandes (#115)**, l'onglet **Variables (#114)**, la migration des onglets de données vers une base commune (#106) : cette spec n'en modifie pas le contenu ; elle en **réutilise** des briques (ARCH-003) et peut répondre à `open_object` (REQ-018).
- **Défaut 13** (la vérification dépliée BI-01 : `eta_s` et `eta` la même formule écrite deux fois ; f<sub>m,y,d</sub> sans clause alors que f<sub>t,0,d</sub> de ZT-01 cite SIA 265 Tableau 8) : c'est le **générateur de `unfold.py`**, non l'onglet ; il est noté, **une issue à part** (inféré : l'issue ne l'assigne à aucune demande de la liste « Demandes »).
- **Défaut 9** (police de `#var` et `#eq` en bloc) : **issue GitHub à part** (Q-003, A, D-18) — le « = 1.35 » d'un `#var` plus petit et d'une autre police que le « = 4.238 kN/m » d'un `#eq` en bloc, cause dans `lib/formula.typ` ; la corriger change l'impression de tous les rapports qui emploient un bloc et leurs rendus de référence (`tests/test_report_golden.py`, `examples/out/`). Cette spec ne touche pas `lib/`. **L'issue est à ouvrir à la fin du lot** (dernière étape du plan, §14) ; elle reprend le constat de T85 et cette phrase.
- Un changement du moteur (`lib/`), de la sémantique des commandes ou de leurs exemples (« rien de nouveau dans le moteur », T73).
- La résolution des liens et la garde de boucle (`resolve_import`, CON-004).
- Un raccourci clavier pour déplacer une ligne (T22).
- Les groupes des onglets spécialisés ne sont **pas modifiés** dans leur contenu, seulement repliés dans la liste.

## 9. Idées non retenues comme exigences

- **Réutiliser la bulle des valeurs de #115** pour les listes de valeurs du module « Arguments de la ligne » (T100 / spec #115 §9 : « pourrait réutiliser ») : idée ; seule la brique commune est exigée (ARCH-003).
- **Le domaine « Panne de toiture P2 »**, écrit pour le prototype, comme **fixture de test** (neige SL et charges permanentes lues de l'export) : utile pour REQ-010, REQ-011, UI-021 ; sa place (`tests/projet-exemple/Domains/` ou une fixture) est à fixer à l'implémentation.
- **Le script de l'artefact** (T7) comme référence de comportement : cité dans ARCH-001, non copié ; un test peut reprendre ses cas limites.
- **La copie du prototype** dans `docs/requirements/prototypes/` est une tâche de documentation (ARCH-008).

## 10. Questions

### Q-001 — Que devient un texte qui contient une commande dans sa ligne ?
- **Contexte** : le fichier d'un domaine mêle du texte de l'ingénieur et des commandes ; une commande peut être écrite **au milieu d'une ligne de texte**, par exemple `- $0°$ bis $30°$: #eq(…)` (spec 2026-10-14-commandes-en-ligne-domaine), et le texte d'un paragraphe se colle à la commande voisine tant qu'aucune ligne vide ne les sépare (ce que `formula_layout.from_paragraphs` règle aujourd'hui avec les pastilles). Dans le nouveau formulaire, une rangée est une commande **ou** un texte. Un texte qui contient une commande ne rentre dans aucune des deux.
- **Pourquoi elle compte** : elle fixe ce que l'ingénieur voit pour ces lignes, si le fichier change quand il édite le texte (impression modifiée), et la taille du travail sur le modèle (`split_items`, `glued_before/glued_after`). REQ-016 impose seulement que rien ne change à l'impression.
- **Options** :
  - **A (recommandée)** — une rangée de texte **qui contient sa commande** : le texte est éditable, la commande est un petit bloc non éditable à l'intérieur (symbole = valeur) dont les champs et arguments s'ouvrent dans le module de droite ; le fichier ne change pas (D-02 de la spec 2026-10-14 reste vraie). Coût : un champ de texte avec un élément enchâssé, donc le seul endroit où le formulaire ressemble encore à une pastille.
  - **B** — **couper** le texte : la commande devient sa rangée, le texte avant et après deux rangées de texte. Rangées toutes simples ; mais Typst imprime autre chose (un nouveau paragraphe là où il y avait un mot de la phrase), ce qui contredit CON-001, et la spec 2026-10-14 serait à rouvrir.
  - **C** — ces lignes restent **en lecture seule** dans le Formulaire (rangée grisée « édition en Code ») et s'éditent en Code. Aucun risque pour le fichier ; l'ingénieur doit changer de mode pour ces lignes.
- **Réponse** : A — une rangée de texte qui contient sa commande, la commande en bloc non éditable à l'intérieur ; le fichier et l'impression ne changent pas (ingénieur, 24.10.2026). Reporté en D-16, REQ-016, ARCH-011.

### Q-002 — « Annuler » : la dernière suppression, ou tous les gestes ?
- **Contexte** : le prototype offre « Annuler » dans le message qui suit une suppression, pour la **dernière** seulement. Le formulaire fait d'autres gestes qui réécrivent le fichier : déplacer une ligne ou un groupe, lier plusieurs variables d'un coup, changer une option du domaine, éditer un champ.
- **Pourquoi elle compte** : elle fixe la pile d'annulation de l'onglet (le fichier avant chaque geste), le raccourci Ctrl+Z (qui concurrence l'annulation de frappe d'un champ) et les tests. Un oubli se paie : « Valider » de 12 liens ne se défait pas.
- **Options** :
  - **A (recommandée)** — « Annuler » pour la **dernière suppression** et pour le **dernier geste de plusieurs lignes** (déplacement d'un groupe, « Valider » de liens), dans le message qui le suit, une seule étape : suffisant pour les gestes qui défont beaucoup d'un coup, sans Ctrl+Z global.
  - **B** — comme le prototype, **la suppression seule** : le moins de code ; un déplacement de groupe ou un lien multiple mal posé se corrige à la main.
  - **C** — une **pile** pour tous les gestes de l'onglet, Ctrl+Z / Ctrl+Y hors d'un champ en cours de frappe : le plus confortable, le plus de code, et des conflits avec l'annulation propre aux champs.
- **Réponse** : A — « Annuler » pour la dernière suppression et le dernier geste de plusieurs lignes (déplacement d'un groupe, « Valider » de liens), une seule étape, sans Ctrl+Z global (ingénieur, 24.10.2026). Reporté en D-17, UI-007, UI-014, ARCH-015.

### Q-003 — La police de `#var` et `#eq` en bloc : dans ce lot, ou une issue à part ?
- **Contexte** : dans le rendu d'un domaine en bloc (`presets: "block"`), le « = 1.35 » d'un `#var` est plus petit et d'une autre police que le « = 4.238 kN/m » d'un `#eq` (rendu au niveau 3). La cause est dans `lib/formula.typ`, pas dans l'onglet.
- **Pourquoi elle compte** : la corriger change l'impression de **tous** les rapports qui utilisent un bloc, donc les rendus de référence (`tests/test_report_golden.py`, `examples/out/`, les images de l'onglet Commandes) ; la laisser fait que l'Affichage du nouvel onglet montre une différence visible qui dépare le prototype validé.
- **Options** :
  - **A (recommandée)** — **une issue à part** : cette spec ne touche pas `lib/`, l'Affichage montre ce que le moteur imprime, la correction est livrée et ses références régénérées en un lot dédié.
  - **B** — la corriger **dans ce lot** : l'Affichage est juste dès la livraison ; mais le lot touche le moteur et les rendus de référence de tout le dépôt, et se mêle à la refonte de l'onglet.
- **Réponse** : A — la police de `#var` et `#eq` en bloc est une **issue GitHub à part** ; ce lot ne touche pas `lib/` (ingénieur, 24.10.2026). Reporté en D-18, §8 ; l'issue est à ouvrir à la fin du lot (dernière étape du plan, §14).

## 11. Critères d'acceptation

- [x] REQ-001 — `infer_line` : var, eq, verify, texte et ses cas limites.
- [x] REQ-002 — le calcul en symboles : l'existant complété, même valeur à l'aller-retour sur Poutre P1.
- [x] REQ-003 — déplacement d'un groupe refusé avec sa phrase.
- [x] REQ-004 — `#calc-defaults` lu/écrit option par option ; `presets: "block"` pour un domaine nouveau seulement.
- [x] REQ-005 — erreurs en code et valeurs, mots `fm_e_*` en trois langues.
- [x] REQ-006 — une faute dite une fois, ses dépendantes comptées.
- [x] REQ-007 — ligne et colonne de Typst ; « ligne N de `Domains/<id>.typ` ».
- [x] REQ-008 — « Article » est `norm-section:`, `norm-ref:` lu.
- [x] REQ-009 — arguments dérivés de `line_display` (`fine-keys`/`fine-values`) ; `SPECS` de var/eq/verify retirés.
- [x] REQ-010 — variable liée : vrai symbole, vrai libellé.
- [x] REQ-011 — avertissements orange (vérification, unité, domaine non inclus, pas de `presets: "block"`).
- [x] REQ-012 — fichier seule source ; ligne cassée n'écrit rien.
- [x] REQ-013 — lien : nom tapé, fenêtre, correctif du message, mêmes fichiers.
- [x] REQ-014 — bulle de la norme pour huit clauses, relevées d'une édition nommée.
- [x] REQ-015 — domaine déplié : états sur le trait de la rangée.
- [x] REQ-016 — texte et commandes en ligne relus et réécrits octet pour octet (Q-001, A : rangée de texte qui contient sa commande).
- [x] REQ-017 — `examples/data/formulas.json` sans domaine fantôme.
- [x] REQ-018 — (devrait) `GRAPH_KIND = "formula"` et `open_object` sur un domaine.
- [x] REQ-019 — survols liés lus de `compute`.
- [x] UI-001 — trois modes, aucune pastille.
- [x] UI-002 — liste de gauche repliée, sans code Typst.
- [x] UI-003 — en-tête du centre.
- [x] UI-004 — cinq modules dans l'ordre.
- [x] UI-005 — une rangée par ligne.
- [x] UI-006 — la rangée choisie.
- [x] UI-007 — × et « Annuler » (Q-002, A : suppression et geste de plusieurs lignes).
- [x] UI-008 — le + entre deux rangées.
- [x] UI-009 — traits rouge et orange.
- [x] UI-010 — la ligne nouvelle, pastille auto/fixée, Entrée/Échap.
- [x] UI-011 — un clic écrit dans le calcul en cours, curseur gardé.
- [x] UI-012 — module « Arguments de la ligne » en trois contextes.
- [x] UI-013 — poignée, Ctrl+clic, déplacement de groupe, refus.
- [x] UI-014 — fenêtre « Lier une variable… » : cases, Ctrl, Maj, « Valider ».
- [x] UI-015 — module d'état, clic mène à la ligne.
- [x] UI-016 — module « Résultats ».
- [x] UI-017 — module « Variables du domaine ».
- [x] UI-018 — survols jaune/bleu/vert.
- [x] UI-019 — Code : deux marges, commande du curseur.
- [x] UI-020 — Affichage : rendus réels, masqués, zoom.
- [x] UI-021 — Affichage : commande à copier, niveau, options du domaine, éléments.
- [x] UI-022 — erreur de Typst montrée, sans doublon.
- [x] UI-023 — trois langues, mots retirés ôtés.
- [x] ARCH-001 — modèle hors de Qt.
- [x] ARCH-002 — widget du Formulaire tranché par la revue.
- [x] ARCH-003 — briques communes réutilisées (choix multiple, bulle, modules).
- [x] ARCH-004 — vue « Code » dans `views.py`.
- [x] ARCH-005 — format du `.typ` inchangé ; `formula_layout` retiré.
- [x] ARCH-006 — pas de hardcoding.
- [x] ARCH-007 — l'Affichage compile, sans images committées.
- [x] ARCH-008 — copie du prototype dans `docs/requirements/prototypes/2026-10-24-onglet-domaines/`.
- [x] ARCH-009 — l'Affichage est `DomainFileDisplay` sur le fichier de l'ingénieur, sans la base d'`unfold`.
- [x] ARCH-010 — le choix multiple est le modèle de #114, jamais recopié.
- [x] ARCH-011 — les rangées sont les items regroupés par la colle ; `formula_layout` retiré.
- [x] ARCH-012 — `compute` en dit plus ; `resolve_import` et l'algèbre inchangés.
- [x] ARCH-013 — la garde, les contrats lus par d'autres onglets, `GRAPH_KIND`.
- [x] ARCH-014 — une citation trouve son extrait (`for_citation`), les extraits relevés à l'édition nommée.
- [x] ARCH-015 — « Annuler » : une étape, un modèle sans Qt.
- [x] ARCH-016 — le Code lit son tampon avant d'écrire.
- [x] ARCH-017 — aucun module de plus de 1000 lignes ; `formula_domain.py` ne grossit pas.
- [x] Documentation : `docs/ui/tab-formulas.md` réécrit, `docs/typst/formulas.md` si le format change, `docs/ui/window.md` si l'index des onglets change, `docs/architecture/layout.md` (modules nouveaux), `docs/decisions.md` §13 (une entrée nouvelle ; la décision de #40, ligne 65, passe à *[superseded in v0.125]*, avec sa ligne de `docs/decisions-index.md`), ligne au catalogue des tests pour tout fichier nouveau, entrée `CHANGELOG.md`, page « Nouveautés » de la prochaine version en fr/de/en ; aucune commande Typst nouvelle (donc pas de `///` ni de `commands.json`).
- [x] Tests : `tests/test_formula_domain.py`, `tests/test_formula_tab.py` (refait pour les rangées et le code), `tests/test_units.py`, `tests/test_views.py`, `tests/test_i18n.py`, un fichier nouveau pour les modules sans Qt ; tous passent.

## 12. Traçabilité

La table T → élément est dans [docs/history/2026-10-24-onglet-domaines-formulaire-code-tracabilite.md](../../history/2026-10-24-onglet-domaines-formulaire-code-tracabilite.md) (déplacée le 24.10.2026 pour tenir la spec sous 100 KB).

## 13. Revue d'architecture

La revue (verdict : approuver avec réserves ; 20 risques, aucun bloquant) est dans [docs/history/2026-10-24-onglet-domaines-formulaire-code-revue.md](../../history/2026-10-24-onglet-domaines-formulaire-code-revue.md) (déplacée le 24.10.2026 pour tenir la spec sous 100 KB). À lire avant chaque étape du plan.

## 14. Plan d'implémentation

Ordre de la session : #108, #115, #114, puis cette issue. **Avant l'étape 2**, relire tels que ces lots les laissent `hover_bubble.py`, `variable_select.py`, `MainWindow.can_open_tab` / `show_tab`, `module_pane.py`, `norm_bubble.py`, `woodcore_gui_words.py` et `views.py` (fichiers partagés : on les touche par éditions ciblées, jamais réécrits ; avant d'en toucher un qu'un autre lot change, SendMessage). Chaque étape se termine par les tests de sa colonne (`python tests/run_tests.py -k nom` ou `--related`) ; la suite complète une fois à l'étape 22, en arrière-plan. Les étapes 2 à 11 sont sans Qt : elles se prouvent avant tout widget. Aucune étape ne fait passer un module de `calc/` au-dessus de 1000 lignes.

| # | Étape | Fichiers | Couvre | Preuve |
|---|---|---|---|---|
| 1 | **Préalables.** Base verte (`-k formula`, `-k domain_file`, `-k display_view`, `-k views`, `-k unfold`) ; la fixture Panne P2 extraite du prototype (`Artifact action: "read"` avec `path`, le script de l'artefact pour le texte du fichier) dans `tests/fixtures/domains/panne-p2.typ`, hors du projet d'exemple ; relever la version en cours (`VERSION`, dernier `website/content/*/changes/`). | `tests/fixtures/domains/panne-p2.typ` | ARCH-RISK-017 | la fixture, copiée dans une copie temporaire de l'exemple, se compile avec `typst` et ses nombres sont ceux de `compute` ; la base est verte |
| 2 | **Les erreurs en code et valeurs.** `units.FormulaError(message, code="formula", **values)` + `CODES`, vérifié à la construction ; chacun des 14 sites de `units.py` et des 5 de `formula_domain.py` reçoit son code et ses valeurs, le texte anglais est inchangé ; `DomainError` : la liste de ses codes dans `CODES` ; le dictionnaire des mots est déplacé par texte de `formula_tab.py` vers `formula_tab_words.py` (ré-importé), et reçoit les mots `fm_e_*` en de / fr / en, sans coupure à 80 caractères ; `fm_state_misnamed` parle de `#domain`. | `calc/units.py`, `calc/domains/formula_domain.py`, `calc/tools/formula_tab_words.py` (nouveau), `calc/tools/formula_tab.py` | REQ-005, UI-023 (en partie), ARCH-012 | `tests/test_formula_state.py` : chaque code a ses trois mots et ses valeurs ; « no variable named 'L' » en français avec la liste entière ; `tests/test_units.py`, `tests/test_domain_contracts.py` (C7), `tests/test_i18n.py` inchangés et verts |
| 3 | **Le calcul en dit plus.** `Result.uses`, `blocked_by`, `symbol`, `label`, `origin` ; `compute(domain, resolve, digits, describe=None)` : les clés cassées, les lignes bloquées ; `formula_links.py` : `dependencies(domain, results)` (les opérandes de `compute`, jamais recalculés dans l'onglet), `linked_info(here, command, calculations)` ; `variables_of` et `variable_domains` emploient le symbole et le libellé liés ; `resolve_import` non touché. | `calc/domains/formula_domain.py` (paramètres facultatifs), `calc/domains/formula_links.py` (nouveau) | REQ-006, REQ-010, REQ-019, ARCH-012 | `tests/test_formula_state.py` : `L` pour `l` dans Poutre P1 = une erreur, trois lignes bloquées, une seconde faute indépendante reste rouge ; la charge permanente liée de Panne P2 porte `(g_k + a_k)_gew` et « Charges permanentes » ; survoler η rend ses opérandes et b ses utilisateurs ; `git diff` ne touche pas `resolve_import` |
| 4 | **Les rangées et leurs gestes.** `formula_rows.py` : `rows(domain)` (items regroupés par la colle, une rangée de texte portant ses commandes), `item_lines(domain)` (avec `body_of`), `insert`, `delete`, `move(domain, indexes, target)` avec `order_refusal` (la phrase « Déplacement refusé : W_y utilise b, qui serait plus bas. ») pour chaque ligne du groupe et celles qui restent ; `formula_undo.py` : l'étape unique. | `calc/domains/formula_rows.py`, `calc/domains/formula_undo.py` (nouveaux) | REQ-003, REQ-016, UI-007 (modèle), ARCH-011, ARCH-015, D-16, D-17 | `tests/test_formula_rows.py` : un groupe de trois lignes déplacé sous une ligne qui en dépend est refusé avec la phrase, ailleurs il garde son ordre ; chaque fichier de `tests/projet-exemple/Domains/` et des fixtures à commande en ligne est relu et réécrit octet pour octet ; supprimer b puis annuler rend le fichier ; fichier changé entre-temps : refus dit |
| 5 | **Les positions de faute et la lecture d'un texte.** `formula_domain.parse_text` (la lecture de `read` sur un texte) ; `formula_errors.py` : la faute de lecture au délimiteur ouvert, ligne et colonne, une erreur de calcul à « ligne N de `Domains/<id>.typ` » ; `Result.line`. | `calc/domains/formula_domain.py`, `calc/domains/formula_errors.py` (nouveau) | REQ-007, REQ-012 (modèle), ARCH-016 | `tests/test_formula_state.py` : le fichier de l'issue (`#var(` sans parenthèse) = ligne 19, colonne 5, comparée à `typst compile` quand le moteur est là ; un nom inconnu à la ligne 13 : « ligne 13 de `Domains/panne-p2.typ` » |
| 6 | **La ligne déduite et le calcul en symboles.** `formula_infer.py` : `infer_line(text, taken)` (relation → verify, « symbole = nombre unité » → var, « symbole = expression » → eq, sinon texte ; clé par `key_from_symbol`, unique ; le choix explicite l'emporte) ; compléments de `typst_formula` / `display_formula` : la table des lignes au-dessus en paramètre, les espaces dans `sigma_(m, d)`, la clé la plus basse d'un symbole porté par deux clés avec son message. | `calc/domains/formula_infer.py` (nouveau), `calc/domains/formula_domain.py` (retouches) | REQ-001, REQ-002, ARCH-RISK-004 | `tests/test_formula_input.py` : « h = 240 mm », « M_d = q_d * l^2 / 8 », « sigma_(m,d) <= f_(m,d) », `≥`, un nombre sans unité, une unité inconnue, un symbole pris ; l'aller-retour de Poutre P1 donne la même valeur ; les tests existants de `typst_formula` passent |
| 7 | **`#calc-defaults` et « Article ».** `formula_defaults.py` : lecture et écriture de la ligne dans les items de texte (options `presets`, `label-position`, `descr-position`, `norm-position`, `style`, valeurs proposées de T73, arguments inconnus et étiquette gardés, cocher / décocher / tout décocher) ; `new_domain(…, defaults=True)` ; `norm-ref` lu d'un fichier ancien et réécrit `norm-section` ; `formula_tab_domains` appelle la création. | `calc/domains/formula_defaults.py` (nouveau), `calc/domains/formula_domain.py` | REQ-004, REQ-008, D-3 | `tests/test_formula_state.py` : un domaine nouveau écrit la ligne, un existant sans elle est relu / réécrit à l'identique ; ce que `unfold.py` écrit est relu sans perte ; γ_G avec `norm-section: "Tableau 1"` montre « Tableau 1 » ; `norm-ref` jamais avec `norm-section` ; la compilation de Panne P2 avec la ligne imprime par valeur (`typst`) |
| 8 | **L'état du domaine.** `formula_state.py` : les messages rouges (lecture, nom inconnu, unités incohérentes, lien introuvable) et orange (vérification qui échoue, unité demandée ≠ résultat, domaine pas inclus plus haut, pas de `presets: "block"` avec le renvoi aux options), une faute une fois avec « n lignes plus bas en dépendent », le correctif « Lier q_k1 depuis Neige · SL » ; `formula_order.py` : l'ordre des inclusions par document ; la couleur de chaque rangée (dont les états d'un domaine déplié, ARCH-RISK-018). | `calc/domains/formula_state.py`, `calc/domains/formula_order.py` (nouveaux) | REQ-011, REQ-013 (correctif), REQ-015 (modèle), UI-009, UI-015 (modèle) | `tests/test_formula_state.py` : h = 200 mm (orange), un domaine qui en lit un autre non inclus (orange, avec P-2), un domaine sans `calc-defaults` (orange, renvoi aux options), un nom inconnu connu de l'export offre le correctif ; chaque état d'`unfold` a sa couleur et son mot |
| 9 | **Les arguments d'une ligne.** `formula_args.py` : les champs d'une ligne (clé, symbole, valeur, unité, calcul, label, descr, norm, norm-section, as-unit) du modèle, les arguments d'affichage de `line_display.display_args` et leurs valeurs de `fine_values`, *auto* n'écrit rien, `command_at(text, ligne)` pour le Code, `set_argument(command, name, value)` ; retrait de `SPECS["var" | "eq" | "verify"]`, de leurs `DISMISSED`, de `NORM_REF` et du mot `ds_opt_norm_ref` si la recherche n'y trouve aucun autre lecteur (sinon `NORM_REF` corrigé seul). | `calc/domains/formula_args.py` (nouveau), `calc/tools/display_options.py` | REQ-008, REQ-009, UI-012 (modèle), ARCH-RISK-003 | `tests/test_formula_input.py` : les arguments proposés = `display_args`, ajouter une valeur à `lib/display-presets.json` la fait apparaître, chaque valeur écrite compile (`check-fine`) ; `tests/test_display_view.py` vert |
| 10 | **Les extraits de la norme d'une citation.** `norms.excerpts.for_citation` ; les extraits qui manquent des huit clauses relevés dans les fichiers de norme à l'édition nommée de `ExternalFiles/000-Normes/` (page, rectangle, texte, de / fr) ; la logique d'épinglage de `Modules.pin` extraite en une fonction. | `calc/norms/excerpts.py`, `calc/norms/sia26*.json` (extraits relevés), `calc/tools/calc_modules.py`, `calc/tools/module_pane.py` ou `norm_bubble.py` | REQ-014, ARCH-014 | `tests/test_norm_excerpts.py` : les huit clauses se résolvent, chaque rectangle tient dans la page de l'édition, une clause hors liste ne lève rien et n'a pas de bulle ; `tests/test_calc_tab_base.py` et `tests/test_materials_tab.py` verts |
| 11 | **La coquille : vues, mots, jetons.** Les vues `form` et `code` dans `views.py` (`WORDS`, `TIPS`, `ORDER`, `STRINGS`) ; `FormulaTab.VIEWS = ("form", "code", "display")` et son `set_view` (page de travail à deux pages internes, ou l'Affichage) ; `GRAPH_KIND = "formula"` ; les quatre jetons des survols liés dans `theme.json` ; `tab_guard.WRITERS` reçoit les écrivains nouveaux au fil des étapes suivantes. | `calc/tools/views.py`, `calc/tools/formula_tab.py`, `calc/tools/theme.json`, `calc/tools/tab_guard.py` | UI-001, REQ-018, ARCH-004, ARCH-013, ARCH-006 | `tests/test_views.py` (trois vues dans cet ordre, les autres onglets gardent `CALC_VIEWS`), `tests/test_theme.py`, `tests/test_modes_window.py` (`open_object("formula:<id>")` ouvre le domaine), `tests/test_i18n.py` |
| 12 | **Le Formulaire : la colonne de rangées.** `FormRow` (var, eq, verify, variable liée, texte avec ses blocs enchâssés), le conteneur à défilement, le trait rouge / orange et le message dessous, la rangée choisie (clé, libellé, norme, article, description), l'**i** de la clause (`BubbleController.attach`), le suivi du champ de calcul par (rangée, champ, position), la mise à jour sur place, les survols liés (jaune / bleu / vert, lus de `dependencies`). Mesure de la construction sur 200 rangées. | `calc/tools/formula_form.py`, `calc/tools/formula_row.py` (nouveaux) | UI-005, UI-006, UI-009, UI-011 (suivi), UI-018, ARCH-002, ARCH-RISK-008 | `tests/test_formula_form.py` (pytest-qt) : pour Poutre P1 les rangées et les valeurs de `compute` ; modifier un champ réécrit la ligne sans reconstruire les autres rangées ; le curseur dans un calcul, une autre rangée choisie, un clic sur une variable : le symbole est inséré dans le champ vivant, le curseur y reste ; sans calcul en cours, le message |
| 13 | **Ajouter, supprimer, annuler, glisser.** La ligne du bas et sa pastille (auto / var / eq / verify / texte, les champs dessous, Entrée / ✓ / Échap / ×), le + entre deux rangées et ses cinq choix, le × de chaque rangée et le bandeau « Annuler » (une étape), la poignée ⋮⋮ (barre de dépôt), le groupe par Ctrl+clic (cadre pointillé, bandeau, Échap, un clic simple défait) sur `variable_select`, le déplacement du groupe et le refus avec la phrase. | `calc/tools/formula_new_line.py`, `calc/tools/formula_form.py`, `calc/tools/formula_row.py` | UI-007, UI-008, UI-010, UI-013, ARCH-010, D-10, D-11, D-17 | `tests/test_formula_form.py` : « h = 240 mm » montre « var auto » et ses champs, fixer eq le dit sans « auto », Entrée écrit au bon endroit, Échap n'écrit rien ; le + entre 3 et 4 écrit en 4 ; supprimer puis « Annuler » octet pour octet ; Ctrl+clic sur trois rangées, glisser la poignée de la deuxième les déplace ensemble, Échap défait le groupe, un dépôt refusé laisse le fichier intact et affiche la phrase |
| 14 | **Les modules de droite.** Dans un `ModulePane` : État du domaine (le clic va à la ligne : `Blinker`, le champ prend le curseur, en Code la ligne est sélectionnée), Arguments de la ligne (Formulaire : les autres ; Code : tous), Résultats (dépliage, « Tout déplier », « Tout replier », « Copier les valeurs », le nom d'un résultat écrit dans le calcul en cours), Variables du domaine (symbole, valeur, origine, « Lier une variable… »), les extraits épinglés (clic, second clic, Ctrl+clic). | `calc/tools/formula_modules.py`, `calc/tools/formula_args_pane.py` (nouveaux) | UI-004, UI-012, UI-015, UI-016, UI-017, REQ-014 | `tests/test_formula_form.py` et `tests/test_formula_code.py` : les cinq modules dans l'ordre, déplaçables et repliables ; le clic sur un message de la ligne 13 fait clignoter la rangée 13 ; « Copier les valeurs » met celles de `compute` ; Panne P2 liste l'origine « ↗ Neige · SL » ; épingler puis retirer une bulle |
| 15 | **Lier une variable.** La fenêtre « Lier une variable… » (groupée par onglet et par cas, recherche, case à cocher, un clic sans importer, Ctrl+clic, Maj+clic, « Valider (n) », Entrée, Échap, « déjà dans ce domaine » grisé) sur `variable_select` et la source des variables liables de #114 ; l'écriture de tous les liens en **une** écriture au-dessus de la ligne choisie ; le nom tapé et sa complétion (le domaine par clé ou symbole, puis le projet) ; le correctif du message. | `calc/tools/formula_link_dialog.py` (nouveau), `calc/tools/formula_modules.py` | UI-014, REQ-013, ARCH-010, D-5, D-12 | `tests/test_formula_link.py` : cocher trois variables et valider écrit trois `#var(…, domain: …)` dans l'ordre affiché, une annulation les retire ; taper « q_k » propose « Neige · SL » ; les trois chemins écrivent des fichiers identiques ; une variable déjà liée est grisée |
| 16 | **Le Code.** `code_editor.py` (numéros rouge / orange, marge des résultats à droite, brique générique) ; le tampon lu par `parse_text`, écrit seulement s'il se lit, la faute dite à la ligne et à la colonne de Typst ; la ligne du curseur reconnue tout de suite (`command_at`) ; une valeur du module d'arguments écrite par une édition du tampon, le curseur et le défilement gardés ; `TypstHighlighter`. | `calc/tools/code_editor.py`, `calc/tools/formula_code.py` (nouveaux) | UI-019, UI-012, REQ-012, REQ-007, ARCH-016 | `tests/test_formula_code.py` (pytest-qt) : le curseur sur un `#verify` annonce `verify` ; 17 arguments d'un `eq` ; `display-formula: "value"` écrit sans déplacer le curseur, *auto* le retire ; une parenthèse oubliée : le fichier d'avant est intact, la ligne rouge ; chaque mode écrit et relit le fichier |
| 17 | **L'Affichage.** `DomainFileDisplay` prend une source de fichier et un écrivain ; la source d'un domaine de l'ingénieur (éléments tirés des items, écriture par `save`) ; la commande `#include "/Domains/<id>.typ"`, « lire une valeur ailleurs » (`#var("eta", domain: "panne-p2", display: "value-unit")`), le niveau du domaine, les options du domaine cochées (`formula_defaults`), les éléments avec niveau propre, « Rétablir la ligne », « Voir le fichier entier », l'erreur de Typst ou celle de l'état sans doublon. | `calc/tools/domain_file_display.py`, `calc/tools/formula_display.py` (nouveau), `calc/domains/formula_args.py` | UI-020, UI-021, UI-022, ARCH-009, ARCH-007, D-19 | `tests/test_domain_file_display.py` inchangé et vert ; nouveaux cas : cocher `presets: "block"` écrit la ligne sous l'en-tête et recompile en bloc ; un niveau propre posé puis rendu retire `level:` ; aucune base d'`unfold` écrite ; une parenthèse oubliée montre un message, non une page vide |
| 18 | **La liste, l'en-tête, le domaine déplié.** Les domaines sans `children`, l'état (« ✔ 70 % », « 1 ✘ ») au libellé, symboles d'affichage, groupes des onglets spécialisés repliés, archives, « Domaine », « Dupliquer » ; la ligne du nom, de l'id et du fichier, la légende des survols ; la carte « Vérification dépliée » dans les mêmes rangées, ses états sur le trait. | `calc/tools/formula_tab_domains.py`, `calc/tools/formula_tab_unfold.py`, `calc/tools/formula_tab.py` | UI-002, UI-003, REQ-015 | `tests/test_formula_tab.py` (refait) : aucun item ne contient `_("`, un domaine d'un onglet spécialisé n'est pas déplié, le texte de l'en-tête de Panne P2 ; `tests/test_unfold.py` et le test de chaque état de `unfold` : le trait et le mot attendus, aucun état perdu ; `tests/test_member_check_tab.py` inchangé |
| 19 | **Les retraits.** `formula_tab_widgets.py`, `formula_tab_blocks.py`, `formula_layout.py`, `PillPainter`, `FormulaText`, `Block`, l'ancien panneau, Alt+↑/↓ (aucun), `fm_cmd_val`, `fm_cmd_var-unit`, les mots de la pastille ; `tests/test_formula_domain.py` réécrit pour les rangées. | `calc/tools/`, `calc/domains/formula_layout.py`, `tests/test_formula_domain.py`, `tests/test_formula_tab.py` | UI-001, UI-023, ARCH-005, ARCH-017, ARCH-RISK-014 | `grep -rn "var-domain\|fm_cmd_val\|fm_cmd_var-unit\|formula_layout\|PillPainter" calc/tools calc/domains` ne trouve rien de vivant ; `tests/test_module_imports.py`, `tests/test_module_size.py`, `tests/test_i18n.py` verts |
| 20 | **`examples/` tient ses promesses.** Le test qui refuse toute entrée de `examples/data/formulas.json` sans fichier de domaine ; fournir le domaine à `examples/` ou ne plus l'annoncer (selon ce que le test montre). | `examples/`, `tests/` | REQ-017 | le test ; `examples/` se compile comme avant |
| 21 | **La documentation.** `docs/ui/tab-formulas.md` réécrit (trois modes, rangées, pastille, modules, Code, Affichage), `docs/architecture/layout.md` (modules nouveaux), `docs/decisions.md` §13 (une entrée : la fin des pastilles, le formulaire et le code, `presets: "block"` pour un domaine nouveau, une faute dite une fois, la ligne de Typst ; la décision de #40 à la ligne 65 passe à *[superseded in v0.125]* ; sa ligne de `decisions-index.md`), `CHANGELOG.md` (édition ciblée, LF), les pages « Nouveautés » de la version en cours en fr / de / en (`website/content/<lang>/changes/`), une ligne de catalogue pour chacun des six fichiers de test nouveaux (`docs/conventions/testing-catalogue*.md`), la copie du prototype dans `docs/requirements/prototypes/2026-10-24-onglet-domaines/` (`index.html`, `img/`, `norm/`, `pages/`, `prev/`, un `README.md`). | `docs/`, `CHANGELOG.md`, `website/content/*/changes/` | §11 « Documentation », ARCH-008, ARCH-RISK-019 | `tests/test_docs_coherence.py`, `tests/test_site.py` |
| 22 | **La suite complète et la vérification.** La suite en arrière-plan ; la réparation de ce qui échoue ; `verify-requirements` sur la spec ; à la clôture la spec passe en `requirements/completed/` (ARCH-RISK-020). | — | tout | suite verte ; §15 écrit |
| 23 | **L'issue de la police.** Ouvrir (sur la demande de l'ingénieur à la fin du lot) l'**issue GitHub à part** de la police de `#var` et `#eq` en bloc (défaut 9, T85, Q-003, D-18) : le constat, la cause dans `lib/formula.typ`, ce que sa correction change (rendus de référence). | GitHub | Q-003, D-18, T99 | le numéro de l'issue, noté dans §16 |

## 15. Vérification

Vérification indépendante (agent `requirements-verifier`, 25.10.2026, base `4aba5e8`, commits `ac20a24` et `5fbee50`), relue et complétée : aucun ❌. REQ-001 à REQ-019, UI-001 à UI-023, ARCH-001 à ARCH-017 ✅ sur le code et les tests (`test_formula_state`, `test_formula_rows`, `test_formula_input`, `test_formula_form`, `test_formula_code`, `test_formula_link`, `test_formula_tab`, `test_formula_domain`, `test_examples_domains`, `test_norm_excerpts`, `test_units`, `test_views`, `test_i18n`, `test_display_view`, `test_domain_file_display`, `test_member_check_tab`, `test_modes_window` verts). Les ⚠️ relevés et levés ensuite : UI-018 (le survol lié n'allumait que le Formulaire) -- branché sur les lignes du Code (`code_editor.light_lines`), les résultats et la liste des éléments de l'Affichage, testé ; REQ-004 -- un test compile Panne P2 avec et sans la ligne `#calc-defaults` (une ligne par valeur) ; UI-008 -- « lier une variable… » du + ouvre la fenêtre avec sa rangée pour cible, testé ; REQ-015 -- la rangée d'une ligne dépliée dit son état sous son trait, testé. Restent notés, acceptés : REQ-006 (`error` gardé à côté de `blocked_by`, pour les lecteurs existants de `compute`), REQ-016 (le PDF avant/après n'a pas de test dédié : couvert par l'égalité d'octets du fichier), ARCH-017 (`formula_domain.py` passe de 1366 à 1422 lignes, sous le plafond de 1500 ; les ajouts sont `body_pieces`, `parse_text`, `CODES`, les codes de ses refus et les paramètres de `compute`), REQ-014 (les relevés des six clauses ajoutées sont tenus au PDF par test, non revus par l'ingénieur à l'écran). Suite complète : 3387 réussis, 10 sautés, 1055 s.

## 16. Journal d'avancement

| Date | Statut | Fait / reste |
|---|---|---|
| 2026-10-24 | draft | spécification extraite de l'issue #113 (100 points) ; trois questions ouvertes (commande dans un texte, portée de « Annuler », police en bloc) |
| 2026-10-24 | specified | réponses de l'ingénieur reportées : Q-001 A (rangée de texte qui contient sa commande) → D-16, REQ-016, ARCH-011 ; Q-002 A (« Annuler » : suppression et geste de plusieurs lignes) → D-17, UI-007, UI-013, UI-014, ARCH-015 ; Q-003 A (police en bloc : issue à part) → D-18, §8, dernière étape du plan ; aucune question ouverte |
| 2026-10-24 | reviewed | revue d'architecture : APPROUVER AVEC RÉSERVES (20 risques, aucun bloquant) ; REQ-002 et REQ-009 corrigés (l'existant est réemployé : `typst_formula`, `line_display`), REQ-004 sans changement de `parse_domain`, UI-005 compte les items ; ARCH-009 à ARCH-017 ajoutés, D-19 ; un point à trancher à l'approbation (P-1 : l'Affichage est la page compilée de la neige, non le rendu par élément du prototype) ; plan de 23 étapes (§14) |
| 2026-10-24 | approved | approbation unique des huit specs du 24.10.2026 par l'ingénieur (AskUserQuestion) : plan approuvé tel quel ; toutes les propositions « à confirmer » des revues acceptées comme recommandées ; ordre d'implémentation #108 → #115 → #114 → #113 → #112 → #109 → #107 → #106, un agent par issue ; commits et push autorisés au fil du travail ; écarts et questions notés en §16 et posés à la fin |
| 2026-10-25 | implementation | étape 1 : base verte (`-k formula` 151, `-k domain_file` 18, `-k display_view` 13, `-k test_views` 10) ; la fixture `tests/fixtures/domains/panne-p2.typ` copiée de l'artefact (version 2), ses nombres ceux de `compute` sur l'exemple (q_d = 4.238 kN/m, ✔ 9.967 ≤ 11.28 N/mm², η = 88.36 %) ; version en cours 0.125 |
| 2026-10-25 | implementation | étapes 2 à 10 (le modèle, sans Qt) : `units.FormulaError` à code et valeurs (`CODES`), `fd.CODES`, `formula_tab_words.py` (mots `fm_e_*`, `fm_w_*`, `REFUSALS`, `say`) ; `compute` (`uses`, `blocked_by`, `symbol`, `label`, `origin`, `describe`), `formula_links` ; `formula_rows` (`body_pieces`), `formula_undo` ; `parse_text`, `formula_errors` (ligne 19, col. 6 comme `typst compile`) ; `formula_infer` (`_tight` dans `typst_formula`) ; `formula_defaults`, `new_domain(defaults=)`, `norm-ref` → `norm-section` ; `formula_state`, `formula_order` ; `formula_args`, `line_display.values`/`EXCLUDED` ; `excerpts.for_citation`, trois fichiers d'extraits relevés (SIA 260, 261, 265). REQ-001 à REQ-008, REQ-010, REQ-011, REQ-013 (modèle), REQ-014 (données), REQ-019, ARCH-012, ARCH-014, ARCH-015 ; tests `test_formula_state`, `test_formula_rows`, `test_formula_input` |
| 2026-10-25 | testing | étapes 11 à 21 : vues `form`/`code`, jetons `link-*`, `WRITERS` ; `formula_form`, `formula_row`, `formula_new_line`, `formula_modules`, `formula_link_dialog`, `formula_code`, `code_editor`, `formula_display` (`DomainFileDisplay` à source), liste repliée (`GroupedList.roots_first`, `folded`), `norm_bubble.pin_excerpts` ; retraits (`formula_tab_widgets`, `formula_tab_blocks`, `formula_layout`, `SPECS` eq/verify, 32 mots) ; `examples/Domains/poutre-p1.typ` et `build_examples` ; docs, CHANGELOG, Nouveautés, prototype copié. UI-001 à UI-023, REQ-009, REQ-012, REQ-013, REQ-015 à REQ-018, ARCH-002 à ARCH-017 ; tests `test_formula_tab` (refait), `test_formula_form`, `test_formula_code`, `test_formula_link`, `test_examples_domains` |
| 2026-10-25 | completed | étape 22 : suite complète verte (3387, 10 sautés, 1055 s) ; vérification indépendante (§15), quatre ⚠️ levés (survol lié du Code, des résultats et de l'Affichage ; compilation de Panne P2 en bloc ; + → lier ; mot de l'état d'une ligne dépliée) ; spec close et déplacée en `requirements/completed/`. Étape 23 : issues de suivi (défaut 9, défaut 13) ouvertes, numéros dans le journal des écarts |
