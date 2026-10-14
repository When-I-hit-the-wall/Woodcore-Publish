#import "/commands.typ": *

// woodcore:object heading title
== Séisme
// woodcore:/object title
// woodcore:shared earthquake

// woodcore:object text p1
Les séismes sont traités comme des actions accidentelles selon la norme SIA 261, chapitre 16. Le dimensionnement selon cette norme admet des dommages à la structure porteuse en cas de séisme, sans effondrement du bâtiment. Les éléments non porteurs relevant du gros œuvre (cloisons légères, murs de maçonnerie, etc.) sont assurés contre le basculement ; les autres éléments secondaires ne relèvent pas de la responsabilité de l'ingénieur.
// woodcore:/object p1

// woodcore:object doc-choice seismic-zone
#doc-choice(
  label: [Zone sismique (SIA 261, ch. 16.2.1)],
  options: (
    (id: "z1a", label: [Zone Z1a ($a_"gd"$ = 0.6 m/s²)]),
    (id: "z1b", label: [Zone Z1b ($a_"gd"$ = 0.8 m/s²)]),
    (id: "z2", label: [Zone Z2 ($a_"gd"$ = 1.0 m/s²)]),
    (id: "z3a", label: [Zone Z3a ($a_"gd"$ = 1.3 m/s²)]),
    (id: "z3b", label: [Zone Z3b ($a_"gd"$ = 1.6 m/s²)]),
  ),
  selected: none,
)
// woodcore:/object seismic-zone

// woodcore:object doc-choice ground-class
#doc-choice(
  label: [Classe de terrain de fondation (SIA 261, ch. 16.2.2, tab. 24)],
  options: (
    (id: "a", label: [Classe A : rocher ou formation similaire]),
    (id: "b", label: [Classe B : sable et gravier très compacts ou argile très ferme]),
    (id: "c", label: [Classe C : sable et gravier compacts ou moyennement compacts, argile ferme]),
    (id: "d", label: [Classe D : terrain meuble lâche à moyennement compact, ou cohésif mou à ferme]),
    (id: "e", label: [Classe E : couche superficielle de type C ou D sur un sol plus rigide]),
    (id: "f", label: [Classe F : dépôts sensibles, organiques ou très mous (étude de site spectrale requise)]),
  ),
  selected: none,
)
// woodcore:/object ground-class

// woodcore:object doc-choice building-class
#doc-choice(
  label: [Classe d'ouvrage (SIA 261, ch. 16.3, tab. 25)],
  options: (
    (id: "bwk-1", label: [Classe d'ouvrage I (facteur d'importance $γ_f$ = 1.0)]),
    (id: "bwk-2", label: [Classe d'ouvrage II (facteur d'importance $γ_f$ = 1.2)]),
    (id: "bwk-3", label: [Classe d'ouvrage III (facteur d'importance $γ_f$ = 1.5)]),
  ),
  selected: none,
)
// woodcore:/object building-class

// woodcore:object doc-table seismic-parameters
#doc-table(
  columns: (
    (id: "item", title: [Élément]),
    (id: "text", title: [Description], kind: "wide"),
  ),
  hidden: (),
  rows: (
    (item: [Facteur de comportement q], text: [[…]]),
    (item: [Méthode d'analyse], text: [[Méthode des forces de remplacement / méthode du spectre de réponse]]),
    (item: [Éléments secondaires], text: [[Sécurisation contre le basculement des cloisons légères et des murs de maçonnerie non porteurs]]),
  ),
  caption: [Paramètres du dimensionnement sismique],
  header: false,
)
// woodcore:/object seismic-parameters
// woodcore:/shared earthquake
