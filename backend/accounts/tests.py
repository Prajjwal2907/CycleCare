from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from accounts.models import User, PatientProfile, DoctorProfile, ConsentGrant
from core.permissions import HasActiveConsent
from unittest.mock import Mock


class AccountsAuthAndConsentTests(APITestCase):
    def setUp(self):
        # Create a patient user
        self.patient_user = User.objects.create_user(
            email='patient@example.com',
            password='Password123!',
            role='patient',
            full_name='Alice Patient'
        )
        self.patient_profile = PatientProfile.objects.create(
            user=self.patient_user,
            age=26,
            weight=58.5,
            height=162.0,
            dietary_preference='vegetarian',
            vegetarian_days=['monday', 'thursday']
        )

        # Create a doctor user
        self.doctor_user = User.objects.create_user(
            email='doctor@example.com',
            password='Password123!',
            role='doctor',
            full_name='Dr. Bob Smith'
        )
        self.doctor_profile = DoctorProfile.objects.create(
            user=self.doctor_user,
            specialization='Gynecologist',
            years_of_experience=8,
            doctor_code='DOC-TEST01'
        )

    def test_patient_registration(self):
        url = reverse('account-register')
        payload = {
            'email': 'newpatient@example.com',
            'password': 'SecurePassword123!',
            'full_name': 'New Patient',
            'role': 'patient',
            'age': 24,
            'weight': 54.0,
            'height': 160.0,
            'dietary_preference': 'non_veg_with_veg_days',
            'vegetarian_days': ['tuesday', 'saturday']
        }
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('tokens', response.data)
        self.assertIn('access', response.data['tokens'])
        self.assertTrue(PatientProfile.objects.filter(user__email='newpatient@example.com').exists())

    def test_doctor_registration(self):
        url = reverse('account-register')
        payload = {
            'email': 'newdoctor@example.com',
            'password': 'SecurePassword123!',
            'full_name': 'Dr. Carol',
            'role': 'doctor',
            'specialization': 'Endocrinologist',
            'years_of_experience': 5
        }
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(DoctorProfile.objects.filter(user__email='newdoctor@example.com').exists())
        doc = DoctorProfile.objects.get(user__email='newdoctor@example.com')
        self.assertTrue(doc.doctor_code.startswith('DOC-'))

    def test_jwt_login(self):
        url = reverse('account-login')
        payload = {
            'email': 'patient@example.com',
            'password': 'Password123!'
        }
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('user', response.data)
        self.assertEqual(response.data['user']['role'], 'patient')

    def test_patient_profile_retrieve_and_update(self):
        self.client.force_authenticate(user=self.patient_user)
        url = reverse('account-profile')

        # GET profile
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['dietary_preference'], 'vegetarian')

        # PATCH profile
        patch_payload = {
            'weight': 60.0,
            'dietary_preference': 'non_vegetarian'
        }
        response = self.client.patch(url, patch_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.patient_profile.refresh_from_db()
        self.assertEqual(self.patient_profile.weight, 60.0)
        self.assertEqual(self.patient_profile.dietary_preference, 'non_vegetarian')

    def test_consent_grant_and_revoke_flow(self):
        self.client.force_authenticate(user=self.patient_user)

        # 1. Grant consent
        grant_url = reverse('consent-grant')
        grant_payload = {
            'doctor_code': 'DOC-TEST01',
            'notes': 'Granted during clinic visit'
        }
        response = self.client.post(grant_url, grant_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(ConsentGrant.objects.filter(
            patient=self.patient_profile,
            doctor=self.doctor_profile,
            is_active=True
        ).exists())

        # 2. List grants as doctor
        self.client.force_authenticate(user=self.doctor_user)
        list_url = reverse('consent-list')
        response = self.client.get(list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

        # 3. Revoke consent as patient
        self.client.force_authenticate(user=self.patient_user)
        revoke_url = reverse('consent-revoke')
        revoke_payload = {'doctor_code': 'DOC-TEST01', 'notes': 'Patient opted out'}
        response = self.client.post(revoke_url, revoke_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        grant = ConsentGrant.objects.get(patient=self.patient_profile, doctor=self.doctor_profile)
        self.assertFalse(grant.is_active)
        self.assertIsNotNone(grant.revoked_at)

        # 4. Doctor should no longer see active consent
        self.client.force_authenticate(user=self.doctor_user)
        response = self.client.get(list_url)
        self.assertEqual(len(response.data['results']), 0)

    def test_has_active_consent_permission_class(self):
        perm = HasActiveConsent()
        request = Mock()
        request.user = self.doctor_user
        view = Mock()
        view.kwargs = {'patient_id': self.patient_profile.id}

        # 1. When no consent exists -> False
        self.assertFalse(perm.has_permission(request, view))

        # 2. When active consent grant created -> True
        grant = ConsentGrant.objects.create(
            patient=self.patient_profile,
            doctor=self.doctor_profile,
            is_active=True
        )
        self.assertTrue(perm.has_permission(request, view))

        # 3. When consent revoked -> False
        grant.revoke()
        self.assertFalse(perm.has_permission(request, view))
