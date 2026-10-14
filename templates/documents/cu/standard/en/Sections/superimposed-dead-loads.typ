#import "/commands.typ": *

// woodcore:object heading title
== Non-structural self-weight (superimposed dead loads)
// woodcore:/object title
// woodcore:shared superimposed-dead-loads

// woodcore:object text p1
The superimposed dead loads comprise floor build-ups, non-loadbearing walls and suspended ceilings [and services and facade]. The following values are characteristic values and govern the design.
// woodcore:/object p1

// woodcore:object dead-load-table superimposed-table
#dead-load-table(
  columns: (
    (id: "zone"),
    (id: "storey"),
    (id: "buildup"),
    (id: "load"),
  ),
  hidden: (),
  rows: (
    (zone: [[…]], storey: [[…]], buildup: [[Floor build-up, non-loadbearing walls, suspended ceilings]], load: [[…]]),
    (zone: [[…]], storey: [[Roof]], buildup: [[Roof build-up, green roof, photovoltaic system]], load: [[…]]),
  ),
  caption: [Superimposed dead loads by part of building and storey],
)
// woodcore:/object superimposed-table

// woodcore:object text p2
If the intended fill heights or finish thicknesses are exceeded, part of the material must be replaced by a lightweight material (insulation, expanded clay, aerated concrete), and only in agreement with the engineer; the finished ground or floor is surveyed after execution and the results are submitted for checking (SIA 261, 2.3.4). The effects of a possible removal of the superimposed load are examined (2.3.5). [Special measures: …]
// woodcore:/object p2
// woodcore:/shared superimposed-dead-loads
