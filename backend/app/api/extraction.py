"""
EduIntegrity AI — Extraction API Router

This module defines HTTP routes related to file upload and text extraction.

Route handlers are intentionally thin:
  - Receive the HTTP request
  - Validate inputs at the HTTP layer (file size, content-type header)
  - Call the appropriate service function
  - Convert service errors to appropriate HTTP responses
  - Return a structured Pydantic schema response

All business logic (extraction, cleaning, validation of content) lives
in services/extractor.py, not here.
"""

import os

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.schemas.extraction import ExtractionResponse
from app.services.extractor import ALLOWED_EXTENSIONS, extract_text_from_bytes

# APIRouter lets us group related routes together.
# The prefix and tags are applied to every route defined in this file.
# The prefix /api/v1 is added when this router is registered in main.py
router = APIRouter(
    prefix="/extraction",
    tags=["Text Extraction"],
)

# Maximum file size in bytes (default: 10 MB)
# Read from environment variable so it's configurable without code changes
_MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE_BYTES", 10 * 1024 * 1024))  # 10 MB


@router.post(
    "/extract-text",
    response_model=ExtractionResponse,
    summary="Upload and extract text from an assignment file",
    description=(
        "Accepts a PDF, DOCX, or TXT file and returns the extracted text "
        "along with metadata (word count, character count, preview). "
        "The extracted text is the input for all downstream analysis."
    ),
    responses={
        200: {"description": "Text extracted successfully"},
        413: {"description": "File too large"},
        415: {"description": "Unsupported file type"},
        422: {"description": "File could not be processed (corrupt, image-only, empty)"},
    },
)
async def extract_text_endpoint(
    file: UploadFile = File(..., description="Assignment file (.pdf, .docx, or .txt)"),
) -> ExtractionResponse:
    """
    Upload an assignment file and extract its text content.

    This is the first step in the analysis pipeline. The returned
    `full_text` field is passed to all analysis services.

    Steps performed:
      1. Validate file extension
      2. Read file bytes and validate size
      3. Call extraction service (handles PDF/DOCX/TXT)
      4. Return structured response
    """

    # ── Step 1: Validate file extension ──────────────────────────────────────
    # We check the extension from the filename. In Phase 11 (security hardening)
    # we'll also inspect the actual file magic bytes for additional safety.
    filename = file.filename or "unknown"
    suffix = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=(
                f"File type '{suffix}' is not supported. "
                f"Allowed types: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
            ),
        )

    # ── Step 2: Read file bytes and validate size ─────────────────────────────
    # We read the entire file into memory here. For Phase 2 this is fine
    # (max 10 MB). For very large submissions, streaming would be better,
    # but that's beyond the MVP scope.
    file_bytes = await file.read()

    if len(file_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="The uploaded file is empty.",
        )

    if len(file_bytes) > _MAX_FILE_SIZE:
        max_mb = _MAX_FILE_SIZE // (1024 * 1024)
        actual_mb = len(file_bytes) / (1024 * 1024)
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=(
                f"File too large: {actual_mb:.1f} MB. "
                f"Maximum allowed: {max_mb} MB."
            ),
        )

    # ── Step 3: Extract text via service ──────────────────────────────────────
    # The service raises ValueError with clear messages for known failure modes.
    # We catch those and convert them to HTTP 422 responses.
    try:
        result = extract_text_from_bytes(file_bytes, filename)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )

    # ── Step 4: Build and return the response ─────────────────────────────────
    return ExtractionResponse(
        filename=filename,
        file_type=result["file_type"],
        char_count=result["char_count"],
        word_count=result["word_count"],
        text_preview=result["text"][:300],
        full_text=result["text"],
        status="success",
    )
