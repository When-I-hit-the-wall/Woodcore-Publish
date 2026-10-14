---
id: 2026-10-07-publication-github-cloudflare
titre: Publication du site et de l'installateur — de GitLab Pages vers GitHub + Cloudflare Pages
status: approved
cree: 2026-10-07
mis_a_jour: 2026-10-07
source: message écrit (conversation du 07.10.2026)
docs: [docs/conventions/build-and-release.md, docs/architecture/layout.md, docs/conventions/testing.md, docs/decisions.md, docs/open-questions.md]
---

# Publication du site et de l'installateur — de GitLab Pages vers GitHub + Cloudflare Pages — Spécification

## 1. Objectif

Le dépôt de Woodcore est passé de GitLab (BFH) à GitHub, où il reste **privé**. Le site (https://lampf1.pages.ti.bfh.ch/woodcore/) et la publication des installateurs reposaient sur GitLab Pages et sur le Package Registry de GitLab ; l'ingénieur veut de nouveau un site, sur la formule gratuite de Cloudflare Pages (https://woodcore.pages.dev/), construit à chaque `push` par une GitHub Action. Cloudflare Pages refuse tout fichier de plus de 25 MiB : l'installateur (94,9 MiB pour la 0.116.0) ne peut donc plus vivre dans le site et sera publié comme *asset* d'une Release GitHub, dans un petit dépôt public qui ne contient que des installateurs.

## 2. Source

> **T1** — « je viens de modifier mon repo. Il est maintenant sur github à la place de gitlab. »
>
> **T2** — « Je souhaite à nouveaux avoir un site internet. »
>
> **T3** — « Est-ce que github permet de lancer une page html comme gitlab? Sinon, est-il possible d'utiliser la version gratuite de Cloudflare pour cela? »
>
> **T4** — « Guide-moi étape par étape. Tu as accès à mon github »
>
> **T5** — « https://woodcore.pages.dev/ » (adresse du projet Cloudflare Pages qu'il vient de créer en Direct Upload)
>
> **T6** — « GitHub reste privé »
>
> **T7** — « Domaine *.pages.dev pour l'instant »
>
> **T8** — « L'ancien GitLab est encore en ligne, mais ne sera plus utilisé et plus actualisé »

## 3. Exigences fonctionnelles

### REQ-001 — Le site est construit par GitHub et publié sur Cloudflare Pages
- **Exigence** : à chaque `push` sur `master` (et à la main), une GitHub Action construit le site avec `python website/build.py`, puis le publie dans le projet Cloudflare Pages `woodcore` en production. Le fichier `.gitlab-ci.yml` est remplacé par `.github/workflows/site.yml`.
- **Source** : T1, T2, T3, T5
- **Priorité** : doit
- **Critère d'acceptation** : après le premier déploiement autorisé par l'ingénieur, https://woodcore.pages.dev/ répond 200 sur `/fr/`, `/de/`, `/en/` et `/version.json` ; le déploiement est celui de *production* (pas une prévisualisation).

### REQ-002 — L'installateur est publié sur une Release GitHub
- **Exigence** : `packaging/publish.py` envoie `dist/Woodcore-<version>-setup.exe` comme asset de la Release `v<version>` du dépôt public `woodcore-releases` (créée si besoin), avec un jeton GitHub de l'ingénieur ; il refuse comme aujourd'hui une version sans notes dans les trois langues, enregistre le fichier, la taille et le SHA-256 dans `website/releases.json`, et n'écrit nulle part le jeton. Il ne remplace jamais un asset existant sans qu'on le lui demande.
- **Source** : T3, T6 (pas de dépôt public du code)
- **Priorité** : doit
- **Critère d'acceptation** : tests de `tests/test_site.py` sur l'adresse d'envoi et la forme des requêtes (serveur factice local, comme celui de l'envoi GitLab d'aujourd'hui) ; `--dry-run` n'envoie rien.

### REQ-003 — Le build vérifie l'installateur sans le mettre dans le site
- **Exigence** : `website/build.py --fetch-installer` télécharge l'installateur de la dernière version publiée sur GitHub depuis son adresse publique (sans jeton), **par le `updates.download` du programme** (taille, SHA-256, redirections) dans un dossier temporaire, en vérifie la taille et le SHA-256 contre `releases.json`, puis **ne le copie pas** dans `public/` (le dossier `download/` n'est plus créé) ; `version.json` et la page de téléchargement nomment l'adresse GitHub. `--installer FICHIER` (aperçu local) vérifie le fichier de la même façon, marque la version comme publiée et ne le copie pas non plus. La réponse finale d'un téléchargement doit rester en HTTPS (refus d'une redirection vers `http://`), dans le build comme dans `updates.download`. L'échec est traité en REQ-007.
- **Source** : T2, T3 ; contrainte CON-001
- **Priorité** : doit
- **Critère d'acceptation** : test sur un serveur factice local (avec une redirection) : bon fichier → manifeste écrit et `public/` sans `.exe` ni dossier `download/` ; redirection vers `http://` refusée.

### REQ-004 — Un Woodcore installé lit le nouveau site et accepte l'installateur de GitHub
- **Exigence** : `calc/tools/updates.py` lit `version.json` sur le nouveau site ; la règle « l'installateur est sur l'hôte du manifeste » devient « l'installateur est en HTTPS sur l'hôte du manifeste **ou sur la liste fermée d'hôtes d'installateurs que le programme nomme** » (forme exacte selon Q-001), l'intégrité restant garantie par le SHA-256 et la taille du manifeste.
- **Source** : T3, T6 ; Q-001
- **Priorité** : doit
- **Critère d'acceptation** : `tests/test_updates.py` — refus d'un hôte hors liste, d'un `http://`, d'un chemin hors du dépôt de releases ; acceptation de l'adresse de la Release ; `validate` du manifeste que le build écrit passe.

### REQ-005 — Les installateurs de l'ère GitLab ne cassent pas le site
- **Exigence** : `releases.json` enregistre **dix** installateurs (0.89.0, 0.90.0, 0.96.0, 0.99.0, 0.110.0, 0.112.0 à 0.116.0) qui sont dans le Package Registry de GitLab et que personne ne republiera (Q-003 B). Ces entrées sont marquées comme tenues par GitLab (champ `installer.hosted`, forme : Q-004) : le build les saute **sans avertissement**, n'en cherche pas sur GitHub et ne les liste pas comme téléchargeables ; leurs pages « Nouveautés » restent. Un test refuse une entrée qui a un SHA-256 mais pas de `hosted` connu. Tant qu'aucune version n'a d'installateur sur GitHub, le site s'ouvre sans téléchargement, avec la phrase « pas encore publié », et sans `version.json` ; la première version publiée par `publish.py` sur GitHub (0.117.0) ouvre le téléchargement et le manifeste.
- **Source** : T1, T8 ; Q-003
- **Priorité** : doit
- **Critère d'acceptation** : test sur le `releases.json` livré : la construction sans réseau n'écrit aucun avertissement sur les dix entrées de l'ère GitLab ; avec un installateur GitHub factice enregistré pour une version neuve, la page et `version.json` la nomment.

### REQ-006 — Le build refuse ce que Cloudflare refuserait
- **Exigence** : `website/build.py` s'arrête (code de sortie non nul), en nommant le fichier, si `public/` contient un fichier de plus de 25 MiB ou plus de 20 000 fichiers (remplace l'avertissement `PAGES_LIMIT` de 100 Mo de GitLab, qui disparaît).
- **Source** : T3 ; CON-002
- **Priorité** : doit
- **Critère d'acceptation** : test avec un seuil abaissé ou un faux gros fichier : le build échoue en nommant le fichier.

### REQ-007 — Un échec de vérification n'efface pas le site en ligne (revue, ARCH-RISK-006)
- **Exigence** : avec `--fetch-installer`, une panne réseau, une taille ou un SHA-256 qui ne concordent pas pour une version **hébergée sur GitHub** fait sortir `build.py` avec un code non nul, et le workflow ne déploie pas : un déploiement Cloudflare *remplace* le précédent, et un site sans `version.json` ni téléchargement effacerait ceux du site en ligne. Ne s'arrêtent pas : l'absence de toute version GitHub (site d'avant 0.117.0) et les entrées de l'ère GitLab.
- **Source** : revue d'architecture ; règle « un fichier malformé arrête » (CLAUDE.md)
- **Priorité** : doit
- **Critère d'acceptation** : test sur serveur factice : SHA-256 faux → `main()` ≠ 0 et pas de `version.json` ; aucune version GitHub → 0 et phrase « pas encore publié ».

## 4. Exigences d'interface (fenêtre, rapport, site)

### UI-001 — La page de téléchargement
- **Exigence** : le lien de téléchargement mène (lien absolu, sans l'attribut `download`, que les navigateurs ignorent entre origines) à l'asset de la Release GitHub ; la page dit en une phrase d'où vient l'installateur (GitHub) — nouvelle clé de `website/strings.json` dans les trois langues — et donne toujours son SHA-256 ; la liste des « versions publiées » ne contient que les versions téléchargeables.
- **Source** : T2
- **Langues** : fr / de / en (`website/strings.json`, `website/content/<lang>/`)
- **Critère d'acceptation** : `tests/test_site.py` — le lien de `download/` est l'adresse de la Release et l'empreinte affichée est celle de `releases.json`, dans les trois langues.

### UI-002 — Ce que dit le site de l'hébergeur (vie privée)
- **Exigence** : `website/content/{fr,de,en}/legal.md` et la clause du même sujet de `legal/LICENSE-{fr,de,en}.txt` ne disent plus « le GitLab de la Haute école spécialisée bernoise » : elles nomment Cloudflare (qui sert le site et `version.json`) et GitHub (qui sert l'installateur), chacun recevant l'adresse IP du poste. Les textes de l'ingénieur ne se traduisent pas : je propose la formulation, **il la relit**.
- **Source** : T2, T3 ; principe § « ce que l'ingénieur écrit à la main »
- **Langues** : fr / de / en
- **Critère d'acceptation** : aucune occurrence de « GitLab » ni de `ti.bfh.ch` dans ces six textes ; l'ingénieur a validé la formulation.

### UI-003 — Nouveautés de la prochaine version
- **Exigence** : la page « Nouveautés » de la prochaine version (0.117.0), dans les trois langues, dit que le site a changé d'adresse, ce que cela change pour les mises à jour (voir Q-002) et où télécharger.
- **Source** : T1, T2, T8
- **Langues** : fr / de / en
- **Critère d'acceptation** : `website/content/{fr,de,en}/changes/0.117.0.md` contient la section (page éventuellement en cours chez une autre session : y ajouter, ne pas la réécrire).

## 5. Exigences d'architecture

### ARCH-001 — Une seule source pour l'adresse du site et le dépôt de releases
- **Exigence** : `website/site.json` porte l'adresse du site et le dépôt de releases (les clés `gitlab` et `package` disparaissent) ; l'adresse d'un installateur est écrite **une seule fois**, par `publish.py`, dans `releases.json` (Q-004), et lue telle quelle par le build. `packaging/publish.py` les lit là. Toute copie qui doit rester en dehors — `calc/tools/updates.py` (`FEED_URL`, hôte et chemin d'installateurs), `calc/tools/legal.py` (`SITE`), `packaging/woodcore.iss` (deux URL), `legal/LICENSE-*.txt` (lus en `utf-8-sig`, le BOM reste), `README.md` — est **gardée par un test d'égalité**, comme l'est déjà `FEED_URL` (`tests/test_updates.py:85`).
- **Source** : principe 1 (une source de vérité), CLAUDE.md
- **Critère d'acceptation** : un test lit chaque copie et l'égale à `site.json` ; changer l'adresse à un endroit seulement fait échouer la suite en nommant le fichier.

### ARCH-002 — Les épingles de version suivent le nouveau fichier de workflow
- **Exigence** : `.gitlab-ci.yml` est le fichier où `typst_check.pin` réécrit `TYPST_VERSION` et que `tests/test_site.py` égale à `requirements.txt` ; `docs/conventions/testing.md` y lit aussi l'image Python. Ces trois mécanismes (`calc/tools/typst_check.py` `CI_FILE`, `tests/test_typst_check.py`, `tests/test_site.py`) et les trois chaînes de `calc/tools/typst_gui.py` (fr/de/en) pointent désormais vers `.github/workflows/site.yml`, avec la même forme `TYPST_VERSION: "x.y.z"`.
- **Source** : inféré — `grep` du dépôt
- **Critère d'acceptation** : `python tests/run_tests.py -k typst` et `-k site` passent ; épingler Typst réécrit le workflow.

### ARCH-003 — Secrets et chaîne de confiance de l'Action
- **Exigence** : aucun secret dans le dépôt ; `CLOUDFLARE_API_TOKEN` et `CLOUDFLARE_ACCOUNT_ID` sont des *secrets du dépôt* créés par l'ingénieur ; le workflow n'a que `permissions: contents: read` ; il n'utilise que les actions de GitHub (`checkout`, `setup-python`, épinglées) et lance `wrangler` en version fixe par `npx`, sans action tierce du Marketplace ; le jeton Cloudflare n'a que le droit *Cloudflare Pages : Edit*.
- **Source** : inféré — jeton Cloudflare sur un dépôt privé, supply chain
- **Critère d'acceptation** : relecture du workflow par le vérificateur indépendant ; test qui lit le workflow et refuse un `uses:` hors `actions/` et une permission d'écriture.

### ARCH-004 — Décision et coût écrits
- **Exigence** : une entrée dans `docs/decisions.md` (§13) **remplace expressément** la décision de la ligne 195 (« installateur sur GitLab Pages par le Package Registry » ; le prix « seul le dernier installateur est servi » disparaît, les Releases les gardent tous) et celle de la ligne 99 (jeton `WOODCORE_GITLAB_TOKEN` → `WOODCORE_GITHUB_TOKEN`, « demandé à chaque publication » inchangé), **signale** à l'ingénieur celle de la ligne 190 (conditions d'usage du GitLab de la HES et propriété face à l'employeur — à lui de trancher) et dit pourquoi Cloudflare Pages + Releases GitHub, ce que cela coûte (deux fournisseurs ; l'installateur hors de l'hôte du manifeste ; une règle de confiance assouplie, Q-001 ; un installateur qui contient les tableaux SIA lisibles, désormais dans un dépôt public, plus durable et indexable que la page de la BFH, CON-003), et `docs/conventions/build-and-release.md` §12 décrit la nouvelle chaîne ; `docs/open-questions.md` garde ce qui reste ouvert (domaine propre, pont, Cloudflare gratuit).
- **Source** : CLAUDE.md « Preserve the architecture … docs/decisions.md says why and what it costs »
- **Critère d'acceptation** : les trois fichiers à jour, sans plus aucune mention de GitLab comme hébergeur actuel (l'historique reste).

### ARCH-005 — L'adresse précède le numéro de version (revue, ARCH-RISK-005)
- **Exigence** : l'installateur 0.117.0 est construit par le hook `post-commit` au commit qui change `VERSION`. Tout ce qui y est figé — `FEED_URL`, la règle d'hôte d'installateur, `legal.SITE`, `legal/LICENSE-*.txt`, `woodcore.iss` — porte donc la **nouvelle** adresse **avant** ce commit, sinon la 0.117.0 chercherait ses mises à jour sur l'ancien site pour toujours. Un test `test_no_live_file_names_the_retired_host` balaie `calc/`, `packaging/`, `legal/`, `website/` (sauf `releases.json`), `README.md` et `.github/` à la recherche de `ti.bfh.ch` et de `gitlab`, en ignorant `.claude/worktrees/`.
- **Source** : revue
- **Critère d'acceptation** : le test passe ; le compte rendu final rappelle l'ordre des commits à l'ingénieur.

### ARCH-006 — Hôte d'installateur exact, pas un préfixe de chaîne (revue, ARCH-RISK-003)
- **Exigence** : `updates.validate` accepte l'URL d'un installateur si c'est l'hôte du manifeste **ou** si : schéma `https`, `hostname == "github.com"`, ni port, ni identifiant, ni mot de passe, ni requête, ni fragment, chemin commençant par `/When-I-hit-the-wall/woodcore-releases/releases/download/`, sans segment `..`, `%2e`, `%2f` ni barre oblique inverse. `updates.download` reste indifférent à l'hôte (ses tests lui donnent `http://127.0.0.1`) mais refuse une réponse finale qui n'est pas en HTTPS ; les hôtes de redirection de GitHub ne sont **pas** épinglés (ils ont déjà changé une fois). Les docstrings de `updates.py` (ligne 7 et le commentaire de `FEED_URL`) disent la nouvelle règle.
- **Source** : revue ; Q-001 A
- **Critère d'acceptation** : `tests/test_updates.py` refuse `http`, un autre hôte, `github.com.evil.com`, `github.com@evil.com`, un autre dépôt, `..`, `%2e%2e`, un port, une requête, `raw.githubusercontent.com` ; accepte l'adresse de la Release ; le préfixe égale celui de `site.json`.

### ARCH-007 — Aucun jeton ne suit une redirection (revue, ARCH-RISK-004 et 010)
- **Exigence** : dans `publish.py`, le jeton GitHub est posé par `add_unredirected_header` (urllib rejoue sinon les en-têtes sur une redirection) et lu dans `WOODCORE_GITHUB_TOKEN` seul (jamais `GITHUB_TOKEN`, souvent un jeton large) ; jeton fin limité à `woodcore-releases`, droit *Contents : write*. L'adresse d'envoi est celle que l'API donne (`upload_url`). Un asset déjà présent est refusé en nommant `--replace`, que seul cet argument autorise à supprimer. La Release ne recopie pas les notes (elles sont dans `releases.json` : une seconde copie qui vieillirait).
- **Source** : revue
- **Critère d'acceptation** : tests de `publish` sur serveur factice : créer-ou-prendre la Release, en-têtes, `upload_url`, refus d'un asset existant sans `--replace`, jeton absent des requêtes vers un autre hôte.

## 6. Contraintes

- **CON-001** — Cloudflare Pages (gratuit) : 25 MiB par fichier et 20 000 fichiers pour un déploiement par `wrangler` (la limite des 500 constructions par mois vise les constructions faites par Cloudflare, pas le Direct Upload ; celle de 1 000 fichiers vise le glisser-déposer du tableau de bord). Source : T3 ; revue ; à revérifier à l'implémentation.
- **CON-002** — GitHub Actions sur dépôt privé, formule gratuite : 2 000 minutes Linux par mois ; la construction du site (trois langues d'exemples compilés par Typst ; la revue estime 8 à 12 minutes sur un exécuteur à 2 vCPU) doit y tenir : concurrence annulante, `paths-ignore`, déclenchement par `push` et `workflow_dispatch` seulement. Source : inféré.
- **CON-003** — Le dépôt du code reste privé (les valeurs des normes SIA y sont) ; seul `woodcore-releases` est public et ne contient que des installateurs, déjà publics aujourd'hui sur le site BFH. Source : T6.
- **CON-004** — Domaine `*.pages.dev` : l'adresse est `https://woodcore.pages.dev/`, à la racine (aujourd'hui `…/woodcore/` dans un sous-dossier) ; le site produit des liens relatifs (`page.url`) — à vérifier à la revue. Source : T5, T7.
- **CON-005** — Les Woodcore déjà installés lisent `https://lampf1.pages.ti.bfh.ch/woodcore/version.json` et refusent un installateur hors de cet hôte : ils **ne verront aucune version publiée sur le nouveau site**. Source : T8 ; voir Q-002.
- **CON-006** — Rien n'est publié, poussé, téléversé ni déployé sans le mot explicite de l'ingénieur ; je n'ai pas accès à son compte GitHub depuis cette session (connecteur non autorisé, `gh` absent) : les secrets, le dépôt `woodcore-releases` et les jetons sont créés par lui. Source : CLAUDE.md.
- **CON-007** — Plusieurs sessions modifient ce dépôt en même temps ; aucun `checkout --`/`stash`/`reset`/`clean` ; `CHANGELOG.md`, `docs/decisions.md`, `docs/conventions/testing.md` s'éditent par Edit ciblé en CRLF. Source : CLAUDE.md.

## 7. Décisions prises

- **D-001** — Le dépôt GitHub `When-I-hit-the-wall/Woodcore` reste privé (T6). Prix accepté : pas de GitHub Pages (réservé aux dépôts publics ou aux formules payantes), donc Cloudflare.
- **D-002** — Hébergement du site : Cloudflare Pages, projet `woodcore`, Direct Upload, déploiement par GitHub Action (T5). Prix : un fournisseur de plus ; 25 MiB par fichier.
- **D-003** — Adresse : `https://woodcore.pages.dev/` pour l'instant (T7) ; un domaine à lui est une évolution possible (§9).
- **D-004** — L'ancien site GitLab n'est plus actualisé (T8). Prix : voir CON-005.
- **D-005** — Q-001 A : liste fermée dans le programme — HTTPS, hôte `github.com`, chemin sous `/When-I-hit-the-wall/woodcore-releases/releases/download/`, plus SHA-256 et taille du manifeste. Prix accepté : la règle « l'installateur est sur le serveur du manifeste » n'est plus vraie ; un compte Cloudflare compromis (qui sert le manifeste) suffirait à faire annoncer un autre installateur, un compte GitHub seul non.
- **D-006** — Q-002 A : aucun pont ; les postes déjà installés ne seront pas avertis. La page « Nouveautés » 0.117.0 et l'ingénieur annoncent la nouvelle adresse. Prix accepté : une mise à jour manuelle, une fois.
- **D-007** — Q-003 B : dépôt public `When-I-hit-the-wall/woodcore-releases` (la question portait sur le nom ; il garde la proposition) ; **0.116.0 n'est pas republiée**, la première version sur GitHub est 0.117.0 : le site s'ouvre sans téléchargement jusque-là. Prix accepté : pas de téléchargement tant que 0.117.0 n'est pas publiée.

## 8. Hors périmètre

- Un domaine personnel ou un autre fournisseur de DNS.
- Rendre public le dépôt du code ; GitHub Pages.
- Cloudflare R2, Workers, Access, analytics.
- Supprimer le projet GitLab ou y publier quoi que ce soit (sauf pont, Q-002).
- **Pousser, téléverser, déployer** : à chaque fois l'ingénieur le dit.
- Toucher les projets de l'ingénieur (`../Musterprojekt/`).

## 9. Idées non retenues comme exigences

- Un domaine à lui plus tard, pour qu'une prochaine migration ne casse plus les mises à jour des Woodcore installés (T7 « pour l'instant »).
- Une action `workflow_dispatch` pour republier à la main (retenue comme commodité dans REQ-001, pas comme exigence séparée).

## 10. Questions

### Q-001 — Quelle règle de confiance pour l'installateur hébergé hors du site ?
- **Pourquoi elle compte** : `updates.py` refuse aujourd'hui tout installateur qui n'est pas sur l'hôte du manifeste (« un manifeste qui pointe ailleurs n'est pas un manifeste à qui ce programme a été conçu de faire confiance »). Cloudflare ne peut pas héberger le fichier : il faut assouplir la règle ou changer l'hébergement.
- **Options** :
  - **A (recommandée)** — liste fermée dans le programme : `https://github.com/When-I-hit-the-wall/woodcore-releases/releases/download/…`, hôte **et** début du chemin fixés, plus le SHA-256 et la taille du manifeste. On y perd : l'idée que « manifeste et fichier viennent du même serveur » ; un compte GitHub compromis ne suffit pas à faire passer un fichier (le SHA-256 est dans le manifeste, servi par Cloudflare), mais un compte Cloudflare compromis suffirait.
  - **B** — garder la règle de l'hôte unique : l'installateur sous le même domaine via Cloudflare R2 et un Worker. On y perd : la carte bancaire exigée par R2, un composant de plus, et la simplicité.
  - **C** — rendre le dépôt public et utiliser GitHub Pages seul. On y perd : D-001.
- **Réponse** : A — liste fermée (07.10.2026, D-005)

### Q-002 — Que faire des Woodcore déjà installés (pont) ?
- **Pourquoi elle compte** : ils lisent l'ancien site et ne verront jamais 0.117.0.
- **Options** :
  - **A (recommandée)** — aucun pont : les postes installés restent sur leur version, l'ingénieur annonce la nouvelle adresse à ceux qui l'utilisent, et la page « Nouveautés » 0.117.0 l'explique. On y perd : la mise à jour automatique de ces postes, une fois.
  - **B** — un dernier envoi sur GitLab Pages : une version « pont » (installateur + `version.json` sur l'ancien hôte, ~70 Mo, sous la limite de 100 Mo) qui contient déjà la nouvelle adresse. On y perd : du temps et le fait de réutiliser GitLab après coup, et le GitLab doit encore accepter un push.
- **Réponse** : A — aucun pont (07.10.2026, D-006)

### Q-003 — Le dépôt de releases et l'installateur 0.116.0
- **Pourquoi elle compte** : nom et visibilité du dépôt entrent dans `site.json`, `updates.py` et les tests ; et sans installateur sur GitHub, le site neuf n'a rien à proposer au téléchargement.
- **Options** :
  - **A (recommandée)** — dépôt **public** `When-I-hit-the-wall/woodcore-releases`, et republication de `dist/Woodcore-0.116.0-setup.exe` (déjà construit, même SHA-256) pour que le site ait un téléchargement dès le premier jour.
  - **B** — même dépôt, mais on attend la 0.117.0 : le site s'ouvre sans téléchargement et sans `version.json` jusque-là.
  - **C** — un autre nom ou un autre compte (à préciser).
- **Réponse** : B — attendre la 0.117.0 (07.10.2026, D-007)

### Q-004 — Comment marquer les installateurs de l'ère GitLab et noter l'adresse des nouveaux ? (forme de `releases.json`, soulevée par la revue)
- **Pourquoi elle compte** : c'est la forme d'un fichier de données versionné ; trois lecteurs et dix entrées en dépendent.
- **Options** :
  - **A (recommandée)** — `installer.hosted: "gitlab"` sur les dix entrées existantes ; `publish.py` écrit `hosted: "github"` **et** `installer.url` (l'adresse complète de l'asset) pour les nouvelles. Un seul prédicat `has_download(release)` dans le build ; la formule de l'adresse n'existe qu'une fois (dans `publish.py`). On y perd : deux champs de plus.
  - **B** — aucun marqueur : une entrée sans `installer.url` est « de l'ère GitLab ». On y perd : l'explicite (un champ absent veut dire quelque chose).
- **Réponse** : A — hosted + url (07.10.2026)

## 11. Critères d'acceptation

- [x] REQ-001 — workflow `.github/workflows/site.yml` ; déploiement de production de https://woodcore.pages.dev/ (après accord)
- [x] REQ-002 — `publish.py` envoie vers une Release de `woodcore-releases` ; tests sur serveur factice
- [x] REQ-003 — le build vérifie sans copier ; manifeste seulement si SHA-256 et taille concordent
- [x] REQ-004 — `updates.py` accepte l'hôte de releases et refuse tout autre ; tests
- [x] REQ-005 — les entrées de l'ère GitLab sont sautées sans avertissement ; site sans téléchargement tant que rien n'est sur GitHub
- [x] REQ-006 — le build refuse (sortie non nulle) un fichier de plus de 25 MiB ou plus de 20 000 fichiers
- [x] REQ-007 — un échec de vérification GitHub arrête le build, donc le déploiement
- [x] UI-001 — lien et empreinte du téléchargement, trois langues
- [ ] UI-002 — six textes légaux sans GitLab ; formulation relue par l'ingénieur
- [x] UI-003 — page Nouveautés 0.117.0 dans les trois langues
- [x] ARCH-001 — chaque copie de l'adresse égalée à `site.json` par un test
- [x] ARCH-002 — `typst_check`, `test_site`, `test_typst_check`, `testing.md`, chaînes `typst_gui` suivent le workflow
- [x] ARCH-003 — secrets, permissions et actions du workflow contrôlés par un test
- [x] ARCH-004 — `decisions.md` (lignes 195 et 99 remplacées, 190 signalée), `build-and-release.md` §12, `layout.md`, `README.md`, `open-questions.md`
- [x] ARCH-005 — l'adresse précède `VERSION` ; `test_no_live_file_names_the_retired_host`
- [x] ARCH-006 — règle d'hôte exacte, tests nommés
- [x] ARCH-007 — jeton jamais rejoué, `--replace` seul supprime
- [ ] Documentation : sections de `docs/` mises à jour, entrée `CHANGELOG.md`, page « Nouveautés » fr/de/en.
- [ ] Tests : `tests/test_site.py`, `test_updates.py`, `test_typst_check.py` étendus ; `python tests/run_tests.py` passe (noms des échecs relevés s'il y en a).

## 12. Traçabilité

| Source | Élément | Statut |
|---|---|---|
| T1 | REQ-001, REQ-005, UI-003 | capturé |
| T2 | REQ-001, REQ-003, UI-001, UI-002, UI-003 | capturé |
| T3 | REQ-001…REQ-004, REQ-006, UI-002 | capturé |
| T4 | CON-006 | contrainte de méthode |
| T5 | REQ-001, D-002, CON-004 | capturé |
| T6 | D-001, CON-003, REQ-002, REQ-004 | décision |
| T7 | D-003, CON-004, §9 | décision |
| T8 | D-004, D-006, CON-005, REQ-005, UI-003 | décision (Q-002 A) |
| revue | REQ-007, ARCH-005 à ARCH-007, Q-004 | ajouté par la revue d'architecture |

### Points de la source non résolus

_(aucun : Q-001 à Q-003 répondues le 07.10.2026)_

## 13. Revue d'architecture

**Verdict : APPROUVER AVEC RÉSERVES** (revue indépendante, `architecture-reviewer`, 07.10.2026). Rien de bloquant.

**Modules concernés.** `website/build.py` (`release_with_installer` 632, `place_installer`, `installer_url`, `write_manifest` 665-680, `download_card` 971-982, `PAGES_LIMIT` 68 et 1186, `fetch_from_registry` 1214) ; `website/site.json` ; `website/releases.json` ; `packaging/publish.py` (constantes GitLab 34-39, `upload` 102) ; `calc/tools/updates.py` (`FEED_URL` 27, `validate` 80-105 dont la règle de l'hôte à 96, `changes` 185-195, `download` 202) ; `calc/tools/legal.py:16` ; `calc/tools/typst_check.py` (`CI_FILE` 29, `_CI`, `pin` 210-231) ; `calc/tools/typst_gui.py` (six chaînes) ; `packaging/woodcore.iss:18-19` ; `legal/LICENSE-*.txt` (lignes 9 et 32, BOM UTF-8) ; `website/content/*/legal.md:19` ; `README.md` ; `.gitlab-ci.yml`.

**À réutiliser.** `updates.download` (Qt-free, taille, SHA-256, redirections) pour la vérification du build — pas de second téléchargeur ; `publish.upload` et son `opener` injectable ; `typst_check.pin` tel quel si le workflow porte une ligne `TYPST_VERSION: "x.y.z"` unique ; `test_updates._Site` (serveur factice 127.0.0.1, à étendre d'une redirection) ; `Page.url` est déjà relatif, donc un déploiement à la racine de `woodcore.pages.dev` fonctionne (CON-004 levée). Aucun `_headers`/`_redirects` nécessaire : Pages sert `index.html`, `404.html` et revalide `version.json`.

**Risques retenus** (les sept « importants » sont repris dans les exigences ou le plan) : RISK-001 branche de production Cloudflare (`main` par défaut en Direct Upload, la branche du dépôt est `master` : `--branch` explicite et vérifié par `curl -I`, pas par la couleur de l'Action, et `--commit-message="$GITHUB_SHA"`) ; RISK-002 dix entrées de l'ère GitLab et non trois, installateur de 94,9 MiB (corrigé) ; RISK-003 règle d'hôte exacte (ARCH-006) ; RISK-004 redirection de GitHub vers `release-assets.githubusercontent.com`, hôtes non épinglés, HTTPS final exigé, jeton jamais rejoué (ARCH-006, ARCH-007) ; RISK-005 l'adresse avant `VERSION` (ARCH-005) ; RISK-006 échec = build en erreur (REQ-007) ; RISK-007 `--installer` sans copie et limites qui lèvent (REQ-003, REQ-006) ; RISK-008 trois décisions de `decisions.md` contredites (ARCH-004) ; RISK-009 `tests/test_typst_check.py` écrit le nom du fichier en dur, lignes 89, 91, 105, 137 (plan, étape 5) ; RISK-010 déroulé de `publish.py` (ARCH-007) ; RISK-011 minutes et confiance du workflow (CON-002, plan étape 5) ; RISK-012 adresse écrite à plus d'endroits que prévu (plan étape 6) ; RISK-013 mineurs : `download.md` de trois langues dit encore Typst 0.14.2 quand l'épingle est 0.15.1 (copie qui a vieilli, hors périmètre, signalée à l'ingénieur), attribut `download` inutile, `docs/` et `.claude/` non suivis par git (les modifications de documentation n'entreront dans aucun commit tant que l'ingénieur ne les ajoute pas), installateur contenant les tableaux SIA désormais dans un dépôt public.

**Approche.** `site.json` porte `base_url` et `releases_repo` ; `publish.py` parle à GitHub et écrit `hosted` et `installer.url` ; le build n'a qu'un prédicat `has_download` et ne copie jamais l'installateur ; `updates.py` a une règle d'hôte exacte ; l'adresse précède le numéro de version ; le workflow est minimal (actions de GitHub épinglées par SHA, `wrangler` en version fixe par `npx`, aucune action tierce, `permissions: contents: read`, déclenchements `push` et `workflow_dispatch` seulement, `concurrency` annulante, `paths-ignore`).

**Tests.** `test_site.py` : `test_the_installer_is_never_put_in_the_site`, `test_a_release_hosted_by_gitlab_is_skipped_without_a_warning`, `test_every_release_with_an_installer_says_where_it_is_hosted`, `test_the_download_link_is_the_release_asset_and_its_sha_is_shown` (fr, de, en), `test_a_fetch_that_fails_or_differs_stops_the_build_and_writes_no_manifest`, `test_the_build_refuses_a_file_over_25_MiB_or_20000_files`, `test_the_workflow` (remplace `test_the_ci_builds_the_site_with_the_typst_the_program_carries`), `test_every_copy_of_the_site_address_is_site_jsons`, `test_no_live_file_names_the_retired_host`, trois tests de publication ; `test_updates.py` : règle d'hôte fermée, préfixe égal à `site.json`, redirection suivie mais pas vers `http` ; `test_typst_check.py` : nom du fichier tiré de `CI_FILE.name`, épingle sur le vrai workflow.

## 14. Plan d'implémentation

**Avant tout code — ce que fait l'ingénieur** (je ne peux pas, CON-006) : (a) créer le dépôt **public** `When-I-hit-the-wall/woodcore-releases` avec un `README` (un dépôt vide ne peut pas porter d'étiquette) ; (b) un jeton GitHub fin, limité à ce dépôt, droit *Contents : write*, dans la variable d'environnement `WOODCORE_GITHUB_TOKEN` ; (c) un jeton Cloudflare *Pages : Edit* et l'identifiant du compte, enregistrés comme secrets du dépôt `Woodcore` (`CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID`) ; (d) relever dans Cloudflare › woodcore › Settings › Builds la **branche de production** (probablement `main`).

1. **Données** (ARCH-001, REQ-005, Q-004) — `website/site.json` (`base_url`, `releases_repo`, sans `gitlab` ni `package`) ; `website/releases.json` : `installer.hosted: "gitlab"` sur les dix entrées, texte du `_comment` mis à jour, Edit ciblé (LF). Preuve : `test_every_release_with_an_installer_says_where_it_is_hosted`.
2. **Le programme installé** (REQ-004, ARCH-006) — `calc/tools/updates.py` (CRLF, Edit ciblé) : `FEED_URL`, règle d'hôte exacte, HTTPS final dans `download`, docstrings ; `tests/test_updates.py` (cas hostiles nommés, redirection, égalité avec `site.json`). Preuve : `-k updates`.
3. **La publication** (REQ-002, ARCH-007) — `packaging/publish.py` : GitHub (créer-ou-prendre la Release, `upload_url`, jeton non rejoué, `--replace`, `--dry-run`), écrit `hosted` et `installer.url` ; tests sur serveur factice. Preuve : `-k site`, tests de publication.
4. **Le site** (REQ-003, REQ-005, REQ-006, REQ-007, UI-001) — `website/build.py` (CRLF) : `has_download`, `place_installer` par `updates.download` dans un dossier temporaire sans copie, sortie non nulle sur échec GitHub, limites qui lèvent, `download_card` absolu sans `download`, historique des seules versions téléchargeables, suppression de `fetch_from_registry` et de `PAGES_LIMIT` ; `website/strings.json` (CRLF) : phrase d'origine en fr, de, en ; tests du site. Preuve : `-k site`.
5. **L'intégration continue** (REQ-001, ARCH-002, ARCH-003) — `.github/workflows/site.yml` (LF) avec `TYPST_VERSION: "0.15.1"` en `env:` du job, somme de contrôle de l'archive Typst, `python-version: "3.13"`, `--branch=<production>` explicite avec commentaire ; suppression de `.gitlab-ci.yml` (contenu repris) ; `typst_check.CI_FILE`, six chaînes de `typst_gui.py`, `tests/test_typst_check.py` (nom tiré de `CI_FILE.name`), `test_the_workflow`, `docs/conventions/testing.md` (tableau des épingles). Preuve : `-k typst`, `-k site`.
6. **Les copies de l'adresse** (ARCH-001, ARCH-005, UI-002) — `calc/tools/legal.py`, `packaging/woodcore.iss`, `legal/LICENSE-{fr,de,en}.txt` (BOM conservé), `README.md`, `website/content/{fr,de,en}/legal.md` (formulation Cloudflare et GitHub **proposée** à l'ingénieur) ; tests d'égalité et de balayage. Preuve : `-k legal`, `-k site`.
7. **Documentation** (ARCH-004, UI-003) — `docs/decisions.md` (CRLF, Edit ciblé : entrée remplaçant 195 et 99, signalant 190), `docs/conventions/build-and-release.md` §12, `docs/architecture/layout.md`, `docs/open-questions.md`, `docs/ui/window.md` (172, 303), `CHANGELOG.md`, section « Nouveautés » dans `website/content/{fr,de,en}/changes/0.117.0.md` (page éventuellement en cours chez une autre session : y ajouter).
8. **Essai et vérification** — `python tests/run_tests.py` en entier, sortie dans un fichier, noms des échecs relevés ; puis `verify-requirements`.

**Ce que le plan ne fait pas** : commit, `push`, envoi sur GitHub ou Cloudflare, publication d'une Release, `VERSION`. À la fin je rappelle l'ordre que la revue exige : **le commit de l'adresse avant celui du numéro de version**, puis `python packaging/publish.py`, puis le `push` qui déclenche le premier déploiement.

## 15. Vérification

_(Vérificateur indépendant `requirements-verifier`, 07.10.2026, tests lancés un `-k` à la fois ; première ronde.)_

| Élément | Verdict | Preuve |
|---|---|---|
| REQ-001 | ✅ (08.10.2026) | **Déployé et vérifié en ligne** : commits `ae996b6` et `30e32b6`, https://woodcore.pages.dev/ répond 200 sur `/`, `/fr/`, `/de/`, `/en/`, les pages de téléchargement, de documentation, légale et « Nouveautés » 0.117.0, `version.json` 404 voulu (aucun installateur sur GitHub), page d'erreur du site sur une adresse inconnue, aucune erreur dans la console du navigateur. Le premier déploiement, avec `--branch=master`, était vert et allait en *Preview* : la branche de production d'un projet Direct Upload est `main` ; le workflow la lit maintenant dans le projet (`production_branch`). Ancienne note : | `.github/workflows/site.yml` (push sur `master` + `workflow_dispatch`, `wrangler pages deploy public --project-name=woodcore --branch="${PAGES_BRANCH}"`), YAML chargé par PyYAML, `.gitlab-ci.yml` supprimé. Le critère « 200 sur woodcore.pages.dev » n'est vérifiable qu'après le premier déploiement, que l'ingénieur autorise (CON-006) ; `PAGES_BRANCH: main` est à confirmer dans Cloudflare. |
| REQ-002 | ✅ | `packaging/publish.py` : `release_of`, `upload`, `record`, `--dry-run` revient avant `token()` ; 4 tests de publication, `-k publish` 8 passed |
| REQ-003 | ✅ | `website/build.py` `place_installer` : `updates.download` dans un dossier temporaire, aucune copie, pas de `download/` ; `test_the_manifest_written…` ; redirection hors HTTPS refusée (`test_updates`). Mineur : le build est testé avec un `urlopen` remplacé, la vraie redirection l'est dans `test_updates` |
| REQ-004 | ✅ | `calc/tools/updates.py:83-99` ; `-k updates` 17 passed |
| REQ-005 | ✅ | dix `hosted: "gitlab"` ; `has_download` ; `check_releases` ; `test_the_installers_of_the_gitlab_years…` : 0 requête, 0 avertissement, 0 erreur |
| REQ-006 | ✅ | `FILE_LIMIT`, `FILES_LIMIT`, sortie 1 ; `PAGES_LIMIT` et `fetch_from_registry` disparus ; `test_the_build_refuses_a_file_or_a_count…` |
| REQ-007 | ✅ | `main()` retourne 1 ; `test_a_check_that_fails_stops_the_build…` (SHA faux, contenu inversé, aucune réponse) ; aucune version GitHub → 0 |
| UI-001 | ✅ | `download_card` : lien absolu sans `download`, empreinte, `download_origin` en fr/de/en ; historique limité à `has_download` |
| UI-002 | ⚠️ | six textes nomment Cloudflare et GitHub, aucun « GitLab » ni `ti.bfh.ch`, pas de « ß » ; **la relecture de la formulation par l'ingénieur reste à faire** |
| UI-003 | ✅ | une puce ajoutée dans chacune des trois pages `0.117.0.md` (le reste des pages est d'une autre session) |
| ARCH-001 | ✅ | `test_every_copy_of_the_site_address_is_site_jsons` |
| ARCH-002 | ✅ | `typst_check.CI_FILE`, `typst_gui` ×3 langues, `test_typst_check` 14 passed, `testing.md` |
| ARCH-003 | ✅ | `permissions: contents: read`, actions `actions/*` épinglées par SHA de 40 hex (vérifiées par l'API de GitHub), `wrangler@4.148.0`, secrets seulement dans l'étape de déploiement ; mineur : pas de somme de contrôle de l'archive Typst (écart écrit dans `open-questions.md`) |
| ARCH-004 | ✅ | `decisions.md` : la ligne 195 marquée remplacée, la 99 annotée, la 190 signalée ; §12, `layout.md`, `window.md`, `open-questions.md` à jour |
| ARCH-005 | ✅ | adresse dans tous les fichiers figés avant `VERSION` (encore 0.116.0) ; `test_no_live_file_names_the_retired_host` resserré après la vérification (le mot « gitlab » est refusé partout sauf dans cinq fichiers d'historique nommés) ; l'ordre des commits est rappelé dans le compte rendu final |
| ARCH-006 | ✅ | trente adresses sondées par le vérificateur (look-alikes, userinfo, port, requête, `..`, `%2e`, autre dépôt, `GitHub.com`…) toutes refusées ; l'adresse de la Release et l'hôte du site acceptés |
| ARCH-007 | ✅ après correction | `add_unredirected_header`, hôtes limités, `--replace` seul chemin de suppression, `WOODCORE_GITHUB_TOKEN` seul lu. **Défaut trouvé et corrigé** : `test_only_the_woodcore_token_is_read…` bloquait sur `getpass` quand stdin est une console ou NUL (`isatty()` vaut vrai sur NUL sous Windows) ; le test isole maintenant `sys.stdin`, `1 passed` avec stdin sur NUL |

**Restent, pour l'ingénieur** : relire la formulation légale (UI-002) ; créer le dépôt `woodcore-releases`, les jetons et les secrets ; confirmer `PAGES_BRANCH` ; premier déploiement et `curl -I https://woodcore.pages.dev/version.json` ; l'ordre des commits (adresse, puis `VERSION` 0.117.0, puis `publish.py`, puis `push`).

## 16. Journal d'avancement

| Date | Statut | Fait / reste |
|---|---|---|
| 2026-10-07 | draft | spécification extraite de la conversation ; 3 questions ouvertes (Q-001 à Q-003) |
| 2026-10-07 | specified | Q-001 A (liste fermée), Q-002 A (aucun pont), Q-003 B (attendre 0.117.0) ; REQ-005 reformulée |
| 2026-10-07 | reviewed | revue d'architecture : APPROUVER AVEC RÉSERVES ; REQ-007, ARCH-005 à 007, Q-004 ajoutés ; plan §14 écrit ; en attente de l'approbation unique |
| 2026-10-07 | approved | Q-004 A ; plan §14 approuvé par l'ingénieur (une approbation) ; implémentation à venir |
| 2026-10-07 | implementation | étapes 1 et 2 faites : site.json (base_url, releases_repo), releases.json (hosted: gitlab ×10), updates.py (FEED_URL, installer_address_problem, HTTPS final), test_updates.py 17 ✓ — ARCH-006 en place, REQ-004 en place |
| 2026-10-07 | implementation | étapes 3, 4, 5 faites : publish.py (GitHub, REQ-002, ARCH-007) ; build.py (has_download, vérification sans copie via updates.download, sortie 1 sur échec, limites 25 MiB / 20 000, lien absolu, strings download_origin ; REQ-003/005/006/007, UI-001) ; workflow .github/workflows/site.yml, .gitlab-ci.yml supprimé, typst_check/typst_gui/test_typst_check suivent (ARCH-002/003) ; tests verts : updates 17, typst_check 14, site (manifest, check_that_fails, gitlab_years, hosted, limits, no_manifest, names_the_page, workflow), publish |
| 2026-10-07 | implementation | étape 6 faite : legal.py, woodcore.iss, LICENSE ×3 (BOM gardé), legal.md ×3, README ; tests test_every_copy_of_the_site_address_is_site_jsons et test_no_live_file_names_the_retired_host verts, test_legal 9 ✓ ; reste : étape 7 documentation, 8 essai complet et vérification |
| 2026-10-07 | testing | étape 7 faite (decisions.md, open-questions, build-and-release §12, window.md, layout, testing.md, CHANGELOG, Nouveautés 0.117.0 ×3) ; étape 8 : suite complète lancée |
| 2026-10-07 | testing | reprise après redémarrage de l'ordinateur : la suite complète du 20:24 était interrompue (journal tronqué, aucun échec nommé) ; relancée |
| 2026-10-07 | verification | vérification indépendante (1re ronde) : tout ✅ sauf REQ-001 (déploiement, attendu) et UI-002 (relecture de l'ingénieur) ; deux défauts de test corrigés : le test du jeton bloquait sur getpass (stdin = NUL), le balayage « gitlab » resserré ; suite complète et test_site relancés |
| 2026-10-07 | verification | 08.10.2026 : site déployé et vérifié en ligne (REQ-001 ✅) ; suite complète 2570 passés, 17 ignorés, 6 échecs dont 5 d'états intermédiaires d'autres sessions (display_view, views : passent aujourd'hui) et 1 sans rapport (test_title_page : la copie du formulaire BFH du dépôt ../templates diffère du formulaire intégré) ; reste UI-002 (relecture de la formulation légale par l'ingénieur) avant « completed » |
| 2026-10-07 | approved | plan §14 approuvé par l'ingénieur (une approbation) ; implémentation à venir |
