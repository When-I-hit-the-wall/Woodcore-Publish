#import "/commands.typ": *

// woodcore:object heading title
= Accepted risks
// woodcore:/object title
// woodcore:shared accepted-risks

// woodcore:object text p1
The following risks are accepted by the owner; they are not part of the design:
// woodcore:/object p1

// woodcore:object doc-checklist accepted-risks-list
#doc-checklist(
  label: [Accepted risks],
  options: (
    (id: "ground", label: [Ground risk], checked: true, text: [Despite ground investigations carried out beforehand, inhomogeneities in the ground that were not known at the time of design may appear during construction. The resulting costs and delays are a risk accepted by the owner.]),
    (id: "exceptional", label: [Exceptional events], checked: true, text: [Exceptional events such as terrorism, aircraft crash or impact, explosion or a chemical accident are accepted risks.]),
    (id: "explosion", label: [Explosion], checked: true, text: [[Accepted risk / accidental action.]]),
    (id: "vandalism", label: [Vandalism and deliberate damage to the structure], checked: true, text: [Deliberate damage to the structure is not part of the design.]),
    (id: "flood", label: [Flooding], checked: false, text: [[Accepted risk / accidental action.]]),
    (id: "rockfall", label: [Rockfall], checked: false, text: [[…]]),
    (id: "avalanche", label: [Avalanches], checked: false, text: [[…]]),
  ),
  only-checked: true,
)
// woodcore:/object accepted-risks-list
// woodcore:/shared accepted-risks
