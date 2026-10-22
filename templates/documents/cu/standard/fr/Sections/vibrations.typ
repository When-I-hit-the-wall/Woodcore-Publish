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

// woodcore:object table vibrations-table
#figure(
  table(
    columns: (1fr, auto, auto),
    align: (left, right, left),
    table.hline(stroke: 1pt),
    table.header([*Utilisation*], [*Fréquence propre minimale $f$*], [*Base*]),
    table.hline(stroke: 0.5pt),
    [Halles de gymnastique et de sport], [> 8.0], [SIA 260, Tab. 5],
    [Locaux de danse et salles de concert], [> 7.0], [SIA 260, Tab. 5],
    table.hline(stroke: 1pt),
  ),
  caption: [Fréquences propres minimales],
)
// woodcore:/object vibrations-table
// woodcore:/shared vibrations
