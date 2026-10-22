#import "/commands.typ": *

// woodcore:object heading title
== Situations de projet
// woodcore:/object title

// woodcore:object text p1
Les situations de projet considérées incluent toutes les conditions prévisibles durant l'exécution et l'utilisation (SIA 260, ch. 4.2.1). Elles sont réparties en situations durables, transitoires et accidentelles ; les états de construction peuvent être traités comme situations durables ou transitoires (ch. 4.2.2 et 4.2.3).
// woodcore:/object p1

// woodcore:object table design-situations-table
#figure(
  table(
    columns: (auto, auto, auto),
    align: (left, left, left),
    table.hline(stroke: 1pt),
    table.header([*Situation*], [*Description*], [*Cas de charge déterminants*]),
    table.hline(stroke: 0.5pt),
    [Durable], [[Utilisation normale]], [[…]],
    [Transitoire], [[États de construction]], [[…]],
    [Accidentelle], [[Séisme, incendie, choc]], [[…]],
    table.hline(stroke: 1pt),
  ),
  caption: [Situations de projet],
)
// woodcore:/object design-situations-table
