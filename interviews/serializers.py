from rest_framework import serializers
from .models import InterviewSession, InterviewAnswer


class InterviewSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = InterviewSession
        fields = "__all__"


class InterviewAnswerSerializer(serializers.ModelSerializer):
    video_file = serializers.FileField(write_only=True, required=False)
    audio_file = serializers.FileField(write_only=True, required=False)

    class Meta:
        model = InterviewAnswer
        fields = "__all__"
        read_only_fields = [
            "transcript",
            "confidence_score",
            "vocal_clarity_score",
            "english_score",
            "relevance_score",
            "communication_score",
            "gemini_feedback",
            "is_scored",
            "scored_at",
            "video_url",
            "audio_url",
        ]

    def create(self, validated_data):
        video_file = validated_data.pop("video_file", None)
        audio_file = validated_data.pop("audio_file", None)
        answer = super().create(validated_data)
        if video_file:
            answer.video_url = video_file
        if audio_file:
            answer.audio_url = audio_file
        answer.save()
        return answer