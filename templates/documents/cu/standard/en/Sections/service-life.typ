#import "/commands.typ": *

// woodcore:object heading title
== Service life
// woodcore:/object title
// woodcore:shared service-life

// woodcore:object text p1
The service life is the period during which, according to present knowledge, the building is to satisfy the uses defined in the service criteria agreement. It is agreed with the owner; during this period the owner carries out the periodic maintenance work.
// woodcore:/object p1

// woodcore:object doc-choice service-life-class
#doc-choice(
  label: [Service life of the structure (indicative values, SIA 260, 2.3.2)],
  options: (
    (id: "temporary", label: [Temporary structure: up to 10 years]),
    (id: "replaceable", label: [Replaceable member: up to 25 years]),
    (id: "normal", label: [Building or other construction works of average importance: 50 years]),
    (id: "major", label: [Construction works of greater importance: 100 years]),
  ),
  selected: "normal",
)
// woodcore:/object service-life-class

// woodcore:object doc-table service-life-table
#doc-table(
  columns: (
    (id: "part", title: [Member]),
    (id: "years", title: [Service life]),
    (id: "remark", title: [Remark]),
  ),
  hidden: ("remark",),
  rows: (
    (part: [Structure], years: [50 years], remark: []),
    (part: [Waterproofing], years: [25 years], remark: []),
    (part: [Facade], years: [25 years], remark: []),
    (part: [Roof covering], years: [25 years], remark: []),
    (part: [Replaceable members], years: [25 years], remark: []),
  ),
  caption: [Agreed service life by member],
)
// woodcore:/object service-life-table
// woodcore:/shared service-life
