# Tiny Wings (Pygame)

Mini-jeu 2D développé en Python avec la bibliothèque Pygame, inspiré du gameplay du jeu Tiny Wings.

Le joueur contrôle une bille évoluant sur un terrain sinusoïdal généré procéduralement.
Le gameplay repose sur :
- la gestion de l’énergie,
- les sauts multiples,
- les obstacles (trous),
- la progression par niveaux,
- des conditions de Game Over dynamiques.

--------------------------------------------------

GAMEPLAY

- Terrain généré procéduralement (sinusoïdes + trous)
- Trois niveaux de difficulté progressifs
- Système d’énergie influençant la vitesse
- Sauts multiples (jusqu’à 3 impulsions aériennes)
- Multiplicateur de score x2 après 2 secondes consécutives en l’air
- Arrivée progressive de la nuit

--------------------------------------------------

INSTALLATION

PRÉREQUIS
- Python 3.10 ou supérieur
- pip

CRÉATION DE L’ENVIRONNEMENT VIRTUEL

    python -m venv .venv

ACTIVATION DE L’ENVIRONNEMENT

Sous Windows (PowerShell) :

    .venv\Scripts\Activate

Sous macOS / Linux :

    source .venv/bin/activate

INSTALLATION DES DÉPENDANCES

    pip install -r requirements.txt

--------------------------------------------------

LANCER LE JEU

Depuis la racine du projet :

    python src/main.py

--------------------------------------------------

CONTRÔLES

- ESPACE (tap) : saut
  - jusqu’à 3 impulsions successives en l’air
- ESPACE (maintien) : boost
  - accélération horizontale
  - consommation d’énergie
- R : redémarrer la partie après un Game Over
- ESC : quitter le jeu

--------------------------------------------------

RÈGLES DU JEU

- La vitesse horizontale augmente avec l’énergie.
- Le terrain devient plus complexe au fil des niveaux :
  - Niveau 1 : terrain simple, sans trous
  - Niveau 2 : petits trous franchissables
  - Niveau 3 : trous plus larges et plus fréquents
- Le joueur doit anticiper :
  - la position des trous,
  - la gestion de l’énergie,
  - l’arrivée progressive de la nuit.

--------------------------------------------------

CONDITIONS DE GAME OVER

La partie se termine si :
- la nuit rattrape le joueur,
- la bille tombe dans un trou,
- l’énergie reste à zéro pendant plusieurs secondes.

La cause du Game Over est affichée à l’écran.

--------------------------------------------------

TECHNOLOGIES UTILISÉES

- Python 3
- Pygame
- Programmation orientée objet
- Génération procédurale

