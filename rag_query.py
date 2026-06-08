"""
rag_query.py — Milestone 5: Grounded Generation
Wires retrieval (embed_and_retrieve.py) to Groq's LLaMA 3.3 70B
and returns answers grounded strictly in retrieved chunks.

Usage:
    pip install groq sentence-transformers chromadb python-dotenv
    Add GROQ_API_KEY=your_key_here to your .env file
    Then import ask() in app.py, or run directly:
        python rag_query.py
"""

import os
from groq import Groq
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
import chromadb

load_dotenv()

# ── Config ────────────────────────────────────────────────────────────────────

EMBED_MODEL     = "BAAI/bge-small-en-v1.5"
CHROMA_PATH     = "./chroma_db"
COLLECTION_NAME = "berkeley_food"
TOP_K           = 7
GROQ_MODEL      = "llama-3.3-70b-versatile"

# ── System prompt — grounding is enforced, not suggested ──────────────────────

SYSTEM_PROMPT = """You are a helpful food guide assistant for UC Berkeley students.

STRICT RULES — follow these exactly:
1. Answer ONLY using the information in the provided context documents.
2. Do NOT use your general training knowledge about restaurants, food, or Berkeley.
3. If the context does not contain enough information to answer the question, respond with exactly:
   "I don't have enough information on that in my sources."
4. Keep answers concise and practical for a student.
5. Do not fabricate restaurant names, hours, prices, or details not found in the context."""

# ── Lazy-load shared resources (avoids reloading on every call in Gradio) ─────

_model      = None
_collection = None
_groq       = None


def _load_resources():
    global _model, _collection, _groq

    if _model is None:
        print("  Loading embedding model...")
        _model = SentenceTransformer(EMBED_MODEL)

    if _collection is None:
        client      = chromadb.PersistentClient(path=CHROMA_PATH)
        _collection = client.get_collection(COLLECTION_NAME)

    if _groq is None:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError(
                "GROQ_API_KEY not found. Add it to your .env file.\n"
                "Get a free key at https://console.groq.com"
            )
        _groq = Groq(api_key=api_key)


# ── Retrieval ─────────────────────────────────────────────────────────────────

def _retrieve(query: str) -> list[dict]:
    embedding = _model.encode([query], normalize_embeddings=True).tolist()
    results   = _collection.query(
        query_embeddings = embedding,
        n_results        = TOP_K,
        include          = ["documents", "metadatas", "distances"],
    )
    hits = []
    for text, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        hits.append({
            "text":     text,
            "source":   meta["source"],
            "distance": round(dist, 4),
        })
    return hits


# ── Generation ────────────────────────────────────────────────────────────────

def _build_context_block(hits: list[dict]) -> str:
    parts = []
    for i, hit in enumerate(hits, 1):
        parts.append(f"[Document {i} — {hit['source']}]\n{hit['text']}")
    return "\n\n".join(parts)


def _dedupe_sources(hits: list[dict]) -> list[str]:
    seen, sources = set(), []
    for hit in hits:
        if hit["source"] not in seen:
            seen.add(hit["source"])
            sources.append(hit["source"])
    return sources


# ── Public API ────────────────────────────────────────────────────────────────

def ask(question: str) -> dict:
    """
    End-to-end RAG pipeline.

    Returns:
        {
            "answer":  str,         # grounded LLM response
            "sources": list[str],   # unique source filenames used
            "hits":    list[dict],  # raw retrieval results (for debugging)
        }
    """
    _load_resources()

    hits    = _retrieve(question)
    context = _build_context_block(hits)
    sources = _dedupe_sources(hits)

    user_message = (
        f"Context documents:\n\n{context}\n\n"
        f"Question: {question}\n\n"
        "Answer using only the context documents above. "
        "If the answer is not in the documents, say "
        "'I don't have enough information on that in my sources.'"
    )

    response = _groq.chat.completions.create(
        model    = GROQ_MODEL,
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": user_message},
        ],
        temperature = 0.2,
        max_tokens  = 512,
    )

    answer = response.choices[0].message.content.strip()

    return {"answer": answer, "sources": sources, "hits": hits}


# ── Quick CLI test ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    TEST_QUERIES = [
        "What are some good breakfast spots near UC Berkeley?",
        "What is a high end expensive restaurant near Berkeley?",
        "Where can I find vegan food options on campus?",
        "What is the best sushi restaurant in Paris?",   # should decline
    ]

    for q in TEST_QUERIES:
        print("\n" + "=" * 60)
        print(f"Q: {q}")
        result = ask(q)
        print(f"\nA: {result['answer']}")
        print(f"\nSources: {', '.join(result['sources'])}")