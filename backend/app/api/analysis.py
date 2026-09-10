"""
EduIntegrity AI — Analysis API Router

Single endpoint that runs the full integrity analysis pipeline:

  Upload file
  → Extract text
  → Lexical similarity (TF-IDF)
  → Semantic similarity (embeddings)
  → Risk score calculation
  → IBM Granite assessment
  → Return complete report

The reference text that the submission is compared against is also
uploaded by the instructor (e.g. a previous submission or known source).
If no reference is provided, a built-in sample corpus is used.
"""

import os
from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel

from app.services.extractor import ALLOWED_EXTENSIONS, extract_text_from_bytes
from app.services.lexical_similarity import lexical_similarity
from app.services.semantic_similarity import semantic_similarity
from app.services.risk_scoring import calculate_risk_score
from app.services.granite_reasoning import generate_assessment


router = APIRouter(
    prefix="/analysis",
    tags=["Analysis"],
)


# ─── Response schema ─────────────────────────────────────────────────────────

class AnalysisReport(BaseModel):
    """Complete integrity analysis report returned to the instructor."""

    # Submission metadata
    filename: str
    word_count: int
    char_count: int
    text_preview: str

    # Similarity scores (0.0 – 1.0)
    lexical_similarity_score: float
    semantic_similarity_score: float

    # Risk assessment
    risk_score: float            # 0 – 100
    risk_level: str              # LOW / MODERATE / HIGH / VERY HIGH
    risk_band_description: str
    risk_color: str
    risk_contributions: dict
    risk_weights: dict

    # IBM Granite natural-language assessment
    granite_assessment: str
    granite_source: str          # "granite" | "fallback"

    # System disclaimer — always shown
    disclaimer: str


# Built-in reference corpus used when no reference file is uploaded.
# In a real deployment this would come from a database of past submissions.
_DEFAULT_REFERENCE = (
    "Academic integrity requires students to submit original work. "
    "Plagiarism involves presenting someone else's ideas, words, or work as your own. "
    "Proper citation and attribution are fundamental expectations in all academic submissions. "
    "Students must acknowledge all sources used in their work, whether quoted directly or paraphrased. "
    "Academic misconduct includes copying, paraphrasing without attribution, and falsifying references. "
    "Institutions rely on honest scholarship to maintain the value of academic credentials."
)


def _extract_matched_passages(text1: str, text2: str, max_passages: int = 5) -> str:
    """
    Find short overlapping phrases between two texts.
    Returns a formatted string for the Granite prompt and UI display.

    Simple approach: find 4+ word sequences that appear in both texts.
    Good enough for an MVP without needing a full diff library.
    """
    words1 = text1.lower().split()
    words2_set = set(text2.lower().split())

    passages = []
    window = 4   # minimum phrase length in words

    i = 0
    while i <= len(words1) - window and len(passages) < max_passages:
        phrase = " ".join(words1[i:i + window])
        # Check if all words of the phrase appear in text2
        if all(w in words2_set for w in phrase.split()):
            passages.append(f'"{phrase}"')
            i += window   # skip ahead to avoid overlapping matches
        else:
            i += 1

    if not passages:
        return "No significant matching phrases detected."

    return "\n".join(f"  - {p}" for p in passages)


# ─── Endpoint ─────────────────────────────────────────────────────────────────

@router.post(
    "/analyze",
    response_model=AnalysisReport,
    summary="Run full integrity analysis on an uploaded assignment",
    description=(
        "Upload a student submission file and optionally a reference file. "
        "Returns a complete integrity report including similarity scores, "
        "risk assessment, and IBM Granite explanation. "
        "This report is advisory only — the instructor makes the final decision."
    ),
)
async def analyze_submission(
    submission: UploadFile = File(..., description="Student submission (.pdf, .docx, or .txt)"),
    reference:  UploadFile = File(None, description="Reference file to compare against (optional)"),
) -> AnalysisReport:
    """
    Full analysis pipeline:
    1. Extract text from submission
    2. Extract or use default reference text
    3. Compute lexical similarity (TF-IDF)
    4. Compute semantic similarity (embeddings)
    5. Calculate risk score
    6. Generate Granite assessment
    7. Return complete report
    """

    # ── 1. Validate and extract submission ───────────────────────────────────
    sub_filename = submission.filename or "submission"
    sub_suffix = "." + sub_filename.rsplit(".", 1)[-1].lower() if "." in sub_filename else ""

    if sub_suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type '{sub_suffix}'. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )

    sub_bytes = await submission.read()
    if not sub_bytes:
        raise HTTPException(status_code=422, detail="Submission file is empty.")

    max_size = int(os.getenv("MAX_FILE_SIZE_BYTES", 10 * 1024 * 1024))
    if len(sub_bytes) > max_size:
        raise HTTPException(status_code=413, detail="Submission file too large (max 10 MB).")

    try:
        sub_result = extract_text_from_bytes(sub_bytes, sub_filename)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    submission_text = sub_result["text"]

    # ── 2. Get reference text ─────────────────────────────────────────────────
    if reference and reference.filename:
        ref_bytes = await reference.read()
        try:
            ref_result = extract_text_from_bytes(ref_bytes, reference.filename)
            reference_text = ref_result["text"]
        except (ValueError, Exception):
            # If reference extraction fails, fall back to default corpus
            reference_text = _DEFAULT_REFERENCE
    else:
        reference_text = _DEFAULT_REFERENCE

    # ── 3. Lexical similarity ─────────────────────────────────────────────────
    lex_score = lexical_similarity(submission_text, reference_text)

    # ── 4. Semantic similarity ────────────────────────────────────────────────
    # Truncate to 512 words for embedding model input limit
    sub_truncated = " ".join(submission_text.split()[:512])
    ref_truncated = " ".join(reference_text.split()[:512])
    sem_score = semantic_similarity(sub_truncated, ref_truncated)

    # ── 5. Risk score ─────────────────────────────────────────────────────────
    risk = calculate_risk_score(
        lexical_similarity=lex_score,
        semantic_similarity=sem_score,
    )

    # ── 6. Build Granite evidence and get assessment ──────────────────────────
    matched = _extract_matched_passages(submission_text, reference_text)
    evidence = {
        "filename":             sub_filename,
        "word_count":           sub_result["word_count"],
        "lexical_similarity":   lex_score,
        "semantic_similarity":  sem_score,
        "risk_score":           risk["risk_score"],
        "risk_level":           risk["risk_level"],
        "matched_passages":     matched,
    }

    assessment = generate_assessment(evidence)

    # Determine if Granite actually responded or fallback was used
    required_env = ["IBM_CLOUD_API_KEY", "WATSONX_PROJECT_ID", "GRANITE_MODEL_ID"]
    granite_configured = all(
        os.getenv(k) and "your_" not in os.getenv(k, "")
        for k in required_env
    )
    granite_source = "granite" if granite_configured else "fallback"

    # ── 7. Return report ──────────────────────────────────────────────────────
    return AnalysisReport(
        filename=sub_filename,
        word_count=sub_result["word_count"],
        char_count=sub_result["char_count"],
        text_preview=submission_text[:300],
        lexical_similarity_score=round(lex_score, 4),
        semantic_similarity_score=round(sem_score, 4),
        risk_score=risk["risk_score"],
        risk_level=risk["risk_level"],
        risk_band_description=risk["risk_band_description"],
        risk_color=risk["risk_color"],
        risk_contributions=risk["contributions"],
        risk_weights=risk["weights_used"],
        granite_assessment=assessment,
        granite_source=granite_source,
        disclaimer=risk["disclaimer"],
    )
