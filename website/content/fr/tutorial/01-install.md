# Installer Woodcore

Woodcore s'installe en une minute, sans droits d'administrateur, et contient tout ce qu'il faut pour produire un rapport : le programme avec sa fenêtre, la ligne de commande `woodcore-cli` et Typst.

## Télécharger et installer

Téléchargez l'installateur depuis la page [Télécharger](~/download/) et lancez-le. Comme il n'est pas signé, Windows peut afficher « Windows a protégé votre ordinateur » : cliquez sur **Informations complémentaires**, puis **Exécuter quand même**.

Laissez cochée l'option **Ouvrir les fichiers .woodcore avec Woodcore**. Un projet Woodcore est un dossier qui contient un fichier `<nom>.woodcore` : avec cette option, un double-clic sur ce fichier ouvre le projet, comme un document Word s'ouvre dans Word.

> [!tip]
> Woodcore s'installe pour votre utilisateur dans `%LOCALAPPDATA%\Programs\Woodcore\<version>\`. Chaque version a son dossier : une nouvelle version ne remplace jamais l'ancienne.

## Les outils à côté

Woodcore calcule les charges dans sa fenêtre et écrit un rapport en Typst. Un outil rend le travail confortable :

- **Visual Studio Code** avec l'extension **Tinymist**, pour écrire le rapport : Tinymist affiche la documentation de chaque commande au survol et l'aperçu du PDF en direct.

Typst lui-même est livré avec Woodcore : il n'y a rien à installer de plus.

## Rester à jour

À chaque démarrage, Woodcore regarde si une version plus récente est publiée sur ce site. Si oui, une fenêtre la présente avec ses nouveautés et propose de l'installer : Woodcore télécharge l'installateur, vérifie son empreinte, et le lance. Les versions installées restent, et le menu Démarrer ouvre désormais la plus récente.

À l'étape suivante, nous créons un premier projet.
