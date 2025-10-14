from django.db import models

class Tenant(models.Model):
    name = models.CharField(max_length=255)
    premium = models.BooleanField(default=False)
    type = models.CharField(max_length=50, choices=[('hospital', 'Hospital'), ('clinic', 'Clinic'), ('mobile_app', 'Mobile App')])
    allow_partial_patients = models.BooleanField(default=True)