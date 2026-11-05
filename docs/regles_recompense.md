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
- **Équipe adverse** : `gEnemyParty` à 0x02024744 (juste après la nôtre, même format). Vérifié sur des combats sauvages ; elle reste en mémoire après le combat.
- **Manque** : l'indicateur « en combat » et le reste de l'état de combat (attaques, boosts, tour). Adresses à chercher dans les
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

## C. Lot 1 (dans `rewards.py`)

Comme pygba, ces règles forment un score : la récompense d'un pas est sa variation. Perdre des PV
coûte, se soigner (Centre Pokémon, potion) rapporte autant.

L'expérience de pygba rapporte très peu (racine cubique × 0,1 : 20 points d'expérience ≈ 0,27) et
fuir ne coûte rien : le premier agent fuyait tous les combats. Le bonus de niveau est donc le
moteur des combats, et il doit rester plus fort que les pénalités de santé.

| Règle | Poids | Statut | Remarque |
|---|---|---|---|
| Niveau gagné | +1 par niveau | ✅ | Suivi par Pokémon (`personality`) : capturer ou déposer un Pokémon ne compte pas. |
| Évolution | +2 | ✅ | Changement d'espèce d'un même Pokémon. |
| Nouvelle carte extérieure (villes, routes : groupe 0 ; grottes, bois : groupe 24) | +1 (`--carte-ext`) | ✅ | En plus des +5 de pygba pour les 16 villes. Passer à +3 n'a rien changé : un bonus jamais atteint n'apprend rien. |
| Nouvelle carte intérieure (autres groupes) | +0,2 | ✅ | Faible, pour ne pas pousser à entrer dans chaque maison. |
| PV manquants dans l'équipe | jusqu'à −0,5 | ✅ | Proportion des PV manquants sur toute l'équipe. |
| KO | −0,5 par Pokémon | ✅ | |
| Statut (poison, sommeil…) | −0,1 par Pokémon | ✅ | Hors Pokémon KO. |
| Dégâts infligés à un adversaire | +0,5 pour ses PV entiers, au prorata | ✅ | Signal immédiat en combat. Lu dans `gEnemyParty` (0x02024744, vérifié). Par adversaire (`personality`), on garde la perte maximale : s'il se soigne, rien n'est repris ni redonné. |
| KO d'un adversaire | +1 | ✅ | |

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

## Risques connus

- **Flags de script** : pygba compte chaque *changement* de flag, dans les deux sens. Un flag qui
  bascule en boucle rapporterait +1 à l'infini. À vérifier sur les runs (récompenses anormalement
  hautes sans progression visible).
- **Pénalités de santé trop fortes** : l'agent évite les combats.
- **Bonus d'exploration** : plafonne avec la taille de la zone accessible.

## Ordre de travail

1. ~~Run de 200 000 pas avec la récompense actuelle~~ : fait. Récompense 0,62 → 6,52, Rosyères atteinte, flags de script stables (aucun basculement), mais l'agent fuit les combats.
2. Lot 1 (section C) à 512 pas par épisode, comparé au run de référence.
3. ~~Épisodes de 2 048 pas~~ : fait, l'agent combat (~15 KO, 3 à 4 niveaux par épisode) mais reste sur la Route 101.
4. Combiner combat et exploration : points de départ avancés, ou bonus d'exploration global à l'entraînement.
5. Lecture du sac, puis adresse de l'indicateur de combat.
