"""GIF d'un épisode joué par l'agent aléatoire et par un modèle entraîné, côte à côte.

    python -m scripts.gif_avant_apres checkpoints/ppo_exploration_200k_final.zip media/avant_apres.gif
"""
import sys
from pathlib import Path

import mgba.log
from PIL import Image, ImageDraw
from stable_baselines3 import PPO

from train import creer_env

ECHELLE = 1
PAS_PAR_IMAGE = 2  # une image sur deux : GIF plus léger, ~10 s


def jouer(env, choisir):
    obs, _ = env.reset()
    images, done = [], False
    while not done:
        obs, _, term, trunc, _ = env.step(choisir(obs))
        done = term or trunc
        images.append(Image.fromarray(obs.transpose(1, 0, 2)))  # (largeur, hauteur) -> image
    return images, len(env.game_wrapper._visited)


def main():
    mgba.log.silence()
    model = PPO.load(sys.argv[1], device="cuda")
    sortie = Path(sys.argv[2])
    env = creer_env()

    avant, cases_avant = jouer(env, lambda obs: env.action_space.sample())
    apres, cases_apres = jouer(env, lambda obs: int(model.predict(obs, deterministic=False)[0]))

    l, h = avant[0].width * ECHELLE, avant[0].height * ECHELLE
    images = []
    for a, b in list(zip(avant, apres))[::PAS_PAR_IMAGE]:
        image = Image.new("RGB", (2 * l + 8, h + 24), "white")
        image.paste(a.resize((l, h), Image.NEAREST), (0, 24))
        image.paste(b.resize((l, h), Image.NEAREST), (l + 8, 24))
        dessin = ImageDraw.Draw(image)
        dessin.text((4, 6), f"Agent aleatoire ({cases_avant} cases)", fill="black")
        dessin.text((l + 12, 6), f"PPO apres 200 000 pas ({cases_apres} cases)", fill="black")
        images.append(image)

    sortie.parent.mkdir(parents=True, exist_ok=True)
    images[0].save(sortie, save_all=True, append_images=images[1:], duration=40, loop=0, optimize=True)
    print(f">>> {sortie} : {len(images)} images, {sortie.stat().st_size / 1e6:.1f} Mo")


if __name__ == "__main__":
    main()
