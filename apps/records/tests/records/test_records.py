from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from apps.patients.models import Patient
from apps.tenant.models import Tenant
from apps.user.models import UserProfile
from apps.records.models import Record, FlexibleRecord
from django.contrib.auth.models import User

class TestPatientSSNScenarios(TestCase):
    def setUp(self):
        self.client = APIClient()

    def get_token(self, username, password):
        response = self.client.post('/api/token/', {"username": username, "password": password}, format="json")
        self.assertEqual(response.status_code, 200)
        return response.data["access"]

    def test_patient_ssn_hippa_mandatory_true(self):
        tenant = Tenant.objects.create(
            name="HIPAA Clinic",
            type="clinic",
            allow_partial_patients=False,
            patient_visible_fields=["first_name", "last_name", "ssn_data", "email"],
            patient_records_type=Tenant.RIGID,
            ssn_hippa_mandatory=True
        )
        user = User.objects.create_user(username="hippauser", password="hippapass")
        UserProfile.objects.create(user=user, tenant=tenant)
        token = self.get_token("hippauser", "hippapass")
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        # Should fail: ssn as string
        data = {
            "tenant": tenant.id,
            "first_name": "Alice",
            "last_name": "Smith",
            "ssn": "123-45-6789",
            "email": "alice.smith@example.com"
        }
        response = self.client.post(reverse("patient-list"), data, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("ssn_data", response.data)
        # Should succeed: ssn_data as JSON
        data = {
            "tenant": tenant.id,
            "first_name": "Alice",
            "last_name": "Smith",
            "ssn_data": {
                "number": "123-45-6789",
                "verified": "true",
                "verification_date": "null"
            },
            "email": "alice.smith@example.com"
        }
        response = self.client.post(reverse("patient-list"), data, format="json")
        self.assertEqual(response.status_code, 201)
        patient_id = response.data["id"]
        patient = Patient.objects.get(id=patient_id)
        self.assertEqual(patient.ssn_data["number"], "123-45-6789")
        self.assertEqual(patient.ssn_data["verified"], "true")
        self.assertEqual(patient.ssn_data["verification_date"], "null")
        self.assertIsNone(patient.ssn)

    def test_patient_ssn_hippa_mandatory_false(self):
        tenant = Tenant.objects.create(
            name="Non-HIPAA Clinic",
            type="clinic",
            allow_partial_patients=False,
            patient_visible_fields=["first_name", "last_name", "ssn", "email"],
            patient_records_type=Tenant.RIGID,
            ssn_hippa_mandatory=False
        )
        user = User.objects.create_user(username="nonhippauser", password="nonhippapass")
        UserProfile.objects.create(user=user, tenant=tenant)
        token = self.get_token("nonhippauser", "nonhippapass")
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        # Should succeed: ssn as string
        data = {
            "tenant": tenant.id,
            "first_name": "Bob",
            "last_name": "Brown",
            "ssn": "987-65-4321",
            "email": "bob.brown@example.com"
        }
        response = self.client.post(reverse("patient-list"), data, format="json")
        self.assertEqual(response.status_code, 201)
        patient_id = response.data["id"]
        patient = Patient.objects.get(id=patient_id)
        self.assertEqual(patient.ssn, "987-65-4321")
        self.assertTrue(patient.ssn_data is None or patient.ssn_data == {})
        # Should not accept ssn_data
        data = {
            "tenant": tenant.id,
            "first_name": "Bob",
            "last_name": "Brown",
            "ssn_data": {
                "number": "123-45-6789",
                "verified": "true",
                "verification_date": "null"
            },
            "email": "bob2.brown@example.com"
        }
        response = self.client.post(reverse("patient-list"), data, format="json")
        self.assertEqual(response.status_code, 400)

    def test_create_flexible_record(self):
        tenant = Tenant.objects.create(
            name="ClinicFlex",
            type="clinic",
            allow_partial_patients=True,
            patient_visible_fields=["email"],
            patient_records_type=Tenant.FLEXIBLE
        )
        user = User.objects.create_user(username="flexuser", password="flexpass")
        UserProfile.objects.create(user=user, tenant=tenant)
        patient = Patient.objects.create(tenant=tenant, email="flex@example.com")
        token = self.get_token("flexuser", "flexpass")
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        data = {
            "patient": patient.id,
            "record_type": "Diagnosis",
            "data": {
                "custom_field1": "value1",
                "custom_field2": 123,
                "custom_field3": "true"
            }
        }
        self.client.post(reverse("record-list"), data, format="json")
        record = FlexibleRecord.objects.filter(patient=patient).first()
        self.assertIsNotNone(record)
        self.assertEqual(record.record_type, "Diagnosis")
        self.assertEqual(record.data["custom_field1"], "value1")

    def test_create_rigid_record(self):
        tenant = Tenant.objects.create(
            name="HospitalRigid",
            type="hospital",
            allow_partial_patients=False,
            patient_visible_fields=["first_name", "last_name", "ssn", "email"],
            patient_records_type=Tenant.RIGID
        )
        user = User.objects.create_user(username="rigiduser", password="rigidpass")
        UserProfile.objects.create(user=user, tenant=tenant)
        patient = Patient.objects.create(
            tenant=tenant,
            first_name="John",
            last_name="Doe",
            ssn="123-45-6789",
            email="john.doe@example.com"
        )
        token = self.get_token("rigiduser", "rigidpass")
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        data = {
            "patient": patient.id,
            "diagnosis": "Flu",
            "treatment": "Rest",
            "doctor_name": "Dr. Smith",
            "notes": "Patient should rest for 3 days."
        }
        self.client.post(reverse("record-list"), data, format="json")
        record = Record.objects.filter(patient=patient).first()
        self.assertIsNotNone(record)
        self.assertEqual(record.diagnosis, "Flu")
        self.assertEqual(record.doctor_name, "Dr. Smith")


