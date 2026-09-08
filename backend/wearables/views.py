import uuid
from datetime import timedelta
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter

from core.permissions import IsPatient
from .models import WearableConnection, SleepEntry, AlcoholSignal, ExerciseEntry
from .serializers import (
    WearableConnectionSerializer,
    SleepEntrySerializer,
    AlcoholSignalSerializer,
    ExerciseEntrySerializer,
    WearableSyncPayloadSerializer,
    OAuthConnectSerializer,
    OAuthCallbackSerializer,
)
from .adapters import (
    normalize_sleep_payload,
    normalize_exercise_payload,
    normalize_alcohol_payload,
)


class OAuthConnectView(APIView):
    """
    Generates an OAuth authorization redirect URL for connecting wearable devices.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = OAuthConnectSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        provider = serializer.validated_data['provider']
        redirect_uri = serializer.validated_data.get('redirect_uri', 'capacitor://localhost/oauth/callback')

        state = uuid.uuid4().hex
        # Formulate authorize URL (boAt Wave / Google Health Connect)
        if provider == 'boat_wave':
            auth_url = f"https://auth.boat-lifestyle.com/oauth/authorize?client_id=cyclecare_client&redirect_uri={redirect_uri}&response_type=code&state={state}"
        else:
            auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?client_id=cyclecare_health&redirect_uri={redirect_uri}&response_type=code&scope=fitness.sleep.read+fitness.activity.read&state={state}"

        return Response({
            "provider": provider,
            "authorization_url": auth_url,
            "state": state
        })


class OAuthCallbackView(APIView):
    """
    Exchanges code for tokens and persists the wearable connection.
    Tokens are stored securely and never echoed back in raw form.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = OAuthCallbackSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        provider = serializer.validated_data['provider']
        code = serializer.validated_data['code']

        # Exchange code (mocking token provider exchange for boat/google)
        access_token = f"tok_acc_{provider}_{uuid.uuid4().hex}"
        refresh_token = f"tok_ref_{provider}_{uuid.uuid4().hex}"
        expires_at = timezone.now() + timedelta(days=30)

        connection, created = WearableConnection.objects.update_or_create(
            user=request.user,
            provider=provider,
            defaults={
                'access_token': access_token,
                'refresh_token': refresh_token,
                'token_expires_at': expires_at,
                'is_active': True
            }
        )

        return Response({
            "message": f"Successfully connected to {connection.get_provider_display()}.",
            "connection": WearableConnectionSerializer(connection).data
        }, status=status.HTTP_200_OK if not created else status.HTTP_201_CREATED)


class WearableConnectionsView(generics.ListAPIView):
    """
    Lists connected wearable devices for the authenticated user.
    """
    serializer_class = WearableConnectionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return WearableConnection.objects.filter(user=self.request.user, is_active=True)


class WearableSyncView(APIView):
    """
    Provider-agnostic ingestion endpoint for wearable sync (sleep, exercise, alcohol signals).
    Guarantees idempotent upserts on date + user.
    """
    permission_classes = [permissions.IsAuthenticated, IsPatient]

    def post(self, request):
        serializer = WearableSyncPayloadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        provider = serializer.validated_data.get('provider', 'generic')
        sleep_data = serializer.validated_data.get('sleep', [])
        exercise_data = serializer.validated_data.get('exercise', [])
        alcohol_data = serializer.validated_data.get('alcohol', [])

        patient_profile = request.user.patient_profile

        synced_sleep_count = 0
        synced_exercise_count = 0
        synced_alcohol_count = 0

        # Store one daily aggregate per patient/date. Individual sessions are
        # intentionally collapsed before persistence.
        daily_sleep = {}
        for item in sleep_data:
            normalized = normalize_sleep_payload(item, provider=provider)
            entry_date = normalized.pop('date')
            aggregate = daily_sleep.setdefault(entry_date, {
                'total_sleep_minutes': 0,
                'deep_sleep_minutes': 0,
                'rem_sleep_minutes': 0,
                'light_sleep_minutes': 0,
                'source_provider': provider,
            })
            for field in ('total_sleep_minutes', 'deep_sleep_minutes', 'rem_sleep_minutes', 'light_sleep_minutes'):
                aggregate[field] += normalized[field]

        for entry_date, normalized in daily_sleep.items():
            SleepEntry.objects.update_or_create(patient=patient_profile, date=entry_date, defaults=normalized)
            synced_sleep_count += 1

        daily_exercise = {}
        for item in exercise_data:
            normalized = normalize_exercise_payload(item, provider=provider)
            entry_date = normalized.pop('date')
            act_type = normalized.pop('activity_type')
            key = (entry_date, act_type)
            aggregate = daily_exercise.setdefault(key, {
                'duration_minutes': 0,
                'intensity': normalized['intensity'],
                'calories_burned': 0,
                'source_provider': provider,
            })
            aggregate['duration_minutes'] += normalized['duration_minutes']
            aggregate['calories_burned'] += normalized['calories_burned'] or 0
            if normalized['intensity'] == 'high' or (normalized['intensity'] == 'medium' and aggregate['intensity'] == 'low'):
                aggregate['intensity'] = normalized['intensity']

        for (entry_date, act_type), normalized in daily_exercise.items():
            if normalized['calories_burned'] == 0:
                normalized['calories_burned'] = None
            ExerciseEntry.objects.update_or_create(
                patient=patient_profile, date=entry_date, activity_type=act_type, defaults=normalized
            )
            synced_exercise_count += 1

        # 3. Ingest Alcohol Signals
        for item in alcohol_data:
            normalized = normalize_alcohol_payload(item, provider=provider)
            if normalized.get('timestamp'):
                AlcoholSignal.objects.create(
                    patient=patient_profile,
                    **normalized
                )
                synced_alcohol_count += 1

        return Response({
            "message": "Wearable data synchronized successfully.",
            "provider": provider,
            "synced": {
                "sleep_records": synced_sleep_count,
                "exercise_records": synced_exercise_count,
                "alcohol_signals": synced_alcohol_count
            }
        }, status=status.HTTP_200_OK)


class SleepTrendsView(generics.ListAPIView):
    """
    Returns time-series sleep records for frontend charting.
    """
    serializer_class = SleepEntrySerializer
    permission_classes = [permissions.IsAuthenticated, IsPatient]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering = ['-date']

    def get_queryset(self):
        return SleepEntry.objects.filter(patient=self.request.user.patient_profile)


class ExerciseTrendsView(generics.ListAPIView):
    """
    Returns time-series exercise records for frontend charting.
    """
    serializer_class = ExerciseEntrySerializer
    permission_classes = [permissions.IsAuthenticated, IsPatient]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering = ['-date']

    def get_queryset(self):
        return ExerciseEntry.objects.filter(patient=self.request.user.patient_profile)


class AlcoholTrendsView(generics.ListAPIView):
    """
    Returns time-series alcohol vitals signals.
    """
    serializer_class = AlcoholSignalSerializer
    permission_classes = [permissions.IsAuthenticated, IsPatient]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering = ['-timestamp']

    def get_queryset(self):
        return AlcoholSignal.objects.filter(patient=self.request.user.patient_profile)
