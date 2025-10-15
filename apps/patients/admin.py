from django.contrib import admin
from .models import Patient
from apps.api.models import AuditLog

admin.site.register(Patient)
admin.site.register(AuditLog)