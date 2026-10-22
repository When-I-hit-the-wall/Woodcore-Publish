#import "/commands.typ": *

// woodcore:object heading title
== Coefficients de réduction
// woodcore:/object title

// woodcore:object text p1
Les coefficients de réduction ψ₀, ψ₁ et ψ₂ tiennent compte de la probabilité réduite de l'apparition simultanée des valeurs les plus défavorables de plusieurs actions indépendantes ; ils donnent la valeur rare, fréquente et quasi permanente d'une action variable (SIA 260, ch. 3.2.3 et annexe A, tableau 2). [La charge de neige dépend de la hauteur de référence h₀ selon SIA 261.]
// woodcore:/object p1

// woodcore:object table reduction-factors-table
#figure(
  table(
    columns: (auto, auto, auto, auto),
    align: (left, center, center, center),
    table.hline(stroke: 1pt),
    table.header([*Action*], [*$psi_0$*], [*$psi_1$*], [*$psi_2$*]),
    table.hline(stroke: 0.5pt),
    [Charge utile, catégorie [A]], [0.7], [0.5], [0.3],
    [Charge utile, catégorie [C]], [0.7], [0.7], [0.6],
    [Charge utile, catégorie H], [0], [0], [0],
    [Neige], [$1 - 60 \/ h_0$], [$1 - 250 \/ h_0$], [$1 - 1000 \/ h_0$],
    [Vent], [0.6], [0.5], [0],
    table.hline(stroke: 1pt),
  ),
  caption: [Coefficients de réduction pour les bâtiments],
)
// woodcore:/object reduction-factors-table
