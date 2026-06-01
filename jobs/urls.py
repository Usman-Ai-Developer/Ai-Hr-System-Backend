from django.urls import path, include # Add include here
from rest_framework.routers import DefaultRouter
from .views import JobPostingViewSet, HRDashboardSummary

router = DefaultRouter()
router.register(r"", JobPostingViewSet, basename="jobs")

urlpatterns = [
    path('dashboard-summary/', HRDashboardSummary.as_view(), name='hr-dashboard-summary'),
    path('', include(router.urls)), # Wrap it in path() and include()
]