#import "/commands.typ": *

= Baustoffe

Baustoffe und Querschnitte des Tragwerks.

#for id in position-ids() {
  member(id, level: 1, description: true)
}

#if connector-ids().len() > 0 [
  == Verbindungsmittel

  #for id in connector-ids() {
    show-connector(id, description: true)
    parbreak()
  }
]
