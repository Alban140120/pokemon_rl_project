import struct

from pygba import PokemonEmerald
from pygba.game_wrappers.utils.emerald_utils import NUM_SPECIES, Pokemon_format, parse_pokemon

# Groupes de cartes de pokeemerald : 0 = villes et routes, 24 = grottes et bois.
# Les autres groupes sont des intérieurs (maisons, centres, magasins, arènes...).
GROUPES_EXTERIEURS = {0, 24}

# Équipe adverse : juste après la nôtre en RAM (gPlayerParty + 6 × 100 octets), même format.
# Vérifié sur des combats sauvages des Routes 101 à 103. Elle reste en mémoire après le combat.
ADRESSE_EQUIPE_ADVERSE = 0x02024744
TAILLE_POKEMON = struct.calcsize(Pokemon_format)

# Sources tracées dans TensorBoard (rollout/<nom>), valeur en fin d'épisode.
SOURCES = (
    "cases_visitees", "cartes_ext", "cartes_int", "niveaux", "evolutions",
    "degats", "ko_adverses", "ko", "statuts", "pv",
)


class ExplorationEmerald(PokemonEmerald):
    """Récompense de base de pygba + règles maison (exploration, cartes, niveaux, santé...).

    Comme pygba, nos règles forment un score et la récompense d'un pas est la variation de ce
    score : perdre des PV coûte, se soigner rapporte autant. Voir docs/regles_recompense.md.
    """

    def __init__(
        self,
        exploration_reward: float = 0.01,
        carte_ext_reward: float = 1.0,
        carte_int_reward: float = 0.2,
        niveau_reward: float = 1.0,
        evolution_reward: float = 2.0,
        pv_penalite: float = 0.5,
        ko_penalite: float = 0.5,
        statut_penalite: float = 0.1,
        degats_reward: float = 0.5,
        ko_adverse_reward: float = 1.0,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.exploration_reward = exploration_reward
        self.carte_ext_reward = carte_ext_reward
        self.carte_int_reward = carte_int_reward
        self.niveau_reward = niveau_reward
        self.evolution_reward = evolution_reward
        self.pv_penalite = pv_penalite
        self.ko_penalite = ko_penalite
        self.statut_penalite = statut_penalite
        self.degats_reward = degats_reward
        self.ko_adverse_reward = ko_adverse_reward
        self._init_suivi()

    def _init_suivi(self):
        self._visited = set()
        self._cartes = set()
        self._niveau_initial = {}  # personality -> niveau à la première rencontre
        self._niveau_max = {}
        self._especes = {}  # personality -> espèce actuelle
        self._evolutions = 0
        self._degats = {}  # personality de l'adversaire -> part maximale de ses PV retirée
        self._sante = {"ko": 0, "statuts": 0, "pv": 0.0}
        self._score_prec = 0.0

    def _tile_key(self):
        state = self._game_state
        pos = state.get("pos")
        loc = state.get("location")
        if not pos or not loc:
            return None
        return (loc["mapGroup"], loc["mapNum"], pos["x"], pos["y"])

    def _lire_adversaires(self, gba):
        for i in range(6):
            p = parse_pokemon(gba.read_memory(ADRESSE_EQUIPE_ADVERSE + i * TAILLE_POKEMON, TAILLE_POKEMON))
            if p["box"] and p["maxHp"] > 0 and p["hp"] <= p["maxHp"]:
                ident = p["box"]["personality"]
                perte = 1 - p["hp"] / p["maxHp"]
                self._degats[ident] = max(self._degats.get(ident, 0.0), perte)

    def _mettre_a_jour(self, gba):
        """Lit l'état du jeu (déjà rafraîchi par pygba) et met à jour les compteurs."""
        self._lire_adversaires(gba)
        state = self._game_state
        key = self._tile_key()
        if key is not None:
            self._visited.add(key)
            self._cartes.add(key[:2])

        equipe = [p for p in state.get("party", []) if p.get("box")]
        # Lecture pendant que le jeu réécrit l'équipe (évolution...) : espèce invalide, on ignore ce pas
        # pour ne pas compter une fausse évolution.
        if any(not 0 < p["box"]["substructs"][0]["species"] < NUM_SPECIES for p in equipe):
            return
        for p in equipe:
            ident = p["box"]["personality"]
            espece = p["box"]["substructs"][0]["species"]
            self._niveau_initial.setdefault(ident, p["level"])
            self._niveau_max[ident] = max(self._niveau_max.get(ident, 0), p["level"])
            if ident in self._especes and self._especes[ident] != espece:
                self._evolutions += 1
            self._especes[ident] = espece

        if equipe:
            pv, pv_max = sum(p["hp"] for p in equipe), sum(p["maxHp"] for p in equipe)
            self._sante = {
                "ko": sum(p["hp"] == 0 for p in equipe),
                "statuts": sum(p["status"] != 0 and p["hp"] > 0 for p in equipe),
                "pv": 1 - pv / pv_max if pv_max else 0.0,  # part des PV manquants
            }

    def _composantes(self):
        exterieures = sum(g in GROUPES_EXTERIEURS for g, _ in self._cartes)
        return {
            "cases_visitees": len(self._visited),
            "cartes_ext": exterieures,
            "cartes_int": len(self._cartes) - exterieures,
            "niveaux": sum(self._niveau_max[i] - self._niveau_initial[i] for i in self._niveau_max),
            "evolutions": self._evolutions,
            "degats": sum(self._degats.values()),  # en « Pokémon adverses entiers »
            "ko_adverses": sum(d >= 1 for d in self._degats.values()),
            **self._sante,
        }

    def _score(self):
        c = self._composantes()
        return (
            c["cases_visitees"] * self.exploration_reward
            + c["cartes_ext"] * self.carte_ext_reward
            + c["cartes_int"] * self.carte_int_reward
            + c["niveaux"] * self.niveau_reward
            + c["evolutions"] * self.evolution_reward
            + c["degats"] * self.degats_reward
            + c["ko_adverses"] * self.ko_adverse_reward
            - c["pv"] * self.pv_penalite
            - c["ko"] * self.ko_penalite
            - c["statuts"] * self.statut_penalite
        )

    def reward(self, gba, observation):
        try:
            base = super().reward(gba, observation)
        except IndexError:
            # Même cause côté pygba (espèce invalide -> plantage de l'émulateur et du run) : pas ignoré.
            return 0.0
        # Appel interne du reset, ou écran noir de chargement (état du jeu peu fiable) : on attend.
        if observation is None or observation.sum() < 1:
            return base
        self._mettre_a_jour(gba)
        score = self._score()
        bonus, self._score_prec = score - self._score_prec, score
        return base + bonus

    def reset(self, gba):
        super().reset(gba)
        self._init_suivi()
        self._mettre_a_jour(gba)  # l'adversaire resté en mémoire au départ ne rapporte rien
        self._score_prec = self._score()  # score de départ : case, carte et équipe initiales ne rapportent rien

    def info(self, gba, observation):
        # pygba renvoie tout l'état du jeu (boîtes du PC comprises) : trop lourd à
        # faire transiter entre processus à chaque pas avec SubprocVecEnv.
        return self._composantes()
