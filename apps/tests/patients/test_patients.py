import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from apps.patients.models import Patient
from apps.tenant.models import Tenant
from django.contrib.auth.models import User
from apps.user.models import UserProfile



@pytest.mark.django_db
def test_create_patient_partial_fields():
    tenant = Tenant.objects.create(name="Clinic", type="clinic", allow_partial_patients=True, patient_visible_fields=["email"])
    user = User.objects.create_user(username="testuser", password="testpass")
    UserProfile.objects.create(user=user,tenant=tenant)
    user.profile.tenant = tenant
    user.profile.save()
    client = APIClient()
    # Authenticate using JWT
    response = client.post('/api/token/', {"username": "testuser", "password": "testpass"})
    assert response.status_code == 200
    token = response.json()["access"]
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    response = client.post(reverse("patient-list"), {"email": "partial@example.com"})
    assert response.status_code == 201
    assert Patient.objects.filter(email="partial@example.com").exists()

@pytest.mark.django_db
def test_create_patient_all_fields():
    tenant = Tenant.objects.create(name="Hospital", type="hospital", allow_partial_patients=False, patient_visible_fields=["first_name", "last_name", "ssn", "email"])
    user = User.objects.create_user(username="testuser2", password="testpass2")
    UserProfile.objects.create(user=user, tenant=tenant)
    client = APIClient()
    # Authenticate using JWT
    token_response = client.post('/api/token/', {"username": "testuser2", "password": "testpass2"}, format="json")
    token = token_response.json()["access"]
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    data = {
        "first_name": "John",
        "last_name": "Doe",
        "ssn": "123-45-6789",
        "email": "john.doe@example.com"
    }
    response = client.post(reverse("patient-list"), data, format="json")
    assert response.status_code == 201
    assert Patient.objects.filter(email="john.doe@example.com").exists()

@pytest.mark.django_db
def test_patient_detail_fields():
    tenant = Tenant.objects.create(name="Clinic", type="clinic", allow_partial_patients=True, patient_visible_fields=["email"])
    patient = Patient.objects.create(tenant=tenant, email="visible@example.com")
    user = User.objects.create_user(username="testuser3", password="testpass3")
    UserProfile.objects.create(user=user, tenant=tenant)
    client = APIClient()
    # Authenticate using JWT
    token_response = client.post('/api/token/', {"username": "testuser3", "password": "testpass3"}, format="json")
    token = token_response.json()["access"]
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    url = reverse("patient-detail", args=[patient.pk])
    response = client.get(url)
    assert response.status_code == 200
    assert "email" in response.json()
    assert len(response.json()) == 1

@pytest.mark.django_db
def test_create_patient_fails_for_non_partial_tenant():
    tenant = Tenant.objects.create(name="StrictHospital", type="hospital", allow_partial_patients=False, patient_visible_fields=["first_name", "last_name", "ssn", "email"])
    user = User.objects.create_user(username="strictuser", password="strictpass")
    UserProfile.objects.create(user=user, tenant=tenant)
    client = APIClient()
    # Authenticate using JWT
    token_response = client.post('/api/token/', {"username": "strictuser", "password": "strictpass"}, format="json")
    token = token_response.json()["access"] if hasattr(token_response, 'json') else token_response.data["access"]
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    # Try to create patient with only email
    response = client.post(reverse("patient-list"), {"email": "fail@example.com"}, format="json")
    status = response.status_code if hasattr(response, 'status_code') else response.status
    assert status == 400
    # Should fail because required fields are missing
    error_fields = response.json().keys() if hasattr(response, 'json') else response.data.keys()
    assert "first_name" in error_fields or "last_name" in error_fields or "ssn" in error_fields
