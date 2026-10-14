#import "/commands.typ": *

// woodcore:object heading title
== Protection thermique et protection contre l'humidité
// woodcore:/object title

// woodcore:object text p1
Les coefficients de transmission thermique maximaux $U_"max"$ selon la norme #cite-norm(norm: "SIA 180") doivent être respectés. Pour la preuve par performances ponctuelles, les valeurs de la réglementation cantonale sur l'énergie [canton, ordonnance] s'appliquent aux constructions neuves. [Label visé (Minergie …) ou non.]
// woodcore:/object p1

// woodcore:object doc-table u-values-table
#doc-table(
  columns: (
    (id: "element", title: [Élément]),
    (id: "against", title: [Contre]),
    (id: "U", title: [Coefficient de transmission thermique $U$], unit: "W/(m²K)", kind: "number"),
    (id: "basis", title: [Base]),
  ),
  hidden: (),
  rows: (
    (element: [Toiture], against: [Extérieur], U: [[…]], basis: [[ordonnance cantonale]]),
    (element: [Paroi extérieure], against: [Extérieur], U: [[…]], basis: [[ordonnance cantonale]]),
  ),
  caption: [Valeurs limites des coefficients de transmission thermique],
)
// woodcore:/object u-values-table
