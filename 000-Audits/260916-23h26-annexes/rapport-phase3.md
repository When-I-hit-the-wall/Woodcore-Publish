# Audit 260916-2326 — Phase 3 : traductions du rapport Typst (fr, de, en)

Agent « p3 », bac à sable `AUDIT/projet-phase3/`, scripts et sorties dans `AUDIT/p3/` (s31…s39, pdf-*.txt, s37-probe-*.txt, PNG dans `AUDIT/projet-phase3/png/`). Commit audité `997570db`. `git status --short` de l'arbre réel : vide avant et après (vérifié en fin de phase). Aucune écriture dans le projet réel ; les sources de sonde (`AUD-SH-S`, `AUD-SH-A`, `AUD-HH-W`, `AUD-MP-2`) n'existent que dans le bac à sable, dont l'export a été relancé (24 s, code 0). Travail interrompu une fois par la limite de session de l'API, repris sans refaire les étapes acquises.

## Bilan

20 contrôles menés, 7 conformes, 18 constats : 8 de classe A, 5 de classe B, 5 de classe C. NON FAIT : aucun contrôle entier ; deux limites sont signalées dans les contrôles concernés (3.6 : pas de page vue pour les sections 6-7, qui ne contiennent que de la prose de l'ingénieur ; 3.1 point 4 : la source anglaise « predrilled » n'a pas pu être tranchée, EN 1995-1-1 ne donnant ni l'une ni l'autre graphie au texte extrait).

## Contrôles menés

| # | Contrôle | Méthode / preuve | Résultat |
|---|---|---|---|
| 1 | Chaque clé appelée existe (3.1) | `s31_glossary.py` : 51 appels `t-str`/`t`/`t-label`/`t-pattern`/`t-of` dans `lib/*.typ` et `Sections/`, 11 `strings.text()` dans `calc/` | conforme, 0 clé manquante |
| 2 | Clés `engine` utilisées (3.1) | littéral `"clé"` dans le code, clés de légende de plan dynamiques (`"plan.legend." + l.key`) | conforme : 15 clés de légende non utilisées par les plans du projet mais produites par `plan_svg` pour les symboles STE que ces plans n'emploient pas |
| 3 | Modèles `templates` utilisés (3.1) | code + chaînes de l'export correspondant au modèle | conforme : 4 modèles absents de l'export (`connector.mixed_moisture`, `n_tot_override`, `position_gone`, `position_no_grade`) mais composés par `connector.py` ; vérifié dynamiquement (sonde) qu'ils sont reconnus et traduits |
| 4 | Termes `terms` utilisés (3.1) | présence exacte dans `data/*.json` ou littéral du code | 24 termes introuvables : voir AUD-3-14 |
| 5 | Passages `$…$` identiques dans les trois langues (3.1) | 329 entrées comparées | conforme, 0 écart |
| 6 | Source de chaque terme (3.1) | bloc `_sources`, recherche dans les PDF de normes (`s38*.py`) | AUD-3-9, AUD-3-10, AUD-3-17 |
| 7 | Littéraux de `lib/*.typ` (3.2) | `s32_literals.py` : 282 littéraux candidats (hors `panic`/`assert`/commentaires) triés à la main | AUD-3-1, AUD-3-2 |
| 8 | Littéraux allemands des modules Python dessinant ou composant (3.2, étendu) | même script sur `calc/domains/*.py` | alimente AUD-3-3, 3-4, 3-7, 3-8 |
| 9 | Champs texte de l'export classés (3.3) | `s33_export.py` : 224 termes, 21 modèles, 44 valeurs de l'ingénieur, 15 signalés puis triés (tous valeurs de l'ingénieur ou libellés résolus ailleurs, sauf ci-dessous) | AUD-3-5, AUD-3-7 |
| 10 | Captures des modèles (3.3) | 21 correspondances ; une capture de mots du moteur (`connector.embedment_note`), une capture de mots de la norme (`snow.exposure_desc`) | AUD-3-6, AUD-3-7 |
| 11 | Chaînes allemandes du glossaire dans les PDF fr et en (3.4) | `s34_search.py` sur `phase1-pdf/{fr,en}-u3.pdf` : 324 aiguilles, 45 occurrences par langue, triées une à une (titres de `Sections/`, plans d'architecte, valeurs de l'ingénieur exclus) | AUD-3-1, AUD-3-7 |
| 12 | Fuite fr→en et en→fr (3.4) | 323 et 319 aiguilles | conforme, 0 occurrence |
| 13 | Lignes identiques entre PDF de et fr/en (3.4, filet) | `s34_same_lines.py` | AUD-3-13, confirme AUD-3-5 |
| 14 | Texte des SVG (3.5) | `s35_svg.py` sur les 29 SVG de `data/` | conforme sur le projet : légendes de `connections/*-fr|en.svg` traduites, figures de schémas et de modèles sans mot du moteur (seul « Moment », identique en fr/en) |
| 15 | Figures déclarées sans mots (3.5) | `*-section.svg`, `*-kbeta-*.svg` du projet : seulement `mm`, symboles, nombres | conforme sur le projet ; la sonde AUD-3-8 montre un chemin qui y écrit de l'allemand |
| 16 | Chemins non exercés par le projet (3.3 étendu) | `s36_dynamic.py` : 12 variantes de connecteur construites en mémoire (Stahl-Holz ×2, einschnittig, humidités mêlées, n_tot forcé, d = 20 et 40, position disparue, sans classe, sans élément, clou, séisme + treillis) passées par `strings.translate` (même algorithme que `tl-of`) | AUD-3-3, AUD-3-4, AUD-3-15 |
| 17 | Sonde Typst fr/en de ces chemins (3.4) | `s37_probe.py` : export du bac à sable, `p3probe/probe.typ` compilé en de/fr/en (sans avertissement), texte extrait | confirme AUD-3-3, 3-4, 3-7, 3-8 |
| 18 | Contrôle visuel (3.6) | PNG 70 ppi, `uniform=3` : pages 3, 7, 10, 16, 19, 20 en fr et en, plus la page 7 de la sonde fr ; 13 images regardées | aucun débordement (légende de la figure du moment polaire, tableaux, colonne de citation) ; confirme AUD-3-1, AUD-3-2, AUD-3-5, AUD-3-8 |
| 19 | Typographie française du glossaire | `s39_typo.py` | AUD-3-12 |
| 20 | Cohérence terminologique | `s39_typo.py`, `s38_norms.py` | AUD-3-10, AUD-3-11 |

## Constats

### AUD-3-1 | A | `lib/calc-engine.typ:704` | `show-connector` imprime le type et l'assemblage en allemand dans les rapports fr et en

Preuve : `phase1-pdf/fr-u3.pdf` p. 7 et p. 15 : « VU-SD-10: Stabdübel, Holz-Holz zweischnittig, Ø 10 mm, …, prépercé » (en : « …, predrilled »), alors que l'en-tête de `show-connector-resistance` sur la même page traduit : « 4 × Ø 10 mm Broche, C24, Bois – bois à double section ». Les deux chaînes sont des termes du glossaire (`terms["Stabdübel"]`, `terms["Holz-Holz zweischnittig"]`) ; `connector-summary` les pousse sans `tl-str` : `let parts = (c.type, c.assembly).filter(s => s != "").map(s => [#s])`. Vu aussi sur `png/fr-7.png` et `png/en-7.png`.

Correction : remplacer par `let parts = (c.type, c.assembly).filter(s => s != "").map(s => [#tl-str(s)])` (la fonction est appelée depuis `show-connector`, qui est un `context`, ligne 728). Test : compiler `#set-report-language("fr") #show-connector("VU-SD-10")` et vérifier que le texte extrait contient « Broche » et « Bois – bois à double section » et ne contient ni « Stabdübel » ni « zweischnittig ».

### AUD-3-2 | A | `lib/calc-engine.typ:2348` | Les points-virgules de la note sous « Kräfte in den Verbindungsmitteln » sont avalés par Typst, dans les trois langues

Preuve : `pdf-de.txt` l. 1236-1238 « 𝐹𝑥, 𝐹𝑧: Komponenten der Kraft je Verbindungsmittel in x und z 𝛽1 zu T001, 𝛽2 zu S001: Kraft-Faser-Winkel 𝐹 : Resultierende. » ; fr idem (`png/fr-20.png`). La note est écrite `…#t-str("connection.forces_note_head"); #range(…)…: #t-str("force_grain_angle"); $F$:…` : en mode balisage, un `;` qui suit immédiatement une expression `#…` la termine et n'est pas imprimé.

Correction : écrire `#t-str("connection.forces_note_head")\; ` et `#t-str("force_grain_angle")\; ` (point-virgule échappé), ou `[;]` concaténé. Test : compiler `show-polar-moment("VU-MP-1", N: 0, V: 5, M: 3, level: 3)` et vérifier « in x und z; » dans le texte extrait.

### AUD-3-3 | A | `calc/domains/dowel.py:669` (et `:272`) | Tableau k_β des assemblages acier-bois : lignes « Scherfuge A (2×) » jamais traduites, et « Scherfuge Scherfuge (2×) » pour les tôles extérieures, en allemand aussi

Preuve : sonde `s37-probe-fr.txt` p. 2 « Scherfuge A (2×) 20.571 … », « Scherfuge B (2×) 102.857 … » ; p. 5 (`Stahl-Holz, Bleche aussen`) « Scherfuge Scherfuge (2×) 50 0 0 49.905 1.414 1.414 ». `dowel.py:272` pose `"plane": "Scherfuge"` pour les tôles extérieures, puis `:669` compose `"Scherfuge %s (%d×)" % (plane["plane"], plane["count"])`. Aucun terme ni modèle ne reconnaît ces lignes (la cellule passe par `tl-str`, `calc-engine.typ:1426`).

Correction : dans `_k_beta_table`, composer `label = ("Scherfuge %s" % plane["plane"]) if plane["plane"] in ("A", "B") else "Scherfuge"` puis la cellule `"%s (%d×)" % (label, plane["count"])` ; ajouter à `strings.json` deux modèles : `"connector.plane_row"` de « Scherfuge {plane} ({count}×) », fr « Section cisaillée {plane} ({count}×) », en « Shear plane {plane} ({count}×) » (SIA 265:2021 FR tableau 46 p. 97, « section cisaillée A / B ») ; `"connector.plane_row_single"` de « Scherfuge ({count}×) », fr « Section cisaillée ({count}×) », en « Shear plane ({count}×) ». Test : `dowel.analyse` + `record` pour chaque assemblage acier-bois, puis `strings.translate(cellule, "fr")` ne contient plus « Scherfuge », et aucune cellule ne contient deux fois « Scherfuge ».

### AUD-3-4 | A | `calc/domains/dowel.py:297`, `:301`, `:337`, `:555` ; `calc/domains/connector.py:460` | Avertissements de connecteur sans modèle : imprimés en allemand dans les rapports fr et en (dès le niveau 2)

Preuve : sonde fr p. 3 « Tabelle 46, Gleichung (131) gilt nur wenn t_1 >= 0,35 · t_2; hier ist t_1 = 20.6 mm und 0,35 · t_2 = 36.0 mm. » ; p. 9 « Mindestabstand in Faserrichtung unterschritten: 120.0 mm vorhanden, 140 mm verlangt (SIA 265 Tabelle 24). Gleichung (88) gilt nur bei Einhaltung der Mindestabstände (6.2.1.1). » (juste sous « 𝑛tot est fixé à 6 à la main; le dessin en montre 4. », qui, lui, a son modèle). `s36_dynamic.py` : même résultat pour « SIA 265 6.2.1.1 gibt Gleichung (88) für Stabdübel mit d = 6 bis 30 mm an; hier ist d = 40 mm. » et « Bauteil 1 ist keinem Element mit Position zugeordnet… » (ce dernier rend le connecteur non calculé : seul le Katalog l'affiche).

Correction : ajouter dans `templates` (traductions libres, vocabulaire de SIA 265 FR : « espacement », « tableau », « équation », « broche ») :
- `connector.spacing_parallel` : de « Mindestabstand in Faserrichtung unterschritten: {have} mm vorhanden, {want} mm verlangt (SIA 265 Tabelle 24). Gleichung (88) gilt nur bei Einhaltung der Mindestabstände (6.2.1.1). » ; fr « Espacement minimal dans le sens du fil non respecté : {have} mm effectifs, {want} mm requis (SIA 265 tableau 24). L’équation (88) n’est valable que si les espacements minimaux sont respectés (6.2.1.1). » ; en « Minimum spacing parallel to the grain not met: {have} mm actual, {want} mm required (SIA 265 table 24). Equation (88) holds only where the minimum spacings are kept (6.2.1.1). »
- `connector.spacing_perpendicular` : même phrase avec « rechtwinklig zur Faser » / « perpendiculairement au fil » / « perpendicular to the grain » (le `%s` de `dowel.py:555` est un mot allemand : un modèle par direction, sinon la capture resterait allemande).
- `connector.kbeta_condition_130` : de « Tabelle 46, Gleichung (130) gilt nur wenn t_2 >= {factor} · t_1; hier ist t_2 = {t2} mm und {factor} · t_1 = {bound} mm. » ; fr « Tableau 46, l’équation (130) n’est valable que si t_2 >= {factor} · t_1 ; ici t_2 = {t2} mm et {factor} · t_1 = {bound} mm. » ; en « Table 46, equation (130) holds only if t_2 >= {factor} · t_1; here t_2 = {t2} mm and {factor} · t_1 = {bound} mm. » — et `connector.kbeta_condition_131` symétrique (t_1/t_2 inversés).
- `connector.diameter_range` : de « SIA 265 6.2.1.1 gibt Gleichung (88) für Stabdübel mit d = {min} bis {max} mm an; hier ist d = {d} mm. » ; fr « SIA 265 6.2.1.1 donne l’équation (88) pour des broches de d = {min} à {max} mm ; ici d = {d} mm. » ; en « SIA 265 6.2.1.1 gives equation (88) for dowels of d = {min} to {max} mm; here d = {d} mm. »
- `connector.no_element` : de « Bauteil {n} ist keinem Element mit Position zugeordnet und trägt keine Festigkeitsklasse. Wählen Sie ein Element des Schemas oder geben Sie die Festigkeitsklasse von Hand ein. » ; fr « La pièce {n} n’est rattachée à aucun élément doté d’une position et ne porte pas de classe de résistance. Choisissez un élément du schéma ou saisissez la classe de résistance à la main. » ; en « Member {n} is assigned to no element with a position and carries no strength class. Choose an element of the schema or type the strength class by hand. »

Test : table de variantes (celle de `s36_dynamic.py`) construite par `connector.build_record`, chaque avertissement passé par `strings.translate(w, lang)` pour fr et en ne contient aucun mot d'une liste allemande (`gilt`, `unterschritten`, `Gleichung`, `Tabelle`, `Bauteil`, …).

### AUD-3-5 | A | `calc/i18n/strings.json` (`terms`) | Les trois valeurs de C_e sont les mots de SIA 261 et restent allemandes dans les rapports fr et en

Preuve : `png/fr-10.png`, pied de page ² : « 𝐶𝑒 = 0.8: dem Wind stark ausgesetzte Lage », « 𝐶𝑒 = 1.2: vor Wind geschützte Lage » (en idem). SIA 261:2020 DE p. 25, 5.2.4 : « normale Windexposition Ce = 1,0 – dem Wind stark ausgesetzte Lage Ce = 0,8 – vor Wind geschützte Lage Ce = 1,2 » ; FR p. 26, 5.2.4 : « exposition au vent normale Ce = 1,0 – endroit fortement exposé au vent Ce = 0,8 – endroit protégé du vent Ce = 1,2 ». Par la règle du §4bis (précédent des Geländekategorien, v0.54), une valeur de classeur que la norme nomme est un mot de la norme. Les `choices` passent déjà par `tl-str` (`calc-engine.typ:1315`).

Correction : ajouter trois termes : « normale Windexposition » → fr « exposition au vent normale », en « normal wind exposure » ; « dem Wind stark ausgesetzte Lage » → fr « endroit fortement exposé au vent », en « location strongly exposed to wind » ; « vor Wind geschützte Lage » → fr « endroit protégé du vent », en « location sheltered from wind » (anglais : traduction libre, pas d'édition anglaise de SIA 261). Test : `strings.translate` de chaque `desc` de `vars.ce.choices` de `calculations.json` en fr diffère de l'allemand ; et la sonde fr ne contient plus « Windexposition » hors de la capture traitée en AUD-3-6.

### AUD-3-6 | B | `lib/i18n.typ:198-203`, `calc/i18n/strings.py:203-207`, modèle `snow.exposure_desc` | Une capture de modèle est réinsérée telle quelle : « Exposition au vent choisie : normale Windexposition. »

Preuve : `pdf-fr.txt` l. 778 ; `s33` : capture `{'exposure': 'normale Windexposition'}`. Même après AUD-3-5, la capture reste allemande, `fill-template` ne la traduisant pas.

Options : (a) traduire chaque capture par un appel récursif restreint aux termes (`glossary.terms`) avant `fill-template`, des deux côtés (Typst et Python) — risque : une capture qui est un nom de feuille ou une valeur de l'ingénieur égale par hasard à un terme serait traduite ; (b) ne traduire que les captures des modèles qui le déclarent (liste `translate_holes` par modèle, ex. `snow.exposure_desc: ["exposure"]`) ; (c) faire composer à `snow.py` une description sans la valeur (elle figure déjà dans la liste des choix, cochée). Recommandation : (b), explicite et sans effet de bord.

### AUD-3-7 | B | `calc/domains/dowel.py:623-626`, `calc/domains/connector.py:441`, `:445`, `:449`, `:458` | La note du tableau « Lochleibungsfestigkeit » porte la provenance des classes en allemand dans les rapports fr et en

Preuve : `phase1-pdf/fr-u3.pdf` p. 16 : « Tableau 22; pour un effort oblique par rapport au fil, les valeurs sont interpolées linéairement. Bauteil 1: C24, im Verbindungsmittel festgelegt; Bauteil 2: C24, im Verbindungsmittel festgelegt. » ; en p. 16 idem ; vu sur `png/fr-16.png` et `png/en-16.png`. La provenance est captée par le trou `{members}` du modèle `connector.embedment_note` et réémise telle quelle ; variantes « C24, aus Position T001 » et « GL24h, im Verbindungsmittel festgelegt (Position S001: C24) » (sonde p. 7).

Options : (a) retirer la provenance de la note du rapport (le Katalog l'affiche déjà en orange, et le tableau imprime la classe) ; (b) exporter la note en liste de phrases, chacune reconnue par un modèle (« Bauteil {n}: {grade}, im Verbindungsmittel festgelegt » / « …, aus Position {pid} » / « … festgelegt (Position {pid}: {held}) »), ce qui touche `render-table` et le schéma `connectors` ; (c) option (a) de AUD-3-6 étendue aux modèles, avec découpage sur « ; ». Recommandation : (a) ou (b) ; décision de l'ingénieur car la note change en allemand aussi.

### AUD-3-8 | B | `calc/domains/connector_svg.py:278-280` | La coupe, figure déclarée sans mots et commune aux trois langues, écrit « Ø vergrössert/verkleinert, nicht massstäblich »

Preuve : sonde fr p. 7, `png/probe-fr-7.png` : sous la coupe de `AUD-HH-W` (d = 20 mm), « Ø verkleinert, nicht massstäblich » ; texte `"Ø %s, nicht massstäblich" % ("vergrössert" if enlarged else "verkleinert")`. Sur le projet (d = 10 mm) la note n'apparaît pas, d'où le contrôle 15 conforme.

Options : (a) un fichier de coupe par langue, la note passant par `strings.text` (clés à créer « Ø vergrössert, nicht massstäblich » / « Ø agrandi, pas à l’échelle » / « Ø enlarged, not to scale » et « verkleinert » / « réduit » / « reduced ») ; (b) exporter un indicateur (`figures.section.scaled: "enlarged"|"reduced"`) et écrire la note en Typst sous la figure, avec la clé existante `figure.enlarged` et une nouvelle ; (c) un repère sans mot (« Ø ≠ 1:1 »). Recommandation : (b), qui garde la figure sans mots.

### AUD-3-9 | B | `calc/i18n/strings.json` (`terms` « Auflast », « Auflast (Flächenlast) », « Eigen- und Auflasten ») | La traduction d'« Auflasten » contredit SIA 261:2020 tableau 80, que le bloc `_sources` cite

Preuve : SIA 261:2020 FR p. 131, tableau 80 (colonnes alignées) : « Eigenlast – Poids propre – Dead load », « Auflasten – Poids propre non-structural – Non-structural self-weight » ; FR p. 17, titre du chapitre 2 « Poids propres de la structure porteuse et des éléments non-structuraux » (DE p. 16 « Eigenlasten und Auflasten »). Le glossaire donne fr « Charge permanente », en « Superimposed load », et `_sources.en` écrit lui-même « Auflasten = non-structural self-weight ». Dans le rapport fr (p. 8) : « 𝑔𝑘 Total Poids propre / 𝑎𝑘 Total Charge permanente », alors que g_k et a_k sont tous deux permanents (« Ständige Lasten » = « Charges permanentes »).

Options : (a) fr « Poids propre non structural », en « Non-structural self-weight » (mot de la norme), « Eigen- und Auflasten » → fr « Poids propres de la structure porteuse et des éléments non structuraux » ou forme courte « Poids propre et poids propre non structural », en « Dead load and non-structural self-weight » ; (b) garder les traductions actuelles et marquer l'entrée comme traduction libre. Recommandation : (a).

### AUD-3-10 | A | `calc/i18n/strings.json` (9 entrées) | « organe(s) d’assemblage » n'est pas le terme de SIA 265 FR, qui dit « moyen(s) d’assemblage » ; le glossaire mélange les deux

Preuve : `s38.txt` : SIA 265:2021 FR, « moyens? d.assemblage » 51 occurrences (p. 10 1.1.35, p. 11 M_u,k, p. 12 « a1 espacement des moyens d’assemblage »), « organes? d.assemblage » 0. `s39` : 13 entrées du glossaire disent « moyen(s) », 9 disent « organe(s) ». Dans le même rapport fr : « Abbildung 9: VU-SD-10 – Disposition des organes d’assemblage » puis « Abbildung 11: … – Moyens d’assemblage et forces par moyen d’assemblage ».

Correction : remplacer « organe » par « moyen » (accord inchangé : « d’organes » → « de moyens ») dans `templates.connector.pattern_caption` (« Disposition des moyens d’assemblage ») et dans les termes « Abstand der Verbindungsmittel untereinander in Faserrichtung » (« Espacement des moyens d’assemblage dans le sens du fil »), « Anzahl der in Faserrichtung des Holzes hintereinander angeordneten Verbindungsmittel » (« Nombre de moyens d’assemblage disposés l’un derrière l’autre dans le sens du fil »), « Anzahl Verbinder » (« Nombre de moyens d’assemblage »), « Anzahl Verbindungsmittel quer zur Faserrichtung » (« Nombre de moyens d’assemblage perpendiculairement au fil »), « Gleichung (86), jedoch… » (« Pour un moyen d’assemblage seul… »), « Tabelle 24. Gleichung (88)… » (« …du nombre de moyens d’assemblage… »), « Tabelle 25, pro Verbindungsmittel… » (« Tableau 25, par moyen d’assemblage… »), « Tragwiderstand pro Verbindungsmittel » (« Résistance ultime par moyen d’assemblage »). Test : aucune valeur fr du glossaire ne contient `organes? d.assemblage`.

### AUD-3-11 | A | `calc/i18n/strings.json` | Deux graphies anglaises pour la même notion : « predrilled » (clés `engine`) et « pre-drilled » (termes)

Preuve : `s31` `engine_vs_terms_divergent` : « vorgebohrt » → engine `predrilled`, term `pre-drilled` ; « nicht vorgebohrt » → `not predrilled` / `not pre-drilled` ; « Vorbohrung » → `Pre-drilling`. PDF en p. 7 « predrilled » puis p. 16 « Pre-drilling … pre-drilled ». Aucune source dans la bibliothèque (EN 1995-1-1:2004, texte extrait : 0 occurrence de chaque graphie).

Correction : aligner sur la graphie des clés `engine` et de CLAUDE.md : termes « vorgebohrt » → « predrilled », « nicht vorgebohrt » → « not predrilled », « Vorbohrung » → « Predrilling ». Test : aucune valeur `en` ne contient `pre-drill`.

### AUD-3-12 | A | `calc/i18n/strings.json` (10 entrées fr) et `lib/calc-engine.typ:1761`, `:1890`, `:1315`, `:945`, `:1094`, `:1208`, `:2190`, `:2219`, `:2348` | Typographie française incohérente : deux-points et point-virgule sans espace fine avant

Preuve : `s39.txt` : 20 occurrences espacées contre 10 collées dans les valeurs fr (`connector.embedment_note` « Tableau 22; pour », `connector.mixed_moisture` « ({classes}); la plus », `connector.n_tot_override` « à la main; le dessin », termes « Bei mehrschnittigen… » « facteur auxiliaire: », « Die Verbindung trägt keine Feuchteklasse… » « d’humidité; eta_w », « Ein Bauteil trägt keine auswertbare… » « exploitable; la », « Gleichung (88)… » « des N; la », « Tabelle 25… » « courte durée; pour », « Zwischenwerte… (Figur 45). Die vorhandene… » « auxiliaire: », « Zwischenwerte… Massgebend ist der kleinere Wert… » « déterminante; »). Côté Typst, `t-label` applique déjà `\u{202f}:` en français (« Centre de rotation (fixé) : ») mais les jonctions `[:]` / `": "` ne le font pas : « Géométrie du bâtiment: », « Hauteur du gradient: », « Catégorie de surface utile H, Toitures non accessibles (…): », « Assemblage VU-MP-1: … », « Plan de position Pavillon: Grundriss » ; et dans `show-calc("connection", …)` « Centre de rotation (fixé): » contre « Centre de rotation (fixé) : » dans `show-polar-moment` (sonde p. 10 et p. 13).

Correction : dans les 10 valeurs fr, écrire «  ; » et «  : » (espace fine insécable, comme `t-label`) ; dans `calc-engine.typ`, remplacer ces jonctions par une aide commune, par ex. `#let colon() = if report-lang() == "fr" { "\u{202f}:" } else { ":" }` utilisée aux lignes citées (`[:]` → `[#colon()]`, `": " + c.label` → `colon() + " " + c.label`). Test : aucune valeur fr du glossaire ne contient `\S[;:](\s|$)` hors `$…$` et hors « 1: » d'échelle ; compilation fr de `show-calc("snow-load","SL", level: 3)` : texte extrait contient « Géométrie du bâtiment : » (espace fine).

### AUD-3-13 | B | `calc/domains/dead_load.py:30`, `calc/domains/snow.py:138`, `:144`, `calc/domains/wind.py:295` | Citations « SIA 261 §Anhang A / D / E » imprimées telles quelles en fr et en

Preuve : `pdf-fr.txt` l. 659-661 « 𝑔𝑘 = 0.8 kN/m² SIA 261 §Anhang A », l. 770 « §Anhang D », l. 798 « §Anhang E ». SIA 261:2020 FR p. 3 et p. 17 : « Annexe A ». Le §4bis dit que la citation d'une norme reste telle qu'écrite, mais « Anhang » est un mot composé par le moteur, et « §Anhang » (paragraphe + annexe) se lit mal aussi en allemand.

Options : (a) garder (citation invariante) ; (b) exporter `norm_ref: "A"` avec un genre (`kind: "annex"`) et composer « Anhang A » / « annexe A » / « Annex A » sans « § » dans `norm-text` ; (c) ajouter les termes « Anhang A|D|E » et les faire passer par `tl-str` dans `norm-text`. Recommandation : (b).

### AUD-3-14 | C | `calc/i18n/strings.json` | 24 termes absents de l'export et de tout littéral du code : restes à lister

Preuve : `s31` `term_orphans`, recoupé à la main (`grep` des fragments dans `calc/`). Restes de fonctionnalités retirées : « erforderlich », « vorhanden », « Nachweis » (colonnes de Tabelle 24 supprimées en fin de v0.77) ; inatteignables : « Bauteil 3…6 », « Lochleibungsfestigkeit Bauteil 3…6 », « Reduktionsbeiwert Bauteil 3…6 » (`dowel.analyse` ne prend que `members[:spec["members"]]`, au plus 2) ; « Zwei Einzellasten von je der Hälfte… » seul (la note 4 n'apparaît jamais sans la note 3, dont la forme combinée est un autre terme). Produits par des chemins non exercés, donc légitimes : « Scherfuge A/B » (étiquettes de Figur 45, `dowel.py:673`), « Bei mehrschnittigen Stahl-Holz-Verbindungen… », « Zwischenwerte… Die vorhandene Anzahl Scherfugen… », « Dachformbeiwert für die Schneeanhäufung in der Kehle eines Sheddachs… », « Die Verbindung trägt keine Feuchteklasse… », « Ein Bauteil trägt keine auswertbare Festigkeitsklasse… » (raisons affichées par le Katalog). « Nutzfläche » est utilisé (symbole cité `"Nutzfläche"`, `live_load.py:119`, traduit par `value-word`). Suppression éventuelle des 15 restes : décision de l'ingénieur.

### AUD-3-15 | C | `calc/domains/connector.py:676`, `:684-685`, `calc/domains/dowel.py:377-378`, `:937` | Chaînes allemandes sans traduction qui n'atteignent pas le rapport (Katalog seulement, à recouper avec la phase 4)

Preuve : `s36` : « Nagel: für diese Art von Verbindungsmittel gibt es noch keine Berechnung. », « Kein Verbindungsmittel des Schemas ist ausgewählt; ohne Bild der Anordnung sind weder die Mindestabstände noch n_tot bestimmt. » (raisons d'un connecteur non calculé, que le rapport refuse par `panic`, message anglais contenant la raison allemande) ; nom d'étape « Tragwiderstand im Fachwerk » (le rapport n'imprime pas les noms d'étapes). `dowel.py:377` compose « …Klasse %d mit eta_w = %s (SIA 265 Tabelle 4). », variante du modèle `connector.mixed_moisture` qu'elle ne reconnaît pas ; elle est inatteignable depuis `connector.build_record` (une seule classe d'humidité par assemblage depuis le schéma 1.1).

### AUD-3-16 | C | `calc/domains/snow.py:153`, `:170`, `:179`, `:182`, `:211` | Numéros de chiffre des citations de neige décalés par rapport à SIA 261:2020 (à confier aux phases 2/7)

Preuve : SIA 261:2020 DE p. 25 : C_e est 5.2.4 (le rapport cite « 𝐶𝑒 = 1; 𝐶𝑇 = 1 SIA 261 §5.2.2 ») ; DE p. 26 : « 5.3.4 Wenn ein Abgleiten des Schnees vom Dach erschwert oder behindert wird… » alors que la var `abgleiten` et le terme « Ist das Abgleiten behindert oder erschwert… (SIA 261, Ziffer 5.3.6) » citent 5.3.6, qui traite en 2020 des « Gebäuden mit abgestuften Dächern » ; `hoehenspruenge` cite 5.3.5. Relevé en passant, le contenu des citations n'étant pas l'objet de la phase 3.

### AUD-3-17 | C | `calc/i18n/strings.json` (`_sources`) | Aucune entrée n'indique sa source ou « traduction libre » ; le bloc global revendique plus que les normes ne donnent

Preuve : c'est le premier audit, donc tout terme est « ajouté depuis le dernier audit » (3.1 point 4). Le fichier n'a pas de champ par entrée. `_sources.fr` attribue aux tableaux 45 et 46 les noms des quatre configurations, mais « tôles insérées » (« Stahl-Holz, Schlitzbleche ») n'apparaît pas dans SIA 265:2021 FR (0 occurrence de « tôles insérées », « tôles intérieures », « en fente » ; le tableau 46 p. 97 dit « Acier – bois à section multiple ») ; AUD-3-9 contredit le tableau 80 cité. Proposition : un champ facultatif `src` par entrée (« SIA 261:2020 FR p. 26, 5.2.4 » ou « libre »), et un test qui l'exige pour toute entrée nouvelle.

### AUD-3-18 | C | divers | Remarques mineures sans correction proposée d'office

(1) Cinq « modèles » sans trou (`connection.figure_caption`, `connection.forces_note_head`, `connection.forces_note_tail`, `connector.pattern_caption`, `connector.section_caption`) : fonctionnent via `t-str`, mais seraient à leur place dans `engine`. (2) Le terme « Blatt » (assemblage à mi-bois, `connector_svg.py:527`) a pour clé le mot qui veut aussi dire « feuille » : une étiquette « Blatt » ailleurs serait traduite « Assemblage à mi-bois ». (3) Indices allemands dans des symboles composés par le moteur : R_d,Verb, n_quer, K_ser,Verb, (g_k + a_k)_gew — invariants par §4bis (symboles), à confirmer pour `gew`, qui n'est pas un symbole de norme. (4) Virgule décimale « 0,35 » dans les avertissements (130)/(131) (`dowel.py:_de`), alors que le rapport imprime le point dans les trois langues (§4bis). (5) « Déterminant : Moyens d’assemblage 1, 4 » : majuscule après deux-points en français (la clé `fasteners` est capitalisée pour l'allemand). (6) Tableau 8, ligne H : « Toitures non accessibles 5) » et « Nicht begehbare Dächer 5) » impriment l'appel de note en ligne, les colonnes q_k/Q_k en exposant. (7) Valeur de classeur « Dachbegrnung (Bienenweide) (voll Nass) » (ü manquant) dans la bibliothèque de matériaux : donnée de l'ingénieur, à signaler à la phase 2. (8) Les PDF fr/en coupent le français avec les motifs de césure allemands (`doc-lang` de `config.typ`) : voulu par §4bis, aucune coupure fautive vue.

## NON FAIT

- Contrôle visuel des sections 6 et 7 (page 23 fr / 22 en) : elles ne contiennent que la prose de l'ingénieur ; le texte extrait a été contrôlé (contrôle 13).
- Source normative pour « predrilled » / « pre-drilled » (AUD-3-11) : SIA 265 FR annexe G p. 110-111 ne livre pas de texte à pypdf (page graphique) et EN 1995-1-1 ne contient aucune des deux graphies au texte extrait ; la page d'annexe G n'a pas été rendue en image.

## Vérifications manuelles proposées à l'ingénieur

1. Compiler le rapport en français (`build.ps1 -Language fr -Uniform 3`) après correction de AUD-3-1 à 3-5, et relire p. 7 (liste des moyens d'assemblage), p. 16 (note du tableau 22), p. 10 (notes de C_e).
2. Trancher AUD-3-6, 3-7, 3-8, 3-9 et 3-13, qui touchent la forme du texte allemand ou le schéma d'export.
3. Relire dans SIA 261:2020 les chiffres 5.2.4, 5.3.4 et 5.3.6 contre les citations de la neige (AUD-3-16).

## Contrôles qui pourraient devenir des tests (`tests/test_i18n.py`)

1. **Aucun allemand après traduction des chemins de connecteur** : table de variantes (`s36_dynamic.py`) → `build_record` → chaque avertissement, note, titre, en-tête et cellule texte de tableau passé par `strings.translate(…, "fr"|"en")` ne contient aucun mot d'une liste allemande. Aurait attrapé AUD-3-3, 3-4, 3-7.
2. **`show-connector` et `show-connector-resistance` en fr** : compiler une sonde et chercher les clés allemandes de `terms` dans le texte extrait (hors valeurs de l'ingénieur). Aurait attrapé AUD-3-1.
3. **Figures sans mots** : pour toutes les valeurs de d de 6 à 30 mm, `connector_svg.section()` ne contient aucun mot de 3 lettres ou plus hors unités. Aurait attrapé AUD-3-8.
4. **Typographie et terminologie du glossaire** : pas de `;`/`:` collé dans les valeurs fr, pas de `organes? d.assemblage`, une seule graphie de « predrilled » en anglais.
5. **Note du tableau des forces** : le texte extrait de `show-polar-moment(level: 3)` contient les deux « ; » de la note.
6. **Orphelins** : chaque terme est présent dans l'export d'un jeu de sources de test, ou dans une liste blanche commentée (chemins non exercés), de sorte qu'un terme laissé par une fonctionnalité retirée soit signalé.
