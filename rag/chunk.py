# rag/chunk.py
from typing import List

def chunk_text(text: str, max_tokens: int = 500, overlap: int = 100) -> List[str]:
    """
    Very simple chunker by characters (roughly correlated with tokens).
    max_tokens ~= chars here for simplicity.
    """
    if not text:
        return []

    chunks = []
    step = max(1, max_tokens - overlap)
    i = 0
    n = len(text)
    while i < n:
        j = min(i + max_tokens, n)
        chunks.append(text[i:j])
        i += step
    return chunks