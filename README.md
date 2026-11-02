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

Output of `python -m src.main` for the five profiles (the default pop/happy profile is first):

```
Loaded songs: 20

=== High-Energy Pop ===
Profile: {'genre': 'pop', 'mood': 'happy', 'energy': 0.8}
1. Sunrise City by Neon Echo [pop/happy] - 3.98
   Because: genre match (pop) +2.0; mood match (happy) +1.0; energy 0.82 vs target 0.80 +0.98
2. Gym Hero by Max Pulse [pop/intense] - 2.87
   Because: genre match (pop) +2.0; energy 0.93 vs target 0.80 +0.87
3. Rooftop Lights by Indigo Parade [indie pop/happy] - 1.96
   Because: mood match (happy) +1.0; energy 0.76 vs target 0.80 +0.96
4. Glass Skyline by Neon Echo [synthwave/happy] - 1.90
   Because: mood match (happy) +1.0; energy 0.70 vs target 0.80 +0.90
5. Concrete Bars by Kilo Tide [hip hop/confident] - 0.98
   Because: energy 0.78 vs target 0.80 +0.98

=== Chill Lofi ===
Profile: {'genre': 'lofi', 'mood': 'chill', 'energy': 0.4, 'likes_acoustic': True}
1. Library Rain by Paper Lanterns [lofi/chill] - 4.38
   Because: genre match (lofi) +2.0; mood match (chill) +1.0; energy 0.35 vs target 0.40 +0.95; acoustic fit +0.43
2. Midnight Coding by LoRoom [lofi/chill] - 4.33
   Because: genre match (lofi) +2.0; mood match (chill) +1.0; energy 0.42 vs target 0.40 +0.98; acoustic fit +0.35
3. Focus Flow by LoRoom [lofi/focused] - 3.39
   Because: genre match (lofi) +2.0; energy 0.40 vs target 0.40 +1.00; acoustic fit +0.39
4. Afterhours Haze by LoRoom [lofi/moody] - 3.35
   Because: genre match (lofi) +2.0; energy 0.38 vs target 0.40 +0.98; acoustic fit +0.37
5. Spacewalk Thoughts by Orbit Bloom [ambient/chill] - 2.34
   Because: mood match (chill) +1.0; energy 0.28 vs target 0.40 +0.88; acoustic fit +0.46

=== Deep Intense Rock ===
Profile: {'genre': 'rock', 'mood': 'intense', 'energy': 0.92}
1. Storm Runner by Voltline [rock/intense] - 3.99
   Because: genre match (rock) +2.0; mood match (intense) +1.0; energy 0.91 vs target 0.92 +0.99
2. Gym Hero by Max Pulse [pop/intense] - 1.99
   Because: mood match (intense) +1.0; energy 0.93 vs target 0.92 +0.99
3. Neon Cathedral by Voltline [edm/euphoric] - 0.97
   Because: energy 0.95 vs target 0.92 +0.97
4. Broken Amps by Static Youth [punk/angry] - 0.96
   Because: energy 0.96 vs target 0.92 +0.96
5. Sunrise City by Neon Echo [pop/happy] - 0.90
   Because: energy 0.82 vs target 0.92 +0.90

=== Conflicted (classical + angry + max energy) ===
Profile: {'genre': 'classical', 'mood': 'angry', 'energy': 0.95}
1. Moonlit Sonata by Elise Arden [classical/peaceful] - 2.23
   Because: genre match (classical) +2.0; energy 0.18 vs target 0.95 +0.23
2. Broken Amps by Static Youth [punk/angry] - 1.99
   Because: mood match (angry) +1.0; energy 0.96 vs target 0.95 +0.99
3. Neon Cathedral by Voltline [edm/euphoric] - 1.00
   Because: energy 0.95 vs target 0.95 +1.00
4. Gym Hero by Max Pulse [pop/intense] - 0.98
   Because: energy 0.93 vs target 0.95 +0.98
5. Storm Runner by Voltline [rock/intense] - 0.96
   Because: energy 0.91 vs target 0.95 +0.96

=== Conflicted (sad + max energy) ===
Profile: {'genre': 'pop', 'mood': 'sad', 'energy': 0.9}
1. Gym Hero by Max Pulse [pop/intense] - 2.97
   Because: genre match (pop) +2.0; energy 0.93 vs target 0.90 +0.97
2. Sunrise City by Neon Echo [pop/happy] - 2.92
   Because: genre match (pop) +2.0; energy 0.82 vs target 0.90 +0.92
3. Storm Runner by Voltline [rock/intense] - 0.99
   Because: energy 0.91 vs target 0.90 +0.99
4. Neon Cathedral by Voltline [edm/euphoric] - 0.95
   Because: energy 0.95 vs target 0.90 +0.95
5. Broken Amps by Static Youth [punk/angry] - 0.94
   Because: energy 0.96 vs target 0.90 +0.94

=== Unknown genre (bossa nova) ===
Profile: {'genre': 'bossa nova', 'mood': 'relaxed', 'energy': 0.5}
1. Island Drift by Sol Coast [reggae/relaxed] - 2.00
   Because: mood match (relaxed) +1.0; energy 0.50 vs target 0.50 +1.00
2. Coffee Shop Stories by Slow Stereo [jazz/relaxed] - 1.87
   Because: mood match (relaxed) +1.0; energy 0.37 vs target 0.50 +0.87
3. Velvet Hours by Mara Quinn [r&b/romantic] - 0.98
   Because: energy 0.52 vs target 0.50 +0.98
4. Dust Road Home by Cedar Line [country/nostalgic] - 0.95
   Because: energy 0.55 vs target 0.50 +0.95
5. Midnight Coding by LoRoom [lofi/chill] - 0.92
   Because: energy 0.42 vs target 0.50 +0.92
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
1. Sunrise City by Neon Echo [pop/happy] - 3.96
   Because: genre match (pop) +1.0; mood match (happy) +1.0; energy 0.82 vs target 0.80 +1.96
2. Rooftop Lights by Indigo Parade [indie pop/happy] - 2.92
   Because: mood match (happy) +1.0; energy 0.76 vs target 0.80 +1.92
3. Glass Skyline by Neon Echo [synthwave/happy] - 2.80
   Because: mood match (happy) +1.0; energy 0.70 vs target 0.80 +1.80
4. Gym Hero by Max Pulse [pop/intense] - 2.74
   Because: genre match (pop) +1.0; energy 0.93 vs target 0.80 +1.74
5. Concrete Bars by Kilo Tide [hip hop/confident] - 1.96
   Because: energy 0.78 vs target 0.80 +1.96

=== Conflicted (classical + angry + max energy) (shifted weights) ===
Profile: {'genre': 'classical', 'mood': 'angry', 'energy': 0.95}
1. Broken Amps by Static Youth [punk/angry] - 2.98
   Because: mood match (angry) +1.0; energy 0.96 vs target 0.95 +1.98
2. Neon Cathedral by Voltline [edm/euphoric] - 2.00
   Because: energy 0.95 vs target 0.95 +2.00
3. Gym Hero by Max Pulse [pop/intense] - 1.96
   Because: energy 0.93 vs target 0.95 +1.96
4. Storm Runner by Voltline [rock/intense] - 1.92
   Because: energy 0.91 vs target 0.95 +1.92
5. Sunrise City by Neon Echo [pop/happy] - 1.74
   Because: energy 0.82 vs target 0.95 +1.74
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



