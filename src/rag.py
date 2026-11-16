"""
Retrieval over two sources:
  1. data/songs.csv     -> scored by the existing weighted recommender (song retrieval)
  2. docs/music_notes.md -> keyed genre/mood notes (context retrieval)

retrieve_notes() runs AFTER song retrieval, so the notes that reach the explainer
depend on which songs actually came back, not just on what the user typed.
"""
import re
from pathlib import Path
from typing import Dict, List, Tuple

ROOT = Path(__file__).resolve().parent.parent
NOTES_PATH = ROOT / "docs" / "music_notes.md"
MAX_NOTES = 6


def load_notes(path: Path = NOTES_PATH) -> Dict[str, str]:
    """Parses '## genre: lofi' / '## mood: chill' sections into {'genre:lofi': text}."""
    try:
        raw = Path(path).read_text(encoding="utf-8")
    except FileNotFoundError:
        return {}
    notes: Dict[str, str] = {}
    for m in re.finditer(r"^## (genre|mood): (.+?)\n(.*?)(?=^## |\Z)", raw, re.S | re.M):
        notes[f"{m.group(1)}:{m.group(2).strip().lower()}"] = " ".join(m.group(3).split())
    return notes


def retrieve_notes(prefs: Dict, results: List[Tuple[Dict, float, str]],
                   notes: Dict[str, str]) -> Dict[str, str]:
    """Requested genre/mood first, then the genre/mood of each retrieved song."""
    wanted = []
    if prefs.get("genre"):
        wanted.append(f"genre:{prefs['genre']}")
    if prefs.get("mood"):
        wanted.append(f"mood:{prefs['mood']}")
    for song, _, _ in results:
        wanted += [f"genre:{song['genre'].lower()}", f"mood:{song['mood'].lower()}"]
    picked: Dict[str, str] = {}
    for key in wanted:
        if key in notes and key not in picked:
            picked[key] = notes[key]
        if len(picked) >= MAX_NOTES:
            break
    return picked
