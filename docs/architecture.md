# EduIntegrity AI — Architecture

## System Overview

```
┌──────────────────────────────────────────────────────────────┐
│                    Instructor's Browser                       │
│               HTML/CSS/JS Dashboard (index.html)             │
│   Upload Assignment → View Risk Report → Record Decision     │
└───────────────────────────┬──────────────────────────────────┘
                            │ HTTP REST API
                            ▼
┌──────────────────────────────────────────────────────────────┐
│                 FastAPI Backend (Python)                      │
│   POST /api/v1/analysis/analyze                              │
│   POST /api/v1/extraction/extract-text                       │
│   GET  /health                                               │
└──────┬───────────────────────────────────────────────────────┘
       │
       ├── services/extractor.py         PDF / DOCX / TXT → clean text
       ├── services/lexical_similarity.py TF-IDF cosine similarity score
       ├── services/semantic_similarity.py Sentence embeddings similarity
       ├── services/writing_style.py      8 style metrics + deviation score
       ├── services/risk_scoring.py       6-component weighted risk score
       └── services/granite_reasoning.py  IBM Granite via watsonx.ai
                                               │
                                               ▼
                                     IBM watsonx.ai (Granite)
                                     Natural-language assessment
```

---

## Analysis Pipeline

```
Instructor uploads file (.pdf / .docx / .txt)
        │
        ▼
[extractor.py]
  Validate file type + size
  Extract raw text (pypdf / python-docx / plain read)
  Clean whitespace
  Guard: reject < 50 characters
        │
        ├──────────────────────────────────────┐
        ▼                                      ▼
[lexical_similarity.py]             [semantic_similarity.py]
  TF-IDF vectorisation                Sentence Transformer encode
  Cosine similarity vs reference      Cosine similarity vs reference
  Returns: 0.0 – 1.0                  Returns: 0.0 – 1.0
        │                                      │
        └──────────────┬───────────────────────┘
                       │
                       ▼
            [writing_style.py]
              avg_sentence_length
              avg_word_length
              vocabulary_diversity  (Type-Token Ratio)
              punctuation_density
              readability_score     (Flesch Reading Ease)
              long_word_ratio
              sentence_length_std
              calculate_style_deviation() vs reference profile
              Returns: style_profile dict + deviation 0.0–1.0
                       │
                       ▼
            [risk_scoring.py]
              score = (sem × 0.25 + lex × 0.20 + style × 0.20
                       + hist × 0.15 + cit × 0.10 + ai × 0.10) × 100
              Assigns risk band: LOW / MODERATE / HIGH / VERY HIGH
              Returns: risk_score, risk_level, contributions, disclaimer
                       │
                       ▼
            [granite_reasoning.py]
              Builds structured evidence prompt
              Calls IBM Granite via watsonx.ai SDK
              Falls back to rule-based summary if unconfigured
              Returns: natural-language advisory assessment
                       │
                       ▼
            AnalysisReport (Pydantic response)
              → returned to frontend as JSON
```

---

## Risk Score Formula

```
Risk Score (0–100) =
  semantic_similarity  × 0.25 × 100
  + lexical_similarity × 0.20 × 100
  + style_deviation    × 0.20 × 100
  + historical_anomaly × 0.15 × 100   ← uses reference-text proxy in MVP
  + citation_anomaly   × 0.10 × 100   ← 0.0 in MVP (not yet computed)
  + ai_indicator       × 0.10 × 100   ← 0.0 in MVP (not yet computed)

Each input is normalised to [0.0, 1.0] before weighting.
Weights are configurable via environment variables (see .env.example).

Risk Bands (project-defined):
  0–30   → LOW
  31–60  → MODERATE
  61–80  → HIGH
  81–100 → VERY HIGH
```

---

## File Structure

```
EduIntegrity-AI/
├── backend/
│   ├── app/
│   │   ├── main.py                    FastAPI app, CORS, router registration
│   │   ├── api/
│   │   │   ├── analysis.py            POST /api/v1/analysis/analyze
│   │   │   └── extraction.py          POST /api/v1/extraction/extract-text
│   │   ├── schemas/
│   │   │   └── extraction.py          Pydantic response schema for extraction
│   │   └── services/
│   │       ├── extractor.py           Text extraction (PDF/DOCX/TXT)
│   │       ├── lexical_similarity.py  TF-IDF cosine similarity
│   │       ├── semantic_similarity.py Sentence Transformers embeddings
│   │       ├── writing_style.py       8 style metrics + deviation
│   │       ├── risk_scoring.py        Weighted 0-100 risk score
│   │       └── granite_reasoning.py   IBM Granite via watsonx.ai
│   ├── tests/
│   │   └── test_extractor.py          16 unit tests
│   ├── conftest.py                    pytest sys.path config
│   ├── requirements.txt               Python dependencies (actual only)
│   └── test_granite.py               IBM Granite connection test
├── frontend/
│   └── index.html                    Single-page instructor dashboard
├── data/
│   └── samples/                      Test assignment files
├── docker/
│   ├── Dockerfile.backend            Multi-stage Python image
│   ├── Dockerfile.frontend           Nginx static server
│   └── docker-compose.yml            Backend + frontend services
├── docs/
│   └── architecture.md              This file
├── .env.example                      Environment variable template
├── .gitignore
├── README.md
└── PROJECT_NOTES.md
```

---

## IBM Technology Used

| Technology | Role |
|---|---|
| **IBM Granite** | Receives structured evidence dict; generates natural-language advisory assessment |
| **IBM watsonx.ai** | Hosts Granite; accessed via `ibm-watsonx-ai` Python SDK |
| **IBM Bob** | Primary coding assistant — generated all services, tests, and architecture |

---

## What Is Not In This MVP

The following were designed and documented but not implemented in the
time available:

- **PostgreSQL database** — no persistence between sessions
- **JWT authentication** — no login required
- **RAG pipeline** — ChromaDB ingestion and retrieval not built
- **watsonx Orchestrate** — single-endpoint pipeline used instead of agents
- **Full historical profiles** — reference-text proxy used as baseline
