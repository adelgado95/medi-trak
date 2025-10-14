# utils/decorators.py

from functools import wraps
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.auth.models import AnonymousUser


def tenant_required(view_func):
    """
    Decorator that authenticates a request using JWT,
    attaches user and tenant to request, and enforces tenant existence.
    """
    @wraps(view_func)
    def _wrapped_view(view, request, *args, **kwargs):
        user = None
        try:
            # Authenticate with JWT
            jwt_auth = JWTAuthentication()
            auth_result = jwt_auth.authenticate(request)
            if auth_result:
                user, _ = auth_result
        except Exception:
            user = None

        request.user = user or AnonymousUser()

        # Ensure authenticated
        if not user or not user.is_authenticated:
            return Response(
                {"detail": "Unauthorized or invalid token."},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Extract tenant
        tenant = getattr(getattr(user, "profile", None), "tenant", None)

        if not tenant:
            return Response(
                {"detail": "Malformed token or tenant not assigned."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Attach tenant to request
        request.tenant = tenant

        # Continue normal flow
        return view_func(view, request, *args, **kwargs)

    return _wrapped_view
