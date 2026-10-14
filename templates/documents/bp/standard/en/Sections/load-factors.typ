#import "/commands.typ": *

// woodcore:object heading title
== Load factors
// woodcore:/object title

// woodcore:object text p1
Type of building: [building]. The load factors of SIA 260, Table 1, apply to the verification of structural safety. For a building, the values of the limit state of Type 2 (reaching the ultimate resistance of the structure or one of its structural members) are generally governing.
// woodcore:/object p1

// woodcore:object doc-table load-factors-table
#doc-table(
  columns: (
    (id: "action", title: [Actions], kind: "wide"),
    (id: "type1", title: [Limit state Type 1], kind: "number"),
    (id: "type2", title: [Limit state Type 2], kind: "number"),
    (id: "type3", title: [Limit state Type 3], kind: "number"),
  ),
  hidden: (),
  rows: (
    (action: [Permanent actions, acting unfavourably: $γ_(G,"sup")$], type1: 1.1, type2: 1.35, type3: 1.0),
    (action: [Permanent actions, acting favourably: $γ_(G,"inf")$], type1: 0.9, type2: 0.8, type3: 1.0),
    (action: [Variable actions in general: $γ_Q$], type1: 1.5, type2: 1.5, type3: 1.3),
  ),
  caption: [Load factors for the verification of structural safety],
  notes: (
    [G is multiplied by $γ_(G,"sup")$ or $γ_(G,"inf")$ depending on whether the overall effect is unfavourable or favourable (SIA 260, Table 1, note 1). The factors for actions from the ground and from traffic are given in the standard.],
  ),
)
// woodcore:/object load-factors-table
