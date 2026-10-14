#import "/commands.typ": *

// woodcore:object heading title
== Nutzungsdauer
// woodcore:/object title
// woodcore:shared service-life

// woodcore:object text p1
Die Nutzungsdauer ist die Zeitspanne, während welcher das Bauwerk nach heutigen Erkenntnissen den in der Nutzungsvereinbarung definierten Nutzungsarten genügen soll. Sie wird mit der Bauherrschaft vereinbart; während dieser Zeit führt die Bauherrschaft die periodischen Unterhaltsarbeiten aus.
// woodcore:/object p1

// woodcore:object doc-choice service-life-class
#doc-choice(
  label: [Nutzungsdauer des Tragwerks (Richtwerte, SIA 260, Ziffer 2.3.2)],
  options: (
    (id: "temporary", label: [Temporäres Bauwerk: bis 10 Jahre]),
    (id: "replaceable", label: [Austauschbares Bauteil: bis 25 Jahre]),
    (id: "normal", label: [Gebäude und andere Bauwerke von normaler Bedeutung: 50 Jahre]),
    (id: "major", label: [Bauwerk von übergeordneter Bedeutung: 100 Jahre]),
  ),
  selected: "normal",
)
// woodcore:/object service-life-class

// woodcore:object doc-table service-life-table
#doc-table(
  columns: (
    (id: "part", title: [Bauteil]),
    (id: "years", title: [Nutzungsdauer]),
    (id: "remark", title: [Bemerkung]),
  ),
  hidden: ("remark",),
  rows: (
    (part: [Tragwerk], years: [50 Jahre], remark: []),
    (part: [Abdichtungen], years: [25 Jahre], remark: []),
    (part: [Fassade], years: [25 Jahre], remark: []),
    (part: [Bedachung], years: [25 Jahre], remark: []),
    (part: [Austauschbare Bauteile], years: [25 Jahre], remark: []),
  ),
  caption: [Vereinbarte Nutzungsdauer nach Bauteil],
)
// woodcore:/object service-life-table
// woodcore:/shared service-life
