#import "/commands.typ": *

// woodcore:object heading title
== Logistique et transport
// woodcore:/object title
// woodcore:shared transport-dimensions

// woodcore:object text p1
[Moyens de transport envisagés (camion, grue, téléphérique, hélicoptère …), exigences du maître de l'ouvrage, contraintes de dimensions et de poids des éléments préfabriqués, zones de stockage et de transbordement. Moyen de transport principal et exceptions admises.]
// woodcore:/object p1

// woodcore:object doc-table transport-table
#doc-table(
  columns: (
    (id: "transport", title: [Moyen de transport]),
    (id: "length", title: [Longueur max.], unit: "mm", kind: "number"),
    (id: "width", title: [Largeur max.], unit: "mm", kind: "number"),
    (id: "height", title: [Hauteur max.], unit: "mm", kind: "number"),
    (id: "hung", title: [Charge suspendue max.], unit: "kg", kind: "number"),
    (id: "distributed", title: [Charge répartie max.], unit: "kg", kind: "number"),
  ),
  hidden: (),
  rows: (
    (transport: [[…]], length: [[…]], width: [[…]], height: [[…]], hung: [[…]], distributed: [[…]]),
  ),
  caption: [Dimensions maximales des éléments transportés],
)
// woodcore:/object transport-table
// woodcore:/shared transport-dimensions
