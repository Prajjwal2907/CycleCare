from django.db import models
from core.models import TimeStampedModel
from accounts.models import PatientProfile


class CravingRequest(TimeStampedModel):
    patient = models.ForeignKey(
        PatientProfile,
        on_delete=models.CASCADE,
        related_name='craving_requests',
        db_index=True
    )
    craving_text = models.CharField(max_length=255)
    suggested_alternative = models.JSONField(
        default=dict,
        help_text="Healthier recipe/alternative details JSON"
    )
    dietary_preference_used = models.CharField(max_length=50, default='vegetarian')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['patient', '-created_at']),
        ]

    def __str__(self):
        alt_name = self.suggested_alternative.get('name', 'Alternative')
        return f"Craving: '{self.craving_text}' -> '{alt_name}' for {self.patient.user.email}"
