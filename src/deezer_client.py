"""
Deezer lookup (public API, no key). Used to verify that a song suggested by the
LLM really exists and to get an ID the app can play with Deezer's embed widget.

  * find_track(title, artist) only returns a track whose title and artist match
    what was asked for, so a hallucinated song comes back as None.
  * Only the song title and artist are sent to Deezer, never the user's request.
  * It never raises: any network or API failure returns None.
"""
import json
import logging
import re
import time
import urllib.parse
import urllib.request
from typing import Callable, Dict, NamedTuple, Optional

log = logging.getLogger("deezer")

SEARCH_URL = "https://api.deezer.com/search"
WIDGET_URL = "https://widget.deezer.com/widget/auto/track/{id}"
TIMEOUT = 10


class DeezerTrack(NamedTuple):
    track_id: int
    title: str
    artist: str
    url: str
    cover: str


def _http_json(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=TIMEOUT) as resp:
        return json.loads(resp.read().decode("utf-8"))


def norm(text: str) -> str:
    """Lowercase, drop (feat. ...) / [remix] parts and punctuation."""
    text = re.sub(r"[\(\[].*?[\)\]]", " ", text or "")
    text = re.sub(r"\s+-\s+.*$", "", text)          # "Song - Radio Edit" -> "Song"
    return re.sub(r"[^a-z0-9 ]", "", text.lower()).strip()


def _same_title(wanted: str, found: str) -> bool:
    w, f = norm(wanted), norm(found)
    return bool(w) and w == f


def _same_artist(wanted: str, found: str) -> bool:
    w, f = norm(wanted), norm(found)
    return bool(w) and bool(f) and (w == f or w in f or f in w)


class DeezerClient:
    def __init__(self, fetch: Callable[[str], dict] = _http_json, pause: float = 0.12):
        self._fetch, self._pause = fetch, pause
        self._cache: Dict[tuple, Optional[DeezerTrack]] = {}

    def _search(self, query: str) -> list:
        url = SEARCH_URL + "?" + urllib.parse.urlencode({"q": query, "limit": 10})
        data = self._fetch(url)
        time.sleep(self._pause)  # Deezer allows ~50 requests per 5 seconds
        return data.get("data", []) if isinstance(data, dict) else []

    def preview_for(self, track_id: int) -> str:
        """A fresh 30-second preview URL. Deezer signs these and they expire in ~12 minutes,
        so they are never cached or stored. Returns "" on any failure."""
        try:
            data = self._fetch(f"https://api.deezer.com/track/{int(track_id)}")
            return data.get("preview", "") if isinstance(data, dict) else ""
        except Exception as exc:
            log.warning("deezer preview failed for %s: %s", track_id, exc)
            return ""

    def fetch_audio(self, url: str) -> bytes:
        """Download the ~480 KB preview so the app serves the audio itself. The browser then never
        touches Deezer's signed CDN link (which expires, and which ad blockers can block)."""
        if not url:
            return b""
        try:
            with urllib.request.urlopen(url, timeout=TIMEOUT) as resp:
                data = resp.read(2_000_000)
            return data if data[:3] == b"ID3" or data[:2] == b"\xff\xfb" or len(data) > 10_000 else b""
        except Exception as exc:
            log.warning("deezer audio download failed: %s", exc)
            return b""

    def find_track(self, title: str, artist: str) -> Optional[DeezerTrack]:
        key = (norm(title), norm(artist))
        if key in self._cache:
            return self._cache[key]
        found = None
        try:
            for query in (f'artist:"{artist}" track:"{title}"', f"{title} {artist}"):
                for item in self._search(query):
                    if (_same_title(title, item.get("title_short") or item.get("title", ""))
                            and _same_artist(artist, item.get("artist", {}).get("name", ""))):
                        found = DeezerTrack(
                            item["id"], item.get("title_short") or item["title"],
                            item["artist"]["name"], item.get("link", f"https://www.deezer.com/track/{item['id']}"),
                            (item.get("album") or {}).get("cover_medium", ""))
                        break
                if found:
                    break
        except Exception as exc:
            log.warning("deezer lookup failed for %r: %s", key, exc)
            return None  # don't cache failures
        self._cache[key] = found
        return found
