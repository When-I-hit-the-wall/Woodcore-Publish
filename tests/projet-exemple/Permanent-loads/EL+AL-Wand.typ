#import "/000-Typst-Config/commands.typ": *

#domain("EL+AL-Wand", label: "Eigen- und Auflasten – EL+AL-Wand")[
#calc-defaults(presets: "block", scope: "domain") <EL-AL-Wand-presets>

  #var("gk", "g_k", 0.5, "kN/m²", domain: ("dead-load", "EL+AL-Wand"), label: "Eigengewicht (Flächenlast)", norm: "SIA 261", norm-section: "Anhang A", id: "gk")
  #var("ak", "a_k", 0, "kN/m²", domain: ("dead-load", "EL+AL-Wand"), label: "Auflast (Flächenlast)", norm: "SIA 261", norm-section: "Anhang A", id: "ak")
  #var("gk_ak", "g_k + a_k", 0.5, "kN/m²", domain: ("dead-load", "EL+AL-Wand"), label: "Summe (berechnet)", norm: "SIA 261", norm-section: "Anhang A", id: "gk_ak")
  #var("gk_ak_gew", "(g_k + a_k)_\"gew\"", 0.5, "kN/m²", domain: ("dead-load", "EL+AL-Wand"), label: "Ständige Lasten, gewählt", descr: "Auf der sicheren Seite gerundeter Bemessungswert der ständigen Lasten, im Blatt EL+AL-Wand gewählt.", norm: "SIA 261", norm-section: "2.1", id: "gk_ak_gew")

_Schichtaufbau_ <EL-AL-Wand-table-1-title>
#table(columns: 8, table.header([*Type*], [*Ebene*], [*Material*], [*Dicke [m]*], [*Breite [m]*], [*Dist. [m]*], [*Gewicht*], [*Last [kN/m²]*]), [$g_k$], [Konstruktion], [Fi/Ta], [0.2], [0.1], [0.2], [500 kg/m³], [0.5], [*$g_k$*], [*Total*], [*Eigengewicht*], [], [], [], [], [*0.5*], [*$a_k$*], [*Total*], [*Auflast*], [], [], [], [], [*0*]) <EL-AL-Wand-table-1>
Last je Schicht = spez. Gewicht · Dicke · Breite / (Dist. · 100); der Faktor 100 rechnet kg in kN um. Flächenbezogene Materialien (kg/m²) sind mit Dicke = Breite = Dist. = 1 erfasst. <EL-AL-Wand-table-1-note>
]
