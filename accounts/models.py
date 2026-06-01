from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
import uuid

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255, blank=True, null=True)
    ROLE_CHOICES = (
        ('candidate', 'Candidate'),
        ('hr', 'HR'),
        ('admin', 'Admin'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='candidate')
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email

class CandidateProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='candidate_profile')
    phone = models.CharField(max_length=15, blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    summary = models.TextField(blank=True, null=True)
    total_experience = models.FloatField(default=0)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)


    def __str__(self):
        return self.user.email

class HRProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='hr_profile')
    phone = models.CharField(max_length=15, blank=True, null=True)
    company_name = models.CharField(max_length=255, blank=True, null=True)
    institute_name = models.CharField(max_length=255, blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    department = models.CharField(max_length=255, blank=True, null=True)
    designation = models.CharField(max_length=255, blank=True, null=True)
    summary = models.TextField(blank=True, null=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)

    def __str__(self):
        return self.user.email