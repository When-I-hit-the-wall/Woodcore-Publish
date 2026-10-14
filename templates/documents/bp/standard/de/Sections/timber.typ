#import "/commands.typ": *

// woodcore:object heading title
== Holz und Holzwerkstoffe
// woodcore:/object title

// woodcore:object doc-table timber-table
#doc-table(
  columns: (
    (id: "designation", title: [Bezeichnung]),
    (id: "fmd", title: [Biegung $f_"md"$], unit: "N/mm²", kind: "number"),
    (id: "fc0d", title: [Druck parallel zur Faser $f_(c,0,d)$], unit: "N/mm²", kind: "number"),
    (id: "fvd", title: [Schub $f_"vd"$], unit: "N/mm²", kind: "number"),
    (id: "E0", title: [Mittlerer Elastizitätsmodul $E_(0,"mean")$], unit: "N/mm²", kind: "number"),
    (id: "rho", title: [Charakteristische Rohdichte $rho_k$], unit: "kg/m³", kind: "number"),
    (id: "gamma", title: [Raumlast $gamma$], unit: "kN/m³", kind: "number"),
  ),
  hidden: ("rho", "gamma"),
  rows: (
    (designation: [C24], fmd: 14.1, fc0d: 12.4, fvd: 1.5, E0: 11000, rho: 350, gamma: 5),
    (designation: [GL24h], fmd: 16.0, fc0d: 16.0, fvd: 1.8, E0: 11500, rho: 385, gamma: 5),
  ),
  caption: [Vollholz und Brettschichtholz (SIA 265, Bemessungswerte für Feuchteklasse 1)],
  notes: (
    [Die Festigkeits- und Steifigkeitseigenschaften, die Widerstandsbeiwerte und die Beiwerte zur Berücksichtigung der Lasteinwirkungsdauer werden nach den jeweils gültigen SIA-Normen angewendet. Für Holzwerkstoffe (Platten, Brettsperrholz) gelten die Werte der Norm SIA 265/1.],
  ),
)
// woodcore:/object timber-table
