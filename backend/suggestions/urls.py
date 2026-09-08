from django.urls import path
from .views import (
    GenerateAISuggestionsView,
    DoctorPendingSuggestionsView,
    DoctorReviewSuggestionView,
    DoctorCreateSuggestionView,
    PatientSuggestionsView,
)

urlpatterns = [
    # Patient approved suggestions list
    path('', PatientSuggestionsView.as_view(), name='patient-suggestions-list'),

    # AI generation trigger
    path('generate-ai/', GenerateAISuggestionsView.as_view(), name='generate-ai-suggestions'),

    # Doctor review & authoring workflows
    path('doctor/pending/', DoctorPendingSuggestionsView.as_view(), name='doctor-pending-suggestions'),
    path('doctor/create/', DoctorCreateSuggestionView.as_view(), name='doctor-create-suggestion'),
    path('<int:pk>/review/', DoctorReviewSuggestionView.as_view(), name='doctor-review-suggestion'),
]
