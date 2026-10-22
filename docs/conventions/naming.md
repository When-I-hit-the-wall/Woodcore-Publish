# Naming: one thing, one name

> What the code calls each thing the window and the report show, where it has carried more than one name. Written on 19.10.2026 (spec `docs/requirements/active/2026-10-19-base-saine-nettoyage.md`, G8), after the audit found one concept under three names and one name under two concepts.

## The rule

A name says what the thing **is**, in English, the same in a module, a folder, a key of the export and a Typst command. Where history left two names, the table below says which is the thing's own and which is kept only because a file of a project already holds it (a folder name, an export key): those are never renamed, since a project written before would no longer be read.

A **constant that holds a colour** ends in `_COLOUR` (`LABEL_COLOUR`, the ink of a figure's labels), so that it is never read as the word or the label it colours: `LABEL` is, in a domain module, the name of the domain in the report (`snow.LABEL`, read by `registry.py`). British spelling, as the rest of the code (`colour`, `centre`).

## The names

| What it is | Its name in the code | Also met as | Why the other name stays |
|---|---|---|---|
| A detail schema (the «Schémas» tab) | `schema` (`calc/domains/schema.py`, `#schema`, `ids("schema")`) | `details/` (the projects' folder), `schemas.json` (the export) | the folder of every project made since v0.74 |
| A steel check (the «Acier» tabs) | `steel_check` (the source), `steel` (the domain of the export, `steel-domain`) | «Acier» in the window | the export key `steel.json` |
| A polar moment (the «Moments polaires» tab) | `connection` (`calc/domains/connection.py`) | «Moment polaire» in the window; `polar_tab.py`, the tab's module (`woodcore_gui_polar.py` until v0.120) | the export key `connections.json` |
| A connector (the «Connecteurs» tab) | `connector` | «Moyen d'assemblage» in the window | — |
| A member check (the timber checks) | `member_check` (the source), `check` (the domain, `check-domain`, `ids("check-member")`) | `checks.json` | the export key |
| A calculation domain of the «Domaines» tab | `formula_domain` | «Formules» (the tab's name until v0.119), `Formules/` (a project laid out before v0.119) | the folder of a project not yet migrated |
| The ids of one kind | `ids(kind)` | the thirteen `*-ids` until v0.120 | `calc/renamed-commands.json`, which migrates a project's sections |
| One field of a variable | `get(v, field)` | the eight `get-*` until v0.120 | likewise |
