#import "/commands.typ": *

// woodcore:object heading title
== Extension future prévue
// woodcore:/object title

// woodcore:object text p1
[Si une surélévation ou une extension est envisagée : décrire l'option, les niveaux concernés et ce qui est déjà prévu dans la structure porteuse et les installations. Les charges de l'extension (poids propre, charges superposées, charges utiles) sont définies ci-dessous ; elles doivent être validées par l'ingénieur lors de l'étude ultérieure.]
// woodcore:/object p1

// woodcore:object table extension-loads
#figure(
  table(
    columns: (auto, auto, auto, auto),
    align: (left, left, right, right),
    table.hline(stroke: 1pt),
    table.header([*Niveau*], [*Utilisation / composition*], [*Charge superposée*], [*Charge utile*]),
    table.hline(stroke: 0.5pt),
    [[…]], [[…]], [[…]], [[…]],
    table.hline(stroke: 1pt),
  ),
  caption: [Charges prévues pour l'extension],
)
// woodcore:/object extension-loads
