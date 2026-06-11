import streamlit as st
from utils.vector_store_manager import ensure_vector_store


def _get_secret(key: str, default: str = "") -> str:
    try:
        return st.secrets[key]
    except (KeyError, FileNotFoundError):
        return default


st.title("Welcome to NightFall by Shreyas")
st.write("This dashboard is an AI-powered Guild vs Guild performance analysis tool.")
st.write("Use the navigation on the left to explore different sections. For now, only the demo page is available.")


st.write("Please wait for the Ruleset to be synced before continuing.")
# ── Ruleset sync ──────────────────────────────────────────────────────────────
# Runs on every home page load. Fast when documents haven't changed (hash match);
# only does real API work when a document is added or edited.
st.divider()
st.subheader("Ruleset Status")

OPENAI_API_KEY = _get_secret("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    st.warning(
        "OpenAI API key not configured.  "
        "Add `OPENAI_API_KEY` to `.streamlit/secrets.toml` and restart."
    )
else:
    try:
        with st.spinner("Checking ruleset documents for updates..."):
            vs_id, was_rebuilt = ensure_vector_store(OPENAI_API_KEY)

        if was_rebuilt:
            st.success("Ruleset documents updated — vector store rebuilt and ready.")
        else:
            st.success("Ruleset is current. No changes detected.")

    except FileNotFoundError as e:
        st.warning(str(e))
    except Exception as e:
        st.error(f"Ruleset sync failed: {e}")
