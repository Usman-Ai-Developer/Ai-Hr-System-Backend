from django.urls import path
from .views import (
    InterviewSessionView,
    InterviewStartView,
    InterviewCompleteView,
    AnswerSubmitView,
    AnswerListCandidateView,
    AnswerListHRView,
)

urlpatterns = [

    # ================= SESSION =================
    path("session/<uuid:application_id>/", InterviewSessionView.as_view()),

    # ================= START =================
    path("start/<uuid:application_id>/", InterviewStartView.as_view()),

    # ================= COMPLETE =================
    path("complete/<uuid:application_id>/", InterviewCompleteView.as_view()),

    # ================= ANSWERS =================
    path("answers/", AnswerSubmitView.as_view()),
]