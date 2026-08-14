from vector_db import search

def retrieve(query: str, top_k: int = 4) -> list:
    """Return relevant chunks with source metadata."""
    results = search(query, top_k=top_k)
    return results

def format_context(results: list) -> str:
    """Format retrieved chunks into a single context string."""
    if not results:
        return "No relevant context found."
    parts = []
    for i, r in enumerate(results, 1):
        source = r["metadata"].get("source", "Unknown")
        page = r["metadata"].get("page", "")
        ref = f"[{source}" + (f", p.{page}" if page else "") + "]"
        parts.append(f"Source {i} {ref}:\n{r['text']}")
    return "\n\n".join(parts)
