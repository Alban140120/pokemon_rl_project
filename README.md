# Pokémon Émeraude : apprentissage par renforcement

Un agent entraîné **de zéro** par apprentissage par renforcement (PPO) à jouer à Pokémon Émeraude (GBA), piloté depuis Python via l'émulateur mGBA, sur GPU.

> **Statut : projet en cours.** L'infrastructure complète est en place et validée (émulation, lecture de la mémoire du jeu, environnement Gymnasium, entraînement PPO sur GPU). L'agent n'a pas encore démontré d'apprentissage : voir la section [Résultats](#résultats).

## Objectif

Obtenir un comportement cohérent (explorer, combattre, gagner des niveaux) à partir d'une fonction de récompense écrite à la main, sans aucune connaissance préalable du jeu. Finir le jeu n'est pas l'objectif.

L'intérêt du projet est autant dans la conception de la récompense (*reward shaping*) que dans l'ingénierie qui l'entoure : compilation d'un émulateur depuis les sources, lecture de la RAM du jeu, environnement reproductible, entraînement sur GPU.

## Architecture

```
ROM + sauvegarde ──► mGBA (bindings Python) ──► pygba ──► Gymnasium (PyGBAEnv)
                          │                        │              │
                          │                        └── lecture de la RAM (équipe, position, badges...)
                          │                                       │
                          └── instantané mémoire (reset rapide)   ▼
                                                      Stable-Baselines3 (PPO, CnnPolicy, GPU)
```

| Fichier | Rôle |
|---|---|
| `pokemon_loader.py` | Charge la ROM et la sauvegarde, puis passe l'intro jusqu'au point de départ |
| `rewards.py` | Fonction de récompense : base de pygba + bonus d'exploration |
| `train.py` | Entraînement PPO avec checkpoints et suivi TensorBoard |
| `train_test.py` | Test court de l'entraînement (vérification du montage) |
| `test_*.py` | Scripts de validation : état du jeu, instantanés, environnement, ligne de base aléatoire |

### Choix de conception

- **Observation** : l'écran du jeu, image `(240, 160, 3)`.
- **Actions** : 35 actions discrètes (5 choix de flèche × 7 choix de bouton, combinables).
- **Un pas = 24 frames** (`frameskip=23`), ce qui est suffisant pour qu'une action ait un effet visible dans le jeu.
- **Point de départ fixe** : on joue l'intro une fois, puis chaque épisode repart d'un **instantané de l'émulateur en mémoire** (`save_raw_state` / `load_raw_state`). Le reset est instantané au lieu de rejouer ~3000 frames d'intro.
- **Récompense** : la récompense de base de pygba (badges, Pokédex, dresseurs battus, expérience, événements de scénario) plus un bonus de 0,01 par case nouvellement visitée.

## Installation (Windows)

Testé avec Python 3.11, une RTX 5070 Ti et Windows.

### 1. Environnement Python

```powershell
python -m venv venv
venv\Scripts\activate
```

La RTX 50xx (architecture Blackwell) demande une version récente de PyTorch. J'ai utilisé un build **nightly CUDA 12.8** :

```powershell
pip install --pre torch --index-url https://download.pytorch.org/whl/nightly/cu128
pip install gymnasium stable-baselines3 tensorboard pillow cffi pygba
```

### 2. mGBA avec bindings Python

Le paquet `mgba` n'est pas disponible en roue pour Windows : il faut compiler **mGBA depuis les sources**. J'ai utilisé le fork [`hanzi/libmgba-py`](https://github.com/hanzi/libmgba-py) avec Visual Studio (charge de travail « Développement Desktop en C++ »), CMake et vcpkg (géré par le script du fork).

Points qui m'ont coûté du temps :

- **Compiler sur un disque NTFS.** Sur un SSD externe en exFAT, l'extraction des archives de vcpkg échoue (`Can't restore time`).
- **CMake 4.x** refuse certains projets anciens : définir `CMAKE_POLICY_VERSION_MINIMUM=3.5` avant de lancer le script.
- **FFmpeg** (version trop récente) est incompatible avec mGBA 0.10.2 : ajouter `-DUSE_FFMPEG=OFF` à la ligne `cmake` de `build_win64.bat`.
- **Lua** (version trop récente) provoque des erreurs de liaison : ajouter `-DENABLE_SCRIPTING=OFF`.
- Après le build, copier `build\win64\mgba` dans le projet et installer `cffi` (module `_cffi_backend`).

Les fichiers `.dll` et `.pyd` produits sont ignorés par Git (`.gitignore`) : ils se régénèrent avec le script de build.

### 3. ROM et sauvegarde

Aucune ROM n'est fournie dans ce dépôt. Il faut disposer de sa propre copie du jeu.

- **La version USA (code `BPEE`) est nécessaire.** Les adresses mémoire utilisées par pygba sont celles de cette version : avec la version française (`BPEF`), la lecture de la mémoire plante.
- Placer la ROM dans `roms/`.
- Créer une sauvegarde de départ en jouant dans mGBA (choix du starter, puis sauvegarde **dans le jeu**, pas un *save state*), et la copier sous `roms/start_save.sav`.

Ne pas commiter ces fichiers : `*.gba` et `*.sav` sont déjà dans le `.gitignore`.

## Utilisation

```powershell
venv\Scripts\activate

# Vérifier la ligne de base d'un agent aléatoire (~7 min)
python test_random_baseline.py

# Entraînement PPO (checkpoints dans checkpoints/, courbes dans runs/)
python train.py

# Suivre l'entraînement dans un second terminal
tensorboard --logdir runs
```

Les logs verbeux d'mGBA remplissent la console : pour garder une trace exploitable, rediriger la sortie (`python train.py > sortie.txt 2>&1`) et filtrer ensuite avec `Select-String`.

## Résultats

Mesures sur un seul environnement, avec la récompense d'exploration :

| Mesure | Valeur |
|---|---|
| Vitesse d'entraînement | ~58 pas/s (PPO sur GPU inclus) |
| Agent **aléatoire**, 40 épisodes de 512 pas | récompense moyenne 0,609 ± 0,226, soit ~62 cases visitées |
| PPO, 20 480 pas (~40 épisodes) | récompense moyenne finale 0,67 |

**Lecture honnête de ces chiffres :** l'écart entre PPO (0,67) et la ligne de base aléatoire (0,61) est du même ordre que l'incertitude des mesures. À ce stade, rien ne permet d'affirmer que l'agent apprend. Un run de 200 000 pas est prévu pour trancher.

_À compléter : résultat du run de 200 000 pas (courbe `rollout/ep_rew_mean` de TensorBoard)._

## Problèmes rencontrés et enseignements

- **Version de la ROM.** Le wrapper pygba plantait sur la ROM française. Un diagnostic simple (lecture du code du jeu dans l'en-tête et d'une table connue en ROM) a confirmé que les adresses étaient celles de la version USA.
- **Chargement de la sauvegarde.** `autoload_save()` retournait `False` dans ma compilation de mGBA. Contournement : charger le fichier explicitement avec `core.load_save(vfile)` (voir `pokemon_loader.py`).
- **Captures d'écran.** La fonction `save_png` du fork est cassée (incohérence d'arguments avec la bibliothèque C). Contournement : `to_pil()` puis conversion en RGB avant d'enregistrer avec Pillow.
- **Récompense rare.** Sans signal, PPO n'apprend rien : d'où le bonus d'exploration. Il plafonne cependant avec la taille de la zone accessible.

## Feuille de route

- [x] Environnement GPU (PyTorch nightly CUDA 12.8)
- [x] Compilation de mGBA et bindings Python
- [x] Lecture de l'état du jeu (équipe, position, badges, Pokédex)
- [x] Environnement Gymnasium avec reset instantané
- [x] Ligne de base aléatoire
- [x] Premier entraînement PPO (sans preuve d'apprentissage)
- [ ] Run de 200 000 pas avec suivi TensorBoard
- [ ] Récompenses plus riches : expérience, franchissement de portes, niveaux gagnés, KO et statuts
- [ ] Lecture du sac et de l'état de combat (adresses mémoire à identifier)
- [ ] Plusieurs environnements en parallèle (un émulateur par processus)
- [ ] GIF avant/après entraînement

## Remerciements

- [mGBA](https://mgba.io/) pour l'émulateur et [`hanzi/libmgba-py`](https://github.com/hanzi/libmgba-py) pour les bindings Python.
- [`dvruette/pygba`](https://github.com/dvruette/pygba) pour le wrapper Gymnasium et la lecture de la mémoire de Pokémon Émeraude.
- [Stable-Baselines3](https://github.com/DLR-RM/stable-baselines3) et [Gymnasium](https://gymnasium.farama.org/).
- Projet inspiré par les travaux de Peter Whidden sur l'apprentissage par renforcement appliqué à Pokémon.

Pokémon est une marque de Nintendo, Game Freak et Creatures Inc. Ce projet est un travail personnel sans lien avec ces sociétés.
