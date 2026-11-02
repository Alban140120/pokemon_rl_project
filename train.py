"""Entraînement PPO sur plusieurs émulateurs en parallèle (un par processus).

    python train.py                       # run complet : 200 000 pas, 8 environnements
    python train.py --pas 8192 --envs 4   # test court du montage
"""
import argparse
import time

import mgba.log
from pygba import PyGBAEnv
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import BaseCallback, CheckpointCallback
from stable_baselines3.common.vec_env import SubprocVecEnv, VecMonitor

from pokemon_loader import load_gba_with_save, skip_to_game
from rewards import ExplorationEmerald

ROM = "roms/Pokemon - Emerald Version (USA, Europe).gba"
SAV = "roms/start_save.sav"
PAS_PAR_EPISODE = 512


def creer_env():
    """Appelée dans chaque processus : son émulateur, son instantané de départ, sa récompense."""
    mgba.log.silence()  # les logs d'mGBA noient la console
    gba = load_gba_with_save(ROM, SAV)
    skip_to_game(gba)  # l'instantané initial de l'environnement est pris ici
    return PyGBAEnv(gba, ExplorationEmerald(), frameskip=23, max_episode_steps=PAS_PAR_EPISODE)


class CasesVisitees(BaseCallback):
    """Ajoute à TensorBoard le nombre moyen de cases visitées par épisode."""

    def _on_step(self) -> bool:
        for info in self.locals["infos"]:
            if "episode" in info:
                self.logger.record_mean("rollout/cases_visitees", info["cases_visitees"])
        return True


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--pas", type=int, default=200_000, help="nombre total de pas d'entraînement")
    parser.add_argument("--envs", type=int, default=8, help="nombre d'émulateurs en parallèle")
    parser.add_argument("--nom", default="ppo_exploration", help="nom du run (TensorBoard et checkpoints)")
    parser.add_argument("--checkpoint", type=int, default=10_000, help="pas entre deux checkpoints")
    args = parser.parse_args()

    mgba.log.silence()
    env = VecMonitor(SubprocVecEnv([creer_env] * args.envs), info_keywords=("cases_visitees",))

    model = PPO(
        "CnnPolicy",
        env,
        device="cuda",
        n_steps=PAS_PAR_EPISODE,  # lot par mise à jour : n_steps × envs
        batch_size=256,
        tensorboard_log="runs",
        verbose=1,
    )
    checkpoints = CheckpointCallback(
        save_freq=max(args.checkpoint // args.envs, 1),  # compté par environnement
        save_path="checkpoints",
        name_prefix=args.nom,
    )

    debut = time.time()
    model.learn(total_timesteps=args.pas, callback=[checkpoints, CasesVisitees()], tb_log_name=args.nom)
    duree = time.time() - debut

    model.save(f"checkpoints/{args.nom}_final")
    env.close()
    print(f">>> {model.num_timesteps} pas en {duree / 60:.1f} min ({model.num_timesteps / duree:.0f} pas/s)")
    print(f">>> modèle final : checkpoints/{args.nom}_final.zip")


if __name__ == "__main__":  # obligatoire sous Windows avec SubprocVecEnv
    main()
