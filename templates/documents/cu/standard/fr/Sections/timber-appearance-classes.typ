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

// woodcore:object doc-table appearance-classes-table
#doc-table(
  columns: (
    (id: "member", title: [Élément]),
    (id: "product", title: [Produit]),
    (id: "class", title: [Classe d'aspect]),
    (id: "remark", title: [Remarque]),
  ),
  hidden: ("remark",),
  rows: (
    (member: [[Poteaux et poutres apparents]], product: [Bois massif et lamellé-collé], class: [N : qualité normale (bois de construction)], remark: []),
    (member: [[Éléments non visibles]], product: [Bois massif et lamellé-collé], class: [I : qualité industrielle, sans exigence d'aspect], remark: []),
  ),
  caption: [Classes d'aspect par élément],
)
// woodcore:/object appearance-classes-table
