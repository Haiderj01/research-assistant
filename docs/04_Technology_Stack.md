# 04_Technology_Stack.md

## 1. Purpose of this Document

Selecting the correct technology stack is one of the most consequential decisions in the lifecycle of a software project, because these choices are difficult and costly to reverse once development is underway. The technologies chosen determine not only how fast the system can be built, but also how well it performs, how easily it can be maintained, how confidently it can scale, and how effectively future contributors can extend it.

This document serves as the **official technology selection guide** for the AI Research Assistant. It records not just *what* technologies were chosen, but *why* — the reasoning, trade-offs, and alternatives considered for every layer of the system. This is important for three reasons:

- **Justification**: Every technology decision should be traceable to a clear rationale, not an arbitrary or purely familiarity-driven choice, so the decision can be defended in technical review or during a capstone evaluation.
- **Onboarding**: New contributors (or evaluators) can quickly understand why the system is built the way it is without needing to reverse-engineer intent from code.
- **Future Evolution**: When a technology needs to be replaced or upgraded (e.g., swapping the LLM provider), this document provides the context needed to make that decision consistently with the original architectural intent.

This document builds directly on `02_System_Architecture.md`, which defines *where* each technology fits into the system, and `03_Project_Structure.md`, which defines *where* each technology's code lives in the repository.

---

## 2. Technology Selection Principles

The following principles guided every technology decision in this document:

| Principle | Explanation |
|---|---|
| **Simplicity** | Prefer technologies that solve the problem directly, without introducing unnecessary abstraction or operational complexity, given the project's scope and timeline. |
| **Maintainability** | Prefer technologies with clear documentation, predictable behavior, and a coding style that supports long-term readability. |
| **Scalability** | Prefer technologies that can grow with the system's needs (more papers, more users) without requiring an early architectural rewrite. |
| **Performance** | Prefer technologies that meet the system's response-time expectations for PDF processing, retrieval, and generation. |
| **Community Support** | Prefer technologies with active communities, frequent updates, and abundant documentation/troubleshooting resources. |
| **Learning Curve** | Prefer technologies that are approachable within the timeframe of a capstone project, avoiding tools that require disproportionate ramp-up time relative to their benefit. |
| **Open Source Preference** | Prefer open-source technologies where feasible, to avoid licensing costs and vendor lock-in, reserving proprietary/hosted services for capabilities (like frontier LLMs) that are not practically self-hostable. |
| **Production Readiness** | Prefer technologies that are stable, widely adopted in production systems, and not experimental or pre-release. |

Each technology selected in this document was evaluated against these principles, and the specific reasoning is provided in the relevant sections below.

---

## 3. Complete Technology Stack Overview

| Layer | Technology | Purpose | Reason for Selection |
|---|---|---|---|
| Frontend | React | Build the interactive user interface. | Component-based architecture suited to dynamic, stateful UIs; strong ecosystem and community support. |
| Backend | Flask (Python) | Serve the REST API and orchestrate the AI pipeline. | Lightweight, simple, and highly compatible with the Python-based AI/ML ecosystem. |
| Styling | Tailwind CSS | Style the frontend UI. | Utility-first approach enables rapid, consistent styling without writing extensive custom CSS. |
| PDF Processing | PyMuPDF (fitz) | Extract text content from uploaded PDF files. | Fast, reliable, and widely used for accurate text extraction from standard PDFs. |
| NLP | Sentence Transformers / Hugging Face ecosystem | Provide pretrained models for semantic text understanding. | Mature, open-source, well-validated for semantic similarity tasks. |
| Embedding Model | Sentence Transformers (e.g., all-MiniLM-class models) | Convert text into vector representations. | High-quality semantic embeddings at low computational cost, runs locally without per-call cost. |
| Vector Database | FAISS | Store and search vector embeddings efficiently. | High-performance, open-source, no external service dependency, well-suited to project scale. |
| LLM | Groq API | Generate natural-language answers, summaries, and comparisons. | Strong reasoning and generation quality, accessible hosted API with a usable free/low-cost tier. |
| Metadata Database | MongoDB | Store structured paper metadata and query history. | Flexible document schema suited to evolving, semi-structured metadata. |
| REST API | Flask (native routing) | Define the communication contract between frontend and backend. | Simple, stateless, well-understood protocol sufficient for the system's request/response patterns. |
| Charts | Recharts (or equivalent React charting library) | Visualize trends and dashboard statistics. | Native React integration, simple declarative API for common chart types. |
| Authentication (future) | JWT-based auth (planned) | Secure user sessions and data access. | Industry-standard, stateless authentication mechanism suitable for REST APIs. |
| Deployment | Container-based deployment (e.g., Docker, future) | Package and run the application consistently. | Ensures reproducibility across environments and simplifies future cloud migration. |
| Version Control | Git + GitHub | Track code changes and enable collaboration. | Industry-standard version control with strong tooling and collaboration features. |
| Documentation | Markdown (this document series) | Record design, architecture, and usage documentation. | Lightweight, version-controllable, and universally readable format. |
| Testing | Pytest (backend), Jest/React Testing Library (frontend) | Validate correctness of backend services and frontend components. | Widely adopted, well-documented testing frameworks for their respective ecosystems. |

---

## 4. Backend Technologies

**Python**
Python is the foundation of the backend due to its dominant position in the AI/ML ecosystem. Nearly every library required for this project — PDF processing, embeddings, vector search — has first-class Python support, making Python the natural choice for a system whose core value proposition is AI-driven analysis.

**Flask**
Flask is a lightweight WSGI web framework used to implement the backend's REST API and orchestration layer.

**Why Flask instead of FastAPI**
FastAPI offers native asynchronous request handling and automatic OpenAPI documentation generation, which are attractive features for high-concurrency, API-first systems. However, Flask was selected because:
- It has a simpler, more minimal mental model, reducing the learning curve for a project with a defined academic timeline.
- Its synchronous request model is sufficient for the current scale of the system, since the primary bottlenecks (PDF processing, LLM generation) are I/O- or compute-bound regardless of the web framework's concurrency model.
- It has a longer track record and broader base of tutorials/examples for integrating with AI/ML libraries.

**Advantages**
- Minimal boilerplate; easy to reason about request/response flow.
- Extensive extension ecosystem (e.g., Flask-CORS, Flask-PyMongo).
- Straightforward integration with synchronous AI/ML library calls.

**Limitations**
- Native support for asynchronous operations is weaker than FastAPI, which could become a bottleneck under high concurrent load (e.g., many simultaneous LLM calls).
- Lacks automatic request/response schema validation and API documentation generation out of the box (would require an added extension).

**Future Scalability**
If concurrency needs grow significantly, the backend can be migrated to FastAPI or augmented with asynchronous task queues (see Section 14) without changing the overall architecture, since the API layer is cleanly separated from the service layer per `03_Project_Structure.md`.

---

## 5. Frontend Technologies

| Technology | Purpose | Why Selected |
|---|---|---|
| **React** | Build the component-based user interface. | Enables a modular, reusable UI structure well suited to the multiple interactive views (upload, chat, dashboard, history) required by this system; strong community support and abundant learning resources. |
| **Tailwind CSS** | Style UI components. | Utility-first CSS enables fast, consistent styling directly within component markup, reducing the overhead of maintaining separate large stylesheet files, while still allowing full design customization. |
| **Axios** | Handle HTTP requests to the backend API. | Provides a cleaner, more consistent API than the native `fetch` function, including built-in support for request/response interceptors, timeouts, and automatic JSON parsing — useful for centralizing API error handling in the `api/` layer. |
| **React Router** | Manage client-side page navigation. | Enables a single-page application experience across the Upload, Chat, Dashboard, and History views without full page reloads, while keeping routing logic declarative and centralized. |

---

## 6. AI & Machine Learning Stack

### Sentence Transformers

**Purpose**: Generate dense vector embeddings that capture the semantic meaning of text chunks and user queries.

**Advantages**: Open-source and free to run locally; strong performance on semantic similarity benchmarks; wide variety of pretrained models suited to different speed/accuracy trade-offs.

**Alternatives**: OpenAI embeddings API, Groq embeddings API, Cohere embeddings.

**Trade-offs**: Hosted embedding APIs may offer marginally higher embedding quality or larger context windows, but introduce per-call cost and external network dependency. Running Sentence Transformers locally keeps the embedding step free, fast for moderate volumes, and fully within the project's control.

### Hugging Face

**Purpose**: Serves as the ecosystem/distribution platform from which pretrained Sentence Transformer models (and potentially future NLP models) are sourced.

**Advantages**: Centralized, well-documented model repository; consistent model-loading interface across many model types; strong community validation of model quality.

**Alternatives**: Directly hosting custom-trained models; using proprietary embedding APIs exclusively.

**Trade-offs**: Reliance on Hugging Face's model hub introduces a one-time download dependency at setup time, but no ongoing runtime dependency once models are cached locally.

### Embeddings (as a technique)

**Purpose**: Convert unstructured text into a numerical form that enables meaning-based comparison, which is the foundational technique that makes semantic search and retrieval possible.

**Advantages**: Enables retrieval based on conceptual similarity rather than exact keyword overlap, directly addressing the core problem identified in `01_Project_Overview.md`.

**Alternatives**: Traditional keyword-based/lexical search (e.g., TF-IDF, BM25).

**Trade-offs**: Embedding-based search requires more compute and storage than simple keyword indexing, but delivers substantially better relevance for natural-language questions — a trade-off well justified given the system's core purpose.

### Groq API

**Purpose**: Serve as the Large Language Model responsible for generating natural-language answers, summaries, and comparisons grounded in retrieved context.

**Advantages**: Strong reasoning and language generation quality; accessible via a hosted API without requiring local GPU infrastructure; usable free/low-cost tier suitable for development and demonstration.

**Alternatives**: OpenAI GPT models, Anthropic Claude, open-source self-hosted LLMs (e.g., Llama-family models).

**Trade-offs**: Introduces a third-party network dependency and potential rate limits or cost at scale; self-hosted alternatives would eliminate this dependency but require substantially more compute infrastructure than is available within the project's constraints.

### FAISS

**Purpose**: Store chunk embeddings and perform fast approximate/exact nearest-neighbor similarity search to retrieve relevant context for a given query.

**Advantages**: Free, open-source, high-performance, and runs entirely locally without requiring a managed cloud service or ongoing cost.

**Alternatives**: ChromaDB, Pinecone, Weaviate, Milvus.

**Trade-offs**: FAISS lacks built-in persistence management, replication, and multi-tenancy features offered by managed vector databases; acceptable for the project's current scale, with migration to a managed/distributed vector store identified as a future upgrade path (Section 14).

### RAG Architecture (Retrieval-Augmented Generation)

**Purpose**: Combine retrieval (finding relevant source material) with generation (producing a natural-language response) so that the LLM's output is grounded in the actual content of uploaded papers rather than relying solely on the model's pretrained knowledge.

**Advantages**: Reduces hallucination risk by grounding responses in retrieved, verifiable source content; allows the system to answer questions about documents the underlying LLM has never seen during its own training.

**Alternatives**: Fine-tuning an LLM directly on the paper corpus; relying on the LLM's raw context window without a retrieval step (feasible only for very small paper collections).

**Trade-offs**: RAG adds architectural complexity (requiring an embedding pipeline and vector store) compared to naive prompting, but this complexity is directly justified by the accuracy and scalability benefits it provides — RAG is the architectural foundation of the entire system, as established in `02_System_Architecture.md`.

---

## 7. PDF Processing Technologies

**PyMuPDF (fitz)**

**Why Selected**: PyMuPDF provides fast, accurate text extraction from standard, text-based PDF files, along with useful metadata (page numbers, basic structural information) that supports the chunk-tagging requirements described in `02_System_Architecture.md`. It is significantly faster than several alternative Python PDF libraries for large documents, which matters when processing multiple research papers in a single upload batch.

**Alternatives**: PyPDF2, pdfplumber, pdfminer.six.

**Expected Usage**: PyMuPDF will be used within the `pdf_service` (per `03_Project_Structure.md`) to open each uploaded PDF, extract raw text page by page, and pass the result to the Text Preprocessing Module for cleaning and chunking. It will also be used to detect PDFs that yield insufficient extractable text (e.g., scanned documents), allowing the system to flag them as unsupported in Version 1, consistent with the OCR limitation defined in `01_Project_Overview.md`.

---

## 8. Database Technologies

**MongoDB**

MongoDB is used exclusively for structured **metadata** storage: paper titles, upload timestamps, extracted keywords/datasets/algorithms, and user query/answer history. Its document-oriented model is well suited to this data because the metadata associated with different papers can vary in shape (e.g., not every paper yields the same extracted fields), and MongoDB's flexible schema accommodates this variability without requiring rigid, predefined table structures.

**Why Metadata Belongs in MongoDB While Embeddings Belong in FAISS**

These two databases serve fundamentally different purposes and are not interchangeable:

| Aspect | MongoDB | FAISS |
|---|---|---|
| **Data type stored** | Structured/semi-structured documents (text fields, dates, lists). | High-dimensional numerical vectors. |
| **Query type** | Exact-match and structured queries (e.g., "find all papers uploaded by user X"). | Similarity search (e.g., "find the 5 chunks most semantically similar to this vector"). |
| **Underlying mechanism** | B-tree/document indexing suited to structured lookups. | Specialized vector indexing algorithms optimized for high-dimensional nearest-neighbor search. |

**Why FAISS Is Not a Replacement for MongoDB**: FAISS has no concept of structured fields, filtering by arbitrary metadata attributes, or general-purpose querying — it is purpose-built solely for vector similarity search. It cannot efficiently answer questions like "list all papers uploaded this week" or store variable-shape metadata records. Using FAISS as a general-purpose database would require significant workarounds and would perform poorly for non-vector queries; conversely, using MongoDB for vector similarity search would be prohibitively slow at scale, since it is not optimized for high-dimensional nearest-neighbor operations. The two databases are therefore complementary, each handling the class of data and query it is architecturally suited for, consistent with the two-database design established in `02_System_Architecture.md`.

---

## 9. Development Tools

| Tool | Why Used |
|---|---|
| **Git** | Provides distributed version control, enabling tracked history of all code changes and safe experimentation via branching, as defined in the Git Workflow in `03_Project_Structure.md`. |
| **GitHub** | Hosts the remote repository and provides pull request, code review, and issue-tracking functionality, supporting collaborative development and project transparency. |
| **VS Code / Cursor / OpenCode** | Serve as the primary code editor(s), offering integrated debugging, extensions for Python/React development, and AI-assisted coding support to improve development speed and code quality. |
| **Postman** | Used to manually test and validate backend REST API endpoints during development, independent of the frontend, ensuring the API behaves correctly in isolation. |
| **Chrome DevTools** | Used to inspect, debug, and profile the React frontend directly in the browser, including network requests, console errors, and rendering performance. |

---

## 10. Deployment Stack

- **Backend Deployment**: The Flask backend is deployed as a standalone service exposing its REST API, configured to run on the port specified by the `APPLICATION_PORT` environment variable, with the process manager appropriate to the target environment (e.g., a production-grade WSGI server rather than Flask's built-in development server).
- **Frontend Deployment**: The React application is compiled into a static production build and served independently of the backend, either from a static hosting service or alongside the backend behind a reverse proxy.
- **Environment Variables**: All environment-specific configuration (API keys, database URLs, file paths) is supplied via environment variables as defined in `03_Project_Structure.md`, ensuring no secrets are hardcoded into deployed artifacts.
- **Production Logging**: In production, logging verbosity is reduced (`INFO` and above), and log output should be directed to persistent storage or a centralized logging destination rather than relying solely on local ephemeral disk.
- **Future Docker Support**: The application is structured (separate backend/frontend, centralized configuration) to be straightforwardly containerized in the future, with each service packaged into its own Docker image for consistent, reproducible deployment.
- **Cloud Deployment**: The modular, stateless design of the backend API allows it to be deployed to common cloud platforms (e.g., container-hosting services) with minimal adaptation, once containerization is introduced.

---

## 11. Alternative Technologies Considered

| Comparison | Chosen | Reason Chosen Was Preferred |
|---|---|---|
| **Flask vs FastAPI** | Flask | Simpler mental model and lower learning curve for the project's scope and timeline; sufficient performance for the system's I/O/compute-bound workloads; FastAPI remains a viable future migration if async concurrency becomes a bottleneck. |
| **MongoDB vs PostgreSQL** | MongoDB | Flexible schema better accommodates the variable-shape metadata (extracted keywords, datasets, algorithms) generated by the AI pipeline, and allows faster iteration during development without upfront schema migrations. |
| **FAISS vs ChromaDB** | FAISS | Higher raw performance and a longer production track record for similarity search; ChromaDB offers a more batteries-included developer experience but with less mature performance characteristics at the time of selection. |
| **Groq vs OpenAI** | Groq | Strong generation quality with a usable free/low-cost tier suitable for a capstone project's budget constraints; the RAG architecture keeps the LLM provider abstracted, so this choice can be revisited without structural change. |
| **Tailwind vs Bootstrap** | Tailwind CSS | Utility-first styling offers finer-grained design control and avoids the "default look" commonly associated with Bootstrap-based UIs, better supporting a distinctive, polished interface for a capstone presentation. |

---

## 12. Compatibility Matrix

All selected technologies interoperate through well-defined, standard interfaces — HTTP/REST between frontend and backend, and Python function calls between backend modules — ensuring no component is tightly bound to the internal implementation of another.

```
┌───────────────┐        REST (JSON over HTTPS)        ┌───────────────┐
│  React (Axios)  │ ────────────────────────────────────▶ │  Flask Backend  │
│  + Tailwind      │ ◀──────────────────────────────────── │                 │
└───────────────┘                                        └───────┬───────┘
                                                                   │
                        ┌──────────────────────────────────────────┼──────────────────────────────────────────┐
                        ▼                                          ▼                                          ▼
              ┌───────────────────┐                     ┌───────────────────┐                    ┌───────────────────┐
              │ PyMuPDF             │                     │ Sentence Transformers │                │ MongoDB              │
              │ (Text Extraction)    │                     │ (Embeddings)           │                │ (Metadata Storage)   │
              └───────────────────┘                     └──────────┬────────────┘                └───────────────────┘
                                                                    │
                                                                    ▼
                                                          ┌───────────────────┐
                                                          │ FAISS                │
                                                          │ (Vector Search)      │
                                                          └──────────┬────────────┘
                                                                    │
                                                                    ▼
                                                          ┌───────────────────┐
                                                          │ Groq API           │
                                                          │ (Answer Generation)  │
                                                          └───────────────────┘
```

Each arrow represents a standard, documented interface (REST calls, Python library function calls, or hosted API calls), meaning any single technology in this diagram can, in principle, be replaced without requiring changes to unrelated components — a direct benefit of the loosely coupled architecture defined in `02_System_Architecture.md`.

---

## 13. Risks and Limitations

| Risk/Limitation | Description | Consideration |
|---|---|---|
| **Free API limits** | The Groq API's free/low-cost tier imposes rate and quota limits that could restrict testing scale or demo reliability. | Batch requests where possible; monitor usage; design the RAG Engine to handle rate-limit errors gracefully. |
| **Memory usage** | Loading the Sentence Transformer embedding model into memory, alongside a growing FAISS index, consumes non-trivial RAM, particularly on constrained development or free-tier hosting environments. | Select a lightweight embedding model appropriate to available resources; monitor memory usage during testing. |
| **Embedding model size** | Larger, higher-quality embedding models improve semantic accuracy but increase load time and memory footprint. | Balance model size against available compute; smaller models are acceptable for the project's expected scale. |
| **Large PDF collections** | Processing a large number of PDFs synchronously could create slow upload response times and degrade user experience. | Consider background/asynchronous processing (see Section 14) if collection sizes grow significantly. |
| **Deployment limitations** | Free-tier or limited hosting environments may not provide sufficient compute/storage for large FAISS indexes or persistent uploaded file storage. | Plan for cloud storage and containerized deployment as the system scales beyond capstone-level demonstration. |

---

## 14. Future Technology Upgrades

| Technology | Future Role |
|---|---|
| **Docker** | Containerize the backend and frontend independently, ensuring consistent, reproducible deployment across environments. |
| **Kubernetes** | Orchestrate containerized services at scale, enabling automated scaling, self-healing, and rolling deployments once user/traffic volume justifies the added operational complexity. |
| **Redis** | Provide fast in-memory caching for frequently repeated queries or session data, reducing redundant embedding/LLM calls. |
| **Celery** | Enable asynchronous, background task processing for PDF ingestion and embedding generation, preventing long-running operations from blocking API requests. |
| **Cloud Storage** | Replace local file system storage for uploaded PDFs with durable, scalable cloud object storage. |
| **Authentication** | Introduce token-based (e.g., JWT) authentication to support secure, per-user data isolation, as outlined in `02_System_Architecture.md`. |
| **Streaming Responses** | Adopt Server-Sent Events or WebSockets to stream LLM-generated answers token-by-token, improving perceived responsiveness. |
| **Multiple LLMs** | Abstract the Groq integration behind a provider-agnostic interface, enabling support for additional LLM providers (e.g., OpenAI, Claude) as configurable alternatives. |

Each of these upgrades extends the existing architecture rather than replacing it, consistent with the extensibility goals defined throughout this document series.

---

## 15. Technology Stack Summary

The technology stack selected for the AI Research Assistant balances **capability, simplicity, and cost-effectiveness**, prioritizing open-source, well-documented, production-proven tools wherever they meet the project's requirements, and reserving hosted/proprietary services (namely, the Groq LLM) for the one capability — high-quality natural language generation — that is not practically achievable within the project's compute constraints through self-hosting alone.

React and Flask provide a familiar, well-supported foundation for the application layer; Sentence Transformers and FAISS provide a free, self-contained semantic search pipeline; MongoDB provides flexible metadata storage that complements, rather than duplicates, the vector database's role; and Groq provides the natural-language reasoning that ties the entire Retrieval-Augmented Generation pipeline together. Each technology was selected not in isolation, but as part of a coherent, loosely coupled system in which any individual component can be upgraded or replaced as the project evolves beyond its capstone scope — as outlined in Section 14 — without requiring a redesign of the surrounding architecture.

This stack is well-suited to the AI Research Assistant because it directly supports the system's core requirement — transforming static research papers into an interactive, semantically searchable knowledge base — while remaining achievable within the realistic time, budget, and compute constraints of a final-year capstone project.
