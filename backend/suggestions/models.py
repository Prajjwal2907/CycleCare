from django.db import models
from core.models import TimeStampedModel
from accounts.models import PatientProfile, DoctorProfile


class Suggestion(TimeStampedModel):
    SOURCE_CHOICES = (
        ('ai', 'AI Generated'),
        ('doctor', 'Doctor Authored'),
    )

    STATUS_CHOICES = (
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )

    CATEGORY_CHOICES = (
        ('hydration', 'Hydration'),
        ('diet', 'Diet & Nutrition'),
        ('exercise', 'Exercise & Movement'),
        ('lifestyle', 'Sleep & Lifestyle'),
        ('medication', 'Medication & Supplements'),
    )

    patient = models.ForeignKey(
        PatientProfile,
        on_delete=models.CASCADE,
        related_name='suggestions',
        db_index=True
    )
    doctor = models.ForeignKey(
        DoctorProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='authored_suggestions',
        db_index=True
    )
    source = models.CharField(max_length=10, choices=SOURCE_CHOICES, default='ai')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending', db_index=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='lifestyle')
    text = models.TextField()
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['patient', 'status']),
            models.Index(fields=['doctor', 'status']),
        ]

    def __str__(self):
        return f"Suggestion for {self.patient.user.email} [{self.category} - {self.source} - {self.status}]"
