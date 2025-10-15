
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.auth.models import AnonymousUser
from rest_framework.exceptions import AuthenticationFailed
from django.http import JsonResponse

from .models import AuditLog


class DRFTenantMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith("/api/"):
            try:
                jwt_auth = JWTAuthentication()
                auth_result = jwt_auth.authenticate(request)
                if auth_result:
                    user, _ = auth_result
                    request.user = user
                    tenant = getattr(getattr(user, "profile", None), "tenant", None)
                    if not tenant:
                        return JsonResponse(
                            {"detail": "Malformed token or tenant not assigned."},
                            status=400
                        )
                    request.tenant = tenant
                else:
                    request.user = AnonymousUser()
            except AuthenticationFailed as e:
                return JsonResponse({"detail": str(e)}, status=401)
            except Exception:
                request.user = AnonymousUser()

        response = self.get_response(request)
        return response
    

class AuditMixin:
    """
    Mixin para registrar acciones de auditoría en todos los endpoints DRF.
    Solo se activa si el tenant es premium.
    """

    def log_audit(self, action, instance=None, extra=None):
        tenant = getattr(self.request, "tenant", None)
        if not tenant or not tenant.premium:
            return

        AuditLog.objects.create(
            tenant=tenant,
            user=self.request.user if self.request.user.is_authenticated else None,
            model=instance.__class__.__name__ if instance else self.get_queryset().model.__name__,
            object_id=getattr(instance, "id", None),
            action=action,
            metadata={
                "path": self.request.path,
                "method": self.request.method,
                "query": dict(self.request.GET),
                **(extra or {}),
            },
        )

    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        self.log_audit("view", self.get_object())
        return response

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        self.log_audit("list")
        return response

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        instance = getattr(self, "instance", None)
        self.log_audit("create", instance)
        return response

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        self.log_audit("update", self.get_object())
        return response

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.log_audit("delete", instance)
        return super().destroy(request, *args, **kwargs)
