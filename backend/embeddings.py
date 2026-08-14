import numpy as np
from typing import List

def cosine_similarity(a: List[float], b: List[float]) -> float:
    a, b = np.array(a), np.array(b)
    norm_a, norm_b = np.linalg.norm(a), np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))

def tfidf_embed(texts: List[str], query: str = None) -> List[List[float]]:
    """Simple TF-IDF based embedding without heavy ML models."""
    import re
    from math import log

    def tokenize(text):
        return re.findall(r'\b\w+\b', text.lower())

    corpus = texts if query is None else texts + [query]
    tokenized = [tokenize(t) for t in corpus]
    
    # Build vocab
    vocab = sorted(set(w for doc in tokenized for w in doc))
    vocab_idx = {w: i for i, w in enumerate(vocab)}
    n_docs = len(tokenized)

    # IDF
    idf = []
    for word in vocab:
        df = sum(1 for doc in tokenized if word in doc)
        idf.append(log((n_docs + 1) / (df + 1)) + 1)

    # TF-IDF vectors
    vectors = []
    for doc in tokenized:
        tf = {}
        for w in doc:
            tf[w] = tf.get(w, 0) + 1
        vec = [0.0] * len(vocab)
        for w, count in tf.items():
            if w in vocab_idx:
                vec[vocab_idx[w]] = (count / len(doc)) * idf[vocab_idx[w]]
        norm = np.linalg.norm(vec)
        vectors.append([v / norm if norm > 0 else v for v in vec])

    return vectors
