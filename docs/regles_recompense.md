# Règles de récompense : feuille de route

Liste de toutes les idées de *reward shaping*, avec leur statut. On ajoute les règles une ou deux à
la fois, et chaque ajout est comparé au run précédent : sinon, impossible de savoir ce qui aide.

| Statut | Signification |
|---|---|
| ✅ Fait | Dans la récompense actuelle |
| 🟢 Faisable | Lisible dès aujourd'hui avec pygba |
| 🟡 RAM | Demande une adresse mémoire à trouver (indicateur de combat…) |
| ⏸️ Reporté | Faisable, mais inutile ou risqué à ce stade |
| ❌ Abandonné | Mauvais signal d'apprentissage ou impossible |

## Ce que pygba lit déjà

- **Équipe** (`party`) : espèce, niveau, PV, statut, EVs, IVs, Pokérus, expérience.
- **Position** : `location` (mapGroup, mapNum) et `pos` (x, y).
- **Progression** : badges, villes visitées, arènes et Conseil 4 battus, champion, flags de script et
  de dresseurs, Pokédex (vus / capturés), argent, Pokémon du PC.
- **Sac** : lisible avec `read_save_block_1(gba, parse_items=True)` (objets, objets rares, Balls,
  CT/CS, baies), mais pas lu par défaut.
- **Manque** : l'indicateur « en combat » et tout l'état de combat. Adresses à chercher dans les
  symboles de la décompilation [pokeemerald](https://github.com/pret/pokeemerald) (version USA).

## Prérequis : l'horizon

Un épisode dure 512 pas (~3 minutes de jeu) et repart toujours juste après le choix du starter.
Tant que c'est le cas, l'agent ne voit jamais les règles lointaines (Master Ball, Vol, Ligue…),
quelle que soit leur valeur. À faire avant d'empiler les règles :

1. **Épisodes plus longs** (plusieurs milliers de pas).
2. **Points de départ plus avancés** : reprendre depuis des états déjà atteints (après le premier
   badge, etc.).

## A. Récompense de base de pygba (`PokemonEmerald`)

pygba calcule un score cumulé et renvoie à chaque pas la **différence** avec le pas précédent. Une
pénalité exprimée comme un score (ex. PV manquants) récompense donc naturellement le retour à la
normale (se soigner).

| Règle | Poids | Statut |
|---|---|---|
| Badge obtenu | +10 | ✅ |
| Champion de la Ligue | +100 | ✅ |
| Ville visitée | +5 | ✅ |
| Pokémon vu / capturé | +0,2 / +1 | ✅ |
| Dresseur battu | +1 | ✅ |
| Flag de script (événement de scénario) | +1 | ✅ ⚠️ voir risques |
| Expérience gagnée | racine cubique × 0,1 | ✅ |
| Argent | 0 (désactivé) | ✅ |

## B. Ajouté par nous

| Règle | Poids | Statut |
|---|---|---|
| Exploration : case nouvelle (clé mapGroup, mapNum, x, y) | +0,01 | ✅ `rewards.py` |

## C. Lot 1 : faisable tout de suite

| Règle | Statut | Remarque |
|---|---|---|
| Santé de l'équipe (PV bas, KO, soigner avant un KO total) | 🟢 | Un seul terme : pénalité sur les PV manquants et les KO. **Doit rester petit face à l'expérience**, sinon l'agent apprend à fuir tous les combats. |
| Statut (poison, sommeil…) | 🟢 | Petite pénalité. |
| Évolution | 🟢 | Petit bonus, sans risque. |
| Niveau gagné | 🟢 | Déjà largement couvert par l'expérience : petit bonus au plus, sinon doublon. |
| Portes franchies / nouvelles cartes | 🟢 | Bonus par nouvelle carte (mapGroup, mapNum), en plus des cases. |

## D. Plus tard

| Règle | Statut | Remarque |
|---|---|---|
| Objets ramassés | 🟢 | Lecture du sac. |
| Potions, repousses (usage) | 🟢 / 🟡 | Possession lisible ; usage pertinent seulement hors/en combat. Tension repousses ↔ rencontres. |
| Balls possédées / utilisées | 🟢 / 🟡 | Possession lisible ; utilisation demande l'état de combat. |
| Diversité des types de l'équipe | 🟢 | Types lisibles via les infos d'espèce. |
| Diversité des stats par niveau | 🟢 | À définir précisément. |
| PV pas au maximum **hors combat** | 🟡 | Indicateur de combat. |
| Efficacité des attaques, coups critiques | 🟡 | État de combat. |
| Boosts de stats en combat | 🟡 | État de combat. |
| Choix de la Ball selon le contexte (Sombre Ball en grotte/nuit, Rapide Ball au tour 1, statut ou PV bas avant capture, Master Ball sur un légendaire) | 🟡 | État de combat + sac. Légendaire à emplacement fixe : apprenable. |
| Vélo, Flash, Vol | 🟢 / 🟡 | Possession lisible (objets rares, CS) ; usage à détecter. Pertinent seulement avec un horizon long. |
| Avancer dans les dialogues, parler aux PNJ | ✅ en partie | Couvert en partie par les flags de script. |

## E. Reporté ou abandonné

| Règle | Statut | Raison |
|---|---|---|
| Pokérus | ❌ | Purement aléatoire : mauvais signal (comme les chromatiques). |
| Capture d'un chromatique | ❌ | Trop rare et aléatoire. |
| « Capturer le Pokémon d'un dresseur » | ❌ | Impossible dans le jeu. |
| Pénalité « empêcher l'évolution » | ❌ | Trop de nuance, peu de gain. |
| Sauvegarder régulièrement | ❌ | Inutile : chaque épisode repart d'un instantané en mémoire. |
| Maximisation des EVs | ⏸️ | Pousse à farmer au lieu d'avancer. |
| Argent trop élevé | ⏸️ | Idem. |
| Comparaison équipe vs PC | ⏸️ | Complexe pour un gain incertain. |
| Tour de combat, étoiles de la carte de dresseur | ⏸️ | Contenu d'après la Ligue. |
| Règle « F… » | ? | Coupée dans le résumé de la conversation d'origine. |

## Risques connus

- **Flags de script** : pygba compte chaque *changement* de flag, dans les deux sens. Un flag qui
  bascule en boucle rapporterait +1 à l'infini. À vérifier sur les runs (récompenses anormalement
  hautes sans progression visible).
- **Pénalités de santé trop fortes** : l'agent évite les combats.
- **Bonus d'exploration** : plafonne avec la taille de la zone accessible.

## Ordre de travail

1. Run de 200 000 pas avec la récompense actuelle : point de comparaison.
2. Allonger l'horizon (épisodes longs, puis points de départ avancés).
3. Lot 1 (section C), une ou deux règles par run.
4. Lecture du sac, puis adresse de l'indicateur de combat.
