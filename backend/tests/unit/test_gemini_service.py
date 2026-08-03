from unittest.mock import patch, MagicMock
import pytest
from backend.services.gemini_service import (
    answer_question,
    generate_summary,
    generate_comparison,
)
from backend.middlewares.error_handler import AppError


@pytest.fixture(autouse=True)
def mock_gemini():
    """Mock the Gemini API client for all tests."""
    with patch("backend.services.gemini_service._get_client") as mock:
        client = MagicMock()
        response = MagicMock()
        response.text = "This is a generated response."
        client.models.generate_content.return_value = response
        mock.return_value = client
        yield


class TestAnswerQuestion:
    def test_returns_answer(self):
        result = answer_question(
            context="Paper content about machine learning.",
            question="What is this paper about?",
        )
        assert result == "This is a generated response."

    def test_raises_error_on_api_failure(self):
        client = MagicMock()
        client.models.generate_content.side_effect = Exception("API down")
        with patch("backend.services.gemini_service._get_client", return_value=client):
            with pytest.raises(AppError) as exc:
                answer_question(context="text", question="q")
            assert exc.value.code == "GEMINI_ERROR"

    def test_retries_on_503_unavailable(self):
        client = MagicMock()
        response = MagicMock()
        response.text = "Recovered response."
        client.models.generate_content.side_effect = [
            Exception("{'error': {'code': 503, 'status': 'UNAVAILABLE'}}"),
            response,
        ]
        with patch("backend.services.gemini_service._get_client", return_value=client):
            with patch("backend.services.gemini_service.time.sleep") as mock_sleep:
                result = answer_question(context="text", question="q")
        assert result == "Recovered response."
        assert mock_sleep.call_count == 1
        assert client.models.generate_content.call_count == 2

    def test_retries_on_429_quota(self):
        client = MagicMock()
        response = MagicMock()
        response.text = "Recovered response."
        client.models.generate_content.side_effect = [
            Exception("429 RESOURCE_EXHAUSTED"),
            response,
        ]
        with patch("backend.services.gemini_service._get_client", return_value=client):
            with patch("backend.services.gemini_service.time.sleep") as mock_sleep:
                result = answer_question(context="text", question="q")
        assert result == "Recovered response."
        assert mock_sleep.call_count == 1

    def test_gives_up_after_three_attempts(self):
        client = MagicMock()
        client.models.generate_content.side_effect = Exception(
            "{'error': {'code': 503, 'status': 'UNAVAILABLE'}}"
        )
        with patch("backend.services.gemini_service._get_client", return_value=client):
            with patch("backend.services.gemini_service.time.sleep"):
                with pytest.raises(AppError) as exc:
                    answer_question(context="text", question="q")
        assert exc.value.code == "GEMINI_ERROR"
        assert client.models.generate_content.call_count == 3


class TestGenerateSummary:
    def test_returns_summary(self):
        result = generate_summary(context="Paper content here.")
        assert result == "This is a generated response."


class TestGenerateComparison:
    def test_returns_comparison(self):
        result = generate_comparison(
            context="Paper A content. Paper B content.",
            dimensions=["dataset", "method"],
        )
        assert result == "This is a generated response."
