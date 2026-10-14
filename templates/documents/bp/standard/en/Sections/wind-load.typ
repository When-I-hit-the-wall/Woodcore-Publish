#import "/commands.typ": *

// woodcore:object heading title
=== Wind
// woodcore:/object title

// woodcore:object text p1
The wind actions are determined in accordance with SIA 261, chapter 6. The dynamic pressure is:
// woodcore:/object p1

// woodcore:object text p2
$ q_p = c_h dot q_(p 0) $
// woodcore:/object p2

// woodcore:object text p3
the reference value $q_"p0"$ being taken from Annex E, the terrain category and the profile coefficient $c_h$ from 6.2.1 (Table 4). The pressure and force coefficients are those of Annex C.
// woodcore:/object p3

// woodcore:object doc-table wind-parameters
#doc-table(
  columns: (
    (id: "parameter", title: [Parameter], kind: "wide"),
    (id: "symbol", title: [Symbol], kind: "math"),
    (id: "value", title: [Value], kind: "number"),
    (id: "unit", title: [Unit]),
  ),
  hidden: (),
  rows: (
    (parameter: [Terrain category], symbol: [], value: [[…]], unit: []),
    (parameter: [Reference height above ground], symbol: [$z$], value: [[…]], unit: [m]),
    (parameter: [Profile coefficient], symbol: [$c_h$], value: [[…]], unit: []),
    (parameter: [Reference dynamic pressure], symbol: [$q_(p 0)$], value: [[…]], unit: [kN/m²]),
    (parameter: [Dynamic pressure], symbol: [$q_p$], value: [[…]], unit: [kN/m²]),
  ),
  caption: [Wind parameters],
)
// woodcore:/object wind-parameters
