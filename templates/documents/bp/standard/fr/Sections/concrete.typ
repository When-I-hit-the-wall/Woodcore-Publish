#import "/commands.typ": *

// woodcore:object heading title
== Béton
// woodcore:/object title

// woodcore:object doc-table concrete-table
#doc-table(
  columns: (
    (id: "member", title: [Élément]),
    (id: "class", title: [Classe de résistance]),
    (id: "fck", title: [Résistance caractéristique $f_"ck"$], unit: "N/mm²", kind: "number"),
    (id: "fcd", title: [Résistance de calcul $f_"cd"$], unit: "N/mm²", kind: "number"),
    (id: "taucd", title: [Résistance au cisaillement de calcul $tau_"cd"$], unit: "N/mm²", kind: "number"),
    (id: "Ecm", title: [Module d'élasticité moyen $E_"cm"$], unit: "N/mm²", kind: "number"),
    (id: "gamma", title: [Poids volumique $gamma$], unit: "kN/m³", kind: "number"),
  ),
  hidden: ("Ecm",),
  rows: (
    (member: [[Élément]], class: [C25/30], fck: 25, fcd: [[…]], taucd: [[…]], Ecm: [[…]], gamma: 25),
    (member: [[Élément]], class: [C30/37], fck: 30, fcd: [[…]], taucd: [[…]], Ecm: [[…]], gamma: 25),
  ),
  caption: [Béton armé (SIA 262)],
  notes: (
    [Valeurs de calcul selon la norme SIA 262:2025.],
    [Les exigences de durabilité (classes d'exposition) sont indiquées dans la section « Durabilité ».],
  ),
)
// woodcore:/object concrete-table
