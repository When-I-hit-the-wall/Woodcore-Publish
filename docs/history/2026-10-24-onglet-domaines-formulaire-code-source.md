# Source de la spec 2026-10-24-onglet-domaines-formulaire-code (§2, déplacée telle quelle)

La §2 de [la spécification](../requirements/completed/2026-10-24-onglet-domaines-formulaire-code.md) déplacée mot pour mot, pour que la spec reste sous 100 KB tant qu'elle est active (`tests/test_docs_coherence.py`). Les points T restent cités par leur numéro dans la spec.

L'issue #113, par points. Le prototype (artefact claude.ai « Domaines de calcul », version 2) en est la référence visuelle ; ce que l'issue dit l'emporte sur lui. Les citations sont mot pour mot, coupées par « […] » quand un point est long ; le texte entier est dans l'issue.

> **T1** — « L'ingénieur a revu deux versions d'un prototype HTML de l'**onglet « Domaines »** (`tab_formula`, l'onglet où il écrit ses propres calculs : un domaine est un fichier `Domains/<id>.typ` fait de lignes `#var`, `#eq`, `#verify` et de son texte Typst). Le 24.10.2026, il a **validé la version 2**. Cette issue décrit ce qui est à implémenter, dans une autre session. »
>
> **T2** — « Aujourd'hui (master `57172dd`), l'onglet est celui de la v0.117 à 0.122 (`docs/ui/tab-formulas.md`) : `calc/tools/formula_tab.py` (799 lignes), `formula_tab_widgets.py` (598 : `FormulaText`, un `QTextEdit`, et `PillPainter`), `formula_tab_blocks.py` (353), `formula_tab_domains.py` (547), `formula_tab_unfold.py` (178) ; le modèle `calc/domains/formula_domain.py` (1366 lignes : `parse_domain`, `patched`, `compute`, `key_from_symbol`, `header_of`, `new_domain`, `variables_of`, `resolve_import`…) et la place des pastilles `calc/domains/formula_layout.py` ; l'algèbre `calc/units.py` (`FormulaError`), tenue égale à celle du rapport par `tests/test_units.py` ; les options de ligne `calc/tools/display_options.py` (`SPECS` de `var`, `eq`, `verify` ; `NORM_REF`). »
>
> **T3** — « **Le texte et une pastille par commande** : les décisions D-01 à D-05 de l'issue #40 (spec `docs/requirements/completed/2026-10-11-formules-blocs-en-ligne-et-niveau-manuel.md`). Cette issue les remplace. »
>
> **T4** — « **Sa version 2 (24.10.2026) est celle validée.** Sa version 1, à la même adresse, comparait quatre éditions (Formulaire, Code, Les deux, Pastilles). »
>
> **T5** — « Deux domaines : **Poutre P1**, le domaine du projet d'exemple tel quel (`tests/projet-exemple/Domains/poutre-p1.typ`), et **Panne de toiture P2**, écrit pour le prototype, qui lit la neige SL et les charges permanentes dans l'export. Huit exemples au-dessus de la fenêtre montrent les erreurs : h = 200 mm qui ne passe pas, nom inconnu, unités incohérentes, parenthèse oubliée, lien introuvable, unité demandée kN. »
>
> **T6** — « **Chaque nombre est celui que calcule Woodcore 0.122.** Le mode Affichage montre environ 1 200 rendus réels de Typst, compilés par le moteur de Woodcore. Les erreurs de Typst montrées sont ses vrais messages (`typst compile`). »
>
> **T7** — « **Ce que le script de l'artefact contient**, à reprendre dans l'implémentation (en Python sans Qt pour ce qui est du modèle) : `parseFile`, `writeFile`, `renumber`, `computeFile` […] ; `inferLine`, `keyFromSymbol` […] ; `typedSym`, `symTable`, `toSym`, `toKey` […] ; `orderCheck`, `moveItems` […] ; `nlKind`, `nlParse`, `nlBoxes`, `nlCommit` […] ; `deleteItem` et son « Annuler » ; `openPicker`, `linkMany` […] ; `CORE`, `INROW`, `argsLine`, `argList`, `argsHTML`, `applyArg` […] ; `DOPTS`, `defaultsLine`, `setDopt` […] ; `stateList`, `errText` […] ; `deps`, `lite` : les survols liés ; les mots de la fenêtre en fr, de et en (`W`, `W2`, `DW`). »
>
> **T8** — « 1. L'édition | **Formulaire et Code**, sur le même fichier, et un mode **Affichage**. « Les deux » et les **pastilles s'arrêtent**. »
>
> **T9** — « 2. Un domaine nouveau | Woodcore écrit `#calc-defaults(presets: "block", scope: "domain")` en tête ; un domaine existant garde ce qu'il a. **Cette ligne s'active et se désactive dans l'Affichage**, comme les autres options du domaine. »
>
> **T10** — « 3. Ajouter une ligne | Le **+ entre deux lignes** et la **ligne du bas, déduite**. »
>
> **T11** — « 4. Lier une variable | Le **nom tapé**, le bouton **« Lier une variable… »** et le **correctif du message**. »
>
> **T12** — « 5. Un calcul se tape | **Avec les symboles affichés** (`sigma_(m,d) / f_(m,d)`), traduits en clés comme aujourd'hui. »
>
> **T13** — « 6. Une vérification qui ne passe pas | **Orange** : une information sur l'ouvrage, le fichier se compile. »
>
> **T14** — « 7. Un domaine de l'onglet lu par son nom (`domain: "poutre-p1"`) | Woodcore **avertit en orange** tant que ce domaine n'est pas inclus plus haut dans le rapport. »
>
> **T15** — « Les modes | Trois : **Formulaire**, **Code**, **Affichage**. »
>
> **T16** — « Le Code | La commande où est le curseur (#var, #eq, #verify) est **reconnue tout de suite** ; à droite, **tous ses arguments**, modifiables, qui s'écrivent dans la ligne. »
>
> **T17** — « Le Formulaire | Garder : le symbole affiché en ligne, la formule d'une eq, la variable de calcul dessous, le libellé, la norme, l'article, la description. À droite, **les autres arguments** de la ligne choisie ; de même dans l'Affichage. »
>
> **T18** — « Le clic sur une variable à droite, ou sur le nom d'un résultat | **Il doit écrire le nom dans la formule en cours de frappe** (ne marchait pas). »
>
> **T19** — « Une ligne nouvelle | **Une pastille var / eq / verify à gauche** : en *auto* au départ (déduite du texte), un clic pour la choisir ; **les champs de la commande dessous**. Pour la ligne du bas aussi. »
>
> **T20** — « Supprimer | **Un petit × à droite de chaque ligne.** »
>
> **T21** — « Lier des variables | **Cases à cocher à gauche ; Ctrl+clic pour plusieurs, Maj+clic pour une plage ; un clic choisit sans importer ; « Valider » importe tout ce qui est choisi.** »
>
> **T22** — « Réordonner | **La poignée ⋮⋮, sans raccourci** (Alt+↑/↓ retiré). **Ctrl+clic choisit plusieurs lignes, qui se déplacent ensemble.** »
>
> **T23** — « Lier à un autre domaine | **Ne rien changer** au fonctionnement actuel : le risque d'itération infinie est déjà traité dans Woodcore. »
>
> **T24** — « **Trois modes au-dessus de la fenêtre : Formulaire · Code · Affichage.** Formulaire et Code sont la vue Calcul de Woodcore (`calc/tools/views.py`), Affichage sa vue Affichage. Le fichier `.typ` reste **la seule source** : chaque mode l'écrit et le relit. »
>
> **T25** — « **À gauche**, la liste : les domaines de l'onglet, chacun avec son état (✔ 70 %, 1 ✘), puis les groupes des onglets spécialisés (Neige, Vent, Traction…), **repliés** (aujourd'hui chaque domaine est déplié ligne à ligne : plus de 300 lignes). Les archives en bas. « Domaine », « Dupliquer ». »
>
> **T26** — « **Au centre**, la ligne du nom et de l'id, le fichier (`Domains/panne-p2.typ`), la légende des survols, puis le mode choisi. »
>
> **T27** — « **À droite**, les modules déplaçables et repliables (brique commune, issues #94 et #95), dans cet ordre : **État du domaine**, **Arguments de la ligne**, **Résultats**, **Variables du domaine**, les extraits de la norme épinglés. »
>
> **T28** — « **Une rangée par ligne du fichier** : la poignée ⋮⋮, le numéro de ligne, une étiquette de commande (`var`, `eq`, `verify`, `texte`), puis : `var` : le **symbole composé** (Typst), `=`, la valeur, l'unité, l'**i** de la clause, le libellé ; `eq` : le symbole, `=`, **le calcul tapé en symboles** (`sigma_(m,d) / f_(m,d)`), l'unité (auto, ou une unité de la dimension du résultat), `=`, **le résultat**, l'**i** ; `verify` : la relation en symboles, les deux valeurs et ✔ ou ✘ ; une variable liée : son symbole, sa valeur, « ↗ Neige · SL », son libellé lu dans l'export ; le texte de l'ingénieur : une rangée de texte, imprimée telle qu'écrite. »
>
> **T29** — « **La rangée choisie** montre dessous la variable de calcul (la clé), le libellé, la norme, l'article (`norm-section:`), la description. »
>
> **T30** — « **Un × à droite de chaque rangée** la supprime ; le message qui suit offre **« Annuler »**. Les lignes qui l'utilisaient passent en erreur dans l'état, avec leur cause. »
>
> **T31** — « **Le + entre deux rangées** (au survol) offre var, eq, verify, texte, lier une variable. La ligne qu'il ouvre a sa pastille, fixée sur la commande choisie. »
>
> **T32** — « **Une rangée en erreur** a un trait rouge à gauche et son message dessous ; une rangée en avertissement (unité, vérification qui ne passe pas, domaine pas inclus) un trait orange. »
>
> **T33** — « **En bas du formulaire**, une ligne où l'on tape « h = 240 mm », « M_d = q_d * l^2 / 8 » ou « sigma_(m,d) <= f_(m,d) ». »
>
> **T34** — « **À gauche, une pastille** qui dit ce qu'elle déduit : « var auto », « eq auto », « verify auto ». Un clic ouvre auto, var, eq, verify, texte ; un choix la fixe (sans « auto »). »
>
> **T35** — « **Dessous, les champs de la commande**, remplis depuis ce qu'on tape et modifiables : var : symbole, valeur, unité, libellé ; eq : symbole, calcul, unité, libellé ; verify : relation, libellé ; texte : le texte. »
>
> **T36** — « **La règle de déduction** (`inferLine`) : une relation (`<=`, `>=`, `<`, `>`, `!=`, `≤`, `≥`) fait un `verify` ; « symbole = nombre unité » un `var` ; « symbole = expression » un `eq` ; le reste un texte. La clé vient du symbole (`M_(y,d)` → `M_y_d`, `key_from_symbol`, rendue unique). »
>
> **T37** — « **Entrée** ou ✓ écrit la ligne ; Échap ou × l'abandonne. La même pastille et les mêmes champs servent à la ligne ouverte par le +. »
>
> **T38** — « Le champ du calcul montre **les symboles affichés** des variables au-dessus : `sigma_(m,d) / f_(m,d)` ; le fichier garde les clés (`sigma_m_d / f_m_d`). »
>
> **T39** — « **La table symbole → clé** est celle des lignes au-dessus de la ligne tapée. Un symbole se tape s'il est un nom indicé simple (`f_(m,d,"Tab")`, `q_k`). Sinon il se tape par sa clé : un symbole composé comme (g<sub>k</sub> + a<sub>k</sub>)<sub>gew</sub> (`gk_ak_gew`), ou un symbole que porte déjà une autre clé. Les espaces après les virgules sont admis (`sigma_(m, d)`). »
>
> **T40** — « La complétion propose les variables du domaine **par clé ou par symbole** et écrit le symbole ; puis celles du projet (le lien, ci-dessous). »
>
> **T41** — « **La cause du défaut, trouvée dans le prototype** : choisir une rangée redessine le formulaire, et le champ retenu pour l'insertion était l'ancien, retiré de la page. L'implémentation doit retenir **le champ de calcul qui a eu le curseur en dernier, tel qu'il est maintenant**, et sa position de curseur. »
>
> **T42** — « Un clic sur une variable du module « Variables », ou sur **le nom d'un résultat** du module « Résultats » (souligné en pointillé, infobulle « Clic : écrire ce nom dans le calcul en cours »), écrit son symbole **à la place du curseur, sans lui reprendre le curseur**. En Code, il écrit la clé dans le texte. »
>
> **T43** — « Sans calcul en cours, un message le dit. »
>
> **T44** — « **En Code**, il suit le curseur : la commande reconnue tout de suite (« eq · Domains/panne-p2.typ:30 »), puis **tous ses arguments** : `var` : clé, symbole, valeur, unité, label, descr, norm, norm-section, puis display, style, label-position, descr-position, norm-position, level ; `eq` : clé, symbole, calcul, unit, label, descr, norm, norm-section, puis as-unit, display-formula, display-equation, style, role, label-position, descr-position, norm-position, level ; `verify` : relation, label, descr, norm, norm-section, puis display, role, label-position, descr-position, norm-position, level. »
>
> **T45** — « **En Formulaire**, pour la rangée choisie : **les autres arguments**, ceux que la rangée ne montre pas (display…, style, role, as-unit, level). »
>
> **T46** — « **Dans l'Affichage**, la ligne cliquée montre **tous** ses arguments, avec la même liste. »
>
> **T47** — « Une valeur changée **s'écrit dans la ligne** du fichier ; en Code, le curseur et le défilement restent où ils étaient. Dessous, la ligne écrite dans le fichier. »
>
> **T48** — « Les valeurs des listes sont celles de `lib/display-presets.json` (`fine-values`, `fine-keys`) : `none`, `variable`, `value`, `value-unit`, `variable-value-unit` ; `before`, `after`, `footnote` ; `in-line`, `line-right` ; `normal`, `bold`, `underline`, `double` ; `data`, `compute`, `result` ; *auto* n'écrit rien. »
>
> **T49** — « Une ligne de texte n'a pas d'arguments ; une commande qui ne se lit pas encore le dit. »
>
> **T50** — « **La poignée ⋮⋮** : on glisse la rangée, une barre montre où elle ira. **Pas de raccourci clavier.** »
>
> **T51** — « **Ctrl+clic** ajoute une rangée au groupe, ou l'en retire. Le groupe a un cadre pointillé bleu, et un bandeau dit « 3 lignes choisies : glissez une de leurs poignées… ». Échap ou un clic simple défait le groupe. La rangée choisie avant le premier Ctrl+clic entre dans le groupe. »
>
> **T52** — « **Glisser la poignée d'une rangée du groupe déplace tout le groupe**, dans son ordre, à l'endroit du dépôt. »
>
> **T53** — « **Un déplacement est refusé quand une ligne passerait au-dessus de ce dont elle est calculée**, pour chaque ligne du groupe et pour celles qui restent : « Déplacement refusé : W<sub>y</sub> utilise b, qui serait plus bas. » Le refus existe déjà (`fm_drop_order`) ; il s'étend au groupe. »
>
> **T54** — « **Le nom tapé** : en tapant « q_k » dans un calcul, la liste propose ce domaine, puis le reste du projet (« q<sub>k</sub> · Neige · SL · 1.115 kN/m² »). Choisir une variable d'ailleurs écrit au-dessus `#var("q_k1", domain: ("snow-load", "SL"))`. »
>
> **T55** — « **Le correctif du message** : un nom inconnu que l'export connaît, l'état propose « Lier q_k1 depuis Neige · SL ». »
>
> **T56** — « **La fenêtre « Lier une variable… »** (bouton du module Variables, ou + → lier), groupée par onglet et par cas, avec recherche : **une case à cocher à gauche** de chaque variable ; un **clic** choisit une seule variable, **sans l'importer** ; **Ctrl+clic** en ajoute ou en retire une ; **Maj+clic** choisit une plage ; un clic sur la case l'ajoute ou la retire ; **« Valider (3) »** écrit les liens de tout ce qui est coché, d'un coup, dans l'ordre de la liste, au-dessus de la ligne choisie ; Entrée valide, Échap ferme ; une variable déjà dans le domaine est grisée, « déjà dans ce domaine ». »
>
> **T57** — « **Le reste ne change pas** : la résolution des liens, la garde contre une boucle de domaines (`resolve_import`), l'avertissement orange d'un domaine de l'onglet lu par son nom tant qu'il n'est pas inclus plus haut (réponse 7). Typst s'arrête sinon : « var: no domain "poutre-p1" is declared above this line » (vérifié avec le moteur 0.122). »
>
> **T58** — « **Rouge** : une erreur de lecture à sa ligne et sa colonne (la parenthèse oubliée), un nom inconnu, des unités qui ne s'additionnent pas, un lien introuvable. **Une faute est dite une fois**, avec « 3 lignes plus bas en dépendent », pas une fois par ligne qui en dépend. »
>
> **T59** — « **Orange** : une vérification qui ne passe pas (réponse 6) ; une unité demandée qui n'est pas celle du résultat ; un domaine de l'onglet lu par son nom (réponse 7) ; un domaine sans `presets: "block"` (« l'Affichage imprime en un seul paragraphe »), qui mène aux options du domaine. »
>
> **T60** — « Un clic sur un message va à la ligne : la rangée clignote et le champ prend le curseur ; en Code, la ligne est sélectionnée. »
>
> **T61** — « **Les messages sont dans la langue de la fenêtre** (glossaire, `fm_e_*`) : `units.FormulaError` et `formula_domain.DomainError` rendent un code et ses valeurs. Le rapport garde les messages anglais de Typst. »
>
> **T62** — « **Résultats** : chaque `eq` et chaque `verify`, rien de saisi ; un clic déplie la formule en lettres et en nombres ; la clause à droite ; « Tout déplier », « Tout replier », « Copier les valeurs ». Le nom d'un résultat s'écrit dans le calcul en cours (ci-dessus). »
>
> **T63** — « **Variables du domaine** : symbole, valeur, origine (« ce domaine » ou « ↗ Neige · SL ») ; un clic écrit la variable dans le calcul en cours ; « Lier une variable… ». »
>
> **T64** — « **La bulle de la norme** pour chaque ligne qui cite une clause relevée ; un clic l'épingle sous les résultats, un second clic la retire (issue #96) ; Ctrl+clic ouvre la partie de la norme. »
>
> **T65** — « Survoler une ligne (rangée, ligne du code, résultat, élément de l'Affichage) l'allume en jaune ; les lignes dont elle se calcule en bleu ; celles qui l'utilisent en vert. Rien d'autre ne s'allume. Les dépendances viennent de `formula_domain.compute` (les opérandes de chaque ligne). »
>
> **T66** — « **Le fichier `.typ` lui-même**, coloré (`richtext.TypstHighlighter` existe déjà), une marge des numéros de ligne (rouge à une erreur, orange à un avertissement), une marge à droite des résultats de chaque ligne (« = 4.238 kN/m », « ✔ 9.967 ≤ 11.28 N/mm² ») et des erreurs à leur ligne. »
>
> **T67** — « **La ligne du curseur** est reconnue tout de suite et alimente le module « Arguments de la ligne ». »
>
> **T68** — « Une faute de frappe casse la ligne jusqu'à ce qu'elle soit corrigée : l'état le dit ; le fichier n'est écrit qu'une fois relu. »
>
> **T69** — « **Au centre**, le fichier comme Typst l'imprime, élément par élément (rendus réels), les notes en bas de page ; « Montrer les éléments masqués » ; le zoom. »
>
> **T70** — « le fichier et **la commande à copier dans la section**, `#include "/Domains/panne-p2.typ"` ; »
>
> **T71** — « « lire une valeur ailleurs dans le rapport », `#var("eta", domain: "panne-p2", display: "value-unit")` ; »
>
> **T72** — « le **niveau du domaine** (`#domain(level:)`), 1, 2 ou 3 ; »
>
> **T73** — « **les options du domaine, chacune cochée ou non** (réponse 2) : `presets: "block"` (« en bloc : une ligne par valeur »), `label-position`, `descr-position`, `norm-position`, `style`, chacune avec sa valeur. Cocher écrit l'option dans **une** ligne `#calc-defaults(…, scope: "domain")` sous l'en-tête ; décocher la retire ; plus rien de coché retire la ligne. Les options sont celles que `calc-defaults` accepte déjà (`lib/formula.typ`, `calc-default-names`) : rien de nouveau dans le moteur. Valeurs proposées à l'activation : `label-position: "after"`, `descr-position: "footnote"`, `norm-position: "line-right"`, `style: "normal"` ; »
>
> **T74** — « les **éléments du fichier** : une rangée par ligne, avec son niveau propre (0 1 2 3, celui du domaine en pointillé ; un second clic le rend au domaine) ; un clic ouvre tous ses arguments (ci-dessus), « Rétablir la ligne », la ligne écrite dans le fichier ; »
>
> **T75** — « « Voir le fichier entier ». »
>
> **T76** — « Un domaine que Typst ne compile pas montre l'erreur de Typst, ou celle de l'état si c'est la même. »
>
> **T77** — « 1. **Un domaine de l'onglet s'imprime en un seul paragraphe** : l'onglet n'écrit pas `#calc-defaults(presets: "block")` ; dix-sept notes pour Panne P2 au niveau 3. Les fichiers que Woodcore écrit pour la neige ou une vérification ont cette ligne. → réponse 2. »
>
> **T78** — « 2. **L'Affichage d'une ligne n'offre que le niveau et le style** : `display_options.SPECS` donne `level` et `style` à `var` et `eq`, `level` seul à `verify`. Aucun argument fin de la 0.121 ne se règle (`FINE` le note : « until lot 19 (UI-002) gives it their controls »). → le module « Arguments de la ligne ». »
>
> **T79** — « 3. **Le champ « Article » écrit `norm-ref:`, les fichiers écrivent `norm-section:`** (`display_options.NORM_REF`). Pour γ<sub>G</sub>, cité `norm-section: "Tableau 1"`, le champ est vide. Le remplir ajoute `norm-ref:` à côté, et la compilation s'arrête : « var: norm-section: and norm-ref: are one argument -- write norm-section: alone ». → lire et écrire `norm-section:`, lire `norm-ref:` d'un fichier ancien. »
>
> **T80** — « 4. **Les refus du calcul sont en anglais** dans une fenêtre en français, coupés à 80 caractères (`formula_tab_widgets.Block.view_html`) : « eq: no variable named 'L' here -- declared here: gk_ak_gew, q_k1, e, l, gam… ». → glossaire. »
>
> **T81** — « 5. **Une faute devient quatre pastilles rouges** : avec `L` pour `l` dans M<sub>d</sub>, Python refuse M<sub>d</sub>, σ<sub>m,d</sub>, la vérification et η, chacun avec son message. Typst s'arrête à la première. → la cause seule, et « 3 lignes plus bas en dépendent ». »
>
> **T82** — « 6. **Une variable liée s'affiche sous sa clé** (« gk<sub>akgew</sub> » au lieu de (g<sub>k</sub> + a<sub>k</sub>)<sub>gew</sub>) et « repris de dead-load / EL+AL-Dach ohne Wasser » au lieu de « Charges permanentes ». »
>
> **T83** — « 7. **La liste de gauche montre les symboles en code Typst** (« c_("red", "b/h") = 0.804 ») et déplie chaque domaine : plus de 300 lignes. »
>
> **T84** — « 8. **La parenthèse oubliée n'est pas à la même ligne** : Woodcore dit « line 24, column 1 », là où il bute ; Typst ligne 19, colonne 5, là où la parenthèse s'ouvre. → la ligne de Typst. »
>
> **T85** — « 9. **Dans un bloc, `#var` et `#eq` n'ont pas la même police** : le « = 1.35 » d'un `#var` est plus petit et d'une autre police que le « = 4.238 kN/m » d'un `#eq` (rendu niveau 3). À corriger dans `lib/`. »
>
> **T86** — « 10. **Pour un nom inconnu ou des unités incohérentes, Typst ne nomme pas la ligne du domaine** : son message finit dans le moteur (« while calling `get` at lib/formula.typ:1510 »). Seule la fenêtre peut dire « ligne 13 de `Domains/panne-p2.typ` ». »
>
> **T87** — « 11. **`examples/data/formulas.json` annonce `poutre-p1`**, mais `examples/` n'a pas de dossier `Domains/` ; seul `tests/projet-exemple` l'a. »
>
> **T88** — « 12. **Deux mots retirés restent** : `fm_state_misnamed` parle encore de `#var-domain` (retiré en 0.121), et `fm_cmd_val`, `fm_cmd_var-unit` restent dans le glossaire sans bouton. »
>
> **T89** — « 13. **Dans la vérification dépliée BI-01**, `eta_s` et `eta` sont la même formule écrite deux fois, et f<sub>m,y,d</sub> n'a pas de clause, alors que f<sub>t,0,d</sub> de ZT-01 cite SIA 265 Tableau 8. »
>
> **T90** — « Ce qui change dans Woodcore » (tableau de l'issue : Le Formulaire ; Le Code ; La ligne déduite et sa pastille ; Le calcul en symboles ; Le clic qui écrit un nom ; Supprimer, Annuler ; Déplacer à plusieurs ; Lier à plusieurs ; Les arguments d'une ligne ; « Article » ; `presets: "block"` et les options du domaine ; Les messages ; Les extraits de la norme — « Relevés dans le prototype pour huit clauses (SIA 260, 261, 265) ; une clause sans relevé montre son nom, sans bulle. » ; La liste de gauche).
>
> **T91** — « **Le modèle** (`calc/domains/`, sans Qt) : `infer_line(text, taken)` […] ; La traduction symbole ↔ clé […] ; Le contrôle d'ordre d'un groupe de lignes déplacé, avec la phrase du refus ; La ligne `#calc-defaults(…, scope: "domain")` lue et écrite option par option […] ; Les erreurs rendues comme un code et des valeurs ; une faute dite une fois, ses dépendantes comptées ; `norm-section:` lu et écrit, `norm-ref:` lu. »
>
> **T92** — « **L'onglet** : Les trois modes Formulaire · Code · Affichage ; « Les deux » et les pastilles retirés ; Le Formulaire […] ; Le clic sur une variable ou un nom de résultat écrit dans le calcul en cours (défaut corrigé) ; La poignée, Ctrl+clic, le déplacement d'un groupe ; Alt+↑/↓ absent ; La fenêtre « Lier une variable… » […] ; Le Code […] ; Le module « Arguments de la ligne » en Code (tous), en Formulaire (les autres), dans l'Affichage (tous) ; Les options du domaine à cocher dans l'Affichage ; L'état du domaine, en trois langues, un clic qui mène à la ligne ; La liste de gauche : les groupes des onglets spécialisés repliés. »
>
> **T93** — « **Partout** : Les mots en de, fr et en (`tests/test_i18n.py`) ; les mots retirés (défaut 12) ôtés ; une ligne au catalogue des tests. Les tests de l'onglet (`tests/test_formula_tab*.py`) refaits pour les rangées et le code. La documentation : `docs/ui/tab-formulas.md` réécrit, `docs/typst/formulas.md` si le format change, `docs/decisions.md` §13 (la fin des pastilles, D-01 à D-05 de #40 remplacées ; le formulaire et le code ; `presets: "block"` par défaut) ; `CHANGELOG.md` ; la page « Nouveautés » en trois langues. Une copie du prototype dans `docs/requirements/prototypes/2026-10-24-onglet-domaines/`, lue par `action: "read"` sur l'artefact. »
>
> **T94** — « **Le widget du Formulaire** : un `QTableView` et un modèle, ou une colonne de widgets de rangée. Le choix décide du coût du glisser, du Ctrl+clic et du redessin sans perdre le curseur. »
>
> **T95** — « **Le texte de l'ingénieur entre les commandes** : il devient des rangées de texte. Ce que deviennent une commande écrite **dans** une ligne de texte (`- $0°$ bis $30°$: #eq(…)`, spec `2026-10-14-commandes-en-ligne-domaine`) et le collage aux paragraphes (`formula_layout.from_paragraphs`) : une rangée de texte qui contient sa commande, ou une coupure du texte. »
>
> **T96** — « **L'annulation** : seulement la dernière suppression, comme le prototype, ou une pile pour tous les gestes de l'onglet. »
>
> **T97** — « **Un domaine déplié d'un onglet spécialisé** (la carte « Vérification dépliée », `formula_tab_unfold`) : les mêmes rangées, et ses états (« modifiée hors de Woodcore », « conflit »…) sur le trait de la rangée au lieu du contour de la pastille. »
>
> **T98** — « **La ligne de l'erreur** : prendre celle de Typst (défaut 8) demande de la calculer comme Typst, là où la parenthèse s'ouvre. »
>
> **T99** — « **La police de `#var` et `#eq` en bloc** (défaut 9) : à corriger dans `lib/`, hors de l'onglet ; une issue à part si la spec l'écarte. »
>
> **T100** — « Lien avec les autres issues : **#40** : le texte et les pastilles (D-01 à D-05), que cette issue remplace. **#19** : les options d'affichage de l'onglet Formules. **#42** : les variables liées des champs, la source de « Lier une variable… ». **#94, #95** : les briques communes (liste de cas, volet de modules, état, survols liés). **#96** : l'extrait épinglé, retiré au second clic. »
