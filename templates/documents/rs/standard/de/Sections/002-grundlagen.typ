#import "/commands.typ": *

// woodcore:object heading title
= Grundlagen
// woodcore:/object title

// woodcore:object text p1
Pläne, Unterlagen und Annahmen.
// woodcore:/object p1

// Every position plan drawn in Woodcore's «Plan de position» tab (docs/domain/position-plans.md §3.3sexies).
#for id in plan-ids() {
  show-plan(id)
}
