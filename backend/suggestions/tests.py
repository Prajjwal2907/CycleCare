from unittest.mock import patch
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from accounts.models import User, PatientProfile, DoctorProfile, ConsentGrant
from suggestions.models import Suggestion


class SuggestionCenterTests(APITestCase):
    def setUp(self):
        # Patient
        self.patient_user = User.objects.create_user(
            email='sugg_patient@example.com',
            password='Password123!',
            role='patient',
            full_name='Priya'
        )
        self.patient_profile = PatientProfile.objects.create(
            user=self.patient_user,
            age=23,
            dietary_preference='vegetarian'
        )

        # Doctor 1 (with consent)
        self.doctor_user1 = User.objects.create_user(
            email='sugg_doc1@example.com',
            password='Password123!',
            role='doctor',
            full_name='Dr. Sharma'
        )
        self.doctor_profile1 = DoctorProfile.objects.create(
            user=self.doctor_user1,
            specialization='Gynecology',
            doctor_code='DOC-SHARMA'
        )

        # Grant active consent
        self.grant = ConsentGrant.objects.create(
            patient=self.patient_profile,
            doctor=self.doctor_profile1,
            is_active=True
        )

        # Doctor 2 (without consent)
        self.doctor_user2 = User.objects.create_user(
            email='sugg_doc2@example.com',
            password='Password123!',
            role='doctor',
            full_name='Dr. Unapproved'
        )
        self.doctor_profile2 = DoctorProfile.objects.create(
            user=self.doctor_user2,
            specialization='Endocrinology',
            doctor_code='DOC-UNAPPROVED'
        )

    @patch('suggestions.views.ml_client.generate_suggestions')
    def test_ai_suggestion_generation(self, mock_ml):
        mock_ml.return_value = [
            {"category": "hydration", "text": "Drink warm lemon water at 10am."},
            {"category": "exercise", "text": "Take a 20-min gentle stroll."}
        ]
        self.client.force_authenticate(user=self.patient_user)
        url = reverse('generate-ai-suggestions')

        response = self.client.post(url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(response.data['suggestions']), 2)

        # Verify status is 'pending'
        self.assertEqual(response.data['suggestions'][0]['status'], 'pending')
        self.assertEqual(Suggestion.objects.filter(patient=self.patient_profile, status='pending').count(), 2)

    def test_doctor_review_and_approval_workflow(self):
        # Create a pending AI suggestion
        suggestion = Suggestion.objects.create(
            patient=self.patient_profile,
            source='ai',
            status='pending',
            category='hydration',
            text='Hydrate with electrolytes'
        )

        # 1. Consented doctor lists pending suggestions
        self.client.force_authenticate(user=self.doctor_user1)
        pending_url = reverse('doctor-pending-suggestions')
        p_res = self.client.get(pending_url)
        self.assertEqual(p_res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(p_res.data['results']), 1)

        # 2. Unapproved doctor attempts to review -> 403 Forbidden
        self.client.force_authenticate(user=self.doctor_user2)
        review_url = reverse('doctor-review-suggestion', kwargs={'pk': suggestion.id})
        rev_res = self.client.patch(review_url, {'status': 'approved'}, format='json')
        self.assertEqual(rev_res.status_code, status.HTTP_403_FORBIDDEN)

        # 3. Consented doctor approves the suggestion
        self.client.force_authenticate(user=self.doctor_user1)
        rev_res2 = self.client.patch(review_url, {
            'status': 'approved',
            'text': 'Hydrate with 500ml water and electrolytes after morning walk'
        }, format='json')
        self.assertEqual(rev_res2.status_code, status.HTTP_200_OK)

        suggestion.refresh_from_db()
        self.assertEqual(suggestion.status, 'approved')
        self.assertEqual(suggestion.doctor, self.doctor_profile1)
        self.assertIsNotNone(suggestion.reviewed_at)

        # 4. Patient now sees the approved suggestion
        self.client.force_authenticate(user=self.patient_user)
        patient_url = reverse('patient-suggestions-list')
        pat_res = self.client.get(patient_url)
        self.assertEqual(pat_res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(pat_res.data['results']), 1)
        self.assertEqual(pat_res.data['results'][0]['id'], suggestion.id)

    def test_doctor_custom_suggestion_creation(self):
        self.client.force_authenticate(user=self.doctor_user1)
        create_url = reverse('doctor-create-suggestion')

        payload = {
            'patient_id': self.patient_profile.id,
            'category': 'hydration',
            'text': 'Drink water at 3pm every afternoon'
        }
        response = self.client.post(create_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['suggestion']['status'], 'approved')
        self.assertEqual(response.data['suggestion']['source'], 'doctor')
