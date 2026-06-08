"""
chunk.py — Milestone 3: Chunking
Reads all .txt files from documents/, splits into overlapping character chunks,
and saves the result to chunks.json for inspection and embedding.

Spec (from planning.md):
  Chunk size : ~200 characters
  Overlap    : ~30 characters

Usage:
    python chunk.py

Output:
  chunks.json  — list of {text, source, chunk_index} dicts
  Prints 5 random chunks for the Milestone 3 checkpoint.
"""

import os
import json
import random

# ── Config ────────────────────────────────────────────────────────────────────

DOCUMENTS_DIR = "documents"
OUTPUT_FILE   = "chunks.json"
CHUNK_SIZE    = 200   # characters
OVERLAP       = 30    # characters

# ── Chunker ───────────────────────────────────────────────────────────────────

def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = OVERLAP) -> list[str]:
    """
    Splits text into overlapping character-level chunks.
    Skips empty or whitespace-only chunks.
    """
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()
        if len(chunk) > 0:
            chunks.append(chunk)
        start += chunk_size - overlap  # slide forward by (chunk_size - overlap)
    return chunks


def load_and_chunk_all(documents_dir: str) -> list[dict]:
    """
    Reads every .txt file in documents_dir, chunks each one,
    and returns a flat list of chunk dicts with metadata.
    """
    all_chunks = []
    txt_files = sorted(f for f in os.listdir(documents_dir) if f.endswith(".txt"))

    if not txt_files:
        print(f"  ✗  No .txt files found in '{documents_dir}'. Run ingest.py first.")
        return []

    for filename in txt_files:
        path = os.path.join(documents_dir, filename)
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()

        chunks = chunk_text(text)
        for i, chunk in enumerate(chunks):
            all_chunks.append({
                "text":        chunk,
                "source":      filename,
                "chunk_index": i,
            })
        print(f"  ✓  {filename:50s}  →  {len(chunks):4d} chunks")

    return all_chunks


# ── Checkpoint: print 5 random chunks ────────────────────────────────────────

def print_checkpoint(chunks: list[dict], n: int = 5) -> None:
    print("\n" + "=" * 60)
    print(f"  CHECKPOINT — {n} random chunks")
    print("=" * 60)
    sample = random.sample(chunks, min(n, len(chunks)))
    for i, c in enumerate(sample, 1):
        print(f"\n[{i}] source={c['source']}  chunk_index={c['chunk_index']}")
        print(f"    {repr(c['text'])}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("  Berkeley Food Guide — Chunking")
    print("=" * 60)

    chunks = load_and_chunk_all(DOCUMENTS_DIR)
    if not chunks:
        return

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=2, ensure_ascii=False)

    print(f"\n  Total chunks: {len(chunks)}")
    print(f"  Saved to {OUTPUT_FILE}")

    print_checkpoint(chunks)


if __name__ == "__main__":
    main()