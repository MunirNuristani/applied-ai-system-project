"""
End-to-end pipeline:

  request -> normalize_input -> parse (LLM | rules) -> clean_profile (guardrail)
          -> abstain if confidence < MIN_CONFIDENCE
          -> retrieve songs (weighted recommender) -> retrieve notes (RAG)
          -> explain (LLM, grounded) -> check_explanation (guardrail) | template
"""
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from src.explainer import explain
from src.guardrails import MIN_CONFIDENCE, build_catalog, normalize_input
from src.parser import parse_request
from src.rag import load_notes, retrieve_notes
from src.recommender import DEFAULT_MODE, MODES, recommend_songs

log = logging.getLogger("pipeline")


@dataclass
class Recommendation:
    song: Dict
    score: float
    reasons: List[str]
    explanation: str
    explanation_source: str


@dataclass
class PipelineResult:
    request: str
    status: str                      # ok | abstained | rejected
    message: str = ""
    prefs: Dict = field(default_factory=dict)
    issues: List[str] = field(default_factory=list)
    confidence: float = 0.0
    retrieval_fit: Optional[float] = None
    parse_source: str = ""
    recommendations: List[Recommendation] = field(default_factory=list)
    notes_used: List[str] = field(default_factory=list)
    trace: List[str] = field(default_factory=list)


def _max_possible(prefs: Dict, mode: str) -> float:
    w = MODES[mode].weights
    total = 0.0
    for key, weight in (("genre", "genre"), ("mood", "mood"), ("energy", "energy"),
                        ("likes_acoustic", "acoustic"), ("tags", "tags")):
        if prefs.get(key) is not None and prefs.get(key) != []:
            total += w[weight]
    return total


def run_pipeline(request: str, songs: List[Dict], client, notes: Optional[Dict[str, str]] = None,
                 k: int = 5, mode: str = DEFAULT_MODE, diversity: bool = True) -> PipelineResult:
    res = PipelineResult(request=request, status="ok")
    catalog = build_catalog(songs)
    notes = load_notes() if notes is None else notes

    clean, rejection = normalize_input(request)
    if rejection:
        res.status, res.message = "rejected", f"Request rejected: {rejection}."
        res.trace.append(f"input guardrail: {rejection}")
        log.warning("rejected request: %s", rejection)
        return res
    res.request = clean
    res.trace.append("input guardrail: ok")

    parsed = parse_request(clean, catalog, client)
    res.prefs, res.issues = parsed.prefs, parsed.issues
    res.confidence, res.parse_source = parsed.confidence, parsed.source
    res.trace.append(f"parse via {parsed.source}: {parsed.prefs} (confidence {parsed.confidence})")
    for issue in parsed.issues:
        res.trace.append(f"profile guardrail: {issue}")
        log.warning("profile guardrail: %s", issue)

    if parsed.confidence < MIN_CONFIDENCE or not parsed.prefs:
        res.status = "abstained"
        res.message = ("I couldn't tell what you want to listen to. Try naming a genre or mood "
                       f"(e.g. 'chill lofi for studying'). Known genres: {', '.join(sorted(catalog.genres))}.")
        res.trace.append(f"abstained: confidence {parsed.confidence} < {MIN_CONFIDENCE}")
        log.info("abstained on %r", clean)
        return res

    results = recommend_songs(parsed.prefs, songs, k, mode=mode, diversity=diversity)
    dropped = len(results)
    results = [r for r in results if r[1] > 0]   # a 0-score song matched nothing the user asked for
    if len(results) < dropped:
        res.trace.append(f"dropped {dropped - len(results)} result(s) with score <= 0")
    if not results:
        res.status = "abstained"
        res.message = "No songs in the catalog matched that request. Try a different genre or mood."
        res.trace.append("abstained: no results with score > 0")
        return res
    top = results[0][1] if results else 0.0
    denom = _max_possible(parsed.prefs, mode)
    res.retrieval_fit = round(max(0.0, top) / denom, 2) if denom else None
    res.trace.append(f"retrieved {len(results)} songs (top score {top:.2f}, fit {res.retrieval_fit})")

    used = retrieve_notes(parsed.prefs, results, notes)
    res.notes_used = list(used)
    res.trace.append(f"retrieved notes: {res.notes_used}")

    explained = explain(clean, parsed.prefs, results, used, catalog, client)
    for (song, score, why), (text, source) in zip(results, explained):
        res.recommendations.append(Recommendation(song, score, why.split("; "), text, source))
    sources = sorted({r.explanation_source for r in res.recommendations})
    res.trace.append(f"explanations via {sources}")
    return res
