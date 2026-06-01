# accounts/serializers.py
from rest_framework import serializers
from .models import User, CandidateProfile, HRProfile
from resumes.models import Resume
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
import logging

logger = logging.getLogger(__name__)


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["email"] = user.email
        token["role"] = user.role
        token["full_name"] = user.full_name
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        # Add user info to the response body
        data['role'] = self.user.role
        data['email'] = self.user.email
        data['full_name'] = self.user.full_name
        data['id'] = str(self.user.id)
        return data


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    resume = serializers.FileField(write_only=True, required=False)
    full_name = serializers.CharField(required=True)
    institute_name = serializers.CharField(required=False)

    class Meta:
        model = User
        fields = ["email", "password", "role", "full_name", "institute_name", "resume"]

    def validate(self, data):
        role = data.get("role")
        if role == "candidate" and not data.get("resume"):
            raise serializers.ValidationError({"resume": "Resume is required for candidates"})
        if role == "hr" and not data.get("institute_name"):
            raise serializers.ValidationError({"institute_name": "Institute name is required for HR"})
        return data

    def create(self, validated_data):
        from resumes.tasks import parse_resume_task

        resume_file = validated_data.pop("resume", None)
        institute_name = validated_data.pop("institute_name", None)
        
        user = User.objects.create_user(
            email=validated_data["email"],
            password=validated_data["password"],
            role=validated_data["role"],
            full_name=validated_data.get("full_name")
        )

        if user.role == "candidate":
            CandidateProfile.objects.create(user=user)
            if resume_file:
                resume = Resume.objects.create(candidate=user, file=resume_file)
                logger.info(f"📤 Triggering parse_resume_task for resume {resume.id}")
                print(f"📤 Triggering parse_resume_task for resume {resume.id}")
                parse_resume_task.delay(str(resume.id))
        elif user.role == "hr":
            HRProfile.objects.create(user=user, institute_name=institute_name)

        return user