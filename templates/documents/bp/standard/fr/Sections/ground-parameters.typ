#import "/commands.typ": *

// woodcore:object heading title
== Caractéristiques du terrain de fondation
// woodcore:/object title

// woodcore:object text p1
Les caractéristiques du terrain de fondation sont indiquées dans le rapport géotechnique [auteur, date]. Les valeurs caractéristiques suivantes sont admises pour le dimensionnement (valeurs prudentes selon SIA 260, ch. 3.3.3.5 et SIA 267) :
// woodcore:/object p1

// woodcore:object doc-table ground-parameters-table
#doc-table(
  columns: (
    (id: "layer", title: [Couche]),
    (id: "gamma", title: [Poids volumique $gamma$], unit: "kN/m³", kind: "number"),
    (id: "phi", title: [Angle de frottement $phi'$], unit: "°", kind: "number"),
    (id: "c", title: [Cohésion $c'$], unit: "kPa", kind: "number"),
    (id: "Es", title: [Module de compressibilité $E_s$], unit: "MN/m²", kind: "number"),
    (id: "remark", title: [Remarque]),
  ),
  hidden: ("remark",),
  rows: (
    (layer: [[…]], gamma: [[…]], phi: [[…]], c: [[…]], Es: [[…]], remark: []),
  ),
  caption: [Valeurs caractéristiques du terrain de fondation],
)
// woodcore:/object ground-parameters-table
