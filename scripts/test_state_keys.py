from pygba.game_wrappers.pokemon_emerald import get_game_state

from pokemon_loader import load_gba_with_save, skip_to_game

ROM = "roms/Pokemon - Emerald Version (USA, Europe).gba"
SAV = "roms/start_save.sav"

gba = load_gba_with_save(ROM, SAV)
skip_to_game(gba)
state = get_game_state(gba)

for key, value in state.items():
    if isinstance(value, (int, float, bool, str)):
        print(">>>", key, "=", value)
    elif hasattr(value, "__len__"):
        print(">>>", key, "->", type(value).__name__, "de taille", len(value))
    else:
        print(">>>", key, "->", type(value).__name__)