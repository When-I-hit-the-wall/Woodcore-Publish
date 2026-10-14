#import "/commands.typ": *

// woodcore:object heading title
== Requirements for building elements
// woodcore:/object title

// woodcore:object doc-image separating-elements-plan
#doc-image(
  file: none,
  caption: [Identification of separating elements [storey]],
  placeholder: [[Plan or section with the numbering of the separating elements]],
)
// woodcore:/object separating-elements-plan

// woodcore:object doc-table airborne-exterior-table
#doc-table(
  columns: (
    (id: "element", title: [Element]),
    (id: "basis", title: [Basis]),
    (id: "requirement", title: [Requirement day / night], unit: "dB"),
    (id: "execution", title: [Execution / values]),
  ),
  hidden: (),
  rows: (
    (element: [[Bedroom facade]], basis: [SIA 181, tab. 2], requirement: [[…] / […]], execution: [[…]]),
  ),
  caption: [Airborne sound from outside],
)
// woodcore:/object airborne-exterior-table

// woodcore:object doc-table airborne-interior-table
#doc-table(
  columns: (
    (id: "element", title: [Zone / element]),
    (id: "basis", title: [Basis]),
    (id: "requirement", title: [Requirement], unit: "dB"),
    (id: "execution", title: [Execution / values]),
  ),
  hidden: (),
  rows: (
    (element: [[Bedroom / bedroom]], basis: [SIA 181, tab. 3], requirement: [[…]], execution: [[…]]),
  ),
  caption: [Airborne sound within the building],
)
// woodcore:/object airborne-interior-table

// woodcore:object doc-table impact-sound-table
#doc-table(
  columns: (
    (id: "element", title: [Zone / element]),
    (id: "basis", title: [Basis]),
    (id: "requirement", title: [Requirement], unit: "dB"),
    (id: "execution", title: [Execution / values]),
  ),
  hidden: (),
  rows: (
    (element: [[Terrace / bedroom]], basis: [SIA 181, tab. 5], requirement: [[…]], execution: [[…]]),
  ),
  caption: [Impact sound],
)
// woodcore:/object impact-sound-table

// woodcore:object doc-table installation-noise-table
#doc-table(
  columns: (
    (id: "kind", title: [Type of noise]),
    (id: "element", title: [Zone / element]),
    (id: "basis", title: [Basis]),
    (id: "requirement", title: [Requirement], unit: "dB"),
    (id: "execution", title: [Execution / values]),
  ),
  hidden: (),
  rows: (
    (kind: [Isolated noises], element: [[Kitchen / restaurant]], basis: [SIA 181, tab. 6], requirement: [[…]], execution: [[…]]),
  ),
  caption: [Noise from technical installations],
)
// woodcore:/object installation-noise-table
