#import "/commands.typ": *

// woodcore:object heading title
== Ground parameters
// woodcore:/object title

// woodcore:object text p1
The ground parameters are given in the geotechnical report [author, date]. The following characteristic values are assumed for the design (prudent estimates in accordance with SIA 260, 3.3.3.5 and SIA 267):
// woodcore:/object p1

// woodcore:object table ground-parameters-table
#figure(
  table(
    columns: (auto, auto, auto, auto, auto),
    align: (left, right, right, right, right),
    table.hline(stroke: 1pt),
    table.header([*Layer*], [*Unit weight $gamma$*], [*Friction angle $phi'$*], [*Cohesion $c'$*], [*Constrained modulus $E_s$*]),  // woodcore:hidden 6=[Remark]
    table.hline(stroke: 0.5pt),
    [[…]], [[…]], [[…]], [[…]], [[…]],  // woodcore:hidden 6=[]
    table.hline(stroke: 1pt),
  ),
  caption: [Characteristic ground parameters],
)
// woodcore:/object ground-parameters-table
