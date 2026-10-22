#import "/commands.typ": *

// woodcore:object heading title
= Structural analysis
// woodcore:/object title

// woodcore:object text p1
Static models and internal forces.
// woodcore:/object p1

// Every static model drawn in Woodcore's «Modèles statiques» tab (docs/domain/static-models.md §3.3octies).
#for id in ids("static-model") {
  figure(image-static-model(id), kind: image, caption: [#id])
}
