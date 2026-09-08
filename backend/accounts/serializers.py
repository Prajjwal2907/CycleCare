from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.password_validation import validate_password
from .models import User, PatientProfile, DoctorProfile, ConsentGrant


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'full_name', 'role', 'date_joined')
        read_only_fields = ('id', 'date_joined')


class PatientProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = PatientProfile
        fields = (
            'id', 'user', 'age', 'weight', 'height',
            'dietary_preference', 'vegetarian_days',
            'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at')

    def validate_age(self, value):
        if value is not None and (value < 10 or value > 120):
            raise serializers.ValidationError("Age must be between 10 and 120.")
        return value

    def validate_weight(self, value):
        if value is not None and (value < 20 or value > 300):
            raise serializers.ValidationError("Weight must be between 20kg and 300kg.")
        return value

    def validate_height(self, value):
        if value is not None and (value < 80 or value > 250):
            raise serializers.ValidationError("Height must be between 80cm and 250cm.")
        return value


class DoctorProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = DoctorProfile
        fields = (
            'id', 'user', 'specialization', 'years_of_experience',
            'doctor_code', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'doctor_code', 'created_at', 'updated_at')


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    # Optional profile onboarding fields
    age = serializers.IntegerField(required=False, allow_null=True)
    weight = serializers.FloatField(required=False, allow_null=True)
    height = serializers.FloatField(required=False, allow_null=True)
    dietary_preference = serializers.CharField(required=False, default='vegetarian')
    vegetarian_days = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list
    )
    specialization = serializers.CharField(required=False, default="Gynecologist / PCOD Specialist")
    years_of_experience = serializers.IntegerField(required=False, default=0)

    class Meta:
        model = User
        fields = (
            'id', 'email', 'password', 'full_name', 'role',
            'age', 'weight', 'height', 'dietary_preference', 'vegetarian_days',
            'specialization', 'years_of_experience'
        )
        extra_kwargs = {
            'role': {'required': True},
            'full_name': {'required': False},
        }

    def validate_role(self, value):
        if value not in ('patient', 'doctor'):
            raise serializers.ValidationError("Role must be either 'patient' or 'doctor'.")
        return value

    def create(self, validated_data):
        age = validated_data.pop('age', None)
        weight = validated_data.pop('weight', None)
        height = validated_data.pop('height', None)
        dietary_preference = validated_data.pop('dietary_preference', 'vegetarian')
        vegetarian_days = validated_data.pop('vegetarian_days', [])
        specialization = validated_data.pop('specialization', 'Gynecologist / PCOD Specialist')
        years_of_experience = validated_data.pop('years_of_experience', 0)

        password = validated_data.pop('password')
        user = User.objects.create_user(password=password, **validated_data)

        if user.role == 'patient':
            PatientProfile.objects.create(
                user=user,
                age=age,
                weight=weight,
                height=height,
                dietary_preference=dietary_preference,
                vegetarian_days=vegetarian_days
            )
        elif user.role == 'doctor':
            DoctorProfile.objects.create(
                user=user,
                specialization=specialization,
                years_of_experience=years_of_experience
            )

        return user


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Enhanced JWT token serializer that includes role, user ID, email,
    full name, and profile metadata in the login response.
    """
    def validate(self, attrs):
        data = super().validate(attrs)
        data['user'] = {
            'id': self.user.id,
            'email': self.user.email,
            'full_name': self.user.full_name,
            'role': self.user.role,
        }
        if self.user.role == 'patient' and hasattr(self.user, 'patient_profile'):
            data['user']['patient_profile_id'] = self.user.patient_profile.id
            data['user']['dietary_preference'] = self.user.patient_profile.dietary_preference
        elif self.user.role == 'doctor' and hasattr(self.user, 'doctor_profile'):
            data['user']['doctor_profile_id'] = self.user.doctor_profile.id
            data['user']['doctor_code'] = self.user.doctor_profile.doctor_code

        return data


class ConsentGrantSerializer(serializers.ModelSerializer):
    doctor_name = serializers.CharField(source='doctor.user.full_name', read_only=True)
    doctor_email = serializers.CharField(source='doctor.user.email', read_only=True)
    doctor_code = serializers.CharField(source='doctor.doctor_code', read_only=True)
    doctor_specialization = serializers.CharField(source='doctor.specialization', read_only=True)
    patient_name = serializers.CharField(source='patient.user.full_name', read_only=True)
    patient_email = serializers.CharField(source='patient.user.email', read_only=True)

    class Meta:
        model = ConsentGrant
        fields = (
            'id', 'patient', 'doctor', 'doctor_name', 'doctor_email', 'doctor_code',
            'doctor_specialization', 'patient_name', 'patient_email',
            'is_active', 'granted_at', 'revoked_at', 'notes'
        )
        read_only_fields = ('id', 'patient', 'doctor', 'granted_at', 'revoked_at')


class GrantConsentActionSerializer(serializers.Serializer):
    doctor_code = serializers.CharField(required=True, max_length=20)
    notes = serializers.CharField(required=False, allow_blank=True, default='')

    def validate_doctor_code(self, value):
        code = value.strip().upper()
        if not DoctorProfile.objects.filter(doctor_code=code).exists():
            raise serializers.ValidationError(f"No doctor found with doctor code '{code}'.")
        return code


class RevokeConsentActionSerializer(serializers.Serializer):
    doctor_code = serializers.CharField(required=False, allow_blank=True)
    grant_id = serializers.IntegerField(required=False)
    notes = serializers.CharField(required=False, allow_blank=True, default='')

    def validate(self, attrs):
        if not attrs.get('doctor_code') and not attrs.get('grant_id'):
            raise serializers.ValidationError("Either 'doctor_code' or 'grant_id' must be provided to revoke consent.")
        return attrs
