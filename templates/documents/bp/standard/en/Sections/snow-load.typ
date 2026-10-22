#import "/commands.typ": *

// woodcore:object heading title
=== Snow
// woodcore:/object title

// woodcore:object text p1
The snow load is determined in accordance with SIA 261, chapter 5, for the project site. The characteristic value on roofs, related to the covered plan area, is:
// woodcore:/object p1

// woodcore:object text p2
$ q_k = mu_i dot C_e dot C_T dot s_k $
// woodcore:/object p2

// woodcore:object text p3
with the value on level ground (5.2.6), the reference altitude h₀ being determined in accordance with Annex D:
// woodcore:/object p3

// woodcore:object text p4
$ s_k = [1 + (h_0 / 350)^2] dot 0.4 " kN/m"^2 >= 0.9 " kN/m"^2 $
// woodcore:/object p4

// woodcore:object text p5
[A value agreed with the owner or based on measurements is to be justified here (5.2.1).]
// woodcore:/object p5

// woodcore:object table snow-parameters
#figure(
  table(
    columns: (1fr, auto, auto, auto),
    align: (left, center, right, left),
    table.hline(stroke: 1pt),
    table.header([*Parameter*], [*Symbol*], [*Value*], [*Unit*]),
    table.hline(stroke: 0.5pt),
    [Altitude of the site], [], [[…]], [m],
    [Reference altitude], [$h_0$], [[…]], [m],
    [Exposure coefficient], [$C_e$], [[…]], [],
    [Thermal coefficient], [$C_T$], [[…]], [],
    [Roof shape coefficient], [$mu$], [[…]], [],
    [Snow load on level ground], [$s_k$], [[…]], [kN/m²],
    [Snow load on the roof], [$q_k$], [[…]], [kN/m²],
    table.hline(stroke: 1pt),
  ),
  caption: [Snow load parameters],
)
// woodcore:/object snow-parameters
