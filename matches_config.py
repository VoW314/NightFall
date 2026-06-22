"""
matches_config.py
-----------------
Central registry for all league matches.

To add a new match:
  1. Append an entry to MATCHES below.
  2. Create a 3-line page file in pages/matches/ — copy june20_26.py as a template.
  3. That's it. The sidebar nav updates automatically from this list.

Field reference:
  id          — unique slug, used as the session_state key and vector store name
  nav_label   — text shown in the sidebar nav
  page_file   — path to the thin page file that calls render_match()
  date        — human-readable match date shown on the page
  teams       — (our_guild, opponent) tuple
  result      — result string shown in the summary card
  csv         — path to the post-game CSV (shown as a table + download button)
  video       — YouTube URL, or None if not yet available
  docs_dir    — folder whose .txt/.md/.pdf files are indexed into this match's vector store
"""

MATCHES = [
    {
        "id": "june20-26",
        "nav_label": "6/20 — Evolux vs Seraph",
        "page_file": "pages/matches/june20_26.py",
        "date": "June 20, 2026",
        "teams": ("Evolux", "Seraph"),
        "result": "Seraph Defeat",
        "csv": "data/league/june20-26.csv",
        "video": "https://www.youtube.com/watch?v=LX_Wfi0nnos",
        # Vector store is built from all supported files found in this folder.
        # Currently contains: post_game.txt, video_stats.txt
        "docs_dir": "page_outputs/june20-26",
    },
]
