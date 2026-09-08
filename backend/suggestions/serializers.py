from rest_framework import serializers
from .models import Suggestion
from accounts.models import PatientProfile, ConsentGrant


class SuggestionSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source='patient.user.full_name', read_only=True)
    doctor_name = serializers.CharField(source='doctor.user.full_name', read_only=True, default='')

    class Meta:
        model = Suggestion
        fields = (
            'id', 'patient', 'patient_name', 'doctor', 'doctor_name',
            'source', 'status', 'category', 'text',
            'created_at', 'reviewed_at'
        )
        read_only_fields = ('id', 'patient', 'doctor', 'source', 'created_at', 'reviewed_at')


class DoctorSuggestionCreateSerializer(serializers.Serializer):
    patient_id = serializers.IntegerField(required=True)
    category = serializers.ChoiceField(
        choices=[('hydration', 'Hydration'), ('diet', 'Diet & Nutrition'), ('exercise', 'Exercise & Movement'), ('lifestyle', 'Sleep & Lifestyle'), ('medication', 'Medication & Supplements')],
        default='lifestyle'
    )
    text = serializers.CharField(required=True)

    def validate_patient_id(self, value):
        request = self.context.get('request')
        doctor_profile = request.user.doctor_profile

        # Ensure doctor has active consent for this patient
        if not ConsentGrant.objects.filter(patient_id=value, doctor=doctor_profile, is_active=True).exists():
            raise serializers.ValidationError("You do not have active consent to author suggestions for this patient.")
        return value


class DoctorSuggestionReviewSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=[('approved', 'Approved'), ('rejected', 'Rejected')])
    text = serializers.CharField(required=False, allow_blank=True)
    category = serializers.ChoiceField(
        choices=[('hydration', 'Hydration'), ('diet', 'Diet & Nutrition'), ('exercise', 'Exercise & Movement'), ('lifestyle', 'Sleep & Lifestyle'), ('medication', 'Medication & Supplements')],
        required=False
    )
