import mgba.core
import mgba.image

core = mgba.core.load_path("roms/Pokemon - Emerald Version (USA, Europe).gba")
screen = mgba.image.Image(*core.desired_video_dimensions())
core.set_video_buffer(screen)
core.reset()

for _ in range(1500):
    core.run_frame()

print(">>> méthodes liées aux sauvegardes :", [m for m in dir(core) if "save" in m.lower()])