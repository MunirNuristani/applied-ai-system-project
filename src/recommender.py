import csv
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

@dataclass
class Song:
    """
    Represents a song and its attributes.
    Required by tests/test_recommender.py
    """
    id: int
    title: str
    artist: str
    genre: str
    mood: str
    energy: float
    tempo_bpm: float
    valence: float
    danceability: float
    acousticness: float

@dataclass
class UserProfile:
    """
    Represents a user's taste preferences.
    Required by tests/test_recommender.py
    """
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool

# Weights for the Algorithm Recipe. Max possible score is the sum of all four.
WEIGHTS = {"genre": 2.0, "mood": 1.0, "energy": 1.0, "acoustic": 0.5}


def _score(genre: str, mood: str, energy: float, acousticness: float,
           fav_genre: str, fav_mood: str, target_energy: float,
           likes_acoustic: Optional[bool], weights: Dict[str, float]) -> Tuple[float, List[str]]:
    """Shared scoring rule used by both the OOP and functional APIs."""
    score = 0.0
    reasons: List[str] = []

    if fav_genre and genre.lower() == fav_genre.lower():
        score += weights["genre"]
        reasons.append(f"genre match ({genre}) +{weights['genre']:.1f}")
    if fav_mood and mood.lower() == fav_mood.lower():
        score += weights["mood"]
        reasons.append(f"mood match ({mood}) +{weights['mood']:.1f}")

    # Reward closeness to the target, not simply higher or lower energy.
    if target_energy is not None:
        pts = weights["energy"] * (1.0 - abs(energy - target_energy))
        score += pts
        reasons.append(f"energy {energy:.2f} vs target {target_energy:.2f} +{pts:.2f}")

    if likes_acoustic is not None:
        fit = acousticness if likes_acoustic else 1.0 - acousticness
        pts = weights["acoustic"] * fit
        score += pts
        reasons.append(f"acoustic fit +{pts:.2f}")

    return score, reasons


class Recommender:
    """
    OOP implementation of the recommendation logic.
    Required by tests/test_recommender.py
    """
    def __init__(self, songs: List[Song], weights: Optional[Dict[str, float]] = None):
        self.songs = songs
        self.weights = weights or WEIGHTS

    def _score(self, user: UserProfile, song: Song) -> Tuple[float, List[str]]:
        return _score(song.genre, song.mood, song.energy, song.acousticness,
                      user.favorite_genre, user.favorite_mood, user.target_energy,
                      user.likes_acoustic, self.weights)

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        ranked = sorted(self.songs, key=lambda s: self._score(user, s)[0], reverse=True)
        return ranked[:k]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        score, reasons = self._score(user, song)
        return f"{song.title}: score {score:.2f} because " + "; ".join(reasons)


def load_songs(csv_path: str) -> List[Dict]:
    """
    Loads songs from a CSV file, converting numeric columns to int/float.
    Required by src/main.py
    """
    int_cols = {"id"}
    float_cols = {"energy", "tempo_bpm", "valence", "danceability", "acousticness"}
    songs: List[Dict] = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            for c in int_cols:
                row[c] = int(row[c])
            for c in float_cols:
                row[c] = float(row[c])
            songs.append(row)
    return songs


def score_song(user_prefs: Dict, song: Dict,
               weights: Optional[Dict[str, float]] = None) -> Tuple[float, List[str]]:
    """
    Scores a single song against user preferences.
    Returns (score, reasons). Recognised prefs: genre, mood, energy, likes_acoustic.
    """
    return _score(song["genre"], song["mood"], song["energy"], song["acousticness"],
                  user_prefs.get("genre"), user_prefs.get("mood"),
                  user_prefs.get("energy"), user_prefs.get("likes_acoustic"),
                  weights or WEIGHTS)


def recommend_songs(user_prefs: Dict, songs: List[Dict], k: int = 5,
                    weights: Optional[Dict[str, float]] = None) -> List[Tuple[Dict, float, str]]:
    """
    Scores every song, sorts high to low, and returns the top k as
    (song_dict, score, explanation).
    """
    scored = []
    for song in songs:
        score, reasons = score_song(user_prefs, song, weights)
        scored.append((song, score, "; ".join(reasons)))
    return sorted(scored, key=lambda t: t[1], reverse=True)[:k]
