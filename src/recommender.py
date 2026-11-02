import csv
from dataclasses import dataclass, asdict, field
from typing import List, Dict, Tuple, Optional


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
    # Extended attributes (Challenge 1); optional so older callers still work.
    popularity: int = 50
    release_decade: int = 2020
    mood_tags: str = ""
    language: str = "english"
    explicit: int = 0


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
    # Optional extended preferences (Challenge 1).
    target_popularity: Optional[int] = None
    favorite_decade: Optional[int] = None
    favorite_tags: List[str] = field(default_factory=list)
    language: Optional[str] = None
    allow_explicit: Optional[bool] = None


# --- Challenge 2: Strategy pattern -------------------------------------------
# A scoring mode is just a named bundle of weights. The scoring rule is the same
# for every mode; swapping the strategy swaps the weights, so adding a mode never
# touches the scoring code.
@dataclass(frozen=True)
class ScoringMode:
    """A named ranking strategy: the weights the scoring rule applies."""
    name: str
    weights: Dict[str, float]


_BASE = {"genre": 2.0, "mood": 1.0, "energy": 1.0, "acoustic": 0.5,
         "decade": 0.5, "tags": 0.5, "popularity": 0.5, "language": 0.5,
         "explicit": 1.0}

MODES: Dict[str, ScoringMode] = {
    "genre_first": ScoringMode("genre_first", dict(_BASE)),
    "mood_first": ScoringMode("mood_first", {**_BASE, "genre": 1.0, "mood": 2.5, "tags": 1.0}),
    "energy_focused": ScoringMode("energy_focused", {**_BASE, "genre": 1.0, "energy": 2.5}),
}
DEFAULT_MODE = "genre_first"
WEIGHTS = MODES[DEFAULT_MODE].weights  # kept for backwards compatibility

# Diversity penalty (Challenge 3), per already-chosen song in the list.
ARTIST_PENALTY = 1.0
GENRE_PENALTY = 0.5


def _closeness(value: float, target: float, scale: float = 1.0) -> float:
    """1.0 when value == target, falling linearly to 0.0 at `scale` apart."""
    return max(0.0, 1.0 - abs(value - target) / scale)


def score_song(user_prefs: Dict, song: Dict,
               weights: Optional[Dict[str, float]] = None) -> Tuple[float, List[str]]:
    """
    Scores one song against user preferences and returns (score, reasons).

    Core prefs: genre, mood, energy, likes_acoustic. Optional prefs: popularity
    (0-100), decade, tags (list), language, allow_explicit.
    """
    w = {**WEIGHTS, **(weights or {})}
    score, reasons = 0.0, []

    def add(pts: float, why: str) -> None:
        nonlocal score
        score += pts
        reasons.append(f"{why} {pts:+.2f}")

    genre, mood = user_prefs.get("genre"), user_prefs.get("mood")
    if genre and song["genre"].lower() == genre.lower():
        add(w["genre"], f"genre match ({song['genre']})")
    if mood and song["mood"].lower() == mood.lower():
        add(w["mood"], f"mood match ({song['mood']})")

    # Reward closeness to the target, not simply higher or lower energy.
    if user_prefs.get("energy") is not None:
        add(w["energy"] * _closeness(song["energy"], user_prefs["energy"]),
            f"energy {song['energy']:.2f} vs target {user_prefs['energy']:.2f}")

    if user_prefs.get("likes_acoustic") is not None:
        fit = song["acousticness"] if user_prefs["likes_acoustic"] else 1.0 - song["acousticness"]
        add(w["acoustic"] * fit, "acoustic fit")

    # Extended attributes (Challenge 1). Every check is skipped if the pref or the
    # column is absent, so the original 10-column catalog still scores.
    if user_prefs.get("popularity") is not None and "popularity" in song:
        add(w["popularity"] * _closeness(song["popularity"], user_prefs["popularity"], 100.0),
            f"popularity {song['popularity']} vs {user_prefs['popularity']}")
    if user_prefs.get("decade") is not None and "release_decade" in song:
        # Full credit for the same decade, half for the adjacent one.
        gap = abs(song["release_decade"] - user_prefs["decade"])
        if gap == 0:
            add(w["decade"], f"decade match ({song['release_decade']}s)")
        elif gap == 10:
            add(w["decade"] / 2, f"adjacent decade ({song['release_decade']}s)")
    if user_prefs.get("tags") and song.get("mood_tags"):
        song_tags = set(song["mood_tags"].split("|"))
        hits = sorted(song_tags & {t.lower() for t in user_prefs["tags"]})
        if hits:
            add(w["tags"] * len(hits) / len(user_prefs["tags"]), f"tag match ({', '.join(hits)})")
    if user_prefs.get("language") and song.get("language"):
        if song["language"].lower() == user_prefs["language"].lower():
            add(w["language"], f"language match ({song['language']})")
    if user_prefs.get("allow_explicit") is False and int(song.get("explicit", 0)):
        add(-w["explicit"], "explicit content")

    return score, reasons


def recommend_songs(user_prefs: Dict, songs: List[Dict], k: int = 5,
                    weights: Optional[Dict[str, float]] = None,
                    mode: Optional[str] = None,
                    diversity: bool = False) -> List[Tuple[Dict, float, str]]:
    """
    Scores every song and returns the top k as (song_dict, score, explanation).

    `mode` picks a ScoringMode by name; `weights` overrides individual weights.
    With diversity=True, songs are picked greedily and repeat artists/genres in
    the list so far are penalized.
    """
    if mode is not None:
        weights = {**MODES[mode].weights, **(weights or {})}
    scored = []
    for song in songs:
        score, reasons = score_song(user_prefs, song, weights)
        scored.append((song, score, reasons))

    if not diversity:
        ranked = sorted(scored, key=lambda t: t[1], reverse=True)[:k]
        return [(s, sc, "; ".join(r)) for s, sc, r in ranked]

    picked: List[Tuple[Dict, float, str]] = []
    remaining = scored[:]
    while remaining and len(picked) < k:
        def adjusted(item):
            song, score, _ = item
            penalty = sum(ARTIST_PENALTY for p, _, _ in picked if p["artist"] == song["artist"])
            penalty += sum(GENRE_PENALTY for p, _, _ in picked if p["genre"] == song["genre"])
            return score - penalty, penalty
        best = max(remaining, key=lambda it: adjusted(it)[0])
        remaining.remove(best)
        final, penalty = adjusted(best)
        reasons = best[2] + ([f"diversity penalty {-penalty:+.2f}"] if penalty else [])
        picked.append((best[0], final, "; ".join(reasons)))
    return picked


def load_songs(csv_path: str) -> List[Dict]:
    """
    Loads songs from a CSV file, converting numeric columns to int/float.
    Required by src/main.py
    """
    int_cols = {"id", "popularity", "release_decade", "explicit"}
    float_cols = {"energy", "tempo_bpm", "valence", "danceability", "acousticness"}
    songs: List[Dict] = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            for c in int_cols & row.keys():
                row[c] = int(row[c])
            for c in float_cols & row.keys():
                row[c] = float(row[c])
            songs.append(row)
    return songs


def format_table(results: List[Tuple[Dict, float, str]]) -> str:
    """Renders recommendations as an ASCII table that includes the reasons."""
    width = 58
    def wrap(text: str) -> List[str]:
        lines, cur = [], ""
        for part in text.split("; "):
            if cur and len(cur) + len(part) + 2 > width:
                lines.append(cur + ";")
                cur = part
            else:
                cur = f"{cur}; {part}" if cur else part
        return lines + [cur]

    head = ["#", "Title", "Artist", "Score", "Reasons"]
    body = []
    for i, (song, score, why) in enumerate(results, 1):
        r = wrap(why)
        body.append([[str(i)], [song["title"]], [song["artist"]], [f"{score:.2f}"], r])
    cols = [max(len(head[c]), *(len(l) for row in body for l in row[c])) for c in range(5)]
    sep = "+" + "+".join("-" * (w + 2) for w in cols) + "+"
    fmt = lambda cells: "| " + " | ".join(c.ljust(w) for c, w in zip(cells, cols)) + " |"
    out = [sep, fmt(head), sep]
    for row in body:
        for n in range(len(row[4])):
            out.append(fmt([row[c][0] if n == 0 and c < 4 else "" for c in range(4)] + [row[4][n]]))
        out.append(sep)
    return "\n".join(out)


class Recommender:
    """
    OOP implementation of the recommendation logic.
    Required by tests/test_recommender.py
    """
    def __init__(self, songs: List[Song], weights: Optional[Dict[str, float]] = None):
        self.songs = songs
        self.weights = weights

    @staticmethod
    def _prefs(user: UserProfile) -> Dict:
        return {"genre": user.favorite_genre, "mood": user.favorite_mood,
                "energy": user.target_energy, "likes_acoustic": user.likes_acoustic,
                "popularity": user.target_popularity, "decade": user.favorite_decade,
                "tags": user.favorite_tags, "language": user.language,
                "allow_explicit": user.allow_explicit}

    def _score(self, user: UserProfile, song: Song) -> Tuple[float, List[str]]:
        return score_song(self._prefs(user), asdict(song), self.weights)

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        ranked = sorted(self.songs, key=lambda s: self._score(user, s)[0], reverse=True)
        return ranked[:k]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        score, reasons = self._score(user, song)
        return f"{song.title}: score {score:.2f} because " + "; ".join(reasons)
