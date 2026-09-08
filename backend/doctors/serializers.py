from rest_framework import serializers
from accounts.models import PatientProfile


class ConsentedPatientListSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email', read_only=True)
    full_name = serializers.CharField(source='user.full_name', read_only=True)
    active_since = serializers.SerializerMethodField()

    class Meta:
        model = PatientProfile
        fields = (
            'id', 'email', 'full_name', 'active_since'
        )

    def get_active_since(self, obj):
        request = self.context.get('request')
        if request and hasattr(request.user, 'doctor_profile'):
            grant = obj.consent_grants.filter(doctor=request.user.doctor_profile, is_active=True).first()
            if grant:
                return grant.granted_at
        return None


class DoctorPatientDashboardSerializer(serializers.Serializer):
    patient = serializers.DictField()
    cycle_summary = serializers.DictField()
    sleep_summary = serializers.DictField()
    exercise_summary = serializers.DictField()
    alcohol_summary = serializers.DictField()
    suggestion_summary = serializers.DictField()
