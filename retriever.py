# retriever.py
import os
import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from config import EMBEDDING_MODEL, get_workspace_paths


class HybridRetriever:
    def __init__(self, workspace_id: str, top_k: int = 5):
        self.workspace_id = workspace_id
        self.top_k = top_k

        data_dir, index_dir, index_path, meta_path, log_dir = get_workspace_paths(workspace_id)

        if not (os.path.exists(index_path) and os.path.exists(meta_path)):
            raise FileNotFoundError(
                f"Index or metadata not found for workspace '{workspace_id}'.\n"
                f"Expected:\n  {index_path}\n  {meta_path}\n"
                "Run build_index.py (via the Upload/Build tab) first."
            )

        print(f"[RETRIEVER] Loading FAISS index from {index_path}")
        self.index = faiss.read_index(index_path)

        print(f"[RETRIEVER] Loading metadata from {meta_path}")
        with open(meta_path, "r", encoding="utf-8") as f:
            self.metadata = json.load(f)

        print(f"[RETRIEVER] Loaded {len(self.metadata)} chunks for workspace '{workspace_id}'.")
        self.embedder = SentenceTransformer(EMBEDDING_MODEL)

    def search(self, query: str, top_k: int = None):
        if top_k is None:
            top_k = self.top_k

        query_vec = self.embedder.encode([query])
        query_vec = np.array(query_vec, dtype="float32")

        distances, indices = self.index.search(query_vec, top_k)
        idxs = indices[0]

        contexts = []
        for idx in idxs:
            if 0 <= idx < len(self.metadata):
                contexts.append(self.metadata[idx]["text"])
        return contexts
