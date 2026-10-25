#import "/000-Typst-Config/commands.typ": *

#domain("EL+AL-Dach_ohne_Wasser", label: "Eigen- und Auflasten – EL+AL-Dach_ohne_Wasser")[
#calc-defaults(presets: "block", scope: "domain") <EL-AL-Dach_ohne_Wasser-presets>

#from-level(2)[#figure(image("/Permanent-loads/Exports/Figures/dead-load-EL+AL-Dach_ohne_Wasser.svg", width: 80%), caption: [Schichtaufbau]) <EL-AL-Dach_ohne_Wasser-figure-1>]

  #var("gk", "g_k", 0.8, "kN/m²", domain: ("dead-load", "EL+AL-Dach_ohne_Wasser"), label: "Eigengewicht (Flächenlast)", norm: "SIA 261", norm-section: "Anhang A", id: "gk")
  #var("ak", "a_k", 1.012, "kN/m²", domain: ("dead-load", "EL+AL-Dach_ohne_Wasser"), label: "Auflast (Flächenlast)", norm: "SIA 261", norm-section: "Anhang A", id: "ak")
  #var("gk_ak", "g_k + a_k", 1.812, "kN/m²", domain: ("dead-load", "EL+AL-Dach_ohne_Wasser"), label: "Summe (berechnet)", norm: "SIA 261", norm-section: "Anhang A", id: "gk_ak")
  #var("gk_ak_gew", "(g_k + a_k)_\"gew\"", 1.9, "kN/m²", domain: ("dead-load", "EL+AL-Dach_ohne_Wasser"), label: "Ständige Lasten, gewählt", descr: "Auf der sicheren Seite gerundeter Bemessungswert der ständigen Lasten.", norm: "SIA 261", norm-section: "2.1", id: "gk_ak_gew")

#from-level(3)[_Schichtaufbau_ <EL-AL-Dach_ohne_Wasser-table-1-title>]
#from-level(3)[#table(columns: 8, table.header([*Type*], [*Ebene*], [*Material*], [*Dicke [m]*], [*Breite [m]*], [*Dist. [m]*], [*Gewicht*], [*Last [kN/m²]*]), [$a_k$], [], [Direkt eingegebene Last], [], [], [], [], [1], [$a_k$], [], [PUR / PIR Dämmung], [0.04], [], [], [0.3 kN/m³], [0.012], [$g_k$], [], [Kerto-Q], [0.06], [], [], [5 kN/m³], [0.3], [$g_k$], [], [Fi/Ta], [0.2], [0.1], [0.2], [5 kN/m³], [0.5], [*$g_k$*], [*Total*], [*Eigengewicht*], [], [], [], [], [*0.8*], [*$a_k$*], [*Total*], [*Auflast*], [], [], [], [], [*1.012*]) <EL-AL-Dach_ohne_Wasser-table-1>]
#from-level(3)[Last je Schicht = Wichte · Dicke · Breite / Abstand; eine Flächenlast ohne die Dicke. Gewichte in kg werden mit g = 10 m/s² in kN umgerechnet. <EL-AL-Dach_ohne_Wasser-table-1-note>]
]
