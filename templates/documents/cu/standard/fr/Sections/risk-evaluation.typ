#import "/commands.typ": *

// woodcore:object heading title
== Évaluation du risque et objectifs de protection
// woodcore:/object title

// woodcore:object text p1
Les actions sur les structures porteuses sont prises en compte selon la norme SIA 261. Les objectifs de protection et le degré de protection sont fixés sur la base d'une évaluation du risque (SIA 260, ch. 2.2.3). Les objectifs de protection et les risques particuliers sont traités comme suit :
// woodcore:/object p1

// woodcore:object table hazards-table
#figure(
  table(
    columns: (auto, auto, auto),
    align: (left, left, left),
    table.hline(stroke: 1pt),
    table.header([*Danger*], [*Traitement*], [*Remarque*]),
    table.hline(stroke: 0.5pt),
    [Température], [Pris en compte dans le dimensionnement], [Les variations de température climatiques sont prises en compte dans le dimensionnement des éléments de contreventement et de stabilisation extérieurs.],
    [Choc], [Pris en compte dans le dimensionnement], [Action accidentelle selon la norme SIA 261. [Véhicules, chariots élévateurs …]],
    [Incendie], [Pris en compte dans le dimensionnement], [Action accidentelle selon la norme SIA 261 ; les exigences sont prises en compte selon les prescriptions suisses de protection incendie.],
    [Séisme], [Pris en compte dans le dimensionnement], [Action accidentelle selon la norme SIA 261.],
    [Explosion], [Risque accepté], [[Risque accepté / action accidentelle.]],
    [Inondation], [Risque accepté], [[Risque accepté / action accidentelle.]],
    [Chute de pierres], [Sans objet], [[…]],
    [Avalanches], [Sans objet], [[…]],
    [Vandalisme], [Risque accepté], [[…]],
    [Foudre], [Relève d'un tiers], [Le concept de protection contre la foudre ne relève pas de l'ingénieur.],
    table.hline(stroke: 1pt),
  ),
  caption: [Dangers et risques particuliers],
)
// woodcore:/object hazards-table

// woodcore:object text hazards-table-notes
Les risques classés « accepté » sont repris dans la section « Risques acceptés ».
// woodcore:/object hazards-table-notes
