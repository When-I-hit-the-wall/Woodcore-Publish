#import "/000-Typst-Config/commands.typ": *

#domain("EL+AL-DachRand", label: "Eigen- und Auflasten – EL+AL-DachRand")[
#calc-defaults(presets: "block", scope: "domain") <EL-AL-DachRand-presets>

  #var("gk", "g_k", 0.3, "kN/m²", domain: ("dead-load", "EL+AL-DachRand"), label: "Eigengewicht (Flächenlast)", norm: "SIA 261", norm-section: "Anhang A", id: "gk")
  #var("ak", "a_k", 0.23, "kN/m²", domain: ("dead-load", "EL+AL-DachRand"), label: "Auflast (Flächenlast)", norm: "SIA 261", norm-section: "Anhang A", id: "ak")
  #var("gk_ak", "g_k + a_k", 0.53, "kN/m²", domain: ("dead-load", "EL+AL-DachRand"), label: "Summe (berechnet)", norm: "SIA 261", norm-section: "Anhang A", id: "gk_ak")
  #var("gk_ak_gew", "(g_k + a_k)_\"gew\"", 0.6, "kN/m²", domain: ("dead-load", "EL+AL-DachRand"), label: "Ständige Lasten, gewählt", descr: "Auf der sicheren Seite gerundeter Bemessungswert der ständigen Lasten.", norm: "SIA 261", norm-section: "2.1", id: "gk_ak_gew")

#from-level(3)[_Schichtaufbau_ <EL-AL-DachRand-table-1-title>]
#from-level(3)[#table(columns: 8, table.header([*Type*], [*Ebene*], [*Material*], [*Dicke [m]*], [*Breite [m]*], [*Dist. [m]*], [*Gewicht*], [*Last [kN/m²]*]), [$a_k$], [], [Direkt eingegebene Last], [], [], [], [], [0.08], [$a_k$], [], [3-Schichtplatte], [0.03], [], [], [5 kN/m³], [0.15], [$g_k$], [], [Kerto-Q], [0.06], [], [], [5 kN/m³], [0.3], [*$g_k$*], [*Total*], [*Eigengewicht*], [], [], [], [], [*0.3*], [*$a_k$*], [*Total*], [*Auflast*], [], [], [], [], [*0.23*]) <EL-AL-DachRand-table-1>]
#from-level(3)[Last je Schicht = Wichte · Dicke · Breite / Abstand; eine Flächenlast ohne die Dicke. Gewichte in kg werden mit g = 10 m/s² in kN umgerechnet. <EL-AL-DachRand-table-1-note>]
]
