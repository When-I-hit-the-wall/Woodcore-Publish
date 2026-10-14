#import "/commands.typ": *

// woodcore:object heading title
=== Charges utiles
// woodcore:/object title
// woodcore:shared live-loads

// woodcore:object text p1
Les charges utiles admissibles dépendent de l'affectation prévue sur le sol de l'étage concerné ; elles sont fixées par la norme SIA 261, chapitre 8, tableau 8. 1 kN/m² correspond à environ 100 kg/m² et 10 kN à environ une tonne.
// woodcore:/object p1

// woodcore:object text p2
Les valeurs suivantes sont des valeurs maximales : elles servent au dimensionnement et ne doivent pas être dépassées pendant la durée d'utilisation. [Pour les éléments porteurs verticaux de bâtiments à plusieurs niveaux, la charge utile peut être réduite selon SIA 261, ch. 8.3 : à préciser.]
// woodcore:/object p2

// woodcore:object live-load-table live-loads-table
#live-load-table(
  columns: (
    (id: "zone"),
    (id: "storey"),
    (id: "use"),
    (id: "category"),
    (id: "q_k"),
    (id: "Q_k"),
  ),
  hidden: (),
  rows: (
    (zone: [[…]], storey: [[…]], use: [[Locaux d'habitation]], category: "A1", q_k: auto, Q_k: auto),
    (zone: [[…]], storey: [[Toiture]], use: [[Accessible pour l'entretien uniquement]], category: "H", q_k: auto, Q_k: auto),
  ),
  caption: [Charges utiles par zone et par niveau],
  notes: (
    [$Q_k$ : surface d'appui 50 × 50 mm ; en général, $Q_k$ n'est pas combinée avec $q_k$. Pour les surfaces avec rayonnages ou parcourues par des engins de levage, $Q_k$ est à fixer pour le projet (SIA 261, tableau 8, note 1).],
    [Catégories F et G : $Q_k$ et $q_k$ agissent simultanément ; deux charges ponctuelles de $Q_k$/2 à 1.8 m d'entraxe sur des surfaces d'appui de 200 × 200 mm (SIA 261, tableau 8, notes 3 et 4).],
    [Catégorie E : les valeurs sont à fixer pour le projet (SIA 261, ch. 8.2.2) et à consigner dans la convention d'utilisation et dans la base de projet.],
    [Les toitures praticables ou carrossables sont traitées selon leur utilisation comme des surfaces des catégories A à G ; la catégorie H ne vaut que pour les toitures accessibles uniquement pour l'entretien (SIA 261, tableau 8, note 5).],
  ),
)
// woodcore:/object live-loads-table

// woodcore:object text p3
Mesures particulières (SIA 261, ch. 8.4) : les surfaces de catégorie E sont signalées, dans les locaux concernés, par la valeur maximale de la charge utile convenue ici ; l'accès aux surfaces de catégorie F est limité par des mesures constructives ; les surfaces des catégories F et G sont signalées de manière appropriée. [Surfaces carrossables : limitation de vitesse et signalisation à l'entrée.]
// woodcore:/object p3
// woodcore:/shared live-loads
