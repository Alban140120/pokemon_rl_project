"""Joue quelques épisodes avec un modèle entraîné et décompose la récompense par source.

    python -m scripts.decomposer_recompense checkpoints/ppo_exploration_200k_final.zip
    python -m scripts.decomposer_recompense aleatoire     # agent aléatoire
"""
import sys
from collections import Counter

import mgba.log
import numpy as np
from stable_baselines3 import PPO

from pygba.game_wrappers.pokemon_emerald import count_changed_flags, count_flags
from train import creer_env

EPISODES = 3


def composantes(wrapper, etat_depart, maison_depart):
    """Ce que chaque source a rapporté depuis le début de l'épisode (poids appliqués)."""
    s = wrapper._game_state
    m = {nom: wrapper._composantes()[nom] - maison_depart[nom] for nom in maison_depart}
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
        "exploration": m["cases_visitees"] * wrapper.exploration_reward,
        "cartes extérieures": m["cartes_ext"] * wrapper.carte_ext_reward,
        "cartes intérieures": m["cartes_int"] * wrapper.carte_int_reward,
        "niveaux": m["niveaux"] * wrapper.niveau_reward,
        "évolutions": m["evolutions"] * wrapper.evolution_reward,
        "pv manquants": -m["pv"] * wrapper.pv_penalite,
        "ko": -m["ko"] * wrapper.ko_penalite,
        "statuts": -m["statuts"] * wrapper.statut_penalite,
    }


def main():
    mgba.log.silence()
    env = creer_env()
    if sys.argv[1] == "aleatoire":
        choisir = lambda obs: env.action_space.sample()  # noqa: E731
    else:
        model = PPO.load(sys.argv[1], device="cuda")
        choisir = lambda obs: int(model.predict(obs, deterministic=False)[0])  # noqa: E731
    w = env.game_wrapper

    for ep in range(EPISODES):
        obs, _ = env.reset()
        depart, maison_depart = dict(w._game_state), w._composantes()
        total, done, flags_changes = 0.0, False, Counter()
        prec = depart.get("script_flags")
        while not done:
            obs, r, term, trunc, _ = env.step(choisir(obs))
            total += r
            done = term or trunc
            nouv = w._game_state.get("script_flags")
            if prec is not None and nouv is not None and count_changed_flags(prec, nouv):
                diff = np.frombuffer(prec, np.uint8) ^ np.frombuffer(nouv, np.uint8)
                for octet in np.nonzero(diff)[0]:
                    flags_changes[int(octet)] += 1
            prec = nouv

        print(f"\n=== épisode {ep + 1} : récompense {total:.2f}, carte finale {w._game_state.get('location')}")
        parts = composantes(w, depart, maison_depart)
        parts["expérience (reste)"] = total - sum(parts.values())
        for nom, valeur in parts.items():
            print(f"    {nom:20s} {valeur:7.2f}")
        print("    octets de flags qui changent le plus (octet: nb de changements) :", flags_changes.most_common(5))


if __name__ == "__main__":
    main()
