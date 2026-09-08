from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from core.models import TimeStampedModel
from accounts.models import PatientProfile


class CycleEntry(TimeStampedModel):
    FLOW_CHOICES = (
        ('light', 'Light'),
        ('normal', 'Normal'),
        ('heavy', 'Heavy'),
    )

    patient = models.ForeignKey(
        PatientProfile,
        on_delete=models.CASCADE,
        related_name='cycle_entries',
        db_index=True
    )
    start_date = models.DateField(db_index=True)
    end_date = models.DateField()
    flow_intensity = models.CharField(max_length=10, choices=FLOW_CHOICES, default='normal')
    symptoms = models.JSONField(
        default=list,
        blank=True,
        help_text="List of symptoms experienced, e.g. ['cramps', 'bloating', 'fatigue']"
    )
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-start_date']
        indexes = [
            models.Index(fields=['patient', '-start_date']),
        ]

    def clean(self):
        super().clean()
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValidationError({'end_date': "End date cannot be earlier than start date."})
        if self.start_date and self.start_date > timezone.now().date():
            raise ValidationError({'start_date': "Cycle start date cannot be in the future."})

    @property
    def cycle_duration(self):
        """Total duration of bleeding in days (inclusive)."""
        if self.start_date and self.end_date:
            return (self.end_date - self.start_date).days + 1
        return 0

    def __str__(self):
        return f"Cycle for {self.patient.user.email}: {self.start_date} to {self.end_date} ({self.flow_intensity})"
