from django.db import models
from apps.tenant.models import Tenant

class Patient(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='patients')
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    ssn = models.CharField(max_length=20)
    email = models.EmailField(max_length=254, blank=True, null=True, unique=True)

