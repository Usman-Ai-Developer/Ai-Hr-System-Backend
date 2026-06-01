# semantic_matching/models.py
import uuid
from django.db import models


class ResumeJobMatch(models.Model):
    """
    Stores the semantic similarity between a candidate's resume and a job posting.
    Created automatically when a candidate applies.

    Vectors are stored as comma-separated floats (portable, no pgvector needed).
    When the project migrates to PostgreSQL + pgvector, these can be replaced
    with proper vector columns for ANN search.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    application = models.OneToOneField(
        "applications.Application",
        on_delete=models.CASCADE,
        related_name="semantic_match"
    )

    # Cosine similarity score scaled to 0–100
    semantic_score = models.FloatField(default=0.0)

    # Serialised embedding vectors (384-dim MiniLM → ~2KB each as CSV floats)
    resume_embedding = models.TextField(blank=True, null=True)
    job_embedding    = models.TextField(blank=True, null=True)

    # Human-readable breakdown stored for the report/dashboard
    matched_skills   = models.JSONField(default=list)   # skills in both resume & job
    missing_skills   = models.JSONField(default=list)   # job skills absent from resume
    extra_skills     = models.JSONField(default=list)   # candidate skills not required
    experience_gap   = models.FloatField(default=0.0)   # years short (negative = surplus)

    computed_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Resume–Job Match"
        verbose_name_plural = "Resume–Job Matches"

    def __str__(self):
        return (
            f"{self.application.candidate.email} → "
            f"{self.application.job.title} "
            f"({self.semantic_score:.1f}%)"
        )
