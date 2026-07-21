from backend.services import embedding_service, gemini_service
from backend.services.vector_store_service import vector_store
from backend.models import chunk_model, conversation_model, question_model, search_history_model
from backend.config.settings import settings
from backend.middlewares.error_handler import AppError
from backend.utils.logger import logger


def answer_query(
    question: str,
    paper_ids: list[str],
    conversation_id: str = None,
    top_k: int = None,
) -> dict:
    """Run the full RAG pipeline for a user question.

    Steps:
        1. Embed the question.
        2. Search FAISS for similar chunks.
        3. Resolve chunk IDs and retrieve text from MongoDB.
        4. Filter by paper scope.
        5. Build context and generate answer via Gemini.
        6. Persist conversation, question, and search history.

    Args:
        question: The user's natural-language question.
        paper_ids: Papers to scope the answer to.
        conversation_id: Existing conversation ID, or None to create new.
        top_k: Number of chunks to retrieve (default from settings).

    Returns:
        A dict with keys:
            - answer (str): Generated answer text.
            - sources (list[dict]): Source chunks used.
            - conversation_id (str): The conversation this exchange belongs to.
    """
    top_k = top_k or settings.DEFAULT_TOP_K

    if not question or not question.strip():
        raise AppError(
            message="Question cannot be empty.",
            status_code=422,
            code="EMPTY_QUESTION",
        )
    if not paper_ids:
        raise AppError(
            message="At least one paper ID is required.",
            status_code=422,
            code="MISSING_PAPER_IDS",
        )

    query_vector = embedding_service.generate_embedding(question)

    results = vector_store.search(query_vector, k=top_k)
    if not results:
        answer = (
            "The uploaded papers do not contain information relevant to your question. "
            "Try rephrasing or uploading papers on the topic."
        )
        return {
            "answer": answer,
            "sources": [],
            "conversation_id": conversation_id or "",
        }

    vector_ids = [r["chunk_id"] for r in results]
    chunks = chunk_model.get_chunks_by_vector_ids(vector_ids)
    chunks_by_id = {c["vector_id"]: c for c in (chunks or [])}

    source_chunks = []
    for r in results:
        cid = r["chunk_id"]
        chunk = chunks_by_id.get(cid)
        if chunk:
            source_chunks.append({
                "chunk_id": cid,
                "text": chunk["chunk_text"],
                "paper_id": str(chunk["paper_id"]),
                "page_number": chunk.get("page_number"),
                "score": r["score"],
            })

    if not source_chunks:
        answer = (
            "No relevant content could be retrieved from the selected papers. "
            "Please try a different question."
        )
        return {
            "answer": answer,
            "sources": [],
            "conversation_id": conversation_id or "",
        }

    context = "\n\n---\n\n".join(
        f"[Source {i+1}] {s['text']}" for i, s in enumerate(source_chunks)
    )

    generated_answer = gemini_service.answer_question(
        context=context, question=question
    )

    if conversation_id:
        conversation_model.update_conversation(conversation_id)
    else:
        conv = conversation_model.create_conversation(paper_ids=paper_ids)
        conversation_id = str(conv["_id"]) if conv else ""
    logger.debug(f"Using conversation_id={conversation_id}")

    if conversation_id:
        question_model.create_question(
            conversation_id=conversation_id,
            question_text=question,
            answer_text=generated_answer,
            source_chunk_ids=[s["chunk_id"] for s in source_chunks],
        )
        search_history_model.create_search_entry(
            query_text=question,
            paper_ids=paper_ids,
            result_chunk_ids=[s["chunk_id"] for s in source_chunks],
        )

    logger.info(f"RAG answer generated ({len(source_chunks)} sources, {len(context)} chars)")

    return {
        "answer": generated_answer,
        "sources": source_chunks,
        "conversation_id": conversation_id,
    }
