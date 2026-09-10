# EduIntegrity AI — Project Notes

This file is a living development log. Update it as you progress through each phase.

---

## Project Summary

**Name:** EduIntegrity AI — AI-Driven Plagiarism Intelligence for Assignments  
**Goal:** A web-based academic integrity analysis platform where instructors upload assignments and receive explainable, evidence-based integrity analysis powered by IBM Granite.

**Key constraint:** The system identifies suspicious indicators and calculates a risk score. It does NOT accuse students. The instructor always makes the final decision.

---

## IBM Technology Roles

| Technology | Role in This Project |
|---|---|
| **IBM Bob** | Development assistant — generates code, reviews implementation, helps with debugging and deployment |
| **IBM Granite** | AI reasoning — analyzes structured evidence, generates natural-language explanations, produces risk assessments |
| **IBM watsonx.ai** | AI platform — hosts Granite, provides the SDK and API for model inference |
| **IBM watsonx Orchestrate** | Agent coordinator — manages the multi-step analysis workflow, routes tasks to specialized agents |
| **IBM Cloud** | Cloud platform — deployment target, infrastructure |

---

## Build Phases

| Phase | Description | Status |
|---|---|---|
| 1 | Foundation — structure, environment, Git | ✅ Complete |
| 2 | Text Processing — file upload, PDF/DOCX extraction | ✅ Complete |
| 3 | Lexical Similarity — TF-IDF, cosine, n-gram | ✅ Complete |
| 4 | Semantic Analysis — embeddings, vector similarity | ✅ Complete |
| 5 | Writing Profile — style metrics, deviation | ✅ Complete |
| 6 | Historical Intelligence — student profiles, anomaly detection | 🔶 MVP baseline (reference-text proxy; full DB implementation deferred) |
| 7 | RAG — document ingestion, retrieval | 🔶 Deferred (architecture documented) |
| 8 | IBM Granite — watsonx.ai connection, prompts | ✅ Complete |
| 9 | Agents — specialized agent definitions | 🔶 Deferred (pipeline implemented as single endpoint) |
| 10 | watsonx Orchestrate — agent coordination | 🔶 Deferred |
| 11 | Backend — FastAPI APIs | ✅ Complete (no DB/auth in MVP) |
| 12 | Frontend — instructor dashboard | ✅ Complete (HTML/CSS/JS) |
| 13 | Integration — end-to-end workflow | ✅ Complete — tested end-to-end |
| 14 | Testing — unit tests | ✅ 16 unit tests passing |
| 15 | Deployment — Docker | ✅ Dockerfile + docker-compose ready |
| 16 | Documentation — README, diagrams, notes | ✅ Complete |

---

## Risk Score Design

These are **project-defined values** — not scientifically universal thresholds.

### Component Weights (default, configurable)

| Component | Weight |
|---|---|
| Semantic similarity | 25% |
| Lexical similarity | 20% |
| Writing-style deviation | 20% |
| Historical anomaly | 15% |
| Citation anomaly | 10% |
| AI-authorship indicator | 10% |
| **Total** | **100%** |

### Risk Bands

| Score | Band |
|---|---|
| 0–30 | LOW |
| 31–60 | MODERATE |
| 61–80 | HIGH |
| 81–100 | VERY HIGH |

---

## Analysis Dimensions

1. **Lexical Similarity** — TF-IDF, cosine similarity, n-gram matching, matching passage extraction
2. **Semantic Similarity** — Sentence embeddings, vector cosine similarity, paraphrase detection
3. **Writing Style** — Sentence length, vocabulary diversity, readability, punctuation patterns, complexity
4. **Historical Analysis** — Compare against student's previous submissions, detect anomalies in writing profile
5. **Citation Analysis** — Detect unusual or missing citation patterns
6. **AI-Authorship Indicator** — Probabilistic indicator only; NOT proof of AI generation
7. **Contextual Analysis** — Assignment requirements, instructor feedback, course context (via RAG)

---

## Agent Definitions

| Agent | Input | Output |
|---|---|---|
| Assignment Analyzer | Raw file | Clean extracted text |
| Similarity Detection | Current text + corpus | Lexical similarity scores, matching passages |
| Semantic Analysis | Current text + corpus | Semantic similarity scores |
| Writing Style | Current text + historical texts | Style metrics, deviation scores |
| Historical Analysis | Current submission + student history | Historical profile, anomaly flags |
| Integrity Assessment | All analysis results | Structured evidence package for Granite |
| Supervisor/Orchestrator | Submission + metadata | Coordinates all agents, returns final report |

---

## Important Decisions & Notes

- **Frontend language:** Next.js with TypeScript (not plain HTML for production)
- **Database:** PostgreSQL via SQLAlchemy ORM
- **Vector DB:** ChromaDB for RAG (FAISS as fallback for prototype)
- **Embeddings:** `sentence-transformers/all-MiniLM-L6-v2` (runs locally, no API key needed)
- **Authentication:** JWT-based, bcrypt password hashing
- **File storage:** Local filesystem for prototype; IBM Cloud Object Storage for production
- **Granite model ID:** Must be verified from IBM watsonx Prompt Lab — do not hardcode unverified IDs

---

## IBM Bob Usage Log

Update this section after each IBM Bob session to document what was built.

| Date | Phase | What Bob Helped Build |
|---|---|---|
| Session 1 | Phase 1 | Project structure, .gitignore, .env.example, README, PROJECT_NOTES, main.py scaffold |
| Session 1 | Phase 2 | File upload endpoint, extractor service rewrite, Pydantic schemas, 16 unit tests, conftest.py |
| Session 2 | MVP | risk_scoring.py (correct weights), granite_reasoning.py (correct prompt + fallback), POST /api/v1/analysis/analyze pipeline, instructor dashboard UI |
| Session 3 | Phase 5 | writing_style.py — 8 metrics, Flesch readability, style deviation score; wired into pipeline; Docker multi-stage config |

---

## Questions / Uncertainties to Resolve

- [ ] Confirm exact Granite model ID from IBM watsonx Prompt Lab
- [ ] Confirm watsonx Orchestrate agent API format (verify from current IBM documentation)
- [ ] Decide: deploy database to IBM Cloud or use managed PostgreSQL service
- [ ] Confirm IBM Cloud region for deployment (us-south vs eu-gb)

---

## Git Branch Strategy

```
main          ← production-ready only
└── develop   ← integration branch for all features

feature/text-processing
feature/similarity
feature/semantic-analysis
feature/writing-style
feature/historical-analysis
feature/rag
feature/granite
feature/agents
feature/orchestrate
feature/backend-api
feature/frontend
feature/auth
feature/docker
```

**Rule:** Never commit directly to `main`. All work goes through feature branches → develop → main.
