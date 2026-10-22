#import "/commands.typ": *

// woodcore:object heading title
== Situations de danger
// woodcore:/object title

// woodcore:object text p1
Les situations de danger possibles ont été examinées et les mesures propres à tenir ces dangers sous contrôle ou à les réduire à un niveau acceptable sont définies (SIA 260, ch. 2.4.4). Les situations de danger considérées, avec leurs mesures, la suite à donner et les hypothèses de dimensionnement, sont les suivantes :
// woodcore:/object p1

// woodcore:object text hazard-influences
*Influences pouvant représenter un danger (SIA 260, ch. 2.4.5)* :
- *Écarts par rapport aux valeurs admises pour les actions*
- *Actions physiques, p. ex. humidité ou température*
- *Actions biologiques, p. ex. insectes ou champignons*
- *Réduction de la résistance par le feu, une explosion, un choc, une rupture de conduite ou un séisme*
// woodcore:/object hazard-influences

// woodcore:object table hazard-scenarios-table
#figure(
  table(
    columns: (auto, auto, auto, auto),
    align: (left, left, left, left),
    table.hline(stroke: 1pt),
    table.header([*Situation de danger*], [*Mesures*], [*Suite à donner*], [*Hypothèses pour l'analyse et le dimensionnement*]),
    table.hline(stroke: 0.5pt),
    [[Incendie]], [[Compartiments coupe-feu, résistance au feu, dimensions suffisantes des éléments, revêtement de protection incendie]], [[Concept de protection incendie ; étude de protection incendie]], [[R 60]],
    [[Séisme]], [[Dimensionnement ; mesures constructives selon SIA 261]], [[Calcul statique]], [[Zone, classe de terrain, classe d'ouvrage, q]],
    table.hline(stroke: 1pt),
  ),
  caption: [Situations de danger et mesures],
)
// woodcore:/object hazard-scenarios-table
