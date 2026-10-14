#import "/commands.typ": *

// woodcore:object heading title
== Earthquake
// woodcore:/object title
// woodcore:shared earthquake

// woodcore:object text p1
Earthquakes are treated as accidental actions in accordance with SIA 261, chapter 16. Design in accordance with this standard permits damage to the structure in the event of an earthquake, but the building must not collapse. Non-loadbearing members relevant to the shell (light partitions, masonry walls, etc.) are secured against tipping; all other secondary members are outside the engineer's responsibility.
// woodcore:/object p1

// woodcore:object doc-choice seismic-zone
#doc-choice(
  label: [Seismic zone (SIA 261, 16.2.1)],
  options: (
    (id: "z1a", label: [Zone Z1a ($a_"gd"$ = 0.6 m/s²)]),
    (id: "z1b", label: [Zone Z1b ($a_"gd"$ = 0.8 m/s²)]),
    (id: "z2", label: [Zone Z2 ($a_"gd"$ = 1.0 m/s²)]),
    (id: "z3a", label: [Zone Z3a ($a_"gd"$ = 1.3 m/s²)]),
    (id: "z3b", label: [Zone Z3b ($a_"gd"$ = 1.6 m/s²)]),
  ),
  selected: none,
)
// woodcore:/object seismic-zone

// woodcore:object doc-choice ground-class
#doc-choice(
  label: [Ground class (SIA 261, 16.2.2, Table 24)],
  options: (
    (id: "a", label: [Ground class A: rock or rock-like formation]),
    (id: "b", label: [Ground class B: very dense sand or gravel or very stiff clay]),
    (id: "c", label: [Ground class C: dense or medium-dense sand or gravel, or stiff clay]),
    (id: "d", label: [Ground class D: loose to medium-dense granular soil, or soft to stiff cohesive soil]),
    (id: "e", label: [Ground class E: surface layer as in C or D over stiffer material]),
    (id: "f", label: [Ground class F: sensitive, organic or very soft deposits (spectral site study required)]),
  ),
  selected: none,
)
// woodcore:/object ground-class

// woodcore:object doc-choice building-class
#doc-choice(
  label: [Building class (SIA 261, 16.3, Table 25)],
  options: (
    (id: "bwk-1", label: [Building class I (importance factor $γ_f$ = 1.0)]),
    (id: "bwk-2", label: [Building class II (importance factor $γ_f$ = 1.2)]),
    (id: "bwk-3", label: [Building class III (importance factor $γ_f$ = 1.5)]),
  ),
  selected: none,
)
// woodcore:/object building-class

// woodcore:object doc-table seismic-parameters
#doc-table(
  columns: (
    (id: "item", title: [Item]),
    (id: "text", title: [Description], kind: "wide"),
  ),
  hidden: (),
  rows: (
    (item: [Behaviour factor q], text: [[…]]),
    (item: [Method of analysis], text: [[Equivalent lateral force method / response spectrum method]]),
    (item: [Secondary members], text: [[Tipping restraint for light partitions and non-loadbearing masonry walls]]),
  ),
  caption: [Seismic design parameters],
  header: false,
)
// woodcore:/object seismic-parameters
// woodcore:/shared earthquake
