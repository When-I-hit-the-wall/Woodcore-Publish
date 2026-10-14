# Nouveautés

Ce que chaque version de Woodcore apporte, ce qu'elle change dans un rapport déjà écrit, et ce qu'il faut faire en passant à elle. Lisez les pages de toutes les versions entre la vôtre et la nouvelle : les changements s'additionnent.

## Mettre à jour Woodcore

1. **Installez la nouvelle version.** Woodcore la propose à son démarrage (**Installer**), ou téléchargez-la depuis la page [Télécharger](~/download/). Elle s'installe **à côté** des versions précédentes, sans les remplacer.
2. **Ouvrez votre projet.** Woodcore compare le moteur copié dans le projet (`Statischer Bericht (typst)/_woodcore/`) au sien et demande : « Ce projet utilise le moteur de Woodcore 0.88.0. Le mettre à jour vers 0.89.0 ? ».
   - **Voir les différences…** montre ce qui change dans les fichiers du moteur ;
   - **Mettre à jour** copie le nouveau moteur : les nouvelles commandes deviennent disponibles dans le rapport ;
   - **Plus tard** ne change rien ; la question revient à la prochaine ouverture et au prochain export.
3. **Exportez le PDF et relisez-le.** Un nouveau moteur peut imprimer un rapport autrement — la mise en page, un texte, un niveau de détail. Les nombres, eux, ne changent que si la page de la version le dit.
4. **Faites les points « À faire »** des versions que vous avez sautées.

> [!tip]
> Un projet terminé peut rester sur sa version : dans **Fichier › Propriétés du projet…**, le champ **Version de Woodcore** l'épingle. Un double-clic sur le projet ouvre alors cette version-là, qui reste installée.

## Revenir en arrière

Rien n'est perdu à une mise à jour : chaque export dépose dans `_Archiv/` un zip de l'état qui l'a produit, moteur compris, et les versions précédentes de Woodcore restent installées. Une version se désinstalle séparément, dans **Paramètres › Applications** de Windows.
