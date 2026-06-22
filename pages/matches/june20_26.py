from matches_config import MATCHES
from utils.match_renderer import render_match

render_match(next(m for m in MATCHES if m["id"] == "june20-26"))
