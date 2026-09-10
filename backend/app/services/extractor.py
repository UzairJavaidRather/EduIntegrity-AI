from pathlib import Path
import re

from pypdf import PdfReader
from docx import Document


def _clean_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def extract_text(file_path: str) -> str:
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    suffix = path.suffix.lower()

    if suffix == ".pdf":
        reader = PdfReader(str(path))
        pages = []
        for page in reader.pages:
            pages.append(page.extract_text() or "")
        text = "\n".join(pages)

    elif suffix == ".docx":
        doc = Document(str(path))
        text = "\n".join(paragraph.text for paragraph in doc.paragraphs)

    elif suffix in {".txt", ".md"}:
        text = path.read_text(encoding="utf-8", errors="ignore")

    else:
        raise ValueError(f"Unsupported file type: {suffix}")

    return _clean_text(text)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python extractor.py <file_path>")
        raise SystemExit(1)

    file_path = sys.argv[1]
    text = extract_text(file_path)
    print(f"Extracted {len(text)} characters:")
    print(text[:1500])
