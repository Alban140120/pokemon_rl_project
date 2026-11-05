"""Entraînement PPO sur plusieurs émulateurs en parallèle (un par processus).

    python train.py                       # run complet : 200 000 pas, 8 environnements
    python train.py --pas 8192 --envs 4   # test court du montage
    python train.py --reprendre checkpoints/x_330000_steps.zip --pas 670000 --episode 2048 --nom x
"""
import argparse
import time
from functools import partial

import mgba.log
from pygba import PyGBAEnv
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import BaseCallback, CheckpointCallback
from stable_baselines3.common.vec_env import SubprocVecEnv, VecMonitor

from pokemon_loader import load_gba_with_save, skip_to_game
from rewards import SOURCES, ExplorationEmerald

ROM = "roms/Pokemon - Emerald Version (USA, Europe).gba"
SAV = "roms/start_save.sav"
PAS_PAR_EPISODE = 512
N_STEPS = 512  # pas par environnement entre deux mises à jour (lot : N_STEPS × envs)


def creer_env(pas_par_episode: int = PAS_PAR_EPISODE):
    """Appelée dans chaque processus : son émulateur, son instantané de départ, sa récompense."""
    mgba.log.silence()  # les logs d'mGBA noient la console
    gba = load_gba_with_save(ROM, SAV)
    skip_to_game(gba)  # l'instantané initial de l'environnement est pris ici
    return PyGBAEnv(gba, ExplorationEmerald(), frameskip=23, max_episode_steps=pas_par_episode)


class SourcesRecompense(BaseCallback):
    """Ajoute à TensorBoard la moyenne par épisode de chaque source de récompense (cases, cartes, niveaux...)."""

    def _on_step(self) -> bool:
        for info in self.locals["infos"]:
            if "episode" in info:
                for nom in SOURCES:
                    self.logger.record_mean(f"rollout/{nom}", info[nom])
        return True


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--pas", type=int, default=200_000, help="nombre total de pas d'entraînement")
    parser.add_argument("--envs", type=int, default=8, help="nombre d'émulateurs en parallèle")
    parser.add_argument("--nom", default="ppo_exploration", help="nom du run (TensorBoard et checkpoints)")
    parser.add_argument("--episode", type=int, default=PAS_PAR_EPISODE, help="pas par épisode")
    parser.add_argument("--checkpoint", type=int, default=10_000, help="pas entre deux checkpoints")
    # Avec 3e-4 et sans entropie (défauts de SB3), approx_kl montait à 0,2 et la politique se figeait.
    parser.add_argument("--lr", type=float, default=1e-4, help="taux d'apprentissage")
    parser.add_argument("--entropie", type=float, default=0.01, help="bonus d'entropie (ent_coef)")
    parser.add_argument("--reprendre", help="checkpoint (.zip) à partir duquel continuer ; --pas = pas en plus")
    args = parser.parse_args()

    mgba.log.silence()
    env = VecMonitor(SubprocVecEnv([partial(creer_env, args.episode)] * args.envs), info_keywords=SOURCES)

    if args.reprendre:
        # Les poids et le compteur de pas viennent du checkpoint ; la récompense est celle du code actuel.
        model = PPO.load(
            args.reprendre, env=env, device="cuda", tensorboard_log="runs",
            custom_objects={"learning_rate": args.lr, "ent_coef": args.entropie},
        )
    else:
        model = PPO(
            "CnnPolicy",
            env,
            device="cuda",
            n_steps=N_STEPS,
            batch_size=256,
            learning_rate=args.lr,
            ent_coef=args.entropie,
            tensorboard_log="runs",
            verbose=1,
        )
    checkpoints = CheckpointCallback(
        save_freq=max(args.checkpoint // args.envs, 1),  # compté par environnement
        save_path="checkpoints",
        name_prefix=args.nom,
    )

    debut = time.time()
    model.learn(
        total_timesteps=args.pas,
        callback=[checkpoints, SourcesRecompense()],
        tb_log_name=args.nom,
        reset_num_timesteps=not args.reprendre,  # en reprise, la courbe continue où elle s'était arrêtée
    )
    duree = time.time() - debut

    model.save(f"checkpoints/{args.nom}_final")
    env.close()
    print(f">>> {args.pas} pas en {duree / 60:.1f} min ({args.pas / duree:.0f} pas/s), total {model.num_timesteps}")
    print(f">>> modèle final : checkpoints/{args.nom}_final.zip")


if __name__ == "__main__":  # obligatoire sous Windows avec SubprocVecEnv
    main()
