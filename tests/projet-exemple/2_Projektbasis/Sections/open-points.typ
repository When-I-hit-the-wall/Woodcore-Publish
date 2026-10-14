#import "/commands.typ": *

// woodcore:object heading title
== Offene Punkte
// woodcore:/object title

// woodcore:object text p1
Die folgenden Punkte sind in der nächsten Projektphase zu klären bzw. im Detail zu untersuchen:
// woodcore:/object p1

// woodcore:object doc-table open-points-table
#doc-table(
  columns: (
    (id: "point", title: [Zu klärender Punkt]),
    (id: "owner", title: [Verantwortlich]),
    (id: "phase", title: [Phase / Termin]),
    (id: "status", title: [Stand]),
  ),
  hidden: ("status",),
  rows: (
    (point: [[…]], owner: [[…]], phase: [[…]], status: []),
    (point: [[…]], owner: [[…]], phase: [[…]], status: []),
  ),
  caption: [Offene Punkte],
)
// woodcore:/object open-points-table
