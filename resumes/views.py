# resumes/views.py
from rest_framework import viewsets, permissions
from .models import Resume
from .serializers import ResumeSerializer
from .tasks import parse_resume_task


class ResumeViewSet(viewsets.ModelViewSet):
    serializer_class = ResumeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Resume.objects.filter(candidate=self.request.user)

    def perform_create(self, serializer):
        resume = serializer.save(candidate=self.request.user)
        # Trigger async AI parsing
        parse_resume_task.delay(str(resume.id))