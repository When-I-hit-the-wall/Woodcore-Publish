#import "../commands.typ": *

= Tragwerksanalyse

Statische Modelle und Schnittkräfte.

// Every static model drawn in Woodcore's «Modèles statiques» tab (docs/domain/static-models.md §3.3octies).
#for id in ids("static-model") {
  figure(image-static-model(id), kind: image, caption: [#id])
}
