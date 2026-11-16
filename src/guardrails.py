"""
Guardrails. Three checkpoints, all pure functions that return a reason string
instead of raising, so the pipeline can log the problem and degrade safely:

  normalize_input    -> before anything else sees the request
  clean_profile      -> between the parser (LLM or rules) and the retriever
  check_explanation  -> between the LLM explainer and the user
"""
import math
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

MAX_INPUT_CHARS = 300
MIN_CONFIDENCE = 0.3   # below this the system abstains and asks the human to rephrase
MAX_TAGS = 5
MAX_EXPLANATION_CHARS = 400
ALLOWED_KEYS = {"genre", "mood", "energy", "likes_acoustic", "tags"}


@dataclass(frozen=True)
class Catalog:
    genres: frozenset
    moods: frozenset
    titles: frozenset   # lowercase
    artists: frozenset  # lowercase


def build_catalog(songs: List[Dict]) -> Catalog:
    return Catalog(
        genres=frozenset(s["genre"].lower() for s in songs),
        moods=frozenset(s["mood"].lower() for s in songs),
        titles=frozenset(s["title"].lower() for s in songs),
        artists=frozenset(s["artist"].lower() for s in songs),
    )


def normalize_input(text) -> Tuple[str, Optional[str]]:
    """Returns (clean_text, rejection_reason). Control characters become spaces."""
    if not isinstance(text, str):
        return "", "request must be text"
    cleaned = "".join(ch if ch.isprintable() else " " for ch in text)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    if not cleaned:
        return "", "empty request"
    if len(cleaned) > MAX_INPUT_CHARS:
        return "", f"request too long ({len(cleaned)} chars, max {MAX_INPUT_CHARS})"
    return cleaned, None


def clean_profile(raw, catalog: Catalog) -> Tuple[Dict, List[str]]:
    """Validates a parsed taste profile against the real catalog. Returns (prefs, issues)."""
    prefs: Dict = {}
    issues: List[str] = []
    if not isinstance(raw, dict):
        return {}, ["profile was not a JSON object"]

    for key in raw:
        if key not in ALLOWED_KEYS and key != "confidence":
            issues.append(f"dropped unknown field '{key}'")

    for key, allowed in (("genre", catalog.genres), ("mood", catalog.moods)):
        val = raw.get(key)
        if val is None:
            continue
        v = str(val).strip().lower()
        if v in allowed:
            prefs[key] = v
        elif v:
            issues.append(f"{key} '{v}' is not in the catalog; ignored")

    energy = raw.get("energy")
    if energy is not None:
        try:
            x = float(energy)
        except (TypeError, ValueError):
            x = None
        if x is None or math.isnan(x) or math.isinf(x):
            issues.append(f"energy '{energy}' is not a number; ignored")
        else:
            if x < 0 or x > 1:
                issues.append(f"energy {x:g} out of range; clamped to [0, 1]")
                x = min(1.0, max(0.0, x))
            prefs["energy"] = round(x, 2)

    acoustic = raw.get("likes_acoustic")
    if isinstance(acoustic, bool):
        prefs["likes_acoustic"] = acoustic
    elif isinstance(acoustic, str) and acoustic.lower() in ("true", "false"):
        prefs["likes_acoustic"] = acoustic.lower() == "true"
    elif acoustic is not None:
        issues.append("likes_acoustic must be true/false; ignored")

    tags = raw.get("tags")
    if isinstance(tags, list):
        clean = [t.strip().lower() for t in tags if isinstance(t, str) and t.strip()][:MAX_TAGS]
        if clean:
            prefs["tags"] = clean
    elif tags is not None:
        issues.append("tags must be a list; ignored")

    return prefs, issues


def _numbers_for(song: Dict) -> set:
    """Every way a number from this song's data could legitimately be written."""
    allowed = set()
    for field in ("energy", "valence", "danceability", "acousticness"):
        v = song.get(field)
        if v is not None:
            allowed |= {f"{v:g}", f"{v:.1f}", f"{v:.2f}", str(round(v * 100))}
    for field in ("tempo_bpm", "popularity", "release_decade", "id"):
        v = song.get(field)
        if v is not None:
            allowed |= {f"{v:g}", str(int(v))}
    return allowed


def check_explanation(text, song: Dict, catalog: Catalog, reasons: List[str]) -> Optional[str]:
    """
    Grounding check for LLM-written explanations. Returns None if OK, else the
    reason it was rejected. Catches: empty/huge output, comparisons to songs or
    artists we did not retrieve, and numbers that are not in this song's data.
    It does NOT verify subjective claims (e.g. "feels warm") -- see model_card.md.
    """
    if not isinstance(text, str) or not text.strip():
        return "empty explanation"
    if len(text) > MAX_EXPLANATION_CHARS:
        return f"explanation too long ({len(text)} chars)"
    low = text.lower()
    own_title, own_artist = song["title"].lower(), song["artist"].lower()
    for title in catalog.titles - {own_title}:
        if re.search(r"(?<!\w)" + re.escape(title) + r"(?!\w)", low):
            return f"mentions another song ('{title}')"
    for artist in catalog.artists - {own_artist}:
        if re.search(r"(?<!\w)" + re.escape(artist) + r"(?!\w)", low):
            return f"mentions another artist ('{artist}')"
    allowed = _numbers_for(song)
    for r in reasons:
        allowed |= set(re.findall(r"\d+(?:\.\d+)?", r))
    for num in re.findall(r"\d+(?:\.\d+)?", text):
        if num not in allowed:
            return f"number {num} is not in this song's data"
    return None


# --- guardrail 4: LLM song suggestions (new "discover" flow) -------------------
MAX_SUGGESTIONS = 10
MAX_FIELD_CHARS = 120


def check_suggestions(raw, k: int) -> Tuple[List[Dict], List[str]]:
    """
    Validates the LLM's song suggestions BEFORE any of them reaches Deezer or the user.
    Returns (clean_suggestions, issues). Each clean item is {title, artist, reason}.
    Drops: non-dict items, missing/oversized title or artist, duplicates, anything
    past k. A reason is replaced with "" (the caller substitutes a template) when it
    is too long, has a URL, contains digits (nothing to verify them against), or
    names another suggested song or artist.
    """
    issues: List[str] = []
    items = raw.get("songs") if isinstance(raw, dict) else raw
    if not isinstance(items, list):
        return [], ["suggestions were not a list"]

    clean: List[Dict] = []
    seen = set()
    for i, it in enumerate(items):
        if not isinstance(it, dict):
            issues.append(f"suggestion {i} was not an object; dropped")
            continue
        title, artist = it.get("title"), it.get("artist")
        if not (isinstance(title, str) and isinstance(artist, str) and title.strip() and artist.strip()):
            issues.append(f"suggestion {i} missing title or artist; dropped")
            continue
        title, artist = " ".join(title.split()), " ".join(artist.split())
        if len(title) > MAX_FIELD_CHARS or len(artist) > MAX_FIELD_CHARS:
            issues.append(f"suggestion {i} had an oversized title or artist; dropped")
            continue
        key = (title.lower(), artist.lower())
        if key in seen:
            issues.append(f"duplicate suggestion '{title}'; dropped")
            continue
        seen.add(key)
        reason = it.get("reason")
        clean.append({"title": title, "artist": artist, "reason": reason if isinstance(reason, str) else ""})

    clean = clean[:min(k, MAX_SUGGESTIONS)]
    for s in clean:
        low = s["reason"].lower()
        problem = None
        if not low.strip():
            problem = None
        elif len(s["reason"]) > MAX_EXPLANATION_CHARS:
            problem = "too long"
        elif re.search(r"https?://|www\.", low):
            problem = "contains a link"
        elif re.search(r"\d", low):
            problem = "contains numbers that cannot be verified"
        else:
            for o in clean:
                if o is s:
                    continue
                for name in (o["title"].lower(), o["artist"].lower()):
                    if name != s["artist"].lower() and name != s["title"].lower() and \
                            re.search(r"(?<!\w)" + re.escape(name) + r"(?!\w)", low):
                        problem = f"mentions another suggestion ('{name}')"
                        break
                if problem:
                    break
        if problem:
            issues.append(f"reason for '{s['title']}' rejected: {problem}")
            s["reason"] = ""
        s["reason"] = s["reason"].strip()
    return clean, issues
