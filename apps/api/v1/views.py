from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import login, logout
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .serializers import (
    LoginSerializer, 
    UserSerializer, 
    RegisterSerializer,
    ChangePasswordSerializer
)


class LoginAPIView(APIView):
    """
    API endpoint for user login.
    
    POST /api/v1/auth/login/
    Request Body:
    {
        "username": "your_username",
        "password": "your_password"
    }
    
    Response:
    {
        "user": {...},
        "tokens": {
            "access": "...",
            "refresh": "..."
        },
        "message": "Login successful"
    }
    """
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        operation_summary="Login user",
        request_body=LoginSerializer,
        responses={
            200: openapi.Response(
                description="Login successful",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'user': openapi.Schema(type=openapi.TYPE_OBJECT),
                        'tokens': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'access': openapi.Schema(type=openapi.TYPE_STRING),
                                'refresh': openapi.Schema(type=openapi.TYPE_STRING),
                            },
                        ),
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                    },
                ),
            ),
            400: "Validation error",
        },
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        
        if serializer.is_valid():
            user = serializer.validated_data['user']
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            
            # Login user (for session-based as well)
            login(request, user)
            
            return Response({
                'user': UserSerializer(user).data,
                'tokens': {
                    'access': str(refresh.access_token),
                    'refresh': str(refresh),
                },
                'message': 'Login successful'
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutAPIView(APIView):
    """
    API endpoint for user logout.
    
    POST /api/v1/auth/logout/
    Headers: Authorization: Bearer <access_token>
    
    Response:
    {
        "message": "Logout successful"
    }
    """
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_summary="Logout user",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'refresh_token': openapi.Schema(type=openapi.TYPE_STRING),
            },
        ),
        responses={
            200: openapi.Response(
                description="Logout successful",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={'message': openapi.Schema(type=openapi.TYPE_STRING)},
                ),
            ),
            400: "Logout failed",
        },
    )
    def post(self, request):
        try:
            # Logout from session
            logout(request)
            
            # Optionally blacklist the refresh token if using token blacklist
            refresh_token = request.data.get('refresh_token')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            
            return Response({
                'message': 'Logout successful'
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class RegisterAPIView(APIView):
    """
    API endpoint for user registration.
    
    POST /api/v1/auth/register/
    Request Body:
    {
        "username": "new_user",
        "email": "user@example.com",
        "password": "secure_password",
        "password2": "secure_password",
        "first_name": "John",
        "last_name": "Doe",
        "role": "EMPLOYEE"
    }
    
    Response:
    {
        "user": {...},
        "tokens": {
            "access": "...",
            "refresh": "..."
        },
        "message": "Registration successful"
    }
    """
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        operation_summary="Register user",
        request_body=RegisterSerializer,
        responses={
            201: openapi.Response(
                description="Registration successful",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'user': openapi.Schema(type=openapi.TYPE_OBJECT),
                        'tokens': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'access': openapi.Schema(type=openapi.TYPE_STRING),
                                'refresh': openapi.Schema(type=openapi.TYPE_STRING),
                            },
                        ),
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                    },
                ),
            ),
            400: "Validation error",
        },
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        
        if serializer.is_valid():
            user = serializer.save()
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'user': UserSerializer(user).data,
                'tokens': {
                    'access': str(refresh.access_token),
                    'refresh': str(refresh),
                },
                'message': 'Registration successful'
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserProfileAPIView(APIView):
    """
    API endpoint to get current user profile.
    
    GET /api/v1/auth/profile/
    Headers: Authorization: Bearer <access_token>
    
    Response:
    {
        "user": {...}
    }
    """
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_summary="Get current user profile",
        responses={200: UserSerializer},
    )
    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response({
            'user': serializer.data
        }, status=status.HTTP_200_OK)
    
    @swagger_auto_schema(
        operation_summary="Update current user profile",
        request_body=UserSerializer,
        responses={200: UserSerializer, 400: "Validation error"},
    )
    def put(self, request):
        """Update user profile"""
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                'user': serializer.data,
                'message': 'Profile updated successfully'
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordAPIView(APIView):
    """
    API endpoint to change user password.
    
    POST /api/v1/auth/change-password/
    Headers: Authorization: Bearer <access_token>
    Request Body:
    {
        "old_password": "current_password",
        "new_password": "new_password",
        "new_password2": "new_password"
    }
    
    Response:
    {
        "message": "Password changed successfully"
    }
    """
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_summary="Change user password",
        request_body=ChangePasswordSerializer,
        responses={
            200: openapi.Response(
                description="Password changed successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={'message': openapi.Schema(type=openapi.TYPE_STRING)},
                ),
            ),
            400: "Validation error",
        },
    )
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            user = request.user
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            
            return Response({
                'message': 'Password changed successfully'
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([AllowAny])
@swagger_auto_schema(
    operation_summary='API root',
    responses={
        200: openapi.Response(
            description='API root endpoints',
            schema=openapi.Schema(type=openapi.TYPE_OBJECT),
        )
    },
)
def api_root(request):
    """
    API Root endpoint - provides an overview of available API endpoints.
    
    GET /api/v1/
    """
    return Response({
        'message': 'Welcome to Inventory Management API',
        'version': 'v1',
        'endpoints': {
            'auth': {
                'login': '/api/v1/auth/login/',
                'logout': '/api/v1/auth/logout/',
                'register': '/api/v1/auth/register/',
                'profile': '/api/v1/auth/profile/',
                'change_password': '/api/v1/auth/change-password/',
                'token_refresh': '/api/v1/auth/token/refresh/',
            },
            'documentation': {
                'swagger': '/api/docs/',
                'redoc': '/api/redoc/',
            }
        }
    })
