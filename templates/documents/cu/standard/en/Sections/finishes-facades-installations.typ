#import "/commands.typ": *

// woodcore:object heading title
== Finishes, facades and services
// woodcore:/object title

// woodcore:object text p1
Non-loadbearing walls built with the shell (e.g. non-loadbearing masonry) are separated from the floor by soft intermediate layers, so that the floor deformations defined above (in addition to the construction tolerance) have no consequences for them. Those built after the shell and after the removal of propping have a soft intermediate layer of at least [20] mm. Non-loadbearing masonry walls that do not stabilise themselves are to be secured against tipping in the event of an earthquake. [Weight and permissible deformations of the facade: …]
// woodcore:/object p1

// woodcore:object doc-table deformation-margins
#doc-table(
  columns: (
    (id: "element", title: [Member]),
    (id: "margin", title: [Floor deformation to be expected], unit: "mm", kind: "number"),
  ),
  hidden: (),
  rows: (
    (element: [Non-loadbearing partitions], margin: [[…]]),
    (element: [Facade], margin: [[…]]),
  ),
  caption: [Deformation margins to allow for after installation],
  notes: (
    [Deformation margin in addition to the construction tolerance; the floor edges are surveyed before the facade is produced and installed.],
  ),
)
// woodcore:/object deformation-margins
