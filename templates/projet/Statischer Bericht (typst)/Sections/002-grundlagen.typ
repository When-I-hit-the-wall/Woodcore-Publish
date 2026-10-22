#import "../commands.typ": *

= Grundlagen

Pläne, Unterlagen und Annahmen.

// Every position plan drawn in Woodcore's «Plan de position» tab (docs/domain/position-plans.md §3.3sexies).
#for id in ids("plan") {
  figure(image-positions-plan(id), kind: image, caption: context t-str("plan.caption", id: id))
}
