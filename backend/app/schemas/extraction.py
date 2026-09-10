"""
EduIntegrity AI — Extraction Schemas

Pydantic models define the exact shape of API request and response data.
FastAPI uses these to:
  1. Automatically validate data before it reaches route handlers
  2. Auto-generate Swagger UI documentation
  3. Serialize Python objects to JSON responses

Think of schemas as contracts: the frontend knows exactly what to expect,
and FastAPI enforces those contracts automatically.
"""

from pydantic import BaseModel, Field


class ExtractionResponse(BaseModel):
    """
    Returned by POST /api/v1/extract-text after a successful extraction.

    Contains both metadata (counts, preview) and the full extracted text.
    The full_text field is what gets passed to all downstream analysis services.
    """

    # Original filename as uploaded — useful for display and audit trail
    filename: str = Field(..., description="Original uploaded filename")

    # File extension detected — confirms what type was processed
    file_type: str = Field(..., description="Detected file type: pdf, docx, or txt")

    # Character count of the cleaned extracted text
    char_count: int = Field(..., description="Number of characters in extracted text")

    # Word count — a quick quality indicator (very low = possibly empty/corrupt)
    word_count: int = Field(..., description="Number of words in extracted text")

    # First 300 characters of the text — shown in UI as a preview before full analysis
    text_preview: str = Field(
        ...,
        description="First 300 characters of extracted text for preview"
    )

    # The complete extracted and cleaned text — fed to all analysis services
    full_text: str = Field(..., description="Complete extracted and cleaned text")

    # Extraction status — always 'success' when returned (errors raise HTTP exceptions)
    status: str = Field(default="success", description="Extraction status")

    model_config = {
        "json_schema_extra": {
            "example": {
                "filename": "essay_submission.pdf",
                "file_type": "pdf",
                "char_count": 4823,
                "word_count": 847,
                "text_preview": "Academic integrity is a foundational principle...",
                "full_text": "Academic integrity is a foundational principle...[full text]",
                "status": "success",
            }
        }
    }


class ErrorResponse(BaseModel):
    """
    Returned when an API call fails validation or processing.
    Having a consistent error shape makes frontend error handling simpler.
    """

    detail: str = Field(..., description="Human-readable error description")
    error_code: str = Field(..., description="Machine-readable error code")

    model_config = {
        "json_schema_extra": {
            "example": {
                "detail": "File type '.exe' is not supported. Allowed: .pdf, .docx, .txt",
                "error_code": "UNSUPPORTED_FILE_TYPE",
            }
        }
    }
