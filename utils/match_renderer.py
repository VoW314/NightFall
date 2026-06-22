"""
utils/match_renderer.py
------------------------
Shared rendering logic for all league match pages.

Each match's vector store is built from the files in its docs_dir
(defined in matches_config.py).  The vector store ID is cached in
st.session_state so the check only runs once per browser session —
no spinner on every button click.
"""

import os
from pathlib import Path
import streamlit as st
import pandas as pd
from openai import OpenAI
from utils.vector_store_manager import ensure_page_vector_store


def _get_secret(key: str, default: str = "") -> str:
    try:
        return st.secrets[key]
    except (KeyError, FileNotFoundError):
        return default


def render_match(match: dict) -> None:
    team_a, team_b = match["teams"]
    match_id    = match["id"]
    docs_dir    = Path(match["docs_dir"])
    store_name  = f"league-{match_id}"
    session_key = f"vs_{store_name}"

    st.title(f"{team_a} vs {team_b}")
    st.caption(match["date"])
    st.divider()

    # ── 1. Match Summary ──────────────────────────────────────────────────────
    st.header("Match Summary")
    col1, col2, col3 = st.columns(3)
    col1.metric("Date", match["date"])
    col2.metric("Match-up", f"{team_a} vs {team_b}")
    col3.metric("Result", match["result"])
    st.divider()

    # ── 2. Performance Video ──────────────────────────────────────────────────
    st.header("Performance Video")
    if match.get("video"):
        st.video(match["video"])
    else:
        st.info("Video recording not yet available for this match.")
    st.divider()

    # ── 3. Post-Game Statistics ───────────────────────────────────────────────
    st.header("Post-Game Statistics")
    csv_path = match.get("csv", "")
    if csv_path and os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        st.dataframe(df)
        fname = os.path.basename(csv_path)
        with open(csv_path, "rb") as f:
            st.download_button("Download CSV Stats", f, fname, "text/csv")
    else:
        st.info("CSV stats not yet available for this match.")
    st.divider()

    # ── 4. AI Coach Analysis ──────────────────────────────────────────────────
    st.header("AI Coach Analysis")

    OPENAI_API_KEY = _get_secret("OPENAI_API_KEY")

    if not OPENAI_API_KEY:
        st.warning("OpenAI API key not configured. Add `OPENAI_API_KEY` to `.streamlit/secrets.toml`.")
        return

    # -- Vector store blurb --
    st.info(
        f"**About the Vector Store**\n\n"
        f"The Coach AI indexes the context files for this match (`{docs_dir}/`) into a private "
        f"Vector Store so it can search and reference specific data — post-game stats, video stats, "
        f"and any other documents added to that folder. "
        f"The store is checked once per session — **subsequent interactions on this page are instant**."
    )

    # -- Session-cached check --
    if session_key not in st.session_state:
        with st.spinner(f"Checking vector store for {match['date']} match — fast if nothing changed..."):
            vs_id, was_rebuilt = ensure_page_vector_store(OPENAI_API_KEY, store_name, docs_dir)
        st.session_state[session_key] = {"vs_id": vs_id, "rebuilt": was_rebuilt}

    cached = st.session_state[session_key]
    vs_id  = cached["vs_id"]

    if vs_id is None:
        st.info(
            f"No context documents found in `{docs_dir}/`. "
            "The Coach AI will be enabled once `.txt`, `.md`, or `.pdf` files are added there."
        )
        return

    if cached["rebuilt"]:
        st.success("Vector store rebuilt with updated documents — ready.")
    else:
        st.success("Vector store is up to date — ready.")

    # -- Files preview --
    txt_files = sorted(docs_dir.glob("*.txt")) if docs_dir.exists() else []
    if txt_files:
        with st.expander("Files in this match's vector store"):
            for f in txt_files:
                st.markdown(f"**{f.name}**")
                st.code(f.read_text(), language="text")

    # -- Generate --
    if st.button("Generate Coach Analysis"):
        # Concatenate all txt files from docs_dir as direct context for the model.
        stats_text = "\n\n".join(
            f"=== {f.name} ===\n{f.read_text()}"
            for f in sorted(docs_dir.glob("*.txt"))
        )

        context = (
            f"Match date: {match['date']}\n"
            f"Teams: {team_a} vs {team_b}\n"
            f"Result: {match['result']}\n\n"
            f"{stats_text}"
        )

        with st.spinner("Analysing performance..."):
            client = OpenAI(api_key=OPENAI_API_KEY)
            response = client.responses.create(
                model="gpt-4o",
                instructions=(
                    "You are an expert GvG (Guild vs Guild) coach for the game Where Winds Meet. "
                    "Analyse the provided match detection statistics and give specific, actionable "
                    "coaching feedback. Use the documents in the vector store to ground your feedback "
                    "in the team's actual strategy and role assignments. "
                    "Structure your response with clear sections: Overall Assessment, "
                    "What Went Well, Areas to Improve, and Tactical Recommendations."
                ),
                input=(
                    f"Here are the details and context files from a league GvG match:\n\n"
                    f"{context}\n\n"
                    "Please analyse our performance and provide coaching feedback."
                ),
                tools=[{"type": "file_search", "vector_store_ids": [vs_id]}],
            )

        st.success("Analysis complete!")
        st.markdown(response.output_text)
