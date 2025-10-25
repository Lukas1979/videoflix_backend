from django.contrib.auth.models import User
from rest_framework import serializers


class RegistrationSerializer(serializers.ModelSerializer):
    """
    Checks the data and creates a new user.
    """

    confirmed_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['password', 'confirmed_password', 'email']
        extra_kwargs = {'password': { 'write_only': True }, 'email': { 'required': True }}

    def validate_confirmed_password(self, value):
        password = self.initial_data.get('password')
        if password and value and password != value:
            raise serializers.ValidationError('Passwords do not match')
        
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('Email already exists')
        
        return value

    def save(self):
        email = self.validated_data['email']
        pw = self.validated_data['password']
        account = User(email=email, username=email, is_active=False)
        account.set_password(pw)
        account.save()

        return account
