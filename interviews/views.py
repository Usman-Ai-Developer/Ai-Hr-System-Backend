# interviews/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from django.utils import timezone

from .models import InterviewSession, InterviewAnswer
from .serializers import InterviewSessionSerializer, InterviewAnswerSerializer
from core.permissions import IsCandidate, IsHR


class InterviewSessionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, application_id):
        session = InterviewSession.objects.filter(application_id=application_id).first()
        if not session:
            return Response(
                {"error": "Interview session is being prepared by AI. Please wait."},
                status=404
            )
        # Candidates can only view their own sessions
        if request.user.role == "candidate" and session.application.candidate != request.user:
            return Response({"error": "Forbidden"}, status=403)

        return Response({
            "id": str(session.id),
            "application": str(session.application_id),
            "generated_questions": session.generated_questions,
            "is_completed": session.is_completed,
            "started_at": session.started_at,
            "completed_at": session.completed_at,
        })


class InterviewStartView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsCandidate]

    def post(self, request, application_id):
        # Bug fix #3: use filter+first instead of bare .get() to avoid unhandled DoesNotExist
        session = InterviewSession.objects.filter(application_id=application_id).first()
        if not session:
            return Response(
                {"error": "Interview session not found. It may still be preparing."},
                status=404
            )
        # Bug fix #4: verify this candidate owns this interview
        if session.application.candidate != request.user:
            return Response({"error": "Forbidden"}, status=403)

        if session.started_at:
            return Response({"message": "Interview already started."}, status=400)

        session.started_at = timezone.now()
        session.save()
        return Response({"message": "Interview started"})


class InterviewCompleteView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsCandidate]

    def post(self, request, application_id):
        # Bug fix #3: use filter+first instead of bare .get() to avoid unhandled DoesNotExist
        session = InterviewSession.objects.filter(application_id=application_id).first()
        if not session:
            return Response(
                {"error": "Interview session not found."},
                status=404
            )
        # Bug fix #4: verify this candidate owns this interview
        if session.application.candidate != request.user:
            return Response({"error": "Forbidden"}, status=403)

        if session.is_completed:
            return Response({"message": "Interview already completed."}, status=400)

        session.is_completed = True
        session.completed_at = timezone.now()
        session.save()

        from ai_analysis.tasks import evaluate_interview_from_file_task
        evaluate_interview_from_file_task.delay(str(session.id))

        return Response({"message": "Interview completed. AI is generating your final report."})


class AnswerSubmitView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsCandidate]

    def post(self, request):
        serializer = InterviewAnswerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Bug fix #4: verify this candidate owns the session they're submitting to
        session_id = serializer.validated_data.get("session").id if hasattr(serializer.validated_data.get("session"), "id") else serializer.validated_data.get("session")
        try:
            session = InterviewSession.objects.get(id=session_id)
        except InterviewSession.DoesNotExist:
            return Response({"error": "Interview session not found."}, status=404)

        if session.application.candidate != request.user:
            return Response({"error": "Forbidden"}, status=403)

        if session.is_completed:
            return Response({"error": "Cannot submit answers to a completed interview."}, status=400)

        answer = serializer.save()
        return Response({"message": "Answer submitted", "id": answer.id})


class AnswerListCandidateView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsCandidate]

    def get(self, request, application_id):
        # Bug fix #3 & #9: safe lookup + ownership check
        session = InterviewSession.objects.filter(application_id=application_id).first()
        if not session:
            return Response({"error": "Interview session not found."}, status=404)
        if session.application.candidate != request.user:
            return Response({"error": "Forbidden"}, status=403)
        answers = session.answers.all()
        return Response(InterviewAnswerSerializer(answers, many=True).data)


class AnswerListHRView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsHR]

    def get(self, request, session_id):
        session = InterviewSession.objects.filter(id=session_id).first()
        if not session:
            return Response({"error": "Interview session not found."}, status=404)
        answers = session.answers.all()
        return Response(InterviewAnswerSerializer(answers, many=True).data)
