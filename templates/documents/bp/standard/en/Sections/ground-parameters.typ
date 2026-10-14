#import "/commands.typ": *

// woodcore:object heading title
== Ground parameters
// woodcore:/object title

// woodcore:object text p1
The ground parameters are given in the geotechnical report [author, date]. The following characteristic values are assumed for the design (prudent estimates in accordance with SIA 260, 3.3.3.5 and SIA 267):
// woodcore:/object p1

// woodcore:object doc-table ground-parameters-table
#doc-table(
  columns: (
    (id: "layer", title: [Layer]),
    (id: "gamma", title: [Unit weight $gamma$], unit: "kN/m³", kind: "number"),
    (id: "phi", title: [Friction angle $phi'$], unit: "°", kind: "number"),
    (id: "c", title: [Cohesion $c'$], unit: "kPa", kind: "number"),
    (id: "Es", title: [Constrained modulus $E_s$], unit: "MN/m²", kind: "number"),
    (id: "remark", title: [Remark]),
  ),
  hidden: ("remark",),
  rows: (
    (layer: [[…]], gamma: [[…]], phi: [[…]], c: [[…]], Es: [[…]], remark: []),
  ),
  caption: [Characteristic ground parameters],
)
// woodcore:/object ground-parameters-table
