# Écrire le rapport

Le rapport est un document Typst : `Statischer Rapport.typ` et ses sections, dans `Statischer Bericht (typst)/Sections/`. **Fichier › Ouvrir dans VS Code** ouvre le dossier ; avec l'extension Tinymist, épinglez `Statischer Rapport.typ` comme fichier principal (*Typst: Pin the main file*) pour voir l'aperçu du PDF en direct.

## Une section

Chaque section commence par la même ligne, qui rend toutes les commandes de Woodcore disponibles :

```typ
#import "../commands.typ": *

= Einwirkungen

Die Schneelast wird nach SIA 261 ermittelt.

#show-calc("snow-load", "SL")
```

Le texte est le vôtre, dans la langue du rapport ; les commandes impriment ce que l'export a calculé. La [référence](~/docs/) les liste toutes, avec leurs exemples.

## Rattacher les calculs à une position

`#calc-block` groupe les calculs qui concernent une ou plusieurs positions, et imprime en tête la ligne que `#member` imprime de chacune au niveau 1 :

{{example calc-block-1}}

## Trois niveaux de détail

Chaque commande imprime plus ou moins selon le **niveau** : 1 le résultat, pour le maître d'ouvrage ; 2 le calcul important, pour l'ingénieur ; 3 tout le détail, pour le vérificateur. Le niveau du rapport se choisit à l'export (étape 8), et un appel peut imposer le sien :

```typ
#show-calc("snow-load", "SL", level: 3)
```

> [!tip]
> Dans la fenêtre de Woodcore, l'onglet **Commandes** montre chaque exemple aux niveaux 1, 2 et 3 : c'est le moyen le plus rapide de voir ce qu'un appel imprimera.
