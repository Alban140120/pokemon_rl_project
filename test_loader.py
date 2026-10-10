import os

from pygba.game_wrappers.pokemon_emerald import get_game_state

from pokemon_loader import load_gba_with_save, skip_to_game

ROM = "roms/Pokemon - Emerald Version (USA, Europe).gba"
SAV = "roms/start_save.sav"

# Charge la ROM et la sauvegarde
gba = load_gba_with_save(ROM, SAV)

# Buffer vidéo pour pouvoir faire une capture d'écran

# Intro -> CONTINUE -> jeu
skip_to_game(gba)

# Capture d'écran
os.makedirs("diag", exist_ok=True)
gba.screen.to_pil().convert("RGB").save("diag/loader_jeu.png")

# Lecture de l'état du jeu
state = get_game_state(gba)
print(">>> Taille de l'équipe :", len(state["party"]))
for pokemon in state["party"]:
    print(">>>", pokemon["box"]["nickname"], "| niveau", pokemon["level"],
          "| PV", pokemon["hp"], "/", pokemon["maxHp"])
print(">>> Badges :", state["badges"])