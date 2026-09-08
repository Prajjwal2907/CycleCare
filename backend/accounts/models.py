import uuid
from django.db import models
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser, PermissionsMixin
from django.utils import timezone
from core.models import TimeStampedModel


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'doctor')

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = (
        ('patient', 'Patient'),
        ('doctor', 'Doctor'),
    )

    email = models.EmailField(unique=True, db_index=True)
    full_name = models.CharField(max_length=150, blank=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['role']

    def __str__(self):
        return f"{self.email} ({self.role})"


class PatientProfile(TimeStampedModel):
    DIETARY_CHOICES = (
        ('vegetarian', 'Vegetarian'),
        ('non_vegetarian', 'Non-Vegetarian'),
        ('non_veg_with_veg_days', 'Non-Vegetarian with Vegetarian Days'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='patient_profile')
    age = models.PositiveIntegerField(null=True, blank=True)
    weight = models.FloatField(null=True, blank=True, help_text="Weight in kg")
    height = models.FloatField(null=True, blank=True, help_text="Height in cm")
    dietary_preference = models.CharField(max_length=30, choices=DIETARY_CHOICES, default='vegetarian')
    vegetarian_days = models.JSONField(default=list, blank=True, help_text="List of vegetarian weekdays e.g. ['monday', 'thursday']")

    def __str__(self):
        return f"Patient: {self.user.email} (Age: {self.age or 'N/A'})"


class DoctorProfile(TimeStampedModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='doctor_profile')
    specialization = models.CharField(max_length=150, default="Gynecologist / PCOD Specialist")
    years_of_experience = models.PositiveIntegerField(default=0)
    doctor_code = models.CharField(max_length=20, unique=True, db_index=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.doctor_code:
            # Generate a 6-character unique doctor code e.g. DOC-AB12
            self.doctor_code = f"DOC-{uuid.uuid4().hex[:6].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Dr. {self.user.full_name or self.user.email} [{self.doctor_code}]"


class ConsentGrant(TimeStampedModel):
    """
    Append-only auditable log of patient consent grants to doctors.
    A patient can grant or revoke access at any time.
    """
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name='consent_grants')
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE, related_name='consent_grants')
    is_active = models.BooleanField(default=True, db_index=True)
    granted_at = models.DateTimeField(default=timezone.now)
    revoked_at = models.DateTimeField(null=True, blank=True)
    notes = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['-granted_at']
        indexes = [
            models.Index(fields=['patient', 'doctor', 'is_active']),
        ]

    def revoke(self, notes=""):
        self.is_active = False
        self.revoked_at = timezone.now()
        if notes:
            self.notes = notes
        self.save(update_fields=['is_active', 'revoked_at', 'notes', 'updated_at'])

    def __str__(self):
        status = "Active" if self.is_active else f"Revoked ({self.revoked_at.strftime('%Y-%m-%d') if self.revoked_at else ''})"
        return f"Consent: {self.patient.user.email} -> {self.doctor.user.email} [{status}]"
