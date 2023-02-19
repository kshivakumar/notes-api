import uuid

from django.conf import settings
from django.db import models
from django.db import connection, transaction
from django.contrib.auth.models import AbstractUser
from django.contrib.postgres import fields as pg_models


class User(AbstractUser):
    notebooks = pg_models.ArrayField(models.UUIDField(), default=list, editable=False)
    # To store user-defined notebook ordering
    # Reordering is easy compared to managing an additional "ordering" column in Notebook model
    # Ordering notebooks by title/created/updated should be performed on the client side.
    # Only the order and filter settings are stored on the server side - `preferences` column

    preferences = models.JSONField(null=True)
    # Store user prefrences, notebook order/filters, any other metadata


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
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)

    pages = pg_models.ArrayField(models.UUIDField(), default=list, editable=False)
    # To store user-defined page ordering.
    # See `User` preferences field

    preferences = models.JSONField(null=True)
    # For storing description, page order/filters settings, stylistic settings(e.g., bg color) and
    # UI behaviour settings(show/hide description, list/thumbnail view, etc).
    # May become a dumping groud for anything that can't be stored in other columns.

    def __repr__(self):
        return f"Notebook(user={self.user.username}, uuid={self.uuid}, title={self.title})"


class Page(TimestampedModel):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    notebook = models.ForeignKey(Notebook, on_delete=models.CASCADE)

    title = models.CharField(max_length=100)

    blocks = pg_models.ArrayField(models.UUIDField(), default=list, editable=False)
    # Using an ArrayField provides implicit ordering of blocks.
    # Blocks always follow user-defined order.

    preferences = models.JSONField(null=True)
    # similar to Notebook's field

    def save(self, *args, **kwargs):
        with transaction.atomic():
            super().save(*args, **kwargs)
            with connection.cursor() as cur:
                # TODO: Use psycopg2.sql
                cur.execute(f"UPDATE {self.notebook._meta.db_table} SET pages = ARRAY_APPEND(pages, %s) WHERE uuid = %s", [self.uuid, self.notebook.pk])

    def __repr__(self):
        return f"Page(notebook={self.notebook.uuid}, uuid={self.uuid}, title={self.title})"


BLOCK_TYPE = [ # Non-exhaustive list
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
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    page = models.ForeignKey(Page, on_delete=models.CASCADE)
    block_type = models.CharField(max_length=50, choices=BLOCK_TYPE)

    content = pg_models.ArrayField(models.JSONField(), default=list)
    # Why content is array-of-jsons?
    # The original intention was to have an array-of-arrays data type where each element is either a text or another array of length two or three.
    # This would allowing storing the text and the formatting(bold, color, etc) in a compact format.
    # If the text is "It's a rare, but dangerous potion" where "rare" is in bold and "dangerous" in red,
    # it would be stored as ["It's a ", ["rare", "b"], ", but ", ["dangerous", "color", "#ff0000"], " potion"].
    # ArrayField(ArrayField()) is not possible because Postgres requires all the inner arrays be of same size.
    # With array-of-jsons, data would be stored as [["It's a "], ["rare", "b"], [", but "], ["dangerous", "color", "#ff0000"], [" potion"]]

    # Why not just `content = JSONField()`?
    # ArrayField provides an intuitive and efficient "append" operation which is going to be the most common operation on the content field.

    # TODO: Explore alternative databases (e.g., MongoDB) for storing Blocks
    # that support mixed data types in `content` and efficient array/json operations.

    metadata = models.JSONField(null=True)
    # Primarily useful for non-text and container-type blocks such as image/video embeddings(size, show/hide thumbnail, etc.),
    # tables, backlinks and to-do lists

    def save(self, *args, **kwargs):
        with transaction.atomic():
            super().save(*args, **kwargs)
            with connection.cursor() as cur:
                # TODO: Use psycopg2.sql
                cur.execute(f"UPDATE {self.page._meta.db_table} SET blocks = ARRAY_APPEND(blocks, %s) WHERE uuid = %s", [self.uuid, self.page.pk])

    def __repr__(self):
        return f"Block(page={self.page.uuid}, id={self.id}, content={self.content})"


class NotesRecycleBin(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    item_type = models.CharField(max_length=100, choices=[("notebook", "Notebook"), ("page", "Page")])
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

