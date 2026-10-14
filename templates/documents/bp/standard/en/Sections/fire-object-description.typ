#import "/commands.typ": *

// woodcore:object heading title
== Description of the object
// woodcore:/object title

// woodcore:object doc-table fire-object-table
#doc-table(
  columns: (
    (id: "item", title: [Item]),
    (id: "text", title: [Description], kind: "wide"),
  ),
  hidden: (),
  rows: (
    (item: [Use], text: [[…]]),
    (item: [Number of places or beds], text: [[…]]),
    (item: [Number of storeys and total height], text: [[…]]),
    (item: [Neighbouring buildings], text: [[…]]),
    (item: [Availability of extinguishing water], text: [[…]]),
    (item: [Concept chosen (constructional / technical)], text: [[…]]),
  ),
  caption: [Description of the object for fire protection],
  header: false,
)
// woodcore:/object fire-object-table

// woodcore:object doc-choice fire-building-height
#doc-choice(
  label: [Building height category (VKF)],
  options: (
    (id: "low", label: [Low-rise building (up to 11 m)]),
    (id: "medium", label: [Medium-rise building (up to 30 m)]),
    (id: "high", label: [High-rise building (over 30 m)]),
  ),
  selected: none,
)
// woodcore:/object fire-building-height
