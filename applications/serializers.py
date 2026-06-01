# applications/serializers.py
from rest_framework import serializers
from .models import Application


class ApplicationSerializer(serializers.ModelSerializer):
    candidate_name = serializers.CharField(source='candidate.full_name', read_only=True)
    candidate_email = serializers.CharField(source='candidate.email', read_only=True)
    job_title = serializers.CharField(source='job.title', read_only=True)
    job_company = serializers.CharField(source='job.company_name', read_only=True)
    job_location = serializers.CharField(source='job.location', read_only=True)
    interview_session_id = serializers.SerializerMethodField()
    interview_started_at = serializers.SerializerMethodField()
    interview_completed = serializers.SerializerMethodField()

    class Meta:
        model = Application
        fields = '__all__'
        read_only_fields = ['candidate', 'status', 'ai_score', 'created_at', 'updated_at']

    def get_interview_session_id(self, obj):
        session = getattr(obj, 'interview_session', None)
        return str(session.id) if session else None

    def get_interview_started_at(self, obj):
        session = getattr(obj, 'interview_session', None)
        return session.started_at if session else None

    def get_interview_completed(self, obj):
        session = getattr(obj, 'interview_session', None)
        return session.is_completed if session else False