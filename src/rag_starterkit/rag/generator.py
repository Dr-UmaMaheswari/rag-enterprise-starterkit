from typing import List, Dict, Tuple
from rag_starterkit.api.schemas import Citation

def generate_answer(query: str, contexts: List[Dict[str, str]]) -> Tuple[str, List[Citation]]:
    if not contexts:
        return (
            "I don’t have enough context to answer that from the current knowledge base.",
            [],
        )

    # Grounded response stub (replace with LLM call later)
    joined = "\n".join([c["text"] for c in contexts])
    answer = f"Grounded summary based on retrieved context:\n\n{joined[:700]}"

    citations = []
    for c in contexts:
        citations.append(Citation(source_id=c["id"], snippet=c["text"][:240]))
    return answer, citations
