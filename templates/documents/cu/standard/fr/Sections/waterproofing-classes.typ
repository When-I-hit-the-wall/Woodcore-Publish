#import "/commands.typ": *

// woodcore:object heading title
== Étanchéité à l'eau
// woodcore:/object title

// woodcore:object text p1
[Concept d'étanchéité des parties d'ouvrage enterrées (p. ex. cuve blanche ou cuve jaune) : les exigences sont fixées en référence à la norme SIA 272 ; le concept détaillé est établi en phase d'exécution avec l'entreprise et, le cas échéant, le fournisseur du système. La responsabilité du respect des critères incombe à l'entreprise ou à l'entreprise d'étanchéité. La détection du risque de condensation relève de la physique du bâtiment.]
// woodcore:/object p1

// woodcore:object table sealing-classes-table
#figure(
  table(
    columns: (auto, 1fr, auto),
    align: (right, left, left),
    table.hline(stroke: 1pt),
    table.header([*Classe*], [*Définition*], [*Parties d'ouvrage*]),
    table.hline(stroke: 0.5pt),
    [1], [Complètement sec ; aucune tache d'humidité admise sur les surfaces côté sec.], [[…]],
    [2], [Sec à légèrement humide ; taches d'humidité isolées admises ; pas d'eau qui goutte sur les surfaces côté sec.], [[…]],
    [3], [Humide ; taches d'humidité locales et quelques gouttes admises ; injection ultérieure des fissures acceptée.], [[…]],
    [4], [Humide à mouillé ; taches d'humidité et gouttes admises.], [[…]],
    table.hline(stroke: 1pt),
  ),
  caption: [Classes d'étanchéité et affectation aux parties d'ouvrage],
)
// woodcore:/object sealing-classes-table
