from django.db import models
import uuid


class InterviewSession(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    application = models.OneToOneField(
        "applications.Application",
        on_delete=models.CASCADE,
        related_name="interview_session"
    )

    generated_questions = models.JSONField(default=list)

    is_completed = models.BooleanField(default=False)

    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Interview - {self.application}"


class InterviewAnswer(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    session = models.ForeignKey(
        InterviewSession,
        on_delete=models.CASCADE,
        related_name="answers"
    )

    question_order = models.IntegerField()
    question_text = models.TextField()

    audio_url = models.FileField(upload_to='interview_audio/', blank=True, null=True)
    video_url = models.FileField(upload_to='interview_videos/', blank=True, null=True)

    transcript = models.TextField(blank=True, null=True)

    transcript_confidence = models.FloatField(default=0.0)

    # AI Scores
    confidence_score = models.FloatField(default=0.0)
    vocal_clarity_score = models.FloatField(default=0.0)
    english_score = models.FloatField(default=0.0)
    relevance_score = models.FloatField(default=0.0)

    communication_score = models.FloatField(default=0.0)

    gemini_feedback = models.TextField(blank=True, null=True)

    is_scored = models.BooleanField(default=False)

    scored_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def compute_communication_score(self):
        self.communication_score = (
            self.english_score * 0.4 +
            self.relevance_score * 0.4 +
            self.vocal_clarity_score * 0.1 +
            self.confidence_score * 0.1
        )

    def __str__(self):
        return f"Q{self.question_order} - {self.session_id}"