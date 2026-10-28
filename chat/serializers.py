from rest_framework import serializers


class ChatRequestSerializer(serializers.Serializer):
    message = serializers.CharField(max_length=1000, trim_whitespace=True)
    session_id = serializers.CharField(max_length=64, required=False, allow_blank=True, default="")


class FeedbackSerializer(serializers.Serializer):
    rating = serializers.ChoiceField(choices=[1, -1])
    session_id = serializers.CharField(max_length=64)
