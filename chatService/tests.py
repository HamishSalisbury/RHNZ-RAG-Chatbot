import os

os.environ.setdefault("RULES_TOP_K", "3")
os.environ.setdefault("PATH_TO_INDEX", "test-index")
os.environ.setdefault("MIN_COSINE_SIMILIARTY", "0.4")
os.environ.setdefault("GEMINI_API_KEY", "dummy-key")
os.environ.setdefault("LLM_MODEL", "gemini-3.5-flash")
os.environ.setdefault("LLM_TIMEOUT_S", "10")
os.environ.setdefault("THROTTLE_BURST", "20/min")
os.environ.setdefault("THROTTLE_SUSTAINED", "30/day")

from unittest.mock import patch
from django.urls import reverse
from django.test import override_settings
from django.core.cache import cache
from rest_framework import status
from rest_framework.test import APITestCase
from google.genai import errors


FAKE_CHUNKS = {
    "documents": [["A team may request two timeouts per half."]],
    "metadatas": [[{"rule_id": "9.1", "source": "rules.pdf", "page": 10}]],
    "distances": [[0.23]],
}

CACHE_TEST_SETTINGS = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

# The real production burst limit (must match settings.py / .env).
BURST_LIMIT = int(os.environ["THROTTLE_BURST"].split("/")[0])


@override_settings(CACHES=CACHE_TEST_SETTINGS)
class AskChatbotLLMFailureTests(APITestCase):
    def setUp(self):
        self.url = reverse("ask_chatbot")
        cache.clear()  # start each test with an empty throttle counter

    @patch("chatService.views.generate_answer")
    @patch("chatService.views.query_chatbot")
    def test_llm_api_error_returns_503_not_500(self, mock_query, mock_generate):
        """An APIError from the LLM maps to 503, not an unhandled 500."""
        mock_query.return_value = FAKE_CHUNKS
        mock_generate.side_effect = errors.APIError("boom", response_json={})

        resp = self.client.post(self.url, {"question": "timeouts?"}, format="json")

        self.assertEqual(resp.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertNotEqual(resp.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    @patch("chatService.views.generate_answer")
    @patch("chatService.views.query_chatbot")
    def test_llm_empty_response_returns_503(self, mock_query, mock_generate):
        """An empty/None answer from the model is not shipped as a 200."""
        mock_query.return_value = FAKE_CHUNKS
        mock_generate.return_value = ""

        resp = self.client.post(self.url, {"question": "timeouts?"}, format="json")

        self.assertEqual(resp.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)

    @patch("chatService.views.generate_answer")
    @patch("chatService.views.query_chatbot")
    def test_successful_answer_returns_200(self, mock_query, mock_generate):
        """Control case: when the LLM succeeds, the view returns its text at 200."""
        mock_query.return_value = FAKE_CHUNKS
        mock_generate.return_value = "Each team may request two timeouts per half (Rule 9.1)."

        resp = self.client.post(self.url, {"question": "timeouts?"}, format="json")

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(
            resp.data["answer"][0]["text"],
            "Each team may request two timeouts per half (Rule 9.1).",
        )

    @patch("chatService.views.generate_answer")
    @patch("chatService.views.query_chatbot")
    def test_llm_not_called_when_no_chunks(self, mock_query, mock_generate):
        """When retrieval returns nothing, the LLM is never called (no spend)."""
        mock_query.return_value = {"documents": [[]], "metadatas": [[]], "distances": [[]]}

        resp = self.client.post(self.url, {"question": "obscure?"}, format="json")

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        mock_generate.assert_not_called()


@override_settings(CACHES=CACHE_TEST_SETTINGS)
class RateLimitingTests(APITestCase):
    def setUp(self):
        self.url = reverse("ask_chatbot")
        cache.clear()

    def _post(self, ip):
        with patch("chatService.views.query_chatbot", return_value={
            "documents": [["chunk"]],
            "metadatas": [[{"rule_id": "1.1"}]],
            "distances": [[0.2]],
        }), patch("chatService.views.generate_answer", return_value="ok"):
            return self.client.post(
                self.url,
                {"question": "hi"},
                format="json",
                REMOTE_ADDR=ip,
            )

    def test_single_ip_is_throttled_after_limit(self):
        """The first BURST_LIMIT requests pass; the next is throttled with 429."""
        ip = "10.0.0.1"

        for _ in range(BURST_LIMIT):
            self.assertEqual(self._post(ip).status_code, status.HTTP_200_OK)

        self.assertEqual(self._post(ip).status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    def test_different_ips_are_throttled_separately(self):
        """Exhausting one IP's allowance does not affect a different IP."""
        ip_a = "10.0.0.1"
        ip_b = "10.0.0.2"

        for _ in range(BURST_LIMIT):
            self.assertEqual(self._post(ip_a).status_code, status.HTTP_200_OK)
        self.assertEqual(self._post(ip_a).status_code, status.HTTP_429_TOO_MANY_REQUESTS)

        for _ in range(BURST_LIMIT):
            self.assertEqual(self._post(ip_b).status_code, status.HTTP_200_OK)
        self.assertEqual(self._post(ip_b).status_code, status.HTTP_429_TOO_MANY_REQUESTS)