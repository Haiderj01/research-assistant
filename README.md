# AI Research Assistant

A RAG-based research paper Q&A system. Upload PDFs, ask questions, get summaries, and compare papers.

## Features

- Upload and auto-process PDFs (extraction -> chunking -> embedding -> FAISS indexing)
- Ask questions with answers cited to source pages
- Paper summaries and side-by-side comparison
- Gap analysis across papers
- JWT authentication
- Google Sign-In (OAuth 2.0)

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python, Flask, PyMongo |
| Frontend | React, Vite, Tailwind CSS |
| Database | MongoDB / Atlas |
| Vector Store | FAISS |
| Embeddings | Sentence Transformers (all-MiniLM-L6-v2) |
| LLM | Groq (openai/gpt-oss-120b) |
| PDF | PyMuPDF |

## Quick Start

### Prerequisites

- Python 3.12+
- Node.js 22+
- A [Groq API key](https://console.groq.com/keys)

### 1. Clone & configure

```bash
git clone https://github.com/Haiderj01/research-assistant.git
cd research-assistant
cp .env.example .env      # add your Groq API key and MongoDB connection string
```

### 2. Backend

```bash
python3 -m venv backend/venv
source backend/venv/bin/activate
pip install -r backend/requirements.txt
OMP_NUM_THREADS=1 TOKENIZERS_PARALLELISM=false python -m backend.app
```

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000.

> **Note:** Without MongoDB running, the app falls back to an in-memory mock (data resets on restart). The `OMP_NUM_THREADS=1` flag avoids a known macOS FAISS segfault.

## Configuration

Set these in `.env` at the project root:

| Variable | Description |
|---|---|
| `GROQ_API_KEY` | **Required.** Groq API key (free tier) |
| `DATABASE_URL` | **Required.** MongoDB / Atlas connection string |
| `JWT_SECRET_KEY` | **Required.** Secret used to sign auth tokens |
| `GOOGLE_CLIENT_ID` | Google OAuth client ID (only needed for Google Sign-In) |
| `GOOGLE_CLIENT_SECRET` | Google OAuth client secret (only needed for Google Sign-In) |
| `GROQ_MODEL_NAME` | Groq model (defaults to `openai/gpt-oss-120b`) |
| `APPLICATION_PORT` | Backend port (defaults to `5003`) |

## API

All endpoints are prefixed with `/api/v1/`.

| Method | Path | Description |
|---|---|---|
| `POST` | `/auth/register` | Create an account |
| `POST` | `/auth/login` | Log in and receive a JWT |
| `POST` | `/upload` | Upload and process PDF(s) |
| `POST` | `/ask` | Ask a question (RAG) |
| `POST` | `/summarize` | Generate a paper summary |
| `POST` | `/compare` | Compare multiple papers |
| `POST` | `/gap-analysis` | Gap analysis across papers |
| `GET` | `/papers` | List uploaded papers |
| `GET` | `/paper/:id` | Paper details |
| `DELETE` | `/paper/:id` | Delete a paper |
| `GET` | `/history` | Conversation / search history |
| `GET` | `/health` | Health check |

## Testing

```bash
source backend/venv/bin/activate
OMP_NUM_THREADS=1 TOKENIZERS_PARALLELISM=false python -m pytest backend/tests -q
```