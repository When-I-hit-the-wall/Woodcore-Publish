#import "/commands.typ": *

// woodcore:object heading title
== Timber moisture and creep
// woodcore:/object title

// woodcore:object doc-choice moisture-class
#doc-choice(
  label: [Moisture class (SIA 265, Table 3)],
  options: (
    (id: "1", label: [Moisture class 1: mean moisture content ≤ 12 %, protected from the weather]),
    (id: "2", label: [Moisture class 2: > 12 to 20 %, partly protected from the weather or directly exposed]),
    (id: "3", label: [Moisture class 3: > 20 %, damp or under water]),
  ),
  selected: "1",
)
// woodcore:/object moisture-class

// woodcore:object doc-table moisture-factors
#doc-table(
  columns: (
    (id: "item", title: [Item]),
    (id: "text", title: [Description], kind: "wide"),
  ),
  hidden: (),
  rows: (
    (item: [Strength reduction $η_w$], text: [[according to the moisture class chosen (SIA 265, Table 4)]]),
    (item: [Stiffness reduction $η_w$], text: [[according to the moisture class chosen (SIA 265, Table 4)]]),
    (item: [Creep coefficient φ, timber preconditioned to service moisture], text: [[…]]),
    (item: [Creep coefficient φ, timber installed wet or partly dried], text: [[…]]),
  ),
  caption: [Moisture and creep factors],
  header: false,
)
// woodcore:/object moisture-factors
