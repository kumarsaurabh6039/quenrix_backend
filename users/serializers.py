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
    userid = serializers.CharField(read_only=True)  # ✅ Prevents validation error

    class Meta:
        model = Users
        fields = ['userid', 'username', 'password', 'roleid', 'role', 'is_active']

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
