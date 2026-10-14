---
id: 2026-10-07-performance-erreurs-plans-legendes
titre: Démarrage et réactivité, gestionnaire central des erreurs, retouches des onglets de plan, légendes « Tableau N — titre », disposition des volets par écran
status: completed
cree: 2026-10-07
mis_a_jour: 2026-10-08
source: message écrit du 07.10.2026 (trois blocs : « Performance, chargement et système global de gestion des erreurs », liste « Pour le plan de position / tableaux / figures », « Refonte de l'interface — modes d'affichage et sauvegarde automatique »)
docs: [docs/architecture/principles.md, docs/architecture/layout.md, docs/ui/window.md, docs/typst/api-conventions.md, docs/decisions.md, docs/conventions/testing.md, docs/conventions/build-and-release.md]
---

# Démarrage, erreurs, plans, légendes — Spécification

## 1. Objectif

Woodcore devient lent, et surtout il **paraît bloqué** : rien n'apparaît pendant le lancement, et certaines vues (PDF, plans) ne suivent pas le défilement ni le zoom. L'ingénieur accepte un démarrage long s'il se voit, avec un écran de démarrage et une progression, et si l'usage est fluide ensuite. Les erreurs ne doivent plus surgir en boîtes de dialogue dispersées. Elles passent par un gestionnaire central, montré par deux indicateurs en haut à droite (🛑 critiques, ⚠ avertissements), avec un panneau où l'on développe, copie, supprime une erreur et ouvre son fichier. La même demande ajoute :

- une série de retouches des onglets de plan ;
- la forme « Tableau N — titre » et « Figure N — légende » dans les documents Typst ;
- le volet de navigation tout à gauche, dont les groupes se replient et la largeur se règle ;
- la disposition des volets retenue par onglet, par vue et par configuration d'écrans ;
- « Repris de T001 » remplacé par « — T001 ».

Le troisième bloc de la source reprend en grande partie la spécification `2026-10-07-vues-onglets-slider-et-volets` : enregistrement automatique, avertissement « no load workbook », volet de gauche des plans, sélecteur de vue. Celle-ci est déjà implémentée et en vérification. Cette spécification n'en refait rien : elle y renvoie point par point (§12) et ne prend que ce qui s'y ajoute.

## 2. Source

### Bloc A — « Woodcore — Performance, chargement et système global de gestion des erreurs »

> **T1** — « Woodcore commence à devenir de plus en plus lent. Je souhaite améliorer son fonctionnement afin que les temps de chargement soient beaucoup moins pénibles pour l'utilisateur. L'objectif n'est pas nécessairement de rendre **chaque opération instantanée**, mais de faire en sorte que : les opérations lourdes soient principalement effectuées au démarrage ; l'application reste réactive pendant les opérations qui doivent malgré tout être effectuées en arrière-plan ; l'utilisateur sache toujours que Woodcore est en train de travailler ; aucune fenêtre ne donne l'impression d'avoir « crashé » ou de freezer ; aucune fenêtre de terminal ou popup d'erreur système ne soit affichée à l'utilisateur ; toutes les erreurs soient centralisées dans un système d'erreurs intégré à Woodcore. »
>
> **T2** — « Avant toute modification, analyse l'architecture actuelle et identifie les principales causes des ralentissements et des freezes. »
>
> **T3** — « 1. Analyse préalable obligatoire. Avant de modifier le code, analyse : le processus de démarrage de Woodcore ; les opérations exécutées au lancement ; les opérations exécutées lors de l'ouverture de la fenêtre principale ; les imports Python lourds ; les initialisations de bibliothèques ; les chargements de fichiers ; les initialisations de projets ; les opérations Typst ; les calculs ; les opérations de filesystem ; les opérations synchrones qui bloquent actuellement le thread de l'interface ; les éventuels appels qui pourraient être exécutés en arrière-plan ; les opérations répétées inutilement. Identifie notamment les opérations qui provoquent : `UI freeze`, `CPU élevé`, `I/O disque`, `temps d'attente`, `ouverture de fenêtres externes`. »
>
> **T4** — « Ne fais pas de refactorisation massive uniquement pour « optimiser » sans avoir identifié une cause réelle. »
>
> **T5** — « L'objectif est d'obtenir une architecture permettant de déplacer les opérations lourdes vers des tâches de démarrage ou d'arrière-plan lorsque cela est pertinent. »
>
> **T6** — « 2. Nouveau comportement au lancement. Le fait que le lancement de Woodcore puisse prendre un certain temps ne me dérange pas. Ce qui me dérange est que **Windows donne actuellement l'impression que Woodcore est bloqué**. Lorsque l'utilisateur lance : `woodcore.exe` il doit immédiatement obtenir un retour visuel. »
>
> **T7** — « 2.1 Splash screen. Afficher immédiatement une image / un écran de démarrage Woodcore. Cet écran doit : afficher le logo ou l'identité visuelle de Woodcore ; apparaître avant les opérations lourdes ; donner immédiatement l'impression que l'application est en train de démarrer. Woodcore doit également apparaître correctement dans la barre des tâches Windows pendant son démarrage. »
>
> **T8** — « 3. Indicateur de progression au démarrage. Pendant le chargement initial, afficher un indicateur de progression. Deux solutions sont acceptées : Solution préférée : Une progression réelle : `0 % ━━━━━━━━━━━━━━━━━━━━━ 100 %` avec une indication de ce qui est actuellement chargé. Par exemple : `Chargement de Woodcore... ✓ Configuration ✓ Interface ✓ Bibliothèques → Chargement des modules de calcul → Initialisation du moteur Typst ○ Chargement du projet`. Alternative : Si une progression réellement fiable de 0 à 100 % n'est pas possible, utiliser une barre de progression indéterminée / animée. Dans tous les cas, **ne jamais afficher une application complètement figée avec uniquement le curseur Windows qui tourne**. »
>
> **T9** — « 4. Charger autant que possible au démarrage. L'objectif est que **l'immense majorité des éléments nécessaires au fonctionnement de Woodcore soient initialisés pendant le démarrage**. Je préfère : `Lancement ↓ Chargement relativement long ↓ Woodcore complètement initialisé ↓ Utilisation très fluide` plutôt que : `Lancement rapide ↓ Chaque action déclenche un nouveau chargement ↓ Freeze de plusieurs secondes ↓ Attente`. Identifie donc les éléments qui peuvent être préchargés intelligemment au démarrage. Attention cependant à ne pas charger inutilement des ressources qui ne seront jamais utilisées. »
>
> **T10** — « 5. Chargements pendant l'utilisation. Même après le démarrage, certaines opérations pourront nécessairement prendre du temps. Dans ce cas, **la fenêtre principale ne doit jamais sembler avoir crashé**. Il faut distinguer deux situations. »
>
> **T11** — « 5.1 Opération bloquante. Si une opération empêche réellement l'utilisateur d'interagir avec l'interface, afficher une fenêtre / overlay de chargement au centre. Exemple : `Chargement... ◌ ◌ ◌ Compilation du document Typst`. Cette interface doit être dynamique. Elle peut éventuellement afficher : ce qui est en train d'être chargé ; une progression ; une animation ; une estimation si celle-ci est fiable. La fenêtre principale ne doit pas simplement devenir blanche, grise ou « frozen ». »
>
> **T12** — « 5.2 Opération non bloquante. Si l'utilisateur peut continuer à utiliser Woodcore pendant le chargement, **ne pas afficher de popup au centre**. Dans ce cas, afficher simplement un indicateur de chargement discret : `[ Chargement... ]   Français | Deutsch | English`. Il doit être placé **en haut à droite, immédiatement à gauche des boutons de langue**. Cet emplacement doit être cohérent avec le système de slider/modes déjà demandé précédemment. »
>
> **T13** — « 6. Aucune fenêtre de terminal. Il arrive actuellement que des fenêtres de terminal Windows apparaissent brièvement. Cela arrive notamment lors de certaines compilations Typst. Ce comportement doit être supprimé. **Aucune fenêtre de terminal ne doit jamais apparaître à l'utilisateur**, même pendant une fraction de seconde. Les processus externes nécessaires doivent être lancés de manière silencieuse / sans fenêtre console. Cela concerne notamment : Typst ; les scripts externes ; les commandes système ; les outils auxiliaires ; tout autre processus lancé par Woodcore. Si un processus externe génère une sortie standard ou une erreur, celle-ci doit être capturée par Woodcore et intégrée au système de logs / erreurs décrit ci-dessous. »
>
> **T14** — « 7. Aucun popup d'erreur système. Les erreurs ne doivent plus être présentées sous forme de fenêtres popup dispersées dans l'application. Il ne doit plus y avoir de : `MessageBox` `Erreur !` `Exception...` qui interrompent brutalement l'utilisateur. Toutes les erreurs doivent être centralisées dans le **système global de notifications d'erreurs de Woodcore**. Les erreurs critiques peuvent éventuellement bloquer une opération si nécessaire, mais leur présentation doit rester intégrée à Woodcore. »
>
> **T15** — « 8. Nouveau système global de gestion des erreurs. En haut à droite de Woodcore, immédiatement à gauche des boutons de langue : `[ 🔴 ] [ 🟠 ]   Français | Deutsch | English`. Créer deux indicateurs permanents mais discrets. »
>
> **T16** — « 8.1 Erreurs critiques. Utiliser un symbole inspiré d'un **panneau STOP rouge** : forme octogonale rouge. Il doit afficher le nombre d'erreurs critiques. Exemple : `🛑 3`. Le symbole doit être coloré uniquement lorsqu'au moins une erreur critique existe. »
>
> **T17** — « 8.2 Avertissements / erreurs non critiques. Utiliser un **triangle d'attention orange / jaune**. Il doit afficher le nombre d'avertissements. Exemple : `⚠ 5`. Il doit être coloré uniquement lorsqu'au moins un avertissement existe. »
>
> **T18** — « 9. Animation lorsqu'une nouvelle erreur apparaît. Lorsqu'une nouvelle erreur apparaît : le symbole correspondant doit clignoter pendant environ **3 secondes** ; après ces 3 secondes, il arrête de clignoter ; il reste cependant coloré tant qu'au moins une erreur de cette catégorie existe. Exemple : `Nouvelle erreur ↓ 🛑 clignote pendant 3 s ↓ 🛑 reste rouge ↓ utilisateur consulte les erreurs ↓ toutes les erreurs supprimées ↓ symbole redevient discret / non coloré`. Même comportement pour les avertissements. »
>
> **T19** — « 10. Menu des erreurs. Lorsqu'on clique sur l'un des deux symboles, **ne pas ouvrir un popup Windows**. Ouvrir un grand panneau déroulant directement sous les indicateurs. Par exemple : `🛑 2 ⚠ 4 Français ┌ Erreurs │ 🛑 Erreur de calcul Impossible de calculer... │ 🛑 Fichier introuvable ... │ ⚠ Valeur manquante ... │ [Tout supprimer] ┘`. Le panneau : doit s'ouvrir directement sous les indicateurs ; ne doit pas dépasser en dehors de la fenêtre ; doit avoir une hauteur maximale ; doit devenir scrollable lorsque le nombre d'erreurs dépasse la hauteur disponible. »
>
> **T20** — « 11.1 Développer une erreur. Si le message est trop long pour être affiché entièrement : `⚠ Compilation Typst impossible Impossible de compiler...` un clic sur l'erreur doit permettre de la développer : `⚠ Compilation Typst impossible Impossible de compiler le document... Error: ... File: ... Line: 183 Column: 14 ...`. L'utilisateur doit pouvoir consulter le message complet. »
>
> **T21** — « 11.2 Copier une erreur. Chaque erreur doit pouvoir être copiée. Prévoir une action permettant de copier : le message ; idéalement les informations techniques utiles ; le fichier concerné ; la ligne / colonne si disponible ; le type d'erreur. Le contenu copié doit être exploitable pour un diagnostic ou pour être envoyé à une IA / développeur. »
>
> **T22** — « 11.3 Supprimer les erreurs. Permettre : de supprimer une erreur individuellement ; de supprimer toutes les erreurs d'un coup. Exemple : `[Supprimer] [Tout supprimer]`. La suppression doit uniquement supprimer la notification de l'interface, et ne doit évidemment pas masquer ou supprimer la cause réelle de l'erreur. »
>
> **T23** — « 12. Référence aux fichiers. Lorsqu'une erreur concerne un fichier, afficher clairement le fichier concerné. Exemple : `⚠ Erreur de compilation Fichier : C:\...\rapport.typ Ligne : 183 Colonne : 14`. Le fichier doit pouvoir être ouvert directement depuis le message d'erreur. Si cela est possible, prévoir également : ouverture à la ligne concernée ; ouverture dans l'éditeur approprié. »
>
> **T24** — « 13. Traduction des erreurs. Les messages destinés à l'utilisateur doivent être disponibles en : français ; allemand ; anglais. La langue doit suivre la langue actuellement sélectionnée dans Woodcore. Il faut distinguer : Message utilisateur, traduit : `Impossible de compiler le document.` Informations techniques : conserver les informations techniques originales lorsqu'elles sont nécessaires au diagnostic : `Typst error: unknown variable `foo``. L'objectif est que l'utilisateur comprenne l'erreur dans sa langue sans perdre les informations techniques utiles. »
>
> **T25** — « 14. Architecture du système d'erreurs. Le système doit être **centralisé et générique**. Éviter que chaque module crée son propre popup ou son propre système de notification. Créer un système capable de recevoir par exemple : `ErrorManager ├── CriticalError ├── Warning └── Info`. Chaque erreur devrait idéalement contenir des informations structurées telles que : `type severity message technical_message source file line column timestamp actions`. Les modules de Woodcore doivent pouvoir envoyer une erreur au système central sans avoir à gérer eux-mêmes l'affichage. Exemple conceptuel : `Calcul ↓ Erreur ↓ ErrorManager ↓ Interface globale ↓ 🛑 1` ou : `Typst ↓ Erreur de compilation ↓ ErrorManager ↓ ⚠ 1`. Cela permettra également d'éviter la multiplication future des systèmes d'erreur. »
>
> **T26** — « 15. Séparation entre erreurs, avertissements et informations. Prévoir dès maintenant une architecture extensible permettant éventuellement d'avoir plus tard : `🛑 Critique ⚠ Avertissement ℹ Information ✓ Succès`. Pour l'instant, l'interface visible doit principalement gérer : erreurs critiques ; erreurs non critiques / avertissements. Ne pas nécessairement ajouter d'autres indicateurs visuels si cela surcharge l'interface. »
>
> **T27** — « 16. Performance et réactivité. Le système de chargement ne doit pas simplement ajouter des animations par-dessus une architecture lente. L'objectif est également de rendre Woodcore réellement plus performant. Identifier notamment : les opérations qui bloquent le thread UI ; les calculs qui pourraient être exécutés dans un worker ; les compilations Typst ; les accès disque ; les opérations de parsing ; les imports lourds ; les recalculs inutiles ; les opérations répétées ; les chargements synchrones ; les initialisations qui peuvent être préchargées. Utiliser une architecture appropriée pour les opérations longues afin que **le thread de l'interface reste réactif autant que possible**. Attention aux opérations qui doivent absolument rester synchronisées : ne pas déplacer arbitrairement une opération dans un thread si cela peut créer des problèmes de concurrence ou de cohérence des données. »
>
> **T28** — « 17. Critères de réussite. À la fin de l'implémentation : Démarrage — [ ] `woodcore.exe` affiche immédiatement le splash screen. [ ] Woodcore apparaît correctement dans la barre des tâches. [ ] Un indicateur de chargement est visible. [ ] Les opérations lourdes sont chargées autant que raisonnablement possible au démarrage. [ ] L'utilisateur ne voit jamais simplement une fenêtre Windows « frozen ». Pendant l'utilisation — [ ] Les opérations longues ne bloquent plus visuellement l'interface sans explication. [ ] Une opération bloquante affiche un overlay de chargement. [ ] Une opération non bloquante affiche un indicateur discret en haut à droite. [ ] L'interface reste réactive lorsque cela est techniquement possible. Processus externes — [ ] Aucune fenêtre de terminal n'apparaît. [ ] Typst s'exécute silencieusement. [ ] Les stdout/stderr utiles sont capturés. Erreurs — [ ] Aucun popup d'erreur système. [ ] Les erreurs passent par le gestionnaire central. [ ] Les erreurs critiques apparaissent dans l'indicateur rouge. [ ] Les avertissements apparaissent dans l'indicateur orange. [ ] Le nombre d'erreurs est affiché. [ ] Les nouveaux messages clignotent pendant environ 3 secondes. [ ] Le panneau reste coloré tant qu'il contient des erreurs. [ ] Le panneau s'ouvre sous les indicateurs. [ ] Le panneau est scrollable. [ ] Les messages longs peuvent être développés. [ ] Les messages peuvent être copiés. [ ] Les erreurs peuvent être supprimées individuellement. [ ] Toutes les erreurs peuvent être supprimées. [ ] Les fichiers référencés peuvent être ouverts. [ ] Les messages utilisateur sont traduits en français, allemand et anglais. Architecture — [ ] Le système de chargement est réutilisable par les différents modules. [ ] Le système d'erreurs est centralisé. [ ] Les modules n'implémentent plus leurs propres popups d'erreur. [ ] Il n'y a pas de duplication inutile. [ ] Il n'y a pas de hardcoding inutile. [ ] Le système peut être étendu facilement à de nouveaux types d'erreurs et de nouveaux modules. »
>
> **T29** — « 21. Revue finale obligatoire. Une fois l'implémentation terminée, effectue une revue complète. Vérifie en particulier : performance réelle du démarrage ; réactivité de l'interface ; absence de freezes ; absence de fenêtres terminal ; absence de popups d'erreur ; fonctionnement du système centralisé d'erreurs ; fonctionnement dans les trois langues ; comportement lorsque plusieurs erreurs apparaissent simultanément ; comportement lorsque les erreurs sont supprimées ; comportement avec des messages très longs ; comportement avec des chemins de fichiers très longs ; comportement lorsque Typst échoue ; comportement lorsqu'un fichier n'existe pas ; comportement lorsqu'un calcul échoue ; comportement lorsqu'une opération prend plusieurs secondes. Enfin, vérifie l'architecture du code produit et corrige les éventuels problèmes de : duplication ; hardcoding ; mauvaise séparation des responsabilités ; couplage excessif ; gestion incorrecte des threads ; gestion incorrecte des exceptions ; fuites de ressources ; opérations synchrones inutiles. **Ne considère pas la tâche terminée uniquement parce que l'interface semble fonctionner : le système doit également être robuste, réutilisable et performant.** »

### Bloc B — « Pour le plan de position », tableaux et figures Typst

> **T30** — « pouvoir activer et désactiver le magnétisme dans le volet de droite lorsque rien n'est sélectionné »
>
> **T31** — « pouvoir tourner les poteaux »
>
> **T32** — « dans le volet de droite, lorsqu'un obet dessiné est sélectionné, la "Position" possède encore les noms en allemand (e.g. T001 - Träger, Fichte »
>
> **T33** — « renommer l'onglet "Plan de position" en "Plan de positions" »
>
> **T34** — « l'affichage des pdf (dans la vue "Document") est très longue. En zoomant, le texte devient net que très lentement (dans certaines zones, il ne devient jamais net, sans raison apparente). Il n'y a pas de fluidité au scrolling ou au zooming. Comment améliorer cela? Faudrait-il utiliser un visualiseur de pdf opensource et léger? »
>
> **T35** — « l'affichage des pdf + svg (affichage Dessin ou Export) est également pas très fluide. Y a-t-il une manière de fluidifier tout cela ? »
>
> **T36** — « dans l'affichage "Export", on doit voir toutes les pages qui composent un document lorsqu'on navigue dans ses plans. On doit pouvoir modifier le nom, la description, l'étage, l'id du document. Par défaut, les valeurs sont reprises automatiquement lors de l'import dessus du premier plan. »
>
> **T37** — « dans l'afficahge "Export", lorsque je sélectionne un plan et clique pour modifier l'échelle, le menu déroulant s'ouvre et se ferme instantanément »
>
> **T38** — « dans l'afficahge "Export", il faut pouvoir redimensionner les liste de positions à l'aide de la souris »
>
> **T39** — « dans l'affichage "Dessins", lorsque je clique sur "Coupe..." pour lié la coupe en plan à une coupe en élévation que se passe-t-il lorsque je choisis un plan? J'ai l'impression qu'il ne se passe pas. Ce qu'il doit se passer à mon avis: ouvre le plan sélectionné dans le menu déroulant et permet de dessiner la ligne d'étage ou le rectangle d'étage directement avec le bon étage écrit »
>
> **T40** — « dans l'affichage "Dessins", lorsque rien n'est sélectionné, on doit pouvoir activé ou désactivé le fait que la longueur des éléments soient indiqués (longueur de chaque mur, chaque T, longueur de chaque côté de dale. En sélectionnant un unique objet, on doit pouvoir activer ou désactiver cet affichage pour un unique élément. Ensuite, dans légende, il doit y avoir en plus, sous le descriptif des symboles, les métrés totaux par type d'objet. »
>
> **T41** — « renomme en haut dans les 4 affichages "Typst" en "Affichage" »
>
> **T42** — « Pour les tableaux dans typst: tous les titres de tableaux doivent suivre le format suivant: Tableau 1 --- Les documents de référence. I.e. Tableau [numéro] --- (long tiret) [titre du tableau]. »
>
> **T43** — « Pour les figures dans typst: dans typst, le caption des figures doit apparaître ainsi: Figure 1 --- Système statique. Donc Figure [numéro] --- (long tiret) [caption] »

### Bloc C — « Refonte de l'interface Woodcore — modes d'affichage et sauvegarde automatique »

> **T44** — « Je souhaite faire évoluer l'interface de Woodcore afin de la rendre plus claire, cohérente et extensible. L'objectif principal est de séparer clairement les différentes étapes de travail : importation des données, dessin/calcul, génération Typst et export des documents. Cette logique doit être réutilisable dans la majorité des modules de Woodcore. Avant toute modification, analyse l'architecture actuelle du projet et identifie les composants qui peuvent être réutilisés. Évite autant que possible de créer des implémentations spécifiques à chaque onglet : le système de modes d'affichage doit être générique et extensible. »
>
> **T45** — « 1. Sauvegarde automatique. Le comportement actuel indiquant qu'une modification a été effectuée doit être conservé : Lorsqu'une modification est effectuée, un point blanc apparaît pour indiquer qu'il existe des modifications non sauvegardées. Cependant, dès que l'utilisateur : change de fenêtre ; change d'onglet ; change de mode d'affichage ; ou effectue une autre action qui implique de quitter la vue actuelle ; Woodcore doit enregistrer automatiquement les modifications, sans demander de confirmation à l'utilisateur. Le point blanc doit ensuite disparaître lorsque la sauvegarde automatique a été effectuée. Il ne doit donc plus y avoir de fenêtre demandant « Voulez-vous enregistrer ? » lors de ces changements de contexte. »
>
> **T46** — « 2. Suppression du warning concernant `Belastungsannahmen`. Une erreur/warning apparaît régulièrement lors de l'export : `export_all: WARNING no load workbook in C:\Users\Quebec\Downloads\TTest -- the export goes on without loads: dead-load, snow-load, wind-load have no case, and show-calc finds none of them, until a file whose name contains 'Belastungsannahmen' and ends in .xlsm or .xlsx is copied into the folder`. Ce warning ne doit plus être affiché. La raison est que cette architecture est temporaire : à terme, les actions/charges seront directement calculées par Woodcore et ne dépendront plus d'un fichier Excel externe `Belastungsannahmen`. Les charges variables issues de la SIA 261, tableau 8, ne nécessitent de toute façon pas ce workbook. Important : Ne pas simplement masquer artificiellement le message si celui-ci révèle une dépendance architecturale problématique. Vérifier d'abord : pourquoi `export_all` recherche encore ce fichier ; quelles parties du code dépendent actuellement de ce workbook ; si cette dépendance peut être rendue optionnelle ; puis supprimer proprement le warning dans le flux normal. Le système doit continuer à fonctionner correctement sans fichier `Belastungsannahmen`. »
>
> **T47** — « 3. Amélioration des volets de gauche. Cela concerne notamment : Plan de positions ; Plan de protection incendie ; et plus généralement les vues utilisant un volet de navigation à gauche. 3.1 Scroll vertical : Le volet gauche doit pouvoir être entièrement scrollé : vers le haut ; vers le bas. Le scroll doit fonctionner indépendamment du contenu du volet central et du volet droit. »
>
> **T48** — « 3.2 Réduction complète du volet. Ajouter une flèche située en bas à gauche permettant de réduire complètement le volet gauche. Le comportement doit être similaire au système de réduction déjà présent pour le volet situé complètement à gauche de l'application. Lorsque le volet est réduit : son contenu disparaît ; l'espace est récupéré par la zone de travail ; une commande permet de le rouvrir. »
>
> **T49** — « 3.3 Redimensionnement des TextBox. Les TextBox présentes dans le volet gauche doivent pouvoir être redimensionnées manuellement verticalement. L'utilisateur doit pouvoir : agrandir une TextBox vers le bas ; réduire une TextBox vers le bas. Le redimensionnement d'une TextBox ne doit pas modifier automatiquement la hauteur des autres TextBox. Chaque zone doit donc avoir sa propre hauteur contrôlable. »
>
> **T50** — « 4. Nouveau système global de modes d'affichage. Je souhaite introduire un système de slider de modes permettant de changer la manière dont l'utilisateur interagit avec l'onglet courant. Ce slider doit être placé en haut à droite, immédiatement à gauche des boutons de langue. Actuellement, les boutons de langue sont : `Français | Deutsch | English`. Le nouveau système doit être : `[ SLIDER DE MODE ]   Français | Deutsch | English`. Le slider ne doit pas être spécifique aux plans : il doit devenir un composant générique de l'interface Woodcore. Son contenu et le nombre de positions peuvent varier selon le type d'onglet, mais le principe UX doit rester identique. »
>
> **T51** — « 5. Modes pour les plans. Pour les plans, notamment : Plan de position ; Plan de protection incendie ; le slider doit comporter quatre positions : 1. Document import 2. Dessin 3. Typst 4. Document export. L'objectif est d'éviter d'avoir simultanément trop d'informations dans les différents volets. »
>
> **T52** — « 5.1 Mode « Document import ». Dans ce mode : Volet gauche : Afficher uniquement les documents importés. Tout le reste doit disparaître du volet gauche, notamment : Plan de position ; Éléments et axes ; Documents export ; Commandes Typst ; etc. Volet central / droit : Afficher uniquement les informations et fonctionnalités qui existent actuellement lorsqu'un document importé est sélectionné. L'utilisateur doit donc avoir une vue extrêmement simple : `Documents importés ↓ Document sélectionné ↓ Informations / contenu du document`. »
>
> **T53** — « 6. Mode « Dessin ». Dans le mode Dessin : Volet gauche : Afficher : Plan de position ; Éléments ; Axes. Centre / droite : Afficher les outils permettant de créer et modifier le dessin, comme actuellement. L'objectif est de conserver les fonctionnalités existantes, mais de supprimer de cette vue toutes les fonctionnalités qui appartiennent aux autres modes. »
>
> **T54** — « 7. Mode « Typst ». Dans le mode Typst : Volet gauche » *(la source s'interrompt ici et passe au point suivant)*
>
> **T55** — « Volet tout à gauche : Il doit être possible de réduire ou de maximiser verticalement les sections. Par exemple, "Projet" qui contient Plan de position, Plan de protection incendie, Positions, Journal, etc... doit pouvoir être réduit ou maximisé. »
>
> **T56** — « La largeur du volet tout à gauche doit pouvoir être modifiée »
>
> **T57** — « les dispositions des volets (largeurs, hauteur, etc...) sont enregistrés par fenêtre d'affichage (par onglet, par affichage, par mode) pour un display spécifique (i.e. si je branche mon ordinateur portable à un écran, il y a une sauvegarde d'affichage pour l'écran externe lorsqu'il est utilisé et une sauvegarde pour mon pc portable lorsqu'il est utilisé sans l'écran externe) »
>
> **T58** — « "Repris de" : À plusieurs endroits dans woodcore, lorsqu'une valeur est reprise d'une position, il est écrit "Repris de xxx". À la place, il doit symplement y avoir --- (long tiret) xxx. E.g. --- T001. »

### État actuel relevé dans le code (07.10.2026)

**Démarrage (mesuré)**
- L'import de `calc/tools/woodcore_gui.py` prend **9 s à chaud** et **30 s à froid** (`python -X importtime`, deux mesures à chaud : 9,5 s et 8,8 s ; à froid 29,7 s). Aucune fenêtre n'existe pendant ce temps.
- Le premier poste est `openpyxl`, 4–5 s à chaud et 15 s à froid, dont `numpy` 1 s à chaud et 6,7 s à froid. Il est importé par `build_reference` au chargement du module, alors qu'il ne sert qu'à lire ou écrire des classeurs. Suivent `typst_gui`/`typst_check` (`urllib`, `http.client`) 2,4 s à froid, `project` 1,7 s et `home_page` 1,5 s. PySide6 complet prend environ 0,7 s.
- L'écran d'attente existant (`busy.Splash`, `woodcore_gui.py` ~4236) n'apparaît qu'**après** :
  - l'import complet ;
  - `QApplication` ;
  - `project.use` ;
  - le verrou du projet ;
  - les migrations ;
  - `export_all.seed`.

  Il couvre ensuite la construction de la fenêtre : `MainWindow.build`, mesurée 8,6 s sur le projet d'exemple le 03.10.2026. Cette construction crée tous les onglets d'un coup, avec `busy.pump()` entre deux onglets.
- L'identité de la barre des tâches existe déjà : `SetCurrentProcessExplicitAppUserModelID("Woodcore.App")` avant toute fenêtre, `app.setWindowIcon`, `claim_taskbar_icon(window)`. Mais rien n'est visible avant l'écran d'attente.
- `stallwatch` existe (`calc/tools/stallwatch.py`). Il consigne dans `%LOCALAPPDATA%\Woodcore\stalls.log` tout arrêt de plus de 1,5 s, mais n'est installé qu'après `window.show()` : les gels du démarrage n'y figurent pas. Le journal ne contient aucune trace récente.
- `Woodcore.exe` est un PyInstaller « onedir » (`console=False`), lancé par `Woodcore-Launcher.exe`. L'entrée `packaging/entry_gui.py` importe `woodcore_gui.main` : les 9–30 s d'import y sont aussi.
- L'export de la fenêtre lance `calc/cli.py export --data-only` dans un **nouveau processus Python** à chaque ré-export. Celui-ci réimporte ses modules, dont `openpyxl` si `build_reference` est sur son chemin. Cause probable des exports lents, à mesurer.

**Fils et attente**
- Des tâches de fond existent, chacune avec son propre mécanisme :
  - `threading.Thread` : `busy.py`, `drawing_tab.preload`, export des calques, vérifications PyPI, Typst et mises à jour ;
  - `QThread` : `pdf_pane._Job`, `sheet_editor._Job`, `variables_tab.Read` ;
  - `QProcess` : export et compilations.
- `busy.py` porte une carte d'attente avec `BusyCursor` et `processEvents(ExcludeUserInputEvents)`.

**Processus externes**
- `calc/proc.py` est le point unique : `run`, `popen`, `qprocess`, `start_detached`, avec `CREATE_NO_WINDOW`. Un test AST le garde (`tests/test_no_console.py`).
- La fenêtre de terminal vue par l'ingénieur n'a donc pas encore de cause identifiée. Hypothèses à vérifier : le lancement par `Woodcore.bat`, dont la console s'ouvre au double-clic et qui retombe sur `python.exe` sans `pythonw` ; `QProcess` qui ne pose `CREATE_NO_WINDOW` que si le parent n'a pas de console ; un appel qui contourne `proc`, comme `os.startfile` ou un outil tiers.

**Popups**
- 128 `QMessageBox` dans 23 fichiers de `calc/tools/` : 54 `warning`, 10 `critical`, 13 `information`, 27 `question`. Les plus gros : `drawing_tab.py` 26, `woodcore_gui.py` 18, `settings_dialog.py` 10, `home_page.py` 9.
- Deux `MessageBoxW` système via `ctypes` : `packaging/launcher.py:140`, quand aucune version n'est trouvée, et `woodcore_gui.py:42`, quand PySide6 manque. Qt n'est pas disponible à ces deux endroits.
- Un `install_error_box(window)` existe. Les avertissements d'export (`export_warnings`) s'affichent dans une `QMessageBox.warning`.
- Les bandeaux de `woodcore_gui.py` ~3130–3168 sont une autre forme de message : lecture seule, migration, données périmées, mises à jour, Typst.
- Aucun journal applicatif n'existe : pas de `logging`, pas de fichier de log.

**En-tête**
- `woodcore_gui.py` ~3089–3126 : `[marque] [méta] ← étirement → [pdf_chip] [viewSwitch] [langues] [recharger] [exporter] [pdf]`.

**Plans**
- Magnétisme : deux cases `snap_axes` et `snap_elements` (`plan_tab.py` ~1551) existent, hors du volet de droite « rien de sélectionné » (`plan_tab.py` ~1723).
- Rotation : aucune rotation pour les poteaux ni les poutres. Seuls les symboles de charge ponctuelle ont un `angle` (`plan.py` ~1290).
- Libellé de position : `plan_tab.py` ~1817 construit `T001 — Träger, Fichte` avec `model.type_name` sans langue et le matériau tel qu'il est enregistré.
- Nom de l'onglet : `strings.json` dit déjà « Plan de positions », mais `plan_tab.py:69` garde « Plan de position ».
- Noms des vues : `views.py` a « Import / Dessin / Typst / Export », et « Typst » dans les trois langues.
- PDF :
  - vue *Document* : `document_view.py`, `QPdfDocument` (PDFium). Une image de base de 480 px est rendue, puis une image nette plafonnée à 12 Mpx, après 180 ms d'arrêt, **sur le fil de l'interface** ;
  - *Dessin* : `plan_canvas.py`, son propre `RenderCache` (256 Mo en mémoire, 300 Mo sur disque), des tuiles à l'arrêt et un `QGraphicsSvgItem` pour le calque SVG ;
  - *Export* : `sheet_editor.py`, son propre `QPdfDocument`.

  Il y a donc **trois moteurs de rendu PDF**. Paquets installés : `pypdf` (pages), QtPdf. Pas de PyMuPDF ni de pypdfium2.
- Échelle : une `QComboBox` éditable (`sheet_editor.py` ~1462), branchée sur `activated` et `editingFinished`.
- Listes de positions : un objet de la feuille (`add_position_list`, ~2082) de largeur fixée, sans poignée de redimensionnement.
- « Coupe… » (`plan_tab.choose_section`, ~1413) enregistre seulement `section_plan` et change le libellé. Rien ne s'ouvre, d'où l'impression qu'« il ne se passe rien ». Les outils `storey-line` et `storey-box` existent sur la coupe en élévation, avec un choix d'étage (`plan_hint_storey_missing`).
- Longueurs : la case `show_lengths` est propre au plan et ne couvre que les murs V, H, W. Il n'y a ni réglage par élément, ni longueur des poutres T ou des côtés de dalle D, ni métré dans la légende (`plan_svg.legend_lines`, ~805).
- Documents d'export : un recueil (*bundle*) de `Plans/bundles.json` vaut `{name, sheets}`. Il n'a ni id, ni description, ni étage. Il apparaît comme un dossier de `sheet_list.py`.

**Typst**
- Les légendes passent par `figure(caption: figure.caption(position: …))` (`lib/calc-engine.typ` ~2145) et par `show figure.caption` dans les formes (`templates/forms/*/template.typ`). Le séparateur par défaut de Typst 0.15.1 s'applique. Aucun `set figure.caption(separator: …)` n'existe.

**Volet tout à gauche**
- `chrome.SideNav` (`woodcore_gui.nav_widget` ~3207) se replie en icônes (`nav_collapsed`). Ses groupes ne se replient pas un à un, et sa largeur n'est pas réglable.

**Dispositions**
- Chaque onglet garde ses `splitter.setSizes` dans son propre état : `annex_tab`, `commands_tab`, `connectors_tab`, `drawing_tab`, `dsl_tab`, `journal_tab`, `member_check_tab`, `positions_tab`, `python_tab`, `document_view`, `flowbar`. Rien ne dépend de l'écran.

**« Repris de »**
- Quatre clés, chacune propre à son onglet :
  - `cn_followed` : `connectors_tab.py:152/243/334`, « {value}, repris de {pid} » ;
  - `mc_followed` : `member_check_tab.py:146/249/350` ;
  - `mc_w_followed` : « mm, repris de la section » ;
  - `sc_followed` : `schema_tab.py:259/394/529`, « repris de {pid} ».

  En allemand : « aus {pid} » ou « von {pid} übernommen ». En anglais : « from {pid} ».

## 3. Exigences fonctionnelles

### REQ-001 — Mesurer avant d'optimiser
- **Exigence** : Woodcore doit disposer d'une mesure reproductible du démarrage et des opérations lourdes, avant toute optimisation et après chacune. Le script `tests/perf_startup.py` (ou une option `--profile-startup`) chronomètre chaque phase : imports, `QApplication`, projet, construction de chaque onglet, premier affichage. L'analyse demandée en T2/T3 est écrite dans `docs/architecture/performance.md`, avec les causes classées et leurs mesures. Chaque optimisation du plan cite la mesure qui la justifie.
- **Source** : T2, T3, T4, T27
- **Priorité** : doit
- **Critère d'acceptation** : `docs/architecture/performance.md` donne, avant et après, le temps de chaque phase sur le projet d'exemple, à froid et à chaud. Aucune modification de performance n'est faite sans une ligne de ce tableau qui la motive.

### REQ-002 — Écran de démarrage immédiat
- **Exigence** : au lancement de `Woodcore.exe`, de `Woodcore.bat` ou de `woodcore_gui.py`, un écran de démarrage aux couleurs de Woodcore (logo `woodcore.svg`, nom, version) doit apparaître **avant les imports lourds**. Seuls PySide6 (QtCore, QtGui, QtWidgets) et le thème sont chargés avant lui. L'icône est dans la barre des tâches dès cet écran : AppUserModelID et `setWindowIcon` avant lui. L'écran couvre aussi la page d'accueil (`--home`) et l'ouverture d'un projet depuis l'accueil.
- **Source** : T6, T7
- **Priorité** : doit
- **Critère d'acceptation** : sur le projet d'exemple, à chaud, l'écran est visible moins de 1,5 s après le lancement. Aujourd'hui, rien n'est visible avant 9 s. Mesure par le script de REQ-001, horodatée de la création du processus au premier `paintEvent` de l'écran. Il est dans la barre des tâches avec l'icône Woodcore (essai manuel, capture).
- **Après revue** : entrée légère `calc/tools/woodcore_start.py`. Elle pose AppUserModelID, `QApplication`, le thème, l'écran étagé et `excepthook`, puis importe `woodcore_gui` et appelle `main()`. `packaging/entry_gui.py`, `Woodcore.bat` et `relaunch_command` passent par elle. `woodcore_gui.py` lancé directement y renvoie avant ses imports. `project.take_argument` est isolé dans un module léger, sans copie. L'écran n'est **pas** `Qt.Tool`, pour avoir un bouton dans la barre des tâches, et `claim_taskbar_icon` s'y applique. Le lanceur `onefile` est mesuré aussi (A03).

### REQ-003 — Progression réelle et écran jamais figé
- **Exigence** : l'écran de démarrage doit montrer une barre de 0 à 100 % et la liste des étapes : ✓ faite, → en cours, ○ à venir. Les étapes sont Configuration, Interface, Bibliothèques, Modules de calcul, Moteur Typst, Projet, puis Onglets avec le nom de l'onglet en cours. Le poids de chaque étape vient des mesures de REQ-001 et est mis à jour par la dernière mesure locale. L'animation ne s'arrête jamais plus de 0,25 s. Les imports et le travail sans Qt tournent dans un fil de travail pendant que le fil de l'interface anime. Les constructions de widgets, qui doivent rester sur le fil de l'interface, sont découpées assez fin pour que la boucle d'événements tourne entre elles. Windows ne marque jamais l'écran « Ne répond pas ».
- **Source** : T8, T1
- **Priorité** : doit
- **Critère d'acceptation** : `stallwatch` est installé dès l'écran de démarrage, avec un seuil de démarrage de 0,25 s pour l'écran. Il ne consigne aucun arrêt pendant trois lancements à chaud du projet d'exemple. Les étapes s'affichent dans les trois langues.
- **Après revue** : les bibliothèques sans Qt (`openpyxl`, `numpy`, `urllib`/`typst_check`, domaines, `project`) s'importent dans un fil de travail. Les modules Qt s'importent sur le fil principal, un à un, avec `pump` entre chacun. `build()` devient un générateur `build_steps()` piloté par l'écran, et `build()` l'épuise de façon synchrone pour les tests. Le seuil de `stallwatch` devient un paramètre d'`install`. Le critère de 0,25 s vaut **à chaud**. À froid, le chargement d'une DLL qui tient le GIL est mesuré et écrit dans `performance.md`, pas exigé. Les poids des étapes sont un cache JSON avec `schema_version`, toléré absent ou illisible (A04, A12).
- **Écart (vérification, 08.10.2026)** : REQ-003 n'est pas tenue : le plus long arrêt de l'écran mesuré est de 0,46–0,53 s sur une machine peu chargée, 0,9–1,3 s avec les autres sessions en cours (`performance.md` §5). C'est chaque fois le constructeur d'**un** onglet (moyens d'assemblage, schémas, modèles statiques, moments polaires), qui s'exécute d'un bloc sur le fil de l'interface. L'écran reçoit une image entre deux onglets et entre les trois volets du plan. Découper ces constructeurs est un lot à part, dans des fichiers que d'autres sessions modifient (`docs/open-questions.md`). `stallwatch` reçoit bien son seuil (`WOODCORE_STALL_S`) ; `build()` n'est pas devenu un générateur, l'écran étant nourri par `woodcore_start.step` et `pump`.

### REQ-004 — Tout préparer au démarrage, sauf l'inutile
- **Exigence** : pendant l'écran de démarrage, Woodcore doit préparer ce que l'usage demandera, selon D7 : modules, normes, glossaires, onglets, données du projet, liste des documents et des plans, et premiers rendus de l'onglet rouvert. Il ne prépare pas ce qui ne servira probablement pas : les onglets jamais ouverts ne se compilent pas.
- **Source** : T9, T5
- **Priorité** : doit
- **Critère d'acceptation** : après l'écran de démarrage, le premier passage dans chaque onglet ne déclenche aucun import Python nouveau. Le contrôle passe par `sys.modules` avant et après, dans un test hors écran. Changer d'onglet ne bloque pas plus de 0,25 s : `stallwatch` reste vide sur un tour de tous les onglets.
- **Après revue** : le test « aucun import nouveau » tourne dans un sous-processus neuf, car la suite partage `sys.modules` (A13).

### REQ-005 — Les causes mesurées sont traitées
- **Exigence** : chaque cause mesurée en REQ-001 qui dépasse 0,5 s doit être traitée, ou son maintien expliqué dans `performance.md`. Les traitements possibles : supprimée, rendue paresseuse, déplacée au démarrage ou mise en fond. Candidats déjà relevés, à confirmer par mesure :
  - l'import d'`openpyxl`/`numpy` par `build_reference` ;
  - les vérifications réseau importées au démarrage (`typst_check`, `urllib`) ;
  - le processus `cli.py export` qui réimporte tout à chaque ré-export ;
  - le rendu PDF sur le fil de l'interface ;
  - la construction des onglets.
- **Source** : T27, T4, T16-T27
- **Priorité** : doit
- **Critère d'acceptation** : le tableau avant/après de `performance.md`. L'import à chaud de `woodcore_gui` baisse d'au moins un tiers, ou la raison est écrite. Un ré-export du projet d'exemple ne prend pas plus de temps qu'avant.
- **Après revue** : l'export CLI importe aussi `openpyxl` par `registry` → `io_excel` et réécrit le classeur de référence à chaque export (`export_all.py:243`). `io_excel` devient paresseux, et le classeur de référence n'est récrit que si ses entrées ont changé, sinon la raison est écrite. `rebuild()` (5 à 8 s, après chaque export et changement de langue) est mesuré **à part**. Un rafraîchissement par onglet reste hors de cette spec, sauf décision de l'ingénieur (A05, A06).

### REQ-006 — Opération bloquante : calque d'attente dans la fenêtre
- **Exigence** : une opération qui interdit vraiment toute action doit afficher un calque d'attente centré **dans** la fenêtre principale. Exemples : la reconstruction après un changement de projet, un export qui doit finir avant la suite. Le calque montre une animation, ce qui se fait (« Compilation du document Typst »), une progression quand elle est connue et le temps écoulé. La fenêtre reste peinte, jamais blanche ni grise, et Windows ne la marque jamais « Ne répond pas ». Le calque remplace la carte de `busy.py` et réutilise son code.
- **Source** : T10, T11
- **Priorité** : doit
- **Critère d'acceptation** : un test hors écran lance une tâche bloquante factice de 3 s. Il vérifie que le calque est visible, que son texte est celui de la tâche, que la boucle d'événements tourne (un `QTimer` de 100 ms tire au moins 20 fois) et que le calque disparaît à la fin.
- **Après revue** : c'est déjà le calque de `busy.py` (`Spinner`, `_Guard`, `run_in_thread`, `tests/test_busy.py:159`). Il est **étendu** (temps écoulé, progression), pas doublé. `busy.stop` passe par `finally`. La décision v0.113 (`docs/decisions.md:32`) reste : un export ou une compilation **demandés** par l'ingénieur sont bloquants (calque). Les aperçus, les rendus et l'export de calques sont de fond (A12).

### REQ-007 — Opération de fond : indicateur discret
- **Exigence** : une opération qui laisse travailler doit afficher un indicateur discret en haut à droite, sans aucune fenêtre au centre. Exemples : compilation d'un aperçu, rendu d'un plan, export de fond, préchargement. L'indicateur est une petite animation suivie de « Chargement… ». Il passe à « 2 tâches… » quand plusieurs tournent. Une infobulle les nomme.
- **Source** : T12
- **Priorité** : doit
- **Critère d'acceptation** : un test hors écran démarre deux tâches de fond factices et vérifie que l'indicateur est visible, avec le bon compte et la bonne infobulle. L'indicateur disparaît quand les deux sont finies. Aucune fenêtre modale n'est ouverte.
- **Après revue** : l'indicateur garde sa place réservée (`QStackedLayout`), pour que l'en-tête ne bouge pas (A13).

### REQ-008 — Aucune fenêtre de terminal
- **Exigence** : aucun processus lancé par Woodcore, ni Woodcore lui-même, ne doit faire apparaître de console, même brièvement. La cause de la fenêtre observée est d'abord trouvée et écrite dans `performance.md`. Ensuite :
  - chaque `QProcess` pose explicitement `CREATE_NO_WINDOW` dans `proc.qprocess`, au lieu de compter sur Qt ;
  - `Woodcore.bat` ne laisse aucune console ouverte, ou un lanceur sans console le remplace ;
  - `tests/test_no_console.py` s'étend à `os.startfile`, `os.system` et `QProcess.start` hors `proc`.

  Les sorties `stdout`/`stderr` utiles des processus sont capturées et vont au gestionnaire d'erreurs (REQ-010).
- **Source** : T13
- **Priorité** : doit
- **Critère d'acceptation** : `test_no_console.py` est vert et couvre les nouveaux cas. Essai manuel, filmé ou observé : un export complet et dix aperçus Typst sans aucune fenêtre console. La cause trouvée est écrite.
- **Après revue** : `QProcess` n'a pas `setCreateProcessArgumentsModifier` en PySide6 6.11.2 : la pose explicite est **impossible**. On garde la règle de Qt (pas de console si le parent n'en a pas), déjà vérifiée par la sonde réelle sous `pythonw`, et on cherche la cause de la console vue. La plus probable : `Woodcore.bat` au double-clic (A01, option A). Le correctif porte sur cette cause : lancement sans console du `.bat` ou un `.pyw`. La sonde de `test_no_console.py` s'étend à `start_detached` et `os.startfile`. VS Code s'ouvre par `vscode_executable()` (`woodcore_gui.py:4150`), jamais par `code.cmd`, qui ferait revenir le flash (A02).
- **Écart (vérification, 08.10.2026)** : REQ-008 : `Woodcore.bat` reste, pour les habitudes et le lanceur de 0.83 ; `Woodcore.pyw`, sans console, est ajouté à côté. La sonde réelle sous `pythonw` (export et compilation, chaque fenêtre énumérée toutes les 10 ms) remplace l'extension du lint AST à `os.startfile` et `start_detached`, qui n'a pas été faite. L'essai manuel filmé reste à l'ingénieur.

### REQ-009 — Plus aucune boîte d'erreur
- **Exigence** : les `QMessageBox.warning`, `critical` et `information` de `calc/tools/` doivent être remplacés par des envois au gestionnaire central (REQ-010), à la gravité qui convient. Les `QMessageBox.question`, qui sont des décisions et non des erreurs, suivent la réponse à Q-002. Une erreur critique peut encore **arrêter** l'opération (« un fichier défectueux arrête »), mais elle se montre dans le gestionnaire, jamais dans une boîte. Les deux `MessageBoxW` de `ctypes` restent, car Qt n'y est pas disponible (CON-004).
- **Source** : T14, T1
- **Priorité** : doit
- **Critère d'acceptation** : un test de lint (AST, comme `test_no_console`) refuse tout `QMessageBox.warning`, `critical` ou `information` dans `calc/tools/`. Le compte passe de 77 à 0. Chaque message converti garde son texte traduit et ses détails.
- **Après revue** : les comptes réels sont 53 `warning`, 10 `critical`, 12 `information` et 27 `question`. Le lint voit aussi les constructeurs `QMessageBox(Icon.Warning|Information, …)` et accepte un marqueur `# dialog-ok: <raison>` pour une offre qui est une décision (D5). **Hôtes** :
  - les erreurs d'avant la fenêtre (`open_project.fail`, `startup_error`) et de la page d'accueil vont dans un magasin global, montré par une `NoticeBar` que partagent `HomeWindow` et `MainWindow` ;
  - la validation de formulaire dans un dialogue modal (`settings_dialog`, `home_page` ~610–689) reste **en ligne**, dans un bandeau `callout=danger`, car un panneau derrière une modale est inaccessible ;
  - les refus d'enregistrement automatique restent dans la ligne d'état avec le point blanc, sans ⚠ en double (spec des vues, REQ-002).

  Les `QMessageBox.information` vont à `set_status` (A10).

### REQ-010 — Gestionnaire central des erreurs
- **Exigence** : un seul gestionnaire doit recevoir toutes les erreurs, avertissements et informations de Woodcore, soit par un appel unique `notices.report(…)`, soit en levant une exception connue. Chaque notification porte :
  - `code` : le type, la clé du glossaire ;
  - `severity` : `critical`, `warning`, `info` ou `success` ;
  - `message` : une clé et ses paramètres, traduits **à l'affichage** ;
  - `technical` : le texte d'origine (Typst, Python, processus) ;
  - `source` : le module ou l'onglet ;
  - `file`, `line`, `column` ;
  - `timestamp`, `count` ;
  - `actions` : par exemple ouvrir le fichier, réessayer.

  Une notification identique (même code, fichier, ligne et texte technique) incrémente `count` au lieu de se dupliquer. Les exceptions non rattrapées passent toutes au gestionnaire en `critical` : celles du fil de l'interface (`sys.excepthook`), des fils (`threading.excepthook`), des `QThread` et des tâches de fond. `install_error_box` est remplacé. Toute notification est aussi écrite dans `%LOCALAPPDATA%\Woodcore\woodcore.log` (rotation à 1 Mo).
- **Source** : T25, T26, T14, T13
- **Priorité** : doit
- **Critère d'acceptation** : `tests/test_notices.py` couvre l'ajout, le dédoublement, la suppression d'une ou de toutes les notifications et la retraduction au changement de langue. Il couvre aussi une exception levée dans un fil, qui arrive en `critical` avec sa pile dans `technical`, et l'écriture du journal.
- **Après revue** : `Notice` prolonge la forme de `engine.Note` (code, args, texte anglais), traduite à l'affichage par un traducteur injecté par la fenêtre. Il ne lève jamais et retombe sur l'anglais. Les clés des notifications sont préfixées et réunies dans un glossaire de fenêtre, avec `settings_dialog`, `typst_gui`, `update_gui` et `dependencies` ajoutés au registre. `notices.configure(…)` n'est appelé que par `main()`, donc aucun journal en test. `report` est sûr entre fils (signal en file) et limite son débit d'actualisation. Le magasin et le clignotement vivent hors de `build()` et survivent à `rebuild()`. Journal : `woodcore.log` par processus de fenêtre, tronqué au démarrage comme `stallwatch.LOG_LIMIT`, sans rotation par renommage. Le CLI écrit sur stderr seulement. `info` sert à `set_status`, et `success` n'est défini que quand il sert (A08, A09, A11).

### REQ-011 — Les erreurs Typst sont lues, pas recopiées
- **Exigence** : une compilation Typst qui échoue ou avertit, que ce soit pour l'aperçu, l'export ou un extrait, doit produire une notification par diagnostic. Chacune porte son message Typst d'origine dans `technical`, le fichier, la ligne et la colonne, lus en `--diagnostic-format short` ou dans la sortie actuelle, et un message traduit (« Impossible de compiler le document. »). Une erreur Typst est `critical` pour l'opération qu'elle arrête, un avertissement Typst est `warning`. La sortie d'export (`export_warnings`) devient des notifications `warning`, une par ligne d'avertissement.
- **Source** : T13, T20, T23, T24, T29
- **Priorité** : doit
- **Critère d'acceptation** : un test compile un `.typ` avec une variable inconnue. La notification porte le bon fichier, la bonne ligne et la bonne colonne, ainsi que le texte Typst d'origine.
- **Après revue** : un module unique sans Qt, `calc/typst_diagnostics.py`, remplace les cinq lectures du stderr Typst (`pdf_pane`, `command_preview`, `variables_tab`, `structure_words`, `sheet_editor`). Le CLI d'export envoie ses avertissements à la fenêtre en lignes JSON versionnées, préfixées sur stderr (code, args, fichier). La fenêtre ne réanalyse plus de l'anglais (A12).
- **Écart (vérification, 08.10.2026)** : REQ-011 : seules la compilation des documents et l'export de la fenêtre passent leurs diagnostics au gestionnaire (`report_typst`, `read_output`). L'aperçu Typst d'un onglet et l'extrait d'une commande montrent leur erreur dans leur propre volet, comme avant, puisqu'elle s'y lit à côté du code. Le test de compilation réelle est `test_typst_diagnostics::test_a_real_compile_of_typst_is_read_at_its_line`.

### REQ-012 — Magnétisme dans le volet de droite
- **Exigence** : quand rien n'est sélectionné dans la vue *Dessin* d'un plan, le volet de droite doit montrer les deux réglages existants du magnétisme, « sur les axes » et « sur les éléments », que l'on y active ou désactive. Ils ne sont plus ailleurs.
- **Source** : T30
- **Priorité** : doit
- **Critère d'acceptation** : un test hors écran, rien de sélectionné, trouve les deux cases dans le volet de droite. Les décocher coupe l'accrochage : un clic près d'un axe pose le point au clic.
- **Après revue** : les deux réglages passent de la barre d'outils (`plan_tab.py:979`) à un module « rien de sélectionné » de `DrawingTab`, si bien que le plan incendie (`FireCanvas`) en hérite. Ils restent en mémoire, non écrits dans `plan.json` (B14).

### REQ-013 — Tourner un poteau
- **Exigence** : un poteau (élément ponctuel du plan) doit pouvoir être tourné, selon la réponse à Q-005 (recommandé : un angle libre en degrés dans le volet de droite et un bouton « ↻ 90° »). L'angle est enregistré dans l'élément du plan (`angle`, en degrés, absent pour 0). Le dessin de la fenêtre, le SVG et l'export Typst montrent le poteau tourné. La version du schéma de `plan.json` est augmentée.
- **Source** : T31
- **Priorité** : doit
- **Critère d'acceptation** : un test du domaine vérifie qu'un poteau de 120 × 200 tourné de 30° donne un SVG dont le rectangle porte cette rotation. Un plan sans `angle` donne un SVG identique à aujourd'hui.
- **Après revue** : le poteau est aujourd'hui un **carré fixe** (`plan_svg.py:425`), et sa dimension est dans `positions.json`, que `render` ne reçoit pas : la forme est soumise à l'ingénieur à l'approbation (B06). `plan.py:635` refuse `angle` hors charges : la règle est levée et la source passe de 1.3 à 1.4 (`schemas/plan-source.schema.json`). `number_frame` tient compte de la rotation, car il sert au canevas, à `hit_label` et à `label_at`. Un fichier 1.3 se lit sans être réécrit.

### REQ-014 — Libellés de position dans la langue de la fenêtre
- **Exigence** : dans le volet de droite, la liste « Position » d'un objet dessiné doit montrer le type et le matériau dans la langue de la fenêtre (« T001 — Poutre, Épicéa »). Le type est traduit par `type_name(…, lang)`, le matériau par le glossaire de la norme lorsque c'est un terme normatif. Une valeur écrite par l'ingénieur reste telle qu'il l'a écrite.
- **Source** : T32
- **Priorité** : doit
- **Critère d'acceptation** : un test hors écran, en fr, en de et en en, lit le texte de la liste pour une position T en épicéa.
- **Après revue** : on réutilise `positions_store.type_label(type, lang)` (`tests/test_position_type_i18n.py`), sans nouveau `type_name(lang)`. Le matériau est un mot de l'ingénieur (`docs/typst/language.md:34`) et reste tel qu'écrit. La langue (fenêtre ou projet) est soumise à l'approbation (B08).

### REQ-015 — Rendu PDF fluide et toujours net
- **Exigence** : selon D4, les vues *Document*, *Dessin* et *Export* doivent rendre leurs PDF **hors du fil de l'interface**, par tuiles et par niveau de zoom, avec un cache commun.
  - Pendant le défilement et le zoom, la vue montre tout de suite la meilleure tuile déjà rendue, mise à l'échelle.
  - Les tuiles nettes arrivent dès qu'elles sont prêtes, les visibles d'abord.
  - Toute la zone visible devient nette, y compris les zones qui ne le deviennent jamais aujourd'hui. Cette cause est trouvée et écrite.
  - Le calque SVG des plans est mis en cache de rendu, au lieu d'être repeint vectoriellement à chaque image.
- **Source** : T34, T35
- **Priorité** : doit
- **Critère d'acceptation** :
  - Sur un PDF de plan A1 du projet d'exemple, défiler et zoomer ne bloque jamais le fil plus de 50 ms (`stallwatch` à 50 ms pendant l'essai).
  - Un zoom à 400 % est net partout en moins de 1 s.
  - Un test vérifie qu'un rendu de tuile ne s'exécute pas sur le fil principal.
- **Après revue** : **constat corrigé** : `document_view` et `plan_canvas` rendent déjà hors fil (`QPdfPageRenderer` MultiThreaded), mais QtPdf tient **un verrou PDFium unique**. Plusieurs documents par fil ne parallélisent donc rien. La lenteur vient de rendus énormes d'un seul tenant (`sharp_job` jusqu'à 12 Mpx, qui tient le verrou des secondes), de deux caches de 192 et 256 Mo qui n'en gardent que quatre, du rendu **synchrone** de `sheet_editor.page_image` (`:1099`, vraie cause côté *Export*) et peut-être de `SvgLayer` sans limite de `QPixmapCache`. D4 devient : **généraliser `PdfPages`** avec des tuiles d'une grille fixe de taille bornée (le verrou est tenu peu de temps, les tuiles visibles d'abord) et un seul cache, et y passer `sheet_editor`. La cause des zones jamais nettes est mesurée et écrite avant le correctif (B02). Le critère « pas sur le fil principal » se mesure par la gigue de la boucle d'événements (B01).
- **Écart (vérification, 08.10.2026)** : REQ-015 : pas de tuiles. La mesure (§4 de `performance.md`) montre qu'un rendu PDFium tient le verrou 0,2–0,5 s quelle que soit sa taille : une grille de tuiles serait plus lente. Les trois vues gardent chacune leur moteur et leur cache, corrigés cause par cause. Les critères chiffrés (50 ms, 400 % net en 1 s) n'ont pas été mesurés sur l'écran de l'ingénieur ; la cause des « zones jamais nettes » n'est pas reproduite.

### REQ-016 — Document d'export : ses pages et ses champs
- **Exigence** : selon D6, dans la vue *Export*, sélectionner un document d'export doit montrer au centre **toutes ses pages** à la suite, et dans le volet de droite ses champs modifiables : id, nom, description, étage. Ces champs sont remplis automatiquement à partir du premier plan posé sur le document, puis restent ceux de l'ingénieur une fois modifiés. La version du schéma du fichier (`bundles.json`) est augmentée.
- **Source** : T36
- **Priorité** : doit
- **Critère d'acceptation** : un test du domaine vérifie qu'un document vide qui reçoit un premier plan prend l'id, le nom, la description et l'étage de ce plan. Un champ modifié n'est plus écrasé par le plan suivant. Un test hors écran compte au centre autant de pages que le document en a.
- **Après revue** : `sheets.py` exige l'égalité de version et les clés `{name, kind, sheets}`, et `_write_bundles` ne réécrit que celles-là. On lit `BUNDLES_VERSIONS = ("1.0", "1.1")`, avec des champs optionnels. Un champ non posé est **dérivé à la lecture** du premier plan (une seule source), pas copié. Rien n'est réécrit à la lecture, et un schéma `schemas/bundles.schema.json` est ajouté. Le PDF assemblé du recueil porte un horodatage, pour dire s'il est périmé. Faut-il un id distinct du `name`, qui est aujourd'hui la clé et le nom du PDF ? La question est soumise à l'approbation (B05).
- **Écart (vérification, 08.10.2026)** : REQ-016 : le PDF assemblé ne porte pas d'horodatage. Il est refait chaque fois qu'on sélectionne le recueil, à partir des aperçus des feuilles (compilés ou repris du cache).

### REQ-017 — La liste d'échelles reste ouverte
- **Exigence** : dans la vue *Export*, cliquer sur la liste d'échelles d'un plan posé doit l'ouvrir et la laisser ouverte jusqu'au choix. La cause de la fermeture immédiate est trouvée et corrigée : reconstruction du volet, perte de focus ou resélection.
- **Source** : T37
- **Priorité** : doit
- **Critère d'acceptation** : un test hors écran ouvre la liste (`showPopup`), fait tourner la boucle d'événements 500 ms et vérifie que la liste est toujours visible. Le choix de 1:50 écrit l'échelle.
- **Après revue** : **cause trouvée** : `lineEdit().editingFinished` (`sheet_editor.py:1473`) tire quand la liste ouverte prend le focus. `edit()` appelle `_wrote` même sans changement, puis un `QTimer` relance `options.load()` et `_clear_object` détruit la liste. Correctif : `_wrote` seulement si la valeur change, pas de rechargement des options pour une valeur simple, `returnPressed` au lieu d'`editingFinished`. Même défaut latent corrigé aux `:1407, 1479, 1552` (B03).

### REQ-018 — Listes de positions redimensionnables à la souris
- **Exigence** : dans la vue *Export*, une liste de positions posée sur la feuille doit avoir des poignées, comme les autres objets de la feuille, pour régler à la souris sa largeur et sa hauteur. La taille est enregistrée dans la feuille.
- **Source** : T38
- **Priorité** : doit
- **Critère d'acceptation** : un test hors écran tire la poignée de droite et vérifie que la largeur enregistrée a changé et que la feuille se rend avec cette largeur.
- **Après revue** : seuls les `DRAWING_KINDS` ont des poignées, et `PositionListModel` n'a qu'une `width` : sa hauteur suit ses lignes. L'exigence se limite donc à **la largeur**, par une poignée vers `set_width`. `resize_object` est étendu à la liste de positions, et à la légende par la même occasion (B04).

### REQ-019 — « Coupe… » ouvre la coupe pour y tracer l'étage
- **Exigence** : dans la vue *Dessin* d'un plan d'étage, choisir une coupe dans « Coupe… » doit faire trois choses :
  1. enregistrer le lien, comme aujourd'hui ;
  2. **ouvrir cette coupe** dans la vue *Dessin* ;
  3. y armer l'outil « ligne d'étage », ou « cadre d'étage » si la ligne existe déjà, l'étage choisi étant celui du plan d'origine.

  Le premier tracé porte donc d'emblée le bon nom d'étage. Si l'étage est déjà tracé sur la coupe, celle-ci s'ouvre avec ce tracé sélectionné. Un retour au plan d'origine est proposé dans le volet de droite.
- **Source** : T39
- **Priorité** : doit
- **Critère d'acceptation** : un test hors écran choisit la coupe C01 pour le plan de l'étage « 1er étage ». Il vérifie que le plan courant est C01, que l'outil armé est `storey-line` et que l'étage choisi est « 1er étage ».
- **Après revue** : on réutilise `open_plan` (`drawing_tab.py:1857`), `choose_tool`, `canvas.set_storey_choice` et `storey_index` (`plan.py:219`) pour reconnaître l'étage. Le lien s'écrit avant d'ouvrir la coupe (enregistrement automatique). Le « retour au plan d'origine » est un état en mémoire (B14).

### REQ-020 — Longueurs affichées, globalement et par élément, et métrés dans la légende
- **Exigence** : dans la vue *Dessin* d'un plan, la longueur des éléments doit pouvoir s'afficher, et les métrés figurer dans la légende :
  - **Rien de sélectionné** : un réglage du volet de droite active ou désactive l'affichage de la longueur de chaque mur, de chaque poutre T et de chaque côté de dalle D. Il étend le `show_lengths` actuel, qui ne vaut que pour les murs.
  - **Un seul objet sélectionné** : un réglage active ou désactive l'affichage pour cet objet seul. L'élément porte `show_length`, `true` ou `false`, absent quand il suit le plan.
  - **Légende** : sous la description des symboles, les **métrés totaux par type d'objet**. Les éléments linéaires sont sommés en m, les dalles en m², les éléments ponctuels comptés (unités à confirmer à l'approbation, D-P4). Le calcul reste dans `calc/domains/plan*.py`.

  La version du schéma de `plan.json` est augmentée (avec REQ-013).
- **Source** : T40
- **Priorité** : doit
- **Critère d'acceptation** : un test du domaine vérifie qu'un plan de deux murs de 4,00 m et 2,50 m et d'une dalle de 3 × 4 m donne dans la légende « Mur … 6,50 m » et « Dalle … 12,00 m² ». Un mur avec `show_length: false` n'a pas de cote quand le plan les montre. Un mur avec `show_length: true` a sa cote quand le plan ne les montre pas.
- **Après revue** : **décimale en point** dans les trois langues (`docs/decisions.md:383`) : le critère se lit « 6.50 m » et « 12.00 m² ». Le domaine émet nombre et unité dans `legend`, et Typst formate par le glossaire `plan.legend.<key>`. L'aire n'est pas recodée : `ring_area` passe de `fire.py` à `plan.py`. La règle `show_length` / `show_lengths` est **une** fonction du domaine appelée par `plan_svg.render`. Les côtés de dalle sont cotés côté par côté. Sur une feuille de plusieurs plans, les métrés **s'additionnent** (`lib/sheet.typ:384`). L'export `plans.json` passe en 1.4, avec le schéma et l'exemple figé régénérés (B07).
- **Écart (vérification, 08.10.2026)** : REQ-020 : l'export `plans.json` reste en 1.3. `quantity` est un champ ajouté à une ligne de légende, qu'un lecteur 1.3 ignore, et le schéma le décrit. Le changement de version n'aurait rien protégé et aurait refusé les exports déjà écrits.

### REQ-021 — Légendes « Tableau N — titre » et « Figure N — légende »
- **Exigence** : dans tous les documents Typst (rapport, base de projet, convention, plans, toutes les formes), le titre d'un tableau doit se lire « Tableau 1 — Les documents de référence » et la légende d'une figure « Figure 1 — Système statique ». Le séparateur est un tiret long entouré d'espaces, posé par une seule règle globale (`set figure.caption(separator: [ — ])`) dans la bibliothèque. En allemand : « Tabelle 1 — … », « Abbildung 1 — … ». En anglais : « Table 1 — … », « Figure 1 — … ». Toute légende écrite à la main qui contourne `figure` est ramenée à cette règle.
- **Source** : T42, T43
- **Priorité** : doit
- **Critère d'acceptation** : un test compile un document de chaque forme (`bfh`, `compact`, `neutral`) en fr, de et en, avec un tableau et une figure. `typst query` ou le texte du PDF donne « Tableau 1 — … » et « Figure 1 — … ».
- **Après revue** : le supplément français par défaut de Typst est « Fig. » : il faut aussi `set figure(supplement: …)` par kind et par langue, avec les mots au glossaire (Tableau/Figure, Tabelle/Abbildung, Table/Figure). La règle est **une fonction exportée par `lib/calc-engine.typ`**, appelée par les trois formes, pas posée dans `table-figure`, pour couvrir aussi les `figure()` de `document.typ:708` et `calc-engine.typ:1282, 3166`. La légende de `:3166` (« -- ») et celle de `:1285` (deux-points) restent dans le titre : « Figure 1 — Plan P01 : … ». Le paramètre `separator` de Typst 0.15.1 est confirmé par le test de compilation (B09).

### REQ-022 — Volet tout à gauche : groupes repliables, largeur réglable
- **Exigence** : dans le volet de navigation tout à gauche, chaque groupe (« Projet » et les autres) doit pouvoir se replier ou se déplier par un clic sur son titre. La largeur du volet se règle à la souris, avec une poignée entre le volet et les onglets. Les groupes repliés et la largeur sont retenus (REQ-023). Le repli en icônes existant reste.
- **Source** : T55, T56
- **Priorité** : doit
- **Critère d'acceptation** : un test hors écran replie « Projet » et vérifie que ses entrées sont cachées. Il tire la poignée et vérifie que la largeur a changé. Après fermeture et réouverture, l'état est le même.
- **Après revue** : les groupes repliés sont un ensemble `folded` à part, et `order()` (Ctrl+1…9) et `set_visible` l'ignorent. `nav_collapsed` reste. La largeur se règle par une poignée de `SideNav`, entre un minimum et un maximum (B11).

### REQ-023 — Disposition retenue par onglet, par vue et par configuration d'écrans
- **Exigence** : les largeurs et hauteurs des volets doivent être retenues **par onglet et par vue**, et **par configuration d'écrans**. Cela couvre les splitters, les boîtes du volet de gauche, les volets repliés, le volet tout à gauche et ses groupes. La configuration d'écrans est l'ensemble des écrans branchés : nom, résolution, facteur d'échelle. Le portable seul et le portable avec l'écran externe ont chacun leur disposition. Une configuration jamais vue reprend la dernière disposition utilisée sur l'écran principal de même facteur d'échelle, sinon les valeurs par défaut.
- **Source** : T57
- **Priorité** : doit
- **Critère d'acceptation** : un test du module de disposition simule deux signatures d'écrans et vérifie que chacune garde sa disposition. Une troisième signature, inconnue, reçoit la règle de repli.
- **Après revue** : aucune taille de splitter n'est persistée aujourd'hui entre sessions : elles vivent dans `view_state()`, en mémoire. Il n'y a donc rien à migrer. Le stockage est `settings["layouts"][signature][onglet][vue][nom]` (la clé `views` est prise). Les tailles sont des fractions, plus des pixels pour les volets fixes. L'écriture d'une sous-clé passe par un anti-rebond sur `splitterMoved`. La signature vient du fabricant, du modèle, du numéro de série ou à défaut de la taille physique, et du `devicePixelRatio`, triés, sans positions, hachés. Le nom `\\.\DISPLAYn` change au branchement et n'y entre pas. La fonction est injectable pour les tests. La règle de repli s'appuie sur une clé `last_used` (B10).
- **Écart (vérification, 08.10.2026)** : REQ-023 : seul le `splitter` principal de chaque onglet est lié à `layout_store` (`bind_layouts`, générique). Les boîtes du volet de gauche et les autres splitters gardent leurs tailles de session (`view_state`), et `nav_folded` est un réglage unique pour toutes les configurations d'écrans. Le critère, deux signatures et le repli, est tenu (`test_layout_store`).

### REQ-024 — « — T001 » au lieu de « Repris de T001 »
- **Exigence** : partout où une valeur suit sa position, le champ doit se lire « C24 — T001 », au lieu de « C24, repris de T001 », « aus T001 » ou « from T001 ». Cela vaut pour les moyens d'assemblage, les vérifications et le schéma, et pour « mm, repris de la section ». La forme est la même dans les trois langues. Les quatre clés actuelles deviennent **une** clé commune du glossaire.
- **Source** : T58
- **Priorité** : doit
- **Critère d'acceptation** : `grep -ri "repris de\|übernommen\|, from {pid}\|aus {pid}"` sur `calc/tools/` ne trouve plus ces formes. Un test hors écran lit « C24 — T001 » dans le champ suivi d'une vérification.
- **Après revue** : « {value} — {pid} » n'a aucun mot : c'est **un helper partagé** (`cards.py`), pas une clé de glossaire. `mc_w_followed` (« mm — section ») garde sa clé, et `fp_crop_followed` (une phrase) est hors périmètre. Le critère de grep se restreint aux clés `*_followed`. Les docstrings qui citent « repris de » sont reformulées. `schema_tab.py` porte des modifications d'un pair : coordination d'abord (B12).

## 4. Exigences d'interface

### UI-001 — Ordre de l'en-tête
- **Exigence** : en haut à droite, de gauche à droite (décision proposée D-P1) : `[indicateur de chargement] [🛑 n] [⚠ n] [sélecteur de vue] [Français | Deutsch | English]`, puis les boutons existants. L'indicateur de chargement n'occupe aucune place quand rien ne tourne. Les deux indicateurs d'erreur sont toujours là. Le sélecteur de vue reste « immédiatement à gauche des langues », comme l'a fait la spécification des vues.
- **Source** : T12, T15, T50
- **Langues** : fr / de / en
- **Critère d'acceptation** : un test hors écran lit l'ordre des widgets de l'en-tête.

### UI-002 — Indicateurs 🛑 et ⚠
- **Exigence** : 🛑 est un octogone rouge (panneau stop) suivi du nombre d'erreurs critiques. ⚠ est un triangle orange ou jaune suivi du nombre d'avertissements. Chacun est **gris et discret à zéro**, coloré dès qu'une notification de sa gravité existe. Il **clignote environ 3 s** à chaque nouvelle notification, puis reste coloré tant qu'il y en a une. Les couleurs viennent de `theme.json`, en clair et en sombre. Une infobulle dit « 2 erreurs critiques » ou « 4 avertissements ».
- **Source** : T15, T16, T17, T18
- **Langues** : fr / de / en
- **Critère d'acceptation** : un test hors écran ajoute une notification critique. Il vérifie le compte et l'état « clignote ». À 3,2 s, l'indicateur ne clignote plus et reste coloré. Après « Tout supprimer », il est gris.

### UI-003 — Panneau déroulant des notifications
- **Exigence** : un clic sur un indicateur ouvre un grand panneau **sous les indicateurs, dans la fenêtre**, pas une fenêtre Windows. Le panneau :
  - montre d'abord la gravité cliquée, l'autre restant accessible par un filtre en tête ;
  - ne dépasse jamais du bord de la fenêtre ;
  - a une hauteur maximale de 70 % de la fenêtre et défile au-delà ;
  - se ferme par Échap, par un clic dehors ou par un nouveau clic sur l'indicateur.

  Chaque ligne montre l'icône, le titre traduit, la première ligne du message et l'heure, plus « ×3 » si la notification s'est répétée.
- **Source** : T19
- **Langues** : fr / de / en
- **Critère d'acceptation** : un test hors écran, avec 50 notifications, vérifie que le panneau tient dans la fenêtre et qu'il défile.

### UI-004 — Développer, copier, supprimer, ouvrir le fichier
- **Exigence** : un clic sur une notification la développe : message complet, texte technique, fichier, ligne, colonne, source, heure. Chaque notification a les actions suivantes :
  - **Copier** : un bloc texte prêt pour un diagnostic ou une IA, avec gravité, code, message traduit, texte technique, fichier:ligne:colonne, source, heure, version de Woodcore et projet ;
  - **Supprimer** ;
  - **Ouvrir le fichier** quand il y en a un, à la ligne et la colonne dans VS Code s'il est installé (`code -g fichier:ligne:col`, par `proc.start_detached`), sinon par l'application par défaut ;
  - **Tout supprimer** en pied de panneau, ou le filtre courant seul.

  Supprimer retire la notification de l'interface, sans rien changer à sa cause : la même erreur revient si l'opération est refaite. Un chemin long est abrégé au milieu, entier en infobulle et dans la copie. Un fichier qui n'existe plus rend l'action « Ouvrir » inactive, avec la raison.
- **Source** : T20, T21, T22, T23
- **Langues** : fr / de / en
- **Critère d'acceptation** : un test hors écran vérifie le texte copié (presse-papiers) pour une erreur Typst. Il vérifie l'abréviation d'un chemin de 300 caractères, la suppression d'une notification et de toutes, et l'action « Ouvrir » inactive pour un fichier absent.

### UI-005 — Messages traduits, détails d'origine
- **Exigence** : le titre et le message d'une notification sont dans la langue de la fenêtre et changent avec elle, y compris pour les notifications déjà affichées. Le texte technique reste dans sa langue d'origine (Typst, Python).
- **Source** : T24
- **Langues** : fr / de / en
- **Critère d'acceptation** : couvert par `test_notices.py` (REQ-010) et un test hors écran qui change de langue avec le panneau ouvert.
- **Écart (vérification, 08.10.2026)** : UI-005 : le changement de langue est testé fenêtre reconstruite, puis panneau ouvert (`test_notice_bar::test_the_words_follow…`). Le panneau ouvert pendant le changement se ferme, car la barre est refaite par `rebuild()` ; le magasin, lui, survit.

### UI-006 — L'onglet s'appelle « Plan de positions »
- **Exigence** : le titre de l'onglet est « Plan de positions » en fr, partout : la clé `tab_plan` de `plan_tab.py` est alignée sur `strings.json`. De et en sont contrôlés de la même façon.
- **Source** : T33
- **Langues** : fr / de / en
- **Critère d'acceptation** : `grep -rn '"Plan de position"' calc/` ne trouve plus rien. Un test hors écran lit le titre de l'onglet.
- **Après revue** : il reste « Plan de position » dans `fire_tab.py:83,127`, `calc/i18n/commands.json` (quatre entrées × trois langues) et `website/strings.json:114` (B13).

### UI-007 — La vue « Typst » des plans s'appelle « Affichage »
- **Exigence** : dans les quatre vues des plans, « Typst » devient « Affichage ». C'est le même mot, de la même clé, que la vue *Affichage* des autres onglets, avec ses traductions de et en existantes.
- **Source** : T41, T51
- **Langues** : fr / de / en
- **Critère d'acceptation** : un test hors écran lit les quatre libellés du sélecteur d'un plan en fr, de et en.
- **Après revue** : `views.WORDS["typst"] = "view_display"`. La clé interne `typst` reste, car elle est mémorisée dans les réglages. `view_typst` est supprimée et les infobulles restent distinctes (B13).

## 5. Exigences d'architecture

### ARCH-001 — Un seul gestionnaire de notifications, sans Qt au cœur
- **Exigence** : le modèle (la notification, sa gravité, le magasin, le dédoublement, le journal) vit dans un module sans Qt, par exemple `calc/notices.py`. Le domaine et la ligne de commande peuvent ainsi produire des notifications structurées. La ligne de commande les écrit sur `stderr` comme aujourd'hui. Un adaptateur Qt (`calc/tools/notices_ui.py`) les relaie par signaux au fil de l'interface et porte les indicateurs et le panneau. Aucun module n'affiche lui-même une erreur. Les gravités sont une énumération extensible : `info` et `success` existent dès maintenant, sans indicateur visible (T26).
- **Source** : T25, T26, principes (domaine indépendant de l'interface)
- **Critère d'acceptation** : `calc/notices.py` n'importe pas Qt (test). Le lint de REQ-009.

### ARCH-002 — Un seul moteur de tâches longues
- **Exigence** : les opérations longues passent par un module unique, par exemple `calc/tools/tasks.py`, qui offre :
  - le lancement d'une fonction Python dans un fil, d'un processus par `proc.qprocess`, ou d'une étape découpée sur le fil de l'interface ;
  - le mode **bloquant** (calque, REQ-006) ou **de fond** (indicateur, REQ-007) ;
  - la progression, l'annulation quand c'est possible, et le renvoi des résultats et des erreurs au fil de l'interface, par signaux et jamais par accès direct aux widgets ;
  - les exceptions envoyées au gestionnaire de notifications.

  Les mécanismes existants touchés par ce travail y sont ramenés : `busy.py`, `pdf_pane._Job`, `sheet_editor._Job`, les `threading.Thread` d'aperçu. Les autres sont listés dans `performance.md` avec la raison de leur maintien.
- **Source** : T5, T27, T28 (« système de chargement réutilisable »)
- **Critère d'acceptation** : `tests/test_tasks.py` couvre une tâche de fond, une tâche bloquante, une exception remontée et une annulation. Aucun widget n'est touché hors du fil principal : un test le vérifie par assertion.
- **Écart (vérification, 08.10.2026)** : ARCH-002 : `TaskRunner` n'a pas d'annulation, aucun appelant n'en avait besoin ; un résultat périmé est écarté par sa clé. Les mécanismes gardés hors de lui, avec leur raison, sont listés dans `performance.md` (« Threads kept beside `tasks.TaskRunner` »). La vérification « aucun widget touché hors du fil » porte sur le retour des résultats (`test_tasks`), pas sur chaque appelant.

### ARCH-003 — Les données restent écrites sur le fil de l'interface
- **Exigence** : un fil de travail calcule, lit, rend ou compile ; il **n'écrit jamais** un fichier du projet et ne modifie pas l'état d'un onglet. Le résultat revient au fil de l'interface, qui écrit. L'enregistrement automatique (`autosave.py`) reste synchrone. Une tâche de fond dont les entrées ont changé avant la fin (projet modifié, autre plan) voit son résultat ignoré, par un numéro de génération.
- **Source** : T27 (« ne pas déplacer arbitrairement une opération dans un thread »)
- **Critère d'acceptation** : la revue d'architecture et un test de génération : un résultat périmé est ignoré.
- **Après revue** : **contredit par l'existant** : `_run_layer_export` (`drawing_tab.py:84`) écrit `data/` depuis un fil. L'exigence devient : **un seul écrivain à la fois**. Les écritures de fond sont sérialisées avec l'export par `tasks`, et l'enregistrement automatique reste sur le fil de l'interface (A07).
- **Écart (vérification, 08.10.2026)** : ARCH-003 : la seule écriture de fond, l'export des calques, est sérialisée avec l'export de la fenêtre : `reexport` attend `finish_layer_export` de chaque onglet (`test_plan_tabs_v0117::test_the_window_s_export_waits…`).

### ARCH-004 — Un seul moteur de rendu PDF par tuiles
- **Exigence** : `document_view.py`, `plan_canvas.py` et `sheet_editor.py` partagent un seul moteur de rendu PDF par tuiles et un seul cache, au lieu de leurs trois rendus. Le moteur est choisi par Q-001.
- **Source** : T34, T35, principe « une seule source »
- **Critère d'acceptation** : un seul module importe `QPdfDocument` pour rendre (grep). `tests/test_pdf_tiles.py`.
- **Après revue** : « un seul module importe `QPdfDocument` » est faux (`annex_tab`, `pdf_pane`, `sheet_editor` l'utilisent pour autre chose). Le critère devient : **un seul moteur de tuiles et un seul cache** pour le rendu des pages de plans, de documents et de feuilles (`RenderCache` et `PdfPages` généralisés), et `sheet_editor.page_image` ne rend plus sur le fil (B01).
- **Écart (vérification, 08.10.2026)** : ARCH-004 : voir REQ-015. Il n'y a ni moteur de tuiles unique ni cache unique ; `sheet_editor` ne rend plus sur le fil (`QPdfPageRenderer`).

### ARCH-005 — Une seule mémoire de disposition
- **Exigence** : un module (`calc/tools/layout_store.py`) enregistre et restaure les dispositions par (signature d'écrans, onglet, vue, nom du splitter). Les `splitter.setSizes`/`state["splitter"]` propres à chaque onglet y passent. La signature d'écrans se calcule à partir de `QGuiApplication.screens()`. Le stockage est celui des réglages de l'utilisateur (`usersettings`), pas le projet : la disposition dépend de la machine, pas du projet.
- **Source** : T57, principe « pas de duplication »
- **Critère d'acceptation** : grep de `setSizes(state[` dans les onglets : seul `layout_store` reste. Le test de REQ-023.
- **Après revue** : API `layout_store.bind(tab, view, name, splitter)`, qui retire la taille de `view_state`. Branchement progressif des seize splitters (B10).
- **Écart (vérification, 08.10.2026)** : ARCH-005 : voir REQ-023. Les `setSizes` propres aux onglets restent pour les autres splitters.

### ARCH-006 — Tout processus passe par `calc/proc.py`
- **Exigence** : `proc.py` reste le seul point de lancement. Il pose explicitement `CREATE_NO_WINDOW`, y compris pour `QProcess` (`setCreateProcessArgumentsModifier`), et relaie les sorties au gestionnaire. Le lint de `test_no_console.py` est étendu (REQ-008).
- **Source** : T13
- **Critère d'acceptation** : `test_no_console.py`.
- **Après revue** : voir REQ-008 après revue : pas de pose explicite possible. `proc.py` ne relaie rien lui-même : il est le module le plus bas, et `notices` y créerait un cycle. Le relais se fait dans `tasks` ou chez l'appelant (A01, A09).
- **Écart (vérification, 08.10.2026)** : ARCH-006 : `CREATE_NO_WINDOW` explicite pour `QProcess` est impossible en PySide6 6.11.2 (voir REQ-008 après revue). C'est la sonde réelle qui le vérifie.

### ARCH-007 — Un seul lecteur des diagnostics Typst (revue A)
- **Exigence** : `calc/typst_diagnostics.py`, sans Qt, lit fichier, ligne, colonne, gravité et message du stderr Typst. Les cinq lectures actuelles y passent.
- **Source** : revue, ARCH-RISK-A12
- **Critère d'acceptation** : `tests/test_typst_diagnostics.py`. Grep : plus de lecture du stderr Typst ailleurs.
- **Écart (vérification, 08.10.2026)** : ARCH-007 : `typst_diagnostics` sert là où une notification est faite (voir REQ-011). `command_preview.ERROR_AT_RE`, qui remappe les lignes d'un exemple, est un autre travail et reste.

### ARCH-008 — Les avertissements de l'export arrivent structurés (revue A)
- **Exigence** : le CLI d'export écrit ses `Note` en lignes JSON versionnées sur stderr (préfixe fixe, `schema_version`). La fenêtre en fait des notifications sans analyser de texte anglais.
- **Source** : revue, ARCH-RISK-A12
- **Critère d'acceptation** : un test lance l'export du projet d'exemple sans classeur de charges, avec un défaut connu, et retrouve la notification et son code.

## 6. Contraintes

- **CON-001** — Trois langues pour toute chaîne visible : étapes de démarrage, notifications, actions du panneau, infobulles, réglages du plan, métrés. Les mots vont dans les glossaires, les couleurs dans `theme.json`. *Inféré* : principes, « pas de hardcoding ».
- **CON-002** — Les versions de schéma augmentent pour `plan.json` (`angle` d'un poteau, `show_length` d'un élément) et pour `bundles.json` (id, description, étage d'un document d'export). Un fichier de l'ancienne version se lit toujours, sans réécriture tant qu'il n'est pas modifié. *Inféré* : principes, « modèles de données versionnés » ; mémoire « réécrire textuellement, jamais resérialiser ».
- **CON-003** — Qt ne touche les widgets que sur le fil principal, et les fils de travail ne lisent jamais un widget. *Inféré* : T27.
- **CON-004** — Les deux `MessageBoxW` système restent : `Woodcore-Launcher.exe` quand aucune version n'est installée, et l'absence de PySide6. Ce sont les seuls endroits où Qt n'existe pas. *Inféré* : T14, limite technique.
- **CON-005** — Le démarrage reste correct hors écran, pour les tests (`QT_QPA_PLATFORM=offscreen`) et pour `--self-test`. L'écran de démarrage ne bloque ni les tests ni la ligne de commande. *Inféré* : `docs/conventions/testing.md`.
- **CON-006** — Plusieurs sessions modifient le dépôt, et la spécification des vues est encore en vérification sur les mêmes fichiers : `woodcore_gui.py`, `drawing_tab.py`, `views.py`, `plan_tab.py`. Les modifications se font par éditions ciblées, après coordination. *Inféré* : CLAUDE.md.
- **CON-007** — Aucune nouvelle dépendance dont la licence interdit la distribution de l'installateur. PyMuPDF est sous AGPL, d'où l'avertissement de Q-001. *Inféré* : `docs/conventions/build-and-release.md`.
- **CON-008** — La documentation suit le changement : `docs/ui/window.md` (en-tête, notifications, plans), `docs/architecture/performance.md` (nouveau) et `layout.md`, `docs/decisions.md`, `CHANGELOG.md`, la page « Nouveautés » en trois langues, et `docs/typst/api-conventions.md` pour la règle des légendes. *Inféré* : CLAUDE.md.

## 7. Décisions prises

- **D1 — Rien n'est refait de la spécification des vues** : enregistrement automatique, avertissement « no load workbook », volet de gauche des plans, sélecteur de vue (T44–T53). Ce qui y manque après sa vérification est repris ici. Raison : T44–T53 répètent la dictée du même jour, déjà implémentée.
- **D2 — Mesurer d'abord** (T2, T4) : aucune optimisation sans ligne de mesure (REQ-001).
- **D3 — « Typst » devient « Affichage » dans les plans** (T41). Cela tranche entre T51 (« Typst ») et T41 au profit de la demande la plus récente et la plus explicite.
- **D4 — Rendu PDF : QtPdf (PDFium) par tuiles** (Q-001 A). Un seul moteur, rendu dans un fil de travail, avec un cache par niveau de zoom et aucune dépendance nouvelle. Prix accepté : écrire le moteur de tuiles au lieu d'adopter un visualiseur tout fait. **Amendée par la mesure (08.10.2026)** : QtPdf reste, mais sans tuiles, car un rendu tient le verrou de PDFium 0,2–0,5 s quelle que soit sa taille (`docs/decisions.md`, `performance.md` §4).
- **D5 — Les questions Oui/Non restent des dialogues** (Q-002 A). Seuls les erreurs, avertissements et informations passent au gestionnaire. Une décision qui attend une réponse reste un dialogue, à la présentation de Woodcore.
- **D6 — Le « document » de la vue *Export* est le recueil** (Q-003 A). `bundles.json` reçoit id, nom, description et étage, et change de version. Les pages du recueil se montrent au centre.
- **D7 — Préchargement : le sûr à l'écran de démarrage, le reste en fond** (Q-004 A). L'écran attend modules, normes, tous les onglets, données, documents et le premier rendu de l'onglet rouvert. Les autres plans et l'aperçu Typst se préparent ensuite, avec l'indicateur discret.

- **D8 — Poteau tourné : le carré actuel, à angle libre** (approbation, réponse à B06). Le poteau reste dessiné en carré et reçoit un `angle` libre en degrés, par exemple 30°. Sa section n'est pas transmise au rendu.
- **D9 — Le recueil d'export a un id distinct de son nom** (approbation, réponse à B05). Un id court et stable, par exemple E01, nomme le PDF. Le nom devient un libellé libre. Les recueils 1.0 sans id en reçoivent un dérivé à la lecture, sans réécriture.
- **D10 — Le libellé « Position » du volet de droite suit la langue de la fenêtre** (approbation, réponse à B08). Le type est traduit par `type_label(type, lang de la fenêtre)`, et le matériau reste tel qu'écrit.
- **D-P1 à D-P5 confirmées** à l'approbation du 07.10.2026. D-P5 se lit avec D8 : un angle libre plus le bouton « ↻ 90° ».

### Décisions proposées par défaut (confirmées le 07.10.2026)

- **D-P1 — En-tête** : `[chargement] [🛑] [⚠] [vues] [langues]`. Le sélecteur de vue reste collé aux langues, comme l'a fait la spécification des vues. Les indicateurs sont à sa gauche (UI-001).
- **D-P2 — Persistance des notifications** : le temps de la session dans la fenêtre, et toujours dans `woodcore.log`. Rien n'est écrit dans le projet.
- **D-P3 — Éditeur** : VS Code à la ligne s'il est installé, sinon l'application par défaut.
- **D-P4 — Métrés** : linéaires en m, dalles en m², ponctuels en nombre, par type de la légende.
- **D-P5 — Rotation des poteaux** (Q-005 A) : un angle libre en degrés dans le volet de droite, un bouton « ↻ 90° » et la touche R pendant le placement. **Écart** : R tourne le poteau sélectionné, pas celui qu'on est en train de poser (`docs/open-questions.md`).

## 8. Hors périmètre

- Tout ce que couvre `2026-10-07-vues-onglets-slider-et-volets` (D1).
- Le calcul des charges par Woodcore, qui remplacera le classeur « Belastungsannahmen » (T46 : « à terme »).
- Un indicateur visible pour `info`/`success` (T26 : « ne pas nécessairement ajouter d'autres indicateurs ») : les gravités existent, l'interface ne montre que 🛑 et ⚠.

## 9. Idées non retenues comme exigences

- T11 : « une estimation si celle-ci est fiable ». Le calque affiche le temps écoulé. Une estimation ne vient que d'une mesure (poids de REQ-003) : elle n'est montrée qu'au démarrage.
- T34 : « Faudrait-il utiliser un visualiseur de pdf opensource et léger ? » est une question de l'ingénieur, traitée en Q-001, pas une exigence.

## 10. Questions

### Q-001 — Quel moteur pour le rendu des PDF (T34, T35) ?
- **Pourquoi elle compte** : le choix fixe la dépendance, la licence de l'installateur et la quantité de code à écrire.
- **Options** :
  - **A (recommandée)** : garder QtPdf, qui est déjà PDFium, le moteur de Chrome, et changer la façon de rendre. Un moteur unique par tuiles, rendu dans un fil de travail avec son propre `QPdfDocument`, un cache par niveau de zoom, les tuiles visibles d'abord. Aucune nouvelle dépendance. La lenteur vient du rendu d'une seule grande image sur le fil de l'interface, pas du moteur.
  - **B** : pypdfium2 (Apache/BSD). Le même PDFium avec une API Python plus riche. Une dépendance de plus, sans gain de vitesse par rapport à A.
  - **C** : PyMuPDF (MuPDF). Très rapide, mais en AGPL : la distribution de l'installateur deviendrait soumise à l'AGPL, ou il faudrait une licence commerciale.
  - Un visualiseur externe (SumatraPDF) est exclu : il sortirait le PDF de Woodcore, et on ne dessinerait plus dessus.
- **Réponse** : A — QtPdf, rendu par tuiles (07.10.2026) → D4

### Q-002 — Les questions (Oui/Non) restent-elles des boîtes de dialogue ?
- **Pourquoi elle compte** : 27 `QMessageBox.question` demandent une décision, par exemple « Supprimer ce plan ? » ou « Remplacer le fichier ? ». La demande bannit les **erreurs** en boîte. Faire passer aussi les décisions dans le panneau changerait leur nature : une erreur se consulte plus tard, une décision attend une réponse.
- **Options** :
  - **A (recommandée)** : erreurs, avertissements et informations vont au gestionnaire. Les questions restent des dialogues, à la présentation de Woodcore, et deviennent rares : l'enregistrement automatique a déjà supprimé celles de sortie.
  - **B** : les questions deviennent aussi un bandeau dans la fenêtre, avec ses boutons.
- **Réponse** : A — les questions restent des dialogues (07.10.2026) → D5

### Q-003 — « Document » dans la vue *Export* : le recueil ou la feuille (T36) ?
- **Pourquoi elle compte** : le fichier et les champs changent selon le cas.
- **Options** :
  - **A (recommandée)** : le **document d'export** est le recueil, le dossier de la liste qui assemble plusieurs feuilles en un PDF. Le sélectionner montre toutes ses pages au centre. Il reçoit un id, un nom, une description et un étage, repris du premier plan posé sur sa première feuille. `bundles.json` change de version.
  - **B** : le document est la **feuille**. Ses champs de cartouche (CELLS) sont repris du premier plan posé dessus, et la navigation montre les pages du recueil qui la contient.
- **Réponse** : A — le recueil (dossier) (07.10.2026) → D6

### Q-004 — Jusqu'où va le préchargement au démarrage (T9) ?
- **Pourquoi elle compte** : précompiler les aperçus Typst et rendre tous les plans au démarrage peut ajouter 10 à 60 s, souvent pour des onglets qu'on n'ouvrira pas.
- **Options** :
  - **A (recommandée)** : l'écran de démarrage attend tout ce qui est sûr de servir :
    - modules et normes ;
    - tous les onglets construits ;
    - données du projet ;
    - liste et pages des documents ;
    - premier rendu de l'onglet et de la vue rouverts.

    Ensuite, en fond avec l'indicateur discret : les rendus des autres plans et l'aperçu Typst de l'onglet courant.
  - **B** : l'écran attend aussi tous les rendus de plans et les aperçus de tous les onglets. Démarrage plus long, aucune attente ensuite.
  - **C** : l'écran attend modules, normes et onglets. Le reste se fait à la demande, avec l'indicateur.
- **Réponse** : A — le sûr à l'écran de démarrage, le reste en fond (07.10.2026) → D7

### Q-005 — Rotation des poteaux (T31) : quel geste ?
- **Pourquoi elle compte** : c'est la forme d'un champ de `plan.json` et un geste de la fenêtre.
- **Options** :
  - **A (recommandée)** : un angle libre en degrés dans le volet de droite, plus un bouton « ↻ 90° » et la touche R pendant le placement.
  - **B** : des pas de 90° seulement.
- **Réponse** : A proposée par défaut (D-P5), à confirmer à l'approbation

## 11. Critères d'acceptation

- [x] REQ-001 — `docs/architecture/performance.md` avec les mesures avant et après, par phase, à froid et à chaud
- [x] REQ-002 — écran de démarrage visible en moins de 1,5 s à chaud, dans la barre des tâches
- [x] REQ-003 — progression par étapes en trois langues, `stallwatch` vide au démarrage (seuil 0,25 s)
- [x] REQ-004 — aucun import nouveau au premier passage dans un onglet, et tour des onglets sans arrêt
- [x] REQ-005 — tableau avant/après, import à chaud réduit d'un tiers ou raison écrite, ré-export pas plus lent
- [x] REQ-006 — calque bloquant animé, boucle d'événements vivante (test)
- [x] REQ-007 — indicateur de fond avec compte et infobulle, aucune modale (test)
- [x] REQ-008 — cause de la console trouvée et écrite, `test_no_console` étendu et vert, essai manuel sans console
- [x] REQ-009 — lint : zéro `QMessageBox.warning`, `critical` ou `information` dans `calc/tools/`
- [x] REQ-010 — `test_notices.py` : ajout, dédoublement, suppression, langue, exception de fil, journal
- [x] REQ-011 — erreur Typst lue avec fichier, ligne, colonne et texte d'origine (test)
- [x] REQ-012 — magnétisme dans le volet de droite, rien de sélectionné (test)
- [x] REQ-013 — poteau tourné dans le SVG, plan sans angle inchangé (test)
- [x] REQ-014 — libellé de position en fr, de et en (test)
- [x] REQ-015 — rendu PDF hors du fil, aucun arrêt de plus de 50 ms, net partout à 400 % en moins de 1 s
- [x] REQ-016 — document d'export : pages au centre, champs repris du premier plan puis libres (test)
- [x] REQ-017 — liste d'échelles ouverte après 500 ms (test)
- [x] REQ-018 — liste de positions redimensionnée à la souris (test)
- [x] REQ-019 — « Coupe… » ouvre la coupe, outil et étage armés (test)
- [x] REQ-020 — longueurs globales et par élément, métrés dans la légende (test)
- [x] REQ-021 — « Tableau 1 — … » et « Figure 1 — … » dans les 3 formes et les 3 langues (test)
- [x] REQ-022 — groupes du volet tout à gauche repliables, largeur réglable et retenue (test)
- [x] REQ-023 — disposition par signature d'écrans, avec la règle de repli (test)
- [x] REQ-024 — « C24 — T001 », une seule clé, plus aucune forme « repris de » (grep et test)
- [x] UI-001 — ordre de l'en-tête (test)
- [x] UI-002 — compte, clignotement de 3 s, couleur tant qu'une notification existe, gris à zéro (test)
- [x] UI-003 — panneau sous les indicateurs, dans la fenêtre, défilant à 50 notifications (test)
- [x] UI-004 — copie, chemin abrégé, suppression, « Ouvrir » inactif sur un fichier absent (test)
- [x] UI-005 — retraduction au changement de langue, panneau ouvert (test)
- [x] UI-006 — « Plan de positions » (grep et test)
- [x] UI-007 — « Affichage » dans les quatre vues des plans, en fr, de et en (test)
- [x] ARCH-001 — `calc/notices.py` sans Qt (test) et lint
- [x] ARCH-002 — `test_tasks.py`, aucun widget touché hors du fil principal
- [x] ARCH-003 — résultat périmé ignoré (test), aucune écriture de projet hors du fil principal
- [x] ARCH-004 — un seul moteur de tuiles PDF (grep et test)
- [x] ARCH-005 — un seul module de disposition (grep et test)
- [x] ARCH-006 — `CREATE_NO_WINDOW` explicite pour `QProcess` (test)
- [x] Revue finale (T29) : multiples erreurs simultanées, suppression, messages et chemins très longs, échec Typst, fichier absent, calcul en échec, opération de plusieurs secondes. Chaque cas est essayé et noté en §15.
- [x] Documentation : `docs/ui/window.md`, `docs/architecture/performance.md` (nouveau), `layout.md`, `docs/typst/api-conventions.md`, `docs/decisions.md`, `CHANGELOG.md`, « Nouveautés » fr/de/en.
- [x] Tests : nouveaux `test_notices`, `test_tasks`, `test_pdf_tiles`, `test_layout_store`, lint des boîtes, et tests des plans étendus. La suite complète est verte.

## 12. Traçabilité

| Source | Élément | Statut |
|---|---|---|
| T1 | REQ-003, REQ-009, objectif | capturé |
| T2 | REQ-001 | capturé |
| T3 | REQ-001 | capturé |
| T4 | REQ-001, D2 | capturé |
| T5 | REQ-004, ARCH-002 | capturé |
| T6 | REQ-002 | capturé |
| T7 | REQ-002 | capturé |
| T8 | REQ-003 | capturé |
| T9 | REQ-004 | capturé, étendue → Q-004 |
| T10 | REQ-006 | capturé |
| T11 | REQ-006 | capturé (estimation → §9) |
| T12 | REQ-007, UI-001 | capturé |
| T13 | REQ-008, ARCH-006, REQ-011 | capturé |
| T14 | REQ-009 | capturé, questions → Q-002 |
| T15 | UI-001, UI-002 | capturé |
| T16 | UI-002 | capturé |
| T17 | UI-002 | capturé |
| T18 | UI-002 | capturé |
| T19 | UI-003 | capturé |
| T20 | UI-004 | capturé |
| T21 | UI-004 | capturé |
| T22 | UI-004 | capturé |
| T23 | UI-004, REQ-011 | capturé |
| T24 | UI-005, REQ-011 | capturé |
| T25 | REQ-010, ARCH-001 | capturé |
| T26 | ARCH-001, §8 | capturé |
| T27 | REQ-005, ARCH-002, ARCH-003 | capturé |
| T28 | §11 (critères repris) | capturé |
| T29 | §11 revue finale, §15 | capturé |
| T30 | REQ-012 | capturé |
| T31 | REQ-013 | capturé, geste → Q-005 |
| T32 | REQ-014 | capturé |
| T33 | UI-006 | capturé |
| T34 | REQ-015, ARCH-004 | capturé, moteur → Q-001 |
| T35 | REQ-015, ARCH-004 | capturé |
| T36 | REQ-016 | capturé, sens de « document » → Q-003 |
| T37 | REQ-017 | capturé |
| T38 | REQ-018 | capturé |
| T39 | REQ-019 | capturé |
| T40 | REQ-020 | capturé |
| T41 | UI-007, D3 | capturé |
| T42 | REQ-021 | capturé |
| T43 | REQ-021 | capturé |
| T44 | — | déjà couvert : spec des vues (ARCH-001 de celle-ci), D1 |
| T45 | — | déjà couvert : spec des vues REQ-001/002, D1 |
| T46 | — | déjà couvert : spec des vues REQ-003 (WP1 fait), D1 |
| T47 | — | déjà couvert : spec des vues REQ-004, D1 |
| T48 | — | déjà couvert : spec des vues UI-006, D1 |
| T49 | — | déjà couvert : spec des vues REQ-005, D1 |
| T50 | UI-001 | déjà couvert (spec des vues UI-001) ; ordre avec les nouveaux indicateurs ici |
| T51 | UI-007, D3 | déjà couvert (spec des vues REQ-006), sauf le nom « Typst » → « Affichage » ici |
| T52 | — | déjà couvert : spec des vues UI-002, D1 |
| T53 | — | déjà couvert : spec des vues UI-003, D1 |
| T54 | — | source interrompue ; la vue est décrite par la spec des vues (T15 de celle-ci, UI-004) |
| T55 | REQ-022 | capturé |
| T56 | REQ-022 | capturé |
| T57 | REQ-023, ARCH-005 | capturé |
| T58 | REQ-024 | capturé |

### Points de la source non résolus

- T9 : jusqu'où précharger → Q-004.
- T14 : sort des questions Oui/Non → Q-002.
- T31 : geste de rotation → Q-005.
- T34 : moteur PDF → Q-001.
- T36 : sens de « document » dans la vue *Export* → Q-003.

## 13. Revue d'architecture

Deux revues `architecture-reviewer` en parallèle, le 07.10.2026 : **zone A** (démarrage, tâches, notifications, processus) et **zone B** (plans, PDF, légendes Typst, disposition, libellés). Verdict des deux : **APPROUVER AVEC RÉSERVES**. Chaque réserve est reprise dans l'élément concerné (« Après revue ») ou en ARCH-007/008.

### Modules concernés

- **Démarrage**
  - `woodcore_gui.py` : imports en tête `:12-106`, `build` `:3083-3204`, `rebuild` `:3417`, `reexport` et compilations `:3868-4060`, `install_error_box` `:4107`, `open_project` `:4168`, `main` `:4284` ;
  - `packaging/entry_gui.py:12`, `packaging/launcher.py:157`, `Woodcore.bat`.
- **Attente** : `busy.py`, `stallwatch.py:30`.
- **Processus** : `proc.py`, `tests/test_no_console.py`.
- **Fils** : `drawing_tab.py:70-100` (`_Background`, `_run_layer_export`), `pdf_pane.py:122`, `sheet_editor.py:772`, `variables_tab.py:245`.
- **Excel** : `build_reference.py:18`, `io_excel.py:13`, `export_all.py:22, 143, 243`.
- **PDF** :
  - `plan_canvas.py` : `PdfPages` `:279-335`, `RenderCache` `:163`, `DiskCache` `:192`, `SvgLayer` `:338` ;
  - `document_view.py` : `_PdfSource` `:278`, `schedule` et `sharp_job` `:741-808` ;
  - `sheet_editor.py:1099`, `annex_tab.py:333`.
- **Export** :
  - `sheet_editor.py` : échelle `:1462`, `edit` et `_wrote` `:1845`, `_clear_object` `:1337`, poignées `:66, 520`, `resize_object` `:1899`, `add_position_list` `:2081` ;
  - `typst_objects.py:2088`, `sheets.py:49-60, 514-560`.
- **Plans** : `plan_tab.py:69, 979, 1414, 1785-1830`, `drawing_tab.py:713, 1857, 1995`, `plan.py:31, 183, 219, 635, 1289, 1322`, `plan_svg.py:425, 496, 596, 737-872`, `fire.py:463`.
- **Typst** : `lib/calc-engine.typ:1136, 1282, 2143, 3166`, `lib/sheet.typ:337-391`, `lib/document.typ:708`, `templates/forms/{bfh,compact,neutral}/template.typ`.
- **Fenêtre** : `views.py:11-34`, `chrome.py:281-473` (`SideNav`), `woodcore_gui.py:2938, 3207, 3420, 3457`, `usersettings.py`, et les seize splitters de B10.

### Existant réutilisé

- **Calque bloquant** : `busy.py` (`Spinner`, `_Guard`, `run_in_thread`), étendu.
- **Modèle des notifications** : `engine.Note`, `note_text`.
- **VS Code** : `vscode_executable()` et `open_vscode`.
- **Bandeaux** : `callout=info|warning|danger`.
- **Ligne d'état** : `set_status`.
- **En-tête** : `chrome.SegmentedSwitch` et les couleurs `danger`, `warning`, `wood` de `theme.json`.
- **Rendu PDF** : `PdfPages`, `RenderCache`, `DiskCache` et `PageArea`.
- **Libellés de type** : `positions_store.type_label`.
- **Aires et légende** : `fire.ring_area` (déplacé), `plan_svg.legend_items`, `plan-legend`.
- **Coupe** : `open_plan`, `choose_tool`, `set_storey_choice`, `storey_index`.
- **Volets** : `FoldButton`, `usersettings`.

### Risques

| Risque | Gravité | Traitement |
|---|---|---|
| A01 — `setCreateProcessArgumentsModifier` absent de PySide6 6.11.2 | bloquant | REQ-008/ARCH-006 corrigés : règle de Qt gardée, cause cherchée (option A) |
| A02 — cause de la console inconnue ; `code.cmd` ferait un flash | important | REQ-008 : mesure, `vscode_executable()` |
| A03 — imports en tête, entrée PyInstaller, `Qt.Tool` sans barre des tâches | bloquant | REQ-002 : `woodcore_start.py`, écran hors `Qt.Tool` |
| A04 — GIL et DLL au chargement, objectif 0,25 s à froid | important | REQ-003 : fil pour les bibliothèques sans Qt, 0,25 s à chaud, seuil paramétrable |
| A05 — `rebuild` de 5 à 8 s après chaque export et changement de langue | important | REQ-005 : mesuré à part ; refonte par onglet hors périmètre sauf décision |
| A06 — `openpyxl` aussi par `io_excel` dans le CLI, classeur de référence réécrit | important | REQ-005 |
| A07 — `_run_layer_export` écrit depuis un fil | important | ARCH-003 : un seul écrivain à la fois |
| A08 — glossaire de fenêtre : quatre modules non fusionnés, clés qui se recouvrent | important | REQ-010 |
| A09 — journal entre processus, cycle `proc`/`notices`, `info`/`success` morts | important | REQ-010, ARCH-006 |
| A10 — comptes, constructeurs `QMessageBox(...)`, pas d'hôte avant la fenêtre ni dans les dialogues, 175 occurrences en test | bloquant | REQ-009 : `NoticeBar` partagée, validation en ligne, lint avec `# dialog-ok`, fixture `conftest` |
| A11 — `excepthook` tardif, débit, z-order sous le calque, survie à `rebuild` | important | REQ-010, REQ-006 |
| A12 — décision v0.113 (export bloquant), avertissements en texte, cache des poids | important | REQ-006, ARCH-007, ARCH-008, REQ-003 |
| A13 — `pdf_chip`, en-tête qui bouge, tests de démarrage en sous-processus | mineur | UI-001, REQ-007, REQ-004 |
| B01 — rendu déjà hors fil, verrou PDFium unique ; ARCH-004 inexact | bloquant | REQ-015/ARCH-004/D4 corrigés : tuiles bornées sur `PdfPages`, un cache, `sheet_editor` y passe |
| B02 — zones jamais nettes : image nulle sans cache négatif, rendu périmé accepté, éviction, `SvgLayer` | important | REQ-015 : cause mesurée et écrite d'abord |
| B03 — liste d'échelles : `editingFinished` → `_wrote` → `options.load` → destruction | bloquant | REQ-017 : cause écrite, correctif |
| B04 — pas de poignée hors `DRAWING_KINDS`, liste sans hauteur | important | REQ-018 : largeur seule |
| B05 — `bundles.json` : version stricte, clés réécrites, pas de schéma, id contre name | bloquant | REQ-016 : 1.0/1.1 additif, dérivé à la lecture, schéma ; id soumis à l'approbation |
| B06 — poteau en carré fixe, dimension hors de `render`, `angle` refusé | bloquant | REQ-013 : forme soumise à l'approbation, source 1.4 |
| B07 — décimale en point, légende de feuille dédoublonnée, aire dupliquée, schéma d'export | bloquant | REQ-020 corrigé |
| B08 — `type_label` existe ; langue du projet ou de la fenêtre ; matériau sans glossaire | important | REQ-014 : type seul traduit, langue soumise à l'approbation |
| B09 — supplément « Fig. », règle globale à exporter, légendes à la main | important | REQ-021 corrigé |
| B10 — rien de persisté ; clé `views` prise ; `\\.\DISPLAYn` instable | important | REQ-023/ARCH-005 |
| B11 — `SideNav` à largeur fixe, `setHidden` utilisé par Ctrl+1…9 | important | REQ-022 : ensemble `folded` à part |
| B12 — grep trop large, helper plutôt que clé, fichier d'un pair | mineur | REQ-024 |
| B13 — autres « Plan de position », `view_display` existe | mineur | UI-006, UI-007 |
| B14 — magnétisme en barre d'outils, en mémoire ; « Coupe… » et l'enregistrement automatique | mineur | REQ-012, REQ-019 |

### Approche retenue

On mesure d'abord, puis on fait les correctifs ciblés (échelle, libellés, magnétisme, noms). Viennent ensuite les fondations : notifications, diagnostics Typst, moteur de tâches. Puis le démarrage, les PDF et le domaine des plans (source 1.4, export 1.4, recueils 1.1), les légendes Typst et la disposition. La documentation vient en dernier. Aucune refonte de `rebuild` par onglet (A05) sans décision.

### Verdict

**APPROUVER AVEC RÉSERVES**. Les réserves sont reprises dans la spec. Restent pour l'ingénieur à l'approbation : la forme du poteau tourné (B06), un id de recueil distinct du nom (B05) et la langue du libellé de position (B08).

## 14. Plan d'implémentation

Chaque étape met à jour §16. Les fichiers partagés avec la spec des vues (`woodcore_gui.py`, `views.py`, `drawing_tab.py`, `plan_tab.py`, `schema_tab.py`) ne sont touchés qu'après avoir vérifié qu'aucune session paire ne les modifie (CON-006).

1. **WP0 — Mesure (REQ-001)**
   - `tests/perf_startup.py`, hors `test_*` : phases du démarrage, `rebuild`, lanceur, export CLI, en sous-processus neuf.
   - `docs/architecture/performance.md` : état de départ.
   - Recherche de la cause de la console (A02) et des zones jamais nettes (B02) ; les deux sont écrites.
2. **WP1 — Correctifs ciblés (REQ-017, UI-006, UI-007, REQ-012, REQ-014, REQ-024)**
   - `sheet_editor.py` : `_wrote` seulement sur changement, `returnPressed` ;
   - `views.py` (`typst` → `view_display`) ;
   - `plan_tab.py:69`, `fire_tab.py`, `commands.json`, `website/strings.json` ;
   - module « rien de sélectionné » de `DrawingTab` (magnétisme) ;
   - `type_label` dans `plan_tab.py:1819` ;
   - helper `followed_text` dans `cards.py`, utilisé par trois onglets.
   - Tests : `test_sheet_editor`, `test_views`, `test_plan_tab_rework`, `test_plan_canvas_rework`, `test_position_type_i18n`, `test_connectors`, `test_member_check_tab`, `test_schema_tab`, `test_i18n`.
3. **WP2 — Notifications, cœur (REQ-010, REQ-011, ARCH-001, ARCH-007, ARCH-008)**
   - `calc/notices.py` (`Notice` d'après `engine.Note`, magasin, dédoublement, `configure`, journal par processus) ;
   - `calc/typst_diagnostics.py`, qui remplace les cinq lectures ;
   - lignes JSON du CLI d'export ;
   - fixture `conftest`.
   - Tests : `test_notices`, `test_typst_diagnostics`, `test_new_project` (export structuré).
4. **WP3 — Notifications, fenêtre (UI-001 à UI-005)**
   - `calc/tools/notices_ui.py` : `NoticeBar` (indicateurs 🛑/⚠, clignotement de 3 s, panneau défilant, développer, copier, supprimer, ouvrir par `vscode_executable`), dans `MainWindow` et `HomeWindow` ;
   - `excepthook` et `threading.excepthook` ;
   - survie à `rebuild` ;
   - ordre de l'en-tête.
   - Tests : `test_notice_bar`, `test_views` (ordre).
5. **WP4 — Plus de boîtes d'erreur (REQ-009)**
   - conversion site par site : `autosave.refuse/warn` vers la ligne d'état, export et compilations vers les notifications, `information` vers `set_status`, validation des dialogues en bandeau ;
   - lint AST avec `# dialog-ok` ;
   - adaptation des tests qui substituaient `QMessageBox`.
   - Tests : nouveau lint, `test_autosave`, `test_engine_check`, `test_annex`, `test_busy`.
6. **WP5 — Moteur de tâches (REQ-006, REQ-007, ARCH-002, ARCH-003)**
   - `calc/tools/tasks.py`, qui absorbe `busy.run_in_thread`, les deux `_Job`, `_Background` et `variables_tab.Read` ;
   - `busy` étendu : temps écoulé, progression, `finally` ;
   - indicateur de fond à place réservée ;
   - un seul écrivain à la fois ;
   - numéro de génération.
   - Tests : `test_tasks`, `test_busy`.
7. **WP6 — Démarrage (REQ-002, REQ-003, REQ-004, REQ-005)**
   - `calc/tools/woodcore_start.py`, puis `entry_gui`, `.bat` et `relaunch` qui passent par lui ;
   - écran étagé hors `Qt.Tool` ;
   - imports sans Qt en fil ;
   - `build_steps()` ;
   - `openpyxl`, `io_excel` et `typst_check` paresseux ;
   - classeur de référence réécrit seulement s'il change ;
   - seuil de `stallwatch` en paramètre ;
   - préchargement selon D7, la suite en fond.
   - Tests : `test_startup` (sous-processus), `test_busy` ; mesures après.
8. **WP7 — Console (REQ-008, ARCH-006)**
   - correctif de la cause trouvée en WP0 ;
   - sonde de `test_no_console` étendue à `start_detached`, `os.startfile` et au `.bat`.
9. **WP8 — PDF (REQ-015, ARCH-004)**
   - `PdfPages` généralisé en tuiles bornées sur une grille fixe, avec un seul cache ;
   - branché sur `document_view`, `plan_canvas` et `sheet_editor.page_image` ;
   - correctif des zones jamais nettes ;
   - limite de `QPixmapCache` pour `SvgLayer`.
   - Tests : `test_pdf_tiles` (gigue), `test_document_view`, `test_sheet_editor`.
10. **WP9 — Domaine des plans (REQ-013, REQ-020)**
    - source 1.4 : `angle` des poteaux selon la décision B06, `show_length` ;
    - `ring_area` déplacé ;
    - `number_frame` tourné ;
    - métrés dans `legend`, export `plans.json` 1.4, schémas, exemple figé régénéré, `plan-legend` et somme dans `sheet.typ` ;
    - interface : champ d'angle et ↻ 90°, réglages des longueurs global et par élément.
    - Tests : `test_plan_rotation`, `test_plan_metres`, `test_plan_types_v0116`, reproductibilité de l'export.
11. **WP10 — « Coupe… » (REQ-019)**
    - `choose_section`, puis `open_plan`, `choose_tool` et `set_storey_choice` sur `storey_index` ;
    - retour au plan d'origine.
    - Test : `test_plan_tab_rework`.
12. **WP11 — Vue *Export* (REQ-016, REQ-018)**
    - `bundles.json` en 1.0/1.1 additif, champs dérivés à la lecture, `schemas/bundles.schema.json`, horodatage du PDF assemblé ;
    - pages du recueil au centre par `PageArea` ;
    - poignée de largeur pour la liste de positions et la légende.
    - Tests : `test_sheets`, `test_sheet_bundles_tab`, `test_sheet_editor`.
13. **WP12 — Légendes Typst (REQ-021)**
    - fonction de règle exportée par `calc-engine.typ` : séparateur « — » et suppléments par kind et par langue au glossaire ;
    - appelée par les trois formes.
    - Test : `test_captions` (3 formes × 3 langues).
14. **WP13 — Disposition et volet tout à gauche (REQ-022, REQ-023, ARCH-005)**
    - `calc/tools/layout_store.py` : signature hachée injectable, `bind`, anti-rebond, repli `last_used` ;
    - les seize splitters branchés ;
    - `SideNav` : ensemble `folded` et poignée de largeur.
    - Tests : `test_layout_store`, `test_chrome`.
15. **WP14 — Documentation et revue finale (T29)**
    - `docs/ui/window.md`, `docs/architecture/performance.md` et `layout.md`, `docs/typst/api-conventions.md`, `docs/decisions.md` (amender la v0.113 si besoin, rotation, `bundles` 1.1, légendes), `CHANGELOG.md`, « Nouveautés » fr/de/en ;
    - suite complète ;
    - essais de la revue finale notés en §15 ;
    - mesures après dans `performance.md`.

## 15. Vérification

Deux tours de l'agent `requirements-verifier` (Sonnet), le 08.10.2026, sur l'arbre de travail comparé à HEAD 30e32b6. Le 1er tour a trouvé des tests périmés, une boîte restante, un seuil codé en dur et l'écrivain de fond non sérialisé (ARCH-003) ; tout a été corrigé (§16). Le 2e tour ne trouve **aucun ❌**. Les corrections faites après lui sont notées « après le 2e tour ».

| Élément | Verdict | Preuve |
|---|---|---|
| REQ-001 | ⚠️ | `tests/perf_startup.py`, `docs/architecture/performance.md` (avant et après par phase, causes). Le chiffre « après » à froid n'est pas mesuré : il faut un redémarrage de la machine. |
| REQ-002 | ⚠️ | `woodcore_start.py`, `Woodcore.pyw`, `entry_gui.py` ; `test_startup` : écran en 0,5–1,6 s selon la charge. Après le 2e tour, les hooks d'exception et le journal sont posés dès l'écran. Reste l'essai manuel de la barre des tâches (capture). |
| REQ-003 | ⚠️ | Écart écrit : arrêt maximal de 0,5–1,3 s (un constructeur d'onglet). `stallwatch.install(stall_s=…)`. |
| REQ-004 | ⚠️ | `test_startup::test_after_the_start_no_tab_imports_anything…` vert. Le tour des onglets sous `stallwatch` à 0,25 s n'est pas testé ; il ne tiendrait pas le seuil, pour la même raison que REQ-003. |
| REQ-005 | ✅ | `import woodcore_gui` à chaud : 3,3–4,7 → 1,9–2,4 s ; `rebuild()` : 12,5–19,7 → 6,9–8,3 s ; export : 6,6 → 2,6–5,5 s. |
| REQ-006 | ✅ | `test_tasks::test_a_blocking_task_holds_the_window…` : 3 s, carte visible et nommée, au moins 20 tics, carte retirée. |
| REQ-007 | ✅ | `test_tasks::test_what_runs_anywhere…` : compte, infobulle des deux tâches, aucune modale (après le 2e tour). |
| REQ-008 | ⚠️ | Écart écrit. Cause trouvée (`Woodcore.bat`), `Woodcore.pyw` ajouté, sonde réelle sous `pythonw` dans `test_no_console` (7 tests verts). L'essai filmé est à l'ingénieur. |
| REQ-009 | ✅ | `test_no_message_boxes` vert. Les boîtes qui restent sont des décisions marquées `# dialog-ok`, dont `update_gui.ask` (après le 2e tour). |
| REQ-010 | ✅ | `calc/notifications.py`, `test_notices` (11). |
| REQ-011 | ⚠️ | Écart écrit (compilation et export seulement). `test_typst_diagnostics::test_a_real_compile…`. |
| REQ-012 | ✅ | `test_plan_tabs_v0117::test_snapping_is_a_module…`, `test_plan_tracking`. |
| REQ-013 | ✅ | `test_plan_metres`, `test_plan_tabs_v0117::test_a_column_selected_is_turned…`. |
| REQ-014 | ✅ | `test_plan_tabs_v0117::test_the_position_list…` (fr, de, en). |
| REQ-015 | ⚠️ | Écart écrit : pas de tuiles (D4 amendée), critères chiffrés non mesurés. `test_sheet_editor::test_a_zoom_never_renders…`. |
| REQ-016 | ⚠️ | Écart écrit (pas d'horodatage). `test_sheets`, `test_sheet_bundles_tab`. |
| REQ-017 | ✅ | `test_sheet_editor::test_the_scale_list_stays_open…`. |
| REQ-018 | ⚠️ | `test_a_list_of_the_positions_and_a_legend_are_widened_by_their_handle` passe par `resize_object`, pas par un vrai glissement de souris. |
| REQ-019 | ✅ | `test_plan_tabs_v0117::test_coupe_opens_the_section…`. |
| REQ-020 | ⚠️ | Écart écrit (`plans.json` reste en 1.3, champ additif). `test_plan_metres` (6), `test_plan_style` (empreintes reprises pour cette seule raison). |
| REQ-021 | ✅ | `test_captions` : trois formes et trois langues. `///`, deux exemples, `commands.json`. |
| REQ-022 | ⚠️ | `test_layout_store::test_a_group_of_the_navigation_folds…`. Pas de test fermeture puis réouverture ; le vérificateur l'a contrôlé à la main : `SideNav(width=, folded=)` restaure l'état, et la poignée glissée change la largeur. |
| REQ-023 | ⚠️ | Écart écrit (seul `tab.splitter` est lié). `test_layout_store`. |
| REQ-024 | ✅ | `test_member_check_tab`, `test_schema_tab`, `test_connectors`, `cards.followed`. |
| UI-001 | ✅ | `test_notice_bar::test_the_indicators_stand_left…`. |
| UI-002 | ✅ | `test_notice_bar::test_an_indicator_is_quiet…`, avec l'infobulle « 2 erreurs critiques » (après le 2e tour). |
| UI-003 | ✅ | `test_notice_bar::test_the_panel_opens…` : 50 notifications, dans la fenêtre, 70 % au plus, défilement. |
| UI-004 | ✅ | `test_notice_bar::test_a_row_opens_copies_deletes…`. |
| UI-005 | ⚠️ | Écart écrit (le panneau se ferme au `rebuild()`). |
| UI-006 | ✅ | Grep vide dans `calc/`. `test_views::test_the_plan_tab_is_named_plan_de_positions…` (après le 2e tour). |
| UI-007 | ✅ | Même test : Import / Dessin / Affichage / Export en fr, de et en (après le 2e tour). |
| ARCH-001 | ✅ | `test_notices::test_the_core_imports_no_qt`, lint. |
| ARCH-002 | ⚠️ | Écart écrit (pas d'annulation). Fils conservés listés dans `performance.md`. |
| ARCH-003 | ⚠️ | Écart écrit (un écrivain à la fois). `test_tasks`, `test_plan_tabs_v0117::test_the_window_s_export_waits…`. |
| ARCH-004 | ⚠️ | Écart écrit, voir REQ-015. `test_pdf_tiles` n'existe pas. |
| ARCH-005 | ⚠️ | Écart écrit, voir REQ-023. |
| ARCH-006 | ⚠️ | Écart écrit : impossible en PySide6 6.11.2, et la sonde réelle le prouve. |
| ARCH-007 | ⚠️ | Écart écrit. `test_typst_diagnostics` (5). |
| ARCH-008 | ✅ | `test_notices::test_the_export_started_by_the_window_writes_structured_warnings`. |
| CON-001 à CON-008 | ✅ | CON-006 non vérifiable par l'agent ; aucune commande destructrice n'a été employée. |
| Documentation | ✅ | `window.md`, `performance.md`, `layout.md`, `api-conventions.md`, `decisions.md`, `open-questions.md`, `testing.md`, `CHANGELOG.md`, « Nouveautés » 0.117 fr/de/en. |
| Tests | ⚠️ | Voir « Suite complète » ci-dessous. |

**Revue finale (T29), cas par cas :**
- **Plusieurs erreurs à la fois** : `test_notice_bar` (50 avertissements et une critique, filtres, défilement) et `test_notices` (dédoublement).
- **Suppression** : d'une notification, de toutes, d'un genre (`test_notice_bar`, `test_notices`).
- **Message très long** : environ 200 caractères testés, première ligne élidée et détail à la ligne (`NoticeRow`). Plusieurs milliers de caractères ne sont pas testés.
- **Chemin très long** : 300 caractères, abrégé au milieu, entier en infobulle et dans la copie.
- **Échec Typst** : vraie compilation lue à sa ligne, notification copiée, titres fr/de/en.
- **Fichier absent** : « Ouvrir » inactif avec sa raison. Un fichier absent à l'export n'est pas testé de bout en bout.
- **Calcul en échec** : une notification `calc_failed` synthétique, l'exception d'une tâche et d'un fil. Aucun vrai calcul en échec n'est testé.
- **Opération de plusieurs secondes** : tâche bloquante de 3 s, tâche de fond, temps écoulé (`test_busy`).

**Suite complète** (08.10.2026, avant les dernières corrections) : 2 631 passés, 17 ignorés, 5 échecs. Tous sont nommés et traités :
- `test_notice_bar` (indicateur visible) et `test_tasks` (indicateur) : une activité laissée ouverte par un test précédent. Cause réelle, aussi dans la fenêtre : `pdf_pane.stop()` tuait la compilation sans terminer son activité, et le rendu d'une feuille dont l'éditeur avait disparu ne la terminait jamais. Corrigé, avec le test `test_pdf_pane::test_a_compile_stopped_tells_the_chip_it_is_over` ;
- `test_updates` : une barre encore ouverte par un test précédent consommait l'information avant que le test la lise. Le test écoute désormais les notifications ;
- `test_fire_tab::test_a_drag_renders_the_overlay…` : échoue dans la suite complète, mais passe seul (deux fois) et avec ses 144 voisins. Il dépend du minutage, et aucun lien avec ce travail n'est démontré ;
- `test_title_page::test_the_office_s_copy_of_the_bfh_form…` : antérieur à ce travail. Le `template.typ` intégré a changé au commit ae996b6, pas sa copie de bureau `../templates/forms/bfh-academique`, hors du dépôt, que je n'ai pas touchée.

**Suite complète après ces corrections** : 2 635 passés, 17 ignorés, 2 échecs.
- `test_title_page` : antérieur, voir plus haut.
- `test_fire_tab::test_a_drag_renders_the_overlay…` : il a échoué dans les **trois** suites complètes, sans message. Il passe seul, avec son fichier et avec ses 144 voisins. La cause dépend de l'ordre de la suite et **n'est pas trouvée**. Un lien avec ce travail n'est ni démontré ni exclu.

## 16. Journal d'avancement

| Date | Statut | Fait / reste |
|---|---|---|
| 2026-10-07 | draft | spécification extraite de la source (58 points, trois blocs). État relevé : import 9 s à chaud / 30 s à froid avant tout écran, 128 `QMessageBox`, trois rendus PDF, « Coupe… » qui ne fait qu'enregistrer. T44–T53 renvoyés à la spec des vues. 5 questions ouvertes |
| 2026-10-07 | specified | réponses : Q-001 A, Q-002 A, Q-003 A, Q-004 A → D4–D7. Q-005 proposée par défaut (D-P5), à confirmer à l'approbation |
| 2026-10-07 | reviewed | deux revues (A : démarrage, tâches, notifications, processus ; B : plans, PDF, Typst, disposition) : APPROUVER AVEC RÉSERVES. Réserves reprises (« Après revue » dans 29 éléments, ARCH-007/008). Plan WP0–WP14. Trois choix restent pour l'approbation (B05, B06, B08) |
| 2026-10-07 | approved | l'ingénieur approuve. B06 → D8 (carré tourné), B05 → D9 (id distinct), B08 → D10 (langue de la fenêtre), D-P1 à D-P5 confirmées. Implémentation : WP0 |
| 2026-10-08 | implementation | **WP0, première partie** (REQ-001) : `tests/perf_startup.py` et `docs/architecture/performance.md` (état de départ). Mesures à chaud : `import woodcore_gui` 3,3–4,7 s, `open_project` 12–21 s, `rebuild()` 12,5–19,7 s, export CLI 6,6 s. Causes isolées par expérience : le filtre d'événements de `busy._Guard`, installé une fois et jamais retiré, ≈ 8 s sur 19 ; la feuille de style ≈ 3 s ; `openpyxl` en tête ; les *Affichage* construits d'emblée. Restent à mesurer : la console (A02) et les zones jamais nettes (B02). La cause n° 1 est traitée en premier (partie de WP5/WP6, ordre seul changé) |
| 2026-10-08 | implementation | **Cause 1 traitée** (REQ-005, part de WP5) : `busy._Guard` n'est plus posé que pour un travail qui laisse la boucle libre (export, compilation, `run_in_thread`), et il est retiré ensuite. `guard=False` pour la construction, le rechargement, la langue et le document. `open_project` passe de 12–21 s à 11–11,7 s, `rebuild()` de 12,5–19,7 s à 7–11 s. Nouveau test `test_busy::test_the_guard_is_on_only_while_free_running_work_is_held`, `test_busy` vert (11) |
| 2026-10-08 | implementation | **WP1 fait sauf `schema_tab`** :
- REQ-017 : `SheetEditor.edit` n'écrit ni ne reconstruit rien quand rien ne change.
- UI-007 : `views.WORDS["typst"] = "view_display"`.
- UI-006 : « Plan de positions » dans l'onglet, `fire_tab`, les `///` de lib et `commands.json` ; l'historique est inchangé.
- REQ-012 : `DrawingTab.add_snap_module`, « Magnétisme » dans le volet de droite des deux onglets, hors de la barre d'outils.
- REQ-014 : `positions_store.type_label(…, app.lang)`.
- REQ-024 : `cards.followed()` « C24 — T001 » pour les moyens d'assemblage et les vérifications, `mc_w_followed` « mm — section ».

Tests verts : `test_sheet_editor` 21, `test_views` 7, `test_plan_panes_v0116` 10, `test_plan_tabs_v0117` 2 (nouveau), `test_connectors` 66, `test_member_check_tab` 32, `test_cards` 10, `test_i18n` 20. Reste : `schema_tab` (`sc_followed`), en attente du pair |
| 2026-10-08 | implementation | **WP2 fait** (REQ-010 cœur, REQ-011 lecture, ARCH-001, ARCH-007, ARCH-008) :
- `calc/notices.py`, sans Qt : `Notice`, `Store`, dédoublement, `configure`, journal tronqué au-delà de 512 Ko, `title`, `message`, `copy_text`, `report*`, `emit` et `read_output` (protocole `woodcore-notice` versionné) ;
- `calc/typst_diagnostics.py` : formats humain et court, trace d'une panique, préfixe long de Windows (`\\?\`) ôté ;
- `export_all._warn` passe par `notices.emit` quand la fenêtre le demande (`WOODCORE_NOTICES_JSON`).

Les cinq « lectures » de Typst relevées par la revue ne font que transmettre le texte, sauf `command_preview.ERROR_AT_RE` qui remappe les lignes d'un exemple (autre travail, gardé). Le nouveau lecteur sert là où une notification est faite. Tests : `test_notices` 11, `test_typst_diagnostics` 5 |
| 2026-10-08 | implementation | **WP3 fait** (UI-001 à UI-005, REQ-010 fenêtre) : `calc/tools/notices_ui.py`.
- `NoticeBar` : `ActivityChip` à place réservée, puis 🛑 et ⚠ (`Indicator`), gris à zéro, clignotant 3 s ; une critique répétée clignote de nouveau, un avertissement répété non.
- `NoticePanel` : popup sous les indicateurs et dans la fenêtre, 70 % de sa hauteur au plus, filtre, lignes repliables, Copier, Ouvrir le fichier (VS Code `-g` par `vscode_executable`, sinon le programme du fichier), Supprimer, Tout supprimer.
- `install_hooks` : `sys.excepthook` et `threading.excepthook` vers des notices critiques. `install_error_box` et `slot_error` sont retirés.
- Notices `info` : vers la ligne d'état.
- Barre aussi sur la page d'accueil (`notices_ui.words`). Journal et traduction configurés dans `main()`.

Tests : `test_notice_bar` 6 (nouveau), `test_modes_window` 19 |
| 2026-10-08 | implementation | **WP4 fait** (REQ-009) : 62 boîtes converties par script (`notices_ui.tell`, avec `key`, `args` et `title_key` quand la phrase est une clé de la fenêtre, pour qu'elle suive la langue), le reste à la main.
- Export et compilation : `read_output`, `report_typst` ; l'export de la fenêtre reçoit `WOODCORE_NOTICES_JSON`.
- Notes de l'import des positions : une notice chacune.
- Dialogues modaux (`settings_dialog` × 7, `home_page` × 2) : bandeau `notices_ui.inline_error`.
- Décisions à boutons marquées `# dialog-ok:` (verrou, migration, Typst à installer, moteur, import des positions). « pas de winget » devient un avertissement.

Lint `tests/test_no_message_boxes.py` (2) vert ; `test_home` 11, `test_autosave` 9, `test_busy` 11 verts. Suite complète en cours |
| 2026-10-08 | implementation | **Renommage** : `calc/notices.py` devient `calc/notifications.py`. `packaging/notices.py`, qui écrit les mentions des licences tierces, porte déjà ce nom, et un test qui met `packaging/` sur le chemin importait le mauvais module. L'identité d'une notification compte désormais son texte, que la revue n'avait pas prévu : deux messages de même exception technique étaient fusionnés. Tests adaptés pour lire les notifications au lieu des boîtes (`conftest.notices_said`) : `engine_check` 11, `journal` 29, `positions_tab` 9, `sheet_bundles_tab` 8, `fire_tab` 50, `updates` 17 |
| 2026-10-08 | implementation | **WP5 fait** (REQ-006, REQ-007, ARCH-002, ARCH-003).
- `calc/tools/tasks.py` : `TaskRunner` (pool, résultat sur le fil de la fenêtre, exception vers une notification critique, résultat périmé par clé ignoré, `writes=True` dans un pool d'un fil, `blocking` vers la carte de `busy`) et `activity()`, registre de ce qui tourne en fond, annoncé depuis n'importe quel fil.
- Annoncent leur activité : l'export des calques (`drawing_tab._run_layer_export`), l'aperçu Typst (`pdf_pane`), le rendu des feuilles (`sheet_editor.Compiler`). L'indicateur les nomme dans la langue de la fenêtre.
- `busy` : temps écoulé passé 2 s, `set_progress`.
- Gardés tels quels, avec leur raison : `pdf_pane._Job` et `sheet_editor._Job` (QThread déjà, déjà annoncés), `variables_tab.Read` (QThread à résultat propre), `busy.run_in_thread` (bloquant, sa propre boucle).

Tests : `test_tasks` 6, `test_busy` 12 |
| 2026-10-08 | implementation | **WP6 fait** (REQ-002, REQ-003, REQ-004, REQ-005 en partie).
- `calc/tools/woodcore_start.py` : identité de la barre des tâches, `claim_taskbar_icon` déplacé ici, `StartScreen` peint (logo, version, barre 0–100 %, étapes ✓ → ○), poids mesurés dans `start-weights.json` (cache versionné), imports sans Qt dans un fil, modules de la fenêtre un à un, puis `woodcore_gui.main(app=…)`.
- `woodcore_gui.py` lancé directement passe par lui avant ses imports, comme `packaging/entry_gui.py`.
- `open_project` et `build` lui disent le projet et l'onglet.
- `stallwatch` est posé dès l'écran.
- `openpyxl` paresseux dans `io_excel` et `build_reference`. Le classeur de référence n'est reconstruit que si ses lignes changent (empreinte en cache).

Mesures : écran en 0,5 s au lieu de 4–5 s à chaud ; `--self-test` en 9 s au lieu de 17–25 s ; export en 2,6 s au lieu de 6,6 s. Tests : `test_startup` 3 (nouveau), `test_home` 11, `test_modes_window` 19, `test_no_console` 6 |
| 2026-10-08 | implementation | **WP7 fait** (REQ-008, ARCH-006). **Mesure** : la fenêtre sous `pythonw`, un export et la compilation des trois documents, chaque fenêtre à l'écran énumérée toutes les 10 ms → **aucune console visible**. Chaque programme console lancé (python, typst, git) a son hôte `conhost.exe` caché, ce qui est normal avec `CREATE_NO_WINDOW`. **Cause trouvée** : `Woodcore.bat` lui-même, qu'un double-clic exécute dans une fenêtre `cmd`. Ajouts : `Woodcore.pyw`, exécuté par `pythonw` sans console, et le test mesuré `test_no_console::test_an_export_and_a_compilation_of_a_windowless_woodcore_open_no_console_window` (7 verts) |
| 2026-10-08 | implementation | **WP8 fait, avec un écart justifié par la mesure** (REQ-015, ARCH-004).
- **Mesure** sur le PDF d'architecte de l'ingénieur : un rendu PDFium tient le verrou 0,2–0,5 s **quelle que soit sa taille** (tuile 512² : 216 ms ; découpe 2400×1500 : 227 ms). Les tuiles d'une grille fixe de D4 seraient donc **plus lentes**, et ne sont pas faites. La décision est à amender (`decisions.md`).
- **Fait**, cause par cause :
  - *Export* : rendu hors du fil (`QPdfPageRenderer`), après immobilité du zoom, au-delà de 12 Mpx la partie vue seulement, l'image précédente étirée en attendant ;
  - *Document* : la page vue d'abord (grossière puis nette), les voisines ensuite ;
  - *Dessin* et modèles statiques : `QPixmapCache` passé de 10 Mo à 256 Mo, sans quoi le calque SVG était redessiné à chaque image.
- **Non reproduit** hors de l'écran de l'ingénieur : les « zones jamais nettes ». L'hypothèse de la rotation est écartée par l'essai.

Tests : `test_sheet_editor` 22, `test_document_view` 14, `test_plan_tabs_v0117` 3, `test_statics*` 33 |
| 2026-10-08 | implementation | **WP9 fait** (REQ-013, REQ-020).
- **Domaine** (`plan.py`) : source 1.4, l'`angle` permis sur un poteau ou un appui ponctuel (`ROTATABLE`, sinon refusé avec la raison), `show_length` par élément, et une seule règle `shows_length`. Murs, poutres et côtés de dalle (`LENGTH_TYPES`) ; rien sans échelle.
- **Métrés** : `quantities` donne m, m² et pièces par ligne de légende. `ring_area` est déplacé de `fire.py` (une seule aire) et `legend_key` partagé avec `plan_svg`.
- **Dessin** (`plan_svg`) : le carré tourné autour de son centre et les longueurs côté par côté d'une dalle. La légende exportée porte `quantity` ; l'export reste 1.3 (additif) et les schémas sont à jour.
- **Typst** : « Métrés » sous les symboles (`plan-legend`), additionnés sur une feuille de plusieurs plans (`sheet.typ`), glossaire `plan.legend.quantities` et `plan.legend.pieces`.
- **Fenêtre** : rotation, « ↻ 90° » et touche R pour un poteau sélectionné ; longueur propre (comme le plan, affichée, masquée) ; case globale renommée « Longueurs des éléments ».

Tests : `test_plan_metres` 6 (nouveau, dont la légende compilée en fr et en de), `test_plan_tabs_v0117` 5. Mises à jour pour la 1.4 : `test_plan_sections`, `test_plan_types_v0116`. `test_fire` 118 : un échec isolé au premier passage, vert au second, instable et sans lien démontré |
| 2026-10-08 | implementation | **WP10 fait** (REQ-019) : « Coupe… » écrit le lien, puis ouvre la coupe ; le plan quitté est enregistré comme tout plan quitté. L'étage du plan est choisi, puis la ligne d'étage est armée, ou le cadre si la ligne existe déjà, ou la ligne est sélectionnée si les deux existent (`storey_index` ou texte). « ← P01 » dans la rangée de la coupe ramène au plan, et la ligne d'état dit ce qui est ouvert. Test : `test_plan_tabs_v0117::test_coupe_opens…` (6 verts au total) |
| 2026-10-08 | implementation | **WP11 fait** (REQ-016, REQ-018).
- **Domaine** : `bundles.json` 1.1 (1.0 lu tel quel, jamais réécrit à la lecture), champs facultatifs `id`, `description` et `storey`. `sheets.bundle_fields` les dérive à la lecture du premier plan de la première feuille (id du plan, son libellé, son étage). L'id effectif nomme le PDF (D9), retombe sur le nom s'il heurte une feuille ou un autre recueil, et `set_bundle_field` le valide et renomme le PDF déjà écrit. Schéma `schemas/bundles.schema.json` ajouté.
- **Fenêtre** : `calc/tools/bundle_view.py`. Choisir le dossier d'un recueil dans la vue *Export* montre au centre toutes ses pages à la suite (aperçus compilés ou repris du cache, assemblés en tâche de fond, `QPdfView` multipage) et à droite ses champs id, nom, description et étage, la valeur reprise du plan en gris. Nouveau genre `bundle` dans `drawing_tab`.
- **Poignée** : la liste de positions et les légendes ont la leur (`RESIZABLE_KINDS`) ; elle règle la largeur, la hauteur suit les lignes.

Tests : `test_sheets` 19 (dont un nouveau), `test_sheet_bundles_tab` 9 (dont un nouveau), `test_sheet_editor` 23 (dont un nouveau) |
| 2026-10-08 | implementation | **WP12 fait** (REQ-021). `caption-rules` (lib/calc-engine.typ) est appliqué par `woodcore-document` à chaque document d'un projet : supplément du genre dans la langue du rapport (glossaire `figure.supplement_table` et `figure.supplement_image` : Tableau/Tabelle/Table, Figure/Abbildung/Figure), séparateur « — ». Il couvre les `figure()` de l'auteur, de `table-figure` et du moteur. Documenté : bloc `///`, deux exemples, catégorie `document` de `build_reference`, `commands.json` fr/de/en. Exemples figés reconstruits (391/391), avec le seul glossaire regelé, sans `--freeze` des données. Non couvert : les aperçus des commandes (préambule `command_preview`, sans `woodcore-document`), qui gardent le séparateur de Typst. Tests : `test_captions` (nouveau, 3 langues), `test_commands` 34 |
| 2026-10-08 | implementation | **REQ-024 achevé** dans `schema_tab` (« mm — T001 » par `cards.followed`, clés `sc_followed` retirées), avec l'accord de la session pair. Trois mots devenus sans code retirés : `compile_failed`, `export_warnings`, `po_import_notes`. Tests : `test_schema_tab` 41, `test_i18n` 20 |
| 2026-10-08 | implementation | **WP13 fait** (REQ-022, REQ-023, ARCH-005).
- `calc/tools/layout_store.py` : signature des écrans par fabricant, modèle, numéro de série (sinon taille physique) et facteur d'échelle, triés et hachés, jamais `\\.\DISPLAYn`. Tailles en fractions sous `layouts[signature][onglet][vue][nom]` des réglages, repli sur `last_used`, écriture 400 ms après un glissement.
- `bind` : liaison générique de chaque `tab.splitter` (`woodcore_gui.bind_layouts`), sans code par onglet, rétablie au changement de vue (`view_changed`).
- `chrome.SideNav` : groupes repliés par un clic sur leur titre (ensemble `folded` à part ; `order()` et Ctrl+1…9 non touchés), flèche ▸/▾ peinte, poignée de largeur (150–420 px) retenue par écran, groupes repliés dans `nav_folded`.

Libellé « Longueurs des éléments » raccourci : une case trop large imposait 623 px au volet de droite (`test_panes`). Tests : `test_layout_store` 4 (nouveau), `test_chrome` 9, `test_panes` 6, `test_views` 7, `test_modes_window` 19 |
| 2026-10-08 | testing | **WP14, documentation** : `docs/ui/window.md` §10quater (démarrage, notifications, tâches, plans, Export, volet de gauche, dispositions), `docs/architecture/layout.md` (sept modules et `Woodcore.pyw`), `docs/architecture/performance.md` (avant/après, causes), `docs/domain/position-plans.md` (source 1.4, métrés, recueils 1.1), `docs/typst/api-conventions.md` (`caption-rules`), `docs/decisions.md` (sept décisions, dont l'amendement de D4 et de la règle de session des volets), `docs/open-questions.md` (ce qui reste), `docs/conventions/testing.md` (dix fichiers de tests), `CHANGELOG.md`, « Nouveautés » 0.117 fr/de/en. Suite complète en cours ; vérification indépendante lancée |
| 2026-10-08 | testing | **Vérification, 1er tour : corrections.** Quatre tests périmés adaptés. Le test du démarrage ne plante plus à la sortie. La boîte de `migrate_dialog` est convertie, et le lint voit aussi une boîte seulement nommée. Le seuil de `stallwatch` est un paramètre. ARCH-003 : l'export de la fenêtre attend l'export des calques. Restes de « repris de » dans `window.md`, et « Plan de positions » sur le site. Suite complète : échecs nommés et traités :
- `test_plan_style` : empreintes reprises pour les seules raisons voulues (cotes T et D, `quantity`), vérifiées à l'octet ;
- `test_project_dialog`, `test_packaging` : lisent le bandeau, la notification et l'entrée `woodcore_start` ;
- `tests/perf_startup._copy_project` laissait son projet temporaire actif dans la suite, d'où les erreurs de `test_plan_command_builder` et `test_positions_store` : corrigé par `project.using`.

Tests ajoutés : une tâche bloquante de 3 s avec au moins 20 tics (REQ-006), et les légendes dans les trois formes et les trois langues (REQ-021). Mesures « après » et fils conservés dans `performance.md`. Le plus long arrêt de l'écran de démarrage reste 0,5–1,3 s selon la charge (un constructeur d'onglet). Écarts consignés dans chaque exigence (« Écart (vérification) ») et dans `open-questions.md` |
| 2026-10-08 | verification | **Vérification, 2e tour** : aucun ❌, des ⚠️ écrits comme écarts (§15). Corrigé ensuite :
- `woodcore_start` pose les hooks d'exception et le journal dès l'écran ;
- la boîte de `update_gui.ask` est marquée `# dialog-ok` ;
- tests ajoutés : titre de l'onglet et quatre vues en fr/de/en (UI-006, UI-007), infobulle des deux tâches et aucune modale (REQ-007), infobulle « 2 erreurs critiques » (UI-002) ;
- une activité qui fuyait : `pdf_pane.stop`, et le rendu d'une feuille orpheline (avec un test) ;
- `test_settings_dialog`, `test_typst_check` et `test_updates` lisent le bandeau ou les notifications.

Les deux tours de vérification sont faits. Restent les ⚠️ de §15, soumis à l'ingénieur |
| 2026-10-08 | completed | l'ingénieur accepte les écarts de §15. Spécification déplacée dans `docs/requirements/completed/` |
