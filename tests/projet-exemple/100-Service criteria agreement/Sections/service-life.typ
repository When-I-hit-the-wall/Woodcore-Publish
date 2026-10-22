#import "/000-Typst-Config/commands.typ": *

// woodcore:object heading title
== Nutzungsdauer
// woodcore:/object title
// woodcore:shared service-life

// woodcore:object text p1
Die Nutzungsdauer ist die Zeitspanne, während welcher das Bauwerk nach heutigen Erkenntnissen den in der Nutzungsvereinbarung definierten Nutzungsarten genügen soll. Sie wird mit der Bauherrschaft vereinbart; während dieser Zeit führt die Bauherrschaft die periodischen Unterhaltsarbeiten aus.
// woodcore:/object p1

// woodcore:object text service-life-class
*Nutzungsdauer des Tragwerks (Richtwerte, SIA 260, Ziffer 2.3.2)*: Gebäude und andere Bauwerke von normaler Bedeutung: 50 Jahre
// woodcore:/object service-life-class

// woodcore:object table service-life-table
#figure(
  table(
    columns: (auto, auto),
    align: (left, left),
    table.hline(stroke: 1pt),
    table.header([*Bauteil*], [*Nutzungsdauer*]),  // woodcore:hidden 3=[Bemerkung]
    table.hline(stroke: 0.5pt),
    [Tragwerk], [50 Jahre],  // woodcore:hidden 3=[]
    [Abdichtungen], [25 Jahre],  // woodcore:hidden 3=[]
    [Fassade], [25 Jahre],  // woodcore:hidden 3=[]
    [Bedachung], [25 Jahre],  // woodcore:hidden 3=[]
    [Austauschbare Bauteile], [25 Jahre],  // woodcore:hidden 3=[]
    table.hline(stroke: 1pt),
  ),
  caption: [Vereinbarte Nutzungsdauer nach Bauteil],
)
// woodcore:/object service-life-table
// woodcore:/shared service-life
