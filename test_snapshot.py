import inspect
import os
import time

from PIL import ImageChops

from pokemon_loader import load_gba_with_save, skip_to_game

ROM = "roms/Pokemon - Emerald Version (USA, Europe).gba"
SAV = "roms/start_save.sav"

gba = load_gba_with_save(ROM, SAV)
skip_to_game(gba)
os.makedirs("diag", exist_ok=True)


def screenshot():
    return gba.screen.to_pil().convert("RGB").copy()


# Instantané de l'état de l'émulateur
t0 = time.time()
snapshot = gba.core.save_raw_state()
t_save = time.time() - t0
avant = screenshot()
avant.save("diag/snap_1_avant.png")

# On joue un peu pour changer l'état du jeu
for _ in range(4):
    gba.press_down(10)
    gba.wait(30)
for _ in range(3):
    gba.press_a(10)
    gba.wait(60)
apres = screenshot()
apres.save("diag/snap_2_apres_actions.png")

# Restauration
t0 = time.time()
resultat = gba.core.load_raw_state(snapshot)
t_load = time.time() - t0
gba.wait(2)
restaure = screenshot()
restaure.save("diag/snap_3_restaure.png")

# Affichés en dernier, pour ne pas être noyés dans les logs
print(">>> signature save_raw_state :", inspect.signature(gba.core.save_raw_state))
print(">>> signature load_raw_state :", inspect.signature(gba.core.load_raw_state))
print(">>> type de l'instantané :", type(snapshot), "| taille :", len(snapshot))
print(f">>> sauvegarde : {t_save:.4f} s | restauration : {t_load:.4f} s")
print(">>> load_raw_state a retourné :", resultat)
print(">>> les actions ont changé l'écran :", ImageChops.difference(avant, apres).getbbox() is not None)
print(">>> écran restauré identique à l'original :", ImageChops.difference(avant, restaure).getbbox() is None)