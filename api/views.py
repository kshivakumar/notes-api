from django.db import transaction, connection
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from rest_framework import generics, mixins, viewsets

from .models import Notebook, Page, Block, NotesRecycleBin
from .serializers import (
    UserSerializer,
    NotebookListSerializer,
    NotebookCreateSerializer,
    NotebookDetailSerializer,
    PageListSerializer,
    PageReadSerializer,
    PageCreateSerializer,
    BlockListSerializer,
    BlockReadSerializer,
    BlockCreateSerializer,
    NotesRecycleBinListSerializer,
    NotesRecycleBinDetailSerializer,
)


@api_view(["GET"])
def user(request):
    return Response(UserSerializer(request.user).data)


# TODO: Use psycopg2.sql for raw SQL
@api_view(["POST"])
def move_pages(request):
    nbs = request.user.notebooks.filter(
        pk__in=[request.data["source_notebook"], request.data["destination_notebook"]]
    )
    if len(nbs) != 2:
        return Response(status=404)

    src_nb = nbs.get(pk=request.data["source_notebook"])
    dest_nb = nbs.get(pk=request.data["destination_notebook"])
    pages = request.data["pages"]
    with transaction.atomic(), connection.cursor() as cur:
        cur.execute(
            f"UPDATE {Page._meta.db_table} SET notebook_id = %s WHERE id = ANY(%s::uuid[])",
            (dest_nb.pk, list(pages)),
        )
        cur.execute(
            f"""
            UPDATE {Notebook._meta.db_table}
            SET custom_page_order = ARRAY(
                SELECT UNNEST(custom_page_order)
                EXCEPT
                SELECT UNNEST(%s::uuid[])
            )
            WHERE id = %s
            """,
            (list(pages), src_nb.pk),
        )
        cur.execute(
            f"""
            UPDATE {Notebook._meta.db_table}
            SET custom_page_order = ARRAY_CAT(custom_page_order, %s::uuid[])
            WHERE id = %s
            """,
            (list(pages), dest_nb.pk),
        )
    return Response(status=204)


class NotebookViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        return Notebook.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == "list":
            return NotebookListSerializer
        elif self.action == "create":
            return NotebookCreateSerializer
        else:
            return NotebookDetailSerializer

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["user"] = self.request.user
        flag = self.request.query_params.get("include_page_list", "").lower()
        ctx["include_page_list"] = flag == "true"
        return ctx

    def perform_destroy(self, instance):
        serialized_nb = NotebookDetailSerializer(
            instance, context={"include_page_list": True}
        ).data
        serialized_nb["page_items"] = [
            PageReadSerializer(page, context={"include_block_list": True}).data
            for page in instance.pages.all()
        ]
        with transaction.atomic():
            NotesRecycleBin.objects.create(
                user=self.request.user,
                notebook_id=str(instance.pk),
                notebook_title=instance.title,
                item_type="notebook",
                item=serialized_nb,
            )
            super().perform_destroy(instance)

    @action(detail=False, methods=["POST"])
    def reposition(self, request):
        payload = request.data
        request.user.reposition_notebook(
            payload["element"],
            position=payload.get("position"),
            after=payload.get("after"),
        )
        return Response(status=204)


class PageListCreateView(generics.ListCreateAPIView):

    def get_queryset(self):
        return Page.objects.filter(notebook__pk=self.kwargs["notebook_id"])

    def get_serializer_class(self):
        if self.request.method == "GET":
            return PageListSerializer
        else:
            return PageCreateSerializer

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["notebook_id"] = self.kwargs["notebook_id"]
        return ctx


@api_view(["POST"])
def reposition_page(request, notebook_id, *args, **kwargs):
    payload = request.data
    nb = Notebook.objects.get(pk=notebook_id)
    nb.reposition_page(
        payload["element"],
        position=payload.get("position"),
        after=payload.get("after"),
    )
    return Response(status=204)


class PageDetailView(
    generics.RetrieveAPIView, generics.UpdateAPIView, generics.DestroyAPIView
):
    queryset = Page.objects.all()
    serializer_class = PageReadSerializer

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        flag = self.request.query_params.get("include_block_list", "").lower()
        ctx["include_block_list"] = flag == "true"
        return ctx

    def perform_destroy(self, instance):
        serialized_page = PageReadSerializer(
            instance, context={"include_block_list": True}
        ).data
        serialized_page["block_items"] = [
            BlockReadSerializer(block).data for block in instance.blocks.all()
        ]
        with transaction.atomic():
            NotesRecycleBin.objects.create(
                user=self.request.user,
                notebook_id=str(instance.notebook.pk),
                notebook_title=instance.notebook.title,
                item_type="page",
                item=serialized_page,
            )
            super().perform_destroy(instance)


class BlockListCreateView(generics.ListCreateAPIView):

    def get_queryset(self):
        return Block.objects.filter(page__pk=self.kwargs["page_id"])

    def get_serializer_class(self):
        if self.request.method == "GET":
            return BlockListSerializer
        else:
            return BlockCreateSerializer

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["page_id"] = self.kwargs["page_id"]
        return ctx


@api_view(["POST"])
def reposition_block(request, page_id):
    payload = request.data
    page = Page.objects.get(page_id)
    page.reposition_block(
        payload["element"],
        position=payload.get("position"),
        after=payload.get("after"),
    )
    return Response(status=204)


class BlockDetailView(
    generics.RetrieveAPIView, generics.UpdateAPIView, generics.DestroyAPIView
):
    queryset = Block.objects.all()
    serializer_class = BlockReadSerializer


class NotesRecycleBinViewSet(viewsets.ReadOnlyModelViewSet):

    def get_queryset(self):
        return NotesRecycleBin.objects.filter(user=self.request.user).order_by(
            "deleted_on"
        )

    def get_serializer_class(self):
        if self.action == "list":
            return NotesRecycleBinListSerializer
        return NotesRecycleBinDetailSerializer

    @action(detail=True, methods=["POST"])
    def restore(self, request):
        raise NotImplementedError()
