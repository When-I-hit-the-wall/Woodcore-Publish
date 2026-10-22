#import "/commands.typ": *

// woodcore:object heading title
= Historique des versions
// woodcore:/object title

// woodcore:object text p1
Les révisions du présent rapport, la plus récente en premier -- saisies dans l'onglet « Journal » de Woodcore.
// woodcore:/object p1

// The level decides what each revision prints: 1 its label, 2 also the short description, 3 everything. `form:` sets them as a table (here), a list («list») or a grid of cards («grid»).
#include domain-file("journal", "rs")
