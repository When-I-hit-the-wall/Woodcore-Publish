#import "/commands.typ": *

// woodcore:object heading title
=== Erdbeben
// woodcore:/object title
// woodcore:shared earthquake

// woodcore:object text p1
Erdbeben werden nach der Norm SIA 261, Kapitel 16, als aussergewöhnliche Einwirkungen behandelt. Die Bemessung nach dieser Norm lässt im Erdbebenfall Schäden an der Tragstruktur zu, das Gebäude darf jedoch nicht einstürzen. Nichttragende rohbaurelevante Bauteile (Leichtbauwände, Mauerwerkswände usw.) werden gegen Kippen gesichert; alle weiteren sekundären Bauteile liegen nicht im Verantwortungsbereich der Ingenieurin bzw. des Ingenieurs.
// woodcore:/object p1

// woodcore:object doc-choice seismic-zone
#doc-choice(
  label: [Erdbebenzone (SIA 261, Ziffer 16.2.1)],
  options: (
    (id: "z1a", label: [Zone Z1a ($a_"gd"$ = 0.6 m/s²)]),
    (id: "z1b", label: [Zone Z1b ($a_"gd"$ = 0.8 m/s²)]),
    (id: "z2", label: [Zone Z2 ($a_"gd"$ = 1.0 m/s²)]),
    (id: "z3a", label: [Zone Z3a ($a_"gd"$ = 1.3 m/s²)]),
    (id: "z3b", label: [Zone Z3b ($a_"gd"$ = 1.6 m/s²)]),
  ),
  selected: none,
)
// woodcore:/object seismic-zone

// woodcore:object doc-choice ground-class
#doc-choice(
  label: [Baugrundklasse (SIA 261, Ziffer 16.2.2, Tab. 24)],
  options: (
    (id: "a", label: [Baugrundklasse A: Fels oder felsähnliche Formation]),
    (id: "b", label: [Baugrundklasse B: sehr dichter Sand, Kies oder sehr steifer Ton]),
    (id: "c", label: [Baugrundklasse C: dichter oder mitteldichter Sand, Kies oder steifer Ton]),
    (id: "d", label: [Baugrundklasse D: lockeres bis mitteldichtes Lockergestein oder weiches bis steifes kohäsives Lockergestein]),
    (id: "e", label: [Baugrundklasse E: oberflächliche Schicht gemäss C oder D über steiferem Material]),
    (id: "f", label: [Baugrundklasse F: strukturempfindliche, organische oder sehr weiche Ablagerungen (spektrale Standortstudie erforderlich)]),
  ),
  selected: none,
)
// woodcore:/object ground-class

// woodcore:object doc-choice building-class
#doc-choice(
  label: [Bauwerksklasse (SIA 261, Ziffer 16.3, Tab. 25)],
  options: (
    (id: "bwk-1", label: [Bauwerksklasse I (Bedeutungsbeiwert $γ_f$ = 1.0)]),
    (id: "bwk-2", label: [Bauwerksklasse II (Bedeutungsbeiwert $γ_f$ = 1.2)]),
    (id: "bwk-3", label: [Bauwerksklasse III (Bedeutungsbeiwert $γ_f$ = 1.5)]),
  ),
  selected: none,
)
// woodcore:/object building-class

// woodcore:object doc-table seismic-parameters
#doc-table(
  columns: (
    (id: "item", title: [Element]),
    (id: "text", title: [Beschreibung], kind: "wide"),
  ),
  hidden: (),
  rows: (
    (item: [Verhaltensbeiwert q], text: [[…]]),
    (item: [Berechnungsmethode], text: [[Ersatzkraftverfahren / Antwortspektrenverfahren]]),
    (item: [Sekundäre Bauteile], text: [[Kippsicherung von Leichtbauwänden und nichttragenden Mauerwerkswänden]]),
  ),
  caption: [Parameter der Erdbebenbemessung],
  header: false,
)
// woodcore:/object seismic-parameters
// woodcore:/shared earthquake
