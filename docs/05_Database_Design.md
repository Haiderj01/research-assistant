# 05_Database_Design.md

## 1. Purpose of the Database

This document defines the complete data model for the AI Research Assistant, covering both the structured metadata layer (MongoDB) and the vector embedding layer (FAISS). It exists to ensure that data storage decisions are made deliberately and consistently *before* implementation begins, rather than emerging ad hoc as features are built.

**What Should Be Stored Permanently**
- Paper metadata (title, filename, upload timestamp, extracted keywords/datasets/algorithms).
- Chunk metadata (chunk text, position, associated paper, mapping to its vector).
- Chunk embeddings (persisted in FAISS, referenced by chunk metadata).
- Conversation and question/answer history (for user reference and the History feature defined in `01_Project_Overview.md`).
- Generated summaries and comparison reports (so they do not need to be regenerated on every view).

**What Should NOT Be Stored Permanently**
- Raw, unprocessed intermediate text buffers used only during the extraction/chunking pipeline (these are transient and discarded once chunking and embedding are complete).
- Full raw LLM prompts sent to Groq (only the final answer and its source references need to be persisted; the constructed prompt itself is a transient artifact of a single request).
- Temporary upload buffers beyond what is needed for processing, unless the product explicitly requires retaining the original PDF file for later re-download (a decision the system should make deliberately, not by default retaining everything indefinitely).
- Session-only UI state (e.g., which tab is open, in-progress unsent form input) — this belongs in frontend state, never persisted server-side.

This distinction matters because indiscriminately persisting everything increases storage cost, expands the security/privacy surface area, and slows down maintenance; the system should persist only what is needed to power the features defined in the Project Overview.

---

## 2. Database Architecture

The system uses **two distinct, complementary storage systems**, plus file storage and a third-party generation API, each responsible for a different class of data:

```
┌───────────────┐
│  Flask Backend  │
└───────┬───────┘
        │
        ├──────────────────────────────┬───────────────────────────────┬───────────────────────┐
        ▼                              ▼                               ▼                        ▼
┌───────────────────┐      ┌────────────────────────┐      ┌─────────────────────┐   ┌───────────────────┐
│  MongoDB              │      │  FAISS                    │      │  File Storage            │   │  Groq API           │
│  (Structured metadata,  │      │  (Vector embeddings,        │      │  (Raw uploaded PDFs)      │   │  (Answer/summary       │
│  history, summaries)    │      │  similarity search index)    │      │                            │   │  generation — no        │
│                        │      │                            │      │                            │   │  persistent storage)    │
└───────────────────┘      └────────────────────────┘      └─────────────────────┘   └───────────────────┘
```

**Relationships**

- **MongoDB** stores everything structured and queryable: paper records, chunk metadata, conversations, questions, and history. Every chunk record in MongoDB stores a reference (`vector_id`) pointing to its corresponding vector in FAISS.
- **FAISS** stores only the numerical vector embeddings and an internal ID that maps back to the corresponding chunk record in MongoDB. FAISS has no awareness of paper titles, users, or any structured field — it only knows vectors and their IDs.
- **File Storage** holds the original uploaded PDF files on disk (or, in future, in cloud object storage), referenced from MongoDB via a stored file path.
- **Groq API** is not a data store — it is a stateless generation service. The backend sends it a constructed prompt and receives a generated response; nothing is persisted on the Groq side, and the backend is responsible for persisting the final answer in MongoDB if history retention is required.
- **Flask Backend** is the sole coordinator: it is the only component that reads from and writes to all four systems, ensuring that MongoDB and FAISS remain synchronized (see Section 6).

---

## 3. Data Storage Strategy

| Data Type | Storage Location | Rationale |
|---|---|---|
| **Uploaded PDFs** | File Storage (local disk in Version 1; cloud object storage in future) | Raw binary files are not suited to a document or vector database; a file system (or object store) is the natural fit. |
| **Extracted text (raw, pre-chunking)** | Transient (in-memory / temporary processing only) | This is an intermediate artifact of the pipeline; only its downstream chunked form needs to be persisted. |
| **Paper metadata** | MongoDB (`papers` collection) | Structured, queryable fields (title, upload date, extracted keywords) fit MongoDB's document model well. |
| **Chunk metadata** | MongoDB (`chunks` collection) | Chunk text and its structural metadata are queryable/filterable data, distinct from the vector itself. |
| **Embeddings** | FAISS | High-dimensional numerical vectors require a specialized similarity-search index, not a general-purpose document database. |
| **Search/query history** | MongoDB (`search_history` collection) | Structured, chronological records tied to a user and/or paper. |
| **Generated summaries** | MongoDB (`papers` collection, embedded field, or a dedicated `summaries` sub-structure) | Generated content is reused across views and should be cached rather than regenerated on every request. |
| **Conversation history** | MongoDB (`conversations` and `questions` collections) | Structured, ordered exchange of questions and answers tied to a paper or session. |

---

## 4. Collections

### 4.1 `papers`

**Purpose**: Store metadata for every uploaded research paper.

**Fields**
| Field | Type | Description |
|---|---|---|
| `_id` | ObjectId | Unique identifier for the paper. |
| `title` | String | Extracted or user-provided paper title. |
| `filename` | String | Original uploaded filename. |
| `file_path` | String | Path to the stored PDF file (local or cloud). |
| `upload_date` | DateTime | Timestamp of upload. |
| `page_count` | Integer | Number of pages in the PDF. |
| `status` | String (enum) | Processing status: `pending`, `processing`, `processed`, `failed`. |
| `keywords` | Array[String] | Extracted keywords. |
| `datasets` | Array[String] | Extracted dataset names. |
| `algorithms` | Array[String] | Extracted algorithm/method names. |
| `summary` | String | Cached generated summary of the paper. |
| `user_id` | ObjectId (nullable) | Reference to the owning user (future authentication). |

**Relationships**: One `papers` document relates to many `chunks` documents (one-to-many), and many `search_history`/`conversations` documents may reference it.

**Indexes**: Index on `upload_date` (for recency sorting), index on `status` (for filtering unprocessed/failed papers), text index on `title` and `keywords` (for basic lexical lookup independent of semantic search).

**Validation Rules**: `title` and `filename` are required; `status` must be one of the defined enum values; `file_path` must be a non-empty string referencing an existing stored file.

---

### 4.2 `chunks`

**Purpose**: Store the segmented text chunks derived from each paper, along with a reference to their corresponding FAISS vector.

**Fields**
| Field | Type | Description |
|---|---|---|
| `_id` | ObjectId | Unique identifier for the chunk. |
| `paper_id` | ObjectId | Reference to the parent `papers` document. |
| `chunk_text` | String | The actual text content of the chunk. |
| `chunk_index` | Integer | Sequential position of the chunk within the paper. |
| `page_number` | Integer (nullable) | Approximate page number the chunk originates from. |
| `vector_id` | Integer/String | Identifier mapping this chunk to its embedding in FAISS. |
| `created_at` | DateTime | Timestamp of chunk creation. |

**Relationships**: Many `chunks` belong to one `papers` document (many-to-one). Each `chunks` document maps to exactly one vector in FAISS (one-to-one).

**Indexes**: Index on `paper_id` (to retrieve all chunks for a given paper efficiently), index on `vector_id` (to resolve FAISS search results back to their source chunk quickly).

**Validation Rules**: `paper_id` must reference an existing `papers` document; `chunk_text` must be non-empty; `vector_id` must be unique across the collection.

---

### 4.3 `conversations`

**Purpose**: Represent a logical conversation thread, potentially spanning multiple questions, tied to one or more papers.

**Fields**
| Field | Type | Description |
|---|---|---|
| `_id` | ObjectId | Unique identifier for the conversation. |
| `paper_ids` | Array[ObjectId] | Paper(s) this conversation is scoped to. |
| `title` | String | Optional display title for the conversation (e.g., auto-generated from the first question). |
| `created_at` | DateTime | Timestamp of conversation creation. |
| `updated_at` | DateTime | Timestamp of the most recent activity. |
| `user_id` | ObjectId (nullable) | Reference to the owning user (future authentication). |

**Relationships**: One `conversations` document relates to many `questions` documents (one-to-many); references one or more `papers` documents (many-to-many).

**Indexes**: Index on `updated_at` (for recency sorting in the History view), index on `user_id` (future, for per-user filtering).

**Validation Rules**: `paper_ids` must reference existing `papers` documents; must contain at least one paper ID.

---

### 4.4 `questions`

**Purpose**: Store each individual question asked and its generated answer within a conversation.

**Fields**
| Field | Type | Description |
|---|---|---|
| `_id` | ObjectId | Unique identifier for the question/answer pair. |
| `conversation_id` | ObjectId | Reference to the parent `conversations` document. |
| `question_text` | String | The user's submitted question. |
| `answer_text` | String | The generated answer. |
| `source_chunk_ids` | Array[ObjectId] | References to the `chunks` used to generate the answer. |
| `created_at` | DateTime | Timestamp of the question/answer exchange. |

**Relationships**: Many `questions` belong to one `conversations` document (many-to-one); references many `chunks` documents (many-to-many, via `source_chunk_ids`).

**Indexes**: Index on `conversation_id` (to retrieve all questions in a conversation, ordered by `created_at`).

**Validation Rules**: `conversation_id` must reference an existing `conversations` document; `question_text` must be non-empty.

---

### 4.5 `users` (Future)

**Purpose**: Store user account information once authentication is introduced.

**Fields**
| Field | Type | Description |
|---|---|---|
| `_id` | ObjectId | Unique identifier for the user. |
| `email` | String | User's email address (unique). |
| `password_hash` | String | Hashed password (never stored in plaintext). |
| `created_at` | DateTime | Account creation timestamp. |
| `role` | String (enum) | E.g., `student`, `researcher`, `professor`, `admin` (future, optional). |

**Relationships**: One `users` document relates to many `papers`, `conversations`, and `search_history` documents (one-to-many, once `user_id` foreign keys are activated).

**Indexes**: Unique index on `email`.

**Validation Rules**: `email` must be unique and valid; `password_hash` must never be the raw password.

---

### 4.6 `search_history`

**Purpose**: Track semantic search / query events for the History feature and future analytics.

**Fields**
| Field | Type | Description |
|---|---|---|
| `_id` | ObjectId | Unique identifier for the search history entry. |
| `query_text` | String | The raw query submitted by the user. |
| `paper_ids` | Array[ObjectId] | Paper(s) the query was scoped to. |
| `result_chunk_ids` | Array[ObjectId] | Chunks retrieved as most relevant for this query. |
| `created_at` | DateTime | Timestamp of the search event. |
| `user_id` | ObjectId (nullable) | Reference to the user who performed the search (future). |

**Relationships**: References many `papers` and `chunks` documents (many-to-many).

**Indexes**: Index on `created_at` (recency), index on `user_id` (future, per-user filtering).

**Validation Rules**: `query_text` must be non-empty.

---

### 4.7 `settings` (Future)

**Purpose**: Store user- or system-level configurable preferences (e.g., default chunk size, preferred LLM provider, theme preference).

**Fields**
| Field | Type | Description |
|---|---|---|
| `_id` | ObjectId | Unique identifier for the settings record. |
| `user_id` | ObjectId (nullable) | Reference to the owning user, or null for global/system defaults. |
| `key` | String | Setting name (e.g., `preferred_llm_provider`). |
| `value` | Mixed | Setting value. |
| `updated_at` | DateTime | Timestamp of last modification. |

**Relationships**: Many `settings` documents may belong to one `users` document (many-to-one), or none (system defaults).

**Indexes**: Compound index on `(user_id, key)` for fast lookup.

**Validation Rules**: `key` must be non-empty and drawn from a recognized set of supported setting names.

---

## 5. Entity Relationships

```
┌──────────────┐          1        ┌──────────────┐        1          ┌──────────────┐
│    users        │ ─────────────────▶ │    papers        │ ─────────────────▶ │    chunks        │
│ (future)        │        (owns)     │                  │      (contains)     │                  │
└──────┬────────┘                    └──────┬───────┘                    └──────┬───────┘
       │ 1                                  │ M                                 │ 1
       │                                    │                                   │
       │ M                                  │ M                                 │ M
       ▼                                    ▼                                   ▼
┌──────────────┐          1        ┌──────────────┐                    ┌──────────────┐
│ conversations   │ ─────────────────▶ │  questions       │ ───────────────────▶ │  (source_chunk_ids)│
│                  │     (contains)    │                  │   references chunks   │  → chunks         │
└──────┬────────┘                    └──────────────┘                    └──────────────┘
       │ M
       │
       ▼
┌──────────────┐
│ search_history  │
│ (references     │
│  papers/chunks)  │
└──────────────┘
```

**Relationship Summary**
- A `user` (future) owns many `papers`, `conversations`, and `search_history` entries.
- A `paper` contains many `chunks` (one-to-many).
- A `conversation` is scoped to one or more `papers` and contains many `questions` (one-to-many).
- A `question` references the specific `chunks` used as source material for its answer (many-to-many, via ID array).
- A `search_history` entry references the `papers` searched and the `chunks` returned as results.

---

## 6. FAISS Storage Design

**What Is Stored in FAISS**
FAISS stores exclusively the **numerical vector embeddings** generated for each text chunk, along with an internal integer index position for each vector. FAISS has no concept of paper titles, text content, or any other structured metadata — it is purely a similarity-search index over vectors.

**Metadata Mapping**
Because FAISS only knows vectors and internal index positions, a mapping must be maintained between each FAISS vector's index position and the corresponding `chunks._id` in MongoDB. This mapping is the critical link that allows a similarity search result (a list of vector index positions) to be resolved back into actual chunk text and paper context. This mapping is stored either as a side file (e.g., an ID-mapping array persisted alongside the FAISS index) or via FAISS's built-in ID-mapping index types, ensuring every vector can be traced back to its MongoDB chunk record.

**Index Persistence**
The FAISS index is serialized to disk (within `backend/vector_store/`, per `03_Project_Structure.md`) after every batch of new embeddings is added, ensuring that the index survives application restarts. The corresponding ID-mapping file is persisted alongside it and must always be updated in the same operation as the index itself, to prevent drift between the two.

**File Organization**
```
backend/vector_store/
├── index.faiss          # Serialized FAISS index (the vectors themselves)
└── id_mapping.json       # Maps FAISS internal vector IDs → MongoDB chunk _id values
```

**Synchronization with MongoDB**
MongoDB and FAISS must always remain consistent with one another, since each depends on the other for a complete picture of the data (MongoDB holds the meaning/content; FAISS holds the searchable vector). The following rules govern synchronization:
- A chunk is only considered fully "processed" once **both** its MongoDB record and its corresponding FAISS vector have been successfully written; if either write fails, the operation must be treated as failed and retried, not left in a partially completed state.
- Deleting a paper must remove its chunks from MongoDB **and** remove (or mark as invalid) their corresponding vectors in FAISS — an orphaned vector with no MongoDB record must never be searchable, and an orphaned MongoDB chunk with no vector must never be assumed searchable.
- Because FAISS does not support efficient in-place deletion in all index types, a common approach is to mark deleted chunks in MongoDB and periodically rebuild the FAISS index excluding deleted entries, rather than attempting real-time deletion within FAISS itself.

---

## 7. Data Lifecycle

1. **Upload**: A user uploads a PDF; a `papers` document is created with `status: pending`, and the raw file is written to File Storage.
2. **Processing**: The PDF Processing Module extracts text; `status` is updated to `processing`.
3. **Chunking & Embedding**: Extracted text is chunked and embedded; `chunks` documents are created in MongoDB, and corresponding vectors are added to FAISS with synchronized ID mappings.
4. **Ready**: Once all chunks are successfully persisted in both MongoDB and FAISS, the `papers` document's `status` is updated to `processed`.
5. **Active Use**: The user queries the paper; `questions`, `conversations`, and `search_history` records accumulate as the user interacts with the system.
6. **Update (rare)**: If a paper needs reprocessing (e.g., due to an extraction bug fix), its existing `chunks` and corresponding FAISS vectors are invalidated/removed and regenerated, rather than accumulating duplicates.
7. **Deletion**: If a user deletes a paper, its `papers` document, all associated `chunks` documents, all referencing FAISS vectors (via the rebuild process described in Section 6), and its raw file in File Storage are all removed. Associated `questions`/`conversations`/`search_history` entries should either be deleted or retained with a "referenced paper deleted" indicator, depending on product requirements — this decision must be made explicitly, not left ambiguous.
8. **Retention**: Data not explicitly deleted by the user persists indefinitely in Version 1; future versions may introduce configurable retention policies (e.g., auto-purging old search history) as part of the Settings expansion described in Section 4.7.

---

## 8. CRUD Operations

| Collection | Create | Read | Update | Delete |
|---|---|---|---|---|
| `papers` | On upload. | On dashboard load, paper detail view, comparison selection. | On reprocessing, or when summary/keywords are (re)generated. | On explicit user deletion (cascades to chunks, FAISS vectors, file storage). |
| `chunks` | During chunking/embedding pipeline. | During retrieval (by `paper_id` or `vector_id` lookup). | Rare; only during reprocessing. | On paper deletion, or during reprocessing (old chunks removed before new ones are created). |
| `conversations` | When a user starts a new question thread. | On history view, on continuing an existing conversation. | On new question added (`updated_at` refreshed). | On explicit user deletion of a conversation. |
| `questions` | On every question submitted. | When loading a conversation's full history. | Not typically updated once created (append-only). | On conversation deletion (cascade), or individual removal if supported. |
| `users` (future) | On registration. | On login, profile view. | On profile edit, password change. | On account deletion (cascades per data-retention policy). |
| `search_history` | On every search/query event. | On history view, on analytics aggregation. | Not typically updated. | On explicit user clearing of history, or retention-policy-driven purge. |
| `settings` (future) | On first preference set. | On application load (to apply preferences). | On preference change. | On reset-to-default action. |

---

## 9. Indexing Strategy

| Collection | Recommended Index | Purpose |
|---|---|---|
| `papers` | `upload_date` (descending) | Fast recency-sorted dashboard listing. |
| `papers` | `status` | Fast filtering of pending/failed papers for monitoring. |
| `papers` | Text index on `title`, `keywords` | Basic lexical lookup independent of semantic/FAISS search. |
| `chunks` | `paper_id` | Fast retrieval of all chunks belonging to a given paper. |
| `chunks` | `vector_id` (unique) | Fast resolution of FAISS search results back to MongoDB chunk records. |
| `conversations` | `updated_at` (descending) | Fast recency-sorted history listing. |
| `questions` | `conversation_id` | Fast retrieval of all questions within a conversation, in order. |
| `search_history` | `created_at` (descending) | Fast recency-sorted history/analytics queries. |
| `users` (future) | `email` (unique) | Enforce uniqueness and support fast login lookup. |
| `settings` (future) | Compound `(user_id, key)` | Fast lookup of a specific setting for a specific user. |

**Rule**: Every index must be justified by an actual query pattern used in the application — indexes must not be added speculatively, since each index adds write overhead.

---

## 10. Scalability Considerations

- **Thousands of Papers**: MongoDB's document model and indexing scale horizontally well beyond thousands of records; the primary scaling concern is the FAISS index, which grows linearly with the number of chunks. At larger scale, FAISS's index type can be upgraded from an exact search structure to an approximate nearest-neighbor structure (e.g., IVF-based indexes) to maintain fast query times as the vector count grows.
- **Sharding metadata by paper collection**: If the system grows to support many independent users or teams, MongoDB collections can be partitioned (e.g., via sharding on `user_id`) to distribute load across multiple database nodes.
- **Vector store partitioning**: For very large deployments, a single FAISS index may be replaced by multiple indexes partitioned by user, team, or subject domain, reducing the search space per query and improving performance.
- **Read/write separation**: As read volume (dashboard views, history queries) grows relative to write volume (new uploads), MongoDB read replicas can be introduced to distribute read load without affecting write performance.
- **Migration path**: Because all vector-store access is isolated behind a single service interface (per `03_Project_Structure.md` and `04_Technology_Stack.md`), migrating from local FAISS to a distributed/managed vector database (e.g., Milvus, Weaviate) at scale requires changes only within that service, not throughout the codebase.

---

## 11. Backup and Recovery

- **MongoDB Backups**: Regular scheduled backups (e.g., daily snapshots) of all collections should be taken and stored in a location separate from the primary database, ensuring metadata and history can be restored in the event of data loss or corruption.
- **FAISS Index Backups**: The serialized FAISS index file and its accompanying ID-mapping file must be backed up together, on the same schedule, since they are only valid as a consistent pair — restoring one without the other would produce a broken mapping.
- **File Storage Backups**: Uploaded PDF files should be included in the backup schedule, or, in a future cloud-storage configuration, rely on the durability guarantees of the chosen cloud object storage provider.
- **Recovery Procedure**: In the event of data loss, MongoDB collections and the FAISS index/mapping pair should be restored together from the same backup timestamp to guarantee consistency between chunk metadata and their corresponding vectors; restoring only one system independently risks the same orphaned-data problem described in Section 6.
- **Disaster Recovery Testing**: Backup restoration should be periodically tested (not merely assumed to work) to ensure the recovery procedure is valid and complete.

---

## 12. Security Considerations

- **Data Validation**: Every document written to MongoDB must be validated against its defined schema (Section 4) before persistence, rejecting malformed or incomplete records rather than silently storing them.
- **File Safety**: Uploaded PDFs must be validated for file type and structural integrity before being written to File Storage or processed, per the security rules defined in `PROJECT_RULES.md`.
- **Access Control**: Even in Version 1 (prior to full authentication), the data model should associate records with a `user_id` field (nullable for now) so that access-control logic can be introduced later without a schema migration.
- **Sensitive Data Minimization**: Only the data necessary for the system's features (Section 1) should be persisted; raw prompts, full LLM request payloads, and other non-essential intermediate artifacts should not be stored.
- **Credential Protection**: MongoDB connection strings and any FAISS-related configuration (e.g., storage paths) must be supplied via environment variables, never hardcoded, per `PROJECT_RULES.md`.
- **Query Injection Prevention**: All queries against MongoDB must use parameterized query construction (via the database driver's standard query-building interface) rather than string-concatenated queries, to prevent injection-style vulnerabilities.

---

## 13. Future Database Expansion

- **Authentication**: The `users` collection (Section 4.5) and the `user_id` fields already present across `papers`, `conversations`, and `search_history` provide a ready foreign-key structure for enforcing per-user data ownership once authentication is implemented — no schema redesign is required, only activation of existing fields.
- **Teams/Collaboration**: A future `teams` collection could be introduced, with `papers` and `conversations` gaining an additional optional `team_id` field, enabling shared ownership without disrupting the existing single-owner (`user_id`) model.
- **Cloud Storage**: The `file_path` field in `papers` is already an abstract reference rather than a hardcoded local path, meaning it can transparently point to a cloud object storage URL in the future without changing the surrounding schema.
- **Analytics**: The existing `search_history` and `questions` collections already capture the raw event data needed to power future research-trend analytics (Section 5 of `01_Project_Overview.md`); a future `analytics` aggregation layer can be built on top of this existing data without requiring new raw data collection to be retrofitted.
- **Settings Expansion**: The `settings` collection (Section 4.7) is designed to accommodate arbitrary key-value preferences, allowing new configurable behaviors (e.g., default LLM provider, chunk size preference) to be added without further schema changes.

---

## 14. Database Summary

This database design deliberately separates two fundamentally different kinds of data into two purpose-built storage systems: **MongoDB** for structured, queryable metadata and history, and **FAISS** for high-dimensional vector embeddings requiring specialized similarity search. This separation is not incidental — it reflects the fact that no single database technology efficiently serves both access patterns, as established in `04_Technology_Stack.md`.

The schema defined in this document — `papers`, `chunks`, `conversations`, `questions`, and their future extensions (`users`, `search_history`, `settings`) — provides a complete, normalized foundation for every feature described in `01_Project_Overview.md`, from question answering and summarization to comparison and search history, while explicitly reserving extension points (nullable `user_id` fields, abstracted file paths, a flexible settings model) for authentication, collaboration, and cloud storage without requiring future schema migrations.

Combined with the explicit synchronization rules between MongoDB and FAISS (Section 6) and the lifecycle rules governing creation, update, and deletion (Section 7), this design ensures the two storage systems remain consistent with one another at all times — a critical property for a system whose core value depends on every retrievable vector correctly resolving back to real, accurate paper content.
