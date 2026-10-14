#import "/commands.typ": *

// woodcore:object heading title
== États-limites ultimes
// woodcore:/object title

// woodcore:object text p1
La sécurité structurale est vérifiée pour les états-limites de types 2 et 3 lorsque la valeur de calcul des effets $E_d$ du cas de charge déterminant dans la situation de projet est inférieure ou égale à la valeur de calcul de la résistance $R_d$ (SIA 260, ch. 4.4.3.3) :
// woodcore:/object p1

// woodcore:object text p2
$ E_d <= R_d $
// woodcore:/object p2

// woodcore:object text p3
Pour l'état-limite de type 1 (stabilité d'ensemble), on vérifie $E_(d,"dst")$ ≤ $E_(d,"stb")$ (ch. 4.4.3.2) ; pour le type 4 (fatigue), $E_d$ ≤ $R_d$ (ch. 4.4.3.8). Dans le bâtiment, l'état-limite de type 2 (résistance ultime de la structure porteuse) est en général déterminant. [Le choix de ne pas vérifier un état-limite est justifié dans la section « Vérifications omises ».]
// woodcore:/object p3

// woodcore:object doc-checklist limit-state-types
#doc-checklist(
  label: [États-limites ultimes vérifiés],
  options: (
    (id: "type-1", label: [Type 1 : stabilité d'ensemble (renversement, soulèvement, flottaison)], checked: true),
    (id: "type-2", label: [Type 2 : résistance ultime de la structure porteuse ou d'un de ses éléments], checked: true),
    (id: "type-3", label: [Type 3 : résistance ultime du terrain de fondation], checked: false),
    (id: "type-4", label: [Type 4 : résistance à la fatigue], checked: false),
  ),
)
// woodcore:/object limit-state-types
