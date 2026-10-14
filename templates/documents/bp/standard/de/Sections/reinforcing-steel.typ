#import "/commands.typ": *

// woodcore:object heading title
== Bewehrungsstahl
// woodcore:/object title

// woodcore:object doc-table reinforcing-steel-table
#doc-table(
  columns: (
    (id: "designation", title: [Bezeichnung]),
    (id: "fsk", title: [Charakteristische Streckgrenze $f_"sk"$], unit: "N/mm²", kind: "number"),
    (id: "fsd", title: [Bemessungswert der Streckgrenze $f_"sd"$], unit: "N/mm²", kind: "number"),
    (id: "Es", title: [Elastizitätsmodul $E_s$], unit: "N/mm²", kind: "number"),
    (id: "gamma", title: [Raumlast $gamma$], unit: "kN/m³", kind: "number"),
  ),
  hidden: (),
  rows: (
    (designation: [B500B], fsk: 500, fsd: [[…]], Es: [[…]], gamma: 78.5),
  ),
  caption: [Betonstahl (SIA 262)],
  notes: (
    [Bemessungswerte nach der Norm SIA 262:2025.],
  ),
)
// woodcore:/object reinforcing-steel-table
