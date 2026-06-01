# applications/admin.py
from django.contrib import admin
from .models import Application
from interviews.tasks import generate_interview_questions_task


@admin.action(description="Generate interview questions for selected applications")
def generate_questions(modeladmin, request, queryset):
    count = 0
    for app in queryset:
        if not hasattr(app, 'interview_session'):
            generate_interview_questions_task.delay(str(app.id))
            count += 1
    modeladmin.message_user(request, f"Triggered question generation for {count} application(s).")


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ("candidate", "job", "status", "created_at")
    list_filter = ("status",)
    actions = [generate_questions]