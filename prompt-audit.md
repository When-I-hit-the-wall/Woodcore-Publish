# Audit périodique du moteur de rapport statique

> À lancer tous les quelques jours dans une session Claude Code ouverte à la racine du projet : « Exécute prompt-audit.md ». Les trois réglages ci-dessous peuvent être modifiés dans le message de lancement (« Exécute prompt-audit.md, PORTÉE = incrémental »).

```
PORTÉE      = complet      # complet | incrémental (seulement ce qui a changé depuis le dernier audit, plus le socle de la phase 1)
CORRECTIONS = A            # aucune | A (corriger les défauts de classe A, voir phase 9)
AGENTS      = oui          # oui : les phases 2 à 7 tournent en parallèle, chacune dans son propre bac à sable | non : tout en séquence
```

Tu es l'auditeur qualité de ce projet. Beaucoup de modifications y sont faites, souvent par plusieurs sessions et plusieurs agents en même temps. Il en reste des commandes anciennes encore référencées, des morceaux non traduits, des données en double et une documentation (`docs/`) qui ne décrit plus tout à fait le code. Ton travail est de **trouver** ces défauts avec des preuves, de **corriger** ceux qui sont sûrs, et de **rapporter** le reste, pour que chaque audit laisse le projet plus robuste que le précédent. Un audit qui dit « tout va bien » sans preuve n'a aucune valeur : chaque affirmation du rapport doit s'appuyer sur une commande exécutée, un fichier lu ou une valeur comparée.

---

## 0. Règles absolues (à relire avant chaque phase)

1. **Ne jamais écrire dans les classeurs de l'ingénieur** : `Positionen.xlsx`, `*Belastungsannahmen*.xlsm`, `Verbindung.xlsm`, `Verbindungen.xlsx`, ni dans aucun fichier de `ExternalFiles/`. Un classeur ne s'ouvre qu'en **copie**, dans le bac à sable, et Excel ne sauvegarde jamais l'original.
2. **Ne jamais toucher à l'état git de tout l'arbre** : pas de `git stash`, `git checkout -- .`, `git reset --hard` ni `git clean`. D'autres sessions ont du travail non commité dans ce même arbre (mémoire `concurrent-sessions`). Pour savoir si un défaut existait avant une modification, extraire **un seul fichier** d'un commit vers le bac à sable (`git show <commit>:<chemin> > …`).
3. **Pas de commit ni de push**, sauf demande explicite de l'ingénieur dans le message de lancement.
4. **Tout ce qui s'exécute s'exécute dans un bac à sable** (§0.2), sauf la suite de tests de la phase 1, qui tourne dans l'arbre réel **et seule**. `export_all.py`, `typst compile`, la fenêtre de Woodcore, `woodcore-cli` et les classeurs recalculés écrivent dans le bac à sable, jamais dans `_woodcore/data/`, `Statischer Rapport.pdf` ou `_Archiv/` du vrai projet.
5. **Coordination** : lancer `ListAgents` au début. Si une autre session travaille sur ce projet, lui envoyer (SendMessage) la liste des fichiers que la phase 9 risque de modifier, et ne pas lancer la suite de tests pendant qu'elle lance la sienne. Deux exécutions simultanées produisent de faux échecs. On reconnaît une collision à son **message** (`file not found … tests\.tmp …` ou `….preview…`), jamais à la durée du test.
6. **Pièges du poste** (mémoire `shell-and-path-hazards`) : tout script de plus d'une ligne est écrit avec l'outil Write dans le bac à sable, puis lancé avec `python -u "C:/…/script.py"`. Ne pas passer par un heredoc, ne pas utiliser de chemins `/c/…` pour Python ou Typst, lancer avec `PYTHONIOENCODING=utf-8`. Pour Qt hors écran, définir `QT_QPA_PLATFORM=offscreen` et `QT_QPA_FONTDIR=C:\Windows\Fonts`. Tout dialogue modal est remplacé par un bouchon (stub) : un modal hors écran ne revient jamais. Chaque script Qt tourne dans un sous-processus avec un délai maximal (300 s), pour qu'un blocage ne fige pas l'audit.
7. **La référence est dans `docs/`** (index : `docs/README.md`) ; `CLAUDE.md` n'en est que le point d'entrée court. `docs/decisions.md`, `docs/ui/window.md` et `docs/conventions/testing.md` dépassent 100 Ko : ne jamais les réécrire en entier. Utiliser des remplacements ciblés (Edit), en conservant les fins de ligne du fichier. Une modification s'y écrit en anglais, un paragraphe par ligne (§1ter).
8. **La norme tranche** (§2 règle 13). Quand Python, Typst et un classeur Excel ne donnent pas la même valeur, on ne suppose pas que l'un a raison : on lit la clause dans le PDF de `ExternalFiles/000-Normes/`, à la page citée.
9. **Ne rien sauter en silence.** Un contrôle impossible à mener (outil absent, délai dépassé, cas non automatisable) figure dans le rapport comme « NON FAIT », avec sa raison.

### 0.1 Préparation

1. Noter la date, l'heure, `git rev-parse HEAD`, `git status --short` (compter les fichiers modifiés par d'autres), `typst --version`, `python --version` et les versions installées comparées à `Woodcore/requirements.txt`. Vérifier aussi que Excel COM répond (`New-Object -ComObject Excel.Application`, puis `Quit`).
2. Lire le **dernier rapport** de `Woodcore/000-Audits/` (le plus récent par nom) : son commit, ses constats encore ouverts et ses durées. En mode `incrémental`, calculer `git diff --name-only <commit du dernier audit> HEAD` plus les fichiers modifiés non commités. Cette liste délimite ce que les phases 2 à 7 examinent. La phase 1 et les contrôles marqués **[toujours]** tournent dans tous les cas.
3. Lire `CLAUDE.md` et `docs/README.md`, puis `docs/architecture/principles.md` (§2), `docs/architecture/layout.md` (§11), `docs/conventions/testing.md` (§11ter), `docs/decisions.md` (§13) et `docs/open-questions.md` (§14), et les spécifications de `docs/requirements/active/`. Lire aussi `CHANGELOG.md` (les entrées depuis le dernier audit), `README.md` et `tests/README.md`.

### 0.2 Le bac à sable

Créer `%TEMP%\typst-audit-AAMMJJ-HHhMM\projet\`. ⚠️ Pas dans le scratchpad de la session : son chemin est si profond que les fichiers du projet copiés dessous dépassent les 260 caractères de Windows, et Python ne trouve plus `engine.py` (constaté à l'audit 260916). Le programme et le projet y sont séparés comme dans l'arbre réel (v0.82) : chaque commande y nomme le projet du bac à sable par `--project`, et le programme lu est celui de l'arbre réel, qui n'écrit rien en lui-même :

- `projet/`, copie de `Musterprojekt/` **sans** `_Archiv/`, `__pycache__/`, `.render-cache/` et `_woodcore/out/` — les classeurs, `01_Pläne/` (fonds de plan), `Statischer Bericht (typst)/` et `Woodcore-Datei/` compris, tous **copiés** ;
- `ExternalFiles/` n'est pas copié : une phase qui en a besoin le lit à son emplacement réel.

La fenêtre de Woodcore lancée depuis le bac à sable reçoit `WOODCORE_SETTINGS=<bac à sable>/settings.json` (`TYPST_KATALOG_SETTINGS` jusqu'à la v0.82), pour que les réglages de l'ingénieur ne soient jamais modifiés, et elle est ouverte sur le projet du bac à sable (`--project`), jamais sur celui de la page d'accueil. Si `AGENTS = oui`, **chaque agent crée son propre bac à sable** (`projet-phase2/`, `projet-phase3/`, …). Avant de rendre la main, chaque agent vérifie par `git status --short` sur l'arbre réel qu'il n'y a rien écrit.

---

## Phase 1 — Le socle **[toujours]**

Cette phase tourne dans la session principale, avant de lancer les agents.

1. `cd Woodcore` puis `python -u tests/run_tests.py`, **seul** (règle 5). Relever le nombre de tests réussis, échoués et ignorés, et le nom de chaque test ignoré avec sa raison. Relancer chaque échec **seul** (`-k <nom> -v`) : un échec qui disparaît est une collision à expliquer, un échec qui persiste est un constat. Un test ignoré parce qu'un outil manque sur ce poste (Typst, PySide6, Excel) est lui-même un constat, puisque ces outils y sont installés.
2. **Dans le bac à sable** : `python -u calc/export_all.py --project <bac à sable>/projet/Musterprojekt.woodcore`. Relever chaque avertissement. Relancer une seconde fois : les fichiers de `data/` doivent être identiques octet pour octet entre les deux exécutions (comparer les hachages). Comparer ensuite `data/` du bac à sable avec `data/` de l'arbre réel : une différence signifie que l'export commité n'est pas à jour avec ses sources, ce qui est un constat.
3. **Dans le bac à sable** : compiler le rapport, avec `--root` pointant sur `projet/Statischer Bericht (typst)/`, vers des PDF du bac à sable, dans ces six configurations : tel qu'écrit ; `--input lang=de|fr|en` × `--input uniform=3` ; `--input uniform=1` et `--input uniform=2` en allemand. Relever **chaque avertissement Typst** (stderr), qui est un constat, et la durée de chaque compilation.
4. Relever les durées de l'export, de la suite de tests et des compilations, et les comparer au dernier audit. Une dérive de plus de 30 % est un constat de classe C.
5. Lire `%LOCALAPPDATA%\Woodcore\stalls.log` (`typst-katalog\stalls.log` jusqu'à la v0.83). Chaque entrée postérieure au dernier audit est résumée : pile Python, « System hitch » ou blocage dans Qt.

Si la phase 1 révèle un pipeline cassé (l'export échoue, ou le rapport ne compile pas), le noter en tête du rapport. Les phases qui en dépendent sont alors menées sur le dernier commit qui compile, extrait dans le bac à sable.

---

## Phase 2 — Les calculs contre les classeurs de référence vérifiés

**But** : chaque valeur calculée par Python, puis imprimée par Typst, est identique à celle du classeur d'entreprise vérifié qui fait le même calcul, sur un large éventail de cas et pas seulement sur l'exemple du classeur.

Classeurs de référence : `ExternalFiles/201-excelTools/` (modèles `.xltx`/`.xltm`, versionnés dans leur nom de fichier), et `Musterprojekt/Verbindung.xlsm`, qui sert déjà d'oracle à `tests/test_dowel.py`.

### 2.1 Inventaire et correspondance **[toujours]**

1. Lister chaque modèle avec sa version (tirée du nom de fichier) et ses feuilles. Comparer avec la liste du dernier audit : un **nouveau modèle**, ou une **version qui a changé**, se note. Il faut alors lire la feuille de journal du classeur (`Änderungsjournal`, `VERSIONEN INDEX`, `Versions Index`) et dire si le changement touche un calcul que le projet reproduit, auquel cas l'oracle de test est peut-être périmé.
2. Reconstruire la table de correspondance **à partir du code actuel** (grep des modules de `calc/domains/` et des commandes de `lib/`), sans supposer qu'elle est restée la même. Au 16.09.2026, elle se présentait ainsi :

| Classeur | Feuilles | Module Python | Commande Typst |
|---|---|---|---|
| `«dowel connections» template` et `Verbindung.xlsm` | `Stabdübel (Holz-Holz)`, `Stabdübel (Stahl-Holz)`, `Daten` | `domains/dowel.py`, `domains/connector.py`, `norms/sia265*` | `show-connector-resistance`, `show-calc("connector", …)` |
| `«rigid connection» template` | `Biegesteifer Anschluss` | `domains/connection.py` (`fastener_forces`) | `show-polar-moment` (qui calcule **en Typst**) |
| `«R_k to R_d» template` | `Berechnung` | **aucun** : ce classeur applique les γ_M 1,3/1,15 et le η_mod de SIA 265/1, que rien ne lit (`sia265.gamma_m()` n'est appelé que par les tests ; constat AUD-2-9 de l'audit 260916) | — |
| `«load workbook» template` | `Schnee`, `Wind`, `Flachdach`, `Steildach`, `Innenwand`, `Aussenwand`, `Decke Innen-Innen`, `Material (hier ergänzen)`, `Dropdowns` | `domains/snow.py`, `wind.py`, `dead_load.py` | `show-calc("snow-load" / "wind-load" / "dead-load", …)` |
| Tous les autres (clous, agrafes, vis, feu, stabilité, Brettsperrholz, séisme, …) | — | **aucun** à ce jour | — |

3. Un modèle sans module Python correspondant est noté « non couvert » (classe C), sans plus. Si un module est apparu depuis le dernier audit (par exemple `nail.py`, ou le bouton *Vis* activé dans l'onglet Connecteurs), il entre dans la comparaison ci-dessous.
4. **Noms des feuilles de charges : comportement voulu, pas un constat.** Le modèle `Belastungsannahmen_*` nomme ses feuilles `Schnee`, `Wind`, `Flachdach`, etc. Dans un projet, l'ingénieur les **renomme toujours** au préfixe que lit `registry.py` (`SL-…`, `WL-…`, `EL+AL-…`). Pour les comparaisons de la phase 2, renommer de la même façon les feuilles de la copie du modèle dans le bac à sable. Ne pas signaler cet écart de noms. Si un jour le code se met à lire les noms du modèle (l'ingénieur l'envisage), adapter ce point au comportement du code.

### 2.2 Niveau A — l'exemple enregistré dans chaque classeur

Pour chaque classeur couvert : lire avec openpyxl (`data_only=True`, **sur une copie**) toutes les entrées et toutes les cellules de résultat, y compris les **intermédiaires** (f_h,α,k, k_red, M_u,k, β_f, t_1,1, k_β, p·k_β, R_d,Verb, R_d, n_tot, a_min ; pour la charge de neige h_ref, s_k, μ, q_k ; pour les charges permanentes chaque couche puis g_k et a_k ; pour le moment polaire I_p, F_Ed,max, l'angle et le numéro du connecteur déterminant). Construire l'entrée Python équivalente **dans le bac à sable** : source `connectors/<id>.json`, source `connections/<id>.json` avec son schéma `details/<id>.json`, ou copie de classeur de charges aux feuilles renommées au préfixe attendu par `registry.py`. Lancer l'export du bac à sable, puis comparer **chaque intermédiaire**, pas seulement le résultat final.

- Tolérance : écart relatif ≤ 1·10⁻⁶. Au-delà, il y a constat.
- **Conventions de signe** : le classeur `Biegesteifer Anschluss` n'a pas le repère du projet. Il utilise y vertical et un M positif dans le sens horaire, alors que le projet (§3.3quinquies) utilise x à droite, z vers le bas, et un M positif dans le sens antihoraire sur le dessin. Établir la conversion sur trois cas élémentaires (F_x seul, F_y seul, M seul) **avant** tout balayage, et l'écrire dans le rapport.
- **Écarts connus et acceptés**, qui ne sont pas des constats tant qu'ils restent les seuls. Vérifier qu'ils le sont toujours :
  - t₂,ᵢ en *Holz-Holz einschnittig* : le classeur prend la parenthèse de la pièce 1, alors que la norme (éq. (125)) prend celle de la pièce 2 ;
  - k_red = 1 pour n = 1 (Tabelle 21), là où la feuille Holz-Holz du classeur ne le protège pas ;
  - les conditions des éq. (130)/(131), que le classeur n'impose que par la validation de données de sa cellule C20 (0,35 ≤ t₁/t₂ ≤ 0,5), contournée par une valeur tapée par-dessus (AUD-2-5 de l'audit 260916) ;
  - η_w issu de la classe d'humidité des positions et non de la classe 1 du classeur ;
  - K_ser,Verb avec η_w de rigidité (SIA 265 3.2.1.3, Tabelle 25 « für Feuchteklasse 1 ») : le **modèle** 1.62 ne l'applique pas (C62, C66 ; AUD-2-3), `Verbindung.xlsm` l'applique depuis le 17.09.2026 et doit concorder avec Python ; le responsable du modèle est prévenu (`000-Audits/260917-hinweis-vorlage-stabduebel-kser.md`) ;
  - dans le classeur `Biegesteifer Anschluss` 1.0, l'angle force-fil de C50 pour α ≠ 0 (valeur absolue, AUD-2-4) et le `#DIV/0!` d'un groupe à une seule file (AUD-2-10) : défauts du classeur, signalés à son responsable (`000-Audits/260917-hinweis-vorlage-biegesteifer-anschluss.md`), à exclure des comparaisons.

  Ces écarts sont décrits au §3.3nonies. Un **nouvel** écart se tranche contre la norme (règle 8), sans jamais s'aligner d'office sur Excel ni sur Python.

### 2.3 Niveau B — balayage de cas recalculés par Excel

L'exemple du classeur ne teste qu'un seul point. Pour chaque classeur couvert, construire **au moins 25 cas** qui couvrent le domaine et ses bords, puis faire recalculer Excel lui-même :

1. Piloter Excel par COM, depuis PowerShell, ou avec `win32com` s'il est déjà installé (**ne pas installer de nouvelle dépendance**). Ouvrir une instance **dédiée** (`New-Object -ComObject Excel.Application`) avec `Visible = $false`, `DisplayAlerts = $false`, `EnableEvents = $false` et `AutomationSecurity = 3` (macros désactivées). Ouvrir le classeur avec `Workbooks.Add(<copie du modèle dans le bac à sable>)`, écrire les entrées (`Range.Value2`), appeler `Application.CalculateFull()`, lire les sorties, puis fermer **sans enregistrer**. Terminer par `Quit()` dans un bloc `finally`, et ne tuer que le PID de **cette** instance, jamais tous les `EXCEL.EXE` (l'ingénieur peut avoir Excel ouvert).
2. Les entrées se trouvent par leur **libellé** (colonne voisine), jamais par une adresse supposée. Si une liste déroulante refuse une valeur, le noter et passer au cas suivant.
3. Cas à couvrir, au minimum :
   - **Stabdübel** : classes C24, GL24h, GL28h, GL32h et D30 (feuillu) ; d de 8 à 16 ; α = 0°, 30°, 60° et 90° ; avec et sans prépercage (feuillu non prépercé : refus attendu) ; classes d'humidité 1, 2 et 3 ; einschnittig, zweischnittig, Stahl-Holz avec tôle en fente et avec tôles extérieures ; n de 1 à 6 ; a₁ de 5d à 10d ; β_f ≠ 1 (deux essences ou deux angles différents) ; t₂ < 2·t₁ et t₁ < 0,35·t₂ ; séisme ; nœud de treillis.
   - **Moment polaire** : groupes 1×n, 2×2, 3×4 et 4×3 ; efforts F_x seul, F_y seul, M seul, puis les trois ensemble avec des signes mélangés ; α ≠ 0.
   - **Charges permanentes** : chaque feuille de couches du modèle, avec une couche en kg/m² et une en kg/m³, et un matériau présent sous deux `Ebene`.
   - **Neige** : chaque modèle de charge de la liste déroulante, au moins deux altitudes de part et d'autre du plancher de 0,9 kN/m², et avec et sans *Abgleiten*.
4. Comparer Excel et Python sur chaque intermédiaire, avec la tolérance du §2.2. Rapporter, pour chaque classeur, le nombre de cas conformes, le nombre de cas en écart et la table des écarts (entrées, grandeur, Excel, Python, écart relatif, verdict tiré de la norme).
5. Si un contrôle de ce niveau est stable et rapide, le **proposer comme test** dans `tests/`, sous la forme d'une table de cas figés avec les valeurs Excel en dur et le nom du classeur et de sa version en docstring. C'est ainsi qu'un audit se transforme en garde permanente (§11ter).

### 2.4 Niveau C — ce que Typst imprime

1. **Dans le bac à sable**, placer les sources de 5 à 10 cas du §2.3 (y compris un cas refusé et un cas sous les espacements minimaux), puis lancer l'export. Écrire une sonde `projet/Statischer Bericht (typst)/.probe-audit/<pid>/probe.typ` qui importe `/commands.typ` **par un chemin absolu**. Pour chaque cas, elle appelle `show-connector-resistance(id, level: 3)`, `show-polar-moment(id, N:, V:, M:, level: 3)` et `show-calc(domain, instance, level: 3)`.
2. Compiler la sonde dans le bac à sable, extraire le texte avec `pypdf` et vérifier que chaque résultat (R_d, R_d,Verb, F_max, q_k, g_k, …) apparaît avec la valeur **formatée comme le fait `fmt-decimals`** (au plus 3 décimales, zéros finaux supprimés). Pour `show-polar-moment`, dont le calcul se fait en Typst, comparer la force F_max imprimée à `connection.fastener_forces()` et à Excel.
3. Vérifier qu'un cas refusé imprime la **raison** du refus, et non un nombre.
4. **Valeurs normatives [toujours, par échantillon]** : tirer au hasard 10 valeurs parmi les fichiers de `calc/norms/*.json`, avec la date du jour comme graine pour que les audits successifs couvrent tout. Retrouver chacune dans le PDF de la norme cité (texte extrait avec pypdf à la page indiquée, ou rendu de la page en image quand le tableau est un graphique) et rapporter : conforme, écart, ou page introuvable.

---

## Phase 3 — Traductions du rapport Typst (fr, de, en)

**But** : tout ce que le moteur **compose** apparaît dans la langue du rapport, et rien de ce que l'ingénieur écrit n'est traduit (§4bis). La règle de tri est celle du §4bis : **une chaîne est un mot du moteur si le glossaire la porte, ou si le moteur ou la norme la compose ; elle appartient à l'ingénieur si seul le classeur ou `Sections/` la nomme**. Ne pas signaler comme défaut un nom de matériau, un nom de feuille, « Flachdach », « Ja », un titre de section ou la prose de `Sections/`.

1. **Dans le glossaire** [toujours] : les tests `test_i18n` sont nécessaires mais pas suffisants. En plus :
   - chaque `t-str("clé")`, `t("clé")` et `t-label`/`t-pattern` de `lib/*.typ`, et chaque `strings.text()`/`template()` de `calc/`, désigne une clé qui existe ;
   - chaque clé de `engine`, chaque modèle (`templates`) et chaque terme (`terms`) est **utilisé** quelque part, ou correspond à une chaîne réellement présente dans l'export. Les orphelins sont des restes de fonctionnalités supprimées : les lister ;
   - les passages `$…$` sont les mêmes dans les trois langues, pour chaque entrée ;
   - un terme ajouté depuis le dernier audit indique sa source (édition et page de la norme) ou est marqué comme traduction libre (§4bis).
2. **Dans les littéraux de `lib/*.typ`** : repérer toute chaîne ou tout contenu en crochets contenant des mots allemands, français ou anglais imprimés sans passer par `t`/`tl`/`t-str`/`tl-str` (par exemple `[Massgebend]`, `"mit "`, `"Verbindungsmittel"`). Exclure les messages d'erreur (`panic`/`assert`, qui restent en anglais, §4bis) et les noms de commandes.
3. **Dans l'export** : parcourir tous les champs texte de `data/*.json` (`label`, `name`, `title`, `note`, `group_label`, `description`, `desc`, les libellés de colonnes, les notes de figures, la légende des plans) et les classer en trois catégories : traduit par le glossaire (terme ou modèle reconnu), valeur de l'ingénieur (vient d'une cellule de classeur que seul le classeur nomme), ou **mot du moteur sans traduction**, qui est un constat.
4. **Dans les PDF** : prendre les trois compilations `uniform=3` de la phase 1 (fr, de, en) et extraire le texte page par page. Dans les PDF **fr** et **en**, chercher chaque clé allemande du glossaire (termes, parties littérales des modèles, valeurs `de` de `engine`) : toute occurrence hors prose de l'ingénieur est un défaut de traduction. Chercher de même les valeurs **fr** dans le PDF en et les valeurs **en** dans le PDF fr (fuite d'une langue dans l'autre).
5. **Dans les figures dessinées par Python** : extraire le contenu des `<text>` des SVG `data/connections/*-{de,fr,en}.svg`, `data/statics/*-{…}.svg`, `data/connectors/*-pattern-{…}.svg` et `data/schemas/*-{…}.svg`. Dans les versions fr et en, aucun mot allemand du glossaire ne doit apparaître. Les figures déclarées sans mots (`*-section.svg`, `*-kbeta-*.svg`) ne doivent contenir que des symboles, des nombres et des unités.
6. **Contrôle visuel par échantillon** : rendre en PNG (`typst compile --format png --pages …`, dans le bac à sable) une page par section du rapport, en fr et en en, et **regarder** chaque image. Chercher un texte français plus long qui déborde d'une figure, d'un tableau ou de la colonne de citation, et une ligne restée en allemand qui aurait échappé aux contrôles textuels.

---

## Phase 4 — Traductions de la fenêtre de Woodcore (fr, de, en)

**But** : **tout** ce que la fenêtre affiche d'elle-même est traduit dans les trois langues : libellés, boutons, infobulles, menus, en-têtes de tableaux, textes d'aide, messages de la barre d'état, boîtes de dialogue, textes de substitution (placeholders) et avertissements. Les valeurs issues des données (identifiants, libellés allemands de l'export, nombres, unités, symboles) restent telles quelles, comme le prévoit le §10quater, et ne sont pas des constats.

1. **Analyse statique** [toujours] :
   - Dans `calc/tools/*.py`, relever tout littéral de texte passé à un widget ou à une boîte de dialogue sans passer par `self.t(...)`/`STRINGS` : `QLabel("…")`, `QPushButton("…")`, `setText`, `setToolTip`, `setStatusTip`, `setPlaceholderText`, `setWindowTitle`, `setTitle`, `addItem`/`addItems`, `QAction("…")`, `addMenu`, `setHorizontalHeaderLabels`, `showMessage`, `QMessageBox.*(…, "…", "…")`, `QInputDialog.getText(…, "…")`, et les f-strings contenant des mots. Chaque occurrence est classée comme légitime (symbole, unité, nom du produit « Woodcore ») ou comme défaut.
   - Relever aussi les messages de `schema.Refused`, les avertissements des domaines et les exceptions **affichés à l'utilisateur** sans passer par un code traduit (§3.3decies : `code`/`detail` ; depuis v0.79, `engine.Note` et `woodcore_gui.note_text` pour les avertissements).
   - Relever chaque clé de `STRINGS` **jamais lue**. Attention aux clés composées dynamiquement (`f"tool_{name}"`) : reconstituer ces familles avant de conclure.
   - Relever les **incohérences terminologiques** : un même terme allemand du rapport (par exemple « Stabdübel ») traduit différemment dans `strings.json` et dans `STRINGS` (« broche », « tige »…).
2. **Récolte dynamique**, dans le bac à sable, en sous-processus hors écran avec tous les dialogues bouchonnés. Ouvrir `MainWindow()`, puis pour chaque langue fr, de et en (en changeant la langue par le mécanisme de la fenêtre elle-même) et pour chaque onglet :
   - parcourir les **états** qui changent l'interface : premier et dernier élément de chaque liste, chaque outil de chaque barre d'outils, chaque type de sélection (point, barre, charge, cote dans Modèles statiques ; élément, marqueur, aide, cote dans Schémas), chaque assemblage de l'onglet Connecteurs (y compris les assemblages désactivés), chaque menu des boutons à menu *Importer Excel*/*Exporter PDF*, chaque menu contextuel des listes à dossiers, un élément archivé, et un onglet sans aucune source (bac à sable vidé) ;
   - dans chaque état, collecter par `findChildren` le texte visible et l'infobulle de tous les `QLabel`, `QAbstractButton`, `QGroupBox`, `QTabBar`, `QComboBox` (éléments), `QLineEdit`/`QTextEdit` (placeholder), en-têtes de `QTableWidget`/`QTreeWidget`, `QAction` et `QMenu`, ainsi que le titre de la fenêtre et la barre d'état ;
   - bouchonner `QMessageBox`, `QInputDialog` et `QFileDialog` pour **enregistrer** leur titre et leur texte, puis déclencher les chemins d'erreur courants : enregistrer avec un identifiant déjà pris, supprimer, cliquer un outil STE sans position disponible, quitter une source modifiée.
3. **Analyse de la récolte** :
   - un texte **identique dans les trois langues**, de plus d'un mot, qui n'est ni une donnée, ni un identifiant, ni un symbole, ni une unité, est un défaut de traduction ;
   - un texte d'une langue apparaissant dans la fenêtre d'une autre (mots propres à `STRINGS["fr"]` dans la fenêtre de ou en, et inversement) est un défaut ;
   - un texte vide ou une clé brute affichée (`cn_…`, `sc_…`, `ref_…`) est un défaut.
4. Mettre en regard la liste « à corriger » et les mots de `test_i18n.SAME_IN_TWO_LANGUAGES` : une exception ajoutée sans justification visible est à revoir.
5. **Captures d'écran** : pour chaque onglet et chaque langue, enregistrer `window.grab()` en PNG dans le bac à sable et regarder chaque image, pour repérer un libellé tronqué ou élidé (*Axe ...ical*) ou un texte qui déborde.

---

## Phase 5 — Chaque bouton de Woodcore fonctionne et fait ce qu'il annonce

**But** : aucun bouton, action de menu ou outil n'est mort, ne lève d'exception ou n'agit sans effet vérifiable. `tests/test_editor_buttons.py` ne clique que les boutons des listes des cinq éditeurs. Cette phase couvre **tout le reste**.

1. **Inventaire** : ouvrir `MainWindow()` dans le bac à sable, hors écran. Pour chaque onglet (plans, charges, combinaisons, modèles statiques, schémas, connecteurs, moments polaires, commandes), la barre du haut, **le menu *Fichier*** et **la page d'accueil** (`home_page.HomeWindow`, ouverte à part avec une liste de projets récents du bac à sable, dont un introuvable ; v0.83), lister chaque `QAbstractButton`, chaque `QAction` (menus, menus contextuels, boutons à menu) et chaque outil de canvas. Pour chacun, noter l'onglet, le texte fr, la classe, l'état activé ou désactivé et **le nombre de récepteurs connectés** (`receivers(SIGNAL("clicked()"))` ou `receivers(SIGNAL("triggered()"))`). Un élément actif sans aucun récepteur, qui n'appartient pas à un groupe exclusif et n'ouvre pas de menu, est un **bouton mort**. Un élément désactivé doit avoir une infobulle qui explique pourquoi (règle v0.47).
2. **Clic et effet attendu** : remplacer `woodcore_gui.install_error_box` par un enregistreur d'exceptions, bouchonner tous les dialogues (une question de confirmation répond « Oui » ; une question « enregistrer, ignorer ou annuler » répond « Ignorer »), `os.startfile` et `QDesktopServices.openUrl`. Cliquer chaque élément dans un état où il est actif, puis **vérifier l'effet**, pas seulement l'absence d'exception :

| Famille | Effet vérifié |
|---|---|
| Nouveau | la liste compte une entrée de plus ; la fiche est marquée modifiée (point) ; l'identifiant proposé est libre |
| Enregistrer | `<dossier>/<id>.json` existe dans le bac à sable et passe `check_source` ; l'export du domaine a tourné (`data/…` mis à jour) ; le point de modification disparaît |
| Dupliquer | nouvel identifiant, contenu identique à l'original sauf l'identité |
| Supprimer | la source est déplacée dans `<dossier>/archives/` ; sa figure disparaît de `data/` après export ; restaurer la fait revenir |
| Annuler les modifications | la fiche égale de nouveau le fichier |
| Annuler / Rétablir (canvas) | la pile d'annulation change d'une étape ; une modification refusée ne laisse aucune étape |
| Outils de canvas | `canvas.tool` change ; le texte d'aide change ; un clic simulé par l'API `place()` produit une entrée valide pour `check_source` |
| Trancher / Fusionner / Grille… | l'effet géométrique attendu (§3.3decies), ou un refus avec un message traduit |
| Ajuster | la transformation de la vue change et la figure est entièrement visible |
| Copier (chaque appel proposé) | le presse-papiers contient l'appel, **et cet appel compile** dans le bac à sable (§2.4, sonde) |
| Importer Excel | le processus d'export se termine avec le code 0 dans le bac à sable |
| Exporter PDF (chaque réglage du menu) | `Statischer Rapport.pdf` du **bac à sable** est produit ; les arguments `--input` passés correspondent au réglage ; `_Archiv/` du bac à sable reçoit l'archive (un zip et le PDF) |
| Ouvrir le classeur, ouvrir le PDF | l'appel bouchonné reçoit le bon chemin |
| Nouveau dossier, renommer, glisser vers un dossier | le champ `group` de la source est écrit ; le dossier vide survit à une reconstruction de la liste et est écrit dans les réglages du bac à sable |
| Langue | toutes les fiches ouvertes survivent au changement, y compris les modifications non enregistrées |
| Onglet Commandes | chaque flèche ouvre une page d'exemple (PNG figé) ; le sélecteur de niveau 1·2·3 est désactivé lorsqu'un exemple fixe son niveau |

3. **Appels copiés, en masse** [toujours] : collecter **tous** les appels que la fenêtre de Woodcore propose à la copie, dans tous les onglets et pour chaque élément (onglet charges : chaque variable et chaque cas ; les autres onglets : l'élément sélectionné ; onglet commandes : appel complet et minimal de chaque commande). Les compiler dans le bac à sable : une sonde par onglet pour les appels sans effet global, et **un document par appel** pour ceux qui contiennent `#var`, `#unit`, `#var-unit` ou `#var-domain` (§10sexies). Chaque appel qui ne compile pas est un constat.
4. **Ce qui ne s'automatise pas hors écran** (survol, glisser-déposer à la souris, poignées, zoom à la molette, rendu réel des PDF d'architecte) : le noter comme tel et l'ajouter à la **liste de vérification manuelle** du rapport, formulée en étapes courtes que l'ingénieur peut suivre en moins de dix minutes.
5. Chaque bouton cassé trouvé ici reçoit un test de non-régression (classe A, phase 9), en étendant `test_editor_buttons.py` ou dans un fichier par onglet.

---

## Phase 6 — Anciennes commandes, code mort, données en double

**But** : ce qui a été renommé ou supprimé a disparu **partout**, et chaque donnée n'a qu'une seule source (§2 règle 1).

### 6.1 Anciennes commandes et restes [toujours]

1. Extraire de `CHANGELOG.md` et de `docs/` chaque identifiant annoncé comme **renommé, supprimé, remplacé ou retiré** (« named … until », « gone », « removed », « deleted », « replaced by », « no alias », « was … until »). Exemples connus : `show-fastener-forces`, `show-fastener-polar-moment`, `show-position-summary`, `verdict`, `test` (la commande), `linked-connector`, `sia261_tables`, `calc/connectors.py`, `width` d'un élément de schéma, `variant` et `connector` d'une connexion, `Positions Connectors`, `IMPORT_NAMES`, `ENGINE_IMPORT_PATH`, `Réexporter depuis Excel`, `show-position` (remplacé par `#member(id, level: 1)`), `schema.parse_section`.
2. Chercher chacun dans tout l'arbre **hors** `CHANGELOG.md`, `ExternalFiles/`, `_Archiv/` et `.git/` : `lib/`, `Sections/`, `commands.typ`, `calc/`, `tests/`, `examples/` (fences et `.typ` générés), `docs/typst-reference.xlsx` (régénérer dans le bac à sable puis chercher), `strings.json`, les `STRINGS` de la fenêtre de Woodcore, `README.md`, `CLAUDE.md`, `docs/` (hors `docs/history/` et passages historiques explicitement datés), `calc/cli.py` et les `.bat`. Chaque occurrence vivante est un constat.
3. Vérifier la cohérence des listes qui doivent se correspondre :
   - `build_reference.CATEGORIES` avec les `#let` de `lib/` (`test_commands` le fait ; vérifier qu'il passe) ;
   - la table des fonctions du §10bis avec les **signatures réelles** des `#let` : nom, ordre des paramètres positionnels, paramètres nommés et valeurs par défaut. Script à écrire dans le bac à sable ;
   - `TABS` de `woodcore_gui.py` avec la description des onglets du §10quater ;
   - les appels `call_*` de `build_reference.py` avec les signatures de `lib/`.
4. `Sections/*.typ` : chaque appel utilise la signature actuelle, et aucun nombre saisi à la main n'égale une valeur disponible dans `data/`, qui devrait alors être lue par `var-of`/`value-of`.
   **Exceptions acceptées par l'ingénieur (décisions de l'audit 260916), à ne pas signaler à nouveau :**
   - `Sections/005` écrit η_w et γ_M/η_M à la main : η_w vient de SIA 265 Tableau 4 et SIA 265/1 pour les matériaux dérivés du bois, γ_M/η_M de SIA 265 Tableau 1 et SIA 265/1 ; « ce calcul ne changera pas » (B6) ;
   - `Sections/004` nomme ses cas à la main, chacun à son niveau (B4) : ne signaler qu'une instance exportée **nouvelle** qui n'y est pas nommée (`EL+AL-Wand` ne l'est pas, par choix, au 17.09.2026) ;
   - les exemples figés citent `SD_02`, `SD_01-8mm`, `SD_02-10mm` et `Beispiel`, que le projet n'a plus : les deux tests `test_commands` correspondants restent rouges jusqu'à ce que l'ingénieur re-fige (B25) ;
   - une `ValidationError` affichée par la fenêtre reste en anglais : elle décrit un défaut de fichier (B22) ; les avertissements des domaines, eux, passent par `engine.Note` et doivent être traduits.

### 6.2 Code et fichiers morts

1. Dans `calc/` : une analyse `ast` (bibliothèque standard) liste chaque fonction, classe et constante de module **jamais référencée** ailleurs que dans sa définition (chercher le nom dans `calc/`, `tests/`, `lib/` et les fichiers `.bat`/`.ps1`). Chaque candidat est vérifié à la main (points d'entrée `main()`, connexions de signaux Qt par nom, `getattr` dynamique) avant d'être signalé. Les 21 définitions listées dans `000-Audits/260917-code-mort.md` sont gardées à la demande de l'ingénieur, en attente de sa décision : ne signaler que les écarts à cette liste (une définition ajoutée, ou une qui a retrouvé un appelant).
2. Dans `lib/*.typ` : chaque `#let` interne (hors catégories publiques) qui n'est appelé par aucun autre `#let`, par aucune section et par aucun exemple.
3. Fichiers générés orphelins : dans `data/`, toute figure ou tout enregistrement qui ne correspond plus à une source (comparer avec l'export du bac à sable de la phase 1) ; dans `examples/`, les `.typ` et `.png` sans fence correspondante ; dans `calc/norms/`, les fichiers non lus (`test_norms` le fait) ; dans `schemas/`, les contrats que `validation.py` n'utilise pas.
4. Outils ponctuels (`migrate_*.py`) : encore nécessaires ? Si un outil est documenté comme ponctuel et que ses entrées n'existent plus, en faire un constat de classe B (suppression à décider).
5. Hygiène git : fichiers générés ou caches suivis par git alors qu'ils devraient être ignorés (`__pycache__`, `.render-cache`, `.preview`, `tests/.tmp`, `examples/lib`), fichiers de plus de 5 Mo ajoutés depuis le dernier audit, `.gitignore` incohérent avec le §11.
6. `Positionen.xlsx` (lecture seule, sur une copie) : une feuille retirée (`Positions Connectors`, `data_connector`, `data_assembly`, `data_steel`) encore présente, ou une colonne que plus rien ne lit, donne un constat de classe B pour l'ingénieur.

### 6.3 Données et valeurs en double

1. **Valeurs normatives réécrites** : pour chaque nombre des fichiers `calc/norms/*.json` (hors 0, 1, 2 et 10), chercher le même littéral dans `calc/**/*.py`, `lib/*.typ` et `Sections/*.typ`, puis confirmer à la main s'il s'agit de la même grandeur. Une valeur normative écrite deux fois est un constat de classe A (§11, v0.77).
2. **Listes répétées** : langues (`strings.py`, `woodcore_gui.LANGUAGES`, `i18n.typ`), types de connecteurs, classes d'humidité, espèces, largeurs et couleurs reproduites entre Python et Typst (`ACTION_WIDTH`, `action-width`…), chemins du livrable (`calc/cli.py`, `project.Project.report_typ`/`report_pdf`, le `.vscode/settings.json` d'un projet). Chaque copie doit être gardée par un test (`test_constants`, `test_pdf_button`, `test_arrows`) ; une copie **sans test** est un constat.
3. **Fichiers identiques** : hacher les sources de `details/`, `connectors/`, `connections/`, `statics/` et `plans/`, puis signaler deux sources dont le contenu géométrique est identique à l'identité près (par exemple deux schémas qui dessinent le même assemblage, ce que v0.74 voulait éviter).
4. **`examples/lib/`** comparé à `lib/` (`test_commands` le fait), et `docs/typst-reference.xlsx` comparé à sa régénération dans le bac à sable : s'ils diffèrent, le fichier commité est périmé.
5. **Deux glossaires** : une même chaîne allemande présente dans `strings.json` **et** dans un `STRINGS` avec des traductions différentes est un constat (classe B si la terminologie est à choisir).

---

## Phase 7 — Comprendre le projet et le confronter à sa documentation (`docs/`)

**But** : chaque affirmation vérifiable de `CLAUDE.md`, de `docs/` et de `README.md` est vraie dans le code actuel, et chaque comportement important du code est décrit. Avec `AGENTS = oui`, répartir les fichiers de `docs/` entre plusieurs agents (par exemple `docs/architecture/` + `docs/project/`, `docs/domain/`, `docs/typst/`, `docs/ui/`, `docs/conventions/` + `docs/decisions.md` + `docs/open-questions.md`). Chaque agent lit sa part **et le code qu'elle décrit**.

1. **Contrôle mécanique** [toujours], par un script du bac à sable :
   - chaque chemin cité (`calc/domains/x.py`, `schemas/y.schema.json`, `tests/test_z.py`, `lib/…`) existe ;
   - chaque symbole cité entre accents graves (fonction, constante, clé JSON, commande Typst) existe là où le texte le situe ;
   - chaque `schema_version` cité est celui des contrats `schemas/*.schema.json` et des fichiers `data/*.json` ;
   - chaque constante citée avec sa valeur (`MIN_MEMBERS`, `MAX_MEMBERS`, `SHARE_SHOWN`, `CHOSEN_TOLERANCE`, `STALL_S`, `BASE_RENDER_PX`, seuil 99 999, `MIN_WORDS`…) a cette valeur dans le code ;
   - l'arbre du §11 correspond au système de fichiers : fichiers décrits mais absents, et fichiers présents mais non décrits (par exemple `dependencies.py`, `source_archive.py`, `archive_export.py`) ;
   - la table des tests du §11ter et celle de `tests/README.md` correspondent à `tests/test_*.py`. La table du README est connue pour être très incomplète : la mettre à jour ;
   - les options de `woodcore-cli` (`calc/cli.py`) correspondent au §12 ;
   - les **nombres** cités (« 202 noms », « 167 pages », « 53 PDF de normes », « 89 des 90 valeurs »…) sont recomptés. Un compte faux se corrige ou se reformule sans nombre.
2. **Contrôle par lecture** : pour chaque section, lire le code qu'elle décrit et relever chaque **contradiction** de comportement (ce qui est calculé, validé, bloquant ou simple avertissement, niveau d'affichage, ordre d'impression, règles de refus). Prioriser les modules modifiés depuis le dernier audit (liste du §0.1).
3. **§13 et §14** :
   - une décision du §13 que le code contredit est un constat de classe B, car c'est soit le code, soit la décision qui doit changer, et c'est à l'ingénieur de choisir ;
   - un point « encore ouvert » du §14 déjà réalisé dans le code est un constat de classe A : le déplacer ou le barrer, en citant la version ;
   - un comportement nouveau du code absent du §13 et du §14, alors qu'il tranche une question, est un constat de classe B.
4. **Journal** : la dernière entrée de `CHANGELOG.md` décrit la version courante, chaque spécification de `docs/requirements/completed/` a été vérifiée, et le travail non commité visible dans `git status` a une entrée dans le journal.
5. **README.md** : ne contredit ni `docs/` ni le code (commandes de build, prérequis, arborescence).

---

## Phase 8 — Robustesse **[toujours, dans le bac à sable]**

1. **Projet vide** : bac à sable sans aucune source dans `connectors/`, `connections/`, `details/`, `statics/` et `plans/`. L'export réussit, le rapport compile et la fenêtre de Woodcore s'ouvre sur chaque onglet sans exception.
2. **Références cassées** : renommer une position dans la copie de `Positionen.xlsx`, supprimer un schéma nommé par un connecteur et supprimer un marqueur. Chaque cas donne des **avertissements** et jamais un arrêt (règle v0.33), et le rapport refuse d'imprimer ce qui est cassé avec un message qui dit quoi faire.
3. **Classeur non recalculé** : une copie de classeur de charges où une cellule de formule a perdu sa valeur en cache doit donner une erreur bloquante qui nomme la cellule.
4. **Idempotence** : Enregistrer deux fois de suite une source inchangée ne modifie aucun octet de `data/`.
5. **Performance** : ouverture de la fenêtre de Woodcore jusqu'à la première peinture, changement d'onglet, changement de plan (premier affichage puis affichage depuis le cache), et export seul d'un connecteur. Comparer au dernier audit.

---

## Phase 9 — Corrections

Chaque constat reçoit une classe :

- **A — corriger maintenant** : le défaut est local, la correction évidente et sans conséquence sur un calcul ou une décision. Exemples : traduction manquante d'un texte de l'interface ou d'un mot du moteur dont la source est connue, référence résiduelle à une commande supprimée, bouton mort dont l'intention est claire, test ou table de README périmé, dérive documentaire de `docs/` (chemin, constante, compte, signature, point du §14 déjà réalisé), valeur normative écrite en double dans le code.
- **B — décision de l'ingénieur** : écart de calcul avec Excel non expliqué par la norme ou tranché contre le classeur ; changement du modèle d'entreprise ; décision du §13 contredite ; suppression d'un outil, d'une feuille ou d'un fichier source ; changement de terminologie ; tout ce qui modifie un nombre imprimé ; toute montée de `schema_version`.
- **C — information** : non couvert, dérive de performance, point de vigilance.

Si `CORRECTIONS = A`, la session principale (jamais les agents, pour éviter les collisions) applique les corrections de classe A **une par une** :

1. Prévenir les sessions pairs (règle 5) et relire le fichier juste avant de le modifier.
2. Faire une modification ciblée (Edit), en conservant les fins de ligne du fichier et en respectant le §1ter (un paragraphe par ligne).
3. Pour tout défaut de code, **ajouter un test de non-régression** dans `tests/`, qui échoue sans la correction (le vérifier en réintroduisant le défaut) et dont la docstring cite le défaut et la date de l'audit (§11ter).
4. Relancer seuls les tests concernés.
5. À la fin, relancer **toute** la suite, seule. Si elle régresse, annuler la correction fautive (fichier par fichier) plutôt que de laisser l'arbre cassé.
6. Si du code a changé : ajouter une entrée à `CHANGELOG.md` et mettre à jour les fichiers de `docs/` concernés, en convenant du numéro de version avec les sessions pairs ; sinon, pas de nouvelle version.
7. Tenir la liste exacte des fichiers modifiés, **vérifiée avec `git diff`** et non déduite de ce qui était prévu.

---

## Phase 10 — Rapport

Écrire `Woodcore/000-Audits/AAMMJJ-HHhMM-audit.md`, en français, un paragraphe par ligne. Ce dossier est **versionné** (il ne doit jamais apparaître dans `.gitignore`) : l'historique des audits est ce qui permet de comparer d'un audit à l'autre. Le rapport contient :

1. **En-tête** : date, commit, fichiers non commités au départ, portée, versions des outils et durée de chaque phase.
2. **Tableau de bord** : une ligne par phase, avec le nombre de contrôles menés, conformes, en constat A, B et C, et « non fait ».
3. **Comparaison avec le dernier audit** : constats **nouveaux**, **résolus** et **persistants**, en citant leur identifiant (`AUD-<phase>-<n>`, stable d'un audit à l'autre quand le constat est le même).
4. **Constats**, du plus grave au moins grave. Pour chacun : identifiant, classe, `fichier:ligne`, description en une phrase, **preuve** (commande exécutée et extrait de sortie, ou valeurs comparées), et soit la correction faite avec le test ajouté, soit la décision attendue de l'ingénieur avec les options.
5. **Phase 2 en détail** : pour chaque classeur, sa version, le nombre de cas comparés et la table des écarts, et la conversion de repère utilisée pour le moment polaire.
6. **Fichiers modifiés** par l'audit, tirés de `git diff --stat`.
7. **Vérification manuelle** : les étapes courtes que l'ingénieur doit faire lui-même (phase 5, point 4, et contrôles visuels douteux).
8. **Contrôles devenus tests** : ce qui a été ajouté à `tests/` pendant cet audit, et ce qui pourrait l'être la prochaine fois.

Terminer la session par un message de moins de quinze lignes : l'état général en une phrase, les constats B qui attendent une décision, les corrections faites, et le lien vers le rapport.
