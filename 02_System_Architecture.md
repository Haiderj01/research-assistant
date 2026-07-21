# 02_System_Architecture.md

## 1. Purpose of this Document

This document defines the complete **system architecture** for the AI Research Assistant: Intelligent Research Paper Analysis and Question Answering System. While `01_Project_Overview.md` describes *what* the system does, *why* it is needed, and *who* it serves, this document describes *how* the system is structured internally — the components, their responsibilities, their interactions, and the technical decisions that shape the implementation.

This document exists to serve as the primary engineering blueprint for development. It translates the functional and non-functional requirements defined in the Project Overview into a concrete architectural design: component boundaries, data flow, communication patterns, and technology choices. Engineers implementing this system should be able to build each module independently by referring to the component contracts (inputs, outputs, responsibilities) defined here, without needing to guess at how pieces fit together.

This document deliberately avoids implementation code. Its purpose is to establish the *shape* of the system — the architecture — so that implementation can proceed consistently, predictably, and in a way that supports future extension without requiring structural rework.

---

## 2. Architectural Goals

| Goal | Explanation | Why It Matters for This Project |
|---|---|---|
| **Scalability** | The system should handle growth in the number of papers, users, and queries without requiring a redesign. | Research libraries can grow from a handful of papers to hundreds; the architecture must not assume a small, fixed dataset. |
| **Maintainability** | Code and components should be easy to understand, debug, and modify over time. | As a capstone project intended to demonstrate engineering competence, the codebase must remain approachable for review and future extension. |
| **Modularity** | The system is divided into independent, well-defined components with clear boundaries. | AI pipelines (extraction, embedding, retrieval, generation) evolve independently; modularity allows each to be swapped or improved in isolation. |
| **Performance** | The system should respond to user actions (uploads, queries) within acceptable time limits. | Slow question-answering undermines the core value proposition of saving the user time. |
| **Reliability** | The system should behave predictably and recover gracefully from failures. | PDF parsing and third-party AI APIs are inherently failure-prone; the system must not crash or produce silent corruption when they fail. |
| **Security** | User data and uploaded documents must be protected from unauthorized access or misuse. | Uploaded research papers may be unpublished or sensitive; API keys and secrets must not be exposed. |
| **Extensibility** | The architecture should accommodate new features (OCR, multi-language support, new LLM providers) without major rewrites. | The Project Overview explicitly defines a roadmap of future enhancements; the architecture must not block that roadmap. |
| **Simplicity** | The design should be as simple as the problem allows, avoiding unnecessary complexity. | As a capstone-scale system with limited development time, over-engineering increases risk of an incomplete or unstable deliverable. |

---

## 3. High-Level Architecture

```
                                   ┌─────────────┐
                                   │     User     │
                                   └──────┬──────┘
                                          │
                                          ▼
                                 ┌─────────────────┐
                                 │  React Frontend  │
                                 └────────┬────────┘
                                          │  REST API (HTTPS/JSON)
                                          ▼
                                 ┌─────────────────┐
                                 │  Flask Backend   │
                                 │   (API Layer)    │
                                 └────────┬────────┘
                    ┌─────────────────────┼─────────────────────┐
                    ▼                     ▼                     ▼
          ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────────┐
          │ PDF Processing     │  │   RAG Engine      │  │  Metadata Database    │
          │ Module             │  │   (Orchestrator)   │  │  (MongoDB)            │
          └────────┬──────────┘  └────────┬──────────┘  └──────────────────────┘
                    │                      │
                    ▼                      ▼
          ┌──────────────────┐  ┌──────────────────────┐
          │  Text Extraction   │  │  Embedding Generator  │
          └────────┬──────────┘  │ (Sentence Transformers)│
                    │             └────────┬──────────────┘
                    ▼                      │
          ┌──────────────────┐             ▼
          │  Text Chunking     │  ┌──────────────────────┐
          └────────┬──────────┘  │  FAISS Vector Store    │
                    │             └────────┬──────────────┘
                    └─────────────────────►│
                                            ▼
                                  ┌──────────────────────┐
                                  │  Context Retriever     │
                                  └────────┬──────────────┘
                                           ▼
                                  ┌──────────────────────┐
                                  │  Gemini API (LLM)      │
                                  └────────┬──────────────┘
                                           ▼
                                  ┌──────────────────────┐
                                  │  Generated Response     │
                                  └────────┬──────────────┘
                                           ▼
                                  ┌──────────────────────┐
                                  │  React Frontend         │
                                  │  (Display to User)      │
                                  └──────────────────────┘
```

**Component Responsibilities**

- **React Frontend**: Provides the user interface for uploading papers, submitting questions, viewing summaries/comparisons, and browsing history. Communicates with the backend exclusively via REST API calls.
- **Flask Backend (API Layer)**: The central orchestration layer. Receives requests from the frontend, routes them to the appropriate internal module, and returns structured JSON responses. Acts as the single entry point into the system's business logic.
- **PDF Processing Module**: Handles ingestion of uploaded PDF files, including validation, text extraction, and cleaning.
- **Text Extraction**: Extracts raw text content from PDF files.
- **Text Chunking**: Splits extracted text into semantically coherent, appropriately sized chunks for embedding.
- **Embedding Generator (Sentence Transformers)**: Converts text chunks (and user questions) into vector embeddings representing semantic meaning.
- **FAISS Vector Store**: Stores chunk embeddings and performs fast similarity search to retrieve the most relevant chunks for a given query.
- **RAG Engine (Orchestrator)**: Coordinates the retrieval-augmented generation process — invoking the embedding generator, querying FAISS, constructing prompts, and calling the LLM.
- **Context Retriever**: A sub-component of the RAG Engine responsible for selecting and ranking the most relevant retrieved chunks before they are passed to the LLM.
- **Gemini API (LLM)**: Generates natural-language answers, summaries, and comparisons based on retrieved context and user prompts.
- **Metadata Database (MongoDB)**: Stores structured metadata such as paper titles, upload timestamps, user query history, and extracted structured data (keywords, datasets, algorithms).
- **Generated Response**: The final structured output (answer, summary, or comparison) returned to the frontend for display.

---

## 4. Architectural Style

The system adopts a **layered, modular architecture** with clear separation of concerns between presentation, orchestration, processing, and storage layers.

- **Layered Architecture**: The system is organized into distinct layers — presentation (frontend), API/orchestration (backend), processing (PDF/embedding/RAG modules), and storage (vector database, metadata database). This layering is chosen because it maps naturally onto the pipeline nature of the problem: data flows in a mostly linear sequence from ingestion to generation, and each layer has a distinct responsibility and technology profile.

- **Modular Architecture**: Within the backend, functionality is divided into independent modules (PDF Processing, Embedding, RAG Engine, Analytics, Logging) rather than a single monolithic codebase. This is chosen because the AI pipeline components (extraction, embedding, retrieval, generation) are conceptually and technically distinct, use different libraries/technologies, and are likely to evolve at different rates (e.g., swapping the LLM provider should not require touching the PDF extraction logic).

- **Separation of Concerns**: Each module is responsible for exactly one part of the system's behavior (e.g., the Embedding Module only converts text to vectors; it does not know how those vectors are stored or retrieved). This makes each module easier to test, reason about, and replace independently.

- **Loose Coupling**: Modules interact through well-defined interfaces (function calls or internal APIs) rather than sharing internal implementation details. This means, for example, that the RAG Engine depends on the *interface* of the Embedding Module (a function that returns a vector given text) rather than its internal implementation (which specific embedding model is used).

- **High Cohesion**: Each module groups together closely related functionality (e.g., all PDF-related operations live within the PDF Processing Module) rather than scattering related logic across unrelated parts of the system.

These principles matter for this project because they directly support the architectural goals defined in Section 2: modularity and loose coupling enable extensibility (e.g., swapping Gemini for another LLM) and maintainability (each module can be debugged and modified independently), while separation of concerns and high cohesion reduce the cognitive load required to understand and safely modify any single part of the system.

---

## 5. Core Components

### 5.1 Frontend

**Purpose**
Provide the user-facing interface for interacting with the AI Research Assistant.

**Responsibilities**
- Render the paper upload interface, chat/question interface, dashboard, and history views.
- Send user actions (uploads, questions, comparison requests) to the backend via REST API calls.
- Display responses, summaries, comparisons, and error messages to the user.

**Inputs**
- User interactions (file uploads, text queries, button clicks).
- JSON responses from the backend API.

**Outputs**
- HTTP requests to the backend (multipart file uploads, JSON query payloads).
- Rendered UI reflecting system state and responses.

**Internal Processing**
- Manages UI state (loading indicators, uploaded paper list, chat history).
- Performs basic client-side validation (e.g., file type checks) before submission.

**Dependencies**
- Flask Backend API (via HTTP).

**Possible Errors**
- Network failures when contacting the backend.
- Invalid file types selected by the user.
- Timeout while awaiting a long-running backend response.

---

### 5.2 Backend (Flask API Layer)

**Purpose**
Serve as the central orchestration and routing layer between the frontend and all internal processing modules.

**Responsibilities**
- Expose REST endpoints for upload, question answering, summarization, comparison, and history retrieval.
- Validate incoming requests.
- Route requests to the appropriate internal module.
- Aggregate and format responses as JSON.

**Inputs**
- HTTP requests from the frontend (file uploads, JSON payloads).

**Outputs**
- JSON responses containing answers, summaries, comparisons, or error details.

**Internal Processing**
- Request validation and routing logic.
- Coordination between PDF Processing, RAG Engine, and Metadata Database.

**Dependencies**
- PDF Processing Module, RAG Engine, Metadata Database, Logging Module.

**Possible Errors**
- Malformed requests.
- Downstream module failures (e.g., PDF processing failure, LLM API failure).
- Timeout errors under heavy load.

---

### 5.3 PDF Processing Module

**Purpose**
Ingest and prepare uploaded PDF files for downstream text processing.

**Responsibilities**
- Validate that uploaded files are valid, well-formed PDFs.
- Extract raw text content from PDFs.
- Perform basic cleaning (removing headers/footers/artifacts where feasible).

**Inputs**
- Raw PDF file(s) uploaded by the user.

**Outputs**
- Cleaned, extracted text content associated with each paper.

**Internal Processing**
- File validation → text extraction → text cleaning.

**Dependencies**
- Text Preprocessing Module (for downstream cleaning/chunking).

**Possible Errors**
- Corrupted or password-protected PDFs.
- Scanned/image-based PDFs with no extractable text (out of scope for Version 1, must be detected and flagged).
- Unsupported file formats.

---

### 5.4 Text Preprocessing Module

**Purpose**
Transform raw extracted text into clean, appropriately segmented chunks suitable for embedding.

**Responsibilities**
- Normalize whitespace, remove non-content artifacts.
- Split text into semantically coherent chunks of an appropriate size.
- Attach metadata to each chunk (paper ID, section, page number where available).

**Inputs**
- Raw extracted text from the PDF Processing Module.

**Outputs**
- A list of cleaned, chunked text segments with associated metadata.

**Internal Processing**
- Cleaning → segmentation/chunking → metadata tagging.

**Dependencies**
- PDF Processing Module (upstream), Embedding Module (downstream).

**Possible Errors**
- Poorly structured text leading to incoherent chunk boundaries.
- Extremely short or empty documents producing insufficient chunks.

---

### 5.5 Embedding Module

**Purpose**
Convert text (chunks or queries) into vector representations capturing semantic meaning.

**Responsibilities**
- Generate embeddings for each text chunk during ingestion.
- Generate embeddings for user queries at question-answering time.

**Inputs**
- Text chunks (during ingestion) or a user question (during query time).

**Outputs**
- Numerical vector embeddings.

**Internal Processing**
- Text passed through a pretrained Sentence Transformer model to produce a fixed-size vector.

**Dependencies**
- Sentence Transformers library/model.
- FAISS Vector Store (as the consumer of generated embeddings).

**Possible Errors**
- Model loading failures.
- Excessively long input text exceeding model token limits.

---

### 5.6 Vector Database (FAISS)

**Purpose**
Store chunk embeddings and enable fast similarity search.

**Responsibilities**
- Persist embeddings alongside references to their source chunk/paper metadata.
- Perform nearest-neighbor similarity search given a query embedding.

**Inputs**
- Chunk embeddings (during ingestion), query embeddings (during search).

**Outputs**
- A ranked list of the most similar chunk references for a given query.

**Internal Processing**
- Index construction and similarity search using FAISS's vector indexing algorithms.

**Dependencies**
- Embedding Module (upstream), RAG Engine (downstream consumer).

**Possible Errors**
- Index corruption or loss (if not persisted correctly).
- Degraded search relevance if embeddings are inconsistent (e.g., generated by different model versions).

---

### 5.7 RAG Engine

**Purpose**
Orchestrate the retrieval-augmented generation process to produce grounded, natural-language answers.

**Responsibilities**
- Accept a user question and relevant paper scope.
- Generate the question embedding via the Embedding Module.
- Query the Vector Database for relevant chunks.
- Construct a well-formed prompt combining retrieved context and the user question.
- Invoke the Gemini Integration to generate the final answer.

**Inputs**
- User question, target paper(s) scope.

**Outputs**
- Final generated answer, along with source references.

**Internal Processing**
- Query embedding → retrieval → context ranking/selection → prompt construction → LLM invocation → response formatting.

**Dependencies**
- Embedding Module, FAISS Vector Store, Gemini Integration.

**Possible Errors**
- No relevant chunks found (e.g., question unrelated to uploaded papers).
- LLM API failure or timeout.
- Context exceeding LLM prompt size limits.

---

### 5.8 Gemini Integration

**Purpose**
Provide natural language generation capability for answers, summaries, and comparisons.

**Responsibilities**
- Accept a constructed prompt (context + instructions).
- Return a generated natural-language response.

**Inputs**
- Prompt text (retrieved context + user question or task instruction).

**Outputs**
- Generated text response.

**Internal Processing**
- API call to the hosted Gemini LLM service.

**Dependencies**
- Third-party Gemini API (external network dependency).

**Possible Errors**
- API rate limiting or quota exhaustion.
- Network failures or timeouts.
- Malformed or unexpected API responses.

---

### 5.9 Metadata Database (MongoDB)

**Purpose**
Persist structured, non-vector data associated with papers and users.

**Responsibilities**
- Store paper metadata (title, upload date, extracted keywords/datasets/algorithms).
- Store user query/answer history.
- Support retrieval for the dashboard and history views.

**Inputs**
- Structured records generated by the Backend, PDF Processing Module, and RAG Engine.

**Outputs**
- Stored and queryable records for dashboard, history, and reporting features.

**Internal Processing**
- Standard document-oriented CRUD operations.

**Dependencies**
- Flask Backend (as the primary consumer).

**Possible Errors**
- Connection failures.
- Write conflicts or data inconsistency under concurrent access.

---

### 5.10 Analytics Module

**Purpose**
Derive aggregate insights such as research trends and usage statistics.

**Responsibilities**
- Analyze extracted keywords, datasets, and algorithms across a paper collection to identify trends.
- Provide summarized statistics for the dashboard.

**Inputs**
- Structured metadata from the Metadata Database.

**Outputs**
- Aggregated trend summaries and dashboard statistics.

**Internal Processing**
- Aggregation and basic statistical analysis over stored metadata.

**Dependencies**
- Metadata Database.

**Possible Errors**
- Insufficient data for meaningful trend analysis (e.g., very few uploaded papers).

---

### 5.11 Logging Module

**Purpose**
Provide consistent, centralized logging across all backend components.

**Responsibilities**
- Record system events, errors, and key processing milestones (upload received, processing complete, query answered).
- Support debugging and post-incident analysis.

**Inputs**
- Log events emitted by all other backend modules.

**Outputs**
- Structured log entries (console, file, or external logging service).

**Internal Processing**
- Log formatting, severity classification, and output routing.

**Dependencies**
- Consumed by all backend modules; itself depends on no other module.

**Possible Errors**
- Log storage failure (should degrade gracefully without affecting core functionality).

---

## 6. End-to-End System Workflow

1. **User uploads papers** — The user selects one or more PDF files through the frontend and submits them.
2. **PDF Processing** — The backend receives the files and passes them to the PDF Processing Module, which validates the file format and integrity.
3. **Text Extraction** — Raw text is extracted from each valid PDF.
4. **Cleaning** — Extracted text is normalized (whitespace, artifacts removed) to prepare it for chunking.
5. **Chunking** — Cleaned text is divided into semantically coherent chunks, each tagged with metadata (paper ID, approximate section/page).
6. **Embedding Generation** — Each chunk is passed through the Embedding Module to produce a vector representation.
7. **Vector Storage** — Chunk embeddings and metadata are stored in the FAISS Vector Store; corresponding paper metadata is stored in MongoDB.
8. **Question Asked** — The user submits a natural-language question via the frontend, optionally scoped to specific papers.
9. **Question Embedding** — The RAG Engine sends the question to the Embedding Module to generate a query vector.
10. **Similarity Search** — The query vector is used to search the FAISS Vector Store for the most semantically relevant chunks.
11. **Context Retrieval** — The top-ranked chunks are retrieved and assembled as context.
12. **Prompt Construction** — The RAG Engine constructs a structured prompt combining the retrieved context, the user's question, and generation instructions.
13. **Gemini Response** — The constructed prompt is sent to the Gemini API, which generates a grounded natural-language answer.
14. **Frontend Display** — The generated answer, along with source references, is returned to the frontend and displayed to the user; the interaction is logged to the Metadata Database for history tracking.

---

## 7. Data Flow

```
   INPUT                PROCESSING                STORAGE              RETRIEVAL              GENERATION            PRESENTATION
┌──────────┐        ┌──────────────────┐      ┌───────────────┐    ┌─────────────────┐    ┌──────────────────┐    ┌───────────────┐
│ PDF Files │───────▶│ Extraction,        │────▶│ FAISS (vectors) │───▶│ Similarity Search│───▶│ Gemini LLM         │───▶│ Frontend UI     │
│ User Query│        │ Chunking, Embedding │     │ MongoDB (meta)  │    │ Context Selection │    │ Answer/Summary Gen  │    │ (Answer/Report) │
└──────────┘        └──────────────────┘      └───────────────┘    └─────────────────┘    └──────────────────┘    └───────────────┘
```

**Explanation**

- **Input**: Data enters the system as either uploaded PDF files or user-submitted natural-language queries.
- **Processing**: Uploaded files pass through extraction, cleaning, chunking, and embedding; queries pass through embedding directly.
- **Storage**: Chunk embeddings are persisted in the FAISS Vector Store; structured metadata (paper info, history) is persisted in MongoDB.
- **Retrieval**: At query time, the system performs similarity search against stored embeddings and selects the most relevant context.
- **Generation**: Retrieved context and the user's request are passed to the Gemini LLM to produce a grounded natural-language output.
- **Presentation**: The final output is returned to the frontend and rendered for the user, with the interaction persisted for history/analytics.

---

## 8. Component Interaction

| Component | Communicates With | Purpose |
|---|---|---|
| React Frontend | Flask Backend | Send user actions (uploads, queries); receive responses for display. |
| Flask Backend | PDF Processing Module | Delegate PDF validation and text extraction. |
| Flask Backend | RAG Engine | Delegate question answering, summarization, and comparison requests. |
| Flask Backend | Metadata Database | Persist and retrieve paper metadata and query history. |
| Flask Backend | Analytics Module | Retrieve aggregated statistics for the dashboard. |
| Flask Backend | Logging Module | Emit request/response and error logs. |
| PDF Processing Module | Text Preprocessing Module | Pass extracted raw text for cleaning and chunking. |
| Text Preprocessing Module | Embedding Module | Pass chunked text for vector generation. |
| Embedding Module | FAISS Vector Store | Store generated chunk embeddings; supply query embeddings for search. |
| RAG Engine | Embedding Module | Request embedding of the user's question. |
| RAG Engine | FAISS Vector Store | Perform similarity search to retrieve relevant chunks. |
| RAG Engine | Gemini Integration | Submit constructed prompts and receive generated responses. |
| RAG Engine | Metadata Database | Retrieve/store paper scope information and log query history. |
| Analytics Module | Metadata Database | Read structured metadata to compute trends and statistics. |
| Logging Module | All Backend Modules | Receive log events from every module for centralized tracking. |

---

## 9. Sequence Diagram

**Scenario: User uploads a paper and asks a question**

```
User        Frontend       Backend        PDFProcessor   EmbeddingGen    FAISS          Gemini         Database
 │              │              │                │              │            │              │               │
 │  Upload PDF  │              │                │              │            │              │               │
 │─────────────▶│              │                │              │            │              │               │
 │              │  POST /upload│                │              │            │              │               │
 │              │─────────────▶│                │              │            │              │               │
 │              │              │  Extract Text   │              │            │              │               │
 │              │              │───────────────▶│              │            │              │               │
 │              │              │◀───────────────│              │            │              │               │
 │              │              │  Chunk + Embed                │            │              │               │
 │              │              │───────────────────────────────▶│            │              │               │
 │              │              │◀───────────────────────────────│            │              │               │
 │              │              │  Store Vectors                              │              │               │
 │              │              │─────────────────────────────────────────────▶│              │               │
 │              │              │  Store Metadata                                             │               │
 │              │              │──────────────────────────────────────────────────────────────────────────▶│
 │              │  Upload OK   │                                                                              │
 │              │◀─────────────│                                                                              │
 │  Upload OK   │              │                                                                              │
 │◀─────────────│              │                                                                              │
 │              │              │                                                                              │
 │  Ask Question│              │                                                                              │
 │─────────────▶│              │                                                                              │
 │              │ POST /query  │                                                                              │
 │              │─────────────▶│                                                                              │
 │              │              │  Embed Question               │            │              │               │
 │              │              │───────────────────────────────▶│            │              │               │
 │              │              │◀───────────────────────────────│            │              │               │
 │              │              │  Similarity Search                          │              │               │
 │              │              │─────────────────────────────────────────────▶│              │               │
 │              │              │◀─────────────────────────────────────────────│              │               │
 │              │              │  Construct Prompt + Generate Answer                         │               │
 │              │              │──────────────────────────────────────────────────────────────▶│               │
 │              │              │◀──────────────────────────────────────────────────────────────│               │
 │              │              │  Log Query + Answer                                                          │
 │              │              │──────────────────────────────────────────────────────────────────────────▶│
 │              │  Answer      │                                                                              │
 │              │◀─────────────│                                                                              │
 │  Display     │              │                                                                              │
 │◀─────────────│              │                                                                              │
```

---

## 10. Technology Mapping

| Layer | Technology | Responsibility | Reason |
|---|---|---|---|
| Frontend | React | User interface for upload, query, dashboard, and history. | Component-based architecture well-suited to dynamic, interactive UIs. |
| Backend | Flask | API orchestration and routing. | Lightweight Python framework with strong AI/ML ecosystem compatibility. |
| PDF Processing | PDF text-extraction library (e.g., PyPDF2/pdfplumber-class tooling) | Extracting raw text from uploaded PDFs. | Mature, widely used tooling for text-based PDF parsing. |
| Embeddings | Sentence Transformers | Converting text into semantic vector representations. | Strong performance on semantic similarity tasks; open-source and self-hostable. |
| Vector Database | FAISS | Storing and searching vector embeddings efficiently. | High-performance, open-source similarity search library well-suited for local/small-to-medium scale deployment. |
| LLM | Gemini | Natural language answer generation, summarization, and comparison. | Strong reasoning and generation capability accessible via hosted API. |
| Database | MongoDB | Storing paper metadata and query history. | Flexible document schema suited to varied, evolving metadata structures. |
| Charts | Charting library (frontend, e.g., Recharts-class tooling) | Visualizing trends and dashboard statistics. | Simple integration with React for rendering analytics visuals. |
| Deployment | Containerized deployment (e.g., Docker) on cloud or local infrastructure | Packaging and running the application consistently across environments. | Ensures reproducibility and simplifies future cloud migration. |

---

## 11. Design Decisions

### Why Flask instead of FastAPI
- **Decision**: Use Flask as the backend web framework.
- **Reason**: Flask is lightweight, well-documented, and widely taught, making it accessible for a capstone-scale project with a defined timeline.
- **Advantages**: Simple routing model, minimal boilerplate, large ecosystem of extensions, strong compatibility with Python AI/ML libraries.
- **Possible Alternatives**: FastAPI (offers async support and automatic OpenAPI docs), Django (more batteries-included, heavier).
- **Trade-offs**: FastAPI provides better native async performance and automatic request validation, which could benefit high-concurrency scenarios; Flask was chosen for simplicity and team familiarity, with the understanding that async-heavy scaling can be revisited in future architecture evolution.

### Why React
- **Decision**: Use React for the frontend.
- **Reason**: Component-based structure is well suited to the interactive, stateful nature of a chat-and-dashboard interface.
- **Advantages**: Large ecosystem, reusable components, strong community support, straightforward integration with REST APIs.
- **Possible Alternatives**: Vue.js, Angular, plain HTML/JS.
- **Trade-offs**: React has a steeper learning curve than plain JS but offers far better maintainability for a UI with multiple interactive views (upload, chat, dashboard, history).

### Why FAISS
- **Decision**: Use FAISS as the vector database.
- **Reason**: FAISS provides fast, efficient similarity search and can run locally without requiring a managed cloud vector database service.
- **Advantages**: Free, open-source, high performance, no external service dependency or cost.
- **Possible Alternatives**: Pinecone, Weaviate, Chroma, Milvus.
- **Trade-offs**: FAISS lacks built-in persistence/replication features of managed vector databases; for a capstone-scale system this is acceptable, but a production system at larger scale might migrate to a managed or distributed vector store.

### Why Sentence Transformers
- **Decision**: Use Sentence Transformers for generating embeddings.
- **Reason**: Provides strong, well-validated semantic embedding quality and can run locally or via lightweight hosted inference.
- **Advantages**: Open-source, no per-call API cost, good performance on semantic similarity benchmarks.
- **Possible Alternatives**: OpenAI embeddings API, Gemini embeddings API, Cohere embeddings.
- **Trade-offs**: Hosted embedding APIs may offer higher quality or scale, but introduce additional cost and external dependency; Sentence Transformers keeps the embedding step self-contained and free.

### Why Gemini
- **Decision**: Use Gemini as the LLM for generation tasks.
- **Reason**: Provides strong natural language reasoning and generation capability via an accessible hosted API, suitable for question answering, summarization, and comparison tasks.
- **Advantages**: High-quality generation, manageable API integration, competitive free/low-cost tier for development and demonstration purposes.
- **Possible Alternatives**: OpenAI GPT models, Anthropic Claude, open-source self-hosted LLMs (e.g., Llama-family models).
- **Trade-offs**: Reliance on a third-party hosted API introduces external dependency risk (rate limits, downtime); self-hosted alternatives would remove this dependency but require significantly more compute infrastructure.

### Why MongoDB
- **Decision**: Use MongoDB for metadata storage.
- **Reason**: Document-oriented storage naturally fits the semi-structured nature of paper metadata (varying fields such as extracted keywords, datasets, algorithms) and query history.
- **Advantages**: Flexible schema, easy to iterate on during development, good Python driver support.
- **Possible Alternatives**: PostgreSQL, SQLite.
- **Trade-offs**: A relational database would offer stronger consistency guarantees and structured querying, but at the cost of schema rigidity that would slow iteration during a project with evolving metadata requirements.

### Why REST APIs
- **Decision**: Use REST as the communication protocol between frontend and backend.
- **Reason**: REST is simple, well-understood, stateless, and sufficient for the request/response interaction patterns required by this system.
- **Advantages**: Broad tooling support, easy to test and document, straightforward to implement in Flask.
- **Possible Alternatives**: GraphQL, gRPC, WebSockets (for streaming responses).
- **Trade-offs**: REST does not natively support streaming token-by-token LLM responses as elegantly as WebSockets or Server-Sent Events; this is acceptable for Version 1 and identified as a candidate for future architecture evolution (Section 16).

---

## 12. Scalability Considerations

- **Thousands of PDFs**: The chunking and embedding pipeline can be scaled horizontally by processing uploads asynchronously in batches rather than synchronously within the request/response cycle; FAISS indexes can be sharded or migrated to a distributed vector database at larger scale.
- **Multiple Users**: The Metadata Database schema should associate papers, queries, and history with a user identifier from the outset, even if authentication is not fully implemented in Version 1, to avoid a costly schema migration later.
- **Cloud Deployment**: The layered, modular design allows each component (frontend, backend, databases) to be deployed as independent, horizontally scalable services in a cloud environment (e.g., container orchestration).
- **Authentication**: A dedicated authentication layer (e.g., token-based auth) can be introduced at the API gateway/backend layer without affecting the internal processing modules.
- **Caching**: Frequently requested summaries or repeated queries can be cached (e.g., in-memory or Redis-backed) to reduce redundant LLM calls and improve response time.
- **Streaming Responses**: The backend can be extended to support streamed, token-by-token LLM responses (e.g., via Server-Sent Events or WebSockets) to improve perceived responsiveness for long answers.
- **Background Processing**: PDF ingestion and embedding generation, which can be time-consuming for large files or batches, can be moved to an asynchronous task queue (e.g., Celery-class background workers) rather than blocking API requests.
- **Distributed Vector Databases**: As the paper collection grows beyond what a single-node FAISS index can efficiently serve, migration to a distributed or managed vector database (e.g., Milvus, Weaviate, Pinecone) becomes a natural evolution path, since the RAG Engine interacts with the vector store through an abstracted interface.

---

## 13. Security Architecture

- **File Validation**: All uploaded files must be validated for correct file type (PDF), reasonable size limits, and structural integrity before processing, to prevent malformed or malicious files from reaching downstream modules.
- **PDF Upload Protection**: Uploaded files should be scanned for basic threats (e.g., embedded scripts) where feasible, and processed in an isolated manner to prevent any potential exploit from affecting the broader system.
- **API Security**: All backend endpoints should validate input payloads and reject malformed or unexpected request structures before processing.
- **Environment Variables**: Sensitive configuration values (API keys, database connection strings) must be stored in environment variables, never hardcoded into source code.
- **Secrets Management**: Secrets should be excluded from version control and managed through a secure mechanism appropriate to the deployment environment (e.g., `.env` files locally, secret managers in cloud deployment).
- **Input Sanitization**: All user-provided text (queries, filenames) must be sanitized before use in downstream processing or storage to prevent injection-style issues.
- **Rate Limiting**: API endpoints, particularly those triggering LLM calls, should be rate-limited per user/session to prevent abuse and control third-party API costs.
- **Error Handling**: Error responses returned to the frontend must avoid exposing internal implementation details, stack traces, or sensitive configuration information.
- **Future Authentication**: The architecture should reserve a clear extension point (e.g., an authentication middleware layer in the Flask Backend) so that user authentication and authorization can be added without restructuring the core processing pipeline.

---

## 14. Error Handling Strategy

| Layer | Error Type | Handling Approach |
|---|---|---|
| Frontend | Network/API failure | Display a user-friendly error message; allow retry where appropriate. |
| Backend | Invalid request/payload | Return a structured error response with a clear status code and message. |
| API Failures (general) | Downstream module exception | Catch exceptions at the API layer boundary; return a generic, safe error message to the client while logging full details internally. |
| Gemini Failures | API timeout, rate limit, malformed response | Retry with backoff where appropriate; surface a clear "generation failed, please retry" message if retries are exhausted. |
| Embedding Failures | Model load failure, oversized input | Validate input length before embedding; return a descriptive error if the model is unavailable. |
| FAISS Failures | Index corruption, search failure | Fall back to a safe error response indicating search is temporarily unavailable; log for investigation. |
| Database Failures | Connection loss, write failure | Retry transient failures; return a clear error if persistence fails, without losing the user's in-progress action where possible. |
| File Upload Failures | Corrupted/invalid/oversized file | Reject at validation stage with a specific, actionable error message (e.g., "unsupported file format"). |
| Logging Strategy | N/A | All errors, regardless of layer, are logged centrally through the Logging Module with severity level, timestamp, and relevant context, enabling post-incident debugging without exposing internal details to end users. |

The general principle across all layers is: **fail safely and informatively**. Internal errors are logged with full detail for developers, while user-facing messages remain clear, non-technical, and actionable, without leaking internal system information.

---

## 15. Performance Considerations

- **Lazy Loading**: Heavy resources (e.g., the embedding model) should be loaded once at application startup rather than on every request, avoiding repeated initialization overhead.
- **Caching**: Frequently repeated queries or previously generated summaries can be cached to avoid redundant embedding and LLM generation calls.
- **Vector Indexing**: FAISS index type and parameters should be selected based on the expected scale of the paper collection, balancing search speed against index build time and memory usage.
- **Chunk Size Optimization**: Chunk size should be tuned to balance retrieval precision (smaller chunks are more targeted) against context sufficiency (larger chunks preserve more surrounding meaning); this is a key tunable parameter affecting both retrieval quality and performance.
- **Embedding Reuse**: Once a paper's chunks are embedded, embeddings should be persisted and reused across all future queries rather than regenerated, avoiding redundant computation.
- **Database Optimization**: Metadata queries (e.g., fetching a user's paper list or history) should be indexed appropriately in MongoDB to maintain fast dashboard and history load times as data grows.
- **Prompt Optimization**: Prompts sent to the Gemini API should include only the most relevant retrieved context (not excessive or redundant chunks) to minimize latency and token usage while preserving answer quality.

---

## 16. Future Architecture Evolution

- **OCR**: Introduce an OCR module (e.g., for scanned/image-based PDFs) as an additional branch within the PDF Processing Module, activated when standard text extraction yields insufficient content.
- **Multi-language Papers**: Extend the Embedding Module and Gemini prompts to support multilingual models and language-aware processing.
- **Citation Generation**: Add a dedicated Citation Module that parses bibliographic metadata and formats citations in standard styles (APA, MLA, BibTeX).
- **Cloud Storage**: Migrate uploaded PDF storage from local/ephemeral storage to durable cloud object storage (e.g., S3-class storage) for reliability and scale.
- **Collaborative Workspaces**: Extend the Metadata Database schema to support shared workspace entities, with access control governing which users can view/edit a shared paper collection.
- **Multiple LLM Providers**: Abstract the Gemini Integration behind a provider-agnostic interface, allowing the RAG Engine to route requests to different LLM providers based on configuration.
- **Semantic Paper Recommendations**: Leverage existing embeddings to power a recommendation module that suggests related papers based on a user's uploaded collection and query history.
- **Research Graph Generation**: Build a graph-based representation connecting papers, shared concepts, datasets, and methods, enabling visual exploration of a research area's structure — a natural extension of the existing Analytics Module.

---

## 17. Architecture Summary

The architecture defined in this document establishes a **layered, modular, retrieval-augmented system** purpose-built for transforming static research papers into an interactive, queryable knowledge base. By clearly separating the frontend, API orchestration layer, AI processing modules (PDF processing, embedding, retrieval, generation), and storage layers (vector database and metadata database), the system achieves the architectural goals of scalability, maintainability, modularity, and extensibility defined in Section 2.

This design is well-suited to an AI-powered Research Assistant specifically because it mirrors the natural pipeline of the problem domain: documents flow through extraction and embedding into a searchable form, questions flow through the same embedding space to retrieve relevant context, and a language model synthesizes that context into grounded, useful answers. Each stage of this pipeline is implemented as an independently replaceable component, ensuring that the system can evolve — new LLM providers, distributed vector stores, OCR support, or collaborative features — without requiring a fundamental architectural rewrite.

This document, together with `01_Project_Overview.md`, provides the complete conceptual and structural foundation required to begin detailed implementation planning.
