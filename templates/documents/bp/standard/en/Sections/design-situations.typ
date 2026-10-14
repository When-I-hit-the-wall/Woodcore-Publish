#import "/commands.typ": *

// woodcore:object heading title
== Design situations
// woodcore:/object title

// woodcore:object text p1
The design situations considered include all foreseeable conditions that may occur during execution and use (SIA 260, 4.2.1). They are divided into persistent, transient and accidental situations; construction states may be treated as persistent or transient design situations (4.2.2 and 4.2.3).
// woodcore:/object p1

// woodcore:object doc-table design-situations-table
#doc-table(
  columns: (
    (id: "situation", title: [Situation]),
    (id: "description", title: [Description]),
    (id: "governing", title: [Governing load cases]),
  ),
  hidden: (),
  rows: (
    (situation: [Persistent], description: [[Normal use]], governing: [[…]]),
    (situation: [Transient], description: [[Construction states]], governing: [[…]]),
    (situation: [Accidental], description: [[Earthquake, fire, impact]], governing: [[…]]),
  ),
  caption: [Design situations],
)
// woodcore:/object design-situations-table
