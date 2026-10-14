#import "/commands.typ": *

// woodcore:object heading title
== Cas de charge : aptitude au service
// woodcore:/object title

// woodcore:object text p1
Pour l'aptitude au service, les effets $E_d$ sont en général déterminés avec $γ_F$ = $γ_m$ = 1.0 (SIA 260, ch. 4.4.4.3). On distingue trois types de cas de charge (ch. 4.4.4.4) :
// woodcore:/object p1

// woodcore:object text p2
- cas de charge rares : action variable prépondérante à sa valeur caractéristique, actions concomitantes avec ψ₀ ;
- cas de charge fréquents : action variable prépondérante avec ψ₁, actions concomitantes avec ψ₂ ;
- cas de charge quasi permanents : toutes les actions variables avec ψ₂.
// woodcore:/object p2

// woodcore:object doc-table sls-load-cases-table
#doc-table(
  columns: (
    (id: "element", title: [Élément]),
    (id: "case", title: [Cas]),
    (id: "permanent", title: [Poids propre et charges permanentes], kind: "number"),
    (id: "live", title: [Charge utile [catégorie]], kind: "number"),
    (id: "snow", title: [Neige], kind: "number"),
    (id: "wind", title: [Vent], kind: "math"),
  ),
  hidden: (),
  rows: (
    (element: [[Toiture]], case: [CC 1], permanent: 1.0, live: [–], snow: 1.0, wind: [$ψ_0$]),
    (element: [[Étage type]], case: [CC 2], permanent: 1.0, live: 1.0, snow: [–], wind: [$ψ_0$]),
  ),
  caption: [Cas de charge : aptitude au service],
)
// woodcore:/object sls-load-cases-table
