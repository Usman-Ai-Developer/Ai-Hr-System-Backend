from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, CandidateProfile, HRProfile


# =========================
# USER ADMIN
# =========================
class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ("email", "role", "is_staff", "is_active")
    list_filter = ("role", "is_staff", "is_active")

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal Info", {"fields": ("full_name", "role")}),
        ("Permissions", {
            "fields": (
                "is_staff",
                "is_active",
                "is_superuser",
                "groups",
                "user_permissions"
            )
        }),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "password1", "password2", "role"),
        }),
    )

    search_fields = ("email",)
    ordering = ("email",)


# =========================
# PROFILE ADMINS
# =========================
@admin.register(CandidateProfile)
class CandidateProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "phone", "total_experience")
    search_fields = ("user__email", "user__full_name")


@admin.register(HRProfile)
class HRProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "company_name", "department", "designation")
    search_fields = ("user__email", "user__full_name", "company_name")


# =========================
# REGISTER USER
# =========================
admin.site.register(User, CustomUserAdmin)