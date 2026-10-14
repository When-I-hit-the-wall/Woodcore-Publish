#import "/commands.typ": *

// woodcore:object heading title
== Dauerhaftigkeit
// woodcore:/object title
// woodcore:shared durability

// woodcore:object text p1
Es soll ein möglichst unterhaltsarmes und auf eine lange Gebrauchsdauer der Bauteile ausgelegtes Bauwerk entstehen; es soll entsprechend den geplanten Nutzungen verwendet werden können, wobei künftige Nutzungsänderungen zusätzliche Massnahmen erforderlich machen können. Die Massnahmen zur Gewährleistung der Dauerhaftigkeit (SIA 260, Ziffer 2.3.7) sind: [konstruktiver Holzschutz (Befeuchtung vermeiden, Wasserablauf und Austrocknung sicherstellen), Baustoffwahl und Behandlung, Korrosionsschutz von Stahlteilen und Verbindungsmitteln, Betonüberdeckung, Schutz gegen Chloride und Frost …].
// woodcore:/object p1

// woodcore:object doc-checklist timber-use-classes
#doc-checklist(
  label: [Gebrauchsklassen für Holz (SN EN 335, SIA 265.131)],
  options: (
    (id: "uc-1", label: [Gebrauchsklasse 1: Innenbereich, trocken], checked: false),
    (id: "uc-2", label: [Gebrauchsklasse 2: Innenbereich oder überdacht, nicht bewittert (Kondensation möglich)], checked: false),
    (id: "uc-3-1", label: [Gebrauchsklasse 3.1: Aussenbereich über Boden, kurze Befeuchtungsdauer], checked: false),
    (id: "uc-3-2", label: [Gebrauchsklasse 3.2: Aussenbereich über Boden, lange Befeuchtungsdauer], checked: false),
    (id: "uc-4", label: [Gebrauchsklasse 4: in Kontakt mit Erdreich oder Süsswasser], checked: false),
    (id: "uc-5", label: [Gebrauchsklasse 5: in Salzwasser getaucht], checked: false),
  ),
)
// woodcore:/object timber-use-classes

// woodcore:object doc-checklist concrete-exposure-classes
#doc-checklist(
  label: [Expositionsklassen für Beton (SN EN 206, SIA 262)],
  options: (
    (id: "xc1", label: [XC1: trocken oder dauernd nass], checked: false),
    (id: "xc2", label: [XC2: nass, selten trocken], checked: false),
    (id: "xc3", label: [XC3: mässige Feuchte], checked: false),
    (id: "xc4", label: [XC4: wechselnd nass und trocken], checked: false),
    (id: "xd1", label: [XD1: mässige Feuchte (Chloride)], checked: false),
    (id: "xd2", label: [XD2: nass, selten trocken (Chloride)], checked: false),
    (id: "xd3", label: [XD3: wechselnd nass und trocken (Chloride)], checked: false),
    (id: "xf1", label: [XF1: Frost, mässige Wassersättigung, ohne Taumittel], checked: false),
    (id: "xf2", label: [XF2: Frost, mässige Wassersättigung, mit Taumittel], checked: false),
    (id: "xf3", label: [XF3: Frost, hohe Wassersättigung, ohne Taumittel], checked: false),
    (id: "xf4", label: [XF4: Frost, hohe Wassersättigung, mit Taumittel], checked: false),
  ),
)
// woodcore:/object concrete-exposure-classes

// woodcore:object text p2
Der Korrosionsschutz des Bewehrungsstahls ist durch die Einhaltung einer genügenden Betonüberdeckung gemäss den aktuellen Normen sicherzustellen. [Schutz gegen Chloride in Parkierungsanlagen: chloridbeständiger Bodenbelag, Korrosionsschutzanstrich von Stahl-Stützenfüssen und -köpfen …]
// woodcore:/object p2
// woodcore:/shared durability
