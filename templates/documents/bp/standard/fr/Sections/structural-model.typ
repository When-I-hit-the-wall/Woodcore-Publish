#import "/commands.typ": *

// woodcore:object heading title
== Modèle de la structure et modèle d'analyse
// woodcore:/object title

// woodcore:object table structural-model-table
#figure(
  table(
    columns: (auto, 1fr),
    align: (left, left),
    table.hline(stroke: 1pt),
    [Logiciel et modèle de calcul], [[Programme de calcul, type de modèle (barres, éléments finis), niveau de détail.]],
    [Système statique et appuis], [[…]],
    [Rigidités admises], [[Rigidité du terrain de fondation, des assemblages (modules de glissement), des éléments mixtes, fissuration.]],
    [Effets du second ordre], [[…]],
    [Interaction terrain-structure], [[…]],
    [Humidité et durée d'application des charges (bois)], [[…]],
    [Contrôle de plausibilité], [[Les résultats de l'analyse structurale sont contrôlés quant à leur plausibilité (SIA 260, ch. 3.1.4).]],
    table.hline(stroke: 1pt),
  ),
  caption: [Hypothèses de modélisation],
)
// woodcore:/object structural-model-table
