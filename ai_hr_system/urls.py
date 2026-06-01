from django.contrib import admin
from django.urls import path, include
from core.health import health_check
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse

def home(request):
    return JsonResponse({
        "message": "AI Interview System API Running",
        "status": "OK",
        "endpoints": {
            "auth": "/api/auth/",
            "jobs": "/api/jobs/",
            "applications": "/api/applications/",
            "interviews": "/api/interviews/",
            "analysis": "/api/analysis/",
        }
    })

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home),
    
    # Modular API Routes
    path('api/health/', health_check, name='health-check'),
    path('api/auth/', include('accounts.urls')),
    path('api/jobs/', include('jobs.urls')),
    path('api/applications/', include('applications.urls')),
    path('api/resumes/', include('resumes.urls')),
    path('api/interviews/', include('interviews.urls')),
    path('api/analysis/', include('ai_analysis.urls')),

]

# ✅ Allow serving uploaded files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)