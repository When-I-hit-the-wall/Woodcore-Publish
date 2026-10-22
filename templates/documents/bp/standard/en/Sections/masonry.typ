#import "/commands.typ": *

// woodcore:object heading title
== Masonry
// woodcore:/object title

// woodcore:object table masonry-table
#figure(
  table(
    columns: (auto, auto, auto),
    align: (left, right, right),
    table.hline(stroke: 1pt),
    table.header([*Designation*], [*Design compressive strength $f_"xd"$*], [*Design modulus of elasticity $E_"xd"$*]),  // woodcore:hidden 4=[Further properties]
    table.hline(stroke: 0.5pt),
    [[…]], [[…]], [[…]],  // woodcore:hidden 4=[]
    table.hline(stroke: 1pt),
  ),
  caption: [Masonry (SIA 266)],
)
// woodcore:/object masonry-table
