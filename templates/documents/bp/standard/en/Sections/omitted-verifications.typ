#import "/commands.typ": *

// woodcore:object heading title
== Omitted verifications
// woodcore:/object title

// woodcore:object text p1
A verification can be dispensed with if it is clear that it is not decisive; it can also be dispensed with if it can be shown that the corresponding requirements are of secondary importance or can be achieved by constructional or execution measures. The chosen procedure shall in every case be documented in the basis of design (SIA 260, 4.4.1.2 and 4.4.1.3).
// woodcore:/object p1

// woodcore:object doc-table omitted-verifications-table
#doc-table(
  columns: (
    (id: "verification", title: [Verification omitted]),
    (id: "reason", title: [Reason]),
    (id: "justification", title: [Justification]),
  ),
  hidden: (),
  rows: (
    (verification: [[…]], reason: [Not decisive], justification: [[…]]),
  ),
  caption: [Verifications not carried out],
)
// woodcore:/object omitted-verifications-table
