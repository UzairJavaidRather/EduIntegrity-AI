"""
EduIntegrity AI — Tests for the Text Extraction Service

Run with:
    cd backend
    venv\\Scripts\\pytest tests/test_extractor.py -v

Why test the extractor?
  The extractor is the first step in the entire pipeline.
  If it fails silently (returns empty text for a corrupt file, accepts
  a wrong file type), every downstream result becomes meaningless.
  These tests ensure the extractor behaves correctly before we build
  anything else on top of it.

Testing approach:
  We test the SERVICE FUNCTION directly (extract_text_from_path,
  extract_text_from_bytes) — not the HTTP endpoint.
  This means we don't need a running web server to run these tests.
  We create real temp files with known content and verify the output.
"""

import tempfile
from pathlib import Path

import pytest

from app.services.extractor import (
    ALLOWED_EXTENSIONS,
    extract_text_from_bytes,
    extract_text_from_path,
    _clean_text,
)


# ─── Helper ──────────────────────────────────────────────────────────────────

def _make_txt_file(content: str) -> str:
    """Write content to a temp .txt file and return its path."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False, encoding="utf-8"
    ) as f:
        f.write(content)
        return f.name


# ─── Tests for _clean_text ───────────────────────────────────────────────────

class TestCleanText:
    """Tests for the internal whitespace-cleaning function."""

    def test_collapses_multiple_spaces(self):
        result = _clean_text("hello    world")
        assert result == "hello world"

    def test_collapses_tabs(self):
        result = _clean_text("hello\t\tworld")
        assert result == "hello world"

    def test_collapses_newlines(self):
        result = _clean_text("hello\n\nworld")
        assert result == "hello world"

    def test_strips_leading_and_trailing(self):
        result = _clean_text("  hello world  ")
        assert result == "hello world"

    def test_preserves_punctuation(self):
        # Punctuation must be preserved for style analysis
        result = _clean_text("Hello, world! How are you?")
        assert "," in result
        assert "!" in result
        assert "?" in result

    def test_empty_string(self):
        result = _clean_text("")
        assert result == ""


# ─── Tests for extract_text_from_path ────────────────────────────────────────

class TestExtractTextFromPath:
    """Tests for file-path-based extraction."""

    def test_extracts_txt_file(self):
        content = "Academic integrity means honesty and original work. " * 5
        path = _make_txt_file(content)
        try:
            result = extract_text_from_path(path)
            assert result["file_type"] == "txt"
            assert result["char_count"] > 0
            assert result["word_count"] > 0
            assert "Academic integrity" in result["text"]
        finally:
            Path(path).unlink(missing_ok=True)

    def test_returns_correct_word_count(self):
        # 10 words exactly
        content = "one two three four five six seven eight nine ten. " * 3
        path = _make_txt_file(content)
        try:
            result = extract_text_from_path(path)
            # Word count should be roughly 30 (10 words × 3 repetitions)
            assert result["word_count"] >= 25
        finally:
            Path(path).unlink(missing_ok=True)

    def test_raises_for_unsupported_extension(self):
        with tempfile.NamedTemporaryFile(suffix=".exe", delete=False) as f:
            f.write(b"fake content that is definitely long enough to pass")
            tmp_path = f.name
        try:
            with pytest.raises(ValueError, match="Unsupported file type"):
                extract_text_from_path(tmp_path)
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    def test_raises_for_nonexistent_file(self):
        with pytest.raises(FileNotFoundError):
            extract_text_from_path("/nonexistent/path/essay.txt")

    def test_raises_for_too_short_content(self):
        # A file with only a few characters — should be rejected
        path = _make_txt_file("Hi.")
        try:
            with pytest.raises(ValueError, match="too short"):
                extract_text_from_path(path)
        finally:
            Path(path).unlink(missing_ok=True)

    def test_allowed_extensions_constant(self):
        # Verify the allowed set contains exactly what we expect
        assert ".pdf" in ALLOWED_EXTENSIONS
        assert ".docx" in ALLOWED_EXTENSIONS
        assert ".txt" in ALLOWED_EXTENSIONS
        assert ".md" in ALLOWED_EXTENSIONS
        assert ".exe" not in ALLOWED_EXTENSIONS
        assert ".js" not in ALLOWED_EXTENSIONS


# ─── Tests for extract_text_from_bytes ───────────────────────────────────────

class TestExtractTextFromBytes:
    """Tests for byte-based extraction (as used by the HTTP upload endpoint)."""

    def test_extracts_from_txt_bytes(self):
        content = "This is a test submission about academic integrity standards. " * 4
        file_bytes = content.encode("utf-8")
        result = extract_text_from_bytes(file_bytes, "test_essay.txt")
        assert result["file_type"] == "txt"
        assert "academic integrity" in result["text"].lower()
        assert result["char_count"] > 0

    def test_raises_for_unsupported_type_in_filename(self):
        with pytest.raises(ValueError, match="Unsupported file type"):
            extract_text_from_bytes(b"some content here that is long enough", "malware.exe")

    def test_raises_for_empty_content(self):
        # Empty bytes will produce a too-short error after extraction
        # (the file exists but has no content)
        with pytest.raises(ValueError):
            extract_text_from_bytes(b"", "empty.txt")

    def test_temp_file_is_cleaned_up(self):
        """Verify no temp files are left behind after extraction."""
        import glob
        import os

        # Count temp files before
        tmp_dir = tempfile.gettempdir()
        before = set(glob.glob(os.path.join(tmp_dir, "tmp*.txt")))

        content = "This is a valid submission text for testing purposes. " * 5
        extract_text_from_bytes(content.encode("utf-8"), "submission.txt")

        # Count temp files after
        after = set(glob.glob(os.path.join(tmp_dir, "tmp*.txt")))

        # No new .txt temp files should remain
        new_files = after - before
        assert len(new_files) == 0, f"Temp files not cleaned up: {new_files}"
