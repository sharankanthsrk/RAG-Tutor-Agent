from retriever import retrieve, format_context
from llm_local import generate

def summarize(topic: str) -> dict:
    """Summarize a topic from indexed study material."""
    results = retrieve(topic, top_k=6)
    context = format_context(results)

    prompt = f"""You are an expert academic summarizer.
Summarize the following study material on "{topic}" clearly and concisely.

Structure your summary as:
## Overview
(2-3 sentence overview)

## Key Concepts
(bullet points of the most important ideas)

## Key Takeaways
(3-5 short takeaway points a student should remember)

CONTEXT:
{context}

Summary:"""

    summary = generate(prompt)
    return {
        "topic": topic,
        "summary": summary,
        "sources": [{"source": r["metadata"].get("source", ""), "score": r["score"]} for r in results]
    }
