#import "/commands.typ": *

// woodcore:object heading title
== Anforderungen an die Bauteile
// woodcore:/object title

// woodcore:object doc-image separating-elements-plan
#doc-image(
  file: none,
  caption: [Bezeichnung der Trennbauteile [Geschoss]],
  placeholder: [[Plan oder Schnitt mit der Nummerierung der Trennbauteile]],
)
// woodcore:/object separating-elements-plan

// woodcore:object doc-table airborne-exterior-table
#doc-table(
  columns: (
    (id: "element", title: [Bauteil]),
    (id: "basis", title: [Grundlage]),
    (id: "requirement", title: [Anforderung Tag / Nacht], unit: "dB"),
    (id: "execution", title: [Ausführung / Werte]),
  ),
  hidden: (),
  rows: (
    (element: [[Fassade Zimmer]], basis: [SIA 181, tab. 2], requirement: [[…] / […]], execution: [[…]]),
  ),
  caption: [Luftschall aussen],
)
// woodcore:/object airborne-exterior-table

// woodcore:object doc-table airborne-interior-table
#doc-table(
  columns: (
    (id: "element", title: [Bereich / Bauteil]),
    (id: "basis", title: [Grundlage]),
    (id: "requirement", title: [Anforderung], unit: "dB"),
    (id: "execution", title: [Ausführung / Werte]),
  ),
  hidden: (),
  rows: (
    (element: [[Zimmer / Zimmer]], basis: [SIA 181, tab. 3], requirement: [[…]], execution: [[…]]),
  ),
  caption: [Luftschall innen],
)
// woodcore:/object airborne-interior-table

// woodcore:object doc-table impact-sound-table
#doc-table(
  columns: (
    (id: "element", title: [Bereich / Bauteil]),
    (id: "basis", title: [Grundlage]),
    (id: "requirement", title: [Anforderung], unit: "dB"),
    (id: "execution", title: [Ausführung / Werte]),
  ),
  hidden: (),
  rows: (
    (element: [[Terrasse / Zimmer]], basis: [SIA 181, tab. 5], requirement: [[…]], execution: [[…]]),
  ),
  caption: [Trittschall],
)
// woodcore:/object impact-sound-table

// woodcore:object doc-table installation-noise-table
#doc-table(
  columns: (
    (id: "kind", title: [Geräuschart]),
    (id: "element", title: [Bereich / Bauteil]),
    (id: "basis", title: [Grundlage]),
    (id: "requirement", title: [Anforderung], unit: "dB"),
    (id: "execution", title: [Ausführung / Werte]),
  ),
  hidden: (),
  rows: (
    (kind: [Einzelne Geräusche], element: [[Küche / Restaurant]], basis: [SIA 181, tab. 6], requirement: [[…]], execution: [[…]]),
  ),
  caption: [Geräusche haustechnischer Anlagen],
)
// woodcore:/object installation-noise-table
