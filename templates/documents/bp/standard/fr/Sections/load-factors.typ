#import "/commands.typ": *

// woodcore:object heading title
== Facteurs de charge
// woodcore:/object title

// woodcore:object text p1
Type d'ouvrage : [bâtiment]. Les facteurs de charge de la norme SIA 260, tableau 1, s'appliquent pour la vérification de la sécurité structurale. Pour un bâtiment, les valeurs de l'état-limite de type 2 (résistance ultime de la structure porteuse ou d'un de ses éléments) sont en général déterminantes.
// woodcore:/object p1

// woodcore:object doc-table load-factors-table
#doc-table(
  columns: (
    (id: "action", title: [Actions], kind: "wide"),
    (id: "type1", title: [État-limite type 1], kind: "number"),
    (id: "type2", title: [État-limite type 2], kind: "number"),
    (id: "type3", title: [État-limite type 3], kind: "number"),
  ),
  hidden: (),
  rows: (
    (action: [Actions permanentes, effet défavorable : $γ_(G,"sup")$], type1: 1.1, type2: 1.35, type3: 1.0),
    (action: [Actions permanentes, effet favorable : $γ_(G,"inf")$], type1: 0.9, type2: 0.8, type3: 1.0),
    (action: [Actions variables en général : $γ_Q$], type1: 1.5, type2: 1.5, type3: 1.3),
  ),
  caption: [Facteurs de charge pour la vérification de la sécurité structurale],
  notes: (
    [G est multiplié par $γ_(G,"sup")$ ou par $γ_(G,"inf")$ selon que l'effet d'ensemble de l'action est défavorable ou favorable (SIA 260, tableau 1, note 1). Les facteurs des actions du terrain de fondation et du trafic figurent dans la norme.],
  ),
)
// woodcore:/object load-factors-table
