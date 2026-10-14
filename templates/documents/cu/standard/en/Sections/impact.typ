#import "/commands.typ": *

// woodcore:object heading title
== Impact
// woodcore:/object title
// woodcore:shared impact

// woodcore:object text p1
Impact is an accidental action (SIA 261, 14.1.1). It is considered where the structure lies closer than 3 m (in built-up areas) or 10 m (outside built-up areas) to the edge of the carriageway (14.2.1). For impact from ships, helicopters, aircraft or falling parts, the equivalent forces are determined for the project and recorded in the basis of design (14.1.8). [Protective measures (benches, bollards): …]
// woodcore:/object p1

// woodcore:object doc-table impact-table
#doc-table(
  columns: (
    (id: "storey", title: [Storey]),
    (id: "area", title: [Part of building]),
    (id: "use", title: [Use], kind: "wide"),
    (id: "category", title: [Category (SIA 261)], kind: "math"),
    (id: "force", title: [Impact force $Q_"gd"$], unit: "kN", kind: "number"),
    (id: "height", title: [Height of application], unit: "m", kind: "number"),
  ),
  hidden: (),
  rows: (
    (storey: [[…]], area: [[…]], use: [[Car park for vehicles up to 3.5 t]], category: "F", force: 60, height: 0.6),
    (storey: [[…]], area: [[…]], use: [[Delivery zone, vehicles from 3.5 t to 16 t]], category: "G", force: 180, height: 1.2),
  ),
  caption: [Impact forces of road vehicles in buildings],
)
// woodcore:/object impact-table
// woodcore:/shared impact
