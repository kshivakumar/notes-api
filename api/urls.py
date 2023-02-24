from django.urls import path, include
from rest_framework import routers

from api import views

#########################################################################
# APIs
#########################################################################
#
# /user
# GET dictionary of user details, preferences(themes, UI toggles, notebook order), last_viewed_page, etc.
#
# /notebooks
# GET user's notebooks (id and title)
#     Query Params: order, filters, pagination, prefetch notebooks details
# POST create a new notebook
#
# /notebooks/reposition
# POST reposition a notebook (custom ordering)
#
# /notebooks/<notebook_id>
# GET notebook details
# PUT/PATCH/DELETE notebook
#
# /notebooks/<notebook_id>/pages
# GET notebook's page ids and titles
#     Query Params: order, filters, pagination, prefetch pages details
# POST create a new page
#
# /notebooks/<notebook_id>/pages/reposition
# POST reposition a page within the same notebook (custom ordering)
#
# /pages/move
# POST move one or more pages to another notebook
#
# /pages/<page_id>
# GET page details
# PUT/PATCH/DELETE page details such as title and metadata
#
# /pages/<page_id>/blocks
# GET page's block ids
#     Query Params: pagination, prefetch blocks details
# POST add a new block
#
# /pages/<page_id>/blocks/reposition
# POST reposition a block within the same page
#
# /blocks/<block_id>
# GET/PATCH/DELETE a block
#
# /recylebin
# GET list of deleted notebooks and pages with pagination
#
# /recyclebin/<id>
# GET retrieve a deleted page or notebook(with all its pages)
# DELETE permanently delete a notebook or page
#
# /recyclebin/<id>/restore
# POST restore a page/notebook
#
##########################################################################

router = routers.DefaultRouter()
router.register("notebooks", views.NotebookViewSet, basename="notebooks")
router.register("recyclebin", views.NotesRecycleBinViewSet, basename="recyclebin")

api_urls = [
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

urlpatterns = [
    path("api/", include(api_urls), name="api"),
]
