from datetime import date, timedelta
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from accounts.models import User, PatientProfile
from cycles.models import CycleEntry


class CycleTrackingTests(APITestCase):
    def setUp(self):
        # Patient 1
        self.user1 = User.objects.create_user(
            email='alice@example.com',
            password='Password123!',
            role='patient',
            full_name='Alice'
        )
        self.profile1 = PatientProfile.objects.create(user=self.user1, age=25)

        # Patient 2
        self.user2 = User.objects.create_user(
            email='bobbie@example.com',
            password='Password123!',
            role='patient',
            full_name='Bobbie'
        )
        self.profile2 = PatientProfile.objects.create(user=self.user2, age=27)

    def test_create_cycle_entry_with_duration(self):
        self.client.force_authenticate(user=self.user1)
        url = reverse('cycle-entry-list')
        payload = {
            'start_date': str(date.today() - timedelta(days=10)),
            'end_date': str(date.today() - timedelta(days=6)),
            'flow_intensity': 'heavy',
            'symptoms': ['cramps', 'fatigue', 'back_pain'],
            'notes': 'Severe cramps on day 1 and 2'
        }
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['cycle_duration'], 5)  # 10 to 6 inclusive is 5 days
        self.assertEqual(response.data['flow_intensity'], 'heavy')

    def test_invalid_dates_validation(self):
        self.client.force_authenticate(user=self.user1)
        url = reverse('cycle-entry-list')

        # 1. End date before start date
        payload = {
            'start_date': str(date.today() - timedelta(days=5)),
            'end_date': str(date.today() - timedelta(days=8)),
            'flow_intensity': 'normal'
        }
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('end_date', response.data)

        # 2. Start date in the future
        payload = {
            'start_date': str(date.today() + timedelta(days=2)),
            'end_date': str(date.today() + timedelta(days=6)),
            'flow_intensity': 'light'
        }
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('start_date', response.data)

    def test_patient_data_isolation(self):
        # Alice creates an entry
        entry = CycleEntry.objects.create(
            patient=self.profile1,
            start_date=date.today() - timedelta(days=30),
            end_date=date.today() - timedelta(days=25),
            flow_intensity='normal'
        )

        # Bobbie authenticates and tries to access Alice's entry
        self.client.force_authenticate(user=self.user2)
        url = reverse('cycle-entry-detail', kwargs={'pk': entry.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_cycle_summary_endpoint(self):
        self.client.force_authenticate(user=self.user1)

        # Cycle 1: 60 days ago
        CycleEntry.objects.create(
            patient=self.profile1,
            start_date=date.today() - timedelta(days=60),
            end_date=date.today() - timedelta(days=56),
            flow_intensity='heavy',
            symptoms=['cramps', 'bloating']
        )
        # Cycle 2: 32 days ago (gap = 28 days)
        CycleEntry.objects.create(
            patient=self.profile1,
            start_date=date.today() - timedelta(days=32),
            end_date=date.today() - timedelta(days=28),
            flow_intensity='normal',
            symptoms=['cramps']
        )

        url = reverse('cycle-summary')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_entries'], 2)
        self.assertEqual(response.data['average_duration_days'], 5.0)
        self.assertEqual(response.data['average_gap_days'], 28.0)
        self.assertIn('cramps', response.data['symptom_frequency'])
        self.assertEqual(response.data['symptom_frequency']['cramps'], 2)
        self.assertEqual(len(response.data['history']), 2)
