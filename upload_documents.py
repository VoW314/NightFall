"""
upload_documents.py
-------------------
One-time setup script: scans the documents/ folder, uploads every .txt/.md/.pdf
to OpenAI Files, creates a Vector Store called "Nightfall Ruleset", then links
all uploaded files into that store in a single batch.

Run this whenever you add new documents:
    python upload_documents.py

Copy the printed VECTOR_STORE_ID into .streamlit/secrets.toml when done.
"""

import os
import re
from pathlib import Path
from openai import OpenAI

# ===== CONFIGURATION =====
# Path to the folder that holds your GvG ruleset documents.
DOCS_DIR = Path(__file__).parent / "documents"

# Name shown in the OpenAI dashboard for this vector store.
VECTOR_STORE_NAME = "Nightfall Ruleset"

# File types the script will pick up.
SUPPORTED_EXTENSIONS = {".txt", ".md", ".pdf"}


# ===== HELPERS =====

def _load_api_key() -> str:
    """Read the API key from .streamlit/secrets.toml, then fall back to env var."""
    secrets_path = Path(__file__).parent / ".streamlit" / "secrets.toml"
    if secrets_path.exists():
        content = secrets_path.read_text(encoding="utf-8")
        match = re.search(r'^OPENAI_API_KEY\s*=\s*["\'](.+?)["\']', content, re.MULTILINE)
        if match:
            return match.group(1)
    return os.environ.get("OPENAI_API_KEY", "")


# ===== MAIN =====

def main():
    api_key = _load_api_key()
    if not api_key:
        raise SystemExit(
            "No API key found. Add OPENAI_API_KEY to .streamlit/secrets.toml "
            "or set it as an environment variable."
        )

    client = OpenAI(api_key=api_key)

    # --- Discover documents ---
    doc_files = sorted(
        f for f in DOCS_DIR.iterdir()
        if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS
    )

    if not doc_files:
        raise SystemExit(f"No supported documents found in: {DOCS_DIR}")

    print(f"Found {len(doc_files)} document(s) in '{DOCS_DIR}':")

    # --- Upload each file to OpenAI Files API ---
    # purpose="assistants" is required for files used with file_search.
    file_ids: list[str] = []
    for doc in doc_files:
        print(f"  Uploading {doc.name!r} ...", end=" ", flush=True)
        with open(doc, "rb") as fh:
            uploaded = client.files.create(file=fh, purpose="assistants")
        file_ids.append(uploaded.id)
        print(f"ok  [{uploaded.id}]")

    # --- Create a fresh Vector Store ---
    print(f"\nCreating vector store '{VECTOR_STORE_NAME}' ...")
    vector_store = client.vector_stores.create(name=VECTOR_STORE_NAME)
    print(f"  Created  [{vector_store.id}]")

    # --- Batch-link all files into the store ---
    # create_and_poll sends every file_id in one request, then polls OpenAI
    # until every document has finished chunking and indexing.  The call
    # blocks here so the store is fully queryable by the time it returns.
    print(f"\nIndexing {len(file_ids)} file(s) into vector store (this may take a moment) ...")
    batch = client.vector_stores.file_batches.create_and_poll(
        vector_store_id=vector_store.id,
        file_ids=file_ids,
    )
    print(f"  Batch status : {batch.status}")
    print(f"  File counts  : {batch.file_counts}")

    # --- Print the ID the user needs to paste into secrets ---
    print(f"\n{'=' * 55}")
    print("Done!  Paste this line into .streamlit/secrets.toml:")
    print(f'\nVECTOR_STORE_ID = "{vector_store.id}"')
    print(f"{'=' * 55}\n")


if __name__ == "__main__":
    main()
