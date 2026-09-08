from django.db import models
from core.models import TimeStampedModel
from accounts.models import User, PatientProfile


class WearableConnection(TimeStampedModel):
    PROVIDER_CHOICES = (
        ('boat_wave', 'boAt Wave'),
        ('health_connect', 'Google Health Connect'),
        ('healthkit', 'Apple HealthKit'),
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='wearable_connections',
        db_index=True
    )
    provider = models.CharField(max_length=50, choices=PROVIDER_CHOICES)
    access_token = models.TextField(help_text="OAuth access token")
    refresh_token = models.TextField(blank=True, help_text="OAuth refresh token")
    token_expires_at = models.DateTimeField(null=True, blank=True)
    connected_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('user', 'provider')
        ordering = ['-connected_at']

    def __str__(self):
        return f"{self.user.email} - {self.get_provider_display()} ({'Active' if self.is_active else 'Disconnected'})"


class SleepEntry(TimeStampedModel):
    patient = models.ForeignKey(
        PatientProfile,
        on_delete=models.CASCADE,
        related_name='sleep_entries',
        db_index=True
    )
    date = models.DateField(db_index=True)
    total_sleep_minutes = models.PositiveIntegerField(help_text="Total sleep duration in minutes")
    deep_sleep_minutes = models.PositiveIntegerField(help_text="Deep sleep duration in minutes")
    rem_sleep_minutes = models.PositiveIntegerField(default=0, help_text="REM sleep in minutes")
    light_sleep_minutes = models.PositiveIntegerField(default=0, help_text="Light sleep in minutes")
    source_provider = models.CharField(max_length=50, default='health_connect')

    class Meta:
        unique_together = ('patient', 'date')
        ordering = ['-date']
        indexes = [
            models.Index(fields=['patient', '-date']),
        ]

    def __str__(self):
        return f"Sleep on {self.date} for {self.patient.user.email}: {self.total_sleep_minutes // 60}h {self.total_sleep_minutes % 60}m"


class AlcoholSignal(TimeStampedModel):
    patient = models.ForeignKey(
        PatientProfile,
        on_delete=models.CASCADE,
        related_name='alcohol_signals',
        db_index=True
    )
    timestamp = models.DateTimeField(db_index=True)
    signal_source = models.CharField(max_length=50, default='vitals')
    confidence_score = models.FloatField(default=0.0, help_text="Confidence between 0.0 and 1.0")
    is_estimated = models.BooleanField(default=True, help_text="True if derived via vitals, False if logged by user")
    notes = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['patient', '-timestamp']),
        ]

    def __str__(self):
        return f"Alcohol signal for {self.patient.user.email} at {self.timestamp} (conf: {self.confidence_score})"


class ExerciseEntry(TimeStampedModel):
    INTENSITY_CHOICES = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    )

    patient = models.ForeignKey(
        PatientProfile,
        on_delete=models.CASCADE,
        related_name='exercise_entries',
        db_index=True
    )
    date = models.DateField(db_index=True)
    activity_type = models.CharField(max_length=100, default='walking')
    duration_minutes = models.PositiveIntegerField()
    intensity = models.CharField(max_length=10, choices=INTENSITY_CHOICES, default='medium')
    calories_burned = models.PositiveIntegerField(null=True, blank=True)
    source_provider = models.CharField(max_length=50, default='health_connect')

    class Meta:
        unique_together = ('patient', 'date', 'activity_type')
        ordering = ['-date']
        indexes = [
            models.Index(fields=['patient', '-date']),
        ]

    def __str__(self):
        return f"Exercise for {self.patient.user.email} on {self.date}: {self.activity_type} ({self.duration_minutes}m)"
