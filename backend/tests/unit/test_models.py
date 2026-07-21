import mongomock
import pytest
from bson import ObjectId
from backend.services.database_service import DatabaseService
from backend.models import paper_model, chunk_model, conversation_model
from backend.models import question_model, search_history_model


@pytest.fixture(autouse=True)
def mock_db():
    """Replace the real MongoDB with an in-memory mock for all tests."""
    client = mongomock.MongoClient()
    db = client["research_assistant"]
    DatabaseService._client = client
    DatabaseService._db = db
    DatabaseService._ensure_indexes()
    yield
    DatabaseService.disconnect()


class TestPaperModel:
    def test_create_paper(self):
        doc = paper_model.create_paper(
            title="Test Paper", filename="test.pdf", file_path="/tmp/test.pdf"
        )
        assert doc is not None
        assert doc["title"] == "Test Paper"
        assert doc["status"] == "pending"

    def test_get_paper(self):
        created = paper_model.create_paper(
            title="My Paper", filename="my.pdf", file_path="/tmp/my.pdf"
        )
        fetched = paper_model.get_paper(str(created["_id"]))
        assert fetched["title"] == "My Paper"

    def test_get_all_papers(self):
        paper_model.create_paper(title="A", filename="a.pdf", file_path="/tmp/a.pdf")
        paper_model.create_paper(title="B", filename="b.pdf", file_path="/tmp/b.pdf")
        papers = paper_model.get_all_papers()
        assert len(papers) == 2

    def test_update_paper(self):
        created = paper_model.create_paper(
            title="Old", filename="old.pdf", file_path="/tmp/old.pdf"
        )
        updated = paper_model.update_paper(
            str(created["_id"]), {"status": "processed"}
        )
        assert updated is True
        fetched = paper_model.get_paper(str(created["_id"]))
        assert fetched["status"] == "processed"

    def test_delete_paper(self):
        created = paper_model.create_paper(
            title="Del", filename="del.pdf", file_path="/tmp/del.pdf"
        )
        pid = str(created["_id"])
        assert paper_model.delete_paper(pid) is True
        assert paper_model.get_paper(pid) is None


class TestChunkModel:
    def test_create_chunks(self):
        paper = paper_model.create_paper(
            title="P", filename="p.pdf", file_path="/tmp/p.pdf"
        )
        chunks_data = [
            {"paper_id": str(paper["_id"]), "chunk_text": "Text A",
             "chunk_index": 0, "page_number": 1, "vector_id": "0"},
            {"paper_id": str(paper["_id"]), "chunk_text": "Text B",
             "chunk_index": 1, "page_number": 1, "vector_id": "1"},
        ]
        docs = chunk_model.create_chunks(chunks_data)
        assert len(docs) == 2
        assert docs[0]["chunk_text"] == "Text A"

    def test_get_chunks_by_paper(self):
        paper = paper_model.create_paper(
            title="P", filename="p.pdf", file_path="/tmp/p.pdf"
        )
        chunk_model.create_chunks([
            {"paper_id": str(paper["_id"]), "chunk_text": "C1",
             "chunk_index": 0, "vector_id": "0"},
        ])
        chunks = chunk_model.get_chunks_by_paper(str(paper["_id"]))
        assert len(chunks) == 1
        assert chunks[0]["chunk_text"] == "C1"

    def test_get_chunk_by_vector_id(self):
        paper = paper_model.create_paper(
            title="P", filename="p.pdf", file_path="/tmp/p.pdf"
        )
        chunk_model.create_chunks([
            {"paper_id": str(paper["_id"]), "chunk_text": "Vec1",
             "chunk_index": 0, "vector_id": "v42"},
        ])
        chunk = chunk_model.get_chunk_by_vector_id("v42")
        assert chunk is not None
        assert chunk["chunk_text"] == "Vec1"

    def test_delete_chunks_by_paper(self):
        paper = paper_model.create_paper(
            title="P", filename="p.pdf", file_path="/tmp/p.pdf"
        )
        chunk_model.create_chunks([
            {"paper_id": str(paper["_id"]), "chunk_text": "D",
             "chunk_index": 0, "vector_id": "0"},
        ])
        deleted = chunk_model.delete_chunks_by_paper(str(paper["_id"]))
        assert deleted == 1
        assert chunk_model.get_chunks_by_paper(str(paper["_id"])) == []


class TestConversationModel:
    def test_create_conversation(self):
        conv = conversation_model.create_conversation(
            paper_ids=[str(ObjectId())], title="Test Conv"
        )
        assert conv is not None
        assert conv["title"] == "Test Conv"

    def test_get_conversation(self):
        conv = conversation_model.create_conversation(
            paper_ids=[str(ObjectId())]
        )
        fetched = conversation_model.get_conversation(str(conv["_id"]))
        assert fetched is not None

    def test_get_all_conversations(self):
        conversation_model.create_conversation(paper_ids=[str(ObjectId())])
        conversation_model.create_conversation(paper_ids=[str(ObjectId())])
        convs = conversation_model.get_all_conversations()
        assert len(convs) == 2


class TestQuestionModel:
    def test_create_question(self):
        conv = conversation_model.create_conversation(
            paper_ids=[str(ObjectId())]
        )
        q = question_model.create_question(
            conversation_id=str(conv["_id"]),
            question_text="What is this?",
            answer_text="A test.",
            source_chunk_ids=[str(ObjectId())],
        )
        assert q is not None
        assert q["question_text"] == "What is this?"

    def test_get_questions_by_conversation(self):
        conv = conversation_model.create_conversation(
            paper_ids=[str(ObjectId())]
        )
        question_model.create_question(
            conversation_id=str(conv["_id"]),
            question_text="Q1", answer_text="A1",
            source_chunk_ids=[],
        )
        question_model.create_question(
            conversation_id=str(conv["_id"]),
            question_text="Q2", answer_text="A2",
            source_chunk_ids=[],
        )
        questions = question_model.get_questions_by_conversation(
            str(conv["_id"])
        )
        assert len(questions) == 2
        assert questions[0]["question_text"] == "Q1"


class TestSearchHistoryModel:
    def test_create_search_entry(self):
        entry = search_history_model.create_search_entry(
            query_text="test query",
            paper_ids=[str(ObjectId())],
            result_chunk_ids=[str(ObjectId())],
        )
        assert entry is not None
        assert entry["query_text"] == "test query"

    def test_get_search_history(self):
        search_history_model.create_search_entry(
            query_text="q1", paper_ids=[], result_chunk_ids=[],
        )
        search_history_model.create_search_entry(
            query_text="q2", paper_ids=[], result_chunk_ids=[],
        )
        history = search_history_model.get_search_history()
        assert len(history) == 2
