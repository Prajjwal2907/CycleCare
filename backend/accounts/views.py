from django.utils import timezone
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken

from core.permissions import IsPatient, IsDoctor
from .models import User, PatientProfile, DoctorProfile, ConsentGrant
from .serializers import (
    UserSerializer,
    UserRegistrationSerializer,
    CustomTokenObtainPairSerializer,
    PatientProfileSerializer,
    DoctorProfileSerializer,
    ConsentGrantSerializer,
    GrantConsentActionSerializer,
    RevokeConsentActionSerializer,
)


class RegisterView(generics.CreateAPIView):
    """
    Registers a new user (Doctor or Patient) with role-specific profile details.
    Immediately returns JWT access and refresh tokens upon creation.
    """
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        user_data = UserSerializer(user).data

        profile_data = {}
        if user.role == 'patient' and hasattr(user, 'patient_profile'):
            profile_data = PatientProfileSerializer(user.patient_profile).data
        elif user.role == 'doctor' and hasattr(user, 'doctor_profile'):
            profile_data = DoctorProfileSerializer(user.doctor_profile).data

        return Response(
            {
                "message": "User registered successfully.",
                "user": user_data,
                "profile": profile_data,
                "tokens": {
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                }
            },
            status=status.HTTP_201_CREATED
        )


class LoginView(TokenObtainPairView):
    """
    Authenticates user credentials and returns JWT tokens along with role and profile info.
    """
    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = [permissions.AllowAny]


class UserProfileView(APIView):
    """
    Retrieves or updates the profile corresponding to the currently authenticated user.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        if user.role == 'patient':
            profile, _ = PatientProfile.objects.get_or_create(user=user)
            serializer = PatientProfileSerializer(profile)
        elif user.role == 'doctor':
            profile, _ = DoctorProfile.objects.get_or_create(user=user)
            serializer = DoctorProfileSerializer(profile)
        else:
            return Response({"detail": "Unknown user role."}, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.data)

    def patch(self, request):
        user = request.user
        # Update user full name if provided
        if 'full_name' in request.data:
            user.full_name = request.data['full_name']
            user.save(update_fields=['full_name'])

        if user.role == 'patient':
            profile, _ = PatientProfile.objects.get_or_create(user=user)
            serializer = PatientProfileSerializer(profile, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
        elif user.role == 'doctor':
            profile, _ = DoctorProfile.objects.get_or_create(user=user)
            serializer = DoctorProfileSerializer(profile, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)

        return Response({"detail": "Invalid role."}, status=status.HTTP_400_BAD_REQUEST)


class ConsentGrantListView(generics.ListAPIView):
    """
    Lists consent grants.
    - If Patient: lists all consent grants (both active and revoked) for audit visibility.
    - If Doctor: lists patients who have currently active consent for this doctor.
    """
    serializer_class = ConsentGrantSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'patient':
            profile, _ = PatientProfile.objects.get_or_create(user=user)
            return ConsentGrant.objects.filter(patient=profile).select_related('doctor__user', 'patient__user')
        elif user.role == 'doctor':
            profile, _ = DoctorProfile.objects.get_or_create(user=user)
            return ConsentGrant.objects.filter(doctor=profile, is_active=True).select_related('patient__user', 'doctor__user')
        return ConsentGrant.objects.none()


class GrantConsentView(APIView):
    """
    Allows a patient to grant access to a doctor by providing their doctor_code.
    Creates or activates a ConsentGrant in an auditable append-only fashion.
    """
    permission_classes = [permissions.IsAuthenticated, IsPatient]

    def post(self, request):
        serializer = GrantConsentActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        doctor_code = serializer.validated_data['doctor_code']
        notes = serializer.validated_data.get('notes', '')

        patient_profile, _ = PatientProfile.objects.get_or_create(user=request.user)
        doctor_profile = DoctorProfile.objects.get(doctor_code=doctor_code)

        # Check for existing active grant
        active_grant = ConsentGrant.objects.filter(
            patient=patient_profile,
            doctor=doctor_profile,
            is_active=True
        ).first()

        if active_grant:
            return Response(
                {
                    "message": f"Consent is already active for Dr. {doctor_profile.user.full_name or doctor_profile.user.email}.",
                    "grant": ConsentGrantSerializer(active_grant).data
                },
                status=status.HTTP_200_OK
            )

        # Create new active consent record
        new_grant = ConsentGrant.objects.create(
            patient=patient_profile,
            doctor=doctor_profile,
            is_active=True,
            granted_at=timezone.now(),
            notes=notes
        )

        return Response(
            {
                "message": f"Consent successfully granted to Dr. {doctor_profile.user.full_name or doctor_profile.user.email}.",
                "grant": ConsentGrantSerializer(new_grant).data
            },
            status=status.HTTP_201_CREATED
        )


class RevokeConsentView(APIView):
    """
    Allows a patient to revoke a doctor's access to their health data.
    Sets is_active=False and timestamps the revoked_at field.
    """
    permission_classes = [permissions.IsAuthenticated, IsPatient]

    def post(self, request):
        serializer = RevokeConsentActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        patient_profile, _ = PatientProfile.objects.get_or_create(user=request.user)
        doctor_code = serializer.validated_data.get('doctor_code')
        grant_id = serializer.validated_data.get('grant_id')
        notes = serializer.validated_data.get('notes', '')

        query = ConsentGrant.objects.filter(patient=patient_profile, is_active=True)
        if grant_id:
            query = query.filter(id=grant_id)
        elif doctor_code:
            query = query.filter(doctor__doctor_code=doctor_code.strip().upper())

        active_grants = list(query)
        if not active_grants:
            return Response(
                {"detail": "No active consent grant found matching the criteria."},
                status=status.HTTP_404_NOT_FOUND
            )

        for grant in active_grants:
            grant.revoke(notes=notes or "Revoked by patient.")

        return Response(
            {
                "message": f"Successfully revoked consent for {len(active_grants)} grant(s).",
                "revoked_count": len(active_grants)
            },
            status=status.HTTP_200_OK
        )


class DoctorDirectoryView(generics.ListAPIView):
    """
    Publicly visible directory of doctors for patients to find doctor codes.
    """
    queryset = DoctorProfile.objects.all().select_related('user')
    serializer_class = DoctorProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
