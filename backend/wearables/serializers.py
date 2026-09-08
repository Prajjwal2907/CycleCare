from rest_framework import serializers
from .models import WearableConnection, SleepEntry, AlcoholSignal, ExerciseEntry


class WearableConnectionSerializer(serializers.ModelSerializer):
    provider_name = serializers.CharField(source='get_provider_display', read_only=True)

    class Meta:
        model = WearableConnection
        fields = (
            'id', 'provider', 'provider_name', 'is_active',
            'connected_at', 'token_expires_at'
        )
        read_only_fields = ('id', 'connected_at')


class SleepEntrySerializer(serializers.ModelSerializer):
    formatted_total_sleep = serializers.SerializerMethodField()
    formatted_deep_sleep = serializers.SerializerMethodField()

    class Meta:
        model = SleepEntry
        fields = (
            'id', 'date', 'total_sleep_minutes', 'deep_sleep_minutes',
            'rem_sleep_minutes', 'light_sleep_minutes',
            'formatted_total_sleep', 'formatted_deep_sleep',
            'source_provider', 'created_at'
        )
        read_only_fields = ('id', 'created_at')

    def get_formatted_total_sleep(self, obj):
        hours = obj.total_sleep_minutes // 60
        mins = obj.total_sleep_minutes % 60
        return f"{hours}h {mins}m"

    def get_formatted_deep_sleep(self, obj):
        hours = obj.deep_sleep_minutes // 60
        mins = obj.deep_sleep_minutes % 60
        return f"{hours}h {mins}m"


class AlcoholSignalSerializer(serializers.ModelSerializer):
    class Meta:
        model = AlcoholSignal
        fields = (
            'id', 'timestamp', 'signal_source', 'confidence_score',
            'is_estimated', 'notes', 'created_at'
        )
        read_only_fields = ('id', 'created_at')


class ExerciseEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = ExerciseEntry
        fields = (
            'id', 'date', 'activity_type', 'duration_minutes',
            'intensity', 'calories_burned', 'source_provider', 'created_at'
        )
        read_only_fields = ('id', 'created_at')


class WearableSyncPayloadSerializer(serializers.Serializer):
    provider = serializers.ChoiceField(
        choices=[('boat_wave', 'boAt Wave'), ('health_connect', 'Google Health Connect'), ('healthkit', 'Apple HealthKit'), ('generic', 'Generic')],
        default='generic'
    )
    sleep = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        default=list
    )
    exercise = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        default=list
    )
    alcohol = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        default=list
    )


class OAuthConnectSerializer(serializers.Serializer):
    provider = serializers.ChoiceField(choices=[('boat_wave', 'boAt Wave'), ('health_connect', 'Google Health Connect'), ('healthkit', 'Apple HealthKit')])
    redirect_uri = serializers.CharField(required=False, allow_blank=True)


class OAuthCallbackSerializer(serializers.Serializer):
    provider = serializers.ChoiceField(choices=[('boat_wave', 'boAt Wave'), ('health_connect', 'Google Health Connect'), ('healthkit', 'Apple HealthKit')])
    code = serializers.CharField(required=True)
    redirect_uri = serializers.CharField(required=False, allow_blank=True)
