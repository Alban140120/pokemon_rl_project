"""Joue quelques épisodes avec un modèle entraîné et décompose la récompense par source.

    python -m scripts.decomposer_recompense checkpoints/ppo_exploration_200k_final.zip
"""
import sys
from collections import Counter

import mgba.log
import numpy as np
from stable_baselines3 import PPO

from pygba.game_wrappers.pokemon_emerald import count_changed_flags, count_flags
from train import creer_env

EPISODES = 3


def composantes(wrapper, etat_depart):
    """Ce que chaque source a rapporté depuis le début de l'épisode (poids de pygba appliqués)."""
    s = wrapper._game_state
    return {
        "flags de script": wrapper._total_script_flags * wrapper.event_reward,
        "dresseurs battus": (count_flags(s.get("trainer_flags")) - count_flags(etat_depart.get("trainer_flags")))
        * wrapper.trainer_beat_reward,
        "pokémon vus": (s.get("num_seen_pokemon", 0) - etat_depart.get("num_seen_pokemon", 0))
        * wrapper.seen_pokemon_reward,
        "pokémon capturés": (s.get("num_caught_pokemon", 0) - etat_depart.get("num_caught_pokemon", 0))
        * wrapper.caught_pokemon_reward,
        "villes": (sum(s.get("visited_cities", {}).values()) - sum(etat_depart.get("visited_cities", {}).values()))
        * wrapper.visit_city_reward,
        "badges": (s.get("num_badges", 0) - etat_depart.get("num_badges", 0)) * wrapper.badge_reward,
        "exploration": (len(wrapper._visited) - 1) * wrapper.exploration_reward,
    }


def main():
    mgba.log.silence()
    model = PPO.load(sys.argv[1], device="cuda")
    env = creer_env()
    w = env.game_wrapper

    for ep in range(EPISODES):
        obs, _ = env.reset()
        depart = dict(w._game_state)
        total, done, flags_changes = 0.0, False, Counter()
        prec = depart.get("script_flags")
        while not done:
            action, _ = model.predict(obs, deterministic=False)  # SB3 remet l'image en canaux d'abord
            obs, r, term, trunc, _ = env.step(int(action))
            total += r
            done = term or trunc
            nouv = w._game_state.get("script_flags")
            if prec is not None and nouv is not None and count_changed_flags(prec, nouv):
                diff = np.frombuffer(prec, np.uint8) ^ np.frombuffer(nouv, np.uint8)
                for octet in np.nonzero(diff)[0]:
                    flags_changes[int(octet)] += 1
            prec = nouv

        print(f"\n=== épisode {ep + 1} : récompense {total:.2f}, carte finale {w._game_state.get('location')}")
        parts = composantes(w, depart)
        parts["expérience (reste)"] = total - sum(parts.values())
        for nom, valeur in parts.items():
            print(f"    {nom:18s} {valeur:7.2f}")
        print("    octets de flags qui changent le plus (octet: nb de changements) :", flags_changes.most_common(5))


if __name__ == "__main__":
    main()
