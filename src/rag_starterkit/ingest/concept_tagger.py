import re
from typing import Dict, List

CONCEPT_PATTERNS = {
    "CTS": [r"\bCTS\b", r"Cheque\s+Truncation\s+System"],
    "PPS": [r"\bPPS\b", r"Positive\s+Pay"],
    "DISHONOUR": [r"\bdishono[u]?r\b", r"return\s+memo", r"unpaid\s+cheque"],
    "OUTSTATION": [r"\boutstation\b", r"\bOMC\b"],
    "IMMEDIATE_CREDIT": [r"immediate\s+credit", r"credit\s+before\s+realization"],
    "RBI_CIRCULAR": [r"\bRBI\b.*\bcircular\b", r"Reserve\s+Bank\s+of\s+India.*circular"],
    "NI_ACT": [r"\bNI\s*Act\b", r"Negotiable\s+Instruments\s+Act"],
}

def tag_concepts(text: str) -> List[str]:
    t = (text or "")
    tags = []
    for concept, pats in CONCEPT_PATTERNS.items():
        for p in pats:
            if re.search(p, t, flags=re.IGNORECASE):
                tags.append(concept)
                break
    return sorted(set(tags))
