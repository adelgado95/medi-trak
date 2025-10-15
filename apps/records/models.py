from django.db import models
from apps.patients.models import Patient

from django.db import models

class BaseRecord(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True

class Record(BaseRecord):
    diagnosis = models.TextField()
    treatment = models.TextField()
    doctor_name = models.CharField(max_length=255)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"RigidRecord({self.patient} - {self.diagnosis[:20]})"
    

class FlexibleRecord(BaseRecord):
    record_type = models.CharField(max_length=50,)
    data = models.JSONField(default=dict)

    def __str__(self):
        return f"FlexibleRecord({self.patient} - {self.record_type})"
