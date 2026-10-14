#import "/commands.typ": *

// woodcore:object heading title
== Situations de projet
// woodcore:/object title

// woodcore:object text p1
Les situations de projet considérées incluent toutes les conditions prévisibles durant l'exécution et l'utilisation (SIA 260, ch. 4.2.1). Elles sont réparties en situations durables, transitoires et accidentelles ; les états de construction peuvent être traités comme situations durables ou transitoires (ch. 4.2.2 et 4.2.3).
// woodcore:/object p1

// woodcore:object doc-table design-situations-table
#doc-table(
  columns: (
    (id: "situation", title: [Situation]),
    (id: "description", title: [Description]),
    (id: "governing", title: [Cas de charge déterminants]),
  ),
  hidden: (),
  rows: (
    (situation: [Durable], description: [[Utilisation normale]], governing: [[…]]),
    (situation: [Transitoire], description: [[États de construction]], governing: [[…]]),
    (situation: [Accidentelle], description: [[Séisme, incendie, choc]], governing: [[…]]),
  ),
  caption: [Situations de projet],
)
// woodcore:/object design-situations-table
