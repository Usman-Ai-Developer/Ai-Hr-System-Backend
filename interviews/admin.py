from django.contrib import admin
from .models import InterviewSession, InterviewAnswer


admin.site.register(InterviewSession)
admin.site.register(InterviewAnswer)