def calculate_risk_score(
    lexical_similarity: float,
    semantic_similarity: float,
    financial_risk: float = 0,
    progress_risk: float = 0,
    document_risk: float = 0,
    weights: dict | None = None,
) -> dict:
    if weights is None:
        weights = {
            "lexical_similarity": 0.35,
            "semantic_similarity": 0.45,
            "financial_risk": 0.10,
            "progress_risk": 0.05,
            "document_risk": 0.05,
        }

    contributions = {
        "lexical_similarity": lexical_similarity * weights["lexical_similarity"] * 100,
        "semantic_similarity": semantic_similarity * weights["semantic_similarity"] * 100,
        "financial_risk": financial_risk * weights["financial_risk"] * 100,
        "progress_risk": progress_risk * weights["progress_risk"] * 100,
        "document_risk": document_risk * weights["document_risk"] * 100,
    }

    risk_score = sum(contributions.values())

    if risk_score >= 75:
        risk_level = "VERY HIGH"
    elif risk_score >= 55:
        risk_level = "HIGH"
    elif risk_score >= 35:
        risk_level = "MODERATE"
    else:
        risk_level = "LOW"

    return {
        "risk_score": round(risk_score, 2),
        "risk_level": risk_level,
        "contributions": {k: round(v, 2) for k, v in contributions.items()},
        "weights_used": weights,
    }


if __name__ == "__main__":
    result = calculate_risk_score(
        lexical_similarity=0.82,
        semantic_similarity=0.78,
        financial_risk=0.6,
        progress_risk=0.7,
        document_risk=0.4,
    )
    print(result)
