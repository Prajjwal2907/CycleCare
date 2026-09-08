from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    RegisterView,
    LoginView,
    UserProfileView,
    ConsentGrantListView,
    GrantConsentView,
    RevokeConsentView,
    DoctorDirectoryView,
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='account-register'),
    path('login/', LoginView.as_view(), name='account-login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('profile/', UserProfileView.as_view(), name='account-profile'),
    path('consent/', ConsentGrantListView.as_view(), name='consent-list'),
    path('consent/grant/', GrantConsentView.as_view(), name='consent-grant'),
    path('consent/revoke/', RevokeConsentView.as_view(), name='consent-revoke'),
    path('doctors/', DoctorDirectoryView.as_view(), name='doctor-directory'),
]
