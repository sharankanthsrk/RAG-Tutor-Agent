from retriever import retrieve, format_context
from llm_local import generate

def answer_doubt(question: str) -> dict:
    """Retrieve context and answer a student's doubt."""
    results = retrieve(question, top_k=4)
    context = format_context(results)

    prompt = f"""You are an expert tutor helping a student understand a concept.
Use the context below to answer the question clearly and completely.
Break your explanation into steps where helpful. Include examples if relevant.

CONTEXT:
{context}

QUESTION:
{question}

Answer in a structured, educational way:"""

    answer = generate(prompt)
    return {
        "answer": answer,
        "sources": [{"text": r["text"][:200], "source": r["metadata"].get("source", ""), "score": r["score"]} for r in results]
    }
