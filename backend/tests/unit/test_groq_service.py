from unittest.mock import patch, MagicMock
import pytest
from backend.services.groq_service import (
    answer_question,
    generate_summary,
    generate_comparison,
    merge_summaries,
)
from backend.middlewares.error_handler import AppError


def _mock_completion(text: str) -> MagicMock:
    message = MagicMock()
    message.content = text
    choice = MagicMock()
    choice.message = message
    response = MagicMock()
    response.choices = [choice]
    return response


@pytest.fixture(autouse=True)
def mock_llm():
    """Mock the LLM API client for all tests."""
    with patch("backend.services.groq_service._get_client") as mock:
        client = MagicMock()
        client.chat.completions.create.return_value = _mock_completion(
            "This is a generated response."
        )
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
        client.chat.completions.create.side_effect = Exception("API down")
        with patch("backend.services.groq_service._get_client", return_value=client):
            with pytest.raises(AppError) as exc:
                answer_question(context="text", question="q")
            assert exc.value.code == "GROQ_ERROR"

    def test_retries_on_503_unavailable(self):
        client = MagicMock()
        client.chat.completions.create.side_effect = [
            Exception("{'error': {'code': 503, 'status': 'UNAVAILABLE'}}"),
            _mock_completion("Recovered response."),
        ]
        with patch("backend.services.groq_service._get_client", return_value=client):
            with patch("backend.services.groq_service.time.sleep") as mock_sleep:
                result = answer_question(context="text", question="q")
        assert result == "Recovered response."
        assert mock_sleep.call_count == 1
        assert client.chat.completions.create.call_count == 2

    def test_retries_on_429_quota(self):
        client = MagicMock()
        client.chat.completions.create.side_effect = [
            Exception("429 RATE_LIMIT"),
            _mock_completion("Recovered response."),
        ]
        with patch("backend.services.groq_service._get_client", return_value=client):
            with patch("backend.services.groq_service.time.sleep") as mock_sleep:
                result = answer_question(context="text", question="q")
        assert result == "Recovered response."
        assert mock_sleep.call_count == 1

    def test_gives_up_after_three_attempts(self):
        client = MagicMock()
        client.chat.completions.create.side_effect = Exception(
            "{'error': {'code': 503, 'status': 'UNAVAILABLE'}}"
        )
        with patch("backend.services.groq_service._get_client", return_value=client):
            with patch("backend.services.groq_service.time.sleep"):
                with pytest.raises(AppError) as exc:
                    answer_question(context="text", question="q")
        assert exc.value.code == "GROQ_ERROR"
        assert client.chat.completions.create.call_count == 3

    def test_fails_fast_on_long_rate_limit_reset(self):
        client = MagicMock()
        err = Exception("429 RATE_LIMIT")
        err.response = MagicMock()
        err.response.headers = {"retry-after": "18000"}
        client.chat.completions.create.side_effect = err
        with patch("backend.services.groq_service._get_client", return_value=client):
            with patch("backend.services.groq_service.time.sleep") as mock_sleep:
                with pytest.raises(AppError) as exc:
                    answer_question(context="text", question="q")
        assert exc.value.code == "GROQ_ERROR"
        assert mock_sleep.call_count == 0
        assert client.chat.completions.create.call_count == 1


class TestGenerateSummary:
    def test_returns_summary(self):
        result = generate_summary(context="Paper content here.")
        assert result == "This is a generated response."


class TestMergeSummaries:
    def test_returns_merged_summary(self):
        result = merge_summaries(["Part A summary.", "Part B summary."])
        assert result == "This is a generated response."


class TestGenerateComparison:
    def test_returns_comparison(self):
        result = generate_comparison(
            context="Paper A content. Paper B content.",
            dimensions=["dataset", "method"],
        )
        assert result == "This is a generated response."
