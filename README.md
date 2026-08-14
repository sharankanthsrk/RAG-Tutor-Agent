# RAG Tutor — AI Multi-Agent Study Assistant

A lightweight, production-ready **RAG + Multi-Agent EdTech** platform. Ask questions, generate quizzes, and get summaries from your own study material — runs completely offline or with any LLM API.

## Quick Start

### 1. Install backend dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 2. Run the backend
```bash
python app.py
# API available at http://localhost:8000
```

### 3. Open the frontend
Open `frontend/index.html` in your browser (or serve it with Live Server).

---

## Features

| Feature | Description |
|---|---|
| 🧠 **Doubt Solver** | Ask any question, get a detailed answer from your study material |
| 📝 **Quiz Arena** | Auto-generate MCQ quizzes with scoring and explanations |
| 📄 **Summarizer** | Get structured summaries, key concepts, and takeaways |
| 📂 **Upload** | Index PDF or plain text files |
| ⚙ **LLM Settings** | Switch between Offline / Groq / OpenAI / Ollama at runtime |

## LLM Providers

| Provider | Setup |
|---|---|
| **Offline (default)** | Zero setup — uses built-in context-based responses |
| **Groq** | Free API key from [console.groq.com](https://console.groq.com) |
| **OpenAI** | API key from [platform.openai.com](https://platform.openai.com) |
| **Ollama** | Install [Ollama](https://ollama.ai) and run `ollama serve` |

## Docker
```bash
docker compose up --build
# Backend: http://localhost:8000
# Frontend: http://localhost:3000
```

## Project Structure
```
backend/       FastAPI server + RAG engine + 3 AI Agents
frontend/      Single-page dark glassmorphic web app
docker-compose.yml
```
