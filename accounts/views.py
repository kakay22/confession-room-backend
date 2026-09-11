from django.contrib.auth.models import User

from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated

from .serializers import (
    RegisterSerializer,
    UserSerializer,
    AnonymousProfileSerializer,
)

from confessions.models import UserProfile


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]


class ProfileView(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class AnonymousProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = AnonymousProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        profile, created = UserProfile.objects.get_or_create(
            user=self.request.user,
            defaults={
                "anonymous_username": f"Anonymous{self.request.user.id}",
                "anonymous_avatar": "avatar1",
            }
        )

        return profile