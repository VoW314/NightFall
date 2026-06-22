"""
utils/vector_store_manager.py
------------------------------
Per-page vector store management.

Each page (demo, each league match) gets its own isolated vector store built
from its own source folder.  Stores are identified by a unique store_name and
rebuilt only when the contents of their source folder change.

Config is persisted to vector_store_config.json as a dict keyed by store_name:
    {
      "demo":           {"vector_store_id": "vs_xxx", "docs_hash": "abc..."},
      "league-june21-26": {"vector_store_id": "vs_yyy", "docs_hash": "def..."},
      ...
    }
"""

import hashlib
import json
from pathlib import Path
from openai import OpenAI
import streamlit as st

CONFIG_PATH = Path("vector_store_config.json")
SUPPORTED_EXTENSIONS = {".txt", ".md", ".pdf"}


def compute_docs_hash(docs_dir: str | Path) -> str:
    """SHA-256 fingerprint of all supported files in docs_dir. Returns '' if empty/missing."""
    path = Path(docs_dir)
    if not path.exists():
        return ""
    files = sorted(
        f for f in path.iterdir()
        if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS
    )
    if not files:
        return ""
    h = hashlib.sha256()
    for f in files:
        h.update(f.name.encode())
        h.update(f.read_bytes())
    return h.hexdigest()


def load_config() -> dict:
    if CONFIG_PATH.exists():
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    return {}


def _save_page_config(store_name: str, vector_store_id: str, docs_hash: str) -> None:
    config = load_config()
    config[store_name] = {"vector_store_id": vector_store_id, "docs_hash": docs_hash}
    CONFIG_PATH.write_text(json.dumps(config, indent=2), encoding="utf-8")


@st.cache_resource
def _build_vector_store(api_key: str, store_name: str, docs_hash: str, docs_dir: str) -> str:
    """
    Upload every supported file in docs_dir and create a new Vector Store.

    Keyed on (api_key, store_name, docs_hash) so the cache busts only when that
    page's documents actually change.  Within one server process this runs at
    most once per unique (page, document-state) combination.
    """
    client = OpenAI(api_key=api_key)

    doc_files = sorted(
        f for f in Path(docs_dir).iterdir()
        if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS
    )

    file_ids: list[str] = []
    for doc in doc_files:
        with open(doc, "rb") as fh:
            uploaded = client.files.create(file=fh, purpose="assistants")
        file_ids.append(uploaded.id)

    vs_name = f"Nightfall — {store_name}"
    vector_store = client.vector_stores.create(name=vs_name)

    # create_and_poll links all files in one batch and blocks until every
    # document has been chunked and indexed — the store is query-ready on return.
    client.vector_stores.file_batches.create_and_poll(
        vector_store_id=vector_store.id,
        file_ids=file_ids,
    )

    _save_page_config(store_name, vector_store.id, docs_hash)
    return vector_store.id


def ensure_page_vector_store(
    api_key: str,
    store_name: str,
    docs_dir: str | Path,
) -> tuple[str | None, bool]:
    """
    Return (vector_store_id, was_rebuilt) for a specific page.

    Returns (None, False) when docs_dir is empty or missing — callers should
    skip file_search in that case and show an appropriate message.
    """
    current_hash = compute_docs_hash(docs_dir)

    if not current_hash:
        return None, False

    config = load_config()
    page_cfg = config.get(store_name, {})

    if page_cfg.get("docs_hash") == current_hash and page_cfg.get("vector_store_id"):
        return page_cfg["vector_store_id"], False

    vs_id = _build_vector_store(api_key, store_name, current_hash, str(docs_dir))
    return vs_id, True
