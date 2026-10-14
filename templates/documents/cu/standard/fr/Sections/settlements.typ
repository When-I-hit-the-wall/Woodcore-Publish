#import "/commands.typ": *

// woodcore:object heading title
== Tassements
// woodcore:/object title
// woodcore:shared settlements

// woodcore:object text p1
Les tassements ne doivent pas avoir d'effets préjudiciables sur l'ouvrage ni sur son environnement (bâtiments voisins, conduites, routes, etc.). Pour le garantir, les valeurs limites suivantes sont fixées pour le comportement aux tassements :
// woodcore:/object p1

// woodcore:object doc-table settlements-table
#doc-table(
  columns: (
    (id: "kind", title: [Tassement]),
    (id: "limit", title: [Valeur limite], unit: "mm", kind: "number"),
    (id: "basis", title: [Référence / validité]),
  ),
  hidden: (),
  rows: (
    (kind: [Tassement absolu], limit: [[…]], basis: [[dès l'achèvement de la dalle du sous-sol]]),
    (kind: [Tassement différentiel], limit: [[…]], basis: [[sur une longueur de … m]]),
  ),
  caption: [Valeurs limites des tassements],
)
// woodcore:/object settlements-table
// woodcore:/shared settlements
