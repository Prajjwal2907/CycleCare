from django.utils import timezone
from rest_framework import serializers
from .models import CycleEntry


class CycleEntrySerializer(serializers.ModelSerializer):
    cycle_duration = serializers.IntegerField(read_only=True)

    class Meta:
        model = CycleEntry
        fields = (
            'id', 'start_date', 'end_date', 'flow_intensity',
            'symptoms', 'notes', 'cycle_duration',
            'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'cycle_duration', 'created_at', 'updated_at')

    def validate(self, attrs):
        start_date = attrs.get('start_date') or getattr(self.instance, 'start_date', None)
        end_date = attrs.get('end_date') or getattr(self.instance, 'end_date', None)

        if start_date and end_date and end_date < start_date:
            raise serializers.ValidationError({
                "end_date": "End date cannot be earlier than start date."
            })

        if start_date and start_date > timezone.now().date():
            raise serializers.ValidationError({
                "start_date": "Cycle start date cannot be in the future."
            })

        return attrs

    def create(self, validated_data):
        # Automatically tie to the authenticated patient's profile
        request = self.context.get('request')
        patient_profile = request.user.patient_profile
        validated_data['patient'] = patient_profile
        return super().create(validated_data)


class CycleSummarySerializer(serializers.Serializer):
    total_entries = serializers.IntegerField()
    average_duration_days = serializers.FloatField()
    average_gap_days = serializers.FloatField()
    predicted_next_cycle_gap = serializers.IntegerField()
    predicted_next_start_date = serializers.DateField(allow_null=True)
    days_until_next_cycle = serializers.IntegerField(allow_null=True)
    symptom_frequency = serializers.DictField(child=serializers.IntegerField())
    flow_distribution = serializers.DictField(child=serializers.IntegerField())
    history = CycleEntrySerializer(many=True, read_only=True)
