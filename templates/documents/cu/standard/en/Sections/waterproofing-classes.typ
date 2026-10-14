#import "/commands.typ": *

// woodcore:object heading title
== Watertightness
// woodcore:/object title

// woodcore:object text p1
[Waterproofing concept for below-ground parts (e.g. white tank or yellow tank): the requirements are set with reference to SIA 272; the detailed concept is drawn up during execution planning with the contractor and, where applicable, the system supplier. Responsibility for meeting the criteria lies with the contractor or the waterproofing contractor. Identifying the risk of condensation is a matter for building physics.]
// woodcore:/object p1

// woodcore:object doc-table sealing-classes-table
#doc-table(
  columns: (
    (id: "class", title: [Class], kind: "number"),
    (id: "definition", title: [Definition], kind: "wide"),
    (id: "parts", title: [Building parts]),
  ),
  hidden: (),
  rows: (
    (class: 1, definition: [Completely dry; no damp patches permitted on the dry-side surfaces.], parts: [[…]]),
    (class: 2, definition: [Dry to slightly damp; isolated damp patches permitted; no dripping water on the dry-side surfaces.], parts: [[…]]),
    (class: 3, definition: [Damp; localised damp patches and isolated drips permitted; subsequent injection of cracks accepted.], parts: [[…]]),
    (class: 4, definition: [Damp to wet; damp patches and drips permitted.], parts: [[…]]),
  ),
  caption: [Sealing classes and allocation to building parts],
)
// woodcore:/object sealing-classes-table
