from django.db import models
from django.contrib.auth.models import User


class TimestampedModel(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Notebook(TimestampedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notebooks")
    title = models.CharField(max_length=200)

    def __str__(self):
        return self.title


class Page(TimestampedModel):
    notebook = models.ForeignKey(
        Notebook, on_delete=models.CASCADE, related_name="pages"
    )
    title = models.CharField(max_length=200)
    content = models.TextField()

    def __str__(self):
        return f"[{self.notebook.title}] {self.title}"
