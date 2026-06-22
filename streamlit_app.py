import streamlit as st
from matches_config import MATCHES

st.set_page_config(layout="wide", page_title="NightFall App")

home = st.Page("pages/home.py", title="Home", icon="🏠")
demo = st.Page("pages/demo.py", title="Demo", icon="⚽")

# Build one nav entry per match from the central registry.
# Adding a new match only requires editing matches_config.py + creating its page file.
match_pages = [
    st.Page(m["page_file"], title=m["nav_label"], icon="⚔️")
    for m in MATCHES
]

pg = st.navigation({
    "": [home, demo],
    "League Matches": match_pages,
})

pg.run()
