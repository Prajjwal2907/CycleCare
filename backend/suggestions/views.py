from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter

from core.permissions import IsPatient, IsDoctor, HasActiveConsent
from core.ml_client import ml_client, MLServiceError, MLServiceTimeoutError
from accounts.models import ConsentGrant, PatientProfile
from cycles.models import CycleEntry
from cycles.services import calculate_cycle_metrics
from wearables.models import SleepEntry, ExerciseEntry, AlcoholSignal
from django.db.models import Avg, Count, Sum
from .models import Suggestion
from .serializers import (
    SuggestionSerializer,
    DoctorSuggestionCreateSerializer,
    DoctorSuggestionReviewSerializer,
)


def _json_safe_records(records):
    """Convert date and datetime values returned by Django into JSON values."""
    return [
        {
            key: value.isoformat() if hasattr(value, 'isoformat') else value
            for key, value in record.items()
        }
        for record in records
    ]


def _rounded_stats(stats):
    return {
        key: round(value, 1) if isinstance(value, float) else (value or 0)
        for key, value in stats.items()
    }


class GenerateAISuggestionsView(APIView):
    """
    Gathers patient's recent cycle, sleep, exercise, and food tracking data,
    calls ml-service AI suggestion engine, and persists suggestions as status='pending'.
    Can be triggered by the patient or by a consented doctor.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        if user.role == 'patient':
            patient_profile = user.patient_profile
        elif user.role == 'doctor':
            patient_id = request.data.get('patient_id')
            if not patient_id:
                return Response({"detail": "patient_id is required when invoked by a doctor."}, status=status.HTTP_400_BAD_REQUEST)
            if not ConsentGrant.objects.filter(patient_id=patient_id, doctor=user.doctor_profile, is_active=True).exists():
                return Response({"detail": "You do not have active consent for this patient."}, status=status.HTTP_403_FORBIDDEN)
            patient_profile = PatientProfile.objects.get(id=patient_id)
        else:
            return Response({"detail": "Invalid role."}, status=status.HTTP_400_BAD_REQUEST)

        # Only aggregate statistics are sent to the ML service. Raw health,
        # session, and food records never cross this service boundary.
        cycle_metrics = calculate_cycle_metrics(patient_profile)
        sleep_stats = SleepEntry.objects.filter(patient=patient_profile).aggregate(
            days_tracked=Count('id'), average_sleep_minutes=Avg('total_sleep_minutes'),
            average_deep_sleep_minutes=Avg('deep_sleep_minutes')
        )
        exercise_stats = ExerciseEntry.objects.filter(patient=patient_profile).aggregate(
            activity_days=Count('date', distinct=True), total_activity_minutes=Sum('duration_minutes'),
            average_activity_minutes=Avg('duration_minutes')
        )
        alcohol_stats = AlcoholSignal.objects.filter(patient=patient_profile).aggregate(
            signals_tracked=Count('id'),
            average_confidence=Avg('confidence_score'),
        )

        payload = {
            "patient_id": patient_profile.id,
            "dietary_preference": patient_profile.dietary_preference,
            "cycle_summary": {
                "total_entries": cycle_metrics['total_entries'],
                "average_duration_days": cycle_metrics['average_duration_days'],
                "average_gap_days": cycle_metrics['average_gap_days'],
            },
            "sleep_summary": _rounded_stats(sleep_stats),
            "exercise_summary": _rounded_stats(exercise_stats),
            "alcohol": {
                "signals_tracked": alcohol_stats['signals_tracked'] or 0,
                "average_confidence": round(alcohol_stats['average_confidence'], 2) if alcohol_stats['average_confidence'] is not None else 0,
            }
        }

        try:
            ai_suggestions = ml_client.generate_suggestions(payload)
        except MLServiceTimeoutError:
            return Response(
                {"detail": "ML suggestion generation service timed out."},
                status=status.HTTP_504_GATEWAY_TIMEOUT
            )
        except MLServiceError as e:
            return Response(
                {"detail": f"ML suggestion generation service error: {str(e)}"},
                status=status.HTTP_502_BAD_GATEWAY
            )

        created_suggestions = []
        for item in ai_suggestions:
            sug = Suggestion.objects.create(
                patient=patient_profile,
                source='ai',
                status='pending',
                category=item.get('category', 'lifestyle'),
                text=item.get('text', '')
            )
            created_suggestions.append(sug)

        return Response({
            "message": f"Generated {len(created_suggestions)} AI suggestions pending doctor review.",
            "suggestions": SuggestionSerializer(created_suggestions, many=True).data
        }, status=status.HTTP_201_CREATED)


class DoctorPendingSuggestionsView(generics.ListAPIView):
    """
    Returns pending AI suggestions across all patients who have active consent with the logged-in doctor.
    """
    serializer_class = SuggestionSerializer
    permission_classes = [permissions.IsAuthenticated, IsDoctor]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['category', 'patient']
    ordering = ['-created_at']

    def get_queryset(self):
        doctor_profile = self.request.user.doctor_profile
        # Find all patients with active consent
        consented_patient_ids = ConsentGrant.objects.filter(
            doctor=doctor_profile,
            is_active=True
        ).values_list('patient_id', flat=True)

        return Suggestion.objects.filter(
            patient_id__in=consented_patient_ids,
            status='pending'
        ).select_related('patient__user', 'doctor__user')


class DoctorReviewSuggestionView(APIView):
    """
    Allows a doctor to approve, reject, or edit a pending AI suggestion.
    Enforces active consent for the patient.
    """
    permission_classes = [permissions.IsAuthenticated, IsDoctor]

    def patch(self, request, pk):
        try:
            suggestion = Suggestion.objects.select_related('patient').get(pk=pk)
        except Suggestion.DoesNotExist:
            return Response({"detail": "Suggestion not found."}, status=status.HTTP_404_NOT_FOUND)

        doctor_profile = request.user.doctor_profile

        # Verify doctor consent for this patient
        if not ConsentGrant.objects.filter(patient=suggestion.patient, doctor=doctor_profile, is_active=True).exists():
            return Response(
                {"detail": "You do not have active consent for this patient."},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = DoctorSuggestionReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_status = serializer.validated_data['status']
        edited_text = serializer.validated_data.get('text')
        edited_category = serializer.validated_data.get('category')

        suggestion.status = new_status
        suggestion.doctor = doctor_profile
        suggestion.reviewed_at = timezone.now()

        if edited_text:
            suggestion.text = edited_text
        if edited_category:
            suggestion.category = edited_category

        suggestion.save()

        return Response({
            "message": f"Suggestion {new_status} successfully.",
            "suggestion": SuggestionSerializer(suggestion).data
        }, status=status.HTTP_200_OK)


class DoctorCreateSuggestionView(APIView):
    """
    Allows a doctor to author a custom suggestion/reminder directly for a patient.
    Automatically marked as source='doctor' and status='approved'.
    """
    permission_classes = [permissions.IsAuthenticated, IsDoctor]

    def post(self, request):
        serializer = DoctorSuggestionCreateSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        patient_id = serializer.validated_data['patient_id']
        category = serializer.validated_data['category']
        text = serializer.validated_data['text']

        patient_profile = PatientProfile.objects.get(id=patient_id)
        doctor_profile = request.user.doctor_profile

        suggestion = Suggestion.objects.create(
            patient=patient_profile,
            doctor=doctor_profile,
            source='doctor',
            status='approved',
            category=category,
            text=text,
            reviewed_at=timezone.now()
        )

        return Response({
            "message": "Custom suggestion created and approved successfully.",
            "suggestion": SuggestionSerializer(suggestion).data
        }, status=status.HTTP_201_CREATED)


class PatientSuggestionsView(generics.ListAPIView):
    """
    Lists approved suggestions for the authenticated patient.
    Pending or rejected suggestions are strictly hidden from the patient.
    """
    serializer_class = SuggestionSerializer
    permission_classes = [permissions.IsAuthenticated, IsPatient]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['category', 'source']
    ordering = ['-created_at']

    def get_queryset(self):
        return Suggestion.objects.filter(
            patient=self.request.user.patient_profile,
            status='approved'
        ).select_related('doctor__user')
