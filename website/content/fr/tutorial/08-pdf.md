# Exporter le PDF

**Exporter PDF** importe les classeurs, puis compile le rapport : `Statischer Rapport.pdf` s'écrit à côté de `Statischer Rapport.typ` et s'ouvre. Si l'import échoue, rien n'est compilé et le PDF précédent reste tel quel.

## Choisir le niveau et la langue

La petite flèche à côté du bouton ouvre un menu de réglages ; ils valent pour les exports suivants :

| Réglage | Effet |
|---|---|
| **Tel qu'écrit (document)** | le niveau et la langue que le document déclare lui-même |
| **Niveau de détail de base 1, 2 ou 3** | le niveau du rapport ; un appel qui impose le sien le garde |
| **Niveau de détail uniforme 1, 2 ou 3** | tout le rapport à ce niveau, même les appels qui en imposent un |
| **Langue du document, de, fr, en** | la langue des mots que Woodcore imprime |

Un même projet donne ainsi le rapport du maître d'ouvrage (uniforme 1), celui de l'ingénieur (niveau de base 2) et celui du vérificateur (uniforme 3).

## Chaque export est archivé

Chaque export réussi dépose dans `_Archiv/` une copie du PDF et un zip de l'état qui l'a produit — le rapport, l'export, le moteur, les dessins —, nommés par la date et l'heure. Un rapport remis il y a longtemps se retrouve ainsi tel qu'il était.

## En ligne de commande

`woodcore-cli.exe`, dans le dossier d'installation, fait la même chose sans fenêtre :

```bash
woodcore-cli export --project "Halle Nord.woodcore" --uniform 3 --lang fr
```

C'est la fin du tutoriel. La [référence des commandes](~/docs/) et les [exemples](~/examples/) vont plus loin.
