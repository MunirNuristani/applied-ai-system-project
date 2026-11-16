from src.recommender import Song, UserProfile, Recommender

def make_small_recommender() -> Recommender:
    songs = [
        Song(
            id=1,
            title="Test Pop Track",
            artist="Test Artist",
            genre="pop",
            mood="happy",
            energy=0.8,
            tempo_bpm=120,
            valence=0.9,
            danceability=0.8,
            acousticness=0.2,
        ),
        Song(
            id=2,
            title="Chill Lofi Loop",
            artist="Test Artist",
            genre="lofi",
            mood="chill",
            energy=0.4,
            tempo_bpm=80,
            valence=0.6,
            danceability=0.5,
            acousticness=0.9,
        ),
    ]
    return Recommender(songs)


def test_recommend_returns_songs_sorted_by_score():
    user = UserProfile(
        favorite_genre="pop",
        favorite_mood="happy",
        target_energy=0.8,
        likes_acoustic=False,
    )
    rec = make_small_recommender()
    results = rec.recommend(user, k=2)

    assert len(results) == 2
    # Starter expectation: the pop, happy, high energy song should score higher
    assert results[0].genre == "pop"
    assert results[0].mood == "happy"


def test_explain_recommendation_returns_non_empty_string():
    user = UserProfile(
        favorite_genre="pop",
        favorite_mood="happy",
        target_energy=0.8,
        likes_acoustic=False,
    )
    rec = make_small_recommender()
    song = rec.songs[0]

    explanation = rec.explain_recommendation(user, song)
    assert isinstance(explanation, str)
    assert explanation.strip() != ""


# --- Extension tests -------------------------------------------------------
from src.recommender import load_songs, score_song, recommend_songs, format_table, MODES


def _songs():
    return load_songs("data/songs_sample.csv")


def test_load_songs_parses_extended_columns():
    s = _songs()[0]
    assert isinstance(s["popularity"], int) and isinstance(s["energy"], float)
    assert "|" in s["mood_tags"]


def test_extended_attributes_affect_score_and_explicit_penalty():
    song = next(s for s in _songs() if s["explicit"] == 1)
    base, _ = score_song({"genre": song["genre"]}, song)
    penalised, reasons = score_song({"genre": song["genre"], "allow_explicit": False}, song)
    assert penalised < base and any("explicit" in r for r in reasons)
    _, r = score_song({"tags": [song["mood_tags"].split("|")[0]]}, song)
    assert any("tag match" in x for x in r)


def test_modes_change_the_ranking():
    prefs = {"genre": "classical", "mood": "angry", "energy": 0.95}
    genre_first = recommend_songs(prefs, _songs(), 1, mode="genre_first")[0][0]["genre"]
    energy_first = recommend_songs(prefs, _songs(), 1, mode="energy_focused")[0][0]["genre"]
    assert genre_first == "classical" and energy_first != "classical"
    assert set(MODES) == {"genre_first", "mood_first", "energy_focused"}


def test_diversity_penalty_reduces_repeat_artists():
    prefs = {"genre": "lofi", "mood": "chill", "energy": 0.4}
    artists = lambda res: [s["artist"] for s, _, _ in res]
    plain = artists(recommend_songs(prefs, _songs(), 4))
    diverse = artists(recommend_songs(prefs, _songs(), 4, diversity=True))
    assert len(set(diverse)) > len(set(plain))


def test_table_includes_reasons():
    table = format_table(recommend_songs({"genre": "pop"}, _songs(), 2))
    assert "genre match" in table and table.count("+---") >= 3
