# 🎧 Model Card: Music Recommender Simulation

## 1. Model Name

**VibeFinder 1.0**

---

## 2. Goal / Task

VibeFinder suggests the top 5 songs from a small catalog. It predicts which songs a user will like, based on a favorite genre, a favorite mood, a target energy level and an optional acoustic preference.

---

## 3. Data Used

- 20 songs in `data/songs.csv`: the 10 starter songs plus 10 I added (country, EDM, R&B, hip hop, classical, punk, folk, reggae, a happy synthwave song and a moody lofi song).
- Each song has: genre, mood, energy, tempo, valence, danceability, acousticness.
- Only genre, mood, energy and acousticness are used in scoring.
- Limits: lofi has 4 songs, pop and synthwave 2 each, and most other genres have just 1. There is no sad song. There are no lyrics, languages, years or popularity data.

---

## 4. Algorithm Summary

Every song gets points for how well it fits the user:

- Same genre: +2 points.
- Same mood: +1 point.
- Energy: up to +1 point. The closer the song's energy is to the target, the more points. A song that is too quiet is penalized the same as one that is too loud.
- Acoustic: up to +0.5 point, for acoustic songs if the user likes them, or non-acoustic songs if not.

Then all songs are sorted from highest to lowest score and the top 5 are shown, each with the reasons for its score. We need two steps because one rule judges a single song, and a second rule compares all the songs to pick the best. The starter code just returned the first songs in the file.

---

## 5. Observed Behavior / Biases

Genre is worth the most points, so it can beat a song that fits the user's mood and energy much better. For example, a user who wants angry, very high-energy music but whose favorite genre is classical gets a quiet classical piece at #1 (score 2.23). It scored only 0.23 on energy, but the genre bonus carried it. Because most genres have only one song, the system also gives lofi fans a full list of good matches, while fans of other genres get one good match followed by songs that only match on energy. Moods that do not exist in the catalog (like "sad") are silently ignored.

---

## 6. Evaluation Process

I ran six profiles and looked at the top 5 for each. I checked whether the obvious best song came first and whether the reasons made sense. Then I ran an experiment: genre weight halved (2.0 to 1.0) and energy weight doubled (1.0 to 2.0). Full outputs are in the README and `outputs/sample_output.txt`. Two automated tests (`pytest`) check the ranking order and that explanations are not empty.

**Profile comparisons:**

- **High-Energy Pop vs Chill Lofi:** Pop gives bright, fast songs (Sunrise City, 0.82 energy). Lofi gives slow, acoustic ones (Library Rain, 0.35 energy). The energy target and genre together pull the lists to opposite ends of the catalog, which is what we want.
- **High-Energy Pop vs Deep Intense Rock:** Both want high energy, so Gym Hero shows up in both. In Pop it is #2 because of the genre match. In Rock it is #2 because of the "intense" mood match. Rock has only one rock song, so after #1 the list is just high-energy songs of any genre.
- **Chill Lofi vs Deep Intense Rock:** Almost no overlap. They are opposites on energy and acousticness, and the lists reflect that.
- **Deep Intense Rock vs Classical + angry (conflicted):** Both want very high energy. Rock puts its genre match first. The conflicted profile instead gets a quiet classical song at #1, because genre outranks energy. That is the clearest sign of the genre bias.
- **Conflicted (sad + max energy) vs High-Energy Pop:** Both are "pop, high energy" but this one wants "sad". No song is sad, so the results are the same pop songs minus the happy-mood boost. The user's mood was ignored, and the system did not tell them.
- **Unknown genre (bossa nova) vs Chill Lofi:** Lofi has many matching songs. Bossa nova has none, so the ranking falls back to mood and energy (relaxed reggae and jazz). It degrades sensibly but gives a less personal list.

**Why does Gym Hero keep showing up for people who want "Happy Pop"?** Gym Hero is a pop song with very high energy (0.93). The user asked for pop, so it gets the big genre bonus. Its energy is close to what they asked for, so it gets almost full energy points. It is not happy (it is "intense"), but missing the mood bonus only costs 1 point, and the genre bonus is worth 2. So an energetic pop workout song still beats happy songs that are not pop. When I shifted weight from genre to energy, Gym Hero dropped from #2 to #4 and the happy songs moved up.

**What surprised me:** one weight change flipped the conflicted profile completely, from a calm classical song to an angry punk song. The punk result matches what the user asked for, but it only "felt" right because I already knew what I wanted. The change was different for plain pop, not clearly better.

---

## 7. Intended Use and Non-Intended Use

**Intended:** classroom exploration of how scoring and ranking can turn data into recommendations, with explanations a person can read.

**Not intended:** real music discovery for real listeners, or any decision that matters. The catalog is tiny, hand-picked, and has no behavior data from real users. It should not be used to judge anyone's taste or to decide what artists get promoted.

---

## 8. Ideas for Improvement

1. Score tempo and valence too, and treat similar genres and moods as partly matching (indie pop is close to pop; chill is close to relaxed).
2. Add a diversity penalty so one artist or genre cannot fill the whole top 5.
3. Tell the user when a preference (like "sad") can't be matched, and grow the catalog so each genre has more than one or two songs.

---

## 9. Personal Reflection

**Biggest learning moment:** seeing one weight change flip the top result for the conflicted profile. It showed me that the "AI" here is really my own choices about what matters, written as numbers.

**How AI helped, and when I double-checked it:** Claude Code wrote the first version of the scoring code, the extra songs and the draft documents quickly. I did not take its word for what the system does. I ran the code and read the actual outputs, and I wrote the profile comparisons and the Gym Hero explanation from those outputs. Anything described in this card was checked against a real run. I also noticed the AI could not read the course instructions behind a login, so I had to supply them myself.

**What surprised me:** how much a few if-statements and an energy gap "feel" like a real recommendation, especially with reasons printed next to each score. Yet the sad-mood case shows how easily it can be wrong without any sign of it.

**What I would try next:** add tempo and valence, a diversity penalty, and more songs per genre. Then I would compare against a collaborative-filtering approach using fake "listening history" for several users.
