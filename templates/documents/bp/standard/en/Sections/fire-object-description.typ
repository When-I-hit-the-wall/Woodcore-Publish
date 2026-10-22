#import "/commands.typ": *

// woodcore:object heading title
== Description of the object
// woodcore:/object title

// woodcore:object table fire-object-table
#figure(
  table(
    columns: (auto, 1fr),
    align: (left, left),
    table.hline(stroke: 1pt),
    [Use], [[…]],
    [Number of places or beds], [[…]],
    [Number of storeys and total height], [[…]],
    [Neighbouring buildings], [[…]],
    [Availability of extinguishing water], [[…]],
    [Concept chosen (constructional / technical)], [[…]],
    table.hline(stroke: 1pt),
  ),
  caption: [Description of the object for fire protection],
)
// woodcore:/object fire-object-table

// woodcore:object text fire-building-height
*Building height category (VKF)*:
- Low-rise building (up to 11 m)
- Medium-rise building (up to 30 m)
- High-rise building (over 30 m)
// woodcore:/object fire-building-height
