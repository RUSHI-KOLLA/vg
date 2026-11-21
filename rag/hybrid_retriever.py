"""
VG Hybrid RAG Retriever — Combines Dense + Sparse + Recency for Superior Retrieval.

Enhancement over basic ChromaDB retrieval:
1. Dense semantic search (existing embeddings)
2. Sparse keyword matching (BM25-style)
3. Recency boosting for time-sensitive queries
4. Re-ranking for final selection
"""

import os
import re
import math
from collections import Counter
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime

# ChromaDB for dense retrieval
try:
    import chromadb
    HAS_CHROMA = True
except ImportError:
    HAS_CHROMA = False

# Fastembed for embeddings
try:
    from fastembed import TextEmbedding
    HAS_EMBEDDINGS = True
except ImportError:
    HAS_EMBEDDINGS = False


# ═══════════════════════════════════════════════════════════════════
#  1. SPARSE RETRIEVER (BM25-style keyword matching)
# ═══════════════════════════════════════════════════════════════════

@dataclass
class SparseIndex:
    """Inverted index for keyword matching."""
    doc_freq: Dict[str, int] = field(default_factory=dict)  # term → doc count
    term_docs: Dict[str, Dict[str, int]] = field(default_factory=dict)  # term → {doc_id: tf}
    doc_lengths: Dict[str, int] = field(default_factory=dict)  # doc_id → word count
    avg_doc_length: float = 0.0
    num_docs: int = 0


class SparseRetriever:
    """
    BM25-style sparse retrieval for keyword matching.
    Complements dense embeddings by catching exact term matches.
    """

    # BM25 parameters
    K1 = 1.5  # Term frequency saturation
    B = 0.75  # Length normalization

    # Stopwords to ignore
    STOPWORDS = {
        "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
        "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
        "being", "have", "has", "had", "do", "does", "did", "will", "would",
        "could", "should", "may", "might", "must", "shall", "can", "need",
        "it", "its", "this", "that", "these", "those", "what", "which",
        "who", "whom", "whose", "when", "where", "why", "how",
    }

    def __init__(self):
        self.index = SparseIndex()
        self.documents: Dict[str, str] = {}  # doc_id → text

    def tokenize(self, text: str) -> List[str]:
        """Tokenize and normalize text."""
        # Lowercase and extract words
        tokens = re.findall(r'\b[a-z]{2,}\b', text.lower())
        # Remove stopwords
        return [t for t in tokens if t not in self.STOPWORDS]

    def add_document(self, doc_id: str, text: str):
        """Add a document to the sparse index."""
        self.documents[doc_id] = text
        tokens = self.tokenize(text)

        # Update doc length
        self.index.doc_lengths[doc_id] = len(tokens)

        # Update term frequencies
        term_counts = Counter(tokens)
        for term, tf in term_counts.items():
            # Update term → doc mapping
            if term not in self.index.term_docs:
                self.index.term_docs[term] = {}
            self.index.term_docs[term][doc_id] = tf

            # Update doc frequency
            if doc_id not in self.index.doc_freq:
                self.index.doc_freq[term] = 0
            self.index.doc_freq[term] += 1

        # Update stats
        self.index.num_docs = len(self.documents)
        total_length = sum(self.index.doc_lengths.values())
        self.index.avg_doc_length = total_length / self.index.num_docs if self.index.num_docs > 0 else 0

    def build_index(self, documents: Dict[str, str]):
        """Build index from multiple documents."""
        for doc_id, text in documents.items():
            self.add_document(doc_id, text)

    def score_bm25(self, query: str, doc_id: str) -> float:
        """Calculate BM25 score for a query-document pair."""
        query_tokens = self.tokenize(query)
        doc_length = self.index.doc_lengths.get(doc_id, 0)

        if doc_length == 0:
            return 0.0

        score = 0.0
        for term in query_tokens:
            # Get term frequency in document
            tf = self.index.term_docs.get(term, {}).get(doc_id, 0)
            if tf == 0:
                continue

            # Get document frequency
            df = self.index.doc_freq.get(term, 0)
            if df == 0:
                continue

            # IDF component
            idf = math.log((self.index.num_docs - df + 0.5) / (df + 0.5) + 1)

            # TF component (saturating)
            tf_normalized = tf * (self.K1 + 1) / (tf + self.K1 * (1 - self.B + self.B * doc_length / self.index.avg_doc_length))

            score += idf * tf_normalized

        return score

    def retrieve(self, query: str, top_k: int = 5) -> List[Tuple[str, float, str]]:
        """
        Retrieve top-k documents for query.

        Returns:
            List of (doc_id, score, text) tuples
        """
        scores = []
        for doc_id in self.documents:
            score = self.score_bm25(query, doc_id)
            if score > 0:
                scores.append((doc_id, score, self.documents[doc_id]))

        # Sort by score descending
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]


# ═══════════════════════════════════════════════════════════════════
#  2. DENSE RETRIEVER (ChromaDB with embeddings)
# ═══════════════════════════════════════════════════════════════════

class DenseRetriever:
    """
    Dense semantic retrieval using ChromaDB and embeddings.
    """

    def __init__(self, chroma_path: str = "./chroma_db"):
        self.chroma_path = chroma_path
        self._client = None
        self._model = None

    def _get_client(self):
        if self._client is None and HAS_CHROMA:
            self._client = chromadb.PersistentClient(path=self.chroma_path)
        return self._client

    def _get_model(self):
        if self._model is None and HAS_EMBEDDINGS:
            self._model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
        return self._model

    def retrieve(self, query: str, collection_name: str, top_k: int = 5) -> List[Tuple[str, float, str]]:
        """
        Retrieve top-k documents from collection.

        Returns:
            List of (doc_id, score, text) tuples
        """
        client = self._get_client()
        model = self._get_model()

        if client is None or model is None:
            return []

        try:
            collection = client.get_collection(name=collection_name)
        except Exception:
            return []

        # Generate query embedding
        try:
            query_embedding = list(model.embed([query]))[0]
        except Exception:
            return []

        # Query collection
        try:
            results = collection.query(
                query_embeddings=query_embedding,
                n_results=top_k,
                include=["documents", "distances"],
            )

            if not results or not results["documents"] or not results["documents"][0]:
                return []

            # ChromaDB returns nested lists
            docs = results["documents"][0]
            distances = results["distances"][0] if results.get("distances") else [0.0] * len(docs)
            ids = results["ids"][0] if results.get("ids") else [str(i) for i in range(len(docs))]

            # Convert distance to similarity (ChromaDB uses L2 distance)
            scores = [1.0 / (1.0 + d) for d in distances]

            return [(ids[i], scores[i], docs[i]) for i in range(len(docs))]

        except Exception:
            return []


# ═══════════════════════════════════════════════════════════════════
#  3. RECENCY BOOSTER (Time-decay scoring)
# ═══════════════════════════════════════════════════════════════════

class RecencyBooster:
    """
    Applies time-decay boosting to retrieval scores.
    Recent documents get a score boost for time-sensitive queries.
    """

    def __init__(self, half_life_days: float = 30.0):
        """
        Args:
            half_life_days: Score halves after this many days
        """
        self.half_life_days = half_life_days

    def boost(self, doc_id: str, base_score: float, doc_date: Optional[datetime] = None) -> float:
        """
        Apply time-decay boost to score.

        Args:
            doc_id: Document identifier
            base_score: Original retrieval score
            doc_date: Document date (if None, uses doc_id as fallback)
        """
        if doc_date is None:
            # Try to extract date from doc_id (assume format: YYYY-MM-DD_*)
            match = re.match(r'(\d{4}-\d{2}-\d{2})_', doc_id)
            if match:
                try:
                    doc_date = datetime.strptime(match.group(1), '%Y-%m-%d')
                except ValueError:
                    pass

        if doc_date is None:
            return base_score  # No date, no boost

        # Calculate days since document
        days_old = (datetime.now() - doc_date).days

        if days_old < 0:
            return base_score  # Future date, no boost

        # Time-decay factor: 2^(-days/half_life)
        decay_factor = 0.5 ** (days_old / self.half_life_days)

        # Boost: recent docs get multiplier > 1, old docs get < 1
        # Normalize so that fresh docs get 1.5x, half-life docs get 1.0x, old docs get < 1.0x
        boost_multiplier = 1.5 * decay_factor

        return base_score * boost_multiplier


# ═══════════════════════════════════════════════════════════════════
#  4. HYBRID RETRIEVER (Combines all methods)
# ═══════════════════════════════════════════════════════════════════

@dataclass
class RetrievalResult:
    """A retrieval result with all metadata."""
    doc_id: str
    text: str
    dense_score: float = 0.0
    sparse_score: float = 0.0
    recency_boost: float = 1.0
    final_score: float = 0.0
    rank: int = 0


class HybridRetriever:
    """
    Hybrid retriever combining dense, sparse, and recency scoring.

    Uses reciprocal rank fusion (RRF) for combining multiple retrieval signals.
    """

    # RRF parameter: constant added to rank denominator
    RRF_K = 60

    # Weights for score combination
    DENSE_WEIGHT = 0.5
    SPARSE_WEIGHT = 0.3
    RECENCY_WEIGHT = 0.2

    def __init__(self, chroma_path: str = "./chroma_db"):
        self.dense_retriever = DenseRetriever(chroma_path=chroma_path)
        self.sparse_retriever = SparseRetriever()
        self.recency_booster = RecencyBooster()

        # Cache for documents
        self._documents: Dict[str, str] = {}

    def add_documents(self, documents: Dict[str, str]):
        """
        Add documents to sparse index.
        Dense index (ChromaDB) should be pre-built separately.
        """
        self._documents.update(documents)
        self.sparse_retriever.build_index(documents)

    def retrieve(
        self,
        query: str,
        collection_name: str,
        top_k: int = 5,
        apply_recency: bool = True,
    ) -> List[RetrievalResult]:
        """
        Hybrid retrieval with RRF fusion.

        Args:
            query: Search query
            collection_name: ChromaDB collection name
            top_k: Number of results to return
            apply_recency: Whether to apply recency boosting

        Returns:
            List of RetrievalResult objects
        """
        # Get dense results
        dense_results = self.dense_retriever.retrieve(query, collection_name, top_k * 2)

        # Get sparse results
        sparse_results = self.sparse_retriever.retrieve(query, top_k * 2)

        # Build document → scores mapping
        doc_scores: Dict[str, Dict[str, float]] = {}

        # Dense scores (convert to ranks)
        for rank, (doc_id, score, text) in enumerate(dense_results):
            if doc_id not in doc_scores:
                doc_scores[doc_id] = {"dense": 0.0, "sparse": 0.0, "text": text}
            doc_scores[doc_id]["dense"] = score

        # Sparse scores
        for rank, (doc_id, score, text) in enumerate(sparse_results):
            if doc_id not in doc_scores:
                doc_scores[doc_id] = {"dense": 0.0, "sparse": 0.0, "text": text}
            doc_scores[doc_id]["sparse"] = score

        # Calculate RRF scores
        rrf_scores: Dict[str, float] = {}
        for doc_id, scores in doc_scores.items():
            dense_rank = self._get_rank(dense_results, doc_id)
            sparse_rank = self._get_rank(sparse_results, doc_id)

            rrf_score = 0.0
            if dense_rank >= 0:
                rrf_score += 1.0 / (self.RRF_K + dense_rank)
            if sparse_rank >= 0:
                rrf_score += 1.0 / (self.RRF_K + sparse_rank)

            # Apply recency boost if requested
            recency_boost = 1.0
            if apply_recency:
                recency_boost = self.recency_booster.boost(doc_id, rrf_score)
                rrf_score *= recency_boost

            rrf_scores[doc_id] = rrf_score

        # Sort by RRF score
        sorted_docs = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]

        # Build results
        results = []
        for rank, (doc_id, final_score) in enumerate(sorted_docs):
            text = doc_scores.get(doc_id, {}).get("text", "")
            dense_rank = self._get_rank(dense_results, doc_id)
            sparse_rank = self._get_rank(sparse_results, doc_id)

            result = RetrievalResult(
                doc_id=doc_id,
                text=text,
                dense_score=dense_results[dense_rank][1] if dense_rank >= 0 else 0.0,
                sparse_score=sparse_results[sparse_rank][1] if sparse_rank >= 0 else 0.0,
                recency_boost=self.recency_booster.boost(doc_id, 1.0),
                final_score=final_score,
                rank=rank + 1,
            )
            results.append(result)

        return results

    def _get_rank(self, results: List[Tuple], doc_id: str) -> int:
        """Get rank of document in results (-1 if not found)."""
        for i, (d_id, _, _) in enumerate(results):
            if d_id == doc_id:
                return i
        return -1


# ═══════════════════════════════════════════════════════════════════
#  5. ENHANCED RAG SEARCHER (Drop-in replacement for existing searcher)
# ═══════════════════════════════════════════════════════════════════

class EnhancedRAGSearcher:
    """
    Enhanced RAG searcher with hybrid retrieval.
    Drop-in replacement for vg.rag.searcher.search_wisdom.
    """

    _instance: Optional["EnhancedRAGSearcher"] = None
    _hybrid_retriever: Optional[HybridRetriever] = None

    def __new__(cls, chroma_path: str = "./chroma_db"):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, chroma_path: str = "./chroma_db"):
        if self._initialized:
            return
        self.chroma_path = chroma_path
        self.hybrid_retriever = HybridRetriever(chroma_path=chroma_path)
        self._initialized = True

    def search_wisdom(
        self,
        query: str,
        collection_name: str,
        top_k: int = 3,
        min_score: float = 0.3,
    ) -> str:
        """
        Search with hybrid retrieval and return formatted wisdom.

        Args:
            query: Search query
            collection_name: ChromaDB collection name
            top_k: Number of chunks to return
            min_score: Minimum score threshold

        Returns:
            Formatted wisdom text (empty string if nothing found)
        """
        results = self.hybrid_retriever.retrieve(
            query=query,
            collection_name=collection_name,
            top_k=top_k,
            apply_recency=True,
        )

        # Filter by minimum score
        filtered = [r for r in results if r.final_score >= min_score]

        if not filtered:
            return ""

        # Format results
        chunks = [r.text for r in filtered[:top_k]]
        return "\n---\n".join(chunks)

    def search_with_metadata(
        self,
        query: str,
        collection_name: str,
        top_k: int = 3,
    ) -> List[RetrievalResult]:
        """
        Search and return full metadata for debugging/analysis.
        """
        return self.hybrid_retriever.retrieve(
            query=query,
            collection_name=collection_name,
            top_k=top_k,
            apply_recency=True,
        )


# ═══════════════════════════════════════════════════════════════════
#  GLOBAL SEARCHER INSTANCE
# ═══════════════════════════════════════════════════════════════════

def get_enhanced_searcher(chroma_path: str = "./chroma_db") -> EnhancedRAGSearcher:
    """Get or create the enhanced RAG searcher."""
    return EnhancedRAGSearcher(chroma_path=chroma_path)
