from django.db import models
from apps.patients.models import Patient

class Record(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='records')
    record_type = models.CharField(max_length=50)
    data = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)