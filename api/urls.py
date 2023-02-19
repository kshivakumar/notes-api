from django.urls import path, include
from rest_framework.routers import DefaultRouter

from api import views

#########################################################################
# APIs
#########################################################################
#
# /user
# GET dictionary of user details, preferences(themes, UI toggles, notebook order), last_viewed_page, etc.
#
# /notebooks
# GET user's notebooks
#     Query Params: order, filters, pagination, prefetch notebooks details
# POST create a new notebook
#
# /notebooks/reorder
# POST re-arrange a notebook (custom ordering)
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
# /notebooks/<notebook_id>/pages/reorder
# POST re-arrange a page within the same notebook (custom ordering)
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
# /pages/<page_id>/blocks/reorder
# POST re-arrange one or more blocks within the same page
#
# /blocks/<block_id>
# GET/PUT/PATCH/DELETE a block
#
# /blocks/move
# POST move one or more blocks to other pages of same or different notebooks
#
# /recylebin
# GET list of deleted notebooks and pages with pagination
#
# /recyclebin/<id>
# PATCH restore a notebook or page
# DELETE permanently delete a notebook or page
#
##########################################################################

urlpatterns = []

