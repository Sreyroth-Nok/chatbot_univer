"""Integration tests. Run inside Docker:  docker compose exec web python manage.py test

They use the "hash" embeddings and no AI key, so they need no internet.
"""
from django.test import override_settings
from rest_framework.test import APITestCase

from knowledge.models import FAQ

from .models import ChatLog, Escalation


@override_settings(EMBEDDING_BACKEND="hash", LLM_API_KEY="", RAG_MAX_DISTANCE=0.70)
class ChatAPITests(APITestCase):
    def setUp(self):
        self.faq = FAQ.objects.create(
            question="What are the library opening hours?",
            answer="The library is open Monday to Saturday, 7:30–20:00.",
        )

    def ask(self, message, session_id="test-session"):
        return self.client.post("/api/chat/", {"message": message, "session_id": session_id}, format="json")

    def test_saving_faq_creates_search_chunk(self):
        self.assertEqual(self.faq.chunks.count(), 1)

    def test_known_question_returns_faq_answer(self):
        response = self.ask("library opening hours?")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data["escalated"])
        self.assertEqual(response.data["answer"], self.faq.answer)
        self.assertEqual(response.data["sources"][0]["title"], self.faq.question)

    def test_unknown_question_is_handed_to_staff(self):
        response = self.ask("zzqx unrelated parking permit for drones")
        self.assertTrue(response.data["escalated"])
        self.assertEqual(Escalation.objects.count(), 1)

    def test_khmer_question_gets_khmer_fallback(self):
        response = self.ask("តើមានកន្លែងចតឡានទេ?")
        self.assertEqual(response.data["language"], "km")

    def test_inactive_faq_is_not_used(self):
        self.faq.is_active = False
        self.faq.save()
        self.assertEqual(self.faq.chunks.count(), 0)
        self.assertTrue(self.ask("library opening hours?").data["escalated"])

    def test_every_question_is_logged(self):
        self.ask("library opening hours?")
        self.assertEqual(ChatLog.objects.count(), 1)

    def test_rating_only_by_same_session(self):
        log_id = self.ask("library opening hours?").data["log_id"]
        url = f"/api/chat/{log_id}/feedback/"
        other = self.client.post(url, {"rating": 1, "session_id": "someone-else"}, format="json")
        self.assertEqual(other.status_code, 404)
        own = self.client.post(url, {"rating": 1, "session_id": "test-session"}, format="json")
        self.assertEqual(own.status_code, 200)
        self.assertEqual(ChatLog.objects.get(pk=log_id).rating, 1)

    def test_empty_message_is_rejected(self):
        self.assertEqual(self.ask("   ").status_code, 400)
