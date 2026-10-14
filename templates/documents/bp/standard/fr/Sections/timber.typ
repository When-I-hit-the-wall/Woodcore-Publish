#import "/commands.typ": *

// woodcore:object heading title
== Bois et dérivés du bois
// woodcore:/object title

// woodcore:object doc-table timber-table
#doc-table(
  columns: (
    (id: "designation", title: [Désignation]),
    (id: "fmd", title: [Flexion $f_"md"$], unit: "N/mm²", kind: "number"),
    (id: "fc0d", title: [Compression parallèle au fil $f_(c,0,d)$], unit: "N/mm²", kind: "number"),
    (id: "fvd", title: [Cisaillement $f_"vd"$], unit: "N/mm²", kind: "number"),
    (id: "E0", title: [Module d'élasticité moyen $E_(0,"mean")$], unit: "N/mm²", kind: "number"),
    (id: "rho", title: [Masse volumique caractéristique $rho_k$], unit: "kg/m³", kind: "number"),
    (id: "gamma", title: [Poids volumique $gamma$], unit: "kN/m³", kind: "number"),
  ),
  hidden: ("rho", "gamma"),
  rows: (
    (designation: [C24], fmd: 14.1, fc0d: 12.4, fvd: 1.5, E0: 11000, rho: 350, gamma: 5),
    (designation: [GL24h], fmd: 16.0, fc0d: 16.0, fvd: 1.8, E0: 11500, rho: 385, gamma: 5),
  ),
  caption: [Bois massif et lamellé-collé (SIA 265, valeurs de calcul pour la classe d'humidité 1)],
  notes: (
    [Les propriétés de résistance et de rigidité, les coefficients de résistance et les coefficients tenant compte de la durée d'application des charges sont appliqués selon les normes SIA en vigueur. Pour les dérivés du bois (panneaux, bois lamellé croisé), les valeurs sont celles de la norme SIA 265/1.],
  ),
)
// woodcore:/object timber-table
