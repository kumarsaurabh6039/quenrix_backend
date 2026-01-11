from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from .models import Users, Roles

class RolesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Roles
        fields = ['roleid', 'rolename', 'is_active']


class UsersSerializer(serializers.ModelSerializer):
    username = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True)
    roleid = serializers.PrimaryKeyRelatedField(queryset=Roles.objects.all())
    role = RolesSerializer(read_only=True)
    userid = serializers.CharField(read_only=True)

    class Meta:
        model = Users
        fields = ['userid', 'username', 'password', 'roleid', 'role', 'is_active']

    #  NEW: Custom Validation for Gmail 
    def validate_username(self, value):
        """
        Check that the email is a valid Gmail address.
        """
        email = value.lower()
        if not email.endswith('@gmail.com'):
            raise serializers.ValidationError("Only @gmail.com email addresses are allowed.")
        
        # Optional: Backend check for 'numeric only' username if you want strictly enforcing it
        local_part = email.split('@')[0]
        if local_part.isdigit():
             raise serializers.ValidationError("Username part cannot be purely numeric.")

        return value

    def create(self, validated_data):
        """Hash password before saving new user"""
        password = validated_data.pop('password')
        user = Users(**validated_data)
        user.password = make_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        """Hash password if updated"""
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.password = make_password(password)
        instance.save()
        return instance