#import "/commands.typ": *

// woodcore:object heading title
== Surface quality of timber members
// woodcore:/object title

// woodcore:object text p1
Timber is a naturally growing raw material: knots, resin pockets (depending on the species), colour differences and sometimes discolouration appear on the surface. The number and size of permissible knots and the acceptability of discolouration are defined by appearance classes, to be agreed with the engineer during the design. A detailed definition is given in the Lignum publication “Qualitätskriterien für Holz und Holzwerkstoffe im Bau und Ausbau, Handelsgebräuche für die Schweiz” [edition].
// woodcore:/object p1

// woodcore:object text p2
The timber surface changes over time: members directly exposed to the weather turn grey, which is not a defect but an optical change; timber surfaces in weather-protected areas darken through UV radiation. With changing air humidity, timber swells and shrinks, which can lead to isolated cracks in linear members (columns, beams).
// woodcore:/object p2

// woodcore:object doc-table appearance-classes-table
#doc-table(
  columns: (
    (id: "member", title: [Member]),
    (id: "product", title: [Product]),
    (id: "class", title: [Appearance class]),
    (id: "remark", title: [Remark]),
  ),
  hidden: ("remark",),
  rows: (
    (member: [[Exposed columns and beams]], product: [Solid timber and glulam], class: [N: normal quality (structural timber)], remark: []),
    (member: [[Non-visible members]], product: [Solid timber and glulam], class: [I: industrial quality, no appearance requirements], remark: []),
  ),
  caption: [Appearance classes by member],
)
// woodcore:/object appearance-classes-table
