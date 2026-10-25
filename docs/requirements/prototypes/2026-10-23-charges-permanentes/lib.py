"""The material library of the prototype: SIA 261 Anhang A (Tabellen 28, 29, 30, the norm files of Woodcore, French names read on the French edition p. 77-78) and the workbook library (calc/libraries/materials-library.json, «Externe»), merged by name and weight."""
import json, pathlib, re
W = pathlib.Path(__file__).resolve().parents[4]  # the repository
out = []
def add(**k): out.append(k)
# --- SIA 261, Tabelle 28 (kN/m³): id of the norm file -> (fr, en, family)
T28 = {
 "aluminium": ("Aluminium", "Aluminium", "metal"), "baustahl": ("Acier", "Steel", "metal"),
 "beton_unbewehrt": ("Béton non armé", "Concrete, plain", "conc"), "beton_bewehrt": ("Béton armé", "Concrete, reinforced", "conc"),
 "holz_nadelhoelzer_allgemein": ("Bois résineux en général", "Softwood, general", "wood"), "holz_laubhoelzer_allgemein": ("Bois feuillus en général", "Hardwood, general", "wood"),
 "holz_verleimte_nadelhoelzer": ("Bois résineux collés", "Glued softwood", "wood"), "holz_spanplatten": ("Panneaux en bois aggloméré", "Particle board", "board"),
 "natursteinmauerwerk_bruchstein_kalkstein": ("Maçonnerie en moellons (calcaire)", "Rubble masonry (limestone)", "conc"), "natursteinmauerwerk_granit": ("Maçonnerie en granite", "Granite masonry", "conc"),
 "natursteinmauerwerk_basalt": ("Maçonnerie en basalte", "Basalt masonry", "conc"), "natursteinmauerwerk_molasse_sandstein": ("Maçonnerie en molasse, grès", "Molasse, sandstone masonry", "conc"),
 "moertelueberzuege_kalkmoertel": ("Mortier de chaux", "Lime mortar", "gyps"), "moertelueberzuege_zementmoertel": ("Mortier de ciment", "Cement mortar", "gyps"),
 "moertelueberzuege_gipsmoertel": ("Mortier de plâtre", "Gypsum mortar", "gyps"), "moertelueberzuege_wandverputz_aussen": ("Crépi mural extérieur", "External render", "gyps"),
 "moertelueberzuege_wandverputz_innen": ("Crépi mural intérieur", "Internal plaster", "gyps"),
 "mauerwerk_unverputzt_backsteine_voll": ("Briques de terre cuite pleines", "Clay bricks, solid", "conc"), "mauerwerk_unverputzt_backsteine_gelocht": ("Briques de terre cuite perforées", "Clay bricks, perforated", "conc"),
 "mauerwerk_unverputzt_backsteine_schalldaemmend": ("Briques à haute isolation phonique", "Sound-insulating bricks", "conc"), "mauerwerk_unverputzt_sichtbacksteine_gelocht": ("Briques apparentes perforées", "Facing bricks, perforated", "conc"),
 "mauerwerk_unverputzt_zementsteine_voll": ("Agglomérés de béton pleins", "Concrete blocks, solid", "conc"), "mauerwerk_unverputzt_zementsteine_gelocht": ("Agglomérés de béton perforés", "Concrete blocks, perforated", "conc"),
 "mauerwerk_unverputzt_zementsteine_schalldaemmend": ("Agglomérés isolants phoniquement", "Sound-insulating concrete blocks", "conc"), "mauerwerk_unverputzt_kalksandsteine_voll": ("Briques silico-calcaires pleines", "Sand-lime bricks, solid", "conc"),
 "mauerwerk_unverputzt_kalksandsteine_gelocht": ("Briques silico-calcaires perforées", "Sand-lime bricks, perforated", "conc"), "mauerwerk_unverputzt_gasbetonsteine_normale_qualitaet": ("Béton cellulaire, qualité normale", "Aerated concrete, normal", "conc"),
 "mauerwerk_unverputzt_gasbetonsteine_hochwertig": ("Béton cellulaire, haute qualité", "Aerated concrete, high grade", "conc"), "mauerwerk_unverputzt_glasbausteine_voll": ("Briques de verre pleines", "Glass blocks, solid", "metal"),
 "mauerwerk_unverputzt_glasbausteine_hohl": ("Briques de verre creuses", "Glass blocks, hollow", "metal"), "mauerwerk_unverputzt_zelltonplatten": ("Plaques d'argile cellulaire", "Cellular clay slabs", "conc"),
 "mauerwerk_unverputzt_gipsplatten": ("Plaques de plâtre", "Gypsum boards", "gyps"), "bodenbelaege_keramikplatten": ("Dallage en céramique", "Ceramic tiles", "floor"),
 "bodenbelaege_natursteine": ("Revêtement en pierre naturelle", "Natural stone flooring", "floor"), "bodenbelaege_holzparkett_geklebt": ("Parquet en bois collé", "Glued wood parquet", "floor"),
 "bodenbelaege_linoleum": ("Linoléum", "Linoleum", "floor"), "bituminoese_belaege_gussasphalt": ("Asphalte coulé", "Mastic asphalt", "floor"),
 "bituminoese_belaege_bituminoeser_belag_hmt": ("Revêtement bitumineux (HMT)", "Bituminous surfacing (HMT)", "floor"),
}
T29 = {
 "faserzement": ("Ciment armé de fibres", "Fibre cement", "tile"), "profilbleche_hoehe_80_mm_dicke_0_8_mm_stahlblech": ("Tôles profilées en acier, h = 80, d = 0,8 mm", "Profiled steel sheets, h 80, t 0.8 mm", "metal"),
 "profilbleche_hoehe_80_mm_dicke_0_8_mm_aluminiumblech": ("Tôles profilées en aluminium, h = 80, d = 0,8 mm", "Profiled aluminium sheets, h 80, t 0.8 mm", "metal"),
 "faserzementschieferdach_einfachdeckung": ("Ardoise fibres-ciment, recouvrement simple", "Fibre-cement slates, single lap", "tile"), "faserzementschieferdach_doppeldeckung": ("Ardoise fibres-ciment, recouvrement double", "Fibre-cement slates, double lap", "tile"),
 "tonziegeldach_inkl_lattung_biberschwanz_doppeldeckung": ("Tuiles plates en terre cuite, recouvrement double, lattis compris", "Clay plain tiles, double lap, battens incl.", "tile"),
 "tonziegeldach_inkl_lattung_pfannenziegel": ("Tuiles flamandes en terre cuite, lattis compris", "Clay pantiles, battens incl.", "tile"),
 "betonziegeldach_inkl_lattung_flachziegel": ("Tuiles plates en béton, lattis compris", "Concrete plain tiles, battens incl.", "tile"),
 "betonziegeldach_inkl_lattung_pfannenziegel": ("Tuiles flamandes en béton, lattis compris", "Concrete pantiles, battens incl.", "tile"),
 "unterdaecher_schindelunterzug": ("Sous-toiture en bardeaux", "Shingle underlay", "board"), "unterdaecher_hartfaserplatten": ("Sous-toiture en panneaux de fibres durs", "Hardboard underlay", "board"),
 "unterdaecher_faserzementplatten": ("Sous-toiture en panneaux fibres-ciment", "Fibre-cement underlay", "board"),
 "unterdaecher_holzschalung_24_mm_inkl_eine_lage_bitumenpappe_oder_kunststofffolie": ("Lambris de 24 mm, y.c. carton bitumé ou feuille plastique", "24 mm boarding incl. bitumen felt or foil", "wood"),
 "verglasung_inkl_rahmenkonstruktion_normalglas_5_mm": ("Vitrage, verre normal 5 mm, châssis compris", "Glazing, 5 mm glass incl. frame", "metal"),
 "verglasung_inkl_rahmenkonstruktion_armiertes_glas_6_mm": ("Vitrage, verre armé 6 mm, châssis compris", "Glazing, 6 mm wired glass incl. frame", "metal"),
 "feinkiesauflage_pro_10_mm_dicke": ("Gravillon, par 10 mm d'épaisseur", "Fine gravel, per 10 mm", "fill"), "bitumenpappe_pro_lage": ("Carton bitumé, par couche", "Bitumen felt, per layer", "memb"),
 "kunststofffolie": ("Feuille plastique", "Plastic foil", "memb"), "moertelueberzuege": ("Enduits de mortier", "Mortar coatings", "gyps"),
}
def norm_rows(f, key, col):
    t = json.load(open(W / "calc/norms" / f))[key]
    return t["rows"]
for r in norm_rows("sia261-2020-tab28-raumlasten-baustoffe.json", "table_28", "raumlast"):
    if r["raumlast"] is None: continue
    fr, en, fam = T28[r["id"]]
    de = (r["group"] + ", " + r["name"]) if r["group"] and r["group"] not in ("Bodenbeläge", "Mörtelüberzüge") else r["name"]
    add(id="sia28-" + r["id"], de=de, fr=fr, en=en, fam=fam, v=r["raumlast"], u="kN/m³", src="sia", ref="SIA 261:2020, tableau 28, p. 77")
for r in norm_rows("sia261-2020-tab29-flaechenlasten-bedachungen.json", "table_29", "flaechenlast"):
    fr, en, fam = T29[r["id"]]
    de = (r["group"] + ", " + r["name"]) if r["group"] else r["name"]
    if r["id"] == "feinkiesauflage_pro_10_mm_dicke":
        add(id="sia29-" + r["id"], de=de, fr=fr, en=en, fam=fam, v=20, u="kN/m³", src="sia", ref="SIA 261:2020, tableau 29, p. 78 : 0,20 kN/m² par 10 mm, soit 20 kN/m³"); continue
    add(id="sia29-" + r["id"], de=de, fr=fr, en=en, fam=fam, v=r["flaechenlast"], u="kN/m²", src="sia", ref="SIA 261:2020, tableau 29, p. 78")
T30 = [("sable", "Sand", "Sable", "Sand", 15), ("tout", "Kies-Sand-Gemisch", "Tout venant, mélangé", "Gravel-sand mix", 20), ("ballast", "Schotter, gebrochen", "Ballast, concassé", "Crushed ballast", 18), ("terre_s", "Erde, trocken", "Terre, sèche", "Soil, dry", 16), ("terre_h", "Erde, feucht", "Terre, humide", "Soil, moist", 21)]
for i, de, fr, en, v in T30: add(id="sia30-" + i, de=de, fr=fr, en=en, fam="fill", v=v, u="kN/m³", src="sia", ref="SIA 261:2020, tableau 30, p. 78")
# --- the workbook library (Externe): name -> (fr, en, family)
X = {
 "Parkett Hartholz": ("Parquet bois dur", "Hardwood parquet", "floor"), "Natursteinboden": ("Sol en pierre naturelle", "Natural stone floor", "floor"), "Keramikplatten": ("Carrelage céramique", "Ceramic tiles", "floor"),
 "Steinholzböden": ("Sol en xylolithe", "Magnesite-wood floor", "floor"), "Anhydritestrich": ("Chape anhydrite", "Anhydrite screed", "conc"), "Bodenriemen Fi/Ta": ("Lames de plancher épicéa/sapin", "Spruce/fir floorboards", "wood"),
 "Zement UB": ("Chape ciment", "Cement screed", "conc"), "Linoleum": ("Linoléum", "Linoleum", "floor"), "Gussasphalt": ("Asphalte coulé", "Mastic asphalt", "floor"),
 "Hartbeton leichtbeansprucht": ("Béton dur, faible sollicitation", "Hard concrete, light duty", "conc"), "Hartbeton schwerbeansprucht": ("Béton dur, forte sollicitation", "Hard concrete, heavy duty", "conc"),
 "3-Schichtplatte": ("Panneau trois plis", "Three-layer board", "board"), "Haltopex (Walo)": ("Haltopex (Walo)", "Haltopex (Walo)", "floor"), "Magnesit UB": ("Chape magnésie", "Magnesite screed", "conc"),
 "Spanplatten": ("Panneaux de particules", "Particle boards", "board"), "OSB-Platten": ("Panneaux OSB", "OSB boards", "board"), "Fermacell Estrich": ("Chape sèche Fermacell", "Fermacell dry screed", "gyps"),
 "Duripanel": ("Duripanel", "Duripanel", "board"), "Blindboden Tanne": ("Faux plancher sapin", "Fir subfloor", "wood"), "Blindboden Fi/Ta": ("Faux plancher épicéa/sapin", "Spruce/fir subfloor", "wood"),
 "Stahlbeton (Holzbetonverbund)": ("Béton armé (mixte bois-béton)", "Reinforced concrete (timber-concrete)", "conc"), "Flumroc Trittschall": ("Flumroc phonique", "Flumroc impact sound", "ins"),
 "Isover Trittschall PS81": ("Isover phonique PS81", "Isover impact sound PS81", "ins"), "Weichfaserplatte Pavapor": ("Panneau fibres tendres Pavapor", "Softboard Pavapor", "ins"),
 "Isover uniroll": ("Isover uniroll", "Isover uniroll", "ins"), "Isover PBM 032 / 034": ("Isover PBM 032 / 034", "Isover PBM 032 / 034", "ins"), "Isover Isolene P": ("Isover Isolene P", "Isover Isolene P", "ins"),
 "Flumroc Typ 1": ("Laine de roche Flumroc 1", "Flumroc stone wool 1", "ins"), "Flumroc Typ 3": ("Laine de roche Flumroc 3", "Flumroc stone wool 3", "ins"), "Flumroc Solo": ("Laine de roche Flumroc Solo", "Flumroc Solo", "ins"),
 "Weichfaserplatte Pavatherm": ("Panneau fibres tendres Pavatherm", "Softboard Pavatherm", "ins"), "Weichfaserplatte Thermoflex": ("Fibre de bois Thermoflex", "Wood fibre Thermoflex", "ins"),
 "Zellulosefaserplatte FlexCL": ("Panneau cellulose FlexCL", "Cellulose board FlexCL", "ins"), "Zellulosefasern 1": ("Ouate de cellulose 1", "Cellulose fibre 1", "ins"), "Zellulosefasern 2": ("Ouate de cellulose 2", "Cellulose fibre 2", "ins"),
 "Schlacke": ("Scories", "Slag", "fill"), "Kalksplittschüttung trocken": ("Gravillon calcaire sec", "Dry limestone chippings", "fill"), "Flumroc prima": ("Laine de roche Flumroc prima", "Flumroc prima", "ins"),
 "PUR / PIR Dämmung": ("Isolant PUR / PIR", "PUR / PIR insulation", "ins"), "OSB3": ("Panneau OSB/3", "OSB/3 board", "board"), "Kerto-T": ("LVL Kerto-T", "LVL Kerto-T", "wood"), "Kerto-S": ("LVL Kerto-S", "LVL Kerto-S", "wood"),
 "Kerto-Q": ("LVL Kerto-Q", "LVL Kerto-Q", "wood"), "Schalung": ("Lambris, coffrage", "Boarding", "wood"), "Fermacell": ("Plaque fibres-gypse Fermacell", "Fermacell gypsum fibre board", "gyps"),
 "Rigips": ("Plaque de plâtre", "Plasterboard", "gyps"), "Sperrholzplatte": ("Contreplaqué", "Plywood", "board"), "Weichfaserplatte": ("Panneau fibres tendres", "Softboard", "board"),
 "Heraklith-BM": ("Heraklith-BM", "Heraklith-BM", "board"), "Kalk, Kalkzementputz": ("Enduit chaux, chaux-ciment", "Lime, lime-cement plaster", "gyps"), "Gipsdecke auf Lättli": ("Plafond plâtre sur lattis", "Plaster ceiling on laths", "gyps"),
 "Substrat nass": ("Substrat humide (végétalisation)", "Wet substrate (green roof)", "fill"), "Ziegelschrot": ("Brique concassée", "Crushed brick", "fill"), "Gartenplatten": ("Dalles de jardin", "Garden slabs", "floor"),
 "Kiesauflage": ("Gravier de toiture", "Roof gravel", "fill"), "Natursteinplatten": ("Dalles en pierre naturelle", "Natural stone slabs", "floor"), "Erde": ("Terre", "Soil", "fill"), "Sand": ("Sable", "Sand", "fill"),
 "Granit": ("Granite", "Granite", "conc"), "Bruchstein": ("Moellons", "Rubble stone", "conc"), "Blech Aluminium 2mm": ("Tôle aluminium 2 mm", "Aluminium sheet 2 mm", "metal"),
 "Blech Kupfer 2mm": ("Tôle cuivre 2 mm", "Copper sheet 2 mm", "metal"), "Blech Stahl 2mm": ("Tôle acier 2 mm", "Steel sheet 2 mm", "metal"), "xps Roofmate": ("XPS Roofmate", "XPS Roofmate", "ins"),
 "Lärchenrost": ("Caillebotis mélèze", "Larch decking", "wood"), "Gummischrotmatte": ("Natte en granulat de caoutchouc", "Rubber granulate mat", "memb"), "PV-Anlage": ("Installation photovoltaïque", "PV system", "metal"),
 "GL24h": ("Lamellé-collé GL24h", "Glulam GL24h", "wood"), "C24": ("Bois massif C24", "Solid timber C24", "wood"), "Fi/Ta": ("Épicéa/sapin", "Spruce/fir", "wood"), "Eiche": ("Chêne", "Oak", "wood"),
 "Buche": ("Hêtre", "Beech", "wood"), "Robinie": ("Robinier", "Robinia", "wood"), "Kastanie": ("Châtaignier", "Chestnut", "wood"), "Stahlbeton": ("Béton armé", "Reinforced concrete", "conc"),
 "Mauerwerk BN": ("Maçonnerie BN", "Masonry BN", "conc"), "Fi/Ta auf Federbügel": ("Épicéa/sapin sur suspentes élastiques", "Spruce/fir on resilient hangers", "wood"), "Lehmsteine Lecca": ("Briques de terre crue Lecca", "Clay blocks Lecca", "fill"),
 "Lehmsteine Voll-Lehm": ("Briques de terre crue pleines", "Solid clay blocks", "fill"), "Kies": ("Gravier", "Gravel", "fill"), "Liapor (Lecca)": ("Argile expansée Liapor", "Expanded clay Liapor", "fill"),
 "Fermacell Ausgleichsschüttung": ("Granulat d'égalisation Fermacell", "Fermacell levelling fill", "fill"), "Fermacell Wabenschüttung": ("Granulat nid d'abeille Fermacell", "Fermacell honeycomb fill", "fill"),
 "Fermacell Gebundene Schüttung": ("Granulat lié Fermacell", "Fermacell bonded fill", "fill"), "Biberschw. einf.": ("Tuiles plates, recouvrement simple", "Plain tiles, single lap", "tile"),
 "Biberschw. Doppelt": ("Tuiles plates, recouvrement double", "Plain tiles, double lap", "tile"), "Betonziegel": ("Tuiles en béton", "Concrete tiles", "tile"), "Pfannenziegel": ("Tuiles flamandes", "Pantiles", "tile"),
 "Welleternit": ("Plaques ondulées fibres-ciment", "Corrugated fibre cement", "tile"), "Eternitschiefer": ("Ardoises fibres-ciment", "Fibre-cement slates", "tile"), "Glas": ("Verre", "Glass", "metal"),
 "Scobalit": ("Scobalit", "Scobalit", "tile"), "Aluwellblech": ("Tôle ondulée aluminium", "Corrugated aluminium", "metal"), "Profilblech": ("Tôle profilée", "Profiled sheet", "metal"),
 "Dachpappe": ("Carton bitumé", "Bitumen felt", "memb"), "EPDM": ("Lé EPDM", "EPDM membrane", "memb"), "Sarnafil": ("Lé Sarnafil", "Sarnafil membrane", "memb"), "Ampack": ("Lé Ampack", "Ampack membrane", "memb"),
 "Polyesterflies": ("Non-tissé polyester", "Polyester fleece", "memb"), "Weichfaserplatte Isoroof": ("Panneau fibres tendres Isoroof", "Softboard Isoroof", "board"),
 "Weichfaserplatte ISOLAIR": ("Panneau fibres tendres ISOLAIR", "Softboard ISOLAIR", "board"), "Faserzement Swisspearl": ("Fibres-ciment Swisspearl", "Swisspearl fibre cement", "board"),
 "Schalung Fi/Ta": ("Lambris épicéa/sapin", "Spruce/fir boarding", "wood"), "Fermacell HD": ("Fermacell HD", "Fermacell HD", "gyps"), "Lärche": ("Mélèze", "Larch", "wood"), "Eternit": ("Fibres-ciment Eternit", "Eternit fibre cement", "board"),
 "Blech Aluminium": ("Tôle aluminium", "Aluminium sheet", "metal"), "Stamisol FA": ("Lé de façade Stamisol FA", "Stamisol FA facade membrane", "memb"), "Stamisol": ("Lé Stamisol", "Stamisol membrane", "memb"),
 "Flammex": ("Lé Flammex", "Flammex membrane", "memb"), "Sisalex": ("Lé Sisalex", "Sisalex membrane", "memb"), "Fassadenbahn": ("Lé de façade", "Facade membrane", "memb"),
}
ROLE_FR = {"Fussboden": "revêtement de sol", "Unterlagsboden": "chape", "Trittschalldämmung": "isolation phonique", "Dämmung": "isolation", "Beplankung": "panneau de contreventement", "Bekleidung": "revêtement intérieur",
 "Konstruktion": "structure", "Lattung": "lattage", "Gefällslattung": "lattage de pente", "Rostung": "lattage croisé", "Dachlattung": "lattes de toiture", "Konterlattung": "contre-lattes", "Fassade": "façade",
 "Beschwerung": "lestage", "Beschichtung": "couche de protection", "Dachhaut": "couverture", "Schutzbahn/Dachhaut": "lé de protection", "Unterdach": "sous-toiture", "Abdeckbahn": "lé de recouvrement",
 "Abdichtung": "étanchéité", "Unterdachbahn": "lé de sous-toiture"}
lib = json.load(open(W / "calc/libraries/materials-library.json"))["materials"]
groups = {}
for x in lib:
    groups.setdefault((x["material"], x["mass"], x["unit"]), []).append(x)
for (name, mass, unit), xs in groups.items():
    fr, en, fam = X[name]
    same = [k for k in groups if k[0] == name]
    if len(same) > 1:
        q = ROLE_FR[xs[0]["ebene"]]; fr = fr + " (" + q + ")"; en = en + " (" + xs[0]["ebene"] + ")"; de = name + " (" + xs[0]["ebene"] + ")"
    else: de = name
    quelle = ", ".join(sorted(set(x["quelle"] for x in xs if x.get("quelle"))))
    sia = quelle.startswith("SIA 261")
    v = mass / 100.0
    add(id="wb-" + re.sub(r"[^a-z0-9]+", "-", (name + "-" + str(mass)).lower()), de=de, fr=fr, en=en, fam=fam, v=v, u="kN/m³" if unit == "kg/m³" else "kN/m²",
        src="sia" if sia else "ext", ref=("Classeur Belastungsannahmen, ligne " + ", ".join(str(x["row"]) for x in xs[:3]) + (" · « " + quelle + " »" if quelle else "")),
        roles=sorted(set(ROLE_FR[x["ebene"]] for x in xs)), info=xs[0].get("info") or "")
# --- two examples of an engineer's own library (Personnel), kept on his machine
add(id="perso-3s-meleze", de="Dreischichtplatte Lärche (Muster)", fr="Panneau trois plis mélèze (exemple)", en="Three-layer larch board (example)", fam="board", v=5.2, u="kN/m³", src="perso", ref="Bibliothèque personnelle · exemple saisi pour le prototype")
add(id="perso-installations", de="Installationen und Innenwände (Muster)", fr="Installations et cloisons (exemple)", en="Services and partitions (example)", fam="direct", v=0.5, u="kN/m²", src="perso", ref="Bibliothèque personnelle · exemple saisi pour le prototype")
add(id="perso-foamglas", de="Schaumglas (Muster)", fr="Verre cellulaire (exemple)", en="Cellular glass (example)", fam="ins", v=1.15, u="kN/m³", src="perso", ref="Bibliothèque personnelle · exemple saisi pour le prototype, 115 kg/m³ à vérifier sur la fiche du fabricant")
# the tiles SIA 261 Tabelle 29 weighs with their battens, and the workbook's own entry of the same weight
for x in out:
    if x["id"] in ("sia29-tonziegeldach_inkl_lattung_pfannenziegel", "sia29-tonziegeldach_inkl_lattung_biberschwanz_doppeldeckung", "sia29-betonziegeldach_inkl_lattung_flachziegel", "sia29-betonziegeldach_inkl_lattung_pfannenziegel"): x["battens"] = "norm"
    if x["id"] == "wb-pfannenziegel-47": x["battens"] = "same"
json.dump(out, open(pathlib.Path(__file__).parent / "lib.json", "w"), ensure_ascii=False)
import collections
print(len(out), collections.Counter(x["src"] for x in out), collections.Counter(x["fam"] for x in out))
