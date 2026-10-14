#import "/commands.typ": *

// woodcore:object heading title
== Radon
// woodcore:/object title

// woodcore:object doc-choice radon-risk
#doc-choice(
  label: [Risque radon (carte du radon de la Suisse, OFSP)],
  options: (
    (id: "low", label: [Risque faible : aucune mesure de gros œuvre]),
    (id: "medium", label: [Risque moyen : mesures selon les recommandations de l'OFSP (p. ex. traversées de conduites étanches)]),
    (id: "high", label: [Risque élevé : mesures selon les recommandations de l'OFSP (p. ex. traversées étanches, dalle de fond de classe d'étanchéité 1)]),
  ),
  selected: none,
)
// woodcore:/object radon-risk

// woodcore:object text p1
L'étanchéité éventuelle contre le radon relève de la responsabilité du maître de l'ouvrage et de l'architecte, et non de l'ingénieur.
// woodcore:/object p1
