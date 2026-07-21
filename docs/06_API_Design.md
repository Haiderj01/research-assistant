# 06_API_Design.md

## 1. Purpose

Finalizing the API contract before implementation begins ensures that the frontend and backend can be developed in parallel, against a shared, agreed-upon specification, rather than being tightly coupled to whatever the backend happens to return at any given moment. A well-defined API specification serves as a binding agreement between the two sides of the system: the frontend team can build UI components against a known response shape before the backend logic is even fully implemented, and the backend team can implement endpoints without needing to guess what the frontend expects.

Finalizing the API contract early also surfaces design problems before they become expensive to fix — inconsistent response formats, missing validation rules, or ambiguous error handling are far cheaper to correct on paper than after both sides of the system have been built around a flawed assumption. This document, together with `05_Database_Design.md`, defines the complete data contract of the system: what goes in, what comes out, and under what conditions each operation succeeds or fails.

---

## 2. API Design Principles

| Principle | Explanation |
|---|---|
| **REST** | The API is organized around resources (papers, questions, history) and standard HTTP verbs (GET, POST, DELETE) that operate on them, following conventional REST semantics rather than a single generic RPC-style endpoint. |
| **Stateless Communication** | Each request contains all the information the backend needs to process it; the server does not rely on stored session state between requests, making the API predictable and horizontally scalable. |
| **JSON** | All request and response bodies use JSON as the exchange format, except for the binary PDF upload payload itself (sent as multipart form data). |
| **Consistency** | Every endpoint follows the same response structure, naming conventions, and error format, defined in Section 6, regardless of which module it belongs to. |
| **Error Handling** | Every endpoint returns errors in a predictable, structured format with an appropriate HTTP status code, never a raw stack trace or ambiguous failure. |
| **Validation** | Every endpoint validates its input before performing any processing, rejecting invalid requests early with a clear `400`-class response rather than allowing invalid data to propagate into business logic. |

---

## 3. API Architecture

```
┌───────────────┐
│  React Frontend │
└───────┬───────┘
        │  HTTPS / JSON (REST)
        ▼
┌───────────────────┐
│   Flask Backend      │
│   (API Layer)         │
└───────┬───────────┘
        │
        ▼
┌───────────────────┐
│   AI Modules           │
│  (PDF Processing,      │
│   Chunking, Embedding,  │
│   RAG Engine)            │
└───────┬───────────┘
        │
   ┌────┴─────────────────┬─────────────────────┐
   ▼                       ▼                       ▼
┌───────────┐     ┌───────────────┐      ┌───────────────┐
│  MongoDB     │     │   FAISS          │      │  Gemini API      │
│ (metadata,    │     │ (vector search)   │      │ (generation)      │
│  history)     │     │                    │      │                    │
└───────────┘     └───────────────┘      └───────────────┘
```

**Flow Explanation**: The React Frontend never communicates directly with MongoDB, FAISS, or Gemini — every request passes through the Flask Backend, which is the sole orchestrator of the AI Modules and the sole client of the underlying data stores and external API. This ensures a single, consistent point of validation, error handling, and business logic enforcement, consistent with the layered architecture defined in `02_System_Architecture.md`.

---

## 4. API Modules

| Module | Responsibility |
|---|---|
| **Paper Management** | Uploading, processing, listing, retrieving, and deleting research papers. |
| **Question Answering** | Submitting natural-language questions and receiving grounded answers. |
| **Summarization & Comparison** | Generating paper summaries and multi-paper comparisons. |
| **History** | Retrieving past questions, conversations, and search activity. |
| **Analytics** | Retrieving dashboard statistics and research trend data. |
| **Health Check** | Verifying system availability and readiness. |

---

## 5. Endpoint Specifications

### 5.1 `POST /upload`

**Purpose**: Upload one or more PDF research papers for processing.

**HTTP Method**: `POST`

**URL**: `/upload`

**Request Body** (multipart/form-data):
| Field | Type | Required | Description |
|---|---|---|---|
| `files` | File[] | Yes | One or more PDF files to upload. |

**Response Body** (`201 Created`):
| Field | Type | Description |
|---|---|---|
| `success` | Boolean | Indicates upload acceptance. |
| `data.papers` | Array[Object] | List of created paper records, each including `id`, `title`, `status`. |

**Status Codes**
| Code | Meaning |
|---|---|
| `201` | Files accepted and queued for processing. |
| `400` | No files provided, or an unsupported file type submitted. |
| `413` | File(s) exceed the configured maximum size limit. |
| `500` | Unexpected server error during upload handling. |

**Validation Rules**: Only `.pdf` files are accepted; each file must not exceed the configured maximum size; at least one file must be present in the request.

**Possible Errors**: Corrupted or unreadable PDF; unsupported file extension; storage write failure.

---

### 5.2 `POST /process`

**Purpose**: Trigger (or re-trigger) the extraction, chunking, and embedding pipeline for a previously uploaded paper.

**HTTP Method**: `POST`

**URL**: `/process`

**Request Body** (JSON):
| Field | Type | Required | Description |
|---|---|---|---|
| `paper_id` | String | Yes | The ID of the paper to process. |

**Response Body** (`200 OK`):
| Field | Type | Description |
|---|---|---|
| `success` | Boolean | Indicates processing was triggered successfully. |
| `data.paper_id` | String | The processed paper's ID. |
| `data.status` | String | Updated processing status (e.g., `processing`, `processed`). |

**Status Codes**
| Code | Meaning |
|---|---|
| `200` | Processing completed or successfully triggered. |
| `404` | No paper found with the given `paper_id`. |
| `422` | The paper's file could not be processed (e.g., no extractable text). |
| `500` | Unexpected server error during processing. |

**Validation Rules**: `paper_id` must be a valid, existing identifier.

**Possible Errors**: Text extraction yields no usable content (e.g., scanned PDF); embedding generation failure; FAISS write failure.

---

### 5.3 `POST /ask`

**Purpose**: Submit a natural-language question and receive a grounded answer generated from one or more uploaded papers.

**HTTP Method**: `POST`

**URL**: `/ask`

**Request Body** (JSON):
| Field | Type | Required | Description |
|---|---|---|---|
| `question` | String | Yes | The user's natural-language question. |
| `paper_ids` | Array[String] | Yes | The paper(s) to scope the question to. |
| `conversation_id` | String | No | Existing conversation to append this exchange to; a new conversation is created if omitted. |

**Response Body** (`200 OK`):
| Field | Type | Description |
|---|---|---|
| `success` | Boolean | Indicates the question was answered successfully. |
| `data.answer` | String | The generated answer. |
| `data.sources` | Array[Object] | Referenced chunks/papers used to ground the answer. |
| `data.conversation_id` | String | The conversation this exchange belongs to. |

**Status Codes**
| Code | Meaning |
|---|---|
| `200` | Answer generated successfully. |
| `400` | Missing question text or empty `paper_ids`. |
| `404` | One or more referenced papers do not exist. |
| `422` | Referenced paper(s) are not yet fully processed. |
| `502` | The LLM (Gemini) API failed or timed out. |
| `500` | Unexpected server error. |

**Validation Rules**: `question` must be a non-empty string within a reasonable length limit; `paper_ids` must reference existing, fully processed papers.

**Possible Errors**: No relevant chunks found for the question; Gemini API rate limit or timeout; malformed LLM response.

---

### 5.4 `GET /papers`

**Purpose**: Retrieve the list of all uploaded papers.

**HTTP Method**: `GET`

**URL**: `/papers`

**Request Body**: None (optional query parameters: `status`, `sort`).

**Response Body** (`200 OK`):
| Field | Type | Description |
|---|---|---|
| `success` | Boolean | Indicates successful retrieval. |
| `data.papers` | Array[Object] | List of paper summaries (`id`, `title`, `upload_date`, `status`). |

**Status Codes**
| Code | Meaning |
|---|---|
| `200` | Papers retrieved successfully (including an empty list). |
| `500` | Unexpected server error. |

**Validation Rules**: Optional `status` query parameter, if present, must be one of the recognized status values.

**Possible Errors**: Database connectivity failure.

---

### 5.5 `GET /paper/{id}`

**Purpose**: Retrieve full details for a single paper, including metadata and cached summary.

**HTTP Method**: `GET`

**URL**: `/paper/{id}`

**Request Body**: None.

**Response Body** (`200 OK`):
| Field | Type | Description |
|---|---|---|
| `success` | Boolean | Indicates successful retrieval. |
| `data.paper` | Object | Full paper record including `title`, `keywords`, `datasets`, `algorithms`, `summary`, `status`. |

**Status Codes**
| Code | Meaning |
|---|---|
| `200` | Paper found and returned. |
| `404` | No paper exists with the given `id`. |
| `500` | Unexpected server error. |

**Validation Rules**: `id` must be a well-formed identifier.

**Possible Errors**: Invalid ID format; database lookup failure.

---

### 5.6 `DELETE /paper/{id}`

**Purpose**: Delete a paper and all associated data (chunks, vectors, file, and optionally related history).

**HTTP Method**: `DELETE`

**URL**: `/paper/{id}`

**Request Body**: None.

**Response Body** (`200 OK`):
| Field | Type | Description |
|---|---|---|
| `success` | Boolean | Indicates successful deletion. |
| `data.deleted_id` | String | The ID of the deleted paper. |

**Status Codes**
| Code | Meaning |
|---|---|
| `200` | Paper and associated data deleted successfully. |
| `404` | No paper exists with the given `id`. |
| `500` | Unexpected server error during deletion. |

**Validation Rules**: `id` must reference an existing paper.

**Possible Errors**: Partial deletion failure (e.g., MongoDB record removed but FAISS vectors not yet cleaned up) — must be handled per the synchronization rules in `05_Database_Design.md`.

---

### 5.7 `GET /history`

**Purpose**: Retrieve past conversations and/or search history for display in the History view.

**HTTP Method**: `GET`

**URL**: `/history`

**Request Body**: None (optional query parameters: `limit`, `offset`, `paper_id`).

**Response Body** (`200 OK`):
| Field | Type | Description |
|---|---|---|
| `success` | Boolean | Indicates successful retrieval. |
| `data.conversations` | Array[Object] | List of past conversations, each with `id`, `title`, `updated_at`, `paper_ids`. |

**Status Codes**
| Code | Meaning |
|---|---|
| `200` | History retrieved successfully (including an empty list). |
| `500` | Unexpected server error. |

**Validation Rules**: `limit`/`offset`, if provided, must be valid non-negative integers.

**Possible Errors**: Database connectivity failure.

---

### 5.8 `GET /health`

**Purpose**: Verify that the backend service and its critical dependencies (MongoDB, FAISS index availability) are operational.

**HTTP Method**: `GET`

**URL**: `/health`

**Request Body**: None.

**Response Body** (`200 OK`):
| Field | Type | Description |
|---|---|---|
| `success` | Boolean | Overall health status. |
| `data.database` | String | `"connected"` or `"unavailable"`. |
| `data.vector_store` | String | `"available"` or `"unavailable"`. |

**Status Codes**
| Code | Meaning |
|---|---|
| `200` | System is healthy. |
| `503` | One or more critical dependencies are unavailable. |

**Validation Rules**: None (no input).

**Possible Errors**: Database unreachable; vector store file inaccessible.

---

### 5.9 `POST /summarize`

**Purpose**: Generate (or retrieve a cached) summary for a single paper.

**HTTP Method**: `POST`

**URL**: `/summarize`

**Request Body** (JSON):
| Field | Type | Required | Description |
|---|---|---|---|
| `paper_id` | String | Yes | The paper to summarize. |
| `force_regenerate` | Boolean | No | If true, regenerates the summary even if a cached version exists. |

**Response Body** (`200 OK`):
| Field | Type | Description |
|---|---|---|
| `success` | Boolean | Indicates successful summary generation. |
| `data.summary` | String | The generated summary text. |

**Status Codes**
| Code | Meaning |
|---|---|
| `200` | Summary generated or retrieved successfully. |
| `404` | Paper not found. |
| `422` | Paper is not yet fully processed. |
| `502` | LLM generation failure. |
| `500` | Unexpected server error. |

**Validation Rules**: `paper_id` must reference an existing, fully processed paper.

**Possible Errors**: LLM timeout; insufficient chunk content to summarize.

---

### 5.10 `POST /compare`

**Purpose**: Generate a structured comparison across two or more papers.

**HTTP Method**: `POST`

**URL**: `/compare`

**Request Body** (JSON):
| Field | Type | Required | Description |
|---|---|---|---|
| `paper_ids` | Array[String] | Yes | The papers to compare (minimum two). |
| `dimensions` | Array[String] | No | Specific comparison dimensions requested (e.g., `dataset`, `method`, `results`); defaults to a standard set if omitted. |

**Response Body** (`200 OK`):
| Field | Type | Description |
|---|---|---|
| `success` | Boolean | Indicates successful comparison generation. |
| `data.comparison_table` | Array[Object] | Structured comparison rows, one per dimension, with values per paper. |

**Status Codes**
| Code | Meaning |
|---|---|
| `200` | Comparison generated successfully. |
| `400` | Fewer than two `paper_ids` provided. |
| `404` | One or more referenced papers do not exist. |
| `422` | One or more papers are not yet fully processed. |
| `502` | LLM generation failure. |
| `500` | Unexpected server error. |

**Validation Rules**: `paper_ids` must contain at least two valid, existing, fully processed paper IDs.

**Possible Errors**: LLM timeout; insufficient comparable content across selected papers.

---

## 6. Standard Response Format

All endpoints return a consistent JSON response envelope.

**Success Response Shape**
| Field | Type | Description |
|---|---|---|
| `success` | Boolean | Always `true` for successful responses. |
| `data` | Object | The endpoint-specific payload. |
| `message` | String (optional) | A human-readable confirmation message, where useful. |

**Error Response Shape**
| Field | Type | Description |
|---|---|---|
| `success` | Boolean | Always `false` for error responses. |
| `error.code` | String | A short, machine-readable error identifier (e.g., `INVALID_FILE_TYPE`, `PAPER_NOT_FOUND`). |
| `error.message` | String | A clear, human-readable description of what went wrong, safe for display to the end user. |

**Rule**: No endpoint may deviate from this envelope structure. No response may include raw internal exception text, stack traces, or implementation details, consistent with the error-handling standards defined in `PROJECT_RULES.md`.

---

## 7. Authentication Strategy

Version 1 of the API does not implement authentication; all endpoints are currently accessible without a login step, consistent with the defined Version 1 scope in `01_Project_Overview.md`. However, the API is designed to support authentication without requiring a redesign:

- Every resource-owning collection (`papers`, `conversations`, `search_history`) already includes a nullable `user_id` field, per `05_Database_Design.md`, ready to be populated once authentication is introduced.
- Future authentication will use a token-based approach (e.g., JWT), where the frontend includes a bearer token in the `Authorization` header of every request.
- Once introduced, authentication will be enforced via a dedicated middleware layer (per `03_Project_Structure.md`) applied uniformly across protected endpoints, rather than being checked inconsistently within individual controllers.
- Endpoints such as `/health` will likely remain unauthenticated even after authentication is introduced, since health checks are typically used by infrastructure monitoring tools rather than end users.

---

## 8. Error Handling

- Every error response follows the standard envelope defined in Section 6.
- HTTP status codes are chosen to accurately reflect the nature of the failure (client error vs. server error vs. upstream dependency failure), per the code table established in `PROJECT_RULES.md`.
- Validation errors (missing/malformed fields) always return `400 Bad Request` with a message identifying the specific invalid field.
- Errors originating from an external dependency (e.g., Gemini API failure) are returned as `502 Bad Gateway`, distinguishing them clearly from internal application bugs (`500 Internal Server Error`).
- Every error, regardless of status code, is logged internally with full contextual detail (per the Logging Standards in `PROJECT_RULES.md`), even though that detail is never returned to the client.

---

## 9. API Versioning Strategy

The API will adopt **URL-based versioning** (e.g., `/api/v1/upload`, `/api/v1/ask`) once the system moves beyond initial development, ensuring that future breaking changes (e.g., a redesigned response shape for `/ask`) can be introduced as `/api/v2/...` without disrupting existing frontend clients still targeting `v1`. During initial Version 1 development, the `/v1` prefix may be implicit, but all endpoint paths should be structured so that introducing the explicit version prefix later requires only a routing-level change, not a redesign of controller or service logic. Any breaking change to a response shape, required field, or status code semantics constitutes a new version; purely additive changes (new optional fields) do not require a version bump.

---

## 10. Rate Limiting

Version 1 does not implement rate limiting, but the API is designed to accommodate it in the future, particularly for endpoints that trigger costly downstream operations (`/ask`, `/summarize`, `/compare`), since these invoke the Gemini API and are subject to its own quota constraints. Future rate limiting will likely be applied per user/session (once authentication exists) or per IP address (in the interim), using a sliding-window or token-bucket strategy at the API Layer, returning a `429 Too Many Requests` status code with a clear retry-after indication when a client exceeds its allotted request rate. Rate limiting will be introduced as middleware, consistent with the layered error-handling and validation approach already established, rather than embedded ad hoc within individual endpoint logic.

---

## 11. Security

- **File Validation**: Every file submitted to `/upload` is validated for file type (`.pdf` only), structural integrity, and size before being accepted, per the security rules in `PROJECT_RULES.md` and `05_Database_Design.md`.
- **Request Validation**: Every endpoint validates the shape and content of its request body before any processing begins, rejecting malformed requests with a `400` response rather than allowing invalid data to reach business logic.
- **API Protection**: Endpoints that trigger third-party API calls (`/ask`, `/summarize`, `/compare`) are candidates for future rate limiting (Section 10) to prevent abuse and control cost exposure.
- **Input Sanitization**: User-provided text (questions, comparison dimension names) is sanitized before being included in any downstream prompt construction or persisted to MongoDB.
- **No Sensitive Data Exposure**: Response bodies never include internal file system paths, database connection details, or raw exception content, per the Standard Response Format in Section 6.

---

## 12. Future APIs

The following endpoints are anticipated for Version 2 and beyond, extending the current API without requiring changes to the Version 1 contract:

| Endpoint | Purpose |
|---|---|
| `POST /auth/register` | Register a new user account. |
| `POST /auth/login` | Authenticate a user and issue a token. |
| `GET /trends` | Retrieve research trend analysis across a paper collection. |
| `GET /dashboard` | Retrieve aggregated dashboard statistics (paper counts, recent activity). |
| `POST /report/download` | Generate and return a downloadable report (summary or comparison) as a file. |
| `POST /papers/{id}/reprocess` | Explicitly re-trigger processing for a specific paper (distinct from the general `/process` endpoint). |
| `GET /settings` / `PUT /settings` | Retrieve or update user/system preferences, per the `settings` collection defined in `05_Database_Design.md`. |
| `POST /teams` | Create a shared team workspace, supporting future research collaboration features. |

---

## 13. API Summary

This document defines a complete, consistent REST API contract covering every feature required for Version 1 of the AI Research Assistant: paper upload and processing, question answering, summarization, comparison, history retrieval, and system health monitoring. Every endpoint follows a uniform response envelope, a consistent validation and error-handling approach, and clearly defined status code semantics, ensuring that frontend and backend development can proceed independently against a shared, unambiguous specification.

The design deliberately reserves clear extension points — nullable ownership fields, a versioning strategy, and an explicit list of Version 2 endpoints — so that authentication, rate limiting, analytics, and collaboration features can be added in the future without breaking existing clients or requiring a redesign of the core API contract. Combined with `05_Database_Design.md`, this document completes the full data and communication contract required to begin backend and frontend implementation in parallel.
