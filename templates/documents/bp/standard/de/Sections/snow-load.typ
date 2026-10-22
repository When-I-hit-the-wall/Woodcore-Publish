#import "/commands.typ": *

// woodcore:object heading title
=== Schnee
// woodcore:/object title

// woodcore:object text p1
Die Schneelast wird nach der Norm SIA 261, Kapitel 5, für den Projektstandort ermittelt. Der charakteristische Wert auf Dächern, bezogen auf die überdeckte Grundrissfläche, beträgt:
// woodcore:/object p1

// woodcore:object text p2
$ q_k = mu_i dot C_e dot C_T dot s_k $
// woodcore:/object p2

// woodcore:object text p3
mit dem Wert auf horizontalem Gelände (Ziffer 5.2.6), wobei die Bezugshöhe h₀ nach Anhang D zu ermitteln ist:
// woodcore:/object p3

// woodcore:object text p4
$ s_k = [1 + (h_0 / 350)^2] dot 0.4 " kN/m"^2 >= 0.9 " kN/m"^2 $
// woodcore:/object p4

// woodcore:object text p5
[Ein von der Bauherrschaft vereinbarter oder auf Messungen beruhender Wert ist hier zu begründen (Ziffer 5.2.1).]
// woodcore:/object p5

// woodcore:object table snow-parameters
#figure(
  table(
    columns: (1fr, auto, auto, auto),
    align: (left, center, right, left),
    table.hline(stroke: 1pt),
    table.header([*Parameter*], [*Symbol*], [*Wert*], [*Einheit*]),
    table.hline(stroke: 0.5pt),
    [Höhe über Meer], [], [[…]], [m],
    [Bezugshöhe], [$h_0$], [[…]], [m],
    [Expositionsbeiwert], [$C_e$], [[…]], [],
    [Thermischer Beiwert], [$C_T$], [[…]], [],
    [Dachformbeiwert], [$mu$], [[…]], [],
    [Schneelast auf horizontalem Gelände], [$s_k$], [[…]], [kN/m²],
    [Schneelast auf dem Dach], [$q_k$], [[…]], [kN/m²],
    table.hline(stroke: 1pt),
  ),
  caption: [Parameter der Schneelast],
)
// woodcore:/object snow-parameters
