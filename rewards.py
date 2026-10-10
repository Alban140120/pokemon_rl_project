from pygba import PokemonEmerald


class ExplorationEmerald(PokemonEmerald):
    """Récompense de base de pygba + bonus pour chaque nouvelle case visitée."""

    def __init__(self, exploration_reward: float = 0.01, **kwargs):
        super().__init__(**kwargs)
        self.exploration_reward = exploration_reward
        self._visited = set()

    def _tile_key(self):
        state = self._game_state
        pos = state.get("pos")
        loc = state.get("location")
        if not pos or not loc:
            return None
        return (loc["mapGroup"], loc["mapNum"], pos["x"], pos["y"])

    def reward(self, gba, observation):
        base = super().reward(gba, observation)
        if observation is None:  # appel interne du reset : pas de bonus
            return base
        key = self._tile_key()
        if key is not None and key not in self._visited:
            self._visited.add(key)
            return base + self.exploration_reward
        return base

    def reset(self, gba):
        super().reset(gba)
        self._visited = set()
        key = self._tile_key()
        if key is not None:
            self._visited.add(key)  # la case de départ ne rapporte rien