# applications/views.py
from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from .models import Application
from .serializers import ApplicationSerializer
from core.permissions import IsHR
from interviews.models import InterviewSession


class ApplicationViewSet(viewsets.ModelViewSet):
    serializer_class = ApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role in ['hr', 'admin']:
            return Application.objects.all()
        return Application.objects.filter(candidate=user)

    def perform_create(self, serializer):
        user = self.request.user
        job = serializer.validated_data.get("job")

        if Application.objects.filter(candidate=user, job=job).exists():
            raise ValidationError("You have already applied for this position.")

        application = serializer.save(candidate=user)

        # Trigger interview question generation
        try:
            from interviews.tasks import generate_interview_questions_task
            generate_interview_questions_task.delay(str(application.id))
        except ImportError:
            pass


class DeleteInterviewView(APIView):
    """
    Standalone view to delete the interview session (and all related data)
    for a given application. Only HR (or admin) can access.
    """
    permission_classes = [permissions.IsAuthenticated, IsHR]

    def post(self, request, pk):
        try:
            application = Application.objects.get(id=pk)
        except Application.DoesNotExist:
            return Response(
                {"error": "Application not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        session = InterviewSession.objects.filter(application=application).first()
        if session:
            session.delete()  # cascades to answers, analysis, and media files
            return Response({"message": "Interview data deleted successfully."})
        return Response(
            {"message": "No interview session found."},
            status=status.HTTP_404_NOT_FOUND
        )


class ApplicationHRUpdateView(APIView):
    """
    Update application status (shortlisted, rejected, hired, etc.)
    Only HR (or admin) can access.
    """
    permission_classes = [permissions.IsAuthenticated, IsHR]

    def patch(self, request, pk):
        try:
            app = Application.objects.get(id=pk)
        except Application.DoesNotExist:
            return Response({"error": "Application not found"}, status=status.HTTP_404_NOT_FOUND)

        app.status = request.data.get("status", app.status)
        app.save()
        return Response({"message": "Application status updated successfully."})
    