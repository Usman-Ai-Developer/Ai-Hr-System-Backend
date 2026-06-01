# ai_analysis/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from .models import AIAnalysis
from .tasks import evaluate_interview_from_file_task  # ✅ updated import
from interviews.models import InterviewSession
from core.permissions import IsHR


class AnalysisDetailView(APIView):
    """
    Retrieve the AI Analysis results for a specific interview session.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, interview_id):
        analysis = get_object_or_404(AIAnalysis, interview_id=interview_id)

        data = {
            "interview_id": str(analysis.interview.id),
            "scores": {
                "english": analysis.avg_english_score,
                "relevance": analysis.avg_relevance_score,
                "communication": analysis.communication_score,
                "technical": analysis.technical_score,
                "confidence": analysis.confidence_score,  # added
            },
            "insights": {
                "strengths": analysis.strengths,
                "weaknesses": analysis.weaknesses,
                "summary": analysis.overall_summary,
                "feedback": analysis.candidate_feedback,
            },
            "detailed_breakdown": analysis.detailed_breakdown,
            "status": analysis.status,
            "created_at": analysis.created_at
        }

        return Response(data, status=status.HTTP_200_OK)


class TriggerAnalysisView(APIView):
    """
    Manually trigger the Celery task to analyze an interview.
    """
    permission_classes = [IsAuthenticated, IsHR]

    def post(self, request, interview_id):
        interview = get_object_or_404(InterviewSession, id=interview_id)
        evaluate_interview_from_file_task.delay(str(interview.id))  # ✅ updated task
        return Response(
            {"message": "Analysis task has been queued."},
            status=status.HTTP_202_ACCEPTED
        )