import io
import json
from unittest.mock import patch, MagicMock
import pytest
from backend.app import create_app
from backend.services import auth_service


@pytest.fixture(autouse=True)
def set_secret(monkeypatch):
    monkeypatch.setattr(auth_service.settings, "JWT_SECRET_KEY", "test-secret-key")


@pytest.fixture
def app():
    application = create_app()
    application.config["TESTING"] = True
    return application


class _AuthedTestClient:
    """Wraps a Flask test client to attach a valid JWT to every request."""

    def __init__(self, inner, token):
        self._inner = inner
        self._headers = {"Authorization": f"Bearer {token}"}

    def _merge(self, kwargs):
        headers = dict(kwargs.get("headers") or {})
        headers.setdefault("Authorization", self._headers["Authorization"])
        kwargs["headers"] = headers
        return kwargs

    def get(self, *args, **kwargs):
        return self._inner.get(*args, **self._merge(kwargs))

    def post(self, *args, **kwargs):
        return self._inner.post(*args, **self._merge(kwargs))

    def delete(self, *args, **kwargs):
        return self._inner.delete(*args, **self._merge(kwargs))

    def patch(self, *args, **kwargs):
        return self._inner.patch(*args, **self._merge(kwargs))


@pytest.fixture
def client(app):
    token = auth_service.generate_token("507f1f77bcf86cd799439011")
    return _AuthedTestClient(app.test_client(), token)


class TestHealth:
    def test_health_returns_200(self, client):
        resp = client.get("/api/v1/health")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert data["data"]["status"] == "healthy"


class TestUpload:
    @patch("backend.services.ingestion_service.save_and_queue")
    def test_upload_pdf_success(self, mock_process, client):
        mock_process.return_value = {
            "_id": "507f1f77bcf86cd799439011",
            "title": "Test Paper",
            "status": "processed",
            "upload_date": "2026-07-21T00:00:00",
        }

        data = {
            "files": (io.BytesIO(b"%PDF-1.4 test"), "paper.pdf"),
        }
        resp = client.post(
            "/api/v1/upload",
            data=data,
            content_type="multipart/form-data",
        )
        assert resp.status_code == 201
        body = resp.get_json()
        assert body["success"] is True
        assert len(body["data"]["papers"]) == 1
        assert body["data"]["papers"][0]["title"] == "Test Paper"

    def test_upload_no_files(self, client):
        resp = client.post("/api/v1/upload", content_type="multipart/form-data")
        assert resp.status_code == 400
        body = resp.get_json()
        assert body["success"] is False
        assert body["error"]["code"] == "MISSING_FILES"


class TestAsk:
    @patch("backend.services.rag_service.answer_query")
    def test_ask_question_success(self, mock_answer, client):
        mock_answer.return_value = {
            "answer": "This is the answer.",
            "sources": [
                {
                    "chunk_id": "chunk_1",
                    "text": "Paper content",
                    "paper_id": "507f1f77bcf86cd799439011",
                    "page_number": 1,
                    "score": 0.95,
                },
            ],
            "conversation_id": "conv_123",
        }

        resp = client.post(
            "/api/v1/ask",
            json={"question": "What is this about?", "paper_ids": ["507f1f77bcf86cd799439011"]},
        )
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["success"] is True
        assert body["data"]["answer"] == "This is the answer."
        assert len(body["data"]["sources"]) == 1

    def test_ask_invalid_json(self, client):
        resp = client.post("/api/v1/ask", data="not-json", content_type="application/json")
        assert resp.status_code == 400

    def test_ask_empty_question(self, client):
        resp = client.post(
            "/api/v1/ask",
            json={"question": "", "paper_ids": ["507f1f77bcf86cd799439011"]},
        )
        assert resp.status_code == 422


class TestPapers:
    @patch("backend.models.paper_model.get_all_papers")
    def test_list_papers(self, mock_list, client):
        mock_list.return_value = [
            {
                "_id": "507f1f77bcf86cd799439011",
                "title": "Paper 1",
                "status": "processed",
                "page_count": 10,
                "upload_date": "2026-07-21T00:00:00",
                "keywords": ["ml"],
            },
        ]

        resp = client.get("/api/v1/papers")
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["success"] is True
        assert len(body["data"]["papers"]) == 1

    @patch("backend.models.paper_model.get_paper")
    def test_get_paper_found(self, mock_get, client):
        mock_get.return_value = {
            "_id": "507f1f77bcf86cd799439011",
            "title": "Paper 1",
            "filename": "paper.pdf",
            "status": "processed",
            "page_count": 10,
            "upload_date": "2026-07-21T00:00:00",
            "keywords": [],
            "datasets": [],
            "algorithms": [],
            "summary": "",
        }

        resp = client.get("/api/v1/paper/507f1f77bcf86cd799439011")
        assert resp.status_code == 200
        assert resp.get_json()["data"]["paper"]["title"] == "Paper 1"

    def test_get_paper_invalid_id(self, client):
        resp = client.get("/api/v1/paper/invalid")
        assert resp.status_code == 400

    @patch("backend.models.paper_model.get_paper")
    def test_get_paper_not_found(self, mock_get, client):
        mock_get.return_value = None
        resp = client.get("/api/v1/paper/507f1f77bcf86cd799439011")
        assert resp.status_code == 404

    @patch("backend.models.paper_model.get_paper")
    @patch("backend.models.chunk_model.get_chunks_by_paper")
    @patch("backend.models.chunk_model.delete_chunks_by_paper")
    @patch("backend.models.paper_model.delete_paper")
    @patch("backend.services.vector_store_service.vector_store.remove_vectors")
    def test_delete_paper(
        self, mock_remove, mock_delete, mock_delete_chunks, mock_chunks, mock_paper, client
    ):
        mock_paper.return_value = {
            "_id": "507f1f77bcf86cd799439011",
            "title": "Paper 1",
        }
        mock_chunks.return_value = [{"vector_id": "vec_1"}]

        resp = client.delete("/api/v1/paper/507f1f77bcf86cd799439011")
        assert resp.status_code == 200
        assert resp.get_json()["data"]["deleted_id"] == "507f1f77bcf86cd799439011"


class TestHistory:
    @patch("backend.models.conversation_model.get_all_conversations")
    @patch("backend.models.search_history_model.get_search_history")
    def test_get_history(self, mock_search, mock_conv, client):
        mock_conv.return_value = [
            {
                "_id": "conv_1",
                "title": "Test conversation",
                "paper_ids": [],
                "created_at": "2026-07-21T00:00:00",
                "updated_at": "2026-07-21T00:00:00",
            },
        ]
        mock_search.return_value = []

        resp = client.get("/api/v1/history")
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["success"] is True
        assert len(body["data"]["conversations"]) == 1


class TestSummarize:
    @patch("backend.models.paper_model.get_paper")
    @patch("backend.models.chunk_model.get_chunks_by_paper")
    @patch("backend.services.gemini_service.generate_summary")
    @patch("backend.models.paper_model.update_paper")
    def test_summarize_success(
        self, mock_update, mock_generate, mock_chunks, mock_paper, client
    ):
        mock_paper.return_value = {
            "_id": "507f1f77bcf86cd799439011",
            "title": "Paper",
            "status": "processed",
            "summary": "",
        }
        mock_chunks.return_value = [{"chunk_text": "Paper content."}]
        mock_generate.return_value = "This is a summary."

        resp = client.post(
            "/api/v1/summarize",
            json={"paper_id": "507f1f77bcf86cd799439011"},
        )
        assert resp.status_code == 200
        assert resp.get_json()["data"]["summary"] == "This is a summary."

    def test_summarize_missing_id(self, client):
        resp = client.post("/api/v1/summarize", json={"paper_id": ""})
        assert resp.status_code == 400
        assert resp.get_json()["error"]["code"] == "MISSING_PAPER_ID"


class TestCompare:
    @patch("backend.models.paper_model.get_paper")
    @patch("backend.models.chunk_model.get_chunks_by_paper")
    @patch("backend.services.gemini_service.generate_comparison")
    def test_compare_success(self, mock_gen, mock_chunks, mock_paper, client):
        def get_paper_side_effect(pid):
            return {
                "_id": pid,
                "title": f"Paper {pid[-4:]}",
                "status": "processed",
            }

        mock_paper.side_effect = get_paper_side_effect
        mock_chunks.return_value = [{"chunk_text": "Content."}]
        mock_gen.return_value = "Comparison text."

        resp = client.post(
            "/api/v1/compare",
            json={
                "paper_ids": [
                    "507f1f77bcf86cd799439011",
                    "507f1f77bcf86cd799439012",
                ],
            },
        )
        assert resp.status_code == 200
        assert resp.get_json()["success"] is True

    def test_compare_too_few_papers(self, client):
        resp = client.post(
            "/api/v1/compare",
            json={"paper_ids": ["507f1f77bcf86cd799439011"]},
        )
        assert resp.status_code == 400
        assert resp.get_json()["error"]["code"] == "INSUFFICIENT_PAPERS"

    def test_compare_invalid_ids(self, client):
        resp = client.post(
            "/api/v1/compare",
            json={"paper_ids": ["bad_id", "507f1f77bcf86cd799439011"]},
        )
        assert resp.status_code == 400
        assert resp.get_json()["error"]["code"] == "INVALID_IDS"
