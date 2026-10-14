# Rapport phase 7c — CLAUDE.md §3.3quinquies à §3.3decies, points 2 et 3 (audit 260916-2326)

Agent p7c. Bac à sable `projet-phase7c`. Scripts et sorties dans `AUDIT/p7c/` (`t_connection.py`, `t_connector.py`, `t_crop.py`, `t_schema_labels.py`, `t_typst.py`, PDF des sondes dans `p7c/typ/`). Projet réel : `git status --short` vide au départ et à la fin. Les sources modifiées dans le bac à sable pour les sondes (`connections/VU-MP-1.json`, `connectors/VU-SD-10.json`) ont été remises à l'identique (`cmp` avec le projet réel) et réexportées.

Dédoublonnage : lus `rapport-phase2.md`, `rapport-phase3.md`, `rapport-phase6.md`, `rapport-phase7a.md`, `rapport-phase7b.md`. Non re-signalés (déjà rendus) : AUD-2-6 (numéros d'équations (126)/(127) dans `dowel.py`), AUD-6-2 et AUD-6-5 (commentaires de connecteurs « Positions Connectors », formes de `material` dans `connector.py:7`), AUD-6-21 et AUD-7-119 (chemins `calc/norms/sia263/`, `sia261_tables.json` du §14), AUD-6-23 (ids d'exemple `A01`, `SD001`), AUD-6-24 et AUD-7-127 (`plan_svg.FONT`), AUD-7-115 (« a third » / `SHARE_MIN` du §3.3octies), AUD-7-116 (minimum des flèches au §10bis), AUD-7-120 (lecture d'un connecteur 1.0), AUD-7-219 (défaut `aids: false` de `show-schema`). Établi par la session principale en phase 8 et seulement cité ici : supprimer le schéma `VU-Skizze` fait échouer l'export (`validation.py:458` « has no fastener ») et supprimer le point A12 aussi (`validation.py:416` « n_tot is 4 and the drawing has 3 »). Mes sondes le confirment pour la connexion et l'étendent aux cas « aucune fixation cochée » et « schéma vide de source » (`t_connection.py` : `no-fastener-ticked`, `schema-renamed`, `no-schema`, `all-markers-missing` → STOP `has no fastener`) : même cause, non numéroté.

## Contrôles menés

46 contrôles de comportement (lecture du code + exécution dans le bac à sable) : 25 conformes, 17 constats A, 2 constats B, 2 constats C, 0 NON FAIT bloquant (voir fin).

Conformes (extrait, preuve entre parenthèses) :

- §3.3quinquies : source 4.0, `connector`/`variant` refusés, 3.0/3.1 lus comme 4.0 sans écriture, 1.0/2.0/2.1 renvoyés à `migrate_to_schemas.py` (`connection.check_source`) ; id = nom de fichier ; 2 à 6 membres ; centre `centroid`/`manual`/`aid` avec repli sur le centroïde et avertissement (`t_connection.py` : `centre-aid-missing`, `aid-not-point-shaped`) ; niveaux des vars (n, I_p niveau 2, le reste 3) ; tableau « Lage der Verbindungsmittel » niveau 3, totaux I_px/I_pz ; ordre d'impression niveaux 1/2/3 de `show-polar-moment` (lecture `calc-engine.typ:2203-2393`, PDF `p7c/typ/pm-base-l3.pdf`) ; décomposition de N/V seulement hors quart de tour ; `β_r = arctan` seulement si `axis` du membre de référence = 0 ; égalités à 1e-9·max(1, F) des deux côtés (Python `connection.py:397`, Typst `:2169`) ; gardes (id inconnu, niveau, force, unité, M sur I_p = 0) ; arc M de sud-ouest à sud-est (`MOMENT_SPAN = (135, 45)`), `ACTION_WIDTH`/`RESULTANT_WIDTH` 1,6/2,4 des deux côtés ; marqueurs `<!-- forces -->` et `<!-- note -->`.
- §3.3sexies : refus bloquants de `plan.check_source` (type, points, recadrage, fond hors projet, page, T/A à deux points), avertissements (numéro inconnu, lettre, hors cadre, numéro déplacé hors cadre) sans avertissement pour un numéro partagé ; `auto_label` dans l'ordre décrit ; enregistrement (sheet, crop, scale, style, unit, `label_at`, `length_m`, légende en lignes) ; unité = plus grand côté / 850 ; voile blanc = 1 − opacité ; `show-plan` : halo, détail 1,5 m (ou 1/10), même échelle, `zoom`, `axes: false`, barre d'échelle ≥ 25 mm sous le plan, légende 8 pt ≤ 3 colonnes ≥ 11 cm, légende 1.0 en SVG ; `calc-block(plan: auto)` en détail sans légende ni barre.
- §3.3septies : `ENGINE = "norm"`, `SHEET_PREFIX = None`, vars et niveaux du tableau, E sans valeurs avec `hinweis`, Tabelle 8 niveau 3 au-dessus avec `highlight`, contrôles de `sia261.py` ; `show-live-load("E")` refuse avec la phrase de la norme, `show-calc("live-load", "E", level: 3)` compile, `show-live-load("A1", level: 1)` et `level: 3` impriment ce que dit la table (`t_typst.py` : `ll-*`).
- §3.3octies : ids uniques sans casse, un appui par point, ressort = membre en kN/m, raideur de rotule seulement en moment, angle refusé sur `vertical`/`horizontal`, `along` exige un membre de référence, cotations refusées (même point, angle d'un membre avec lui-même, membres parallèles), largeur du modèle ignorée sur un kN, étiquettes empilées par membre et par sens, étiquette hors bande si trop peu profonde, charge sans valeur à pleine longueur, valeur illisible grise et courte, note « Vergrössert », halo rectangle blanc (v0.77), `FONT = "Arial"`, régions `<!-- loads -->`/`<!-- dims -->` indépendantes, figure normalisée à 1000 unités.
- §3.3nonies : deux formes de `material`, `position` refusé ; classe d'humidité unique, la pire si nulle ; refus 6.1.1.11 des assemblages non couverts (`uncovered-assembly` STOP) ; module absent, classe non bois (S355), feuillu non prépercé → `calculated: false` + raison + avertissement ; `R_d_Verb_Fachwerk` en second résultat (`truss`) ; quatre tableaux avec niveaux et côtés annoncés ; Figur 45 portée par le tableau k_β ; `show-connector-resistance` niveau 1 (Tabelle 24), 2 (figures + avertissements), 3 (`show-calc`), refus avec la raison (`cn-uncalculated`) ; `checks` vide imposé.
- §3.3decies : dossier `details/`, 1.0 lu comme 1.1, `width` refusé en 1.1, `b`/`h` suivis ou écrits par-dessus, `parse_section`, légende « T001 C24 100/200 » au milieu libre, `shown` par défaut, `editing`, lignes de construction découpées au cadre (`clip_line`), points verts par-dessus, croisements à 1e-6 mm, `fastener_places` et `default_fasteners`, verbes de modification (identité de quatre quarts de tour, doublon sans cotation, découpe qui garde le numéro, fusion refusée entre positions), trois fichiers de langue identiques.

## Constats

### AUD-7-301 | B | `calc/domains/connection.py:563-584` ; `lib/calc-engine.typ:2108-2395` ; CLAUDE.md:465 (§3.3quinquies), 748 (§3.3decies)

Une connexion dont le schéma a perdu un repère (ou un point « connecteur ») ou un élément est exportée avec un simple avertissement, puis **imprimée sans refus** sur les fixations restantes (angles 0° pour l'élément perdu), alors que CLAUDE.md dit deux fois « the report refuses to print what it names ». Le record de `data/connections.json` ne porte ni `missing` ni `calculated`, et `show-polar-moment`/`find-calculation` n'ont donc aucun moyen de refuser. (Le cas où plus rien ne reste arrête l'export : phase 8.)

Preuve : `t_typst.py`, fixations `["A12","A13","A14","ZZ9"]` → avertissement « no longer carries the marker(s) or point(s) ZZ9 », compilation `#show-polar-moment("VU-MP-1", N: 5, V: 10, M: 2, level: 2)` exit 0, PDF `pm-marker-missing-l2.pdf` : « 𝑛 = 3 », « 𝐼𝑝 = 19200 mm² », F₁ = 11.932 kN (contre n = 4, I_p = 28 800 mm² sur la source intacte). Côté connecteur, la même perte arrête l'export (phase 8) : les deux modules d'un même schéma se comportent à l'opposé.

Options : (a) exporter `missing` (repères, éléments, centre) sur le record (`connections` 4.1, additif) et faire refuser `show-polar-moment` et `find-calculation` quand `missing.markers` ou `missing.elements` n'est pas vide, comme `show-connector-resistance` refuse un connecteur non calculé ; (b) garder l'impression et écrire la vérité. Pour (b), remplacements exacts :
- CLAUDE.md:465 : `each is a warning naming what to do, the report refuses to print what it names, and the Katalog stays able to open the file and point it somewhere else` → `each is a warning naming what to do; the report prints the calculation on what the schema still carries -- the fasteners it lost left out, a lost element's angles taken as 0°, a lost centre replaced by the centroid -- and the Katalog stays able to open the file and point it somewhere else`
- CLAUDE.md:748 : `each is a warning naming what to do, the report refuses to print what it names, and the Katalog stays able to open the file and point it somewhere else.` → `each is a warning naming what to do, and the Katalog stays able to open the file and point it somewhere else. A connector the schema no longer gives a pattern is exported with `calculated: false` and the report refuses to print its resistance; a polar moment is printed on what remains.`

Test : `tests/test_schema_consumers.py` — passer une connexion à repère perdu par `connection.prepare` puis compiler `show-polar-moment` ; attendre le refus (option a) ou n = 3 et l'avertissement (option b).

### AUD-7-302 | A | `calc/domains/connection.py:499`, `:541`

Un centre `aid` que le schéma a perdu est remplacé par le centroïde (avertissement correct), mais le niveau 3 imprime « Drehpunkt (festgelegt): x_c = 0 mm; z_c = 0 mm » au lieu de la formule du centroïde, et le record garde `center.mode = "aid"`. CLAUDE.md §3.3quinquies : « one the schema no longer carries falls back to the centroid with a warning » ; le rapport dit l'inverse de ce qui a été calculé.

Preuve : `t_typst.py`, `center = {"mode": "aid", "aid": "NOPE"}` → PDF `pm-aid-missing-l3.pdf` « Drehpunkt (festgelegt): 𝑥𝑐 = 0 mm; 𝑧𝑐 = 0 mm » ; source intacte `pm-base-l3.pdf` « Drehpunkt (Schwerpunkt der Verbindungsmittel): 𝑥𝑐 = ∑𝑥𝑖/𝑛 = … ».

Correction (code) :
- `connection.py:499` `    manual = source["center"]["mode"] in ("manual", "aid")` → `    mode = "centroid" if geometry["missing"]["centre"] else source["center"]["mode"]` puis `    manual = mode in ("manual", "aid")`
- `connection.py:541` `        "center": {"mode": source["center"]["mode"], "x": xc, "z": zc},` → `        "center": {"mode": mode, "x": xc, "z": zc},`

Aucun nombre ne change (le centroïde était déjà utilisé). Test : `test_schema_consumers.test_a_centre_the_schema_lost_falls_back_to_the_centroid_and_says_so` — ajouter `connection.build_record(source, _detail())["center"]["mode"] == "centroid"` et `vars["x_c"]["group_label"]` commençant par « Drehpunkt (Schwerpunkt ».

### AUD-7-303 | A | CLAUDE.md:471 (§3.3quinquies), 2039 (§13 v0.74)

Le libellé d'un membre sur la figure est décrit comme `T001` ; depuis v0.75 il est « T001 C24 100/200 » (§3.3decies, §13 v0.75). Preuve : texte de `pm-base-l3.pdf` : « T001 C24 100/200 », « S001 C24 100/200 » ; `schema.element_caption`.

Remplacements :
- `⚠️ A member's label is therefore the **schema's** — `T001`, where until v0.73 it read `T001 100/**400**` with the drawn dimension bold, a schema element carrying the width it is drawn at and not the other dimension (§14).` → `⚠️ A member's label is therefore the **schema's** — «T001 C24 100/200», the position, its strength class and the element's own section (v0.75); in v0.74 it read `T001` alone, and until v0.73 `T001 100/**400**` with the drawn dimension bold.`
- §13 : `The section is still in the report's own text and the drawing is at its real size, so nothing is unmeasurable, but the figure alone no longer shows it (§14).` → `The section is still in the report's own text and the drawing is at its real size, so nothing is unmeasurable, but the figure alone no longer showed it -- until v0.75, whose label «T001 C24 100/200» gave it back (§13 v0.75).`
### AUD-7-304 | A | CLAUDE.md:469, 461 (§3.3quinquies)

« its direction on the drawing (`page`) » : aucun champ `page` n'existe (record des membres : `name`, `element`, `position`, `local`, `axis` ; `connections.schema.json:114-133`). « the drawing's orientation » : `orientation` a disparu en v0.74 (même section).

Remplacements :
- `It also gives every member's angle from the reference member's grain (θ_(r,j), its `local` angle) and its direction on the drawing (`page`).` → `It also gives every member's angle from the reference member's grain (θ_(r,j), its `local` angle) and from the schema's x (its `axis` angle).`
- `Every angle — the directions of N and V, a member's angle from member 1, the drawing's orientation — is counted from x towards z` → `Every angle — the directions of N and V, a member's `local` and `axis` angles — is counted from x towards z`

Test : un test de doc refusant `` `page` `` et `orientation` au présent dans §3.3quinquies (ou la vérification mécanique de p7a sur les clés de record).

### AUD-7-305 | A | CLAUDE.md:471 (§3.3quinquies) ; `calc/domains/connection_svg.py:455-476`

« it is drawn under the members' labels, each of which carries a halo of its own band so that it is read over the arc (v0.50) » : depuis v0.74 les libellés viennent de `schema_svg.body()` (halo **blanc**), appelé **avant** l'arc ; l'arc est donc dessiné **par-dessus** les libellés. Preuve : `data/connections/VU-MP-1-de.svg`, libellés « T001 C24 100/200 » lignes 4-7, `<polyline>` de l'arc ligne 20.

Remplacement (doc, aucun effet sur un nombre) : `it is drawn under the members' labels, each of which carries a halo of its own band so that it is read over the arc (v0.50);` → `it is drawn over the schema's drawing, the members' labels included, and under the fasteners;`. Alternative de code si l'ordre de v0.50 est voulu : redessiner les libellés des éléments après l'arc dans `overlay`. Test : dans `test_arrows.py` ou `test_schema_consumers.py`, position de l'arc par rapport au premier `<text>` de libellé dans le SVG exporté.

### AUD-7-306 | A | CLAUDE.md:486 (§3.3quinquies) ; `lib/calc-engine.typ:2390-2391`

« and the largest F* is bold » : le code met en gras toute la colonne F* (`bold-columns: (3,)`) et les lignes du maximum (`bold-rows`), comme le premier tableau. Remplacement : `Its formulas stand in letters above it, and the largest F* is bold.` → `Its formulas stand in letters above it; the F* column is bold, and so are the rows carrying the largest F*.`

### AUD-7-307 | A | CLAUDE.md:673, 675 (§3.3nonies)

Un motif sous les distances de Tabelle 24 **calcule** (`calculated: true`, R_d imprimé) avec un avertissement, contrairement à « Each of these sets `calculated: false` » ; et depuis v0.77 (colonnes « vorhanden »/« Nachweis » retirées) le rapport n'imprime aucun ✘ : l'avertissement apparaît en texte orangé sous le calcul à partir du niveau 2 seulement. Preuve : `t_connector.py` `spacing-below-tab24` (d = 30) → `calculated=True`, R_d = 16.16, avertissement « Mindestabstand in Faserrichtung unterschritten » ; `t_typst.py` `cn-spacing-l1` : « Mindestabstand » absent, « ✘ » absent ; `cn-spacing-l2` : « Mindestabstand » présent, « ✘ » absent.

Remplacements :
- `It is said loudly, printed in the report with a ✘ against the row, and left to the engineer: the fix is a layout to move, not data to correct.` → `It is said loudly -- the resistance is still calculated, and the warning is printed under it from level 2 -- and left to the engineer: the fix is a layout to move, not data to correct.`
- `Each of these sets `calculated: false` with a `reason`, and `show-connector-resistance` refuses to print a resistance nobody produced, saying that reason instead.` → `Each of the first three sets `calculated: false` with a `reason`, and `show-connector-resistance` refuses to print a resistance nobody produced, saying that reason instead; the fourth leaves the resistance calculated and carries its warning.`

Test : `tests/test_connectors.py` — motif sous Tabelle 24 : `calculated` vrai, avertissement dans `record["warnings"]`.

### AUD-7-308 | A | CLAUDE.md:685 (§3.3nonies) ; `calc/domains/connector.py:78` ; `calc/domains/connector_svg.py:328`

Le motif est dessiné par langue « its frame being sized from its words » ; or `pattern_of` appelle `overlay(legend=False)` : aucune phrase du moteur, les libellés des pièces sont des données. Seule la note « Vergrössert … Ø d » (plancher de lisibilité atteint) est un mot, et elle ne change que la hauteur. Preuve : `md5sum data/connectors/VU-SD-10-pattern-{de,fr,en}.svg` → trois empreintes identiques `c980e078…`.

Remplacements :
- CLAUDE.md : `It is drawn once per language, its frame being sized from its words (§4bis).` → `It is drawn once per language all the same (§4bis): it carries no word of the engine's but the note under it where a fastener is drawn larger than its d, so its three files are identical otherwise -- as a schema's are (§3.3decies).`
- `connector.py:78` : `The **pattern** carries words -- the member labels and the legend of connection_svg -- so it is drawn once per language, as a connection's figure is (CLAUDE.md section 4bis).` → `The **pattern** carries no legend, only data and, where a fastener is drawn larger than its d, one translated note; it is drawn once per language all the same, as a connection's figure is (CLAUDE.md section 4bis).`
- `connector_svg.py:328` : `Drawn once per language, as a connection's figure is: its frame is sized from the words in it (CLAUDE.md section 4bis).` → `Drawn once per language, as a connection's figure is; with no legend, only the note under it differs between languages (CLAUDE.md section 4bis).`

### AUD-7-309 | A | `calc/domains/schema_svg.py:313`, `:497-505` ; `connection_svg.py:161` ; `connector_svg.py:336` ; CLAUDE.md:720 (§3.3decies)

CLAUDE.md : « A connection's and a connector's own figures keep their frame, which their arrows and legend need. » Faux : `schema_svg.layout` remplace le cadre par `crop` dès que `editing` est faux, et les deux figures consommatrices l'appellent ainsi. Un recadrage serré coupe les fixations du motif. Aucun schéma du projet n'a de `crop` aujourd'hui : aucune figure imprimée n'est touchée.

Preuve : `t_crop.py` sur `VU-Skizze` : sans crop, viewBox connexion `-336 -356.6 672 792.6`, motif `-336 -136 672 572` ; avec `crop = {x: -30, z: -30, w: 60, h: 60}`, connexion `-303 -356.6 526.85 580.46`, motif `-48 -48 96 96` alors que les fixations sont à ±60 mm (hors cadre).

Correction (code, intention écrite dans CLAUDE.md) :
- `schema_svg.py:313` `def layout(source, lang=strings.SOURCE_LANGUAGE, positions=None, editing=False):` → `def layout(source, lang=strings.SOURCE_LANGUAGE, positions=None, editing=False, use_crop=True):`
- `schema_svg.py:498` `    if isinstance(crop, dict) and not editing:` → `    if isinstance(crop, dict) and use_crop and not editing:`
- `connection_svg.py:161` `    base = schema_svg.layout(detail or EMPTY_SCHEMA, positions=positions)` → `    base = schema_svg.layout(detail or EMPTY_SCHEMA, positions=positions, use_crop=False)`
- `connector_svg.py:336` `    drawing = schema_svg.layout(detail, lang=lang, positions=positions)` → `    drawing = schema_svg.layout(detail, lang=lang, positions=positions, use_crop=False)`

Test : `tests/test_schema_section.py` (la partie « crop ») — un schéma recadré donne à `connection_svg.render` et à `connector_svg.pattern_of` le même `viewBox` que sans recadrage.

### AUD-7-310 | B | `calc/domains/schema_svg.py:313-462`, `:650-717` ; `schema.py:194-215` ; CLAUDE.md:730 (§3.3decies)

CLAUDE.md : « a piece's, a marker's, an aid's and a dimension's value may each be **dragged clear** of what it names … and a thin leader runs back to that place once it has left it ». Le code : (1) une aide accepte `label` et `label_offset` (`_check_aid`) mais aucun libellé d'aide n'est ni placé ni dessiné (`label_frames` ne contient que éléments, repères, cotations ; donc pas non plus de saisie dans le Katalog) ; (2) seul le libellé d'un **élément** reçoit un trait de rappel (`body` n'appelle `_leader` que pour les éléments) ; un repère ou une cotation déplacés n'en ont pas.

Preuve : `t_schema_labels.py` — cadres `[('elements','E1',moved,leader), ('connectors','C1',moved,None), ('dimensions','D1',moved,None)]` ; « Punkt A » et « Zentrum » absents du SVG ; une seule ligne de rappel (largeur 0,12·font) pour trois libellés déplacés.

Options : (a) compléter le code : cadres de libellé pour les aides ponctuelles qui en portent un, et `_leader` pour repères et cotations (règle `moved`) ; (b) réduire la doc et refuser un `label`/`label_offset` sur une aide. Pour (b) : `a piece's, a marker's, an aid's and a dimension's value may each be **dragged clear** of what it names, its `label_offset` saved from its own place so it follows its element, and a thin leader runs back to that place once it has left it (the v0.42 rule, §3.3sexies).` → `a piece's, a marker's and a dimension's value may each be **dragged clear** of what it names, its `label_offset` saved from its own place so it follows its element; a piece's label grows a thin leader back to that place once it has left it (the v0.42 rule, §3.3sexies), a marker's and a dimension's do not, and an aid carries no label on the figure.` Test : `test_schema.py` — libellé de repère et de cotation déplacés → rappel (a) ou absence documentée (b) ; `label` d'aide dessiné (a) ou refusé (b).

### AUD-7-311 | A | `calc/domains/schema.py:1745` ; `schemas/schemas.schema.json:39`

Le record exporté d'un schéma porte `"source": "schemas/<id>.json"`, fichier inexistant : la source est `details/<id>.json` — précisément la confusion que §3.3decies et §13 (« The source folder is `details/` ») écartent. Preuve : `data/schemas.json` → `SD_01 schemas/SD_01.json`, `VU-Skizze schemas/VU-Skizze.json` ; contrat : `"schemas/<id>.json, the source it was exported from."`.

Corrections : `        "source": f"schemas/{sid}.json",` → `        "source": f"details/{sid}.json",` ; `"description": "schemas/<id>.json, the source it was exported from."` → `"description": "details/<id>.json, the source it was exported from."`. Réexport : seul `data/schemas.json` change. Test : `test_schema.py` — `(ROOT / record["source"]).is_file()` pour chaque schéma exporté, et même contrôle pour `connections.json`, `connectors.json`, `plans.json`, `statics.json`.

### AUD-7-312 | A | CLAUDE.md:603 (§3.3octies) ; `calc/domains/statics_svg.py:884-892`, `:1273-1318`

« A node with no articulation keeps its dot. » : depuis v0.56 le rapport ne dessine **aucun** point de nœud (`render(..., nodes=False)` par défaut, `nodes=True` seulement pour le Katalog et les icônes), et un appui encastré ou à rotule partagée masque aussi le point dans l'éditeur. Preuve : lecture ; CHANGELOG v0.56 « `render(..., nodes: True)`, passed by the Katalog and by its tool icons and by nothing else ».

Remplacement : `**A node carrying an articulation is not drawn** (v0.51, second review): the articulation's own symbol stands on that node and is the mark there, and a dot under it only thickened the symbol. A node with no articulation keeps its dot.` → `**A node is never drawn in the report** (v0.56): a dot there would claim an articulation, and what the report draws at a node it draws as the thing itself -- a hinge's circle, a release's mark, a wall's hatching. The Katalog alone marks the nodes one may click, and not where a release, a fixed support or a shared pin already stands (v0.51, second review; v0.56).`

### AUD-7-313 | A | CLAUDE.md:577 (§3.3octies, tableau des collections)

La ligne `supports` omet `hinge` (`shared`/`through`, v0.56), champ de la source que `statics.check_source` contrôle (`statics.py:397-402`) et que `statics_svg` dessine. Remplacement : `` | `supports` | `id`, the `point` it holds, `type` (`fixed` Einspannung, `pinned` Festlager, `roller` Loslager) and an `angle`, 0 putting the ground below. **At most one support per point** | `` → `` | `supports` | `id`, the `point` it holds, `type` (`fixed` Einspannung, `pinned` Festlager, `roller` Loslager), an `angle`, 0 putting the ground below, and for a Festlager or a Loslager its `hinge`, `shared` (the pin on the node, the default) or `through` (a bar running over the support, the pin set back under it); a `hinge` on an Einspannung is refused. **At most one support per point** | ``

### AUD-7-314 | A | CLAUDE.md:597 (§3.3octies)

« A unit that is neither per metre nor per square metre has no width to be multiplied by and stops the export naming the load. » : vrai pour une valeur **saisie** (`_check_width`, refus), faux pour une valeur **référencée** : `resolve` met la valeur à `None`, l'export avertit et la figure écrit `?` (`statics.py:292`, `:1275-1286`). Remplacement : `A unit that is neither per metre nor per square metre has no width to be multiplied by and stops the export naming the load.` → `A unit that is neither per metre nor per square metre has no width to be multiplied by: a value typed on the load stops the export naming it, while a variable of the export that turns out to be one is a warning, the figure writing `?` for it (the var may simply have changed since).`

### AUD-7-315 | A | CLAUDE.md:710 (§3.3decies, tableau des collections)

« taken as they stand … with the same anchors » : les ancres diffèrent. Une extrémité linéaire nomme une **aide ponctuelle** (`{"point": <aid id>}`) ou un lieu ; une extrémité d'angle nomme un **élément linéaire** ou une **ligne de construction** (`{"element": …}`/`{"aid": …}`), jamais un « member » (`schema._check_anchor`, `schema.py:218-246`). Remplacement : `with the same anchors, the same `offset` measured from the middle of the two ends` → `with a schema's own anchors -- a length between two point-shaped aids (`{"point": id}`) or places of their own, an angle between two linear elements or construction lines (`{"element": id}`, `{"aid": id}`) -- the same `offset` measured from the middle of the two ends`

### AUD-7-316 | A | CLAUDE.md:2210 (§14, schémas)

Point « encore ouvert » réalisé en v0.77 : `schema_svg.clip_line` découpe une ligne de construction montrée au cadre (§3.3decies le dit). Remplacement : `; a construction line is drawn to a generous reach rather than clipped exactly to the frame;` → `; (a construction line is clipped exactly to the frame since v0.77);`

### AUD-7-317 | A | CLAUDE.md:2187 (§14, « The Typst-Katalog's reserved tab »)

La moitié du point décrit comme non décidé est réalisée depuis v0.68 : la résistance est calculée en Python dans l'onglet *Connecteurs* (SIA 265 6.2.1), la source est `connectors/<id>.json`, f_u,k vient de SN EN 14592, `data_steel`/`data_assembly` sont retirés, et le calcul est adressé par l'id du **connecteur** (pas de la connexion, qui n'en nomme plus depuis v0.76). AUD-6-21 ne traite que la sous-phrase `data_steel's f_u,k`. Remplacement : de `The *Connecteurs* tab is the natural home of the next calculation on a connection` jusqu'à `A tab is filled by replacing its `FutureTab` entry in `TABS`.` → `The fasteners' resistance was settled in v0.68: it is calculated in Python in the *Connecteurs* tab from SIA 265 6.2.1, addressed by the connector's id, for the Stabdübel alone (the other kinds are the item above). A tab is filled by replacing its `FutureTab` entry in `TABS`.`

### AUD-7-318 | A | CLAUDE.md:2059 (§13 v0.70), 2068 (§13 v0.68)

Deux décisions décrivent des formes de `material` refusées depuis schéma 2.0 (v0.74) : `{"position": "T001"}` et `{"grade": …, "moisture_class": …}` (v0.68), `{"position": "T001", "grade": "GL32h"}` (v0.70). L'intention tient (référence relue à chaque export, dérogation qui reste), mais la position est désormais celle de l'**élément** du schéma. Preuve : `t_connector.py` `material-names-position` → STOP « material names a position -- since schema 2.0 the member's element does » ; classe d'humidité par membre refusée depuis 1.1 (`connector.py:245-246`). (AUD-6-5 ne couvre que la docstring de `connector.py`.)

Remplacements (ajout d'une incise, décisions inchangées) :
- `` `{"position": "T001"}` reads that element's strength class and moisture class at every export; `{"grade": …, "moisture_class": …}` states them in the file (§3.3nonies). `` → `` `{"position": "T001"}` reads that element's strength class and moisture class at every export; `{"grade": …, "moisture_class": …}` states them in the file (§3.3nonies). ⚠️ The shapes changed since, the decision did not: the moisture class became the connection's in schema 1.1, and in schema 2.0 (v0.74) the position is the one the member's schema element names, `material` being `null` (follow) or `{"grade": …}` (override). ``
- `` `{"position": "T001", "grade": "GL32h"}` is a third shape beside «follow» and «stated here»: `` → `` `{"position": "T001", "grade": "GL32h"}` was a third shape beside «follow» and «stated here» -- since schema 2.0 (v0.74) the position is the element's and the override is `{"grade": "GL32h"}` alone: ``

### AUD-7-319 | A | commentaires de code des §3.3quinquies-decies (non couverts par p6)

Remplacements exacts :
1. `calc/domains/connector.py:34` `# The file data/connectors.json is written to -- connection.py reads the same name to check that a connection's connector exists.` → `# The file data/connectors.json is written to.`
2. `calc/domains/connector.py:37` ` A polar-moment calculation of it is named <id>-<variant>, which is why the same pattern serves.` → supprimer cette phrase (une connexion ne nomme plus de connecteur, v0.76).
3. `calc/validation.py:408` `        # always names at least one marker -- check_source refuses none -- but the coordinates are the` → `        # may name no marker at all -- check_source allows it since schema 2.0 -- and the coordinates are the`
4. `(CLAUDE.md section 3.3quinquies; plan 3 of je-souhaite-commencer-generic-valley.md)` → `(CLAUDE.md section 3.3decies)` dans `calc/domains/schema.py:1`, `calc/domains/schema_svg.py:1`, `calc/validation.py:642`, `lib/calc-engine.typ:1101`, `calc/export_all.py:30`, `calc/tools/build_reference.py:448`, `calc/tools/schema_canvas.py:1`, `calc/tools/schema_tab.py:1`, `tests/test_schema.py:1` (même chaîne partout ; `examples/lib/` est la copie régénérée).
5. `lib/calc-engine.typ:1102` `*Connecteurs* and *Moments polaires* will name a schema instead of carrying their own geometry (plan 5) -- this block is the display layer that already reads it, on its own, exactly as show-static-model reads a static model on its own.` → `*Connecteurs* and *Moments polaires* name a schema since v0.74 instead of carrying their own geometry; this block prints one on its own, exactly as show-static-model prints a static model.`
6. `lib/calc-engine.typ:1944` `// The frame is the reference member's (section 3.3quinquies): x along its grain, z a quarter clockwise from it on the drawing, down when x points right;` → `// The frame is the detail schema's (section 3.3quinquies): millimetres, x to the right, z down;`
7. `calc/domains/plan.py:7` `A label that is not there is a warning, never an error -- a plan may be drawn before its positions are entered -- and nothing here writes to the workbook.` → `A label that is not there is a warning at export, never an error -- a position renamed or removed in Excel since it was drawn; the Katalog draws only the sheet's positions and refuses to save another (v0.45) -- and nothing here writes to the workbook.`
8. `calc/domains/statics_svg.py:5` `and a text's white halo is the text drawn twice.` → `and a label's white halo is a rectangle, its own box turned with its text (v0.77).`

Test : étendre le test « aucun nom retiré n'est vivant » proposé par p6 à `je-souhaite-commencer`, `3.3quinquies; plan 3` et `<id>-<variant>`.

### AUD-7-320 | C | CLAUDE.md:668-675 (§3.3nonies, « What warns, and what stops »)

La liste « Four things only warn » est incomplète : l'export avertit aussi pour d hors 6-30 mm (`dowel.py:334-338`, SIA 265 6.2.1.1), pour les conditions de (130)/(131), pour `n_tot` écrit à la main, pour des classes d'humidité différentes et pour un id qui ne commence pas par le symbole du type ; et deux états posent `calculated: false` **sans** avertissement (aucune fixation cochée, aucune classe d'humidité : `connector.py:682-702`). Information ; à reprendre si le paragraphe est réécrit avec AUD-7-307.

### AUD-7-321 | C | `lib/calc-engine.typ:866`, `:931` ; CLAUDE.md §3.3sexies

`show-plan` ne met jamais la légende sous un détail (`legend and not detail`) ; la docstring le dit, §3.3sexies non (« under them the scale bar and the legend »). Information.

## Point 3 — §13 et §14 touchant ces sections

Décisions vérifiées conformes au code : polar moment sans connecteur (v0.76) ; id de moment polaire issu du nom (v0.76) ; b/h suivis et écrits par-dessus, bande = côté vu, `width` refusé (v0.75) ; libellé « position classe section » sur le milieu libre (v0.75 ; nuance : à égalité de longueur, le plus proche du milieu de la pièce l'emporte avant « le plus tardif », `schema_svg.py:303`) ; un schéma par calcul, deux angles `local`/`axis` (v0.74) ; sources à dessin propre refusées (connexion ; connecteur 1.0 : AUD-7-120) ; découpe qui garde le numéro, fusion limitée à une position (v0.73) ; `details/` (v0.72, mais AUD-7-311) ; point nommé = aide ; schéma à taille réelle ; ligne de construction non exportée par défaut ; deux constructions de rectangle (`rectangle_from_edge`) ; classe d'humidité unique (v0.70) ; `plates.thickness` refusé ; connecteur hors Excel, un fichier par calcul ; k_β de l'Anhang A et refus 6.1.1.11 ; calcul refusé qui n'arrête pas l'export (v0.68) ; points « connecteur » repris par tout module, Figur 45 sans mots, valeurs normatives dans `calc/norms/`, lignes de construction découpées (v0.77) ; norme lue comme domaine `norm`, catégorie E refusée (v0.49) ; modèle statique en x/z, ressort = membre, dessin sans calcul, grandeur référencée, largeur d'influence, cotations (v0.51-v0.57) ; plan dessiné au Katalog, positions d'Excel seulement (export : avertissement), deux couches, halo par Typst (v0.34-v0.48).

Décision contredite : « An empty fastener list is a draft and not a defect » (v0.74) et la règle v0.33 citée au §3.3quinquies/§3.3decies — établi en phase 8 pour la connexion et le connecteur ; complément AUD-7-301 (perte partielle imprimée sans refus).

Points du §14 déjà réalisés : AUD-7-316, AUD-7-317 (et AUD-7-119/AUD-6-21 pour les chemins de normes). Points toujours ouverts vérifiés : épaisseur t d'un connecteur non lue de l'élément (`connector.resolve_member`) ; membres d'une connexion nommés un par un ; fusion d'aires seulement sur arête commune ; moment concentré, ressort d'appui, charge projetée sur barre inclinée, chaînes de cotes absents de `statics.py` ; nuances d'acier 263 transcrites mais Lochleibung de la tôle non construite.

Comportement nouveau non décrit tranchant une question : aucun hors AUD-7-313 (`hinge`, décrit au CHANGELOG v0.56 mais pas au §3.3octies).

## NON FAIT

- Rendu visuel (PNG) des figures sondées : le contrôle s'est fait sur le SVG et le texte PDF ; l'ordre de dessin (AUD-7-305) est établi par la position dans le SVG, pas par une image.
- Plans (§3.3sexies) : aucune sonde d'export avec un fond PDF modifié (hash, page, calques cachés) ; lecture du code seulement.
- Comportements du Katalog cités dans ces sections (enregistrement, refus d'un plan à numéro inconnu, sélection) : hors périmètre (phase 5).

## Vérifications manuelles proposées

1. Décider AUD-7-301 : une connexion à repère perdu doit-elle être refusée par le rapport, comme un connecteur non calculé ?
2. Décider AUD-7-310 : libellés d'aides et traits de rappel des repères/cotations, à implémenter ou à retirer de la doc.
3. Regarder `data/connections/VU-MP-1-de.svg` : l'arc de M passe-t-il sur un libellé de pièce, et est-ce acceptable (AUD-7-305) ?

## Contrôles qui pourraient devenir des tests

- Connexion à repère perdu passée par `prepare` puis `show-polar-moment` (AUD-7-301).
- Centre `aid` perdu : `center.mode == "centroid"` et libellé « Schwerpunkt » (AUD-7-302).
- Motif sous Tabelle 24 : `calculated` vrai et avertissement (AUD-7-307).
- Recadrage d'un schéma sans effet sur le `viewBox` du motif et de la figure de connexion (AUD-7-309).
- `source` de chaque record exporté désignant un fichier existant (AUD-7-311).
- Libellés déplacés de repère/cotation, libellé d'aide (AUD-7-310).
- Refus au présent de `page`, `orientation`, `3.3quinquies; plan 3`, `<id>-<variant>` dans la doc et les commentaires (AUD-7-304, AUD-7-319).
