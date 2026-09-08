from datetime import date, timedelta
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from accounts.models import User, PatientProfile
from wearables.models import WearableConnection, SleepEntry, ExerciseEntry, AlcoholSignal


class WearablesTests(APITestCase):
    def setUp(self):
        self.patient_user = User.objects.create_user(
            email='wearer@example.com',
            password='Password123!',
            role='patient',
            full_name='Wearer'
        )
        self.patient_profile = PatientProfile.objects.create(user=self.patient_user, age=26)

    def test_oauth_flow(self):
        self.client.force_authenticate(user=self.patient_user)

        # 1. Connect endpoint returns auth url
        connect_url = reverse('wearable-oauth-connect')
        res = self.client.get(connect_url, {'provider': 'boat_wave'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('authorization_url', res.data)
        self.assertIn('boat_wave', res.data['provider'])

        # 2. Callback endpoint exchanges code and saves connection
        callback_url = reverse('wearable-oauth-callback')
        cb_res = self.client.post(callback_url, {'provider': 'boat_wave', 'code': 'test_auth_code_123'}, format='json')
        self.assertEqual(cb_res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(WearableConnection.objects.filter(user=self.patient_user, provider='boat_wave', is_active=True).exists())

    def test_wearable_sync_idempotency(self):
        self.client.force_authenticate(user=self.patient_user)
        sync_url = reverse('wearable-sync')

        target_date = str(date.today() - timedelta(days=1))
        payload = {
            'provider': 'boat_wave',
            'sleep': [
                {
                    'date': target_date,
                    'total_sleep_minutes': 450,
                    'deep_sleep_minutes': 120,
                    'rem_sleep_minutes': 90,
                    'light_sleep_minutes': 240
                }
            ],
            'exercise': [
                {
                    'date': target_date,
                    'activity_type': 'walking',
                    'duration_minutes': 35,
                    'intensity': 'medium',
                    'calories_burned': 150
                }
            ],
            'alcohol': [
                {
                    'timestamp': timezone.now().isoformat(),
                    'confidence_score': 0.85,
                    'notes': 'Elevated nocturnal HR signature'
                }
            ]
        }

        # First sync call
        res1 = self.client.post(sync_url, payload, format='json')
        self.assertEqual(res1.status_code, status.HTTP_200_OK)
        self.assertEqual(SleepEntry.objects.filter(patient=self.patient_profile).count(), 1)
        self.assertEqual(ExerciseEntry.objects.filter(patient=self.patient_profile).count(), 1)
        self.assertEqual(AlcoholSignal.objects.filter(patient=self.patient_profile).count(), 1)

        # Second sync call with updated sleep duration on SAME date (idempotent update)
        payload['sleep'][0]['total_sleep_minutes'] = 480
        res2 = self.client.post(sync_url, payload, format='json')
        self.assertEqual(res2.status_code, status.HTTP_200_OK)

        # Counts must remain 1 for sleep and exercise
        self.assertEqual(SleepEntry.objects.filter(patient=self.patient_profile).count(), 1)
        self.assertEqual(ExerciseEntry.objects.filter(patient=self.patient_profile).count(), 1)

        sleep_record = SleepEntry.objects.get(patient=self.patient_profile, date=target_date)
        self.assertEqual(sleep_record.total_sleep_minutes, 480)

    def test_trends_endpoints(self):
        self.client.force_authenticate(user=self.patient_user)

        # Create sample records
        SleepEntry.objects.create(
            patient=self.patient_profile,
            date=date.today() - timedelta(days=1),
            total_sleep_minutes=420,
            deep_sleep_minutes=100
        )
        ExerciseEntry.objects.create(
            patient=self.patient_profile,
            date=date.today() - timedelta(days=1),
            activity_type='yoga',
            duration_minutes=30,
            intensity='low'
        )

        # 1. Sleep trends
        sleep_url = reverse('sleep-trends')
        s_res = self.client.get(sleep_url)
        self.assertEqual(s_res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(s_res.data['results']), 1)
        self.assertEqual(s_res.data['results'][0]['formatted_total_sleep'], '7h 0m')

        # 2. Exercise trends
        ex_url = reverse('exercise-trends')
        e_res = self.client.get(ex_url)
        self.assertEqual(e_res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(e_res.data['results']), 1)
        self.assertEqual(e_res.data['results'][0]['activity_type'], 'yoga')

    def test_sync_collapses_multiple_sessions_into_daily_totals(self):
        self.client.force_authenticate(user=self.patient_user)
        target_date = str(date.today() - timedelta(days=2))
        response = self.client.post(reverse('wearable-sync'), {
            'provider': 'health_connect',
            'sleep': [
                {'date': target_date, 'total_sleep_minutes': 300, 'deep_sleep_minutes': 80},
                {'date': target_date, 'total_sleep_minutes': 120, 'deep_sleep_minutes': 20},
            ],
            'exercise': [
                {'date': target_date, 'activity_type': 'walking', 'duration_minutes': 15, 'intensity': 'low'},
                {'date': target_date, 'activity_type': 'walking', 'duration_minutes': 25, 'intensity': 'medium'},
            ],
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        sleep = SleepEntry.objects.get(patient=self.patient_profile, date=target_date)
        exercise = ExerciseEntry.objects.get(patient=self.patient_profile, date=target_date, activity_type='walking')
        self.assertEqual(sleep.total_sleep_minutes, 420)
        self.assertEqual(sleep.deep_sleep_minutes, 100)
        self.assertEqual(exercise.duration_minutes, 40)
        self.assertEqual(exercise.intensity, 'medium')
