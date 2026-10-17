"""
Hybrid Document Retriever for Project 1 (Enterprise Copilot).
Combines Qdrant Cloud / Local Vector Search (Dense) + BM25 (Sparse) +
Reciprocal Rank Fusion (RRF k=60) + BGE Reranker.
"""

from typing import Any, Dict, List, Tuple
from apps.enterprise_copilot.backend.config import settings
from apps.enterprise_copilot.rag.bm25 import BM25Retriever
from apps.enterprise_copilot.rag.embeddings import embedding_engine
from apps.enterprise_copilot.rag.rrf import reciprocal_rank_fusion
from apps.enterprise_copilot.rag.reranker import reranker


class HybridRetriever:
    def __init__(self):
        self.bm25 = BM25Retriever()
        self.embedding_engine = embedding_engine
        self.reranker = reranker
        self.qdrant_client = None
        self.in_memory_docs: List[Dict[str, Any]] = []

        if settings.QDRANT_URL:
            try:
                from qdrant_client import QdrantClient
                self.qdrant_client = QdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY)
            except Exception:
                pass

    def index_documents(self, documents: List[Dict[str, Any]]) -> None:
        self.in_memory_docs = documents
        self.bm25.fit(documents)

        if self.qdrant_client:
            try:
                from qdrant_client.http import models
                collections = [c.name for c in self.qdrant_client.get_collections().collections]
                if settings.QDRANT_COLLECTION not in collections:
                    self.qdrant_client.create_collection(
                        collection_name=settings.QDRANT_COLLECTION,
                        vectors_config=models.VectorParams(size=1024, distance=models.Distance.COSINE),
                    )
                points = []
                for i, doc in enumerate(documents):
                    vec = self.embedding_engine.embed_text(doc["content"])
                    points.append(models.PointStruct(id=i + 1, vector=vec, payload=doc))
                self.qdrant_client.upsert(collection_name=settings.QDRANT_COLLECTION, points=points)
            except Exception:
                pass

    def search_dense(self, query: str, top_k: int = 5) -> List[Tuple[Dict[str, Any], float]]:
        query_vec = self.embedding_engine.embed_text(query)
        if self.qdrant_client:
            try:
                results = self.qdrant_client.search(
                    collection_name=settings.QDRANT_COLLECTION,
                    query_vector=query_vec,
                    limit=top_k,
                )
                return [(hit.payload, float(hit.score)) for hit in results if hit.payload]
            except Exception:
                pass

        scored = []
        for doc in self.in_memory_docs:
            doc_vec = self.embedding_engine.embed_text(doc["content"])
            dot = sum(a * b for a, b in zip(query_vec, doc_vec))
            scored.append((doc, dot))
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]

    def search_sparse(self, query: str, top_k: int = 5) -> List[Tuple[Dict[str, Any], float]]:
        return self.bm25.search(query, top_k=top_k)

    def retrieve(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        dense_results = self.search_dense(query, top_k=10)
        sparse_results = self.search_sparse(query, top_k=10)
        rrf_fused = reciprocal_rank_fusion([dense_results, sparse_results], k=60, top_n=8)
        final_ranked = self.reranker.rerank(query, rrf_fused, top_k=top_k)
        results = []
        for doc, score in final_ranked:
            doc_data = dict(doc)
            doc_data["score"] = round(float(score), 4)
            results.append(doc_data)
        return results


hybrid_retriever = HybridRetriever()
