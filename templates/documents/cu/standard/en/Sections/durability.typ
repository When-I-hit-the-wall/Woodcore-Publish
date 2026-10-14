#import "/commands.typ": *

// woodcore:object heading title
== Durability
// woodcore:/object title
// woodcore:shared durability

// woodcore:object text p1
The building should be low-maintenance and designed for a long service life of its members; it should be usable in accordance with the intended uses, although future changes of use may require additional measures. The measures to ensure durability (SIA 260, 2.3.7) are: [constructional timber protection (avoid wetting, ensure drainage and drying), choice and treatment of materials, corrosion protection of steel members and fasteners, concrete cover, protection against chlorides and frost …].
// woodcore:/object p1

// woodcore:object doc-checklist timber-use-classes
#doc-checklist(
  label: [Use classes for timber (SN EN 335, SIA 265.131)],
  options: (
    (id: "uc-1", label: [Use class 1: indoors, dry], checked: false),
    (id: "uc-2", label: [Use class 2: indoors or under cover, not exposed to the weather (condensation possible)], checked: false),
    (id: "uc-3-1", label: [Use class 3.1: outdoors above ground, short wetting periods], checked: false),
    (id: "uc-3-2", label: [Use class 3.2: outdoors above ground, prolonged wetting periods], checked: false),
    (id: "uc-4", label: [Use class 4: in contact with the ground or fresh water], checked: false),
    (id: "uc-5", label: [Use class 5: immersed in salt water], checked: false),
  ),
)
// woodcore:/object timber-use-classes

// woodcore:object doc-checklist concrete-exposure-classes
#doc-checklist(
  label: [Exposure classes for concrete (SN EN 206, SIA 262)],
  options: (
    (id: "xc1", label: [XC1: dry or permanently wet], checked: false),
    (id: "xc2", label: [XC2: wet, rarely dry], checked: false),
    (id: "xc3", label: [XC3: moderate humidity], checked: false),
    (id: "xc4", label: [XC4: cyclic wet and dry], checked: false),
    (id: "xd1", label: [XD1: moderate humidity (chlorides)], checked: false),
    (id: "xd2", label: [XD2: wet, rarely dry (chlorides)], checked: false),
    (id: "xd3", label: [XD3: cyclic wet and dry (chlorides)], checked: false),
    (id: "xf1", label: [XF1: freeze-thaw, moderate water saturation, without de-icing agent], checked: false),
    (id: "xf2", label: [XF2: freeze-thaw, moderate water saturation, with de-icing agent], checked: false),
    (id: "xf3", label: [XF3: freeze-thaw, high water saturation, without de-icing agent], checked: false),
    (id: "xf4", label: [XF4: freeze-thaw, high water saturation, with de-icing agent], checked: false),
  ),
)
// woodcore:/object concrete-exposure-classes

// woodcore:object text p2
Corrosion protection of the reinforcing steel is ensured by providing sufficient concrete cover in accordance with the current standards. [Protection against chlorides in car parks: chloride-resistant floor finish, anti-corrosion coating of steel column bases and heads …]
// woodcore:/object p2
// woodcore:/shared durability
