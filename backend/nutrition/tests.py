from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from accounts.models import User, PatientProfile
from nutrition.models import CravingRequest


class NutritionTests(APITestCase):
    def setUp(self):
        self.patient_user = User.objects.create_user(
            email='nutritionist_patient@example.com',
            password='Password123!',
            role='patient',
            full_name='Maya'
        )
        self.patient_profile = PatientProfile.objects.create(
            user=self.patient_user,
            age=24,
            dietary_preference='vegetarian',
            vegetarian_days=['monday', 'thursday']
        )

    def test_craving_alternative_endpoint(self):
        self.client.force_authenticate(user=self.patient_user)
        url = reverse('craving-alternative')

        payload = {'craving': 'pizza'}
        response = self.client.post(url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('alternative', response.data)
        self.assertIn('Cauliflower Crust', response.data['alternative']['name'])
        self.assertEqual(response.data['dietary_preference_used'], 'vegetarian')

        # Verify persisted craving request
        self.assertTrue(CravingRequest.objects.filter(
            patient=self.patient_profile,
            craving_text='pizza'
        ).exists())

        # Test history endpoint
        hist_url = reverse('craving-history')
        h_res = self.client.get(hist_url)
        self.assertEqual(h_res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(h_res.data['results']), 1)
