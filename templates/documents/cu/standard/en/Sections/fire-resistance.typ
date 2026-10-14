#import "/commands.typ": *

// woodcore:object heading title
== Fire resistance of the structure
// woodcore:/object title

// woodcore:object text p1
The fire protection requirements are set in accordance with the Swiss fire protection regulations (VKF), the Lignum fire protection documentation and the [constructional / technical] fire protection concept. Fire is treated as an accidental action in accordance with SIA 261, chapter 15. The requirements for the structure are:
// woodcore:/object p1

// woodcore:object doc-choice structure-fire-resistance
#doc-choice(
  label: [Fire resistance of the structure (general)],
  options: (
    (id: "r30", label: [R 30]),
    (id: "r60", label: [R 60]),
    (id: "r90", label: [R 90]),
    (id: "none", label: [No requirements]),
  ),
  selected: "r60",
)
// woodcore:/object structure-fire-resistance

// woodcore:object text p2
[Exceptions by storey (e.g. basement, top storey).] The required fire resistance is in principle provided by the concrete cover to the reinforcement and the minimum member dimensions (concrete), by fire protection cladding or charring calculations in accordance with the Lignum documentation (timber); prefabricated concrete or steel members must have a VKF approval.
// woodcore:/object p2
