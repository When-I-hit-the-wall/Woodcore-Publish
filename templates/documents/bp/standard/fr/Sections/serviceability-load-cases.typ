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

// woodcore:object table sls-load-cases-table
#figure(
  table(
    columns: (auto, auto, auto, auto, auto, auto),
    align: (left, left, right, right, right, center),
    table.hline(stroke: 1pt),
    table.header([*Élément*], [*Cas*], [*Poids propre et charges permanentes*], [*Charge utile [catégorie]*], [*Neige*], [*Vent*]),
    table.hline(stroke: 0.5pt),
    [[Toiture]], [CC 1], [1.0], [–], [1.0], [$ψ_0$],
    [[Étage type]], [CC 2], [1.0], [1.0], [–], [$ψ_0$],
    table.hline(stroke: 1pt),
  ),
  caption: [Cas de charge : aptitude au service],
)
// woodcore:/object sls-load-cases-table
