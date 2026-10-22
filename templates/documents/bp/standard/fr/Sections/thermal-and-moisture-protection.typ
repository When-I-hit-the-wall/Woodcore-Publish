#import "/commands.typ": *

// woodcore:object heading title
== Protection thermique et protection contre l'humidité
// woodcore:/object title

// woodcore:object text p1
Les coefficients de transmission thermique maximaux $U_"max"$ selon la norme #cite-norm(norm: "SIA 180") doivent être respectés. Pour la preuve par performances ponctuelles, les valeurs de la réglementation cantonale sur l'énergie [canton, ordonnance] s'appliquent aux constructions neuves. [Label visé (Minergie …) ou non.]
// woodcore:/object p1

// woodcore:object table u-values-table
#figure(
  table(
    columns: (auto, auto, auto, auto),
    align: (left, left, right, left),
    table.hline(stroke: 1pt),
    table.header([*Élément*], [*Contre*], [*Coefficient de transmission thermique $U$*], [*Base*]),
    table.hline(stroke: 0.5pt),
    [Toiture], [Extérieur], [[…]], [[ordonnance cantonale]],
    [Paroi extérieure], [Extérieur], [[…]], [[ordonnance cantonale]],
    table.hline(stroke: 1pt),
  ),
  caption: [Valeurs limites des coefficients de transmission thermique],
)
// woodcore:/object u-values-table
