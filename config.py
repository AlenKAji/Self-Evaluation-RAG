# config.py
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Root folders (do not use directly for RAG, only via get_workspace_paths)
DATA_ROOT = os.path.join(BASE_DIR, "data")
INDEX_ROOT = os.path.join(BASE_DIR, "index")
LOG_ROOT = os.path.join(BASE_DIR, "logs")

# Make sure roots exist
os.makedirs(DATA_ROOT, exist_ok=True)
os.makedirs(INDEX_ROOT, exist_ok=True)
os.makedirs(LOG_ROOT, exist_ok=True)

# Models
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
GENERATION_MODEL = "gemma3:1b"      # adjust to your actual model
EVALUATION_MODEL = "gemma3:1b"      # or gemma:2b if you use a bigger one

DEFAULT_WORKSPACE = "default"


def sanitize_workspace_id(workspace_id: str) -> str:
    """Make workspace id safe for use in paths."""
    ws = workspace_id.strip().lower()
    if not ws:
        ws = DEFAULT_WORKSPACE
    # basic cleanup: replace spaces and forbidden chars
    for ch in [" ", "/", "\\", ":", ";", "|"]:
        ws = ws.replace(ch, "_")
    return ws


def get_workspace_paths(workspace_id: str):
    """
    Return (data_dir, index_dir, faiss_index_path, meta_path, log_dir)
    for a given workspace.
    """
    ws = sanitize_workspace_id(workspace_id)

    data_dir = os.path.join(DATA_ROOT, ws)
    index_dir = os.path.join(INDEX_ROOT, ws)
    log_dir = os.path.join(LOG_ROOT, ws)

    faiss_index_path = os.path.join(index_dir, "faiss_index.bin")
    meta_path = os.path.join(index_dir, "metadata.json")

    # ensure dirs exist
    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(index_dir, exist_ok=True)
    os.makedirs(log_dir, exist_ok=True)

    return data_dir, index_dir, faiss_index_path, meta_path, log_dir
