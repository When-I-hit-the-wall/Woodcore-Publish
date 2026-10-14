# Open questions, closed

> The points of `docs/open-questions.md` (§14) that were closed or settled, moved there verbatim on 2026-10-10 (issue #31): a whole point closed, or a sub-point struck through under the point it belonged to (named on the line before it). What settled each is in its own text and in `docs/decisions.md`.

## 14 (closed)

- **What the RFEM work does not do yet** -- closed in 0.117: the RFEM import was retired on the engineer's request of 08.10.2026 (docs/decisions.md, «Retrait de RFEM»); the open points as they stood are `archive/rfem/docs/open-questions-rfem.md`.

- **The RFEM import, what it does not do yet** -- closed in 0.117: the RFEM import was retired on the engineer's request of 08.10.2026 (docs/decisions.md, «Retrait de RFEM»); the open points as they stood are `archive/rfem/docs/open-questions-rfem.md`.

- From «The variables tab: the one question for the engineer, and what the tab does not do yet»:
  - ⚠️ ~~**When the reading is paid for.**~~ **Settled (v0.110): he chose (c)**, the PDF carrying it (§13). The tab reads the attachment where the PDF is newer than every source — 0.7 s — and compiles otherwise; what is left of the question is only the price he accepted with it, that every delivered PDF embeds a JSON of the report's values.

- From «The connectors, what is not calculated yet»:
  - ~~**Taking a connector's geometry into a polar moment.**~~ Superseded: since v0.74 a connector and a polar moment read one schema, and since v0.76 a polar moment names no connector at all, so there is nothing to copy.

- From «The schemas module, what it does not do yet»:
  - ~~**Modifying what is drawn.**~~ **Done in v0.73** (§3.3decies, §10quater, §13): the six verbs, the multiple selection, and the two rules the engineer set. What it still does not do is listed below with the rest.

- From «The schemas module, what it does not do yet»:
  - ~~**What consumes a schema.**~~ **Done in v0.74** (§3.3decies, §3.3nonies, §3.3quinquies, §13): both sources name a schema, its markers and its elements, and carry no geometry of their own. The paragraph that stood here described the plan; what landed is in §13, including the one place it read the plan narrowly (a polar moment keeps its `connector`). What it left open is listed next.

- From «The schemas module, what it does not do yet»:
  - ~~**What a schema element's label should carry.**~~ **Settled in v0.75** (§13): the position, its strength class and the section, «T001 C24 100/200», the section being the element's own b and h.
