from django.urls import path

from .views import ChatView, FeedbackView

urlpatterns = [
    path("chat/", ChatView.as_view(), name="chat"),
    path("chat/<int:log_id>/feedback/", FeedbackView.as_view(), name="chat-feedback"),
]
