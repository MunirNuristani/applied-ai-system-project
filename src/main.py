"""
Command line runner for the Music Recommender Simulation.

Run with: python -m src.main
"""

from src.recommender import load_songs, recommend_songs, format_table, MODES, WEIGHTS

PROFILES = {
    "High-Energy Pop": {"genre": "pop", "mood": "happy", "energy": 0.8},
    "Chill Lofi": {"genre": "lofi", "mood": "chill", "energy": 0.4, "likes_acoustic": True},
    "Deep Intense Rock": {"genre": "rock", "mood": "intense", "energy": 0.92},
    # Adversarial: genre and mood disagree with energy / the catalog
    "Conflicted (classical + angry + max energy)": {"genre": "classical", "mood": "angry", "energy": 0.95},
    "Conflicted (sad + max energy)": {"genre": "pop", "mood": "sad", "energy": 0.9},
    "Unknown genre (bossa nova)": {"genre": "bossa nova", "mood": "relaxed", "energy": 0.5},
}

# Uses the extended attributes: popularity, decade, mood tags, language, explicit.
EXTENDED = {"genre": "synthwave", "mood": "moody", "energy": 0.7, "popularity": 70,
            "decade": 1980, "tags": ["nostalgic", "neon", "driving"],
            "language": "english", "allow_explicit": False}

# Experiment: halve genre weight, double energy weight
SHIFTED = {**WEIGHTS, "genre": 1.0, "energy": 2.0}


def show(name: str, prefs: dict, songs: list, k: int = 5, **kwargs) -> None:
    print(f"\n=== {name} ===")
    print(f"Profile: {prefs}")
    print(format_table(recommend_songs(prefs, songs, k, **kwargs)))


def main() -> None:
    songs = load_songs("data/songs.csv")
    print(f"Loaded songs: {len(songs)}")
    for name, prefs in PROFILES.items():
        show(name, prefs, songs)

    print("\n\n##### EXPERIMENT: genre weight 2.0 -> 1.0, energy weight 1.0 -> 2.0 #####")
    for name in ("High-Energy Pop", "Conflicted (classical + angry + max energy)"):
        show(name + " (shifted weights)", PROFILES[name], songs, weights=SHIFTED)

    print("\n\n##### CHALLENGE 1: extended attributes #####")
    show("Retro synthwave fan (decade, tags, popularity, no explicit)", EXTENDED, songs)

    print("\n\n##### CHALLENGE 2: scoring modes (Strategy pattern) #####")
    for mode in MODES:
        show(f"High-Energy Pop, mode={mode}", PROFILES["High-Energy Pop"], songs, mode=mode)

    print("\n\n##### CHALLENGE 3: diversity penalty #####")
    show("Chill Lofi, no diversity", PROFILES["Chill Lofi"], songs)
    show("Chill Lofi, diversity=True", PROFILES["Chill Lofi"], songs, diversity=True)


if __name__ == "__main__":
    main()
