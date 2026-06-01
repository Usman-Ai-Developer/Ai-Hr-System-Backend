# jobs/views.py
from rest_framework import viewsets, permissions
from .models import JobPosting
from .serializers import JobSerializer
from .permissions import IsHRUser
from rest_framework.decorators import action
from rest_framework.response import Response
from applications.models import Application
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Avg
from resumes.models import Resume

class JobPostingViewSet(viewsets.ModelViewSet):
    """
    Handles Job Postings. 
    - Public: View active jobs.
    - HR Only: Create, Edit, Delete jobs.
    """
    queryset = JobPosting.objects.filter(is_active=True).order_by("-created_at")
    serializer_class = JobSerializer

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [permissions.IsAuthenticated(), IsHRUser()]
        return [permissions.AllowAny()]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    # jobs/views.py (inside JobPostingViewSet)
    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated])
    def apply(self, request, pk=None):
        job = self.get_object()
        if Application.objects.filter(candidate=request.user, job=job).exists():
            return Response({"error": "Already applied for this position."}, status=400)

        from resumes.models import Resume
        resume = Resume.objects.filter(candidate=request.user).order_by('-created_at').first()
        cover_letter = request.data.get('cover_letter', '')

        application = Application.objects.create(
            candidate=request.user,
            job=job,
            resume=resume,
            cover_letter=cover_letter
        )

        try:
            from interviews.tasks import generate_interview_questions_task
            generate_interview_questions_task.delay(str(application.id))
        except ImportError:
            pass

        return Response({"message": "Application submitted successfully."}, status=201)
    
    
class HRDashboardSummary(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != 'hr':
            return Response({"error": "Unauthorized"}, status=403)

        total_jobs = JobPosting.objects.filter(created_by=request.user).count()
        total_applicants = Application.objects.filter(job__created_by=request.user).count()
        top_matches = Application.objects.filter(
            job__created_by=request.user, 
            ai_score__gte=80
        ).count()

        recent_jobs = JobPosting.objects.filter(created_by=request.user).annotate(
            applicant_count=Count('applications'),
            avg_score=Avg('applications__ai_score')
        ).order_by('-created_at')[:5]

        jobs_data = [{
            "id": job.id,
            "title": job.title,
            "applicant_count": job.applicant_count,
            "avg_score": round(job.avg_score or 0, 1),
            "status": job.status
        } for job in recent_jobs]

        return Response({
            "stats": {
                "totalJobs": total_jobs,
                "totalApplicants": total_applicants,
                "topMatches": top_matches
            },
            "recent_jobs": jobs_data
        })