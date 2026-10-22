# Fields that follow a variable

> What a field of the window that is linked to a variable of the export holds, how it is resolved, and what it may name. Written for issues #42 and #43 (spec `docs/requirements/completed/2026-10-11-variables-liees-champs-et-textes.md`, lots 1 to 3, 11.10.2026); the text a drawing prints a variable in is §3.3duovicies-bis.

## 3.3duovicies. A field that follows a variable (v0.117, issue #42)

**What it is.** A number the engineer types in a tab — a member check's N, a side of its section, a static model's point, a spring's stiffness, b_e — may instead **follow a variable of the export**: a load of `data/calculations.json`, a connection's, a connector's, a script's, or a domain of the «Formules» tab. The engineer's words: «pouvoir entrer des variables dans les champs qui nécessitent en fait de mettre des valeurs dans les onglets». The button beside the field (𝑥) brings the «Variables» tab forward in its choosing mode, every other module unavailable (the side navigation and Ctrl+1 … Ctrl+9 off), until a variable is chosen or the choice given up; the tab that asked comes back (`MainWindow.begin_variable_pick`, `calc/tools/linkable_spin.py`). In a project opened read-only the button is closed: a link is a change to the project's sources.

**The shape: beside the field, never in its place** (D-17, the engineer's choice of 11.10.2026). The number stays in the source where it always was, and is the **last value known**; the entry's `links` names, by the field's key, the variable it follows:

```json
"N": {"value": 18.75, "unit": "kN"},
"links": {"N": {"domain": "snow-load", "instance": "SL", "var": "F", "factor": 1.5}}
```

⚠️ *Retired by the spec 2026-10-21-commandes-typst-refonte (lot 19): `var-of` -- write #var(name, domain: (domain, instance)) to read a value of the export, get(name, "value") for its number. What follows describes it as it was.* `domain` and `instance` are the pair a call names an export's calculation by (`var-of("snow-load", "SL", "F")`, the «Variables» tab's `address`); a domain of the «Formules» tab carries `"origin": "formulas"` and its id as `instance`. `factor` and `offset` (1 and 0 when absent) make the value `factor × variable + offset`, the offset in the variable's own unit — what a static model's load magnitude has done since v0.79. A key is a field's path in the entry: `N`, `alpha`, `section.b`, `x`, `width`, `stiffness`. **Why beside**: every reader of a number — the validation, `member_check.compute`, the canvases, the figures — stays right without a substitution; what it costs is that the window and the export reconcile the number with its variable, which `calc/domains/links.py` does once.

A static model's load magnitude keeps the reference form it has had since v0.79, `{domain, instance, var, factor?, offset?, description?}`, to which `last` (its last value, `{value, unit}`) and `origin` are added: it named its variable in its place before any other field could follow one, and its files are not rewritten.

**Units** (REQ-003, REQ-004, D-15). While a field is linked, the «Variables» tab lists only numbers of the export or of a «Formules» domain whose unit has the field's dimension by `calc/units.py` — the algebra `lib/formula.typ` computes with, read from `lib/units.json` — and none of a document's registry (D-02: a link is resolved by Python, without a compile). The value is converted into the field's unit: 12 500 N fills a field in kN with 12.5. A field in ° takes only °; a field without a unit (β) takes only a variable without one, never one in rad, which `lib/units.json` holds dimensionless. A load's magnitude, which has no unit of its own, takes a force, a force per metre or per square metre, or a moment.

**Live, and never a stop** (D-03, D-06, D-14). The export resolves every link against the values it has just built — `variable_sources.export_values`: the loads, the connections, the connectors, the scripts, and the «Formules» domains computed against these loads in memory, never the last export on the disk —, so a field follows its variable from one export to the next. A variable that can no longer be read (gone, renamed, not a number, of another dimension) leaves the field's last value in place, and is a warning naming the file, the field and the variable (`link_stale`, `statics_unread`), never a stop. **The last value is written by the window**, when it saves (`member_check.stamp_version`, `statics.stamp_version`, `links.refresh`), and as a static model opens (`statics.refresh_links`), so the drawing on screen is the one the report will print; the export writes no source.

**Provenance** (REQ-012, rule 5). A record whose fields follow variables carries `links`, where each value came from: the variable, the factor and the offset, the variable's own value and unit, and `stale` where the last value was kept. `data/checks.json` keeps `N = {value, unit}` flat with the value resolved — `#show-check-member` and `member_check.compute` are unchanged — and carries `links` beside it; `data/statics.json`, `data/connectors.json`, `data/connections.json` and an instance of `data/calculations.json` carry `links` as a list of `{entry, field, …}`, `entry` being `self` for the source's own fields, an entry's id, or its place (`members[0]`, `layers[1]`).

**Versions** (ARCH-004, rules 8 to 10). Written only by a source that follows a variable, so one that follows none is saved and exported byte for byte as before:

| Contract | Without a link | With one |
|---|---|---|
| `member-check-source` | 1.0 | 1.1 (`links`) |
| `checks` (export) | 1.0 | 1.1 (`links` on a record) |
| `statics-source` | 1.1 (1.0 read) | 1.2 (`links` on the model, a point, a member, a release, a load; `last` and `origin` on a magnitude) |
| `statics` (export) | 1.1 | 1.2 (`links` on a model) |
| `connector-source` | 2.0 | 2.1 (`links` on the connector and on a member) |
| `connectors` (export) | 3.0 | 3.1 (`links` on a record) |
| `connection-source` | 4.0 | 4.1 (`links`; `trial` is additive and read at both) |
| `connections` (export) | 4.1 | 4.2 (`links` on a record) |
| `dead-load-source`, `snow-source`, `wind-source` | 1.0 | 1.1 (`links`; a build-up's layer carries its own) |
| `calculations` (export) | 1.5 (1.4 read) | 1.6 (`links` on an instance) |

A field the source does not hold takes no link: a spacing a single fastener has none of, a rotation centre not placed by hand, a roof dimension the roof shape does not read (`links.drop_unheld`, which the window runs as it drafts). A linked value is shown, and written as the last value, at the field's own precision (a height in whole metres shows 12.5 as 13); the export resolves it whole.

**What a consumer may name** (ARCH-005, D-11). One table, `links.allowed`, read both by the choice and by the export:

| Consumer | May follow | Resolved |
|---|---|---|
| A load (dead load, snow, wind) — `links.LOADS` | another load, a «Formules» domain — naming anything else is a defect of the file, refused | in `registry.build_calculations`, after the sheets and the sources that follow nothing, each source once every load it names is built; a «Formules» domain computed against the loads built so far, a source naming one built last; a circle stops the export, naming the chain («snow-load/SN-09 → wind-load/WI-09 → snow-load/SN-09») |
| A connector, a polar moment — `links.JOINTS` | a load, a script, a «Formules» domain — never a joint, a joint giving variables of its own; naming one is a defect of the file, refused | after the scripts and the «Formules» index, before the joints are built |
| A member check, a static model — `links.ANY` | anything of the export | once every variable of the export is built, the joints' included |

Since this version the export runs the scripts and computes the «Formules» index **before** the connectors and the polar moments. **A circle is refused as it is chosen** too: a load tab asks `registry.load_graph`, the links of every load source on the disk, whether the link it is given would close one (`links.find_cycle`), and says so in the status line («Refusé : ce lien fermerait une boucle de charges (…)») without taking it.

**Where the fields are.**
- *Vérifications de barres* (`member_check.LINKABLE`): N, V_z, V_y, M_y, M_z, α, the section's b, h and d — only where the check states its section; one that follows its position takes no variable, its button closed —, l, w, l_y, l_z, a, β_y, β_z, σ_m,crit. The strength class, the moisture class («Pour la classe humidité, on ne doit pas pouvoir lier une variable») and every other choice from a list take none.
- *Modèles statiques* (`statics.LINKABLE`): a point's x and z (the card «Coordonnées» of a selected point), a spring member's stiffness, a rotational release's stiffness, the influence width b_e of the model or of a load, and a load's magnitude — chosen through the «Variables» tab since this version, the three lists domain → case → variable it had being retired (UI-005).
- *Moyens d'assemblage* (`connector.LINKABLE`): the diameter, the dowel's f_u,k, and each timber member's α, t, a₁ — for a Stahl-Holz joint the steel half's b, which is its member's t, the slot and t₁/t₂. The kinds, the grades, the moisture class and the counts take none.
- *Moments polaires* (`connection.LINKABLE`): the rotation centre placed by hand (x, z), the two directions, and the **trial forces** N, V, M of «Calcul», which are data of the calculation since this version (D-12: `trial`, saved with it).
- Onglets de charges: *Poids propre et surcharge* — the chosen value and each layer's thickness, width, spacing and load, the layer carrying its own links —, *Neige* — h_0, C_t, the roof's length, width and slopes —, *Vent* — q_p0, b, d, h, z, c_d.
- *Schémas*, *Modèles statiques*, *Plan de positions*, *Plan de protection incendie*: a text of the Text tool prints variables, §3.3duovicies-bis.

## 3.3duovicies-bis. A text on a drawing, and the variables it prints (v0.117, issue #43)

**What it is.** The four drawing engines — the schemas, the static models, the position plans and the fire-protection plans — have one tool **Texte**: a click puts a text down, written in the right pane, moved and deleted as the rest of the drawing, sized by the drawing's `text` factor, which the text may state over it (`figure_style.ENTRY_KEYS`, `texts`). The engineer's words: «Pour tous les moteurs de dessin, on doit avoir un outil texte, et dans le menu à droite du texte, on peut insérer une variable». One module draws it, `calc/domains/figure_text.py`, and one pane edits it, `calc/tools/text_pane.py` (ARCH-003).

**The shape: a token text** (D-13, the engineer's choice). Beside the place each engine gives it — `x`, `z` in a static model (metres) and a schema (mm), one point `points: [[x, y]]` on a plan's or a fire plan's sheet, a fire plan's text carrying an id too (`X1`, the letter T being a door's) —:

```json
"text": "N = {1}",
"vars": {"1": {"domain": "snow-load", "instance": "SL", "var": "F", "show": "symbol",
               "last": {"value": 18.75, "unit": "kN", "symbol": "F"}}}
```

`{1}` is a token, where the variable `vars["1"]` is printed; a literal brace is typed twice, `{{`. A token naming no variable, and a brace standing alone, are defects of the file, which stop the export naming the file and the text (`figure_text.check`); the pane says so under the content and does not take it. A variable is a link (§3.3duovicies: `domain`, `instance`, `var`, `factor`, `offset`, `origin`) with two keys of its own: `show`, chosen per insertion (D-09) — «valeur», `18.75 kN`, or «symbole = valeur», `F = 18.75 kN` —, and `last`, its value, unit and symbol when the window last saved (D-14).

**What it prints.** Any number of the export or of a «Formules» domain may be inserted, whatever its unit (D-08): a text fills no field. The value is printed in the variable's own unit after its factor and offset, as a figure prints a number (at most three decimals, the real minus); the symbol as the window sets it, read once by `calc/typst_math.py` — `q_(k,"max")` is `q_(k,max)` on the figure and q<sub>k,max</sub> in the window. A variable that can no longer be read prints its `last`, with a warning (`text_stale`, D-06); one with no last value either prints `?`. What the engineer types is set by the one text engine of the figures, `calc/domains/svg_text.py` (D-19): an `_` makes a subscript, as in every label.

**Live.** The export resolves every text against the values it has just built (`variable_sources.export_values`): the schemas are therefore exported after the joints and the loads, their sources still read first for the connectors drawn on them. The window shows a text against the export on the disk, read as the drawing opens (`linkable_spin.current_values`), so it shows what the report will print. A text placed on a schema is also drawn in a connector's and a polar moment's figure of that schema, with its last values.

**Records and versions.** The record of a drawing carries `texts`, each with what it printed (`lines`) and, where it printed a variable, where that came from (`links`, REQ-012). Written only by a drawing that holds a text, so one without is saved, exported and drawn byte for byte as before:

| Contract | Without a text | With one |
|---|---|---|
| `statics-source` / `statics` | 1.1 / 1.1 | 1.2 / 1.2 (with the links of §3.3duovicies) |
| `schema-source` / `schemas` | 1.1 / 1.1 | 1.2 / 1.2 |
| `plan-source` / `plans` | 1.6 / 1.3 | 1.7 / 1.4 |
| `fire-source` / `fire` | 2.0 / 2.0 | 2.1 / 2.1 |

A text turns with its page (`plan.rotate_source`, `fire.rotate_source`), moves and is copied with «Déplacer» and «Copier» (a plan's, a fire plan's, a schema's), and is no entry of a fire plan's lists: it is in `fire.ENTRY_COLLECTIONS`, not in `fire.COLLECTIONS`, which the lists and the snapping read. No Typst command or argument is added: a text is printed in the SVG Typst already sets (ARCH-007).
