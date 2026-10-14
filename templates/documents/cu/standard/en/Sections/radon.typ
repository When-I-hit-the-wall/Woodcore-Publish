#import "/commands.typ": *

// woodcore:object heading title
== Radon exposure
// woodcore:/object title

// woodcore:object doc-choice radon-risk
#doc-choice(
  label: [Radon risk (radon map of Switzerland, FOPH)],
  options: (
    (id: "low", label: [Low risk: no shell construction measures]),
    (id: "medium", label: [Medium risk: measures in accordance with FOPH recommendations (e.g. sealed pipe penetrations)]),
    (id: "high", label: [High risk: measures in accordance with FOPH recommendations (e.g. sealed penetrations, base slab of sealing class 1)]),
  ),
  selected: none,
)
// woodcore:/object radon-risk

// woodcore:object text p1
Any sealing against radon is the responsibility of the owner and the architect, not of the engineer.
// woodcore:/object p1
