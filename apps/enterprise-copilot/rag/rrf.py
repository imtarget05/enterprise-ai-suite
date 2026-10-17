"""
Reciprocal Rank Fusion (RRF) Implementation.
Fuses ranked candidate lists from Dense Retrieval and BM25 Sparse Retrieval.
Standard formula: RRF_score(d) = sum_{m in models} 1 / (k + rank_m(d)), with k=60.
"""

from typing import Dict, List, Tuple, Any


def reciprocal_rank_fusion(
    ranked_lists: List[List[Tuple[Dict[str, Any], float]]],
    k: int = 60,
    top_n: int = 5,
) -> List[Tuple[Dict[str, Any], float]]:
    """
    Takes multiple ranked lists of (doc_dict, score) and combines them using RRF.
    """
    rrf_scores: Dict[str, float] = {}
    doc_lookup: Dict[str, Dict[str, Any]] = {}

    for ranked_list in ranked_lists:
        for rank, (doc, _original_score) in enumerate(ranked_list, start=1):
            doc_id = doc.get("id", str(doc))
            doc_lookup[doc_id] = doc
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + (1.0 / (k + rank))

    # Sort items by accumulated RRF score descending
    sorted_docs = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)

    results = []
    for doc_id, score in sorted_docs[:top_n]:
        results.append((doc_lookup[doc_id], score))

    return results
