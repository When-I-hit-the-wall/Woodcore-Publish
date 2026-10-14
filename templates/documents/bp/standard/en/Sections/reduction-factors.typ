#import "/commands.typ": *

// woodcore:object heading title
== Reduction factors
// woodcore:/object title

// woodcore:object text p1
The reduction factors ψ₀, ψ₁ and ψ₂ take account of the reduced probability of the most unfavourable values of several independent actions occurring at the same time; they give the occasional, frequent and quasi-permanent value of a variable action (SIA 260, 3.2.3 and Annex A, Table 2). [The snow load depends on the reference altitude h₀ in accordance with SIA 261.]
// woodcore:/object p1

// woodcore:object doc-table reduction-factors-table
#doc-table(
  columns: (
    (id: "action", title: [Action]),
    (id: "psi_0", title: [$psi_0$], kind: "math"),
    (id: "psi_1", title: [$psi_1$], kind: "math"),
    (id: "psi_2", title: [$psi_2$], kind: "math"),
  ),
  hidden: (),
  rows: (
    (action: [Live load, category [A]], psi_0: 0.7, psi_1: 0.5, psi_2: 0.3),
    (action: [Live load, category [C]], psi_0: 0.7, psi_1: 0.7, psi_2: 0.6),
    (action: [Live load, category H], psi_0: 0, psi_1: 0, psi_2: 0),
    (action: [Snow], psi_0: [$1 - 60 \/ h_0$], psi_1: [$1 - 250 \/ h_0$], psi_2: [$1 - 1000 \/ h_0$]),
    (action: [Wind], psi_0: 0.6, psi_1: 0.5, psi_2: 0),
  ),
  caption: [Reduction factors for buildings],
)
// woodcore:/object reduction-factors-table
