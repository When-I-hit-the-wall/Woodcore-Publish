#import "/commands.typ": *

// woodcore:object heading title
== Masonry
// woodcore:/object title

// woodcore:object doc-table masonry-table
#doc-table(
  columns: (
    (id: "designation", title: [Designation]),
    (id: "fxd", title: [Design compressive strength $f_"xd"$], unit: "N/mm²", kind: "number"),
    (id: "Exd", title: [Design modulus of elasticity $E_"xd"$], unit: "N/mm²", kind: "number"),
    (id: "remark", title: [Further properties]),
  ),
  hidden: ("remark",),
  rows: (
    (designation: [[…]], fxd: [[…]], Exd: [[…]], remark: []),
  ),
  caption: [Masonry (SIA 266)],
)
// woodcore:/object masonry-table
