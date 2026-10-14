#import "/commands.typ": *

// woodcore:object heading title
== Durée d'utilisation
// woodcore:/object title
// woodcore:shared service-life

// woodcore:object text p1
La durée d'utilisation est la période pendant laquelle, selon l'état actuel des connaissances, l'ouvrage doit satisfaire aux usages définis dans la convention d'utilisation. Elle est convenue avec le maître de l'ouvrage ; pendant cette période, le maître de l'ouvrage effectue les travaux d'entretien périodiques.
// woodcore:/object p1

// woodcore:object doc-choice service-life-class
#doc-choice(
  label: [Durée d'utilisation de la structure porteuse (valeurs indicatives, SIA 260, ch. 2.3.2)],
  options: (
    (id: "temporary", label: [Ouvrage temporaire : jusqu'à 10 ans]),
    (id: "replaceable", label: [Élément de construction remplaçable : jusqu'à 25 ans]),
    (id: "normal", label: [Bâtiment et autre ouvrage d'importance normale : 50 ans]),
    (id: "major", label: [Ouvrage d'importance majeure : 100 ans]),
  ),
  selected: "normal",
)
// woodcore:/object service-life-class

// woodcore:object doc-table service-life-table
#doc-table(
  columns: (
    (id: "part", title: [Élément]),
    (id: "years", title: [Durée d'utilisation]),
    (id: "remark", title: [Remarque]),
  ),
  hidden: ("remark",),
  rows: (
    (part: [Structure porteuse], years: [50 ans], remark: []),
    (part: [Étanchéités], years: [25 ans], remark: []),
    (part: [Façade], years: [25 ans], remark: []),
    (part: [Couverture], years: [25 ans], remark: []),
    (part: [Éléments remplaçables], years: [25 ans], remark: []),
  ),
  caption: [Durée d'utilisation convenue par élément],
)
// woodcore:/object service-life-table
// woodcore:/shared service-life
