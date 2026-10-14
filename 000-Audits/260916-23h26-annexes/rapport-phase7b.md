# Rapport phase 7b — CLAUDE.md §1 à §3.3quater et §3.4 à §10bis, contrôle par lecture (points 2 et 3)

Agent p7b, audit 260916-2326, commit audité `997570db`. Bacs à sable : `projet-phase7b` (export et sondes Typst), `projet-p7b-e` (expériences destructives). Scripts et sorties : `AUDIT/p7b/` (`kw.py`, `wb.py`, `globals.typ`/`globals.json`, `pdftext.py`, `experiments.py`, `probe1.pdf`/`probe1.txt`). Travail interrompu une fois par la limite de session de l'API, repris sans refaire les bacs à sable.

`git -C <projet réel> status --short` : vide au départ et à la fin (rien écrit dans le projet réel).

Dédoublonnage : les constats déjà rendus par p7a (AUD-7-111 sept champs du §3.1, 7-113 comptes du glossaire, 7-114 `02_Belastungsannahmen`, 7-116 minimum des flèches dans la ligne `show-polar-moment` du §10bis, 7-117 `load-loads`, 7-118 `bending.py`/`combinations.py` au §3.5 et au §8, 7-119 `sia261_tables.json`), par p6 (AUD-6-2 feuille `Positions Connectors` dans `calc-engine.typ`, 6-6 `share-min`, 6-7 `#test` dans `calc-engine.typ`, 6-21 ancien appel `show-calc("T001", "bending", …)` du §4 et du §10bis point 1, 6-34 `TYPST_GLOBALS`) et par p3 ne sont pas répétés ; ils sont cités là où ils touchent un constat d'ici.

## Bilan

- Contrôles menés : 67 ; conformes : 40 ; constats : 27 (A : 24, B : 2, C : 1) ; NON FAIT : 2.

## Méthode

1. Lecture du code décrit : `registry.py`, `engine.py`, `io_excel.py`, `export_all.py`, `validation.py`, `domains/snow.py`, `dead_load.py`, `wind.py`, `live_load.py`, `i18n/strings.py`, `lib/calc-engine.typ` (accès aux données, `show-position`, `show-connector`, `calc-block`, `var-row`, `show-input`, `inline-value`, `render-table`, `step-rows`, `show-calc`, `show-check`, `show-live-load`, flèches de `show-polar-moment`, `show-schema`), `lib/formula.typ` (`var`, `var-unit`, `eq`, `unit`, `var-domain`, `val`, `verify`), `lib/i18n.typ`, `commands.typ`, `config.typ`, `Statischer Rapport.typ`, `Sections/*.typ`, les 13 contrats `schemas/*.schema.json`.
2. Export complet dans `projet-phase7b` (sortie identique à la phase 1 : mêmes quatre avertissements).
3. Sonde Typst `projet-phase7b/000-TypstRapport/p7b-probe1.typ` compilée et relue avec pypdf (`p7b/probe1.txt`) : en-tête de `calc-block`, `show-calc` dead-load aux niveaux 1/2/3, snow-load aux niveaux 1/2, wind-load au niveau 1, `domain-ids()`, langue avant/après `set-report-language`, `show-position("S002")`.
4. Sondes d'erreur (fichier temporaire supprimé) : `show-position("NOPE")`, `show-connector("NOPE")`, `show-calc("snow-load", "SL-Dach1")`, `show-calc("dead", "T001")`, ``verify(`1 == 1`)``, `moisture-class-of("NOPE")`.
5. Formules du classeur de charges lues par openpyxl sur la copie du bac à sable (`p7b/wb.py`).
6. Globaux de Typst 0.14.2 lus par `typst query` sur `#metadata(dictionary(std).keys())` (157 noms, `p7b/globals.json`) et croisés avec les liaisons de haut niveau de `lib/*.typ`.
7. Expériences destructives dans `projet-p7b-e` (`p7b/experiments.py`) : E2 `elements` d'un connecteur, E3 défaut planté dans le glossaire avec et sans figures, E4 feuille de charges exportée mais absente du rapport.

## Contrôles conformes (preuve courte)

- §3.0 : chaque contrat de `schemas/` épingle `schema_version` par `const` ou `enum`, et le vérificateur maison ne rencontre aucun mot-clé qu'il ignore (`kw.py` : seuls `type`, `properties`, `required`, `patternProperties`, `items`, `const`, `enum` et des annotations).
- §3.3 : classeurs trouvés par nom, insensible à la casse, fichiers `~$` exclus, pas de sous-dossier, ordre de nom de fichier (`io_excel.find_workbooks`), aucun classeur = erreur bloquante (`registry.open_workbooks`), noms imprimés à chaque export.
- §3.3 : feuille revendiquée par deux préfixes ou présente dans deux classeurs = erreur bloquante nommant les deux ; domaine sans feuille = avertissement (`registry._discover`).
- §3.3 : lecture par classeur contre ses propres tables (`registry.build_calculations`, une appel `read_instances` par classeur).
- §3.3 : `engine` ∈ {excel, python, norm}, `action` ∈ {permanent, variable}, domaine `norm` sans préfixe ni `workbook`/`sheet` et inversement, vérifiés dans les deux sens (`validate_calculations_business`).
- §3.3 : ancienne clé `table` refusée ; `highlight` hors plage refusé ; `formula` d'un tableau exige `norm`/`norm_ref` ; cellule `value` nommant un var inexistant refusée ; ligne de totaux au mauvais nombre de colonnes refusée (`_check_tables`).
- §3.3 : tableau `level` 3 et `place` `above` par défaut, ordre de liste conservé, vars des cellules `value` retirés des lignes (`show-calc`, l. 1704-1708) ; tableau centré dans la colonne de calcul sauf s'il est plus large ou porte une colonne `wide` ; corps à la taille du texte, note en 7,5 pt ; `table-spacing` 1,6 em ; premier tableau sous le titre à 0,7 em ; tableau plus court qu'une page gardé entier (`render-table`).
- §3.3 notes : `group`/`group_label` des vars consécutifs, `description` d'une étape en note, `bold` d'une étape lu comme l'appartenance à `results` pour le gras et pour les opérandes gardés (`show-calc`, l. 1701-1766).
- §3.3bis : cellules, niveaux et ordre du tableau identiques au code (`snow.py`) et à l'export (`h_0`…`q_k11`) ; étape s_k bornée imprimée avec la note « mit » (`is-bounded`) ; formule de q_k qui suit `F29` ; `RESULT_CELLS` contrôlées ; `_check_mu_helper` n'agit que si la cellule μ lit `Dropdowns`.
- §3.3bis : sondes niveau 1 et 2 du cas `SL` conformes (niveau 1 = formule en lettres et en nombres de q_k ; niveau 2 = h_ref, s_k valeurs seules puis q_k).
- §3.3ter : formule par couche, lignes sans matériau ignorées, clé `(Ebene, Material)` puis repli par nom qui refuse l'ambiguïté, `CHOSEN_TOLERANCE` 1e-3, formule de la colonne I lue, aucune adresse de ligne figée (`find_row`) ; sonde : niveau 1 = seulement la valeur choisie en gras, niveau 2 = quatre lignes simples, niveau 3 = tableau « Schichtaufbau » au-dessus avec ses deux totaux.
- §3.3quater : cellules, niveaux et ordre conformes ; q_p étape `bold` ; tableau global niveau 1 dessous, local niveau 2 dessous ; enveloppe calculée sur les directions lues en colonne B ; `glm. (-)` seul optionnel ; comparaison à `F90:F98` bloquante sur désaccord, avertissement sur les cellules sans nombre ; `source` Python du tableau local. `L70` des trois feuilles WL porte toujours `=J19*1*MIN(S79:S81)*J60` (`wb.py`), donc l'avertissement du §3.3quater reste vrai (nom du classeur : AUD-7-114).
- §3.3/§8 : aucun `calc-block` dans `Sections/004`, scope guard absent pour un domaine de calcul et pour les domaines `connection`/`connector` (`resolve-source`).
- §3.4 : aucun `assignments.json`, aucun module d'affectation.
- §3.6 : `export_all.run()` construit et valide tout avant d'écrire ; `ValidationError`/`EngineError` donnent un code de sortie 1 sans trace.
- §3.7 et §4 : `resolve-level` est le seul point de résolution (9 appels : `show-input`, `show-calc`, `show-live-load`, `show-polar-moment`, `show-connector-resistance`, `var`, `var-unit`, `eq`, `verify`) ; `uniform-level` l'emporte sur `level:`.
- §4 : `number-digits` 3 dans `Statischer Rapport.typ` ; `fmt-decimals` construit les chiffres à partir d'un entier et supprime les zéros finaux.
- §4bis : `config.typ` ne lit aucun état ; `doc-lang`/`doc-region` appliqués dans `conf` ; `set-report-language` refuse une langue inconnue en nommant les trois ; `tl-of` ne traduit que ce que le glossaire porte, puis gabarit par segments littéraux ; `t-label` met une espace fine insécable en français ; `value-word` et symbole-mot traduits (`render-symbol`) ; aucune lecture de la langue hors de `lib/`.
- §4bis : `strings.py` refuse langue manquante, chaîne vide, trous différents, terme portant son propre allemand (vérifié par E3a : l'export échoue « terms[…].fr is empty »).
- §5 : `calc-block` accepte une ou plusieurs positions, un `axes` commun ou un par position (assertion sur le nombre), pile `block-scope` imbriquable, `plan: auto` = détail surligné de chaque plan qui porte les positions ; sonde : un `show-input` de charge dans un bloc ne déclenche pas le garde.
- §6 et §6bis : les `get-*` du §6 existent ; `render-symbol` évalue le symbole en mode math.
- §7 : huit colonnes exportées ; `_column` bloquant sur colonne requise absente ; colonne d'humidité requise, cellule facultative, entier 1-3 ou `null`, `Wood moisture class` encore lu ; feuille `Positions` sans `Positions Element` refusée ; `positions-index.json` dans l'ordre de la feuille, doublon bloquant ; `Sections/003` boucle sur `position-ids()` ; `strength_class` optionnel dans `position.schema.json`, version 1.2.
- §7bis : clés descriptives de `connector._descriptive` ; `predrilled` dérivé (`_predrilled`) ; avertissement pour les feuilles retirées et pour un id qui ne commence pas par le symbole (log d'export) ; `Sections/003` boucle sur `connector-ids()`.
- §9 : une seule note par var fusionnant `description` et `choices` (`var-row`), dès le niveau 2 dans `show-input` et `show-calc`.
- §10 : citation « norme §clause » en 8 pt dans une colonne de 3,8 cm, sans « § » si la clause est vide (`norm-text`) ; une seule colonne quand aucune ligne n'est citée (`annotated-rows`).
- §10bis table : comportements vérifiés par lecture pour `show-calc`, `show-input`, `inline-value`, `show-check`, `var-of`/`value-of` (sans garde de bloc), `var` (niveau 1 rien, 2 ligne, 3 description sur la ligne), `verify` (niveaux 1/2/3, signe imprimé selon la vérité, tolérance relative 1e-9, dimensions différentes bloquantes), `eq` (niveaux, substitution par mots entiers la plus longue clé d'abord), `unit` (table par défaut identique à la liste), `var-unit`, `var-domain`/`val`, `moisture-class-of` (assertion listant les positions), `show-live-load`, `live-load`.
- §10bis règle des globaux : aucune liaison de `lib/*.typ` ne porte le nom d'un des 157 globaux de Typst 0.14.2 (intersection vide, `globals.json`).
- §13/§14 dans mon périmètre, encore ouverts et bien ouverts : `domains` toujours `{}` pour chaque position ; coefficients c_f et c_pe/c_pi du vent non imprimés ; `N37`/`N38` de `GiebeldachLM2` toujours refusés ; bloc μ de `Dropdowns` toujours lié à une seule feuille (`=SL!H23`) ; aucun facteur ψ lu.

## Constats

### AUD-7-201 | A | CLAUDE.md:197, 242 (§3.1)
La note du §3.1 dit que `material` porte aussi la classe (« `GL24h` is both the material family and its grade ») et que « nothing anywhere parses » `dimension`. Depuis v0.77, `material` vaut `Fichte` et la classe est `strength_class` (`data/positions/T001.json` : `"material": "Fichte", "strength_class": "C24"`), et depuis v0.75 `schema.parse_section` lit `dimension` (le §7 le dit lui-même). L'exemple JSON n'a pas `strength_class`. (p7a a traité le nombre de champs de la ligne 190.)
Remplacements :
1. `  "material": "GL24h",` → `  "material": "Fichte",` suivi d'une nouvelle ligne `  "strength_class": "GL24h",` (dans le bloc JSON du §3.1 ; la chaîne est unique).
2. `` `material` doubles as the "quality"/grade (e.g. `GL24h` is both the material family and its grade); `dimension` is **free descriptive text**, carried through exactly as typed in Excel (`"140/400"` for a cross-section, `"180"` for a panel thickness) — no `{b, h}` object, and nothing anywhere parses it. Dimensions a calculation needs are given manually in Typst, not read back out of this string (§7). `` → `` `material` is what the element is made of (`Fichte`, `Stahl`) and `strength_class` its strength class (`C24`, `GL24h`, `S355`), two columns since v0.77 (§7); `dimension` is **free descriptive text**, carried through exactly as typed in Excel (`"140/400"` for a cross-section, `"180"` for a panel thickness) — no `{b, h}` object. Dimensions a calculation needs are given manually in Typst, not read back out of this string (§7), with one lenient exception: a detail schema's element takes its default b and h from it (`schema.parse_section`, v0.75, §3.3decies). ``
Test : aucun (texte).

### AUD-7-202 | A | CLAUDE.md:1052, 1059, 1063, 1219 (§7, §10bis)
Le §7 se contredit : le tableau dit « descriptive text, never parsed » et le paragraphe « no code anywhere splits, parses, or does arithmetic on it », puis la fin du même paragraphe décrit `schema.parse_section`. L'exemple d'impression « `T001: Träger, C24, 100/200 mm, Feuchteklasse 1` » ne correspond pas au code : la sonde imprime `T001: Träger, Fichte C24, 100/200 mm, Feuchteklasse 2` (matériau et classe joints, `show-position` l. 668). Le message d'erreur cité (« Wood moisture class is 4 ») nomme l'en-tête trouvé, donc `moisture class is 4` avec l'en-tête actuel (`export_all._moisture_class` l. 80). La ligne `show-position` du §10bis ne mentionne pas la classe de résistance.
Remplacements :
1. `` | `dimension` | descriptive text, never parsed: `` → `` | `dimension` | descriptive text, parsed nowhere but by a detail schema's element for its default b and h (§3.3decies): ``
2. `and no code anywhere splits, parses, or does arithmetic on it.` → `and no code splits, parses, or does arithmetic on it but the one lenient reader named at the end of this paragraph.`
3. `` `show-position` prints it after the section, `T001: Träger, C24, 100/200 mm, Feuchteklasse 1`, `` → `` `show-position` prints it after the section, `T001: Träger, Fichte C24, 100/200 mm, Feuchteklasse 1`, ``
4. `` (`Positions Element, T001: Wood moisture class is 4 -- expected 1, 2, 3 or nothing`) `` → `` (`Positions Element, T001: moisture class is 4 -- expected 1, 2, 3 or nothing`, the header named as the sheet spells it) ``
5. `` `type`, `material` (skipped when blank), `dimension` + `units`, `` → `` `type`, `material` and `strength_class` as one part (`Fichte C24`, each skipped when blank), `dimension` + `units`, ``
Test : `tests/test_export.py` — compiler `show-position("T001")` sur une position de fixture `Fichte`/`C24` et vérifier `Fichte C24`.

### AUD-7-203 | A | CLAUDE.md:149 (§2 règle 3)
« Every piece of data is attached to a position, with its plan axes » contredit le §8 (« every link from a position to a load is gone »), la décision §13 « No load-to-position link of any kind » et le code : une charge, une connexion, un connecteur et un schéma n'appartiennent à aucune position (`find-calculation`, commentaires l. 224, 230, 236 ; `Sections/004` sans `calc-block`).
Remplacement : `3. **Every piece of data is attached to a position**, with its plan axes (supplied at display time, see point 12).` → `3. **What a calculation concerns is stated in the report, never in the data**: a `calc-block` attributes calculations to positions and their plan axes at display time (§5, point 12), and a load, a connection, a connector or a schema belongs to no position (§8, §14).`
Test : aucun (texte).

### AUD-7-204 | A | CLAUDE.md:806, 811, 813, 814 (§3.6)
« a numeric result is not negative » est faux : `validation.py:241` dit « A result is deliberately not required to be positive » et l'export porte des résultats négatifs (`wind-load/WL-Velo/qk_min_db` = −0,34, imprimé dans la sonde). « stresses >= 0 » ne correspond à aucune règle (la seule règle de signe est `eta < 0` d'un check) ; la cohérence des combinaisons n'est vérifiée par rien, `combinations.py` n'existant pas ; « `value` is a number » oublie les valeurs texte (`lastmodell = Flachdach`, schéma `["number", "string"]`).
Remplacements :
1. `` - `value` is a number, `` → `` - `value` is a number, or text for a var the workbook fills from a dropdown (§3.3bis), ``
2. `- physical constraints (e.g. stresses >= 0),` → `` - physical constraints where the sign is known (e.g. a check's `eta` is not negative, a layer's `Dist.` is not 0), ``
3. `` - combination consistency (e.g. a ULS combination does reference calculations that exist in `calculations.json`), `` → `` - combination consistency, once `combinations.py` exists (§3.5, §14): a ULS combination will have to reference calculations that exist in `calculations.json` — nothing checks it today, there being no combination, ``
4. `` - every name in an instance's `results` is a declared var, and a numeric result is not negative (§3.3). `` → `` - every name in an instance's `results` is a declared var whose value is a number or text — deliberately not required to be positive, a wind suction or an uplift being a negative result (§3.3quater). ``
Test : `tests/test_export.py` — une instance dont un résultat vaut −1 passe `validate_calculations_business`.

### AUD-7-205 | B | CLAUDE.md:261 (§3.3), 2072 (§13 v0.18) ; Sections/004-einwirkungen.typ:7-9
Le §3.3 dit « copying a sheet in Excel adds that case to the report — no Python edit, no Typst edit » et « `Sections/004-einwirkungen.typ` loops over `instance-ids(domain)` » ; la décision §13 v0.18 retient « copying a sheet adds a case to the report with no code edit ». Or `Sections/004` nomme chaque cas à la main depuis le commit `3478841f` (v0.53 : 0 occurrence de `instance-ids(` contre 2 dans `b0868e07`), et son propre commentaire l. 9 affirme encore « Nothing is listed by hand either ». Preuve : E4 — `EL+AL-Wand` est exporté (`calculations.json`) mais absent de `Sections/004` et de `phase1-pdf/as-written.pdf` (pypdf : seuls `EL+AL-Dach mit Wasser`, `… ohne Wasser`, `…DachRand`). Le « prix accepté » de la décision est inversé : une feuille renommée ne disparaît plus en silence, elle casse la compilation.
Options :
(a) revenir à la décision : `Sections/004` boucle sur `instance-ids` (les niveaux et titres par cas écrits à la main se perdent ou passent dans les données) ;
(b) garder la liste à la main et amender la documentation : §3.3 `` So **copying a sheet in Excel adds that case to the report** — no Python edit, no Typst edit, no id to invent. `calc/registry.py` discovers the sheets, `Sections/004-einwirkungen.typ` loops over `instance-ids(domain)`. `` → `` So **copying a sheet in Excel adds that case to the export** — no Python edit, no id to invent — and a section that loops over `instance-ids(domain)` prints it with no Typst edit either. `calc/registry.py` discovers the sheets; `Sections/004-einwirkungen.typ` names its cases by hand since v0.53, each with its own level and title, so a copied sheet reaches this report once it is named there. `` ; §13 `copying a sheet adds a case to the report with no code edit,` → `copying a sheet adds a case to the export with no code edit, and to the report with none where a section loops over instance-ids (Sections/004 names its cases by hand since v0.53),` ; commentaire `Sections/004` l. 9 `// Nothing is listed by hand either. Each load is` … `adds those cases to the report with no edit here at all.` → `// The cases are named by hand, each with its level and title. Each load is a *domain* whose instances are the sheets carrying its prefix, in every workbook of the project folder whose name contains "Belastungsannahmen" (CLAUDE.md section 3.3): copying a sheet in Excel adds its case to the export, and it reaches this page once it is named here -- `#for s in instance-ids("dead-load") { show-calc("dead-load", s) }` would show every case with no edit.`
Contrôle à faire devenir test (quel que soit le choix) : chaque instance de `data/calculations.json` est citée par `Sections/*.typ` ou la section boucle sur `instance-ids`, sinon avertissement.

### AUD-7-206 | A | CLAUDE.md:351, 386 (§3.3bis)
« Two sheets ship today … `SL-Dach1` … `SL-Dach2` » et « 👉 On the workbook as it stands this fires on `SL-Dach2` … » décrivent un état disparu : le classeur n'a qu'une feuille `SL` (`wb.py`), le bloc d'aide est lié à elle (`Dropdowns!C57 = SL!H23`, `F64 = …SL!H23…`) et l'export passe sans erreur. Remarque signalée par p7a pour p7b.
Remplacements :
1. `` Two sheets ship today, and they exercise both shapes the reader has to handle: `SL-Dach1` (`Flachdach`, one result q_(k,11)) and `SL-Dach2` (`GiebeldachLM2`, two results q_(k,11) and q_(k,12)). `` → `` The reader handles both shapes a sheet can take: a flat roof with one result q_(k,11) (the project's one SL sheet today, `SL`) and a pitched load model with two results q_(k,11) and q_(k,12) (`SL-Dach2` of the workbook this module was written against, `GiebeldachLM2`). ``
2. `` 👉 On the workbook as it stands this fires on `SL-Dach2` `` → `` 👉 On the workbook of v0.24 this fired on `SL-Dach2` `` (le reste de la phrase inchangé), et ajouter à la fin du paragraphe : `` The project's workbook today carries one SL sheet, `SL`, and the helper block is anchored to it, so the check passes; the next SL sheet copied from it will trip it. ``
Test : `tests/test_snow.py` (ou `test_export.py`) — une fixture à deux feuilles SL partageant `Dropdowns` doit échouer en nommant `H26`.

### AUD-7-207 | A | CLAUDE.md:286-332 (§3.3, exemple JSON)
L'exemple donne `ce` au niveau 2 alors que le code et le tableau du §3.3bis le mettent au niveau 3 (`snow.py:153`, export `('ce', 3)`), et les domaines `snow-load` et `dead-load` n'y portent pas le champ obligatoire `action`.
Remplacements : `"label": "Expositionsbeiwert", "level": 2,` → `"label": "Expositionsbeiwert", "level": 3,` ; `      "label": "Schneelast",` → `      "label": "Schneelast", "action": "variable",` ; `      "label": "Eigen- und Auflasten", "engine": "python",` → `      "label": "Eigen- und Auflasten", "action": "permanent", "engine": "python",`
Test : aucun (exemple).

### AUD-7-208 | A | CLAUDE.md:835 (§4)
L'exemple montre `default: "1"`, `Statischer Rapport.typ:13` porte `default: "2"`. (L'ancien appel `show-calc("T001", "bending", …)` du même bloc est AUD-6-21.)
Remplacement : `#let default-level = int(sys.inputs.at("level", default: "1"))` → `#let default-level = int(sys.inputs.at("level", default: "2"))`
Test : aucun.

### AUD-7-209 | A | CLAUDE.md:906 (§4bis)
« `render-prose` … at the six sites » : `grep render-prose(` en compte davantage — titre de tableau et cellule texte portant `$` (v0.77, `calc-engine.typ:1426, 1478`), avertissements d'un connecteur (l. 2547), description imprimée par `#var` et `#var-unit` (`formula.typ:826, 899`), en plus des six cités.
Remplacement : `` `render-prose` in `lib/calc-engine.typ` does it, at the six sites that print a sentence from the data — a table's `note`, a var's `description` and each of its `choices` (the value and the text beside it), a step's `description`, and the footnote of a live load. `` → `` `render-prose` in `lib/calc-engine.typ` does it wherever a sentence from the data is printed — a table's `title`, `note` and a text cell carrying a dollar (v0.77), a var's `description` and each of its `choices` (the value and the text beside it), a step's `description`, the footnote of a live load, a connector's warnings, and the description `#var` and `#var-unit` print (§10quinquies). ``
Test : aucun.

### AUD-7-210 | A | CLAUDE.md:922 (§4bis) ; calc/export_all.py:148 ; calc/i18n/strings.py:105
« Each stops the export naming the key » n'est vrai que si une figure demande un mot au glossaire : `strings._load()` n'est appelé que par `connection_svg`, `connector_svg`, `statics_svg`, et `strings.check()` n'est appelé par personne. Preuve E3 : défaut planté (`terms[…].fr = ""`) → export complet exit 1, export du même projet sans connecteurs/connexions/modèles/schémas/plans exit 0. De plus, la vérification « language list that is not the one `lib/i18n.typ` expects » est faite par `i18n.typ` à la compilation, Python ne comparant qu'à son propre `LANGUAGES`.
Correction : appeler `strings.check()` au début de `export_all.run()` (avant `io_excel.read_workbook`). Texte : `` or a language list that is not the one `lib/i18n.typ` expects. Each stops the export naming the key, exactly as a defective norm table does. `` → `` or a language list other than `LANGUAGES` (which `lib/i18n.typ` asserts again at compile time). `export_all.py` checks it first, so each stops the export naming the key, exactly as a defective norm table does. ``
Test : `tests/test_i18n.py` — sources vides + glossaire au `fr` vide ⇒ `export_all.run()` lève `ValidationError`.

### AUD-7-211 | A | 000-Python/lib/i18n.typ:52-54
Le bloc `///` de `set-report-language` dit « it may stand anywhere in the preamble, since `config.typ` reads the final value » ; `config.typ` ne lit aucun état depuis v0.54 (§4bis) et la sonde montre qu'un mot imprimé avant l'appel reste allemand (`MARK-LANG1 Massgebend`, puis `Déterminant` après `set-report-language("fr")`). Ce texte est l'infobulle de Tinymist et la notice de l'onglet Commandes.
Remplacement : `beside `report-level.update` and `number-digits.update` -- it may stand anywhere in the preamble,` + ligne suivante `/// since `config.typ` reads the final value.` → `beside `report-level.update` and `number-digits.update`. Put it before the first thing the engine prints:` + `/// like every state, it reaches only what follows it, and `config.typ` reads no state (CLAUDE.md section 4bis).`
Test : exemple figé ou test de compilation : un `t-str` avant l'appel reste en allemand.

### AUD-7-212 | A | CLAUDE.md:1194, 1199 (§10bis point 2)
« Every `show-*` function keeps the same positional-argument order — `domain`, then `instance` » et « it holds for every other `show-*` function » : neuf `show-*` prennent un seul identifiant (`show-position`, `show-connector`, `show-connector-resistance`, `show-polar-moment`, `show-live-load`, `show-plan`, `show-plan-legend`, `show-static-model`, `show-schema` ; signatures l. 657-2500).
Remplacements : `` **2. A stable, predictable call shape.** Every `show-*` function keeps the same positional-argument order — `` → `` **2. A stable, predictable call shape.** Every `show-*` function that reads a calculation record — `show-calc`, `show-input`, `show-check`, and `inline-value` beside them — keeps the same positional-argument order — `` ; `` Once an engineer has learned this order for `show-calc()`, it holds for every other `show-*` function, `` → `` Once an engineer has learned this order for `show-calc()`, it holds for the other three, the remaining `show-*` functions taking the one id they display (`show-position("T001")`, `show-plan("Pavillon")`), ``
Test : aucun.

### AUD-7-213 | A | CLAUDE.md:1201 (§10bis point 3)
« `commands.typ` re-exports the whole of `lib/calc-engine.typ` » et « A second library file would be re-exported … the same way » : `commands.typ` importe aussi `lib/formula.typ` (et `i18n.typ` via `calc-engine.typ`). « Today every name but `fmt` is hyphenated » est faux : `fmt`, `var`, `eq`, `val`, `unit`, `verify`, `t`, `tl`, `sup`, `quantity`, `tokenize`, `placeholder`, `present`, `substituted`, `converted`, `glossary` ; aucun n'est un global de Typst 0.14.2 (intersection vide avec `dictionary(std).keys()`). Voir AUD-6-34 pour la liste de test.
Remplacements : `` `000-TypstRapport/commands.typ` re-exports the whole of `lib/calc-engine.typ` with a wildcard, `` → `` `000-TypstRapport/commands.typ` re-exports the whole of `lib/calc-engine.typ` and `lib/formula.typ` (and, through the first, `lib/i18n.typ`) with a wildcard, `` ; `` every top-level binding of `calc-engine.typ` reaches every file, `` → `` every top-level binding of those files reaches every file, `` ; `` Today every name but `fmt` is hyphenated, and `fmt` is not a global. A second library file would be re-exported from `commands.typ` the same way. `` → `` Several names are not hyphenated — `fmt`, `var`, `eq`, `val`, `unit`, `verify`, `t`, `tl` among them — and none is a Typst global, checked against `dictionary(std)`; another library file would be re-exported from `commands.typ` the same way. ``
Test : remplacer la liste fixe de `test_no_engine_name_shadows_a_typst_global` par `typst query` sur `#metadata(dictionary(std).keys())`.

### AUD-7-214 | A | 000-Python/lib/calc-engine.typ:657-662 ; CLAUDE.md:1203 (§10bis)
« every `show-*` function validates its lookup-key arguments with `assert(..., message: ...)` » : `show-position("NOPE")` échoue sur `file not found (searched at …\data\positions\NOPE.json)`, sans la liste des positions (sonde), alors que `moisture-class-of` et `show-connector` listent les ids valides.
Correction (code) : en tête de `show-position`, `let known = position-ids()` puis `assert(type(position) == str and position in known, message: "show-position: no position " + repr(position) + " -- " + (if known.len() == 0 { "none in Positionen.xlsx yet (sheet Positions Element)" } else { "valid positions: " + known.join(", ") }))` ; bullet `///` : `Must have a data/positions/<position>.json file (unknown ids fail via Typst's own file-not-found error -- positions can't be enumerated from Typst itself).` → `An unknown id fails listing the valid ones.`
Test : `tests/test_report.py` — compiler `show-position("NOPE")` et attendre `valid positions:`.

### AUD-7-215 | A | 000-Python/lib/calc-engine.typ:177
Doc de `domain-ids()` : « Every calculation domain whose instances are workbook sheets … e.g. ("dead-load", "snow-load") » ; la sonde renvoie `("dead-load", "snow-load", "wind-load", "live-load")`, `live-load` étant un domaine de norme.
Remplacement : `/// Every calculation domain whose instances are workbook sheets (data/calculations.json), e.g. ("dead-load", "snow-load"). Data access, not a display function.` → `/// Every calculation domain of data/calculations.json, in its order -- the sheet domains, then the norm tables: ("dead-load", "snow-load", "wind-load", "live-load"). Connections and connectors are addressed as domains too but are not listed here. Data access, not a display function.`
Test : aucun.

### AUD-7-216 | A | 000-Python/lib/formula.typ:796
Bullet `descr` de `#var` : « printed as a footnote at level 3 » ; le code imprime la description sur la ligne, après un tiret cadratin (l. 824-826), comme le dit la table du §10bis.
Remplacement : `/// - descr (str, none): what the value is, printed as a footnote at level 3.` → `/// - descr (str, none): what the value is, printed on the line after the unit, set apart by an em dash, at level 3.`
Test : aucun (le test des blocs `///` ne lit pas le sens).

### AUD-7-217 | A | 000-Python/calc/engine.py:58-86
`step()` accepte `group` et `group_formula` et sa docstring affirme qu'ils servent aux charges de neige (« one q_k formula above three substituted lines ») ; aucun module ne les passe (`grep group_formula` : seul `engine.py`) et `calc-engine.typ` ne lit pas le `group` d'une étape (seuls les `group` de colonnes l. 1449 et de vars l. 1752). Le comportement décrit n'existe pas ; CLAUDE.md ne le décrit pas non plus. (Non listé par AUD-6-11, qui ne relevait que des définitions entières.)
Correction : retirer les deux paramètres, les deux `if` et le deuxième paragraphe de la docstring de `step()`. Test : aucun (le test de code mort proposé par AUD-6-11 le couvrirait avec les paramètres).

### AUD-7-218 | A | Sections/006-nachweise.typ:7
Le commentaire renvoie à `#test` (retiré en v0.61, remplacé par `#verify`). AUD-6-7 ne couvre que `calc-engine.typ`.
Remplacement : `A comparison written by hand in the report is marked with #test, which performs it (section 10bis)` → `A comparison written by hand in the report is marked with #verify, which performs it (sections 10bis, 10quinquies)`
Test : étendre le test « aucun nom retiré n'est vivant » (AUD-6) à `Sections/`.

### AUD-7-219 | B | 000-Python/lib/calc-engine.typ:1176 ; CLAUDE.md §10bis ligne `show-schema`, §3.3decies
`show-schema(…, aids: false, …)` retire par défaut les aides que la source a marquées `shown`. Le §3.3decies dit « A point or a centre carries `shown: true` by default and reaches the report » et la ligne du §10bis présente `aids: false` comme un choix (« leaves the construction aids out, for a figure that wants the detail alone »). Preuve : `data/schemas/VU-Skizze-de.svg` a 857 caractères entre `<!-- aids -->` et `<!-- /aids -->` (points A12-A15, `shown: true`), retirés par l'appel sans argument. Recoupe p7c (§3.3decies).
Options : (a) défaut `aids: true`, et les aides montrées atteignent le rapport ; (b) garder `false` et écrire au §3.3decies et au §10bis que les aides montrées n'apparaissent qu'avec `aids: true`.
Test : compiler `show-schema("VU-Skizze")` et vérifier la présence ou l'absence du bloc d'aides selon l'option choisie.

### AUD-7-220 | A | CLAUDE.md:1106 (§7bis) ; calc/tools/connectors_tab.py:1480
« `elements` … so «(Bauteile: T001, S001)» is never typed and never stale » : `connector._descriptive` recopie `source["elements"]` tel quel ; la liste n'est recalculée qu'à l'enregistrement dans le Katalog. Preuve E2 : `elements: ["ZZZ999"]` écrit dans la source → exporté `['ZZZ999']` alors que `ZZZ999` n'est pas une position et que les membres n'en nomment aucune.
Remplacement : `` so «(Bauteile: T001, S001)» is never typed and never stale `` → `` so «(Bauteile: T001, S001)» is never typed — it is the list of the last save, not read again at export: an element's position changed in «Schémas» reaches it when the connector is saved again `` ; même correction dans le commentaire de `connectors_tab.py:1480` (`is never typed and never stale.` → `is never typed; it is refreshed on every save.`). Variante de code (qui rendrait le texte actuel vrai) : dériver `elements` dans `_descriptive` à partir des `member_position` déjà résolus.
Test : `tests/test_connectors.py` — la valeur exportée de `elements` égale les positions des éléments des membres bois.

### AUD-7-221 | A | 000-Python/lib/calc-engine.typ:2451
`connector-headline` imprime le diamètre par `fmt-decimals(d.value, 3)` au lieu du réglage du document, contrairement au §4 (« every number the engine prints goes through `fmt-decimals` » au `number-digits`). Aucun écart visible aujourd'hui (réglage 3, d = 10).
Correction : `#fmt-decimals(d.value, 3)` → `#fmt-decimals(d.value, number-digits.get())` (la fonction est appelée dans le `context` de `show-connector-resistance`).
Test : compiler `#number-digits.update(1)` + `show-connector-resistance` sur un connecteur de d = 10,25 et attendre `10.3`.

### AUD-7-222 | A | CLAUDE.md:979 (§5)
Le rendu cité « │ T001: Träger, GL24h, 140 × 400 mm (Achse X3 / Achse YC) — Roof beam, axis 3-C » ne correspond pas au code : dimension écrite `140/400` (jamais `×`), matériau et classe joints, classe d'humidité, et description absente par défaut (`description: false`). Sonde : `T001: Träger, Fichte C24, 100/200 mm, Feuchteklasse 2 (Achse X3 / Achse YC)`.
Remplacement : `│ T001: Träger, GL24h, 140 × 400 mm (Achse X3 / Achse YC) — Roof beam, axis 3-C` → `│ T001: Träger, Fichte GL24h, 140/400 mm, Feuchteklasse 1 (Achse X3 / Achse YC)`
Test : aucun.

### AUD-7-223 | A | CLAUDE.md:168, 186 (§3.0)
« Every JSON file produced by the pipeline (`positions`, `loads`) » nomme un fichier `loads` disparu en v0.18 et omet les autres ; « the `schema_version` is read and displayed/archived the same way as a norm edition number » : Typst ne lit `schema_version` nulle part (`validation.py:85` le dit : « Typst, which reads the field nowhere at all »), il est vérifié à l'export et archivé avec `data/`.
Remplacements : `` (`positions`, `loads`) `` → `` (`positions`, `positions-index`, `calculations`, `connectors`, `connections`, `plans`, `statics`, `schemas`) `` ; `` (the `schema_version` is read and displayed/archived the same way as a norm edition number, see §1bis) `` → `` (the `schema_version` is checked against its contract on every export (§3.6) and archived with `data/` (§12); the report itself does not print it, §1bis) ``
Test : aucun.

### AUD-7-224 | A | 000-Python/lib/calc-engine.typ:2424 ; lib/formula.typ:1127
`test-aliases` déclare `"==": "="`, mais `relation-ops` ne contient pas `"=="` : ``#verify(`1 == 1`)`` est découpé sur le premier `=` et échoue « verify: cannot evaluate "= 1" » (sonde). L'alias est inatteignable.
Correction : insérer `"=="` en tête de `relation-ops` (`("==", "<=", ">=", "!=", …)`), ou retirer l'alias. Test : ``#verify(`F == F`)`` compile et marque ✔.

### AUD-7-225 | A | 000-Python/lib/calc-engine.typ:246-252 ; CLAUDE.md:§10bis ligne `show-calc`
La table dit « An unknown `domain` panics listing both the valid domains and the valid positions » ; avec un domaine inconnu et une instance qui est une position, le message ne cite que les domaines de la position (`show-calc("dead", "T001")` → « position 'T001' has no domain 'dead' -- its domains: none (it carries no calculation) »), sans les domaines de calcul, alors que la faute de frappe la plus probable est sur `dead-load`.
Correction : dans cette branche, ajouter au message `" -- calculation domains: " + (doms.keys() + (connection-domain, connector-domain)).join(", ")`. Test : compiler l'appel et attendre `calculation domains: dead-load`.

### AUD-7-226 | A | CLAUDE.md:1063 (§7), 2231 (§14)
§7 « Nothing calculates with it yet (§14). » et le point ouvert §14 « The moisture class, not calculated with yet … no calculation reads it … whether a connector takes the class of the elements it joins (§7bis) or needs a column of its own » : c'est réalisé pour les connecteurs depuis v0.68/v0.70 (§3.3nonies) — `connector.resolve_moisture` prend la classe de la connexion ou, à `null`, la pire des positions des membres (`moisture_from`) et en tire η_w (`VU-SD-10` : `eta_w = 0.8`, source `norm:SIA 265:2021, Tabelle 4`). Point 3 : point ouvert déjà réalisé.
Remplacements : `Nothing calculates with it yet (§14).` → `A connector reads it through its members' positions when the connection states no class of its own (§3.3nonies); no element calculation reads it yet (§14).` ; la puce §14 entière `- **The moisture class, not calculated with yet** (v0.36, §7). … or needs a column of its own.` → `- **The moisture class, read by the connectors only** (v0.36, §7; settled for a connector in v0.70, §3.3nonies: one class for the connection, stated in its source or, left null, the worst of its members' positions). No element calculation reads it yet, there being none (the first item above); the factors it picks for one belong in `calc/norms/`, keyed by the class, so that no domain module restates it. One question stays open for then: whether a blank class on a timber element stops that element's calculation or is only a warning at export.`
Test : aucun (texte).

### AUD-7-227 | C | divers
Informations sans correction évidente : (1) §2 règle 2 « rendered with the same display function » : un même enregistrement a plusieurs fonctions d'affichage (`show-calc` et `show-live-load`, `show-polar-moment`, `show-connector-resistance`), accepté par le §13 v0.49 ; (2) §6 « every new display function must go through these get-* » : `show-check` lit `c.eta`/`c.status`, `connector-summary` et `connector-headline` lisent `q.value`/`d.value` directement ; (3) `show-polar-moment` exige qu'un var soit exactement en `kN`/`kNm` (comparaison de chaînes, l. 2131) : un var du registre calculé après `#unit("N")` est refusé au lieu d'être converti, alors que `formula.typ` sait convertir ; (4) §13 « No load-to-position link … the domain modules that computed it are kept, uncalled, rather than deleted » est historique et explicitement renversé par l'entrée v0.59 : rien à corriger, mais une note « (reversed in v0.59) » éviterait la lecture au présent.

## NON FAIT

- Compilation du rapport entier après les corrections proposées : phase 9 (session principale), aucune correction appliquée ici.
- Vérification visuelle (PNG) du gras des cellules `value` du tableau global du vent au niveau 1 : l'extraction de texte pypdf ne rend pas le gras ; relève de la phase 3.

## Vérifications manuelles proposées à l'ingénieur

- AUD-7-205 : choisir entre une boucle `instance-ids` dans `Sections/004` et une liste à la main documentée ; dans les deux cas, décider si `EL+AL-Wand` doit figurer au rapport.
- AUD-7-219 : décider si les points de construction marqués « visibles » doivent apparaître par défaut dans `show-schema`.

## Contrôles qui pourraient devenir des tests

- Chaque instance exportée est nommée par `Sections/` ou atteinte par une boucle `instance-ids` (AUD-7-205).
- Export d'un projet sans sources avec un glossaire défectueux : échec bloquant (AUD-7-210).
- Globaux de Typst lus par `dictionary(std)` au lieu d'une liste fixe (AUD-7-213, AUD-6-34).
- `show-position` d'un id inconnu liste les positions (AUD-7-214) ; `show-calc` d'un domaine inconnu liste les domaines de calcul (AUD-7-225).
- `elements` exporté = positions des éléments des membres (AUD-7-220).
- Un résultat négatif passe la validation (AUD-7-204).
- ``#verify(`a == b`)`` compile (AUD-7-224).
- `connector-headline` suit `number-digits` (AUD-7-221).
