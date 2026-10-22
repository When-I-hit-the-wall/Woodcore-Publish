#import "/commands.typ": *

// woodcore:object heading title
== Ground
// woodcore:/object title
// woodcore:shared ground-conditions

// woodcore:object text p1
[Type of ground, stratigraphy, hydrogeological conditions (groundwater, slope and seam water) and the source of this information: geotechnical report (author, date). If the investigations are not complete, state those still needed before the design.]
// woodcore:/object p1

// woodcore:object table ground-layers
#figure(
  table(
    columns: (auto, auto, auto),
    align: (left, left, right),
    table.hline(stroke: 1pt),
    table.header([*Layer*], [*Description*], [*Depth / thickness*]),
    table.hline(stroke: 0.5pt),
    [[…]], [[…]], [[…]],
    table.hline(stroke: 1pt),
  ),
  caption: [Ground layers],
)
// woodcore:/object ground-layers

// woodcore:object table design-water-levels
#figure(
  table(
    columns: (auto, auto),
    align: (left, right),
    table.hline(stroke: 1pt),
    table.header([*Water level*], [*Elevation (m a.s.l.)*]),  // woodcore:hidden 3=[Remark]
    table.hline(stroke: 0.5pt),
    [High water (HW)], [[…]],  // woodcore:hidden 3=[]
    [Mean water (MW)], [[…]],  // woodcore:hidden 3=[]
    table.hline(stroke: 1pt),
  ),
  caption: [Design water levels],
)
// woodcore:/object design-water-levels

// woodcore:object text ground-profile
#figure(rect(width: 100%, height: 5cm, stroke: 0.5pt + luma(60%))[[Figure with caption and source]], caption: [Geological profile / extract from the geotechnical report])
// woodcore:/object ground-profile
// woodcore:/shared ground-conditions
