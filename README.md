# 🎵 Music Recommender Simulation

## Project Summary

In this project you will build and explain a small music recommender system.

Your goal is to:

- Represent songs and a user "taste profile" as data
- Design a scoring rule that turns that data into recommendations
- Evaluate what your system gets right and wrong
- Reflect on how this mirrors real world AI recommenders

My version, **VibeFinder 1.0**, is a content-based recommender. It loads a 20-song catalog from CSV, scores every song against a user's taste profile (genre, mood, target energy, optional acoustic preference), and returns the top-k songs with a plain-language explanation of each score.

---

## How The System Works

Explain your design in plain language.

Some prompts to answer:

- What features does each `Song` use in your system
  - For example: genre, mood, energy, tempo
- What information does your `UserProfile` store
- How does your `Recommender` compute a score for each song
- How do you choose which songs to recommend

**How real recommenders work (and what mine copies).** Platforms like Spotify and YouTube mix two ideas. *Collaborative filtering* looks at behavior across many users (likes, skips, replays, playlist adds) and assumes people who liked the same things will like the same new things. *Content-based filtering* looks at the attributes of the items themselves (tempo, energy, mood, genre) and finds songs similar to what you already like. Real systems blend both at huge scale and learn their weights from data. My version is purely content-based: it has no other users, only song attributes and a single stated taste profile, and it prioritizes matching genre first, then mood, then how close a song's energy is to the target.

**Song features:** `genre`, `mood`, `energy`, `acousticness` are used in scoring; `tempo_bpm`, `valence` and `danceability` are loaded but not scored yet.

**User profile:** favorite genre, favorite mood, target energy (0-1), and whether they like acoustic music.

**Algorithm recipe (max 4.5 points):**

| Signal | Rule | Points |
|---|---|---|
| Genre | exact match | +2.0 |
| Mood | exact match | +1.0 |
| Energy | `1 - abs(song - target)` (closeness, not "higher is better") | 0 to 1.0 |
| Acousticness | `acousticness` if user likes acoustic, else `1 - acousticness` | 0 to 0.5 |

**Ranking:** score every song, sort descending, take the top k. Each result carries the list of reasons that produced its score. Weights live in `WEIGHTS` in `src/recommender.py` and can be overridden for experiments.

**Known biases:** genre is weighted heaviest, so a genre match can outrank a better mood/energy fit. Exact-string matching means "indie pop" gets no credit for "pop".

---

## Getting Started

### Setup

1. Create a virtual environment (optional but recommended):

   ```bash
   python -m venv .venv
   source .venv/bin/activate      # Mac or Linux
   .venv\Scripts\activate         # Windows

2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Run the app:

```bash
python -m src.main
```

### Running Tests

Run the starter tests with:

```bash
pytest
```

You can add more tests in `tests/test_recommender.py`.

---

## Sample Recommendation Output

Paste a sample of your recommender's output here as a text block so a reader can see what it produces:

Output of `python -m src.main` for the six profiles (the default pop/happy profile is first):

```
Loaded songs: 20

=== High-Energy Pop ===
Profile: {'genre': 'pop', 'mood': 'happy', 'energy': 0.8}
+---+----------------+---------------+-------+------------------------------------------------------------+
| # | Title          | Artist        | Score | Reasons                                                    |
+---+----------------+---------------+-------+------------------------------------------------------------+
| 1 | Sunrise City   | Neon Echo     | 3.98  | genre match (pop) +2.00; mood match (happy) +1.00;         |
|   |                |               |       | energy 0.82 vs target 0.80 +0.98                           |
+---+----------------+---------------+-------+------------------------------------------------------------+
| 2 | Gym Hero       | Max Pulse     | 2.87  | genre match (pop) +2.00; energy 0.93 vs target 0.80 +0.87  |
+---+----------------+---------------+-------+------------------------------------------------------------+
| 3 | Rooftop Lights | Indigo Parade | 1.96  | mood match (happy) +1.00; energy 0.76 vs target 0.80 +0.96 |
+---+----------------+---------------+-------+------------------------------------------------------------+
| 4 | Glass Skyline  | Neon Echo     | 1.90  | mood match (happy) +1.00; energy 0.70 vs target 0.80 +0.90 |
+---+----------------+---------------+-------+------------------------------------------------------------+
| 5 | Concrete Bars  | Kilo Tide     | 0.98  | energy 0.78 vs target 0.80 +0.98                           |
+---+----------------+---------------+-------+------------------------------------------------------------+

=== Chill Lofi ===
Profile: {'genre': 'lofi', 'mood': 'chill', 'energy': 0.4, 'likes_acoustic': True}
+---+--------------------+----------------+-------+-------------------------------------------------------------+
| # | Title              | Artist         | Score | Reasons                                                     |
+---+--------------------+----------------+-------+-------------------------------------------------------------+
| 1 | Library Rain       | Paper Lanterns | 4.38  | genre match (lofi) +2.00; mood match (chill) +1.00;         |
|   |                    |                |       | energy 0.35 vs target 0.40 +0.95; acoustic fit +0.43        |
+---+--------------------+----------------+-------+-------------------------------------------------------------+
| 2 | Midnight Coding    | LoRoom         | 4.33  | genre match (lofi) +2.00; mood match (chill) +1.00;         |
|   |                    |                |       | energy 0.42 vs target 0.40 +0.98; acoustic fit +0.35        |
+---+--------------------+----------------+-------+-------------------------------------------------------------+
| 3 | Focus Flow         | LoRoom         | 3.39  | genre match (lofi) +2.00; energy 0.40 vs target 0.40 +1.00; |
|   |                    |                |       | acoustic fit +0.39                                          |
+---+--------------------+----------------+-------+-------------------------------------------------------------+
| 4 | Afterhours Haze    | LoRoom         | 3.35  | genre match (lofi) +2.00; energy 0.38 vs target 0.40 +0.98; |
|   |                    |                |       | acoustic fit +0.37                                          |
+---+--------------------+----------------+-------+-------------------------------------------------------------+
| 5 | Spacewalk Thoughts | Orbit Bloom    | 2.34  | mood match (chill) +1.00; energy 0.28 vs target 0.40 +0.88; |
|   |                    |                |       | acoustic fit +0.46                                          |
+---+--------------------+----------------+-------+-------------------------------------------------------------+

=== Deep Intense Rock ===
Profile: {'genre': 'rock', 'mood': 'intense', 'energy': 0.92}
+---+----------------+--------------+-------+-------------------------------------------------------+
| # | Title          | Artist       | Score | Reasons                                               |
+---+----------------+--------------+-------+-------------------------------------------------------+
| 1 | Storm Runner   | Voltline     | 3.99  | genre match (rock) +2.00; mood match (intense) +1.00; |
|   |                |              |       | energy 0.91 vs target 0.92 +0.99                      |
+---+----------------+--------------+-------+-------------------------------------------------------+
| 2 | Gym Hero       | Max Pulse    | 1.99  | mood match (intense) +1.00;                           |
|   |                |              |       | energy 0.93 vs target 0.92 +0.99                      |
+---+----------------+--------------+-------+-------------------------------------------------------+
| 3 | Neon Cathedral | Voltline     | 0.97  | energy 0.95 vs target 0.92 +0.97                      |
+---+----------------+--------------+-------+-------------------------------------------------------+
| 4 | Broken Amps    | Static Youth | 0.96  | energy 0.96 vs target 0.92 +0.96                      |
+---+----------------+--------------+-------+-------------------------------------------------------+
| 5 | Sunrise City   | Neon Echo    | 0.90  | energy 0.82 vs target 0.92 +0.90                      |
+---+----------------+--------------+-------+-------------------------------------------------------+

=== Conflicted (classical + angry + max energy) ===
Profile: {'genre': 'classical', 'mood': 'angry', 'energy': 0.95}
+---+----------------+--------------+-------+------------------------------------------------------------+
| # | Title          | Artist       | Score | Reasons                                                    |
+---+----------------+--------------+-------+------------------------------------------------------------+
| 1 | Moonlit Sonata | Elise Arden  | 2.23  | genre match (classical) +2.00;                             |
|   |                |              |       | energy 0.18 vs target 0.95 +0.23                           |
+---+----------------+--------------+-------+------------------------------------------------------------+
| 2 | Broken Amps    | Static Youth | 1.99  | mood match (angry) +1.00; energy 0.96 vs target 0.95 +0.99 |
+---+----------------+--------------+-------+------------------------------------------------------------+
| 3 | Neon Cathedral | Voltline     | 1.00  | energy 0.95 vs target 0.95 +1.00                           |
+---+----------------+--------------+-------+------------------------------------------------------------+
| 4 | Gym Hero       | Max Pulse    | 0.98  | energy 0.93 vs target 0.95 +0.98                           |
+---+----------------+--------------+-------+------------------------------------------------------------+
| 5 | Storm Runner   | Voltline     | 0.96  | energy 0.91 vs target 0.95 +0.96                           |
+---+----------------+--------------+-------+------------------------------------------------------------+

=== Conflicted (sad + max energy) ===
Profile: {'genre': 'pop', 'mood': 'sad', 'energy': 0.9}
+---+----------------+--------------+-------+-----------------------------------------------------------+
| # | Title          | Artist       | Score | Reasons                                                   |
+---+----------------+--------------+-------+-----------------------------------------------------------+
| 1 | Gym Hero       | Max Pulse    | 2.97  | genre match (pop) +2.00; energy 0.93 vs target 0.90 +0.97 |
+---+----------------+--------------+-------+-----------------------------------------------------------+
| 2 | Sunrise City   | Neon Echo    | 2.92  | genre match (pop) +2.00; energy 0.82 vs target 0.90 +0.92 |
+---+----------------+--------------+-------+-----------------------------------------------------------+
| 3 | Storm Runner   | Voltline     | 0.99  | energy 0.91 vs target 0.90 +0.99                          |
+---+----------------+--------------+-------+-----------------------------------------------------------+
| 4 | Neon Cathedral | Voltline     | 0.95  | energy 0.95 vs target 0.90 +0.95                          |
+---+----------------+--------------+-------+-----------------------------------------------------------+
| 5 | Broken Amps    | Static Youth | 0.94  | energy 0.96 vs target 0.90 +0.94                          |
+---+----------------+--------------+-------+-----------------------------------------------------------+

=== Unknown genre (bossa nova) ===
Profile: {'genre': 'bossa nova', 'mood': 'relaxed', 'energy': 0.5}
+---+---------------------+-------------+-------+----------------------------------+
| # | Title               | Artist      | Score | Reasons                          |
+---+---------------------+-------------+-------+----------------------------------+
| 1 | Island Drift        | Sol Coast   | 2.00  | mood match (relaxed) +1.00;      |
|   |                     |             |       | energy 0.50 vs target 0.50 +1.00 |
+---+---------------------+-------------+-------+----------------------------------+
| 2 | Coffee Shop Stories | Slow Stereo | 1.87  | mood match (relaxed) +1.00;      |
|   |                     |             |       | energy 0.37 vs target 0.50 +0.87 |
+---+---------------------+-------------+-------+----------------------------------+
| 3 | Velvet Hours        | Mara Quinn  | 0.98  | energy 0.52 vs target 0.50 +0.98 |
+---+---------------------+-------------+-------+----------------------------------+
| 4 | Dust Road Home      | Cedar Line  | 0.95  | energy 0.55 vs target 0.50 +0.95 |
+---+---------------------+-------------+-------+----------------------------------+
| 5 | Midnight Coding     | LoRoom      | 0.92  | energy 0.42 vs target 0.50 +0.92 |
+---+---------------------+-------------+-------+----------------------------------+
```

The same output is saved in [`outputs/sample_output.txt`](outputs/sample_output.txt).

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or demo video link here -->

---

## Experiments You Tried

Use this section to document the experiments you ran. For example:

**Weight-shift experiment output** (genre 2.0 -> 1.0, energy 1.0 -> 2.0):

```
##### EXPERIMENT: genre weight 2.0 -> 1.0, energy weight 1.0 -> 2.0 #####

=== High-Energy Pop (shifted weights) ===
Profile: {'genre': 'pop', 'mood': 'happy', 'energy': 0.8}
+---+----------------+---------------+-------+------------------------------------------------------------+
| # | Title          | Artist        | Score | Reasons                                                    |
+---+----------------+---------------+-------+------------------------------------------------------------+
| 1 | Sunrise City   | Neon Echo     | 3.96  | genre match (pop) +1.00; mood match (happy) +1.00;         |
|   |                |               |       | energy 0.82 vs target 0.80 +1.96                           |
+---+----------------+---------------+-------+------------------------------------------------------------+
| 2 | Rooftop Lights | Indigo Parade | 2.92  | mood match (happy) +1.00; energy 0.76 vs target 0.80 +1.92 |
+---+----------------+---------------+-------+------------------------------------------------------------+
| 3 | Glass Skyline  | Neon Echo     | 2.80  | mood match (happy) +1.00; energy 0.70 vs target 0.80 +1.80 |
+---+----------------+---------------+-------+------------------------------------------------------------+
| 4 | Gym Hero       | Max Pulse     | 2.74  | genre match (pop) +1.00; energy 0.93 vs target 0.80 +1.74  |
+---+----------------+---------------+-------+------------------------------------------------------------+
| 5 | Concrete Bars  | Kilo Tide     | 1.96  | energy 0.78 vs target 0.80 +1.96                           |
+---+----------------+---------------+-------+------------------------------------------------------------+

=== Conflicted (classical + angry + max energy) (shifted weights) ===
Profile: {'genre': 'classical', 'mood': 'angry', 'energy': 0.95}
+---+----------------+--------------+-------+------------------------------------------------------------+
| # | Title          | Artist       | Score | Reasons                                                    |
+---+----------------+--------------+-------+------------------------------------------------------------+
| 1 | Broken Amps    | Static Youth | 2.98  | mood match (angry) +1.00; energy 0.96 vs target 0.95 +1.98 |
+---+----------------+--------------+-------+------------------------------------------------------------+
| 2 | Neon Cathedral | Voltline     | 2.00  | energy 0.95 vs target 0.95 +2.00                           |
+---+----------------+--------------+-------+------------------------------------------------------------+
| 3 | Gym Hero       | Max Pulse    | 1.96  | energy 0.93 vs target 0.95 +1.96                           |
+---+----------------+--------------+-------+------------------------------------------------------------+
| 4 | Storm Runner   | Voltline     | 1.92  | energy 0.91 vs target 0.95 +1.92                           |
+---+----------------+--------------+-------+------------------------------------------------------------+
| 5 | Sunrise City   | Neon Echo    | 1.74  | energy 0.82 vs target 0.95 +1.74                           |
+---+----------------+--------------+-------+------------------------------------------------------------+
```

**Profiles tested:** High-Energy Pop, Chill Lofi, Deep Intense Rock, plus three adversarial ones: classical + angry + energy 0.95, pop + sad + energy 0.9, and an unknown genre (bossa nova).

**Weight shift (genre 2.0 -> 1.0, energy 1.0 -> 2.0):**
- For High-Energy Pop, #1 stayed the same, but *Gym Hero* (pop, intense) dropped from #2 to #4 and the happy songs *Rooftop Lights* and *Glass Skyline* moved up. Results felt more like the "vibe" and less like the genre label.
- For the conflicted profile, the result flipped. With the original weights, *Moonlit Sonata* (a quiet classical piece) ranked #1 for someone who wanted max energy and anger, purely on the genre bonus. With shifted weights, the angry punk song won, which matches intent better.

**Other observations:**
- Unknown genre: nothing can earn the genre bonus, so mood and energy decide the order. It degraded gracefully (reggae/jazz "relaxed" songs on top).
- Lofi users get a tight cluster of lofi songs because the catalog has four, while most genres have one song, so niche-genre users get little variety.
- Sad + high energy: there is no sad song in the catalog, so the mood preference was silently ignored and the pop genre bonus decided everything.
- Was the shift "more accurate"? For the conflicted profile, yes. For plain pop, it was mostly just different. Genre is a weak proxy for taste but energy alone is too, so neither weighting is clearly right.
- Not tried yet: scoring tempo or valence.

---

## Optional Extensions

All four extensions are implemented; run `python -m src.main` to see each one at the bottom of the output (also in [`outputs/sample_output.txt`](outputs/sample_output.txt)).

1. **Advanced song features.** `data/songs.csv` has 5 new columns: `popularity` (0-100), `release_decade`, `mood_tags` (pipe-separated, e.g. `nostalgic|neon|driving`), `language` and `explicit`. Optional user prefs `popularity`, `decade`, `tags`, `language` and `allow_explicit` add or remove points (decade: full credit for the same decade, half for adjacent; tags: share of the user's tags matched; explicit songs lose 1.0 point if the user says no explicit).
2. **Multiple scoring modes.** `MODES` in `src/recommender.py` holds `genre_first` (default), `mood_first` and `energy_focused`. Call `recommend_songs(prefs, songs, mode="mood_first")`. It is a Strategy pattern: the scoring rule is shared and each mode only supplies its weights. For the High-Energy Pop profile, `genre_first` ranks Gym Hero #2, while `mood_first` and `energy_focused` push it to #4 behind the happy songs.
3. **Diversity penalty.** `recommend_songs(..., diversity=True)` picks songs greedily and subtracts 1.0 for each song by the same artist and 0.5 for each song of the same genre already chosen. For Chill Lofi it breaks up the run of LoRoom tracks (see the output). The penalty appears in each song's reasons.
4. **Visual summary table.** Output uses `format_table()`, a plain-ASCII table with title, artist, score and the wrapped reasons. I used simple formatting instead of `tabulate` so there is no new dependency.

AI workflow notes for extensions 1 and 2 are in [`ai_interactions.md`](ai_interactions.md).

---

## Limitations and Risks

Summarize some limitations of your recommender.

Examples:

- Only 20 songs, and most genres have exactly one, so top-5 lists for niche tastes are padded with energy-only matches.
- Genre and mood are exact string matches with no notion of similarity (indie pop vs pop, chill vs relaxed).
- Genre weight can outrank a much better energy/mood fit (see the classical + angry experiment).
- Ignores lyrics, language, artist, tempo, valence and danceability.
- No diversity control: the top results can be near-duplicates (several LoRoom lofi tracks).
- One fixed profile per user; it cannot model someone with several tastes.

You will go deeper on this in your model card.

---

## Reflection

Read and complete `model_card.md`:

[**Model Card**](model_card.md)

Building this showed me that a recommender is mostly a set of choices about what to measure and how much each thing matters. Turning "taste" into numbers forced me to decide that genre is worth twice a mood match, and that energy should be scored by closeness rather than size. Changing one weight reordered the results, so the "intelligence" lives largely in those hand-picked numbers. Printing the reasons alongside each score made it easy to see why a song ranked where it did, and to catch the odd cases.

Bias can enter through the catalog (genres with one song get thin results), through the features (anything unmeasured, like lyrics or culture, is invisible), and through the weights (a heavy genre weight keeps users inside their stated genre and can trap them in a bubble). A real system would have the same issues at scale, and they'd be harder to see.



