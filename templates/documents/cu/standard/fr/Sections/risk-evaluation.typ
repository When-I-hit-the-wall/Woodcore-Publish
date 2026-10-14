#import "/commands.typ": *

// woodcore:object heading title
== Évaluation du risque et objectifs de protection
// woodcore:/object title

// woodcore:object text p1
Les actions sur les structures porteuses sont prises en compte selon la norme SIA 261. Les objectifs de protection et le degré de protection sont fixés sur la base d'une évaluation du risque (SIA 260, ch. 2.2.3). Les objectifs de protection et les risques particuliers sont traités comme suit :
// woodcore:/object p1

// woodcore:object doc-table hazards-table
#doc-table(
  columns: (
    (id: "hazard", title: [Danger]),
    (id: "handling", title: [Traitement]),
    (id: "remark", title: [Remarque]),
  ),
  hidden: (),
  rows: (
    (hazard: [Température], handling: [Pris en compte dans le dimensionnement], remark: [Les variations de température climatiques sont prises en compte dans le dimensionnement des éléments de contreventement et de stabilisation extérieurs.]),
    (hazard: [Choc], handling: [Pris en compte dans le dimensionnement], remark: [Action accidentelle selon la norme SIA 261. [Véhicules, chariots élévateurs …]]),
    (hazard: [Incendie], handling: [Pris en compte dans le dimensionnement], remark: [Action accidentelle selon la norme SIA 261 ; les exigences sont prises en compte selon les prescriptions suisses de protection incendie.]),
    (hazard: [Séisme], handling: [Pris en compte dans le dimensionnement], remark: [Action accidentelle selon la norme SIA 261.]),
    (hazard: [Explosion], handling: [Risque accepté], remark: [[Risque accepté / action accidentelle.]]),
    (hazard: [Inondation], handling: [Risque accepté], remark: [[Risque accepté / action accidentelle.]]),
    (hazard: [Chute de pierres], handling: [Sans objet], remark: [[…]]),
    (hazard: [Avalanches], handling: [Sans objet], remark: [[…]]),
    (hazard: [Vandalisme], handling: [Risque accepté], remark: [[…]]),
    (hazard: [Foudre], handling: [Relève d'un tiers], remark: [Le concept de protection contre la foudre ne relève pas de l'ingénieur.]),
  ),
  caption: [Dangers et risques particuliers],
  notes: (
    [Les risques classés « accepté » sont repris dans la section « Risques acceptés ».],
  ),
)
// woodcore:/object hazards-table
