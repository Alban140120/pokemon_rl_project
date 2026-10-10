import os
import time

import numpy as np
from PIL import Image
from pygba import PokemonEmerald, PyGBAEnv
from pygba.game_wrappers.pokemon_emerald import get_game_state

from pokemon_loader import load_gba_with_save, skip_to_game

ROM = "roms/Pokemon - Emerald Version (USA, Europe).gba"
SAV = "roms/start_save.sav"

gba = load_gba_with_save(ROM, SAV)
skip_to_game(gba)  # l'instantané initial de l'environnement est pris ICI

env = PyGBAEnv(gba, PokemonEmerald(), frameskip=23, max_episode_steps=300)

os.makedirs("diag", exist_ok=True)


def save_obs(obs, name):
    Image.fromarray(obs.transpose(1, 0, 2)).save(f"diag/{name}.png")


obs1, _ = env.reset()
save_obs(obs1, "env_1_reset")

total = 0.0
steps = 0
t0 = time.time()
for _ in range(300):
    obs, reward, terminated, truncated, info = env.step(env.action_space.sample())
    total += reward
    steps += 1
    if terminated or truncated:
        break
duree = time.time() - t0
save_obs(obs, "env_2_apres_pas")

obs2, _ = env.reset()
save_obs(obs2, "env_3_apres_reset")
etat = get_game_state(gba)

print(">>> observation :", obs1.shape, obs1.dtype)
print(">>> pixels non noirs au reset :", int((obs1.sum(axis=2) > 0).sum()))
print(f">>> {steps} pas en {duree:.1f} s ({steps / duree:.1f} pas/s) | récompense cumulée : {total}")
print(">>> reset identique à l'état initial :", bool(np.array_equal(obs1, obs2)))
print(">>> équipe après reset :", len(etat["party"]))