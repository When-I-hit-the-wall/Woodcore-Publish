#import "/commands.typ": *

// woodcore:object heading title
== Humidité du bois et fluage
// woodcore:/object title

// woodcore:object doc-choice moisture-class
#doc-choice(
  label: [Classe d'humidité (SIA 265, tab. 3)],
  options: (
    (id: "1", label: [Classe d'humidité 1 : humidité moyenne du bois ≤ 12 %, à l'abri des intempéries]),
    (id: "2", label: [Classe d'humidité 2 : > 12 à 20 %, partiellement protégé ou directement exposé aux intempéries]),
    (id: "3", label: [Classe d'humidité 3 : > 20 %, humide ou sous l'eau]),
  ),
  selected: "1",
)
// woodcore:/object moisture-class

// woodcore:object doc-table moisture-factors
#doc-table(
  columns: (
    (id: "item", title: [Élément]),
    (id: "text", title: [Description], kind: "wide"),
  ),
  hidden: (),
  rows: (
    (item: [Réduction de la résistance $η_w$], text: [[selon la classe d'humidité choisie (SIA 265, tab. 4)]]),
    (item: [Réduction de la rigidité $η_w$], text: [[selon la classe d'humidité choisie (SIA 265, tab. 4)]]),
    (item: [Coefficient de fluage φ, bois préconditionné à l'humidité d'utilisation], text: [[…]]),
    (item: [Coefficient de fluage φ, bois mis en œuvre humide ou partiellement séché], text: [[…]]),
  ),
  caption: [Coefficients d'humidité et de fluage],
  header: false,
)
// woodcore:/object moisture-factors
