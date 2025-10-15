from django.db import models
from django.utils import timezone
from apps.tenant.models import Tenant

class AuditLog(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    user = models.ForeignKey("auth.User", on_delete=models.SET_NULL, null=True, blank=True)
    model = models.CharField(max_length=100)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    action = models.CharField(max_length=20)  # "view", "list", "create", "update", "delete"
    timestamp = models.DateTimeField(default=timezone.now)
    metadata = models.JSONField(default=dict, blank=True)
