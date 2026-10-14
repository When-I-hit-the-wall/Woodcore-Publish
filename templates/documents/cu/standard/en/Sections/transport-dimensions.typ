#import "/commands.typ": *

// woodcore:object heading title
== Logistics and transport
// woodcore:/object title
// woodcore:shared transport-dimensions

// woodcore:object text p1
[Envisaged means of transport (lorry, crane, cable car, helicopter …), owner's requirements, size and weight limits for prefabricated elements, storage and transhipment areas. Main means of transport and permitted exceptions.]
// woodcore:/object p1

// woodcore:object doc-table transport-table
#doc-table(
  columns: (
    (id: "transport", title: [Means of transport]),
    (id: "length", title: [Max. length], unit: "mm", kind: "number"),
    (id: "width", title: [Max. width], unit: "mm", kind: "number"),
    (id: "height", title: [Max. height], unit: "mm", kind: "number"),
    (id: "hung", title: [Max. suspended load], unit: "kg", kind: "number"),
    (id: "distributed", title: [Max. distributed load], unit: "kg", kind: "number"),
  ),
  hidden: (),
  rows: (
    (transport: [[…]], length: [[…]], width: [[…]], height: [[…]], hung: [[…]], distributed: [[…]]),
  ),
  caption: [Maximum dimensions of the transported elements],
)
// woodcore:/object transport-table
// woodcore:/shared transport-dimensions
