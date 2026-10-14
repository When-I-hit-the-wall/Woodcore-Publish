#import "/commands.typ": *

// woodcore:object heading title
== Étanchéité à l'eau
// woodcore:/object title

// woodcore:object text p1
[Concept d'étanchéité des parties d'ouvrage enterrées (p. ex. cuve blanche ou cuve jaune) : les exigences sont fixées en référence à la norme SIA 272 ; le concept détaillé est établi en phase d'exécution avec l'entreprise et, le cas échéant, le fournisseur du système. La responsabilité du respect des critères incombe à l'entreprise ou à l'entreprise d'étanchéité. La détection du risque de condensation relève de la physique du bâtiment.]
// woodcore:/object p1

// woodcore:object doc-table sealing-classes-table
#doc-table(
  columns: (
    (id: "class", title: [Classe], kind: "number"),
    (id: "definition", title: [Définition], kind: "wide"),
    (id: "parts", title: [Parties d'ouvrage]),
  ),
  hidden: (),
  rows: (
    (class: 1, definition: [Complètement sec ; aucune tache d'humidité admise sur les surfaces côté sec.], parts: [[…]]),
    (class: 2, definition: [Sec à légèrement humide ; taches d'humidité isolées admises ; pas d'eau qui goutte sur les surfaces côté sec.], parts: [[…]]),
    (class: 3, definition: [Humide ; taches d'humidité locales et quelques gouttes admises ; injection ultérieure des fissures acceptée.], parts: [[…]]),
    (class: 4, definition: [Humide à mouillé ; taches d'humidité et gouttes admises.], parts: [[…]]),
  ),
  caption: [Classes d'étanchéité et affectation aux parties d'ouvrage],
)
// woodcore:/object sealing-classes-table
