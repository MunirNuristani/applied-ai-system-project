"""
Thin Gemini wrapper with three safety nets:

1. record/replay cache (data/llm_cache.json) -> graders can reproduce LLM output
   without an API key, and repeat runs cost zero quota.
2. daily call budget (logs/llm_usage.json) -> the free tier is tiny, so we stop
   *before* Google starts returning 429s.
3. complete() never raises. On any failure it returns text=None and callers fall
   back to the deterministic rule-based path.

Modes:
  offline -> never touch cache or network (NullClient)
  replay  -> cache only
  auto    -> cache first, then live Gemini if GEMINI_API_KEY is set and budget remains
"""
import hashlib
import json
import logging
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import NamedTuple, Optional

log = logging.getLogger("llm")

ROOT = Path(__file__).resolve().parent.parent
CACHE_PATH = ROOT / "data" / "llm_cache.json"
USAGE_PATH = ROOT / "logs" / "llm_usage.json"
# Model names change often and free-tier quota differs per model. Override with
# GEMINI_MODEL in .env after checking which model your AI Studio project lists.
DEFAULT_MODEL = "gemini-3.5-flash-lite"
DEFAULT_DAILY_BUDGET = 18  # stay under a 20/day quota
DEFAULT_TIMEOUT = 120      # seconds per call; override with GEMINI_TIMEOUT


class LLMResult(NamedTuple):
    text: Optional[str]
    source: str  # cache | live | offline | no_key | budget | error


def load_env(path: Path = ROOT / ".env") -> None:
    """Tiny .env loader (avoids a python-dotenv dependency). Real env vars win."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def _today() -> str:
    """Gemini's daily quota resets at midnight Pacific; approximate with UTC-8."""
    return datetime.now(timezone(timedelta(hours=-8))).strftime("%Y-%m-%d")


class NullClient:
    """Used for --mode offline and in tests: the LLM is simply never available."""
    def complete(self, prompt: str, purpose: str = "") -> LLMResult:
        return LLMResult(None, "offline")


class GeminiClient:
    def __init__(self, mode: str = "auto", model: Optional[str] = None,
                 cache_path: Path = CACHE_PATH, usage_path: Path = USAGE_PATH,
                 daily_budget: Optional[int] = None):
        load_env()
        self.mode = mode
        self.model = model or os.environ.get("GEMINI_MODEL", DEFAULT_MODEL)
        self.api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        self.cache_path = Path(cache_path)
        self.usage_path = Path(usage_path)
        self.daily_budget = int(daily_budget if daily_budget is not None
                                else os.environ.get("GEMINI_DAILY_BUDGET", DEFAULT_DAILY_BUDGET))

    # -- cache ---------------------------------------------------------------
    @staticmethod
    def _key(prompt: str, purpose: str) -> str:
        return hashlib.sha256(f"{purpose}\n{prompt}".encode("utf-8")).hexdigest()

    def _read_cache(self) -> dict:
        try:
            return json.loads(self.cache_path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _write_cache(self, cache: dict) -> None:
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.cache_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(cache, indent=2, sort_keys=True), encoding="utf-8")
        tmp.replace(self.cache_path)

    # -- budget --------------------------------------------------------------
    def _calls_today(self) -> int:
        try:
            data = json.loads(self.usage_path.read_text(encoding="utf-8"))
            return data["calls"] if data.get("date") == _today() else 0
        except (FileNotFoundError, json.JSONDecodeError, KeyError):
            return 0

    def _count_call(self) -> None:
        self.usage_path.parent.mkdir(parents=True, exist_ok=True)
        self.usage_path.write_text(
            json.dumps({"date": _today(), "calls": self._calls_today() + 1}), encoding="utf-8")

    # -- public --------------------------------------------------------------
    def complete(self, prompt: str, purpose: str = "") -> LLMResult:
        key = self._key(prompt, purpose)
        cache = self._read_cache()
        if key in cache:
            log.info("llm cache hit purpose=%s", purpose)
            return LLMResult(cache[key]["response"], "cache")
        if self.mode == "replay":
            return LLMResult(None, "offline")
        if not self.api_key:
            log.warning("no GEMINI_API_KEY; falling back to rule-based path")
            return LLMResult(None, "no_key")
        if self._calls_today() >= self.daily_budget:
            log.warning("daily budget of %d calls reached; skipping live call", self.daily_budget)
            return LLMResult(None, "budget")
        try:
            self._count_call()  # count attempts, not just successes
            text = self._call_gemini(prompt)
        except Exception as exc:  # network, 429, bad key, SDK missing: all degrade the same way
            log.error("gemini call failed (%s): %s", type(exc).__name__, exc)
            return LLMResult(None, "error")
        if not text:
            return LLMResult(None, "error")
        cache[key] = {"purpose": purpose, "model": self.model, "response": text,
                      "recorded_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
        self._write_cache(cache)
        log.info("llm live call ok purpose=%s model=%s", purpose, self.model)
        return LLMResult(text, "live")

    def _call_gemini(self, prompt: str) -> str:
        from google import genai  # lazy: offline runs and tests don't need the SDK
        from google.genai import types
        timeout_ms = int(float(os.environ.get("GEMINI_TIMEOUT", DEFAULT_TIMEOUT)) * 1000)
        client = genai.Client(api_key=self.api_key, http_options=types.HttpOptions(timeout=timeout_ms))
        resp = client.models.generate_content(
            model=self.model, contents=prompt,
            config=types.GenerateContentConfig(temperature=0,
                                               response_mime_type="application/json"))
        return resp.text


def make_client(mode: str = "auto"):
    if mode == "offline":
        return NullClient()
    return GeminiClient(mode=mode)
