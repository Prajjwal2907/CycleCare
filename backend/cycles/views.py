from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter

from core.permissions import IsPatient
from .models import CycleEntry
from .serializers import CycleEntrySerializer, CycleSummarySerializer
from .services import calculate_cycle_metrics


class CycleEntryViewSet(viewsets.ModelViewSet):
    """
    CRUD endpoints for cycle entries, strictly scoped to the authenticated patient.
    """
    serializer_class = CycleEntrySerializer
    permission_classes = [permissions.IsAuthenticated, IsPatient]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['flow_intensity']
    ordering_fields = ['start_date', 'created_at']
    ordering = ['-start_date']

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'patient_profile'):
            return CycleEntry.objects.filter(patient=user.patient_profile)
        return CycleEntry.objects.none()


class CycleSummaryView(APIView):
    """
    Returns historical cycle trends, rolling predictions, symptom frequencies,
    and recent cycle entry history for the authenticated patient.
    """
    permission_classes = [permissions.IsAuthenticated, IsPatient]

    def get(self, request):
        patient_profile = request.user.patient_profile
        metrics = calculate_cycle_metrics(patient_profile)

        # Include up to the last 10 cycle entries
        recent_history = CycleEntry.objects.filter(patient=patient_profile).order_by('-start_date')[:10]
        metrics['history'] = CycleEntrySerializer(recent_history, many=True).data

        serializer = CycleSummarySerializer(metrics)
        return Response(serializer.data, status=status.HTTP_200_OK)
