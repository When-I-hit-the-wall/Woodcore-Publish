#import "/commands.typ": *

// woodcore:object heading title
== Résistance au feu de la structure porteuse
// woodcore:/object title

// woodcore:object text p1
Les exigences de protection incendie sont fixées selon les prescriptions suisses de protection incendie (AEAI), la documentation Lignum Protection incendie et le concept de protection incendie [constructif / technique]. L'incendie est traité comme une action accidentelle selon la norme SIA 261, ch. 15. Les exigences relatives aux éléments porteurs sont les suivantes :
// woodcore:/object p1

// woodcore:object doc-choice structure-fire-resistance
#doc-choice(
  label: [Résistance au feu de la structure porteuse (général)],
  options: (
    (id: "r30", label: [R 30]),
    (id: "r60", label: [R 60]),
    (id: "r90", label: [R 90]),
    (id: "none", label: [Aucune exigence]),
  ),
  selected: "r60",
)
// woodcore:/object structure-fire-resistance

// woodcore:object text p2
[Exceptions par niveau (p. ex. sous-sol, niveau supérieur).] La résistance au feu est en principe assurée par l'enrobage des armatures et les dimensions minimales des éléments (béton), par des revêtements de protection incendie ou par un calcul de la carbonisation selon les documentations Lignum (bois) ; les éléments préfabriqués en béton ou en acier doivent disposer d'un agrément AEAI.
// woodcore:/object p2
