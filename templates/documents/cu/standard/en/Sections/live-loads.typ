#import "/commands.typ": *

// woodcore:object heading title
== Live loads
// woodcore:/object title
// woodcore:shared live-loads

// woodcore:object text p1
The permissible loads depend on the intended use of the floor concerned and are set by SIA 261, chapter 8, Table 8. 1 kN/m² corresponds to about 100 kg/m² and 10 kN to about one tonne.
// woodcore:/object p1

// woodcore:object text p2
The following values are maximum values: they are used for the design and must not be exceeded during the service life. [For the vertical members of multi-storey buildings, the live load may be reduced in accordance with SIA 261, 8.3: to be specified.]
// woodcore:/object p2

// woodcore:object live-load-table live-loads-table
#live-load-table(
  columns: (
    (id: "zone"),
    (id: "storey"),
    (id: "use"),
    (id: "category"),
    (id: "q_k"),
    (id: "Q_k"),
  ),
  hidden: (),
  rows: (
    (zone: [[…]], storey: [[…]], use: [[Dwelling rooms]], category: "A1", q_k: auto, Q_k: auto),
    (zone: [[…]], storey: [[Roof]], use: [[Accessible for maintenance only]], category: "H", q_k: auto, Q_k: auto),
  ),
  caption: [Live loads by part of building and storey],
  notes: (
    [$Q_k$: bearing area 50 × 50 mm; $Q_k$ generally need not be combined with $q_k$. For areas with storage racking or used by lifting equipment, $Q_k$ is to be determined for the project (SIA 261, Table 8, note 1).],
    [Categories F and G: $Q_k$ and $q_k$ act simultaneously; two point loads of $Q_k$/2 at 1.8 m spacing on bearing areas of 200 × 200 mm (SIA 261, Table 8, notes 3 and 4).],
    [Category E: the values are to be determined for the project (SIA 261, 8.2.2) and recorded in the service criteria agreement and in the basis of design.],
    [Roofs that can be walked on or driven on are treated according to their use as areas of categories A to G; category H applies only to roofs accessible for maintenance work only (SIA 261, Table 8, note 5).],
  ),
)
// woodcore:/object live-loads-table

// woodcore:object text p3
Special measures (SIA 261, 8.4): areas of category E are marked in the rooms concerned with the maximum live load agreed here; access to areas of category F is restricted by constructional measures; areas of categories F and G are marked and signposted accordingly. [Areas open to vehicles: speed limit and signposting at the entrance.]
// woodcore:/object p3
// woodcore:/shared live-loads
