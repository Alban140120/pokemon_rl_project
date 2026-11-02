from pygba import PyGBA, PyGBAEnv, PokemonEmerald

rom_path = "roms/Pokemon - Emerald Version (USA, Europe).gba"

# Charge la ROM et crée le wrapper de récompense
gba = PyGBA.load(rom_path)
game_wrapper = PokemonEmerald()

# Crée l'environnement Gym standard
env = PyGBAEnv(gba, game_wrapper)

# Réinitialise l'environnement (comme au début de chaque partie)
observation, info = env.reset()
print("Forme de l'observation :", observation.shape if hasattr(observation, "shape") else type(observation))
print("Espace d'actions :", env.action_space)

# Fait jouer un agent 100% aléatoire pendant 200 pas
total_reward = 0.0
for i in range(200):
    action = env.action_space.sample()  # action aléatoire
    observation, reward, terminated, truncated, info = env.step(action)
    total_reward += reward

    if terminated or truncated:
        observation, info = env.reset()

print(f"\nTerminé : {i + 1} pas joués, récompense cumulée = {total_reward}")