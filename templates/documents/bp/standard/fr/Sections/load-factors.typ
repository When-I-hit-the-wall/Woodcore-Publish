#import "/commands.typ": *

// woodcore:object heading title
== Facteurs de charge
// woodcore:/object title

// woodcore:object text p1
Type d'ouvrage : [bâtiment]. Les facteurs de charge de la norme SIA 260, tableau 1, s'appliquent pour la vérification de la sécurité structurale. Pour un bâtiment, les valeurs de l'état-limite de type 2 (résistance ultime de la structure porteuse ou d'un de ses éléments) sont en général déterminantes.
// woodcore:/object p1

// woodcore:object table load-factors-table
#figure(
  table(
    columns: (1fr, auto, auto, auto),
    align: (left, right, right, right),
    table.hline(stroke: 1pt),
    table.header([*Actions*], [*État-limite type 1*], [*État-limite type 2*], [*État-limite type 3*]),
    table.hline(stroke: 0.5pt),
    [Actions permanentes, effet défavorable : $γ_(G,"sup")$], [1.1], [1.35], [1.0],
    [Actions permanentes, effet favorable : $γ_(G,"inf")$], [0.9], [0.8], [1.0],
    [Actions variables en général : $γ_Q$], [1.5], [1.5], [1.3],
    table.hline(stroke: 1pt),
  ),
  caption: [Facteurs de charge pour la vérification de la sécurité structurale],
)
// woodcore:/object load-factors-table

// woodcore:object text load-factors-table-notes
G est multiplié par $γ_(G,"sup")$ ou par $γ_(G,"inf")$ selon que l'effet d'ensemble de l'action est défavorable ou favorable (SIA 260, tableau 1, note 1). Les facteurs des actions du terrain de fondation et du trafic figurent dans la norme.
// woodcore:/object load-factors-table-notes
