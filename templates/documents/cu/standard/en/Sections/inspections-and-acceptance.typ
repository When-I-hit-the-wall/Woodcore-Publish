#import "/commands.typ": *

// woodcore:object heading title
== Inspections and acceptance
// woodcore:/object title

// woodcore:object text p1
The following inspections and acceptance procedures are agreed; the detailed inspection programme is set out in the construction inspection plan.
// woodcore:/object p1

// woodcore:object doc-checklist inspections-list
#doc-checklist(
  label: [Inspections and acceptance],
  options: (
    (id: "shell-acceptance", label: [Acceptance of the timber shell before interior fit-out begins], checked: true),
    (id: "acoustic-measurements", label: [Acoustic measurements (floors) before the final floor finish is laid], checked: true),
    (id: "excavation-acceptance", label: [Acceptance of the excavation base by the engineer or the geologist], checked: false),
    (id: "timber-moisture", label: [Check of the timber moisture content before members are closed in], checked: false),
    (id: "final-acceptance", label: [Final acceptance [calendar week …]], checked: true),
  ),
)
// woodcore:/object inspections-list
