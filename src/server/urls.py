from xml.etree.ElementInclude import include
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token

from .views import NotebookView, PageViewSet, SignupView


router = DefaultRouter()
router.register(r"pages", PageViewSet)


urlpatterns = [
    path("signup", SignupView.as_view()),
    path('api-token-auth', obtain_auth_token),
    # path("/login",),
    # path("/logout",),
    path("", include(router.urls)),
    path("notebook", NotebookView.as_view(), name="notebook") 
]
