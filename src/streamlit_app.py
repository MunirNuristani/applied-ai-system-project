"""
Streamlit UI: describe your mood, Gemini picks songs, Deezer plays them.

  streamlit run src/streamlit_app.py
"""
import logging
import sys
from pathlib import Path

# `streamlit run` puts src/ on sys.path, not the project root; the imports are package-style.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st  # noqa: E402

from src.deezer_client import DeezerClient  # noqa: E402
from src.discover import discover  # noqa: E402
from src.llm_client import ROOT, make_client  # noqa: E402
from src.recommender import load_songs  # noqa: E402

EXAMPLES = [
    "chill lofi beats to study to",
    "angry punk, high energy",
    "a rainy evening, feeling nostalgic",
    "upbeat songs for a road trip",
]

st.set_page_config(page_title="Mood to Music", page_icon="🎵", layout="centered")
st.markdown("""
<style>
.block-container {max-width: 760px; padding-top: 2.5rem;}
.hero h1 {margin-bottom: .1rem;}
.hero p {color: #8a8f98; margin-top: 0;}
.badge {display:inline-block; padding:2px 10px; border-radius:999px; font-size:.78rem;
        background:rgba(128,128,128,.18); margin-right:6px;}
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def _setup():
    (ROOT / "logs").mkdir(exist_ok=True)
    logging.basicConfig(filename=ROOT / "logs" / "app.log", level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    return True


@st.cache_data
def _songs():
    return load_songs(str(ROOT / "data" / "songs.csv"))


@st.cache_resource
def _deezer():
    return DeezerClient()


def _pick_example(text: str) -> None:
    st.session_state.request = text
    st.session_state.run = True


def _search(request: str) -> None:
    use_ai = st.session_state.get("use_ai", True)
    st.session_state.result = discover(request, _songs(), make_client("auto" if use_ai else "offline"),
                                       _deezer(), use_ai=use_ai)


_setup()
st.session_state.setdefault("request", "")
st.session_state.setdefault("run", False)

st.markdown('<div class="hero"><h1>🎵 Mood to Music</h1>'
            '<p>Tell us how you feel. Gemini picks the songs, and you can play a preview of each right here.</p></div>',
            unsafe_allow_html=True)

with st.form("search"):
    st.text_input("How are you feeling?", key="request", placeholder="chill lofi beats to study to",
                  label_visibility="collapsed")
    c1, c2 = st.columns([3, 1.4])
    c1.toggle("Use Gemini", value=True, key="use_ai",
              help="Off: skip Gemini and show the local list, ranked by our own scorer.")
    submitted = c2.form_submit_button("Find songs", type="primary", use_container_width=True)

cols = st.columns(len(EXAMPLES))
for col, ex in zip(cols, EXAMPLES):
    col.button(ex, key=f"ex_{ex}", on_click=_pick_example, args=(ex,), use_container_width=True)

if submitted or st.session_state.run:
    st.session_state.run = False
    if not st.session_state.request.strip():
        st.warning("Type a mood or request first.")
    else:
        with st.spinner("Asking Gemini (a call can take about a minute; repeats are cached)..."
                        if st.session_state.use_ai else "Finding songs..."):
            _search(st.session_state.request)

res = st.session_state.get("result")
if res:
    if res.status == "rejected":
        st.error(res.message)
    elif res.status == "abstained":
        st.warning(res.message)
    else:
        if res.source == "ai":
            st.success("Songs picked by Gemini and found on Deezer.")
        else:
            st.warning(f"Showing the local list. {res.fallback_reason}")
        st.markdown(f'<span class="badge">{"Gemini picks" if res.source == "ai" else "Local list"}</span>'
                    f'<span class="badge">{len(res.picks)} songs</span>', unsafe_allow_html=True)

        for i, p in enumerate(res.picks, 1):
            with st.container(border=True):
                st.subheader(f"{i}. {p.title}")
                st.caption(p.artist + (" · from our catalog" if p.origin == "catalog" else ""))
                st.write(p.reason)
                if p.audio:
                    st.audio(p.audio, format="audio/mpeg")
                    st.caption("30-second preview")
                else:
                    st.caption("No preview available for this song.")

    if res.issues:
        st.info("Guardrail notes: " + "; ".join(res.issues))
    with st.expander("What the system did"):
        st.write(f"Parsed profile: `{res.prefs}` (confidence {res.confidence:.2f})")
        st.write("Notes retrieved: " + (", ".join(res.notes_used) or "none"))
        for t in res.trace:
            st.write(f"- {t}")
