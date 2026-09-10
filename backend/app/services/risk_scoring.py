"""
EduIntegrity AI — Risk Scoring Service

Combines all analysis component scores into a single 0-100 risk score.

IMPORTANT DISCLAIMER:
  These weights are project-defined values created for this prototype.
  They are NOT scientifically validated thresholds.
  The risk score is an indicator to support instructor review —
  it is NOT proof of plagiarism or academic misconduct.
  The instructor always makes the final decision.

Component weights (must sum to 1.0):
  - semantic_similarity  : 0.25  (paraphrasing detection)
  - lexical_similarity   : 0.20  (direct text overlap)
  - style_deviation      : 0.20  (unusual writing style change)
  - historical_anomaly   : 0.15  (deviation from student's past work)
  - citation_anomaly     : 0.10  (unusual citation patterns)
  - ai_indicator         : 0.10  (writing patterns consistent with AI assistance)

For the MVP, style_deviation, historical_anomaly, citation_anomaly,
and ai_indicator are optional — they default to 0.0 when not provided.
"""

import os


def _load_weights() -> dict:
    """
    Load weights from environment variables, falling back to defaults.
    This makes them configurable without changing code.
    """
    return {
        "semantic_similarity": float(os.getenv("WEIGHT_SEMANTIC_SIMILARITY", 0.25)),
        "lexical_similarity":  float(os.getenv("WEIGHT_LEXICAL_SIMILARITY",  0.20)),
        "style_deviation":     float(os.getenv("WEIGHT_STYLE_DEVIATION",     0.20)),
        "historical_anomaly":  float(os.getenv("WEIGHT_HISTORICAL_ANOMALY",  0.15)),
        "citation_anomaly":    float(os.getenv("WEIGHT_CITATION_ANOMALY",    0.10)),
        "ai_indicator":        float(os.getenv("WEIGHT_AI_INDICATOR",        0.10)),
    }


# Risk band thresholds (project-defined)
_BANDS = [
    (81, "VERY HIGH"),
    (61, "HIGH"),
    (31, "MODERATE"),
    (0,  "LOW"),
]

# Human-readable descriptions shown in the UI
_BAND_DESCRIPTIONS = {
    "LOW":       "Low risk indicators detected. Routine review recommended.",
    "MODERATE":  "Moderate risk indicators present. Closer review recommended.",
    "HIGH":      "High risk indicators detected. Instructor review strongly recommended.",
    "VERY HIGH": "Very high risk indicators detected. Immediate instructor review required.",
}

# UI color hints for the frontend
_BAND_COLORS = {
    "LOW":       "#16a34a",   # green
    "MODERATE":  "#d97706",   # amber
    "HIGH":      "#dc2626",   # red
    "VERY HIGH": "#7f1d1d",   # dark red
}


def _get_band(score: float) -> str:
    for threshold, band in _BANDS:
        if score >= threshold:
            return band
    return "LOW"


def calculate_risk_score(
    lexical_similarity: float,
    semantic_similarity: float,
    style_deviation: float = 0.0,
    historical_anomaly: float = 0.0,
    citation_anomaly: float = 0.0,
    ai_indicator: float = 0.0,
    weights: dict | None = None,
) -> dict:
    """
    Calculate a 0-100 academic integrity risk score.

    Args:
        lexical_similarity  : 0.0-1.0  TF-IDF cosine similarity score
        semantic_similarity : 0.0-1.0  Embedding cosine similarity score
        style_deviation     : 0.0-1.0  How much style differs from baseline (0 = no data)
        historical_anomaly  : 0.0-1.0  Deviation from student's historical profile (0 = no data)
        citation_anomaly    : 0.0-1.0  Citation pattern anomaly score (0 = no data)
        ai_indicator        : 0.0-1.0  AI-authorship indicator (0 = no data)
        weights             : Optional custom weights dict. Uses env/defaults if None.

    Returns:
        dict with risk_score, risk_level, risk_band_description,
        risk_color, contributions, weights_used, disclaimer
    """
    if weights is None:
        weights = _load_weights()

    # Each component contributes: score × weight × 100
    # Score is 0.0-1.0, weight is 0.0-1.0, result is 0-100 proportional contribution
    contributions = {
        "semantic_similarity": round(semantic_similarity * weights["semantic_similarity"] * 100, 2),
        "lexical_similarity":  round(lexical_similarity  * weights["lexical_similarity"]  * 100, 2),
        "style_deviation":     round(style_deviation     * weights["style_deviation"]     * 100, 2),
        "historical_anomaly":  round(historical_anomaly  * weights["historical_anomaly"]  * 100, 2),
        "citation_anomaly":    round(citation_anomaly    * weights["citation_anomaly"]    * 100, 2),
        "ai_indicator":        round(ai_indicator        * weights["ai_indicator"]        * 100, 2),
    }

    risk_score = round(sum(contributions.values()), 2)
    band = _get_band(risk_score)

    return {
        "risk_score": risk_score,
        "risk_level": band,
        "risk_band_description": _BAND_DESCRIPTIONS[band],
        "risk_color": _BAND_COLORS[band],
        "contributions": contributions,
        "weights_used": weights,
        "disclaimer": (
            "This risk score is a project-defined indicator to assist instructor review. "
            "It is NOT proof of plagiarism or misconduct. "
            "The instructor makes the final academic integrity decision."
        ),
    }


if __name__ == "__main__":
    result = calculate_risk_score(
        lexical_similarity=0.72,
        semantic_similarity=0.81,
        style_deviation=0.45,
        historical_anomaly=0.60,
    )
    print(f"Risk Score : {result['risk_score']}")
    print(f"Risk Level : {result['risk_level']}")
    print(f"Description: {result['risk_band_description']}")
    print(f"Breakdown  : {result['contributions']}")
