"""GIF d'un épisode joué par l'agent aléatoire et par un modèle entraîné, côte à côte.

    python -m scripts.gif_avant_apres checkpoints/ppo_exploration_200k_final.zip media/avant_apres.gif
    python -m scripts.gif_avant_apres checkpoints/x_final.zip media/combat.gif --episode 2048 --pas-par-image 6
"""
import argparse
from pathlib import Path

import mgba.log
from PIL import Image, ImageDraw
from stable_baselines3 import PPO

from train import creer_env

ECHELLE = 1


def jouer(env, choisir):
    obs, _ = env.reset()
    images, done = [], False
    while not done:
        obs, _, term, trunc, _ = env.step(choisir(obs))
        done = term or trunc
        images.append(Image.fromarray(obs.transpose(1, 0, 2)))  # (largeur, hauteur) -> image
    c = env.game_wrapper._composantes()
    return images, f"{c['cases_visitees']} cases, {c['ko_adverses']} KO, +{c['niveaux']} niv."


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("modele")
    parser.add_argument("sortie", type=Path)
    parser.add_argument("--episode", type=int, default=512, help="pas par épisode")
    parser.add_argument("--pas-par-image", type=int, default=2, help="une image tous les N pas (taille du GIF)")
    parser.add_argument("--titre", default="PPO entraine", help="légende de l'agent entraîné (ASCII)")
    args = parser.parse_args()

    mgba.log.silence()
    model = PPO.load(args.modele, device="cuda")
    env = creer_env(args.episode)

    avant, bilan_avant = jouer(env, lambda obs: env.action_space.sample())
    apres, bilan_apres = jouer(env, lambda obs: int(model.predict(obs, deterministic=False)[0]))

    l, h = avant[0].width * ECHELLE, avant[0].height * ECHELLE
    images = []
    for a, b in list(zip(avant, apres))[:: args.pas_par_image]:
        image = Image.new("RGB", (2 * l + 8, h + 24), "white")
        image.paste(a.resize((l, h), Image.NEAREST), (0, 24))
        image.paste(b.resize((l, h), Image.NEAREST), (l + 8, 24))
        dessin = ImageDraw.Draw(image)
        dessin.text((4, 6), f"Aleatoire ({bilan_avant})", fill="black")
        dessin.text((l + 12, 6), f"{args.titre} ({bilan_apres})", fill="black")
        images.append(image)

    args.sortie.parent.mkdir(parents=True, exist_ok=True)
    images[0].save(args.sortie, save_all=True, append_images=images[1:], duration=40, loop=0, optimize=True)
    print(f">>> {args.sortie} : {len(images)} images, {args.sortie.stat().st_size / 1e6:.1f} Mo")


if __name__ == "__main__":
    main()
