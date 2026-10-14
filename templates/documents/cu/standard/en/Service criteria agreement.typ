// Entry point of the service criteria agreement: assembles the document from the project's config, a title page and the sections structure.json lists.
//
// The lines between the two `woodcore:structure` tags at the foot of this file are written by Woodcore from structure.json -- the order of the sections, how they nest and which of them are printed live there, not here. Everything else in this file is yours.

#import "/config.typ": conf
#import "/commands.typ": *
#import "/title.typ": title-page
#show: conf
// The PDF's own metadata -- the project's name, the author and office, the versions that produced it -- and which revision journal `show-journal` prints: this document's own, and not the report's (docs/domain/journal.md §3.3terdecies).
#show: woodcore-document.with(document: "cu")

// The language of what the ENGINE prints: "de", "fr" or "en" (docs/typst/language.md §4bis). Edit the default here; --input lang=fr forces it for one run. Your own words in this file and in Sections/ are yours to write in the language of the document, and the language Typst itself works in is declared in config.typ.
#set-report-language(sys.inputs.at("lang", default: "en"))

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
#title-page(document: "cu")

#outline()
#pagebreak()

// --- Sections ------------------------------------------------------------
// woodcore:structure -- written by Woodcore from structure.json; what lies between these two lines is replaced
#include "Sections/introduction.typ"
#include "Sections/purpose.typ"
#include "Sections/scope-and-limits.typ"
#include "Sections/project-description.typ"
#include "Sections/project-overview.typ"
#include "Sections/building-description.typ"
#include "Sections/transport-dimensions.typ"
#include "Sections/sustainability-certification.typ"
// disabled: future-extension (Sections/future-extension.typ)
// disabled: civil-protection-shelter (Sections/civil-protection-shelter.typ)
// disabled: ground-conditions (Sections/ground-conditions.typ)
#include "Sections/use-objectives.typ"
#include "Sections/intended-use.typ"
#include "Sections/live-loads.typ"
#include "Sections/superimposed-dead-loads.typ"
#include "Sections/service-life.typ"
#include "Sections/other-actions.typ"
#include "Sections/flexibility-and-alterations.typ"
#include "Sections/drilling-and-openings.typ"
// disabled: prestressing (Sections/prestressing.typ)
#include "Sections/energy-and-building-physics.typ"
#include "Sections/noise-protection-objectives.typ"
#include "Sections/environment-and-third-parties.typ"
#include "Sections/third-party-requirements.typ"
#include "Sections/construction-site.typ"
#include "Sections/neighbouring-buildings.typ"
#include "Sections/utilities.typ"
#include "Sections/contaminated-sites.typ"
#include "Sections/occupational-safety.typ"
#include "Sections/emissions.typ"
#include "Sections/prefabricated-elements.typ"
// disabled: radon (Sections/radon.typ)
#include "Sections/operation-and-maintenance.typ"
#include "Sections/maintenance-obligations.typ"
#include "Sections/maintenance-by-building-part.typ"
#include "Sections/owner-requirements.typ"
#include "Sections/building-requirements.typ"
#include "Sections/construction-stages.typ"
#include "Sections/structural-preferences.typ"
#include "Sections/material-requirements.typ"
#include "Sections/execution-details.typ"
#include "Sections/schedule.typ"
#include "Sections/inspections-and-acceptance.typ"
#include "Sections/structure-requirements.typ"
#include "Sections/deformation-limits.typ"
#include "Sections/settlements.typ"
#include "Sections/vibrations.typ"
#include "Sections/durability.typ"
#include "Sections/timber-appearance-classes.typ"
// disabled: cracking-requirements (Sections/cracking-requirements.typ)
// disabled: waterproofing-classes (Sections/waterproofing-classes.typ)
#include "Sections/finishes-facades-installations.typ"
#include "Sections/construction-tolerances.typ"
#include "Sections/further-requirements.typ"
#include "Sections/protection-objectives-and-risks.typ"
#include "Sections/risk-evaluation.typ"
#include "Sections/earthquake.typ"
#include "Sections/fire-resistance.typ"
// disabled: impact (Sections/impact.typ)
#include "Sections/accepted-risks.typ"
#include "Sections/bases-and-documents.typ"
#include "Sections/project-documents.typ"
#include "Sections/norms.typ"
#include "Sections/agreement-signatures.typ"
// disabled: annexes (Sections/annexes.typ)
// disabled: annex-floor-load-plans (Sections/annex-floor-load-plans.typ)
// disabled: annex-crack-types (Sections/annex-crack-types.typ)
// disabled: annex-waterproofing-plan (Sections/annex-waterproofing-plan.typ)
// disabled: annex-pages (Sections/annex-pages.typ)
#include "Sections/journal.typ"
// woodcore:/structure
