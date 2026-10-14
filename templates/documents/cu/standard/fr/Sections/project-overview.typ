#import "/commands.typ": *

// woodcore:object heading title
== Projet et environnement
// woodcore:/object title

// woodcore:object doc-table project-overview-table
#doc-table(
  columns: (
    (id: "item", title: [Élément]),
    (id: "text", title: [Description], kind: "wide"),
  ),
  hidden: (),
  rows: (
    (item: [Environnement], text: [[Situation, altitude, topographie, nature du terrain, bâtiments voisins, zones protégées …]]),
    (item: [Concept architectural], text: [[Organisation par niveau (sous-sols, rez-de-chaussée, étages), mode de construction (bois, béton, mixte), ouvrage existant ou neuf, intégration dans le site, grandes ouvertures, aménagement intérieur, toiture (plate, photovoltaïque …), public cible, matériaux à faible émission de CO₂ …]]),
    (item: [Plans du projet], text: [[Plans et maquette 3D de l'architecte faisant foi, avec leur état (indice, date).]]),
    (item: [Particularités], text: [[Contraintes d'accès et de transport, exploitation à maintenir pendant les travaux, contraintes environnementales …]]),
  ),
  caption: [Description générale],
  header: false,
)
// woodcore:/object project-overview-table
