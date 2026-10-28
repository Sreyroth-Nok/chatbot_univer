import logging

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from .models import ChatLog
from .serializers import ChatRequestSerializer, FeedbackSerializer
from .services.language import detect_language
from .services.messages import ERROR
from .services.rag import answer_question, save_rating

logger = logging.getLogger(__name__)


class PublicAPIView(APIView):
    # Public, anonymous endpoints: no login and no CSRF cookie needed
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]


class ChatView(PublicAPIView):
    """POST /api/chat/  {"message": "...", "session_id": "..."}"""

    throttle_scope = "chat"

    def post(self, request):
        serializer = ChatRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            result = answer_question(data["message"], channel=ChatLog.Channel.WEB, session_id=data["session_id"])
        except Exception:
            logger.exception("Chat request failed")
            lang = detect_language(data["message"])
            return Response({"error": ERROR[lang]}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        return Response(result.as_dict())


class FeedbackView(PublicAPIView):
    """POST /api/chat/<log_id>/feedback/  {"rating": 1 or -1, "session_id": "..."}"""

    throttle_scope = "feedback"

    def post(self, request, log_id):
        serializer = FeedbackSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        if not save_rating(log_id, data["rating"], data["session_id"]):
            return Response({"error": "Message not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response({"ok": True})
