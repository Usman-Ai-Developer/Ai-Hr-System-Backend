from django.db import models
import uuid


class Resume(models.Model):

    class Status(models.TextChoices):
        PENDING = "pending"
        PARSING = "parsing"
        PARSED  = "parsed"
        FAILED  = "failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    candidate = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="resumes"
    )

    file = models.FileField(upload_to="resumes/")

    raw_text = models.TextField(blank=True, null=True)

    skills = models.JSONField(default=list)
    education = models.JSONField(default=list)
    experience = models.JSONField(default=list)
    certifications = models.JSONField(default=list)
    languages = models.JSONField(default=list)

    parse_status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )

    parse_error = models.TextField(blank=True, null=True)

    parsed_at = models.DateTimeField(null=True, blank=True)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.candidate} - Resume"