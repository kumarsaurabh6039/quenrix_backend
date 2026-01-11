from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import connection
from django.core.mail import send_mail
from django.contrib.auth.hashers import make_password, check_password
from django.db.models.functions import Cast, Substr
from django.db.models import IntegerField
from .models import Users
from .serializers import UsersSerializer
from django.conf import settings
from rest_framework import generics

# === IMPORTS ===
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated, AllowAny 

class RegisterUserView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UsersSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            
            # ✅ Check if user already exists (Case Insensitive)
            if Users.objects.filter(username__iexact=data['username']).exists():
                # FIX: Use 409 Conflict and 'detail' key so frontend catches it correctly
                return Response(
                    {'detail': 'User is already registered.'}, 
                    status=status.HTTP_409_CONFLICT
                )

            raw_password = request.data['password']
            hashed_password = make_password(raw_password)
            userId = data.get('userid') or self.generate_user_id()
            role_name = data['roleid'].rolename 

            try:
                with connection.cursor() as cursor:
                    cursor.execute("""
                        EXEC sp_register_user @userId=%s, @username=%s, @password=%s, @roleId=%s
                    """, [userId, data['username'], hashed_password, data['roleid'].roleid])
                    result = cursor.fetchall()

                # Send welcome email
                self.send_welcome_email(data['username'], raw_password, role_name)

                return Response({
                    'message': 'User registered successfully',
                    'userId': userId,
                    'username': data['username'],
                    'role': role_name,
                    'email_sent': True,
                    'db_result': result
                }, status=status.HTTP_201_CREATED)

            except Exception as e:
                # FIX: Use 'detail' key for generic exceptions too
                return Response({'detail': f'Registration failed: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)

        # ✅ Clean Error Message for Validation Errors
        # Instead of returning the full dict, return the first error message directly
        first_error = "Invalid data provided."
        if serializer.errors:
            # Extract the first error from the dictionary
            field, errors = next(iter(serializer.errors.items()))
            if errors and isinstance(errors, list):
                first_error = errors[0]
            else:
                first_error = str(errors)
        
        # FIX: Use 'detail' key so frontend displays this message instead of "Invalid data sent"
        return Response({'detail': first_error}, status=status.HTTP_400_BAD_REQUEST)

    def generate_user_id(self):
        last_user = (
            Users.objects.filter(userid__startswith='USR')
            .annotate(num_part=Cast(Substr('userid', 4), IntegerField()))
            .order_by('-num_part')
            .first()
        )
        if last_user:
            last_number = int(last_user.userid[3:])
            new_number = last_number + 1
        else:
            new_number = 1
        return f"USR{new_number:03d}"

    def send_welcome_email(self, username, raw_password, role_name):
        subject = 'Welcome to the LMS Platform'
        message = f"""
Hi {username},

Your account has been successfully created.

Username: {username}
Password: {raw_password}
Role: {role_name}

Please keep this information secure.

Regards,
LMS Team
"""
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [username],
                fail_silently=False
            )
        except Exception:
            # Don't break registration if email fails
            pass


class UpdatePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        userId = request.data.get('userId')
        raw_password = request.data.get('newPassword')
        if not userId or not raw_password:
            return Response({'error': 'User ID and new password are required.'}, status=status.HTTP_400_BAD_REQUEST)

        hashed_password = make_password(raw_password)

        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    EXEC sp_update_user_password @userId=%s, @newPassword=%s
                """, [userId, hashed_password])
                result = cursor.fetchall()
            return Response({'message': 'Password updated successfully', 'data': result}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class SoftDeleteUserView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        userId = request.data.get('userId')
        if not userId:
            return Response({'error': 'User ID is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with connection.cursor() as cursor:
                cursor.execute("UPDATE users SET is_active = 0 WHERE userId = %s", [userId])
            return Response({'message': f'User {userId} deactivated successfully'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class HardDeleteUserView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        userId = request.data.get('userId')
        if not userId:
            return Response({'error': 'User ID is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    EXEC sp_hard_delete_user @userId=%s
                """, [userId])
            return Response({'message': f'User {userId} permanently deleted'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class LoginUserView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        # Validation
        if not username or not password:
            return Response(
                {'error': 'Both username and password are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = Users.objects.select_related('roleid').get(username=username)
        except Users.DoesNotExist:
            return Response(
                {'error': 'Invalid username or password.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Check if user is active
        if not user.is_active:
            return Response(
                {'error': 'Account is deactivated. Please contact admin.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Verify password
        if not check_password(password, user.password):
            return Response(
                {'error': 'Invalid username or password.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        refresh = RefreshToken()
        refresh['user_id'] = user.userid
        refresh['role'] = user.roleid.rolename if user.roleid else 'Unknown'
        return Response({
            'message': 'Login successful',
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'userId': user.userid,
            'username': user.username,
            'role': user.roleid.rolename if user.roleid else None
        }, status=status.HTTP_200_OK)


class ListAllUsersView(generics.ListAPIView):
    """
    API view to list all users.
    """
    permission_classes = [IsAuthenticated]
    
    serializer_class = UsersSerializer

    def get_queryset(self):
        queryset = Users.objects.select_related('roleid').all()
        return queryset


class ReactivateUserView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        userId = request.data.get('userId')
        if not userId:
            return Response({'error': 'User ID is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with connection.cursor() as cursor:
                cursor.execute("UPDATE users SET is_active = 1 WHERE userId = %s", [userId])

            return Response(
                {'message': f'User {userId} reactivated successfully'},
                status=status.HTTP_200_OK
            )
            

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)