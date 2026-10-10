import mgba.core
import mgba.image

# Charge la ROM
core = mgba.core.load_path("roms/Pokemon - Version Emeraude (France).gba")

# Crée un buffer d'image aux bonnes dimensions pour ce jeu
screen = mgba.image.Image(*core.desired_video_dimensions())
core.set_video_buffer(screen)

# Réinitialise et fait avancer l'émulation de quelques centaines de frames
core.reset()
for i in range(300):
    core.run_frame()

# Convertit en image Pillow, corrige le mode couleur, puis sauvegarde
pil_image = screen.to_pil()
pil_image = pil_image.convert("RGB")
pil_image.save("test_screenshot.png")

print("Capture d'écran réussie ! Regarde test_screenshot.png")