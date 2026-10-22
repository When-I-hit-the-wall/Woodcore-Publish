#import "/commands.typ": *

// woodcore:object heading title
== Terrain de fondation
// woodcore:/object title
// woodcore:shared ground-conditions

// woodcore:object text p1
[Nature du terrain de fondation, stratigraphie, conditions hydrogéologiques (nappe phréatique, eaux de pente ou de couche) et source de ces informations : rapport géotechnique (auteur, date). Si les investigations ne sont pas terminées, indiquer celles qui restent nécessaires avant l'étude du projet.]
// woodcore:/object p1

// woodcore:object table ground-layers
#figure(
  table(
    columns: (auto, auto, auto),
    align: (left, left, right),
    table.hline(stroke: 1pt),
    table.header([*Couche*], [*Description*], [*Profondeur / épaisseur*]),
    table.hline(stroke: 0.5pt),
    [[…]], [[…]], [[…]],
    table.hline(stroke: 1pt),
  ),
  caption: [Couches de terrain],
)
// woodcore:/object ground-layers

// woodcore:object table design-water-levels
#figure(
  table(
    columns: (auto, auto),
    align: (left, right),
    table.hline(stroke: 1pt),
    table.header([*Niveau d'eau*], [*Cote (m s.m. / m ü. M. / m a.s.l.)*]),  // woodcore:hidden 3=[Remarque]
    table.hline(stroke: 0.5pt),
    [Crue (HW)], [[…]],  // woodcore:hidden 3=[]
    [Niveau moyen (MW)], [[…]],  // woodcore:hidden 3=[]
    table.hline(stroke: 1pt),
  ),
  caption: [Niveaux d'eau déterminants],
)
// woodcore:/object design-water-levels

// woodcore:object text ground-profile
#figure(rect(width: 100%, height: 5cm, stroke: 0.5pt + luma(60%))[[Figure avec légende et source]], caption: [Profil géologique / extrait du rapport géotechnique])
// woodcore:/object ground-profile
// woodcore:/shared ground-conditions
