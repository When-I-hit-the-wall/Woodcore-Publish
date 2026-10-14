# Télécharger Woodcore

{{download}}

## Prérequis

| Élément | | Remarque |
|---|---|---|
| Windows 10 ou 11, 64 bits | nécessaire | Woodcore est un programme Windows. |
| Environ 250 Mo par version | nécessaire | Chaque version s'installe dans un dossier à elle. |
| Droits d'administrateur | non | L'installation se fait pour l'utilisateur, dans `%LOCALAPPDATA%\Programs\Woodcore\`. |
| Microsoft Excel | recommandé | Pour remplir le classeur des charges (les positions se saisissent dans Woodcore). Woodcore lit les valeurs qu'Excel a calculées : enregistrez le classeur dans Excel avant d'importer. |
| Le classeur des charges Belastungsannahmen | pour les charges | Woodcore en lit les feuilles `SL-`, `EL+AL-` et `WL-` au format du modèle 3.2. Il n'est pas livré avec Woodcore. |
| Visual Studio Code et l'extension Tinymist | recommandé | Pour écrire le rapport, avec la documentation de chaque commande au survol. |
| Typst | inclus | Typst 0.14.2 est livré avec Woodcore : rien à installer. |
| Une connexion Internet | facultative | Seulement pour savoir si une nouvelle version est publiée. |

## Installer

1. Téléchargez l'installateur ci-dessus et lancez-le.
2. Windows peut afficher « Windows a protégé votre ordinateur » : l'installateur n'est pas signé. Cliquez sur **Informations complémentaires**, puis **Exécuter quand même**.
3. Choisissez la langue de l'assistant et laissez cochée l'option **Ouvrir les fichiers .woodcore avec Woodcore** : un double-clic sur un projet l'ouvrira.
4. À la fin, Woodcore s'ouvre sur sa page d'accueil.

Le menu Démarrer contient **Woodcore**, qui ouvre toujours la version la plus récente installée, et une entrée par version.

## Mises à jour

À chaque démarrage, Woodcore demande à ce site si une nouvelle version est publiée. Si c'est le cas, une fenêtre la présente avec ses nouveautés :

- **Installer** télécharge l'installateur, vérifie son empreinte SHA-256 et le lance ;
- **Plus tard** repose la question le lendemain ;
- **Ignorer cette version** ne la propose plus — la suivante le sera.

Sans connexion, rien ne s'affiche et rien n'est ralenti.

## Plusieurs versions côte à côte

Une nouvelle version s'installe **à côté** des précédentes, sans les remplacer. Un projet exporté il y a des années se rouvre ainsi avec la version qui l'a produit : dans **Fichier › Propriétés du projet**, le champ **Version de Woodcore** épingle un projet à une version. Un double-clic sur un projet ouvre la version qu'il demande, sinon la plus récente.

## Désinstaller

Chaque version se désinstalle séparément, dans **Paramètres › Applications** de Windows, sous le nom « Woodcore 0.89.0 ». Vos projets ne sont jamais touchés : ils vivent dans leurs propres dossiers.
