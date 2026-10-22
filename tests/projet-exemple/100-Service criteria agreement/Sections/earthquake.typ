#import "/000-Typst-Config/commands.typ": *

// woodcore:object heading title
== Erdbeben
// woodcore:/object title
// woodcore:shared earthquake

// woodcore:object text p1
Erdbeben werden nach der Norm SIA 261, Kapitel 16, als aussergewöhnliche Einwirkungen behandelt. Die Bemessung nach dieser Norm lässt im Erdbebenfall Schäden an der Tragstruktur zu, das Gebäude darf jedoch nicht einstürzen. Nichttragende rohbaurelevante Bauteile (Leichtbauwände, Mauerwerkswände usw.) werden gegen Kippen gesichert; alle weiteren sekundären Bauteile liegen nicht im Verantwortungsbereich der Ingenieurin bzw. des Ingenieurs.
// woodcore:/object p1

// woodcore:object text seismic-zone
*Erdbebenzone (SIA 261, Ziffer 16.2.1)*:
- Zone Z1a ($a_"gd"$ = 0.6 m/s²)
- Zone Z1b ($a_"gd"$ = 0.8 m/s²)
- Zone Z2 ($a_"gd"$ = 1.0 m/s²)
- Zone Z3a ($a_"gd"$ = 1.3 m/s²)
- Zone Z3b ($a_"gd"$ = 1.6 m/s²)
// woodcore:/object seismic-zone

// woodcore:object text ground-class
*Baugrundklasse (SIA 261, Ziffer 16.2.2, Tab. 24)*:
- Baugrundklasse A: Fels oder felsähnliche Formation
- Baugrundklasse B: sehr dichter Sand, Kies oder sehr steifer Ton
- Baugrundklasse C: dichter oder mitteldichter Sand, Kies oder steifer Ton
- Baugrundklasse D: lockeres bis mitteldichtes Lockergestein oder weiches bis steifes kohäsives Lockergestein
- Baugrundklasse E: oberflächliche Schicht gemäss C oder D über steiferem Material
- Baugrundklasse F: strukturempfindliche, organische oder sehr weiche Ablagerungen (spektrale Standortstudie erforderlich)
// woodcore:/object ground-class

// woodcore:object text building-class
*Bauwerksklasse (SIA 261, Ziffer 16.3, Tab. 25)*:
- Bauwerksklasse I (Bedeutungsbeiwert $γ_f$ = 1.0)
- Bauwerksklasse II (Bedeutungsbeiwert $γ_f$ = 1.2)
- Bauwerksklasse III (Bedeutungsbeiwert $γ_f$ = 1.5)
// woodcore:/object building-class

// woodcore:object table seismic-parameters
#figure(
  table(
    columns: (auto, 1fr),
    align: (left, left),
    table.hline(stroke: 1pt),
    [Verhaltensbeiwert q], [[…]],
    [Berechnungsmethode], [[Ersatzkraftverfahren / Antwortspektrenverfahren]],
    [Sekundäre Bauteile], [[Kippsicherung von Leichtbauwänden und nichttragenden Mauerwerkswänden]],
    table.hline(stroke: 1pt),
  ),
  caption: [Parameter der Erdbebenbemessung],
)
// woodcore:/object seismic-parameters
// woodcore:/shared earthquake
