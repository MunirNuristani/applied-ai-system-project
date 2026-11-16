"""
CLI for the applied AI system.

  python -m src.app "chill lofi to study to"
  python -m src.app --mode offline "angry punk, high energy"
  python -m src.app --trace "relaxing country road trip"
"""
import argparse
import logging
import sys
from pathlib import Path

from src.llm_client import ROOT, make_client
from src.pipeline import run_pipeline
from src.recommender import MODES, load_songs


def setup_logging() -> None:
    (ROOT / "logs").mkdir(exist_ok=True)
    logging.basicConfig(filename=ROOT / "logs" / "app.log", level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")


def render(res, show_trace: bool) -> str:
    lines = [f"Request: {res.request!r}"]
    if res.status != "ok":
        lines += [f"Status:  {res.status}", res.message]
    else:
        lines += [f"Profile: {res.prefs}  (parsed via {res.parse_source})",
                  f"Confidence: {res.confidence:.2f} | retrieval fit: {res.retrieval_fit}",
                  f"Notes retrieved: {', '.join(res.notes_used) or 'none'}", ""]
        for i, r in enumerate(res.recommendations, 1):
            lines += [f"{i}. {r.song['title']} - {r.song['artist']}  "
                      f"[{r.song['genre']}/{r.song['mood']}] score {r.score:.2f}",
                      f"   {r.explanation}  ({r.explanation_source})"]
    if res.issues:
        lines += ["", "Guardrail notes: " + "; ".join(res.issues)]
    if show_trace:
        lines += ["", "Trace:"] + [f"  - {t}" for t in res.trace]
    return "\n".join(lines)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Music recommender with RAG + guardrails")
    p.add_argument("request", nargs="*", help="what you want to listen to")
    p.add_argument("--mode", choices=["auto", "replay", "offline"], default="auto",
                   help="auto: cache then live Gemini; replay: cache only; offline: no LLM")
    p.add_argument("-k", type=int, default=5)
    p.add_argument("--scoring", choices=list(MODES), default="genre_first")
    p.add_argument("--no-diversity", action="store_true")
    p.add_argument("--trace", action="store_true")
    args = p.parse_args(argv)

    setup_logging()
    request = " ".join(args.request)
    songs = load_songs(str(ROOT / "data" / "songs.csv"))
    res = run_pipeline(request, songs, make_client(args.mode), k=args.k,
                       mode=args.scoring, diversity=not args.no_diversity)
    print(render(res, args.trace))
    return 0 if res.status == "ok" else 2


if __name__ == "__main__":
    sys.exit(main())
