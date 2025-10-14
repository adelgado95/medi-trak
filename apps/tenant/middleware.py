from django.utils.deprecation import MiddlewareMixin
from .models import Tenant
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.auth.models import AnonymousUser

class TenantMiddleware(MiddlewareMixin):
    def process_request(self, request):
        user = None
        try:
            user_auth = JWTAuthentication()
            user_auth_result = user_auth.authenticate(request)
            if user_auth_result:
                user, _ = user_auth_result
        except Exception:
            user = None
        request.user = user or AnonymousUser()

        # Obtener tenant solo desde el perfil de usuario autenticado
        tenant = None
        if user and hasattr(user, 'profile') and hasattr(user.profile, 'tenant'):
            tenant = user.profile.tenant
        request.tenant = tenant