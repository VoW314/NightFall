import streamlit as st


# ── Header ────────────────────────────────────────────────────────────────────
st.title("NightFall")
st.subheader("Automated GvG Video Review System for *Where Winds Meet*")
st.divider()

# ── Project Overview ──────────────────────────────────────────────────────────
st.header("About the Project")
st.write(
    "NightFall is an end-to-end AI pipeline that automatically reviews Guild vs Guild "
    "combat footage from *Where Winds Meet*. Raw video is processed by a custom-trained "
    "computer vision model, detection statistics are extracted per frame, and the results "
    "are handed to a GPT-4o coaching AI that gives actionable tactical feedback — all without "
    "manual review."
)

st.divider()

# ── Key Stats ─────────────────────────────────────────────────────────────────
st.header("Project Stats")
col1, col2, col3 = st.columns(3)
col1.metric("Training Images", "~6.2k", help="Individual labelled frames from multiple match perspectives")
col2.metric("Model", "YOLOv11", help="Custom-trained locally on GvG footage")
col3.metric("Coach AI", "GPT-4o", help="Powered by OpenAI Responses API with file search")

st.divider()

# ── How It Works ──────────────────────────────────────────────────────────────
st.header("How It Works")

col_a, col_b, col_c = st.columns(3)

with col_a:
    st.markdown("### 1 — Collect")
    st.write(
        "GvG match footage is recorded and organised. Video data is gathered from "
        "multiple player perspectives to give the model broad coverage of in-game scenarios."
    )

with col_b:
    st.markdown("### 2 — Detect")
    st.write(
        "A custom **YOLOv11** model — trained locally on 6,200 labelled images — processes "
        "the footage frame by frame, tracking players, towers, and objectives. Detection "
        "statistics are compiled into a structured match report."
    )

with col_c:
    st.markdown("### 3 — Analyse")
    st.write(
        "The match report is passed to a **GPT-4o** coaching AI. The AI cross-references "
        "the stats against the Nightfall Ruleset (the guild's strategic playbook) and "
        "returns a structured coaching breakdown."
    )

st.divider()

# ── Roadmap ───────────────────────────────────────────────────────────────────
st.header("Current Development")
st.write("The project is actively expanding. Work in progress:")

st.markdown(
    """
- **OCR Integration** — Optical character recognition is being developed to automatically read
  post-game scoreboards, supplementing the frame-by-frame detection stats with official end-screen data.
- **Additional Match Pages** — More GvG sessions will be added to the League Matches section over time.
- **Expanded Ruleset** — The Nightfall Ruleset document will grow as guild strategy evolves.
- **Version 3** — An updated version of the custom YOLOv11 model. Version 2 used about 6k images in total, but the model only used the 3k+ images for training.
"""
)

st.divider()

# ── Footer ────────────────────────────────────────────────────────────────────
st.divider()
st.write("For getting a version of the model: spartaiger314@gmail.com")
st.markdown(
    "<div style='text-align: center; color: grey; font-size: 0.8em;'>"
    "Powered by <a href='https://openai.com' target='_blank' style='color: grey;'>OpenAI</a>"
    " &nbsp;|&nbsp; "
    "Built by <a href='https://vow314.github.io' target='_blank' style='color: grey;'>Shreyas</a>"
        " &nbsp;|&nbsp; "
    "Request model file by emailing: spartaiger314@gmail.com</a>"
    "</div>",
    unsafe_allow_html=True,
)
