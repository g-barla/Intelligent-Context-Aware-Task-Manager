# rag/query.py
from typing import List
from .store import collection

def query_task(task_id: int, query_text: str, k: int = 3) -> List[str]:
    """
    Query related chunks for this task.
    Returns a list of snippet strings (best efforts).
    """
    coll = collection(f"task_{task_id}")
    if coll.count() == 0:
        return []

    res = coll.query(query_texts=[query_text], n_results=max(1, k))
    # Defensive extraction – Chroma returns a dict with 'documents' as a list of lists
    docs_lists = res.get("documents") or []
    if not docs_lists:
        return []
    return [d for d in docs_lists[0] if d]