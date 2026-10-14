#import "/commands.typ": *

// woodcore:object heading title
== Assurance qualité et contrôles
// woodcore:/object title

// woodcore:object text p1
La garantie d'une fiabilité adéquate exige des mesures d'assurance qualité durant l'élaboration du projet, l'exécution, l'utilisation et la maintenance (SIA 260, ch. 2.3.6), avec responsabilités, démarches, contrôles et mécanismes de correction (ch. 2.5.2). Le système porteur est choisi de manière à offrir une redondance suffisante (insensibilité à une défaillance locale, ch. 2.4.6). Les instruments essentiels sont [le plan de contrôle du projeteur et le plan d'essais de l'entreprise, selon le mémento SIA 2007 « Qualität im Bauwesen »].
// woodcore:/object p1

// woodcore:object doc-table controls-table
#doc-table(
  columns: (
    (id: "phase", title: [Phase]),
    (id: "measure", title: [Mesure]),
    (id: "responsible", title: [Responsable]),
    (id: "verification", title: [Contrôle / preuve]),
  ),
  hidden: (),
  rows: (
    (phase: [Élaboration du projet], measure: [[Vérification $E_d$ ≤ $R_d$ selon les normes SIA ; contrôle de plausibilité des résultats]], responsible: [[Ingénieur]], verification: [[Contrôle par un tiers]]),
    (phase: [Exécution], measure: [[Programme d'assurance qualité de l'entreprise ; contrôle et surveillance des matériaux utilisés]], responsible: [[Entreprise / direction des travaux]], verification: [[Plan de contrôle]]),
  ),
  caption: [Mesures et contrôles],
)
// woodcore:/object controls-table
