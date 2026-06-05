
import streamlit as st
import pandas as pd
import os

st.title("Demo Analysis")

# 1. Summary
st.header("Project Summary")
st.write("Integration of YOLOv8 results with CSV player statistics. This demo showcases the potential of combining video analysis" \
"with CSV data. Since this is only a demo, the CSV data is not related to the video and is only meant to show that download is possible.")

# 2. The performance video
st.header("Performance Video")
video_path = "vods/demo/Demo.mp4"
if os.path.exists(video_path):
    st.video(video_path)
else:
    st.error(f"Video file not found at: {video_path}")

# 3. CSV stats
st.header("Post-Game Statistics")
csv_path = "data/demo.csv"
if os.path.exists(csv_path):
    df = pd.read_csv(csv_path)
    st.dataframe(df)
    with open(csv_path, "rb") as file:
        st.download_button("Download CSV Stats", file, "demo.csv", "text/csv")
else:
    st.warning("CSV file not found.")

# 4. AI Coach Summary
st.header("AI Coach Summary (WIP)")
if st.button("Generate Coach Analysis"):
    st.info("Currently working on fixing the System Prompt and giving more context")
