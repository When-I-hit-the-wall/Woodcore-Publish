#import "/000-Typst-Config/commands.typ": *

= Tragwerksanalyse

Statisches Modell und daraus resultierende Schnittkräfte.

== Verbindung oben

#grid(
  columns: (1fr, 1fr),
  gutter: 10pt,
  figure(
  image("/Images/260914-Screenshot-1817.png", width: 100%),
  caption: [Biegesteife Verbindung],
  ),
  figure(
  image("/Images/260914-Screenshot-1818.png", width: 100%),
  caption: [Gelenkige Verbindung],
  ),

  grid.cell(
    colspan: 2,
    figure(
    image("/Images/260914-Screenshot-1819.png", width: 70%),
  caption: [Alternative Schrauben für die gelenkige Verbindung],)
  ),
)

=== Biegesteife Verbindung

==== Tragsicherheit

// The resistance of the connector SD-10 is in its file, Connectors/SD-10.typ, which section 003 includes with every connector: included once, its lines' ids being its own.

==== Polares Trägheitsmoment
#var("n_v", 5, label: "Anzahl statischer Systeme pro Laufmeter", level: 3)
#var("N", 0, "kN", level:3)
#var("V", 24.99, "kN", level:3)
#var("M", 15.02, "kNm", level:3)

#eq("N_Ed", `N / n_v`, level:3)
#eq("V_Ed", `V / n_v`, level:3)
#eq("M_Ed", `M / n_v`, level:3)

#include domain-file("connection", "VU-MP-1")

=== Gelenkige Verbindung


== Velo Unterstand

=== Verbindung oben






== Bänkli

#figure(
  image("/Images/260912-Screenshot-1792.png", width: 80%),
  caption: [Bänkli mit Sherpa System],
)

#figure(
  image("/Images/260912-Screenshot-1793.png", width: 80%),
  caption: [Sherpa: Tragfähigkeitswerte],
)

=== Sherpa S 10

#figure(
  image("/Images/260912-Screenshot-1794.png", width: 80%),
  caption: [Sherpa: Kenndaten S 10],
)

#grid(
  columns: (1fr, 1fr),
  gutter: 10pt,
  image-static-model("Bankli-Fall1", width: 100%),
  image-static-model("Bankli-Fall2", width: 100%)
)
#var("R_k", 7, "kN")
#var("k_dens", 0.806)
#var("eta_w", 0.8)
#var("gamma_M", 1.7)
#var("eta_M", 1)

#eq("R_d", `k_dens dot eta_w / (gamma_M \/ eta_M) dot R_k`,
    style: "bold", norm: "Sherpa", norm-ref: "ETA-12/0197", level:3)

#grid(
  columns: (1fr, 1fr),
  column-gutter: 12pt,

  domain("S10 - 0.55 kN Ende")[
    #underline[*0.55 kN Ende Träger:*]

    #var("F", 0.55, "kN")
    #var("l", 0.5, "m")
    #var("a", 135, "mm", label: "Abstand für das Moment")

    #var("F")

    #eq("M", `F dot l`)

    #eq("F_Ed", `M / a`)

    #verify(`F_Ed <= R_d`)

    #eq("eta", `F_Ed / R_d`)

    #verify(`eta <= 1`)
  ],
  domain("S10 - 1 kN Mitte")[
    #underline[*1 kN Mitte Träger:*]

    #var("F", 1, "kN")
    #var("l", 0.5, "m")

    #eq("M", `F dot l/2`)

    $=>$ #underline[nicht massgebend]
  ],
)

Das massgebende Moment am Trägerende beträgt #var("M", domain: "S10 - 0.55 kN Ende", display: "value-unit", label-position: "none", descr-position: "none", norm-position: "none"), dasjenige in Trägermitte #var("M", domain: "S10 - 1 kN Mitte", display: "value-unit", label-position: "none", descr-position: "none", norm-position: "none") -- ein Domain-Name genügt, um eine Variable später wieder zu lesen.

=== Sherpa S 10 Duo

#figure(
  image("/Images/260912-Screenshot-1795.png", width: 80%),
  caption: [Sherpa: Kenndaten S 10 Duo],
)

#var("R_k", 13.1, "kN")

#eq("R_d", `k_dens dot eta_w / (gamma_M \/ eta_M) dot R_k`,
    style: "bold", norm: "Sherpa", norm-ref: "ETA-12/0197")

#grid(
  columns: (1fr, 1fr),
  column-gutter: 12pt,

  domain("S10 Duo - 0.55 kN Ende")[
    #underline[*0.55 kN Ende Träger:*]

    #var("F", 0.55, "kN")
    #var("l", 0.5, "m")
    #var("a", 135, "mm", label: "Abstand für das Moment", level: 3)

    #eq("M", `F dot l`)
    #eq("F_Ed", `M / a`)

    #verify(`F_Ed <= R_d`, level:3)

    #eq("eta", `F_Ed / R_d`)

    #verify(`eta <= 1`)
  ],
  domain("S10 Duo - 1 kN Mitte")[
    #underline[*1 kN Mitte Träger:*]

    #var("F", 1, "kN")
    #var("l", 0.5, "m")

    #eq("M", `F dot l/2`, level:3)

    $=>$ #underline[nicht massgebend]
  ],
)
