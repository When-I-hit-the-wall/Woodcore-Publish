"""The compositions of the prototype: the project's three, and the templates read in Lignum, «Holzbau mit System» (2023). Every layer names a material of lib.json by its German name and weight."""
import json, pathlib
H = pathlib.Path(__file__).parent
LIB = json.load(open(H / "lib.json"))
def m(de, v=None):
    xs = [x for x in LIB if (x["de"] == de or x["de"].split(" (")[0] == de) and (v is None or abs(x["v"] - v) < 1e-9)]
    assert len(xs) >= 1, (de, v, [x["de"] for x in LIB if de.split()[0] in x["de"]])
    return xs[0]["id"]
def L(mat, pose, k="a", t=None, b=None, e=None, link=False, role=None, count="full", note=None):
    d = {"mat": mat, "pose": pose, "k": k, "t": t, "b": b, "e": e, "link": link, "role": role, "count": count}
    if note: d["note"] = note
    return d
C24, FITA, R5 = m("C24", 5), m("Fi/Ta", 5), m("Bois résineux collés".replace("Bois résineux collés", "Holz, verleimte Nadelhölzer"))
TPL = [
 {"id": "T-toit-entre", "kind": "roof", "fr": "Toiture inclinée, isolée entre chevrons", "de": "Geneigtes Dach, zwischengedämmt", "en": "Pitched roof, insulated between rafters",
  "src": "Lignum, Holzbau mit System, C4 Geneigte Dächer, tableau 6", "assume": "chevrons 80/220 e = 625, isolation 200, contre-lattes 60/50 e = 625, lattage 50/30 e = 400",
  "layers": [L(m("Tonziegeldach inkl. Lattung, Pfannenziegel"), "surf", role="couverture"), L(C24, "ent", t=50, b=60, e=625, role="contre-lattes"),
             L(m("Unterdächer, Hartfaserplatten"), "surf", role="sous-toiture"), L(C24, "ent", "g", t=220, b=80, e=625, link=True, role="structure"),
             L(m("Flumroc Typ 1"), "cont", t=200, role="isolation"), L(m("Kunststofffolie"), "surf", role="pare-vapeur"),
             L(FITA, "ent", t=30, b=50, e=400, role="lattage"), L(m("Rigips"), "cont", t=15, role="revêtement intérieur")]},
 {"id": "T-toit-sur", "kind": "roof", "fr": "Toiture inclinée, isolée sur chevrons", "de": "Geneigtes Dach, aussen gedämmt", "en": "Pitched roof, insulated above rafters",
  "src": "Lignum, Holzbau mit System, C4 Geneigte Dächer, tableau 10", "assume": "isolation 200 sur lambris 27, chevrons 120/240 e = 1000 apparents",
  "layers": [L(m("Betonziegeldach inkl. Lattung, Pfannenziegel"), "surf", role="couverture"), L(C24, "ent", t=50, b=60, e=625, role="contre-lattes"),
             L(m("Ampack", 0.05), "surf", role="lé de sous-toiture"), L(m("Flumroc Typ 3"), "cont", t=200, role="isolation"),
             L(m("Kunststofffolie"), "surf", role="pare-vapeur"), L(m("Schalung"), "cont", "g", t=27, role="lambris"), L(m("GL24h", 5), "ent", "g", t=240, b=120, e=1000, role="structure")]},
 {"id": "T-toit-plat", "kind": "flat", "fr": "Toit plat compact sur bois massif", "de": "Flachdach, Verbunddach auf Massivholz", "en": "Compact flat roof on solid timber",
  "src": "Lignum, Holzbau mit System, C5 Flachdächer, tableau 13", "assume": "verre cellulaire 200 (matériau personnel), bois massif 100 mm",
  "layers": [L(m("Kiesauflage"), "cont", t=60, role="couche de protection"), L(m("Polyesterflies"), "surf", role="couche de protection"),
             L(m("EPDM", 0.1), "surf", role="étanchéité"), L("perso-foamglas", "cont", t=200, role="isolation"),
             L(m("Dachpappe", 0.05), "surf", role="pare-vapeur"), L(R5, "cont", "g", t=100, role="structure")]},
 {"id": "T-paroi-ossature", "kind": "wall", "fr": "Paroi à ossature bois, façade ventilée", "de": "Holzrahmenbau, hinterlüftet", "en": "Timber-frame wall, ventilated facade",
  "src": "Lignum, Holzbau mit System, A2, figure 24", "assume": "montants 60/240 e = 625, lattage 30/50 e = 600",
  "layers": [L(m("Lärche"), "cont", t=21, role="façade"), L(FITA, "ent", t=30, b=50, e=600, role="lattage"), L(m("Fassadenbahn"), "surf", role="lé de façade"),
             L(m("Fermacell", 12), "cont", t=15, role="panneau de contreventement"), L(C24, "ent", "g", t=240, b=60, e=625, link=True, role="structure"),
             L(m("Flumroc Typ 1"), "cont", t=240, role="isolation"), L(m("OSB3"), "cont", "g", t=15, role="panneau de contreventement"),
             L(m("Fermacell", 12), "cont", t=18, role="revêtement intérieur")]},
 {"id": "T-paroi-clt", "kind": "wall", "fr": "Paroi en bois lamellé-croisé, isolation crépie", "de": "Massivholzbau, Brettsperrholz", "en": "Cross-laminated timber wall, rendered insulation",
  "src": "Lignum, Holzbau mit System, A2, figure 24", "assume": "crépi 15 mm",
  "layers": [L(m("Wandverputz aussen"), "cont", t=15, role="façade"), L(m("Flumroc Typ 3"), "cont", t=200, role="isolation"), L(R5, "cont", "g", t=120, role="structure")]},
 {"id": "T-plancher-sable", "kind": "floor", "fr": "Plancher à solives, sable entre lattes", "de": "Holzbalkendecke, Sand zwischen Lattung", "en": "Joisted floor, sand between battens",
  "src": "Lignum, Holzbau mit System, C7, figure 13, exemple 2, p. 415", "book": 127, "assume": "lattes 50/50 e = 500, solives 140/200 e = 600, sable compté au prorata",
  "layers": [L(m("Spanplatten"), "cont", t=25, role="chape"), L(m("Polyesterflies"), "surf", role="isolation phonique"), L(FITA, "ent", t=50, b=50, e=500, link=True, role="lattage"),
             L(m("Sand", 15), "cont", t=50, role="lestage", count="prorata"), L(m("Polyesterflies"), "surf", role="couche de protection"),
             L(m("Schalung"), "cont", "g", t=21, role="structure"), L(C24, "ent", "g", t=200, b=140, e=600, role="structure")]},
 {"id": "T-plancher-chape", "kind": "floor", "fr": "Plancher à solives, chape ciment", "de": "Holzbalkendecke, Zementestrich", "en": "Joisted floor, cement screed",
  "src": "Lignum, Holzbau mit System, C7, figure 11, exemple 2, p. 415", "book": 150, "assume": "chape 50 mm, solives 140/200 e = 600",
  "layers": [L(m("Zement UB"), "cont", t=50, role="chape"), L(m("Kunststofffolie"), "surf", role="couche de protection"), L(m("Flumroc Trittschall"), "cont", t=15, role="isolation phonique"),
             L(m("Schalung"), "cont", "g", t=21, role="structure"), L(C24, "ent", "g", t=200, b=140, e=600, role="structure")]},
 {"id": "T-plancher-caisson", "kind": "floor", "fr": "Plancher caisson, gravillon entre nervures", "de": "Hohlkastendecke, Kalksplittschüttung", "en": "Box floor, chippings between ribs",
  "src": "Lignum, Holzbau mit System, A2, figure 19", "assume": "nervures 80/200 e = 625 ; gravillon 120 sous 80 mm d'air",
  "layers": [L(m("3-Schichtplatte"), "cont", "g", t=27, role="structure"), L(C24, "ent", "g", t=200, b=80, e=625, link=True, role="structure"),
             L(m("Kalksplittschüttung trocken"), "cont", t=120, role="lestage"), L(m("3-Schichtplatte"), "cont", "g", t=27, role="structure")]},
]
PROJECT = [
 {"id": "AU-01", "kind": "roof", "fr": "Toiture inclinée, tuiles", "desc": "Le cas de la première version : sept couches, chevrons 60/200 e = 625",
  "layers": [L(m("Pfannenziegel"), "surf", role="couverture"), L(C24, "ent", t=24, b=48, e=330, role="lattes de toiture"), L(C24, "ent", t=40, b=60, e=625, role="contre-lattes"),
             L(m("Weichfaserplatte ISOLAIR"), "cont", t=35, role="sous-toiture"), L(C24, "ent", "g", t=200, b=60, e=625, link=True, role="structure"),
             L(m("Flumroc Typ 1"), "cont", t=200, role="isolation"), L(m("Rigips"), "cont", t=12.5, role="revêtement intérieur")]},
]
for k in ("T-plancher-sable", "T-paroi-ossature"):
    t = [x for x in TPL if x["id"] == k][0]; p = dict(t); p["id"] = {"T-plancher-sable": "PL-01", "T-paroi-ossature": "PA-01"}[k]; p["from"] = k; PROJECT.append(p)
json.dump({"templates": TPL, "project": PROJECT}, open(H / "comps.json", "w"), ensure_ascii=False)
print(len(TPL), len(PROJECT))
