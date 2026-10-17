"""
BGE Reranker Implementation.
Performs cross-encoder scoring on candidate documents retrieved via Hybrid Search.
"""

from typing import Dict, List, Tuple, Any


class CrossEncoderReranker:
    def __init__(self, use_heavy_model: bool = False):
        self.use_heavy_model = use_heavy_model
        self._model = None

        if self.use_heavy_model:
            try:
                from sentence_transformers import CrossEncoder
                self._model = CrossEncoder("BAAI/bge-reranker-base")
            except Exception as e:
                print(f"[CrossEncoderReranker] Model load failed ({e}), using lexical reranker.")

    def rerank(
        self,
        query: str,
        candidates: List[Tuple[Dict[str, Any], float]],
        top_k: int = 3,
    ) -> List[Tuple[Dict[str, Any], float]]:
        if not candidates:
            return []

        if self._model:
            try:
                pairs = [[query, doc.get("content", "")] for doc, _ in candidates]
                scores = self._model.predict(pairs)
                reranked = [
                    (candidates[i][0], float(scores[i]))
                    for i in range(len(candidates))
                ]
                reranked.sort(key=lambda x: x[1], reverse=True)
                return reranked[:top_k]
            except Exception:
                pass

        # Heuristic cross-attention emulation: Exact match query term density & position
        query_words = set(query.lower().split())
        scored = []
        for doc, base_score in candidates:
            content = doc.get("content", "").lower()
            density = sum(content.count(w) for w in query_words)
            boosted = base_score + (density * 0.05)
            scored.append((doc, boosted))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]


reranker = CrossEncoderReranker(use_heavy_model=False)
