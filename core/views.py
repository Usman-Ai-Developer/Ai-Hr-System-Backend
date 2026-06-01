from rest_framework.views import APIView
from rest_framework.response import Response
from jobs.models import JobPosting
from applications.models import Application
from accounts.models import User

class SystemStatusView(APIView):
    permission_classes = [] # Allow public or restrict to Admin

    def get(self, request):
        return Response({
            "stats": {
                "active_jobs": JobPosting.objects.filter(is_active=True).count(),
                "total_applicants": User.objects.filter(role='candidate').count(),
                "total_applications": Application.objects.count(),
            },
            "system": "Online",
            "version": "1.0.0-FYP"
        })