from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, AuthenticationFailed
from .models import Users

class CustomJWTAuthentication(JWTAuthentication):
    def get_user(self, validated_token):
        """
        Custom logic to find user from Users table using userId from token.
        Default Django logic fails because it looks for 'id' in auth_user table.
        """
        try:
            user_id = validated_token.get('user_id')
            if not user_id:
                 raise InvalidToken('Token contained no recognizable user identification')
        except KeyError:
            raise InvalidToken('Token contained no recognizable user identification')

        try:
            user = Users.objects.get(userid=user_id)
        except Users.DoesNotExist:
            raise AuthenticationFailed('User not found', code='user_not_found')

        if not user.is_active:
             raise AuthenticationFailed('User is inactive', code='user_inactive')

        return user