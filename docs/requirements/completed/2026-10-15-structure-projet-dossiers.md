---
id: 2026-10-15-structure-projet-dossiers
titre: Structure d'un projet — dossiers générés à la création (issue #64)
status: completed
cree: 2026-10-15
mis_a_jour: 2026-10-16
source: message écrit (issue GitHub #64, dictée de l'ingénieur du 2026-10-15, ses réponses aux questions de /issue et de big-feature), modèle C:\Users\florian.lamprecht\Downloads\Test
docs: [docs/architecture/layout.md, docs/architecture/principles.md, docs/ui/window.md, docs/typst/api-conventions.md, docs/domain/position-plans.md, docs/domain/annexes.md, docs/domain/scripts.md]
---

# Structure d'un projet — Spécification

## 1. Objectif

Rendre l'arborescence d'un projet lisible au premier coup d'œil : ce qui configure les documents d'un côté (`000-Typst-Config/`), ce qui appartient à Woodcore et que l'ingénieur n'a pas besoin d'ouvrir de l'autre (`000-Woodcore/`), puis les trois documents à rendre (`100-`, `200-`, `300-`), puis un dossier par onglet spécialisé — un `.typ` par domaine de calcul, les documents importés et les exports pour les onglets de dessin — et `Domains/` pour les domaines que l'ingénieur crée lui-même. Les projets existants passent à cette structure à leur ouverture. Les calculs dépliés par onglet viennent ensuite, chacun dans une issue à part.

## 2. Source

Dictée de l'ingénieur (issue #64), mot pour mot :

> **T1** — « Je souhaite modifier la structure des fichiers, l'arborescence des fichiers qui est générée automatiquement lors d'un nouveau projet. »
>
> **T2** — « L'idée est de clairement séparer les fichiers de configuration types, comme les templates, les configs et la page de titre. »
>
> **T3** — « Séparer également tout ce qui concerne WoodCore, tout ce qui, ce qui concerne WoodCore et que l'utilisateur n'a pas forcément besoin d'aller regarder. »
>
> **T4** — « Ensuite, il y a les trois dossiers pour les trois documents à rendre, convention d'utilisation, base de projet et rapport de statique. »
>
> **T5** — « Et ensuite, il y a euh, un dossier par type de domaine. Donc, euh, dans le dossier Snow, il y aura dedans à chaque fois un fichier typst par domaine de neige. »
>
> **T6** — « Et il y a ensuite, il doit y avoir un, également un dossier euh, domaine qui contient en fait tous les domaines euh, où il faut trouver un autre nom, mais euh, personal domains ou trouve un nom pour ce dossier. Et dedans, il y a tous les domaines qui sont créés manuellement par l'utilisateur et qui ne proviennent pas d'onglets spécialisés. »
>
> **T7** — « Voici le lien où j'ai restructuré l'arborescence: C:\Users\florian.lamprecht\Downloads\Test »

Réponses de l'ingénieur aux questions de `/issue` (2026-10-15) :

> **T8** — « Domains (l'onglet woodcore Formules et également renommé "Domains") »
>
> **T9** — « Tout en anglais, fixe »
>
> **T10** — « Tout onglet qui produit un domaine »
>
> **T11** — « Migrés à l'ouverture »

Réponses aux questions de cette spec (2026-10-15), voir §10 :

> **T12** (Q-008) — « les dossiers des onglets qui n'ont pas de domaines de calcul possède deux choses: (1) les imports, (2) les exports. Par exemple, pour Plan de positions, il y a un dossier dans "Plan-positions" qui s'appelle "Imported Plans". À l'intérieur, il y a tous les documents ajoutés. Si j'écrase un document par un document du même nom, cela est également mis à jour dans woodcore. Les fichiers exports sont, par exemple, des svg (utilisés pour faire les figures) ou des plans d'exports. Il faut également un dossier "Appendix" Contient les annexes »

Le modèle T7 (arborescence relevée le 2026-10-15) :

```
Test/
├── Test.woodcore, .vscode/settings.json
├── 000-Typst-Config/      commands.typ, config.typ, references.bib, title.typ, Template/ (form.json, template.typ)
├── 000-Woodcore/          calc/, lib/, data/, stamps/, docs/, VERSION (le contenu de _woodcore/), Woodcore-Datei/, _Archiv/
├── 100-Convention d'utilisation/   Convention d'utilisation.typ, structure.json, sync.json, Sections/
├── 200-Base de projet/             Base de projet.typ, structure.json, sync.json, Sections/
├── 300-Rapport de statique/        Statischer Rapport.typ, Sections/
├── Formules/              test_traction.typ, unfold.json
├── Images/
├── Plan-fire/, Plan-position/, Snow/, Wind/   (vides)
```

## 3. Exigences fonctionnelles

La structure cible, qui découle des réponses (D-01 à D-27) — **elle remplace les noms de dossiers donnés dans les REQ ci-dessous là où ils diffèrent** (Q-021 à Q-026 sont venues après) :

```
<Projet>/
├── <Projet>.woodcore, .vscode/settings.json
├── 000-Typst-Config/        config.typ, commands.typ, title.typ, references.bib, Template/
├── 000-Woodcore/            lib/, calc/, data/, stamps/, docs/, out/, VERSION, sources/, archives/
├── 100-Service criteria agreement/   <entrée>.typ, structure.json, sync.json, Sections/
├── 200-Basis of design/              idem
├── 300-Statical report/              Statischer Rapport.typ, Sections/
├── Domains/                 <id>.typ (domaines manuels), archives/
├── Images/
├── Positions/               positions.json (la source), Positions.xlsx (écrit à chaque changement, jamais lu)
├── Permanent-loads/         <id>.typ par composition (+ Exports/Figures/)
├── Variable-loads/          Snow/, Wind/   (<id>.typ par domaine)
├── Plans/                   Position-plan/, Fire-plan/   (chacun : Imported Plans/, Exports/ [feuilles], Exports/Figures/)
├── Statics/, Details/       Exports/Figures/
├── Connectors/, Connections/   <id>.typ par domaine (+ Exports/Figures/)
├── Timber-checks/           Tension/, Compression/, Bending/, Shear/, Torsion/, Buckling/, Lateral-torsional/, Deformation/, Vibration/   (<id>.typ par vérification, stub puis déplié)
├── Steel-checks/            Class/, Tension/, Compression/, Bending/, Shear/, Buckling/, Lateral-torsional/, Interaction/, Bolts/, Welds/, Splice/
├── Scripts/                 <id>.py et <id>.typ par script
└── Appendix/                les PDF des annexes, Exports/ (extraits)
```

Correspondance avec les noms des REQ : `Snow/` → `Variable-loads/Snow/`, `Wind/` → `Variable-loads/Wind/`, `Dead-load/` → `Permanent-loads/`, `Checks/<id>.typ` → `Timber-checks/<Genre>/<id>.typ`, `Steel/` → `Steel-checks/<Genre>/`, `Plan-position/` → `Plans/Position-plan/`, `Plan-fire/` → `Plans/Fire-plan/`, `<Dossier>/Exports/` (figures) → `<Dossier>/Exports/Figures/`. **Lot 1** : REQ-001 à 006, 010 à 016, UI-001, UI-002, ARCH-001, 002, 004 ; **lot 2** : REQ-007, 008, 009, ARCH-003 (D-20).

### REQ-001 — Configuration Typst à part
- **Exigence** : Woodcore doit placer `config.typ`, `commands.typ`, `title.typ`, `references.bib` et `Template/` dans `000-Typst-Config/`, et non plus à la racine du projet ; chaque entrée et chaque section importe `"/000-Typst-Config/commands.typ"` (resp. `config.typ`, `title.typ`).
- **Source** : T2, T7
- **Priorité** : doit
- **Critère d'acceptation** : un projet créé par `woodcore-cli new` et par la fenêtre a ces cinq éléments dans `000-Typst-Config/` et aucun à la racine ; ses trois documents compilent.

### REQ-002 — Woodcore à part
- **Exigence** : Woodcore doit placer dans `000-Woodcore/` le contenu de l'actuel `_woodcore/` (`lib/`, `calc/`, `data/`, `stamps/`, `docs/`, `out/`, `VERSION`), les sources dessinées dans `000-Woodcore/sources/` (actuel `Woodcore-Datei/`) et les archives dans `000-Woodcore/archives/` (actuel `_Archiv/`).
- **Source** : T3, T7, D-08
- **Priorité** : doit
- **Critère d'acceptation** : après création et export, la racine ne contient ni `_woodcore/`, ni `Woodcore-Datei/`, ni `_Archiv/` ; `000-Woodcore/` contient `sources/` et `archives/` ; l'export ne vide jamais `sources/` ni `archives/` en reconstruisant ce qu'il génère.

### REQ-003 — Trois dossiers de documents numérotés
- **Exigence** : Woodcore doit placer les documents dans `100-Service criteria agreement/`, `200-Basis of design/`, `300-Statical report/`, quelle que soit la langue du projet.
- **Source** : T4, D-07
- **Priorité** : doit
- **Critère d'acceptation** : un projet neuf en de, fr et en a ces trois dossiers.

### REQ-004 — Un dossier par onglet de calcul, un `.typ` par domaine
- **Exigence** : Woodcore doit écrire, à la création d'un domaine dans un onglet de calcul, un fichier `<Dossier>/<id>.typ` qui imprime ce domaine par sa commande actuelle, que l'ingénieur complète et qu'une section inclut par `#include "/<Dossier>/<id>.typ"`. Onglets et dossiers : Neige → `Snow/` (`#show-calc("snow-load", id)`), Vent → `Wind/` (`#show-calc("wind-load", id)`), Charges permanentes → `Dead-load/` (`#show-calc("dead-load", id)`), Connecteurs → `Connectors/` (`#show-connector`), Moment polaire → `Connections/` (`#show-polar-moment`), Vérifications bois → `Checks/` (`#show-check-member`), Acier → `Steel/` (`#show-check-steel`). Le fichier est à l'ingénieur une fois écrit : Woodcore ne le réécrit pas ; renommer, dupliquer, archiver et restaurer le domaine suivent son fichier, comme dans l'onglet Domains (`formula_domain.py`).
- **Source** : T5, T10, D-03, D-05
- **Priorité** : doit
- **Critère d'acceptation** : créer le domaine de neige `neige` écrit `Snow/neige.typ` ; une section qui l'inclut compile et imprime le domaine ; l'archiver le déplace dans `Snow/archives/`.

### REQ-005 — `Domains/` pour les domaines personnels
- **Exigence** : Woodcore doit écrire les domaines créés à la main (aujourd'hui `Formules/<id>.typ`) dans `Domains/<id>.typ`, avec `Domains/archives/` ; `#include "/Domains/<id>.typ"` les imprime.
- **Source** : T6, T8, D-01
- **Priorité** : doit
- **Critère d'acceptation** : un nouveau domaine de l'onglet est écrit dans `Domains/` ; `lib/timber.typ` et `formula_domain.include_call` écrivent `/Domains/` ; aucun `"/Formules/"` ne reste dans `calc/` ni `lib/` hors migration.

### REQ-006 — Vérifications dépliées dans `Checks/`
- **Exigence** : une vérification de barre dépliée (aujourd'hui `Formules/<id>.typ` et `Formules/unfold.json`, issue #62) doit être écrite dans `Checks/<id>.typ`, son index `unfold.json` dans `Checks/`.
- **Source** : D-06
- **Priorité** : doit
- **Critère d'acceptation** : l'export d'une vérification dépliée écrit `Checks/<id>.typ` ; la reprise ligne à ligne (unfold) fonctionne depuis `Checks/`.

### REQ-007 — Onglets de dessin : documents importés
- **Exigence** : Woodcore doit copier un document importé dans le plan de positions dans `Plan-position/Imported Plans/` (resp. `Plan-fire/Imported Plans/` pour le plan incendie), sous son nom, et le relire (pages, calques, SHA-256 : `plan_documents.refresh`) au prochain affichage de l'onglet ou à l'export, s'il a été remplacé par un fichier du même nom.
- **Source** : T12, D-09
- **Priorité** : doit
- **Critère d'acceptation** : importer `03_Pavillon.pdf` le copie dans `Plan-position/Imported Plans/` et la fiche du document nomme cette copie ; remplacer ce fichier par un autre du même nom puis rouvrir l'onglet met à jour les pages et le SHA-256.

### REQ-008 — Onglets : exports dans le dossier de l'onglet, seul exemplaire
- **Exigence** : l'export doit écrire les figures d'un onglet (SVG, fond de plan réduit) et ses feuilles d'export dans `<Dossier>/Exports/` (`Plan-position/`, `Plan-fire/`, `Statics/`, `Details/`, `Connectors/`, `Connections/`, `Dead-load/`…), et le moteur doit les y lire ; `000-Woodcore/data/` ne garde que le JSON. Les feuilles d'export (aujourd'hui `Plans/<feuille>.typ`) vont dans `Plan-position/Exports/` ou `Plan-fire/Exports/` selon leur genre.
- **Source** : T12, D-06, D-10
- **Priorité** : doit
- **Critère d'acceptation** : après export, aucun `.svg` ni fond de plan sous `000-Woodcore/data/` ; les figures sont dans les `Exports/` ; les documents compilent et les figures s'impriment comme avant.

### REQ-009 — `Appendix/` pour les PDF des annexes
- **Exigence** : Woodcore doit copier un PDF ajouté comme annexe dans `Appendix/` (aujourd'hui `Woodcore-Datei/annexes/sources/<id>.pdf`) ; ses fiches et extraits restent dans `000-Woodcore/sources/annexes/` ; un PDF remplacé par un fichier du même nom est relu comme un document importé (REQ-007).
- **Source** : T12, D-11
- **Priorité** : doit
- **Critère d'acceptation** : ajouter une annexe écrit son PDF dans `Appendix/` ; `#show-annexes` l'imprime ; le remplacer met à jour la fiche.

### REQ-010 — Scripts : `.py` et `.typ` par script
- **Exigence** : Woodcore doit placer un script dans `Scripts/<id>.py` (aujourd'hui `Woodcore-Datei/scripts/<id>.py`) et écrire à sa création `Scripts/<id>.typ`, qui imprime ses valeurs (commande d'impression existante d'un domaine `("script", id)`).
- **Source** : D-12
- **Priorité** : doit
- **Critère d'acceptation** : créer un script écrit les deux fichiers ; l'export exécute `Scripts/<id>.py` ; `#include "/Scripts/<id>.typ"` compile.

### REQ-011 — Tous les dossiers à la création
- **Exigence** : `woodcore-cli new` et la fenêtre doivent créer tous les dossiers de la structure cible, vides compris (avec `Imported Plans/` et `Exports/` des onglets de dessin).
- **Source** : D-04
- **Priorité** : doit
- **Critère d'acceptation** : un projet neuf contient chaque dossier de la structure cible (§3).

### REQ-012 — Migration à l'ouverture
- **Exigence** : à l'ouverture d'un projet à l'ancienne structure (trois documents), Woodcore doit proposer de le migrer ; avec l'accord de l'ingénieur : copie de l'état avant dans un espace de migration, déplacements, réécriture de chaque `#import`/`#include`/`image()`/`read()` qui nomme un chemin déplacé (`calc/typst_paths.py`), réécriture du `.woodcore` et de `.vscode/settings.json`, copie des documents importés (aujourd'hui référencés là où l'ingénieur les garde) dans `Imported Plans/`, écriture d'un `.typ` par domaine existant (REQ-004, REQ-010), puis compilation et comparaison des PDF avant/après (`project_migrate.compare_pdf`) et retour arrière possible (`rollback`) — la migration de v0.111 étendue. Refusée, le projet s'ouvre tel quel. Un projet « rapport seul » passe d'abord par la migration existante.
- **Source** : T11, D-02
- **Priorité** : doit
- **Critère d'acceptation** : une copie de `tests/projet-exemple` migrée par `woodcore-cli migrate` compile ses trois documents avec un PDF identique au texte près des dates ; `rollback` remet l'ancienne structure octet pour octet.

### REQ-013 — Noms fixes en anglais
- **Exigence** : tous les dossiers que Woodcore crée portent les noms anglais de la structure cible, les mêmes dans tous les projets, quelle que soit la langue du projet.
- **Source** : T9, D-02
- **Priorité** : doit
- **Critère d'acceptation** : un projet créé en de, en fr et en en a les mêmes noms de dossiers.

### REQ-014 — `Positions/`
- **Exigence** : la source des positions (`positions.json`, aujourd'hui dans `Woodcore-Datei/`) est dans `Positions/` ; à chaque changement des positions, Woodcore y écrit `Positions.xlsx`, qu'il ne relit jamais.
- **Source** : Q-024, D-24
- **Priorité** : doit
- **Critère d'acceptation** : enregistrer une position dans l'onglet Positions réécrit `Positions/Positions.xlsx` ; supprimer ce fichier ne change rien à l'export.

### REQ-015 — Un dossier par genre de vérification
- **Exigence** : une vérification bois va dans `Timber-checks/<Genre>/<id>.typ`, une vérification acier dans `Steel-checks/<Genre>/<id>.typ`, le genre (`member_check.KINDS`, `steel_check.KINDS`) fixant le dossier ; changer le genre déplace le fichier. Le stub écrit à la création est remplacé par le calcul déplié au dépliage s'il est resté tel que Woodcore l'a écrit (empreinte enregistrée), sinon un conflit est dit ; un `.typ` ne s'inclut jamais lui-même.
- **Source** : Q-014, Q-021, Q-022, D-16, D-21, D-22
- **Priorité** : doit
- **Critère d'acceptation** : une vérification de traction `ZT-01` crée `Timber-checks/Tension/ZT-01.typ` ; son dépliage remplace le stub inchangé ; un stub modifié donne un conflit et n'est pas écrasé ; le document compile.

### REQ-016 — Onglet Domaines groupé par genre
- **Exigence** : l'onglet Domaines liste, en groupes, les domaines manuels (« Domaines ») et les domaines dépliés des autres dossiers, un groupe par type (« Neige », « Vent », « Traction », « Compression »…), sans groupe général des vérifications ; l'édition ligne à ligne (#62) reste possible dans chaque groupe. Les stubs (non dépliés) n'y figurent pas.
- **Source** : Q-019, D-19
- **Priorité** : doit
- **Critère d'acceptation** : avec un domaine manuel et une vérification de traction dépliée, l'onglet montre deux groupes « Domaines » et « Traction » (fr), les noms traduits en de/en.

## 4. Exigences d'interface

### UI-001 — L'onglet « Formules » devient « Domaines »
- **Exigence** : l'onglet « Formules » est renommé : « Domaines » (fr), « Domänen » (de), « Domains » (en), clé `tab_formula` de `calc/i18n/strings.json` ; l'aide et `docs/ui/` suivent.
- **Source** : T8, D-13
- **Langues** : fr / de / en
- **Critère d'acceptation** : la navigation affiche le nouveau nom dans les trois langues.

### UI-002 — Dialogue de migration
- **Exigence** : à l'ouverture d'un projet à l'ancienne structure, la fenêtre dit ce qui va bouger et demande l'accord (Migrer / Plus tard) ; le résultat (réussite, retour arrière) est dit.
- **Source** : T11
- **Langues** : fr / de / en
- **Critère d'acceptation** : test hors écran : un projet ancien ouvert affiche le dialogue ; « Plus tard » laisse le projet intact.

## 5. Exigences d'architecture

### ARCH-001 — Une seule source pour la structure
- **Exigence** : tous les noms de dossiers et de fichiers de la structure sont lus de `calc/project.py` (`Project`, `layout`) et de `calc/documents.py` ; aucune chaîne `"Formules"`, `"_woodcore"`, `"Woodcore-Datei"`, `"Template"`, `"Plans"`, `"/commands.typ"` en dur ailleurs (relevés : `sheets.py:29,36`, `structure.py:480`, `structure_preview.py:166,240`, `structure_tab.py:351`, `forms.py:46,294`, `templates.py:141`, `project_template.py:284`, `documents.py:43`, `member_check.py:414-430`, `lib/timber.typ:1563`).
- **Source** : principe 1, CLAUDE.md « No hardcoding » — inféré
- **Critère d'acceptation** : un test grep sur `calc/` et `lib/` ne trouve ces littéraux qu'aux définitions et dans la migration.

### ARCH-002 — Le `.woodcore` déclare la nouvelle structure
- **Exigence** : la nouvelle structure se reconnaît au `.woodcore` (nouvelles clés `layout`), validées par `schemas/woodcore-project.schema.json` ; un projet qui ne les déclare pas est lu comme avant jusqu'à sa migration (`Project.has_modes` étendu).
- **Source** : principe 8, T11 — inféré
- **Critère d'acceptation** : `tests/test_project.py` couvre l'ancienne et la nouvelle structure ; le schéma liste les nouvelles clés.

### ARCH-003 — Le moteur trouve l'export et les figures
- **Exigence** : le moteur copié dans `000-Woodcore/lib/` lit le JSON par `../data/` comme aujourd'hui, et les figures par le chemin que l'export écrit dans le JSON (depuis la racine Typst) ; une seule fonction du moteur résout ce chemin.
- **Source** : REQ-008 — inféré (`lib/calc-engine.typ:1178-3602`, lectures `"../data/" + file`)
- **Critère d'acceptation** : les trois documents du projet exemple compilent après migration ; un grep de `lib/` ne trouve plus `"../data/" + ` pour une figure hors de cette fonction.

### ARCH-004 — Un modèle commun pour « un `.typ` par domaine »
- **Exigence** : écrire, renommer, archiver et restaurer le `.typ` d'un domaine d'onglet spécialisé passe par un module Qt-free commun, tiré de `calc/domains/formula_domain.py`, et non par une copie par onglet.
- **Source** : principe 1, principe 16 (« work alike ») — inféré
- **Critère d'acceptation** : un seul module écrit les `.typ` de domaine ; les onglets l'appellent.

## 6. Contraintes

- **CON-001** — Un projet migré imprime les mêmes PDF qu'avant (au texte près des dates). Source : T11, inféré.
- **CON-002** — Les fichiers de l'ingénieur ne sont jamais réécrits sans son accord ; seule la migration acceptée réécrit ses lignes `#import`/`#include`. Un `.typ` de domaine, une fois écrit, est à lui. Source : CLAUDE.md.
- **CON-003** — Un projet « rapport seul » reste lisible et migrable. Source : inféré (`Project.has_modes`).
- **CON-004** — Les projets de l'ingénieur (`../Musterprojekt/`…) ne sont pas touchés ; `tests/projet-exemple/`, `templates/projet/`, `templates/documents/` sont restructurés dans le dépôt. Source : CLAUDE.md.
- **CON-005** — Documentation : `docs/architecture/layout.md` §11, `docs/typst/api-conventions.md` §10bis, `docs/domain/*` des onglets touchés, `docs/ui/`, `docs/decisions.md` §13, `CHANGELOG.md`, « Nouveautés » de/fr/en. Source : CLAUDE.md.
- **CON-006** — OneDrive : déplacer des centaines de fichiers doit réessayer un renommage refusé (`project_migrate._retrying`). Source : inféré.

## 7. Décisions prises

- **D-01** — Domaines personnels dans `Domains/` (T8).
- **D-02** — Projets existants migrés à l'ouverture, avec accord (T11).
- **D-03** — Tout onglet spécialisé qui produit un domaine reçoit son dossier à la racine (T10, Q-002 : toutes les familles cochées).
- **D-04** — Tous les dossiers sont créés à la création du projet (Q-003).
- **D-05** — Le calcul déplié complet est le but (Q-001) ; **cette spec** livre la structure et un `.typ` par domaine qui contient l'appel d'impression ; chaque onglet de calcul reçoit son calcul déplié dans une issue à part (Q-009).
- **D-06** — Feuilles d'export dans `Plan-position/` ou `Plan-fire/` selon leur genre ; vérifications dépliées dans `Checks/` (Q-004).
- **D-07** — Dossiers de documents : `100-Service criteria agreement`, `200-Basis of design`, `300-Statical report` (Q-005).
- **D-08** — Dans `000-Woodcore/` : `sources/` et `archives/` (Q-006).
- **D-09** — Un document importé est copié dans `<Onglet de dessin>/Imported Plans/` et relu s'il est remplacé par un fichier du même nom, au prochain affichage de l'onglet ou à l'export (Q-010, T12).
- **D-10** — Les exports (SVG, feuilles) sont le seul exemplaire, dans `<Dossier>/Exports/`, lus par Typst ; `data/` ne garde que le JSON (Q-011).
- **D-11** — `Appendix/` remplace le dossier « Annexes » et ne contient que les PDF des annexes ; fiches et extraits dans `000-Woodcore/sources/annexes/` (Q-012).
- **D-12** — `Scripts/` contient `<id>.py` et `<id>.typ` (Q-013).
- **D-13** — L'onglet est traduit : Domaines / Domänen / Domains (Q-007).
- **D-14** — Tous les noms de dossiers sont fixes et en anglais (T9).
- **D-15** — Les onglets de dessin (plans, incendie, modèles statiques, détails) n'ont pas de `.typ` par objet : leur dossier contient leurs imports et leurs exports (T12).
- **D-16** — Stub et calcul déplié partagent un fichier : le dépliage remplace le stub resté tel quel (empreinte), sinon conflit (Q-014). Le même mécanisme servira aux dépliés futurs (D-05).
- **D-17** — Les figures générées vont dans `Exports/Figures/`, dossier entièrement géré par Woodcore ; les feuilles restent à la racine d'`Exports/` ; le nettoyage ne supprime que ce que l'export a écrit (manifeste) (Q-015, ARCH-RISK-C01).
- **D-18** — Un import qui porte le nom d'un document déjà importé mais d'autre contenu remplace celui-ci après confirmation, et les plans dessinés dessus le suivent (Q-016).
- **D-19** — Les extraits d'annexes vont dans `Appendix/Exports/` (Q-017). L'onglet Domaines groupe par type, sans dossier général de vérifications (Q-019).
- **D-20** — Une clé `layout.config` ("000-Typst-Config") et `schema_version` 1.1 du `.woodcore` ; les dossiers de domaines sont une table fixe de Woodcore, absente du fichier (Q-018). Livraison en deux lots d'une même spec (Q-020).
- **D-21** — Vérifications bois rangées par genre sous `Timber-checks/` (Q-021) ; acier de même sous `Steel-checks/` (Q-022).
- **D-22** — Parents : `Permanent-loads/` (sans sous-dossier, Q-023), `Variable-loads/` (Snow, Wind), `Plans/` (Position-plan, Fire-plan), `Positions/` (Q-021 texte libre, Q-026 noms longs).
- **D-23** — Seuls les onglets existants ont un dossier ; `Earthquake/` viendra avec son onglet (Q-025).
- **D-24** — `Positions/` contient `positions.json`, la source, et `Positions.xlsx` écrit à chaque changement, jamais lu (Q-024).

## 8. Hors périmètre

- Le calcul déplié (`#var`/`#eq`) de la neige, du vent, des charges permanentes, des connecteurs, du moment polaire et de l'acier : une issue par onglet, après cette spec (D-05).
- Les dossiers propres au bureau (`01_Pläne/`, classeurs Excel) : Woodcore ne les crée ni ne les déplace (la migration copie dans `Imported Plans/` les documents importés, sans toucher l'original).
- Un observateur de fichiers en direct (Q-010 option B, non retenue).

## 9. Idées non retenues comme exigences

_(aucune)_

## 10. Questions

### Q-001 — Contenu de `Snow/<id>.typ`
- **Options** : A appel d'impression ; B calcul déplié complet.
- **Réponse** : B, « Calcul déplié complet » (2026-10-15) — découpé par Q-009.

### Q-002 — Dossiers de domaines
- **Réponse** : toutes les familles : Snow, Wind, Dead-load ; Plan-position, Plan-fire ; Statics, Details, Connectors, Connections ; Checks, Steel, Scripts, Annexes (2026-10-15). « Annexes » devient `Appendix/` (Q-012).

### Q-003 — Moment de création des dossiers
- **Réponse** : « Tous à la création » (2026-10-15).

### Q-004 — Feuilles d'export et vérifications dépliées
- **Réponse** : « Selon l'onglet d'origine » (2026-10-15).

### Q-005 — Noms des dossiers 100/200/300
- **Réponse** : « Noms anglais actuels » (2026-10-15).

### Q-006 — Noms dans `000-Woodcore/`
- **Réponse** : « En anglais : sources/, archives/ » (2026-10-15).

### Q-007 — Nom de l'onglet par langue
- **Réponse** : « Traduit » (2026-10-15).

### Q-008 — `.typ` des onglets qui ne calculent pas
- **Réponse** : T12 (2026-10-15).

### Q-009 — Découpage
- **Réponse** : « Structure d'abord, dépliés ensuite » (2026-10-15).

### Q-010 — Documents importés
- **Réponse** : « Copiés à l'import, relus si écrasés » (2026-10-15).

### Q-011 — Exports
- **Réponse** : « Seul exemplaire, lu par Typst » (2026-10-15).

### Q-012 — Appendix
- **Réponse** : « Les PDF des annexes » (2026-10-15).

### Q-013 — Scripts
- **Réponse** : « Les .py et un .typ par script » (2026-10-15).

### Q-014 à Q-026 — questions nées de la revue d'architecture (2026-10-15)
- **Q-014** stub/déplié : « Bascule stub → déplié ».
- **Q-015** Exports : « Figures dans Exports/Figures/ ».
- **Q-016** collision à l'import : « Remplace après confirmation ».
- **Q-017** extraits d'annexes : « Appendix/Exports/ ».
- **Q-018** `.woodcore` : « Une clé config + schéma 1.1 ».
- **Q-019** onglet Domaines : « oui. Il y a un groupe "Domaines", un groupe "Neige", un groupe "Vent", un groupe "Traction", un groupe "Compression", etc... (i.e. pas de dossier check général) ».
- **Q-020** livraison : « Deux lots, une seule spec ».
- **Q-021** dossiers par genre : « oui, mais sous un parent. Modifie la structure du reste également pour les charges: il y a le parent "Charges permanentes" (en anglais) qui contient le poids propre et la surcharge et "Charge variables" qui contient la neige, le vent, le séisme, etc.... Il y a le parent "Plans" qui contient le plan de position, le plan de feu, il y a le dossier "Positions" qui contient l'excel Positions.xlsx ».
- **Q-022** acier : « Comme le bois ».
- **Q-023** charges permanentes : « Permanent-loads/ sans sous-dossier ».
- **Q-024** positions : « positions.json est la source et se trouve également dans ce dossier. À chaque changement export un Positions.xlsx dans ce dossier, jamais lu ».
- **Q-025** séisme : « Seulement les onglets existants ».
- **Q-026** noms : « Longs et explicites ».

## 11. Critères d'acceptation

- [x] REQ-001 — config, commands, title, references.bib, Template/ dans `000-Typst-Config/`, imports à jour
- [x] REQ-002 — `000-Woodcore/` avec `sources/` et `archives/`
- [x] REQ-003 — dossiers `100-`, `200-`, `300-` en anglais
- [x] REQ-004 — un `.typ` par domaine des sept onglets de calcul, inclus et compilé, archivé avec son domaine
- [x] REQ-005 — `Domains/` remplace `Formules/`
- [x] REQ-006 — vérifications dépliées dans `Checks/`
- [x] REQ-007 — documents importés copiés dans `Imported Plans/`, relus si remplacés
- [x] REQ-008 — figures et feuilles dans `<Dossier>/Exports/`, seul exemplaire
- [x] REQ-009 — PDF des annexes dans `Appendix/`
- [x] REQ-010 — `Scripts/<id>.py` et `<id>.typ`
- [x] REQ-011 — tous les dossiers créés à la création
- [x] REQ-012 — migration à l'ouverture, PDF identiques, retour arrière
- [x] REQ-013 — mêmes noms dans les trois langues
- [x] REQ-014 — `Positions/positions.json` et `Positions.xlsx` écrit à chaque changement
- [x] REQ-015 — vérifications par genre, stub → déplié par empreinte, conflit sinon
- [x] REQ-016 — onglet Domaines groupé par type
- [x] UI-001 — onglet Domaines / Domänen / Domains
- [x] UI-002 — dialogue de migration
- [x] ARCH-001 — aucun nom de structure en dur hors définitions
- [x] ARCH-002 — nouvelles clés `layout` au schéma, ancienne structure lue
- [x] ARCH-003 — une fonction du moteur résout le chemin d'une figure
- [x] ARCH-004 — un module commun écrit les `.typ` de domaine
- [x] Documentation : layout.md §11, api-conventions.md §10bis, domain/*, ui/, decisions.md, CHANGELOG, Nouveautés de/fr/en
- [x] Tests : test_project, test_documents, test_project_migrate, test_formula_domain, tests des onglets touchés, suite complète verte

## 12. Traçabilité

| Source | Élément | Statut |
|---|---|---|
| T1 | §1, REQ-011 | capturé |
| T2 | REQ-001 | capturé |
| T3 | REQ-002, ARCH-003 | capturé |
| T4 | REQ-003 | capturé |
| T5 | REQ-004, D-05 | capturé |
| T6 | REQ-005 | capturé |
| T7 | REQ-001…003, structure cible | capturé |
| T8 | D-01, REQ-005, UI-001 | décision |
| T9 | D-14, REQ-013 | décision |
| T10 | D-03, REQ-004 | décision |
| T11 | D-02, REQ-012, UI-002 | décision |
| T12 | D-09, D-10, D-11, D-15, REQ-007, REQ-008, REQ-009 | décision |

### Points de la source non résolus

_(aucun)_

## 13. Revue d'architecture

Trois revues `architecture-reviewer` en parallèle (2026-10-15) : A structure/création/migration, B un `.typ` par domaine, C imports/exports/figures. Verdict de chacune : **REVOIR** ; les points bloquants ont été tranchés par l'ingénieur (Q-014 à Q-026) ou ont un correctif repris au plan. Verdict consolidé après réponses : **APPROUVER AVEC RÉSERVES** — les réserves sont les correctifs ci-dessous, chacun une étape du plan.

### Modules concernés (principaux)
- `calc/project.py:61-110,312-440` (layout, constantes de noms, chemins) ; `calc/documents.py:28-46,90-160` (dossiers des documents, `commands_import`, `import_line`) ; `schemas/woodcore-project.schema.json:13-14` (`schema_version` const 1.0).
- `calc/project_template.py:278-327`, `calc/templates.py:128-141`, `templates/projet/`, `templates/documents/` (création) ; `calc/project_migrate.py:468-600,804,835-1345` (migration v0.111) ; `calc/tools/migrate_dialog.py`, `woodcore_gui.py:1086-1092` (proposée seulement si `not has_modes`) ; `calc/typst_paths.py:464,501` (réécrit déjà import, include, image, read, json, `project:`).
- `calc/domains/formula_domain.py` (cycle complet d'un domaine `.typ`) ; `calc/domains/unfold.py:191-342`, `unfold_migrate.py:126`, `export_all.py:278-281`, `lib/timber.typ:1559-1563` (dépliés dans `Formules/`) ; `calc/tools/source_archive.py:163` (archivage commun, `backend=`) ; renommages par onglet : `connectors_tab.py:598`, `load_tab.py:820`, `member_check_tab_actions.py:344`, `woodcore_gui_polar.py:1179`, `python_tab.py:586`.
- Lot 2 : `plan_documents.py:208,245` (`import_file` refuse un fichier hors projet, `refresh` jamais appelée en production) ; huit `write()` qui balaient leur dossier de `data/` (`plan.py:1177`, `fire.py:933`, `statics.py:1124`, `schema.py:720`, `connection.py:676`, `connector.py:977`, `annex.py:691`, `registry.py:253`) ; onze lectures `"../data/" + …` de `lib/calc-engine.typ` ; `validation.py:651-912` (formes de chemins) ; `sheets.py:29,119,531` ; `stamps.py:33,191,203` ; `archive_export.py:123-149`.

### Existant à réutiliser
- Les clés `layout` existantes portent la plupart des nouveaux emplacements comme **valeurs** (`generated`, `sources`, `archives`, `images`) ; une seule clé nouvelle, `config`.
- La migration v0.111 entière (journal, `before.zip`, `_retrying`, `typst_paths`, `compare_pdf`, `rollback`, `_audit`, dialogue) : la généraliser, pas en écrire une seconde.
- `formula_domain` (`free_id`, `slug`, `remove`, `restore`, `ArchiveBackend`) comme base du module commun ; `source_archive.Actions(backend=…)` comme point d'accroche de l'archivage ; `unfold.json` (base à trois voies, #62) comme modèle des empreintes de stubs.
- `plan_documents.refresh`/`_pages_and_layers` pour la relecture ; `_write_atomic`.

### Risques et correctifs
| Risque | Sévérité | Correctif (étape §14) |
|---|---|---|
| A01 — `archive_export` (`GENERATED_LEFT_OUT`), `stamps.enumerated`, `unfold_migrate`, `renumbering`, `templates` parcourent `generated` entier : `archives/` et `sources/` imbriqués seraient zippés dans chaque archive | bloquant | `Project.generated_excludes()` unique, chemins résolus ; test qui échoue d'abord (étape 2) |
| A02 — `schema_version` const 1.0 : un Woodcore ancien lirait le nouveau projet sans rien dire | bloquant | schéma 1.1 (`enum ["1.0","1.1"]`), écrit 1.1, 1.0 lue (étape 1, D-20) |
| A03 — marqueur de structure | important | `layout.config` seule ; `config_dir` (= `typst_root` si absente) dont dérivent config/commands/title/references/Template (étape 1) |
| A04 — `commands.typ` importe le moteur en relatif ; `config.typ` importe `/Template/template.typ` (`forms.py:45-46,276,294,381`) | important | `#import "/000-Woodcore/lib/calc-engine.typ"` ; regex de forme acceptant les deux formes, littéral tiré de `config_dir` (étape 3) |
| A05 — `project: "references.bib"` dans `bibliography.typ:361`, `document.typ:957`, modèles `007-literatur.typ` | important | littéral tenu égal à `Project.references_bib` par un test (étape 3) |
| A06 — `project_migrate.plan` ne sait que « rapport seul → trois » ; `before.zip` ne couvre que le dossier du rapport ; `_Archiv` (qui contient l'espace de migration) est lui-même déplacé | important | second plan chaîné sous un même journal ; zip de toute la racine ; journal hors de l'arbre déplacé, `archives` déplacé en dernier (étape 9) |
| A07 — littéraux en double (`"_woodcore"`, `"/commands.typ"` dans ~15 fichiers, `"Formules"`, `"Plans"`, `MODE_FOLDERS` par langue) | important | une source (`project.py`/`documents.py`) + test grep ARCH-001 (étape 3) |
| A08/A09/A10 — `.vscode` (`ROOT_PATH_COMMENT`), `_check_documents` ne vérifie pas `config`, 68 `_woodcore` dans `tests/*.py` | mineur | étapes 1, 9, 11 ; le projet exemple est migré par `woodcore-cli migrate` lui-même et committé avec le code |
| B01 — stub et déplié au même nom ; `show-check-member` d'un record `gen` inclurait le stub, qui s'inclut lui-même | bloquant | bascule par empreinte (D-16) ; l'appel du stub déplié ne passe jamais par `include` de lui-même (étape 6) |
| B02 — `formula_domain.prepare` lève sur tout `.typ` sans `#var-domain` | bloquant | `domain_files()` distingue stub et domaine ; aucun balayage récursif ; `prepare` ne lit que les domaines (étape 6) |
| B03 — « jamais réécrit » contre les dépliés futurs | important | empreinte de chaque stub enregistrée dès maintenant (base par dossier parent) (étape 5) |
| B04 — ids : slug minuscule (`formula_domain.check_id`) contre ids des sources (`A-Z . +`) ; clé `domain:` par id seul | important | unicité vérifiée sur tous les dossiers de domaines ; le stub garde l'id de la source tel quel (étape 6) |
| B05/B06 — module commun Qt-free ; création et renommage dispersés dans 6 onglets | important | `calc/domains/domain_file.py` (table unique `{type: (dossier, appel)}` dans `project.py`) ; archivage par `backend`, création/renommage par un `on_saved` unique appelé au point d'écriture de chaque source (étape 5) |
| B07 — `FORMULAS_FOLDER` a deux sens ; `timber.typ:1561-1563` écrit `/Formules/` en dur | important | `DOMAINS_FOLDER` et dossiers des vérifications séparés ; le chemin du déplié passe par le record exporté ; test de parité (étape 6) |
| B08 — scripts : `script.sources_dir`, provenance `python:scripts/<id>.py`, renommage des deux fichiers | important | `Scripts/` via `project.py`, renommage atomique des deux (étape 7) |
| B09/B10 — `tab_formula` est dans `formula_tab.py:48,156,264`, pas `strings.json` ; « Formules » dans `fm_domain_note`, `lib/formula.typ:1740`, `timber.typ:1537,1558` ; `archive_export`, `cited_by` | mineur | étapes 6, 10 |
| C01 — le balayage des fichiers périmés supprimerait les fichiers de l'ingénieur dans un dossier qu'il voit | bloquant | `engine.write_managed(base, files, manifest)` : supprime seulement ce que le JSON précédent listait ; les huit `write()` l'appellent (étape 12, D-17) |
| C02/C03 — feuilles et figures mêlées ; genre d'une feuille lu dans son texte ; id unique sur deux dossiers ; bundles | bloquant/important | `Exports/Figures/` (D-17) ; feuilles par genre, unicité sur les deux, bundles réécrits (étape 8) |
| C04/C05 — relecture à construire ; copie à l'import ; collision | important | `refresh_all` Qt-free à l'affichage et à l'export, garde `WRITERS` ; copie dans `Imported Plans/`, collision → remplacement confirmé (D-18) (étape 13) |
| C06 — annexes nommées par id ; extraits dérivés | important | nom d'origine dans la fiche (champ additif, `schema_version` montée) ; extraits dans `Appendix/Exports/` (étape 14) |
| C07/C08 — fonds de plan ; chemins de figure en JSON | important | fond réduit = export (`Exports/Figures/`) ; chemin racine-absolu, `figure-path()` unique dans le moteur, anciens JSON lus, `schema_version` des exports montées (étape 12) |
| C09/C10/C11 — estampilles, archives, octets LF | important/mineur | `stamps`, `archive_export` étendus ; écriture en octets LF dans `write_managed` (étapes 12, 15) |

### Approche recommandée
Tout chemin vient de `project.py` (une clé `config` de plus, une table fixe des dossiers de domaines) ; la création et la migration lisent cette table ; un module Qt-free `domain_file.py` écrit les stubs pour tous les onglets ; le lot 2 déplace les figures derrière une fonction d'écriture commune et une fonction de lecture du moteur.

## 14. Plan d'implémentation

Deux lots (D-20), chacun testé, vérifié et committé à part. Le lot 1 laisse les figures dans `data/` et les documents importés là où ils sont.

### Lot 1 — structure, migration, domaines
1. **`project.py` et schéma** : constantes `CONFIG_FOLDER`, `WOODCORE_FOLDER`, `DOMAINS_FOLDER`, `POSITIONS_FOLDER`, table `DOMAIN_FOLDERS` (`snow-load` → `Variable-loads/Snow`, `wind-load` → `Variable-loads/Wind`, `dead-load` → `Permanent-loads`, connecteurs, moment polaire, `Timber-checks/<Genre>`, `Steel-checks/<Genre>`, scripts) et des dossiers de dessin ; clé `layout.config`, `config_dir`, `positions_dir`, `domain_dir(kind, genre)`, `generated_excludes()` ; `SCHEMA_VERSION` 1.1, 1.0 lue ; `_check_documents` étendu. → REQ-002, 013, ARCH-002. Tests : `test_project`.
2. **Exclusions de `generated`** (A01) : `archive_export`, `stamps`, `unfold_migrate`, `renumbering`, `templates` passent par `generated_excludes()`. → REQ-002. Tests : `test_archive_export`, `test_stamps` (sources/archives imbriqués non parcourus), écrits avant le correctif.
3. **Une source pour les chemins Typst** : `documents.MODE_FOLDERS` fixe (`100-Service criteria agreement`…), `GENERATED_FOLDER` tiré de `project` ; `commands_import`/`import_line` depuis `config_dir` ; remplacer les littéraux `"/commands.typ"`, `"/Template/template.typ"`, `"references.bib"`, `"_woodcore"`, `"Plans"` (liste A07) ; `commands.typ` du modèle importe `/000-Woodcore/lib/…` ; nouveau test grep ARCH-001. → REQ-001, 003, 013, ARCH-001. Tests : `test_documents`, `test_forms`, `test_typst_paths`, `test_structure`, nouveau `test_layout_literals`.
4. **Création** : `templates/projet/`, `templates/documents/` et `project_template.create` produisent la structure cible complète, tous les dossiers de lot 1 créés (REQ-011) depuis la table ; `.vscode/settings.json` du modèle à jour. → REQ-001…003, 011. Tests : `test_project_template`, `test_templates`, compilation d'un projet neuf.
5. **`calc/domains/domain_file.py`** (Qt-free) — *réalisé autrement sur un point, noté à la vérification* : pas de `move_with` ni d'`on_saved` par onglet, mais une réconciliation unique `sync` (à l'export et après chaque écriture des onglets de domaines, `woodcore_gui.synced_domains`) : un stub intact d'un domaine renommé, archivé ou changé de genre est archivé et le nouveau écrit (même octets) ; un stub édité par l'ingénieur ne suit pas son domaine et est dit (`domain_file_orphan`) — conforme à CON-002 (le fichier est à lui), au prix qu'un renommage ne déplace pas son texte. : `stub_text(kind, id)` (appels d'impression de la table : `show-calc` neige/vent/charges permanentes/script, `show-connector`, `show-polar-moment` avec N/V/M écrits, `show-check-member`, `show-check-steel`), `write_once` avec base d'empreintes par dossier parent, `move_with` (renommer, dupliquer, changer de genre), `archive`/`restore` ; `on_saved(here, kind, old_id, new_id)` appelé au point d'écriture des sources (`load_tab`, `connectors_tab`, `woodcore_gui_polar`, `member_check_tab_actions`, onglet Acier, `python_tab`) ; `TypBackend` pour `source_archive`. → REQ-004, 010, 015, ARCH-004. Tests : nouveau `test_domain_file` (chaque stub compile après export), tests des onglets.
6. **`Domains/` et dépliés par genre** : `formula_domain` sur `DOMAINS_FOLDER` ; `domain_files()` distingue stubs et domaines (B02) ; ids uniques sur tous les dossiers (B04) ; `unfold` écrit `Timber-checks/<Genre>/<id>.typ` en remplaçant le stub inchangé, conflit sinon (B01, D-16), `unfold.json` dans `Timber-checks/` ; `timber.typ` tire le chemin du record (B07) ; onglet renommé Domaines/Domänen/Domains et groupé par type (UI-001, REQ-016). → REQ-005, 006, 015, 016, UI-001. Tests : `test_formula_domain`, `test_formula_tab`, `test_unfold`, `test_member_check*`, test de parité Python/Typst.
7. **`Scripts/` et `Positions/`** : `script.sources_dir` → `Scripts/`, `.typ` par script, renommage des deux fichiers ; `positions_store` lit/écrit `Positions/positions.json` et écrit `Positions/Positions.xlsx` à chaque enregistrement (jamais lu). → REQ-010, 014. Tests : `test_script`, `test_python_tab`, `test_positions_store`.
8. **Feuilles d'export par genre** : `sheets` écrit `Plans/Position-plan/Exports/<id>.typ` ou `Plans/Fire-plan/Exports/<id>.typ` selon `sheet(kind:)`, id unique sur les deux, bundles et liens réécrits. → REQ-008 (partie feuilles), D-06. Tests : `test_sheets`.
9. **Migration** : second plan « trois documents → structure 1.1 » chaîné après la migration existante, sous un même journal ; `before.zip` de toute la racine ; journal hors de l'arbre déplacé, `archives` en dernier ; déplacements (config, `_woodcore`, `Woodcore-Datei`, `_Archiv`, `Formules` → `Domains`/`Timber-checks`, `1_…` → `100-…`, scripts, positions, feuilles), réécriture de toutes les lignes par `typst_paths`, stubs des domaines existants, `.woodcore` 1.1, `.vscode` ; dialogue proposé quand la structure n'est pas à jour (UI-002) ; `tests/projet-exemple/` migré par `woodcore-cli migrate` et committé. → REQ-012, UI-002, CON-001, 006. Tests : `test_project_migrate` (PDF identiques, rollback octet pour octet), `test_migrate_dialog`.
10. **Documentation lot 1** : `layout.md` §11, `api-conventions.md` §10bis, `docs/domain/*` touchés, `docs/ui/` (onglet Domaines), `decisions.md` §13 (structure 1.1, D-16, D-20), `testing-catalogue*.md`, `CHANGELOG.md`, « Nouveautés » de/fr/en.
11. **Tests lot 1** : fichiers liés pendant le travail, suite complète en arrière-plan ; vérification indépendante ; commit du lot 1.

### Lot 2 — imports, exports, Appendix
12. **Exports** : `project.exports_dir(kind)`/`figures_dir(kind)` ; `engine.write_managed` (manifeste, octets LF, atomique) ; les huit `write()` écrivent dans `<Dossier>/Exports/Figures/` ; JSON en chemins depuis la racine, `schema_version` des exports montées, `validation.py` ; `figure-path()` unique dans `lib/calc-engine.typ` (anciens JSON lus). → REQ-008, ARCH-003. Tests : `test_plan`, `test_fire`, `test_statics`, `test_schema`, `test_connection`, `test_connector`, `test_export_all` (aucun svg sous `data/`, deux exports identiques, un fichier de l'ingénieur survit), grep `"../data/" + ` dans `lib/`.
13. **Imported Plans** : `import_file` copie dans `Plans/<Plan>/Imported Plans/`, collision → remplacement confirmé (D-18) ; `refresh_all` à l'affichage de l'onglet et à l'export, garde `WRITERS`. → REQ-007. Tests : `test_plan_documents`, `test_plan_tab_rework`.
14. **Appendix** : PDF d'annexe sous son nom d'origine dans `Appendix/` (champ additif, version de la fiche montée), relecture si remplacé, extraits dans `Appendix/Exports/`. → REQ-009. Tests : `test_annex`.
15. **Estampilles, archives, migration du lot 2** — *réalisé ainsi* : la copie des documents importés et des PDF d'annexes (`plan_documents.adopt`, `annex.adopt`) se fait dans la migration (sauvegardée dans before.zip, défaite par le rollback) et, idempotente, à chaque export -- l'accord de l'ingénieur étant la migration ou l'export qu'il lance ; les originaux restent où ils sont (le PDF d'annexe à côté de son ancienne fiche aussi : gardé, jamais supprimé par Woodcore, décision de l'ingénieur du 2026-10-16 « non, ne pas le supprimer »). La relecture à l'affichage d'un onglet est un écrivain de `WRITERS` que l'onglet n'appelle pas sur un projet ouvert en lecture seule (pas de refus affiché à chaque affichage). Les appelants de la fenêtre continuent de passer `data/` : le module retrouve le projet (`project.owning`). Plan initial : `stamps` et `archive_export` incluent les nouveaux dossiers ; à l'ouverture, copie des documents importés existants dans `Imported Plans/` et des PDF d'annexes dans `Appendix/` (idempotent, avec accord) ; projet exemple mis à jour. Tests : `test_stamps`, `test_archive_export`, `test_project_migrate`.
16. **Documentation et tests lot 2**, vérification indépendante, commit.

## 15. Vérification

Lot 1, vérifié par l'agent `requirements-verifier` le 2026-10-15 sur l'arbre de travail contre HEAD 1143d13 (tests relancés un fichier à la fois), puis ses ⚠️ corrigés et revérifiés par les tests nommés.

| Élément | Verdict | Preuve |
|---|---|---|
| REQ-001 | ✅ | `project.py` `CONFIG_FOLDER`, `config_dir` ; `test_new_project` 34/34 (les cinq parties dans `000-Typst-Config/`) ; exemple migré |
| REQ-002 | ✅ | `generated_excludes` dans archive_export, stamps, templates ; `test_stamps`, `test_archive` (un test par structure) |
| REQ-003 | ✅ | `documents.MODE_FOLDERS` ; `test_documents` 11/11 |
| REQ-004 | ✅ | `domain_file.py` ; `test_domain_file` 8/8, dont la neige compilée après export et chaque genre de stub de l'exemple compilé (`test_every_kind_of_stub_of_the_example_compiles`) ; écart assumé au plan : `sync` au lieu de `move_with` (§14 étape 5) |
| REQ-005 | ✅ | `formula_domain` (Domains, `include_call` depuis le chemin du domaine) ; `test_formula_domain`, `test_formula_tab` |
| REQ-006 | ✅ | `unfold.domain_path`, `base_path` ; `test_unfold` 20/20 |
| REQ-010 | ✅ | `script.sources_dir(here)` ; `test_a_script_lies_in_scripts_with_its_stub_and_runs_from_there` |
| REQ-011 | ✅ | `structure_folders`/`ensure_folders` ; `test_new_project`, `test_migrate_folders` |
| REQ-012 | ✅ | `project_migrate_folders.py` ; `test_migrate_folders` 4/4 (migration par la commande, trois PDF comparés, rollback octet pour octet, échec défait) ; `test_migrate` 19 |
| REQ-013 | ✅ | `test_documents.test_the_folders_are_the_engineer_s_own_forms` |
| REQ-014 | ✅ | `test_positions_store.test_a_project_laid_out_by_folders_keeps_its_positions_in_positions_and_a_workbook_beside_them` |
| REQ-015 | ✅ | `unfold.unfold_checks` ; `test_a_check_s_stub_is_unfolded_over_and_an_edited_one_is_kept_and_said` (remplacement, `unfold_stub_edited`, `file`, compilation) |
| REQ-016 | ✅ | `group_of`, `group_label` ; `test_the_domains_tab_groups_an_unfolded_check_by_its_kind` (fr/de/en, stubs exclus) |
| REQ-008 (feuilles) | ✅ | `sheets.folder(here, kind)` ; `test_sheets.test_laid_out_by_folders_a_sheet_lies_in_the_exports_of_its_kind` |
| UI-001 | ✅ | `formula_tab.py` `tab_formula` ; `test_formula_tab` |
| UI-002 | ✅ | `migrate_dialog` ; `test_modes_window` 18 |
| ARCH-001 | ✅ | `test_layout_literals` ; `structure_preview` et `structure_tab` lisent `template_dir` ; `ALLOWED` justifié dans le test (définitions, migration, écrivains de la forme canonique des modèles que la création réécrit) |
| ARCH-002 | ✅ | schéma 1.1 `enum`, `config` documenté dans woodcore-project et template ; `test_project` |
| ARCH-004 | ✅ | `domain_file.py`, seul écrivain des `.typ` de domaine |
| CON-001/006 | ✅ | `compare_pdf`, `_retrying` |
| CON-005 | ✅ | layout.md §11, api-conventions §10bis, ui/tab-formulas, domain/{member-checks, scripts, positions, connections, connectors, steel, loads}, decisions + index, open-questions, CHANGELOG, Nouveautés fr/de/en, catalogue ; chaînes visibles sans `Woodcore-Datei/` |
| REQ-007, REQ-008 (figures), REQ-009, ARCH-003 | lot 2 | dossiers créés vides ; §14 étapes 12-16 |

Lot 2, vérifié par l'agent `requirements-verifier` le 2026-10-16 sur l'arbre de travail contre 998bb96 (tests relancés un fichier à la fois) : aucun ❌, cinq ⚠️ corrigés puis prouvés par les tests nommés.

| Élément | Verdict | Preuve |
|---|---|---|
| REQ-007 | ✅ | `plan_documents.imported_dir`, `_copy_in`, `import_file`, `refresh_all` ; `test_plan_documents` (copie depuis n'importe où, `doc_replace` puis remplacement, relecture, adoption) ; ⚠️ fenêtre corrigé : `test_plan_tab_rework.test_a_document_of_the_same_name_is_replaced_on_a_yes_and_one_written_over_is_read_again_as_the_tab_is_shown` (Non / Oui, relecture à l'affichage, rien en lecture seule) |
| REQ-008 (figures) | ✅ | `engine.write_managed`, `Figures` ; `test_figure_exports.test_the_export_writes_its_figures_into_the_tabs_exports_and_keeps_the_engineer_s_file` (aucune figure sous data/, fichier de l'ingénieur gardé, deux exports identiques) |
| REQ-009 | ✅ | `annex.copy_pdf`, `refresh_sources` ; `test_annex` (Appendix/, fiche 1.1, extraits dans Appendix/Exports/, relecture) ; ⚠️ fenêtre corrigé : `test_a_pdf_written_over_in_appendix_is_read_again_as_the_tab_is_shown_and_not_read_only` |
| ARCH-003 | ✅ | `figure-path` (`lib/calc-engine.typ`) ; `test_an_export_written_before_names_its_figures_under_data_and_is_read_as_it_was` |
| Étapes 12-16, C01-C11 | ✅ | voir ci-dessus ; `test_stamps`, `test_archive`, `test_the_stamps_and_the_archive_take_in_the_tabs_exports_and_the_appendix` ; ⚠️ retour arrière des figures corrigé : `test_migrate_folders.test_a_rollback_sets_aside_the_figures_the_proof_s_export_wrote_and_the_records_adopted_get_their_bytes_back` |
| CON-001, 002 | ✅ | `test_migrate_folders` (trois PDF, rollback octet pour octet) ; `write_managed`, `appendix_name`, `doc_replace` |
| CON-005 | ✅ | ⚠️ corrigé : `docs/ui/tab-plans.md`, `tab-annexes.md` ; docstrings de `plan_svg`, `statics_svg`, `schema_svg`, `connection_svg`, `registry` |

Reste, hors lot : la migration complète sans `--skip-data` ne peut pas être prouvée sur la fixture (le projet exemple n'a pas de classeur de charges : son rapport ne compile pas après un export complet), comme au lot 1.

Hors lot : `test_formula_domain.test_a_value_beside_domain_is_read_and_written_back_and_a_gen_is_kept` échoue aussi sur HEAD sous Windows (le test écrit son fichier en CRLF puis le compare au texte lu en LF) ; non touché.

## 16. Journal d'avancement

| Date | Statut | Fait / reste |
|---|---|---|
| 2026-10-15 | draft | spécification extraite de l'issue #64 et du modèle Test ; 7 questions ouvertes |
| 2026-10-15 | specified | 13 questions répondues par l'ingénieur ; 13 REQ, 2 UI, 4 ARCH, 6 CON, 15 décisions |
| 2026-10-15 | reviewed | trois revues (A, B, C) REVOIR ; Q-014 à Q-026 répondues ; REQ-014 à 016 ajoutées ; structure cible révisée (parents) ; §13 et plan §14 en deux lots écrits |
| 2026-10-15 | approved | approuvée par l'ingénieur («Approuver et implémenter»), lot 1 d'abord |
| 2026-10-15 | implementation | lot 1 étape 1 : `project.py` (clé `config`, `has_folders`, `config_dir`, `from_root`, table `DOMAIN_FOLDERS`/`KIND_FOLDERS`/`DRAWING_FOLDERS`, `domain_dir`, `unfolded_dir`, `positions_dir`, `structure_folders`, `ensure_folders`, `generated_excludes`, `schema_version_for`), schéma 1.1, `documents.py` (dossiers 100/200/300 fixes, `000-Woodcore`, `commands_import` depuis `config_dir`) ; tests `test_project`, `test_documents` verts (REQ-002, 003, 013, ARCH-002 en partie) |
| 2026-10-15 | implementation | lot 1 étape 2 : `generated_excludes()` dans `archive_export` (et domaines, `Template` par `template_dir`, positions par `positions_dir`), `stamps.enumerated` (config par `config_dir`, domaines) et `templates.save_project` ; `conftest.legacy_modes_layout` ; tests `test_stamps` (25) et `test_archive` (11) verts, dont un test par structure par dossiers (REQ-002, ARCH-RISK-A01) |
| 2026-10-15 | implementation | lot 1 étapes 3-4 (en partie) : `documents.config_moves`/`relocate_config_paths`/`root_import_line`, `forms` (Template via `template_dir`, regex des deux formes, chemins du titre et du config réécrits), `templates.config_for`/`Template.config`, `project_template` (parties de config dans `000-Typst-Config/`, sources/archives dans `000-Woodcore/`, réécriture des chemins des modèles, `ensure_folders`), `positions_store.path` → `positions_dir`, lignes d'import de `sheets`, `formula_domain`, `unfold`, messages de `member_check` ; nouveau `test_layout_literals` (reste : onglet Formules et `timber.typ`, étape 6) ; `test_new_project` 34/34 vert |
| 2026-10-15 | implementation | lot 1 étapes 5-6 : `domains/domain_file.py` (stubs, `sync`, `is_untouched`, archives, orphelins), appelé à l'export et après chaque écriture des onglets de domaines (`woodcore_gui.synced_domains`) ; `formula_domain` (Domains, liste élargie aux dépliés hors stubs, `group_of`, ids uniques sur tous les dossiers) ; `unfold` (`domain_path` par genre, `unfold.json` dans `Timber-checks/`, bascule stub → déplié, `unfolded_files`) ; export des vérifications 1.4 (`file`) ; `timber.typ` inclut `rec.file` ; onglet Domaines/Domänen/Domains et groupes fixes ; `script.sources_dir` → `Scripts/` (tests à venir) |
| 2026-10-15 | implementation | lot 1 étapes 7-8 : `positions_store.write_workbook` (Positions/Positions.xlsx à chaque changement, à l'export s'il manque), `renumbering`/`plan_tab` l'appellent ; `sheets` par genre (`folder(here, kind)`, `folders`, `bundles_folder`, `path` sur les deux dossiers), `renumbering.typst_files` (dossiers des feuilles et des domaines, archives exclues) ; tests `test_domain_file` (4), `test_positions_store` (16), `test_sheets` (23), `test_renumbering` (15) verts |
| 2026-10-15 | implementation | lot 1 étape 9 : `project_migrate_folders.py` (plan, check, describe, run avec preuve des trois PDF, `_undo`, `rollback`), `project_migrate` chaîne les deux étapes (`woodcore-cli migrate`, `--rollback` selon le journal), `documents.legacy_modes_layout`/`LEGACY_MODE_FOLDERS` pour la première étape ; dialogue et bannière (UI-002) ; `tests/projet-exemple/` migré par la commande elle-même (174 fichiers réécrits, trois PDF identiques), `checks.json` 1.4 et `formulas.json` mis à jour ; fixtures `legacy_three` (vérifié : 304 fichiers identiques au commit, `checks.json` excepté) et `legacy_example` ; `conftest` copie sans moteur ni archives ; tests `test_migrate_folders` (4) et `test_migrate` (15) verts |
| 2026-10-15 | testing | lot 1 étape 10 : documentation -- layout.md §11 (arbre par dossiers, fichiers de domaine, migration), api-conventions §10bis, ui/tab-formulas (Domaines, groupes), decisions.md §13 + index, open-questions (lot 2, dépliés par onglet, dialogue de création, séisme), catalogue (test_layout_literals, test_domain_file, test_migrate_folders), CHANGELOG v0.119 issue #64, Nouveautés 0.119 fr/de/en ; suite complète en cours |
| 2026-10-15 | testing | lot 1 étape 11 : suite complète -- 2965 verts, 11 skips ; derniers échecs corrigés (fichiers d'essai des tests vers `000-Typst-Config`, `structure_preview.header`, `formula_domain.include_call`, `doc_templates.instantiate` et `content_switch` lisent les modèles comme le projet les tient, `documents.relocate_config_text` textuel et sans écriture double, `forms.apply` réécrit avant de mettre en place, `cli_unfold`, `template.schema.json` documente `config`, traduction de `show-check-member`) ; reste `test_formula_domain.test_a_value_beside_domain_is_read_and_written_back_and_a_gen_is_kept`, rouge aussi sur HEAD sous Windows (fins de ligne CRLF), sans lien |
| 2026-10-15 | verification | lot 1 vérifié (requirements-verifier) : 15 ✅, 7 ⚠️ ; ⚠️ corrigés -- tests REQ-004 (chaque genre compile), REQ-010, REQ-015, REQ-016, `Template` tiré de `template_dir` (structure_preview, structure_tab), chaînes visibles, docs/domain ; lot 1 complet, lot 2 restant (§14 étapes 12-16) |
| 2026-10-15 | implementation | lot 1 committé ; la spec reste active pour le lot 2 (§14 étapes 12 à 16) |
| 2026-10-16 | implementation | lot 2 étape 12 : `project.FIGURE_KINDS`, `figures_folder`, `exports_dir`, `figures_dir`, `owning` ; `engine.write_managed`, `Figures` ; les huit écrivains (plan, fire, statics, schema, connection, connector, annex, registry + dead_load_source) écrivent dans `Exports/Figures/`, noms depuis la racine, versions montées, `validation.figure_names` ; `figure-path` unique dans `lib/calc-engine.typ` |
| 2026-10-16 | implementation | lot 2 étapes 13-14 : `plan_documents` (`imported_dir`, copie à l'import, `doc_replace` → confirmation dans la fenêtre, `refresh_document`, `refresh_all` à l'affichage et à l'export) ; `annex` 1.1 (`file`, `appendix_dir`, `copy_pdf`, `refresh_sources`), extraits dans `Appendix/Exports/` ; onglets et mots fr/de/en |
| 2026-10-16 | implementation | lot 2 étape 15 : `stamps.enumerated`, `archive_export` ; `adopt` des documents et annexes dans la migration (before.zip, rollback, figures écartées) et à l'export ; projet exemple réexporté (calculations.json et project.json gardés), PDF d'annexe dans `Appendix/` ; `legacy_three` défait le lot 2 ; tests `test_figure_exports` (nouveau), `test_plan_documents`, `test_annex`, `test_migrate_folders` verts |
| 2026-10-16 | testing | lot 2 étape 16 : documentation (layout.md §11, domain/*, decisions.md + index, open-questions, catalogue, CHANGELOG, Nouveautés 0.119 fr/de/en) ; suite complète : 2981 verts, 11 skips, l'échec connu de test_formula_domain (CRLF) ; test_links et test_linkable_spin corrigés |
| 2026-10-16 | verification | lot 2 vérifié (requirements-verifier) : aucun ❌, 5 ⚠️ corrigés (tests fenêtre des deux relectures, test du retour arrière des figures, docs/ui, docstrings) |
| 2026-10-16 | completed | spec close : lots 1 et 2 livrés ; déplacée dans `docs/requirements/completed/` |
