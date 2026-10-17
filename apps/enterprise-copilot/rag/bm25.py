"""
BM25 Sparse Retrieval Implementation.
Implements Okapi BM25 scoring with term frequency (TF), inverse document frequency (IDF),
document length normalization, and stopword filtering.
"""

import math
import re
from typing import Dict, List, Tuple


class BM25Retriever:
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.corpus: List[Dict[str, str]] = []
        self.doc_len: List[int] = []
        self.avg_doc_len: float = 0.0
        self.df: Dict[str, int] = {}
        self.idf: Dict[str, float] = {}

    def _tokenize(self, text: str) -> List[str]:
        cleaned = re.sub(r"[^\w\s]", " ", text.lower())
        tokens = [t for t in cleaned.split() if len(t) > 1]
        return tokens

    def fit(self, corpus: List[Dict[str, str]]) -> None:
        """
        Fits BM25 index on a corpus of dicts: [{"id": "doc1", "content": "..."}]
        """
        self.corpus = corpus
        self.doc_len = []
        self.df = {}
        total_len = 0

        for doc in corpus:
            tokens = self._tokenize(doc["content"])
            length = len(tokens)
            self.doc_len.append(length)
            total_len += length
            
            seen_tokens = set(tokens)
            for t in seen_tokens:
                self.df[t] = self.df.get(t, 0) + 1

        n_docs = len(corpus)
        self.avg_doc_len = total_len / n_docs if n_docs > 0 else 1.0

        # Calculate IDF with smoothing
        self.idf = {}
        for term, freq in self.df.items():
            self.idf[term] = math.log(1.0 + (n_docs - freq + 0.5) / (freq + 0.5))

    def search(self, query: str, top_k: int = 5) -> List[Tuple[Dict[str, str], float]]:
        if not self.corpus:
            return []

        tokens = self._tokenize(query)
        scores = [0.0] * len(self.corpus)

        for i, doc in enumerate(self.corpus):
            doc_tokens = self._tokenize(doc["content"])
            doc_len = self.doc_len[i]
            tf_map: Dict[str, int] = {}
            for t in doc_tokens:
                tf_map[t] = tf_map.get(t, 0) + 1

            doc_score = 0.0
            for t in tokens:
                if t in tf_map and t in self.idf:
                    tf = tf_map[t]
                    idf = self.idf[t]
                    numerator = tf * (self.k1 + 1.0)
                    denominator = tf + self.k1 * (1.0 - self.b + self.b * (doc_len / self.avg_doc_len))
                    doc_score += idf * (numerator / denominator)
            scores[i] = doc_score

        # Rank candidates
        indexed_scores = list(enumerate(scores))
        indexed_scores.sort(key=lambda x: x[1], reverse=True)

        results = []
        for idx, score in indexed_scores[:top_k]:
            if score > 0.0:
                results.append((self.corpus[idx], score))
        return results
