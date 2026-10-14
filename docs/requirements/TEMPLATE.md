---
id: AAAA-MM-JJ-slug
titre: Titre court de la fonctionnalité
status: draft
cree: AAAA-MM-JJ
mis_a_jour: AAAA-MM-JJ
source: transcription dictée | message écrit | fichier <chemin>
docs: [docs/domain/xxx.md, docs/ui/window.md]   # fichiers de référence concernés
---

# <Titre> — Spécification

## 1. Objectif

Ce que l'ingénieur veut obtenir, en deux ou trois phrases, et pourquoi.

## 2. Source

La demande telle qu'elle a été donnée, **mot pour mot**, découpée en points numérotés `T1`, `T2`… (un point = une demande, une remarque ou une idée). Rien n'est reformulé ici.

> **T1** — « … »
>
> **T2** — « … »

## 3. Exigences fonctionnelles

### REQ-001 — <titre>
- **Exigence** : Woodcore doit …
- **Source** : T1
- **Priorité** : doit | devrait | pourrait
- **Critère d'acceptation** : vérifiable par un test ou une observation précise (quoi, où, quelle valeur).

## 4. Exigences d'interface (fenêtre, rapport, site)

### UI-001 — <titre>
- **Exigence** : …
- **Source** : T2
- **Langues** : fr / de / en (toute chaîne visible existe dans les trois)
- **Critère d'acceptation** : …

## 5. Exigences d'architecture

### ARCH-001 — <titre>
- **Exigence** : par ex. « le calcul reste dans `calc/domains/` sans Qt », « une seule source pour … »
- **Source** : T3 ou principe (docs/architecture/principles.md règle n)
- **Critère d'acceptation** : …

## 6. Contraintes

- **CON-001** — contrainte imposée (norme, édition, compatibilité d'un fichier existant, version de schéma, performance…). Source : T4.

## 7. Décisions prises

Ce que l'ingénieur a tranché (dans la source ou en répondant aux questions), avec la raison et le prix accepté. Une décision durable est reportée dans `docs/decisions.md` à la fin.

## 8. Hors périmètre

Ce qui est explicitement exclu de cette spécification.

## 9. Idées non retenues comme exigences

Réflexions, pistes ou exemples de la source qui ne sont **pas** des demandes (T7 : « on pourrait peut-être… » → idée, pas exigence).

## 10. Questions

### Q-001 — <question>
- **Pourquoi elle compte** : ce qui change selon la réponse.
- **Options** : A (recommandée) …, B …
- **Réponse** : _(en attente)_ | réponse de l'ingénieur, date

## 11. Critères d'acceptation

- [ ] REQ-001 — <critère, une ligne>
- [ ] UI-001 — …
- [ ] ARCH-001 — …
- [ ] Documentation : sections de `docs/` mises à jour, entrée `CHANGELOG.md`, page « Nouveautés » fr/de/en, `///` + exemples + traductions pour toute commande Typst.
- [ ] Tests : fichiers `tests/test_*.py` ajoutés ou étendus, et passent.

## 12. Traçabilité

| Source | Élément | Statut |
|---|---|---|
| T1 | REQ-001 | capturé |
| T2 | UI-001 | capturé |
| T5 | — | idée (§9) |
| T6 | Q-001 | ambigu → question |

### Points de la source non résolus

- T6 — ce qui est ambigu et pourquoi ; renvoi à la question.

## 13. Revue d'architecture

_(écrite par `architecture-review`)_ Modules concernés, architecture existante à réutiliser, risques `ARCH-RISK-xxx` (duplication, hardcoding, logique métier dans l'UI, dépendances circulaires, contrats/schémas, i18n, règles de `docs/architecture/principles.md`), approche recommandée, verdict : APPROUVER | APPROUVER AVEC RÉSERVES | REVOIR.

## 14. Plan d'implémentation

Étapes ordonnées, chacune avec les fichiers touchés et les éléments (REQ/UI/ARCH) qu'elle réalise, et les tests qui la prouvent.

1. …

## 15. Vérification

_(écrite par `verify-requirements`, sur preuve dans le code et les tests)_

| Élément | Verdict | Preuve (fichier:ligne, test, sortie) |
|---|---|---|
| REQ-001 | ✅ / ⚠️ / ❌ | … |

## 16. Journal d'avancement

| Date | Statut | Fait / reste |
|---|---|---|
| AAAA-MM-JJ | draft | spécification extraite de la source |
