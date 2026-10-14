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

// woodcore:object doc-table vibrations-table
#doc-table(
  columns: (
    (id: "use", title: [Use], kind: "wide"),
    (id: "f", title: [Minimum eigenfrequency $f$], unit: "Hz", kind: "number"),
    (id: "basis", title: [Basis]),
  ),
  hidden: (),
  rows: (
    (use: [Gymnasiums and sports halls], f: [> 8.0], basis: [SIA 260, Tab. 5]),
    (use: [Dance and concert halls], f: [> 7.0], basis: [SIA 260, Tab. 5]),
  ),
  caption: [Minimum eigenfrequencies],
)
// woodcore:/object vibrations-table
// woodcore:/shared vibrations
