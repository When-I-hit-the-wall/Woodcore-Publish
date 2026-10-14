#import "/commands.typ": *

// woodcore:object heading title
== Contrôles et réceptions
// woodcore:/object title

// woodcore:object text p1
Les contrôles et réceptions suivants sont convenus ; le programme de contrôle détaillé est établi dans le plan de contrôle.
// woodcore:/object p1

// woodcore:object doc-checklist inspections-list
#doc-checklist(
  label: [Contrôles et réceptions],
  options: (
    (id: "shell-acceptance", label: [Réception du gros œuvre en bois avant le début de l'aménagement intérieur], checked: true),
    (id: "acoustic-measurements", label: [Mesures acoustiques (planchers d'étage) avant la pose du revêtement de sol définitif], checked: true),
    (id: "excavation-acceptance", label: [Réception du fond de fouille par l'ingénieur ou le géologue], checked: false),
    (id: "timber-moisture", label: [Contrôle de l'humidité du bois avant la fermeture des éléments], checked: false),
    (id: "final-acceptance", label: [Réception finale [semaine civile …]], checked: true),
  ),
)
// woodcore:/object inspections-list
