#import "/commands.typ": *

// woodcore:object heading title
== Timber and wood-based materials
// woodcore:/object title

// woodcore:object table timber-table
#figure(
  table(
    columns: (auto, auto, auto, auto, auto),
    align: (left, right, right, right, right),
    table.hline(stroke: 1pt),
    table.header([*Designation*], [*Bending $f_"md"$*], [*Compression parallel to the grain $f_(c,0,d)$*], [*Shear $f_"vd"$*], [*Mean modulus of elasticity $E_(0,"mean")$*]),  // woodcore:hidden 6=[Characteristic density $rho_k$] 7=[Unit weight $gamma$]
    table.hline(stroke: 0.5pt),
    [C24], [14.1], [12.4], [1.5], [11000],  // woodcore:hidden 6=[350] 7=[5]
    [GL24h], [16.0], [16.0], [1.8], [11500],  // woodcore:hidden 6=[385] 7=[5]
    table.hline(stroke: 1pt),
  ),
  caption: [Solid timber and glulam (SIA 265, design values for moisture class 1)],
)
// woodcore:/object timber-table

// woodcore:object text timber-table-notes
The strength and stiffness properties, the resistance factors and the factors taking account of load duration are applied in accordance with the SIA standards in force. For wood-based materials (panels, cross-laminated timber) the values of SIA 265/1 apply.
// woodcore:/object timber-table-notes
