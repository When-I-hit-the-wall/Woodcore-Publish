#import "/commands.typ": *

// woodcore:object heading title
=== Poids propre et poids volumiques
// woodcore:/object title

// woodcore:object text p1
Les actions permanentes agissent en continu. Elles comprennent le poids propre de la structure porteuse et les charges permanentes des éléments de construction. Le poids propre est déterminé à partir des dimensions prévues aux plans et des poids volumiques moyens de la norme SIA 261, annexe A ; il est traité globalement avec des valeurs de calcul supérieures ou inférieures, selon que l'effet d'ensemble est défavorable ou favorable (SIA 261, ch. 2.1.2).
// woodcore:/object p1

// woodcore:object doc-table permanent-actions-table
#doc-table(
  columns: (
    (id: "action", title: [Action / danger]),
    (id: "measures", title: [Mesures]),
    (id: "followup", title: [Suite à donner]),
    (id: "assumptions", title: [Hypothèses pour l'analyse et le dimensionnement]),
  ),
  hidden: (),
  rows: (
    (action: [Poids propre], measures: [Dimensionnement ; contrôles d'exécution], followup: [Calcul statique ; plan de contrôle], assumptions: [Poids volumiques selon SIA 261, annexe A (tableau ci-dessous)]),
    (action: [Charges permanentes], measures: [Dimensionnement ; contrôles d'exécution ; surveillance en service (modifications)], followup: [Calcul statique ; plan de contrôle ; plan de surveillance], assumptions: [Selon les compositions d'éléments (section « Charges superposées »)]),
  ),
  caption: [Actions permanentes : mesures et hypothèses],
)
// woodcore:/object permanent-actions-table

// woodcore:object doc-table unit-weights-table
#doc-table(
  columns: (
    (id: "material", title: [Matériau]),
    (id: "gamma", title: [Poids volumique $gamma$], unit: "kN/m³", kind: "number"),
  ),
  hidden: (),
  rows: (
    (material: [Acier de construction], gamma: 78.5),
    (material: [Béton armé], gamma: 25),
    (material: [Bois résineux, en général], gamma: 5),
  ),
  caption: [Poids volumiques des matériaux],
  notes: (
    [Valeurs moyennes de la norme SIA 261, annexe A, tableau 28 ; le tableau complet se trouve dans la norme.],
  ),
)
// woodcore:/object unit-weights-table
