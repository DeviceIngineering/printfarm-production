"""
Authentication utilities for file downloads.
"""
from functools import wraps
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework import status

def auth_from_query_param(view_func):
    """
    Decorator that allows authentication via query parameter for file downloads.
    """
    @wraps(view_func)
    def wrapped_view(request, *args, **kwargs):
        # Try to authenticate from query parameter if not already authenticated
        if not request.user.is_authenticated:
            auth_token = request.GET.get('auth_token')
            if auth_token:
                try:
                    token = Token.objects.get(key=auth_token)
                    request.user = token.user
                    request.auth = token
                except Token.DoesNotExist:
                    return Response(
                        {'error': 'Invalid authentication token'},
                        status=status.HTTP_401_UNAUTHORIZED
                    )
        
        # Check if user is authenticated
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Authentication required'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        return view_func(request, *args, **kwargs)
    
    return wrapped_view