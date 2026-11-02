# AI Interactions Log

> **Stretch features only.** Only fill in the sections that apply to stretch features you attempted. If you did not attempt a stretch feature, leave its section blank or delete it. This file is not required for the core project.

---

## Agentic Workflow (SF8)

> Document your experience using an AI agent (e.g., Cursor Agent, Claude, Copilot) to make multi-step changes autonomously.

**What task did you give the agent?**

Challenge 1: add 5+ new song attributes to the dataset and make the scoring use them. (Claude Code was also used to implement Challenges 2-4 in the same session.)

**Prompts used:**

> "implement the optional extensions and do a commit"

(The extension text from the course instructions had been pasted into the session earlier.)

**What did the agent generate or change?**

- `data/songs.csv`: added `popularity`, `release_decade`, `mood_tags`, `language`, `explicit` for all 20 songs. The values were invented by the agent, not taken from real data.
- `src/recommender.py`: rewrote scoring to a single dict-based `score_song` that handles the new attributes; `Song` and `UserProfile` got optional fields with defaults so the original tests still construct them.
- `src/main.py`, `tests/test_recommender.py`, `README.md`: demo output, 5 new tests, docs.
- Commands run: `python -m src.main`, `pytest`.

**What did you verify or fix manually?**

Checked by running the code, not just reading it: `pytest` passes (7 tests), and the printed reasons show each new rule firing (decade, tags, popularity, language, explicit). Things to review by hand: the invented attribute values (e.g. the decade for "Moonlit Sonata" is set to 1800 as a stand-in, which only matters for the decade rule), and one odd result in the extended demo, where "Island Drift" ranks #3 for a synthwave fan purely because of decade, popularity and language. That is the scoring behaving as written, but it shows the new weights can add noise.

---

## Design Pattern (SF10)

> Document how AI helped you choose or implement a design pattern.

**Which design pattern did you use?**

Strategy.

**How did AI help you brainstorm or implement it?**

Claude Code proposed treating a scoring mode as a named set of weights, with one shared scoring function, instead of separate scoring functions per mode. That keeps the code modular: adding a mode is one dictionary entry and no change to scoring logic.

**How does the pattern appear in your final code?**

`ScoringMode` and the `MODES` registry in `src/recommender.py`; `recommend_songs(..., mode=...)` looks up the strategy and passes its weights to `score_song`. `src/main.py` loops over `MODES` to compare them.
