from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Avg, Count, Sum

from core.permissions import IsDoctor, HasActiveConsent
from accounts.models import PatientProfile, ConsentGrant
from cycles.services import calculate_cycle_metrics
from wearables.models import SleepEntry, ExerciseEntry, AlcoholSignal
from suggestions.models import Suggestion

from .serializers import ConsentedPatientListSerializer, DoctorPatientDashboardSerializer


def _rounded_stats(stats):
    return {
        key: round(value, 1) if isinstance(value, float) else (value or 0)
        for key, value in stats.items()
    }


class DoctorPatientsListView(generics.ListAPIView):
    """
    Returns only patients who have an active, unrevoked ConsentGrant for the authenticated doctor.
    """
    serializer_class = ConsentedPatientListSerializer
    permission_classes = [permissions.IsAuthenticated, IsDoctor]

    def get_queryset(self):
        doctor_profile = self.request.user.doctor_profile
        consented_patient_ids = ConsentGrant.objects.filter(
            doctor=doctor_profile,
            is_active=True
        ).values_list('patient_id', flat=True)

        return PatientProfile.objects.filter(
            id__in=consented_patient_ids
        ).select_related('user').prefetch_related('consent_grants').order_by('-created_at')



class DoctorPatientDashboardView(APIView):
    """
    Consolidated read-only patient dashboard for doctors.
    Strictly enforced by HasActiveConsent permission: returns 403 Forbidden
    if the requesting doctor lacks an active consent grant from this patient.
    """
    permission_classes = [permissions.IsAuthenticated, IsDoctor, HasActiveConsent]

    def get(self, request, patient_id):
        patient_profile = get_object_or_404(PatientProfile.objects.select_related('user'), id=patient_id)

        # Only aggregate statistics cross the doctor boundary. Raw health,
        # nutrition, wearable, and cycle records remain patient-only.
        cycle_metrics = calculate_cycle_metrics(patient_profile)
        cycle_summary = {
            key: cycle_metrics[key]
            for key in (
                'total_entries', 'average_duration_days', 'average_gap_days',
                'predicted_next_cycle_gap', 'predicted_next_start_date',
                'days_until_next_cycle'
            )
        }

        sleep_stats = SleepEntry.objects.filter(patient=patient_profile).aggregate(
            days_tracked=Count('id'),
            average_sleep_minutes=Avg('total_sleep_minutes'),
            average_deep_sleep_minutes=Avg('deep_sleep_minutes'),
        )
        exercise_stats = ExerciseEntry.objects.filter(patient=patient_profile).aggregate(
            activity_days=Count('date', distinct=True),
            total_activity_minutes=Sum('duration_minutes'),
            average_activity_minutes=Avg('duration_minutes'),
        )
        alcohol_stats = AlcoholSignal.objects.filter(patient=patient_profile).aggregate(
            signals_tracked=Count('id'),
            average_confidence=Avg('confidence_score'),
        )
        suggestion_counts = {
            row['status']: row['count']
            for row in Suggestion.objects.filter(patient=patient_profile)
            .values('status').annotate(count=Count('id'))
        }

        dashboard_data = {
            "patient": {
                "id": patient_profile.id,
                "email": patient_profile.user.email,
                "full_name": patient_profile.user.full_name,
            },
            "cycle_summary": cycle_summary,
            "sleep_summary": _rounded_stats(sleep_stats),
            "exercise_summary": _rounded_stats(exercise_stats),
            "alcohol_summary": _rounded_stats(alcohol_stats),
            "suggestion_summary": suggestion_counts,
        }

        serializer = DoctorPatientDashboardSerializer(dashboard_data, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
