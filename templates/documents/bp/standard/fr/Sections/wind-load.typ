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

// woodcore:object doc-table wind-parameters
#doc-table(
  columns: (
    (id: "parameter", title: [Paramètre], kind: "wide"),
    (id: "symbol", title: [Symbole], kind: "math"),
    (id: "value", title: [Valeur], kind: "number"),
    (id: "unit", title: [Unité]),
  ),
  hidden: (),
  rows: (
    (parameter: [Catégorie de terrain], symbol: [], value: [[…]], unit: []),
    (parameter: [Hauteur de référence], symbol: [$z$], value: [[…]], unit: [m]),
    (parameter: [Coefficient de profil], symbol: [$c_h$], value: [[…]], unit: []),
    (parameter: [Pression dynamique de référence], symbol: [$q_(p 0)$], value: [[…]], unit: [kN/m²]),
    (parameter: [Pression dynamique], symbol: [$q_p$], value: [[…]], unit: [kN/m²]),
  ),
  caption: [Paramètres du vent],
)
// woodcore:/object wind-parameters
