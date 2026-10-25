#import "/000-Typst-Config/commands.typ": *

#domain("WL-Pavillon", label: "Windlast – WL-Pavillon")[
#calc-defaults(presets: "block", scope: "domain") <WL-Pavillon-presets>

#from-level(3)[#figure(image("/Variable-loads/Wind/Exports/Figures/WL-Pavillon-fig-de.pdf", width: 80%), caption: [Figur der Tabelle 31 (SIA 261, Anhang C)]) <WL-Pavillon-figure-1>]

  #var("qp0", "q_(p 0)", 0.9, "kN/m²", domain: ("wind-load", "WL-Pavillon"), label: "Referenzwert des Staudrucks", descr: "Referenzwert des Staudrucks am Standort nach SIA 261.", norm: "SIA 261", norm-section: "Anhang E", id: "qp0")
  #var("b", 17.5, "m", domain: ("wind-load", "WL-Pavillon"), label: "Gebäudelänge", norm: "SIA 261", norm-section: "6.3", id: "b")
  #var("d", 4.25, "m", domain: ("wind-load", "WL-Pavillon"), label: "Gebäudebreite", norm: "SIA 261", norm-section: "6.3", id: "d")
  #var("h", 2.95, "m", domain: ("wind-load", "WL-Pavillon"), label: "Gebäudehöhe", norm: "SIA 261", norm-section: "6.3", id: "h")
  #var("gelaendekategorie", domain: ("wind-load", "WL-Pavillon"), label: "Geländekategorie", descr: "Die Geländekategorie bestimmt die Gradientenhöhe und die Bodenrauigkeit des Windprofils.", norm: "SIA 261", norm-section: "Tableau 4", id: "gelaendekategorie")
  #var("zg", "z_g", 526, "m", domain: ("wind-load", "WL-Pavillon"), label: "Gradientenhöhe", norm: "SIA 261", norm-section: "Tableau 4", id: "zg")
  #var("alpha_r", 0.3, domain: ("wind-load", "WL-Pavillon"), label: "Bodenrauigkeit", norm: "SIA 261", norm-section: "Tableau 4", id: "alpha_r")
  #var("z", 10, "m", domain: ("wind-load", "WL-Pavillon"), label: "Höhe über Boden", descr: "Höhe über Boden, für die der Staudruck bestimmt wird; die Norm setzt sie mindestens zu 5 m an (10 m in Geländekategorie IV).", norm: "SIA 261", norm-section: "6.2.1.2", id: "z")
  #var("ch", "c_h", 0.738931, domain: ("wind-load", "WL-Pavillon"), label: "Windprofilbeiwert", norm: "SIA 261", norm-section: "6.2.1.2", id: "ch")
  #var("cred_bh", "c_(\"red\", \"b/h\")", 0.803968, domain: ("wind-load", "WL-Pavillon"), label: "Reduktionsfaktor b", descr: "Reduktionsfaktor für die Bezugsfläche b·h, aus dem Verhältnis Länge (b) zu Höhe (h).", norm: "SIA 261", norm-section: "Figur 9", id: "cred_bh")
  #var("cred_dh", "c_(\"red\", \"d/h\")", 0.900091, domain: ("wind-load", "WL-Pavillon"), label: "Reduktionsfaktor d", descr: "Reduktionsfaktor für die Bezugsfläche d·h, aus dem Verhältnis Breite (d) zu Höhe (h).", norm: "SIA 261", norm-section: "Figur 9", id: "cred_dh")
  #var("cred_max", "c_(\"red\", \"max\")", 0.900091, domain: ("wind-load", "WL-Pavillon"), label: "Reduktionsfaktor schräge Windrichtung", descr: "Für eine Windrichtung, die um 15° oder mehr von den Bezugsrichtungen abweicht, gilt der ungünstigere (grössere) der beiden Reduktionsfaktoren.", norm: "SIA 261", norm-section: "6.3.3", id: "cred_max")
  #var("cd", "c_d", 1, domain: ("wind-load", "WL-Pavillon"), label: "Dynamischer Faktor", norm: "SIA 261", norm-section: "6.3.5", id: "cd")
  #eq("qp", "q_p", `ch dot qp0`, unit: "kN/m²", label: "Staudruck", norm: "SIA 261", norm-section: "6.2 (11)", id: "qp")
  #var("tabelle", domain: ("wind-load", "WL-Pavillon"), label: "Tabelle der Druckbeiwerte", descr: "SIA 261, Anhang C, Tabelle 31, h : b : d = 0,3 : 1 : 1 – 0,05 : 1 : 1.", norm: "SIA 261", norm-section: "Anhang C", id: "tabelle")
  #var("qk_max_cf1", "q_(k,\"max\",\"b·h\")", 0.507936, "kN/m²", domain: ("wind-load", "WL-Pavillon"), label: "Maximale globale Windlast je m², Bezugsfläche b·h", norm: "SIA 261", norm-section: "6.2.3.2", id: "qk_max_cf1")
  #var("qk_min_cf1", "q_(k,\"min\",\"b·h\")", 0, "kN/m²", domain: ("wind-load", "WL-Pavillon"), label: "Minimale globale Windlast je m², Bezugsfläche b·h", norm: "SIA 261", norm-section: "6.2.3.2", id: "qk_min_cf1")
  #var("qk_max_cf2", "q_(k,\"max\",\"d·h\")", 0.568664, "kN/m²", domain: ("wind-load", "WL-Pavillon"), label: "Maximale globale Windlast je m², Bezugsfläche d·h", norm: "SIA 261", norm-section: "6.2.3.2", id: "qk_max_cf2")
  #var("qk_min_cf2", "q_(k,\"min\",\"d·h\")", 0, "kN/m²", domain: ("wind-load", "WL-Pavillon"), label: "Minimale globale Windlast je m², Bezugsfläche d·h", norm: "SIA 261", norm-section: "6.2.3.2", id: "qk_min_cf2")
  #var("qk_max_cf3", "q_(k,\"max\",\"d·b\")", -0.252714, "kN/m²", domain: ("wind-load", "WL-Pavillon"), label: "Maximale globale Windlast je m², Bezugsfläche d·b", norm: "SIA 261", norm-section: "6.2.3.2", id: "qk_max_cf3")
  #var("qk_min_cf3", "q_(k,\"min\",\"d·b\")", -0.266015, "kN/m²", domain: ("wind-load", "WL-Pavillon"), label: "Minimale globale Windlast je m², Bezugsfläche d·b", norm: "SIA 261", norm-section: "6.2.3.2", id: "qk_min_cf3")
  #var("Qk_max_cf1", "Q_(k,\"max\",\"b·h\")", 26.222187, "kN", domain: ("wind-load", "WL-Pavillon"), label: "Maximale globale Windkraft, Bezugsfläche b·h", norm: "SIA 261", norm-section: "6.2.3.2", id: "Qk_max_cf1")
  #var("Qk_min_cf1", "Q_(k,\"min\",\"b·h\")", 0, "kN", domain: ("wind-load", "WL-Pavillon"), label: "Minimale globale Windkraft, Bezugsfläche b·h", norm: "SIA 261", norm-section: "6.2.3.2", id: "Qk_min_cf1")
  #var("Qk_max_cf2", "Q_(k,\"max\",\"d·h\")", 7.129631, "kN", domain: ("wind-load", "WL-Pavillon"), label: "Maximale globale Windkraft, Bezugsfläche d·h", norm: "SIA 261", norm-section: "6.2.3.2", id: "Qk_max_cf2")
  #var("Qk_min_cf2", "Q_(k,\"min\",\"d·h\")", 0, "kN", domain: ("wind-load", "WL-Pavillon"), label: "Minimale globale Windkraft, Bezugsfläche d·h", norm: "SIA 261", norm-section: "6.2.3.2", id: "Qk_min_cf2")
  #var("Qk_max_cf3", "Q_(k,\"max\",\"d·b\")", -18.795628, "kN", domain: ("wind-load", "WL-Pavillon"), label: "Maximale globale Windkraft, Bezugsfläche d·b", norm: "SIA 261", norm-section: "6.2.3.2", id: "Qk_max_cf3")
  #var("Qk_min_cf3", "Q_(k,\"min\",\"d·b\")", -19.784872, "kN", domain: ("wind-load", "WL-Pavillon"), label: "Minimale globale Windkraft, Bezugsfläche d·b", norm: "SIA 261", norm-section: "6.2.3.2", id: "Qk_min_cf3")

_Globale Windkräfte_ <WL-Pavillon-table-1-title>
#table(columns: 5, table.header(table.cell(colspan: 2, []), table.cell(colspan: 3, [*Bezugsfläche*]), [*Globale Windkraft [kN]*], [], [*b·h*], [*d·h*], [*d·b*]), [maximale globale Windkraft], [$Q_k =$], [26.2], [7.1], [−18.8], [minimale globale Windkraft], [$Q_k =$], [0], [0], [−19.8]) <WL-Pavillon-table-1>
$Q_k = c_"red" dot c_d dot c_f dot q_p dot A_"ref"$ (SIA 261, 6.2.3.2); $A_"ref"$: b·h = 51.6 m², d·h = 12.5 m², d·b = 74.4 m². Negative Werte sind Sog. <WL-Pavillon-table-1-note>

_Lokale Windkräfte_ <WL-Pavillon-table-2-title>
#table(columns: (auto,) + (1fr,) * 11, table.header([], table.cell(colspan: 11, [*Öffnungen gleichmässig verteilt*]), [*$q_k$ [kN/m²]*], [*A*], [*B*], [*C*], [*D*], [*E*], [*F*], [*G*], [*H*], [*m*], [*n*], [*o*]), [*max*], [0.605], [−0.027], [0.565], [−0.067], [−0.193], [−0.067], [−0.027], [−0.027], [−0.2], [−0.16], [0.399], [*min*], [−0.333], [−0.333], [−0.333], [−0.333], [−0.432], [−0.466], [−0.432], [−0.299], [−0.665], [−0.665], [−0.765]) <WL-Pavillon-table-2>
Grösster (max) und kleinster (min) Wert von $q_k = q_p dot (c_d dot c_"pe" - c_"pi")$ je Fläche über die Windrichtungen der Tabelle 31; lokale Flächen (Figur 22): m, n, o. Negative Werte sind Sog. <WL-Pavillon-table-2-note>
]
