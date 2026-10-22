#import "/commands.typ": *

// woodcore:object heading title
== Vibrations
// woodcore:/object title
// woodcore:shared vibrations

// woodcore:object text p1
Vibrations must neither restrict the functionality of the building nor impair the comfort of its users. The following minimum eigenfrequencies are standard values; different values are permitted if a more exact dynamic analysis taking damping into account is carried out. [Particular criteria for light (timber) floors: …]
// woodcore:/object p1

// woodcore:object text p2
Equipment that generates vibrations is mounted on a floating base in accordance with the building physicist's instructions. [Vibrations from rail or road traffic: to be clarified by the owner.]
// woodcore:/object p2

// woodcore:object table vibrations-table
#figure(
  table(
    columns: (1fr, auto, auto),
    align: (left, right, left),
    table.hline(stroke: 1pt),
    table.header([*Use*], [*Minimum eigenfrequency $f$*], [*Basis*]),
    table.hline(stroke: 0.5pt),
    [Gymnasiums and sports halls], [> 8.0], [SIA 260, Tab. 5],
    [Dance and concert halls], [> 7.0], [SIA 260, Tab. 5],
    table.hline(stroke: 1pt),
  ),
  caption: [Minimum eigenfrequencies],
)
// woodcore:/object vibrations-table
// woodcore:/shared vibrations
