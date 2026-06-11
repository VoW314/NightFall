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


st.title("Demo Analysis")

OPENAI_API_KEY = _get_secret("OPENAI_API_KEY")

# Vector store ID is managed automatically by the home page on every session.
# Reading it from the config file means demo.py always uses whatever store
# was built most recently (home.py rebuilds it when documents change).
VECTOR_STORE_ID = load_config().get("vector_store_id", "")


# ===== 1. Summary =====
st.header("Project Summary")
st.write(
    "Integration of YOLOv8 results with CSV player statistics. This demo showcases the potential "
    "of combining video analysis with CSV data. Since this is only a demo, the CSV data is not "
    "related to the video and is only meant to show that download is possible."
)

# ===== 2. Performance Video =====
st.header("Performance Video")
st.write("Video Link: https://youtu.be/MtBDzws_1Ko")
video_path = "vods/demo/Demo.mp4"
if os.path.exists(video_path):
    st.video(video_path)
else:
    st.error(f"Video file not found at: {video_path}\n Please use the video link above!")

# ===== 3. CSV Stats =====
st.header("Post-Game Statistics")
csv_path = "data/demo.csv"
if os.path.exists(csv_path):
    df = pd.read_csv(csv_path)
    st.dataframe(df)
    with open(csv_path, "rb") as file:
        st.download_button("Download CSV Stats", file, "demo.csv", "text/csv")
else:
    st.warning("CSV file not found.")

# ===== 4. AI Coach Analysis =====
st.header("AI Coach Analysis")

STATS_PATH = "page_outputs/demo/demo_stats.txt"

if not OPENAI_API_KEY:
    st.warning("OpenAI API key not configured. Add `OPENAI_API_KEY` to `.streamlit/secrets.toml`.")
    st.stop()

if not VECTOR_STORE_ID:
    st.info(
        "The Nightfall Ruleset hasn't been indexed yet.  "
        "Please visit the **Home** page first — it will set up the vector store automatically."
    )
    st.stop()

if not os.path.exists(STATS_PATH):
    st.warning(f"Stats file not found at: `{STATS_PATH}`")
    st.stop()

with st.expander("Detection stats that will be analysed"):
    st.code(open(STATS_PATH).read(), language="text")

if st.button("Generate Coach Analysis"):
    stats_text = open(STATS_PATH).read()

    with st.spinner("Analysing performance against the Nightfall Ruleset..."):
        client = OpenAI(api_key=OPENAI_API_KEY)

        # Responses API with file_search: the model retrieves relevant
        # passages from the vector store and weaves them into its analysis.
        response = client.responses.create(
            model="gpt-4o",
            instructions=(
                "You are an expert GvG (Guild vs Guild) coach for the game Where Winds Meet. "
                "Your job is to analyse detection statistics from a match recording and give "
                "specific, actionable coaching feedback to the team. "
                "Use the Nightfall Ruleset documents to ground your feedback in the team's "
                "actual strategy and role assignments. "
                "Structure your response with clear sections: Overall Assessment, "
                "What Went Well, Areas to Improve, and Tactical Recommendations."
            ),
            input=(
                f"Here are the automated detection stats from our latest GvG session:\n\n"
                f"{stats_text}\n\n"
                "Please analyse our performance and provide coaching feedback based on the Nightfall Ruleset."
            ),
            tools=[{
                "type": "file_search",
                "vector_store_ids": [VECTOR_STORE_ID],
            }],
        )

    st.success("Analysis complete!")
    st.markdown(response.output_text)
