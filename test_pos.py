from pygba.game_wrappers.pokemon_emerald import get_game_state
from pygba.game_wrappers.utils.emerald_utils import ADRESSES

from pokemon_loader import load_gba_with_save, skip_to_game

ROM = "roms/Pokemon - Emerald Version (USA, Europe).gba"
SAV = "roms/start_save.sav"

gba = load_gba_with_save(ROM, SAV)
skip_to_game(gba)

s = get_game_state(gba)
print(">>> pos :", s["pos"])
print(">>> location :", s["location"])
print(">>> lastHealLocation :", s["lastHealLocation"])

# On déplace le personnage pour voir si pos change
for nom, appui in (("bas", gba.press_down), ("bas", gba.press_down),
                   ("gauche", gba.press_left), ("gauche", gba.press_left)):
    appui(20)
    gba.wait(30)
    print(">>> après", nom, ":", get_game_state(gba)["pos"])

print(">>> adresses connues de pygba :", list(ADRESSES))