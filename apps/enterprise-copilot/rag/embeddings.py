"""
Dense Embedding Engine.
Supports BGE-M3 (1024-dim) in full profile, with lightweight hash-based
or SentenceTransformer fallback for low-resource demo environments.
"""

import hashlib
import math
from typing import List


class DenseEmbeddingEngine:
    def __init__(self, dim: int = 1024, use_heavy_model: bool = False):
        self.dim = dim
        self.use_heavy_model = use_heavy_model
        self._model = None

        if self.use_heavy_model:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer("BAAI/bge-m3")
            except Exception as e:
                print(f"[DenseEmbeddingEngine] BGE-M3 model load failed ({e}), using deterministic hash fallback.")

    def embed_text(self, text: str) -> List[float]:
        if self._model:
            try:
                emb = self._model.encode(text)
                return emb.tolist()
            except Exception:
                pass

        # Deterministic normalized embedding vector fallback (zero-dependency, memory-safe)
        seed = int(hashlib.md5(text.encode("utf-8")).hexdigest()[:8], 16)
        vec = []
        for i in range(self.dim):
            val = math.sin(seed + i * 0.17)
            vec.append(val)
        
        # Normalize to unit length
        norm = math.sqrt(sum(x * x for x in vec)) or 1.0
        return [x / norm for x in vec]

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        return [self.embed_text(t) for t in texts]


embedding_engine = DenseEmbeddingEngine(dim=1024, use_heavy_model=False)
