import json
from typing import Dict, List, Tuple
from rag_starterkit.rag.embeddings import embed_texts
import numpy as np

def _cos(a: np.ndarray, b: np.ndarray) -> float:
    a = a / (np.linalg.norm(a) + 1e-12)
    b = b / (np.linalg.norm(b) + 1e-12)
    return float(a @ b)

def build_relations(chunks: List[Dict], out_path: str, build_similarity: bool = True, sim_threshold: float = 0.78):
    """
    chunks: list of dicts with keys:
      - chunk_id, doc_id, bank (optional), text, concept_tags (list[str])
    """
    rel = {"concept_edges": [], "similarity_edges": []}

    # Concept edges
    concept_map: Dict[str, List[str]] = {}
    for c in chunks:
        for tag in c.get("concept_tags", []):
            concept_map.setdefault(tag, []).append(c["chunk_id"])

    for concept, ids in concept_map.items():
        if len(ids) < 2:
            continue
        # connect all-to-all lightly (or star pattern). Use star to keep edges small.
        hub = ids[0]
        for other in ids[1:]:
            rel["concept_edges"].append({"type": "CONCEPT_SHARED", "concept": concept, "from": hub, "to": other})

    # Similarity edges (cross-document only)
    if build_similarity and len(chunks) > 2:
        texts = [c["text"][:1200] for c in chunks]
        vecs = np.array(embed_texts(texts))
        for i in range(len(chunks)):
            for j in range(i + 1, len(chunks)):
                if chunks[i]["doc_id"] == chunks[j]["doc_id"]:
                    continue
                s = _cos(vecs[i], vecs[j])
                if s >= sim_threshold:
                    rel["similarity_edges"].append({
                        "type": "SIMILAR_TO",
                        "score": s,
                        "from": chunks[i]["chunk_id"],
                        "to": chunks[j]["chunk_id"],
                    })

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(rel, f, ensure_ascii=False, indent=2)

    return rel
