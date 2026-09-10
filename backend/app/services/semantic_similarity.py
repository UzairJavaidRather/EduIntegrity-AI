from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


_model = None


def _get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def semantic_similarity(text1: str, text2: str) -> float:
    model = _get_model()
    embeddings = model.encode([text1, text2])
    score = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
    return float(score)


if __name__ == "__main__":
    text_a = "Academic integrity means doing your own work and giving credit to others."
    text_b = "Academic integrity requires honesty, originality, and proper attribution of sources."
    text_c = "The weather in this city is very pleasant today."

    print("Paraphrased (same meaning):", semantic_similarity(text_a, text_b))
    print("Unrelated meaning:", semantic_similarity(text_a, text_c))
