from django.contrib.auth.models import User
from rest_framework.viewsets import ModelViewSet
from rest_framework.generics import CreateAPIView, ListAPIView
from rest_framework.authentication import SessionAuthentication, TokenAuthentication, BasicAuthentication
from rest_framework.permissions import AllowAny, IsAuthenticated

from rest_framework.authtoken.models import Token

from .models import Notebook, Page
from .serializers import PageSerializer, UserSerializer, NotebookSerializer


class SignupView(CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (AllowAny,)


class LoginView():
    pass


class LogoutView():
    pass


class NotebookView(ListAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = NotebookSerializer

    def get_queryset(self):
        return self.request.user.notebooks.all()


class PageViewSet(ModelViewSet):
    queryset = Page.objects.all()
    serializer_class = PageSerializer
