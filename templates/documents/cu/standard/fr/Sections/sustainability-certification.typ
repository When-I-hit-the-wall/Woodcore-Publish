#import "/commands.typ": *

// woodcore:object heading title
== Certification et standard de durabilité
// woodcore:/object title
// woodcore:shared sustainability-certification

// woodcore:object doc-checklist certification-choice
#doc-checklist(
  label: [Certification ou standard visé],
  options: (
    (id: "snbs", label: [SNBS Bâtiment (Standard Construction durable Suisse)], checked: false),
    (id: "minergie", label: [Minergie], checked: false),
    (id: "minergie-p", label: [Minergie-P], checked: false),
    (id: "minergie-a", label: [Minergie-A], checked: false),
    (id: "minergie-eco", label: [Minergie-ECO (complément)], checked: false),
    (id: "sia-2040", label: [Voie SIA vers l'efficacité énergétique (SIA 2040) et énergie grise (SIA 2032)], checked: false),
    (id: "none", label: [Aucune certification visée], checked: true),
  ),
)
// woodcore:/object certification-choice

// woodcore:object text p1
[Indiquer ce que l'objectif visé implique pour la structure porteuse, p. ex. des valeurs limites pour les émissions de gaz à effet de serre, l'énergie grise et le carbone stocké, et l'emploi, autant que possible, d'éléments en bois à faibles émissions de CO₂ et à fort stockage de carbone.]
// woodcore:/object p1

// woodcore:object text p2
[Préciser qui vérifie le respect des valeurs limites : ce contrôle ne fait en général pas partie des tâches de la personne chargée du projet de structure porteuse.]
// woodcore:/object p2
// woodcore:/shared sustainability-certification
