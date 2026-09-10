# EduIntegrity AI
### AI-Driven Plagiarism Intelligence for Assignments

> **Disclaimer:** This system is designed to identify suspicious patterns and provide evidence-based risk indicators. It does **not** automatically accuse any student of plagiarism or academic misconduct. The instructor always makes the final decision.

---

## What Is This?

EduIntegrity AI is a web-based academic integrity analysis platform that helps instructors identify potential integrity concerns in student assignments. The system performs multi-dimensional analysis — lexical similarity, semantic similarity, writing-style profiling, historical pattern comparison, citation analysis, and AI-authorship indicators — and presents a transparent, explainable risk score to support instructor review.

IBM Granite (via IBM watsonx.ai) provides the contextual AI reasoning layer that interprets structured evidence and generates natural-language explanations. IBM watsonx Orchestrate coordinates the multi-agent workflow.

---

## Technology Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js (React, TypeScript) |
| Backend | Python, FastAPI |
| Database | PostgreSQL |
| AI Platform | IBM watsonx.ai |
| AI Model | IBM Granite |
| Agent Orchestration | IBM watsonx Orchestrate |
| Semantic Embeddings | Sentence Transformers (`all-MiniLM-L6-v2`) |
| Vector Database | ChromaDB (FAISS for prototype) |
| Containerization | Docker, Docker Compose |
| Cloud | IBM Cloud |
| Version Control | GitHub |

---

## Project Structure

```
EduIntegrity-AI/
│
├── backend/
│   ├── app/
│   │   ├── main.py              ← FastAPI application entry point
│   │   ├── api/                 ← HTTP route handlers
│   │   ├── services/            ← Core analysis business logic
│   │   ├── agents/              ← AI agent definitions
│   │   ├── models/              ← SQLAlchemy database models
│   │   ├── schemas/             ← Pydantic request/response schemas
│   │   └── utils/               ← Shared utility functions
│   └── tests/                   ← Backend test suite
│
├── frontend/
│   ├── app/                     ← Next.js app router pages
│   ├── components/              ← Reusable UI components
│   ├── services/                ← API client functions
│   └── public/                  ← Static assets
│
├── rag/                         ← RAG pipeline (document ingestion, retrieval)
├── data/                        ← Sample assignments, test fixtures
├── docs/                        ← Architecture diagrams, project notes
├── docker/                      ← Dockerfiles and compose configuration
│
├── .env.example                 ← Environment variable template (safe to commit)
├── .gitignore
├── README.md
└── PROJECT_NOTES.md
```

---

## Risk Score

The platform calculates a 0–100 risk score using configurable weights:

| Component | Default Weight |
|---|---|
| Semantic similarity | 25% |
| Lexical similarity | 20% |
| Writing-style deviation | 20% |
| Historical anomaly | 15% |
| Citation anomaly | 10% |
| AI-authorship indicator | 10% |

**Risk Bands:**
- `0–30` → LOW
- `31–60` → MODERATE
- `61–80` → HIGH
- `81–100` → VERY HIGH

> These weights are project-defined values configured for this prototype. They are not scientifically universal thresholds. Institutions should review and adjust these weights based on their specific context and requirements.

---

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+
- PostgreSQL (or Docker)
- IBM Cloud account with watsonx.ai access

### 1. Clone the repository

```bash
git clone https://github.com/your-username/EduIntegrity-AI.git
cd EduIntegrity-AI
```

### 2. Configure environment variables

```bash
cp .env.example .env
# Edit .env with your real IBM credentials and database details
```

### 3. Set up the Python backend

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
```

### 4. Start the backend

```bash
cd backend
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`  
Interactive API docs: `http://localhost:8000/docs`

### 5. Set up the frontend (Phase 12)

```bash
cd frontend
npm install
npm run dev
```

The UI will be available at `http://localhost:3000`

---

## IBM Bob Role

IBM Bob is used as the primary development and coding assistant throughout this project:
- Generating and modifying backend services
- Creating project structure and configuration
- Writing and improving tests
- Debugging and code review
- Docker and deployment configuration
- IBM service integration guidance

---

## Important Notes

- API keys and credentials must **never** be committed to Git
- The `.env` file is excluded by `.gitignore`
- Only `.env.example` (with placeholder values) is committed
- All AI-generated risk scores and indicators are advisory only
- The instructor always makes the final academic integrity decision

---

## License

This project is developed as an internship demonstration. Refer to your institution's guidelines for usage terms.
