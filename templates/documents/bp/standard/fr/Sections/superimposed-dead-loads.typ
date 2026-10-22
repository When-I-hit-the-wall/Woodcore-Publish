#import "/commands.typ": *

// woodcore:object heading title
=== Poids propres non structuraux (charges superposées)
// woodcore:/object title
// woodcore:shared superimposed-dead-loads

// woodcore:object text p1
Les charges superposées comprennent les compositions de sol, les cloisons non porteuses et les plafonds suspendus [ainsi que les installations et la façade]. Les valeurs suivantes sont des valeurs caractéristiques, déterminantes pour le dimensionnement.
// woodcore:/object p1

// woodcore:object table superimposed-table
#figure(
  table(
    columns: (auto, auto, 1fr, auto),
    align: (left, left, left, right),
    table.hline(stroke: 1pt),
    table.header([*Zone*], [*Niveau*], [*Utilisation / composition*], [*Poids propre non-structural*]),
    table.hline(stroke: 0.5pt),
    [[…]], [[…]], [[Composition du sol, cloisons non porteuses, plafonds suspendus]], [[…]],
    [[…]], [[Toiture]], [[Composition de toiture, végétalisation, installation photovoltaïque]], [[…]],
    table.hline(stroke: 1pt),
  ),
  caption: [Charges superposées par zone et par niveau],
)
// woodcore:/object superimposed-table

// woodcore:object text p2
Si les épaisseurs de remblai ou de revêtement prévues sont dépassées, une partie du matériau doit être remplacée par un matériau léger (isolant, argile expansée, béton cellulaire), uniquement en accord avec l'ingénieur ; le terrain ou le sol fini est relevé après exécution et les résultats sont remis à l'ingénieur pour contrôle (SIA 261, ch. 2.3.4). Les effets d'un retrait éventuel de la charge superposée sont examinés (ch. 2.3.5). [Mesures particulières : …]
// woodcore:/object p2
// woodcore:/shared superimposed-dead-loads
