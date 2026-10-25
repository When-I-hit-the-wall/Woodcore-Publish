#import "/000-Typst-Config/commands.typ": *

#domain("WL-Fluchttreppe+Geraete", label: "Windlast – WL-Fluchttreppe+Geraete")[
#calc-defaults(presets: "block", scope: "domain") <WL-Fluchttreppe-Geraete-presets>

#from-level(3)[#figure(image("/Variable-loads/Wind/Exports/Figures/WL-Fluchttreppe+Geraete-fig-de.pdf", width: 80%), caption: [Figur der Tabelle 59a (SIA 261, Anhang C)]) <WL-Fluchttreppe-Geraete-figure-1>]

  #var("qp0", "q_(p 0)", 0.9, "kN/m²", domain: ("wind-load", "WL-Fluchttreppe+Geraete"), label: "Referenzwert des Staudrucks", descr: "Referenzwert des Staudrucks am Standort nach SIA 261.", norm: "SIA 261", norm-section: "Anhang E", id: "qp0")
  #var("b", 8.9, "m", domain: ("wind-load", "WL-Fluchttreppe+Geraete"), label: "Gebäudelänge", norm: "SIA 261", norm-section: "6.3", id: "b")
  #var("d", 6.5, "m", domain: ("wind-load", "WL-Fluchttreppe+Geraete"), label: "Gebäudebreite", norm: "SIA 261", norm-section: "6.3", id: "d")
  #var("h", 3, "m", domain: ("wind-load", "WL-Fluchttreppe+Geraete"), label: "Gebäudehöhe", norm: "SIA 261", norm-section: "6.3", id: "h")
  #var("gelaendekategorie", domain: ("wind-load", "WL-Fluchttreppe+Geraete"), label: "Geländekategorie", descr: "Die Geländekategorie bestimmt die Gradientenhöhe und die Bodenrauigkeit des Windprofils.", norm: "SIA 261", norm-section: "Tableau 4", id: "gelaendekategorie")
  #var("zg", "z_g", 526, "m", domain: ("wind-load", "WL-Fluchttreppe+Geraete"), label: "Gradientenhöhe", norm: "SIA 261", norm-section: "Tableau 4", id: "zg")
  #var("alpha_r", 0.3, domain: ("wind-load", "WL-Fluchttreppe+Geraete"), label: "Bodenrauigkeit", norm: "SIA 261", norm-section: "Tableau 4", id: "alpha_r")
  #var("z", 10, "m", domain: ("wind-load", "WL-Fluchttreppe+Geraete"), label: "Höhe über Boden", descr: "Höhe über Boden, für die der Staudruck bestimmt wird; die Norm setzt sie mindestens zu 5 m an (10 m in Geländekategorie IV).", norm: "SIA 261", norm-section: "6.2.1.2", id: "z")
  #var("ch", "c_h", 0.738931, domain: ("wind-load", "WL-Fluchttreppe+Geraete"), label: "Windprofilbeiwert", norm: "SIA 261", norm-section: "6.2.1.2", id: "ch")
  #var("cred_bh", "c_(\"red\", \"b/h\")", 0.85646, domain: ("wind-load", "WL-Fluchttreppe+Geraete"), label: "Reduktionsfaktor b", descr: "Reduktionsfaktor für die Bezugsfläche b·h, aus dem Verhältnis Länge (b) zu Höhe (h).", norm: "SIA 261", norm-section: "Figur 9", id: "cred_bh")
  #var("cred_dh", "c_(\"red\", \"d/h\")", 0.878409, domain: ("wind-load", "WL-Fluchttreppe+Geraete"), label: "Reduktionsfaktor d", descr: "Reduktionsfaktor für die Bezugsfläche d·h, aus dem Verhältnis Breite (d) zu Höhe (h).", norm: "SIA 261", norm-section: "Figur 9", id: "cred_dh")
  #var("cred_max", "c_(\"red\", \"max\")", 0.878409, domain: ("wind-load", "WL-Fluchttreppe+Geraete"), label: "Reduktionsfaktor schräge Windrichtung", descr: "Für eine Windrichtung, die um 15° oder mehr von den Bezugsrichtungen abweicht, gilt der ungünstigere (grössere) der beiden Reduktionsfaktoren.", norm: "SIA 261", norm-section: "6.3.3", id: "cred_max")
  #var("cd", "c_d", 1, domain: ("wind-load", "WL-Fluchttreppe+Geraete"), label: "Dynamischer Faktor", norm: "SIA 261", norm-section: "6.3.5", id: "cd")
  #eq("qp", "q_p", `ch dot qp0`, unit: "kN/m²", label: "Staudruck", norm: "SIA 261", norm-section: "6.2 (11)", id: "qp")
  #var("tabelle", domain: ("wind-load", "WL-Fluchttreppe+Geraete"), label: "Tabelle der Druckbeiwerte", descr: "SIA 261, Anhang C, Tabelle 59a, h : b : d = 1 : 2 : 5, h ≈ 8 m.", norm: "SIA 261", norm-section: "Anhang C", id: "tabelle")
  #var("qk_max_cf1", "q_(k,\"max\",\"b·h\")", 0.51262, "kN/m²", domain: ("wind-load", "WL-Fluchttreppe+Geraete"), label: "Maximale globale Windlast je m², Bezugsfläche b·h", norm: "SIA 261", norm-section: "6.2.3.2", id: "qk_max_cf1")
  #var("qk_min_cf1", "q_(k,\"min\",\"b·h\")", 0, "kN/m²", domain: ("wind-load", "WL-Fluchttreppe+Geraete"), label: "Minimale globale Windlast je m², Bezugsfläche b·h", norm: "SIA 261", norm-section: "6.2.3.2", id: "qk_min_cf1")
  #var("qk_max_cf2", "q_(k,\"max\",\"d·h\")", 0.554967, "kN/m²", domain: ("wind-load", "WL-Fluchttreppe+Geraete"), label: "Maximale globale Windlast je m², Bezugsfläche d·h", norm: "SIA 261", norm-section: "6.2.3.2", id: "qk_max_cf2")
  #var("qk_min_cf2", "q_(k,\"min\",\"d·h\")", 0, "kN/m²", domain: ("wind-load", "WL-Fluchttreppe+Geraete"), label: "Minimale globale Windlast je m², Bezugsfläche d·h", norm: "SIA 261", norm-section: "6.2.3.2", id: "qk_min_cf2")
  #var("qk_max_cf3", "q_(k,\"max\",\"d·b\")", -0.219462, "kN/m²", domain: ("wind-load", "WL-Fluchttreppe+Geraete"), label: "Maximale globale Windlast je m², Bezugsfläche d·b", norm: "SIA 261", norm-section: "6.2.3.2", id: "qk_max_cf3")
  #var("qk_min_cf3", "q_(k,\"min\",\"d·b\")", -0.305917, "kN/m²", domain: ("wind-load", "WL-Fluchttreppe+Geraete"), label: "Minimale globale Windlast je m², Bezugsfläche d·b", norm: "SIA 261", norm-section: "6.2.3.2", id: "qk_min_cf3")
  #var("Qk_max_cf1", "Q_(k,\"max\",\"b·h\")", 13.686963, "kN", domain: ("wind-load", "WL-Fluchttreppe+Geraete"), label: "Maximale globale Windkraft, Bezugsfläche b·h", norm: "SIA 261", norm-section: "6.2.3.2", id: "Qk_max_cf1")
  #var("Qk_min_cf1", "Q_(k,\"min\",\"b·h\")", 0, "kN", domain: ("wind-load", "WL-Fluchttreppe+Geraete"), label: "Minimale globale Windkraft, Bezugsfläche b·h", norm: "SIA 261", norm-section: "6.2.3.2", id: "Qk_min_cf1")
  #var("Qk_max_cf2", "Q_(k,\"max\",\"d·h\")", 10.821847, "kN", domain: ("wind-load", "WL-Fluchttreppe+Geraete"), label: "Maximale globale Windkraft, Bezugsfläche d·h", norm: "SIA 261", norm-section: "6.2.3.2", id: "Qk_max_cf2")
  #var("Qk_min_cf2", "Q_(k,\"min\",\"d·h\")", 0, "kN", domain: ("wind-load", "WL-Fluchttreppe+Geraete"), label: "Minimale globale Windkraft, Bezugsfläche d·h", norm: "SIA 261", norm-section: "6.2.3.2", id: "Qk_min_cf2")
  #var("Qk_max_cf3", "Q_(k,\"max\",\"d·b\")", -12.695902, "kN", domain: ("wind-load", "WL-Fluchttreppe+Geraete"), label: "Maximale globale Windkraft, Bezugsfläche d·b", norm: "SIA 261", norm-section: "6.2.3.2", id: "Qk_max_cf3")
  #var("Qk_min_cf3", "Q_(k,\"min\",\"d·b\")", -17.697318, "kN", domain: ("wind-load", "WL-Fluchttreppe+Geraete"), label: "Minimale globale Windkraft, Bezugsfläche d·b", norm: "SIA 261", norm-section: "6.2.3.2", id: "Qk_min_cf3")

_Globale Windkräfte_ <WL-Fluchttreppe-Geraete-table-1-title>
#table(columns: 5, table.header(table.cell(colspan: 2, []), table.cell(colspan: 3, [*Bezugsfläche*]), [*Globale Windkraft [kN]*], [], [*b·h*], [*d·h*], [*d·b*]), [maximale globale Windkraft], [$Q_k =$], [13.7], [10.8], [−12.7], [minimale globale Windkraft], [$Q_k =$], [0], [0], [−17.7]) <WL-Fluchttreppe-Geraete-table-1>
$Q_k = c_"red" dot c_d dot c_f dot q_p dot A_"ref"$ (SIA 261, 6.2.3.2); $A_"ref"$: b·h = 26.7 m², d·h = 19.5 m², d·b = 57.9 m². Negative Werte sind Sog. <WL-Fluchttreppe-Geraete-table-1-note>

_Lokale Windkräfte_ <WL-Fluchttreppe-Geraete-table-2-title>
#table(columns: (auto,) + (1fr,) * 11, table.header([], table.cell(colspan: 11, [*Öffnungen gleichmässig verteilt*]), [*$q_k$ [kN/m²]*], [*A*], [*B*], [*C*], [*D*], [*E*], [*F*], [*G*], [*H*], [*m*], [*n*], [*o*]), [*max*], [0.466], [−0.133], [0.532], [−0.1], [−0.166], [−0.1], [−0.133], [−0.1], [−0.233], [−0.233], [−0.233], [*min*], [−0.299], [−0.299], [−0.333], [−0.333], [−0.466], [−0.466], [−0.366], [−0.299], [−0.632], [−0.632], [−0.732]) <WL-Fluchttreppe-Geraete-table-2>
Grösster (max) und kleinster (min) Wert von $q_k = q_p dot (c_d dot c_"pe" - c_"pi")$ je Fläche über die Windrichtungen der Tabelle 59a; lokale Flächen (Figur 22): m, n, o. Negative Werte sind Sog. <WL-Fluchttreppe-Geraete-table-2-note>
]
