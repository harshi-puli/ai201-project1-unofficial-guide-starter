"""
embed_and_retrieve.py — Milestone 4: Embedding + Retrieval
Loads chunks from chunks.json, embeds with bge-small-en-v1.5,
stores in a ChromaDB vector store, and tests retrieval.

Spec (from planning.md):
  Embedding model : BAAI/bge-small-en-v1.5
  Top-k           : 7

Usage:
    pip install sentence-transformers chromadb
    python chunk.py          # must run first
    python embed_and_retrieve.py

The script will:
  1. Load chunks.json
  2. Embed all chunks and upsert into ChromaDB (persisted to ./chroma_db)
  3. Run 3 test queries and print retrieved chunks + distance scores
"""

import json
import chromadb
from sentence_transformers import SentenceTransformer

# ── Config ────────────────────────────────────────────────────────────────────

CHUNKS_FILE      = "chunks.json"
CHROMA_PATH      = "./chroma_db"
COLLECTION_NAME  = "berkeley_food"
EMBED_MODEL      = "BAAI/bge-small-en-v1.5"
TOP_K            = 7
BATCH_SIZE       = 64   # embed this many chunks at a time to avoid OOM

# ── Load chunks ───────────────────────────────────────────────────────────────

def load_chunks(path: str) -> list[dict]:
    with open(path, "r", encoding="utf-8") as f:
        chunks = json.load(f)
    print(f"  Loaded {len(chunks):,} chunks from {path}")
    return chunks


# ── Embed + store ─────────────────────────────────────────────────────────────

def build_vector_store(chunks: list[dict], model: SentenceTransformer) -> chromadb.Collection:
    """Embed all chunks and upsert into a persistent ChromaDB collection."""
    client     = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},   # cosine distance for similarity
    )

    # Skip embedding if collection already populated
    if collection.count() >= len(chunks):
        print(f"  Collection '{COLLECTION_NAME}' already has {collection.count()} entries — skipping embed.")
        return collection

    print(f"  Embedding {len(chunks):,} chunks in batches of {BATCH_SIZE}...")
    for batch_start in range(0, len(chunks), BATCH_SIZE):
        batch   = chunks[batch_start : batch_start + BATCH_SIZE]
        texts   = [c["text"]   for c in batch]
        ids     = [f"{c['source']}__chunk{c['chunk_index']}" for c in batch]
        metas   = [{"source": c["source"], "chunk_index": c["chunk_index"]} for c in batch]

        embeddings = model.encode(texts, normalize_embeddings=True).tolist()

        collection.upsert(
            ids        = ids,
            embeddings = embeddings,
            documents  = texts,
            metadatas  = metas,
        )
        end = min(batch_start + BATCH_SIZE, len(chunks))
        print(f"    Upserted chunks {batch_start}–{end}")

    print(f"  ✓  Vector store ready  ({collection.count()} total entries)")
    return collection


# ── Retrieval function ────────────────────────────────────────────────────────

def retrieve(
    query: str,
    collection: chromadb.Collection,
    model: SentenceTransformer,
    top_k: int = TOP_K,
) -> list[dict]:
    """
    Embed the query and return the top-k most similar chunks
    with their text, source metadata, and cosine distance score.
    """
    query_embedding = model.encode([query], normalize_embeddings=True).tolist()
    results = collection.query(
        query_embeddings = query_embedding,
        n_results        = top_k,
        include          = ["documents", "metadatas", "distances"],
    )
    hits = []
    for text, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        hits.append({"text": text, "source": meta["source"], "distance": round(dist, 4)})
    return hits


# ── Test retrieval ────────────────────────────────────────────────────────────

TEST_QUERIES = [
    "What dining hall has the most vegan options for dinner?",
    "What are some good breakfast spots near UC Berkeley?",
    "What is a high end expensive restaurant near Berkeley?",
]

def run_retrieval_tests(collection: chromadb.Collection, model: SentenceTransformer) -> None:
    print("\n" + "=" * 60)
    print("  RETRIEVAL TEST — 3 evaluation queries")
    print("=" * 60)
    for query in TEST_QUERIES:
        print(f"\nQuery: \"{query}\"")
        print("-" * 50)
        hits = retrieve(query, collection, model)
        for rank, hit in enumerate(hits, 1):
            relevance = "✓" if hit["distance"] < 0.5 else "⚠ high dist"
            print(f"  [{rank}] dist={hit['distance']}  {relevance}  source={hit['source']}")
            # Print a preview (first 120 chars) so you can judge relevance
            print(f"       {hit['text'][:120].strip()!r}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("  Berkeley Food Guide — Embedding & Retrieval")
    print("=" * 60)

    chunks = load_chunks(CHUNKS_FILE)

    print(f"\n  Loading model: {EMBED_MODEL}")
    model = SentenceTransformer(EMBED_MODEL)

    collection = build_vector_store(chunks, model)
    run_retrieval_tests(collection, model)

    print("\n" + "=" * 60)
    print("  Done. If distances look high (> 0.5), see debug tips in")
    print("  the Milestone 4 checkpoint notes.")
    print("=" * 60)


if __name__ == "__main__":
    main()