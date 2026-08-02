# AI Research Assistant

Intelligent RAG-based research paper Q&A system. Upload PDFs, ask questions, get summaries, and compare papers using AI.

## Quick Start

### Prerequisites

- Python 3.12+
- Node.js 22+
- A [Gemini API key](https://aistudio.google.com/apikey)

### 1. Clone & configure

```bash
git clone https://github.com/Haiderj01/research-assistant.git
cd research-assistant
cp .env.example .env    # edit with your Gemini API key
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

Open **http://localhost:3000**. The frontend proxies `/api` requests to the backend.

### Notes

- **MongoDB not required** — falls back to an in-memory mock automatically
- **macOS FAISS + PyTorch** — the `OMP_NUM_THREADS=1` flag avoids a known segfault
- **Port 5000** — used by AirPlay Receiver on macOS; set `APPLICATION_PORT=5001` in `.env` if needed

## Configuration

Variables go in `.env` at the project root:

| Variable | Default | Description |
|---|---|---|
| `GEMINI_API_KEY` | — | Google Gemini API key **(required)** |
| `JWT_SECRET_KEY` | — | Secret used to sign JWT auth tokens **(required)** |
| `APPLICATION_PORT` | `5000` | Backend server port |
| `DATABASE_URL` | `mongodb://localhost:27017/research_assistant` | MongoDB connection string (optional — uses in-memory mock if unavailable) |
| `DEBUG_MODE` | `false` | Enables Flask debug mode |
| `LOGGING_LEVEL` | `INFO` | Log verbosity |

## API

All endpoints are prefixed with `/api/v1/`.

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | System health check |
| `POST` | `/auth/register` | Create an account |
| `POST` | `/auth/login` | Log in and receive a JWT |
| `POST` | `/upload` | Upload and auto-process PDF(s) |
| `POST` | `/ask` | Ask a question (RAG pipeline) |
| `GET` | `/papers` | List uploaded papers |
| `GET` | `/paper/:id` | Paper details |
| `DELETE` | `/paper/:id` | Delete paper + chunks + vectors |
| `POST` | `/summarize` | Generate paper summary |
| `POST` | `/compare` | Compare multiple papers |
| `GET` | `/history` | Conversation and search history |
| `PATCH` | `/conversation/:id` | Rename a conversation |

## Project Structure

```
backend/              Flask API + AI pipeline
├── config/           Settings and environment
├── controllers/      Request parsing and response formatting
├── middlewares/      Error handling
├── models/           MongoDB document models
├── routes/           URL → controller mapping
├── services/         Core business logic (PDF, chunking, embeddings, RAG, Gemini)
└── tests/            Unit and integration tests

frontend/             React + Vite + Tailwind
├── src/api/          Backend API client
├── src/components/   Reusable UI components
├── src/context/      Global state (React Context)
├── src/hooks/        Custom React hooks
├── src/layouts/      Page layout wrappers
└── src/pages/        Page views (Upload, Chat, Compare, History, Dashboard)

docs/                 Design documentation
```

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python, Flask |
| Frontend | React 19, Vite, Tailwind CSS |
| Database | MongoDB (or mongomock in-memory) |
| Vector Store | FAISS |
| Embeddings | Sentence Transformers (all-MiniLM-L6-v2) |
| LLM | Google Gemini 3.1 Flash Lite |
| PDF | PyMuPDF |

## Documentation

See `docs/` for detailed design documents covering architecture, database schema, API contracts, and the RAG pipeline.
