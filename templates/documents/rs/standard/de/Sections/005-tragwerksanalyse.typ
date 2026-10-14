#import "/commands.typ": *

// woodcore:object heading title
= Tragwerksanalyse
// woodcore:/object title

// woodcore:object text p1
Statische Modelle und Schnittkräfte.
// woodcore:/object p1

// Every static model drawn in Woodcore's «Modèles statiques» tab (docs/domain/static-models.md §3.3octies).
#for id in static-model-ids() {
  show-static-model(id)
}
