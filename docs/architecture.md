# EduIntegrity AI — Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        Instructor's Browser                              │
│                         Next.js Frontend                                 │
│   Login → Upload Assignment → View Risk Report → Make Final Decision    │
└────────────────────────────┬────────────────────────────────────────────┘
                             │ HTTPS REST API
                             ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      FastAPI Backend (Python)                            │
│  /api/v1/auth  /api/v1/submissions  /api/v1/analysis  /api/v1/reports  │
└──────┬──────────────────────────────────────────────────────────────────┘
       │
       ├──────────────────────► PostgreSQL Database
       │                         Users, Submissions, Analysis Results,
       │                         Historical Profiles, Instructor Decisions
       │
       └──────────────────────► IBM watsonx Orchestrate
                                 │  (Multi-agent coordinator)
                                 │
                  ┌──────────────┼──────────────────────────┐
                  │              │                           │
                  ▼              ▼                           ▼
        Assignment Analyzer  Similarity          Writing Style Agent
        Agent                Detection Agent     Historical Analysis
        (text extraction,    (TF-IDF, n-gram,   Agent
         preprocessing)      cosine similarity)  (style metrics,
                              Semantic Analysis   deviation detection)
                              Agent
                              (embeddings,
                               vector similarity)
                  │
                  └──────────────────────────────────────────►
                                                    Integrity Assessment Agent
                                                    (packages all evidence)
                                                         │
                                                         ▼
                                                    RAG Pipeline
                                                    (ChromaDB)
                                                    Historical assignments,
                                                    instructor feedback,
                                                    course rubrics,
                                                    integrity policies
                                                         │
                                                         ▼
                                                    IBM Granite
                                                    (via watsonx.ai)
                                                    Contextual reasoning,
                                                    explanation generation,
                                                    risk assessment
                                                         │
                                                         ▼
                                                    Risk Score Engine
                                                    (0–100, configurable weights)
                                                         │
                                                         ▼
                                                    Integrity Report
                                                    (returned to frontend)
```

---

## Analysis Pipeline

```
Instructor uploads file (.pdf / .docx / .txt)
        │
        ▼
[Assignment Analyzer Agent]
  - Validate file type and size
  - Extract raw text (pypdf / python-docx)
  - Clean and preprocess text
        │
        ▼
[Similarity Detection Agent]                [Semantic Analysis Agent]
  - TF-IDF vectorization                      - Sentence embeddings
  - Cosine similarity score                   - Vector cosine similarity
  - N-gram matching                           - Paraphrase detection
  - Extract matching passages                 - Semantic similarity score
        │                                           │
        └─────────────────────┬─────────────────────┘
                              │
                              ▼
                   [Writing Style Agent]
                     - Avg sentence length
                     - Vocabulary diversity
                     - Readability score
                     - Sentence complexity
                     - Punctuation patterns
                              │
                              ▼
                   [Historical Analysis Agent]
                     - Retrieve student's past submissions
                     - Compare style metrics
                     - Detect anomalies in writing profile
                              │
                              ▼
                   [RAG Retrieval]
                     - Query ChromaDB with submission text
                     - Retrieve relevant: historical assignments,
                       instructor feedback, assignment instructions,
                       integrity policies
                              │
                              ▼
                   [Integrity Assessment Agent]
                     - Package all scores and evidence
                     - Build structured context for Granite
                              │
                              ▼
                   [IBM Granite via watsonx.ai]
                     - Receives structured evidence
                     - Generates contextual explanation
                     - Identifies suspicious patterns
                     - Produces recommendations
                     - Output is advisory, not accusatory
                              │
                              ▼
                   [Risk Score Engine]
                     - Combines component scores
                     - Applies configurable weights
                     - Calculates 0–100 risk score
                     - Assigns risk band (LOW/MODERATE/HIGH/VERY HIGH)
                              │
                              ▼
                   [Integrity Report]
                     - Risk score + band
                     - Component breakdown
                     - Matching passages
                     - Granite explanation
                     - Evidence summary
                     - Instructor decision section
```

---

## Risk Score Formula

```
Risk Score = (semantic_sim × 0.25 +
              lexical_sim × 0.20 +
              style_deviation × 0.20 +
              historical_anomaly × 0.15 +
              citation_anomaly × 0.10 +
              ai_indicator × 0.10) × 100

Each component is normalized to [0.0, 1.0] before weighting.
Weights are configurable via environment variables.
Weights must sum to 1.0.

Risk Bands (project-defined):
  0–30   → LOW
  31–60  → MODERATE
  61–80  → HIGH
  81–100 → VERY HIGH
```

---

## Database Schema (Phase 11)

```
users               ← Instructors and admin accounts
students            ← Student records
courses             ← Course information
assignments         ← Assignment definitions and rubrics
submissions         ← Individual student submissions
analysis_results    ← Full analysis output per submission
similarity_results  ← Detailed similarity scores
style_profiles      ← Student writing style history
instructor_feedback ← Instructor notes and decisions
```

---

## Technology Decisions

| Decision | Choice | Reason |
|---|---|---|
| Backend framework | FastAPI | Fast, async, automatic OpenAPI docs, Pydantic validation |
| Frontend framework | Next.js | React-based, TypeScript, production-ready, IBM-compatible |
| Database | PostgreSQL | Relational, reliable, production-grade |
| Vector DB | ChromaDB | Persistent, easy Python integration, good for prototype |
| Embeddings | all-MiniLM-L6-v2 | Runs locally, no API key, good semantic quality |
| AI model | IBM Granite | Required by project spec, strong reasoning |
| Orchestration | watsonx Orchestrate | Required by project spec, multi-agent coordination |

---

## Security Considerations

- Credentials stored in `.env` — never in source code
- File upload validation: type, size, content checks
- JWT authentication with bcrypt password hashing
- CORS restricted to known frontend origins
- SQL injection prevented by SQLAlchemy ORM
- Input sanitization before AI prompts
- Safe logging (no credentials in logs)
