from rest_framework import serializers
from .models import Resume

class ResumeSerializer(serializers.ModelSerializer):
    candidate = serializers.PrimaryKeyRelatedField(read_only=True)   # ✅ make read-only

    class Meta:
        model = Resume
        fields = "__all__"
        read_only_fields = [
            "raw_text", "skills", "education", "experience",
            "certifications", "languages", "parse_status",
            "parse_error", "parsed_at",
        ]