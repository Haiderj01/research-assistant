# PROJECT_RULES.md

## AI Research Assistant — Official Engineering Handbook

This document is the **binding engineering standard** for the AI Research Assistant: Intelligent Research Paper Analysis and Question Answering System. It applies to every contributor — human developers and AI coding assistants alike — and to every piece of code, configuration, or documentation added to this project from this point forward.

---

## 1. Purpose

Coding standards exist because a codebase is not written once; it is read, modified, debugged, and extended repeatedly, often by people (or AI assistants) who did not write the original code. Without enforced standards, a codebase built by multiple contributors — especially a mix of human developers and AI coding assistants operating independently across sessions — will drift toward inconsistency: different naming schemes, different error-handling patterns, duplicated logic, and unpredictable file placement.

This is especially critical for a project where **multiple AI coding assistants may contribute code at different times, in different sessions, with no shared memory of prior decisions**. Each assistant must be able to infer the correct pattern to follow purely from this document and the existing codebase — not from conversational context that may not persist. Enforced, written standards are therefore the single mechanism that keeps the codebase coherent over time.

This document exists to guarantee:
- **Consistency** — the same kind of problem is solved the same way everywhere in the codebase.
- **Predictability** — any contributor can guess where a piece of code lives and how it should be written, before looking.
- **Quality** — every module meets a minimum, non-negotiable bar for documentation, error handling, and testing.
- **Longevity** — the codebase remains maintainable as it grows, rather than degrading with each new contribution.

Every rule in this document is enforceable and should be treated as a requirement, not a suggestion.

---

## 2. General Engineering Principles

| Principle | Explanation | Application in This Project |
|---|---|---|
| **Clean Code** | Code should be written to be read by humans first, and executed by machines second. Prioritize clarity over cleverness. | Prefer explicit, descriptive logic over compact but obscure one-liners. |
| **SOLID** | A set of five principles (Single Responsibility, Open/Closed, Liskov Substitution, Interface Segregation, Dependency Inversion) that guide maintainable object-oriented and modular design. | Services depend on abstractions (e.g., "an embedding function") rather than concrete implementations, so components (like the LLM provider) can be swapped without rewriting dependents. |
| **DRY (Don't Repeat Yourself)** | Every piece of logic should have a single, authoritative representation in the codebase. | Shared logic (e.g., file validation, response formatting) must live in `utils/` or a shared service, never duplicated across files. |
| **KISS (Keep It Simple, Stupid)** | Prefer the simplest solution that correctly solves the problem. | Avoid introducing frameworks, abstractions, or design patterns that are not justified by an actual current need. |
| **YAGNI (You Aren't Gonna Need It)** | Do not build functionality speculatively for hypothetical future requirements. | Do not implement authentication, multi-LLM routing, or other future-roadmap features until they are actually scheduled for implementation — design for extensibility, not premature complexity. |
| **Separation of Concerns** | Distinct responsibilities (e.g., PDF parsing vs. embedding vs. API routing) must be implemented in distinct modules. | Enforced by the folder structure defined in `03_Project_Structure.md`. |
| **Single Responsibility Principle** | Every function, class, and module should have exactly one reason to change. | A service function that extracts text must not also handle chunking or persistence. |
| **Modular Design** | The system is composed of independent, replaceable units connected through clear interfaces. | Every AI pipeline stage (PDF processing, embedding, retrieval, generation) is its own service module, per `02_System_Architecture.md`. |

These principles are not abstract ideals — every subsequent rule in this document is a direct, concrete application of one or more of them.

---

## 3. Folder Rules

All code and assets must be placed according to the structure defined in `03_Project_Structure.md`. The following rules summarize where each type of content belongs:

| Content Type | Location | Rule |
|---|---|---|
| **Backend business logic** | `backend/services/` | All AI pipeline and core logic (PDF processing, embedding, RAG, database access) lives here — never in routes or controllers. |
| **Backend request handling** | `backend/controllers/` | Only request parsing and response formatting; delegates all logic to `services/`. |
| **Backend endpoint definitions** | `backend/routes/` | Only URL-to-controller mapping; no logic beyond routing. |
| **Frontend UI** | `frontend/src/components/`, `frontend/src/pages/` | Presentational and page-level React code only; no direct API calls (must go through `api/`). |
| **Documentation** | `docs/` | All Markdown design documents, numbered and named per the convention in `03_Project_Structure.md`. |
| **Utilities** | `backend/utils/` (backend), `frontend/src/utils/` (frontend) | Only generic, reusable helper functions with no dependency on business-specific state. |
| **Configuration** | `backend/config/` | All environment loading and application constants; nowhere else. |
| **Assets** | `frontend/src/assets/` | Images, icons, and static media only. |
| **Tests** | `backend/tests/`, `frontend/src/__tests__/` | Mirrors the structure of the code under test. |
| **Logs** | `backend/logs/` | Runtime log output only; never committed to version control. |

**Rule**: If a new file does not clearly belong in one of the folders defined in `03_Project_Structure.md`, do not create a new top-level folder without updating that document first. Structural changes must be deliberate, not incidental.

---

## 4. File Naming Rules

| File Type | Convention | Example |
|---|---|---|
| Python files | `snake_case.py` | `embedding_service.py` |
| React components | `PascalCase.jsx` | `PaperCard.jsx` |
| React hooks | `useCamelCase.js`, prefixed with `use` | `useUpload.js` |
| Utility files | `snake_case.py` (backend) / `camelCase.js` (frontend) | `text_utils.py`, `formatDate.js` |
| Markdown documentation | `NN_Title_Case_With_Underscores.md` | `05_Database_Design.md` |
| Images/media | `kebab-case` | `paper-icon.svg` |
| Configuration files | Tool-standard name, unmodified | `.env`, `.gitignore`, `package.json` |

**Rule**: Every new file must follow the convention for its type without exception. If a contributor is unsure which convention applies, they must default to the convention of the nearest existing analogous file, not invent a new pattern.

---

## 5. Code Style

| Element | Rule |
|---|---|
| **Variables** | Descriptive, `snake_case` (Python) or `camelCase` (JS); no single-letter names except in tightly scoped loop counters. |
| **Functions** | `snake_case` (Python) / `camelCase` (JS), named as a verb phrase describing the action (e.g., `extract_text`, `fetchHistory`). |
| **Classes** | `PascalCase`, noun-based, describing the entity (e.g., `PDFProcessor`, `EmbeddingService`). |
| **Constants** | `UPPER_SNAKE_CASE`, defined centrally in `config/` — never hardcoded inline in business logic. |
| **Imports** | Grouped in order: standard library → third-party packages → local modules. No wildcard (`import *`) imports. |
| **Spacing/Formatting** | Enforced automatically via a formatter (Black for Python, Prettier for JS/React); manual formatting deviations are not permitted. |
| **Docstrings** | Every public function, class, and service method must include a docstring describing its purpose, parameters, and return value. |
| **Comments** | Explain *why*, not *what*. Code should be self-explanatory for *what* it does; comments justify non-obvious decisions. |

**Rule**: Code that does not pass the project's configured linter/formatter must not be merged.

---

## 6. API Standards

Every backend API endpoint must return a consistent, predictable response structure.

**Success Response Shape**
- Must include a clear success indicator, the requested data payload, and an appropriate HTTP status code (e.g., `200 OK`, `201 Created`).

**Error Response Shape**
- Must include a clear failure indicator, a human-readable error message safe for frontend display, and an appropriate HTTP status code.
- Must **never** include internal stack traces, file paths, or raw exception text in the response body.

**Validation Errors**
- Must be returned with a `400 Bad Request` status and a message identifying which field(s) failed validation and why.

**HTTP Status Code Usage**
| Status Code | Usage |
|---|---|
| `200 OK` | Successful GET/POST requests returning data. |
| `201 Created` | Successful resource creation (e.g., paper upload processed). |
| `400 Bad Request` | Invalid or malformed request payload. |
| `404 Not Found` | Requested resource (e.g., paper ID) does not exist. |
| `422 Unprocessable Entity` | Well-formed request that fails business validation (e.g., unsupported file type). |
| `500 Internal Server Error` | Unexpected server-side failure; must be logged internally with full detail. |

**Pagination (Future)**
- When endpoints return lists that may grow large (e.g., paper history), pagination parameters (page number, page size) must be added following a consistent query-parameter convention before the endpoint is considered production-ready — this must not be retrofitted inconsistently per endpoint.

**Rule**: All endpoints must follow this response shape. No endpoint may invent its own ad hoc response format.

---

## 7. Error Handling

- **Every** operation that can fail (file I/O, network calls, third-party API calls, database operations) must be wrapped in explicit error handling — silent failures are prohibited.
- Internal error details (stack traces, exception messages, file paths) must **never** be exposed directly to the frontend or end user.
- Every caught exception must be logged with sufficient context (module, operation, relevant identifiers) via the centralized Logging Module — never silently swallowed.
- User-facing error messages must be clear, actionable, and non-technical (e.g., "This file could not be processed. Please upload a valid PDF." rather than a raw exception message).
- Errors must propagate to a centralized error-handling layer (middleware) rather than being handled inconsistently in each individual route or controller.

---

## 8. Logging Standards

| Level | Usage |
|---|---|
| **DEBUG** | Detailed internal state (e.g., chunk counts, retrieval scores) — enabled only in development environments. |
| **INFO** | Normal operational events (e.g., "upload processed successfully," "query answered"). |
| **WARNING** | Recoverable but noteworthy issues (e.g., a chunk exceeded expected size and was truncated). |
| **ERROR** | Failures that prevented an operation from completing successfully. |

**Rules**
- Log format must be consistent across the codebase: timestamp, severity level, originating module, and message.
- Logs must never include secrets (API keys, credentials) or the full raw content of uploaded documents.
- Log output must be written to `backend/logs/`, never committed to version control.
- Logging verbosity is controlled exclusively via the `LOGGING_LEVEL` environment variable — never hardcoded per module.

---

## 9. Environment Variables

- All environment variables must use `UPPER_SNAKE_CASE` naming (e.g., `GEMINI_API_KEY`, `DATABASE_URL`, `VECTOR_STORE_PATH`).
- Secrets (API keys, database credentials) must **never** be hardcoded anywhere in source code, comments, or committed configuration files.
- All environment variables must be defined in a local `.env` file, which must be listed in `.gitignore` and never committed.
- All required environment variables must be documented (name and purpose, never actual values) in `03_Project_Structure.md` and kept in sync as new variables are introduced.
- The application must fail fast and clearly (not silently) if a required environment variable is missing at startup.

---

## 10. Dependency Rules

- New dependencies (Python or Node.js) must only be added when a genuine functional need exists — not speculatively.
- Every new Python dependency must be immediately recorded in `requirements.txt`; every new Node dependency must be recorded in `package.json`/`package-lock.json` via the standard package manager install process — never installed and left undeclared.
- Dependency versions should be pinned or constrained to known-compatible ranges to ensure reproducible installs across environments.
- Unused dependencies must be removed promptly when no longer referenced anywhere in the codebase — dependency lists must not silently accumulate dead weight.
- Upgrading a major dependency version must be a deliberate, tested, and documented change — never an incidental side effect of an unrelated commit.

---

## 11. Git Standards

**Branch Naming**
- `main` — stable, production-ready code only.
- `develop` — integration branch for completed, tested features.
- `feature/<short-description>` — individual feature branches (e.g., `feature/pdf-chunking`), branched from `develop`.

**Commit Message Format**
- Use a `type: description` format, e.g.:
  - `feat: add PDF text extraction service`
  - `fix: handle empty file upload gracefully`
  - `docs: update API design document`
  - `refactor: extract prompt construction into helper`
  - `test: add unit tests for chunking service`

**Pull Request Guidelines**
- Every merge into `develop` or `main` must go through a pull request — no direct commits to either branch.
- Pull requests must include a clear description of what changed and why, referencing the relevant module or design document.
- Pull requests should be scoped to a single feature or fix — avoid bundling unrelated changes.

**Version Tags**
- Stable, milestone releases must be tagged on `main` using semantic versioning (e.g., `v1.0.0`).

---

## 11B. AI Response Formatting Standard

Every response generated by the AI (via Gemini or any LLM provider) must follow these formatting rules:

| Rule | Description |
|---|---|
| **No Markdown** | Responses must not contain any markdown formatting symbols (`*`, `#`, `-`, `>`, `_`, `` ` ``). |
| **Plain Text Only** | All responses must be plain text with no formatting characters. |
| **Structure** | Use numbered sections (1., 2., 3.) for structure and plain text labels followed by a colon for emphasis. |
| **Professional** | Use clear, direct language. No unnecessary preamble or commentary. |

This applies to all AI-generated content: Q&A answers, paper summaries, and paper comparisons. The prompt files in `backend/services/prompts/` enforce this standard.

---

## 12. Documentation Standards

Every module (service, significant function, or component) must document the following, either as a docstring or accompanying comment block:

- **Purpose** — what problem the module solves.
- **Inputs** — what data/parameters it expects, including type and shape where relevant.
- **Outputs** — what it returns, including type and shape.
- **Dependencies** — what other modules, libraries, or external services it relies on.
- **Exceptions** — what errors it may raise or return, and under what conditions.
- **Future Improvements** — any known limitations or planned enhancements relevant to that module (optional, but encouraged where applicable).

**Rule**: A module without this documentation is not considered complete, regardless of whether it functions correctly (see Section 20, Definition of Done).

---

## 13. Security Rules

- API keys and secrets must never appear in source code, logs, error messages, or version control history.
- Every uploaded PDF must be validated for file type, structural integrity, and size before being processed.
- All user-provided input (queries, filenames, form fields) must be sanitized before use in processing, storage, or display.
- File uploads must be constrained by an explicit maximum size limit, configured centrally, not hardcoded per endpoint.
- Sensitive configuration (database credentials, API keys) must be isolated in environment variables and excluded from version control, per Section 9.
- Error responses must never leak internal system details that could aid an attacker (see Section 6 and 7).

---

## 14. Testing Standards

Every module must include, at minimum:

- **Unit Tests** — verifying the module's core logic in isolation, with dependencies mocked where appropriate.
- **Integration Tests** — verifying that the module functions correctly when combined with the real modules it depends on (e.g., upload → extraction → chunking → embedding).
- **Edge Case Tests** — verifying behavior under unusual but valid input (e.g., an extremely short paper, a paper with no abstract).
- **Failure Tests** — verifying that the module fails gracefully and predictably under invalid input or dependency failure (e.g., corrupted PDF, LLM API timeout).

**Rule**: A pull request introducing new business logic without corresponding tests must not be merged.

---

## 15. Performance Guidelines

- Avoid duplicate processing: a paper's text should be extracted, chunked, and embedded exactly once; results must be persisted and reused, never regenerated redundantly.
- Reuse embeddings: once generated, chunk embeddings must be retrieved from storage for future queries rather than recomputed.
- Optimize prompts: only the most relevant retrieved chunks should be included in LLM prompts — avoid including excessive or redundant context that increases latency and cost without improving answer quality.
- Keep API responses lightweight: return only the data the frontend needs for the current view; avoid returning unnecessarily large payloads.

---

## 16. AI Development Rules

- **Embedding logic and LLM logic must remain separate.** The embedding service must have no knowledge of prompt construction or generation, and vice versa.
- **AI logic must not be mixed with business logic.** Controllers and routes must never call embedding models or the LLM API directly — all AI operations are routed through the RAG Engine and its constituent services.
- **Prompt templates must be centralized** in a single, dedicated location (not scattered inline across multiple functions), so prompt wording and structure can be reviewed and updated consistently.
- **The RAG pipeline must remain modular**: retrieval, context selection, prompt construction, and generation must each be a distinct, independently testable step.
- **The LLM provider must remain replaceable.** All Gemini-specific logic must be isolated behind a single integration module (`gemini_service`), so switching providers requires modifying one file, not logic scattered throughout the codebase.

---

## 17. Backend Rules

- All business logic belongs in `services/` — never in `routes/` or `controllers/`.
- Routes must remain thin: their only responsibility is mapping a URL and HTTP method to the correct controller function.
- Controllers must remain thin: their only responsibility is parsing/validating the request and formatting the response; all actual logic is delegated to services.
- No logic may be duplicated across controllers or services — shared logic belongs in a shared service or `utils/`.
- All configuration (constants, tunable parameters) must be defined centrally in `config/`, never hardcoded inline within a service.

---

## 18. Frontend Rules

- UI elements used in more than one place must be extracted into reusable components under `components/`, not duplicated across pages.
- The application must maintain a consistent visual language (spacing, typography, color usage) across all pages, per the design conventions established in the project.
- All backend communication must go through the centralized `api/` layer — no component or page may call `fetch`/`axios` directly.
- Every asynchronous UI action (upload, query, comparison) must have explicit **loading** and **error** states — a user must never be left looking at an unresponsive or ambiguous UI during or after a failed action.
- The interface must be responsive and usable across common screen sizes (desktop and tablet, at minimum), not designed exclusively for a single fixed viewport.

---

## 19. Future Expansion Rules

All current architectural and coding decisions must preserve a clear extension path for the following future capabilities, without requiring major refactoring when they are eventually implemented:

- **Authentication** — via an isolated middleware layer, not embedded into existing business logic.
- **Cloud Storage** — by keeping file storage access behind a consistent interface within the PDF Processing service, not scattered file-system calls.
- **Multiple LLM Providers** — via the replaceable LLM integration module described in Section 16.
- **Multiple Vector Databases** — via a consistent vector-store service interface, not FAISS-specific calls scattered throughout the RAG Engine.
- **OCR** — as an additional branch within PDF processing, activated when standard extraction yields insufficient text.
- **Citation Generation** — as a new, independent service consuming existing paper metadata.
- **Research Collaboration** — via extension of the existing metadata schema to support shared ownership, not a parallel data model.

**Rule**: Any implementation decision that would make one of the above harder to add later must be flagged and reconsidered before merging.

---

## 20. Definition of Done

No module, feature, or pull request is considered complete unless it satisfies **all** of the following:

- ✓ **Documentation** — purpose, inputs, outputs, dependencies, and exceptions are documented per Section 12.
- ✓ **Error Handling** — all failure modes are explicitly handled per Section 7.
- ✓ **Logging** — relevant operations and errors are logged per Section 8.
- ✓ **Validation** — all inputs are validated before processing.
- ✓ **Testing** — unit, integration, edge case, and failure tests exist per Section 14.
- ✓ **Clean Architecture** — logic is placed in the correct layer per Sections 3, 17, and 18.
- ✓ **Naming Standards** — all files and identifiers follow Sections 4 and 5.
- ✓ **Configuration** — no hardcoded secrets or magic values; all configuration is centralized per Section 9.
- ✓ **Security** — inputs are sanitized and no sensitive data is exposed, per Section 13.
- ✓ **Readability** — code is clear, well-formatted, and understandable without requiring the original author's explanation.

A module that "works" but fails any of the above criteria is **not done**.

---

## Final Engineering Principles

Every contributor — human or AI — must follow these non-negotiable rules throughout the lifetime of this project:

1. **No shortcuts on structure.** Code goes where this document and `03_Project_Structure.md` say it goes — always.
2. **No silent failures.** Every error is caught, logged, and communicated clearly.
3. **No hardcoded secrets, ever.** Configuration lives in environment variables, without exception.
4. **No undocumented modules.** If it isn't documented, it isn't finished.
5. **No untested business logic.** If it isn't tested, it isn't trusted.
6. **No duplicated logic.** If it's written twice, it should have been written once and reused.
7. **No mixing of concerns.** AI logic, business logic, and presentation logic stay in their own lanes.
8. **No breaking the extension path.** Every decision must preserve the future roadmap defined in Section 19.
9. **Consistency over personal preference.** When in doubt, follow the existing pattern in the codebase, not a new one.
10. **This document is binding.** Any deviation must be a deliberate, documented decision — never an oversight.
