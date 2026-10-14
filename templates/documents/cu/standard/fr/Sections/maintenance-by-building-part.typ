#import "/commands.typ": *

// woodcore:object heading title
== Exigences par partie d'ouvrage
// woodcore:/object title

// woodcore:object doc-table maintenance-table
#doc-table(
  columns: (
    (id: "item", title: [Élément]),
    (id: "text", title: [Description], kind: "wide"),
  ),
  hidden: (),
  rows: (
    (item: [Toiture], text: [[Étanchéité, évacuation des eaux accessible, toiture praticable pour l'entretien et le déneigement. Hauteur de neige prise en compte au dimensionnement ; au-delà, déneigement à la charge du maître de l'ouvrage.]]),
    (item: [Étages], text: [[…]]),
    (item: [Rez-de-chaussée], text: [[…]]),
    (item: [Sous-sols], text: [[…]]),
    (item: [Façade], text: [[Remplaçable indépendamment des éléments porteurs ; matériau souhaité (p. ex. bardage en bois).]]),
  ),
  caption: [Exigences d'exploitation et d'entretien],
  header: false,
)
// woodcore:/object maintenance-table
