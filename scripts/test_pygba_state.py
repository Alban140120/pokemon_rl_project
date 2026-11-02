from pygba import PyGBA
from pygba.game_wrappers.pokemon_emerald import get_game_state

rom_path = "roms/Pokemon - Emerald Version (USA, Europe).gba"

# Charge la ROM
gba = PyGBA.load(rom_path)

# Avance de quelques centaines de frames pour dépasser l'écran titre
for _ in range(300):
    gba.core.run_frame()

# Récupère l'état complet du jeu tel que lu par le wrapper
state = get_game_state(gba)

print("=== État du jeu ===")
for key, value in state.items():
    print(f"{key}: {value}")