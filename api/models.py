import uuid

from django.conf import settings
from django.db import models
from django.db import connection, transaction
from django.contrib.auth.models import AbstractUser
from django.contrib.postgres import fields as pg_models


# TODO: Use psycopg2.sql for all raw SQL queries


class User(AbstractUser):
    custom_notebook_order = pg_models.ArrayField(
        models.UUIDField(), default=list, editable=False
    )
    # To store user-defined notebook ordering.
    # Reordering is easy compared to managing an additional "ordering" column in Notebook model.
    # Ordering notebooks by title/created/updated should be performed on the client side.
    # Only the order and filter settings are stored on the server side, in `preferences` column.

    preferences = models.JSONField(null=True)
    # Store user prefrences, notebook order/filters, any other metadata

    def reposition_notebook(self, notebook_id, *, position=None, after=None):
        with connection.cursor() as cur:
            reposition_array_element(
                cur, self, "custom_notebook_order", notebook_id, position, after
            )


class TimestampedModel(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


# Why UUID for Notebook, Page and Block?
# 1. Globally unique, beneficial for distributed systems.
# 2. More secure than sequential ids - UUIDs don't reveal information about the number of notebooks/pages or creation order.
# 3. Can be used as a slug field in the url so that the user can directly open a specific notebook or page in the browser, not applicable to blocks.
# 4. Works well with sharding strategies
# Disadvantages:
# 1. Both the table and the index consumes more space - 8 bytes(bigint) vs 16 bytes
# 2. Slightly lower read performance compared to bigint/int8 - https://www.cybertec-postgresql.com/en/int4-vs-int8-vs-uuid-vs-numeric-performance-on-bigger-joins/
# 3. Larger indexes can worsen write performance


class Notebook(TimestampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notebooks"
    )
    title = models.CharField(max_length=100)
    custom_page_order = pg_models.ArrayField(
        models.UUIDField(), default=list, editable=False
    )
    # To store user-defined page ordering.
    # See `User` preferences field

    preferences = models.JSONField(null=True)
    # For storing description, page order/filters settings, stylistic settings(e.g., bg color) and
    # UI behaviour settings(show/hide description, list/thumbnail view, etc).
    # May become a dumping groud for anything that can't be stored in other columns.

    def save(self, *args, **kwargs):
        with transaction.atomic():
            # https://docs.djangoproject.com/en/4.1/ref/models/instances/#django.db.models.Model._state:
            if self._state.adding:
                with connection.cursor() as cur:
                    cur.execute(
                        f"""
                        UPDATE {self.user._meta.db_table}
                        SET custom_notebook_order = ARRAY_APPEND(custom_notebook_order, %(notebook_id)s)
                        WHERE {self.user._meta.pk.column} = %(user_id)s
                        """,
                        {"notebook_id": self.pk, "user_id": self.user.pk},
                    )
            super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        with connection.cursor() as cur:
            cur.execute(
                f"""
               UPDATE {self.user._meta.db_table}
               SET custom_notebook_order = ARRAY_REMOVE(custom_notebook_order, %(notebook_id)s)
               WHERE {self.user._meta.pk.column} = %(user_id)s
               """,
                {"notebook_id": self.pk, "user_id": self.user.pk},
            )
            super().delete(*args, **kwargs)

    def reposition_page(self, page_id, *, position=None, after=None):
        with connection.cursor() as cur:
            reposition_array_element(
                cur, self, "custom_page_order", page_id, position, after
            )

    def __repr__(self):
        return f"Notebook(user={self.user.username}, pk={self.pk}, title={self.title})"


class Page(TimestampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    notebook = models.ForeignKey(
        Notebook, on_delete=models.CASCADE, related_name="pages"
    )
    title = models.CharField(max_length=100)

    block_order = pg_models.ArrayField(models.UUIDField(), default=list, editable=False)
    # Using an ArrayField provides implicit ordering of blocks.
    # Blocks always follow user-defined order.

    preferences = models.JSONField(null=True)
    # similar to Notebook's field

    def save(self, *args, **kwargs):
        with transaction.atomic():
            if self._state.adding:
                with connection.cursor() as cur:
                    cur.execute(
                        f"""
                        UPDATE {self.notebook._meta.db_table}
                        SET custom_page_order = ARRAY_APPEND(custom_page_order, %(page_id)s)
                        WHERE {self.notebook._meta.pk.column} = %(notebook_id)s""",
                        {
                            "notebook_id": self.notebook.pk,
                            "page_id": self.pk,
                        },
                    )
            super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        with connection.cursor() as cur:
            cur.execute(
                f"""
               UPDATE {self.notebook._meta.db_table}
               SET custom_page_order = ARRAY_REMOVE(custom_page_order, %(page_id)s)
               WHERE {self.notebook._meta.pk.column} = %(notebook_id)s
               """,
                {
                    "notebook_id": self.notebook.pk,
                    "page_id": self.pk,
                },
            )
            super().delete(*args, **kwargs)

    def reposition_block(self, block_id, *, position=None, after=None):
        with connection.cursor() as cur:
            reposition_array_element(cur, self, "block_order", block_id, position, after)

    def __repr__(self):
        return f"Page(notebook={self.notebook.pk}, pk={self.pk}, title={self.title})"


BLOCK_TYPE = [  # Non-exhaustive list
    ("h1", "Heading 1"),
    ("h2", "Heading 2"),
    ("h3", "Heading 3"),
    ("p", "Paragraph"),
    ("code", "Code Block"),
    ("ol", "Ordered List"),
    ("ul", "Unordered List"),
    ("todo", "To-Do List"),
    ("quote", "Quote Block"),
    ("br", "Divider Line"),
    ("empty", "Empty Line"),
]


class Block(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    page = models.ForeignKey(Page, on_delete=models.CASCADE, related_name="blocks")
    block_type = models.CharField(max_length=50, choices=BLOCK_TYPE)

    content = models.TextField()
    # In the current implementation, whenever there's a change in the text,
    # the entire `content` field is overridden with the new text.
    # In a future implementation, only the new/modified/deleted text will be
    # updated in the database. This could be achieved either through
    # a new data type that supports such operations efficiently
    # or by using string operators/functions if the text field is retained.
    # Formatting information such as bold or italic text is stored in the `metadata` field.
    # If the text is "It's a rare, but dangerous potion"
    # where "rare" is in bold and "dangerous" in red,
    # the metadata could be {"b": [7, 10], "#ff0000": [17, 25]} where the values are char indexes.
    # This representation may change and is ultimately dictated
    # by how efficiently the client can parse and render the text.

    metadata = models.JSONField(null=True)
    # To store formatting information for text blocks,
    # configuration details for container blocks (tables, backlinks, to-do lists, etc.),
    # and display settings(such as size, thumbnail visibility) for
    # embedded blocks(images, videos, docs, etc.)

    def save(self, *args, **kwargs):
        with transaction.atomic():
            if self._state.adding:
                with connection.cursor() as cur:
                    cur.execute(
                        f"""
                        UPDATE {self.page._meta.db_table}
                        SET block_order = ARRAY_APPEND(block_order, %(block_id)s)
                        WHERE {self.page._meta.pk.column} = %(page_id)s""",
                        {
                            "page_id": self.page.pk,
                            "block_id": self.pk,
                        },
                    )
            super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        with connection.cursor() as cur:
            cur.execute(
                f"""
               UPDATE {self.page._meta.db_table}
               SET block_order = ARRAY_REMOVE(block_order, %(block_id)s)
               WHERE {self.page._meta.pk.column} = %(page_id)s
               """,
                {"page_id": self.page.pk, "block_id": self.pk},
            )
            super().delete(*args, **kwargs)

    def __repr__(self):
        return f"Block(page={self.page.pk}, pk={self.pk}, content={self.content})"


class NotesRecycleBin(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    notebook_id = models.UUIDField()
    notebook_title = models.CharField(max_length=100)
    # Since notebook is the main container/context,
    # adding notebook id and title for quick access

    item_type = models.CharField(
        max_length=100, choices=[("notebook", "Notebook"), ("page", "Page")]
    )
    item = models.JSONField()
    # Store the entire hierarchy of {notebook -> pages -> blocks} or {pages -> blocks} as json

    deleted_on = models.DateTimeField(auto_now_add=True)

    def __repr__(self):
        return f"NotesRecycleBin(user={self.user.username}, item_type={self.item_type})"


# Why a separate table for storing deleted notebook/pages?
# Why not just add a `is_deleted` field to Notebook/Page model?
# To keep all the tables, especially block table, lean.
# This improves read performance provided tables are frequently vacuumed.
# Disadvantages:
# 1. Delete and restore operations become slow because transaction involves deleting from multiple table and writing to another table.
#    Not a major issue since end-users are willing to wait during restoration.
#    Some kind of queueing mechanism can be used to improve "Delete" operation UX.


def reposition_array_element(cur, instance, array_column, element, position=None, after=None):
    # TODO: Check the element(and the 'after' element) exist
    if position == "top":
        cur.execute(
            f"""
            UPDATE {instance._meta.db_table}
            SET {array_column} = ARRAY_PREPEND(%(element)s::uuid, ARRAY_REMOVE({array_column}, %(element)s::uuid))
            WHERE {instance._meta.pk.column} = %(pk)s
            """,
            {"element": element, "pk": instance.pk},
        )
    elif position == "bottom":
        cur.execute(
            f"""
            UPDATE {instance._meta.db_table}
            SET {array_column} = ARRAY_APPEND(ARRAY_REMOVE({array_column}, %(element)s::uuid), %(element)s::uuid)
            WHERE {instance._meta.pk.column} = %(pk)s
            """,
            {"element": element, "pk": instance.pk},
        )
    elif after:
        cur.execute(
            f"""
            UPDATE
                { instance._meta.db_table }
            SET
                { array_column } = ARRAY_CAT(
                    (ARRAY_REMOVE({ array_column }, %(element)s)) [:array_position(ARRAY_REMOVE({array_column}, %(element)s), %(after)s)],
                    ARRAY_CAT(
                        ARRAY [%(element)s],
                        (ARRAY_REMOVE({ array_column }, %(element)s)) [array_position(ARRAY_REMOVE({array_column}, %(element)s), %(after)s)+1:]
                    )
                )
            WHERE
            { instance._meta.pk.column } = %(pk)s
            """,
            {"element": element, "after": after, "pk": instance.pk},
        )
    else:
        raise ValueError(
            "At least one of `position`(value=top|bottom) or `after`(uuid) is expected"
        )
