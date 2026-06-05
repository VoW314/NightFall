import streamlit as st
pg = st.navigation([
    st.Page("pages/home.py", title="Home"),
    st.Page("pages/demo.py", title="Demo"),
    st.Page("pages/league_match.py", title="League Matches")
])
pg.run()
