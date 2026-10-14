#import "/commands.typ": *

// woodcore:object heading title
== Acier d'armature
// woodcore:/object title

// woodcore:object doc-table reinforcing-steel-table
#doc-table(
  columns: (
    (id: "designation", title: [Désignation]),
    (id: "fsk", title: [Limite d'élasticité caractéristique $f_"sk"$], unit: "N/mm²", kind: "number"),
    (id: "fsd", title: [Limite d'élasticité de calcul $f_"sd"$], unit: "N/mm²", kind: "number"),
    (id: "Es", title: [Module d'élasticité $E_s$], unit: "N/mm²", kind: "number"),
    (id: "gamma", title: [Poids volumique $gamma$], unit: "kN/m³", kind: "number"),
  ),
  hidden: (),
  rows: (
    (designation: [B500B], fsk: 500, fsd: [[…]], Es: [[…]], gamma: 78.5),
  ),
  caption: [Acier d'armature (SIA 262)],
  notes: (
    [Valeurs de calcul selon la norme SIA 262:2025.],
  ),
)
// woodcore:/object reinforcing-steel-table
