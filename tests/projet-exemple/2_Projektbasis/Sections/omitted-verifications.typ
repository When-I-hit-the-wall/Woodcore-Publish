#import "/commands.typ": *

// woodcore:object heading title
== Verzicht auf Nachweise
// woodcore:/object title

// woodcore:object text p1
Auf einen Nachweis kann verzichtet werden, wenn feststeht, dass er nicht massgebend wird; ebenso darf auf einen Nachweis verzichtet werden, wenn gezeigt wird, dass die entsprechenden Anforderungen von untergeordneter Bedeutung sind oder mit konstruktiven oder ausführungstechnischen Massnahmen erreicht werden können. Das gewählte Vorgehen ist auf jeden Fall in der Projektbasis zu dokumentieren (SIA 260, Ziffern 4.4.1.2 und 4.4.1.3).
// woodcore:/object p1

// woodcore:object doc-table omitted-verifications-table
#doc-table(
  columns: (
    (id: "verification", title: [Entfallender Nachweis]),
    (id: "reason", title: [Grund]),
    (id: "justification", title: [Begründung]),
  ),
  hidden: (),
  rows: (
    (verification: [[…]], reason: [Nicht massgebend], justification: [[…]]),
  ),
  caption: [Nicht geführte Nachweise],
)
// woodcore:/object omitted-verifications-table
