#import "/commands.typ": *

// woodcore:object heading title
=== Séisme
// woodcore:/object title
// woodcore:shared earthquake

// woodcore:object text p1
Les séismes sont traités comme des actions accidentelles selon la norme SIA 261, chapitre 16. Le dimensionnement selon cette norme admet des dommages à la structure porteuse en cas de séisme, sans effondrement du bâtiment. Les éléments non porteurs relevant du gros œuvre (cloisons légères, murs de maçonnerie, etc.) sont assurés contre le basculement ; les autres éléments secondaires ne relèvent pas de la responsabilité de l'ingénieur.
// woodcore:/object p1

// woodcore:object text seismic-zone
*Zone sismique (SIA 261, ch. 16.2.1)* :
- Zone Z1a ($a_"gd"$ = 0.6 m/s²)
- Zone Z1b ($a_"gd"$ = 0.8 m/s²)
- Zone Z2 ($a_"gd"$ = 1.0 m/s²)
- Zone Z3a ($a_"gd"$ = 1.3 m/s²)
- Zone Z3b ($a_"gd"$ = 1.6 m/s²)
// woodcore:/object seismic-zone

// woodcore:object text ground-class
*Classe de terrain de fondation (SIA 261, ch. 16.2.2, tab. 24)* :
- Classe A : rocher ou formation similaire
- Classe B : sable et gravier très compacts ou argile très ferme
- Classe C : sable et gravier compacts ou moyennement compacts, argile ferme
- Classe D : terrain meuble lâche à moyennement compact, ou cohésif mou à ferme
- Classe E : couche superficielle de type C ou D sur un sol plus rigide
- Classe F : dépôts sensibles, organiques ou très mous (étude de site spectrale requise)
// woodcore:/object ground-class

// woodcore:object text building-class
*Classe d'ouvrage (SIA 261, ch. 16.3, tab. 25)* :
- Classe d'ouvrage I (facteur d'importance $γ_f$ = 1.0)
- Classe d'ouvrage II (facteur d'importance $γ_f$ = 1.2)
- Classe d'ouvrage III (facteur d'importance $γ_f$ = 1.5)
// woodcore:/object building-class

// woodcore:object table seismic-parameters
#figure(
  table(
    columns: (auto, 1fr),
    align: (left, left),
    table.hline(stroke: 1pt),
    [Facteur de comportement q], [[…]],
    [Méthode d'analyse], [[Méthode des forces de remplacement / méthode du spectre de réponse]],
    [Éléments secondaires], [[Sécurisation contre le basculement des cloisons légères et des murs de maçonnerie non porteurs]],
    table.hline(stroke: 1pt),
  ),
  caption: [Paramètres du dimensionnement sismique],
)
// woodcore:/object seismic-parameters
// woodcore:/shared earthquake
