#import "/commands.typ": *

// woodcore:object heading title
== Humidité du bois et fluage
// woodcore:/object title

// woodcore:object text moisture-class
*Classe d'humidité (SIA 265, tab. 3)* : Classe d'humidité 1 : humidité moyenne du bois ≤ 12 %, à l'abri des intempéries
// woodcore:/object moisture-class

// woodcore:object table moisture-factors
#figure(
  table(
    columns: (auto, 1fr),
    align: (left, left),
    table.hline(stroke: 1pt),
    [Réduction de la résistance $η_w$], [[selon la classe d'humidité choisie (SIA 265, tab. 4)]],
    [Réduction de la rigidité $η_w$], [[selon la classe d'humidité choisie (SIA 265, tab. 4)]],
    [Coefficient de fluage φ, bois préconditionné à l'humidité d'utilisation], [[…]],
    [Coefficient de fluage φ, bois mis en œuvre humide ou partiellement séché], [[…]],
    table.hline(stroke: 1pt),
  ),
  caption: [Coefficients d'humidité et de fluage],
)
// woodcore:/object moisture-factors
