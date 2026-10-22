// Entry point of the basis of design: assembles the document from the project's config, a title page and the sections structure.json lists.
//
// The lines between the two `woodcore:structure` tags at the foot of this file are written by Woodcore from structure.json -- the order of the sections, how they nest and which of them are printed live there, not here. Everything else in this file is yours.

#import "/000-Typst-Config/config.typ": conf
#import "/000-Typst-Config/commands.typ": *
#import "/000-Typst-Config/title.typ": title-page
#show: conf
// The PDF's own metadata -- the project's name, the author and office, the versions that produced it -- and which revision journal `show-journal` prints: this document's own, and not the report's (docs/domain/journal.md §3.3terdecies).
#show: woodcore-document.with(document: "bp")

// The language of what the ENGINE prints: "de", "fr" or "en" (docs/typst/language.md §4bis). Edit the default here; --input lang=fr forces it for one run. Your own words in this file and in Sections/ are yours to write in the language of the document, and the language Typst itself works in is declared in config.typ.
#set-report-language(sys.inputs.at("lang", default: "de"))

// Detail level, fixed at compile time: typst compile --input level=2 ...
#let default-level = int(sys.inputs.at("level", default: "2"))
#assert(
  default-level in (1, 2, 3),
  message: "invalid --input level=" + str(default-level) + ", expected 1, 2, or 3",
)
#report-level.update(default-level)

// typst compile --input uniform=2 renders EVERY show-* at level 2, ignoring the per-call `level:` overrides written in Sections/.
#let uniform = sys.inputs.at("uniform", default: none)
#if uniform != none {
  let uniform-int = int(uniform)
  assert(
    uniform-int in (1, 2, 3),
    message: "invalid --input uniform=" + str(uniform-int) + ", expected 1, 2, or 3",
  )
  uniform-level.update(uniform-int)
}

// Decimals on every number the engine prints. One knob for the whole document.
#number-digits.update(3)

// --- Title page ---------------------------------------------------------
// The title page is title.typ's, at the top of the project and shared by the three documents: its rows take the project's name, number, client, office and people from the .woodcore file, and the words it prints follow the document's language (config.typ's `doc-lang`). Edit it there, in VS Code -- the rows, the labels, the layout.
#title-page(document: "bp")

#outline()
#pagebreak()

// --- Sections ------------------------------------------------------------
// woodcore:structure -- written by Woodcore from structure.json; what lies between these two lines is replaced
#include "Sections/general.typ"
#include "Sections/purpose-of-basis-of-design.typ"
#include "Sections/scope-and-limits.typ"
#include "Sections/bases.typ"
#include "Sections/project-documents.typ"
#include "Sections/norms.typ"
#include "Sections/use-and-logistics.typ"
#include "Sections/building-description.typ"
#include "Sections/service-life.typ"
// disabled: sustainability-certification (Sections/sustainability-certification.typ)
#include "Sections/transport-dimensions.typ"
#include "Sections/structural-concept.typ"
#include "Sections/load-bearing-system.typ"
#include "Sections/horizontal-stability.typ"
#include "Sections/main-dimensions.typ"
#include "Sections/construction-details.typ"
#include "Sections/prefabrication-and-erection.typ"
#include "Sections/structural-concept-drawings.typ"
// disabled: waterproofing-concept (Sections/waterproofing-concept.typ)
#include "Sections/open-points.typ"
#include "Sections/ground.typ"
#include "Sections/ground-conditions.typ"
#include "Sections/ground-parameters.typ"
#include "Sections/foundation-and-excavation.typ"
#include "Sections/materials.typ"
#include "Sections/concrete.typ"
#include "Sections/reinforcing-steel.typ"
#include "Sections/structural-steel.typ"
#include "Sections/timber.typ"
#include "Sections/moisture-class-and-creep.typ"
// disabled: masonry (Sections/masonry.typ)
#include "Sections/actions.typ"
#include "Sections/permanent-actions.typ"
#include "Sections/self-weight-and-unit-weights.typ"
#include "Sections/superimposed-dead-loads.typ"
// disabled: earth-and-water-pressure (Sections/earth-and-water-pressure.typ)
#include "Sections/variable-actions.typ"
#include "Sections/live-loads.typ"
#include "Sections/snow-load.typ"
#include "Sections/wind-load.typ"
#include "Sections/guardrail-loads.typ"
// disabled: temperature-actions (Sections/temperature-actions.typ)
#include "Sections/accidental-actions.typ"
#include "Sections/earthquake.typ"
// disabled: impact (Sections/impact.typ)
#include "Sections/design-values.typ"
#include "Sections/load-factors.typ"
#include "Sections/reduction-factors.typ"
#include "Sections/structural-safety.typ"
#include "Sections/ultimate-limit-states.typ"
#include "Sections/reliability-differentiation.typ"
#include "Sections/hazard-scenarios.typ"
#include "Sections/ultimate-load-cases.typ"
#include "Sections/omitted-verifications.typ"
#include "Sections/serviceability.typ"
#include "Sections/serviceability-criteria.typ"
#include "Sections/deformation-limits.typ"
#include "Sections/horizontal-displacement-limits.typ"
#include "Sections/vibrations.typ"
#include "Sections/settlements.typ"
#include "Sections/durability.typ"
#include "Sections/serviceability-load-cases.typ"
#include "Sections/analysis-assumptions.typ"
#include "Sections/design-situations.typ"
#include "Sections/structural-model.typ"
#include "Sections/geometrical-deviations.typ"
#include "Sections/construction-states.typ"
#include "Sections/measures-and-controls.typ"
#include "Sections/quality-assurance-and-controls.typ"
#include "Sections/monitoring-and-maintenance.typ"
#include "Sections/accepted-risks.typ"
#include "Sections/fire-protection.typ"
#include "Sections/fire-protection-bases.typ"
#include "Sections/fire-object-description.typ"
#include "Sections/fire-protection-plans.typ"
#include "Sections/fire-resistance-of-elements.typ"
#include "Sections/fire-classification-of-materials.typ"
#include "Sections/building-physics.typ"
#include "Sections/building-physics-bases.typ"
#include "Sections/thermal-and-moisture-protection.typ"
#include "Sections/airtightness.typ"
#include "Sections/ventilation-and-cooling.typ"
#include "Sections/heating.typ"
#include "Sections/noise-protection.typ"
#include "Sections/noise-protection-bases.typ"
#include "Sections/noise-exposure.typ"
#include "Sections/noise-sensitivity.typ"
#include "Sections/sound-insulation-requirements.typ"
#include "Sections/basis-signatures.typ"
#include "Sections/journal.typ"
// woodcore:/structure
