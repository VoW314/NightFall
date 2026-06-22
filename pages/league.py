import os
import streamlit as st
import pandas as pd
from openai import OpenAI
from utils.vector_store_manager import load_config


def _get_secret(key: str, default: str = "") -> str:
    try:
        return st.secrets[key]
    except (KeyError, FileNotFoundError):
        return default


st.title("League Matches")
st.write("Competitive GvG match records with full AI coaching analysis.")
st.divider()

# ── Match selector ────────────────────────────────────────────────────────────
# Add new matches to this list as they are recorded.
MATCHES = [
    {
        "label": "2026-06-21 - Evolux vs Seraph",
        "date": "June 21, 2026",
        "teams": ("Evolux", "Seraph"),
        "result": "Seraph Lost",
        "result_color": "red",
        "csv": "data/june21-26.csv",
        "video": "https://www.youtube.com/watch?v=LX_Wfi0nnos",
        "stats": "page_outputs/league/june21-26_stats.txt",   # add when available
    },
]

selected_label = st.selectbox("Select a match", [m["label"] for m in MATCHES])
match = next(m for m in MATCHES if m["label"] == selected_label)

st.divider()

# ── 1. Match Summary ──────────────────────────────────────────────────────────
st.header("Match Summary")

col1, col2, col3 = st.columns(3)
col1.metric("Date", match["date"])
col2.metric("Match-up", f"{match['teams'][0]} vs {match['teams'][1]}")
col3.metric("Result", match["result"])

st.divider()

# ── 2. Performance Video ──────────────────────────────────────────────────────
st.header("Performance Video")
if match["video"]:
    st.video(match["video"])
else:
    st.info("Video recording not yet available for this match.")

st.divider()

# ── 3. Post-Game Statistics ───────────────────────────────────────────────────
st.header("Post-Game Statistics")
if match["csv"] and os.path.exists(match["csv"]):
    df = pd.read_csv(match["csv"])
    st.dataframe(df)
    fname = os.path.basename(match["csv"])
    with open(match["csv"], "rb") as f:
        st.download_button("Download CSV Stats", f, fname, "text/csv")
else:
    st.info("CSV stats not yet available for this match.")

st.divider()

# ── 4. AI Coach Analysis ──────────────────────────────────────────────────────
st.header("AI Coach Analysis")

OPENAI_API_KEY  = _get_secret("OPENAI_API_KEY")
VECTOR_STORE_ID = load_config().get("vector_store_id", "")

if not OPENAI_API_KEY:
    st.warning("OpenAI API key not configured. Add `OPENAI_API_KEY` to `.streamlit/secrets.toml`.")
    st.stop()

if not VECTOR_STORE_ID:
    st.info(
        "The Nightfall Ruleset hasn't been indexed yet. "
        "Please visit the **Home** page first — it sets up the vector store automatically."
    )
    st.stop()

stats_path = match.get("stats", "")
if not stats_path or not os.path.exists(stats_path):
    st.info("Detection stats for this match are not yet available. Coach analysis will be enabled once they are added.")
    st.stop()

with st.expander("Detection stats that will be analysed"):
    st.code(open(stats_path).read(), language="text")

if st.button("Generate Coach Analysis"):
    stats_text = open(stats_path).read()
    context = (
        f"Match date: {match['date']}\n"
        f"Teams: {match['teams'][0]} vs {match['teams'][1]}\n"
        f"Result: {match['result']}\n\n"
        f"{stats_text}"
    )

    with st.spinner("Analysing performance against the Nightfall Ruleset..."):
        client = OpenAI(api_key=OPENAI_API_KEY)

        response = client.responses.create(
            model="gpt-4o",
            instructions=(
                "You are an expert GvG (Guild vs Guild) coach for the game Where Winds Meet. "
                "Analyse the provided match detection statistics and give specific, actionable "
                "coaching feedback. Use the Nightfall Ruleset documents to ground your feedback "
                "in the team's actual strategy and role assignments. "
                "Structure your response with clear sections: Overall Assessment, "
                "What Went Well, Areas to Improve, and Tactical Recommendations."
            ),
            input=(
                f"Here are the details and detection stats from a league GvG match:\n\n"
                f"{context}\n\n"
                "Please analyse our performance and provide coaching feedback based on the Nightfall Ruleset."
            ),
            tools=[{
                "type": "file_search",
                "vector_store_ids": [VECTOR_STORE_ID],
            }],
        )

    st.success("Analysis complete!")
    st.markdown(response.output_text)
