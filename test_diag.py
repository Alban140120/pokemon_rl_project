from pygba import PyGBA
from pygba.game_wrappers.utils.emerald_utils import ADRESSES

gba = PyGBA.load("roms/Pokemon - Emerald Version (USA, Europe).gba")

lo = gba.read_u16(0x080000AC)
hi = gba.read_u16(0x080000AE)
code = bytes([lo & 0xFF, lo >> 8, hi & 0xFF, hi >> 8]).decode("ascii", errors="replace")
print("Code du jeu :", code)

addr = ADRESSES["sSpeciesToNationalPokedexNum"]
print("Adresse utilisée :", hex(addr))
print("10 premieres valeurs :", [gba.read_u16(addr + i * 2) for i in range(10)])