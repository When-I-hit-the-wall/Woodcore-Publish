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

// woodcore:object doc-table snow-parameters
#doc-table(
  columns: (
    (id: "parameter", title: [Parameter], kind: "wide"),
    (id: "symbol", title: [Symbol], kind: "math"),
    (id: "value", title: [Wert], kind: "number"),
    (id: "unit", title: [Einheit]),
  ),
  hidden: (),
  rows: (
    (parameter: [Höhe über Meer], symbol: [], value: [[…]], unit: [m]),
    (parameter: [Bezugshöhe], symbol: [$h_0$], value: [[…]], unit: [m]),
    (parameter: [Expositionsbeiwert], symbol: [$C_e$], value: [[…]], unit: []),
    (parameter: [Thermischer Beiwert], symbol: [$C_T$], value: [[…]], unit: []),
    (parameter: [Dachformbeiwert], symbol: [$mu$], value: [[…]], unit: []),
    (parameter: [Schneelast auf horizontalem Gelände], symbol: [$s_k$], value: [[…]], unit: [kN/m²]),
    (parameter: [Schneelast auf dem Dach], symbol: [$q_k$], value: [[…]], unit: [kN/m²]),
  ),
  caption: [Parameter der Schneelast],
)
// woodcore:/object snow-parameters
