#import "/commands.typ": *

// woodcore:object heading title
== Akzeptierte Risiken
// woodcore:/object title
// woodcore:shared accepted-risks

// woodcore:object text p1
Die folgenden Risiken werden von der Bauherrschaft akzeptiert; sie sind nicht Teil der Bemessung:
// woodcore:/object p1

// woodcore:object doc-checklist accepted-risks-list
#doc-checklist(
  label: [Akzeptierte Risiken],
  options: (
    (id: "ground", label: [Baugrundrisiko], checked: true, text: [Trotz vorgängig durchgeführten Baugrunduntersuchungen können in der Ausführung Inhomogenitäten im Baugrund auftreten, die zum Zeitpunkt der Planung nicht bekannt waren. Die daraus entstehenden Kostenfolgen und Terminverzögerungen gelten als akzeptiertes Risiko der Bauherrschaft.]),
    (id: "exceptional", label: [Aussergewöhnliche Ereignisse], checked: true, text: [Aussergewöhnliche Ereignisse wie Terrorismus, Flugzeugabsturz und -anprall, Explosion, Chemieunfall usw. gelten als akzeptierte Risiken.]),
    (id: "explosion", label: [Explosion], checked: true, text: [[Akzeptiertes Risiko / aussergewöhnliche Einwirkung.]]),
    (id: "vandalism", label: [Vandalenakte und mutwillige Tragwerksbeschädigungen], checked: true, text: [Mutwillige Beschädigungen des Tragwerks sind nicht Teil der Bemessung.]),
    (id: "flood", label: [Überschwemmung], checked: false, text: [[Akzeptiertes Risiko / aussergewöhnliche Einwirkung.]]),
    (id: "rockfall", label: [Steinschlag], checked: false, text: [[…]]),
    (id: "avalanche", label: [Lawinen], checked: false, text: [[…]]),
  ),
  only-checked: true,
)
// woodcore:/object accepted-risks-list
// woodcore:/shared accepted-risks
