#import "/commands.typ": *

// woodcore:object heading title
== Ground
// woodcore:/object title
// woodcore:shared ground-conditions

// woodcore:object text p1
[Type of ground, stratigraphy, hydrogeological conditions (groundwater, slope and seam water) and the source of this information: geotechnical report (author, date). If the investigations are not complete, state those still needed before the design.]
// woodcore:/object p1

// woodcore:object doc-table ground-layers
#doc-table(
  columns: (
    (id: "layer", title: [Layer]),
    (id: "description", title: [Description]),
    (id: "depth", title: [Depth / thickness], unit: "m", kind: "number"),
  ),
  hidden: (),
  rows: (
    (layer: [[…]], description: [[…]], depth: [[…]]),
  ),
  caption: [Ground layers],
)
// woodcore:/object ground-layers

// woodcore:object doc-table design-water-levels
#doc-table(
  columns: (
    (id: "level", title: [Water level]),
    (id: "elevation", title: [Elevation (m a.s.l.)], unit: "m", kind: "number"),
    (id: "remark", title: [Remark]),
  ),
  hidden: ("remark",),
  rows: (
    (level: [High water (HW)], elevation: [[…]], remark: []),
    (level: [Mean water (MW)], elevation: [[…]], remark: []),
  ),
  caption: [Design water levels],
)
// woodcore:/object design-water-levels

// woodcore:object doc-image ground-profile
#doc-image(
  file: none,
  caption: [Geological profile / extract from the geotechnical report],
  placeholder: [[Figure with caption and source]],
)
// woodcore:/object ground-profile
// woodcore:/shared ground-conditions
