from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def lexical_similarity(text1: str, text2: str) -> float:
    corpus = [text1, text2]

    vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words="english")
    tfidf_matrix = vectorizer.fit_transform(corpus)

    similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
    return float(similarity)


if __name__ == "__main__":
    text_a = "Academic integrity means doing your own work and giving credit to others."
    text_b = "Academic integrity requires honesty, originality, and proper attribution of sources."
    text_c = "The weather in this city is very pleasant today."

    print("Identical docs:", lexical_similarity(text_a, text_a))
    print("Same meaning docs:", lexical_similarity(text_a, text_b))
    print("Different docs:", lexical_similarity(text_a, text_c))
