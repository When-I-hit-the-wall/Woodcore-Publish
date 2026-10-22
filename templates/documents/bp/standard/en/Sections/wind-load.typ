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

// woodcore:object table wind-parameters
#figure(
  table(
    columns: (1fr, auto, auto, auto),
    align: (left, center, right, left),
    table.hline(stroke: 1pt),
    table.header([*Parameter*], [*Symbol*], [*Value*], [*Unit*]),
    table.hline(stroke: 0.5pt),
    [Terrain category], [], [[…]], [],
    [Reference height above ground], [$z$], [[…]], [m],
    [Profile coefficient], [$c_h$], [[…]], [],
    [Reference dynamic pressure], [$q_(p 0)$], [[…]], [kN/m²],
    [Dynamic pressure], [$q_p$], [[…]], [kN/m²],
    table.hline(stroke: 1pt),
  ),
  caption: [Wind parameters],
)
// woodcore:/object wind-parameters
