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

// woodcore:object doc-table snow-parameters
#doc-table(
  columns: (
    (id: "parameter", title: [Parameter], kind: "wide"),
    (id: "symbol", title: [Symbol], kind: "math"),
    (id: "value", title: [Value], kind: "number"),
    (id: "unit", title: [Unit]),
  ),
  hidden: (),
  rows: (
    (parameter: [Altitude of the site], symbol: [], value: [[…]], unit: [m]),
    (parameter: [Reference altitude], symbol: [$h_0$], value: [[…]], unit: [m]),
    (parameter: [Exposure coefficient], symbol: [$C_e$], value: [[…]], unit: []),
    (parameter: [Thermal coefficient], symbol: [$C_T$], value: [[…]], unit: []),
    (parameter: [Roof shape coefficient], symbol: [$mu$], value: [[…]], unit: []),
    (parameter: [Snow load on level ground], symbol: [$s_k$], value: [[…]], unit: [kN/m²]),
    (parameter: [Snow load on the roof], symbol: [$q_k$], value: [[…]], unit: [kN/m²]),
  ),
  caption: [Snow load parameters],
)
// woodcore:/object snow-parameters
