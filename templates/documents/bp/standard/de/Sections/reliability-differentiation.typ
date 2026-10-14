#import "/commands.typ": *

// woodcore:object heading title
== Erforderliche Zuverlässigkeit und Schadensfolgeklasse
// woodcore:/object title

// woodcore:object text p1
Die erforderliche Zuverlässigkeit kann je nach Grenzzustand und Bezugszeitraum differenziert werden, für das ganze Tragwerk oder für einzelne Bauteile (SIA 260, Ziffer 2.3.4). Sie kann von Art und Folgen eines Versagens, vom Ausmass der akzeptierten Schäden, von der Bedeutung des Bauwerks für die Katastrophenbewältigung, vom Aufwand zur Verminderung des Risikos und von den Möglichkeiten von Überwachung und Instandhaltung abhängen (Ziffer 2.3.5). [Die Wahl begründen.]
// woodcore:/object p1

// woodcore:object doc-choice consequence-class
#doc-choice(
  label: [Schadensfolgeklasse (zu vereinbaren)],
  options: (
    (id: "cc1", label: [CC1: geringe Folgen (Verlust von Menschenleben sowie wirtschaftliche, soziale oder Umweltfolgen gering oder vernachlässigbar)]),
    (id: "cc2", label: [CC2: mittlere Folgen (Verlust von Menschenleben, erhebliche wirtschaftliche, soziale oder Umweltfolgen)]),
    (id: "cc3", label: [CC3: hohe Folgen (Verlust von Menschenleben, sehr grosse wirtschaftliche, soziale oder Umweltfolgen)]),
  ),
  selected: "cc2",
)
// woodcore:/object consequence-class
