from django.contrib.auth.models import User
from rest_framework import serializers

from .models import Notebook, Page


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["id", "username", "first_name", "last_name", "last_login", "password"]
    
    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class NotebookSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    class Meta:
        model = Notebook
        fields = ["id", "user", "title", "created", "updated"]
    
    def create(self, validated_data):
        user = validated_data.pop('user')
        return Notebook.objects.create(user=user, **validated_data)


class PageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Page
        fields = "__all__"
