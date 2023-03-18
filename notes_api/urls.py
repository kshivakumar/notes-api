from django.urls import path, include


urlpatterns = [
    path("api/", include("notes_api.api.urls")),
    path("api-auth/", include("rest_framework.urls"), name="rest_framework"),
    # TODO: redirect login page to /api/notebooks
]

