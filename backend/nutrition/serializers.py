from rest_framework import serializers
from .models import CravingRequest


class CravingRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = CravingRequest
        fields = (
            'id', 'craving_text', 'suggested_alternative',
            'dietary_preference_used', 'created_at'
        )
        read_only_fields = ('id', 'suggested_alternative', 'dietary_preference_used', 'created_at')


class CravingSubmitSerializer(serializers.Serializer):
    craving = serializers.CharField(max_length=255, required=True)
