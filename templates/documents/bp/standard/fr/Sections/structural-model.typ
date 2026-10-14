#import "/commands.typ": *

// woodcore:object heading title
== Modèle de la structure et modèle d'analyse
// woodcore:/object title

// woodcore:object doc-table structural-model-table
#doc-table(
  columns: (
    (id: "item", title: [Élément]),
    (id: "text", title: [Description], kind: "wide"),
  ),
  hidden: (),
  rows: (
    (item: [Logiciel et modèle de calcul], text: [[Programme de calcul, type de modèle (barres, éléments finis), niveau de détail.]]),
    (item: [Système statique et appuis], text: [[…]]),
    (item: [Rigidités admises], text: [[Rigidité du terrain de fondation, des assemblages (modules de glissement), des éléments mixtes, fissuration.]]),
    (item: [Effets du second ordre], text: [[…]]),
    (item: [Interaction terrain-structure], text: [[…]]),
    (item: [Humidité et durée d'application des charges (bois)], text: [[…]]),
    (item: [Contrôle de plausibilité], text: [[Les résultats de l'analyse structurale sont contrôlés quant à leur plausibilité (SIA 260, ch. 3.1.4).]]),
  ),
  caption: [Hypothèses de modélisation],
  header: false,
)
// woodcore:/object structural-model-table
