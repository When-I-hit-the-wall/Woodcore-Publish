#import "/commands.typ": *

// woodcore:object heading title
== Limites de déformation (flèches)
// woodcore:/object title
// woodcore:shared deformation-limits

// woodcore:object text p1
Les flèches sont limitées aux valeurs indicatives de la norme SIA 260, annexe A, tableau 3 ; elles sont déterminées selon les normes SIA 262 à 266. Des valeurs différentes peuvent être convenues en accord avec les exigences d'utilisation, notamment pour les éléments secondaires ; elles sont alors consignées dans la base de projet. [Le maître de l'ouvrage n'émet pas d'exigences plus sévères que celles de la norme : oui / non.]
// woodcore:/object p1

// woodcore:object doc-table deformation-table
#doc-table(
  columns: (
    (id: "element", title: [Élément]),
    (id: "criterion", title: [Critère]),
    (id: "limit", title: [Valeur limite], kind: "math"),
    (id: "load_case", title: [Cas de charge (SIA 260, tab. 3)]),
  ),
  hidden: (),
  rows: (
    (element: [Planchers et poutres], criterion: [Éléments incorporés à caractère fragile], limit: [$w <= l \/ 500$], load_case: [rare (20)]),
    (element: [Planchers et poutres], criterion: [Éléments incorporés à caractère ductile], limit: [$w <= l \/ 350$], load_case: [fréquent (21)]),
    (element: [Planchers et poutres], criterion: [Utilisation, exploitation et confort (flèche due aux actions variables)], limit: [$w <= l \/ 350$], load_case: [fréquent (21)]),
    (element: [Planchers et poutres], criterion: [Aspect (après déduction d'une éventuelle contreflèche)], limit: [$w <= l \/ 300$], load_case: [quasi permanent (22)]),
  ),
  caption: [Flèches limites],
)
// woodcore:/object deformation-table

// woodcore:object text p2
Flèche due aux actions, y compris les effets à long terme, après le montage de tous les éléments secondaires et de l'équipement technique. Si des éléments incorporés réagissent de manière particulièrement sensible aux déformations de la structure porteuse, des mesures constructives contre les dommages sont à prévoir en plus des mesures de dimensionnement ou à leur place.
// woodcore:/object p2
// woodcore:/shared deformation-limits
