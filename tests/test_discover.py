import json

from src.deezer_client import DeezerClient
from src.discover import discover
from src.guardrails import check_suggestions
from src.llm_client import LLMResult, NullClient
from src.recommender import load_songs

SONGS = load_songs("data/songs_sample.csv")
NOTES = {"genre:lofi": "Lofi is mellow.", "mood:chill": "Chill is easygoing."}


class FakeLLM:
    def __init__(self, text=None, source="live"):
        self.text, self.source, self.prompts = text, source, []

    def complete(self, prompt, purpose=""):
        self.prompts.append(prompt)
        return LLMResult(self.text, self.source)


def fake_deezer(known):
    """known: {(title, artist): id}. Anything else is 'not on Deezer'."""
    def fetch(url):
        items = [{"id": i, "title": t, "title_short": t, "artist": {"name": a},
                  "link": f"https://www.deezer.com/track/{i}", "album": {"cover_medium": ""}}
                 for (t, a), i in known.items()]
        return {"data": items}
    return DeezerClient(fetch=fetch, pause=0)


def answer(*songs):
    return json.dumps({"songs": [{"title": t, "artist": a, "reason": r} for t, a, r in songs]})


# --- output guardrail ---------------------------------------------------------
def test_suggestions_drop_bad_items_and_duplicates():
    raw = {"songs": [{"title": "A", "artist": "X", "reason": "fine"}, "junk",
                     {"title": "A", "artist": "X"}, {"title": "", "artist": "Y"},
                     {"title": "B" * 500, "artist": "Y"}]}
    clean, issues = check_suggestions(raw, 5)
    assert [s["title"] for s in clean] == ["A"] and len(issues) == 4


def test_suggestion_reasons_with_numbers_links_or_other_songs_are_blanked():
    raw = {"songs": [{"title": "Song One", "artist": "Alpha", "reason": "Runs at 120 bpm"},
                     {"title": "Song Two", "artist": "Beta", "reason": "see https://x.io"},
                     {"title": "Song Three", "artist": "Gamma", "reason": "Better than Song One"},
                     {"title": "Song Four", "artist": "Delta", "reason": "Warm and mellow"}]}
    clean, _ = check_suggestions(raw, 5)
    assert [s["reason"] for s in clean] == ["", "", "", "Warm and mellow"]


def test_suggestions_not_a_list():
    assert check_suggestions({"songs": "nope"}, 5)[0] == []
    assert check_suggestions("garbage", 5)[0] == []


def test_suggestions_capped_at_k():
    raw = {"songs": [{"title": f"T{i}", "artist": "A"} for i in range(9)]}
    assert len(check_suggestions(raw, 3)[0]) == 3


# --- flow ---------------------------------------------------------------------
def test_ai_path_plays_verified_songs_and_drops_hallucinations():
    llm = FakeLLM(answer(("Real Song", "Real Band", "Mellow and calm"),
                         ("Made Up Song", "Nobody", "Sounds nice")))
    dz = fake_deezer({("Real Song", "Real Band"): 42})
    res = discover("chill lofi to study", SONGS, llm, dz, NOTES)
    assert res.source == "ai" and [p.title for p in res.picks] == ["Real Song"]
    assert res.picks[0].deezer_id == 42
    assert any("Made Up Song" in i for i in res.issues)


def test_prompt_is_grounded_on_retrieved_notes_and_catalog_candidates():
    llm = FakeLLM(answer(("Real Song", "Real Band", "ok")))
    discover("chill lofi to study", SONGS, llm, fake_deezer({("Real Song", "Real Band"): 1}), NOTES)
    prompt = llm.prompts[0]
    assert "Lofi is mellow." in prompt and "Midnight Coding" in prompt


def test_gemini_failure_falls_back_to_local_list():
    for source in ("error", "budget", "no_key"):
        res = discover("chill lofi to study", SONGS, FakeLLM(None, source), fake_deezer({}), NOTES)
        assert res.source == "fallback" and res.picks and res.fallback_reason
        assert all(p.origin == "catalog" for p in res.picks)


def test_invalid_json_falls_back():
    res = discover("chill lofi to study", SONGS, FakeLLM("not json"), fake_deezer({}), NOTES)
    assert res.source == "fallback"


def test_nothing_verifies_falls_back():
    llm = FakeLLM(answer(("Ghost", "Nobody", "x")))
    res = discover("chill lofi to study", SONGS, llm, fake_deezer({}), NOTES)
    assert res.source == "fallback" and "Deezer" in res.fallback_reason


def test_use_ai_false_never_calls_gemini():
    llm = FakeLLM(answer(("A", "B", "c")))
    res = discover("chill lofi to study", SONGS, llm, fake_deezer({}), NOTES, use_ai=False)
    assert res.source == "fallback" and llm.prompts == []


def test_input_guardrail_rejects_before_any_call():
    llm = FakeLLM(answer(("A", "B", "c")))
    res = discover("   ", SONGS, llm, fake_deezer({}), NOTES)
    assert res.status == "rejected" and llm.prompts == []


def test_free_form_mood_still_reaches_gemini_when_rules_find_nothing():
    llm = FakeLLM(answer(("Real Song", "Real Band", "ok")))
    res = discover("zxqv wibble", SONGS, llm, fake_deezer({("Real Song", "Real Band"): 7}), NOTES)
    assert res.source == "ai" and res.picks


def test_deezer_matching_ignores_feat_and_edit_suffixes():
    dz = fake_deezer({("Get Lucky (Radio Edit)", "Daft Punk"): 5})
    assert dz.find_track("Get Lucky", "Daft Punk").track_id == 5
    assert dz.find_track("Get Lucky", "Someone Else") is None


def test_deezer_failure_returns_none():
    def boom(url):
        raise OSError("down")
    assert DeezerClient(fetch=boom, pause=0).find_track("A", "B") is None


def test_picks_get_a_fresh_preview_url():
    def fetch(url):
        if "/track/" in url:
            return {"preview": "https://cdn.example/p.mp3"}
        return {"data": [{"id": 9, "title": "Real Song", "title_short": "Real Song",
                          "artist": {"name": "Real Band"}, "link": "l", "album": {}}]}
    llm = FakeLLM(answer(("Real Song", "Real Band", "ok")))
    res = discover("chill lofi to study", SONGS, llm, DeezerClient(fetch=fetch, pause=0), NOTES)
    assert res.picks[0].preview_url == "https://cdn.example/p.mp3"


def test_preview_failure_is_empty_not_an_error():
    def boom(url):
        raise OSError("down")
    assert DeezerClient(fetch=boom, pause=0).preview_for(5) == ""
