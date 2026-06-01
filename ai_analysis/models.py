from django.db import models

class AIAnalysis(models.Model):
    interview = models.OneToOneField(
        'interviews.InterviewSession',
        on_delete=models.CASCADE,
        related_name="analysis"
    )

    # 📊 Detailed Scores (Matched to your tasks.py logic)
    avg_english_score = models.FloatField(default=0.0)
    avg_relevance_score = models.FloatField(default=0.0)
    communication_score = models.FloatField(default=0.0)  # Added
    technical_score = models.FloatField(default=0.0)      # Added
    confidence_score = models.FloatField(default=0.0)  # ✅ Add this field


    # 🧠 AI Insights
    strengths = models.TextField(blank=True, null=True)
    weaknesses = models.TextField(blank=True, null=True)
    overall_summary = models.TextField(blank=True, null=True)
    candidate_feedback = models.TextField(blank=True, null=True)
    
    # 📝 Raw breakdown (Great for the frontend charts)
    detailed_breakdown = models.JSONField(default=dict, blank=True)

    # 🎯 Final Decision
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('shortlisted', 'Shortlisted'),
            ('rejected', 'Rejected')
        ],
        default='pending'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Analysis - {self.interview.id}"