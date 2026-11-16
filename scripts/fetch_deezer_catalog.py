"""
Build data/songs.csv from real tracks on Deezer (public API, no key needed).

  python scripts/fetch_deezer_catalog.py            # ~5 tracks per genre/mood pair
  python scripts/fetch_deezer_catalog.py --per-pair 8

How each column is filled:
  title, artist, deezer_id, deezer_url, preview_url   real Deezer data
  popularity    Deezer "rank" scaled to 0-100
  release_decade   from the track's release date
  explicit      Deezer explicit_lyrics flag
  tempo_bpm     Deezer bpm when it has one (often it does not), else the profile value
  genre, mood   the playlist search that returned the track, e.g. "lofi chill".
                Deezer has no mood data, so this is a label from the query, not a measurement.
  energy, valence, danceability, acousticness, mood_tags, language
                Deezer exposes no audio features, so these are ESTIMATED from the matching
                genre/mood profile in data/songs_sample.csv (energy is nudged by bpm when known).
Only generic genre/mood search words are sent to Deezer.
"""
import argparse
import csv
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SAMPLE = ROOT / "data" / "songs_sample.csv"
OUT = ROOT / "data" / "songs.csv"
API = "https://api.deezer.com"
COLUMNS = ["id", "title", "artist", "genre", "mood", "energy", "tempo_bpm", "valence", "danceability",
           "acousticness", "popularity", "release_decade", "mood_tags", "language", "explicit",
           "deezer_id", "deezer_url", "preview_url"]


def get(path: str, **params) -> dict:
    url = f"{API}{path}" + ("?" + urllib.parse.urlencode(params) if params else "")
    for attempt in range(3):
        try:
            with urllib.request.urlopen(url, timeout=15) as r:
                data = json.loads(r.read().decode("utf-8"))
            time.sleep(0.15)  # stay well under Deezer's 50 requests / 5 s limit
            if isinstance(data, dict) and "error" in data:
                raise RuntimeError(data["error"])
            return data
        except Exception as exc:
            if attempt == 2:
                print(f"  ! {path}: {exc}", file=sys.stderr)
                return {}
            time.sleep(1.5)
    return {}


def load_profiles() -> dict:
    """(genre, mood) -> row from the sample catalog; the first song with that pair wins."""
    profiles = {}
    with open(SAMPLE, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            profiles.setdefault((row["genre"], row["mood"]), row)
    return profiles


def pick_playlist(genre: str, mood: str):
    for query in (f"{genre} {mood}", genre):
        for p in get("/search/playlist", q=query, limit=8).get("data", []):
            if p.get("nb_tracks", 0) >= 15:
                return p
    return None


def clamp(x: float) -> float:
    return round(max(0.0, min(1.0, x)), 2)


def build_row(track: dict, detail: dict, genre: str, mood: str, prof: dict) -> dict:
    bpm = float(detail.get("bpm") or 0)
    base_bpm = float(prof["tempo_bpm"])
    energy = float(prof["energy"]) + ((bpm - base_bpm) / 400 if bpm else 0)
    year = int((detail.get("release_date") or "2020")[:4])
    return {
        "title": track["title_short"] or track["title"], "artist": track["artist"]["name"],
        "genre": genre, "mood": mood, "energy": clamp(energy),
        "tempo_bpm": round(bpm) if bpm else round(base_bpm),
        "valence": prof["valence"], "danceability": prof["danceability"],
        "acousticness": prof["acousticness"],
        "popularity": min(100, round(track.get("rank", 0) / 10000)),
        "release_decade": year // 10 * 10, "mood_tags": prof["mood_tags"],
        "language": prof["language"], "explicit": int(bool(track.get("explicit_lyrics"))),
        "deezer_id": track["id"], "deezer_url": track["link"], "preview_url": track.get("preview", ""),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-pair", type=int, default=5)
    n = ap.parse_args().per_pair

    rows, seen_ids, seen_titles = [], set(), set()
    for (genre, mood), prof in load_profiles().items():
        pl = pick_playlist(genre, mood)
        if not pl:
            print(f"- {genre}/{mood}: no playlist found, skipped")
            continue
        tracks = get(f"/playlist/{pl['id']}/tracks", limit=50).get("data", [])
        taken, artists = 0, set()
        for t in tracks:
            if taken >= n:
                break
            key = (t["title_short"].lower(), t["artist"]["name"].lower())
            if (not t.get("readable", True) or t["id"] in seen_ids or key in seen_titles
                    or t["artist"]["id"] in artists):
                continue
            row = build_row(t, get(f"/track/{t['id']}"), genre, mood, prof)
            rows.append(row)
            seen_ids.add(t["id"]); seen_titles.add(key); artists.add(t["artist"]["id"])
            taken += 1
        print(f"- {genre}/{mood}: {taken} tracks from playlist {pl['title']!r}")

    if not rows:
        print("Nothing fetched; leaving data/songs.csv untouched.", file=sys.stderr)
        return 1
    for i, row in enumerate(rows, 1):
        row["id"] = i
    tmp = OUT.with_suffix(".tmp")
    with open(tmp, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows(rows)
    tmp.replace(OUT)
    print(f"Wrote {len(rows)} tracks to {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
