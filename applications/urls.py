# applications/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ApplicationViewSet, ApplicationHRUpdateView, DeleteInterviewView

router = DefaultRouter()
router.register(r"", ApplicationViewSet, basename="applications")

urlpatterns = [
    path("", include(router.urls)),
    path("<uuid:pk>/status/", ApplicationHRUpdateView.as_view()),
    path("<uuid:pk>/delete_interview/", DeleteInterviewView.as_view()),
]