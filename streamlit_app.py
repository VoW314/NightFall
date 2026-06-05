import streamlit as st

# Configure the page
st.set_page_config(layout="wide", page_title="NightFall App")

# Define your pages
home = st.Page("pages/home.py", title="Home", icon="🏠")
demo = st.Page("pages/demo.py", title="Demo", icon="⚽")
league = st.Page("pages/league.py", title="League Matches", icon="⚽")

# Create the navigation menu
pg = st.navigation([home, demo, league])

# Run the selected page
pg.run()
