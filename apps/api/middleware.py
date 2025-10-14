# core/middleware/tenant_middleware.py

from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.auth.models import AnonymousUser
from rest_framework.exceptions import AuthenticationFailed
from django.http import JsonResponse


class DRFTenantMiddleware:
    """
    Middleware that applies tenant extraction to all DRF requests.
    Only triggers for API paths (e.g., /api/).
    """

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
