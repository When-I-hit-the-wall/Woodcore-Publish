#import "/000-Typst-Config/commands.typ": *

#domain("EL+AL-Dach ohne Wasser", label: "Eigen- und Auflasten – EL+AL-Dach ohne Wasser")[
#calc-defaults(presets: "block", scope: "domain") <EL-AL-Dach-ohne-Wasser-presets>

  #var("gk", "g_k", 0.8, "kN/m²", domain: ("dead-load", "EL+AL-Dach ohne Wasser"), label: "Eigengewicht (Flächenlast)", norm: "SIA 261", norm-section: "Anhang A", id: "gk")
  #var("ak", "a_k", 1.012, "kN/m²", domain: ("dead-load", "EL+AL-Dach ohne Wasser"), label: "Auflast (Flächenlast)", norm: "SIA 261", norm-section: "Anhang A", id: "ak")
  #var("gk_ak", "g_k + a_k", 1.812, "kN/m²", domain: ("dead-load", "EL+AL-Dach ohne Wasser"), label: "Summe (berechnet)", norm: "SIA 261", norm-section: "Anhang A", id: "gk_ak")
  #var("gk_ak_gew", "(g_k + a_k)_\"gew\"", 1.9, "kN/m²", domain: ("dead-load", "EL+AL-Dach ohne Wasser"), label: "Ständige Lasten, gewählt", descr: "Auf der sicheren Seite gerundeter Bemessungswert der ständigen Lasten, im Blatt EL+AL-Dach ohne Wasser gewählt.", norm: "SIA 261", norm-section: "2.1", id: "gk_ak_gew")

_Schichtaufbau_ <EL-AL-Dach-ohne-Wasser-table-1-title>
#table(columns: 8, table.header([*Type*], [*Ebene*], [*Material*], [*Dicke [m]*], [*Breite [m]*], [*Dist. [m]*], [*Gewicht*], [*Last [kN/m²]*]), [$a_k$], [Beschichtung], [Dachbegrünung (Bienenweide) (trocken)], [1], [1], [1], [100 kg/m²], [1], [$a_k$], [Dämmung], [PUR / PIR Dämmung], [0.04], [1], [1], [30 kg/m³], [0.012], [$g_k$], [Beplankung], [Kerto-Q], [0.06], [1], [1], [500 kg/m³], [0.3], [$g_k$], [Konstruktion], [Fi/Ta], [0.2], [0.1], [0.2], [500 kg/m³], [0.5], [*$g_k$*], [*Total*], [*Eigengewicht*], [], [], [], [], [*0.8*], [*$a_k$*], [*Total*], [*Auflast*], [], [], [], [], [*1.012*]) <EL-AL-Dach-ohne-Wasser-table-1>
Last je Schicht = spez. Gewicht · Dicke · Breite / (Dist. · 100); der Faktor 100 rechnet kg in kN um. Flächenbezogene Materialien (kg/m²) sind mit Dicke = Breite = Dist. = 1 erfasst. <EL-AL-Dach-ohne-Wasser-table-1-note>
]
