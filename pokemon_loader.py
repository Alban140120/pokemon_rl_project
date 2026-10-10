import tempfile
from pathlib import Path
import mgba.image
import mgba.core
import mgba.vfs
from pygba import PyGBA


def load_gba_with_save(rom_path: str, save_path: str) -> PyGBA:
    """Charge la ROM et la sauvegarde explicitement (autoload_save ne marche pas ici)."""
    tmp_dir = Path(tempfile.mkdtemp())
    tmp_gba = tmp_dir / "rom.gba"
    tmp_sav = tmp_dir / "rom.sav"
    tmp_gba.write_bytes(Path(rom_path).read_bytes())
    tmp_sav.write_bytes(Path(save_path).read_bytes())

    core = mgba.core.load_path(str(tmp_gba))
    if core is None:
        raise ValueError(f"Impossible de charger la ROM : {rom_path}")

    vfile = None
    for mode in ("r+", "rb+", "r"):
        try:
            vfile = mgba.vfs.open_path(str(tmp_sav), mode)
            if core.load_save(vfile):
                break
        except Exception:
            continue
    else:
        raise RuntimeError("La sauvegarde n'a pas pu être chargée")

        # Le buffer vidéo doit être branché AVANT le reset
    screen = mgba.image.Image(*core.desired_video_dimensions())
    core.set_video_buffer(screen)

    core.reset()
    gba = PyGBA(core)
    gba._save_vfile = vfile  # garde une référence pour éviter qu'elle soit fermée
    gba.screen = screen      # accessible ensuite pour les captures d'écran
    return gba


def skip_to_game(gba: PyGBA) -> None:
    """Intro -> titre -> CONTINUE -> écran de reprise -> jeu."""
    gba.wait(2000)
    gba.press_start(10)
    gba.wait(180)
    gba.press_a(10)
    gba.wait(240)
    gba.press_a(10)
    gba.wait(400)
    gba.press_a(10)
    gba.wait(400)