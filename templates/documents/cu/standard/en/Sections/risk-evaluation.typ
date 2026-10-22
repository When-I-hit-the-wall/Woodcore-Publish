#import "/commands.typ": *

// woodcore:object heading title
== Risk evaluation and protection objectives
// woodcore:/object title

// woodcore:object text p1
The actions on the structures are taken into account in accordance with SIA 261. The objectives of protection and the degree of protection are determined on the basis of a risk evaluation (SIA 260, 2.2.3). The objectives of protection and the special risks are treated as follows:
// woodcore:/object p1

// woodcore:object table hazards-table
#figure(
  table(
    columns: (auto, auto, auto),
    align: (left, left, left),
    table.hline(stroke: 1pt),
    table.header([*Hazard*], [*Treatment*], [*Remark*]),
    table.hline(stroke: 0.5pt),
    [Temperature], [Considered in the design], [Climatic temperature variations are taken into account in the design of the external bracing and stabilising members.],
    [Impact], [Considered in the design], [Accidental action in accordance with SIA 261. [Vehicles, fork-lift trucks …]],
    [Fire], [Considered in the design], [Accidental action in accordance with SIA 261; the requirements are taken into account in accordance with the Swiss fire protection regulations.],
    [Earthquake], [Considered in the design], [Accidental action in accordance with SIA 261.],
    [Explosion], [Accepted risk], [[Accepted risk / accidental action.]],
    [Flooding], [Accepted risk], [[Accepted risk / accidental action.]],
    [Rockfall], [Not relevant], [[…]],
    [Avalanches], [Not relevant], [[…]],
    [Vandalism], [Accepted risk], [[…]],
    [Lightning], [Responsibility of others], [The lightning protection concept is not within the engineer's scope.],
    table.hline(stroke: 1pt),
  ),
  caption: [Hazards and special risks],
)
// woodcore:/object hazards-table

// woodcore:object text hazards-table-notes
Risks classed as “accepted” are listed in the section “Accepted risks”.
// woodcore:/object hazards-table-notes
