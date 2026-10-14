#import "/commands.typ": *

// woodcore:object heading title
=== Choc de véhicules
// woodcore:/object title
// woodcore:shared impact

// woodcore:object text p1
Le choc est une action accidentelle (SIA 261, ch. 14.1.1). Il est pris en compte lorsque la structure se trouve à moins de 3 m (en localité) ou de 10 m (hors localité) du bord de la chaussée (ch. 14.2.1). Pour les chocs de bateaux, d'hélicoptères, d'avions ou de parties tombantes, les forces de remplacement sont fixées pour le projet et consignées dans la base de projet (ch. 14.1.8). [Mesures de protection (bancs, bornes) : …]
// woodcore:/object p1

// woodcore:object doc-table impact-table
#doc-table(
  columns: (
    (id: "storey", title: [Niveau]),
    (id: "area", title: [Zone]),
    (id: "use", title: [Utilisation], kind: "wide"),
    (id: "category", title: [Catégorie (SIA 261)], kind: "math"),
    (id: "force", title: [Force d'impact $Q_"gd"$], unit: "kN", kind: "number"),
    (id: "height", title: [Hauteur d'application], unit: "m", kind: "number"),
  ),
  hidden: (),
  rows: (
    (storey: [[…]], area: [[…]], use: [[Parking pour véhicules jusqu'à 3.5 t]], category: "F", force: 60, height: 0.6),
    (storey: [[…]], area: [[…]], use: [[Zone de livraison, véhicules de 3.5 t à 16 t]], category: "G", force: 180, height: 1.2),
  ),
  caption: [Forces d'impact de véhicules routiers dans les bâtiments],
)
// woodcore:/object impact-table
// woodcore:/shared impact
