"""
utils/vector_store_manager.py
------------------------------
Manages the lifecycle of the OpenAI Vector Store for NightFall.

How change detection works:
  1. compute_docs_hash() hashes every file in documents/ by name + content.
  2. ensure_vector_store() compares that hash to the one stored in
     vector_store_config.json from the last successful build.
  3. If the hash matches → return the existing vector store ID immediately (no API calls).
  4. If the hash differs (new file, edited file, deleted file) → _build_vector_store()
     uploads everything and creates a fresh store, then saves the new hash.

_build_vector_store is decorated with @st.cache_resource and keyed on
(api_key, docs_hash), so within a single running Streamlit process it only
executes once per unique document state — even if home.py reruns.
"""

import hashlib
import json
from pathlib import Path
from openai import OpenAI
import streamlit as st

DOCS_DIR = Path("documents")
CONFIG_PATH = Path("vector_store_config.json")
VECTOR_STORE_NAME = "Nightfall Ruleset"
SUPPORTED_EXTENSIONS = {".txt", ".md", ".pdf"}


def compute_docs_hash() -> str:
    """SHA-256 fingerprint of all documents — changes whenever any file is added, edited, or removed."""
    files = sorted(
        f for f in DOCS_DIR.iterdir()
        if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS
    )
    h = hashlib.sha256()
    for f in files:
        h.update(f.name.encode())   # catches renames
        h.update(f.read_bytes())    # catches content edits
    return h.hexdigest()


def load_config() -> dict:
    """Read the persisted vector store config, or return empty dict if it doesn't exist."""
    if CONFIG_PATH.exists():
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    return {}


def _save_config(vector_store_id: str, docs_hash: str) -> None:
    CONFIG_PATH.write_text(
        json.dumps({"vector_store_id": vector_store_id, "docs_hash": docs_hash}, indent=2),
        encoding="utf-8",
    )


@st.cache_resource
def _build_vector_store(api_key: str, docs_hash: str) -> str:
    """
    Upload every document in DOCS_DIR and create a fresh Vector Store.

    Keyed on docs_hash so the cache busts automatically when documents change.
    Within one server process this is only called once per unique doc state.
    """
    client = OpenAI(api_key=api_key)

    doc_files = sorted(
        f for f in DOCS_DIR.iterdir()
        if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS
    )

    # Upload each file individually; collect the file IDs for batch linking below.
    file_ids: list[str] = []
    for doc in doc_files:
        with open(doc, "rb") as fh:
            uploaded = client.files.create(file=fh, purpose="assistants")
        file_ids.append(uploaded.id)

    # Create the vector store container.
    vector_store = client.vector_stores.create(name=VECTOR_STORE_NAME)

    # create_and_poll sends all file IDs in one request and blocks until OpenAI
    # has finished chunking and indexing every document — the store is fully
    # queryable by the time this call returns.
    client.vector_stores.file_batches.create_and_poll(
        vector_store_id=vector_store.id,
        file_ids=file_ids,
    )

    _save_config(vector_store.id, docs_hash)
    return vector_store.id


def ensure_vector_store(api_key: str) -> tuple[str, bool]:
    """
    Return (vector_store_id, was_rebuilt).

    Rebuilds the store only when the documents fingerprint has changed since the
    last successful build.  Fast no-op on every run where nothing has changed.
    """
    if not DOCS_DIR.exists() or not any(
        f for f in DOCS_DIR.iterdir()
        if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS
    ):
        raise FileNotFoundError(f"No supported documents found in '{DOCS_DIR}/'.")

    current_hash = compute_docs_hash()
    config = load_config()

    # Hash matches and we have a stored ID → nothing to do.
    if config.get("docs_hash") == current_hash and config.get("vector_store_id"):
        return config["vector_store_id"], False

    # Hash changed (or first run) → build a new store.
    vs_id = _build_vector_store(api_key, current_hash)
    return vs_id, True
