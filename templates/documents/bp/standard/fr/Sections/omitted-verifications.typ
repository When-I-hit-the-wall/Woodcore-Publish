#import "/commands.typ": *

// woodcore:object heading title
== Vérifications omises
// woodcore:/object title

// woodcore:object text p1
Il peut être renoncé à une vérification lorsqu'il est établi qu'elle n'est pas déterminante ; il peut aussi être renoncé à l'une des vérifications si l'on montre que les exigences qui la concernent sont d'une importance mineure ou peuvent être satisfaites par des mesures constructives ou d'exécution. La procédure choisie doit dans tous les cas être documentée dans la base de projet (SIA 260, ch. 4.4.1.2 et 4.4.1.3).
// woodcore:/object p1

// woodcore:object table omitted-verifications-table
#figure(
  table(
    columns: (auto, auto, auto),
    align: (left, left, left),
    table.hline(stroke: 1pt),
    table.header([*Vérification omise*], [*Motif*], [*Justification*]),
    table.hline(stroke: 0.5pt),
    [[…]], [Non déterminante], [[…]],
    table.hline(stroke: 1pt),
  ),
  caption: [Vérifications omises],
)
// woodcore:/object omitted-verifications-table
