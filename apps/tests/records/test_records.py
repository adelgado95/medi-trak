import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from apps.patients.models import Patient
from apps.tenant.models import Tenant
from apps.user.models import UserProfile
from apps.records.models import Record, FlexibleRecord
from django.contrib.auth.models import User

@pytest.mark.django_db
def test_create_flexible_record():
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
    client = APIClient()
    token_response = client.post('/api/token/', {"username": "flexuser", "password": "flexpass"}, format="json")
    token = token_response.data["access"]
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    data = {
        "patient": patient.id,
        "record_type": "Diagnosis",
        "data": {
            "custom_field1": "value1",
            "custom_field2": 123,
            "custom_field3": "true"
        }
    }
    client.post(reverse("record-list"), data, format="json")
    record = FlexibleRecord.objects.filter(patient=patient).first()
    assert record is not None
    assert record.record_type == "Diagnosis"
    assert record.data["custom_field1"] == "value1"

@pytest.mark.django_db
def test_create_rigid_record():
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
    client = APIClient()
    token_response = client.post('/api/token/', {"username": "rigiduser", "password": "rigidpass"}, format="json")
    token = token_response.data["access"]
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    data = {
        "patient": patient.id,
        "diagnosis": "Flu",
        "treatment": "Rest",
        "doctor_name": "Dr. Smith",
        "notes": "Patient should rest for 3 days."
    }
    client.post(reverse("record-list"), data, format="json")
    record = Record.objects.filter(patient=patient).first()
    assert record is not None
    assert record.diagnosis == "Flu"
    assert record.doctor_name == "Dr. Smith"
