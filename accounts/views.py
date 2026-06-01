# accounts/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.decorators import api_view, permission_classes
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import MyTokenObtainPairSerializer, RegisterSerializer
from .models import User, CandidateProfile, HRProfile
from applications.models import Application
from interviews.models import InterviewSession
from core.permissions import IsHR
from jobs.models import JobPosting
from ai_analysis.models import AIAnalysis


class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        refresh = RefreshToken.for_user(user)
        return Response({
            "message": "User created successfully",
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "role": user.role
        }, status=status.HTTP_201_CREATED)


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        data = {
            "id": str(user.id),
            "email": user.email,
            "role": user.role,
            "full_name": user.full_name,
        }
        if user.role == "candidate":
            profile = getattr(user, 'candidate_profile', None)
            if profile:
                data.update({
                    "phone": profile.phone,
                    "location": profile.location,
                    "summary": profile.summary,
                    "total_experience": profile.total_experience,
                    "avatar": profile.avatar.url if profile.avatar else None,
                })
        elif user.role == "hr":
            profile = getattr(user, 'hr_profile', None)
            if profile:
                data.update({
                    "phone": profile.phone,
                    "company_name": profile.company_name,
                    "institute_name": profile.institute_name,
                    "location": profile.location,
                    "department": profile.department,
                    "designation": profile.designation,
                    "summary": profile.summary,
                    "avatar": profile.avatar.url if profile.avatar else None,   # ✅ new

                })
        return Response(data)

    def patch(self, request):
        user = request.user
        data = request.data

        if 'full_name' in data:
            user.full_name = data['full_name']
            user.save()

        if user.role == "candidate":
            profile, _ = CandidateProfile.objects.get_or_create(user=user)
            if 'phone' in data:
                profile.phone = data['phone']
            if 'location' in data:
                profile.location = data['location']
            if 'summary' in data:
                profile.summary = data['summary']
            if 'total_experience' in data:
                try:
                    profile.total_experience = float(data['total_experience'])
                except (ValueError, TypeError):
                    pass
            profile.save()

        elif user.role == "hr":
            profile, _ = HRProfile.objects.get_or_create(user=user)
            if 'phone' in data:
                profile.phone = data['phone']
            if 'company_name' in data:
                profile.company_name = data['company_name']
            if 'institute_name' in data:
                profile.institute_name = data['institute_name']
            if 'location' in data:
                profile.location = data['location']
            if 'department' in data:
                profile.department = data['department']
            if 'designation' in data:
                profile.designation = data['designation']
            if 'summary' in data:
                profile.summary = data['summary']
            profile.save()

        return Response({"message": "Profile updated successfully"}, status=status.HTTP_200_OK)


class MeAvatarView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        if user.role == 'candidate':
            profile = user.candidate_profile
        elif user.role == 'hr':
            profile = user.hr_profile
        else:
            return Response({"error": "Invalid role"}, status=403)

        if 'avatar' not in request.FILES:
            return Response({"error": "No avatar file provided"}, status=400)

        profile.avatar = request.FILES['avatar']
        profile.save()
        return Response({"avatar": profile.avatar.url if profile.avatar else None})

class LogoutView(APIView):
    def post(self, request):
        return Response({"message": "Logged out successfully"})


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsHR])
def hr_dashboard(request):
    hr = request.user
    jobs = JobPosting.objects.filter(created_by=hr)
    response_data = []

    for job in jobs:
        applications = Application.objects.filter(job=job).exclude(status='rejected')
        applicants = []
        for app in applications:
            interview = InterviewSession.objects.filter(application=app).first()
            score = None
            if interview:
                analysis = AIAnalysis.objects.filter(interview=interview).first()
                if analysis:
                    score = analysis.communication_score

            if score is None:
                status_label = "Not Attempted"
            elif score >= 75:
                status_label = "Excellent"
            elif score >= 50:
                status_label = "Good"
            else:
                status_label = "Weak"

            applicants.append({
                "application_id": str(app.id),
                "candidate_name": app.candidate.full_name,
                "candidate_email": app.candidate.email,
                "job_title": job.title,
                "interview_done": app.status == "interview",
                "score": score,
                "status": app.status,
                "performance_label": status_label,
            })

        response_data.append({
            "job_id": str(job.id),
            "title": job.title,
            "company_name": job.company_name,
            "location": job.location,
            "is_active": job.is_active,
            "total_applicants": applications.count(),
            "interview_done_count": applications.filter(status="interview").count(),
            "applicants": applicants,
        })

    return Response(response_data)