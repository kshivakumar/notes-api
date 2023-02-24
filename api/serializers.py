from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Notebook, Page, Block, NotesRecycleBin


class BlockListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Block
        fields = ["id"]
        read_only_fields = ["id"]


class BlockReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Block
        fields = ["id", "block_type", "content", "metadata"]
        read_only_fields = ["id"]


class BlockCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Block
        fields = ["block_type", "content", "metadata"]

    def create(self, validated_data):
        page = Page.objects.get(pk=self.context["page_id"])
        return super().create({**validated_data, "page": page})

    def to_representation(self, instance):
        return {"id": instance.pk}


class PageListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Page
        fields = ["id", "title", "updated"]
        read_only_fields = fields


class PageReadSerializer(serializers.ModelSerializer):
    notebook = serializers.CharField(source="notebook.pk")
    blocks = serializers.ListField(child=serializers.UUIDField(), source="block_order")

    class Meta:
        model = Page
        fields = [
            "id",
            "notebook",
            "title",
            "created",
            "updated",
            "preferences",
            "blocks",
        ]
        read_only_fields = ["id", "notebook", "created", "updated", "blocks"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.context.get("include_block_list"):
            self.fields.pop("blocks")


class PageCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Page
        fields = ["title", "preferences"]

    def create(self, validated_data):
        nb = Notebook.objects.get(pk=self.context["notebook_id"])
        return super().create({**validated_data, "notebook": nb})

    def to_representation(self, instance):
        return {"id": instance.pk}


class NotebookListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notebook
        fields = ["id", "title"]
        read_only_fields = ["id"]


class NotebookCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notebook
        fields = ["title", "preferences"]

    def create(self, validated_data):
        return super().create({**validated_data, "user": self.context["user"]})


class NotebookDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notebook
        fields = ["id", "title", "created", "updated", "preferences"]
        read_only_fields = ["id", "created", "updated"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.context.get("include_page_list"):
            self.fields["pages"] = PageListSerializer(many=True, read_only=True)


class UserSerializer(serializers.ModelSerializer):
    notebooks = NotebookListSerializer(many=True, read_only=True)

    class Meta:
        model = get_user_model()
        fields = [
            "username",
            "first_name",
            "last_name",
            "last_login",
            "preferences",
            "notebooks",
        ]
        read_only__fields = ["username", "last_login", "notebooks"]


class NotesRecycleBinListSerializer(serializers.ModelSerializer):
    pages = serializers.SerializerMethodField()

    class Meta:
        model = NotesRecycleBin
        fields = [
            "id",
            "item_type",
            "notebook_id",
            "notebook_title",
            "pages",
            "deleted_on",
        ]
        read_only_fields = fields

    def get_pages(self, instance):
        if instance.item_type == "notebook":
            return [
                {"id": p["id"], "title": p["title"]}
                for p in instance.item.get("page_items", [])
            ]
        elif instance.item_type == "page":
            return [{"id": instance.item["id"], "title": instance.item["title"]}]
        else:
            raise ValueError(f"Invalid item_type: {instance.item_type}")


class NotesRecycleBinDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotesRecycleBin
        fields = "__all__"
        read_only_fields = [f.name for f in NotesRecycleBin._meta.fields]
