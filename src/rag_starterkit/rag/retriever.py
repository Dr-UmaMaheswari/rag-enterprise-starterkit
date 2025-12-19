from typing import List, Dict

# Placeholder in-memory store (replace with vector DB later)
_STORE: List[Dict[str, str]] = []

def _load_store():
    return _STORE

def retrieve_context(query: str, top_k: int = 4) -> List[Dict[str, str]]:
    # Very simple retrieval stub: returns first top_k docs
    store = _load_store()
    return store[:top_k]
