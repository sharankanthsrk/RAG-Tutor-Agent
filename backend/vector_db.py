import json, os, uuid
from typing import List, Dict, Optional
from embeddings import tfidf_embed, cosine_similarity

DB_PATH = "vector_store.json"

_store: Dict[str, dict] = {}  # id -> {text, metadata, vector}

def _save():
    with open(DB_PATH, "w") as f:
        json.dump(_store, f)

def _load():
    global _store
    if os.path.exists(DB_PATH):
        with open(DB_PATH) as f:
            _store = json.load(f)

_load()

def add_documents(chunks: List[str], metadata: List[dict]) -> int:
    """Index document chunks into the vector store."""
    if not chunks:
        return 0
    vectors = tfidf_embed(chunks)
    for chunk, meta, vec in zip(chunks, metadata, vectors):
        doc_id = str(uuid.uuid4())
        _store[doc_id] = {"text": chunk, "metadata": meta, "vector": vec}
    _save()
    return len(chunks)

def search(query: str, top_k: int = 5) -> List[dict]:
    """Retrieve top-k most similar chunks for a query."""
    if not _store:
        return []
    texts = [v["text"] for v in _store.values()]
    ids = list(_store.keys())
    all_vecs = tfidf_embed(texts, query=query)
    query_vec = all_vecs[-1]
    doc_vecs = all_vecs[:-1]

    scored = []
    for i, (doc_id, vec) in enumerate(zip(ids, doc_vecs)):
        score = cosine_similarity(query_vec, vec)
        scored.append((score, doc_id))

    scored.sort(reverse=True)
    results = []
    for score, doc_id in scored[:top_k]:
        entry = _store[doc_id]
        results.append({
            "text": entry["text"],
            "metadata": entry["metadata"],
            "score": round(score, 4)
        })
    return results

def list_documents() -> List[str]:
    """Return unique document names indexed."""
    names = set()
    for v in _store.values():
        names.add(v["metadata"].get("source", "Unknown"))
    return sorted(names)

def clear_all():
    global _store
    _store = {}
    _save()
