#import "/commands.typ": *

// woodcore:object heading title
== Risques acceptés
// woodcore:/object title
// woodcore:shared accepted-risks

// woodcore:object text p1
Les risques suivants sont acceptés par le maître de l'ouvrage ; ils ne font pas partie du dimensionnement :
// woodcore:/object p1

// woodcore:object doc-checklist accepted-risks-list
#doc-checklist(
  label: [Risques acceptés],
  options: (
    (id: "ground", label: [Risque lié au terrain de fondation], checked: true, text: [Malgré les investigations préalables, des inhomogénéités du terrain de fondation inconnues lors de l'étude peuvent apparaître à l'exécution. Les conséquences en coûts et en délais sont un risque accepté par le maître de l'ouvrage.]),
    (id: "exceptional", label: [Événements exceptionnels], checked: true, text: [Les événements exceptionnels tels que le terrorisme, la chute ou le choc d'un avion, l'explosion ou un accident chimique sont des risques acceptés.]),
    (id: "explosion", label: [Explosion], checked: true, text: [[Risque accepté / action accidentelle.]]),
    (id: "vandalism", label: [Vandalisme et dommages intentionnels à la structure], checked: true, text: [Les dommages intentionnels à la structure porteuse ne font pas partie du dimensionnement.]),
    (id: "flood", label: [Inondation], checked: false, text: [[Risque accepté / action accidentelle.]]),
    (id: "rockfall", label: [Chute de pierres], checked: false, text: [[…]]),
    (id: "avalanche", label: [Avalanches], checked: false, text: [[…]]),
  ),
  only-checked: true,
)
// woodcore:/object accepted-risks-list
// woodcore:/shared accepted-risks
