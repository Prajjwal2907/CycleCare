from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response

from core.permissions import IsPatient
from core.ml_client import ml_client, MLServiceError, MLServiceTimeoutError
from .models import CravingRequest
from .serializers import CravingRequestSerializer, CravingSubmitSerializer


class CravingAlternativeView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsPatient]

    def post(self, request):
        serializer = CravingSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        patient_profile = request.user.patient_profile
        craving_text = serializer.validated_data['craving']

        try:
            alternative = ml_client.get_craving_alternative(
                craving_text=craving_text,
                dietary_preference=patient_profile.dietary_preference,
                vegetarian_days=patient_profile.vegetarian_days,
            )
        except MLServiceTimeoutError:
            return Response({"detail": "Finding a healthier alternative timed out. Please try again."}, status=status.HTTP_504_GATEWAY_TIMEOUT)
        except MLServiceError as error:
            return Response({"detail": f"Alternative engine error: {error}"}, status=status.HTTP_502_BAD_GATEWAY)

        craving_request = CravingRequest.objects.create(
            patient=patient_profile,
            craving_text=craving_text,
            suggested_alternative=alternative,
            dietary_preference_used=patient_profile.dietary_preference,
        )
        return Response({
            "id": craving_request.id,
            "craving": craving_text,
            "alternative": alternative,
            "dietary_preference_used": patient_profile.dietary_preference,
            "created_at": craving_request.created_at,
        })


class CravingHistoryView(generics.ListAPIView):
    serializer_class = CravingRequestSerializer
    permission_classes = [permissions.IsAuthenticated, IsPatient]

    def get_queryset(self):
        return CravingRequest.objects.filter(patient=self.request.user.patient_profile)
