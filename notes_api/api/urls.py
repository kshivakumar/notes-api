from django.urls import path, include
from rest_framework import routers

from notes_api.api import views


router = routers.DefaultRouter()
router.register("notebooks", views.NotebookViewSet, basename="notebook")
router.register("recyclebin", views.NotesRecycleBinViewSet, basename="recyclebin")

urlpatterns = [
    path("", include(router.urls)),
    path("user/", views.user, name="user"),
    path(
        "notebooks/<uuid:notebook_id>/pages",
        views.PageListCreateView.as_view(),
        name="page-list",
    ),
    path(
        "notebooks/<uuid:notebook_id>/pages/reposition",
        views.reposition_page,
        name="page-reposition",
    ),
    path("pages/move", views.move_pages, name="move-pages"),
    path("pages/<uuid:pk>", views.PageDetailView.as_view(), name="page-detail"),
    path(
        "pages/<uuid:page_id>/blocks",
        views.BlockListCreateView.as_view(),
        name="block-list",
    ),
    path(
        "pages/<uuid:page_id>/blocks/reposition",
        views.reposition_block,
        name="block-reposition",
    ),
    path("blocks/<uuid:pk>", views.BlockDetailView.as_view(), name="block-detail"),
]

