from django.urls import path
from .views import (
    OAuthConnectView,
    OAuthCallbackView,
    WearableConnectionsView,
    WearableSyncView,
    SleepTrendsView,
    ExerciseTrendsView,
    AlcoholTrendsView,
)

urlpatterns = [
    # OAuth flow
    path('oauth/connect/', OAuthConnectView.as_view(), name='wearable-oauth-connect'),
    path('oauth/callback/', OAuthCallbackView.as_view(), name='wearable-oauth-callback'),
    path('connections/', WearableConnectionsView.as_view(), name='wearable-connections'),

    # Provider-agnostic Sync Webhook/Endpoint
    path('sync/', WearableSyncView.as_view(), name='wearable-sync'),

    # Time-series Trend Endpoints
    path('sleep/trends/', SleepTrendsView.as_view(), name='sleep-trends'),
    path('exercise/trends/', ExerciseTrendsView.as_view(), name='exercise-trends'),
    path('alcohol/trends/', AlcoholTrendsView.as_view(), name='alcohol-trends'),
]
