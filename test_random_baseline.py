import numpy as np
from pygba import PyGBAEnv

from pokemon_loader import load_gba_with_save, skip_to_game
from rewards import ExplorationEmerald

ROM = "roms/Pokemon - Emerald Version (USA, Europe).gba"
SAV = "roms/start_save.sav"

gba = load_gba_with_save(ROM, SAV)
skip_to_game(gba)
env = PyGBAEnv(gba, ExplorationEmerald(), frameskip=23, max_episode_steps=512)

rewards, tiles = [], []
for _ in range(40):
    env.reset()
    total = 0.0
    for _ in range(512):
        _, r, terminated, truncated, _ = env.step(env.action_space.sample())
        total += r
        if terminated or truncated:
            break
    rewards.append(total)
    tiles.append(len(env.game_wrapper._visited))

print(">>> aléatoire : récompense moyenne =", round(float(np.mean(rewards)), 3),
      "| écart-type =", round(float(np.std(rewards)), 3))
print(">>> aléatoire : cases visitées en moyenne =", round(float(np.mean(tiles)), 1))