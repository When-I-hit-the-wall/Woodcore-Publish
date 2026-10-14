#import "/commands.typ": *

// woodcore:object heading title
== Situations de danger
// woodcore:/object title

// woodcore:object text p1
Les situations de danger possibles ont été examinées et les mesures propres à tenir ces dangers sous contrôle ou à les réduire à un niveau acceptable sont définies (SIA 260, ch. 2.4.4). Les situations de danger considérées, avec leurs mesures, la suite à donner et les hypothèses de dimensionnement, sont les suivantes :
// woodcore:/object p1

// woodcore:object doc-checklist hazard-influences
#doc-checklist(
  label: [Influences pouvant représenter un danger (SIA 260, ch. 2.4.5)],
  options: (
    (id: "deviations-actions", label: [Écarts par rapport aux valeurs admises pour les actions], checked: true),
    (id: "ground-actions", label: [Actions du terrain de fondation], checked: false),
    (id: "natural-hazards", label: [Actions dues à des dangers naturels d'origine gravitationnelle ou météorologique], checked: false),
    (id: "physical", label: [Actions physiques, p. ex. humidité ou température], checked: true),
    (id: "chemical", label: [Actions chimiques, p. ex. sel de déverglaçage ou eaux souterraines], checked: false),
    (id: "biological", label: [Actions biologiques, p. ex. insectes ou champignons], checked: true),
    (id: "resonance", label: [Effets de résonance], checked: false),
    (id: "resistance-deviations", label: [Écarts par rapport aux valeurs prévues de la résistance ultime de la structure ou du terrain], checked: false),
    (id: "deterioration", label: [Réduction de la résistance par corrosion, fragilité ou fatigue], checked: false),
    (id: "accidental", label: [Réduction de la résistance par le feu, une explosion, un choc, une rupture de conduite ou un séisme], checked: true),
  ),
)
// woodcore:/object hazard-influences

// woodcore:object doc-table hazard-scenarios-table
#doc-table(
  columns: (
    (id: "scenario", title: [Situation de danger]),
    (id: "measures", title: [Mesures]),
    (id: "followup", title: [Suite à donner]),
    (id: "assumptions", title: [Hypothèses pour l'analyse et le dimensionnement]),
  ),
  hidden: (),
  rows: (
    (scenario: [[Incendie]], measures: [[Compartiments coupe-feu, résistance au feu, dimensions suffisantes des éléments, revêtement de protection incendie]], followup: [[Concept de protection incendie ; étude de protection incendie]], assumptions: [[R 60]]),
    (scenario: [[Séisme]], measures: [[Dimensionnement ; mesures constructives selon SIA 261]], followup: [[Calcul statique]], assumptions: [[Zone, classe de terrain, classe d'ouvrage, q]]),
  ),
  caption: [Situations de danger et mesures],
)
// woodcore:/object hazard-scenarios-table
