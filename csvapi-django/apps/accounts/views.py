from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate
from django.conf import settings
import jwt
from datetime import datetime, timedelta
from .serializers import UserRegisterSerializer, UserLoginSerializer

@api_view(['GET'])
def fuck(request):
    return Response({"message": "Registration successful"}, status=status.HTTP_201_CREATED)

@api_view(['POST'])
def register(request):
    serializer = UserRegisterSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({"message": "Registration successful"}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def login(request):
    serializer = UserLoginSerializer(data=request.data)
    if serializer.is_valid():
        username = serializer.validated_data['username']
        password = serializer.validated_data['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            payload = {
                "user_id": user.id,
                "exp": datetime.utcnow() + timedelta(minutes=30)
            }
            token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
            return Response({"message": "Login successful", "token": token}, status=status.HTTP_200_OK)
        return Response({"error": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
