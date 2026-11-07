import re
from typing import List, Dict, Any

def validate_and_extract_citations(answer: str, evidence: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    # Match tags like [S1], [S2]
    tags = re.findall(r"\[S(\d+)\]", answer)
    cited_indices = set(int(t) - 1 for t in tags)

    sources = []
    for idx in sorted(cited_indices):
        if 0 <= idx < len(evidence):
            chunk = evidence[idx]
            sources.append({
                "tag": f"[S{idx+1}]",
                "document": chunk["source"],
                "page": chunk["page"],
                "reference": f"{chunk['source']}, p.{chunk['page']}"
            })
    return sources