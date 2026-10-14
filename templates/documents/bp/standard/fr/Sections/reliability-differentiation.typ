#import "/commands.typ": *

// woodcore:object heading title
== Fiabilité requise et classe de conséquences
// woodcore:/object title

// woodcore:object text p1
La fiabilité requise peut être différenciée selon l'état-limite et la durée de référence, pour l'ensemble de la structure ou pour certains de ses éléments (SIA 260, ch. 2.3.4). Elle peut dépendre de la nature et des conséquences d'une défaillance, de l'ampleur des dégâts acceptés, de l'importance de l'ouvrage dans la maîtrise d'une catastrophe, des investissements consentis pour réduire les risques et des possibilités de surveillance et d'entretien (ch. 2.3.5). [Justifier le choix.]
// woodcore:/object p1

// woodcore:object doc-choice consequence-class
#doc-choice(
  label: [Classe de conséquences d'une défaillance (à convenir)],
  options: (
    (id: "cc1", label: [CC1 : conséquences faibles (pertes humaines, conséquences économiques, sociales ou environnementales faibles ou négligeables)]),
    (id: "cc2", label: [CC2 : conséquences moyennes (pertes humaines, conséquences économiques, sociales ou environnementales considérables)]),
    (id: "cc3", label: [CC3 : conséquences élevées (pertes humaines, conséquences économiques, sociales ou environnementales très importantes)]),
  ),
  selected: "cc2",
)
// woodcore:/object consequence-class
