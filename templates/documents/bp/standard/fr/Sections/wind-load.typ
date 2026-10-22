#import "/commands.typ": *

// woodcore:object heading title
=== Vent
// woodcore:/object title

// woodcore:object text p1
Les actions du vent sont déterminées selon la norme SIA 261, chapitre 6. La pression dynamique est :
// woodcore:/object p1

// woodcore:object text p2
$ q_p = c_h dot q_(p 0) $
// woodcore:/object p2

// woodcore:object text p3
la valeur de référence $q_"p0"$ étant tirée de l'annexe E, la catégorie de terrain et le coefficient de profil $c_h$ de l'article 6.2.1 (tableau 4). Les coefficients de pression et de force sont ceux de l'annexe C.
// woodcore:/object p3

// woodcore:object table wind-parameters
#figure(
  table(
    columns: (1fr, auto, auto, auto),
    align: (left, center, right, left),
    table.hline(stroke: 1pt),
    table.header([*Paramètre*], [*Symbole*], [*Valeur*], [*Unité*]),
    table.hline(stroke: 0.5pt),
    [Catégorie de terrain], [], [[…]], [],
    [Hauteur de référence], [$z$], [[…]], [m],
    [Coefficient de profil], [$c_h$], [[…]], [],
    [Pression dynamique de référence], [$q_(p 0)$], [[…]], [kN/m²],
    [Pression dynamique], [$q_p$], [[…]], [kN/m²],
    table.hline(stroke: 1pt),
  ),
  caption: [Paramètres du vent],
)
// woodcore:/object wind-parameters
