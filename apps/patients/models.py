from django.db import models
from apps.tenant.models import Tenant

class Patient(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='patients', null=True, blank=True)
    first_name = models.CharField(max_length=100, null=True, blank=True)
    last_name = models.CharField(max_length=100, null=True, blank=True)
    ssn = models.CharField(max_length=20, null=True, blank=True)
    email = models.EmailField(max_length=254, unique=True)

