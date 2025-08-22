# rag/store.py
import os
import chromadb

# A single persistent Chroma client for the whole app
_ROOT = os.path.join(os.getcwd(), "vectorstore")
os.makedirs(_ROOT, exist_ok=True)

_client = chromadb.PersistentClient(path=_ROOT)

def client():
    return _client

def collection(name: str):
    # create/get a named collection
    return _client.get_or_create_collection(name=name, metadata={"hnsw:space": "cosine"})