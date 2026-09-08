from datetime import date, timedelta
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from accounts.models import User, PatientProfile, DoctorProfile, ConsentGrant
from cycles.models import CycleEntry
from wearables.models import SleepEntry, ExerciseEntry, AlcoholSignal
from suggestions.models import Suggestion


class DoctorDashboardTests(APITestCase):
    def setUp(self):
        # Patient
        self.patient_user = User.objects.create_user(
            email='dash_patient@example.com',
            password='Password123!',
            role='patient',
            full_name='Clara Patient'
        )
        self.patient_profile = PatientProfile.objects.create(
            user=self.patient_user,
            age=28,
            weight=62.0,
            height=165.0,
            dietary_preference='vegetarian'
        )

        # Consented Doctor
        self.doctor_user1 = User.objects.create_user(
            email='dr_authorized@example.com',
            password='Password123!',
            role='doctor',
            full_name='Dr. Authorized'
        )
        self.doctor_profile1 = DoctorProfile.objects.create(
            user=self.doctor_user1,
            specialization='Gynecology',
            doctor_code='DOC-AUTH'
        )

        # Unconsented Doctor
        self.doctor_user2 = User.objects.create_user(
            email='dr_unauthorized@example.com',
            password='Password123!',
            role='doctor',
            full_name='Dr. Unauthorized'
        )
        self.doctor_profile2 = DoctorProfile.objects.create(
            user=self.doctor_user2,
            specialization='Endocrinology',
            doctor_code='DOC-UNAUTH'
        )

        # Active consent for Doctor 1
        self.consent = ConsentGrant.objects.create(
            patient=self.patient_profile,
            doctor=self.doctor_profile1,
            is_active=True
        )

        # Sample tracked patient data
        CycleEntry.objects.create(
            patient=self.patient_profile,
            start_date=date.today() - timedelta(days=20),
            end_date=date.today() - timedelta(days=15),
            flow_intensity='normal',
            symptoms=['cramps']
        )
        SleepEntry.objects.create(
            patient=self.patient_profile,
            date=date.today() - timedelta(days=1),
            total_sleep_minutes=430,
            deep_sleep_minutes=110
        )
        ExerciseEntry.objects.create(
            patient=self.patient_profile,
            date=date.today() - timedelta(days=1),
            activity_type='walking',
            duration_minutes=40,
            intensity='low'
        )
        AlcoholSignal.objects.create(
            patient=self.patient_profile,
            timestamp=timezone.now(),
            confidence_score=0.8,
        )
        Suggestion.objects.create(
            patient=self.patient_profile,
            source='doctor',
            status='approved',
            category='hydration',
            text='Keep hydrated'
        )

    def test_consented_patients_list(self):
        self.client.force_authenticate(user=self.doctor_user1)
        url = reverse('doctor-consented-patients')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['email'], 'dash_patient@example.com')

        # Unconsented doctor sees empty list
        self.client.force_authenticate(user=self.doctor_user2)
        response2 = self.client.get(url)
        self.assertEqual(len(response2.data['results']), 0)

    def test_doctor_patient_dashboard_access_allowed(self):
        self.client.force_authenticate(user=self.doctor_user1)
        url = reverse('doctor-patient-dashboard', kwargs={'patient_id': self.patient_profile.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('patient', response.data)
        self.assertIn('cycle_summary', response.data)
        self.assertEqual(response.data['sleep_summary']['average_sleep_minutes'], 430.0)
        self.assertEqual(response.data['exercise_summary']['average_activity_minutes'], 40.0)
        self.assertEqual(response.data['alcohol_summary']['signals_tracked'], 1)
        self.assertEqual(response.data['suggestion_summary']['approved'], 1)
        self.assertNotIn('recent_cycles', response.data)
        self.assertNotIn('sleep_records', response.data)
        self.assertNotIn('exercise_records', response.data)
        self.assertNotIn('food_logs', response.data)

    def test_doctor_list_exposes_no_profile_health_details(self):
        self.client.force_authenticate(user=self.doctor_user1)
        response = self.client.get(reverse('doctor-consented-patients'))
        patient = response.data['results'][0]
        self.assertNotIn('weight', patient)
        self.assertNotIn('height', patient)
        self.assertNotIn('dietary_preference', patient)
        self.assertNotIn('vegetarian_days', patient)

    def test_doctor_patient_dashboard_access_denied_without_consent(self):
        # Doctor 2 has no consent
        self.client.force_authenticate(user=self.doctor_user2)
        url = reverse('doctor-patient-dashboard', kwargs={'patient_id': self.patient_profile.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_doctor_patient_dashboard_denied_after_consent_revoked(self):
        # Revoke consent
        self.consent.revoke()

        self.client.force_authenticate(user=self.doctor_user1)
        url = reverse('doctor-patient-dashboard', kwargs={'patient_id': self.patient_profile.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
