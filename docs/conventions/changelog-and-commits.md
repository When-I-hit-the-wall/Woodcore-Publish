# Changelog and commit rule

> Where the journal lives and what every commit must carry.
>
> Moved verbatim from CLAUDE.md (§15) on 2026-10-07. The § numbers are kept as stable anchors: `docs/README.md` maps every § to its file.

## 15. Changelog

Moved to **`CHANGELOG.md`**, beside CLAUDE.md (v0.59). It was 179 KB of the 532 KB this document had reached, and this document is read in full every time the project is worked on.

Nothing was dropped: every entry from v0.1 to the present is there, newest first, each naming the sections it changed. What stays here is the part that is still true — §13's settled decisions and §14's open ones — which is what a reference is for; the journal of how each was arrived at is one file away.

👉 A new version adds its entry to `CHANGELOG.md` (the status of the project is its newest entry), updates the `docs/` files whose sections it changed, and `docs/decisions.md` (§13) / `docs/open-questions.md` (§14) where it settles or opens a decision. Until v0.117 a status paragraph also headed CLAUDE.md; those paragraphs are kept, frozen, in `docs/history/status-notes.md`. A change made through the `big-feature` workflow also moves its specification from `docs/requirements/active/` to `docs/requirements/completed/` once verified.

👉 **At every commit** (v0.94, the engineer's rule: «lors d'un commit, il faut toujours log les changements sur le site internet, modifier la documentation des commandes si besoin, build le .exe»): what the commit changes for a user is written, in French, German and English, into the «Nouveautés» page of the version the next installer will carry — `website/content/<lang>/changes/<version>.md`, *Nouveau* · *Ce qui change dans vos rapports* · *À faire* (§12) —, the page created by the first such commit after a release; a command whose surface changed has its `///` block and its French and German in `calc/i18n/commands.json` brought along in the same commit (§10sexies, `tests/test_commands.py`); the installer is built by the post-commit hook when the commit changes `VERSION` (§12); and publishing — `packaging/publish.py` and the push that redeploys the site — waits for the engineer's word.
