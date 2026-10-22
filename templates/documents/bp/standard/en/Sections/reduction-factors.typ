#import "/commands.typ": *

// woodcore:object heading title
== Reduction factors
// woodcore:/object title

// woodcore:object text p1
The reduction factors ψ₀, ψ₁ and ψ₂ take account of the reduced probability of the most unfavourable values of several independent actions occurring at the same time; they give the occasional, frequent and quasi-permanent value of a variable action (SIA 260, 3.2.3 and Annex A, Table 2). [The snow load depends on the reference altitude h₀ in accordance with SIA 261.]
// woodcore:/object p1

// woodcore:object table reduction-factors-table
#figure(
  table(
    columns: (auto, auto, auto, auto),
    align: (left, center, center, center),
    table.hline(stroke: 1pt),
    table.header([*Action*], [*$psi_0$*], [*$psi_1$*], [*$psi_2$*]),
    table.hline(stroke: 0.5pt),
    [Live load, category [A]], [0.7], [0.5], [0.3],
    [Live load, category [C]], [0.7], [0.7], [0.6],
    [Live load, category H], [0], [0], [0],
    [Snow], [$1 - 60 \/ h_0$], [$1 - 250 \/ h_0$], [$1 - 1000 \/ h_0$],
    [Wind], [0.6], [0.5], [0],
    table.hline(stroke: 1pt),
  ),
  caption: [Reduction factors for buildings],
)
// woodcore:/object reduction-factors-table
