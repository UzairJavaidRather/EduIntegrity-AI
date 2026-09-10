"""
EduIntegrity AI — Text Extraction Service

Responsibility: Given a file path, extract clean readable text from it.

Supported formats:
  - PDF  (.pdf)  — using pypdf
  - DOCX (.docx) — using python-docx
  - TXT  (.txt)  — plain read
  - MD   (.md)   — treated as plain text

This service is intentionally pure:
  - It takes a file path string as input
  - It returns a result dict (or raises a ValueError with a clear message)
  - It has no knowledge of HTTP, FastAPI, or database models
  - This makes it directly testable with plain Python (no web server needed)

Design note: We return a dict rather than just a string so callers
get word count and file type without having to compute them again.
"""

import re
import tempfile
from pathlib import Path

from pypdf import PdfReader
from docx import Document


# Minimum number of characters we require from a successful extraction.
# A PDF with fewer characters is likely image-only or corrupt.
_MIN_CHARS = 50

# Allowed file extensions. Checked here and also at the API layer.
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md"}


def _clean_text(text: str) -> str:
    """
    Normalize whitespace in extracted text.

    What this does:
      - Collapses multiple spaces/tabs/newlines into a single space
      - Strips leading and trailing whitespace

    What this does NOT do:
      - Remove punctuation (needed for n-gram and style analysis)
      - Change case (needed for proper-noun detection)
      - Remove sentences (needed for all downstream analysis)
    """
    # Replace any sequence of whitespace characters with a single space
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _extract_from_pdf(path: Path) -> str:
    """Extract text from a PDF file using pypdf."""
    reader = PdfReader(str(path))

    if len(reader.pages) == 0:
        raise ValueError("PDF has no pages.")

    pages = []
    for page in reader.pages:
        # extract_text() returns None for image-only pages — default to ""
        page_text = page.extract_text() or ""
        pages.append(page_text)

    return "\n".join(pages)


def _extract_from_docx(path: Path) -> str:
    """Extract text from a DOCX file using python-docx."""
    doc = Document(str(path))

    # Each paragraph is a block of text. Join with newlines to preserve
    # document structure (important for sentence boundary detection later).
    paragraphs = [paragraph.text for paragraph in doc.paragraphs if paragraph.text.strip()]
    return "\n".join(paragraphs)


def _extract_from_txt(path: Path) -> str:
    """Read plain text files. Uses UTF-8 with a fallback for legacy encodings."""
    # Try UTF-8 first (modern standard)
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        # Fall back to latin-1 which can decode any byte sequence
        return path.read_text(encoding="latin-1", errors="replace")


def extract_text_from_path(file_path: str) -> dict:
    """
    Extract and clean text from a supported file.

    Args:
        file_path: Absolute or relative path to the file.

    Returns:
        A dict with keys:
          - text       (str)  : The cleaned extracted text
          - file_type  (str)  : The extension without dot (e.g. "pdf")
          - char_count (int)  : Length of cleaned text
          - word_count (int)  : Number of whitespace-separated words

    Raises:
        FileNotFoundError : If the file does not exist at the given path.
        ValueError        : If file type is unsupported, or extraction yields
                            too little text (likely corrupt or image-only file).
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    suffix = path.suffix.lower()

    if suffix not in ALLOWED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file type: '{suffix}'. "
            f"Allowed extensions: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )

    # Dispatch to the correct extractor based on file extension
    if suffix == ".pdf":
        raw_text = _extract_from_pdf(path)
    elif suffix == ".docx":
        raw_text = _extract_from_docx(path)
    else:
        # .txt and .md both treated as plain text
        raw_text = _extract_from_txt(path)

    # Clean up whitespace
    cleaned = _clean_text(raw_text)

    # Reject suspiciously short results — likely a corrupt or image-only file
    if len(cleaned) < _MIN_CHARS:
        raise ValueError(
            f"Extracted text is too short ({len(cleaned)} characters). "
            "The file may be corrupt, image-only, or password-protected."
        )

    word_count = len(cleaned.split())

    return {
        "text": cleaned,
        "file_type": suffix.lstrip("."),   # "pdf", "docx", "txt"
        "char_count": len(cleaned),
        "word_count": word_count,
    }


def extract_text_from_bytes(file_bytes: bytes, filename: str) -> dict:
    """
    Extract text from raw bytes (as received from an HTTP file upload).

    This is the function called by the FastAPI route handler.
    It writes bytes to a temporary file, calls extract_text_from_path,
    then cleans up the temp file whether or not extraction succeeds.

    Args:
        file_bytes : Raw bytes of the uploaded file.
        filename   : Original filename — used to determine file extension.

    Returns:
        Same dict as extract_text_from_path, plus the original filename.

    Raises:
        ValueError        : For unsupported types or failed extraction.
        FileNotFoundError : Should not happen in normal flow (temp file always created).
    """
    suffix = Path(filename).suffix.lower()

    if suffix not in ALLOWED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file type: '{suffix}'. "
            f"Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )

    # Write to a named temporary file so pypdf/python-docx can open it by path.
    # The suffix parameter ensures the temp file has the correct extension,
    # which is required for pypdf and python-docx to work correctly.
    # delete=False means we control deletion ourselves in the finally block.
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            suffix=suffix, delete=False
        ) as tmp_file:
            tmp_file.write(file_bytes)
            tmp_path = tmp_file.name

        result = extract_text_from_path(tmp_path)

    finally:
        # Always clean up the temp file, even if extraction raised an exception
        if tmp_path:
            Path(tmp_path).unlink(missing_ok=True)

    return result


# ─── Quick manual test ───────────────────────────────────────────────────────
# Run this file directly to test extraction:
#   cd backend
#   venv\Scripts\python app\services\extractor.py data\samples\sample_essay.txt

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python extractor.py <file_path>")
        raise SystemExit(1)

    result = extract_text_from_path(sys.argv[1])
    print(f"File type : {result['file_type']}")
    print(f"Characters: {result['char_count']}")
    print(f"Words     : {result['word_count']}")
    print(f"\nPreview:\n{result['text'][:400]}")
