"""A model table export in the shape RFEM 6.15's own *Fichier → Exporter → Tableaux* writes it, as an XLSX workbook or as a folder of CSVs.

Reproduces `Musterprojekt/01_29509-Model.xlsx` in miniature and to the byte where it matters: **two header rows** with a spanning group row, units in brackets, a newline inside a header cell (`Nœud\\nn°`), RFEM's `--` for an empty cell, **an empty row carrying the number of a deleted object**, **a list of object numbers written as a range** (`2-4`), and **the loads on one sheet per load case** whose prefix is the load case's own localised id (`CC1 -` in French, `LF1 -` in German, `LC1 -` in English).

Its **German** headers deliberately break a word at a hyphen (`Last-
fall`), which the French export does not: it is what exercises `fold`'s hyphenation rule, and it is written down here as defensive rather than observed.

Every oddity here was observed on that export, not invented; `calc/rfem_import/model_tables.py` says where each came from. A test writes its own workbook rather than pointing at the engineer's, for the reason `tests/fixtures/workbook.py` already gives: his file is project data, it is not in the repository, and a defect has to be *put into* a file to check that the reader reports it.

The model it describes is deliberately the shape of his: two static systems that share no node, one of them named by a comment on a **node** rather than on a member.
"""

# The words RFEM writes, per language. The French is read off the engineer's own export; the German and the English are read off `DE.xlsx` and `EN.xlsx` of 26.09.2026, so a test in those languages is a test against RFEM's own words and no longer against a guess.
WORDS = {
    "fr": {
        "nodes": "Nœuds", "lines": "Lignes", "members": "Barres", "sections": "Sections",
        "supports": "Appuis nodaux", "hinges": "Articulations de barre",
        "cases": "Cas de charge", "combinations": "Combinaisons de charges",
        "member_loads": "Charges de barre", "nodal_loads": "Charges nodales",
        "case_prefix": "CC", "comment": "Commentaire", "name": "Nom",
        "node_no": "Nœud\nn°", "node_coords": "Coordonnées globales", "node_local": "Coordonnées", "node_ref": "Nœud de référence",
        "line_no": "Ligne\nn°", "line_nodes": "Nœuds n°", "line_type": "Type de ligne",
        "member_no": "Barre\nn°", "member_line": "Ligne", "member_type": "Type de barre",
        "section_group": "Section", "start": "Début i", "end": "Fin j", "hinge_group": "Articulation",
        "length": "Longueur", "cs_no": "Section\nn°", "cs_name": "Nom de la section",
        "cs_members": "Assigné aux barres n°", "cs_material": "Matériau",
        "cs_dims": "Dimensions générales", "cs_b": "Largeur b", "cs_h": "Hauteur h",
        "support_no": "Appui\nn°", "support_nodes": "Assigné aux nœuds n°",
        "spring_group": "Appui/ressort de transl.", "rot_group": "Maintien/ressort de rotat.",
        "hinge_no": "Articul.\nn°", "release_group": "Libération/ressort de translation",
        "hinge_rot_group": "Libération/ressort de rotation",
        "case_no": "Cas de\ncharge", "category": "Catégorie d'action", "duration": "Durée de charge",
        "combination_no": "Comb.\ncharges", "situation": "Situation de projet", "factor": "Facteur",
        "no": "n°", "load_members": "Assignée aux barres n°", "load_nodes": "Assigné aux nœuds n°",
        "load_type": "Type de charge", "load_distribution": "Répartition de charge",
        "direction_group": "Direction", "direction": "de charge", "p": "p",
        "permanent": "Permanent", "variable": "Neige/glace", "beam": "Poutre", "polyline": "Polyligne",
        "force": "Force", "uniform": "Uniforme",
        "forces": "Efforts internes", "section_no": "Section\nn°", "member_col": "Barre",
        "node_col": "Nœud", "location": "Emplacement", "forces_group": "Forces",
        "moments_group": "Moments", "corresponding": "Chargement correspondant",
        "member_trailer": "Section (matériau) | Commentaire sur la barre",
    },
    "de": {
        "nodes": "Knoten", "lines": "Linien", "members": "Stäbe", "sections": "Querschnitte",
        "supports": "Knotenlager", "hinges": "Stabendgelenke",
        "cases": "Lastfälle", "combinations": "Lastkombinationen",
        "member_loads": "Stablasten", "nodal_loads": "Knotenlasten",
        "case_prefix": "LF", "comment": "Kommentar", "name": "Name des Materials",
        "node_no": "Knoten\nNr.", "node_coords": "Globale Koordinaten", "node_local": "Koordinaten", "node_ref": "Bezugsknoten",
        "line_no": "Linie\nNr.", "line_nodes": "Knoten Nr.", "line_type": "Linientyp",
        "member_no": "Stab\nNr.", "member_line": "Linie", "member_type": "Stabtyp",
        "section_group": "Querschnitt", "start": "Anfang i", "end": "Ende j", "hinge_group": "Gelenk",
        "length": "Länge", "cs_no": "Quersch.\nNr.", "cs_name": "Name des Querschnitts",
        "cs_members": "Zugewiesen an Stäbe Nr.", "cs_material": "Material",
        "cs_dims": "Allgemeine Abmessungen", "cs_b": "Breite b", "cs_h": "Höhe h",
        "support_no": "Lager\nNr.", "support_nodes": "Zugewiesen an Knoten Nr.",
        "spring_group": "Lager/Federung", "rot_group": "Einspannung/Drehfederung",
        "hinge_no": "Gelenk\nNr.", "release_group": "Freigabe/Federung",
        "hinge_rot_group": "Freigabe/Drehfederung",
        "case_no": "Last-\nfall", "category": "Einwirkungskategorie", "duration": "Lasteinwirkungsdauer",
        "combination_no": "Last-\nkombin.", "situation": "Bemessungssituation", "factor": "Faktor",
        "no": "Nr.", "load_members": "Zugewiesen an Stäbe Nr.", "load_nodes": "Zugewiesen an Knoten Nr.",
        "load_type": "Lastart", "load_distribution": "Lastverteilung",
        "direction_group": "Last-", "direction": "richtung", "p": "p",
        "permanent": "Ständig", "variable": "Schnee/Eis", "beam": "Träger", "polyline": "Polylinie",
        "force": "Kraft", "uniform": "Konstant",
        "forces": "Schnittgrössen", "section_no": "Quersch.\nNr.", "member_col": "Stab",
        "node_col": "Knoten", "location": "Stelle", "forces_group": "Kräfte",
        "moments_group": "Momente", "corresponding": "Zugehörige Belastung",
        "member_trailer": "Querschnitt (Material) | Kommentar zum Stab",
    },
    "en": {
        "nodes": "Nodes", "lines": "Lines", "members": "Members", "sections": "Cross-Sections",
        "supports": "Nodal Supports", "hinges": "Member Hinges",
        "cases": "Load Cases", "combinations": "Load Combinations",
        "member_loads": "Member Loads", "nodal_loads": "Nodal Loads",
        "case_prefix": "LC", "comment": "Comment", "name": "Material Name",
        "node_no": "Node\nNo.", "node_coords": "Global Coordinates", "node_local": "Coordinates", "node_ref": "Reference Node",
        "line_no": "Line\nNo.", "line_nodes": "Nodes No.", "line_type": "Line Type",
        "member_no": "Member\nNo.", "member_line": "Line", "member_type": "Member Type",
        "section_group": "Cross-Section", "start": "Start i", "end": "End j", "hinge_group": "Hinge",
        "length": "Length", "cs_no": "Section\nNo.", "cs_name": "Cross-Section Name",
        "cs_members": "Assigned to Members No.", "cs_material": "Material",
        "cs_dims": "General Dimensions", "cs_b": "Width b", "cs_h": "Depth h",
        "support_no": "Support\nNo.", "support_nodes": "Assigned to Nodes No.",
        "spring_group": "Support/Spring", "rot_group": "Restraint/Spring",
        "hinge_no": "Hinge\nNo.", "release_group": "Release/Spring",
        "hinge_rot_group": "Rotational Release/Spring",
        "case_no": "Load\nCase", "category": "Action Category", "duration": "Load Duration",
        "combination_no": "Load\nCombs.", "situation": "Design Situation", "factor": "Factor",
        "no": "No.", "load_members": "Assigned to Members No.", "load_nodes": "Assigned to Nodes No.",
        "load_type": "Load Type", "load_distribution": "Load Distribution",
        "direction_group": "Load", "direction": "Direction", "p": "p",
        "permanent": "Permanent", "variable": "Snow/Ice", "beam": "Beam", "polyline": "Polyline",
        "force": "Force", "uniform": "Uniform",
        "forces": "Internal Forces", "section_no": "Cross-Section\nNo.", "member_col": "Member",
        "node_col": "Node", "location": "Location", "forces_group": "Forces",
        "moments_group": "Moments", "corresponding": "Corresponding loading",
        "member_trailer": "Cross-section (material) | Comment on member",
    },
}

NODE_COMMENT = '@model "VU"\n@label "Velo Unterstand"\n@descr "günstige Einwirkung"'
MEMBER_COMMENT = '@position "T001"\n@be 1.7m'
LOAD_COMMENT = '@be 2m\n@note "depuis l\'avant-toit"'


def sheets(lang="fr", results=True):
    """The tables of one small model, as `{sheet name: [row, …]}` -- two header rows first, then the objects."""
    w = WORDS[lang]
    case = w["case_prefix"]
    out = {}

    # ⚠️ Node 3 is a number RFEM lists and no node: a deleted object leaves its row behind, empty.
    # ⚠️ **Two pairs of X/Z columns, which is what RFEM writes: the relative pair, measured from the node's own
    # reference node, then the global one. Both pairs are named X and Z, so a reader that resolves the global
    # column and then asks the table for its *bare* name gets the relative one back. Node 4 below is the trap:
    # relative to node 2 it reads (4.25, 0), and it stands at (4.25, -2.95). The fixture wrote a single pair
    # until v0.99, which is why seven members of the engineer's own model were drawn where they are not -- a
    # bench lying across a bike shelter, and a beam welded onto a structure it does not belong to.
    out[w["nodes"]] = [
        [w["node_no"], "", "", w["node_local"], "", w["node_coords"], "", "", ""],
        ["", "Type", w["node_ref"], "X [m]", "Z [m]", "X [m]", "Z [m]", "Options", w["comment"]],
        ["1", "Standard", "--", "0", "0", "0", "0", "", ""],
        ["2", "Standard", "--", "0", "-2.95", "0", "-2.95", "", ""],
        ["3", "", "", "", "", "", "", "", ""],
        ["4", "Standard", "2", "4.25", "0", "4.25", "-2.95", "", ""],
        ["36", "Standard", "--", "3.5", "-2.95", "3.5", "-2.95", "", NODE_COMMENT],
        ["40", "Standard", "--", "7", "-2.95", "7", "-2.95", "", ""],
        ["50", "Standard", "--", "9", "0", "9", "0", "", ""],
        ["51", "Standard", "--", "9", "-3", "9", "-3", "", ""],
    ]
    out[w["lines"]] = [
        [w["line_no"], "", "", w["length"], "", ""],
        ["", w["line_nodes"], w["line_type"], "L [m]", "Options", w["comment"]],
        ["1", "1,2", w["polyline"], "2.95", "", ""],
        ["2", "2,4", w["polyline"], "4.25", "", ""],
        ["25", "36,40", w["polyline"], "3.5", "", ""],
        ["30", "50,51", w["polyline"], "3", "", ""],
    ]
    # ⚠️ Member 11 is the same trap in the member table -- a number with nothing on it.
    out[w["members"]] = [
        [w["member_no"], w["member_line"], "", w["section_group"], "", w["hinge_group"], "", w["length"], "", ""],
        ["", w["no"], w["member_type"], w["start"], w["end"], w["start"], w["end"], "L [m]", "Options", w["comment"]],
        ["1", "1", w["beam"], "1", "1", "--", "--", "2.95", "", ""],
        ["2", "2", w["beam"], "1", "1", "1", "--", "4.25", "", ""],
        ["11", "", "", "", "", "", "", "", "", ""],
        ["24", "25", w["beam"], "1", "1", "--", "2", "3.5", "", MEMBER_COMMENT],
        ["30", "30", w["beam"], "2", "2", "--", "--", "3", "", ""],
    ]
    # A section's member list carries a range: «1,2,24» on one and «11-13» on the other.
    out[w["sections"]] = [
        [w["cs_no"], "", "", "", w["cs_dims"], "", ""],
        ["", w["cs_name"], w["cs_members"], w["cs_material"], w["cs_b"] + " [mm]", w["cs_h"] + " [mm]", w["comment"]],
        ["1", "R_M1 500/200", "1,2,24", "6 - C24", "500", "200", ""],
        ["2", "R_M1 200/100", "30", "6 - C24", "200", "100", ""],
    ]
    # Support 1 holds three nodes at once, support 2 is a definition assigned to nothing -- both measured on his model.
    out[w["supports"]] = [
        [w["support_no"], "", w["spring_group"], "", "", w["rot_group"], "", ""],
        ["", w["support_nodes"], "Cu,X [kN/m]", "", "Cu,Z [kN/m]", "Cφ,Y [kNm/rad]", "Options", w["comment"]],
        ["1", "1,50,51", "inf", "", "inf", "inf", "", ""],
        ["2", "", "0", "", "inf", "0", "", ""],
        ["3", "2,4", "inf", "", "inf", "0", "", ""],
        # The named structure's own two: a pin and a roller, which is the span its exported moments describe --
        # a bar RFEM holds nowhere is a warning («nothing holds it»), and a figure of one is a beam in mid-air.
        ["4", "36", "inf", "", "inf", "0", "", ""],
        ["5", "40", "0", "", "inf", "0", "", ""],
    ]
    # ⚠️ On a hinge «inf» means *not released*: hinge 1 is a moment release, hinge 2 a rotational spring.
    out[w["hinges"]] = [
        [w["hinge_no"], "", w["release_group"], "", "", w["hinge_rot_group"], "", ""],
        ["", "Système", "Cu,x [kN/m]", "", "Cu,z [kN/m]", "Cφ,y [kNm/rad]", "Options", w["comment"]],
        ["1", "Local", "inf", "", "inf", "0", "", ""],
        ["2", "Local", "inf", "", "inf", "21.672001", "", ""],
    ]
    # ⚠️ A load case's id is «CC1», not a number -- which is what made `data_rows()` drop every one of them.
    out[w["cases"]] = [
        [w["case_no"], "", "", "", "", ""],
        ["", w["name"], w["category"], w["duration"], "Options", w["comment"]],
        [case + "1", "EG + AL", w["permanent"], "Permanente", "", ""],
        [case + "2", "Schnee", w["variable"], "Court terme", "", ""],
    ]
    out[w["combinations"]] = [
        [w["combination_no"], "", "", "", case + ".1", "", case + ".2", "", "", ""],
        ["", w["name"], w["situation"], w["duration"], w["factor"], w["no"], w["factor"], w["no"], "Options", w["comment"]],
        ["CO1", "1.35 * " + case + "1", "SP1 - ELU", "Permanente", "1.35", case + "1", "", "", "", ""],
        ["CO2", "1.35 * " + case + "1 + 1.50 * " + case + "2", "SP1 - ELU", "Court terme",
         "1.35", case + "1", "1.5", case + "2", "", ""],
    ]
    # ⚠️ The loads are one sheet per case, prefixed by the case's own localised id. Load 2 of CC2 names a range.
    out[f"{case}1 - {w['member_loads']}"] = [
        [w["no"], "", "", "", w["direction_group"], w["p"] + " [kN/m]", "", ""],
        ["", w["load_members"], w["load_type"], w["load_distribution"], w["direction"], "", "Options", w["comment"]],
        ["1", "1,2,24", w["force"], w["uniform"], "ZL", "2.5", "", LOAD_COMMENT],
        ["2", "30", w["force"], w["uniform"], "ZL", "0.5", "", ""],
    ]
    out[f"{case}2 - {w['member_loads']}"] = [
        [w["no"], "", "", "", w["direction_group"], w["p"] + " [kN/m]", "", ""],
        ["", w["load_members"], w["load_type"], w["load_distribution"], w["direction"], "", "Options", w["comment"]],
        ["1", "1-2", w["force"], w["uniform"], "ZL", "1.1", "", ""],
    ]
    out[f"{case}1 - {w['nodal_loads']}"] = [
        [w["no"], "", "", "", "Force", "", "", ""],
        ["", w["load_nodes"], w["load_type"], w["direction"], "FX [kN]", "FZ [kN]", "Options", w["comment"]],
        ["1", "40", w["force"], "Z", "", "11.19", "", ""],
    ]
    # A sheet RFEM writes for an object type the model has none of: its header and nothing under it.
    out["Surfaces" if lang != "de" else "Flächen"] = [
        ["Surface n°" if lang != "de" else "Fläche Nr.", "", "", ""],
        ["", "Lignes de contour", "Épaisseur [mm]", w["comment"]],
    ]
    if results:
        out.update(result_sheets(lang))
    return out


# --- the results ---------------------------------------------------------------------------------
#
# A simply supported span under a uniform load, so that the numbers are somebody's arithmetic and not a
# sketch: member 2 is 4.25 m under q = 2.2 kN/m, whence M(x) = q·x·(L−x)/2 and V(x) = q·(L/2 − x). RFEM
# lists a member at its **characteristic points only**, which is the whole reason `diagram_curve.py` exists:
# three rows through a parabola draw a triangle, and the Hermite reconstruction gives the parabola back
# because the shear it also exports is the moment's slope. The fixture is therefore the smallest export on
# which that reconstruction can be exercised at all.
Q, SPAN = 2.2, 4.25
# ⚠️ Member 24 is the **named** structure's one bar -- the only one a report can address -- so it carries a
# span of its own rather than the flat diagram a first draft gave it: what `show-static-model(diagram: true)`
# prints of the example project would otherwise be a straight line.
SPAN_24 = 3.5


def _parabola(x, span=SPAN):
    """`(V_z, M_y)` of a simply supported span at `x`, to RFEM's own six decimals."""
    return round(Q * (span / 2 - x), 6), round(Q * x * (span - x) / 2, 6)


def _force_row(section, member, node, x, forces, trailer):
    """One row of a member-forces sheet: the six forces in RFEM's own column order, N first and M_z last."""
    n, vy, vz, mt, my, mz = forces
    return [section, member, node, f"{x:g}", "", f"{n:g}", f"{vy:g}", f"{vz:g}",
            f"{mt:g}", f"{my:g}", f"{mz:g}", trailer]


def _force_headers(w, last):
    """The two header rows RFEM writes over a member-forces sheet, copied off the engineer's own export.

    ⚠️ The **member** column is headed «n°» alone, the sheet naming «Barre» on the row above — which is why
    `results.forces_of` falls back to the first numeric column rather than trusting `MEMBER_ALIASES`. The
    fixture writes it that way so the fallback is what the tests exercise, as it is on the real export.
    """
    return [
        [w["section_no"], w["member_col"], w["node_col"], w["location"], "",
         w["forces_group"], "", "", w["moments_group"], "", "", last],
        ["", w["no"], w["no"], "x [m]", "",
         "N [kN]", "Vy [kN]", "Vz [kN]", "MT [kNm]", "My [kNm]", "Mz [kNm]", ""],
    ]


def result_sheets(lang="fr"):
    """One combination's distribution and one design situation's extremes, as RFEM writes them.

    ⚠️ **The sheet name is `<loading> | <members> | <internal forces>`**, which Excel cuts at 31 characters —
    «CO1 | Barres | Efforts internes» is 31 exactly, and the German one is cut. That is what `results.loadings_in`
    resolves by prefix and by stem (`_FORCE_WORDS`), so the fixture exercises both without arranging to.
    """
    w = WORDS[lang]
    # The trailing column of a result sheet is «Section (matériau) | Commentaire sur la barre», so the comment
    # the model tables carry is repeated there -- which is why `results` deliberately does not read it
    # (`model_tables` has a clean column for it).
    beam = f'{w["beam"]} | 1 | ' + NODE_COMMENT.replace("\n", " ")
    member = f'{w["beam"]} | 1 | ' + MEMBER_COMMENT.replace("\n", " ")
    out = {}

    # One combination: the distribution, which is what a diagram is drawn from.
    rows = _force_headers(w, w["member_trailer"])
    rows.append(["1", "R_M1 500/200 | 6 - C24", "", "", "", "", "", "", "", "", "", ""])
    rows.append(_force_row("1", "1", "1", 0, (-17.093699, 0, 0, 0, 0, 0), beam))
    rows.append(_force_row("1", "1", "2", 2.95, (-15.10245, 0, 0, 0, 0, 0), beam))
    for x in (0.0, SPAN / 2, SPAN):
        shear, moment = _parabola(x)
        rows.append(_force_row("1", "2", "2" if x == 0 else "4", x, (0, 0, shear, 0, moment, 0), beam))
    # ⚠️ Every number of a member obeys `M' = V`, because `diagram_curve.slope_sign` measures that convention
    # over the whole table and **refuses to reconstruct** where the numbers do not: a first draft of this
    # fixture gave member 24 a shear of +1.1 at one end and −1.1 at the other with a moment of 1.925 between
    # them, which no load produces, and the refusal fired on the whole sheet -- member 2 included.
    for x in (0.0, SPAN_24 / 2, SPAN_24):
        shear, moment = _parabola(x, SPAN_24)
        rows.append(_force_row("1", "24", "36" if x == 0 else "40", x, (-2.5, 0, shear, 0, moment, 0), member))
    out[f'CO1 | {w["members"]} | {w["forces"]}'] = rows

    # One design situation: the extremes, each naming the combination that reached it. ⚠️ Its rows carry a
    # **criterion** where the distribution's carry nothing, and that is the one thing telling the two apart
    # (`results.criterion_at`, `envelopes.is_envelope`).
    rows = _force_headers(w, w["corresponding"])
    rows.append(["1", "R_M1 500/200 | 6 - C24", "", "", "", "", "", "", "", "", "", ""])
    _, peak = _parabola(SPAN / 2)
    _, peak_24 = _parabola(SPAN_24 / 2, SPAN_24)
    shear_24 = _parabola(0, SPAN_24)[0]
    # ⚠️ **Member 24 is the bar of the one named structure**, so it is the bar every `rfem-*` command of the
    # example project addresses -- `T001_1`. A first draft gave extremes for members 1 and 2 only, and the
    # domain came out with one bar and no variable at all.
    for criterion, number, x, forces, loading in (
        ("N", "1", 0.0, (-26.984699, 0, 0, 0, 0, 0), "CO2"),
        ("N", "1", 2.95, (-15.10245, 0, 0, 0, 0, 0), "CO1"),
        ("Vz", "2", 0.0, (0, 0, _parabola(0)[0], 0, 0, 0), "CO1"),
        ("My", "2", SPAN / 2, (0, 0, 0, 0, peak, 0), "CO1"),
        ("My", "2", SPAN / 2, (0, 0, 0, 0, -1.372, 0), "CO2"),
        ("N", "24", 0.0, (-3.375, 0, shear_24, 0, 0, 0), "CO2"),
        ("N", "24", 0.0, (-2.5, 0, shear_24, 0, 0, 0), "CO1"),
        ("Vz", "24", 0.0, (-3.375, 0, round(1.35 * shear_24, 6), 0, 0, 0), "CO2"),
        ("Vz", "24", SPAN_24, (-3.375, 0, round(-1.35 * shear_24, 6), 0, 0, 0), "CO2"),
        ("My", "24", SPAN_24 / 2, (-3.375, 0, 0, 0, round(1.35 * peak_24, 6), 0), "CO2"),
        ("My", "24", SPAN_24 / 2, (-2.5, 0, 0, 0, peak_24, 0), "CO1"),
    ):
        row = _force_row("1", number, "1", x, forces, loading)
        row[4] = criterion
        rows.append(row)
    # ⚠️ RFEM's own column-wise trailer, which names no loading: `envelopes` skips it, since a row that cannot
    # say which combination produced it is a row a report cannot cite.
    rows.append(["", "max/min", "", "", "max", "0", "0", f"{_parabola(0)[0]:g}", "0", f"{peak:g}", "0", ""])
    out[f'SP1 | {w["members"]} | {w["forces"]}'] = rows
    return out


def workbook(path, lang="fr", results=True):
    """The same tables as one XLSX, which is what *Fichier → Exporter → Tableaux* writes in its «XLSX» format.

    ⚠️ Excel truncates a sheet name to 31 characters, exactly as RFEM's export does, so a fixture is also a test of the prefix lookup `Workbook.table` does.
    """
    import openpyxl

    path.parent.mkdir(parents=True, exist_ok=True)
    book = openpyxl.Workbook()
    book.remove(book.active)
    for name, rows in sheets(lang, results).items():
        sheet = book.create_sheet(name[:31])
        for row in rows:
            sheet.append(row)
    book.save(str(path))
    return path


def csv_folder(folder, lang="fr", results=True):
    """The same tables as one CSV per table -- the other format of that dialog: UTF-8 with a BOM, semicolons, CRLF.

    ⚠️ Written through `csv.writer` and not by joining strings, because two cells here carry a **newline**: a header cell («Nœud\\nn°», as RFEM writes it) and every metadata comment, whose one-entry-per-line rule is the whole convention (`metadata_parser`). Joined by hand they would break the row apart; quoted, they survive the round trip, which is what the engineer's own export was verified to do.
    """
    import csv

    folder.mkdir(parents=True, exist_ok=True)
    for name, rows in sheets(lang, results).items():
        # ⚠️ A result table's name carries « | », which Windows forbids in a file name -- and which RFEM's own
        # CSV export does not write either: it names that file «CO1_analyse_statique_barres_efforts_internes.csv».
        # So the separator becomes an underscore, which is one of the three `results._LOADING` reads.
        with open(folder / f"{name.replace(' | ', '_')}.csv", "w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.writer(handle, delimiter=";", lineterminator="\r\n")
            writer.writerows(rows)
    return folder
