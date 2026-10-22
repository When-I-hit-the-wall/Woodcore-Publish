#import "/commands.typ": *

// woodcore:object heading title
== Durée d'utilisation
// woodcore:/object title
// woodcore:shared service-life

// woodcore:object text p1
La durée d'utilisation est la période pendant laquelle, selon l'état actuel des connaissances, l'ouvrage doit satisfaire aux usages définis dans la convention d'utilisation. Elle est convenue avec le maître de l'ouvrage ; pendant cette période, le maître de l'ouvrage effectue les travaux d'entretien périodiques.
// woodcore:/object p1

// woodcore:object text service-life-class
*Durée d'utilisation de la structure porteuse (valeurs indicatives, SIA 260, ch. 2.3.2)* : Bâtiment et autre ouvrage d'importance normale : 50 ans
// woodcore:/object service-life-class

// woodcore:object table service-life-table
#figure(
  table(
    columns: (auto, auto),
    align: (left, left),
    table.hline(stroke: 1pt),
    table.header([*Élément*], [*Durée d'utilisation*]),  // woodcore:hidden 3=[Remarque]
    table.hline(stroke: 0.5pt),
    [Structure porteuse], [50 ans],  // woodcore:hidden 3=[]
    [Étanchéités], [25 ans],  // woodcore:hidden 3=[]
    [Façade], [25 ans],  // woodcore:hidden 3=[]
    [Couverture], [25 ans],  // woodcore:hidden 3=[]
    [Éléments remplaçables], [25 ans],  // woodcore:hidden 3=[]
    table.hline(stroke: 1pt),
  ),
  caption: [Durée d'utilisation convenue par élément],
)
// woodcore:/object service-life-table
// woodcore:/shared service-life
