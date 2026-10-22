#import "/000-Typst-Config/commands.typ": *

= Grundlagen

== Velo Unterstand

=== Positionsplan

#figure(image-positions-plan("Velo-Unterstand", width: 70%), kind: image, caption: context t-str("plan.caption", id: "Velo-Unterstand"))

=== Pläne

#grid(
  columns: (1fr, 1fr),
  gutter: 10pt,

  image("/Images/Plan-VeloUnterstand-1.png", width: 100%),
  image("/Images/Plan-VeloUnterstand-2.png", width: 100%),

  grid.cell(
    colspan: 2,
    image("/Images/Plan-VeloUnterstand-3.png", width: 100%),
  ),
)

== Pavillon

=== Positionsplan

#figure(image-positions-plan("Pavillon", width: 50%), kind: image, caption: context t-str("plan.caption", id: "Pavillon"))

=== Pläne

#grid(
  columns: (1fr, 1fr),
  gutter: 10pt,

  image("/Images/Plan-Pavillon-1.png", width: 100%),
  image("/Images/Plan-Pavillon-2.png", width: 100%),

  grid.cell(
    colspan: 2,
    image("/Images/Plan-Pavillon-3.png", width: 50%),
  ),
)

== Gerätehaus

=== Positionsplan

#figure(image-positions-plan("Geratehaus", width: 70%), kind: image, caption: context t-str("plan.caption", id: "Geratehaus"))

=== Pläne

#grid(
  columns: (2fr, 1fr),
  gutter: 10pt,

  image("/Images/Plan-Geratehaus-1.png", width: 100%),
  image("/Images/Plan-Geratehaus-2.png", width: 100%),

  grid.cell(
    colspan: 2,
    image("/Images/Plan-Geratehaus-3.png", width: 70%),
  ),
)

== Fluchttreppe

=== Positionsplan

#figure(image-positions-plan("Fluchttreppe", width: 30%), kind: image, caption: context t-str("plan.caption", id: "Fluchttreppe"))

=== Pläne

#grid(
  columns: (1fr, 2fr),
  gutter: 10pt,

  image("/Images/Plan-Fluchttreppe-1.png", width: 100%),
  image("/Images/Plan-Fluchttreppe-2.png", width: 100%),

  grid.cell(
    colspan: 2,
    image("/Images/Plan-Fluchttreppe-3.png", width: 70%),
  ),
)