"""
RAG Builder — chunks personality texts → embeds → stores in ChromaDB.
Run once: python -m veritas.rag.builder
"""

import os
import glob
from typing import List

import chromadb
from fastembed import TextEmbedding

from vg.config import config

RAG_DIR = os.path.join(os.path.dirname(__file__), "personalities")
CHROMA_PATH = config.chroma_db_path
CHUNK_WORDS = config.rag_chunk_words

PERSONALITY_COLLECTIONS = {
    "chanakya": "chanakya_wisdom",
    "bose": "bose_wisdom",
    "doval": "doval_wisdom",
    "kissinger": "kissinger_wisdom",
    "kao": "kao_wisdom",
}


def chunk_text(text: str, chunk_words: int = 300) -> List[str]:
    """Split text into word-count-based chunks."""
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_words):
        chunk = " ".join(words[i : i + chunk_words])
        if len(chunk.strip()) > 50:
            chunks.append(chunk.strip())
    return chunks


def build_all():
    """Read all personality txt files, chunk, embed, and store in ChromaDB."""
    print("═" * 50)
    print("VG RAG Builder")
    print("═" * 50)

    model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
    client = chromadb.PersistentClient(path=CHROMA_PATH)

    for persona_dir, collection_name in PERSONALITY_COLLECTIONS.items():
        persona_path = os.path.join(RAG_DIR, persona_dir)
        txt_files = glob.glob(os.path.join(persona_path, "*.txt"))

        if not txt_files:
            print(f"\n⚠  No .txt files found for {persona_dir} in {persona_path}")
            continue

        print(f"\n📚 Processing: {persona_dir}")
        all_chunks = []
        all_ids = []
        all_metadatas = []

        for fpath in txt_files:
            fname = os.path.basename(fpath)
            with open(fpath, "r", encoding="utf-8") as f:
                text = f.read()

            chunks = chunk_text(text, CHUNK_WORDS)
            print(f"   {fname}: {len(chunks)} chunks")

            for i, chunk in enumerate(chunks):
                chunk_id = f"{persona_dir}_{fname}_{i}"
                all_chunks.append(chunk)
                all_ids.append(chunk_id)
                all_metadatas.append({"source": fname, "persona": persona_dir, "chunk_index": i})

        if not all_chunks:
            continue

        # Embed
        print(f"   Embedding {len(all_chunks)} chunks...")
        embeddings = list(model.embed(all_chunks))

        # Store
        collection = client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        # Upsert to allow re-runs
        collection.upsert(
            ids=all_ids,
            documents=all_chunks,
            embeddings=embeddings,
            metadatas=all_metadatas,
        )
        print(f"   ✓ Stored {len(all_chunks)} chunks in collection '{collection_name}'")

    print("\n" + "═" * 50)
    print("RAG build complete! DB stored at:", os.path.abspath(CHROMA_PATH))
    print("═" * 50)


if __name__ == "__main__":
    build_all()
