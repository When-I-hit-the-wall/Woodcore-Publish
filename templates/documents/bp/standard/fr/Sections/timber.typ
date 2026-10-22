#import "/commands.typ": *

// woodcore:object heading title
== Bois et dérivés du bois
// woodcore:/object title

// woodcore:object table timber-table
#figure(
  table(
    columns: (auto, auto, auto, auto, auto),
    align: (left, right, right, right, right),
    table.hline(stroke: 1pt),
    table.header([*Désignation*], [*Flexion $f_"md"$*], [*Compression parallèle au fil $f_(c,0,d)$*], [*Cisaillement $f_"vd"$*], [*Module d'élasticité moyen $E_(0,"mean")$*]),  // woodcore:hidden 6=[Masse volumique caractéristique $rho_k$] 7=[Poids volumique $gamma$]
    table.hline(stroke: 0.5pt),
    [C24], [14.1], [12.4], [1.5], [11000],  // woodcore:hidden 6=[350] 7=[5]
    [GL24h], [16.0], [16.0], [1.8], [11500],  // woodcore:hidden 6=[385] 7=[5]
    table.hline(stroke: 1pt),
  ),
  caption: [Bois massif et lamellé-collé (SIA 265, valeurs de calcul pour la classe d'humidité 1)],
)
// woodcore:/object timber-table

// woodcore:object text timber-table-notes
Les propriétés de résistance et de rigidité, les coefficients de résistance et les coefficients tenant compte de la durée d'application des charges sont appliqués selon les normes SIA en vigueur. Pour les dérivés du bois (panneaux, bois lamellé croisé), les valeurs sont celles de la norme SIA 265/1.
// woodcore:/object timber-table-notes
