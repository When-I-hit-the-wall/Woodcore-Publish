#import "/commands.typ": *

// woodcore:object heading title
=== Neige
// woodcore:/object title

// woodcore:object text p1
La charge de neige est déterminée selon la norme SIA 261, chapitre 5, pour le site du projet. La valeur caractéristique sur un toit, rapportée à la projection horizontale, est :
// woodcore:/object p1

// woodcore:object text p2
$ q_k = mu_i dot C_e dot C_T dot s_k $
// woodcore:/object p2

// woodcore:object text p3
avec la valeur sur terrain horizontal (ch. 5.2.6), la hauteur de référence h₀ étant déterminée selon l'annexe D :
// woodcore:/object p3

// woodcore:object text p4
$ s_k = [1 + (h_0 / 350)^2] dot 0.4 " kN/m"^2 >= 0.9 " kN/m"^2 $
// woodcore:/object p4

// woodcore:object text p5
[Une valeur retenue d'entente avec le maître de l'ouvrage, ou fondée sur des mesures, est à justifier ici (ch. 5.2.1).]
// woodcore:/object p5

// woodcore:object doc-table snow-parameters
#doc-table(
  columns: (
    (id: "parameter", title: [Paramètre], kind: "wide"),
    (id: "symbol", title: [Symbole], kind: "math"),
    (id: "value", title: [Valeur], kind: "number"),
    (id: "unit", title: [Unité]),
  ),
  hidden: (),
  rows: (
    (parameter: [Altitude du lieu], symbol: [], value: [[…]], unit: [m]),
    (parameter: [Altitude de référence], symbol: [$h_0$], value: [[…]], unit: [m]),
    (parameter: [Coefficient d'exposition], symbol: [$C_e$], value: [[…]], unit: []),
    (parameter: [Coefficient thermique], symbol: [$C_T$], value: [[…]], unit: []),
    (parameter: [Coefficient de forme de toiture], symbol: [$mu$], value: [[…]], unit: []),
    (parameter: [Charge de neige sur terrain horizontal], symbol: [$s_k$], value: [[…]], unit: [kN/m²]),
    (parameter: [Charge de neige sur le toit], symbol: [$q_k$], value: [[…]], unit: [kN/m²]),
  ),
  caption: [Paramètres de la charge de neige],
)
// woodcore:/object snow-parameters
