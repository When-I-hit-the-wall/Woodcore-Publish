---
id: 2026-10-07-vues-onglets-slider-et-volets
titre: Vues par onglet (sélecteur de vue près des langues), volet de gauche des plans, enregistrement automatique, fin de l'avertissement « no load workbook »
status: verification
cree: 2026-10-07
mis_a_jour: 2026-10-07
source: transcription dictée (message du 07.10.2026)
docs: [docs/ui/window.md, docs/architecture/principles.md, docs/decisions.md, docs/typst/api-conventions.md]
---

# Vues par onglet, volet de gauche des plans, enregistrement automatique — Spécification

## 1. Objectif

Les onglets de Woodcore mélangent trop d'informations : « on se perd un peu ». Un sélecteur de vue, placé à gauche des boutons de langue, sépare chaque onglet en vues d'une tâche chacune. Les plans ont quatre vues : import des documents, dessin, Typst, documents d'export. Les vérifications et les autres onglets ont deux vues : le travail (calcul, dessin, saisie), puis l'affichage tel qu'il apparaîtra dans le rapport, avec les options de la commande et sa copie. Trois améliorations s'y ajoutent : l'enregistrement automatique sans question à chaque changement de contexte ; un volet de gauche des plans qui défile, se replie et dont chaque boîte a sa propre hauteur ; la fin d'un avertissement d'export devenu inutile.

## 2. Source

> **T1** — « Lorsqu'une modification est faite à quelque part, un point blanc apparait (cela est déjà le cas). »
>
> **T2** — « Lorsqu'on chanque de fenêtre, d'onglet, de mode, il doit y avoir un enregistrement automatique sans demander la confirmation »
>
> **T3** — « Il y a une erreur qui apparait régulièrement: export_all: WARNING no load workbook in C:\Users\Quebec\Downloads\TTest -- the export goes on without loads: dead-load, snow-load, wind-load have no case, and show-calc finds none of them, until a file whose name contains 'Belastungsannahmen' and ends in .xlsm or .xlsx is copied into the folder (the live loads of SIA 261 Tabelle 8 need no workbook). »
>
> **T4** — « => cette erreur ne doit plus être affichée. »
>
> **T5** — « Dans le futur, les actions seront directement calculées par woodcore »
>
> **T6** — « Onglets "Plan de positions" et "Plan de protection incendie": le volet de gauche doit pouvoir se scroll vers le haut et vers le bas. »
>
> **T7** — « De plus, le volet doit pouvoir être complètement réduit à l'aide d'une flêche en bas à gauche (similaire que pour le volet entièrement à gauche) »
>
> **T8** — « Les text-box du volet de gauche doivent pouvoir être manuellement élargis ou réduit vers le bas sans modifier la hauteur des autres textesbox »
>
> **T9** — « Je souhaite améliorer l'interface de Woodcore de telle manière à ajouter un slider à gauche du, des boutons des langues. Donc en haut à droite, il y a français, allemand, anglais. À gauche de cela, je souhaite avoir un slider qui permet de changer l'affichage de l'onglet dans lequel on est. »
>
> **T10** — « Par exemple, lorsqu'on est dans le plan de position, Il y a pour l'instant trop d'informations dans les onglets. On se perd un peu, donc il faudra avoir à gauche des langues, un slider qui permet de basculer de l'affichage dessin à l'affichage texte et à l'affichage document. »
>
> **T11** — « Le slider doit avoir quatre positions, la, la position document import, dessin,typst et document export. »
>
> **T12** — « Dans le, le document import, on verra dans le volet de gauche uniquement les documents qui ont été importés, et donc tout le reste, il n'y aura plus. Plan de position, éléments et axes, documents export, commandes typst, tout ça, il n'y aura plus. »
>
> **T13** — « Et dans le volet de droite, uniquement ce qui est aujourd'hui lorsque l'on sélectionne un document. »
>
> **T14** — « Ensuite, lorsque l'on est en dessin, l'on voit dans, l'on verra dans le volet de, de gauche, plan de position, ainsi que éléments et axes, et dans les volets de droite, tout ce qui permet de faire le dessin, comme c'est déjà aujourd'hui le cas. »
>
> **T15** — « Dans le volet typst, dans la vue typst, l'on verra dans le volet de gauche les plans de position que l'on peut sélectionner un à un, au centre, un affichage typst de ce plan, Et à droite, dans le volet de droite, toutes les options qui sont possibles pour les commandes typst avec euh, évidemment eh bien, l'aperçu compilé au centre qui se met à jour. »
>
> **T16** — « Lorsqu'on est dans le, la vision de document export, l'on voit dans le volet de gauche document export. que l'on peut regrouper en, en un seul document, créer en fait un dossier, etc. Et dans le volet de droite, tout ce qui permet de modifier eh bien, ce document-là. »
>
> **T17** — « Ce système de slider qui se retrouve à gauche des boutons pour choisir la langue n'est pas seulement disponible pour les plans, mais également pour, bien, par exemple, les actions de sécurité structurelle. »
>
> **T18** — « Pour l'instant, ce qu'il y a, c'est un volet de gauche avec les différents objets que l'on a créés pour les calculs. Le volet central, les inputs pour le calcul. Et dans le volet de droite, il y a en fait mélangé un aperçu Python, les commandes à copier, les modifications de la commande ainsi qu'un aperçu compilé immédiat. »
>
> **T19** — « Cela doit changer, il doit en haut y avoir un slider qui passe entre calcul et affichage. »
>
> **T20** — « Et lorsque l'on est dans calcul, et bien dans le volet de gauche, on voit les différents objets qui, sont, qui peuvent être sélectionnés, au centre les inputs que l'on peut donner, et à gauche simplement le résultat Python. »
>
> **T21** — « Lorsque l'on passe dans, dans le mode affichage, le volet de gauche ne change pas. Au centre, on a le compilé comme cela apparaîtrait dans le rapport. Et dans le volet de droite, on a les différentes options pour la commande, ainsi qu'on peut copier à la fin la commande. »
>
> **T22** — « Ce système de slider doit fonctionner pour la plupart des onglets. Donc, pour un plan de position, plan de protection incendie, position, journal. Pour les charges, modèle de statique, schéma, moyen d'assemblage, moment polaire, traction, compression, flexion, effort tranchant, torsion, flambage, déversement, déformation, vibration. et variable. »
>
> **T23** — « Et donc pour les variables, il pourrait y avoir plusieurs commandes qu'il doit être possible d'afficher, donc par exemple une commande val, une commande var, une commande ec, Peut-être encore d'autres commandes en fonction de ce qui est pertinent. »
>
> **T24** — « Et on doit pouvoir, dans le mode de, de vue affichage, pouvoir afficher l'une ou l'autre des commandes et ainsi voir les options qui sont disponibles pour l'une ou l'autre de ces commandes. »

### État actuel relevé dans le code (07.10.2026)

- **Point blanc** : `mark_icon` / `dirty_mark` / `update_tab_marks` (`calc/tools/woodcore_gui.py` ~1177, ~3407) sur l'onglet, la navigation et les lignes des listes.
- **Enregistrement** : les deux onglets de plan s'enregistrent déjà seuls en quittant le plan (`DrawingTab.autosave`, v0.114). Si l'enregistrement est refusé (contrôle du domaine, renommage), ils posent encore la question Enregistrer / Ignorer / Annuler ; lors d'un changement d'onglet, le point reste et la ligne d'état dit pourquoi. Les autres éditeurs posent encore la question dans `confirm_leave` : positions, journal, annexes, schéma, moyens d'assemblage, moments polaires, vérifications, Python. Le changement de document (cu/bp/rs, `on_mode_changed`) appelle ces `confirm_leave`.
- **Avertissement** : `calc/registry.py:no_workbook_note`, émis par `calc/export_all.py:143` sur stderr. La fenêtre le montre dans la boîte « export_warnings » (`woodcore_gui.py` ~3851). Le cas voisin, un classeur lu par l'export précédent et disparu depuis, **arrête** l'export (`ValidationError`). Ce n'est pas un avertissement. Le test `tests/test_new_project.py:279` attend le message.
- **Volet de gauche des plans** : un `QSplitter` vertical non repliable de quatre boîtes (Documents, Plans, Éléments et axes, Documents export avec la ligne « Commandes Typst »), dans une `cards.Column` avec `setWidgetResizable(True)`. Le splitter remplit donc la hauteur visible : rien ne défile, et tirer une poignée prend la hauteur de la boîte voisine (T6, T8).
- **Centre et droite des plans** : deux `CurrentStack` qui suivent ce qui est sélectionné à gauche (`KINDS = plan, document, sheet, command`, `DrawingTab.show_kind`). Les quatre vues demandées existent donc déjà comme états. Le sélecteur les rend explicites et filtre le volet de gauche.
- **Vérifications** (`MemberCheckTab`) : la droite mélange résultat Python, appel à copier, options (repliées) et aperçu compilé (replié) (T18).
- **Autres onglets** : modèle de statique, schéma, moyens d'assemblage, moments polaires, charges, journal et variables ne montrent que des **appels à copier**, sans options ni aperçu compilé. Positions n'en montre aucun. Flexion, effort tranchant, torsion, flambage, déversement, déformation et vibration sont des `SoonTab` (pas encore construits).
- **Barre du haut** : nom du projet, méta, *stretch*, puce PDF, `LanguageSwitch` (FR/DE/EN, un contrôle segmenté), Recharger, Import données, Exporter PDF.
- **Commandes des variables** : `val`, `var`, `find`, `show-calc` sont proposées, chacune sur une ligne à copier. `eq` existe dans `lib/formula.typ`, mais aucun constructeur d'appel `call_eq` n'existe.

## 3. Exigences fonctionnelles

### REQ-001 — Enregistrement automatique sans question à chaque changement de contexte
- **Exigence** : Woodcore doit enregistrer sans poser de question ce qu'un éditeur a de non enregistré quand l'ingénieur change d'onglet, de document (cu/bp/rs), de vue (sélecteur, UI-001) ou de fenêtre (perte de focus de la fenêtre principale, D11), et quand il change d'objet dans un onglet. La règle des plans (v0.114) devient celle de tous les éditeurs : `confirm_leave` enregistre d'abord. La question Enregistrer / Ignorer / Annuler ne reste que là où l'enregistrement est refusé.
- **Source** : T2
- **Priorité** : doit
- **Critère d'acceptation** : pour chaque éditeur (positions, journal, annexes, schéma, modèle de statique, moyens d'assemblage, moments polaires, vérifications, plans), un test modifie un champ valide, change d'onglet ou de document, et constate que le fichier est écrit, que le point est éteint et qu'aucune `QMessageBox` n'est apparue.

### REQ-002 — Une donnée refusée n'est jamais écrite en silence
- **Exigence** : si l'enregistrement automatique est refusé (contrôle du domaine, identifiant en double, renommage à confirmer), Woodcore ne doit rien écrire. Le point blanc reste, et la ligne d'état nomme l'objet et la raison. À la fermeture de la fenêtre, la question est posée (sinon la modification serait perdue). Revue A02 : un **renommage** (ID changé d'un objet enregistré) n'est jamais enregistré en silence ; un brouillon neuf n'est enregistré qu'en remplaçant l'objet ou en fermant, et un brouillon neuf jamais touché est jeté sans fichier ; la perte de focus n'enregistre pas un objet dont le champ ID a le focus.
- **Source** : T1, T2 ; règle « validated before anything is written »
- **Priorité** : doit
- **Critère d'acceptation** : un test rend un objet invalide, change d'onglet et constate que le fichier est inchangé, que le point est toujours là et que la ligne d'état donne la raison.

### REQ-003 — L'avertissement « no load workbook » disparaît
- **Exigence** : un export d'un projet qui n'a jamais eu de classeur de charges ne doit plus émettre l'avertissement `no load workbook … goes on without loads …`, ni sur stderr ni dans la boîte « avertissements » de la fenêtre. Il devient une ligne d'information sur stdout (revue A18 : le principe « un manque avertit » est tenu par le rapport, qui dit qu'un domaine de charges est vide). L'arrêt de l'export lorsqu'un classeur lu par l'export précédent a disparu est **conservé** (ce n'est pas l'erreur citée, et c'est une protection des charges du rapport).
- **Source** : T3, T4
- **Priorité** : doit
- **Critère d'acceptation** : `tests/test_new_project.py` exporte un projet sans classeur : l'export réussit et stderr ne contient pas « no load workbook ». Le test du classeur disparu passe toujours.

### REQ-004 — Le volet de gauche des plans défile
- **Exigence** : dans « Plan de positions » et « Plan de protection incendie », le volet de gauche défile vers le haut et vers le bas dès que ses boîtes dépassent la hauteur visible.
- **Source** : T6
- **Priorité** : doit
- **Critère d'acceptation** : un test rend la fenêtre basse, agrandit les boîtes et constate que la barre de défilement verticale du volet a un maximum > 0.

### REQ-005 — Chaque boîte du volet de gauche a sa propre hauteur
- **Exigence** : chaque boîte du volet de gauche (Documents, Plans, Éléments et axes, Documents export) s'agrandit ou se réduit vers le bas par une poignée sur son bord inférieur. Les autres boîtes gardent leur hauteur, et le volet défile (REQ-004). Les hauteurs sont mémorisées avec l'état de la vue (`view_state`), comme le splitter aujourd'hui. Hypothèse retenue : les « text-box » de T8 sont ces boîtes.
- **Source** : T8
- **Priorité** : doit
- **Critère d'acceptation** : un test tire la poignée d'une boîte de +120 px. Sa hauteur augmente de 120 px, celle des autres boîtes ne change pas, et la hauteur est rétablie après rechargement de l'état de la vue.

### REQ-006 — Quatre vues pour les onglets de plan
- **Exigence** : les onglets « Plan de positions » et « Plan de protection incendie » ont quatre vues, dans cet ordre : *Import*, *Dessin*, *Typst*, *Export* (UI-002 à UI-005). Chaque vue ne montre à gauche que ses boîtes. Rien de ce que l'onglet offre aujourd'hui n'est perdu : chaque élément actuel appartient à une vue. Les deux onglets sont un seul moteur (règle 16) : les vues sont construites une fois, dans `DrawingTab`.
- **Source** : T10, T11, T12–T16, T22
- **Priorité** : doit
- **Critère d'acceptation** : un test passe les quatre vues dans chacun des deux onglets et vérifie, pour chacune, les boîtes visibles à gauche et la page visible au centre et à droite.

### REQ-007 — Deux vues pour les vérifications : *Calcul* et *Affichage*
- **Exigence** : les onglets de vérification (Traction, Compression, puis chaque `SoonTab` quand il sera construit) ont deux vues. *Calcul* montre la liste à gauche, les entrées au centre, le résultat Python seul à droite. *Affichage* montre la même liste à gauche (même sélection), au centre l'aperçu compilé tel qu'il apparaîtra dans le rapport, à droite les options de la commande puis la commande à copier. Le volet de droite mélangé d'aujourd'hui disparaît.
- **Source** : T17–T21
- **Priorité** : doit
- **Critère d'acceptation** : un test sur Traction vérifie qu'en *Calcul* ni appel ni aperçu ne sont visibles, qu'en *Affichage* ni entrées ni résultat Python ne le sont, que la sélection de gauche est la même, et que changer une option met à jour l'appel et relance l'aperçu.

### REQ-008 — Deux vues pour les autres onglets de la liste
- **Exigence** : position, journal, charges, modèle de statique, schéma, moyens d'assemblage, moments polaires et variables ont deux vues : la vue de travail d'aujourd'hui (*Saisie*, *Dessin* ou *Calcul* selon l'onglet, UI-001), sans les appels à copier, et *Affichage*. *Affichage* garde la même liste à gauche, montre l'aperçu compilé de la commande choisie au centre, et à droite un choix de la commande (UI-007), **toutes ses options dans un panneau écrit pour elle** (D9), puis la copie. Chaque option d'un panneau est un argument documenté (`///`) de la commande ; un argument non offert l'est pour une raison écrite à côté. Revue B05 : une commande qui n'imprime rien (`journal-entries`, boucles, `var-of`, `value-of`) ou qui lit le document entier (`show-load-summary`, `show-line-load-summary`, une variable **du document**) montre au centre une note écrite à sa place de l'aperçu. Revue B04 : un objet modifié depuis le dernier export est signalé par une bannière avec le bouton Import données, sans export silencieux.
- **Source** : T17, T22
- **Priorité** : doit
- **Critère d'acceptation** : pour chacun de ces onglets, un test passe en *Affichage*, choisit chaque commande proposée et constate que l'appel change et qu'un aperçu est demandé ; un test compare les options de chaque panneau aux arguments du `///` de sa commande (`build_reference`) et nomme tout argument ni offert ni écarté par une raison ; un appel produit avec chaque option changée compile.

### REQ-009 — Plusieurs commandes au choix (onglet Variables en premier)
- **Exigence** : en *Affichage*, quand plusieurs commandes peuvent montrer l'objet choisi, Woodcore propose de choisir celle à afficher. Pour une variable, ce sont `val` et `var` ; pour un domaine de l'export `show-calc`, pour un domaine d'un document `find` (D18 ; `eq` reporté, D15). Les options montrées sont celles de la commande choisie.
- **Source** : T23, T24
- **Priorité** : doit
- **Critère d'acceptation** : dans Variables, en *Affichage*, passer de `val` à `var` change l'appel copiable, l'aperçu et la liste des options.

### REQ-010 — La vue de chaque onglet est mémorisée
- **Exigence** (déduit) : chaque onglet rouvre la vue dans laquelle l'ingénieur l'a laissé, mémorisée dans les réglages de l'utilisateur (`usersettings`), pas dans le projet. La vue par défaut est *Dessin* pour les plans et la vue de travail pour les autres. Le sélecteur est caché sur un onglet sans vues (Structure, Python, RFEM, Annexes, Commandes, DSL).
- **Source** : T9, T22 (« la plupart des onglets »)
- **Priorité** : devrait
- **Critère d'acceptation** : un test choisit *Typst* dans le plan, change d'onglet puis revient : la vue est *Typst*. Sur l'onglet Commandes, le sélecteur est caché.

## 4. Exigences d'interface

### UI-001 — Sélecteur de vue à gauche des langues
- **Exigence** : dans la barre du haut, immédiatement à gauche de FR/DE/EN, un sélecteur de vue montre les vues de l'onglet courant, libellées : plans *Import · Dessin · Typst · Export* ; vérifications, charges, moyens d'assemblage, moments polaires *Calcul · Affichage* ; modèle de statique, schéma *Dessin · Affichage* ; positions, journal *Saisie · Affichage* ; variables *Données · Affichage*. C'est un contrôle segmenté du même dessin que FR/DE/EN (D10).
- **Source** : T9, T11, T19
- **Langues** : fr / de / en — libellés et infobulle dans `woodcore_gui.STRINGS`, clés `view_*` (revue A13 : `calc/i18n/strings.json` est le glossaire du rapport) (de : *Import · Zeichnung · Typst · Export*, *Berechnung · Darstellung*, *Erfassung*, *Daten* ; en : *Import · Drawing · Typst · Export*, *Calculation · Display*, *Entry*, *Data*)
- **Critère d'acceptation** : le sélecteur est le widget juste avant `LanguageSwitch` dans la barre du haut. Il change de positions en changeant d'onglet, et ses libellés suivent la langue.

### UI-002 — Plan, vue *Import*
- **Exigence** : à gauche, seulement la boîte *Documents* (liste, Importer, Supprimer). Au centre, la page du document choisi (`doc_view`, comme aujourd'hui). À droite, seulement ce qui s'y montre aujourd'hui pour un document (nom, fichier, pages, rotation, calques, cadre). Plans, éléments et axes, documents export et commandes Typst ne sont pas montrés.
- **Source** : T12, T13
- **Critère d'acceptation** : couvert par le test de REQ-006.

### UI-003 — Plan, vue *Dessin*
- **Exigence** : à gauche, *Plans de position* (ou *Plans de protection incendie*) et *Éléments et axes*. Au centre, le canevas et ses outils. À droite, les cartes de dessin d'aujourd'hui, qui suivent la sélection (aucun outil retiré).
- **Source** : T14
- **Critère d'acceptation** : couvert par le test de REQ-006. Les tests existants des plans passent sans changement de comportement du dessin.

### UI-004 — Plan, vue *Typst*
- **Exigence** : à gauche, la liste des plans, un plan choisi à la fois. Au centre, l'aperçu compilé du `#show-plan` (ou `#show-fire-plan`) de ce plan et la commande à copier. À droite, toutes les options de la commande (`CommandOptions`), et l'aperçu se recompile quand une option change. La ligne « Commandes Typst » de la boîte *Documents export* disparaît : elle est remplacée par cette vue.
- **Source** : T15
- **Critère d'acceptation** : choisir un autre plan à gauche change l'appel (`plan:`) et relance l'aperçu. Changer une option à droite relance l'aperçu.

### UI-005 — Plan, vue *Export*
- **Exigence** : à gauche, seulement *Documents export* : les feuilles et leurs dossiers (les « bundles » PDF qui existent déjà : créer, renommer, supprimer un dossier, y déplacer une feuille). Au centre, la feuille. À droite, ses options (`SheetOptions`).
- **Source** : T16
- **Critère d'acceptation** : couvert par le test de REQ-006. Les tests existants des feuilles et des dossiers passent.

### UI-006 — Repli complet du volet de gauche des plans
- **Exigence** : une flèche en bas à gauche du volet de gauche des plans le replie entièrement, puis le rouvre. Elle a la même icône (`nav_collapse` / `nav_expand`), le même style (`QToolButton#fold`) et une infobulle propre au volet (`pane_collapse`/`pane_expand` : celle de la navigation parle du menu, revue A12). Une fois replié, il ne reste que la flèche. L'état est mémorisé avec la vue.
- **Source** : T7
- **Langues** : infobulle fr / de / en
- **Critère d'acceptation** : un test clique la flèche : la largeur du volet tombe à celle de la flèche. Un second clic rétablit la largeur précédente.

### UI-007 — Choix de la commande en *Affichage*
- **Exigence** : en haut du volet de droite en *Affichage*, quand l'objet a plusieurs commandes, une liste déroulante les nomme (`val`, `var`, `eq` ; `show-static-model` et ses variantes ; `show-journal`, `journal-entries`…). Puis viennent les options de la commande choisie, puis l'appel et le bouton Copier.
- **Source** : T21, T23, T24
- **Langues** : fr / de / en (le nom de la commande reste tel quel)
- **Critère d'acceptation** : couvert par REQ-008 et REQ-009.

## 5. Exigences d'architecture

### ARCH-001 — Un seul mécanisme de vues
- **Exigence** : un onglet déclare ses vues (clé, libellé, ce que chaque volet montre) et réagit à `set_view(key)`. La fenêtre possède un seul sélecteur et le relie à l'onglet courant. Aucun onglet ne construit son propre sélecteur.
- **Source** : T22 ; règles 1 et 16
- **Critère d'acceptation** : un test parcourt `TABS` et vérifie que chaque onglet de la liste de T22 qui existe déclare des vues, et que le sélecteur de la barre reflète la déclaration de l'onglet courant.

### ARCH-002 — Un seul volet *Affichage* partagé
- **Exigence** : le trio choix de commande + options + appel à copier, avec l'aperçu `PdfPane.request_snippet` au centre, est un widget partagé. Il est construit une fois à partir de `plan_command_builder.CommandBuilder` et de `Collapsible`, généralisés. Chaque onglet ne fournit que ses commandes et leurs options.
- **Source** : règle 16 (« built once and asked for by hook »)
- **Critère d'acceptation** : le volet *Affichage* des vérifications, du modèle de statique et des variables est la même classe, et aucun onglet ne crée de `PdfPane` pour sa vue *Affichage*.

### ARCH-003 — Les vues ne calculent rien
- **Exigence** : changer de vue ne fait que montrer ou cacher. Les résultats Python viennent des mêmes fonctions de `calc/domains/`, et l'appel vient des mêmes constructeurs (`build_reference.call_*`).
- **Source** : principe « domain logic independent of the UI »
- **Critère d'acceptation** : aucune formule n'est ajoutée dans `calc/tools/`. La revue le vérifie.

### ARCH-004 — Un seul module d'enregistrement automatique (revue A01, A03-A07)
- **Exigence** : `calc/tools/autosave.py` porte les trois contextes (a) l'onglet ou la vue change ou la fenêtre perd le focus — silencieux, le point reste et la ligne d'état dit pourquoi ; (b) l'objet est remplacé — silencieux, question seulement si refusé ; (c) fermeture — question si refusé ; la lecture seule d'abord, la garde de réentrance, aucune action sous une boîte modale ou pendant `busy`, le report pendant `app.process`. Chaque éditeur ne fournit que `save(quiet)` et son `discard`.
- **Source** : revue
- **Critère d'acceptation** : `tests/test_autosave.py` ; aucun `confirm_leave` d'onglet ne construit plus sa propre `QMessageBox`.

### ARCH-005 — Un seul constructeur d'appels, défauts lus dans la signature (revue B01, B02)
- **Exigence** : `build_reference.call_command` écrit un appel en n'y mettant que ce qui diffère du défaut de la signature Typst ; les `call_*` en sont des enveloppes à sortie inchangée.
- **Source** : revue ; règle 1
- **Critère d'acceptation** : un test de sortie identique pour chaque `call_*` ; `aids: false` et un `caption` libre compilent.

### ARCH-006 — Panneaux tenus contre la signature (revue B03)
- **Exigence** : la spécification d'un panneau ne porte aucun défaut ; tout argument nommé d'une commande est offert ou écarté avec une raison (`DISMISSED`).
- **Source** : revue ; règles 1 et 14
- **Critère d'acceptation** : `tests/test_display_view.py` nomme tout argument ni offert ni écarté, et tout défaut initial différent de la signature.

### ARCH-007 — Un aperçu par onglet, construit à la demande (revue B08, A10)
- **Exigence** : un `PdfPane` par onglet, construit à la première entrée en *Affichage*, cache propre, rien compilé hors de la vue ni à la restauration.
- **Source** : revue
- **Critère d'acceptation** : un test démarre la fenêtre avec des vues *Affichage*/*Typst* mémorisées : aucune compilation avant affichage ; les dossiers de cache diffèrent.

## 6. Contraintes

- **CON-001** — Toute chaîne nouvelle existe en de, fr et en (`calc/i18n/strings.json` ou les tables de mots des onglets). Source : déduit (CLAUDE.md).
- **CON-002** — Les couleurs du sélecteur viennent de `calc/tools/theme.json` / `theme.py`. Source : déduit.
- **CON-003** — Aucune fonction actuelle ne disparaît : chaque élément d'un volet d'aujourd'hui appartient à une vue. Les appels offerts aujourd'hui hors de la liste D9 (`show-input`, `value-of`, `show-check`, `var-of`, les boucles `*-loop`, `show-extract`) restent dans le choix de commande, avec un panneau réduit à leurs arguments positionnels et la raison écrite (revue B07). Source : déduit de T12–T21.
- **CON-004** — Règle 15 : aucun code Typst d'un document n'est montré. Les vues *Typst* et *Affichage* montrent un **appel** de commande et son rendu, comme aujourd'hui, jamais le `.typ` d'un document. Source : déduit (principles.md).
- **CON-005** — Les fichiers de projet et leurs schémas ne changent pas : les vues, les hauteurs et le repli sont des réglages de l'utilisateur. Source : déduit.
- **CON-006** — Plusieurs sessions travaillent sur le dépôt : `drawing_tab.py`, `member_check_tab.py` et `woodcore_gui.py` sont touchés par des modifications ciblées, après coordination si un pair y travaille. Source : CLAUDE.md.

## 7. Décisions prises

- **D1** — Plans : quatre vues, *Import · Dessin · Typst · Export* (T11). La formulation « dessin / texte / document » de T10 est remplacée par T11, qui la précise.
- **D2** — Vérifications : deux vues, *Calcul · Affichage* (T19).
- **D3** — Le point blanc reste tel qu'il est (T1).
- **D4** — Enregistrer sans question (T2). La question ne reste que pour une donnée refusée à la fermeture (REQ-002).
- **D5** — L'avertissement « no load workbook » ne s'affiche plus (T4). Seul ce message disparaît : l'arrêt pour un classeur disparu reste (REQ-003).
- **D6** — T20 « et à gauche simplement le résultat Python » est lu « à droite » : la gauche porte déjà les objets dans la même phrase, et la droite portait le résultat Python en T18.
- **D7** — Les « text-box » de T8 sont les quatre boîtes du volet de gauche (REQ-005).
- **D8** — « ec » (T23) est la commande `eq` de `lib/formula.typ` : aucune commande `ec` n'existe.
- **D9** — (Q-001, réponse C) En *Affichage*, chaque commande de chaque onglet de la liste a son panneau d'options **écrit à la main** dans cette version : `show-static-model`, `show-schema`, `show-connector`, `show-connector-resistance`, `show-polar-moment`, `show-calc` (et `show-load-summary`, `show-line-load-summary`, `show-live-load` pour les charges), `show-journal`, `journal-entries`, `show-position-list`, `val`, `var`, `eq`, `find`, en plus de `show-plan`, `show-fire-plan` et `show-check-member` qui en ont déjà. Le prix accepté : le travail le plus long des trois options.
- **D10** — (Q-002) Le sélecteur est un contrôle segmenté du même dessin que FR/DE/EN.
- **D11** — (Q-003) L'enregistrement automatique a lieu aussi quand la fenêtre principale perd le focus.
- **D12** — (Q-004) `eq` n'est proposé que pour une variable de l'export dont Python connaît la formule.
- **D13** — (revue B11) La décision du 07.10.2026 « Résultats → Commande → Options repliées → Aperçu replié » est remplacée par les vues *Calcul · Affichage* ; prix : le résultat Python n'est plus à côté de l'appel.
- **D14** — (revue A05, A11, A16 ; défauts recommandés, pris sans question) L'export (PDF, Import données) enregistre d'abord tous les brouillons ; hauteurs des boîtes et repli du volet restent en mémoire de session comme les splitters aujourd'hui, la vue choisie seule va dans `usersettings` ; l'onglet Python ne s'enregistre pas à la seule perte de focus.
- **D15** — (Q-005, réponse B) `eq` est reporté : la formule de l'export est par étape et en notation mathématique, la convertir en clés du registre est un travail à part. D12 ne s'applique pas dans cette version ; Variables propose `val`, `var`, `find` et `show-calc`.
- **D16** — (vérification, ARCH-005) La sortie des `call_*` est inchangée, à une exception près : **toute** option égale à son défaut n'est plus écrite. Exemples : `form: "table"`, `zoom: 1`, `member-level: 1`, `aids: true`. L'appel imprime la même chose (ronde 2).
- **D17** — (vérification, ARCH-002) Les plans gardent leur panneau propre (`plan_command_builder.CommandOptions`, `FireCommandOptions`) au lieu d'une déclaration. Ce panneau dépend de l'enregistrement d'export du plan (positions offertes, barre d'échelle sans échelle), ce qu'une déclaration ne peut pas dire. La raison est écrite dans `display_options.OWN_PANELS`, comme l'exige la règle 16. Ce qu'ARCH-007 demandait est fait : un volet construit à la demande et un dossier par onglet.
- **D18** — (vérification, REQ-009) Pour un domaine de l'export, seul `show-calc` est offert : `find` sur une paire est l'affaire de `call_find_source`, pas de l'onglet. **Confirmé par l'ingénieur le 08.10.2026** : « oui, seul show-calc me convient ».
- **D19** — (l'ingénieur, 08.10.2026) La vue « Typst » des plans s'appelle **« Affichage »**, comme la vue d'affichage de tous les onglets. La clé interne reste `typst`, mémorisée dans les réglages. Le renommage a été fait par la session « performance et gestion des erreurs » (`views.py`). Il remplace le libellé « Typst » d'UI-001 et d'UI-004.
- À reporter dans `docs/decisions.md` à la fin : D1, D2 (une vue par tâche), D4–D5, D9, D11, D13, D14, D15.

## 8. Hors périmètre

- Le calcul des actions par Woodcore lui-même (T5) : annoncé pour le futur, il justifie D5.
- La construction des onglets Flexion, Effort tranchant, Torsion, Flambage, Déversement, Déformation et Vibration : ils recevront les vues *Calcul · Affichage* en étant construits sur `MemberCheckTab`.
- Toute nouvelle fonction de dessin ou de calcul.
- Tout changement des commandes Typst elles-mêmes (`lib/`) : l'*Affichage* montre les commandes et les options qui existent.
- `eq` dans l'onglet Variables (D15) : demande un convertisseur de la formule d'étape en clés du registre, à spécifier à part (`docs/open-questions.md`).

## 9. Idées non retenues comme exigences

- **I1** — « Peut-être encore d'autres commandes en fonction de ce qui est pertinent » (T23) : la liste suit ce que `build_reference` sait appeler pour l'objet. `find` et `show-calc` y sont déjà.
- **I2** — T10 « dessin / texte / document » : première formulation, remplacée par T11 (D1).

## 10. Questions

### Q-001 — Jusqu'où vont les options en *Affichage* pour les onglets qui n'en ont pas aujourd'hui ?
- **Pourquoi elle compte** : seuls les plans et les vérifications ont aujourd'hui des options de commande et un aperçu. Modèle de statique, schéma, moyens d'assemblage, moments polaires, charges, journal, variables et positions n'ont que des appels à copier. Écrire à la main un panneau d'options par commande (environ 12 commandes) triple la taille du travail.
- **Options** : A (recommandée) — cette version construit le mécanisme, les vues des plans et des vérifications (complètes), et pour les autres onglets l'*Affichage* avec le choix de commande, l'aperçu compilé et la copie. Les options sont générées à partir du `///` de chaque commande (booléen → case, chaînes énumérées → liste, nombre → champ), une seule fois et pour toutes. B — mêmes vues, mais des panneaux d'options écrits à la main, onglet par onglet, dans des versions suivantes (cette version : choix + aperçu + copie seulement). C — tout, avec des panneaux écrits à la main, maintenant.
- **Réponse** : **C**, l'ingénieur, 07.10.2026 : « Tout à la main, maintenant ». Un panneau d'options écrit à la main par commande, dans cette version (D9).

### Q-002 — Forme du sélecteur
- **Pourquoi elle compte** : un « slider » à crans glissant prend de la place et se lit mal avec quatre libellés en trois langues. Le contrôle segmenté FR/DE/EN existe déjà juste à côté.
- **Options** : A (recommandée) — un contrôle segmenté du même dessin que FR/DE/EN (un bouton par vue, la vue active remplie). B — un vrai curseur à crans, les libellés dessous.
- **Réponse** : **A**, l'ingénieur, 07.10.2026 (D10).

### Q-003 — « Changer de fenêtre » : faut-il aussi enregistrer quand Woodcore perd le focus (passage à VS Code, à Excel) ?
- **Pourquoi elle compte** : enregistrer à la perte de focus écrit les fichiers avant que l'ingénieur les ouvre ailleurs (VS Code lit les `.typ`, l'export lit les JSON), mais écrit aussi un objet à moitié saisi qui serait valide.
- **Options** : A (recommandée) — oui : onglet, document, vue, objet, **et** perte de focus de la fenêtre principale. B — non : seulement les changements internes à Woodcore.
- **Réponse** : **A**, l'ingénieur, 07.10.2026 (D11).

### Q-004 — `eq` dans les commandes d'une variable
- **Pourquoi elle compte** : `eq` calcule une **nouvelle** variable à partir d'une formule sur les clés du registre. Il ne montre pas une variable existante. Le proposer pour une variable demande de générer une formule (par ex. `#eq("X_d", `X`)`), ce qui n'a de sens que pour certaines.
- **Options** : A (recommandée) — `val` et `var` (avec `find` et `show-calc` pour un domaine), et `eq` seulement pour une variable de l'export dont Python connaît la formule. B — `eq` toujours proposé, avec la variable comme seul terme de la formule. C — pas de `eq` dans cette version.
- **Réponse** : **A**, l'ingénieur, 07.10.2026 (D12).

### Q-005 — `eq` : la formule de l'export est par étape, en notation mathématique (revue B06)
- **Pourquoi elle compte** : l'export ne porte pas de formule par variable mais par étape de calcul (`steps[].formula`), écrite avec son membre gauche et en symboles (`q_(k,11) = max(mu_11, 0.8) dot C_e dot C_T dot s_k`, parfois une contrainte `>=`) ; 6 étapes sur 22 dans l'exemple (neige, vent ; aucune pour le poids propre). `eq` veut le membre droit en clés du registre : il faut un convertisseur (retirer le membre gauche, remplacer chaque symbole par sa clé, déclarer chaque opérande par `#var`, refuser ce qu'on ne sait pas convertir).
- **Options** : A (recommandée) — le convertisseur, fonction pure sans Qt dans `calc/`, testé en compilant chaque étape de l'exemple ; `eq` n'apparaît que quand la conversion réussit et compile (donc jamais pour le poids propre). B — `eq` reporté à une version suivante.
- **Réponse** : **B**, l'ingénieur, 07.10.2026 : « Reporter eq ». D12 est remplacé par D15.

## 11. Critères d'acceptation

- [ ] REQ-001 — tout éditeur s'enregistre sans question au changement d'onglet, de document, de vue, d'objet et à la perte de focus.
- [ ] REQ-002 — une donnée refusée n'est pas écrite ; le point et la raison restent.
- [ ] REQ-003 — plus de « no load workbook » ; l'arrêt pour classeur disparu reste.
- [ ] REQ-004 — le volet de gauche des plans défile.
- [ ] REQ-005 — chaque boîte a sa hauteur, mémorisée.
- [ ] REQ-006 — quatre vues des plans, dans les deux onglets.
- [ ] REQ-007 — *Calcul · Affichage* des vérifications.
- [ ] REQ-008 — deux vues des autres onglets de la liste, chaque commande avec son panneau d'options écrit à la main.
- [ ] REQ-009 — choix de la commande ; Variables : `val`, `var`, `find`, `show-calc` (`eq` reporté, D15).
- [ ] REQ-010 — vue mémorisée par onglet ; sélecteur caché sans vues.
- [ ] UI-001 — sélecteur à gauche de FR/DE/EN, libellés en trois langues.
- [ ] UI-002 à UI-005 — contenu de chaque vue des plans.
- [ ] UI-006 — flèche de repli du volet de gauche des plans.
- [ ] UI-007 — liste des commandes en tête de l'*Affichage*.
- [ ] ARCH-001 — vues déclarées, un seul sélecteur.
- [ ] ARCH-002 — un seul volet *Affichage* partagé.
- [ ] ARCH-003 — aucune formule dans `calc/tools/`.
- [ ] ARCH-004 — un seul module d'enregistrement, trois contextes.
- [ ] ARCH-005 — `call_command`, défauts de la signature, sorties inchangées.
- [ ] ARCH-006 — panneaux tenus contre la signature.
- [ ] ARCH-007 — aperçu par onglet, à la demande.
- [ ] Documentation : `docs/ui/window.md` (barre du haut, onglets de plan, vérifications, chaque onglet touché), `docs/decisions.md`, `CHANGELOG.md`, page « Nouveautés » fr/de/en.
- [ ] Tests : nouveaux tests des vues, de l'enregistrement automatique et du volet de gauche ; `tests/test_new_project.py` adapté ; suite complète verte.

## 12. Traçabilité

| Source | Élément | Statut |
|---|---|---|
| T1 | REQ-002, D3 | capturé |
| T2 | REQ-001, REQ-002, D4, D11 | capturé (Q-003 → A) |
| T3 | REQ-003 | capturé (contexte) |
| T4 | REQ-003, D5 | capturé |
| T5 | §8 | hors périmètre (futur) |
| T6 | REQ-004 | capturé |
| T7 | UI-006 | capturé |
| T8 | REQ-005, D7 | capturé |
| T9 | UI-001, REQ-010, D10 | capturé (Q-002 → A) |
| T10 | D1, I2 | remplacé par T11 |
| T11 | REQ-006, UI-001, D1 | capturé |
| T12 | UI-002 | capturé |
| T13 | UI-002 | capturé |
| T14 | UI-003 | capturé |
| T15 | UI-004 | capturé |
| T16 | UI-005 | capturé (dossiers existants) |
| T17 | REQ-007, REQ-008, ARCH-001 | capturé |
| T18 | REQ-007 (état actuel) | contexte |
| T19 | REQ-007, UI-001, D2 | capturé |
| T20 | REQ-007, D6 | capturé (lapsus lu « à droite ») |
| T21 | REQ-007, UI-007 | capturé |
| T22 | REQ-008, REQ-010, ARCH-001, §8, D9 | capturé (Q-001 → C) |
| T23 | REQ-009, D8, D15, I1, §8 | capturé ; `eq` reporté (Q-005 → B) |
| T24 | REQ-009, UI-007 | capturé |

### Points de la source non résolus

Aucun : les quatre questions ont reçu leur réponse le 07.10.2026.

## 13. Revue d'architecture

Deux revues en parallèle (`architecture-reviewer`, 07.10.2026), faites sur le code. **Zone A** : sélecteur, vues des plans, volet de gauche, enregistrement automatique, REQ-003. **Zone B** : vue *Affichage* et panneaux d'options. Verdict des deux : **APPROUVER AVEC RÉSERVES**. Chaque réserve est reprise dans le plan (§14) ou dans une exigence (ARCH-004 à ARCH-009).

### Modules concernés

- **Fenêtre** : `calc/tools/woodcore_gui.py`. Barre du haut ~3095-3135 (`LanguageSwitch` 3126), `build`/`rebuild` (3098, 3344, `view_state` porté dans `self.views`), `currentChanged` (3197-3201), `on_mode_changed` (3032, `MODE_BOUND` 2851), `closeEvent` (3977), `WRITERS`/`refused_when_read_only` (2874-2899), `reexport`/`engine_consent` (3792, 3705), `STRINGS` (fr/de/en, parité contrôlée à l'import), `LoadsTab` (1234), `PolarTab` (1708).
- **Cadre** : `calc/tools/chrome.py`. `LanguageSwitch` (103), flèche `SideNav.fold` (281-285, 418-419) ; style dans `theme.py` (`[segment=…]` 320, `QToolButton#fold` 334).
- **Plans** : `drawing_tab.py`. `KINDS` (52), `LEFT_STRETCH` (57), `build_list`/`left_splitter` (492-567), `command_list` (538), `show_kind` (740), `leave_plan` (774), `hideEvent` (834), `finish_layer_export` (1379), `autosave`/`confirm_leave` (1814-1841), `view_state`/`restore` (1895, 1913). Aussi `plan_tab.py`, `fire_tab.py`, `plan_command_builder.py` (`CommandOptions` 192 avec son propre choix de plan, `CommandField` 455, `CommandBuilder` 464, `snippet_source` 184), `sheet_list.py`.
- **Éditeurs** : un `confirm_leave` par onglet, chacun avec sa question. `positions_tab` (824/923), `journal_tab` (587/656), `annex_tab` (1149/1305, le renommage déplace le PDF source), `schema_tab` (1939/1990), `statics_tab` (2378/2433), `connectors_tab` (2038/2000), `member_check_tab` (1392/1355), `PolarTab` (2624/2710), `python_tab` (623/525). `structure_tab` (1990) ne fait que `host.flush()`.
- **Appels** : `calc/tools/build_reference.py`, seul constructeur d'appels (`call_*` 343-633, `parse_doc_block` 266, `split_params` 808, `lib_records` 261, `load_*` 636-720). `structure_preview.header` donne l'en-tête correct d'un snippet. `pdf_pane.PdfPane.request_snippet` (443) attend 250 ms, et la dernière demande gagne.
- **REQ-003** : `calc/registry.py:36` (`no_workbook_note`) et `calc/export_all.py:22,143` ; `tests/test_new_project.py:265-279`.

### Existant réutilisé

- `DrawingTab.autosave` et `save(quiet=True)` des plans et de Python : ils servent de modèle à l'enregistrement de tous les éditeurs.
- `LanguageSwitch` devient un cas de `chrome.SegmentedSwitch`. `SideNav.fold` devient `chrome.FoldButton`.
- `cards.Column` reste le conteneur qui défile. La seule pièce nouvelle est la poignée de hauteur d'une boîte.
- `remember_mode` (fusion d'un dict dans `usersettings`) sert de modèle pour mémoriser les vues.
- Les quatre vues d'un plan sont les quatre états de `KINDS`/`show_kind`, déjà présents.
- `CommandBuilder`, `Collapsible` et `CommandField` sont généralisés en un seul widget *Affichage*.
- `build_reference.call_*` reste le seul constructeur d'appels.
- `commands.json` fournit les infobulles des options.
- `split_params` donne les valeurs par défaut des arguments.
- `tests/test_commands.py:352` sert de modèle pour vérifier que les appels compilent.

### Risques

| Risque | Gravité | Ce qui est fait (§14) |
|---|---|---|
| **A01** — les huit `save()` n'ont pas de mode silencieux : ils ouvrent des boîtes modales (échec, renommage, export refusé) | bloquant | `quiet` ajouté aux huit `save()`. Trois contextes : (a) changement d'onglet, de vue, perte de focus : silencieux, le point reste et la ligne d'état dit pourquoi ; (b) objet remplacé (autre objet, Nouveau, Dupliquer, changement de document) : silencieux, question seulement si l'enregistrement est refusé ; (c) fermeture : question si refusé. → ARCH-004 |
| **A02** — un ID à moitié tapé, un brouillon neuf ou un renommage enregistrés en silence (une annexe renommerait son PDF) | bloquant | Un renommage n'est jamais enregistré en silence. Un brouillon neuf n'est enregistré qu'en (b) ou (c), et un brouillon jamais touché est jeté (`touched`). La perte de focus ne touche pas un objet dont le champ ID a le focus. → REQ-002 complété |
| **A03** — la perte de focus se déclenche aussi sous une boîte modale de Woodcore | important | Le signal utilisé est `QGuiApplication.applicationStateChanged` (Inactive). Garde contre la réentrance, et rien ne se fait sous `activeModalWidget()` ni pendant `busy`. `MainWindow.autosave_all(reason)` est testable directement. |
| **A04** — lecture seule : `save()` ouvrirait la boîte `read_only_refused` | important | Lecture seule testée avant tout `save`. `WRITERS` n'est pas modifié. Les vues dans `usersettings` restent permises en lecture seule. |
| **A05** — un enregistrement lance `reexport`, qui peut poser la question du moteur | important | `reexport(quiet=True)` : si le moteur demande une décision, pas d'export, et la ligne d'état le dit. L'export (PDF, Import données) enregistre d'abord tous les brouillons (`autosave_all`). |
| **A06** — un enregistrement pendant un export, une compilation ou un export de calque | important | Si `app.process` tourne, l'enregistrement est différé puis rejoué. `set_view` termine l'export de calque en quittant *Import*. Les écritures de `data/` sont vérifiées atomiques. |
| **A07** — ordre des signaux au changement d'onglet | important | Un seul slot `on_tab_changed` : il enregistre l'onglet quitté, puis applique la vue, puis `on_shown`. `on_mode_changed` lance `autosave_all` avant de changer de document. |
| **A08/A09** — deux sources pour la vue (`view_kind` et le sélecteur) et deux choix de plan en *Typst* | important | Une seule table `VIEW_KIND`, dérivée de `KINDS`. Tout `show_kind` interne prévient la fenêtre (`view_changed`). La liste des plans de gauche est le seul choix : celui de `CommandOptions` est retiré. Les cas vides sont dits (aucun document, feuille ou plan). |
| **A10** — restaurer une vue *Typst* au démarrage compilerait dans tous les onglets | important | Restaurer une vue ne fait que poser l'état. La compilation part au `showEvent`. Un test le vérifie. |
| **A11** — la persistance | important | La vue choisie va dans `usersettings`, par onglet. Les hauteurs des boîtes et le repli restent en mémoire de session (`view_state`), comme les splitters aujourd'hui. Rien n'entre dans le projet. |
| **A12** — le `QSplitter` est la cause de T6/T8 | mineur | Il est remplacé par des boîtes à poignée propre dans la `cards.Column`. Pied du volet hors de la zone qui défile, avec `FoldButton`. Infobulles propres `pane_collapse`/`pane_expand` (et non celles de la navigation). |
| **A13** — les mots de la fenêtre ne vont pas dans `calc/i18n/strings.json` (lu par Typst) | mineur | Clés `view_*` et `pane_*` dans `woodcore_gui.STRINGS`. UI-001 est corrigé. |
| **A15** — onglet Structure (VS Code) | — | Aucun risque d'écrasement : il écrit au fil de l'eau. La perte de focus appelle `host.flush()`. Un test vérifie que rien n'est écrasé après une modification externe. |
| **A16** — onglet Python | important | Il est enregistré en (b) et (c), pas sur une simple perte de focus : un script à moitié tapé s'exécuterait à l'export. |
| **A17** — tests qui casseront | important | `left_splitter`, `command_list`, les bouchons `QMessageBox.question → Discard` (un brouillon serait désormais écrit), et `test_new_project.py:279`. Ils sont adaptés, chaque test nommé dans son lot. |
| **A18** — REQ-003 contredit « un manque avertit » | important | L'avertissement devient une ligne d'information sur stdout, qui ne va donc pas dans la boîte d'avertissements. `no_workbook_note` est retiré. La décision est écrite dans `decisions.md`. Le rapport garde la raison (`show-calc` d'un domaine vide). |
| **B01** — `build_reference` ne sait pas écrire tous les appels de D9 | important | `call_*` manquants : `show-load-summary`, `show-line-load-summary`, `show-position-list`, `eq`. Arguments manquants : `show-static-model` `dimensions`/`diagram`, `show-connector` `level`, `title`/`width`, `val`/`var` complets, `find` `object`, `journal-entries` `document` (faux aujourd'hui en cu/bp). |
| **B02** — défauts qui dérivent déjà, citation incohérente | important | `aids: false` est impossible à écrire aujourd'hui, et `caption`/`title` sont écrits sans citation. Un seul `call_command(name, …)` n'écrit que ce qui diffère du défaut **lu dans la signature** Typst. Les `call_*` deviennent des enveloppes, avec une sortie identique octet pour octet. → ARCH-005 |
| **B03** — les défauts des panneaux | important | La spécification d'un panneau ne porte aucune valeur par défaut : l'état initial est lu dans la signature. Un test compare chaque panneau à la signature, avec `DISMISSED[commande][argument] = raison`. → ARCH-006 |
| **B04** — l'aperçu lit l'export et peut montrer une ancienne version | important | Bannière « modifié depuis le dernier export » avec le bouton Import données. Aucun export silencieux. → ARCH-007 |
| **B05** — certaines commandes n'ont pas d'aperçu possible dans un snippet | important | `show-load-summary` et `show-line-load-summary` (elles lisent le document), `journal-entries`, les boucles, `var-of`/`value-of` (n'impriment rien), et les variables **du document**. Une note écrite par commande remplace l'aperçu. → REQ-008 précisé |
| **B06** — D12 : l'export ne porte pas de formule par variable mais par étape | important | La formule est en notation mathématique avec membre gauche (parfois `>=`). Seules 6 étapes sur 22 de l'exemple en ont une (neige, vent ; aucune pour le poids propre). → **Q-005** |
| **B07** — CON-003 contre D9 : des appels offerts aujourd'hui ne sont pas dans la liste D9 | important | `show-input`, `value-of`, `show-check`, `var-of`, les boucles, `show-extract` restent dans le choix de commande, avec un panneau réduit à leurs arguments positionnels et une raison écrite. Rien ne disparaît (CON-003). La ligne d'import se décide une fois, dans le widget. |
| **B08** — coût de compilation avec environ 15 onglets | important | Un `PdfPane` par onglet, construit à la première entrée en *Affichage*, avec un dossier de cache propre à chaque onglet (aujourd'hui partagé et en collision). Un seul délai d'attente : celui du pane. En quittant la vue, la demande est annulée sans `stop()`, qui bloquerait jusqu'à 15 s. |
| **B09** — mots écrits deux fois | important | Lexique partagé `dv_opt_*` (niveau, titre, largeur, légende…) dans `STRINGS`. Les mots propres à une commande restent dans son lexique. Le module reçoit `t`. |
| **B10** — widgets partagés mal rangés | mineur | `Collapsible` va dans `cards.py`. `CommandField` et le widget vont dans `display_view.py`. `layout.md` est mis à jour. |
| **B11** — décision du 07.10.2026 (« Résultats → Commande → Options repliées → Aperçu replié ») renversée | mineur | Le renversement est écrit dans `decisions.md`, avec son prix : le résultat Python n'est plus à côté de l'appel. → D13 |
| **B12** — `eq` mal documenté dans `api-conventions.md` | mineur | Tableau corrigé en passant. |

### Approche retenue

- **Une spécification déclarative par commande**, écrite à la main (D9), dans un module sans Qt `calc/tools/display_options.py`. Chaque entrée est `Option(name, kind, choices, label_key, enabled_when, disabled_tip_key)`, sans défaut. S'y ajoute `DISMISSED`.
- **Un seul widget `DisplayView`** (`calc/tools/display_view.py`), qui généralise `CommandBuilder` : choix de la commande, cartes d'options, appel, copie et `PdfPane` du centre. Il reçoit de l'onglet des hooks : `target`, `commands()`, `call_fn`, `snippet_fn` (le brouillon pour les vérifications), `exported(id)`, `stale(id)`.
- `CommandOptions`, `FireCommandOptions` et les options de `MemberCheckTab` y sont **migrés**, puis supprimés. Une classe par commande est écartée : quinze copies, contraires à la règle 16.

### Verdict

**APPROUVER AVEC RÉSERVES** (A et B). Les réserves bloquantes A01 et A02 sont levées par ARCH-004 et REQ-002. B06 attend la réponse de l'ingénieur (Q-005). B05 et B07 sont écrits dans REQ-008 et CON-003.

## 14. Plan d'implémentation

Les lots sont faits dans l'ordre. WP7 à WP11 sont indépendants entre eux une fois WP5 et WP6 faits. Chaque lot se termine par ses tests verts, puis par une ligne au §16.

1. **WP1 — REQ-003.**
   - Ce que fait le lot : `export_all.py` écrit sur stdout une ligne d'information (`export_all: no load workbook in … -- loads: none`) à la place de `_warn`. `no_workbook_note` et son import sont retirés. Les docstrings de `registry.py` sont corrigées.
   - Exigences : REQ-003, A18.
   - Tests : `tests/test_new_project.py:265-279` est inversé (rien sur stderr, l'arrêt du classeur disparu passe toujours) ; `test_registry`, `test_positions_store`.
2. **WP2 — Cadre des vues.**
   - Ce que fait le lot :
     - `chrome.SegmentedSwitch`, avec `LanguageSwitch` construit dessus et une API inchangée ;
     - `chrome.FoldButton`, extrait de `SideNav` ;
     - dans `woodcore_gui.py`, le sélecteur juste avant `self.language`, caché pour un onglet sans `VIEWS` ;
     - un slot unique `on_tab_changed` : il enregistre l'onglet quitté, puis applique la vue, puis `on_shown` ;
     - `set_view`, `view_changed(tab)`, la vue mémorisée dans `usersettings` par fusion, et `view_state()["view"]` à travers `rebuild` ;
     - les clés `view_*` dans `STRINGS`.
   - Exigences : UI-001, REQ-010, ARCH-001, A07, A13, A14.
   - Tests : nouveau `tests/test_views.py` ; `tests/test_chrome.py`, `tests/test_i18n.py`.
3. **WP3 — Enregistrement automatique.**
   - Ce que fait le lot :
     - nouveau `calc/tools/autosave.py` : contextes (a), (b) et (c), lecture seule, garde contre la réentrance, `touched`, renommage jamais silencieux, report pendant `app.process` ;
     - `save(quiet)` dans les huit éditeurs ;
     - les `confirm_leave` réduits à un appel du module partagé, avec le `discard` propre à chaque onglet ;
     - `autosave_all(reason)` sur `applicationStateChanged`, avant `on_mode_changed` et avant l'export (PDF, Import données) ;
     - `reexport(quiet=True)` ;
     - Structure : `flush` à la perte de focus ;
     - Python : enregistré en (b) et (c) seulement.
   - Exigences : REQ-001, REQ-002, ARCH-004, A01-A06, A15, A16.
   - Tests : nouveau `tests/test_autosave.py` (un cas par éditeur : écrit, point éteint, aucune boîte ; invalide ; renommage ; brouillon neuf ; ID à moitié tapé ; lecture seule ; report ; boîte modale active ; ordre). Adaptés : `test_modes_window`, `test_window` (`_editors` a `autosave`), `test_structure_tab`, et les bouchons `Discard` de `test_editor_buttons`, `test_fire_tab`, `test_plan_overlay_v0116`, `test_plan_panes_v0116`, `test_plan_types_v0116`, `test_journal`, `test_positions_tab`, `test_member_check_tab`.
4. **WP4 — Plans : quatre vues et volet de gauche.**
   - Ce que fait le lot :
     - `VIEWS` et `VIEW_KIND` dans `DrawingTab` ;
     - `set_view`, qui montre les boîtes de la vue et les pages des deux `CurrentStack`, et reprend la sélection mémorisée de la vue ;
     - la liste des plans partagée entre *Dessin* et *Typst* (Nouveau, Dupliquer, Supprimer cachés en *Typst*) ;
     - la ligne `command_list` retirée, ainsi que le choix de plan de `CommandOptions` ;
     - `finish_layer_export` en quittant *Import* ;
     - la compilation lancée au `showEvent` ;
     - les cas vides dits ;
     - le `QSplitter` remplacé par des boîtes à poignée propre (nouvelle poignée dans `cards.py`) dans la `cards.Column` ;
     - le pied du volet avec `FoldButton` et les infobulles `pane_*` ;
     - hauteurs et repli dans `view_state`.
   - Exigences : REQ-004, REQ-005, REQ-006, UI-002 à UI-006, A08-A12.
   - Tests : `tests/test_views.py` (les quatre vues × deux onglets, aucune compilation avant affichage) ; `test_plan_panes_v0116` (poignée : +120 px, les autres boîtes inchangées, défilement, repli) ; adaptés : `test_plan_tab_rework`, `test_fire_tab`, `test_doc_frames_v0116`, `test_sheet_bundles_tab`, `test_panes`.
5. **WP5 — `build_reference`.**
   - Ce que fait le lot :
     - `call_command(name, positional, **options)`, qui lit les défauts dans la signature et cite selon le genre de l'option ;
     - les `call_*` existants deviennent des enveloppes, avec une sortie identique octet pour octet ;
     - les `call_*` manquants et les arguments manquants (B01) ;
     - les corrections de B02 (`aids: false`, citation de `caption`/`title`) ;
     - l'argument `document` de `journal-entries`.
   - Exigences : ARCH-005, B01, B02.
   - Tests : `test_commands` (les appels compilent, nouveaux cas), `test_plan_command_builder`, `test_journal:718` ; nouveau test de sortie identique pour chaque `call_*`.
6. **WP6 — Vue *Affichage* partagée, et vérifications.**
   - Ce que fait le lot :
     - `display_options.py` : spécification par commande, `DISMISSED`, sans défaut ;
     - `display_view.py` : `DisplayView` ;
     - `Collapsible` déplacé dans `cards.py`, `CommandField` dans `display_view.py` ;
     - le lexique `dv_*` ;
     - un `PdfPane` par onglet, construit à la demande, avec un cache par onglet et une annulation sans `stop()` ;
     - la bannière « modifié depuis l'export » et les notes de B05 ;
     - la migration de `show-plan`, `show-fire-plan` et `show-check-member` ;
     - les vues *Calcul · Affichage* de `MemberCheckTab`, avec suppression de `OPTION_DELAY_MS` sur le chemin de l'aperçu.
   - Exigences : REQ-007, UI-007, ARCH-002, ARCH-003, ARCH-006, ARCH-007, B03-B05, B08-B10.
   - Tests : nouveau `tests/test_display_view.py` (panneau égal à la signature, défaut initial égal au défaut Typst, chaque option changée compile, dossiers de cache distincts, rien de compilé hors *Affichage*, bannière, notes, parité `dv_*`) ; adaptés : `test_plan_command_builder`, `test_member_check_tab` (l. 310, 441, 850 → vues).
7. **WP7 — Modèle de statique et schéma.**
   - Ce que fait le lot : panneaux `show-static-model` et `show-schema`, avec les boucles ; `fill_commands`/`update_calls` remplacés par le hook *Affichage* ; vues *Dessin · Affichage*.
   - Exigences : REQ-008 ; fichiers `statics_tab.py`, `schema_tab.py`.
   - Tests : un test par onglet (chaque commande : l'appel change, un aperçu est demandé).
8. **WP8 — Moyens d'assemblage et moments polaires.**
   - Ce que fait le lot : panneaux `show-connector`, `show-connector-resistance`, `show-polar-moment`, `show-calc` et `var-of` ; vues *Calcul · Affichage*.
   - Exigences : REQ-008 ; fichiers `connectors_tab.py`, `woodcore_gui.py` (`PolarTab`), après coordination (CON-006).
   - Tests : même modèle qu'en WP7.
9. **WP9 — Charges.**
   - Ce que fait le lot : panneaux `show-calc`, `show-live-load`, `show-load-summary`, `show-line-load-summary`, `show-input`, `show-check`, `value-of` et `var-of` ; vues *Calcul · Affichage*.
   - Exigences : REQ-008 ; fichier `woodcore_gui.py` (`LoadsTab`).
   - Tests : même modèle qu'en WP7.
10. **WP10 — Journal et positions.**
    - Ce que fait le lot : panneaux `show-journal`, `journal-entries` (avec le document de la fenêtre) et `show-position-list` (premier appel de l'onglet Positions) ; vues *Saisie · Affichage*.
    - Exigences : REQ-008 ; fichiers `journal_tab.py`, `positions_tab.py`.
    - Tests : même modèle qu'en WP7.
11. **WP11 — Variables.**
    - Ce que fait le lot : panneaux `val`, `var`, `find` et `show-calc`, avec le choix de commande ; `eq` reporté (D15), noté dans `docs/open-questions.md` ; vues *Données · Affichage*.
    - Exigences : REQ-009, D12.
    - Tests : `tests/test_variables_tab.py` (`val`→`var` change l'appel, l'aperçu et les options), et le test du convertisseur.
12. **WP12 — Documentation et suite complète.**
    - Ce que fait le lot :
      - `docs/ui/window.md` : barre du haut, « plan tabs since v0.116 », vérifications, chaque onglet touché ;
      - `docs/architecture/layout.md` : `chrome`, `cards`, `autosave.py`, `display_view.py`, `display_options.py` ;
      - `docs/decisions.md` : D1, D2, D4, D5/A18, D9, D11, D13 ;
      - `docs/typst/api-conventions.md` : le tableau `eq` ;
      - `CHANGELOG.md`, « Nouveautés » fr/de/en de la version suivante.
    - Tests : `python tests/run_tests.py`, suite complète ; noms des échecs relevés s'il y en a.

## 15. Vérification

### Ronde 1 (`requirements-verifier`, 07.10.2026)

Résultat : **aucun ❌**. Verdicts : 16 ✅, 14 ⚠️. Le vérificateur a lancé les tests un par un — `test_views` 5, `test_autosave` 7, `test_display_view` 6, `test_call_command` 4, `test_plan_panes_v0116` 9, `test_member_check_tab` 32, `test_new_project` 34, `test_i18n` 20, `test_cards` 10, `test_plan_tab_rework` 12, `test_fire_tab` 50 : tous verts. Il a aussi écrit quatre sondes hors écran de son côté.

| Élément | Verdict ronde 1 | Ce qui manquait | Correction |
|---|---|---|---|
| REQ-001 | ⚠️ | aucun test pour les plans, le changement de vue ou le changement d'objet | `test_autosave.test_a_plan_a_view_and_another_object_save_without_a_box` |
| REQ-002 | ⚠️ | un brouillon neuf touché était enregistré au changement d'onglet ou de vue, contrairement à A02 ; le champ ID au focus et la fermeture n'étaient pas testés | `autosave.leave` : un brouillon neuf n'est enregistré qu'en (b) ou (c) ; `test_an_edit_is_saved…` (journal : le brouillon attend, puis `confirm_leave` l'enregistre) ; `test_the_focus_left_never_saves_an_id_being_typed_and_closing_asks_for_what_cannot_be_saved` |
| REQ-003 | ✅ | — | — |
| REQ-004 / REQ-005 / UI-006 | ⚠️ | tests de substitution (`minimumSizeHint`, `set_height`, `set_left_folded`) | `test_plan_panes_v0116.test_the_grip_is_dragged_the_pane_scrolls_and_the_arrow_folds_it_back_to_its_width` : fenêtre montrée, vrai tirage `QTest` de +120 px, maximum de la barre > 0, clic sur la flèche et retour à la largeur d'avant |
| REQ-006, REQ-007, REQ-010 | ✅ | — | — |
| REQ-008 / REQ-009 | ⚠️ | pas de test par onglet ; pas de test sur la vraie `VariablesTab` ; la bannière B04 sans bouton | `test_views.test_affichage_offers_each_tabs_commands_and_each_changes_the_call` (chaque onglet, chaque commande : appel distinct, aperçu demandé ou note ; Variables : `val` puis `var`, options différentes) ; bouton « Import données » à côté de la bannière (`DisplayView.import_button`) |
| UI-001, UI-002, UI-003, UI-005, UI-007 | ✅ | — | — |
| UI-004 | ⚠️ | « autre plan → appel et aperçu ; option → aperçu » non testé | `test_views.test_the_typst_view_takes_its_plan_from_the_list_and_recompiles_at_every_option` |
| ARCH-001, ARCH-002, ARCH-003 | ✅ | ARCH-002 : les plans gardent `CommandBuilder` (voir D17) | — |
| ARCH-004 | ⚠️ | dix `confirm_leave` construisaient encore leur `QMessageBox` | `autosave.confirm` pose la question unique ; les dix `confirm_leave` et `DrawingTab.ask_unsaved` y passent |
| ARCH-005 | ⚠️ | tous les `call_*` n'étaient pas couverts ; `form: "table"` n'est plus écrit | 19 `call_*` ajoutés à `test_call_command` ; l'écart est acté en D16 |
| ARCH-006 | ⚠️ | `OWN_PANELS` n'était confronté à aucune signature | `test_display_view.test_the_panels_of_their_own_take_only_arguments_their_command_has` |
| ARCH-007 | ⚠️ | les deux onglets de plan partageaient le dossier `plan-command` ; leur `PdfPane` était construit à l'avance | `CommandBuilder(cache_key=VIEW_KEY)` ; le volet est construit à la demande (`pane` est une propriété) |
| CON-001 à CON-006, §8 | ✅ | — | — |
| Documentation | ⚠️ | les paragraphes des onglets connecteurs, journal, variables, modèles statiques, schémas, charges, polaire et positions ; le paragraphe des plans ; le tableau `eq` | une note v0.117 dans chacun de ces paragraphes de `docs/ui/window.md` ; le paragraphe des plans corrigé ; `docs/typst/api-conventions.md` : la signature `eq(key, ..rest, …)` |
| Suite complète | ⚠️ | non lancée | relancée après les corrections (ronde 2) |

### Ronde 2 (`requirements-verifier`, 08.10.2026)

Résultat : **aucun ❌**. Sur les 13 éléments revus, 8 ✅ et 5 ⚠️ (ci-dessous). Le vérificateur a relancé les tests : `test_autosave` 9, `test_views` 7, `test_display_view` 7, `test_call_command` 4, `test_plan_panes_v0116` 10, `test_member_check_tab` 32, `test_variables` 44, `test_schema_tab` 41 — tous verts. Il a aussi rejoué les 39 sorties de `UNCHANGED` contre `build_reference` de `949cd25` : 39 sur 39 identiques.

| Élément | Ronde 2 | Suite donnée |
|---|---|---|
| REQ-004, REQ-005, UI-006, UI-004, ARCH-004, ARCH-005, D16, D17 | ✅ | — |
| REQ-001 | ⚠️ | Le code est correct : les sondes du vérificateur ont exercé annexes, plan incendie, compression et changement de document, sans boîte. Les tests de dépôt couvrent les autres éditeurs, la vue et l'objet, mais pas ces quatre cas. |
| REQ-002 | ⚠️ → corrigé | `test_what_is_refused…` affirmait une chaîne vide. Elle compare maintenant la ligne d'état à `autosave_refused` avec le nom réel, suivi d'une raison. |
| REQ-008 | ⚠️ | Pas de test de la bannière B04 ni de son bouton (les sondes les ont exercés). La compilation n'est pas testée pour `val`, `var`, `find`, ni pour les options à `needs`. Le parcours des onglets n'exerce que l'objet sélectionné. |
| REQ-009 / D18 | ✅ | Un domaine de l'export n'offre que `show-calc` : confirmé par l'ingénieur le 08.10.2026. |
| ARCH-006 | ⚠️ | Les trois panneaux propres ne sont confrontés à leur signature que dans un sens (valeurs ⊆ arguments). Le vérificateur constate qu'ils offrent aujourd'hui tous leurs arguments. |
| ARCH-007 | ⚠️ → corrigé | `test_views` affirme maintenant que plan et plan incendie ont des dossiers distincts. |
| Documentation | ⚠️ → corrigé | `window.md` (paragraphe `MemberCheckTab` réécrit), D16 reformulée, D18 dans `decisions.md`, infobulle d'UI-006 alignée. |
| Régression | ❌ → corrigé | `test_variables` sortait sur une violation d'accès (code 139) après 44 tests verts. La cause : trois tests créent un second `VariablesTab` sans parent, qui survit à l'application depuis que l'onglet porte une vue *Affichage`. Ils lui donnent maintenant la fenêtre pour parent ; sortie 0. Dans Woodcore, un onglet a toujours la fenêtre pour parent. |

**Suite complète** (après le redémarrage, en deux parties, avant et après `test_new_project`) : tout est vert, sauf `test_title_page.test_the_office_s_copy_of_the_bfh_form_is_the_builtin_one_and_is_offered_as_shared`. Cet échec ne vient pas de cette spec : la copie du formulaire BFH dans `../templates/` (6.10) diffère de `templates/forms/bfh/template.typ` (modifié le 7.10 à 16 h 12). Après les dernières retouches, les fichiers touchés ont été relancés : `test_schema_tab` 41, `test_views` 7, `test_display_view` 7, `test_cards` 10, `test_autosave` 9, `test_statics` 33, `test_toolbar` 16, `test_i18n` 20, `test_harness` 9, `test_call_command` 4, `test_richtext` 9, `test_variables` 44, `test_modes_window` 19.

**Tests ajoutés après la ronde 2** (demande de l'ingénieur, 08.10.2026), qui ferment les ⚠️ restants :
- **REQ-001** : `test_autosave.test_the_fire_plan_the_compression_an_annex_and_a_script_save_without_a_box` (le script attend le changement d'onglet, pas la perte de focus) et `test_another_document_saves_the_journal_of_the_one_left`. `test_autosave` : 11 verts.
- **REQ-008** :
  - `test_display_view.test_the_banner_says_what_the_export_lacks_beside_the_import_button` (bannière, bouton, `saved_state`/`export_state`, source plus récente que l'export) ;
  - `test_val_var_and_find_with_each_option_changed_compile_on_a_value_of_the_export` ;
  - `test_an_option_that_needs_what_the_object_lacks_is_greyed_and_left_out` (`@diagram` : l'exemple n'a aucun modèle qui en porte, d'où un test de grisage et non de compilation ; `scope=plans`) ;
  - `test_views.test_the_loads_offer_each_rows_commands_a_value_a_case_a_category_and_a_domain`.
- **ARCH-006** : `test_the_panels_of_their_own_take_only_arguments_their_command_has` vérifie maintenant les deux sens : tout argument nommé de `show-plan`, `show-fire-plan` et `show-check-member` est offert.

`test_display_view` 10, `test_views` 9 : tous verts.

**Le test rouge `test_title_page.test_the_office_s_copy_of_the_bfh_form…`** ne relève pas de cette spec. Le découpage de `CLAUDE.md` en `docs/` (`ae996b6`) a réécrit un **commentaire** du formulaire intégré `templates/forms/bfh/template.typ` (« CLAUDE.md section 4bis » → « docs/typst/language.md §4bis »), mais pas la copie du bureau dans le dépôt séparé `../templates/forms/bfh-academique/`. Seule cette ligne diffère ; `form.json`, `title.typ` et le logo sont identiques.

**L'autre session** (`2026-10-07-performance-erreurs-plans-legendes.md`) renomme la vue « Typst » des plans en « Affichage ». C'est la décision de l'ingénieur dans sa spec ; elle remplace les libellés d'UI-001 et d'UI-004.

## 16. Journal d'avancement

| Date | Statut | Fait / reste |
|---|---|---|
| 2026-10-07 | draft | spécification extraite de la source (24 points), état actuel relevé dans le code ; 4 questions ouvertes |
| 2026-10-07 | specified | réponses : Q-001 C (panneaux d'options à la main pour toutes les commandes), Q-002 A, Q-003 A, Q-004 A → D9–D12 |
| 2026-10-07 | reviewed | deux revues (A : vues, plans, enregistrement ; B : *Affichage*) : APPROUVER AVEC RÉSERVES ; réserves reprises (ARCH-004 à 007, REQ-002/003/008, CON-003, D13, D14) ; plan WP1–WP12 ; Q-005 (`eq`) posée avec l'approbation |
| 2026-10-07 | approved | l'ingénieur approuve ; Q-005 → B, `eq` reporté (D15). Implémentation : WP1 |
| 2026-10-07 | implementation | **WP1 fait** (REQ-003) : `export_all.py` écrit `export_all: no load workbook in … -- loads: none` sur stdout, `registry.no_workbook_note` retiré ; `tests/test_new_project.py` inversé — 34 tests verts ; docs `calculation-domains.md`, `decisions.md`, `build-and-release.md` |
| 2026-10-07 | implementation | **WP2 fait** (UI-001, REQ-010, ARCH-001) : `chrome.SegmentedSwitch` (`LanguageSwitch` dessus), `chrome.FoldButton`, `calc/tools/views.py` (mots `view_*`/`pane_*`, contrat `VIEWS`/`set_view(key, enter)`/`view`), sélecteur `viewSwitch` avant les langues, slot unique `on_tab_changed`, `apply_views`, `view_changed`, vue dans `usersettings` (`views`) |
| 2026-10-07 | implementation | **WP3 fait** (REQ-001/002, ARCH-004) : `calc/tools/autosave.py` (contextes, `refuse`/`warn`/`ask_rename`, `untouched_draft`, `SAVE_ON_FOCUS`, `flush_pending`) ; neuf éditeurs branchés ; `autosave_all` (focus d'application, changement de document, export) ; `reexport` silencieux, report pendant un processus. Reste : `tests/test_autosave.py` |
| 2026-10-07 | implementation | **WP4 fait** (REQ-004/005/006, UI-002–006) : `cards.SizedBox`, `cards.CurrentStack`, volet de gauche en boîtes + `FoldButton`, `VIEW_KIND`/`VIEW_BOXES`, `set_view`/`enter_view`, ligne « Commandes Typst » retirée, liste des plans en vue *Typst*, choix de plan du constructeur caché ; `test_plan_panes_v0116` 9, `test_plan_tab_rework` 12, `test_fire_tab` 50, `test_doc_frames_v0116` 10, `test_sheet_bundles_tab` 8, `test_panes` 6 — verts |
| 2026-10-07 | implementation | **WP5 fait** (ARCH-005) : `build_reference.call_command`/`call_expression`/`signature_defaults`/`Raw`/`typst_value`, tous les `call_*` dessus, `call_show_load_summary`, `call_show_line_load_summary`, `call_show_position_list`, `journal-entries(document:)` ; `tests/test_call_command.py` 4 verts (sorties inchangées sauf `form: "table"`, défaut) |
| 2026-10-07 | implementation | **WP6 fait** (REQ-007, UI-007, ARCH-002/006/007) : `display_options.py` (SPECS, DISMISSED, NOTES, OWN_PANELS, mots `ds_*` fr/de/en, `needs`), `display_view.py` (`SpecPanel`, `OwnPanel`, `Entry`, `DisplayView` à volet paresseux et cache par onglet, `ViewPanes`, `DisplayTab`, `saved_state`/`export_state`) ; `MemberCheckTab` en *Calcul · Affichage* (options propres, brouillon compilé), `Collapsible` retiré ; `test_display_view` 6, `test_member_check_tab` 32 verts |
| 2026-10-07 | implementation | **WP7–WP11 faits** (REQ-008/009) : modèle de statique et schéma (*Dessin · Affichage*, `@diagram`), moyens d'assemblage et moments polaires (*Calcul · Affichage*, N/V/M préremplis par l'essai), charges (*Calcul · Affichage* : val, var, show-input, var-of, value-of, show-live-load, show-calc, show-check, boucle, résumés), journal et positions (*Saisie · Affichage* : show-journal, journal-entries, show-position-list), variables (*Données · Affichage* : val, var, find, show-calc ; `eq` reporté) ; essai hors écran de tous les onglets sans erreur ni boîte |
| 2026-10-07 | testing | **WP12 en cours** : `tests/test_views.py` 5 et `tests/test_autosave.py` 7 verts ; `test_cards` adapté ; docs `window.md`, `layout.md`, `decisions.md`, `open-questions.md`, `CHANGELOG.md`, « Nouveautés » 0.117 fr/de/en ; version corrigée v0.118 → v0.117 (la 0.117 n'est pas publiée) ; suite complète en cours |
| 2026-10-07 | verification | **Ronde 1** du vérificateur : aucun ❌, 14 ⚠️, tous corrigés ou actés (D16–D18) ; voir §15. Suite complète relancée après les corrections |
| 2026-10-08 | verification | Redémarrage de l'ordinateur ; la suite complète est reprise en deux parties. **Ronde 2** : aucun ❌, 5 ⚠️ dont 3 corrigés ; le plantage de sortie de `test_variables` est corrigé. Restent REQ-001, REQ-008, ARCH-006 (preuves de test à compléter) et D18 (mot de l'ingénieur). Le travail est committé dans `ae996b6` par une autre session ; les retouches d'après sont non committées. La spec reste dans `active/` |
| 2026-10-08 | verification | L'ingénieur confirme D18 (`show-calc` seul) et le renommage « Typst » → « Affichage » (D19), puis demande de tout committer et pousser. Restent ⚠️ : des preuves de test pour REQ-001, REQ-008 et ARCH-006 (le comportement a été vérifié par sondes) |
| 2026-10-08 | verification | Tests ajoutés pour REQ-001, REQ-008 et ARCH-006 (voir §15) ; tous verts. Diagnostic du test rouge `test_title_page` : un commentaire réécrit par le découpage de la doc, que la copie du bureau n'a pas suivi |
