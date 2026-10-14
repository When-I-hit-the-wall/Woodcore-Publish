# Audit 260916-2326 — Phase 4 : traductions du Typst-Katalog (fr, de, en)

Agent « p4 », bac à sable `AUDIT/projet-phase4/` (et `AUDIT/projet-phase4v/`, copie aux dossiers de sources vidés pour l'état « onglet sans source »). Commit audité `997570db`. Scripts, récoltes et preuves dans `AUDIT/p4/`.

## ⚠️ État git de l'arbre réel à la remise

`git status --short` n'est **pas vide** : 26 fichiers modifiés (29 à la dernière vérification, le travail continue) (CLAUDE.md, README.md, `lib/*.typ`, `calc/domains/connection*.py`, `schema*.py`, `connector_svg.py`, `export_all.py`, `build_reference.py`, `schemas/schemas.schema.json`, 14 fichiers de `tests/`), horodatés entre 07:35 et 07:46 le 17.09. Les diffs citent « periodic audit 260916, AUD-7-210 » : ce sont les corrections de la phase 9 de la session principale (ou d'une autre session), **pas** l'agent p4, dont tous les scripts écrivent exclusivement sous `AUDIT/`. Aucun des fichiers audités ici (`calc/tools/*_tab.py`, `catalog_gui.py`, `grouped_list.py`, `identity.py`, `strings.json`) n'y figure, sauf `build_reference.py` (changement sans rapport avec les textes) ; les numéros de ligne ci-dessous sont ceux du commit `997570db`.

## Bilan chiffré

20 contrôles menés : 8 conformes, 10 ayant produit des constats, 2 partiellement NON FAITS. Constats : **10 A, 2 B, 8 C** (AUD-4-1 à AUD-4-20).

| Contrôle | Résultat |
|---|---|
| 4.1 littéraux passés aux widgets (AST, 18 modules, 30 méthodes/constructeurs) | 22 occurrences : 19 légitimes (« Typst-Katalog » ×18, « auto »), 2 défauts (AUD-4-5, AUD-4-7) |
| 4.1 littéraux larges (≥ 2 mots hors STRINGS/docstrings/exceptions) | 62 : CSS, SVG, HTML, message PySide6 trilingue, textes de repli de `grouped_list`/`source_archive` (AUD-4-15) |
| 4.1 `schema.Refused` contre `schema_tab.REFUSALS` | 2 codes sans mots, inatteignables par l'interface (AUD-4-14) |
| 4.1 avertissements des domaines et exceptions affichés | anglais dans 4 onglets (AUD-4-11), allemand non traduit dans Connecteurs (AUD-4-3, 4-4, 4-5), exception brute (AUD-4-6) |
| 4.1 clés jamais lues | 830 clés ; 16 familles dynamiques reconstituées (79 clés, toutes résolues) ; **40 orphelines** (AUD-4-9) ; 0 clé définie dans deux modules |
| 4.1 terminologie `strings.json` ↔ `STRINGS` (27 termes) | incohérences sur Verbindungsmittel, Stabdübel, Mittelholz (AUD-4-12) |
| 4.2 récolte dynamique | 48 sous-processus (3 langues × 8 onglets × projet complet/vide), 376 131 textes, 0 délai dépassé |
| 4.2 dialogues bouchonnés (question, warning, getText, getDouble, getOpenFileName, PageDialog, GridDialog, menus contextuels) | titres et textes traduits, sauf boutons standard Qt (AUD-4-2) et filtre de fichier (AUD-4-7) |
| 4.2 chemins d'erreur : outil STE sans position, quitter une source modifiée, supprimer, dossier déjà pris | conformes dans les 3 langues |
| 4.2 enregistrer sous un ID pris | conforme dynamiquement pour Plans et Schémas ; NON FAIT dynamiquement pour Modèles statiques, Connecteurs, Moments polaires (voir NON FAIT), vérifié statiquement |
| 4.2 onglet sans source, export absent | textes traduits (« Aucune donnée : … calculations.json est introuvable… ») |
| 4.3 textes identiques dans les 3 langues | 106 candidats : documentation `///` (anglaise par décision §10sexies), données, nom du produit ; défauts : AUD-4-5, 4-7, 4-11 |
| 4.3 fuite de vocabulaire propre à une langue | 96 occurrences : défauts AUD-4-3/4-4 (allemand), AUD-4-2 (« Cancel »), AUD-4-11 (anglais) ; le reste = documentation ou artefacts du harnais |
| 4.3 valeur exacte de `STRINGS` d'une autre langue | 0 (conforme) |
| 4.3 phrase entière dans une autre langue | 30 : même familles |
| 4.3 clé brute ou texte vide affiché | 0 clé brute ; 2 codes de refus bruts atteints seulement par appel forcé (AUD-4-14) ; lecture de pointeur brute (AUD-4-1) |
| 4.4 `SAME_IN_TWO_LANGUAGES` | 2 exceptions, toutes deux justifiées (« vertical + horizontal » fr/en, relevé de coordonnées) : conforme ; les 79 jumeaux courts de `STRINGS` sont des mots apparentés (« Description », « Angle », « Points ») |
| 4.5 captures 1400 × 780, 8 onglets × 3 langues (24 images regardées) | aucun libellé traduit tronqué hors zones défilantes voulues ; élisions notées (AUD-4-18) |
| probe ciblée (9 points × 3 langues, `p4/probe-*.json`) | confirme AUD-4-1, 4-3, 4-5, 4-6, 4-7, 4-10, 4-11 |

## Méthode (reproductible)

- `p4/static_literals.py`, `p4/unused_keys.py`, `p4/terminology.py` : analyse statique (AST).
- `p4/run_harvest.py full|empty <langs> <tabs>` lance `p4/harvest.py` une fois par (langue, onglet), délai 300 s, `QT_QPA_PLATFORM=offscreen`, `QT_QPA_FONTDIR`, `TYPST_KATALOG_SETTINGS`, `LOCALAPPDATA` et `APPDATA` dans le bac à sable. La fenêtre démarre dans une autre langue et change par son propre combo « Langue ». `Catalog()` est construit directement (pas `main()`).
- `p4/analyse.py`, `p4/analyse2.py` : analyse de la récolte (`p4/an_*.json`, `p4/an2.txt`, `p4/dialogs.txt`).
- `p4/probe.py <lang>`, `p4/qt_buttons_probe.py`, `p4/connector_warnings_probe.py`/`…probe2.py`, `p4/connector_messages.py` : preuves ciblées.
- `p4/shots.py <lang>` : captures `p4/shots1400/*.png`.
- ⚠️ Deux pièges de harnais, utiles pour tout futur test hors écran : (1) `QMenu.exec = stub` au niveau de la classe PySide6 **n'a aucun effet** (le vrai menu modal s'ouvre et le processus se fige) — il faut une sous-classe Python substituée au nom `QMenu` du module, ou patcher `exec` sur la classe Python (`PageDialog`, `GridDialog`) ; (2) après un changement de langue, `processEvents()` ne traite pas les `deleteLater` : les widgets de l'ancienne langue restent enfants de la fenêtre (première récolte polluée : « Moments polaires » vu dans la fenêtre allemande). Il faut `app.sendPostedEvents(None, QEvent.Type.DeferredDelete)`.

## Constats

### AUD-4-1 | A | `calc/tools/schema_tab.py:1471-1475`

Le relevé du pointeur de l'onglet « Schémas » affiche les genres d'accrochage bruts, en anglais et au format interne, dans les trois langues : `[midpoint]`, `[on-line]`, `[ray|45|25]`, `[shift||20]` ; l'onglet « Modèles statiques » les traduit (`st_snap_*`, `st_lock`).

Preuve : `p4/probe-de.json` → `schema_readout["midpoint"] = "x = 1 mm    z = 2 mm    [midpoint]"`, `["ray|45|25"] = "…[ray|45|25]"` ; `statics_readout["midpoint"] = "x = 1 m   z = 2 m   [Mitte]"`, `["ray|45|2.5"] = "x = 1 m   z = 2 m   ⟨ 45°  ·  2.5 m   [Richtung]"`. Genres émis : `schema.SNAP_KINDS` (point, midpoint, crossing, on-line, grid) + `ray`, `ray-crossing`, `shift` (`schema_canvas.readout`).

Correction : clés à créer dans `schema_tab.STRINGS` — `sc_snap_point` point / Punkt / point ; `sc_snap_midpoint` milieu / Mitte / midpoint ; `sc_snap_crossing` intersection / Schnittpunkt / crossing ; `sc_snap_on_line` sur la ligne / auf der Linie / on the line ; `sc_snap_grid` grille / Raster / grid ; `sc_snap_ray` direction / Richtung / direction ; `sc_snap_ray_crossing` prolongement / Verlängerung / extension ; `sc_snap_shift` Maj / Umschalt / Shift ; `sc_lock` « ⟨ {angle}°  ·  {distance} mm » (identique dans les trois, sans mot). Remplacement de `on_pointer` :

```python
def on_pointer(self, x, z, kind):
    text = f"x = {model.fmt_number(x)} mm    z = {model.fmt_number(z)} mm"
    if kind:
        parts = kind.split("|")
        key = "sc_snap_" + parts[0].replace("-", "_")
        name = self.t(key) if key in STRINGS["fr"] else parts[0]   # a measured dimension («140 mm») passes as it is
        if len(parts) == 3 and parts[1]:
            text += "    " + self.t("sc_lock", angle=parts[1], distance=parts[2])
        text += f"    [{name}]"
    self.canvas.set_readout(text)
```

(Les coordonnées restent une f-string : sous forme de clé, « x = {x} mm    z = {z} mm » serait un jumeau des trois langues que `test_i18n` signalerait.) Test : dans `tests/test_schema_tab.py`, pour chaque langue, `tab.on_pointer(1, 2, k)` pour chaque genre de `schema.SNAP_KINDS + ("ray|45|2", "ray-crossing|45|2", "shift||2")` ; `canvas._readout` ne contient ni `|` ni le genre anglais brut hors `en`.

### AUD-4-2 | A | `calc/tools/catalog_gui.py:2577` (`Catalog.__init__`) et `:2815` (`on_language`)

Aucun `QTranslator` n'est installé : les boutons standard de Qt restent en anglais dans les fenêtres fr et de — « Save / Discard / Cancel » de toutes les questions « modifications non enregistrées » (`catalog_gui.py:2396`, `plan_tab.py:1977`, `statics_tab.py:2255`, `schema_tab.py:1642`, `connectors_tab.py:1998`), « &Yes / &No » des confirmations d'archivage et de suppression, « Cancel » des dialogues `PageDialog` (`plan_tab.py:719`) et `GridDialog` (`schema_tab.py:575`), et le menu contextuel des champs de saisie (Undo, Cut, Copy…).

Preuve : `p4/qt_buttons_probe.py` → sans traducteur `['OK', 'Save', 'Cancel', 'Discard', '&Yes', '&No', '|', 'OK', 'Cancel']` ; avec `qtbase_fr.qm` (livré dans `PySide6/translations`) `['OK', 'Enregistrer', 'Annuler', 'Ne pas tenir compte', '&Oui', '&Non', '|', 'OK', 'Annuler']` ; de : `Speichern, Abbrechen, Verwerfen, &Ja, &Nein`. Récolte : `DIALOG:GridDialogQPushButton text 'Cancel'` en de et fr ; `probe-de.json` → `page_dialog.buttons = ["Alle wählen", "Keine", "Erstellen (0)", "Cancel"]`.

Correction : dans `catalog_gui.py`, importer `QLibraryInfo, QLocale, QTranslator` de `PySide6.QtCore`, puis

```python
_QT_TRANSLATOR = None

def install_qt_translation(lang):
    """Qt's own words -- Save, Discard, Cancel, Yes, No, the context menu of a field -- in the window's language (qtbase_<lang>.qm ships with PySide6)."""
    global _QT_TRANSLATOR
    app = QApplication.instance()
    if _QT_TRANSLATOR is not None:
        app.removeTranslator(_QT_TRANSLATOR)
    _QT_TRANSLATOR = QTranslator(app)
    if _QT_TRANSLATOR.load(QLocale(lang), "qtbase", "_", QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)):
        app.installTranslator(_QT_TRANSLATOR)
```

appelé à la fin de la ligne 2577 (`install_qt_translation(self.lang)`) et dans `on_language` avant `self.rebuild()`. Aucune clé à créer. Test (`tests/test_i18n.py`) : pour chaque langue, `Catalog()` puis `QMessageBox(QMessageBox.Icon.Question, "", "", Save | Discard | Cancel).button(Save).text()` vaut « Enregistrer » / « Speichern » / « Save ».

### AUD-4-3 | A | `calc/tools/connectors_tab.py:1522-1523`

Les avertissements jaunes de l'onglet « Connecteurs » restent en allemand dans les fenêtres fr et en même quand le glossaire porte leur modèle : l'onglet traduit la liste `warnings` renvoyée par `connector.build_record`, dont chaque ligne commence par `connectors/<id>.json: `, alors que les modèles de `strings.json` (`connector.n_tot_override`, `connector.position_gone`, `connector.position_no_grade`…) commencent par le texte ; `strings.match` exige `startswith`. `connector.finish()` (connector.py:652-655) stocke pourtant la même liste **sans** ce préfixe dans `record["warnings"]`. Contredit CLAUDE.md §10quater (« the warnings… each translated through the glossary »).

Preuve : `p4/connector_warnings_probe.py` (chemin de code de `refresh`) sur VU-SD-10 avec n_tot écrasé à 9 → fr « connectors/VU-SD-10.json: $n_"tot"$ ist mit 9 von Hand gesetzt; die Zeichnung zeigt 4 Verbindungsmittel. » (identique à l'allemand) ; `…probe2.py`, même record, liste `record["warnings"]` → fr « $n_"tot"$ est fixé à 9 à la main; le dessin en montre 4. », en « …is set to 9 by hand; the drawing shows 4. ».

Correction : `connectors_tab.py:1523` `warnings.extend(record_warnings)` → `warnings.extend(record["warnings"])`. Aucune clé à créer pour ce point. Test : `tests/test_connectors.py`, fenêtre en fr, source VU-SD-10 avec `n_tot = {"value": 9, "override": True}`, `tab.refresh()` : `tab.message.text()` contient « à la main » et ne contient ni « von Hand » ni « connectors/ ».

### AUD-4-4 | A | `calc/domains/connector.py:460, 675, 683` ; `calc/domains/dowel.py:297, 301, 337, 555` ; `calc/i18n/strings.json` (`templates`, `terms`)

Sept phrases allemandes composées par le calcul du connecteur n'ont ni terme ni modèle dans le glossaire : elles restent allemandes dans la fenêtre fr/en (même après AUD-4-3) et, via `record["warnings"]`/`reason`, dans le rapport fr/en (à croiser avec la phase 3). Concerné dès l'usage courant : « Tout décocher » affiche « Pas de résistance : Kein Verbindungsmittel des Schemas ist ausgewählt… ».

Preuve : `p4/connector_messages.py` (13 phrases, 6 UNTRANSLATED après retrait du préfixe) et `p4/probe-fr.json` → `connector_results = "Pas de résistance : Kein Verbindungsmittel des Schemas ist ausgewählt; ohne Bild der Anordnung sind weder die Mindestabstände noch n_tot bestimmt."` ; `…probe2.py` → d = 40 mm : « SIA 265 6.2.1.1 gibt Gleichung (88)… » et « Mindestabstand in Faserrichtung unterschritten… » identiques en fr/en.

Correction (vocabulaire repris de `strings.json` : « moyen d’assemblage », « broche », « pièce », « dans le sens du fil », « tableau ») — dans `templates` :
- `connector.no_module` — de « {type}: für diese Art von Verbindungsmittel gibt es noch keine Berechnung. » / fr « {type} : ce type de moyen d’assemblage n’a pas encore de calcul. » / en « {type}: there is no calculation for this kind of fastener yet. »
- `connector.member_unassigned` — de « Bauteil {n} ist keinem Element mit Position zugeordnet und trägt keine Festigkeitsklasse. Wählen Sie ein Element des Schemas oder geben Sie die Festigkeitsklasse von Hand ein. » / fr « La pièce {n} n’est associée à aucun élément ayant une position et ne porte pas de classe de résistance. Choisissez un élément du schéma, ou saisissez la classe de résistance à la main. » / en « Member {n} is assigned to no element with a position and carries no strength class. Choose an element of the schema, or type the strength class by hand. »
- `dowel.diameter_range` — de « SIA 265 6.2.1.1 gibt Gleichung (88) für Stabdübel mit d = {dmin} bis {dmax} mm an; hier ist d = {d} mm. » / fr « La SIA 265, 6.2.1.1, donne l’équation (88) pour des broches de d = {dmin} à {dmax} mm ; ici, d = {d} mm. » / en « SIA 265 6.2.1.1 gives equation (88) for dowels with d = {dmin} to {dmax} mm; here d = {d} mm. »
- `dowel.condition_130` — de « Tabelle 46, Gleichung (130) gilt nur wenn t_2 >= {k} · t_1; hier ist t_2 = {t2} mm und {k2} · t_1 = {kt1} mm. » / fr « Tableau 46 : l’équation (130) ne vaut que si t_2 >= {k} · t_1 ; ici, t_2 = {t2} mm et {k2} · t_1 = {kt1} mm. » / en « Table 46: equation (130) holds only if t_2 >= {k} · t_1; here t_2 = {t2} mm and {k2} · t_1 = {kt1} mm. »
- `dowel.condition_131` — idem avec « (131) », « t_1 >= {k} · t_2 », « t_1 = {t1} mm », « {k2} · t_2 = {kt2} mm ».
- `dowel.spacing_parallel` — de « Mindestabstand in Faserrichtung unterschritten: {have} mm vorhanden, {want} mm verlangt (SIA 265 Tabelle 24). Gleichung (88) gilt nur bei Einhaltung der Mindestabstände (6.2.1.1). » / fr « Distance minimale dans le sens du fil non respectée : {have} mm disponibles, {want} mm exigés (SIA 265, tableau 24). L’équation (88) ne vaut que si les distances minimales sont respectées (6.2.1.1). » / en « Minimum spacing parallel to the grain not met: {have} mm present, {want} mm required (SIA 265 Table 24). Equation (88) holds only where the minimum spacings are kept (6.2.1.1). »
- `dowel.spacing_perpendicular` — idem avec « rechtwinklig zur Faser » / « perpendiculairement au fil » / « perpendicular to the grain » (deux modèles plutôt qu'un trou, car une capture n'est pas retraduite et laisserait « in Faserrichtung » dans la phrase française).
- dans `terms` : « Kein Verbindungsmittel des Schemas ist ausgewählt; ohne Bild der Anordnung sind weder die Mindestabstände noch n_tot bestimmt. » → fr « Aucun moyen d’assemblage du schéma n’est coché ; sans disposition dessinée, ni les distances minimales ni n_tot ne sont déterminés. » / en « No fastener of the schema is ticked; without a drawn layout, neither the minimum spacings nor n_tot are determined. »

Libellés marqués « traduction libre » (§4bis), l'ingénieur étant libre de les reprendre ; vérifier dans `SIA265-2021-FR.pdf` (6.2.1.1, tableaux 24, 45, 46) l'expression « distances minimales ». Test : `tests/test_i18n.py` — rejouer `connector_messages.py` : chaque littéral allemand passé à `warnings.append`/`reason` dans `connector.py`/`dowel.py`, rempli d'exemples, donne `strings.translate(…, "fr") != …`.

### AUD-4-5 | A | `calc/tools/connectors_tab.py:710` (texte : `calc/domains/dowel.py:63-67`)

L'infobulle des trois assemblages désactivés est l'allemand de `dowel.UNCOVERED_ASSEMBLIES` dans les trois langues, alors que le nom de l'assemblage passe par `self.tl`.

Preuve : `p4/probe-en.json` → `assembly_tooltips = ["SIA 265 Tabelle 45 gibt k_beta nur für ein- und zweischnittige Holz-Holz-Verbindungen an. SIA 265 6.1.1.11.", "SIA 265 Tabelle 46 …", "SIA 265 Kapitel 6 behandelt Holz-Beton-Verbindungen nicht. SIA 265 6.1.1.11."]` ; récolte : même texte en fr, de, en (`an_same_all3.json`).

Correction : ligne 710 `"%s SIA 265 6.1.1.11." % reason` → `"%s SIA 265 6.1.1.11." % self.tl(reason)`, et trois `terms` : « SIA 265 Tabelle 45 gibt k_beta nur für ein- und zweischnittige Holz-Holz-Verbindungen an. » → fr « La SIA 265, tableau 45, ne donne k_beta que pour les assemblages bois – bois à simple et à double section. » / en « SIA 265 Table 45 gives k_beta only for single- and double-shear timber-to-timber connections. » ; « SIA 265 Tabelle 46 gibt k_beta nur für zwei- und mehrschnittige Stahl-Holz-Verbindungen an. » → fr « La SIA 265, tableau 46, ne donne k_beta que pour les assemblages acier – bois à double section et à sections multiples. » / en « SIA 265 Table 46 gives k_beta only for double- and multiple-shear steel-to-timber connections. » ; « SIA 265 Kapitel 6 behandelt Holz-Beton-Verbindungen nicht. » → fr « Le chapitre 6 de la SIA 265 ne traite pas des assemblages bois – béton. » / en « Chapter 6 of SIA 265 does not cover timber-to-concrete connections. » (vocabulaire des termes existants « Bois – bois à sections multiples », « Acier – bois… », « Bois – béton »). Test : fenêtre en fr et en, `itemData(i, ToolTipRole)` des éléments désactivés de `assembly_box` ≠ texte allemand.

### AUD-4-6 | A | `calc/tools/schema_tab.py:1002`

Un schéma illisible met dans la barre d'état le message brut de l'exception, sans phrase traduite ni nom de fichier ; « Plans », « Modèles statiques » et « Moments polaires » ont chacun une clé `*_unreadable`.

Preuve : `p4/probe-fr.json` (fichier `details/P4-Bad.json` = `{ not json`, dans le bac à sable) → `schema_unreadable_status = "Expecting property name enclosed in double quotes: line 1 column 3 (char 2)"`, identique en de et en.

Correction : `self.app.set_status(str(exc))` → `self.app.set_status(self.t("sc_unreadable", name=f"{sid}.json", error=exc))` ; clé `sc_unreadable` : fr « {name} est illisible : {error} » / de « {name} ist nicht lesbar: {error} » / en « {name} cannot be read: {error} » (les formules de `plan_unreadable`). Test : fichier invalide dans une copie de `details/`, `tab.load` : le statut commence par « P4-Bad.json est illisible » en fr.

### AUD-4-7 | A | `calc/tools/plan_tab.py:1301`

Le filtre du dialogue « Fond du plan » est un littéral « Plans (*.pdf *.png *.jpg *.jpeg *.svg) », affiché tel quel dans la fenêtre allemande.

Preuve : `p4/probe-de.json` → `dialogs = [["file", "Hintergrund des Plans", "Plans (*.pdf *.png *.jpg *.jpeg *.svg)"]]`.

Correction : clé `plan_background_filter` : fr « Fonds de plan (*.pdf *.png *.jpg *.jpeg *.svg) » / de « Planhintergründe (*.pdf *.png *.jpg *.jpeg *.svg) » / en « Plan backgrounds (*.pdf *.png *.jpg *.jpeg *.svg) » (formulation différente en fr et en, sinon `test_i18n` signale un jumeau) ; ligne 1301 : `self.t("plan_background_filter")`. Test : bouchon de `QFileDialog.getOpenFileName` en de, le filtre commence par « Planhintergründe ».

### AUD-4-8 | A | `calc/tools/catalog_gui.py:137, 311, 485` (clé `polar_id`, lue en `:1586`)

Le champ d'identifiant de « Moments polaires » s'appelle « Identifiant » / « Kennung » / « Id », alors que les quatre autres onglets d'édition affichent « ID » dans les trois langues (`identity.py:106/112/118`, `idn_id`) — la règle « Nom · Description · ID » du §10quater.

Preuve : captures `p4/shots1400/{fr,de,en}-6-PolarTab.png` (« Identifiant », « Kennung », « Id ») contre `…-5-ConnectorsTab.png` (« ID ») ; `terminology.py`/`STRINGS`.

Correction : `"polar_id": "ID"` dans les trois blocs (ou `self.t("idn_id")` à la ligne 1586 et suppression de `polar_id`). Test : dans `tests/test_polar_tab.py`, l'étiquette de la ligne ID de l'identité vaut `identity.STRINGS[lang]["idn_id"]` pour les trois langues.

### AUD-4-9 | A | clés orphelines (40), lignes des blocs fr / de / en

Clés de `STRINGS` lues nulle part (familles dynamiques `f"plan_tool_{…}"`, `"col_" + …`, `"st_snap_" + …`, `"ref_" + state`… reconstituées au préalable) : restes de l'identité « Groupe · Variante · Désignation » (v0.76-v0.77), de la suppression remplacée par l'archivage, et du formulaire de pièces des moments polaires.

- `connectors_tab.py` : cn_delete_ask (145, 249, 353), cn_delete_title (144, 248, 352), cn_description (102, 206, 310), cn_elements (103, 207, 311), cn_exported (137, 241, 345), cn_group (147, 251, 355), cn_id (100, 204, 308), cn_id_auto (150, 254, 358), cn_label (101, 205, 309), cn_length (106, 210, 314), cn_name (148, 252, 356), cn_variant (149, 253, 357).
- `plan_tab.py` : plan_confirm_delete (181, 335, 489), plan_deleted (180, 334, 488), plan_id (118, 272, 426), plan_label (119, 273, 427).
- `catalog_gui.py` : polar_apply_section (144, 318, 492), polar_confirm_delete (188, 362, 536), polar_deleted (181, 355, 529), polar_member_angle (147, 321, 495), polar_member_angle_first (148, 322, 496), polar_position_missing (143, 317, 491), polar_section_unreadable (142, 316, 490), polar_through_tip (141, 315, 489).
- `schema_tab.py` : sc_col_from (168, 270, 372), sc_col_to (169, 271, 373), sc_delete_confirm et sc_delete_title (180, 282, 384), sc_group, sc_id et sc_label (163, 265, 367).
- `statics_tab.py` : st_along_hint (217, 418, 619), st_commands (283, 484, 685), st_delete_confirm (301, 502, 703), st_dim_anchor_hint (195, 396, 597), st_id (249, 450, 651), st_label (250, 451, 652), st_release_several (209, 410, 611), st_tool_release (160, 361, 562), st_warnings (284, 485, 686).

Preuve : `p4/unused_keys.py` → `keys total 830 unused 40 dynamic-candidates 79` ; grep des queues (`delete_ask`, `member_angle`, `along_hint`…) sur `calc/` : aucune lecture. Correction : supprimer ces 40 entrées dans les trois blocs (à coordonner avec la phase 6, code mort). Test : `tests/test_i18n.py::test_every_katalog_key_is_read` — scan AST des constantes de `calc/tools/*.py` hors `STRINGS`, liste explicite des préfixes dynamiques, aucune clé restante.

### AUD-4-10 | A (hors périmètre textes, à transmettre à p5) | `calc/tools/schema_canvas.py:804`

« Grille… » de l'onglet « Schémas » lève `KeyError: 'kind'` quand l'outil actif est « Sélection » (l'outil par défaut) : `kind = kind or TOOLS[self.tool]["kind"] if self.tool in TOOLS else …` se lit `(kind or TOOLS[tool]["kind"]) if tool in TOOLS else …`, et `TOOLS["select"] == {}` ; `place_grid` passe `kind=None` pour tout outil sans genre. Avec `install_error_box`, l'ingénieur voit une boîte d'erreur au lieu de la grille.

Preuve : `p4/probe-{fr,de,en}.json` → `grid_select_tool = "KeyError: 'kind'"` ; les 6 récoltes de l'onglet Schémas, état `grid-dialog-select-tool`. Avec un outil de repère actif, le dialogue s'ouvre (textes traduits).

Correction : ligne 804 → `tool_kind = TOOLS.get(self.tool, {}).get("kind")` puis `kind = kind or (tool_kind if tool_kind in model.CONNECTOR_KINDS else model.CONNECTOR_KINDS[0])` (la règle de `add_default`, lignes 708-709, et la docstring de `place_grid`). Test : `tests/test_schema_tab.py` — `choose_tool("select")`, `GridDialog.exec` bouchonné pour accepter, `place_grid()` ne lève pas et les repères posés sont du genre `CONNECTOR_KINDS[0]`.

### AUD-4-11 | B | avertissements des domaines affichés en anglais dans la fenêtre

Quatre onglets affichent, sous le dessin ou dans le formulaire, les phrases anglaises des domaines et de leurs `check_source`, dans toutes les langues : `plan_tab.py:1547-1555` (`plan.warnings`, plan.py:985-1005), `statics_tab.py:1818-1823` (`statics.warnings`), `schema_tab.py:1627-1629` (`schema.warnings`, schema.py:1723-1729), `catalog_gui.py:2211-2217` (`connection.schema_warnings`, connection.py:563-584, et `check_source`) ; les boîtes « Enregistrement impossible » reprennent aussi les `ValidationError` anglaises (`fail(str(exc))` : catalog_gui.py:2496, 2503 ; connectors_tab.py:1970 ; plan_tab.py:1360, 2081, 2091 ; schema_tab.py:1707, 1716 ; statics_tab.py:2324, 2333). Or les refus du canevas de « Schémas » sont traduits par code (§3.3decies : « a refusal … is chrome and follows the window »), et §4bis réserve l'anglais aux messages d'erreur.

Preuve : `probe-fr.json` → `statics_warnings = "model Bankli-Fall1: point P2 carries nothing and holds nothing"` (visible dans les captures fr/de/en de Modèles statiques), `plan_messages = "plan Pavillon: T999 is not a position of Positionen.xlsx -- add it to its Positions Element sheet\nplan Pavillon: T999 is drawn as a S (Stütze)"`, `schema_warnings = "schema VU-Skizze: element E1 refers to position 'X999' is not a row of Positionen.xlsx"`, `polar_schema_warnings = ["VU-MP-1 is drawn on schema Gone, which the export does not list -- …"]` ; récolte : « A01 is drawn on no schema -- name one in the Typst-Katalog's polar moments tab… » dès « Nouveau calcul » sur un projet sans schéma.

Options : (a) garder l'anglais (messages destinés aussi à la console d'export) et le dire au §10quater ; (b) donner à chaque avertissement un code et un détail comme `schema.Refused`, traduit par l'onglet (~15 phrases, 4 modules) ; (c) composer ces avertissements en allemand et les faire passer par le glossaire comme ceux des connecteurs (le rapport ne les imprime pas, donc le glossaire n'est pas obligatoire) ; (d) seulement pour la fenêtre, une table de traduction par préfixe dans chaque onglet. (b) est la plus robuste, (a) la moins coûteuse.

### AUD-4-12 | B | terminologie des moyens d'assemblage entre la fenêtre et le rapport

- **Verbindungsmittel** : fenêtre fr « Connecteurs », « connecteur(s) » (`connectors_tab.py:82-83`, `catalog_gui.py` polar_fasteners, polar_trial_result…), mais « organes d’assemblage » dans les libellés du formulaire (`cn_*`) ; rapport fr « moyen(s) d’assemblage » (16 entrées de `strings.json`) et « organe(s) d’assemblage » (8). Fenêtre en : onglet « Connections » (`connectors_tab.py:290`) mais liste « Connectors » (`:291`) ; rapport en « fastener » (23 entrées) — la légende de la figure des moments polaires dit « Normal force per fastener » sous un formulaire titré « Fasteners », dans l'onglet « Connections ».
- **Stabdübel** : glossaire en « Dowel-type fastener », fenêtre en « Dowel » (`cn_type_dowel`, `cn_box_dowel` `:299/:361`, « Dowel layout » `:362`) ; fr cohérent (« Broche »).
- **Mittelholz** : glossaire en « central member », fenêtre « Middle member thickness » (`cn_t2`).

Preuve : `p4/terminology.txt` ; captures `en-5-ConnectorsTab.png` (onglet « Connections », liste « Connectors ») et `en-6-PolarTab.png` (légende « per fastener »). Options : aligner la fenêtre sur le glossaire (fr « moyen d’assemblage », en « fastener »/« dowel-type fastener »), ou choisir « connecteur »/« connector » comme terme de l'interface et le dire au §4bis ; dans tous les cas, l'onglet anglais ne devrait pas s'appeler « Connections » (Verbindung) pour une liste de « Connectors ». Décision terminologique de l'ingénieur (SIA 265 FR, annexe G, tableau 51, pour le terme normatif).

### AUD-4-13 | C | guillemets incohérents

de : »{id}« dans 11 clés `polar_*` (« Die Berechnung »A01« hat… »), «{id}» ailleurs, « « {id} » » avec espaces à la française dans `st_*` (« Das System « Bankli-Fall1 » hat… », `st_id_exists`) ; en : “{id}” (20 clés, `polar_*`, `grp_*`) contre «{id}» (43) ; fr : une clé `st_rename` avec des guillemets droits. Preuve : `p4/dialogs.txt` (questions « modifications non enregistrées » des 5 onglets). Style à fixer par l'ingénieur.

### AUD-4-14 | C | `calc/tools/schema_tab.py:412-436` et `:1477-1485`, `schema_canvas.py:1127-1131`

`REFUSALS` n'a pas de mots pour `merge-missing` et `merge-not-element` (schema.py:1622-1624) : la barre d'état afficherait « merge-missing|E9 » ; un code connu reçu sans détail affiche le trou « {detail} » non rempli (`self.t(key)` sans argument) ; la docstring de `refusal_text` promet « falls through as the English sentence » mais c'est le code qui passe. Inatteignable aujourd'hui (le canevas ne passe que des éléments sélectionnés, et chaque `Refused` à trou porte un détail). Preuve : appel forcé `tab.on_refused("merge-missing|E9")`, `on_refused("split-crossings")` → « La ligne traverse cette surface {detail} fois… ».

### AUD-4-15 | C | textes de repli français de `grouped_list._t` et `source_archive.Actions._t`

`grouped_list.py:101, 346-384, 450` et `source_archive.py:92, 159-212` passent un texte français comme repli ; il ne s'affiche que si une clé `grp_` manque, et s'afficherait alors en français dans une fenêtre allemande. Toutes les clés existent (vérifié dans les trois langues, menus contextuels récoltés : « Neuer Ordner… », « Wiederherstellen », « Endgültig löschen… »). Option : repli sur la clé elle-même, qui se verrait.

### AUD-4-16 | C | `catalog_gui.py:125, 299` (+ bloc en) `future_combinations` (onglet « Combinaisons de charges »)

Le texte annonce « Les combinaisons ELU/ELS seront calculées dans calc/domains/combinations.py (CLAUDE.md §3.5) », module supprimé en v0.59 (CLAUDE.md §11) ; le futur le rend défendable. Traduit dans les trois langues. À croiser avec les phases 6-7.

### AUD-4-17 | C | casse et libellés d'en-têtes

En-têtes des tableaux de « Schémas » en minuscules (« id, position, vue, points » en fr ; « id » en de/en) contre « Id, Type, Point 1 » dans « Modèles statiques » ; combo de pas de grille « auto » littéral (`schema_tab.py:723`) contre la clé `st_grid_auto` (`statics_tab.py:1314`) — même mot dans les trois langues. Preuve : captures `*-3-StaticsTab.png`, `*-4-SchemaTab.png`.

### AUD-4-18 | C | élisions et coupes dans les captures 1400 × 780

Aucun libellé traduit n'est tronqué hors zones défilantes. Élisions : « show-connector-resista… » (onglet Commandes, colonne étroite, 3 langues), entrées « VU-MP-1 — Velo Unterstand: Stabdü… » de la liste des moments polaires (données) ; bouton « Ajuster / Einpassen / Fit » coupé au bord de la zone « Navigation » de « Schémas » et groupe « Articulations / Gelenke / Releases » coupé dans « Modèles statiques » — barres à défilement horizontal voulues (v0.66, v0.75) ; libellés allemands les plus longs sur deux lignes sans perte (« Winkel zwischen der Kraft- und Faserrichtung der Holzteile »).

### AUD-4-19 | C | anglais fautif dans deux avertissements (si l'option (a) d'AUD-4-11 est retenue)

`schema.py:1726` + `_unresolved_reasons` : « element E1 refers to position 'X999' is not a row of Positionen.xlsx » (deux verbes) ; `plan.py:996` : « T999 is drawn as a S (Stütze) » (article, et allemand dans la parenthèse) ; `connector.py:200` mélange « SIA 265 Tabellen 45 und 46 give ». Preuve : `probe-*.json`.

### AUD-4-20 | C | pièges du harnais hors écran (information pour les tests)

`QMenu.exec` ne peut pas être bouchonné au niveau de la classe PySide6 (le menu modal s'ouvre et bloque : `p4/menu_probe.py`, sortie 124 après 30 s) ; `processEvents()` ne détruit pas les widgets `deleteLater` d'une reconstruction de fenêtre, ce qui fait récolter l'ancienne langue. Utile pour tout test qui changerait de langue ou ouvrirait un menu contextuel.

## NON FAIT

- **Enregistrer sous un ID déjà pris, dynamiquement, dans « Modèles statiques », « Connecteurs » et « Moments polaires »** : le harnais écrivait l'ID dans `identity.id` d'un brouillon « Nouveau », que ces onglets ne relisent pas avant `save` ; l'enregistrement a créé S01…S07 dans le bac à sable au lieu du refus. Vérifié statiquement : `statics_tab.py:2316` `st_id_exists`, `connectors_tab.py:1958/1961` `cn_taken`, `catalog_gui.py:2489` `polar_id_exists`, tous via `self.t` et présents dans les trois langues.
- **Captures de tous les états** : seules les 24 captures « état par défaut » à 1400 × 780 ont été regardées (plus 0 des 51 captures 900 × 780 de la récolte, qui montrent la largeur minimale de la fenêtre) ; les états sélection, outils, dialogues ont été vérifiés par le texte récolté, non à l'œil.
- **Menu contextuel des champs de saisie Qt** (Annuler, Couper, Copier…) : non récolté ; relève d'AUD-4-2.
- Thème sombre de Windows : hors écran, non vérifiable.

## Vérifications manuelles proposées à l'ingénieur

1. Katalog en français, onglet « Moments polaires » : modifier un calcul puis en choisir un autre → les boutons du dialogue s'appellent « Save / Discard / Cancel » (AUD-4-2).
2. Onglet « Schémas » : promener la souris sur une pièce avec l'accrochage → le relevé en bas à gauche montre « [midpoint] », « [ray|…] » (AUD-4-1).
3. Onglet « Connecteurs », VU-SD-10, « Tout décocher » → « Pas de résistance : Kein Verbindungsmittel… » ; cocher « Écraser le compte du dessin » avec une autre valeur → avertissement jaune en allemand (AUD-4-3, 4-4).
4. Survoler « Bois – bois à sections multiples » (grisé) dans la liste « Assemblage » → infobulle allemande (AUD-4-5).
5. Onglet « Schémas », outil « Sélection », cliquer « Grille… » → boîte d'erreur `KeyError: 'kind'` (AUD-4-10).
6. En anglais : lire le titre de l'onglet « Connections » et la liste « Connectors » à côté (AUD-4-12).

## Contrôles qui pourraient devenir des tests

- `test_i18n` : chaque clé de `STRINGS` est lue (scan AST + préfixes dynamiques déclarés) — AUD-4-9.
- `test_i18n` : traducteur Qt installé, bouton « Save » d'une `QMessageBox` traduit dans chaque langue — AUD-4-2.
- `test_i18n` : chaque phrase allemande littérale de `connector.py`/`dowel.py` est traduite par `strings.translate` en fr et en (générique, `p4/connector_messages.py`) — AUD-4-4.
- `test_connectors` : avertissement d'un n_tot écrasé traduit dans la fenêtre fr ; infobulles des assemblages désactivés non allemandes en fr/en — AUD-4-3, 4-5.
- `test_schema_tab` : relevé du pointeur traduit et sans `|` ; « Grille… » avec l'outil Sélection — AUD-4-1, 4-10.
- Test de récolte allégé : pour chaque onglet et langue, aucun texte visible (hors données, `///` et liste blanche) n'est identique dans les trois langues ; nécessite `sendPostedEvents(DeferredDelete)` et une sous-classe de `QMenu` (AUD-4-20).
