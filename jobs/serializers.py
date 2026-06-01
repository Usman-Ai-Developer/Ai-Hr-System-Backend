# jobs/serializers.py
from rest_framework import serializers
from .models import JobPosting
from applications.models import Application


class ApplicationMiniSerializer(serializers.ModelSerializer):
    candidate_name = serializers.CharField(source="candidate.full_name", read_only=True)
    candidate_email = serializers.CharField(source="candidate.email", read_only=True)

    class Meta:
        model = Application
        fields = ["id", "candidate_name", "candidate_email", "status"]


class JobSerializer(serializers.ModelSerializer):
    applicants = serializers.SerializerMethodField()
    created_by_name = serializers.CharField(source="created_by.email", read_only=True)
    created_by = serializers.PrimaryKeyRelatedField(read_only=True)  # ✅ added

    class Meta:
        model = JobPosting
        fields = "__all__"
        read_only_fields = ["created_by", "created_at", "updated_at"]  # ✅ ensure this line exists

    def get_applicants(self, obj):
        apps = Application.objects.filter(job=obj)
        return ApplicationMiniSerializer(apps, many=True).data