# EduIntegrity AI
### AI-Driven Plagiarism Intelligence for Assignments

> **Disclaimer:** This system identifies suspicious patterns and provides evidence-based risk indicators. It does **not** automatically accuse any student of plagiarism or academic misconduct. The instructor always makes the final decision.

---

## What Is This?

EduIntegrity AI is a web-based academic integrity analysis platform that helps instructors identify potential integrity concerns in student assignments. The system performs multi-dimensional analysis and presents a transparent, explainable risk score to support instructor review.

IBM Granite (via IBM watsonx.ai) provides the contextual AI reasoning layer — it interprets structured evidence and generates natural-language explanations that the instructor can act on.

---

## How It Works

```
Instructor uploads assignment
        ↓
Text extraction (PDF / DOCX / TXT)
        ↓
Lexical similarity   →  TF-IDF + cosine similarity
Semantic similarity  →  Sentence embeddings (all-MiniLM-L6-v2)
Writing style        →  8 measurable style metrics + deviation score
        ↓
Risk score calculation (6-component weighted score, 0–100)
        ↓
IBM Granite assessment via watsonx.ai
        ↓
Instructor dashboard — evidence, score, explanation, decision section
```

---

## Technology Stack (MVP)

| Layer | Technology |
|---|---|
| Frontend | HTML / CSS / JavaScript (single-page dashboard) |
| Backend | Python 3.11, FastAPI |
| AI Platform | IBM watsonx.ai |
| AI Model | IBM Granite |
| Semantic Embeddings | Sentence Transformers (`all-MiniLM-L6-v2`) |
| Lexical Analysis | scikit-learn (TF-IDF, cosine similarity) |
| Containerization | Docker, Docker Compose |
| Version Control | GitHub |

> **IBM Bob** was used as the primary coding assistant throughout — generating services, writing tests, designing the architecture, and integrating IBM watsonx.ai.

---

## Analysis Dimensions

| Dimension | Method | Weight |
|---|---|---|
| Semantic Similarity | Sentence embeddings + cosine similarity | 25% |
| Lexical Similarity | TF-IDF + cosine similarity | 20% |
| Writing Style Deviation | 8 measurable metrics (Flesch, TTR, sentence length…) | 20% |
| Historical Anomaly | Deviation from student's past work | 15% |
| Citation Anomaly | Unusual citation patterns | 10% |
| AI-Authorship Indicator | Writing patterns consistent with AI assistance | 10% |

> These weights are **project-defined values** — not scientifically universal thresholds. The risk score is an advisory indicator. The instructor makes the final decision.

**Risk Bands:**
| Score | Band |
|---|---|
| 0–30 | 🟢 LOW |
| 31–60 | 🟡 MODERATE |
| 61–80 | 🔴 HIGH |
| 81–100 | ⛔ VERY HIGH |

---

## Quick Start

### Prerequisites
- Python 3.10+
- IBM Cloud account with watsonx.ai access

### 1. Clone and configure
```bash
git clone https://github.com/your-username/EduIntegrity-AI.git
cd EduIntegrity-AI
cp .env.example .env
# Edit .env with your IBM credentials
```

### 2. Start the backend
```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

pip install fastapi uvicorn[standard] pydantic python-dotenv python-multipart pypdf python-docx scikit-learn sentence-transformers ibm-watsonx-ai

uvicorn app.main:app --reload
```

### 3. Open the frontend
```bash
# Simply open in a browser:
start frontend\index.html
```

The backend runs at `http://localhost:8000`  
API docs at `http://localhost:8000/docs`

### 4. With Docker
```bash
cd docker
docker-compose up --build
```

---

## Demo Scenarios

| Submission file | Reference file | Expected result |
|---|---|---|
| `data/samples/sample_essay.txt` | *(none — uses default corpus)* | LOW risk |
| `data/samples/high_similarity_essay.txt` | `data/samples/sample_essay.txt` | MODERATE–HIGH risk |

---

## Project Structure

```
EduIntegrity-AI/
├── backend/
│   ├── app/
│   │   ├── main.py                  ← FastAPI entry point
│   │   ├── api/
│   │   │   ├── analysis.py          ← POST /api/v1/analysis/analyze
│   │   │   └── extraction.py        ← POST /api/v1/extraction/extract-text
│   │   └── services/
│   │       ├── extractor.py         ← PDF/DOCX/TXT text extraction
│   │       ├── lexical_similarity.py← TF-IDF cosine similarity
│   │       ├── semantic_similarity.py← Sentence embeddings
│   │       ├── writing_style.py     ← 8 style metrics + deviation score
│   │       ├── risk_scoring.py      ← 6-component risk score (0–100)
│   │       └── granite_reasoning.py ← IBM Granite via watsonx.ai
│   └── tests/
│       └── test_extractor.py        ← 16 unit tests (all passing)
├── frontend/
│   └── index.html                   ← Instructor dashboard
├── data/samples/                    ← Test assignment files
├── docker/                          ← Dockerfile + docker-compose
├── docs/                            ← Architecture diagrams
├── .env.example                     ← Environment variable template
└── PROJECT_NOTES.md                 ← Development log
```

---

## IBM Bob Usage

IBM Bob was the primary development assistant for this project:
- Generated all service layer code and architecture
- Wrote the 16-test unit test suite
- Designed the thin-router / thick-service pattern
- Implemented temp file cleanup and encoding fallback patterns
- Integrated IBM watsonx.ai SDK with graceful fallback
- Built the Docker multi-stage configuration
- Reviewed and explained all generated code

---

## Important Notes

- API keys and credentials are **never** committed to Git — stored in `.env` only
- The `.env` file is excluded by `.gitignore`
- All risk scores and indicators are advisory only
- The system never says "the student plagiarised" — it surfaces patterns for instructor review
- The instructor always makes the final academic integrity decision
