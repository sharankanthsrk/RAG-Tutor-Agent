import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import io

import vector_db
import llm_local
from agents.doubt_agent import answer_doubt
from agents.quiz_agent import generate_quiz
from agents.summarizer_agent import summarize

app = FastAPI(title="RAG Tutor API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Seed sample data on startup ─────────────────────────────────────────────
SAMPLE_DOCS = [
    {
        "source": "AI & ML Fundamentals",
        "chunks": [
            "Machine Learning is a subset of Artificial Intelligence that allows systems to learn and improve from experience without being explicitly programmed. It focuses on developing computer programs that can access data and use it to learn for themselves.",
            "Supervised Learning uses labeled training data to learn a mapping function from input variables X to an output variable Y. Common algorithms include Linear Regression, Decision Trees, Support Vector Machines, and Neural Networks.",
            "Unsupervised Learning finds hidden patterns or intrinsic structures in input data. Clustering algorithms like K-Means group similar data points together without any prior labels.",
            "Neural Networks are computing systems vaguely inspired by biological neural networks. They consist of layers of interconnected nodes (neurons) that process information using connectionist approaches to computation.",
            "Deep Learning is part of a broader family of machine learning methods based on artificial neural networks with representation learning. It uses multiple layers to progressively extract higher-level features from raw input.",
            "Natural Language Processing (NLP) is a subfield of linguistics, computer science, and AI that enables computers to understand, interpret, and generate human language in a way that is both meaningful and useful.",
            "Retrieval-Augmented Generation (RAG) is an AI framework that combines the power of large language models with information retrieval systems to provide more accurate, up-to-date, and contextually relevant responses.",
            "Transformers are a deep learning architecture introduced in the paper 'Attention Is All You Need'. They use self-attention mechanisms to process sequential data and have revolutionized NLP tasks.",
        ]
    },
    {
        "source": "Computer Science Basics",
        "chunks": [
            "An algorithm is a finite sequence of well-defined instructions that solves a problem or performs a computation. Algorithms are expressed in terms of their time complexity (Big-O notation) and space complexity.",
            "Data structures are ways of organizing and storing data so that it can be accessed and modified efficiently. Common data structures include arrays, linked lists, stacks, queues, trees, graphs, and hash tables.",
            "Object-Oriented Programming (OOP) is a programming paradigm that organizes software design around data (objects) rather than functions. The four pillars are Encapsulation, Abstraction, Inheritance, and Polymorphism.",
            "Operating Systems manage computer hardware and software resources. Key concepts include process management, memory management, file systems, and I/O management.",
            "Computer networks enable communication between devices. Key concepts include IP addressing, TCP/IP protocols, HTTP/HTTPS, DNS, and the OSI model with its 7 layers.",
            "Databases store and organize data persistently. SQL databases use structured tables with relationships, while NoSQL databases (MongoDB, Redis) use flexible schemas for unstructured data.",
        ]
    },
    {
        "source": "Mathematics for AI",
        "chunks": [
            "Linear Algebra is fundamental to machine learning. Vectors represent data points, matrices represent transformations, and operations like matrix multiplication and eigendecomposition are used throughout ML algorithms.",
            "Calculus, specifically gradient calculus, is essential for training neural networks. Gradient Descent is an optimization algorithm that iteratively adjusts model parameters to minimize a loss function.",
            "Probability theory provides the mathematical foundation for uncertainty quantification in AI. Key concepts include probability distributions, Bayes' theorem, conditional probability, and statistical inference.",
            "Statistics helps us understand data distributions and make inferences. Measures like mean, median, variance, and standard deviation describe data characteristics, while hypothesis testing validates findings.",
        ]
    }
]

@app.on_event("startup")
def seed_sample_data():
    existing = vector_db.list_documents()
    for doc in SAMPLE_DOCS:
        if doc["source"] not in existing:
            metadata = [{"source": doc["source"], "page": str(i+1)} for i in range(len(doc["chunks"]))]
            vector_db.add_documents(doc["chunks"], metadata)

# ── Models ───────────────────────────────────────────────────────────────────

class DoubtRequest(BaseModel):
    question: str

class QuizRequest(BaseModel):
    topic: str
    num_questions: Optional[int] = 5

class SummarizeRequest(BaseModel):
    topic: str

class SettingsRequest(BaseModel):
    provider: Optional[str] = None   # openai | groq | ollama | fallback
    api_key: Optional[str] = None
    model: Optional[str] = None
    ollama_url: Optional[str] = None

# ── Routes ───────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "provider": llm_local.LLM_PROVIDER}

@app.get("/documents")
def get_documents():
    return {"documents": vector_db.list_documents()}

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    content = await file.read()
    filename = file.filename or "upload"

    if filename.endswith(".pdf"):
        chunks = _parse_pdf(content, filename)
    else:
        text = content.decode("utf-8", errors="ignore")
        chunks = _chunk_text(text)

    if not chunks:
        raise HTTPException(status_code=400, detail="No text could be extracted from the file.")

    metadata = [{"source": filename, "page": str(i+1)} for i in range(len(chunks))]
    count = vector_db.add_documents(chunks, metadata)
    return {"message": f"Indexed {count} chunks from '{filename}'", "chunks": count}

@app.post("/upload/text")
def upload_text(payload: dict):
    text = payload.get("text", "").strip()
    title = payload.get("title", "Pasted Text")
    if not text:
        raise HTTPException(status_code=400, detail="No text provided.")
    chunks = _chunk_text(text)
    metadata = [{"source": title, "page": str(i+1)} for i in range(len(chunks))]
    count = vector_db.add_documents(chunks, metadata)
    return {"message": f"Indexed {count} chunks from '{title}'", "chunks": count}

@app.post("/query/doubt")
def doubt(req: DoubtRequest):
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")
    return answer_doubt(req.question)

@app.post("/query/quiz")
def quiz(req: QuizRequest):
    if not req.topic.strip():
        raise HTTPException(status_code=400, detail="Topic cannot be empty.")
    return generate_quiz(req.topic, req.num_questions)

@app.post("/query/summarize")
def summarize_route(req: SummarizeRequest):
    if not req.topic.strip():
        raise HTTPException(status_code=400, detail="Topic cannot be empty.")
    return summarize(req.topic)

@app.post("/settings")
def update_settings(req: SettingsRequest):
    llm_local.update_settings(
        provider=req.provider,
        api_key=req.api_key,
        model=req.model,
        ollama_url=req.ollama_url
    )
    return {"message": "Settings updated", "provider": llm_local.LLM_PROVIDER}

@app.delete("/documents")
def clear_documents():
    vector_db.clear_all()
    return {"message": "All documents cleared."}

# ── Helpers ───────────────────────────────────────────────────────────────────

def _chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list:
    words = text.split()
    chunks, i = [], 0
    while i < len(words):
        chunk = " ".join(words[i:i+chunk_size])
        if chunk.strip():
            chunks.append(chunk)
        i += chunk_size - overlap
    return chunks

def _parse_pdf(content: bytes, filename: str) -> list:
    try:
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(content))
        chunks = []
        for page in reader.pages:
            text = page.extract_text() or ""
            if text.strip():
                chunks.extend(_chunk_text(text))
        return chunks
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF parsing failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
