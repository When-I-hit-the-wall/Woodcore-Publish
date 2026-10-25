# Créer un projet

Lancé sans projet, Woodcore s'ouvre sur sa page d'accueil : les projets ouverts récemment, et trois boutons — **Ouvrir…**, **Nouveau projet…** et **Convertir un ancien dossier…**.

## Nouveau projet

Cliquez sur **Nouveau projet…**. La fenêtre demande :

- l'**emplacement** et le **dossier du projet**, qui doit être vide ;
- le **nom** et le **numéro** du projet, le **maître d'ouvrage** et l'**adresse** ;
- le **bureau**, l'**auteur** et le **vérificateur**.

Ces informations sont imprimées sur la page de titre du rapport et dans les métadonnées du PDF. Elles se changent à tout moment dans **Fichier › Propriétés du projet…**.

## Ce que contient le dossier

```text
Halle Nord/
├── Halle Nord.woodcore          le projet : c'est ce fichier qu'on ouvre
├── Statischer Bericht (typst)/  le rapport
│   ├── Statischer Rapport.typ   le document principal
│   ├── Sections/                une section par fichier
│   ├── commands.typ             toutes les commandes de Woodcore
│   └── _woodcore/               l'export et le moteur — générés, jamais modifiés à la main
├── Woodcore-Datei/              ce qu'on saisit et dessine dans Woodcore, dont les positions (étape 3)
└── _Archiv/                     un zip et une copie du PDF par export
```

Il n'y a rien d'autre à copier dans ce dossier : le vent, la neige et les charges permanentes se saisissent dans les onglets de Woodcore et s'enregistrent dans `Woodcore-Datei/loads/` (étape 4).

> [!note]
> Un projet ouvert dans une fenêtre est **verrouillé** par un fichier `Halle Nord.woodcore.lock`. Si un collègue l'ouvre en même temps, Woodcore le lui dit et propose la lecture seule : deux fenêtres qui enregistrent le même projet perdraient le travail de la première.

## Ouvrir un projet

Un double-clic sur le fichier `.woodcore`, **Ouvrir…** sur la page d'accueil, ou un fichier `.woodcore` glissé sur la fenêtre. Chaque projet s'ouvre dans sa propre fenêtre ; **Fichier › Ouvrir dans une nouvelle fenêtre…** en ouvre un deuxième à côté.
