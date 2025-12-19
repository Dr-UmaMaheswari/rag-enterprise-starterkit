from pathlib import Path
from rag_starterkit.rag.retriever import _STORE

def ingest_folder(folder_path: str):
    p = Path(folder_path)
    if not p.exists() or not p.is_dir():
        raise ValueError(f"Folder not found: {folder_path}")

    ingested = 0
    for fp in p.glob("*.txt"):
        text = fp.read_text(encoding="utf-8", errors="ignore").strip()
        if text:
            _STORE.append({"id": fp.name, "text": text})
            ingested += 1
    return {"files": ingested}
