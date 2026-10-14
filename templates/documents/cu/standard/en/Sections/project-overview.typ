#import "/commands.typ": *

// woodcore:object heading title
== Project and surroundings
// woodcore:/object title

// woodcore:object doc-table project-overview-table
#doc-table(
  columns: (
    (id: "item", title: [Item]),
    (id: "text", title: [Description], kind: "wide"),
  ),
  hidden: (),
  rows: (
    (item: [Surroundings], text: [[Location, altitude, topography, type of ground, neighbouring buildings, protected areas …]]),
    (item: [Architectural concept], text: [[Organisation by storey (basements, ground floor, upper floors), type of construction (timber, concrete, composite), existing or new building, integration into the site, large openings, interior fit-out, roof (flat, photovoltaic …), target group, materials with low CO₂ emissions …]]),
    (item: [Project drawings], text: [[Authoritative drawings and 3D model of the architect, with their status (index, date).]]),
    (item: [Special features], text: [[Access and transport constraints, operation to be maintained during the works, environmental constraints …]]),
  ),
  caption: [General description],
  header: false,
)
// woodcore:/object project-overview-table
