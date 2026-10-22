// Every command of the report, in one import: each .typ file of the report starts with this one line (docs/typst/api-conventions.md §10bis).
//
// The engine is the copy Woodcore writes into _woodcore/ beside the export (calc/project.py, sync_engine) -- never edited here.

#import "/000-Woodcore/lib/calc-engine.typ": *
#import "/000-Woodcore/lib/formula.typ": *
