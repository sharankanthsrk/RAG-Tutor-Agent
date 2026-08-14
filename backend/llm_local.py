import os, requests

# ----- Configuration (set via environment or /settings API) -----
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama")   # "openai" | "groq" | "ollama" | "fallback"
LLM_API_KEY  = os.getenv("LLM_API_KEY", "")
LLM_MODEL    = os.getenv("LLM_MODEL", "qwen2.5:7b")
OLLAMA_URL   = os.getenv("OLLAMA_URL", "http://localhost:11434")

def update_settings(provider: str = None, api_key: str = None, model: str = None, ollama_url: str = None):
    global LLM_PROVIDER, LLM_API_KEY, LLM_MODEL, OLLAMA_URL
    if provider:   LLM_PROVIDER = provider
    if api_key:    LLM_API_KEY  = api_key
    if model:      LLM_MODEL    = model
    if ollama_url: OLLAMA_URL   = ollama_url

def generate(prompt: str) -> str:
    """Route to the configured LLM provider, with fallback on error."""
    try:
        if LLM_PROVIDER == "openai":
            return _openai(prompt)
        elif LLM_PROVIDER == "groq":
            return _groq(prompt)
        elif LLM_PROVIDER == "ollama":
            return _ollama(prompt)
        else:
            return _fallback(prompt)
    except Exception as e:
        return _fallback(prompt) + f"\n\n⚠️ Provider '{LLM_PROVIDER}' error: {e}"

# ---------- Provider implementations ----------

def _openai(prompt: str) -> str:
    url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {LLM_API_KEY}", "Content-Type": "application/json"}
    body = {"model": LLM_MODEL or "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7}
    r = requests.post(url, json=body, headers=headers, timeout=30)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]

def _groq(prompt: str) -> str:
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {LLM_API_KEY}", "Content-Type": "application/json"}
    body = {"model": LLM_MODEL or "llama3-8b-8192",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7}
    r = requests.post(url, json=body, headers=headers, timeout=30)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]

def _ollama(prompt: str) -> str:
    model_name = LLM_MODEL or "qwen2.5:7b"
    url = f"{OLLAMA_URL}/api/chat"
    body = {"model": model_name, "messages": [{"role": "user", "content": prompt}], "stream": False}
    r = requests.post(url, json=body, timeout=60)
    r.raise_for_status()
    data = r.json()
    if "message" in data and "content" in data["message"]:
        return data["message"]["content"]
    return data.get("response", "")

def _fallback(prompt: str) -> str:
    """
    Template-based fallback — works completely offline.
    Returns a helpful answer using the context embedded in the prompt.
    """
    # Extract context between the markers if present
    ctx_start = prompt.find("CONTEXT:")
    ctx_end   = prompt.find("QUESTION:")
    context   = prompt[ctx_start+8:ctx_end].strip() if ctx_start != -1 and ctx_end != -1 else ""
    question  = prompt[ctx_end+9:].strip() if ctx_end != -1 else prompt

    if context:
        # Use first 800 chars of context as the answer base
        snippet = context[:800].replace("\n\n", " ").strip()
        return (
            f"Based on the available study material:\n\n"
            f"{snippet}\n\n"
            f"💡 **Tip**: Connect an LLM (Groq/OpenAI/Ollama) via Settings for richer, AI-generated responses."
        )
    return (
        "I couldn't find specific information in the indexed documents for this query. "
        "Please upload relevant study material or connect an LLM provider in Settings for better results.\n\n"
        "💡 **Tip**: Try uploading a PDF or pasting text, then ask your question again."
    )
