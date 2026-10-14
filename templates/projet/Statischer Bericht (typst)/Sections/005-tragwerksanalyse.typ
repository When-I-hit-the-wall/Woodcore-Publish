#import "../commands.typ": *

= Tragwerksanalyse

Statische Modelle und Schnittkräfte.

// Every static model drawn in Woodcore's «Modèles statiques» tab (docs/domain/static-models.md §3.3octies).
#for id in static-model-ids() {
  show-static-model(id)
}
