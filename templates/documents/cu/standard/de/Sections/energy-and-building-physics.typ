#import "/commands.typ": *

// woodcore:object heading title
== Energie, Wärmeschutz, Feuchteschutz und Luftdichtheit
// woodcore:/object title

// woodcore:object doc-table energy-table
#doc-table(
  columns: (
    (id: "item", title: [Element]),
    (id: "text", title: [Beschreibung], kind: "wide"),
  ),
  hidden: (),
  rows: (
    (item: [Energiekonzept], text: [[Angestrebte Energieversorgung, Heizung, Energieerzeugung und -speicherung, Lüftung, Klimatisierung. Verweis auf das Energiekonzept der Fachperson (Verfasser, Datum).]]),
    (item: [Wärmeschutz], text: [[Angestrebtes Label (Minergie …) oder keines.] Es gelten die Anforderungen der Norm SIA 180.]),
    (item: [Feuchteschutz], text: [Es gelten die Anforderungen der Norm SIA 180.]),
    (item: [Luftdichtheit], text: [Es gelten die Anforderungen der Norm SIA 180.]),
  ),
  caption: [Energie und Bauphysik],
  header: false,
)
// woodcore:/object energy-table
