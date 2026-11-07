from typing import List, Dict, Any
from .config import TOP_K, MAX_RESULTS, MIN_SIMILARITY
from .indexer import VectorIndexer

def retrieve_evidence(interpretation: Dict[str, Any], indexer: VectorIndexer) -> List[Dict[str, Any]]:
    queries = interpretation.get("search_queries", [])
    if not queries:
        queries = [interpretation.get("resolved_query", "")]

    best_hits = {}
    for q in queries:
        hits = indexer.search(q, top_k=TOP_K)
        for h in hits:
            cid = h["id"]
            if cid not in best_hits or h["similarity"] > best_hits[cid]["similarity"]:
                best_hits[cid] = h

    # Filter by similarity threshold
    filtered = [h for h in best_hits.values() if h["similarity"] >= MIN_SIMILARITY]
    filtered.sort(key=lambda x: x["similarity"], reverse=True)
    return filtered[:MAX_RESULTS]