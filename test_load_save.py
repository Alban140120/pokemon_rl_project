import inspect
import os
import tempfile
from pathlib import Path

import mgba.core
import mgba.image
import mgba.vfs
from pygba import PyGBA
from pygba.game_wrappers.pokemon_emerald import get_game_state

ROM = "roms/Pokemon - Emerald Version (USA, Europe).gba"
SAV = "roms/start_save.sav"

# Copies temporaires, comme le fait PyGBA.load
tmp_dir = Path(tempfile.mkdtemp())
tmp_gba = tmp_dir / "rom.gba"
tmp_sav = tmp_dir / "rom.sav"
tmp_gba.write_bytes(Path(ROM).read_bytes())
tmp_sav.write_bytes(Path(SAV).read_bytes())

core = mgba.core.load_path(str(tmp_gba))

# Chargement explicite de la sauvegarde, AVANT le reset
vf = None
result = None
for mode in ("r+", "rb+", "r"):
    try:
        vf = mgba.vfs.open_path(str(tmp_sav), mode)
        result = core.load_save(vf)
        print(">>> load_save avec le mode", repr(mode), "->", result)
        if result:
            break
    except Exception as e:
        print(">>> échec mode", repr(mode), ":", repr(e))

screen = mgba.image.Image(*core.desired_video_dimensions())
core.set_video_buffer(screen)
core.reset()

gba = PyGBA(core)
os.makedirs("diag", exist_ok=True)

gba.wait(1500)
gba.press_start(10)
gba.wait(90)
screen.to_pil().convert("RGB").save("diag/1_menu.png")

gba.press_a(10)
gba.wait(120)
screen.to_pil().convert("RGB").save("diag/2_recap.png")

gba.press_a(10)
gba.wait(300)
screen.to_pil().convert("RGB").save("diag/3_jeu.png")

state = get_game_state(gba)

print(">>> signature load_save :", inspect.signature(core.load_save))
print(">>> signature open_path :", inspect.signature(mgba.vfs.open_path))
print(">>> Taille de l'équipe :", len(state["party"]))
print(">>> Équipe :", state["party"])