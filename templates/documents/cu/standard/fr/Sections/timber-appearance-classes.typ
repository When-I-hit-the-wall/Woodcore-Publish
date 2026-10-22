#import "/commands.typ": *

// woodcore:object heading title
== Qualité de surface des éléments en bois
// woodcore:/object title

// woodcore:object text p1
Le bois est une matière première naturelle : des nœuds, des poches de résine (selon l'essence), des différences de couleur et parfois des décolorations apparaissent en surface. Le nombre et la taille des nœuds admissibles ainsi que l'admissibilité des décolorations se définissent par des classes d'aspect, à fixer avec l'ingénieur durant l'étude. Une définition détaillée figure dans la publication de Lignum « Qualitätskriterien für Holz und Holzwerkstoffe im Bau und Ausbau, Handelsgebräuche für die Schweiz » [édition].
// woodcore:/object p1

// woodcore:object text p2
Avec le temps, la surface du bois change : les éléments exposés aux intempéries grisonnent, ce qui ne constitue pas un défaut mais une modification optique ; en intérieur, le bois fonce sous l'effet des UV. Sous l'effet des variations d'humidité de l'air, le bois gonfle et se rétracte, ce qui peut provoquer des fissures isolées dans les éléments linéaires (poteaux, poutres).
// woodcore:/object p2

// woodcore:object table appearance-classes-table
#figure(
  table(
    columns: (auto, auto, auto),
    align: (left, left, left),
    table.hline(stroke: 1pt),
    table.header([*Élément*], [*Produit*], [*Classe d'aspect*]),  // woodcore:hidden 4=[Remarque]
    table.hline(stroke: 0.5pt),
    [[Poteaux et poutres apparents]], [Bois massif et lamellé-collé], [N : qualité normale (bois de construction)],  // woodcore:hidden 4=[]
    [[Éléments non visibles]], [Bois massif et lamellé-collé], [I : qualité industrielle, sans exigence d'aspect],  // woodcore:hidden 4=[]
    table.hline(stroke: 1pt),
  ),
  caption: [Classes d'aspect par élément],
)
// woodcore:/object appearance-classes-table
