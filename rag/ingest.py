# rag/ingest.py
import os
from typing import Tuple
from pypdf import PdfReader

from .store import collection
from .chunk import chunk_text

def _load_text(path: str) -> Tuple[str, str]:
    """
    Returns (text, mime) from TXT or PDF.
    Raises on unsupported type or empty extraction.
    """
    ext = os.path.splitext(path)[1].lower()
    if ext == ".txt":
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            txt = f.read()
        if not txt.strip():
            raise ValueError("TXT file is empty after reading.")
        return txt, "text/plain"

    if ext == ".pdf":
        reader = PdfReader(path)
        pages = []
        for p in reader.pages:
            pages.append(p.extract_text() or "")
        txt = "\n".join(pages)
        if not txt.strip():
            raise ValueError("PDF text extraction returned empty string.")
        return txt, "application/pdf"

    raise ValueError(f"Unsupported file type: {ext}")

def ingest_file(task_id: int, path: str):
    """
    Reads file, chunks it, and adds chunks to Chroma collection "task_<id>".
    Each chunk becomes a separate doc with metadata 'src' and 'chunk_idx'.
    """
    # --- loud logging ---
    print(f"[RAG] ingest_file: task_id={task_id}, path={path}")

    text, mime = _load_text(path)
    print(f"[RAG] loaded {len(text)} chars (mime={mime})")

    chunks = chunk_text(text, max_tokens=1200, overlap=200)  # generous chunk size
    if not chunks:
        raise ValueError("No chunks produced from document.")

    coll = collection(f"task_{task_id}")
    print(f"[RAG] collection name: task_{task_id} (currently {coll.count()} docs)")

    ids = []
    metadatas = []
    docs = []

    base = os.path.basename(path)
    for i, ch in enumerate(chunks):
        ids.append(f"{base}-{i}")
        metadatas.append({"src": base, "chunk_idx": i})
        docs.append(ch)

    coll.add(ids=ids, metadatas=metadatas, documents=docs)
    print(f"[RAG] added {len(docs)} chunks. New count = {coll.count()}")