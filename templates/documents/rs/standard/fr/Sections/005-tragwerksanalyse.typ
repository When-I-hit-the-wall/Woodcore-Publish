#import "/commands.typ": *

// woodcore:object heading title
= Analyse structurale
// woodcore:/object title

// woodcore:object text p1
Modèles statiques et efforts intérieurs.
// woodcore:/object p1

// Every static model drawn in Woodcore's «Modèles statiques» tab (docs/domain/static-models.md §3.3octies).
#for id in static-model-ids() {
  show-static-model(id)
}
