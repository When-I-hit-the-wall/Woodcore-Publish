#import "/commands.typ": *

// woodcore:object heading title
== Anforderungen an die Bauteile
// woodcore:/object title

// woodcore:object text separating-elements-plan
#figure(rect(width: 100%, height: 5cm, stroke: 0.5pt + luma(60%))[[Plan oder Schnitt mit der Nummerierung der Trennbauteile]], caption: [Bezeichnung der Trennbauteile [Geschoss]])
// woodcore:/object separating-elements-plan

// woodcore:object table airborne-exterior-table
#figure(
  table(
    columns: (auto, auto, auto, auto),
    align: (left, left, left, left),
    table.hline(stroke: 1pt),
    table.header([*Bauteil*], [*Grundlage*], [*Anforderung Tag / Nacht*], [*Ausführung / Werte*]),
    table.hline(stroke: 0.5pt),
    [[Fassade Zimmer]], [SIA 181, tab. 2], [[…] / […]], [[…]],
    table.hline(stroke: 1pt),
  ),
  caption: [Luftschall aussen],
)
// woodcore:/object airborne-exterior-table

// woodcore:object table airborne-interior-table
#figure(
  table(
    columns: (auto, auto, auto, auto),
    align: (left, left, left, left),
    table.hline(stroke: 1pt),
    table.header([*Bereich / Bauteil*], [*Grundlage*], [*Anforderung*], [*Ausführung / Werte*]),
    table.hline(stroke: 0.5pt),
    [[Zimmer / Zimmer]], [SIA 181, tab. 3], [[…]], [[…]],
    table.hline(stroke: 1pt),
  ),
  caption: [Luftschall innen],
)
// woodcore:/object airborne-interior-table

// woodcore:object table impact-sound-table
#figure(
  table(
    columns: (auto, auto, auto, auto),
    align: (left, left, left, left),
    table.hline(stroke: 1pt),
    table.header([*Bereich / Bauteil*], [*Grundlage*], [*Anforderung*], [*Ausführung / Werte*]),
    table.hline(stroke: 0.5pt),
    [[Terrasse / Zimmer]], [SIA 181, tab. 5], [[…]], [[…]],
    table.hline(stroke: 1pt),
  ),
  caption: [Trittschall],
)
// woodcore:/object impact-sound-table

// woodcore:object table installation-noise-table
#figure(
  table(
    columns: (auto, auto, auto, auto, auto),
    align: (left, left, left, left, left),
    table.hline(stroke: 1pt),
    table.header([*Geräuschart*], [*Bereich / Bauteil*], [*Grundlage*], [*Anforderung*], [*Ausführung / Werte*]),
    table.hline(stroke: 0.5pt),
    [Einzelne Geräusche], [[Küche / Restaurant]], [SIA 181, tab. 6], [[…]], [[…]],
    table.hline(stroke: 1pt),
  ),
  caption: [Geräusche haustechnischer Anlagen],
)
// woodcore:/object installation-noise-table
