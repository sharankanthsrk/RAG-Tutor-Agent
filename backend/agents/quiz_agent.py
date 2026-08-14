import json, re
from retriever import retrieve, format_context
from llm_local import generate

def generate_quiz(topic: str, num_questions: int = 5) -> dict:
    """Generate a multiple-choice quiz on a topic using retrieved context."""
    results = retrieve(topic, top_k=5)
    context = format_context(results)

    prompt = f"""You are an expert quiz maker for students.
Based on the study material below, create {num_questions} multiple-choice questions.

CONTEXT:
{context}

TOPIC: {topic}

Return ONLY a valid JSON array. Each item must have:
- "question": the question text
- "options": array of 4 choices (A, B, C, D)
- "answer": the correct option letter (A/B/C/D)
- "explanation": brief explanation of the correct answer

Example format:
[{{"question":"...","options":["A. ...","B. ...","C. ...","D. ..."],"answer":"A","explanation":"..."}}]

JSON array:"""

    raw = generate(prompt)

    # Try to parse JSON from the response
    try:
        match = re.search(r'\[.*\]', raw, re.DOTALL)
        if match:
            questions = json.loads(match.group())
        else:
            questions = json.loads(raw)
    except Exception:
        # Fallback: return a simple placeholder quiz
        questions = _fallback_quiz(topic, context, num_questions)

    return {
        "topic": topic,
        "questions": questions,
        "sources": [r["metadata"].get("source", "") for r in results]
    }

def _fallback_quiz(topic: str, context: str, n: int) -> list:
    """Offline fallback quiz generator using simple context parsing."""
    sentences = [s.strip() for s in context.replace("\n", " ").split(".") if len(s.strip()) > 40]
    questions = []
    for i, sent in enumerate(sentences[:n]):
        words = sent.split()
        if len(words) < 6:
            continue
        blank_idx = len(words) // 2
        answer_word = words[blank_idx]
        question_text = " ".join(words[:blank_idx]) + " _____ " + " ".join(words[blank_idx+1:]) + "?"
        questions.append({
            "question": f"Fill in: {question_text}",
            "options": [f"A. {answer_word}", "B. process", "C. system", "D. method"],
            "answer": "A",
            "explanation": f"The correct word from the text is '{answer_word}'."
        })
    if not questions:
        questions = [{
            "question": f"What is the main concept discussed in '{topic}'?",
            "options": ["A. A fundamental principle", "B. An unrelated topic", "C. A historical event", "D. A mathematical formula"],
            "answer": "A",
            "explanation": "Upload more material for better quiz generation."
        }]
    return questions[:n]
