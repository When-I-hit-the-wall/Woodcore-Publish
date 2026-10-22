#import "/commands.typ": *

// woodcore:object heading title
== Logistics and transport
// woodcore:/object title
// woodcore:shared transport-dimensions

// woodcore:object text p1
[Envisaged means of transport (lorry, crane, cable car, helicopter …), owner's requirements, size and weight limits for prefabricated elements, storage and transhipment areas. Main means of transport and permitted exceptions.]
// woodcore:/object p1

// woodcore:object table transport-table
#figure(
  table(
    columns: (auto, auto, auto, auto, auto, auto),
    align: (left, right, right, right, right, right),
    table.hline(stroke: 1pt),
    table.header([*Means of transport*], [*Max. length*], [*Max. width*], [*Max. height*], [*Max. suspended load*], [*Max. distributed load*]),
    table.hline(stroke: 0.5pt),
    [[…]], [[…]], [[…]], [[…]], [[…]], [[…]],
    table.hline(stroke: 1pt),
  ),
  caption: [Maximum dimensions of the transported elements],
)
// woodcore:/object transport-table
// woodcore:/shared transport-dimensions
