from django.db import models

class Tenant(models.Model):
    RIGID = "rigid"
    FLEXIBLE = "flexible"
    RECORD_TYPE_CHOICES = {
        RIGID: 'Rigido',
        FLEXIBLE: 'Flexible',
    }
    name = models.CharField(max_length=255)
    premium = models.BooleanField(default=False)
    type = models.CharField(max_length=50, choices=[('hospital', 'Hospital'), ('clinic', 'Clinic'), ('mobile_app', 'Mobile App')])
    allow_partial_patients = models.BooleanField(default=True)
    patient_visible_fields = models.JSONField(
        default=list,
        help_text="List of Patient model fields this tenant is allowed to see, e.g. ['name', 'email'] or ['all']"
    )
    patient_records_type = models.CharField(max_length=50, choices=RECORD_TYPE_CHOICES)
    ssn_hippa_mandatory = models.BooleanField(default=False)

    def __str__(self):
        return self.name + self.type