#import "/commands.typ": *

// woodcore:object heading title
== Exigences relatives aux éléments de construction
// woodcore:/object title

// woodcore:object doc-image separating-elements-plan
#doc-image(
  file: none,
  caption: [Repérage des éléments de séparation [niveau]],
  placeholder: [[Plan ou coupe avec la numérotation des éléments de séparation]],
)
// woodcore:/object separating-elements-plan

// woodcore:object doc-table airborne-exterior-table
#doc-table(
  columns: (
    (id: "element", title: [Élément]),
    (id: "basis", title: [Base]),
    (id: "requirement", title: [Exigence jour / nuit], unit: "dB"),
    (id: "execution", title: [Exécution / valeurs]),
  ),
  hidden: (),
  rows: (
    (element: [[Façade des chambres]], basis: [SIA 181, tab. 2], requirement: [[…] / […]], execution: [[…]]),
  ),
  caption: [Bruit aérien extérieur],
)
// woodcore:/object airborne-exterior-table

// woodcore:object doc-table airborne-interior-table
#doc-table(
  columns: (
    (id: "element", title: [Zone / élément]),
    (id: "basis", title: [Base]),
    (id: "requirement", title: [Exigence], unit: "dB"),
    (id: "execution", title: [Exécution / valeurs]),
  ),
  hidden: (),
  rows: (
    (element: [[Chambre / chambre]], basis: [SIA 181, tab. 3], requirement: [[…]], execution: [[…]]),
  ),
  caption: [Bruit aérien intérieur],
)
// woodcore:/object airborne-interior-table

// woodcore:object doc-table impact-sound-table
#doc-table(
  columns: (
    (id: "element", title: [Zone / élément]),
    (id: "basis", title: [Base]),
    (id: "requirement", title: [Exigence], unit: "dB"),
    (id: "execution", title: [Exécution / valeurs]),
  ),
  hidden: (),
  rows: (
    (element: [[Terrasse / chambre]], basis: [SIA 181, tab. 5], requirement: [[…]], execution: [[…]]),
  ),
  caption: [Bruit de choc],
)
// woodcore:/object impact-sound-table

// woodcore:object doc-table installation-noise-table
#doc-table(
  columns: (
    (id: "kind", title: [Type de bruit]),
    (id: "element", title: [Zone / élément]),
    (id: "basis", title: [Base]),
    (id: "requirement", title: [Exigence], unit: "dB"),
    (id: "execution", title: [Exécution / valeurs]),
  ),
  hidden: (),
  rows: (
    (kind: [Bruits isolés], element: [[Cuisine / restaurant]], basis: [SIA 181, tab. 6], requirement: [[…]], execution: [[…]]),
  ),
  caption: [Bruits des installations techniques],
)
// woodcore:/object installation-noise-table
