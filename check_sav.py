from pathlib import Path

for p in Path("roms").glob("*.sav"):
    data = p.read_bytes()
    used = sum(1 for b in data if b != 0xFF)
    print(">>>", p.name, "|", len(data), "octets |", used, "octets différents de 0xFF")