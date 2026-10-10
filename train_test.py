from pygba import PokemonEmerald, PyGBAEnv
from stable_baselines3 import PPO
from rewards import ExplorationEmerald

from pokemon_loader import load_gba_with_save, skip_to_game

ROM = "roms/Pokemon - Emerald Version (USA, Europe).gba"
SAV = "roms/start_save.sav"

gba = load_gba_with_save(ROM, SAV)
skip_to_game(gba)  # l'état initial de l'environnement est pris ici

env = PyGBAEnv(gba, ExplorationEmerald(), frameskip=23, max_episode_steps=512)

model = PPO(
    "CnnPolicy",
    env,
    device="cuda",
    n_steps=512,
    batch_size=64,
    verbose=1,
)

model.learn(total_timesteps=20480)  # 10 mises à jour, quelques minutes
print(">>> entraînement terminé sans erreur")
print(">>> device :", model.device)
print(">>> cases visitées au dernier épisode :", len(env.game_wrapper._visited))