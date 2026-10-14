#import "/commands.typ": *

// woodcore:object heading title
== Coefficients de réduction
// woodcore:/object title

// woodcore:object text p1
Les coefficients de réduction ψ₀, ψ₁ et ψ₂ tiennent compte de la probabilité réduite de l'apparition simultanée des valeurs les plus défavorables de plusieurs actions indépendantes ; ils donnent la valeur rare, fréquente et quasi permanente d'une action variable (SIA 260, ch. 3.2.3 et annexe A, tableau 2). [La charge de neige dépend de la hauteur de référence h₀ selon SIA 261.]
// woodcore:/object p1

// woodcore:object doc-table reduction-factors-table
#doc-table(
  columns: (
    (id: "action", title: [Action]),
    (id: "psi_0", title: [$psi_0$], kind: "math"),
    (id: "psi_1", title: [$psi_1$], kind: "math"),
    (id: "psi_2", title: [$psi_2$], kind: "math"),
  ),
  hidden: (),
  rows: (
    (action: [Charge utile, catégorie [A]], psi_0: 0.7, psi_1: 0.5, psi_2: 0.3),
    (action: [Charge utile, catégorie [C]], psi_0: 0.7, psi_1: 0.7, psi_2: 0.6),
    (action: [Charge utile, catégorie H], psi_0: 0, psi_1: 0, psi_2: 0),
    (action: [Neige], psi_0: [$1 - 60 \/ h_0$], psi_1: [$1 - 250 \/ h_0$], psi_2: [$1 - 1000 \/ h_0$]),
    (action: [Vent], psi_0: 0.6, psi_1: 0.5, psi_2: 0),
  ),
  caption: [Coefficients de réduction pour les bâtiments],
)
// woodcore:/object reduction-factors-table
