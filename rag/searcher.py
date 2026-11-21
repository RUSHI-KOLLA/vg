"""
RAG Searcher — queries ChromaDB at runtime for relevant personality wisdom.
Uses fastembed for lightweight embeddings.
"""

import os
from typing import Dict, Optional

import chromadb
from fastembed import TextEmbedding

from vg.config import config

CHROMA_PATH = config.chroma_db_path

# Lazy-loaded singletons
_model: Optional[TextEmbedding] = None
_client: Optional[chromadb.ClientAPI] = None


def _get_model() -> TextEmbedding:
    global _model
    if _model is None:
        _model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
    return _model


def _get_client() -> chromadb.ClientAPI:
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path=CHROMA_PATH)
    return _client


def search_wisdom(query: str, collection_name: str, top_k: int = None) -> str:
    """Search a personality's ChromaDB collection and return formatted wisdom."""
    if top_k is None:
        top_k = config.rag_top_k

    client = _get_client()
    model = _get_model()

    try:
        collection = client.get_collection(name=collection_name)
    except Exception:
        return ""

    query_embedding = list(model.embed([query]))[0]

    results = collection.query(
        query_embeddings=query_embedding,
        n_results=top_k,
    )

    if not results or not results["documents"] or not results["documents"][0]:
        return ""

    chunks = results["documents"][0]
    return "\n---\n".join(chunks)


def search_all_wisdoms(query: str) -> Dict[str, str]:
    """Search wisdom for ALL historical personalities. Returns {role_value: wisdom_text}."""
    from vg.rag.builder import PERSONALITY_COLLECTIONS

    wisdoms = {}
    for persona_key, collection_name in PERSONALITY_COLLECTIONS.items():
        wisdom = search_wisdom(query, collection_name)
        if wisdom:
            wisdoms[persona_key] = wisdom

    return wisdoms
