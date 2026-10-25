---
id: 2026-10-24-lanceur-tests-limites
titre: Lanceur de tests — le parent tient la limite de chaque test, limites tirées des durées mesurées, plafond de la suite
status: completed
cree: 2026-10-24
mis_a_jour: 2026-10-25
source: issue GitHub #108 (la suite de tests reste bloquée : la limite par test n'est tenue que dans le processus de travail)
docs: [docs/conventions/testing.md, docs/conventions/testing-catalogue.md, .claude/skills/finish/SKILL.md, docs/architecture/principles.md, docs/decisions.md]
---

# Lanceur de tests — limites tenues par le parent — Spécification

## 1. Objectif

Qu'aucun test, ni aucun fichier de test, ne puisse retenir `python tests/run_tests.py` : le lanceur parent surveille lui-même chaque test (il lit déjà la ligne « ... test_x » que le fils écrit avant chaque test), arrête l'arbre de processus qui dépasse sa limite, et **cesse d'attendre** un processus que Windows ne laisse pas mourir. Les limites par test viennent des durées mesurées au lieu d'un 300 s uniforme, une limite de fichier ne croît plus avec le nombre de tests, et la suite entière a un plafond (le budget de 20 minutes de `finish`) au-delà duquel le lanceur nomme ce qui tourne encore et rend la main, rouge. L'ingénieur n'a plus à arrêter la suite à la main (aujourd'hui : plus d'une heure d'attente alors que 226 processus sur 227 avaient fini en 914 s).

## 2. Source

L'issue #108, par points (le constat, les quatre demandes, les critères d'acceptation, le commentaire de précision).

> **T1** — « La suite complète (`python tests/run_tests.py`) est restée **plus d'une heure** sans finir, alors que 226 processus sur 227 avaient fini en **914 s**. L'ingénieur doit régulièrement l'arrêter à la main ; ce n'est pas la première fois. »
>
> **T2** — « Le processus restant était `test_updates` : le test `test_skip_and_later_are_remembered_and_install_downloads_then_starts` s'est bloqué dans `calc/tools/update_gui.py:188` (`finished`, appelé dans la boucle Qt du test, `tests/test_updates.py:436`) ; »
>
> **T3** — « le chien de garde a bien tiré à 300 s : `faulthandler.dump_traceback_later(timeout, exit=True)` a écrit « Timeout (0:05:00)! » et la pile des deux fils (00:31) ; »
>
> **T4** — « **mais le processus n'est pas mort** : `faulthandler` appelle `_exit(1)`, qui sous Windows peut rester bloqué (un fil natif, Qt, le verrou du chargeur de DLL). Le processus vivait encore à 01:14 ; »
>
> **T5** — « le parent (`_run_once`) n'attend que `proc.wait(timeout=limit)`, avec **`limit = nombre de tests × 300 s + 300 s`** : pour les 17 tests de `test_updates`, **5400 s, soit 90 minutes**. La limite par test n'est donc tenue que dans le processus de travail, jamais par le parent. »
>
> **T6** — « 1. **Le parent tient la limite de chaque test**, pas seulement le fils : le fils annonce déjà chaque test qu'il commence (« ... test_x ») ; le parent lit cette sortie et tue l'arbre (`_kill_tree`) quand un test dépasse sa limite plus une petite marge (par ex. 30 s après le « Timeout » de `faulthandler`). Ne plus dépendre de `_exit` sous Windows. »
>
> **T7** — « 2. **Une limite par test tirée des durées mesurées** : `--times` et le dernier passage connaissent la durée de chaque test ; une limite = max(quelques secondes, k × durée mesurée), plafonnée à `--test-timeout`, arrêterait un test bloqué en secondes plutôt qu'en 5 minutes. Les durées à garder dans un fichier (par ex. `tests/.last-run.json`, qui ne garde aujourd'hui que `failed`). »
>
> **T8** — « 3. **Une limite de fichier qui ne grandit pas avec le nombre de tests** au-delà du raisonnable (aujourd'hui 90 min pour 17 tests), »
>
> **T9** — « et **un plafond pour la suite entière** (le budget de 20 minutes de `finish`) : au-delà, le lanceur s'arrête, nomme ce qui tourne encore et rend la main, rouge. »
>
> **T10** — « 4. **Le test bloqué lui-même** : `test_updates.test_skip_and_later_are_remembered_and_install_downloads_then_starts` (`update_gui.install`, `finished`, boucle `QEventLoop` avec `QTimer.singleShot(5000, loop.quit)`) — comprendre pourquoi il reste dans `finished` au-delà des 5 s de sa propre boucle. »
>
> **T11** — « Critères d'acceptation : un test qui ne rend jamais la main est arrêté et compté rouge en moins de sa limite plus 30 s, même si `_exit` se bloque ; »
>
> **T12** — « la suite complète ne dépasse jamais son plafond ; »
>
> **T13** — « un test planté pour l'essai (une boucle sans fin, un `exec()` modal) le prouve dans `tests/test_runner.py`. »
>
> **T14** — « Voir aussi l'issue #22 (« No test can hold the run »), dont ceci est le reste. »
>
> **T15** — « Précision relevée juste après : le processus de travail bloqué (`test_updates`, PID 11516) **ne se laisse même pas tuer** : `taskkill /T /F /PID 11516` répond « There is no running instance of the task », alors qu'il figure encore dans la liste des processus, enfant du lanceur. Il est coincé dans sa sortie (`_exit` de `faulthandler`), au niveau du noyau. »
>
> **T16** — « Conséquence pour la solution : tuer l'arbre ne suffit pas. Le parent doit **cesser d'attendre** ce processus : compter le test rouge, nommer le fichier et passer à la suite (ou finir), sans `proc.wait()` sans fin après `_kill_tree`. Aujourd'hui `_run_once` fait `_kill_tree(proc)` puis `proc.wait()` sans limite : ce second `wait` resterait bloqué lui aussi. »

## 3. Exigences fonctionnelles

État des lieux (lecture du code, `tests/run_tests.py`) : le fils (`run_file`) arme `faulthandler.dump_traceback_later(timeout, exit=True)` avant chaque test et écrit `...  <fichier>.<test>` (ligne 145) ; le parent (`_run_once`, l. 285-330) ne fait que `proc.wait(timeout=limit)` avec `limit = count * test_timeout + FILE_MARGIN_S` (l. 296-297), puis, au dépassement, `_kill_tree` et un `proc.wait()` **sans limite** (l. 305-306). `run_worker` relance en nouveau processus le reste du fichier après un test arrêté. Les durées par test existent déjà : `tests/.timings.json` (`"test_x.test_y"` → secondes, écrit à chaque passage complet, l. 415 et 421) ; `tests/.last-run.json` ne garde que `failed`. `--times` n'imprime que, il ne persiste rien d'autre.

### REQ-001 — Le parent surveille chaque test pendant qu'il tourne
- **Exigence** : `_run_once` ne se contente plus d'un `proc.wait(timeout=limit)` : tant que le processus de travail vit, le parent lit la sortie qui s'écrit (le fichier `.out`), retient le dernier test annoncé (`...  <fichier>.<test>`) et l'instant où il l'a vu commencer, et déclare un test dépassé quand son temps écoulé passe sa limite (REQ-003) plus une marge de grâce (30 s, constante nommée). Une ligne `ok`/`FAIL`/`ERROR`/`SKIP`/`--` d'un test qu'il a vu commencer le rend de nouveau « entre deux tests » (l'horloge du suivant démarre à sa propre annonce).
- **Source** : T6, T11, T5
- **Priorité** : doit
- **Critère d'acceptation** : un test de `tests/test_runner.py` lance le lanceur sur un fichier planté (REQ-009) dont un test ne rend jamais la main ; le test est compté rouge et nommé, en moins de sa limite plus 30 s, mesuré par le test lui-même.

### REQ-002 — Le parent cesse d'attendre un processus qui ne meurt pas
- **Exigence** : après un test dépassé, le parent tue l'arbre (`_kill_tree`), puis attend **au plus quelques secondes** (constante nommée, par ex. 10 s) que le processus finisse ; s'il vit encore, il l'**abandonne** : le test est compté rouge, le fichier est nommé dans le rapport avec la mention « processus non terminé (PID n) », et le lanceur passe à la suite (reprise du reste du fichier, `run_worker`) ou finit. Aucun `proc.wait()` sans limite ne subsiste dans le lanceur, ni après `_kill_tree` ni ailleurs (lecture finale de la sortie, fermeture du fichier, nettoyage du dossier temporaire compris).
- **Source** : T4, T15, T16, T11
- **Priorité** : doit
- **Critère d'acceptation** : un test de `tests/test_runner.py` fait un faux `_kill_tree` sans effet (processus qui reste vivant, par ex. via un double de `subprocess.Popen` dont `wait()` bloque) ; `_run_once` rend la main dans la grâce, avec un résultat rouge portant la mention de non-terminaison. Une recherche (`grep "\.wait(\|subprocess\.run("` dans `tests/run_tests.py`) ne trouve plus d'appel sans `timeout=` : le `taskkill` de `_kill_tree` est lui aussi une attente (revue, ARCH-RISK-007).

### REQ-003 — Une limite par test tirée des durées mesurées
- **Exigence** : la limite d'un test = `min(--test-timeout, max(plancher, k × durée mesurée))`, la durée mesurée venant de `tests/.timings.json` (la source existante : `"test_x.test_y"` → secondes, dernier passage), `k` et `plancher` étant des constantes nommées (`LIMIT_K = 10`, `LIMIT_FLOOR_S = 30` : Q-001, décision D-4). Un test jamais mesuré (nouveau, renommé, premier passage sur une machine) reçoit `--test-timeout` (300 s par défaut). `--test-timeout` reste le plafond et garde son sens (« un test plus long est arrêté et échoue »). Le parent calcule les limites et les transmet au fils par un fichier JSON (ARCH-001, revue) ; le fils garde son `faulthandler` comme premier filet, réglé sur la limite du test en cours.
- **Source** : T7
- **Priorité** : doit
- **Critère d'acceptation** : une fonction pure `test_limit(timings, label, ceiling)` est testée : test mesuré à 0,2 s → le plancher ; mesuré à 40 s → `min(plafond, k × 40)` ; inconnu → le plafond. Le message d'un test arrêté dit la limite appliquée et son origine (« 30 s : 10 × 0,8 s mesurées » ou « 300 s : jamais mesuré »).

### REQ-004 — Les durées mesurées, une seule source
- **Exigence** : les durées par test restent dans `tests/.timings.json` (déjà écrit à chaque passage, déjà lu par `plan`/`_shard`) ; `tests/.last-run.json` reste `{"failed": [...]}` pour `--failed` (contrat inchangé). Aucune seconde copie des durées n'est créée dans `.last-run.json`. Un passage partiel (`-k`, `--failed`, `--related`) met à jour les durées des seuls tests exécutés sans effacer les autres (comportement actuel : `timings.update`). Une durée issue d'un test arrêté ou en échec par limite n'écrase **pas** la durée mesurée d'un passage réussi (sinon la limite se resserrerait ou s'élargirait d'elle-même).
- **Source** : T7 (« par ex. `tests/.last-run.json` » est un exemple de l'issue ; la source existe déjà ailleurs : règle « une seule source de vérité »)
- **Priorité** : doit
- **Critère d'acceptation** : après un passage où un test est arrêté, `tests/.timings.json` garde l'ancienne durée de ce test ; `.last-run.json` ne gagne aucune clé ; testé dans `tests/test_runner.py`.

### REQ-005 — Une limite de fichier qui ne grandit pas avec le nombre de tests (modifiée par la revue, ARCH-RISK-002)
- **Exigence** : un processus (fichier ou part) n'a plus de limite **totale** proportionnelle au nombre de ses tests (`count × 300 + 300` : 5400 s pour 17 tests) ni de plafond total fixe (un `FILE_CAP_S` de 900 s aurait tué à tort un long fichier sain sur une machine sans `.timings.json`, où rien n'est mesuré, rien n'est découpé et `test_fire_tab` a déjà duré 24 minutes). Sa limite est une **limite de silence** : un processus qui n'annonce ni ne termine aucun test depuis `FILE_MARGIN_S` (300 s, constante existante) alors qu'**aucun test n'est en cours** (import, entre deux tests, après le dernier : `conftest.cleanup`, `atexit`, `_leave`) est arrêté avec la grâce de REQ-002. Tant qu'un test est en cours, seule sa propre limite (REQ-003) s'applique ; la durée totale d'un fichier est bornée par la somme de limites de tests qui avancent, et celle de la suite par REQ-006.
- **Source** : T8, T5 ; revue d'architecture (la forme « somme plafonnée » de la première rédaction est écartée, D-8)
- **Priorité** : doit
- **Critère d'acceptation** : `stop_reason(...)` (fonction pure, ARCH-001) est testée : 17 tests annoncés et terminés à la file ne déclenchent aucune limite de fichier, quel que soit leur nombre ; un silence de plus de `FILE_MARGIN_S` hors test, ou avant tout test (import), déclenche l'arrêt ; un test en cours depuis moins de sa limite plus la grâce ne le déclenche pas.

### REQ-006 — Un plafond pour la suite entière
- **Exigence** : le lanceur connaît un plafond de durée pour un passage complet (`--suite-timeout S`, défaut 1800 : Q-002, D-5). Au plafond atteint : il ne démarre plus aucun processus, arrête les processus en cours (REQ-002, sans attente sans fin), imprime la liste « encore en cours à l'échéance : fichier, test en cours, depuis combien de secondes » avec la pile du fils lorsque la sortie la contient, compte chaque test arrêté comme rouge (les fichiers jamais lancés sont signalés « non lancés » et font aussi rendre `1`, mais ne sont pas comptés comme des échecs de test), écrit `.last-run.json` (les arrêtés dans `failed`, pour que `--failed` les rejoue), et rend `1` (« rouge »). Le plafond ne s'applique qu'à un passage complet (sans `-k`, `--failed`, `--related`) ; un passage partiel a seulement les limites par test et par fichier. Le plafond tient aussi quand tous les cœurs sont pris par des tests qui ne rendent pas la main : l'échéance est vérifiée par chaque sondage de `_run_once` (REQ-001) et par la boucle de collecte du fil principal (`wait` à échéance, jamais `as_completed` sans délai) ; aucun rejeu (REQ-010) après l'échéance.
- **Source** : T9, T12
- **Priorité** : doit
- **Critère d'acceptation** : un test de `tests/test_runner.py` lance le lanceur sur un dossier de faux tests avec `--suite-timeout 5` et un test qui dort 600 s ; le lanceur finit en moins de 5 s plus la grâce, sort avec le code 1, et sa sortie nomme le fichier et le test encore en cours.

### REQ-007 — Les durées de `--times` et le rapport des arrêts
- **Exigence** : le résumé d'un test arrêté dit lequel (fichier.test), pourquoi (« arrêté après 30 s -- limite = 10 × 0,8 s mesurées »), si l'arbre est mort ou abandonné, et renvoie à la sortie (`-v`) pour la pile. `--times` continue de fonctionner ; il ajoute, s'il y en a, la liste des limites individuelles les plus serrées (utile pour repérer un test dont la limite est trop près de sa durée normale).
- **Source** : T6, T7 (inféré : le message actuel `stopped after {test_timeout} s` devient faux dès que la limite varie)
- **Priorité** : devrait
- **Critère d'acceptation** : le message de `result["failed"]` d'un test arrêté contient la limite appliquée et son origine ; la ligne `Failed:` du résumé le reprend.

### REQ-008 — Comprendre le test `test_updates` bloqué
- **Exigence** : le test `test_skip_and_later_are_remembered_and_install_downloads_then_starts` ne doit pas pouvoir rester dans `finished` hors de sa boucle de 5 s. La cause est à établir par une reproduction contrôlée (pas seulement par lecture : voir « Diagnostic » ci-dessous) avant tout correctif ; le correctif vise la cause (la fermeture de la boîte de progression modale en tâche de fond, la dépendance à une fenêtre d'un autre test, la boucle `exec()` sans garde), et non un allongement de limite. Si la cause est un appel natif de Qt/Windows hors de portée de Python, le test se réécrit pour ne plus exercer la fenêtre réelle (`QProgressDialog` remplacée par un double sans fenêtre native, ou `QT_QPA_PLATFORM=offscreen` pour ce fichier) tout en gardant ce que le test prouve : le téléchargement simulé, le lancement, l'avis `info` puis `critical`.
- **Source** : T10, T2
- **Priorité** : doit
- **Critère d'acceptation** : le fichier `tests/test_updates.py` passe 20 fois de suite en parallèle de la suite (charge des 16 cœurs) sans blocage ; le test ne dépend plus d'une fenêtre native visible, ou la dépendance est justifiée dans un commentaire ; la cause trouvée est consignée dans `docs/conventions/testing.md` (ligne courte) et dans le `CHANGELOG.md`.

### REQ-009 — Tests plantés prouvant les limites
- **Exigence** : `tests/test_runner.py` gagne des tests qui écrivent dans un dossier temporaire de **faux fichiers de tests** (le patron de `test_a_test_of_another_system_is_counted_apart_from_the_skips`, l. 24-35 : un fichier `probe` écrit, puis le lanceur lancé dessus) et vérifient : (a) une boucle sans fin en Python pur est arrêtée et comptée rouge dans sa limite plus la grâce ; (b) un `exec()` modal d'une `QEventLoop` sans `quit` l'est de même (test sauté proprement si PySide6 est absent, conformément à `conftest.Skip`) ; (c) le cas « la sortie se bloque » : un processus qui ignore la mort (double de `Popen`, ou faux fils qui bloque sa propre sortie par un `faulthandler` réglé trop long) n'empêche pas le lanceur de finir (REQ-002) ; (d) le plafond de suite (REQ-006) ; (e) les fonctions pures de limite (REQ-003, REQ-005). Les valeurs de limite de ces essais sont minuscules (quelques secondes) pour ne pas allonger la suite ; le fichier garde `TIER`/`PERF` selon l'usage des autres tests du lanceur.
- **Source** : T13, T11, T12
- **Priorité** : doit
- **Critère d'acceptation** : les tests (a) à (e) existent, passent, et chacun, privé du correctif correspondant, échoue ou se bloque (vérifié à la main une fois par le vérificateur, pas en test).

### REQ-010 — Un test arrêté par sa limite est rejoué une fois (Q-003, option B)
- **Exigence** : quand un test est arrêté pour avoir dépassé sa limite (REQ-001) et que le processus a été tué ou abandonné, `run_worker` le rejoue **une fois**, seul, dans un nouveau processus, avec le plafond `--test-timeout` pour limite, après avoir lancé le reste du fichier. S'il passe, il est compté **réussi** et rapporté « intermittent » (une ligne `FLAKY fichier.test` et un compte dans le résumé, jamais silencieux) ; s'il est arrêté de nouveau, il est rouge, avec la limite de chacune des deux tentatives. Pas de rejeu quand (interprétation de l'option B, à confirmer à l'approbation, D-6) : la limite appliquée était déjà le plafond (le rejeu serait identique et coûterait cinq minutes de plus), le processus a été abandonné (REQ-002 : il peut encore tenir des ressources), le test a échoué sur une assertion (rouge franc), ou l'échéance de la suite est atteinte.
- **Source** : Q-003 (réponse de l'ingénieur : B) ; T6, T11
- **Priorité** : doit
- **Critère d'acceptation** : un test planté qui dort la première fois (marqueur dans un fichier du dossier temporaire) et passe la seconde est compté réussi et « intermittent » ; un test qui dort toujours est rouge après deux tentatives ; un test déjà à son plafond n'est pas rejoué ; testé dans `tests/test_runner.py`.

## 4. Exigences d'interface (fenêtre, rapport, site)

Aucune fenêtre, aucun rapport, aucun site : le lanceur est un outil de ligne de commande, en anglais comme le reste du code (`docs/conventions/writing.md`). Ses messages sont destinés à l'ingénieur et à `finish`; pas de glossaire de/fr/en.

### UI-001 — Lisibilité de la sortie en cas d'arrêt
- **Exigence** : la sortie du lanceur reste en ASCII/UTF-8 déjà configuré (l. 43-47), sans couleur hors d'un terminal (déjà le cas), et le rapport d'un arrêt tient en peu de lignes : la ligne `FAIL fichier.test: <raison>`, puis dans `Failed:` la même ligne, puis la commande de reprise. La pile complète n'est imprimée qu'avec `-v`, comme aujourd'hui.
- **Source** : T6, T9 (inféré : conserver la forme existante de la sortie)
- **Langues** : sans objet (outil de développement, anglais)
- **Critère d'acceptation** : la sortie d'un arrêt dans les tests de REQ-009 contient exactement une ligne `FAIL` par test arrêté et le nom du fichier.

## 5. Exigences d'architecture

### ARCH-001 — Un seul module, la logique de limite en fonctions pures
- **Exigence** : tout reste dans `tests/run_tests.py` (bibliothèque standard seulement, ligne 14 de son en-tête : « No framework, on purpose »). Les calculs de limite (`test_limit`, `stop_reason`, `merge_timings`, échéance de la suite) sont des fonctions pures, sans `subprocess` ni horloge (l'horloge est un paramètre), pour être testées sans processus. La surveillance de la sortie vit dans une petite classe ou fonction (`_Watch`) qui reçoit des lignes et un instant et rend l'état (test en cours, depuis quand), testable de même. La transmission des limites au fils : **un fichier JSON** `{"test_x.test_y": secondes}` écrit par le parent dans son dossier temporaire et nommé par une option cachée `--limits` (comme `--result`) ; le fils y lit la limite de chaque test avant de régler son `faulthandler`, `--test-timeout` valant pour un test absent du fichier. La revue a montré que la variante « le fils garde le plafond » perd la pile de tous les fils (ARCH-RISK-001).
- **Source** : T6, T7 ; `docs/architecture/principles.md` (une source de vérité, logique indépendante de l'interface — ici, logique testable hors processus) — inféré
- **Critère d'acceptation** : les fonctions de limite (`test_limit`, `stop_reason`, `merge_timings`) sont importables depuis `run_tests` et appelées directement par `tests/test_runner.py` ; `run_tests.py` n'importe rien hors de la bibliothèque standard ; le fils d'un test planté avec `--limits` s'arrête à la limite du fichier, pas au plafond.

### ARCH-002 — Lecture de la sortie sans bloquer ni perdre de lignes
- **Exigence** : la surveillance lit le fichier `.out` par sondage (position de lecture conservée, lecture en mode texte tolérant `errors="replace"`, sondage toutes les 0,5 s environ), pas par un tube lu dans un fil qui pourrait lui-même rester bloqué. Les lignes sont complètes (une ligne partielle en fin de lecture est gardée pour le sondage suivant). Le fichier `.out` reste la source du rapport final (comportement actuel : `out_file.read_text`).
- **Source** : T6 (inféré : le fils écrit déjà ligne à ligne, `line_buffering=True` et `PYTHONUNBUFFERED=1`, l. 45 et 299)
- **Critère d'acceptation** : un test alimente `_Watch` avec des lignes coupées au milieu et obtient le même test en cours que pour des lignes entières.

### ARCH-003 — Pas de dépendance à `_exit` ni à un processus qui répond
- **Exigence** : aucun chemin du lanceur ne suppose qu'un processus tué est mort ni que `faulthandler` l'a terminé. Le dossier temporaire du lanceur (`tempfile.TemporaryDirectory`) et le `ThreadPoolExecutor` tolèrent un processus abandonné qui tient encore son fichier `.out` ouvert : nettoyage sans exception (`ignore_cleanup_errors=True` ou équivalent), pas d'attente de fils du pool sur un processus abandonné, sortie du lanceur par `sys.exit` sans jointure sur lui. Un enfant abandonné peut subsister après la fin du lanceur ; le lanceur le nomme (PID) pour que l'ingénieur puisse le retrouver.
- **Source** : T4, T15, T16
- **Critère d'acceptation** : dans le test (c) de REQ-009, après l'abandon, le lanceur sort avec le code 1 et sans trace d'exception du nettoyage ; l'arborescence temporaire est supprimée ou signalée.

### ARCH-004 — Le `faulthandler` du fils reste, en premier filet
- **Exigence** : `faulthandler.dump_traceback_later(timeout, exit=True)` dans `run_file` n'est pas retiré : il écrit la pile de tous les fils, ce que le parent seul ne peut pas obtenir, et il tue le plus souvent. Le parent arrive **après** lui : limite du test + grâce de 30 s (T6) ; la grâce laisse au fils le temps d'écrire sa pile avant le `taskkill`. Pour que cela reste vrai avec des limites par test, le fils reçoit les mêmes limites que le parent (`--limits`, ARCH-001) : sinon son `faulthandler` réglé sur le plafond tirerait après le parent et la pile serait perdue.
- **Source** : T3, T6 (« 30 s après le « Timeout » de `faulthandler` »)
- **Critère d'acceptation** : dans une panne simulée où le fils meurt de lui-même à la limite, la pile est dans la sortie et le parent n'appelle pas `_kill_tree` ; si le fils reste, il est tué à limite + grâce.

### ARCH-005 — Le silence hors test est borné (revue)
- **Exigence** : la surveillance (`_Watch`) distingue « un test est en cours » (annoncé, pas terminé) de « aucun test en cours » ; dans le second état, un silence de plus de `FILE_MARGIN_S` arrête le processus (REQ-005). C'est le cas du blocage de l'issue (T4) : un processus dont tous les tests ont fini mais dont la sortie (`_leave`, `atexit`) ne rend jamais la main.
- **Source** : revue d'architecture (ARCH-RISK-002, ARCH-RISK-003)
- **Critère d'acceptation** : `_Watch` testée sur une suite de lignes et d'instants : test en cours, fini, silence hors test, silence avant le premier test.

### ARCH-006 — La coordination est une fonction testable, sans argument de ligne de commande de plus (revue)
- **Exigence** : `main` délègue à `execute(items, jobs, args, scratch, deadline)` qui lance les processus, applique l'échéance de la suite, ne rejoint jamais un fil bloqué (`pool.shutdown(wait=False, cancel_futures=True)`, pas de bloc `with ThreadPoolExecutor`) et rend les résultats ; `main` garde l'impression, l'écriture de `.timings.json` et de `.last-run.json` (par `merge_timings`, fonction pure). `tests/test_runner.py` appelle `execute` sur des fichiers plantés ; aucune option cachée `--tests-dir` n'est ajoutée (la surface de commande est celle que l'ingénieur a arrêtée : `--suite-timeout` seulement, `--limits` étant interne au fils comme `--result`). `tempfile.TemporaryDirectory(..., ignore_cleanup_errors=True)` (Python 3.14 : `.github/workflows/tests.yml`) tolère le fichier `.out` qu'un processus abandonné tient ouvert.
- **Source** : revue d'architecture (ARCH-RISK-003, ARCH-RISK-004)
- **Critère d'acceptation** : le test (d) de REQ-009 appelle `execute` avec une échéance de quelques secondes ; `run_tests.py --help` ne gagne que `--suite-timeout`.

## 6. Contraintes

- **CON-001** — Bibliothèque standard seulement dans `tests/run_tests.py` ; le comportement actuel (une ligne par test annoncée par le fils, `.timings.json`, `.last-run.json {"failed"}`, code de sortie `exit_code`, `MAX_SKIPPED`) reste compatible pour `finish`, `--failed`, `--related`, woodcore-cli et la CI. Source : en-tête de `tests/run_tests.py`, T6.
- **CON-002** — Windows d'abord (le blocage est celui de `_exit` sous Windows), sans casser Linux/macOS : `_kill_tree` y reste `proc.kill()`; le test (c) de REQ-009 se passe d'un comportement propre à Windows (double de `Popen`). Source : T4, T15 ; inféré (CI sous Linux).
- **CON-003** — Aucune des mesures ne doit allonger la suite : les nouveaux tests de `tests/test_runner.py` tiennent en quelques secondes au total ; sinon rangés `PERF = True`. Source : inféré (budget de 20 minutes de `finish`, issue #22).
- **CON-004** — Règles du dépôt : texte LF, prose non coupée, anglais pour le code et les commentaires, ligne de catalogue `docs/conventions/testing-catalogue*.md` mise à jour si `tests/test_runner.py` gagne des tests, aucune action git destructive. Source : `CLAUDE.md`.
- **CON-005** — La limite d'un test mesuré ne doit pas produire de faux rouges sur une machine chargée : les durées mesurées viennent d'un passage où 16 processus se partageaient les cœurs, donc déjà « chargées » ; `k` et le plancher en tiennent compte (Q-001). Source : T7 (inféré).

## 7. Décisions prises

- **D-1** — Le parent tient les limites ; le `faulthandler` du fils reste un filet. (T6)
- **D-2** — Un processus qui ne meurt pas est abandonné et compté rouge, jamais attendu sans fin. (T15, T16)
- **D-3** — Les durées par test restent dans `tests/.timings.json` ; `.last-run.json` n'en prend pas (une seule source ; l'exemple de l'issue y renonce, voir REQ-004). Prix : l'issue citait `.last-run.json` comme exemple, non comme exigence.

- **D-4** (Q-001, A, ingénieur 24.10.2026) — limite d'un test mesuré = `min(--test-timeout, max(30 s, 10 × durée mesurée))`. Prix : un test mesuré à 0,5 s attend 30 s avant d'être arrêté, pas 2 s ; en échange aucun faux rouge sur une machine dix fois plus lente.
- **D-5** (Q-002, A, ingénieur) — `--suite-timeout` en secondes, défaut 1800 (le budget de 20 minutes de `finish` plus la moitié) ; à l'échéance plus rien ne démarre, tout ce qui tourne est arrêté, le lanceur nomme ce qui tournait, rend `1` et écrit les arrêtés dans `.last-run.json`. Prix : une suite saine mais lente passe au rouge au-delà de 30 minutes.
- **D-6** (Q-003, B, ingénieur — non la recommandation) — un test arrêté par sa limite est rejoué une fois au plafond (REQ-010) ; intermittent s'il passe. Prix : un blocage intermittent réel passe au vert avec un avertissement et la suite peut durer jusqu'à cinq minutes de plus par test arrêté ; l'ingénieur l'a accepté. Précision de la rédaction, à confirmer : pas de rejeu quand la limite était déjà le plafond, ni pour un processus abandonné.
- **D-7** (revue) — le parent transmet au fils ses limites par fichier (`--limits`) : le `faulthandler` du fils tire avant le parent et la pile reste dans la sortie.
- **D-8** (revue) — la limite de fichier est une limite de silence hors test, non une somme plafonnée : voir REQ-005.

## 8. Hors périmètre

- Réécrire le lanceur en `pytest` ou ajouter une dépendance (en-tête de `run_tests.py`).
- Tuer proprement un processus coincé au niveau du noyau : impossible depuis l'espace utilisateur (T15) ; on l'abandonne et on le nomme.
- Accélérer la suite (le découpage `SHARD_S`, l'ordre, `--fast` restent tels quels).
- Le correctif des autres tests lents ou fragiles (`test_fire_tab`, etc.) : seul `test_updates` est traité (REQ-008).

## 9. Idées non retenues comme exigences

- Des limites par fichier écrites à la main dans les tests (`TIMEOUT = 20` en tête de fichier) pour un test connu pour être long : écartées au profit des durées mesurées (aucune valeur à copier à la main), à reprendre seulement si une limite mesurée se révèle fausse.
- Tuer aussi les orphelins d'un passage précédent au démarrage du suivant (liste de PID dans le dossier temporaire) : utile si l'abandon devient fréquent ; pas demandé.
- Faire dormir le lanceur sur un événement du système plutôt que de sonder la sortie : trop dépendant de la plate-forme.

## 10. Questions

### Q-001 — Quel multiplicateur k et quel plancher pour la limite d'un test mesuré ?
- **Pourquoi elle compte** : la limite d'un test = max(plancher, k × durée mesurée), plafonnée à 300 s. Trop serrée, elle fait échouer à tort un test normal quand la machine est chargée (16 processus en parallèle, antivirus, OneDrive qui synchronise le dossier) ; trop large, elle ne gagne rien sur les 300 s d'aujourd'hui. Les durées sont déjà mesurées sous charge de la suite complète. Le code ne peut pas trancher : c'est un compromis entre faux rouges et temps d'attente.
- **Options** : A (recommandée) k = 10 et plancher 30 s : un test qui dure normalement 0,5 s est arrêté à 30 s, un test de 20 s à 200 s ; un blocage coûte une demi-minute au lieu de cinq, et un faux rouge exigerait une machine dix fois plus lente. B : k = 5 et plancher 15 s : blocage arrêté en 15 s, mais un risque réel de faux rouge sur une machine très chargée. C : pas de limite mesurée, seul le parent tient les 300 s uniformes (la demande 1 de l'issue seule, sans la demande 2) : aucun faux rouge nouveau, mais un blocage coûte toujours cinq minutes.
- **Réponse** : A -- k = 10, plancher 30 s, plafond 300 s (ingénieur, 24.10.2026)

### Q-002 — Quel plafond pour la suite entière, et que fait le lanceur à l'échéance ?
- **Pourquoi elle compte** : `finish` donne 20 minutes à la suite et la signale à l'ingénieur au-delà ; la suite complète tient aujourd'hui en 914 s (environ 15 minutes). Un plafond trop bas rend rouge une suite saine sur une machine lente ou une CI ; trop haut, il n'arrête rien. À l'échéance, soit on arrête tout (rouge), soit on laisse finir les processus déjà lancés.
- **Options** : A (recommandée) `--suite-timeout` en secondes, défaut 1800 (30 minutes : le budget de 20 minutes plus une marge de moitié pour ne pas rougir une machine lente) ; à l'échéance, plus rien ne démarre, les processus en cours sont arrêtés, le lanceur nomme ce qui tournait, rend 1 et écrit les arrêtés dans `.last-run.json`. B : défaut 1200 (exactement les 20 minutes de `finish`) : respecte la lettre du budget, mais une suite à 19 minutes sur une machine lente passerait au rouge sans qu'un test soit en faute. C : défaut 1200 mais à l'échéance on laisse finir les fichiers déjà lancés (plus rien de nouveau ne démarre) : moins de faux rouges, mais le lanceur peut dépasser le plafond de la durée d'un fichier.
- **Réponse** : A -- `--suite-timeout` 1800 s ; à l'échéance tout est arrêté, ce qui tournait est nommé, code 1, les arrêtés dans `.last-run.json` (ingénieur, 24.10.2026)

### Q-003 — Un test arrêté pour dépassement de limite est-il rejoué une fois ?
- **Pourquoi elle compte** : aujourd'hui, après un test arrêté, `run_worker` relance le **reste** du fichier dans un nouveau processus, mais jamais le test arrêté lui-même : il est rouge. Un test arrêté à tort (machine chargée, avec des limites plus serrées par Q-001) pèserait une suite rouge sans cause réelle ; un rejeu masque en revanche un vrai blocage intermittent et ajoute une limite de temps à la suite.
- **Options** : A (recommandée) pas de rejeu : le test est rouge tout de suite, nommé avec sa limite et son origine, et `--failed` le rejoue à la main ; c'est la règle actuelle, et un test qui se bloque une fois mérite d'être vu. B : un rejeu du test arrêté, avec le plafond (`--test-timeout`) pour limite ; rouge seulement s'il s'arrête encore, et rapporté comme « intermittent » s'il passe au rejeu. C : un rejeu seulement si le test a été arrêté avant son plafond (limite mesurée, pas plafond) : couvre les faux rouges dus à Q-001 sans masquer un blocage franc.
- **Réponse** : B (et non la recommandation A) -- un rejeu du test arrêté, au plafond ; rouge seulement s'il s'arrête encore, « intermittent » s'il passe au rejeu (ingénieur, 24.10.2026)

## 11. Critères d'acceptation

- [x] REQ-001 — un test planté qui ne rend jamais la main est arrêté et rouge en moins de sa limite plus 30 s (mesuré par `tests/test_runner.py`).
- [x] REQ-002 — avec un `_kill_tree` sans effet, `_run_once` rend la main dans la grâce, résultat rouge « processus non terminé » ; plus aucun `.wait(` ni `subprocess.run(` sans `timeout=` dans `tests/run_tests.py`.
- [x] REQ-003 — `test_limit` (k = 10, plancher 30 s, plafond 300 s) : mesuré court → 30 s ; mesuré long → `min(plafond, 10 × durée)` ; inconnu → plafond ; le message dit la limite et son origine ; le fils reçoit les limites par `--limits`.
- [x] REQ-004 — `.timings.json` seule source des durées ; `.last-run.json` inchangé ; la durée d'un test arrêté n'écrase pas l'ancienne.
- [x] REQ-005 — `stop_reason` : aucun total de fichier ; un silence hors test (import compris) de plus de `FILE_MARGIN_S` arrête ; 17 tests qui avancent ne sont jamais arrêtés pour leur nombre.
- [x] REQ-006 — `--suite-timeout` (défaut 1800) : `execute` sur de faux tests avec une échéance de quelques secondes : fin dans l'échéance plus la grâce, code 1, fichier et test en cours nommés, non lancés signalés, arrêtés écrits dans `.last-run.json`.
- [x] REQ-007 — le message d'un arrêt contient la limite et son origine, et le sort de l'arbre (mort ou abandonné).
- [x] REQ-010 — un test arrêté puis réussi au rejeu est réussi et « intermittent » ; arrêté deux fois, rouge ; pas de rejeu au plafond, après abandon ou après l'échéance.
- [~] REQ-008 — la cause du blocage de `test_skip_and_later_are_remembered_and_install_downloads_then_starts` est établie par reproduction, corrigée à sa racine, le fichier tient 20 passages sous charge, la cause est consignée.
- [x] REQ-009 — tests plantés (boucle sans fin, `exec()` modal, sortie bloquée, plafond de suite, fonctions pures) présents dans `tests/test_runner.py` et verts.
- [x] UI-001 — une ligne `FAIL` par test arrêté, nom du fichier, pile seulement avec `-v`.
- [x] ARCH-001 — fonctions de limite pures et importables ; seulement la bibliothèque standard.
- [x] ARCH-002 — surveillance par sondage du fichier `.out`, lignes coupées gérées.
- [x] ARCH-003 — aucun chemin ne suppose qu'un processus tué est mort ; nettoyage sans exception ; PID de l'abandonné nommé.
- [x] ARCH-004 — le `faulthandler` du fils est conservé et règle sur la même limite que le parent ; le parent n'intervient qu'à limite plus grâce.
- [x] ARCH-005 — le silence hors test est borné par `FILE_MARGIN_S`.
- [x] ARCH-006 — `execute` testable ; seule option publique de plus : `--suite-timeout`.
- [x] Documentation : `docs/conventions/testing.md` (le paragraphe « No test can hold the run » et les limites), `.claude/skills/finish/SKILL.md` (budget et plafond de suite), `docs/conventions/testing-catalogue*.md` (nouvelles lignes de `test_runner`), entrée `CHANGELOG.md`, page « Nouveautés » de la version suivante en fr/de/en si l'ingénieur la tient pour utile à l'utilisateur ; `docs/decisions.md` (§13) : pourquoi le parent tient les limites et abandonne un processus coincé. Aucune commande Typst concernée.
- [x] Tests : `tests/test_runner.py` étendu, `tests/test_updates.py` corrigé ; tous passent, et la suite complète ne s'allonge pas (CON-003).

## 12. Traçabilité

| Source | Élément | Statut |
|---|---|---|
| T1 | §1 Objectif | contexte |
| T2 | REQ-008 | capturé |
| T3 | ARCH-004 | capturé |
| T4 | REQ-002, ARCH-003, CON-002 | capturé |
| T5 | REQ-001, REQ-005 | capturé |
| T6 | REQ-001, REQ-007, ARCH-001, ARCH-002, ARCH-004, D-1 | capturé |
| T7 | REQ-003, REQ-004, REQ-007, Q-001, D-4 | capturé (Q-001 : A) |
| T8 | REQ-005 | capturé |
| T9 | REQ-006, Q-002, D-5 | capturé (Q-002 : A) |
| T10 | REQ-008 | capturé |
| T11 | REQ-001, REQ-002, REQ-009, REQ-010 | capturé |
| T12 | REQ-006, REQ-009 | capturé |
| T13 | REQ-009 | capturé |
| Q-003 | REQ-010, D-6 | capturé (B) |
| Revue | ARCH-005, ARCH-006, D-7, D-8, REQ-005 réécrite | ajouté par la revue |
| T14 | §1 (issue #22, `docs/conventions/testing.md`) | contexte |
| T15 | REQ-002, ARCH-003, D-2 | capturé |
| T16 | REQ-002, ARCH-003, D-2 | capturé |

### Points de la source non résolus

- T7 — k et plancher : résolus (Q-001 A, D-4). L'exemple de fichier (`.last-run.json`) est écarté pour `.timings.json`, qui existe déjà (REQ-004, D-3) : à confirmer à l'approbation.
- T9 — plafond de suite et comportement à l'échéance : résolus (Q-002 A, D-5).
- T6/T11 — rejeu d'un test arrêté : résolu (Q-003 B, REQ-010, D-6) ; l'exception « pas de rejeu au plafond / après abandon » est une précision à confirmer.
- T10 — la cause du blocage n'est pas établie : REQ-008 (reproduction avant correctif ; hypothèses ci-dessous).

### Diagnostic par lecture (T10)

Faits : `finished` (`calc/tools/update_gui.py:187-201`) est un slot relié à `bridge.done` ; sa première instruction, la ligne 188, est `dialog.close()` sur un `QProgressDialog` **WindowModal** dont le parent `parent` est une vraie fenêtre affichée (`parent.show()`, `tests/test_updates.py:402`) et que `install` a montré (`dialog.show()`, l. 215). La boucle du test (`loop.exec()`, l. 436) n'est qu'un lieu d'exécution des slots : le `QTimer.singleShot(5000, loop.quit)` (l. 435) ne s'exécute que **si la boucle reprend la main**. Un slot qui reste dans un appel natif (`dialog.close()` → `QProgressDialog::closeEvent`/`hide` → réactivation de la fenêtre parente, destruction de la fenêtre native sous Windows) empêche tout retour à la boucle : le minuteur de 5 s ne peut donc rien contre lui. L'explication n'est pas « la boucle ne s'arrête pas » mais « on ne revient jamais à la boucle ». Le `faulthandler` a écrit deux piles (fil principal dans `finished`, fil de travail du téléchargement terminé ou attendant), ce qui concorde.

Hypothèses à départager par reproduction, dans l'ordre de vraisemblance : (1) un appel natif de Qt/Windows bloqué à la fermeture d'une fenêtre modale (le même verrou du chargeur de DLL ou du système de fenêtres que celui qui bloque `_exit`, T4 : même famille de blocage, ce qui explique que le processus ne se laisse plus tuer) ; (2) une `QProgressDialog` WindowModal laissée par un test précédent du même fichier ou une boîte `QMessageBox.exec()` ouverte hors écran qui tient l'entrée de la fenêtre parente ; (3) une course entre le fil de téléchargement (`bridge.done.emit` depuis un `threading.Thread`, l. 205-214) et la destruction de `parent`/`dialog` (la connexion `bridge.done.connect(finished)` est en file, le slot tourne dans le fil principal ; mais `_KEEP.append(bridge)` garde le pont vivant et un `done` tardif d'un test précédent peut tomber dans la boucle suivante). Le test appelle `install` deux fois, la seconde avec `refused` : un `done` de la première boucle non consommé pourrait aussi y arriver. La reproduction demandée par REQ-008 : lancer ce seul test cent fois sous charge (`-k` en boucle, plusieurs en parallèle), avec `faulthandler` à 20 s pour obtenir la pile du fil principal à chaque blocage.

## 13. Revue d'architecture

Revue faite le 2026-10-24 par lecture de `tests/run_tests.py` (466 lignes), `tests/test_runner.py`, `tests/test_harness.py`, `tests/conftest.py` (`tmpdir`), `docs/conventions/testing.md` (l. 18, 37), `.claude/skills/finish/SKILL.md` (l. 17), `calc/tools/update_gui.py` et `tests/test_updates.py`.

### Modules touchés

- `tests/run_tests.py` : le fils `run_file` (l. 108-176, `faulthandler` l. 121 et 147, ligne `...  <test>` l. 145, `save()` après chaque test) ; le parent `_run_once` (l. 285-330, `proc.wait(timeout=limit)` l. 303, `proc.wait()` sans limite l. 306), `run_worker` (l. 333-350, reprise du reste du fichier), `_kill_tree` (l. 278-282), `main` (l. 353-462 : `TemporaryDirectory` + `ThreadPoolExecutor` en bloc `with` l. 397, collecte par `as_completed` l. 399, écriture de `.timings.json`/`.last-run.json` l. 421-422).
- `tests/test_runner.py` (4 tests aujourd'hui, `TIER = "fast"`) reçoit les tests plantés ; `tests/test_harness.py::test_a_stuck_test_is_stopped_named_and_the_rest_of_its_file_still_runs` (l. 135-148) appelle `run_worker` avec `Namespace(test_timeout=3)` et exige un message commençant par `stopped after 3 s` et la pile dans `traceback` : contrat à conserver.
- `calc/tools/update_gui.py` (`install`, `finished` l. 187-201) et `tests/test_updates.py` (l. 395-450) pour REQ-008.
- Documentation : `docs/conventions/testing.md`, `.claude/skills/finish/SKILL.md`, `docs/conventions/testing-catalogue-guards.md` (ligne `test_runner.py`) et la ligne de `test_harness`, `docs/decisions.md` §13, `CHANGELOG.md`.

### Code à réutiliser

`_read_json`, `_test_names`, `TIMINGS` (source unique des durées, déjà lue par `plan` et `_shard`), la boucle de reprise de `run_worker`, le patron des fichiers plantés de `test_runner.py` (l. 24-35) et de `test_harness.py` (`_runner()`, `conftest.tmpdir`), `--result` comme modèle d'une option cachée du fils. Aucun doublon à créer : pas de seconde copie des durées, pas de seconde lecture du chemin des tests.

### Risques

- **ARCH-RISK-001 — important — la pile serait perdue (ARCH-001 contre ARCH-004).** Si le fils garde `faulthandler` à `--test-timeout` (300 s) alors que le parent applique 30 s + 30 s de grâce, le parent tue l'arbre à 60 s sans que `faulthandler` ait écrit une pile : exactement ce que l'issue veut garder (T3). Correction : le parent écrit un fichier de limites (`--limits`) lu par le fils pour régler son `faulthandler` test par test (D-7, ARCH-001/ARCH-004). Les tests existants de `test_harness` restent valables : sans fichier, le fils prend `--test-timeout`.
- **ARCH-RISK-002 — important — le plafond de fichier de 900 s tue un fichier sain.** Sur une machine sans `.timings.json` (CI, clone neuf), `_estimate` compte 1 s par test inconnu : rien n'est découpé et un long fichier (`test_fire_tab` a duré 24 minutes avant découpage) dépasserait 900 s tout en avançant. Une limite de fichier, plafonnée ou non, mesure le mauvais objet : un fichier qui avance n'est pas bloqué. Correction : la limite de fichier devient une limite de silence hors test (REQ-005 réécrite, ARCH-005, D-8). Repli si l'ingénieur tient à un total : `FILE_CAP_S` ne s'appliquerait qu'aux fichiers entièrement mesurés.
- **ARCH-RISK-003 — important — le plafond de suite ne peut pas être testé tel qu'écrit.** `main` ne lance que `HERE.glob("test_*.py")` (l. 376) : « un dossier de faux tests avec `--suite-timeout 5` » exigerait une option cachée de plus (`--tests-dir`) ou de lancer la vraie suite. De plus la collecte `as_completed` (l. 399) et le bloc `with ThreadPoolExecutor` (l. 397) rejoignent les fils : un fil bloqué retient la sortie. Correction : `execute(items, jobs, args, scratch, deadline)` extraite de `main`, sans bloc `with`, `pool.shutdown(wait=False, cancel_futures=True)` ; l'échéance vérifiée dans le sondage de chaque `_run_once` (ARCH-006, REQ-006). Si, malgré tout, un fil ne rend pas la main après l'échéance plus la grâce, `main` écrit ses fichiers d'état, imprime la liste et sort par `os._exit(1)` après avoir vidé la sortie.
- **ARCH-RISK-004 — important — le nettoyage échoue sur Windows quand un processus est abandonné.** Le processus coincé tient son `.out` ; `TemporaryDirectory.__exit__` lève `PermissionError` et masque le rapport. Correction : `ignore_cleanup_errors=True` (Python 3.14 des workflows), PID de l'abandonné nommé (ARCH-003, ARCH-006).
- **ARCH-RISK-005 — important — le rejeu (Q-003 B) touche quatre comptes.** Le premier échec ne doit pas rester dans `failed`, `.last-run.json` et le résumé quand le rejeu passe ; la durée d'un rejeu réussi ne doit pas fausser `.timings.json` (elle est recopiée : un test lent à froid mais sain gagne ainsi une limite plus large, ce qui est voulu) ; pas de rejeu au plafond (identique), après abandon, sur une assertion, ni après l'échéance. Un rejeu réussi est visible (`FLAKY`, REQ-010). Q-003 B absorbe aussi le faux rouge qu'un test lent à froid (OneDrive, antivirus) causerait sous une limite de 30 s (CON-005).
- **ARCH-RISK-006 — mineur — contrat de `test_harness`.** `Namespace(test_timeout=3)` n'a ni `suite_timeout` ni `limits` : lire ces attributs avec `getattr(..., défaut)` ; garder le préfixe `stopped after {limite} s`. Sans cela, le test existant casse.
- **ARCH-RISK-007 — important — le `taskkill` est une attente sans fin.** `_kill_tree` appelle `subprocess.run(["taskkill", ...])` sans `timeout` (l. 280) : le critère « plus de `.wait(` sans `timeout=` » ne le voit pas. Correction : `timeout=` + `TimeoutExpired` attrapé, repli `proc.kill()` ; le critère de REQ-002 couvre `subprocess.run(` (modifié).
- **ARCH-RISK-008 — mineur — durées issues d'échecs.** Un test qui échoue en 0,01 s écrase aujourd'hui sa durée (l. 415) et resserrerait sa limite (borne : le plancher de 30 s). `merge_timings` ne retient que les tests réussis ou sautés (REQ-004).
- **ARCH-RISK-009 — mineur — lecture de la sortie.** Les marqueurs `ok`/`FAIL`/`ERROR`/`SKIP`/`--` suivis de l'étiquette sont analysés par expression régulière non ancrée (la sortie d'un fils vers un fichier n'a pas de couleur, mais la forme existe : `DIM` l. 145) ; sondage de 0,5 s, ligne partielle gardée (ARCH-002). Un test qui imprime lui-même une ligne `...  fichier.test_x` est un risque accepté et nommé dans le commentaire.
- **ARCH-RISK-010 — mineur — REQ-008.** La reproduction doit précéder le correctif ; la cause (fermeture d'une `QProgressDialog` WindowModal sur un parent affiché, ou `done` tardif d'un test précédent) n'est pas établie par lecture. `update_gui.py` est du code produit : un changement de comportement du produit serait un second sujet pour l'ingénieur ; la voie par défaut est de modifier le test (double sans fenêtre native, `QT_QPA_PLATFORM=offscreen` pour ce test), pas le produit.

Aucun risque de contrat de données (aucun schéma, aucun `schema_version`), de langue (outil en anglais, UI-001), de couleur ni de norme. Une règle de `docs/architecture/principles.md` n'est enfreinte qu'en l'absence des corrections ci-dessus (« une seule source de vérité » : durées dans `.timings.json` seulement ; « une source » aussi pour les limites : `test_limit` seule les calcule, le fils les lit).

### Approche recommandée

Fonctions pures (`test_limit`, `stop_reason`, `merge_timings`) et `_Watch` d'abord, testées sans processus ; puis le fichier de limites et le fils ; `_run_once` en boucle de sondage (lecture incrémentale de `.out`, état du `_Watch`, arrêt de l'arbre, attente bornée, abandon) ; le rejeu dans `run_worker` ; `execute` avec l'échéance de suite ; enfin REQ-008 (indépendant, peut se faire en parallèle) et la documentation.

### Tests à ajouter ou étendre

`tests/test_runner.py` (fonctions pures, `_Watch` à lignes coupées, plantés a à e, rejeu, `.wait(` absents par lecture du texte de `run_tests.py`, `merge_timings`) ; `tests/test_harness.py` inchangé mais relancé (contrat de ARCH-RISK-006) ; `tests/test_updates.py` pour REQ-008.

### Verdict

**APPROUVER AVEC RÉSERVES** : ARCH-RISK-001 à 005 et 007 sont appliqués dans la spécification (REQ-005 réécrite, ARCH-005, ARCH-006, REQ-010, D-7, D-8) et dans le plan §14 ; deux points sont laissés à l'ingénieur (réécriture de REQ-005, exception du rejeu au plafond).

## 14. Plan d'implémentation

Ordre : chaque étape laisse `tests/test_runner.py` et `tests/test_harness.py` verts. Tous les chemins sont ceux du dépôt ; le code et les commentaires sont en anglais.

1. **Fonctions pures et `_Watch`** (`tests/run_tests.py`). Constantes `LIMIT_K = 10`, `LIMIT_FLOOR_S = 30`, `GRACE_S = 30`, `ABANDON_WAIT_S = 10`, `SUITE_TIMEOUT_S = 1800`, `POLL_S = 0.5` (`FILE_MARGIN_S` et `TEST_TIMEOUT_S` existent) ; `test_limit(timings, label, ceiling)` qui rend aussi l'origine ; `stop_reason(state, now, limits)` ; `merge_timings(timings, result, stem)` (tests réussis ou sautés seulement) ; `_Watch.feed(chunk, now)` (lignes partielles gardées, marqueurs `...`/`ok`/`FAIL`/`ERROR`/`SKIP`/`--`, état « test en cours depuis », « silencieux depuis »). Réalise REQ-003, REQ-004, REQ-005, REQ-007 (le message), ARCH-001, ARCH-002, ARCH-005 ; couvre ARCH-RISK-008, 009. Preuve : `tests/test_runner.py` (tests purs : plancher, k fois la durée, inconnu, plafond ; `_Watch` ligne entière contre ligne coupée ; silence avant le premier test et hors test ; `merge_timings`).
2. **Fichier de limites et fils** (`run_file`, `main`). Option cachée `--limits` ; le fils lit `{label: s}` et règle chaque `faulthandler.dump_traceback_later` dessus (l. 147), l'import sur `FILE_MARGIN_S` ; sans fichier, `--test-timeout` (contrat de `test_harness`). Réalise REQ-003 (transmission), ARCH-001, ARCH-004, D-7 ; couvre ARCH-RISK-001, 006 (`getattr` par défaut pour `suite_timeout`/`limits`). Preuve : `tests/test_runner.py` : un fils lancé par `run_worker` avec une limite de 2 s pour un test qui dort écrit « Timeout » et la pile, avant la grâce du parent ; `tests/test_harness.py` inchangé et vert.
3. **`_run_once` en boucle de sondage**. Remplace `proc.wait(timeout=limit)` : `Popen`, puis toutes les `POLL_S` lecture de ce que `.out` a gagné (position conservée, `errors="replace"`), `_Watch`, `stop_reason` ; au dépassement `_kill_tree` (avec `timeout=` sur `taskkill`, repli `proc.kill()`, `TimeoutExpired` attrapé : ARCH-RISK-007), puis `proc.wait(timeout=ABANDON_WAIT_S)` ; s'il vit encore, abandon, test rouge « processus non terminé (PID n) », jamais d'attente de plus. Message de `failed` : limite appliquée et origine, sort de l'arbre (REQ-007). La limite totale de fichier (l. 296-297) disparaît (D-8). Réalise REQ-001, REQ-002, REQ-005, REQ-007, ARCH-002, ARCH-003, UI-001 ; couvre ARCH-RISK-002, 004 (partie `.out`). Preuve : `tests/test_runner.py` : (a) boucle sans fin en Python pur arrêtée et rouge en moins de limite + grâce, mesuré par le test (limites de quelques secondes, `GRACE_S` abaissée par le test) ; (b) `exec()` d'une `QEventLoop` sans `quit` (saute proprement sans PySide6) ; (c) `_kill_tree` neutralisé et `Popen` double dont `wait()` bloque : retour dans la grâce, résultat rouge « non terminé » ; lecture du texte de `run_tests.py` : plus de `.wait(` ni `subprocess.run(` sans `timeout=`.
4. **Rejeu dans `run_worker`** (REQ-010, D-6). Après le reste du fichier, un rejeu du test arrêté par sa limite, seul, avec le plafond pour limite (fichier `--limits` réécrit) ; sauf limite déjà au plafond, processus abandonné, assertion, échéance de suite ; réussi : retiré de `failed`, ajouté à `passed` et à une liste `flaky` (ligne `FLAKY fichier.test`, compte dans le résumé) ; arrêté de nouveau : rouge avec les deux limites. Couvre ARCH-RISK-005. Preuve : `tests/test_runner.py` : dort-puis-passe (marqueur dans `conftest.tmpdir`), dort-toujours, déjà au plafond.
5. **`execute` et l'échéance de la suite** (`main`). Extraction de la coordination (ARCH-006) : pool sans bloc `with`, `concurrent.futures.wait` avec délai, `deadline` (monotone) vérifiée par chaque `_run_once` et avant tout lancement ; à l'échéance : arrêt, liste « encore en cours à l'échéance : fichier, test, depuis n s », « non lancés », écriture de `.last-run.json` (arrêtés dans `failed`), code 1 ; `--suite-timeout` (défaut 1800, passage complet seulement) ; `TemporaryDirectory(ignore_cleanup_errors=True)` ; PID des abandonnés imprimés ; repli de dernier recours `os._exit` si un fil ne rend pas la main. `merge_timings` appelé par `main`. Réalise REQ-006, ARCH-003, ARCH-006, UI-001 ; couvre ARCH-RISK-003, 004. Preuve : `tests/test_runner.py` : (d) `execute` sur deux fichiers plantés (un test qui dort 600 s, un fichier jamais lancé) avec une échéance de 5 s : fin en moins de l'échéance plus la grâce, code 1, fichier et test nommés, un `FAIL` par arrêt ; `--help` ne gagne que `--suite-timeout`.
6. **REQ-008, `test_updates`**. Indépendante des étapes 1-5. D'abord la reproduction : le seul test `test_skip_and_later_are_remembered_and_install_downloads_then_starts` rejoué en boucle et en parallèle sous charge avec `faulthandler` à 20 s pour la pile du fil principal (une commande en dehors du dépôt, notée dans le journal) ; puis le correctif à la racine, dans le test de préférence (double de `QProgressDialog` sans fenêtre native, ou `QT_QPA_PLATFORM=offscreen` pour ce test, `bridge.done` d'un test précédent drainé) ; `calc/tools/update_gui.py` n'est touché que si la cause y est, et l'ingénieur en est informé. Couvre ARCH-RISK-010. Preuve : `tests/test_updates.py` 20 fois de suite sous la charge de la suite sans blocage ; la cause en une ligne dans `docs/conventions/testing.md` et dans `CHANGELOG.md`.
7. **Documentation** (CLAUDE.md : un changement est fini quand sa documentation l'est). `docs/conventions/testing.md` : les deux paragraphes « No test can hold the run » (l. 18) et « One process per file… » (l. 37) décrivent les limites mesurées, la grâce, l'abandon, le silence, le rejeu, `--suite-timeout`, la cause de REQ-008 ; `.claude/skills/finish/SKILL.md` l. 17 : « stops any test stuck… ; the whole run is capped at `--suite-timeout` (1800 s) » ; `docs/conventions/testing-catalogue-guards.md` : la ligne de `test_runner.py` complétée (pas de nouveau fichier de test, donc pas de nouvelle ligne ; la ligne de `test_harness` et celle de `test_updates` relues) ; `docs/decisions.md` §13 : l'entrée « le parent tient les limites, abandonne un processus coincé et rejoue une fois » avec D-4 à D-8 et leur prix, par Edit ciblé en LF ; `CHANGELOG.md` : une entrée en tête (v0.125 ou la version en cours) qui cite les sections modifiées, l'issue #108 et le diagnostic de REQ-008. **Page « Nouveautés »** (`website/content/{fr,de,en}/changes/`) : le lanceur est un outil de développement, rien ne change pour un rapport ; recommandation : aucune page, à confirmer par l'ingénieur (si oui : trois langues, la page de la version suivante). Aucune commande Typst, aucun glossaire.
8. **Vérification finale**. `python tests/run_tests.py -k test_runner`, `-k test_harness`, `-k test_updates` en cours de route ; à la fin la suite complète une fois en arrière-plan (`finish`), puis `python tests/run_tests.py --times` pour constater que la suite ne s'allonge pas (CON-003) ; relevé manuel unique de chaque correctif retiré (REQ-009, par le vérificateur).

Chaque risque de la revue est appliqué : 001 (étape 2), 002 (étapes 1, 3), 003 (étape 5), 004 (étapes 3, 5), 005 (étape 4), 006 (étape 2), 007 (étape 3), 008 (étape 1), 009 (étape 1), 010 (étape 6).

## 15. Vérification

Vérification indépendante (agent `requirements-verifier`, 2026-10-25) sur `7d1c6e9..65cd243`, puis reprise de ses réserves. Retraits de correctif faits à la main sur des copies de `run_tests.py` (REQ-009) : `_stop` sans abandon → le test (c) se bloque ; `stop_reason` sans arrêt de test → le test (a) se bloque ; échéance ignorée → le test (d) échoue ; rejeu désactivé → le test du rejeu échoue ; silence désactivé → le test de `_Watch` échoue. Cinq sur cinq détectés.

| Élément | Verdict | Preuve |
|---|---|---|
| REQ-001 | ✅ | `_Watch`, boucle de sondage de `_run_once`, `stop_reason` ; `test_an_endless_loop_…`, `test_a_modal_exec_…` |
| REQ-002 | ✅ | `_stop` (attente `ABANDON_WAIT_S`, « process not ended (PID n), abandoned ») ; `taskkill` avec `timeout=` ; `test_a_process_that_will_not_die_…`, `test_the_runner_waits_for_nothing_…` |
| REQ-003 | ✅ | `test_limit` pure avec origine, `--limits` écrit par le parent et lu par le fils ; `test_a_test_s_limit_is_ten_times_…` |
| REQ-004 | ✅ | `merge_timings`, `last_run` ; `test_a_stopped_test_keeps_its_last_good_time_…` |
| REQ-005 | ✅ | `stop_reason` sans total de fichier ; 17 tests à la file jamais arrêtés |
| REQ-006 | ✅ | `execute` et `--suite-timeout` ; réserve levée : `main` testé de bout en bout (`test_a_full_run_past_its_ceiling_…` : code 1, listes, `.last-run.json`, `.timings.json`) |
| REQ-007 | ✅ | message limite + origine + sort de l'arbre ; réserve levée : « Tightest limits » de `--times` testé dans le même test |
| REQ-008 | ⚠️ | cause non reproduite (232 passages sous charge sans blocage) ; test passé à un double sans fenêtre de la `QProgressDialog`, `update_gui.py` intact ; 20 passages de `tests/test_updates.py` pendant la suite complète, tous verts ; écart consigné |
| REQ-009 | ✅ | tests (a) à (e) présents, verts, et détectent le retrait de leur correctif |
| REQ-010 | ✅ | dort-puis-passe → `FLAKY`, dort toujours → rouge avec les deux limites, plafond → pas de rejeu ; réserve levée : `_replayable` testé directement (abandon, échéance, plafond, autre arrêt) |
| UI-001 | ✅ | `report_lines` : une ligne `FAIL` par arrêt (testé) ; pile avec `-v` seulement |
| ARCH-001 à ARCH-006 | ✅ | fonctions pures importables, bibliothèque standard seule ; sondage de `.out` à lignes coupées ; `ignore_cleanup_errors`, pool jamais rejoint, `os._exit` de dernier recours ; `faulthandler` réglé sur la même limite ; silence borné ; `--help` ne gagne que `--suite-timeout` |
| CON-001 à CON-005 | ✅ / ⚠️ | CON-003 : les nouveaux tests de `test_runner` prennent environ 40 s dans leur processus, non « quelques secondes » (écart consigné) |
| Documentation | ✅ | `conventions/testing.md`, `finish/SKILL.md`, `testing-catalogue-guards.md`, `CHANGELOG.md`, `decisions.md` + index ; pas de page « Nouveautés » (accepté à l'approbation) |

## 16. Journal d'avancement

| Date | Statut | Fait / reste |
|---|---|---|
| 2026-10-24 | draft | spécification extraite de l'issue #108 ; trois questions ouvertes (Q-001 à Q-003) |
| 2026-10-24 | specified | réponses de l'ingénieur inscrites : Q-001 A (k = 10, plancher 30 s), Q-002 A (1800 s), Q-003 B (rejeu au plafond) ; D-4 à D-6, REQ-010 ajoutée |
| 2026-10-24 | reviewed | revue d'architecture (§13) : APPROUVER AVEC RÉSERVES ; REQ-005 réécrite (limite de silence), ARCH-005 et ARCH-006, D-7 et D-8 ajoutés ; plan §14 écrit en huit étapes |
| 2026-10-24 | approved | approbation unique des huit specs du 24.10.2026 par l'ingénieur (AskUserQuestion) : plan approuvé tel quel ; toutes les propositions « à confirmer » des revues acceptées comme recommandées ; ordre d'implémentation #108 → #115 → #114 → #113 → #112 → #109 → #107 → #106, un agent par issue ; commits et push autorisés au fil du travail ; écarts et questions notés en §16 et posés à la fin |
| 2026-10-24 | implementation | étapes 1 à 5 faites dans `tests/run_tests.py` : `test_limit`, `stop_reason`, `merge_timings`, `last_run`, `_Watch` (REQ-003, REQ-004, REQ-005, ARCH-001, ARCH-002, ARCH-005) ; `--limits` lu par le fils (ARCH-004, D-7) ; `_run_once` en boucle de sondage, `_stop` borné, abandon nommé par son PID, `taskkill` avec `timeout=` (REQ-001, REQ-002, REQ-007, ARCH-003, UI-001) ; rejeu au plafond dans `run_worker` (REQ-010) ; `execute` et `--suite-timeout` (REQ-006, ARCH-006 ; un futur annulé par `shutdown` n'est pas « done » pour `wait` : retiré à la main). `tests/test_runner.py` : dix tests de plus, verts (35 s). Documentation de l'étape 7 en cours |
| 2026-10-25 | testing | étape 6 (REQ-008) : 112 puis 120 passages de `tests/test_updates.py` sous charge (16 en parallèle ; 12 à côté de 8 cœurs occupés), `faulthandler` à 20 s, aucun blocage : cause non reproduite ; le test passe par un double sans fenêtre de la `QProgressDialog` (`_windowless_progress`), `update_gui.py` intact. Étape 7 : documentation (testing.md, finish, catalogue, CHANGELOG, decisions + index). Commit 65cd243 |
| 2026-10-25 | verification | vérification indépendante (§15) ; réserves levées : `_replayable` et `main` de bout en bout testés (16 tests dans `test_runner`, 40 s). Suite complète avec le nouveau lanceur : 3238 réussis, 10 sautés, 2 échecs indépendants (`test_commands.test_an_example_is_rendered_in_the_window_s_language`, vert seul ; `test_docs_coherence` sur la spec `2026-10-24-verifications-elements-v3.md` d'une autre session), 918 s ; 20 passages de `test_updates` en parallèle, tous verts |
| 2026-10-25 | completed | spec déplacée dans `docs/requirements/completed/` |
