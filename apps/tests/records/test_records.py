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

@pytest.mark.django_db
def test_patient_ssn_hippa_mandatory_true():
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
    client = APIClient()
    token_response = client.post('/api/token/', {"username": "hippauser", "password": "hippapass"}, format="json")
    token = token_response.data["access"]
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    # Should fail: ssn as string
    data = {
        "tenant": tenant.id,
        "first_name": "Alice",
        "last_name": "Smith",
        "ssn": "123-45-6789",
        "email": "alice.smith@example.com"
    }
    response = client.post(reverse("patient-list"), data, format="json")
    assert response.status_code == 400
    assert "ssn_data" in response.data
    # Should succeed: ssn_data as JSON
    data = {
        "tenant": tenant.id,
        "first_name": "Alice",
        "last_name": "Smith",
        "ssn_data": {
            "number": "123-45-6789",
            "verified": "true",
            "verification_date": "null"}
        ,
        "email": "alice.smith@example.com"
    }
    response = client.post(reverse("patient-list"), data, format="json")
    assert response.status_code == 201
    patient_id = response.data["id"]
    patient = Patient.objects.get(id=patient_id)
    assert patient.ssn_data["number"] == "123-45-6789"
    assert patient.ssn_data["verified"] == "true"
    assert patient.ssn_data["verification_date"] == "null"
    assert patient.ssn is None

@pytest.mark.django_db
def test_patient_ssn_hippa_mandatory_false():
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
    client = APIClient()
    token_response = client.post('/api/token/', {"username": "nonhippauser", "password": "nonhippapass"}, format="json")
    token = token_response.data["access"]
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    # Should succeed: ssn as string
    data = {
        "tenant": tenant.id,
        "first_name": "Bob",
        "last_name": "Brown",
        "ssn": "987-65-4321",
        "email": "bob.brown@example.com"
    }
    response = client.post(reverse("patient-list"), data, format="json")
    assert response.status_code == 201
    patient_id = response.data["id"]
    patient = Patient.objects.get(id=patient_id)
    assert patient.ssn == "987-65-4321"
    assert patient.ssn_data is None or patient.ssn_data == {}
    # Should not accept ssn hippa
    data = {
        "tenant": tenant.id,
        "first_name": "Bob",
        "last_name": "Brown",
        "ssn_data": {
            "number": "123-45-6789",
            "verified": "true",
            "verification_date": "null"}
        ,
        "email": "bob2.brown@example.com"
    }
    response = client.post(reverse("patient-list"), data, format="json")
    assert response.status_code == 400


