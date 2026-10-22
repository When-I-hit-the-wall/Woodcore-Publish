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

// woodcore:object table snow-parameters
#figure(
  table(
    columns: (1fr, auto, auto, auto),
    align: (left, center, right, left),
    table.hline(stroke: 1pt),
    table.header([*Paramètre*], [*Symbole*], [*Valeur*], [*Unité*]),
    table.hline(stroke: 0.5pt),
    [Altitude du lieu], [], [[…]], [m],
    [Altitude de référence], [$h_0$], [[…]], [m],
    [Coefficient d'exposition], [$C_e$], [[…]], [],
    [Coefficient thermique], [$C_T$], [[…]], [],
    [Coefficient de forme de toiture], [$mu$], [[…]], [],
    [Charge de neige sur terrain horizontal], [$s_k$], [[…]], [kN/m²],
    [Charge de neige sur le toit], [$q_k$], [[…]], [kN/m²],
    table.hline(stroke: 1pt),
  ),
  caption: [Paramètres de la charge de neige],
)
// woodcore:/object snow-parameters
