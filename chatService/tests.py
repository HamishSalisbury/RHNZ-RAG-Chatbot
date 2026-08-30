from unittest.mock import patch

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from google.genai import errors
import os

# Must be set BEFORE anything imports Django settings.
os.environ.setdefault("RULES_TOP_K", "3")
os.environ.setdefault("PATH_TO_INDEX", "test-index")
os.environ.setdefault("MIN_COSINE_SIMILARITY", "0.4")
os.environ.setdefault("GEMINI_API_KEY", "dummy-key")
os.environ.setdefault("LLM_MODEL", "gemini-3.5-flash")
os.environ.setdefault("LLM_TIMEOUT_S", "10")

# Now it's safe to import things that touch settings.
from unittest.mock import patch
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from google.genai import errors
# A valid query_chatbot return: chunks that cleared the threshold,
# so the view proceeds to call the LLM.
FAKE_CHUNKS = {
    "documents": [["A team may request two timeouts per half."]],
    "metadatas": [[{"rule_id": "9.1", "source": "rules.pdf", "page": 10}]],
    "distances": [[0.23]],
}


class AskChatbotLLMFailureTests(APITestCase):
    def setUp(self):
        # reverse() uses the URL name from your urls.py (name='ask_chatbot')
        self.url = reverse("ask_chatbot")

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