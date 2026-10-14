#import "/commands.typ": *

// woodcore:object heading title
== Vibrations
// woodcore:/object title
// woodcore:shared vibrations

// woodcore:object text p1
Les vibrations ne doivent ni limiter l'aptitude au fonctionnement de l'ouvrage ni nuire au confort des personnes qui l'utilisent. Les fréquences propres minimales suivantes sont des valeurs indicatives ; des valeurs différentes sont admises si un calcul dynamique plus précis, tenant compte de l'amortissement, est effectué. [Critères particuliers pour les planchers légers (bois) : …]
// woodcore:/object p1

// woodcore:object text p2
Les appareils générateurs de vibrations sont posés de manière flottante, selon les indications du physicien du bâtiment. [Vibrations dues au trafic ferroviaire ou routier : à clarifier par le maître de l'ouvrage.]
// woodcore:/object p2

// woodcore:object doc-table vibrations-table
#doc-table(
  columns: (
    (id: "use", title: [Utilisation], kind: "wide"),
    (id: "f", title: [Fréquence propre minimale $f$], unit: "Hz", kind: "number"),
    (id: "basis", title: [Base]),
  ),
  hidden: (),
  rows: (
    (use: [Halles de gymnastique et de sport], f: [> 8.0], basis: [SIA 260, Tab. 5]),
    (use: [Locaux de danse et salles de concert], f: [> 7.0], basis: [SIA 260, Tab. 5]),
  ),
  caption: [Fréquences propres minimales],
)
// woodcore:/object vibrations-table
// woodcore:/shared vibrations
