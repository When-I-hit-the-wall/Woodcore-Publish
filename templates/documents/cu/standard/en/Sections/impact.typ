#import "/commands.typ": *

// woodcore:object heading title
== Impact
// woodcore:/object title
// woodcore:shared impact

// woodcore:object text p1
Impact is an accidental action (SIA 261, 14.1.1). It is considered where the structure lies closer than 3 m (in built-up areas) or 10 m (outside built-up areas) to the edge of the carriageway (14.2.1). For impact from ships, helicopters, aircraft or falling parts, the equivalent forces are determined for the project and recorded in the basis of design (14.1.8). [Protective measures (benches, bollards): …]
// woodcore:/object p1

// woodcore:object table impact-table
#figure(
  table(
    columns: (auto, auto, 1fr, auto, auto, auto),
    align: (left, left, left, center, right, right),
    table.hline(stroke: 1pt),
    table.header([*Storey*], [*Part of building*], [*Use*], [*Category (SIA 261)*], [*Impact force $Q_"gd"$*], [*Height of application*]),
    table.hline(stroke: 0.5pt),
    [[…]], [[…]], [[Car park for vehicles up to 3.5 t]], [F], [60], [0.6],
    [[…]], [[…]], [[Delivery zone, vehicles from 3.5 t to 16 t]], [G], [180], [1.2],
    table.hline(stroke: 1pt),
  ),
  caption: [Impact forces of road vehicles in buildings],
)
// woodcore:/object impact-table
// woodcore:/shared impact
