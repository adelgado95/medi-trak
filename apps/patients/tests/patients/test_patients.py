from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from apps.patients.models import Patient
from apps.tenant.models import Tenant
from django.contrib.auth.models import User
from apps.user.models import UserProfile

class TestPatientViews(TestCase):
    def setUp(self):
        self.client = APIClient()

    def get_token(self, username, password):
        response = self.client.post('/api/token/', {"username": username, "password": password})
        self.assertEqual(response.status_code, 200)
        return response.data["access"] if hasattr(response, "data") else response.json()["access"]

    def test_create_patient_partial_fields(self):
        tenant = Tenant.objects.create(name="Clinic", type="clinic", allow_partial_patients=True, patient_visible_fields=["email"])
        user = User.objects.create_user(username="testuser", password="testpass")
        UserProfile.objects.create(user=user, tenant=tenant)
        token = self.get_token("testuser", "testpass")
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.post(reverse("patient-list"), {"email": "partial@example.com"})
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Patient.objects.filter(email="partial@example.com").exists())

    def test_create_patient_all_fields(self):
        tenant = Tenant.objects.create(name="Hospital", type="hospital", allow_partial_patients=False, patient_visible_fields=["first_name", "last_name", "ssn", "email"])
        user = User.objects.create_user(username="testuser2", password="testpass2")
        UserProfile.objects.create(user=user, tenant=tenant)
        token = self.get_token("testuser2", "testpass2")
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        data = {
            "first_name": "John",
            "last_name": "Doe",
            "ssn": "123-45-6789",
            "email": "john.doe@example.com"
        }
        response = self.client.post(reverse("patient-list"), data)
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Patient.objects.filter(email="john.doe@example.com").exists())

    def test_patient_detail_fields(self):
        tenant = Tenant.objects.create(name="Clinic", type="clinic", allow_partial_patients=True, patient_visible_fields=["email"])
        patient = Patient.objects.create(tenant=tenant, email="visible@example.com")
        user = User.objects.create_user(username="testuser3", password="testpass3")
        UserProfile.objects.create(user=user, tenant=tenant)
        token = self.get_token("testuser3", "testpass3")
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        url = reverse("patient-detail", args=[patient.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.data if hasattr(response, "data") else response.json()
        self.assertIn("email", data)
        self.assertEqual(len(data), 1)

    def test_create_patient_fails_for_non_partial_tenant(self):
        tenant = Tenant.objects.create(name="StrictHospital", type="hospital", allow_partial_patients=False, patient_visible_fields=["first_name", "last_name", "ssn", "email"])
        user = User.objects.create_user(username="strictuser", password="strictpass")
        UserProfile.objects.create(user=user, tenant=tenant)
        token = self.get_token("strictuser", "strictpass")
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.post(reverse("patient-list"), {"email": "fail@example.com"})
        self.assertEqual(response.status_code, 400)
        error_fields = response.data.keys() if hasattr(response, "data") else response.json().keys()
        self.assertTrue("first_name" in error_fields or "last_name" in error_fields or "ssn" in error_fields)

    def test_patient_detail_serves_right_fields(self):
        tenant = Tenant.objects.create(
            name="ClinicFields",
            type="clinic",
            allow_partial_patients=True,
            patient_visible_fields=["first_name", "email"]
        )
        patient = Patient.objects.create(
            tenant=tenant,
            first_name="Visible",
            last_name="Hidden",
            ssn="123-45-6789",
            email="visiblefields@example.com"
        )
        user = User.objects.create_user(username="fieldsuser", password="fieldspass")
        UserProfile.objects.create(user=user, tenant=tenant)
        token = self.get_token("fieldsuser", "fieldspass")
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        url = reverse("patient-detail", args=[patient.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.data if hasattr(response, "data") else response.json()
        self.assertEqual(set(data.keys()), {"first_name", "email"})
        self.assertEqual(data["first_name"], "Visible")
        self.assertEqual(data["email"], "visiblefields@example.com")
