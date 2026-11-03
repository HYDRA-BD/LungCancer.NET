"""
rag.py — USPSTF guideline retrieval for LungCancer.NET

Ingests the USPSTF lung cancer screening guideline PDF into a local
ChromaDB vector store and exposes semantic search for the clinical
pre-screening pipeline.
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

# Force offline mode for cached HuggingFace sentence transformer embeddings
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

import chromadb
from sentence_transformers import SentenceTransformer

BASE = Path(__file__).parent
PDF_PATH = BASE / "data" / "uspstf_lung_cancer.pdf"
CHROMA_PATH = BASE / "artifacts" / "chroma"
COLLECTION = "uspstf_guidelines"
MODEL_NAME = "all-MiniLM-L6-v2"

_embedder = None


def _get_embedder():
    global _embedder
    if _embedder is None:
        _embedder = SentenceTransformer(MODEL_NAME)
    return _embedder


def _extract_text(pdf_path: Path):
    import pypdf
    reader = pypdf.PdfReader(str(pdf_path))
    pages = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        pages.append({"page": i + 1, "text": text})
    return pages


def _semantic_chunk(pages, min_len: int = 100):
    """Split on section headers (ALL CAPS lines) and paragraph breaks."""
    chunks = []
    for p in pages:
        text = p["text"]
        parts = re.split(r"\n{2,}|(?=\n[A-Z][A-Z ]{5,}\n)", text)
        for part in parts:
            part = part.strip()
            if len(part) >= min_len:
                chunks.append({"text": part, "page": p["page"]})
    return chunks


def ingest(force: bool = False):
    if not PDF_PATH.exists():
        raise FileNotFoundError(
            f"USPSTF PDF not found at {PDF_PATH}\n"
            "Download from uspreventiveservicestaskforce.org and save it there."
        )

    CHROMA_PATH.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_PATH))

    if force:
        try:
            client.delete_collection(COLLECTION)
        except Exception:
            pass

    col = client.get_or_create_collection(COLLECTION)
    if col.count() > 0 and not force:
        print(f"[rag] collection already has {col.count()} chunks — skipping (use --force to rebuild)")
        return col.count()

    pages = _extract_text(PDF_PATH)
    chunks = _semantic_chunk(pages)
    print(f"[rag] extracted {len(pages)} pages → {len(chunks)} chunks")

    embedder = _get_embedder()
    texts = [c["text"] for c in chunks]
    embeddings = embedder.encode(
        texts, show_progress_bar=True, convert_to_numpy=True
    ).tolist()

    ids = [f"c{i}" for i in range(len(chunks))]
    metadatas = [{"page": c["page"]} for c in chunks]

    col.add(ids=ids, documents=texts, embeddings=embeddings, metadatas=metadatas)
    print(f"[rag] ingested {len(chunks)} chunks into {CHROMA_PATH}")
    return len(chunks)


def search_guidelines(query: str, k: int = 3):
    """Return top-k guideline chunks matching the query with safe bounds."""
    # Sanitize and truncate query
    clean_q = str(query).strip()[:300]
    if not clean_q:
        return []

    safe_k = max(1, min(int(k), 10))

    CHROMA_PATH.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_PATH))
    try:
        col = client.get_collection(COLLECTION)
    except Exception:
        return []
    if col.count() == 0:
        return []

    embedder = _get_embedder()
    q_emb = embedder.encode([clean_q], convert_to_numpy=True).tolist()
    res = col.query(query_embeddings=q_emb, n_results=safe_k)
    docs = res["documents"][0]
    metas = res["metadatas"][0]
    return [{"text": d, "page": m.get("page")} for d, m in zip(docs, metas)]


if __name__ == "__main__":
    if "--ingest" in sys.argv:
        force = "--force" in sys.argv
        n = ingest(force=force)
        print(f"Total chunks: {n}")
    else:
        results = search_guidelines(
            "annual LDCT screening age 50 pack-year", k=3
        )
        if not results:
            print("[rag] no results — run: python rag.py --ingest")
        for i, r in enumerate(results):
            print(f"\n--- Result {i+1} (page {r['page']}) ---")
            print(r["text"][:400])
