#import "/commands.typ": *

// woodcore:object heading title
=== Earthquake
// woodcore:/object title
// woodcore:shared earthquake

// woodcore:object text p1
Earthquakes are treated as accidental actions in accordance with SIA 261, chapter 16. Design in accordance with this standard permits damage to the structure in the event of an earthquake, but the building must not collapse. Non-loadbearing members relevant to the shell (light partitions, masonry walls, etc.) are secured against tipping; all other secondary members are outside the engineer's responsibility.
// woodcore:/object p1

// woodcore:object text seismic-zone
*Seismic zone (SIA 261, 16.2.1)*:
- Zone Z1a ($a_"gd"$ = 0.6 m/s²)
- Zone Z1b ($a_"gd"$ = 0.8 m/s²)
- Zone Z2 ($a_"gd"$ = 1.0 m/s²)
- Zone Z3a ($a_"gd"$ = 1.3 m/s²)
- Zone Z3b ($a_"gd"$ = 1.6 m/s²)
// woodcore:/object seismic-zone

// woodcore:object text ground-class
*Ground class (SIA 261, 16.2.2, Table 24)*:
- Ground class A: rock or rock-like formation
- Ground class B: very dense sand or gravel or very stiff clay
- Ground class C: dense or medium-dense sand or gravel, or stiff clay
- Ground class D: loose to medium-dense granular soil, or soft to stiff cohesive soil
- Ground class E: surface layer as in C or D over stiffer material
- Ground class F: sensitive, organic or very soft deposits (spectral site study required)
// woodcore:/object ground-class

// woodcore:object text building-class
*Building class (SIA 261, 16.3, Table 25)*:
- Building class I (importance factor $γ_f$ = 1.0)
- Building class II (importance factor $γ_f$ = 1.2)
- Building class III (importance factor $γ_f$ = 1.5)
// woodcore:/object building-class

// woodcore:object table seismic-parameters
#figure(
  table(
    columns: (auto, 1fr),
    align: (left, left),
    table.hline(stroke: 1pt),
    [Behaviour factor q], [[…]],
    [Method of analysis], [[Equivalent lateral force method / response spectrum method]],
    [Secondary members], [[Tipping restraint for light partitions and non-loadbearing masonry walls]],
    table.hline(stroke: 1pt),
  ),
  caption: [Seismic design parameters],
)
// woodcore:/object seismic-parameters
// woodcore:/shared earthquake
