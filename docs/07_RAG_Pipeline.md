# 07_RAG_Pipeline.md

## 1. Purpose

It may seem simpler to send an entire research paper's text directly to a Large Language Model along with a user's question, and let the model answer from the full document. In practice, this approach is unreliable and does not scale, for several concrete reasons:

- **Context window limits**: LLMs can only accept a finite amount of text in a single request. A single research paper may fit, but a question spanning 10, 30, or 100 uploaded papers cannot — the combined text would far exceed any practical context window.
- **Cost and latency**: Sending the full text of every uploaded paper on every single question is computationally wasteful and slow; most of that text is irrelevant to any given question, and processing it anyway wastes tokens, time, and money.
- **Precision degradation**: LLMs perform noticeably worse at extracting a specific, narrow answer when it is buried inside a very large amount of irrelevant surrounding text — a phenomenon sometimes described as needing to "find a needle in a haystack."
- **No cross-paper reasoning at scale**: If a user wants to compare or query across dozens of papers, naively concatenating all of them is not feasible even before hitting a hard context limit.

Retrieval-Augmented Generation (RAG) solves these problems by first **finding** only the specific pieces of text that are actually relevant to the user's question, and only then asking the LLM to generate an answer using that focused, relevant context. This document defines the complete RAG pipeline used by the AI Research Assistant — from PDF ingestion to final answer generation — and is intended to be a sufficiently detailed blueprint that an engineer could implement the pipeline directly from this specification.

---

## 2. What is RAG?

**Retrieval-Augmented Generation (RAG)** is an architectural pattern that combines two distinct capabilities — **retrieval** (finding relevant information) and **generation** (producing natural language) — so that an LLM's output is grounded in specific, verifiable source material rather than relying solely on what the model happened to learn during its own training.

| Concept | Explanation |
|---|---|
| **Retrieval** | The process of searching a knowledge base (in this case, the uploaded papers) to find the specific pieces of content most relevant to a given question. |
| **Generation** | The process by which the LLM produces a coherent, natural-language response, typically by continuing/completing a prompt it has been given. |
| **Context** | The specific retrieved text passed to the LLM alongside the user's question, which the LLM is instructed to base its answer on. |
| **Embeddings** | Numerical vector representations of text that capture semantic meaning, allowing pieces of text to be compared for similarity mathematically rather than by exact word matching. |
| **Vector Search** | The process of finding the embeddings most similar (closest in vector space) to a given query embedding, which is how "relevant" content is identified. |
| **LLM (Large Language Model)** | The generative model (Gemini, in this project) responsible for producing the final natural-language answer once given a question and relevant context. |
| **Hallucination Reduction** | A key benefit of RAG: because the LLM is explicitly instructed to answer using only the retrieved context, and that context is drawn from real, verifiable source documents, the model is far less likely to invent facts that have no basis in the actual papers. |

In short: instead of asking an LLM "what do you know about X," RAG asks "here is the specific relevant material — answer the question using only this." This is the foundational technique that makes the AI Research Assistant both scalable (it does not need to process entire paper collections on every question) and trustworthy (answers are grounded in retrievable, citable source text).

---

## 3. High-Level Pipeline

```
                         ┌─────────────┐
                         │  Upload PDF   │
                         └──────┬──────┘
                                ▼
                         ┌─────────────┐
                         │ Extract Text  │
                         └──────┬──────┘
                                ▼
                         ┌─────────────┐
                         │  Clean Text   │
                         └──────┬──────┘
                                ▼
                         ┌─────────────┐
                         │  Chunk Text   │
                         └──────┬──────┘
                                ▼
                         ┌───────────────────┐
                         │ Generate Embeddings  │
                         └──────┬────────────┘
                                ▼
                         ┌─────────────┐
                         │ Store in FAISS │
                         └──────┬──────┘
                                ▼
                    ══════════════════════════
                          (Ingestion Complete)
                    ══════════════════════════
                                │
                                ▼
                         ┌─────────────┐
                         │ User Question  │
                         └──────┬──────┘
                                ▼
                         ┌───────────────────┐
                         │ Question Embedding   │
                         └──────┬────────────┘
                                ▼
                         ┌───────────────────┐
                         │ Similarity Search     │
                         └──────┬────────────┘
                                ▼
                         ┌─────────────┐
                         │ Top-k Chunks   │
                         └──────┬──────┘
                                ▼
                         ┌───────────────────┐
                         │ Prompt Construction   │
                         └──────┬────────────┘
                                ▼
                         ┌─────────────┐
                         │    Gemini      │
                         └──────┬──────┘
                                ▼
                         ┌─────────────┐
                         │    Answer      │
                         └─────────────┘
```

**Stage-by-Stage Explanation**

1. **Upload PDF** — The user submits one or more PDF files through the frontend.
2. **Extract Text** — The system parses each PDF and extracts its raw text content.
3. **Clean Text** — Extracted text is normalized: excess whitespace, page headers/footers, and non-content artifacts are removed.
4. **Chunk Text** — Cleaned text is divided into smaller, semantically coherent segments sized appropriately for embedding (see Section 8).
5. **Generate Embeddings** — Each chunk is passed through the embedding model, producing a numerical vector representing its meaning.
6. **Store in FAISS** — Chunk embeddings are added to the FAISS vector index, with a maintained mapping back to their corresponding chunk metadata in MongoDB (per `05_Database_Design.md`). This completes the one-time ingestion phase for a paper.
7. **User Question** — At query time, the user submits a natural-language question, scoped to one or more uploaded papers.
8. **Question Embedding** — The question is passed through the same embedding model used during ingestion, producing a query vector in the same vector space as the stored chunk embeddings.
9. **Similarity Search** — FAISS searches for the chunk embeddings most similar to the query embedding.
10. **Top-k Chunks** — The most relevant chunks (a fixed number, "k") are selected as the retrieved context.
11. **Prompt Construction** — The retrieved chunks and the user's question are assembled into a structured prompt, following the strategy defined in Section 6.
12. **Gemini** — The constructed prompt is sent to the Gemini LLM, which generates a response grounded in the provided context.
13. **Answer** — The generated answer, along with references to its source chunks, is returned to the user.

---

## 4. Retrieval Phase

The retrieval phase is responsible for identifying which pieces of previously ingested paper content are relevant to a given question, and consists of the following components:

- **Chunking**: As described in Section 8, papers are pre-divided into chunks at ingestion time, since retrieval always operates at the chunk level, not the whole-document level.
- **Embeddings**: Each chunk (and later, each question) is converted into a vector representation that captures its semantic meaning, enabling comparison based on conceptual similarity rather than exact wording.
- **Similarity Search**: Given a question's embedding, the system searches the vector index for the chunk embeddings that are mathematically closest to it (see Section 10).
- **Top-k Retrieval**: Rather than returning every chunk above some similarity threshold, the system retrieves a fixed number of the highest-ranked chunks (commonly denoted "k," e.g., the top 5), balancing completeness of context against prompt size.
- **Context Selection**: The retrieved top-k chunks are assembled, in this project typically ordered by relevance score (and optionally by original document position, for readability), into the context block passed to the LLM.

**Why Retrieval Quality Matters**: The generation phase can only be as good as the context it is given — an LLM cannot answer accurately about content it was never shown. If retrieval returns irrelevant or incomplete chunks, the LLM will either produce a vague, unhelpful answer or, in the worst case, fall back on ungrounded general knowledge, reintroducing the hallucination risk that RAG is specifically designed to prevent. Retrieval is therefore the foundation on which the entire system's accuracy depends, which is why chunking strategy (Section 8), embedding quality (Section 9), and similarity search configuration (Section 10) each receive dedicated design attention in this document.

---

## 5. Generation Phase

Once relevant context has been retrieved, the generation phase produces the final natural-language answer:

- **Prompt Construction**: The retrieved chunks, the user's question, and explicit generation instructions are assembled into a single structured prompt (see Section 6 for the detailed structure).
- **Context Injection**: The retrieved chunk text is inserted into the prompt in a clearly delimited section, distinguishing it from the instructions and the question itself, so the LLM can reliably distinguish "source material" from "task instructions."
- **Gemini Response Generation**: The assembled prompt is submitted to the Gemini API, which produces a generated natural-language response based on the provided context and instructions.
- **Response Formatting**: The raw generated text is processed into the system's standard response shape (per `06_API_Design.md`), attaching source chunk/paper references so the frontend can display which part of which paper the answer was drawn from.

---

## 6. Prompt Engineering Strategy

Prompts sent to Gemini follow a consistent, structured format composed of four conceptual parts:

| Component | Purpose |
|---|---|
| **System Prompt** | Establishes the LLM's role and behavioral constraints — e.g., instructing it to act as a research assistant that answers strictly based on the provided context, and to explicitly state when the provided context does not contain enough information to answer. |
| **Retrieved Context** | The top-k retrieved chunks, clearly delimited (e.g., under a labeled "Context" section), so the model can distinguish source material from instructions. |
| **User Question** | The original natural-language question, presented clearly and separately from the context. |
| **Expected Response Format** | Instructions describing the desired shape of the answer — e.g., a direct answer followed by a brief explanation, or a specific format for summaries and comparisons. |

**Citation Strategy**: Each retrieved chunk carries metadata (paper title, section/page, per `05_Database_Design.md`) that is preserved alongside the chunk text through prompt construction. The system instructs the LLM to reference which source(s) informed each part of its answer, and the backend also independently attaches the actual source chunk/paper metadata to the response (rather than relying solely on the LLM to self-report sources), ensuring users can always trace an answer back to its origin even if the model's own citation behavior is imperfect.

**General Principles**
- The prompt must clearly instruct the model to answer *only* using the provided context, and to say so explicitly if the context is insufficient, rather than filling gaps with outside knowledge.
- Instructions, context, and the question should be visually and structurally separated (e.g., through labeled sections) to reduce the chance of the model conflating instructions with source content.
- Prompts should remain as concise as possible while including all necessary context, since excessive prompt length increases latency and cost without necessarily improving answer quality (see Section 14).

This document intentionally does not include literal prompt text, since prompt wording is an implementation detail to be iterated on during development; the structural principles above are what must be preserved regardless of exact wording.

---

## 7. Hallucination Prevention

Hallucination — an LLM confidently stating something that is not actually supported by its source material — is the central risk RAG is designed to mitigate. The following techniques are used throughout this pipeline to reduce that risk:

- **Strict Context Grounding**: The system prompt explicitly instructs the model to answer only from the retrieved context, and to state clearly when the context does not contain a sufficient answer, rather than guessing.
- **Explicit "Insufficient Context" Handling**: The prompt structure anticipates and instructs for the case where retrieval did not find relevant material, so the model responds with an honest "not found in the provided papers" rather than fabricating a plausible-sounding but ungrounded answer.
- **Source Attribution**: Every answer is paired with the actual retrieved source chunks (attached by the backend, not just claimed by the model), allowing the user to independently verify the answer against the original paper text.
- **Retrieval Quality Controls**: Because hallucination often stems from poor or insufficient retrieved context, improving chunking (Section 8) and similarity search configuration (Section 10) directly reduces hallucination risk at its root cause, rather than only mitigating it at the prompt level.
- **Conservative Top-k Selection**: Retrieving a reasonable, focused number of highly relevant chunks (rather than either too few, risking insufficient context, or too many, risking diluted relevance) supports the model in producing accurate, grounded answers.
- **No Silent Context Truncation**: If the retrieved context combined with the question would exceed the model's practical prompt size, the system should reduce the number of included chunks deliberately (keeping only the most relevant ones) rather than silently truncating context mid-chunk, which could leave partial, misleading information in the prompt.

---

## 8. Chunking Strategy

Chunking determines the granularity at which content is embedded, retrieved, and eventually presented as context to the LLM, making it one of the most consequential design decisions in the pipeline.

| Consideration | Explanation |
|---|---|
| **Chunk Size** | Chunks must be large enough to preserve coherent meaning (a chunk that is too small may lose necessary surrounding context) but small enough to allow precise retrieval (a chunk that is too large dilutes relevance, since only part of it may actually pertain to a given question). A moderate paragraph-to-multi-paragraph sized chunk is generally an appropriate starting point for academic paper text. |
| **Overlap** | Adjacent chunks should share a small amount of overlapping text at their boundaries, preventing important context from being awkwardly split across two chunks in a way that neither one fully captures. |
| **Section Awareness** | Where possible, chunk boundaries should respect the paper's natural structure (paragraph or section breaks) rather than splitting at arbitrary character counts, preserving semantic coherence within each chunk. |
| **Trade-offs** | Smaller chunks improve retrieval precision (more targeted matches) but increase the total number of chunks (and therefore embeddings and index size) and may lose broader context; larger chunks preserve more context per chunk but reduce retrieval precision and risk exceeding prompt size limits when several are retrieved together. The chunking configuration should be tuned empirically based on observed retrieval and answer quality during development, rather than fixed arbitrarily. |

---

## 9. Embedding Strategy

**Why Sentence Transformers**: As established in `04_Technology_Stack.md`, Sentence Transformers are used because they provide strong, well-validated semantic embedding quality, run locally without per-call cost, and are specifically designed (unlike general-purpose word embeddings) to produce meaningful representations of full sentences and passages — which is exactly the granularity at which this system's chunks operate.

**Embedding Consistency**: It is critical that the *same* embedding model (and model version) is used to embed both the paper chunks (at ingestion time) and the user's questions (at query time). Embeddings from different models are not comparable to one another — their vector spaces are not aligned — so mixing models between ingestion and query would silently produce meaningless similarity scores. If the embedding model is ever upgraded or changed, all previously stored chunk embeddings must be regenerated using the new model before they can be meaningfully compared against newly embedded questions; embeddings from different model versions must never coexist in the same FAISS index.

---

## 10. Similarity Search

Once both chunks and questions are represented as vectors, the system needs a way to measure how "close" two vectors are in meaning — this is done using a similarity metric, most commonly **cosine similarity**.

**Cosine Similarity (Conceptual Explanation)**: Cosine similarity measures the angle between two vectors, rather than their raw magnitude. Two vectors pointing in nearly the same direction (a small angle between them) are considered highly similar in meaning, regardless of their length. This makes cosine similarity well suited to comparing text embeddings, where the *direction* of the vector captures semantic meaning, and is a standard choice for semantic search systems.

**Top-k Retrieval (Conceptual Explanation)**: Given a question's embedding, the system computes its similarity to every stored chunk embedding (or an efficient approximation thereof, depending on the FAISS index type) and returns the "k" chunks with the highest similarity scores — for example, the 5 most similar chunks. This is "top-k retrieval": rather than an all-or-nothing threshold, the system always returns a manageable, ranked shortlist of the best available matches, which are then passed on to context selection and prompt construction.

---

## 11. FAISS Interaction

FAISS is responsible for storing chunk embeddings and performing efficient similarity search across them. Its interaction within the pipeline proceeds as follows:

- **At Ingestion Time**: After a chunk's embedding is generated, it is added to the FAISS index, and a corresponding entry is recorded in the ID-mapping structure that links the vector's position within FAISS back to its `chunks._id` in MongoDB (per `05_Database_Design.md`).
- **At Query Time**: The question's embedding is submitted to FAISS as a search query; FAISS returns the top-k most similar vector positions along with their similarity scores.
- **Resolving Results**: The returned vector positions are translated, via the ID-mapping structure, back into their corresponding MongoDB `chunks` documents, from which the actual chunk text and metadata (paper title, section) are retrieved for prompt construction.
- **Index Persistence**: The FAISS index and its ID-mapping file are persisted to disk after ingestion operations, ensuring the vector store survives application restarts, as detailed in `05_Database_Design.md`.

FAISS itself has no understanding of "papers" or "text" — it operates purely on vectors and numerical IDs; all meaning is reconstructed by the backend through the MongoDB mapping layer.

---

## 12. End-to-End Data Flow

```
   Ingestion Flow                                Query Flow
┌───────────────┐                        ┌───────────────┐
│  PDF File        │                        │  User Question    │
└──────┬────────┘                        └──────┬────────┘
       ▼                                          ▼
┌───────────────┐                        ┌───────────────┐
│ Extracted Text   │                        │ Question Embedding │
└──────┬────────┘                        └──────┬────────┘
       ▼                                          ▼
┌───────────────┐                        ┌───────────────┐
│ Cleaned Text     │                        │ FAISS Search        │
└──────┬────────┘                        └──────┬────────┘
       ▼                                          ▼
┌───────────────┐                        ┌───────────────┐
│ Text Chunks       │                        │ Top-k Chunk IDs      │
└──────┬────────┘                        └──────┬────────┘
       ▼                                          ▼
┌───────────────┐                        ┌───────────────┐
│ Chunk Embeddings   │◀──────(shared vector space)──────▶│ Resolved Chunk Text  │
└──────┬────────┘                        │ (via MongoDB)         │
       ▼                                 └──────┬────────┘
┌───────────────┐                                ▼
│ FAISS Index        │                    ┌───────────────┐
│ + MongoDB Chunks    │                    │ Prompt Construction   │
└───────────────┘                    └──────┬────────┘
                                                   ▼
                                           ┌───────────────┐
                                           │  Gemini Response    │
                                           └──────┬────────┘
                                                   ▼
                                           ┌───────────────┐
                                           │  Final Answer       │
                                           └───────────────┘
```

The two flows are connected by a **shared embedding space**: chunk embeddings generated during ingestion and question embeddings generated at query time must originate from the exact same embedding model, since this shared vector space is what makes similarity search between them meaningful.

---

## 13. Failure Scenarios

| Scenario | System Response |
|---|---|
| **Empty PDFs** (no extractable text, e.g., a scanned image-only PDF) | Detected during the Extract Text stage; the paper's status is set to `failed` with a clear message indicating no extractable text was found; the paper is not passed further into the pipeline. OCR support is explicitly out of scope for Version 1 (per `01_Project_Overview.md`). |
| **No Relevant Chunks Found** (similarity search returns only low-relevance matches) | The system proceeds to generation but instructs the LLM (per Section 6/7) to explicitly state that the available papers do not contain sufficient information to answer the question, rather than forcing an answer from weak context. |
| **Gemini Unavailable** (API timeout, outage, or rate limit) | The `/ask`, `/summarize`, and `/compare` endpoints return a `502 Bad Gateway` response (per `06_API_Design.md`) with a clear, user-facing message indicating that answer generation is temporarily unavailable; the error is logged with full detail internally. |
| **Embedding Failures** (model load failure, unexpected input) | The affected paper's processing is marked as `failed`; the error is logged; the user is informed that processing could not complete and may retry. |
| **Corrupted Files** (malformed or unreadable PDF) | Detected during file validation, prior to text extraction; the upload is rejected with a `400`-class error indicating the file could not be read, per `06_API_Design.md`. |

The consistent governing principle across all failure scenarios is: **fail clearly and honestly**, both to the user (a plain, actionable message) and internally (a fully logged error), rather than silently producing a degraded or misleading result.

---

## 14. Performance Considerations

- **Embedding Reuse**: Chunk embeddings are generated exactly once, at ingestion time, and persisted; they are never regenerated on subsequent queries, since embedding generation is comparatively expensive relative to simply reading a stored vector.
- **Indexing**: The FAISS index type should be selected based on expected scale — an exact search index is sufficient and simplest for a moderate number of chunks, while an approximate nearest-neighbor index (e.g., IVF-based) becomes more appropriate as the total chunk count grows substantially, trading a small amount of retrieval accuracy for significantly faster search.
- **Caching**: Repeated identical or near-identical questions can have their generated answers cached, avoiding redundant retrieval and LLM generation calls for the same query against the same paper scope.
- **Retrieval Optimization**: The value of "k" (how many chunks are retrieved) should be tuned to balance answer completeness against prompt size and latency — retrieving too many chunks increases both cost and the risk of diluting the most relevant material within the prompt.
- **Batch Ingestion**: When multiple papers are uploaded simultaneously, embedding generation should be batched where the underlying model supports it, rather than processed one chunk at a time, to improve ingestion throughput.

---

## 15. Future Improvements

- **Hybrid Search**: Combine semantic (vector) search with traditional keyword-based (lexical) search, so that queries containing exact technical terms, model names, or dataset names benefit from both matching strategies rather than relying on semantic similarity alone.
- **Reranking**: Introduce a secondary reranking step after initial top-k retrieval, using a more precise (but more computationally expensive) model to re-score and reorder the initial candidate chunks before final selection, improving context quality without needing to run the expensive reranker over the entire chunk collection.
- **Multiple Vector Databases**: As described in `04_Technology_Stack.md`, the vector store service is abstracted behind a consistent interface, allowing FAISS to be replaced or supplemented by a distributed/managed vector database (e.g., Milvus, Weaviate) as scale increases.
- **Streaming Responses**: Adopt token-by-token streaming of the Gemini response to the frontend (via Server-Sent Events or WebSockets), improving perceived responsiveness for longer answers, summaries, or comparisons.
- **Multiple LLM Providers**: Extend the Gemini integration into a provider-agnostic interface, allowing the RAG Engine to route generation requests to alternative LLM providers (e.g., as a fallback during an outage, or as a user-configurable preference).

---

## 16. RAG Pipeline Summary

The Retrieval-Augmented Generation pipeline defined in this document transforms uploaded research papers into a semantically searchable knowledge base, and transforms user questions into grounded, source-attributed answers, through a consistent two-phase process: an **ingestion phase** (extraction, cleaning, chunking, embedding, and storage) performed once per paper, and a **query phase** (question embedding, similarity search, context retrieval, prompt construction, and generation) performed on every user interaction.

This architecture is well-suited to the AI Research Assistant because it directly addresses the core requirement established in `01_Project_Overview.md` and `02_System_Architecture.md`: enabling accurate, trustworthy natural-language interaction with research papers at a scale that would be infeasible if entire documents were sent to the LLM on every request. By grounding every generated answer in specifically retrieved, verifiable source text — and by explicitly instructing the model to acknowledge when sufficient context is unavailable — this pipeline directly minimizes hallucination risk while remaining modular enough (per the chunking, embedding, and vector-store abstractions defined here) to evolve with future improvements such as hybrid search, reranking, and multi-provider LLM support.
