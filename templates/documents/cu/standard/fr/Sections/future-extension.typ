#import "/commands.typ": *

// woodcore:object heading title
== Extension future prévue
// woodcore:/object title

// woodcore:object text p1
[Si une surélévation ou une extension est envisagée : décrire l'option, les niveaux concernés et ce qui est déjà prévu dans la structure porteuse et les installations. Les charges de l'extension (poids propre, charges superposées, charges utiles) sont définies ci-dessous ; elles doivent être validées par l'ingénieur lors de l'étude ultérieure.]
// woodcore:/object p1

// woodcore:object doc-table extension-loads
#doc-table(
  columns: (
    (id: "storey", title: [Niveau]),
    (id: "buildup", title: [Utilisation / composition]),
    (id: "dead", title: [Charge superposée], unit: "kN/m²", kind: "number"),
    (id: "live", title: [Charge utile], unit: "kN/m²", kind: "number"),
  ),
  hidden: (),
  rows: (
    (storey: [[…]], buildup: [[…]], dead: [[…]], live: [[…]]),
  ),
  caption: [Charges prévues pour l'extension],
)
// woodcore:/object extension-loads
