from django.db import models
import uuid
from accounts.models import User

class JobPosting(models.Model):
    # UUIDs are great for security in URLs
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    title = models.CharField(max_length=255)
    company_name = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    description = models.TextField()
    
    # AI Matching Fields
    experience_required = models.IntegerField(default=0)
    skills_required = models.JSONField(default=list) # e.g. ["Python", "React"]
    requirements = models.TextField(blank=True, null=True) # Full text for AI to read
    department = models.CharField(max_length=100, blank=True, null=True)

    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="jobs"
    )

    # Added 'status' for the Dashboard table logic
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('closed', 'Closed'),
        ('draft', 'Draft'),
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    is_active = models.BooleanField(default=True) # Secondary toggle

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} at {self.company_name}"