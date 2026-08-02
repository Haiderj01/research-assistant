from unittest.mock import patch
import pytest
from bson import ObjectId
from backend.app import create_app
from backend.services import auth_service
from backend.models import paper_model
from backend.services.database_service import DatabaseService

VALID_IDS = [
    "507f1f77bcf86cd799439011",
    "507f1f77bcf86cd799439012",
]


@pytest.fixture(autouse=True)
def set_secret(monkeypatch):
    monkeypatch.setattr(auth_service.settings, "JWT_SECRET_KEY", "test-secret-key")


@pytest.fixture
def app():
    application = create_app()
    application.config["TESTING"] = True
    return application


class _AuthedTestClient:
    def __init__(self, inner, token):
        self._inner = inner
        self._headers = {"Authorization": f"Bearer {token}"}

    def _merge(self, kwargs):
        headers = dict(kwargs.get("headers") or {})
        headers.setdefault("Authorization", self._headers["Authorization"])
        kwargs["headers"] = headers
        return kwargs

    def post(self, *args, **kwargs):
        return self._inner.post(*args, **self._merge(kwargs))


@pytest.fixture
def client(app):
    token = auth_service.generate_token("507f1f77bcf86cd799439011")
    return _AuthedTestClient(app.test_client(), token)


@pytest.fixture
def clean_data(app):
    yield
    db = DatabaseService.get_db()
    if db is not None:
        db["papers"].delete_many({})


def _make_processed_paper(user_id, status="processed"):
    paper = paper_model.create_paper(
        title="Paper", filename="p.pdf", file_path="/tmp/p.pdf", user_id=user_id
    )
    paper_model.update_paper(str(paper["_id"]), {"status": status})
    return paper


class TestGapAnalysisRoutes:
    def test_auth_required(self, app):
        resp = app.test_client().post(
            "/api/v1/gap-analysis",
            json={"paper_ids": VALID_IDS},
        )
        assert resp.status_code == 401
        assert resp.get_json()["error"]["code"] == "UNAUTHORIZED"

    def test_too_few_papers(self, client):
        resp = client.post("/api/v1/gap-analysis", json={"paper_ids": [VALID_IDS[0]]})
        assert resp.status_code == 400
        assert resp.get_json()["error"]["code"] == "INSUFFICIENT_PAPERS"

    @patch("backend.services.gap_analysis_service.analyze_research_gaps")
    def test_happy_path(self, mock_analyze, client):
        mock_analyze.return_value = {
            "gaps": [
                {
                    "description": "Model generalization is limited.",
                    "supporting_papers": VALID_IDS,
                    "strength": "multiple",
                    "suggested_direction": "Evaluate on more domains.",
                }
            ],
            "per_paper_summaries": [
                {"paper_id": VALID_IDS[0], "title": "Paper A", "summary": "S1"},
                {"paper_id": VALID_IDS[1], "title": "Paper B", "summary": "S2"},
            ],
        }
        resp = client.post("/api/v1/gap-analysis", json={"paper_ids": VALID_IDS})
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["success"] is True
        assert len(body["data"]["gaps"]) == 1
        assert len(body["data"]["per_paper_summaries"]) == 2

    def test_ownership_check(self, client, clean_data):
        paper_a = _make_processed_paper("507f1f77bcf86cd799439011")
        paper_b = _make_processed_paper("507f1f77bcf86cd799439099")
        resp = client.post(
            "/api/v1/gap-analysis",
            json={"paper_ids": [str(paper_a["_id"]), str(paper_b["_id"])]},
        )
        assert resp.status_code == 404
        assert resp.get_json()["error"]["code"] == "PAPER_NOT_FOUND"

    def test_unprocessed_paper(self, client, clean_data):
        paper_a = _make_processed_paper("507f1f77bcf86cd799439011", status="pending")
        paper_b = _make_processed_paper("507f1f77bcf86cd799439011")
        resp = client.post(
            "/api/v1/gap-analysis",
            json={"paper_ids": [str(paper_a["_id"]), str(paper_b["_id"])]},
        )
        assert resp.status_code == 422
        assert resp.get_json()["error"]["code"] == "PAPER_NOT_PROCESSED"
