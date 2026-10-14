#import "/commands.typ": *

// woodcore:object heading title
== Risk evaluation and protection objectives
// woodcore:/object title

// woodcore:object text p1
The actions on the structures are taken into account in accordance with SIA 261. The objectives of protection and the degree of protection are determined on the basis of a risk evaluation (SIA 260, 2.2.3). The objectives of protection and the special risks are treated as follows:
// woodcore:/object p1

// woodcore:object doc-table hazards-table
#doc-table(
  columns: (
    (id: "hazard", title: [Hazard]),
    (id: "handling", title: [Treatment]),
    (id: "remark", title: [Remark]),
  ),
  hidden: (),
  rows: (
    (hazard: [Temperature], handling: [Considered in the design], remark: [Climatic temperature variations are taken into account in the design of the external bracing and stabilising members.]),
    (hazard: [Impact], handling: [Considered in the design], remark: [Accidental action in accordance with SIA 261. [Vehicles, fork-lift trucks …]]),
    (hazard: [Fire], handling: [Considered in the design], remark: [Accidental action in accordance with SIA 261; the requirements are taken into account in accordance with the Swiss fire protection regulations.]),
    (hazard: [Earthquake], handling: [Considered in the design], remark: [Accidental action in accordance with SIA 261.]),
    (hazard: [Explosion], handling: [Accepted risk], remark: [[Accepted risk / accidental action.]]),
    (hazard: [Flooding], handling: [Accepted risk], remark: [[Accepted risk / accidental action.]]),
    (hazard: [Rockfall], handling: [Not relevant], remark: [[…]]),
    (hazard: [Avalanches], handling: [Not relevant], remark: [[…]]),
    (hazard: [Vandalism], handling: [Accepted risk], remark: [[…]]),
    (hazard: [Lightning], handling: [Responsibility of others], remark: [The lightning protection concept is not within the engineer's scope.]),
  ),
  caption: [Hazards and special risks],
  notes: (
    [Risks classed as “accepted” are listed in the section “Accepted risks”.],
  ),
)
// woodcore:/object hazards-table
