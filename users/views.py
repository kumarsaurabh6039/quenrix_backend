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


class RegisterUserView(APIView):
    def post(self, request):
        serializer = UsersSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            raw_password = request.data['password']  # original password from request
            hashed_password = make_password(raw_password)
            userId = data.get('userid') or self.generate_user_id()
            role_name = data['roleid'].rolename  # get role name from roleid object

            try:
                with connection.cursor() as cursor:
                    cursor.execute("""
                        EXEC sp_register_user @userId=%s, @username=%s, @password=%s, @roleId=%s
                    """, [userId, data['username'], hashed_password, data['roleid'].roleid])
                    result = cursor.fetchall()

                # Send welcome email
                subject = 'Welcome to the LMS Platform'
                message = f"""
Hi {data['username']},

Your account has been successfully created.

Username: {data['username']}
Password: {raw_password}
Role: {role_name}

Please keep this information secure.

Regards,
LMS Team
"""
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [data['username']],
                    fail_silently=False
                )

                return Response({
                    'message': 'User registered successfully',
                    'userId': userId,
                    'username': data['username'],
                    'role': role_name,
                    'email_sent': True,
                    'db_result': result
                }, status=status.HTTP_201_CREATED)

            except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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



class UpdatePasswordView(APIView):
    def post(self, request):
        userId = request.data.get('userId')
        raw_password = request.data.get('newPassword')
        if not userId or not raw_password:
            return Response({'error': 'userId and newPassword are required'}, status=status.HTTP_400_BAD_REQUEST)

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
    def post(self, request):
        userId = request.data.get('userId')
        if not userId:
            return Response({'error': 'userId is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with connection.cursor() as cursor:
                cursor.execute("UPDATE users SET is_active = 0 WHERE userId = %s", [userId])
            return Response({'message': f'User {userId} deactivated successfully'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


# NOTE: This view deletes permanently only those users 
# have no information in database other than userId, 
# username, passwrod & roleId..

class HardDeleteUserView(APIView):
    def post(self, request):
        userId = request.data.get('userId')
        if not userId:
            return Response({'error': 'userId is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    EXEC sp_hard_delete_user @userId=%s
                """, [userId])
            return Response({'message': f'User {userId} permanently deleted'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class LoginUserView(APIView):
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

        # Login successful
        return Response({
            'message': 'Login successful',
            'userId': user.userid,
            'username': user.username,
            'role': user.roleid.rolename if user.roleid else None
        }, status=status.HTTP_200_OK)