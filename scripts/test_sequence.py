import os

from pokemon_loader import load_gba_with_save

ROM = "roms/Pokemon - Emerald Version (USA, Europe).gba"
SAV = "roms/start_save.sav"

gba = load_gba_with_save(ROM, SAV)
os.makedirs("diag", exist_ok=True)


def snap(name):
    gba.screen.to_pil().convert("RGB").save(f"diag/{name}.png")


gba.wait(2000)
snap("s1_apres_intro")

gba.press_start(10)
gba.wait(180)
snap("s2_apres_start")

gba.press_a(10)
gba.wait(240)
snap("s3_apres_a1")

gba.press_a(10)
gba.wait(400)
snap("s4_apres_a2")

gba.press_a(10)
gba.wait(400)
snap("s5_apres_a3")

print(">>> captures terminées")