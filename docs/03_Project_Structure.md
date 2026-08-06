# 03_Project_Structure.md

## 1. Purpose of this Document

This document defines the complete **project organization** for the AI Research Assistant: folder hierarchy, file responsibilities, naming conventions, coding standards, dependency management, and development workflow. While `01_Project_Overview.md` defines *what* the system does and `02_System_Architecture.md` defines *how* the system is architecturally composed, this document defines *where* every piece of that architecture lives in the codebase and *how* developers should work within it.

A well-defined project structure matters because architecture alone does not prevent a codebase from becoming disorganized as it grows. Without an agreed-upon organization scheme, related logic tends to scatter, naming becomes inconsistent, and new contributors waste time locating the correct place to add or modify code. A clear structure directly improves four things:

- **Scalability** — new features and modules have an obvious, predetermined home, so the codebase can grow without accumulating disorganization.
- **Maintainability** — related code is grouped together, making it easier to understand, modify, and fix without unintended side effects elsewhere.
- **Collaboration** — multiple developers (or a single developer returning after time away) can navigate the codebase predictably, reducing onboarding time and merge conflicts.
- **Debugging** — when an error occurs, a clear structure narrows down where to look, since each folder has a single, well-defined responsibility.

This document should be treated as binding for all development work on the project — every file created during implementation should have an obvious, justified location according to the structure defined here.

---

## 2. Project Organization Philosophy

The folder structure and coding organization for this project are grounded in the following principles, which extend the architectural principles established in `02_System_Architecture.md` down to the file and folder level.

| Principle | Application in This Project |
|---|---|
| **Separation of Concerns** | Frontend, backend, documentation, and data storage are kept in entirely separate top-level directories; within the backend, PDF processing, embeddings, and API routing are never mixed into the same files. |
| **Modular Design** | Each backend capability (PDF processing, embeddings, RAG, database access) is implemented as an independent module with a defined interface, mirroring the component boundaries defined in the architecture document. |
| **Single Responsibility Principle** | Every file and function is designed to do exactly one job — e.g., a file responsible for text extraction does not also handle embedding generation. |
| **Loose Coupling** | Modules interact through clearly defined function interfaces, not through shared global state or direct access to another module's internals. |
| **High Cohesion** | Files that change together are grouped together — e.g., all vector-store-related logic lives within a single `services/vector_store` module rather than being spread across the codebase. |
| **Clean Architecture** | Business logic (services) is kept independent of framework-specific code (routes/controllers), so core logic can be tested and reused without depending on Flask or React specifics. |
| **Scalability** | The structure anticipates growth — e.g., the `routes/` and `services/` folders can each accept new files as features are added, without requiring restructuring. |
| **Maintainability** | Consistent naming, clear folder responsibilities, and centralized configuration reduce the cognitive overhead of maintaining the system over time. |

These principles are not abstract ideals — they directly determine the folder layout defined in Section 3 and the coding standards defined in Section 9.

---

## 3. Complete Folder Structure

```
research-assistant/
│
├── backend/                     # Flask backend application (API + AI pipeline)
│   ├── config/                  # Centralized configuration and environment loading
│   ├── controllers/             # Request-handling logic invoked by routes
│   ├── middlewares/             # Cross-cutting request/response logic (validation, error handling)
│   ├── models/                  # Data models / schemas for MongoDB documents
│   ├── routes/                  # API endpoint definitions (URL → controller mapping)
│   ├── services/                # Core business logic and AI pipeline modules
│   ├── utils/                   # Shared helper functions used across the backend
│   ├── tests/                   # Backend unit and integration tests
│   ├── logs/                    # Runtime log output (backend application/error logs)
│   ├── uploads/                 # Temporary/persisted storage for uploaded PDF files
│   ├── vector_store/            # Persisted FAISS index files
│   ├── app.py                   # Application entry point
│   └── requirements.txt         # Python dependency manifest
│
├── frontend/                    # React frontend application
│   ├── public/                  # Static public assets served as-is
│   ├── src/
│   │   ├── pages/               # Top-level page components (Upload, Chat, Dashboard, History)
│   │   ├── components/          # Reusable, composable UI components
│   │   ├── layouts/             # Shared page layout wrappers (header, sidebar, etc.)
│   │   ├── hooks/                # Custom React hooks encapsulating reusable logic
│   │   ├── services/             # Frontend-side business logic (e.g., formatting, validation)
│   │   ├── api/                  # API client functions for backend communication
│   │   ├── context/               # React context providers for global state
│   │   ├── styles/                # Global and shared styling
│   │   ├── assets/                # Images, icons, and static media
│   │   └── utils/                 # Shared frontend helper functions
│   ├── package.json
│   └── package-lock.json
│
├── docs/                         # Project documentation (design documents)
│
├── .env                          # Environment variable definitions (not committed to version control)
├── .gitignore                    # Files/folders excluded from version control
└── README.md                     # Project introduction, setup, and usage instructions
```

**Design Note**: This structure deliberately avoids unnecessary nesting or speculative folders (e.g., no empty `plugins/` or `extensions/` directory is created preemptively). Every folder listed above has an immediate, concrete purpose tied to a component defined in `02_System_Architecture.md`. Folders are added only when a corresponding architectural need exists, consistent with the **Simplicity** goal defined in the architecture document.

---

## 4. Backend Folder Organization

| Folder | Purpose | Responsibilities | Expected Files | Dependencies | Interacts With |
|---|---|---|---|---|---|
| `config/` | Centralize all application configuration. | Load environment variables; define constants (chunk size, model names, file size limits). | `settings.py` (or equivalent) | `.env` file | Nearly all backend modules read from this. |
| `controllers/` | Handle the logic behind each API request. | Parse validated request data; invoke the appropriate service; format the response. | `upload_controller`, `query_controller`, `summary_controller`, `comparison_controller` | `services/`, `models/` | Called by `routes/`; calls into `services/`. |
| `middlewares/` | Apply cross-cutting logic to incoming requests/outgoing responses. | Request validation, centralized error handling, request logging. | `error_handler`, `validation_middleware`, `logging_middleware` | `utils/`, `config/` | Wraps around `routes/` and `controllers/`. |
| `models/` | Define the structure of data persisted in MongoDB. | Define schemas/data classes for Paper, QueryHistory, User (future), ExtractedMetadata. | `paper_model`, `query_history_model`, `metadata_model` | `backend/services/database_service.py` (connection) | Used by `services/` for persistence operations. |
| `routes/` | Define API endpoints and map them to controllers. | Declare URL paths, HTTP methods, and bind them to the correct controller function. | `upload_routes`, `query_routes`, `summary_routes`, `comparison_routes`, `history_routes` | `controllers/` | Registered in `app.py`; the entry point for all frontend requests. |
| `services/` | Contain the core business logic and AI pipeline. | Implement PDF processing, chunking, embedding generation, vector search, RAG orchestration, Groq integration, analytics. | `pdf_service`, `chunking_service`, `embedding_service`, `vector_store_service`, `rag_service`, `groq_service`, `analytics_service` | External libraries (Sentence Transformers, FAISS, Groq SDK) | Called by `controllers/`; this is the heart of the AI pipeline described in the architecture document. |
| `utils/` | Provide shared, generic helper functions. | File validation, text cleaning helpers, response formatting, date/time helpers. | `file_utils`, `text_utils`, `response_utils` | None (should remain dependency-light) | Used across `services/`, `controllers/`, `middlewares/`. |
| `tests/` | Contain backend automated tests. | Unit tests for each service; integration tests for API endpoints. | `test_pdf_service`, `test_embedding_service`, `test_query_routes`, etc. | `services/`, `routes/` (as test subjects) | Mirrors the structure of the modules it tests. |
| `logs/` | Store runtime log output. | Hold application and error log files generated during execution. | `app.log`, `error.log` | Logging Module (per architecture doc) | Written to by all backend modules via the logging utility. |
| `uploads/` | Temporarily or persistently store uploaded PDF files. | Hold raw uploaded files prior to/after processing. | User-uploaded `.pdf` files (not committed to version control) | `pdf_service` | Read by the PDF Processing service. |
| `vector_store/` | Persist the FAISS vector index to disk. | Store serialized FAISS index files and associated ID mappings. | `index.faiss`, `id_mapping.json` (or equivalent) | `vector_store_service` | Read/written by the Vector Database component. |
| `app.py` | Application entry point. | Initialize the Flask app, register routes/middlewares, start the server. | — | `routes/`, `middlewares/`, `config/` | The root of the backend application. |
| `requirements.txt` | Declare Python dependencies. | List all required Python packages and versions. | — | — | Used by the environment setup process. |

---

## 5. Frontend Folder Organization

```
frontend/src/
│
├── pages/            # Full page views composed of components
├── components/        # Reusable UI building blocks
├── layouts/            # Shared structural wrappers (navbar, sidebar, footer)
├── hooks/               # Custom React hooks for reusable stateful logic
├── services/             # Frontend business logic (formatting, client-side computations)
├── api/                   # Functions responsible for calling backend REST endpoints
├── context/                # Global state providers (React Context API)
├── styles/                  # Shared/global CSS or styling configuration
├── assets/                   # Images, icons, and static media files
└── utils/                     # Generic reusable helper functions
```

| Folder | Responsibility |
|---|---|
| `pages/` | Represents each top-level screen of the application — e.g., `UploadPage`, `ChatPage`, `DashboardPage`, `HistoryPage`, `ComparisonPage`. Each page composes multiple components into a complete view. |
| `components/` | Contains small, reusable UI elements shared across pages — e.g., `PaperCard`, `ChatBubble`, `FileUploader`, `LoadingSpinner`, `ComparisonTable`. Components should not contain page-specific business logic. |
| `layouts/` | Defines shared structural wrappers applied across multiple pages, such as a common header, sidebar navigation, or footer, ensuring visual consistency without duplicating layout code. |
| `hooks/` | Encapsulates reusable stateful logic, such as `useUpload`, `useChat`, `usePapers` — separating "how state behaves" from "how it is displayed." |
| `services/` | Contains frontend-side logic that is not purely presentational, such as formatting API responses for display or client-side validation logic, kept separate from raw API calls. |
| `api/` | Contains functions that directly call backend REST endpoints (e.g., `uploadPapers()`, `askQuestion()`, `getHistory()`), centralizing all HTTP communication in one place so the rest of the app never calls `fetch`/`axios` directly. |
| `context/` | Holds React Context providers for global application state, such as the currently uploaded paper library or active user session. |
| `styles/` | Contains global stylesheets, theme variables, and shared style configuration used across the application. |
| `assets/` | Stores static media such as logos, icons, and illustrations used in the UI. |
| `utils/` | Provides generic, reusable helper functions (e.g., date formatting, text truncation) with no dependency on application-specific state. |

This structure ensures a clean separation between **presentation** (`components/`, `pages/`, `layouts/`, `styles/`), **state and logic** (`hooks/`, `context/`, `services/`), and **communication** (`api/`) — mirroring the separation-of-concerns principle applied to the backend.

---

## 6. Documentation Folder

```
docs/
├── 01_Project_Overview.md
├── 02_System_Architecture.md
├── 03_Project_Structure.md
├── 04_Technology_Stack.md
├── 05_Database_Design.md
├── 06_API_Design.md
├── 07_RAG_Pipeline.md
├── 08_Deployment.md
├── 09_Testing.md
└── 10_Future_Enhancements.md
```

| Document | Purpose |
|---|---|
| `01_Project_Overview.md` | Establishes the project's purpose, problem statement, goals, scope, and feature set. |
| `02_System_Architecture.md` | Defines the system's architectural components, data flow, and technology mapping. |
| `03_Project_Structure.md` | Defines the codebase organization, folder responsibilities, and development standards (this document). |
| `04_Technology_Stack.md` | Provides a detailed breakdown of every technology used, including versions and justification. |
| `05_Database_Design.md` | Defines the MongoDB schema, collections, relationships, and indexing strategy. |
| `06_API_Design.md` | Specifies every REST endpoint, including request/response formats and status codes. |
| `07_RAG_Pipeline.md` | Provides a detailed, step-by-step design of the Retrieval-Augmented Generation pipeline, including chunking and prompt strategy. |
| `08_Deployment.md` | Describes how the application is built, configured, and deployed across environments. |
| `09_Testing.md` | Defines the testing strategy, coverage expectations, and test organization. |
| `10_Future_Enhancements.md` | Expands on the roadmap of future features and how they extend the current architecture. |

Keeping documentation in a dedicated, numbered `docs/` folder ensures that the project's design record remains discoverable, ordered, and easy for new contributors (or evaluators) to review from start to finish.

---

## 7. Configuration Files

| File | Purpose |
|---|---|
| `.env` | Stores environment-specific secrets and configuration values (API keys, database URLs) outside of source code; never committed to version control. |
| `.gitignore` | Specifies files and folders (e.g., `.env`, `node_modules/`, `uploads/`, `vector_store/`, `__pycache__/`, `logs/`) that must be excluded from version control to avoid leaking secrets or bloating the repository. |
| `README.md` | Provides a top-level introduction to the project: what it does, how to set it up, how to run it, and where to find further documentation. |
| `requirements.txt` | Declares all Python package dependencies and their versions for the backend, ensuring a reproducible environment. |
| `package.json` | Declares Node.js/React dependencies, scripts (start, build, test), and frontend project metadata. |
| `package-lock.json` | Locks exact versions of all installed npm packages (including transitive dependencies) to guarantee reproducible frontend installs across machines. |

---

## 8. File Naming Conventions

| Category | Convention | Example |
|---|---|---|
| Python files | `snake_case` | `pdf_service.py`, `query_controller.py` |
| React components | `PascalCase` | `FileUploader.jsx`, `ChatBubble.jsx` |
| Folders | `lowercase` (with hyphens only if unavoidable) | `services/`, `vector_store/` |
| Environment variables | `UPPER_SNAKE_CASE` | `GROQ_API_KEY`, `DATABASE_URL` |
| Markdown documents | `NN_Title_Case_With_Underscores.md` | `01_Project_Overview.md` |
| Images/assets | `kebab-case` | `logo-primary.svg`, `empty-state-icon.png` |
| Configuration files | Standard tool-defined name | `.env`, `.gitignore`, `package.json` |

**Why Consistency Matters**: Predictable naming allows any developer to infer a file's type, purpose, and location conventions without needing to open it. It also prevents subtle cross-platform issues (e.g., case-sensitivity mismatches between operating systems) and keeps auto-generated tooling (linters, import resolvers, build systems) functioning reliably.

---

## 9. Code Organization Standards

| Element | Standard | Example |
|---|---|---|
| **Function naming** | `snake_case` verbs describing the action performed (Python); `camelCase` in JavaScript/React. | `extract_text_from_pdf()` (Python), `fetchPapers()` (JS) |
| **Class naming** | `PascalCase`, noun-based, describing the entity or responsibility. | `PDFProcessor`, `EmbeddingService` |
| **Variable naming** | `snake_case` (Python) / `camelCase` (JS), descriptive rather than abbreviated. | `chunk_size`, `uploadedFiles` |
| **Constants** | `UPPER_SNAKE_CASE`, defined centrally in `config/`. | `MAX_FILE_SIZE_MB`, `DEFAULT_CHUNK_SIZE` |
| **Comments** | Used to explain *why*, not *what* — code should be self-explanatory for the "what." | `# Using overlapping chunks to preserve context across boundaries` |
| **Docstrings** | Every service function/class should include a docstring describing purpose, parameters, and return value. | Standard Python docstring format. |
| **Imports** | Grouped and ordered: standard library → third-party packages → local modules; no wildcard imports. | — |
| **Formatting** | Consistent formatting enforced via an auto-formatter (e.g., Black for Python, Prettier for JS/React) and a linter (e.g., Flake8/ESLint). | — |

**Coding Style Summary**: The project favors explicit, descriptive naming over brevity, small single-purpose functions over large multi-purpose ones, and consistent automated formatting over manually enforced style. This directly supports the Maintainability and Collaboration goals defined in Section 1.

---

## 10. Dependency Management

**Python (Backend)**
- All dependencies are declared in `requirements.txt` with pinned or minimum-compatible versions to ensure reproducibility.
- Development should occur within an isolated **virtual environment** (e.g., `venv`), preventing conflicts with system-wide Python packages.
- New dependencies must be added to `requirements.txt` immediately upon introduction, never installed ad hoc without being recorded.

**Node.js (Frontend)**
- Dependencies are declared in `package.json`, with exact resolved versions locked in `package-lock.json`.
- `npm install` should always be run from the `frontend/` directory to avoid dependency conflicts with the backend environment.
- The lock file must be committed to version control to guarantee that all developers and deployment environments install identical dependency versions.

**Version Management**
- Dependency versions should be upgraded deliberately and tested, not automatically, to avoid introducing breaking changes silently.
- Major framework or library upgrades (e.g., React major versions, Flask major versions) should be documented and tested in isolation before merging into the main development branch.

---

## 11. Environment Variables

| Variable | Purpose |
|---|---|
| `GROQ_API_KEY` | Authenticates requests to the Groq LLM API for answer generation, summarization, and comparison. |
| `GROQ_MODEL_NAME` | Specifies the Groq model to use (default: `llama-3.3-70b-versatile`). |
| `JWT_SECRET_KEY` | Secret key used to sign and verify JWT authentication tokens; required for user login/registration. |
| `UPLOAD_DIRECTORY` | Specifies the file system path where uploaded PDF files are stored prior to and during processing. |
| `DATABASE_URL` | Specifies the connection string used to connect to the MongoDB metadata database. |
| `VECTOR_STORE_PATH` | Specifies the file system path where the FAISS vector index is persisted. |
| `APPLICATION_PORT` | Specifies the port on which the Flask backend server listens for requests. |
| `DEBUG_MODE` | Toggles verbose debugging behavior (e.g., detailed error output) for development environments; disabled in production. |
| `LOGGING_LEVEL` | Controls the verbosity of application logs (e.g., DEBUG, INFO, WARNING, ERROR). |

**Note**: Actual values for these variables must never be committed to version control. They should exist only in a local `.env` file (excluded via `.gitignore`) or in a secure secrets manager for deployed environments.

---

## 12. Logging Strategy

- **Log Directory**: All log output is written to the `backend/logs/` directory, keeping runtime diagnostic output separate from source code and uploaded content.
- **Log Levels**: The system uses standard severity levels — `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` — configurable via the `LOGGING_LEVEL` environment variable, allowing verbosity to differ between development and production.
- **Log Format**: Each log entry should include a timestamp, severity level, originating module, and message, in a consistent structured format to support easy searching and future integration with external log aggregation tools.
- **Error Logs**: Errors and exceptions are logged with sufficient context (module, function, relevant identifiers) to support debugging, while any sensitive data (API keys, full file contents) is explicitly excluded from log output.
- **Application Logs**: General operational events (server start, successful upload, successful query) are logged at `INFO` level to provide a readable audit trail of normal system activity.
- **Debug Logs**: Detailed internal state (e.g., intermediate chunk counts, retrieval scores) is logged at `DEBUG` level only, kept out of production logs by default to avoid excessive noise.
- **Future Monitoring**: The logging format and structure are designed to be compatible with future integration into centralized monitoring/observability tools (e.g., an external log aggregator or application performance monitoring service), without requiring a redesign of the logging approach itself.

---

## 13. Testing Organization

```
backend/tests/
├── unit/
│   ├── test_pdf_service.py
│   ├── test_chunking_service.py
│   ├── test_embedding_service.py
│   ├── test_vector_store_service.py
│   └── test_rag_service.py
├── integration/
│   ├── test_upload_flow.py
│   ├── test_query_flow.py
│   └── test_comparison_flow.py
├── api/
│   ├── test_upload_routes.py
│   ├── test_query_routes.py
│   └── test_history_routes.py
├── mock_data/
│   └── sample_metadata.json
├── sample_pdfs/
│   └── sample_paper_01.pdf
└── test_assets/
    └── expected_outputs.json

frontend/src/__tests__/
├── components/
├── pages/
└── hooks/
```

| Folder | Purpose |
|---|---|
| `unit/` | Tests individual backend service functions in isolation (e.g., verifying that chunking produces the expected number of segments for a given input). |
| `integration/` | Tests multi-step flows spanning several services (e.g., uploading a PDF through to successful vector storage). |
| `api/` | Tests backend REST endpoints directly, verifying correct request handling, status codes, and response structure. |
| `mock_data/` | Contains synthetic metadata and fixture data used to test services without depending on real uploaded content. |
| `sample_pdfs/` | Contains small, representative sample PDF files used consistently across tests to validate extraction and processing behavior. |
| `test_assets/` | Contains expected output files/values used to assert correctness in tests (e.g., expected extracted text for a known sample PDF). |
| `frontend/src/__tests__/` | Mirrors the frontend `src/` structure, containing component, page, and hook-level tests for the React application. |

---

## 14. Development Workflow

Development should proceed in the following logical order, consistent with the dependency chain established in the architecture:

1. **Documentation** — Finalize `01_Project_Overview.md` through `03_Project_Structure.md` (and subsequent design documents) before writing code, ensuring all contributors share a common understanding of scope and structure.
2. **Backend Core** — Implement foundational backend scaffolding: `config/`, `app.py`, basic routing, and database connectivity.
3. **AI Modules** — Implement the PDF processing, chunking, embedding, vector storage, and RAG services, testing each in isolation before integration.
4. **Frontend** — Build the React application against the backend API, starting with the upload flow, then the chat/query interface, then the dashboard and history views.
5. **Testing** — Write and run unit, integration, and API tests alongside (not strictly after) each module's implementation, rather than deferring all testing to the end.
6. **Deployment** — Prepare build artifacts, configure environment variables for the target environment, and deploy backend and frontend components.
7. **Maintenance** — Monitor logs, address issues, and extend functionality according to the roadmap defined in `01_Project_Overview.md` and `02_System_Architecture.md`.

---

## 15. Git Workflow

| Branch/Element | Purpose |
|---|---|
| `main` | Contains stable, production-ready code only; direct commits are not permitted. |
| `develop` | Integration branch where completed features are merged and validated together before promotion to `main`. |
| `feature/<name>` | Short-lived branches for individual features or modules (e.g., `feature/pdf-extraction`, `feature/chat-ui`), branched from `develop` and merged back via pull request. |
| **Commit Message Convention** | Use a consistent, descriptive format, e.g., `feat: add PDF chunking service`, `fix: handle empty PDF upload`, `docs: update architecture document`. |
| **Pull Requests** | All merges into `develop` or `main` occur through pull requests, allowing review and discussion before integration. |
| **Version Tags** | Tag stable releases (e.g., `v1.0.0`) on `main` to mark meaningful project milestones, particularly useful for capstone submission checkpoints. |

**Why This Workflow Is Suitable**: This branching strategy provides a clear separation between stable, in-progress, and experimental code, reduces the risk of breaking the main codebase, and creates a reviewable history of changes — valuable both for collaborative development and for demonstrating engineering discipline in an academic evaluation context.

---

## 16. Build and Deployment Structure

- **Frontend Build**: The React application is compiled into a static production build (`npm run build`), producing optimized, minified assets suitable for serving from a static host or CDN.
- **Backend Deployment**: The Flask backend is deployed as a standalone service (e.g., within a container), exposing its REST API on the configured `APPLICATION_PORT`.
- **Environment Configuration**: Each deployment environment (development, staging, production) maintains its own `.env` configuration, ensuring environment-specific values (API keys, database URLs) are never mixed across environments.
- **Static Assets**: Frontend static assets (images, compiled JS/CSS) are served independently of the backend API, keeping concerns cleanly separated.
- **Production Logs**: In production, logs are written with a reduced verbosity (`INFO` and above) and should be directed toward persistent, centrally accessible storage rather than local ephemeral disk where possible.
- **Deployment Artifacts**: The build process should produce clearly identifiable artifacts (a frontend build folder, a backend deployment package/container image) that can be versioned and traced back to a specific Git tag/commit.

---

## 17. Maintenance Strategy

The project structure is explicitly designed to support the following future extensions without requiring structural rework:

- **Adding New Modules**: New backend capabilities are added as new files within `services/`, with corresponding routes/controllers added in `routes/` and `controllers/` — no existing module needs modification to accommodate an unrelated new feature.
- **Replacing LLM Providers**: Because all LLM interaction is isolated within `groq_service` (behind a consistent interface used by `rag_service`), switching providers requires modifying or replacing a single service file rather than logic scattered throughout the codebase.
- **Replacing Vector Databases**: Similarly, all vector storage/search logic is isolated within `vector_store_service`; migrating from FAISS to another vector database requires changes only within this module.
- **Adding Authentication**: A new `middlewares/auth_middleware` can be introduced and applied to existing routes without modifying the internal business logic of `services/`.
- **Supporting New Document Formats**: Additional document types (e.g., `.docx`, `.txt`) can be supported by extending `pdf_service` (or introducing a parallel `docx_service`) that ultimately feeds into the same downstream chunking and embedding pipeline, since those stages operate on plain text regardless of source format.

This maintenance strategy directly reflects the **loose coupling** and **modular design** principles established in Section 2 — every anticipated future change maps to a modification within a single, well-bounded module.

---

## 18. Best Practices

- Keep modules independent; a module should be understandable and testable without needing to read unrelated modules.
- Avoid duplicate code; extract shared logic into `utils/` or a dedicated shared service rather than copy-pasting.
- Write reusable services; business logic should be callable from multiple controllers/routes where applicable, not duplicated per endpoint.
- Separate business logic from framework code; `services/` should not depend on Flask request/response objects directly, keeping logic portable and testable.
- Centralize configuration; all tunable values (chunk size, model names, file limits) should live in `config/`, never hardcoded inline.
- Handle exceptions consistently; use the shared error-handling middleware pattern rather than ad hoc try/except blocks with inconsistent behavior.
- Document every module; each service and significant function should include a docstring explaining its purpose and usage.
- Maintain clean commits; each commit should represent a single, coherent change with a clear, descriptive message.
- Write tests alongside new functionality rather than deferring testing indefinitely.
- Keep the frontend `api/` layer as the sole point of contact with the backend, avoiding scattered HTTP calls throughout the UI codebase.
- Review the folder structure periodically as the project grows, ensuring new files continue to map cleanly onto existing folder responsibilities rather than accumulating in a catch-all location.

---

## 19. Project Structure Summary

The project structure defined in this document translates the architectural design of `02_System_Architecture.md` into a concrete, navigable codebase organization. By enforcing separation of concerns between frontend and backend, modularizing the AI pipeline into independently replaceable services, centralizing configuration and documentation, and establishing consistent naming and workflow conventions, this structure directly supports the goals of scalability, maintainability, and collaboration identified in Section 1.

This organization ensures that the AI Research Assistant can be developed incrementally and predictably, tested thoroughly at each layer, and extended in the future — whether that means adding new AI capabilities, swapping underlying technologies, or scaling to support more users and papers — without requiring a fundamental reorganization of the codebase. Together with `01_Project_Overview.md` and `02_System_Architecture.md`, this document completes the foundational planning trio required before implementation begins.
