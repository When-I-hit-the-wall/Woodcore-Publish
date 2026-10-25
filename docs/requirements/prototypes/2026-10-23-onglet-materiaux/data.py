"""The data of the Materials tab prototype: what Woodcore ships (SIA 265 Tables 8 and 9, SIA 265/1 Table 19a/b, the weights of SIA 261 and of the workbook) and three examples of an engineer's own library."""
import json, pathlib
H = pathlib.Path(__file__).parent; W = pathlib.Path(__file__).resolve().parents[4]  # the repository
out = []
WEIGHT = {"Nadelholz": (5, "SIA 261:2020, tableau 28 : résineux en général"), "Laubholz": (7.5, "SIA 261:2020, tableau 28 : feuillus en général"), "BSH": (5, "SIA 261:2020, tableau 28 : bois résineux collés")}
for f, k, cat, ref, page in (("sia265-2021-tab08-vollholz.json", "table_8", "wood", "SIA 265:2021, tableau 8", 23), ("sia265-2021-tab09-brettschichtholz.json", "table_9", "wood", "SIA 265:2021, tableau 9", 24)):
    d = json.load(open(W / "calc/norms" / f))[k]
    for g in d["grades"]:
        fam = g["family"]; wk = WEIGHT["BSH" if fam == "Brettschichtholz" else g["species"]]
        nm = {"fr": ("Lamellé-collé " if fam == "Brettschichtholz" else "Bois massif ") + g["id"], "de": ("Brettschichtholz " if fam == "Brettschichtholz" else "Vollholz ") + g["id"], "en": ("Glulam " if fam == "Brettschichtholz" else "Solid timber ") + g["id"]}
        vals = {x: g[x] for x in ("f_m_k", "E_m_mean", "rho_k", "f_m_d", "f_t_0_d", "f_c_0_d", "f_t_90_d", "f_v_d", "E_0_mean", "E_90_mean", "G_mean")}
        vals["f_c_90_d"] = g["f_c_90_d"]["generell"]
        out.append({"id": "sia265-" + g["id"], "name": nm, "cat": cat, "type": "barre", "src": "woodcore", "norm": ref, "w": {"v": wk[0], "u": "kN/m³", "ref": wk[1]}, "vals": vals,
                    "source": {"kind": "norm", "ref": ref + " (" + d["norm_ref"] + ")", "img": ["tab0" + k[-1] + ".jpg"]}, "comment": "", "gm": 1.5 if fam == "Brettschichtholz" else 1.7,
                    "fam": "gl" if fam == "Brettschichtholz" else "hw" if g["species"] == "Laubholz" else "sw"})
R = [[6, 10], [10, 18], [18, 25]]
def two(a, b): return {"par": a, "perp": b}
osb_k = {"plaque": {"f_m_k": two([18.0, 16.4, 14.8], [9.0, 8.2, 7.4]), "f_c_90_k": two([10.0] * 3, [10.0] * 3), "f_v_k": two([1.0] * 3, [1.0] * 3), "E_m_mean": two([4930] * 3, [1980] * 3), "G_mean": two([50] * 3, [50] * 3)},
         "voile": {"f_m_k": two([9.9, 9.4, 9.0], [7.2, 7.0, 6.8]), "f_v_k": two([6.8] * 3, [6.8] * 3), "E_m_mean": two([3800] * 3, [3000] * 3), "G_mean": two([1080] * 3, [1080] * 3)},
         "tc": {"f_t_k": two([9.9, 9.4, 9.0], [7.2, 7.0, 6.8]), "f_c_k": two([15.9, 15.4, 14.8], [12.9, 12.7, 12.4]), "E_tc_mean": two([3800] * 3, [3000] * 3)}}
osb_d = {"plaque": {"f_m_d": two([10.5, 9.6, 8.6], [5.3, 4.8, 4.3]), "f_c_90_d": two([5.8] * 3, [5.8] * 3), "f_v_d": two([0.6] * 3, [0.6] * 3)},
         "voile": {"f_m_d": two([5.8, 5.5, 5.3], [4.2, 4.1, 4.0]), "f_v_d": two([4.0] * 3, [4.0] * 3)},
         "tc": {"f_t_d": two([5.8, 5.5, 5.3], [4.2, 4.1, 4.0]), "f_c_d": two([9.3, 9.0, 8.6], [7.5, 7.4, 7.2])}}
out.append({"id": "sia2651-osb3", "name": {"fr": "Panneau OSB/3", "de": "OSB/3-Platte", "en": "OSB/3 board"}, "cat": "board", "type": "panneau", "src": "woodcore", "norm": "SIA 265/1:2018, tableaux 19a et 19b",
            "rho_k": 550, "ranges": R, "k": osb_k, "d": osb_d, "t": None, "w": {"v": 6.8, "u": "kN/m³", "ref": "Classeur Belastungsannahmen, lignes 62 et 130 : OSB3, 680 kg/m³ (Kronospan, Menznau)"},
            "kind": "osb34", "source": {"kind": "norm", "ref": "SIA 265/1:2018, p. 42, tableaux 19a et 19b", "img": ["tab19a.jpg", "tab19b.jpg"]}, "comment": "Valeurs de dimensionnement pour la classe d'humidité 1 et la KLED moyenne ; autres cas selon 6.1.2.1."})
# the weights of SIA 261 and of the workbook, one material each, as the permanent loads tab reads them
pm = json.load(open(H.parent / "2026-10-23-charges-permanentes" / "lib.json"))
taken = {x["name"]["fr"].lower() for x in out}
for m in pm:
    # a weight the norm's grades and panels already carry (C24, GL24h, OSB/3) is not listed twice
    if m["src"] == "perso" or m["fr"].lower() in taken: continue
    out.append({"id": "w-" + m["id"], "name": {"fr": m["fr"], "de": m["de"], "en": m["en"]}, "cat": m["fam"], "type": "autre", "src": "sia261" if m["src"] == "sia" else "ext", "w": {"v": m["v"], "u": m["u"], "ref": m["ref"]},
                "source": {"kind": "norm" if m["src"] == "sia" else "book", "ref": m["ref"]}, "comment": m.get("info", "")})
# a grade typed by its characteristic values only: the design values are deduced (SIA 265 (3), 3.3.2.2), and 24 / 1.7 = 14.1 matches Table 8
out.append({"id": "perso-c24k", "name": {"fr": "Bois massif saisi par ses valeurs caractéristiques (exemple)", "de": "Vollholz mit charakteristischen Werten (Muster)", "en": "Solid timber typed by its characteristic values (example)"}, "cat": "wood", "type": "barre", "src": "perso", "fam": "sw", "gm": 1.7,
            "vals": {"f_m_k": 24, "E_0_mean": 11000, "E_90_mean": 370, "G_mean": 690, "rho_k": 350}, "w": {"v": 5, "u": "kN/m³", "ref": "SIA 261:2020, tableau 28 : résineux en général"},
            "source": {"kind": "url", "url": ""}, "comment": "Exemple : seules f_m,k, les modules et ρ_k sont saisis ; f_m,d, f_v,d et f_t,90,d sont déduites, f_t,0,k, f_c,0,k et f_c,90,k manquent."})
# three examples of the engineer's own library: marked as examples, their values not checked
out.append({"id": "perso-3plis", "name": {"fr": "Panneau trois plis mélèze 27 mm (exemple)", "de": "Dreischichtplatte Lärche 27 mm (Muster)", "en": "Three-layer larch board 27 mm (example)"}, "cat": "board", "type": "panneau", "src": "perso", "kind": "swp",
            "rho_k": None, "ranges": None, "t": 27, "k": {"plaque": {"f_m_k": two([None], [None]), "f_v_k": two([None], [None]), "E_m_mean": two([None], [None])}, "voile": {}, "tc": {}}, "d": {"plaque": {}, "voile": {}, "tc": {}},
            "w": {"v": 5.2, "u": "kN/m³", "ref": "saisi pour le prototype"}, "source": {"kind": "pdf", "file": None}, "comment": "Exemple : les résistances restent à reprendre de la fiche du fabricant."})
out.append({"id": "perso-foamglas", "name": {"fr": "Verre cellulaire (exemple)", "de": "Schaumglas (Muster)", "en": "Cellular glass (example)"}, "cat": "ins", "type": "autre", "src": "perso",
            "w": {"v": 1.15, "u": "kN/m³", "ref": "115 kg/m³, à vérifier sur la fiche du fabricant"}, "source": {"kind": "url", "url": ""}, "comment": "Exemple saisi pour le prototype."})
out.append({"id": "perso-installations", "name": {"fr": "Installations et cloisons (exemple)", "de": "Installationen und Innenwände (Muster)", "en": "Services and partitions (example)"}, "cat": "direct", "type": "autre", "src": "perso",
            "w": {"v": 0.5, "u": "kN/m²", "ref": "valeur du bureau"}, "source": {"kind": "url", "url": ""}, "comment": "La charge du modèle de classeur 3.2."})
json.dump(out, open(H / "libdata.json", "w"), ensure_ascii=False)
import collections; print(len(out), collections.Counter((x["type"], x["src"]) for x in out))
