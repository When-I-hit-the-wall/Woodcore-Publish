#import "/commands.typ": *

// woodcore:object heading title
== Choc de véhicules
// woodcore:/object title
// woodcore:shared impact

// woodcore:object text p1
Le choc est une action accidentelle (SIA 261, ch. 14.1.1). Il est pris en compte lorsque la structure se trouve à moins de 3 m (en localité) ou de 10 m (hors localité) du bord de la chaussée (ch. 14.2.1). Pour les chocs de bateaux, d'hélicoptères, d'avions ou de parties tombantes, les forces de remplacement sont fixées pour le projet et consignées dans la base de projet (ch. 14.1.8). [Mesures de protection (bancs, bornes) : …]
// woodcore:/object p1

// woodcore:object table impact-table
#figure(
  table(
    columns: (auto, auto, 1fr, auto, auto, auto),
    align: (left, left, left, center, right, right),
    table.hline(stroke: 1pt),
    table.header([*Niveau*], [*Zone*], [*Utilisation*], [*Catégorie (SIA 261)*], [*Force d'impact $Q_"gd"$*], [*Hauteur d'application*]),
    table.hline(stroke: 0.5pt),
    [[…]], [[…]], [[Parking pour véhicules jusqu'à 3.5 t]], [F], [60], [0.6],
    [[…]], [[…]], [[Zone de livraison, véhicules de 3.5 t à 16 t]], [G], [180], [1.2],
    table.hline(stroke: 1pt),
  ),
  caption: [Forces d'impact de véhicules routiers dans les bâtiments],
)
// woodcore:/object impact-table
// woodcore:/shared impact
