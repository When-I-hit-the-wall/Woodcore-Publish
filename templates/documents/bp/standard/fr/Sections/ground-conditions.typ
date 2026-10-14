#import "/commands.typ": *

// woodcore:object heading title
== Terrain de fondation
// woodcore:/object title
// woodcore:shared ground-conditions

// woodcore:object text p1
[Nature du terrain de fondation, stratigraphie, conditions hydrogéologiques (nappe phréatique, eaux de pente ou de couche) et source de ces informations : rapport géotechnique (auteur, date). Si les investigations ne sont pas terminées, indiquer celles qui restent nécessaires avant l'étude du projet.]
// woodcore:/object p1

// woodcore:object doc-table ground-layers
#doc-table(
  columns: (
    (id: "layer", title: [Couche]),
    (id: "description", title: [Description]),
    (id: "depth", title: [Profondeur / épaisseur], unit: "m", kind: "number"),
  ),
  hidden: (),
  rows: (
    (layer: [[…]], description: [[…]], depth: [[…]]),
  ),
  caption: [Couches de terrain],
)
// woodcore:/object ground-layers

// woodcore:object doc-table design-water-levels
#doc-table(
  columns: (
    (id: "level", title: [Niveau d'eau]),
    (id: "elevation", title: [Cote (m s.m. / m ü. M. / m a.s.l.)], unit: "m", kind: "number"),
    (id: "remark", title: [Remarque]),
  ),
  hidden: ("remark",),
  rows: (
    (level: [Crue (HW)], elevation: [[…]], remark: []),
    (level: [Niveau moyen (MW)], elevation: [[…]], remark: []),
  ),
  caption: [Niveaux d'eau déterminants],
)
// woodcore:/object design-water-levels

// woodcore:object doc-image ground-profile
#doc-image(
  file: none,
  caption: [Profil géologique / extrait du rapport géotechnique],
  placeholder: [[Figure avec légende et source]],
)
// woodcore:/object ground-profile
// woodcore:/shared ground-conditions
