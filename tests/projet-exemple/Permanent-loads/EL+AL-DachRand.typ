#import "/000-Typst-Config/commands.typ": *

#domain("EL+AL-DachRand", label: "Eigen- und Auflasten – EL+AL-DachRand")[
#calc-defaults(presets: "block", scope: "domain") <EL-AL-DachRand-presets>

  #var("gk", "g_k", 0.3, "kN/m²", domain: ("dead-load", "EL+AL-DachRand"), label: "Eigengewicht (Flächenlast)", norm: "SIA 261", norm-section: "Anhang A", id: "gk")
  #var("ak", "a_k", 0.23, "kN/m²", domain: ("dead-load", "EL+AL-DachRand"), label: "Auflast (Flächenlast)", norm: "SIA 261", norm-section: "Anhang A", id: "ak")
  #var("gk_ak", "g_k + a_k", 0.53, "kN/m²", domain: ("dead-load", "EL+AL-DachRand"), label: "Summe (berechnet)", norm: "SIA 261", norm-section: "Anhang A", id: "gk_ak")
  #var("gk_ak_gew", "(g_k + a_k)_\"gew\"", 0.6, "kN/m²", domain: ("dead-load", "EL+AL-DachRand"), label: "Ständige Lasten, gewählt", descr: "Auf der sicheren Seite gerundeter Bemessungswert der ständigen Lasten, im Blatt EL+AL-DachRand gewählt.", norm: "SIA 261", norm-section: "2.1", id: "gk_ak_gew")

_Schichtaufbau_ <EL-AL-DachRand-table-1-title>
#table(columns: 8, table.header([*Type*], [*Ebene*], [*Material*], [*Dicke [m]*], [*Breite [m]*], [*Dist. [m]*], [*Gewicht*], [*Last [kN/m²]*]), [$a_k$], [Schutzbahn/Dachhaut], [Blech Aluminium 2mm], [1], [1], [1], [8 kg/m²], [0.08], [$a_k$], [Bekleidung], [3-Schichtplatte], [0.03], [1], [1], [500 kg/m³], [0.15], [$g_k$], [Beplankung], [Kerto-Q], [0.06], [1], [1], [500 kg/m³], [0.3], [*$g_k$*], [*Total*], [*Eigengewicht*], [], [], [], [], [*0.3*], [*$a_k$*], [*Total*], [*Auflast*], [], [], [], [], [*0.23*]) <EL-AL-DachRand-table-1>
Last je Schicht = spez. Gewicht · Dicke · Breite / (Dist. · 100); der Faktor 100 rechnet kg in kN um. Flächenbezogene Materialien (kg/m²) sind mit Dicke = Breite = Dist. = 1 erfasst. <EL-AL-DachRand-table-1-note>
]
