#import "/commands.typ": *

// woodcore:object heading title
== Durabilité
// woodcore:/object title
// woodcore:shared durability

// woodcore:object text p1
L'ouvrage doit demander peu d'entretien et être conçu pour une longue durée d'utilisation des éléments ; il doit pouvoir être utilisé conformément aux affectations prévues, des changements d'affectation pouvant exiger des mesures supplémentaires. Les mesures pour garantir la durabilité (SIA 260, ch. 2.3.7) sont : [protection constructive du bois (éviter l'humidification, assurer l'écoulement de l'eau et le séchage), choix des matériaux et traitement, protection contre la corrosion des éléments en acier et des organes d'assemblage, enrobage du béton, protection contre les chlorures et le gel …].
// woodcore:/object p1

// woodcore:object doc-checklist timber-use-classes
#doc-checklist(
  label: [Classes d'emploi du bois (SN EN 335, SIA 265.131)],
  options: (
    (id: "uc-1", label: [Classe d'emploi 1 : à l'intérieur, au sec], checked: false),
    (id: "uc-2", label: [Classe d'emploi 2 : à l'intérieur ou sous abri, non exposé aux intempéries (condensation possible)], checked: false),
    (id: "uc-3-1", label: [Classe d'emploi 3.1 : à l'extérieur, au-dessus du sol, humidification de courte durée], checked: false),
    (id: "uc-3-2", label: [Classe d'emploi 3.2 : à l'extérieur, au-dessus du sol, humidification prolongée], checked: false),
    (id: "uc-4", label: [Classe d'emploi 4 : en contact avec le sol ou l'eau douce], checked: false),
    (id: "uc-5", label: [Classe d'emploi 5 : immergé dans l'eau salée], checked: false),
  ),
)
// woodcore:/object timber-use-classes

// woodcore:object doc-checklist concrete-exposure-classes
#doc-checklist(
  label: [Classes d'exposition du béton (SN EN 206, SIA 262)],
  options: (
    (id: "xc1", label: [XC1 : sec ou constamment humide], checked: false),
    (id: "xc2", label: [XC2 : humide, rarement sec], checked: false),
    (id: "xc3", label: [XC3 : humidité modérée], checked: false),
    (id: "xc4", label: [XC4 : alternance d'humidité et de séchage], checked: false),
    (id: "xd1", label: [XD1 : humidité modérée (chlorures)], checked: false),
    (id: "xd2", label: [XD2 : humide, rarement sec (chlorures)], checked: false),
    (id: "xd3", label: [XD3 : alternance d'humidité et de séchage (chlorures)], checked: false),
    (id: "xf1", label: [XF1 : gel, saturation modérée, sans sel de déneigement], checked: false),
    (id: "xf2", label: [XF2 : gel, saturation modérée, avec sel de déneigement], checked: false),
    (id: "xf3", label: [XF3 : gel, saturation élevée, sans sel de déneigement], checked: false),
    (id: "xf4", label: [XF4 : gel, saturation élevée, avec sel de déneigement], checked: false),
  ),
)
// woodcore:/object concrete-exposure-classes

// woodcore:object text p2
La protection contre la corrosion de l'acier d'armature est assurée par le respect d'un enrobage de béton suffisant, selon les normes en vigueur. [Protection contre les chlorures dans les parkings : revêtement de sol résistant aux chlorures, peinture anticorrosion des pieds et têtes de poteaux en acier …]
// woodcore:/object p2
// woodcore:/shared durability
