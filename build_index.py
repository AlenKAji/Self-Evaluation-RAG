# build_index.py
import os
import sys
import json
import faiss
import numpy as np
from PyPDF2 import PdfReader
from sentence_transformers import SentenceTransformer
from tqdm import tqdm
import argparse

from config import EMBEDDING_MODEL, get_workspace_paths, DEFAULT_WORKSPACE


def extract_text_from_pdf(pdf_path: str) -> str:
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
    return text.strip()


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50):
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i:i + chunk_size])
        chunks.append(chunk)
    return chunks


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", type=str, default=DEFAULT_WORKSPACE,
                        help="Workspace ID to build index for")
    args = parser.parse_args()
    workspace_id = args.workspace

    data_dir, index_dir, faiss_index_path, meta_path, log_dir = get_workspace_paths(workspace_id)

    print(f"[INFO] Building index for workspace: {workspace_id}")
    print(f"[INFO] Data dir: {data_dir}")
    print(f"[INFO] Index dir: {index_dir}")

    # Cleanup old index/metadata
    for path in (faiss_index_path, meta_path):
        if os.path.exists(path):
            os.remove(path)
            print(f"[CLEANUP] Removed old file: {path}")

    print(f"[INIT] Loading embedding model: {EMBEDDING_MODEL}")
    embedder = SentenceTransformer(EMBEDDING_MODEL)

    pdf_files = [f for f in os.listdir(data_dir) if f.lower().endswith(".pdf")]
    if not pdf_files:
        raise ValueError(f"[ERROR] No PDF files found in '{data_dir}'. Add PDFs and rerun.")

    print(f"[INFO] Found {len(pdf_files)} PDF(s): {pdf_files}")

    documents = []
    metadata = []

    for filename in tqdm(pdf_files, desc="Processing PDFs"):
        pdf_path = os.path.join(data_dir, filename)
        text = extract_text_from_pdf(pdf_path)
        if not text:
            print(f"[WARN] No extractable text in {filename}, skipping.")
            continue
        chunks = chunk_text(text)
        for i, chunk in enumerate(chunks):
            documents.append(chunk)
            metadata.append({
                "source": f"{filename} (chunk {i+1})",
                "text": chunk
            })

    if not documents:
        raise ValueError("[ERROR] No text chunks extracted from any PDF.")

    print(f"[INFO] Total chunks: {len(documents)}")

    print("[STEP] Creating embeddings...")
    embeddings = embedder.encode(documents, show_progress_bar=True)
    embeddings = np.array(embeddings, dtype="float32")

    print("[STEP] Building FAISS index...")
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)

    faiss.write_index(index, faiss_index_path)
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    print("\nIndex build complete.")
    print(f"  FAISS index: {faiss_index_path}")
    print(f"  Metadata:    {meta_path}")


if __name__ == "__main__":
    main()
