import os
from pathlib import Path
import streamlit as st
import pandas as pd
from openai import OpenAI
from utils.vector_store_manager import ensure_page_vector_store

STORE_NAME  = "demo"
DOCS_DIR    = Path("page_outputs/demo")       # demo_stats.txt lives here
SESSION_KEY = f"vs_{STORE_NAME}"


def _get_secret(key: str, default: str = "") -> str:
    try:
        return st.secrets[key]
    except (KeyError, FileNotFoundError):
        return default


st.title("Demo Analysis")

OPENAI_API_KEY = _get_secret("OPENAI_API_KEY")

# ===== 1. Summary =====
st.header("Project Summary")
st.write(
    "Integration of YOLOv11 results with CSV player statistics. This demo showcases the potential "
    "of combining video analysis with CSV data. Since this is only a demo, the CSV data is not "
    "related to the video and is only meant to show that download is possible."
)

# ===== 2. Performance Video =====
st.header("Performance Video")
st.write("Video Link: https://youtu.be/I8PcqtMnPjc?si=_8Ennu-vqPEu27HZ")
st.video("https://youtu.be/I8PcqtMnPjc?si=_8Ennu-vqPEu27HZ")

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
st.divider()
st.header("AI Coach Analysis")

if not OPENAI_API_KEY:
    st.warning("OpenAI API key not configured. Add `OPENAI_API_KEY` to `.streamlit/secrets.toml`.")
    st.stop()

# -- Vector store blurb --
st.info(
    "**About the Vector Store**\n\n"
    "The Coach AI indexes the stats files in `page_outputs/demo/` into a private Vector Store "
    "so it can search and reference specific data when forming its analysis. "
    "The store is checked once per session — **subsequent interactions on this page are instant**."
)

# -- Session-cached check: only runs the hash comparison + possible rebuild once per session --
if SESSION_KEY not in st.session_state:
    with st.spinner("Checking vector store — this is fast if nothing changed..."):
        vs_id, was_rebuilt = ensure_page_vector_store(OPENAI_API_KEY, STORE_NAME, DOCS_DIR)
    st.session_state[SESSION_KEY] = {"vs_id": vs_id, "rebuilt": was_rebuilt}

cached  = st.session_state[SESSION_KEY]
vs_id   = cached["vs_id"]

if vs_id is None:
    st.warning("No context documents found in `page_outputs/demo/`. Add `.txt` files there to enable the Coach AI.")
    st.stop()

if cached["rebuilt"]:
    st.success("Vector store rebuilt with updated documents — ready.")
else:
    st.success("Vector store is up to date — ready.")

# -- Stats preview --
stats_files = sorted(DOCS_DIR.glob("*.txt"))
if stats_files:
    with st.expander("Files in this page's vector store"):
        for f in stats_files:
            st.markdown(f"**{f.name}**")
            st.code(f.read_text(), language="text")

# -- Generate --
if st.button("Generate Coach Analysis"):
    # Concatenate all txt files in DOCS_DIR as the direct context for the model.
    stats_text = "\n\n".join(
        f"=== {f.name} ===\n{f.read_text()}"
        for f in sorted(DOCS_DIR.glob("*.txt"))
    )

    with st.spinner("Analysing performance..."):
        client = OpenAI(api_key=OPENAI_API_KEY)

        response = client.responses.create(
            model="gpt-4o",
            instructions=(
                "You are an expert GvG (Guild vs Guild) coach for the game Where Winds Meet. "
                "Your job is to analyse detection statistics from a match recording and give "
                "specific, actionable coaching feedback to the team. "
                "Use the documents in the vector store to ground your feedback in the team's "
                "actual strategy and role assignments. "
                "Structure your response with clear sections: Overall Assessment, "
                "What Went Well, Areas to Improve, and Tactical Recommendations."
            ),
            input=(
                f"Here are the automated detection stats from our latest GvG session:\n\n"
                f"{stats_text}\n\n"
                "Please analyse our performance and provide coaching feedback."
            ),
            tools=[{"type": "file_search", "vector_store_ids": [vs_id]}],
        )

    st.success("Analysis complete!")
    st.markdown(response.output_text)
