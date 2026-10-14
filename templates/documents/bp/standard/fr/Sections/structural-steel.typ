#import "/commands.typ": *

// woodcore:object heading title
== Acier de construction et assemblages
// woodcore:/object title

// woodcore:object doc-table structural-steel-table
#doc-table(
  columns: (
    (id: "grade", title: [Nuance]),
    (id: "band", title: [Épaisseur]),
    (id: "fy", title: [Limite d'élasticité $f_y$], unit: "N/mm²", kind: "number"),
    (id: "fu", title: [Résistance à la traction $f_u$], unit: "N/mm²", kind: "number"),
    (id: "Ea", title: [Module d'élasticité $E_a$], unit: "N/mm²", kind: "number"),
    (id: "gamma", title: [Poids volumique $gamma$], unit: "kN/m³", kind: "number"),
  ),
  hidden: ("Ea", "gamma"),
  rows: (
    (grade: [S235], band: [t ≤ 40 mm], fy: 235, fu: 360, Ea: 210000, gamma: 78.5),
    (grade: [S355], band: [t ≤ 40 mm], fy: 355, fu: 510, Ea: 210000, gamma: 78.5),
  ),
  caption: [Acier de construction (SIA 263)],
)
// woodcore:/object structural-steel-table

// woodcore:object doc-table bolts-table
#doc-table(
  columns: (
    (id: "class", title: [Classe de résistance]),
    (id: "fyb", title: [Limite d'élasticité $f_"yb"$], unit: "N/mm²", kind: "number"),
    (id: "fub", title: [Résistance à la traction $f_"ub"$], unit: "N/mm²", kind: "number"),
    (id: "use", title: [Emploi]),
  ),
  hidden: (),
  rows: (
    (class: [4.6], fyb: 240, fub: 400, use: [Boulons, tire-fonds]),
    (class: [8.8], fyb: 640, fub: 800, use: [Vis à bois (classe minimale)]),
  ),
  caption: [Boulons, tire-fonds et vis à bois (SIA 263)],
  notes: (
    [Les broches (goujons) en acier S355 se calculent avec $f_(u,k)$ = 510 N/mm² (SN EN 14592).],
  ),
)
// woodcore:/object bolts-table
