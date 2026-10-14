#import "/commands.typ": *

// woodcore:object heading title
== Déplacements horizontaux
// woodcore:/object title

// woodcore:object text p1
Les déplacements horizontaux dus aux actions variables sont limités aux valeurs indicatives de la norme SIA 260, annexe A, tableau 4 ; h désigne la hauteur d'étage et H la hauteur du bâtiment. Pour la situation de projet séisme, les déplacements horizontaux par étage sont limités à 1/500, respectivement 1/200 de la hauteur d'étage en présence d'éléments incorporés fragiles, respectivement ductiles (ch. 4.4.4.5).
// woodcore:/object p1

// woodcore:object doc-table horizontal-limits-table
#doc-table(
  columns: (
    (id: "criterion", title: [Critère]),
    (id: "limit", title: [Valeur limite], kind: "math"),
    (id: "load_case", title: [Cas de charge (SIA 260, tab. 4)]),
  ),
  hidden: (),
  rows: (
    (criterion: [Éléments incorporés à caractère fragile], limit: [$u <= h \/ 500$], load_case: [rare (20)]),
    (criterion: [Éléments incorporés à caractère ductile], limit: [$u <= h \/ 200$], load_case: [fréquent (21)]),
    (criterion: [Utilisation et exploitation], limit: [$u <= H \/ 300$], load_case: [fréquent (21)]),
    (criterion: [Aspect], limit: [$u <= h \/ 250$], load_case: [quasi permanent (22)]),
  ),
  caption: [Déplacements horizontaux limites],
)
// woodcore:/object horizontal-limits-table
