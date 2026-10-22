#import "/commands.typ": *

// woodcore:object heading title
=== Poids propre et poids volumiques
// woodcore:/object title

// woodcore:object text p1
Les actions permanentes agissent en continu. Elles comprennent le poids propre de la structure porteuse et les charges permanentes des éléments de construction. Le poids propre est déterminé à partir des dimensions prévues aux plans et des poids volumiques moyens de la norme SIA 261, annexe A ; il est traité globalement avec des valeurs de calcul supérieures ou inférieures, selon que l'effet d'ensemble est défavorable ou favorable (SIA 261, ch. 2.1.2).
// woodcore:/object p1

// woodcore:object table permanent-actions-table
#figure(
  table(
    columns: (auto, auto, auto, auto),
    align: (left, left, left, left),
    table.hline(stroke: 1pt),
    table.header([*Action / danger*], [*Mesures*], [*Suite à donner*], [*Hypothèses pour l'analyse et le dimensionnement*]),
    table.hline(stroke: 0.5pt),
    [Poids propre], [Dimensionnement ; contrôles d'exécution], [Calcul statique ; plan de contrôle], [Poids volumiques selon SIA 261, annexe A (tableau ci-dessous)],
    [Charges permanentes], [Dimensionnement ; contrôles d'exécution ; surveillance en service (modifications)], [Calcul statique ; plan de contrôle ; plan de surveillance], [Selon les compositions d'éléments (section « Charges superposées »)],
    table.hline(stroke: 1pt),
  ),
  caption: [Actions permanentes : mesures et hypothèses],
)
// woodcore:/object permanent-actions-table

// woodcore:object table unit-weights-table
#figure(
  table(
    columns: (auto, auto),
    align: (left, right),
    table.hline(stroke: 1pt),
    table.header([*Matériau*], [*Poids volumique $gamma$*]),
    table.hline(stroke: 0.5pt),
    [Acier de construction], [78.5],
    [Béton armé], [25],
    [Bois résineux, en général], [5],
    table.hline(stroke: 1pt),
  ),
  caption: [Poids volumiques des matériaux],
)
// woodcore:/object unit-weights-table

// woodcore:object text unit-weights-table-notes
Valeurs moyennes de la norme SIA 261, annexe A, tableau 28 ; le tableau complet se trouve dans la norme.
// woodcore:/object unit-weights-table-notes
