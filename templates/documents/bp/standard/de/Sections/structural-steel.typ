#import "/commands.typ": *

// woodcore:object heading title
== Baustahl und Verbindungsmittel
// woodcore:/object title

// woodcore:object doc-table structural-steel-table
#doc-table(
  columns: (
    (id: "grade", title: [Stahlsorte]),
    (id: "band", title: [Dicke]),
    (id: "fy", title: [Streckgrenze $f_y$], unit: "N/mm²", kind: "number"),
    (id: "fu", title: [Zugfestigkeit $f_u$], unit: "N/mm²", kind: "number"),
    (id: "Ea", title: [Elastizitätsmodul $E_a$], unit: "N/mm²", kind: "number"),
    (id: "gamma", title: [Raumlast $gamma$], unit: "kN/m³", kind: "number"),
  ),
  hidden: ("Ea", "gamma"),
  rows: (
    (grade: [S235], band: [t ≤ 40 mm], fy: 235, fu: 360, Ea: 210000, gamma: 78.5),
    (grade: [S355], band: [t ≤ 40 mm], fy: 355, fu: 510, Ea: 210000, gamma: 78.5),
  ),
  caption: [Baustahl (SIA 263)],
)
// woodcore:/object structural-steel-table

// woodcore:object doc-table bolts-table
#doc-table(
  columns: (
    (id: "class", title: [Festigkeitsklasse]),
    (id: "fyb", title: [Streckgrenze $f_"yb"$], unit: "N/mm²", kind: "number"),
    (id: "fub", title: [Zugfestigkeit $f_"ub"$], unit: "N/mm²", kind: "number"),
    (id: "use", title: [Verwendung]),
  ),
  hidden: (),
  rows: (
    (class: [4.6], fyb: 240, fub: 400, use: [Bolzen, Schlüsselschrauben]),
    (class: [8.8], fyb: 640, fub: 800, use: [Holzschrauben (Mindestklasse)]),
  ),
  caption: [Schrauben und Holzschrauben (SIA 263)],
  notes: (
    [Stabdübel aus Stahl S355 werden mit $f_(u,k)$ = 510 N/mm² berechnet (SN EN 14592).],
  ),
)
// woodcore:/object bolts-table
