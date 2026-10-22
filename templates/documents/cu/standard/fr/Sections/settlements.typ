#import "/commands.typ": *

// woodcore:object heading title
== Tassements
// woodcore:/object title
// woodcore:shared settlements

// woodcore:object text p1
Les tassements ne doivent pas avoir d'effets préjudiciables sur l'ouvrage ni sur son environnement (bâtiments voisins, conduites, routes, etc.). Pour le garantir, les valeurs limites suivantes sont fixées pour le comportement aux tassements :
// woodcore:/object p1

// woodcore:object table settlements-table
#figure(
  table(
    columns: (auto, auto, auto),
    align: (left, right, left),
    table.hline(stroke: 1pt),
    table.header([*Tassement*], [*Valeur limite*], [*Référence / validité*]),
    table.hline(stroke: 0.5pt),
    [Tassement absolu], [[…]], [[dès l'achèvement de la dalle du sous-sol]],
    [Tassement différentiel], [[…]], [[sur une longueur de … m]],
    table.hline(stroke: 1pt),
  ),
  caption: [Valeurs limites des tassements],
)
// woodcore:/object settlements-table
// woodcore:/shared settlements
