"""
Command line runner for the Music Recommender Simulation.

Run with: python -m src.main
"""

from src.recommender import load_songs, recommend_songs, WEIGHTS

PROFILES = {
    "High-Energy Pop": {"genre": "pop", "mood": "happy", "energy": 0.8},
    "Chill Lofi": {"genre": "lofi", "mood": "chill", "energy": 0.4, "likes_acoustic": True},
    "Deep Intense Rock": {"genre": "rock", "mood": "intense", "energy": 0.92},
    # Adversarial: genre and mood disagree with energy / the catalog
    "Conflicted (classical + angry + max energy)": {"genre": "classical", "mood": "angry", "energy": 0.95},
    "Conflicted (sad + max energy)": {"genre": "pop", "mood": "sad", "energy": 0.9},
    "Unknown genre (bossa nova)": {"genre": "bossa nova", "mood": "relaxed", "energy": 0.5},
}

# Experiment: halve genre weight, double energy weight
SHIFTED = {**WEIGHTS, "genre": 1.0, "energy": 2.0}


def show(name: str, prefs: dict, songs: list, weights: dict = None, k: int = 5) -> None:
    print(f"\n=== {name} ===")
    print(f"Profile: {prefs}")
    for i, (song, score, why) in enumerate(recommend_songs(prefs, songs, k, weights), 1):
        print(f"{i}. {song['title']} by {song['artist']} [{song['genre']}/{song['mood']}] - {score:.2f}")
        print(f"   Because: {why}")


def main() -> None:
    songs = load_songs("data/songs.csv")
    print(f"Loaded songs: {len(songs)}")
    for name, prefs in PROFILES.items():
        show(name, prefs, songs)

    print("\n\n##### EXPERIMENT: genre weight 2.0 -> 1.0, energy weight 1.0 -> 2.0 #####")
    for name in ("High-Energy Pop", "Conflicted (classical + angry + max energy)"):
        show(name + " (shifted weights)", PROFILES[name], songs, SHIFTED)


if __name__ == "__main__":
    main()
