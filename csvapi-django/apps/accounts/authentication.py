import jwt
from django.conf import settings
from rest_framework import authentication, exceptions
from django.contrib.auth.models import User

class JWTAuthentication(authentication.BaseAuthentication):
    """
    Xác thực JWT được gửi qua header Authorization dạng:
       Authorization: Bearer <token>
    """
    def authenticate(self, request):
        auth_header = request.headers.get('Authorization')
        print(f"auth header is {auth_header}")
        if not auth_header:
            return None  # Nếu không có token, cho phép các permission khác xử lý
        
        try:
            prefix, token = auth_header.split(' ')
        except ValueError:
            raise exceptions.AuthenticationFailed("Invalid Authorization header format.")
        
        if prefix.lower() != 'bearer':
            raise exceptions.AuthenticationFailed("Authorization header must start with Bearer.")
        
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            raise exceptions.AuthenticationFailed("Token has expired.")
        except jwt.InvalidTokenError:
            raise exceptions.AuthenticationFailed("Invalid token.")
        
        try:
            user = User.objects.get(id=payload.get("user_id"))
        except User.DoesNotExist:
            raise exceptions.AuthenticationFailed("User not found.")
        
        return (user, None)
