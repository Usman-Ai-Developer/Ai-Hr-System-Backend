# ai_analysis/urls.py
from django.urls import path
from .views import AnalysisDetailView, TriggerAnalysisView

urlpatterns = [
    path('results/<uuid:interview_id>/', AnalysisDetailView.as_view(), name='analysis-detail'),
    path('trigger/<uuid:interview_id>/', TriggerAnalysisView.as_view(), name='trigger-analysis'),
]



