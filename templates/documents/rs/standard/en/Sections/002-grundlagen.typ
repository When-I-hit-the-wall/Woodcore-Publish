#import "/commands.typ": *

// woodcore:object heading title
= Basis
// woodcore:/object title

// woodcore:object text p1
Plans, documents and assumptions.
// woodcore:/object p1

// Every position plan drawn in Woodcore's «Plan de position» tab (docs/domain/position-plans.md §3.3sexies).
#for id in ids("plan") {
  figure(image-positions-plan(id), kind: image, caption: context t-str("plan.caption", id: id))
}
