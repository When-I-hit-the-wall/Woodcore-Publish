#import "/commands.typ": *

// woodcore:object heading title
== Logistique et transport
// woodcore:/object title
// woodcore:shared transport-dimensions

// woodcore:object text p1
[Moyens de transport envisagés (camion, grue, téléphérique, hélicoptère …), exigences du maître de l'ouvrage, contraintes de dimensions et de poids des éléments préfabriqués, zones de stockage et de transbordement. Moyen de transport principal et exceptions admises.]
// woodcore:/object p1

// woodcore:object table transport-table
#figure(
  table(
    columns: (auto, auto, auto, auto, auto, auto),
    align: (left, right, right, right, right, right),
    table.hline(stroke: 1pt),
    table.header([*Moyen de transport*], [*Longueur max.*], [*Largeur max.*], [*Hauteur max.*], [*Charge suspendue max.*], [*Charge répartie max.*]),
    table.hline(stroke: 0.5pt),
    [[…]], [[…]], [[…]], [[…]], [[…]], [[…]],
    table.hline(stroke: 1pt),
  ),
  caption: [Dimensions maximales des éléments transportés],
)
// woodcore:/object transport-table
// woodcore:/shared transport-dimensions
