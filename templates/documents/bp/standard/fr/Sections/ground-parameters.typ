#import "/commands.typ": *

// woodcore:object heading title
== Caractéristiques du terrain de fondation
// woodcore:/object title

// woodcore:object text p1
Les caractéristiques du terrain de fondation sont indiquées dans le rapport géotechnique [auteur, date]. Les valeurs caractéristiques suivantes sont admises pour le dimensionnement (valeurs prudentes selon SIA 260, ch. 3.3.3.5 et SIA 267) :
// woodcore:/object p1

// woodcore:object table ground-parameters-table
#figure(
  table(
    columns: (auto, auto, auto, auto, auto),
    align: (left, right, right, right, right),
    table.hline(stroke: 1pt),
    table.header([*Couche*], [*Poids volumique $gamma$*], [*Angle de frottement $phi'$*], [*Cohésion $c'$*], [*Module de compressibilité $E_s$*]),  // woodcore:hidden 6=[Remarque]
    table.hline(stroke: 0.5pt),
    [[…]], [[…]], [[…]], [[…]], [[…]],  // woodcore:hidden 6=[]
    table.hline(stroke: 1pt),
  ),
  caption: [Valeurs caractéristiques du terrain de fondation],
)
// woodcore:/object ground-parameters-table
