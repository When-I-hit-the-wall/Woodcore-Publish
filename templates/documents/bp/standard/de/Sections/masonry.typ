#import "/commands.typ": *

// woodcore:object heading title
== Mauerwerk
// woodcore:/object title

// woodcore:object doc-table masonry-table
#doc-table(
  columns: (
    (id: "designation", title: [Bezeichnung]),
    (id: "fxd", title: [Bemessungswert der Druckfestigkeit $f_"xd"$], unit: "N/mm²", kind: "number"),
    (id: "Exd", title: [Bemessungswert des Elastizitätsmoduls $E_"xd"$], unit: "N/mm²", kind: "number"),
    (id: "remark", title: [Weitere Kennwerte]),
  ),
  hidden: ("remark",),
  rows: (
    (designation: [[…]], fxd: [[…]], Exd: [[…]], remark: []),
  ),
  caption: [Mauerwerk (SIA 266)],
)
// woodcore:/object masonry-table
